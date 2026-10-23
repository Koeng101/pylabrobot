"""Golden tests of what the Opentrons OT-2 does: the HTTP it sends and the deck it leaves.

Each scenario drives a real `OT2`, with its real `OpentronsAPI` and `OpentronsRun`, over
`FakeRobotServer`, the HTTP transport with the network replaced. It records every request, the
deck after each step as the resource store holds it, and the tips each pipette holds with the
spots they came from.
"""

import pathlib
import unittest
from typing import Any, Dict, List, Tuple, Union, cast

from pylabrobot.opentrons import OT2, OT2_8ChannelPipette, OT2SingleChannelPipette
from pylabrobot.opentrons.decks import create_ot2_deck, get_slot_holder
from pylabrobot.opentrons.golden.recorder import FakeRobotServer, Recorder, tip_state
from pylabrobot.resources.store import handles, library
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing.golden import check_golden

GOLDEN = pathlib.Path(__file__).parent

_TIPS = "opentrons_96_filtertiprack_20ul"
_PLATE = "celltreat_96_wellplate_350uL_Fb"

# The model each pipette name reports on its mount.
_MODELS = {"p20_single_gen2": "p20_single_v2.0", "p20_multi_gen2": "p20_multi_v2.0"}


class OT2GoldenTests(unittest.IsolatedAsyncioTestCase):
  """Scenarios through the OT-2's public API, each checked against its golden file."""

  async def _ot2(
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
    deck = await create_ot2_deck(ResourceStore.in_memory())
    robot = OT2("ot2.test", deck=deck, io=server)
    self.addAsyncCleanup(robot.stop)

    async def held() -> Dict[str, Any]:
      """The tips on each pipette, by mount, with the tip spots they were picked up from."""
      found: Dict[str, Any] = {}
      for pipette in robot.pipettes:
        tips = [tip for tip in await pipette.get_mounted_tips() if tip is not None]
        found[pipette.mount] = {
          "tips": [await tip_state(tip) for tip in tips],
          "origins": [spot.name for spot in pipette._tip_origins],
        }
      return found

    return robot, server, await Recorder.start(server, deck, held)

  async def _place(
    self, robot: OT2, source: Union[str, pb.ResourceDefinition], name: str, slot: int
  ) -> Any:
    """Make labware from a model or a definition in a slot of the OT-2's deck."""
    holder = await get_slot_holder(robot.deck, slot)
    return await robot.store.create(source, name=name, parent=holder)

  async def _check(self, recorder: Recorder, scenario: str) -> None:
    check_golden(self, GOLDEN / f"{scenario}.json", await recorder.record())

  async def test_lifecycle(self) -> None:
    """Queries before setup, setup binding both mounts and homing, home, and stop."""
    robot, _, rec = await self._ot2(left="p20_single_gen2", right="p20_multi_gen2")

    await rec.step("connect()", robot.connect())
    await rec.step("get_mounted_pipettes()", robot.get_mounted_pipettes())
    await rec.step("setup()", robot.setup())
    await rec.step("home()", robot.home())
    await rec.step("stop()", robot.stop())
    await self._check(rec, "lifecycle")

  async def test_single_channel(self) -> None:
    """Single channel: tips from an official and a custom rack, aspirate, dispense and mix,
    refusals and a wire failure, return, drop and discard."""
    robot, server, rec = await self._ot2(left="p20_single_gen2")
    tips = cast(handles.TipRack, await self._place(robot, _TIPS, "tips", 1))
    plate = cast(handles.Plate, await self._place(robot, _PLATE, "plate", 2))
    custom_rack = library.get_model(_TIPS).definition
    custom_rack.attributes.model = "custom 20 uL rack"
    custom = cast(handles.TipRack, await self._place(robot, custom_rack, "custom_tips", 3))
    await rec.arrange("plate A1 holds 15 uL", _fill(plate, ["A1"], 15))

    await rec.step("setup(skip_home=True)", robot.setup(skip_home=True))
    pipette = robot.left_pipette
    assert isinstance(pipette, OT2SingleChannelPipette)
    await rec.step("left.pick_up_tip(tips A1)", pipette.pick_up_tip(tips.get_tip_spot("A1")))
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
    await rec.step("left.pick_up_tip(tips B1)", pipette.pick_up_tip(tips.get_tip_spot("B1")))
    await rec.step(
      "left.pick_up_tip(tips C1) while holding a tip", pipette.pick_up_tip(tips.get_tip_spot("C1"))
    )
    await rec.step(
      "left.drop_tip(tips A1) onto an occupied spot", pipette.drop_tip(tips.get_tip_spot("A1"))
    )
    await rec.arrange("an operator takes the tip from tips H12", _take(tips, ["H12"]))
    await rec.step("left.drop_tip(tips H12)", pipette.drop_tip(tips.get_tip_spot("H12")))
    await rec.step(
      "left.pick_up_tip(custom_tips A1) defines the rack",
      pipette.pick_up_tip(custom.get_tip_spot("A1")),
    )
    await rec.step("left.discard_tip()", pipette.discard_tip())
    await rec.step("stop()", robot.stop())
    await self._check(rec, "single_channel")

  async def test_discard_before_7_1(self) -> None:
    """Software older than 7.1.0 discards with a dropTip into the fixed trash labware."""
    robot, _, rec = await self._ot2(right="p20_single_gen2", version="7.0.2")
    tips = cast(handles.TipRack, await self._place(robot, _TIPS, "tips", 1))

    await rec.step("setup(skip_home=True)", robot.setup(skip_home=True))
    pipette = robot.right_pipette
    assert isinstance(pipette, OT2SingleChannelPipette)
    await rec.step("right.pick_up_tip(tips A1)", pipette.pick_up_tip(tips.get_tip_spot("A1")))
    await rec.step("right.discard_tip()", pipette.discard_tip())
    await rec.step("stop()", robot.stop())
    await self._check(rec, "discard_before_7_1")

  async def test_eight_channel(self) -> None:
    """Eight channel: a full column, liquid in columns, return to the rack, a partial column
    refused over tips below it and taken once they are gone, and a discard."""
    robot, _, rec = await self._ot2(left="p20_multi_gen2")
    tips = cast(handles.TipRack, await self._place(robot, _TIPS, "tips", 1))
    plate = cast(handles.Plate, await self._place(robot, _PLATE, "plate", 2))
    await rec.arrange("plate column 1 holds 15 uL a well", _fill(plate, _column(1), 15))

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
    await rec.arrange(
      "an operator takes the tips from E2:H2", _take(tips, ["E2", "F2", "G2", "H2"])
    )
    await rec.step("left.pick_up_tips(tips A2:D2)", pipette.pick_up_tips(tips["A2:D2"]))
    await rec.step("left.aspirate(plate A1:D1, 2)", pipette.aspirate(plate["A1:D1"], 2))
    await rec.step(
      "left.discard_tips(allow_nonzero_volume=True)",
      pipette.discard_tips(allow_nonzero_volume=True),
    )
    await rec.step("stop()", robot.stop())
    await self._check(rec, "eight_channel")


def _column(column: int) -> List[str]:
  """The well names of a 96-format column, numbered from 1."""
  return [f"{row}{column}" for row in "ABCDEFGH"]


async def _fill(plate: handles.Plate, wells: List[str], volume: float) -> None:
  """Set the liquid in `wells` of `plate` by hand."""
  for name in wells:
    await plate.get_well(name).set_volume(volume)


async def _take(rack: handles.TipRack, spots: List[str]) -> None:
  """Take the tips from `spots` of `rack` by hand."""
  await rack.store.commands.update_resources(
    spb.UpdateResourcesRequest(
      updates=[
        spb.ResourceUpdate(
          tip_presence=pb.SetTipPresence(
            spots=[rack.get_tip_spot(spot).ref for spot in spots], present=False
          )
        )
      ]
    )
  )


if __name__ == "__main__":
  unittest.main()
