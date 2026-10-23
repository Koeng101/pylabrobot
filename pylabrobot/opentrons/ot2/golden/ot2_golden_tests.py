"""Golden tests of what the Opentrons OT-2 does today: the HTTP it sends and the deck it leaves.

Each scenario drives a real `OT2`, with its real `OpentronsAPI` and `OpentronsRun`, over
`FakeRobotServer`, the HTTP transport with the network replaced. It records every request, the
deck after each step, and the tips each pipette holds with the spots they came from.
"""

import pathlib
import unittest
from typing import Any, Dict, List, Tuple

from pylabrobot.opentrons import OT2, OT2_8ChannelPipette, OT2SingleChannelPipette
from pylabrobot.opentrons.golden.recorder import FakeRobotServer, Recorder, tip_state
from pylabrobot.resources import Plate, set_tip_tracking, set_volume_tracking
from pylabrobot.resources.celltreat import celltreat_96_wellplate_350uL_Fb
from pylabrobot.resources.opentrons import OTDeck, opentrons_96_filtertiprack_20ul
from pylabrobot.testing.golden import check_golden

GOLDEN = pathlib.Path(__file__).parent

# The model each pipette name reports on its mount.
_MODELS = {"p20_single_gen2": "p20_single_v2.0", "p20_multi_gen2": "p20_multi_v2.0"}


