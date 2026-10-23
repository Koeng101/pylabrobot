"""Partial OT-2 pickup geometry and tracking with mocked run operations."""

import unittest
from typing import List, Sequence, cast
from unittest.mock import ANY, AsyncMock, create_autospec

from pylabrobot.io.http import HTTP
from pylabrobot.opentrons import OT2, OpentronsError, OT2_8ChannelPipette
from pylabrobot.opentrons.decks import OT2_SLOT_LOCATIONS, create_ot2_deck, get_slot_holder
from pylabrobot.opentrons.heads import PipetteShafts
from pylabrobot.opentrons.labware import LabwareRegistry
from pylabrobot.opentrons.run import OpentronsRun
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb


async def _has_tips(spots: Sequence[handles.Resource]) -> List[bool]:
  return [await cast(handles.TipSpot, spot).has_tip() for spot in spots]


async def _tip_names(spots: Sequence[handles.Resource]) -> List[str]:
  names = []
  for spot in spots:
    tip = await cast(handles.TipSpot, spot).get_tip()
    assert tip is not None
    names.append(tip.name)
  return names


async def _take(spots: Sequence[handles.Resource]) -> None:
  """Take the tips from spots by hand."""
  store = spots[0].store
  await store.commands.update_resources(
    spb.UpdateResourcesRequest(
      updates=[
        spb.ResourceUpdate(
          tip_presence=pb.SetTipPresence(spots=[spot.ref for spot in spots], present=False)
        )
      ]
    )
  )


