"""Golden tests of what the Opentrons Flex does: the HTTP it sends and the deck it leaves.

Each scenario drives a real `Flex` over `FakeRobotServer`, the HTTP transport with the network
replaced, and records every request, the deck after each step as the resource store holds it, and
the tips each head holds.
"""

import pathlib
import unittest
from typing import Any, Dict, List, Optional, Tuple, cast

from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.opentrons import Flex
from pylabrobot.opentrons.decks import (
  assign_child_at_slot,
  create_flex_deck,
  get_slot_holder,
  get_trash_area,
  trash,
)
from pylabrobot.opentrons.flex.flex_head import FlexHead1, FlexHead8, FlexHead96
from pylabrobot.opentrons.golden.recorder import FakeRobotServer, Recorder, tip_state
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb
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


def _trough(name: str) -> pb.ResourceDefinition:
  """A single-cavity reservoir with an SBS footprint."""
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 31.4),
    kind=pb.RESOURCE_KIND_CONTAINER,
    type_name="Container",
    container=pb.ContainerSpec(max_volume=10000, material_z_thickness=1),
    state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
  )


class FlexGoldenTests(unittest.IsolatedAsyncioTestCase):
  """Scenarios through the Flex's public API, each checked against its golden file."""

  async def _flex(
    self,
    pipettes: List[Tuple[str, str]],
    gripper: bool = False,
    deck: Optional[handles.Deck] = None,
  ) -> Tuple[Flex, FakeRobotServer, Recorder]:
    """A Flex on a fake robot server reporting `pipettes`, a trash bin in A3, and a recorder."""
    server = FakeRobotServer(
      health={"name": "flex", "robot_model": "OT-3 Standard", "api_version": "8.2.0"},
      instruments=_instruments(pipettes, gripper),
      fixtures=[{"cutoutId": "cutoutA3", "cutoutFixtureId": "trashBinAdapter"}],
    )
    if deck is None:
      deck = await create_flex_deck(ResourceStore.in_memory())
    flex = Flex("robot.test", deck=deck, io=server)
    self.addAsyncCleanup(flex.disconnect)

    async def mounted() -> Dict[str, Any]:
      """The tips on each head, by mount, as channel -> tip for the channels holding one."""
      heads: Dict[str, Any] = {}
      for head in flex.pipettes:
        heads[f"{head.mount}/{head.channels}"] = {
          str(channel): await tip_state(tip)
          for channel, tip in enumerate(await head.get_mounted_tips())
          if tip is not None
        }
      return heads

    return flex, server, await Recorder.start(server, flex.deck, mounted)

  async def _place(self, flex: Flex, source: Any, name: str, slot: str) -> Any:
    """Make labware from a model or a definition in a slot of the Flex's deck."""
    return await flex.store.create(source, name=name, parent=await get_slot_holder(flex.deck, slot))

  async def _check(self, recorder: Recorder, scenario: str) -> None:
    check_golden(self, GOLDEN / f"{scenario}.json", await recorder.record())

  async def test_lifecycle(self) -> None:
    """Setup places the trash where the robot reports it; a new run drops the heads; stop
    discards nothing when no tip is held, homes and releases the robot."""
    deck = await create_flex_deck(ResourceStore.in_memory())
    bin_ = await deck.store.create(trash("trash", Coordinate(120, 80, 40)), name="trash")
    await assign_child_at_slot(deck, bin_, "D3")
    flex, _, rec = await self._flex(
      [("left", "p50_single_flex"), ("right", "p50_multi_flex")], True, deck
    )

    await rec.step("setup()", flex.setup())
    await rec.step("create_run()", flex.create_run())
    await rec.step("initialize()", flex.initialize())
    await rec.step("home()", flex.home())
    await rec.step("stop()", flex.stop())
    await self._check(rec, "lifecycle")

  async def test_single_channel(self) -> None:
    """FlexHead1: tips from an official rack, liquid in a custom plate and a trough, probes,
    refusals and wire failures, return to the rack, discard to trash, and an unsafe drop."""
    flex, server, rec = await self._flex([("left", "p50_single_flex")])
    tips = cast(handles.TipRack, await self._place(flex, "flex_96_tiprack_50ul", "tips", "C1"))
    plate = cast(handles.Plate, await self._place(flex, "cor_96_wellplate_360uL_Fb", "plate", "C2"))
    trough = cast(handles.Container, await self._place(flex, _trough("trough"), "trough", "B2"))
    await rec.arrange("plate A1 holds 40 uL", plate.get_well("A1").set_volume(40))
    await rec.arrange("the trough holds 1000 uL", trough.set_volume(1000))

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    left = flex.left
    assert isinstance(left, FlexHead1)
    trash_area = await get_trash_area(flex.deck)
    await rec.step("left.pick_up_tips(tips A1)", left.pick_up_tips(tips.get_tip_spot("A1")))
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
      left.drop_tips(tips.get_tip_spot("A1")),
    )
    server.answer_tip_presence("absent")
    await rec.step(
      "left.pick_up_tips(tips B1) seats no tip", left.pick_up_tips(tips.get_tip_spot("B1"))
    )
    await rec.step("left.pick_up_tips(tips B1)", left.pick_up_tips(tips.get_tip_spot("B1")))
    await rec.step(
      "left.pick_up_tips(tips C1) while holding a tip",
      left.pick_up_tips(tips.get_tip_spot("C1")),
    )
    await rec.step("left.aspirate(trough, 30)", left.aspirate(trough, 30))
    await rec.step("left.dispense(trough, 10)", left.dispense(trough, 10))
    await rec.step("left.discard_tips(trash) with 20 uL in the tip", left.discard_tips(trash_area))
    await rec.step("left.pick_up_tips(tips C1)", left.pick_up_tips(tips.get_tip_spot("C1")))
    await rec.step("left.unsafe_drop_tip_in_place()", left.unsafe_drop_tip_in_place())
    await rec.step("left.pick_up_tips(tips D1)", left.pick_up_tips(tips.get_tip_spot("D1")))
    await rec.step("stop() discards the held tip", flex.stop())
    await self._check(rec, "single_channel")

  async def test_eight_channel(self) -> None:
    """FlexHead8: full columns, a partial column, a single cherry-picked tip, mixing, a trough,
    column probes, and tips returned to the rack and discarded."""
    flex, server, rec = await self._flex([("right", "p50_multi_flex")])
    tips = cast(handles.TipRack, await self._place(flex, "flex_96_tiprack_50ul", "tips", "C1"))
    plate = cast(handles.Plate, await self._place(flex, "cor_96_wellplate_360uL_Fb", "plate", "C2"))
    trough = cast(handles.Container, await self._place(flex, _trough("trough"), "trough", "B2"))
    await rec.arrange("plate column 1 holds 40 uL a well", _fill(plate, _column(1), 40))
    await rec.arrange("the trough holds 1000 uL", trough.set_volume(1000))

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    right = flex.right
    assert isinstance(right, FlexHead8)
    trash_area = await get_trash_area(flex.deck)
    await rec.step("right.pick_up_tips(tips column 1)", right.pick_up_tips(tips["A1:H1"]))
    server.answer_liquid_probe(7.25)
    await rec.step(
      "right.probe_liquid_heights(plate, 0)", right.probe_liquid_heights(plate, column=0)
    )
    await rec.step(
      "right.try_probe_liquid_heights(plate, 5) finds none",
      right.try_probe_liquid_heights(plate, column=5),
    )
    await rec.step("right.aspirate(plate column 1, 20)", right.aspirate(plate["A1:H1"], 20))
    await rec.step(
      "right.dispense(plate column 2, 20, post_mix=Mix(10, 2, 30))",
      right.dispense(plate["A2:H2"], 20, post_mix=Mix(volume=10, repetitions=2, flow_rate=30)),
    )
    await rec.step("right.mix(plate column 2, 10, 2)", right.mix(plate["A2:H2"], 10, 2))
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
      right.pick_up_tips(tips["E2:H2"], use_channels=[4, 5, 6, 7]),
    )
    await rec.step(
      "right.aspirate(plate E1:H1, 10, use_channels=[4, 5, 6, 7])",
      right.aspirate(plate["E1:H1"], 10, use_channels=[4, 5, 6, 7]),
    )
    await rec.step("right.discard_tips(trash)", right.discard_tips(trash_area))
    await rec.step(
      "right.pick_up_tips(tips A3) as a single tip", right.pick_up_tips(tips.get_tip_spot("A3"))
    )
    await rec.step("right.aspirate_single(plate, A1, 5)", right.aspirate_single(plate, "A1", 5))
    await rec.step("right.dispense_single(plate, A4, 5)", right.dispense_single(plate, "A4", 5))
    await rec.step("right.drop_single_tip(trash)", right.drop_single_tip(trash_area))
    await rec.step("stop()", flex.stop())
    await self._check(rec, "eight_channel")

  async def test_ninety_six_channel(self) -> None:
    """FlexHead96: a whole rack, a whole plate, a trough, return to the rack and discard."""
    flex, _, rec = await self._flex([("left", "p1000_96")])
    tips = cast(handles.TipRack, await self._place(flex, "flex_96_tiprack_200ul", "tips", "C1"))
    plate = cast(handles.Plate, await self._place(flex, "cor_96_wellplate_360uL_Fb", "plate", "C2"))
    trough = cast(handles.Container, await self._place(flex, _trough("trough"), "trough", "B2"))
    await rec.arrange("every plate well holds 100 uL", plate.set_well_volumes(100))

    await rec.step("setup(skip_home=True)", flex.setup(skip_home=True))
    head = flex.head96
    assert isinstance(head, FlexHead96)
    trash_area = await get_trash_area(flex.deck)
    await rec.step("head96.pick_up_tips(tips)", head.pick_up_tips(tips))
    await rec.step("head96.aspirate(plate, 20)", head.aspirate(plate, 20))
    await rec.step("head96.dispense(trough, 10)", head.dispense(trough, 10))
    await rec.step("head96.touch_tip(plate)", head.touch_tip(plate))
    await rec.step("head96.drop_tips(tips) with 10 uL in each tip", head.drop_tips(tips))
    await rec.step("head96.pick_up_tips(tips)", head.pick_up_tips(tips))
    await rec.step("head96.discard_tips(trash)", head.discard_tips(trash_area))
    await rec.step("stop()", flex.stop())
    await self._check(rec, "ninety_six_channel")

  async def test_gripper_and_deck_sync(self) -> None:
    """Gripper moves of a plate and a non-pipettable stub, refusals, the robot's tip record
    synced from the rack, labware taken off the deck and put back, and a reload."""
    flex, _, rec = await self._flex([("left", "p50_single_flex")], gripper=True)
    tips = cast(handles.TipRack, await self._place(flex, "flex_96_tiprack_50ul", "tips", "C1"))
    plate = cast(handles.Plate, await self._place(flex, "cor_96_wellplate_360uL_Fb", "plate", "C2"))
    other = await self._place(flex, "cor_96_wellplate_360uL_Fb", "other_plate", "B2")
    riser = await self._place(
      flex,
      build.resource("riser", Coordinate(127.76, 85.48, 20), type_name="Resource"),
      "riser",
      "D2",
    )
    await rec.arrange("plate A1 holds 40 uL", plate.get_well("A1").set_volume(40))

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
    taken = set([*_column(1), "A2"])
    await rec.arrange(
      "an operator takes the tips in column 1 and A2",
      tips.set_tip_state([identifier not in taken for identifier in tips.identifiers]),
    )
    await rec.step("sync_tips_to_robot(tips)", flex.sync_tips_to_robot(tips))
    await rec.step("labware_moved_off_deck(plate)", flex.labware_moved_off_deck(plate))
    await rec.step(
      "labware_moved_off_deck(other_plate) never loaded", flex.labware_moved_off_deck(other)
    )
    await rec.arrange("plate is put back in C2", assign_child_at_slot(flex.deck, plate, "C2"))
    await rec.step("left.pick_up_tips(tips B2)", left.pick_up_tips(tips.get_tip_spot("B2")))
    await rec.step(
      "left.touch_tip(plate A1) loads the plate afresh", left.touch_tip(plate.get_well("A1"))
    )
    await rec.step("left.aspirate(plate A1, 10)", left.aspirate(plate.get_well("A1"), 10))
    await rec.step("left.dispense(plate A2, 10)", left.dispense(plate.get_well("A2"), 10))
    await rec.step("left.drop_tips(tips B2)", left.drop_tips(tips.get_tip_spot("B2")))
    await rec.step("gripper.move_labware(tips, D1)", gripper.move_labware(tips, "D1"))
    await rec.step("stop()", flex.stop())
    await self._check(rec, "gripper_and_deck_sync")


def _column(column: int) -> List[str]:
  """The well names of a 96-format column, numbered from 1."""
  return [f"{row}{column}" for row in "ABCDEFGH"]


async def _fill(plate: handles.Plate, wells: List[str], volume: float) -> None:
  """Set the liquid in `wells` of `plate` by hand."""
  for name in wells:
    await plate.get_well(name).set_volume(volume)


if __name__ == "__main__":
  unittest.main()
