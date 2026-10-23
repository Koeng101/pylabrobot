"""Golden tests of what the Opentrons Flex does today: the HTTP it sends and the deck it leaves.

Each scenario drives a real `Flex` over `FakeRobotServer`, the HTTP transport with the network
replaced, and records every request, the deck after each step, and the tips each head holds.
"""

import pathlib
import unittest
from typing import Any, Dict, List, Optional, Tuple

from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.opentrons import Flex
from pylabrobot.opentrons.flex.flex_head import FlexHead1, FlexHead8, FlexHead96
from pylabrobot.opentrons.golden.recorder import FakeRobotServer, Recorder, tip_state
from pylabrobot.resources import (
  Container,
  Plate,
  Resource,
  Trash,
  cor_96_wellplate_360uL_Fb,
  set_tip_tracking,
  set_volume_tracking,
)
from pylabrobot.resources.opentrons import FlexDeck
from pylabrobot.resources.opentrons.flex_tip_racks import (
  flex_96_tiprack_50ul,
  flex_96_tiprack_200ul,
)
from pylabrobot.testing.golden import check_golden

GOLDEN = pathlib.Path(__file__).parent

# name, model, channels, minimum and maximum volume of each pipette a scenario mounts
_PIPETTES = {
  "p50_single_flex": ("p50_single_v3.5", 1, 1.0, 50.0),
  "p50_multi_flex": ("p50_multi_v3.5", 8, 1.0, 50.0),
  "p1000_96": ("p1000_96_v3.5", 96, 5.0, 1000.0),
}


def _instruments(pipettes: List[Tuple[str, str]], gripper: bool) -> List[Dict[str, Any]]:
  """`GET /instruments` data for pipettes given as (mount, name), and an optional gripper."""
  instruments: List[Dict[str, Any]] = []
  for mount, name in pipettes:
    model, channels, minimum, maximum = _PIPETTES[name]
    instruments.append(
      {
        "mount": mount,
        "instrumentType": "pipette",
        "instrumentName": name,
        "instrumentModel": model,
        "data": {"channels": channels, "min_volume": minimum, "max_volume": maximum},
      }
    )
  if gripper:
    instruments.append(
      {
        "mount": "extension",
        "instrumentType": "gripper",
        "instrumentName": "flexGripper",
        "instrumentModel": "gripperV1.3",
      }
    )
  return instruments


def _trough(name: str) -> Container:
  """A single-cavity reservoir with an SBS footprint."""
  return Container(name, 127.76, 85.48, 31.4, material_z_thickness=1, max_volume=10000)