class OT2PartialPickupTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    """Create two multi pipettes, a rack, and liquid sources without hardware."""
    self.protocol_run = create_autospec(OpentronsRun, instance=True, spec_set=True)
    self.protocol_run.active = True
    self.protocol_run.get_position.return_value = Coordinate(30.25, 40.5, 20)
    self.store = ResourceStore.in_memory()
    self.deck = await create_ot2_deck(self.store)
    self.robot = OT2("ot2.local", deck=self.deck, io=AsyncMock(spec_set=HTTP))
    self.robot._run = self.protocol_run
    self.robot._labware = LabwareRegistry(self.protocol_run)
    self.pipette = OT2_8ChannelPipette(
      self.robot,
      "left",
      "p20_multi_gen2",
      "left-id",
      await PipetteShafts.create(self.store, "left_pipette", 8),
    )
    self.robot.left_pipette = self.pipette
    self.robot.right_pipette = OT2_8ChannelPipette(
      self.robot,
      "right",
      "p20_multi_gen2",
      "right-id",
      await PipetteShafts.create(self.store, "right_pipette", 8),
    )
    self.rack = cast(
      handles.TipRack,
      await self.store.create(
        "opentrons_96_filtertiprack_20ul", name="tips", parent=await get_slot_holder(self.deck, 1)
      ),
    )
    self.column = self.rack["A1:H1"]
    self.plate = cast(
      handles.Plate,
      await self.store.create(
        "celltreat_96_wellplate_350uL_Fb", name="plate", parent=await get_slot_holder(self.deck, 2)
      ),
    )
    self.sources = cast(List[handles.Container], self.plate["A1:H1"])
    self.destinations = cast(List[handles.Container], self.plate["A2:H2"])
    for well in self.sources:
      await well.set_volume(15)

  async def _volumes(self, wells: Sequence[handles.Container]) -> List[float]:
    return [await well.get_volume() for well in wells]

  async def _tip_volumes(self, pipette: OT2_8ChannelPipette) -> List[float]:
    return [await tip.get_volume() for tip in await pipette.tips()]

  async def test_partial_pickup_liquid_transfer_and_return(self) -> None:
    """E-H tips map to nozzles 0-3 and support a complete protocol on either mount."""
    for pipette in self.robot.pipettes:
      assert isinstance(pipette, OT2_8ChannelPipette)
      with self.subTest(mount=pipette.mount):
        selected = self.rack["E1:H1"]
        original_tips = await _tip_names(selected)
        tip = await cast(handles.TipSpot, selected[0]).get_tip()
        assert tip is not None
        tip_length = (await tip.attributes()).size.z
        self.protocol_run.reset_mock()
        await pipette.pick_up_tips(selected)  # type: ignore[arg-type]
        self.assertEqual([t.name for t in await pipette.tips()], original_tips)
        self.assertTrue(all(await _has_tips(self.column[:4])))
        await pipette.mix(self.sources[:4], volume=5, repetitions=2)
        await pipette.aspirate(self.sources[:4], volume=5)
        await pipette.dispense(self.destinations[:4], volume=5)
        await pipette.return_tips()
        self.assertEqual(await pipette.tips(), ())
        self.assertEqual(await _tip_names(selected), original_tips)
        self.protocol_run.pick_up_tip.assert_awaited_once_with(
          pipette.pipette_id, ANY, "E1", Coordinate(z=tip_length)
        )
        self.protocol_run.drop_tip.assert_awaited_once_with(
          pipette.pipette_id, ANY, "E1", Coordinate(z=10)
        )
    self.assertEqual(await self._volumes(self.sources), [5] * 4 + [15] * 4)
    self.assertEqual(await self._volumes(self.destinations), [10] * 4 + [0] * 4)

  async def test_pickup_grabbing_undeclared_tips_below_is_rejected(self) -> None:
    """A-F from a full column would also grab G/H, and must fail before commands or staging."""
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "undeclared tips"):
      await self.pipette.pick_up_tips(self.column[:6])  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertTrue(all(await _has_tips(self.column)))
    self.assertEqual(await self.pipette.tips(), ())
    await self.pipette.pick_up_tips(self.column)  # type: ignore[arg-type]
    self.assertEqual(len(await self.pipette.tips()), 8)
    self.assertFalse(any(await _has_tips(self.column)))
    await self.pipette.return_tips()
    self.assertTrue(all(await _has_tips(self.column)))

  async def test_undeclared_tip_after_an_empty_spot_is_rejected(self) -> None:
    """An empty G spot does not hide the undeclared H tip under nozzle 7."""
    await _take([self.column[6]])
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "undeclared tips at tips_H1"):
      await self.pipette.pick_up_tips(self.column[:6])  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await self.pipette.tips(), ())
    self.assertEqual(await _has_tips(self.column), [True] * 6 + [False, True])

  async def test_empty_spots_below_selection_allow_partial_pickup(self) -> None:
    """Unused nozzles over empty spots do not count as extra tips."""
    await _take(self.column[6:])
    await self.pipette.pick_up_tips(self.column[:6])  # type: ignore[arg-type]
    self.assertEqual(len(await self.pipette.tips()), 6)
    await self.pipette.return_tips()
    self.assertEqual(await _has_tips(self.column), [True] * 6 + [False] * 2)

  async def test_single_tip_uses_nozzle_zero(self) -> None:
    """A single selected tip stays on nozzle 0 and transfers only one well's volume."""
    await _take(self.column[1:])
    await self.pipette.pick_up_tips(self.column[:1])  # type: ignore[arg-type]
    self.assertEqual(len(await self.pipette.tips()), 1)
    await self.pipette.aspirate(self.sources[:1], volume=5)
    await self.pipette.dispense(self.destinations[:1], volume=5)
    await self.pipette.return_tips()
    self.assertEqual(await self._volumes(self.sources), [10] + [15] * 7)
    self.assertEqual(await self._volumes(self.destinations), [5] + [0] * 7)

  async def test_invalid_partial_geometry_sends_nothing(self) -> None:
    """Reject gaps, duplicates, reversed rows, mixed columns/racks, and non-pitch spacing."""
    other = cast(
      handles.TipRack,
      await self.store.create(
        "opentrons_96_filtertiprack_20ul",
        name="other",
        parent=await get_slot_holder(self.deck, 3),
      ),
    )
    await _take(self.column[2:])
    self.protocol_run.reset_mock()
    for targets in (
      [],
      [self.column[0]] * 9,
      [self.column[0], self.column[2]],
      [self.column[0], self.column[0]],
      self.column[3::-1],
      [self.column[0], self.rack.get_item("B2")],
      [self.column[0], other.get_item("B1")],
    ):
      with self.subTest(targets=targets), self.assertRaises(ValueError):
        await self.pipette.pick_up_tips(targets)  # type: ignore[arg-type]
    location = await self.column[1].get_location()
    assert location is not None
    await self.rack.assign_child_resource(
      self.column[1], location=location + Coordinate(y=0.1), index=1
    )
    with self.assertRaises(ValueError):
      await self.pipette.pick_up_tips(self.column[:2])  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await _has_tips(self.column), [True] * 2 + [False] * 6)

  async def test_pickup_failure_rolls_back_declared_tips(self) -> None:
    """A rejected command must not transfer ownership of the requested tips."""
    self.protocol_run.pick_up_tip.side_effect = OpentronsError("pick_up_tip failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.assertTrue(all(await _has_tips(self.column)))
    self.assertEqual(await self.pipette.tips(), ())
    self.protocol_run.pick_up_tip.side_effect = None
    await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.assertEqual(len(await self.pipette.tips()), 4)

  async def test_partial_liquid_failure_rolls_back_all_mounted_tips(self) -> None:
    """An unsuccessful stroke preserves source and tip volumes for a partial layout."""
    await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.protocol_run.aspirate_in_place.side_effect = OpentronsError("aspirate_in_place failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.aspirate(self.sources[:4], volume=5)
    self.assertEqual(await self._volumes(self.sources), [15] * 8)
    self.assertEqual(await self._tip_volumes(self.pipette), [0] * 4)

  async def test_partial_liquid_targets_match_all_mounted_nozzles(self) -> None:
    """Targets must address exactly the mounted contiguous nozzles for every liquid stroke."""
    await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.protocol_run.reset_mock()
    for targets in (self.sources[:3], self.sources[:5], self.sources[:3] + [self.sources[4]]):
      with self.subTest(targets=targets):
        with self.assertRaises(ValueError):
          await self.pipette.aspirate(targets, volume=5)
        with self.assertRaises(ValueError):
          await self.pipette.dispense(targets, volume=5)
        with self.assertRaises(ValueError):
          await self.pipette.mix(targets, volume=5, repetitions=1)
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await self._volumes(self.sources), [15] * 8)
    self.assertEqual(await self._tip_volumes(self.pipette), [0] * 4)

  async def test_drop_targets_and_failed_return_preserve_mounted_layout(self) -> None:
    """Drop must address every mounted tip, and a failed return keeps their origins."""
    await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.protocol_run.reset_mock()
    with self.assertRaises(ValueError):
      await self.pipette.drop_tips(self.rack["E1:G1"])  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.protocol_run.drop_tip.side_effect = OpentronsError("drop_tip failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.return_tips()
    self.assertEqual(len(await self.pipette.tips()), 4)
    self.assertFalse(any(await _has_tips(self.column[4:])))
    self.protocol_run.drop_tip.side_effect = None
    await self.pipette.return_tips()
    self.assertTrue(all(await _has_tips(self.column)))

  async def test_collision_checks_include_bare_nozzles_beyond_partial_selection(self) -> None:
    """Unused front nozzles can collide with an obstacle beyond the rack's front edge."""
    primary = await self.column[4].get_location_wrt(self.deck, "c", "c", "b")
    obstacle = await self.store.create(
      build.resource("obstacle", Coordinate(10, 10, 100)), name="obstacle"
    )
    holder = await get_slot_holder(self.deck, 3)
    await holder.assign_child_resource(
      obstacle, location=Coordinate(primary.x - 5, primary.y - 63, 0) - OT2_SLOT_LOCATIONS[2]
    )
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "obstacle"):
      await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertTrue(all(await _has_tips(self.column)))

  async def test_retraction_failure_keeps_completed_partial_pickup(self) -> None:
    """A failed retraction retains the nozzle layout from a successful pickup."""
    self.protocol_run.get_position.side_effect = OpentronsError("get_position failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    self.assertEqual(len(await self.pipette.tips()), 4)
    self.assertFalse(any(await _has_tips(self.column[4:])))

  async def test_disabled_tracking_still_rejects_undeclared_tips(self) -> None:
    """Tracking switches do not permit undeclared tips or prevent declared partial pickups."""
    await self.rack.set_tip_tracking(False)
    await self.plate.set_volume_tracking(False)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "undeclared tips"):
      await self.pipette.pick_up_tips(self.column[:6])  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await self.pipette.tips(), ())
    await self.pipette.pick_up_tips(self.rack["E1:H1"])  # type: ignore[arg-type]
    # The fresh tips an untracked spot gives are not tracked either.
    await self.pipette.shafts.root.set_volume_tracking(False)
    self.assertEqual(len(await self.pipette.tips()), 4)
    self.assertTrue(all(await _has_tips(self.column)))
    await self.pipette.aspirate(self.sources[:4], volume=5)
    await self.pipette.discard_tips()
    self.assertEqual(await self.pipette.tips(), ())


if __name__ == "__main__":
  unittest.main()