class OT2GoldenTests(unittest.IsolatedAsyncioTestCase):
  """Scenarios through the OT-2's public API, each checked against its golden file."""

  def setUp(self) -> None:
    set_tip_tracking(True)
    set_volume_tracking(True)
    self.addCleanup(set_tip_tracking, False)
    self.addCleanup(set_volume_tracking, False)

  def _ot2(
    self, left: str = "", right: str = "", version: str = "7.1.0"
  ) -> Tuple[OT2, FakeRobotServer, Recorder]:
    """An OT-2 on a fake robot server with the named pipettes mounted, and a recorder."""
    mounted: Dict[str, Dict[str, Any]] = {"left": {}, "right": {}}
    for mount, name in (("left", left), ("right", right)):
      if name:
        mounted[mount] = {"name": name, "model": _MODELS[name], "id": f"{mount}-serial"}
    server = FakeRobotServer(
      health={"name": "ot2", "robot_model": "OT-2 Standard", "api_version": version},
      mounted=mounted,
    )
    robot = OT2("ot2.test", deck=OTDeck(), io=server)
    self.addAsyncCleanup(robot.stop)

    def held() -> Dict[str, Any]:
      """The tips on each pipette, by mount, with the tip spots they were picked up from."""
      return {
        pipette.mount: {
          "tips": [tip_state(tip) for tip in pipette._tips],
          "origins": [spot.name for spot in pipette._tip_origins],
        }
        for pipette in robot.pipettes
      }

    return robot, server, Recorder(server, robot.deck, held)

  def _check(self, recorder: Recorder, scenario: str) -> None:
    check_golden(self, GOLDEN / f"{scenario}.json", recorder.record())

  async def test_lifecycle(self) -> None:
    """Queries before setup, setup binding both mounts and homing, home, and stop."""
    robot, _, rec = self._ot2(left="p20_single_gen2", right="p20_multi_gen2")

    await rec.step("connect()", robot.connect())
    await rec.step("get_mounted_pipettes()", robot.get_mounted_pipettes())
    await rec.step("setup()", robot.setup())
    await rec.step("home()", robot.home())
    await rec.step("stop()", robot.stop())
    self._check(rec, "lifecycle")

  async def test_single_channel(self) -> None:
    """Single channel: tips from an official and a custom rack, aspirate, dispense and mix,
    refusals and a wire failure, return, drop and discard."""
    robot, server, rec = self._ot2(left="p20_single_gen2")
    tips = opentrons_96_filtertiprack_20ul("tips")
    custom = opentrons_96_filtertiprack_20ul("custom_tips")
    custom.model = "custom 20 uL rack"
    plate = celltreat_96_wellplate_350uL_Fb("plate")
    robot.deck.assign_child_at_slot(tips, 1)
    robot.deck.assign_child_at_slot(plate, 2)
    robot.deck.assign_child_at_slot(custom, 3)
    rec.arrange("plate A1 holds 15 uL", lambda: _fill(plate, ["A1"], 15))

    await rec.step("setup(skip_home=True)", robot.setup(skip_home=True))
    pipette = robot.left_pipette
    assert isinstance(pipette, OT2SingleChannelPipette)
    await rec.step("left.pick_up_tip(tips A1)", pipette.pick_up_tip(tips.get_item("A1")))
    await rec.step("left.aspirate(plate A1, 10)", pipette.aspirate(plate.get_well("A1"), 10))
    await rec.step("left.dispense(plate B1, 6)", pipette.dispense(plate.get_well("B1"), 6))
    await rec.step("left.mix(plate B1, 3, 2)", pipette.mix(plate.get_well("B1"), 3, 2))
    await rec.step(
      "left.aspirate(plate C1, 5) from an empty well is refused",
      pipette.aspirate(plate.get_well("C1"), 5),
    )
    server.fail_next("aspirateInPlace", "PipetteOverpressureError")
    await rec.step(
      "left.aspirate(plate A1, 5) fails on the robot", pipette.aspirate(plate.get_well("A1"), 5)
    )
    await rec.step("left.discard_tip() with 4 uL in the tip is refused", pipette.discard_tip())
    await rec.step(
      "left.return_tip(allow_nonzero_volume=True)", pipette.return_tip(allow_nonzero_volume=True)
    )
    await rec.step("left.pick_up_tip(tips B1)", pipette.pick_up_tip(tips.get_item("B1")))
    await rec.step(
      "left.pick_up_tip(tips C1) while holding a tip", pipette.pick_up_tip(tips.get_item("C1"))
    )
    await rec.step(
      "left.drop_tip(tips A1) onto an occupied spot", pipette.drop_tip(tips.get_item("A1"))
    )
    rec.arrange(
      "an operator takes the tip from tips H12", lambda: tips.set_tip_state({"H12": False})
    )
    await rec.step("left.drop_tip(tips H12)", pipette.drop_tip(tips.get_item("H12")))
    await rec.step(
      "left.pick_up_tip(custom_tips A1) defines the rack",
      pipette.pick_up_tip(custom.get_item("A1")),
    )
    await rec.step("left.discard_tip()", pipette.discard_tip())
    await rec.step("stop()", robot.stop())
    self._check(rec, "single_channel")

  async def test_discard_before_7_1(self) -> None:
    """Software older than 7.1.0 discards with a dropTip into the fixed trash labware."""
    robot, _, rec = self._ot2(right="p20_single_gen2", version="7.0.2")
    tips = opentrons_96_filtertiprack_20ul("tips")
    robot.deck.assign_child_at_slot(tips, 1)

    await rec.step("setup(skip_home=True)", robot.setup(skip_home=True))
    pipette = robot.right_pipette
    assert isinstance(pipette, OT2SingleChannelPipette)
    await rec.step("right.pick_up_tip(tips A1)", pipette.pick_up_tip(tips.get_item("A1")))
    await rec.step("right.discard_tip()", pipette.discard_tip())
    await rec.step("stop()", robot.stop())
    self._check(rec, "discard_before_7_1")

  async def test_eight_channel(self) -> None:
    """Eight channel: a full column, liquid in columns, return to the rack, a partial column
    refused over tips below it and taken once they are gone, and a discard."""
    robot, _, rec = self._ot2(left="p20_multi_gen2")
    tips = opentrons_96_filtertiprack_20ul("tips")
    plate = celltreat_96_wellplate_350uL_Fb("plate")
    robot.deck.assign_child_at_slot(tips, 1)
    robot.deck.assign_child_at_slot(plate, 2)
    rec.arrange("plate column 1 holds 15 uL a well", lambda: _fill(plate, _column(1), 15))

    await rec.step("setup(skip_home=True)", robot.setup(skip_home=True))
    pipette = robot.left_pipette
    assert isinstance(pipette, OT2_8ChannelPipette)
    await rec.step("left.pick_up_tips(tips A1:H1)", pipette.pick_up_tips(tips["A1:H1"]))
    await rec.step("left.aspirate(plate A1:H1, 10)", pipette.aspirate(plate["A1:H1"], 10))
    await rec.step("left.dispense(plate A2:H2, 10)", pipette.dispense(plate["A2:H2"], 10))
    await rec.step("left.mix(plate A2:H2, 5, 2)", pipette.mix(plate["A2:H2"], 5, 2))
    await rec.step("left.return_tips()", pipette.return_tips())
    await rec.step(
      "left.pick_up_tips(tips A2:D2) over tips in E2:H2", pipette.pick_up_tips(tips["A2:D2"])
    )
    rec.arrange(
      "an operator takes the tips from E2:H2",
      lambda: tips.set_tip_state({name: False for name in ["E2", "F2", "G2", "H2"]}),
    )
    await rec.step("left.pick_up_tips(tips A2:D2)", pipette.pick_up_tips(tips["A2:D2"]))
    await rec.step("left.aspirate(plate A1:D1, 2)", pipette.aspirate(plate["A1:D1"], 2))
    await rec.step(
      "left.discard_tips(allow_nonzero_volume=True)",
      pipette.discard_tips(allow_nonzero_volume=True),
    )
    await rec.step("stop()", robot.stop())
    self._check(rec, "eight_channel")


def _column(column: int) -> List[str]:
  """The well names of a 96-format column, numbered from 1."""
  return [f"{row}{column}" for row in "ABCDEFGH"]


def _fill(plate: Plate, wells: List[str], volume: float) -> None:
  """Set the liquid in `wells` of `plate` by hand."""
  for name in wells:
    plate.get_well(name).tracker.set_volume(volume)


if __name__ == "__main__":
  unittest.main()