class FlexGoldenTests(unittest.IsolatedAsyncioTestCase):
  """Scenarios through the Flex's public API, each checked against its golden file."""

  def setUp(self) -> None:
    set_tip_tracking(True)
    set_volume_tracking(True)
    self.addCleanup(set_tip_tracking, False)
    self.addCleanup(set_volume_tracking, False)

  def _flex(
    self,
    pipettes: List[Tuple[str, str]],
    gripper: bool = False,
    deck: Optional[FlexDeck] = None,
  ) -> Tuple[Flex, FakeRobotServer, Recorder]:
    """A Flex on a fake robot server reporting `pipettes`, a trash bin in A3, and a recorder."""
    server = FakeRobotServer(
      health={"name": "flex", "robot_model": "OT-3 Standard", "api_version": "8.2.0"},
      instruments=_instruments(pipettes, gripper),
      fixtures=[{"cutoutId": "cutoutA3", "cutoutFixtureId": "trashBinAdapter"}],
    )
    flex = Flex("robot.test", deck=deck or FlexDeck(), io=server)
    self.addAsyncCleanup(flex.disconnect)

    def mounted() -> Dict[str, Any]:
      """The tips on each head, by mount, as channel -> tip for the channels holding one."""
      heads: Dict[str, Any] = {}
      for head in flex.pipettes:
        heads[f"{head.mount}/{head.channels}"] = {
          str(channel): tip_state(tip)
          for channel, tip in enumerate(head.get_mounted_tips())
          if tip is not None
        }
      return heads

    return flex, server, Recorder(server, flex.deck, mounted)

  def _check(self, recorder: Recorder, scenario: str) -> None:
    check_golden(self, GOLDEN / f"{scenario}.json", recorder.record())

  async def test_lifecycle(self) -> None:
    """Setup places the trash where the robot reports it; a new run drops the heads; stop
    discards nothing when no tip is held, homes and releases the robot."""
    deck = FlexDeck()
    deck.assign_child_at_slot(Trash("trash", size_x=120, size_y=80, size_z=40), "D3")
    flex, _, rec = self._flex(
      [("left", "p50_single_flex"), ("right", "p50_multi_flex")], True, deck
    )

    await rec.step("setup()", flex.setup())
    await rec.step("create_run()", flex.create_run())
    await rec.step("initialize()", flex.initialize())
    await rec.step("home()", flex.home())
    await rec.step("stop()", flex.stop())
    self._check(rec, "lifecycle")

  async def test_single_channel(self) -> None:
    """FlexHead1: tips from an official rack, liquid in a custom plate and a trough, probes,
    refusals and wire failures, return to the rack, discard to trash, and an unsafe drop."""
    flex, server, rec = self._flex([("left", "p50_single_flex")])
    tips = flex_96_tiprack_50ul("tips")
    plate = cor_96_wellplate_360uL_Fb("plate")
    trough = _trough("trough")
    flex.deck.assign_child_at_slot(tips, "C1")
    flex.deck.assign_child_at_slot(plate, "C2")
    flex.deck.assign_child_at_slot(trough, "B2")
    rec.arrange("plate A1 holds 40 uL", lambda: _fill(plate, ["A1"], 40))
    rec.arrange("the trough holds 1000 uL", lambda: trough.tracker.set_volume(1000))

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    left = flex.left
    assert isinstance(left, FlexHead1)
    trash = flex.deck.get_trash_area()
    await rec.step("left.pick_up_tips(tips A1)", left.pick_up_tips(tips.get_item("A1")))
    await rec.step("left.aspirate(plate A1, 20)", left.aspirate(plate.get_well("A1"), 20))
    await rec.step("left.dispense(plate B1, 15)", left.dispense(plate.get_well("B1"), 15))
    await rec.step("left.touch_tip(plate B1)", left.touch_tip(plate.get_well("B1")))
    server.answer_liquid_probe(5.5)
    await rec.step(
      "left.probe_liquid_heights(plate A1) finds liquid at 5.5",
      left.probe_liquid_heights(plate.get_well("A1")),
    )
    await rec.step(
      "left.try_probe_liquid_heights(plate C1) finds none",
      left.try_probe_liquid_heights(plate.get_well("C1")),
    )
    server.fail_next("liquidProbe", "liquidNotFound")
    await rec.step(
      "left.probe_liquid_heights(plate C1) fails with liquidNotFound",
      left.probe_liquid_heights(plate.get_well("C1")),
    )
    await rec.step(
      "left.aspirate(plate C1, 10) from an empty well is refused",
      left.aspirate(plate.get_well("C1"), 10),
    )
    server.fail_next("aspirateInPlace", "PipetteOverpressureError")
    await rec.step(
      "left.aspirate(plate A1, 10) fails on the robot",
      left.aspirate(plate.get_well("A1"), 10),
    )
    await rec.step(
      "left.drop_tips(tips A1) returns a tip holding 5 uL",
      left.drop_tips(tips.get_item("A1")),
    )
    server.answer_tip_presence("absent")
    await rec.step(
      "left.pick_up_tips(tips B1) seats no tip", left.pick_up_tips(tips.get_item("B1"))
    )
    await rec.step("left.pick_up_tips(tips B1)", left.pick_up_tips(tips.get_item("B1")))
    await rec.step(
      "left.pick_up_tips(tips C1) while holding a tip", left.pick_up_tips(tips.get_item("C1"))
    )
    await rec.step("left.aspirate(trough, 30)", left.aspirate(trough, 30))
    await rec.step("left.dispense(trough, 10)", left.dispense(trough, 10))
    await rec.step("left.discard_tips(trash) with 20 uL in the tip", left.discard_tips(trash))
    await rec.step("left.pick_up_tips(tips C1)", left.pick_up_tips(tips.get_item("C1")))
    await rec.step("left.unsafe_drop_tip_in_place()", left.unsafe_drop_tip_in_place())
    await rec.step("left.pick_up_tips(tips D1)", left.pick_up_tips(tips.get_item("D1")))
    await rec.step("stop() discards the held tip", flex.stop())
    self._check(rec, "single_channel")

  async def test_eight_channel(self) -> None:
    """FlexHead8: full columns, a partial column, a single cherry-picked tip, mixing, a trough,
    column probes, and tips returned to the rack and discarded."""
    flex, server, rec = self._flex([("right", "p50_multi_flex")])
    tips = flex_96_tiprack_50ul("tips")
    plate = cor_96_wellplate_360uL_Fb("plate")
    trough = _trough("trough")
    flex.deck.assign_child_at_slot(tips, "C1")
    flex.deck.assign_child_at_slot(plate, "C2")
    flex.deck.assign_child_at_slot(trough, "B2")
    rec.arrange("plate column 1 holds 40 uL a well", lambda: _fill(plate, _column(1), 40))
    rec.arrange("the trough holds 1000 uL", lambda: trough.tracker.set_volume(1000))

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    right = flex.right
    assert isinstance(right, FlexHead8)
    trash = flex.deck.get_trash_area()
    await rec.step("right.pick_up_tips(tips column 1)", right.pick_up_tips(tips.column(0)))
    server.answer_liquid_probe(7.25)
    await rec.step(
      "right.probe_liquid_heights(plate, 0)", right.probe_liquid_heights(plate, column=0)
    )
    await rec.step(
      "right.try_probe_liquid_heights(plate, 5) finds none",
      right.try_probe_liquid_heights(plate, column=5),
    )
    await rec.step("right.aspirate(plate column 1, 20)", right.aspirate(plate.column(0), 20))
    await rec.step(
      "right.dispense(plate column 2, 20, post_mix=Mix(10, 2, 30))",
      right.dispense(plate.column(1), 20, post_mix=Mix(volume=10, repetitions=2, flow_rate=30)),
    )
    await rec.step("right.mix(plate column 2, 10, 2)", right.mix(plate.column(1), 10, 2))
    await rec.step(
      "right.aspirate(plate, 30, column=1) drawing more than column 2 holds",
      right.aspirate(plate, 30, column=1),
    )
    await rec.step("right.aspirate(trough, 5)", right.aspirate(trough, 5))
    await rec.step("right.dispense(trough, 5)", right.dispense(trough, 5))
    await rec.step("right.touch_tip(plate, 0)", right.touch_tip(plate, 0))
    await rec.step("right.drop_tips(tips, column=0)", right.drop_tips(tips, column=0))
    await rec.step(
      "right.pick_up_tips(tips E2:H2, use_channels=[4, 5, 6, 7])",
      right.pick_up_tips(tips.column(1)[4:], use_channels=[4, 5, 6, 7]),
    )
    await rec.step(
      "right.aspirate(plate E1:H1, 10, use_channels=[4, 5, 6, 7])",
      right.aspirate(plate.column(0)[4:], 10, use_channels=[4, 5, 6, 7]),
    )
    await rec.step("right.discard_tips(trash)", right.discard_tips(trash))
    await rec.step("right.pick_up_tips(tips A3) as a single tip", right.pick_up_tips(tips["A3"][0]))
    await rec.step("right.aspirate_single(plate, A1, 5)", right.aspirate_single(plate, "A1", 5))
    await rec.step("right.dispense_single(plate, A4, 5)", right.dispense_single(plate, "A4", 5))
    await rec.step("right.drop_single_tip(trash)", right.drop_single_tip(trash))
    await rec.step("stop()", flex.stop())
    self._check(rec, "eight_channel")

  async def test_ninety_six_channel(self) -> None:
    """FlexHead96: a whole rack, a whole plate, a trough, return to the rack and discard."""
    flex, _, rec = self._flex([("left", "p1000_96")])
    tips = flex_96_tiprack_200ul("tips")
    plate = cor_96_wellplate_360uL_Fb("plate")
    trough = _trough("trough")
    flex.deck.assign_child_at_slot(tips, "C1")
    flex.deck.assign_child_at_slot(plate, "C2")
    flex.deck.assign_child_at_slot(trough, "B2")
    rec.arrange(
      "every plate well holds 100 uL",
      lambda: _fill(plate, [plate.get_child_identifier(w) for w in plate.get_all_items()], 100),
    )

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    head = flex.head96
    assert isinstance(head, FlexHead96)
    trash = flex.deck.get_trash_area()
    await rec.step("head96.pick_up_tips(tips)", head.pick_up_tips(tips))
    await rec.step("head96.aspirate(plate, 20)", head.aspirate(plate, 20))
    await rec.step("head96.dispense(trough, 10)", head.dispense(trough, 10))
    await rec.step("head96.touch_tip(plate)", head.touch_tip(plate))
    await rec.step("head96.drop_tips(tips) with 10 uL in each tip", head.drop_tips(tips))
    await rec.step("head96.pick_up_tips(tips)", head.pick_up_tips(tips))
    await rec.step("head96.discard_tips(trash)", head.discard_tips(trash))
    await rec.step("stop()", flex.stop())
    self._check(rec, "ninety_six_channel")

  async def test_gripper_and_deck_sync(self) -> None:
    """Gripper moves of a plate and a non-pipettable stub, refusals, the robot's tip record
    synced from the rack, labware taken off the deck and put back, and a reload."""
    flex, _, rec = self._flex([("left", "p50_single_flex")], gripper=True)
    tips = flex_96_tiprack_50ul("tips")
    plate = cor_96_wellplate_360uL_Fb("plate")
    other = cor_96_wellplate_360uL_Fb("other_plate")
    riser = Resource("riser", size_x=127.76, size_y=85.48, size_z=20)
    flex.deck.assign_child_at_slot(tips, "C1")
    flex.deck.assign_child_at_slot(plate, "C2")
    flex.deck.assign_child_at_slot(other, "B2")
    flex.deck.assign_child_at_slot(riser, "D2")
    rec.arrange("plate A1 holds 40 uL", lambda: _fill(plate, ["A1"], 40))

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    left, gripper = flex.left, flex.gripper
    assert isinstance(left, FlexHead1) and gripper is not None
    await rec.step(
      "gripper.move_labware(plate, D3, grip_distance_from_top=5)",
      gripper.move_labware(plate, "D3", grip_distance_from_top=5),
    )
    await rec.step(
      "gripper.move_labware(plate, B2) onto an occupied slot", gripper.move_labware(plate, "B2")
    )
    await rec.step("gripper.move_labware(plate, B4)", gripper.move_labware(plate, "B4"))
    await rec.step("gripper.move_labware(riser, C3)", gripper.move_labware(riser, "C3"))
    await rec.step("reload_labware(riser) for the stub", flex.reload_labware(riser))
    await rec.step("reload_labware(plate)", flex.reload_labware(plate))
    rec.arrange(
      "an operator takes the tips in column 1 and A2",
      lambda: tips.set_tip_state({name: False for name in [*_column(1), "A2"]}),
    )
    await rec.step("sync_tips_to_robot(tips)", flex.sync_tips_to_robot(tips))
    await rec.step("labware_moved_off_deck(plate)", flex.labware_moved_off_deck(plate))
    await rec.step(
      "labware_moved_off_deck(other_plate) never loaded", flex.labware_moved_off_deck(other)
    )
    rec.arrange("plate is put back in C2", lambda: flex.deck.assign_child_at_slot(plate, "C2"))
    await rec.step("left.pick_up_tips(tips B2)", left.pick_up_tips(tips.get_item("B2")))
    await rec.step(
      "left.touch_tip(plate A1) loads the plate afresh", left.touch_tip(plate.get_well("A1"))
    )
    await rec.step("left.aspirate(plate A1, 10)", left.aspirate(plate.get_well("A1"), 10))
    await rec.step("left.dispense(plate A2, 10)", left.dispense(plate.get_well("A2"), 10))
    await rec.step("left.drop_tips(tips B2)", left.drop_tips(tips.get_item("B2")))
    await rec.step("gripper.move_labware(tips, D1)", gripper.move_labware(tips, "D1"))
    await rec.step("stop()", flex.stop())
    self._check(rec, "gripper_and_deck_sync")


def _column(column: int) -> List[str]:
  """The well names of a 96-format column, numbered from 1."""
  return [f"{row}{column}" for row in "ABCDEFGH"]


def _fill(plate: Plate, wells: List[str], volume: float) -> None:
  """Set the liquid in `wells` of `plate` by hand."""
  for name in wells:
    plate.get_well(name).tracker.set_volume(volume)


if __name__ == "__main__":
  unittest.main()
