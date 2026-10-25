import asyncio
import unittest
from typing import List, Optional, Sequence, cast
from unittest.mock import ANY, AsyncMock, call, create_autospec

from pylabrobot.io.http import HTTP
from pylabrobot.opentrons import OT2, OpentronsError, OT2_8ChannelPipette, OT2SingleChannelPipette
from pylabrobot.opentrons.decks import create_ot2_deck, get_slot_holder
from pylabrobot.opentrons.heads import PipetteShafts
from pylabrobot.opentrons.labware import LabwareRegistry
from pylabrobot.opentrons.run import OpentronsRun
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import (
  HasTipError,
  NoTipError,
  TooLittleLiquidError,
  TooLittleVolumeError,
)
from pylabrobot.resources.store import build, handles, library
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

_TIPS = "opentrons_96_filtertiprack_20ul"
_PLATE = "celltreat_96_wellplate_350uL_Fb"


async def _set_tips(spots: Sequence[handles.Resource], present: bool) -> None:
  """Put fresh tips in spots, or take theirs, by hand."""
  await spots[0].store.commands.update_resources(
    spb.UpdateResourcesRequest(
      updates=[
        spb.ResourceUpdate(
          tip_presence=pb.SetTipPresence(spots=[spot.ref for spot in spots], present=present)
        )
      ]
    )
  )


async def _has_tip(spot: handles.Resource) -> bool:
  return await cast(handles.TipSpot, spot).has_tip()


async def _has_tips(spots: Sequence[handles.Resource]) -> List[bool]:
  return [await _has_tip(spot) for spot in spots]


async def _tip_name(spot: handles.Resource) -> Optional[str]:
  tip = await cast(handles.TipSpot, spot).get_tip()
  return tip.name if tip is not None else None


async def _volumes(containers: Sequence[handles.Resource]) -> List[float]:
  return [await cast(handles.Container, c).get_volume() for c in containers]


class OT2SingleChannelTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    """Use real resources in a store with mocked run operations."""
    self.protocol_run = create_autospec(OpentronsRun, instance=True, spec_set=True)
    self.protocol_run.active = True
    self.protocol_run.get_position.return_value = Coordinate(30.25, 40.5, 20)
    self.store = ResourceStore.in_memory()
    self.deck = await create_ot2_deck(self.store)
    self.robot = OT2("ot2.local", deck=self.deck, io=AsyncMock(spec_set=HTTP))
    self.robot._run = self.protocol_run
    self.robot._labware = LabwareRegistry(self.protocol_run)
    self.pipette = OT2SingleChannelPipette(
      self.robot,
      "left",
      "p20_single_gen2",
      "pipette-id",
      await PipetteShafts.create(self.deck, "left_pipette", 1),
    )
    self.robot.left_pipette = self.pipette
    self.tips = cast(
      handles.TipRack,
      await self.store.create(_TIPS, name="tips", parent=await get_slot_holder(self.deck, 1)),
    )
    self.plate = cast(
      handles.Plate,
      await self.store.create(_PLATE, name="plate", parent=await get_slot_holder(self.deck, 2)),
    )

  async def _tip(self) -> handles.Tip:
    tip = await self.pipette.get_tip()
    assert tip is not None
    return tip

  async def _put_lid_on(self, resource: handles.Resource) -> None:
    lid = build.resource("lid", Coordinate(127.76, 85.48, 5), kind=pb.RESOURCE_KIND_LID)
    await self.store.create(
      lid, name=f"{resource.name}_lid", parent=resource, location=Coordinate.zero()
    )

  async def test_picking_up_from_a_lidded_rack_is_a_value_error_before_motion(self) -> None:
    """The store refuses a pick-up under a lid; it is raised as a ValueError."""
    await self._put_lid_on(self.tips)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "has its lid on"):
      await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertFalse(await self.pipette.has_tip())

  async def test_pipetting_into_a_lidded_plate_is_a_value_error_before_motion(self) -> None:
    """The store refuses a transfer under a lid; it is raised as a ValueError."""
    await self.plate.set_volume_tracking(False)
    await self.tips.set_volume_tracking(False)
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    await self._put_lid_on(self.plate)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "has its lid on"):
      await self.pipette.aspirate(self.plate.get_well("A1"), volume=1)
    with self.assertRaisesRegex(ValueError, "has its lid on"):
      await self.pipette.dispense(self.plate.get_well("A1"), volume=1)
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_pipetting_into_a_container_without_a_floor_thickness_is_a_value_error(
    self,
  ) -> None:
    """A cavity bottom the store cannot place is raised as a ValueError, before motion."""
    definition = library.get_model(_PLATE).definition
    definition.attributes.itemized.grid.item.attributes.container.ClearField("material_z_thickness")
    await self.plate.unassign()
    plate = cast(
      handles.Plate,
      await self.store.create(
        definition, name="floorless", parent=await get_slot_holder(self.deck, 2)
      ),
    )
    await plate.set_volume_tracking(False)
    await self.tips.set_volume_tracking(False)
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "does not say how thick its bottom is"):
      await self.pipette.aspirate(plate.get_well("A1"), volume=1)
    with self.assertRaisesRegex(ValueError, "does not say how thick its bottom is"):
      await self.pipette.dispense(plate.get_well("A1"), volume=1)
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_failed_aspiration_rolls_back_volume_trackers(self) -> None:
    pipette = self.pipette
    source = self.plate.get_well("A1")
    await source.set_volume(15)
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    self.protocol_run.aspirate_in_place.side_effect = OpentronsError("aspiration failed")

    with self.assertRaisesRegex(OpentronsError, "aspiration failed"):
      await pipette.aspirate(source, volume=10)

    self.assertAlmostEqual(await source.get_volume(), 15)
    self.assertAlmostEqual(await (await self._tip()).get_volume(), 0)

  async def test_rejected_aspiration_preserves_both_volume_trackers(self) -> None:
    pipette = self.pipette
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    await tip.set_volume(15)
    source = self.plate.get_well("A1")
    await source.set_volume(30)
    self.protocol_run.reset_mock()

    with self.assertRaises(TooLittleVolumeError):
      await pipette.aspirate(source, volume=10)

    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await source.get_volume(), 30)
    self.assertEqual(await source.get_volume(pb.VIEW_COMMITTED), 30)
    self.assertEqual(await tip.get_volume(), 15)
    self.assertEqual(await tip.get_volume(pb.VIEW_COMMITTED), 15)

  async def test_rejected_dispense_preserves_both_volume_trackers(self) -> None:
    pipette = self.pipette
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    await tip.set_volume(10)
    destination = self.plate.get_well("A1")
    max_volume = await destination.get_max_volume()
    assert max_volume is not None
    await destination.set_volume(max_volume - 5)
    initial_volume = await destination.get_volume()
    self.protocol_run.reset_mock()

    with self.assertRaises(TooLittleVolumeError):
      await pipette.dispense(destination, volume=10)

    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await destination.get_volume(), initial_volume)
    self.assertEqual(await destination.get_volume(pb.VIEW_COMMITTED), initial_volume)
    self.assertEqual(await tip.get_volume(), 10)
    self.assertEqual(await tip.get_volume(pb.VIEW_COMMITTED), 10)

  async def test_moved_or_unassigned_loaded_rack_is_rejected_before_a_command(self) -> None:
    pipette = self.pipette
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    await pipette.return_tip()
    await self.tips.unassign()
    self.protocol_run.reset_mock()

    with self.assertRaisesRegex(ValueError, "assigned directly"):
      await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    await (await get_slot_holder(self.deck, 5)).assign_child_resource(self.tips)
    with self.assertRaisesRegex(ValueError, "loaded in slot 1"):
      await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))

    self.protocol_run.pick_up_tip.assert_not_awaited()
    self.protocol_run.drop_tip.assert_not_awaited()
    self.protocol_run.load_labware.assert_not_awaited()
    self.protocol_run.get_position.assert_not_awaited()
    self.assertTrue(await _has_tip(self.tips.get_tip_spot("A1")))
    self.assertFalse(await pipette.has_tip())

  async def test_drop_into_moved_rack_preserves_tip_state(self) -> None:
    pipette = self.pipette
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    await self.tips.unassign()
    await (await get_slot_holder(self.deck, 5)).assign_child_resource(self.tips)
    self.protocol_run.reset_mock()

    with self.assertRaisesRegex(ValueError, "loaded in slot 1"):
      await pipette.return_tip()

    self.protocol_run.pick_up_tip.assert_not_awaited()
    self.protocol_run.drop_tip.assert_not_awaited()
    self.protocol_run.load_labware.assert_not_awaited()
    self.protocol_run.get_position.assert_not_awaited()
    self.assertFalse(await _has_tip(self.tips.get_tip_spot("A1")))
    self.assertTrue(await pipette.has_tip())

  async def test_mix_rejects_insufficient_liquid_or_tip_capacity_before_moving(self) -> None:
    pipette = self.pipette
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    source = self.plate.get_well("A1")
    self.protocol_run.reset_mock()
    for source_volume, tip_volume, error in (
      (0, 0, TooLittleLiquidError),
      (30, 15, TooLittleVolumeError),
    ):
      with self.subTest(source_volume=source_volume, tip_volume=tip_volume):
        await source.set_volume(source_volume)
        await tip.set_volume(tip_volume)
        with self.assertRaises(error):
          await pipette.mix(source, volume=10, repetitions=3)
        self.assertEqual(self.protocol_run.mock_calls, [])
        self.assertEqual(await source.get_volume(), source_volume)
        self.assertEqual(await tip.get_volume(), tip_volume)

  async def test_mix_tracks_each_transfer_when_dispense_fails(self) -> None:
    pipette = self.pipette
    await pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    source = self.plate.get_well("A1")
    await source.set_volume(15)
    self.protocol_run.dispense_in_place.side_effect = [None, OpentronsError("dispense failed")]

    with self.assertRaisesRegex(OpentronsError, "dispense failed"):
      await pipette.mix(source, volume=10, repetitions=3)

    self.assertEqual(await source.get_volume(), 5)
    self.assertEqual(await source.get_volume(pb.VIEW_COMMITTED), 5)
    tip = await self._tip()
    self.assertEqual(await tip.get_volume(), 10)
    self.assertEqual(await tip.get_volume(pb.VIEW_COMMITTED), 10)

  async def test_unreachable_move_is_rejected_before_a_run_command(self) -> None:
    pipette = self.pipette
    self.protocol_run.reset_mock()

    with self.assertRaisesRegex(ValueError, "reachable"):
      await pipette.move_to(Coordinate(500, 0, 10))

    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_negative_z_move_is_rejected_before_a_run_command(self) -> None:
    pipette = self.pipette
    self.protocol_run.reset_mock()

    with self.assertRaisesRegex(ValueError, "non-negative"):
      await pipette.move_to(Coordinate(10, 10, -1))

    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_pickup_uses_tip_height_and_retracts_after_committing_ownership(self) -> None:
    origin = self.tips.get_tip_spot("A1")
    tip = await origin.get_tip()
    assert tip is not None
    tip_length = (await tip.attributes()).size.z

    async def read_position(pipette_id: str) -> Coordinate:
      """Check ownership at the start of retraction."""
      self.assertEqual((await self._tip()).name, tip.name)
      self.assertFalse(await origin.has_tip())
      return Coordinate(30.25, 40.5, 20)

    self.protocol_run.get_position.side_effect = read_position

    await self.pipette.pick_up_tip(origin)

    self.protocol_run.pick_up_tip.assert_awaited_once_with(
      "pipette-id", ANY, "A1", Coordinate(z=tip_length)
    )
    self.protocol_run.get_position.assert_awaited_once_with("pipette-id")
    self.protocol_run.move_to.assert_awaited_once_with(
      "pipette-id",
      Coordinate(30.25, 40.5, 120),
      speed=None,
      minimum_z_height=None,
      force_direct=True,
    )

  async def test_return_restores_the_same_tip_and_reuses_loaded_labware(self) -> None:
    origin = self.tips.get_tip_spot("A1")
    tip = await _tip_name(origin)
    await self.pipette.pick_up_tip(origin)
    self.protocol_run.drop_tip.reset_mock()

    await self.pipette.return_tip()

    self.assertEqual(await _tip_name(origin), tip)
    self.assertFalse(await self.pipette.has_tip())
    self.protocol_run.drop_tip.assert_awaited_once_with("pipette-id", ANY, "A1", Coordinate(z=10))
    self.protocol_run.load_labware.assert_awaited_once()

  async def test_pickup_retraction_failure_keeps_completed_pickup(self) -> None:
    origin = self.tips.get_tip_spot("A1")
    for retraction in (self.protocol_run.get_position, self.protocol_run.move_to):
      with self.subTest(retraction=retraction):
        tip = await _tip_name(origin)
        failure = OpentronsError("retraction failed")
        retraction.side_effect = failure

        with self.assertRaises(OpentronsError) as raised:
          await self.pipette.pick_up_tip(origin)

        self.assertIs(raised.exception, failure)
        self.assertEqual((await self._tip()).name, tip)
        self.assertFalse(await origin.has_tip())
        retraction.side_effect = None
        await self.pipette.return_tip()
        self.assertEqual(await _tip_name(origin), tip)

  async def test_move_retracts_from_reported_position_without_lowering(self) -> None:
    for z in (10, 120, 150):
      with self.subTest(z=z):
        self.protocol_run.reset_mock()
        self.protocol_run.get_position.return_value = Coordinate(101, 202, z)

        await self.pipette.move_to(Coordinate(100, 200, z))

        expected = [
          call.move_to(
            "pipette-id",
            Coordinate(100, 200, z),
            speed=None,
            minimum_z_height=None,
            force_direct=False,
          ),
          call.get_position("pipette-id"),
        ]
        if z < 120:
          expected.append(
            call.move_to(
              "pipette-id",
              Coordinate(101, 202, 120),
              speed=None,
              minimum_z_height=None,
              force_direct=True,
            )
          )
        self.assertEqual(self.protocol_run.mock_calls, expected)

  async def test_drop_retracts_from_reported_position_at_configured_height(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    await _set_tips([self.tips.get_tip_spot("A12")], False)
    self.robot.traversal_height = 140
    self.protocol_run.reset_mock()

    await self.pipette.drop_tip(self.tips.get_tip_spot("A12"))

    self.protocol_run.drop_tip.assert_awaited_once_with("pipette-id", ANY, "A12", Coordinate(z=10))
    self.protocol_run.get_position.assert_awaited_once_with("pipette-id")
    self.protocol_run.move_to.assert_awaited_once_with(
      "pipette-id",
      Coordinate(30.25, 40.5, 140),
      speed=None,
      minimum_z_height=None,
      force_direct=True,
    )
    self.assertTrue(await _has_tip(self.tips.get_tip_spot("A12")))
    self.assertFalse(await self.pipette.has_tip())

  async def test_drop_does_not_lower_a_nozzle_above_traversal_height(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    self.protocol_run.get_position.return_value = Coordinate(30.25, 40.5, 130)
    self.protocol_run.reset_mock()

    await self.pipette.return_tip()

    self.protocol_run.drop_tip.assert_awaited_once()
    self.protocol_run.get_position.assert_awaited_once()
    self.protocol_run.move_to.assert_not_awaited()
    self.assertFalse(await self.pipette.has_tip())

  async def test_failed_drop_keeps_tip_and_does_not_retract(self) -> None:
    origin = self.tips.get_tip_spot("A1")
    await self.pipette.pick_up_tip(origin)
    tip = (await self._tip()).name
    self.protocol_run.reset_mock()
    self.protocol_run.drop_tip.side_effect = OpentronsError("drop failed")

    with self.assertRaisesRegex(OpentronsError, "drop failed"):
      await self.pipette.return_tip()

    self.assertEqual((await self._tip()).name, tip)
    self.assertFalse(await origin.has_tip())
    self.protocol_run.get_position.assert_not_awaited()
    self.protocol_run.move_to.assert_not_awaited()

  async def test_discard_uses_fixed_trash_offset_and_retracts(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    self.protocol_run.reset_mock()

    await self.pipette.discard_tip()

    self.assertEqual(
      self.protocol_run.mock_calls,
      [
        call.discard_tip_in_fixed_trash("pipette-id", Coordinate(z=10)),
        call.get_position("pipette-id"),
        call.move_to(
          "pipette-id",
          Coordinate(30.25, 40.5, 120),
          speed=None,
          minimum_z_height=None,
          force_direct=True,
        ),
      ],
    )
    self.assertFalse(await self.pipette.has_tip())

  async def test_drop_retraction_failure_keeps_completed_drop(self) -> None:
    for operation, returned in ((self.pipette.return_tip, True), (self.pipette.discard_tip, False)):
      for retraction in (self.protocol_run.get_position, self.protocol_run.move_to):
        with self.subTest(operation=operation.__name__, retraction=retraction):
          spots = self.tips.items
          occupied = await _has_tips(spots)
          origin = spots[occupied.index(True)]
          await self.pipette.pick_up_tip(cast(handles.TipSpot, origin))
          retraction.side_effect = OpentronsError("retraction failed")

          with self.assertRaisesRegex(OpentronsError, "retraction failed"):
            await operation()

          self.assertIsNone(await self.pipette.get_tip())
          self.assertFalse(await self.pipette.has_tip())
          self.assertEqual(await _has_tip(origin), returned)
          with self.assertRaisesRegex(RuntimeError, "origin is unknown"):
            await self.pipette.return_tip()
          retraction.side_effect = None

  async def test_aspiration_uses_default_flow_rate_and_commits_both_trackers(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    source = self.plate.get_well("A1")
    await source.set_volume(15)

    await self.pipette.aspirate(source, volume=10)

    self.protocol_run.aspirate_in_place.assert_awaited_once_with("pipette-id", 10, 3.78)
    self.assertEqual(await source.get_volume(pb.VIEW_COMMITTED), 5)
    self.assertEqual(await (await self._tip()).get_volume(pb.VIEW_COMMITTED), 10)

  async def test_dispense_uses_default_flow_rate_and_commits_both_trackers(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    await tip.set_volume(10)
    destination = self.plate.get_well("B1")

    await self.pipette.dispense(destination, volume=10)

    self.protocol_run.dispense_in_place.assert_awaited_once_with("pipette-id", 10, 7.56)
    self.assertEqual(await destination.get_volume(pb.VIEW_COMMITTED), 10)
    self.assertEqual(await tip.get_volume(pb.VIEW_COMMITTED), 0)

  async def test_liquid_operations_retract_from_reported_position(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    well = self.plate.get_well("A1")
    for operation, initial_tip in ((self.pipette.aspirate, 0), (self.pipette.dispense, 10)):
      with self.subTest(operation=operation.__name__):
        await well.set_volume(30)
        await tip.set_volume(initial_tip)
        self.protocol_run.reset_mock()

        await operation(well, volume=10)

        self.assertEqual(
          self.protocol_run.mock_calls[-2:],
          [
            call.get_position("pipette-id"),
            call.move_to(
              "pipette-id",
              Coordinate(30.25, 40.5, 120),
              speed=None,
              minimum_z_height=None,
              force_direct=True,
            ),
          ],
        )

  async def test_transfer_retraction_failure_keeps_completed_transfer(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    well = self.plate.get_well("A1")
    for operation, initial_tip, expected_tip, expected_well in (
      (self.pipette.aspirate, 0, 10, 20),
      (self.pipette.dispense, 10, 0, 40),
    ):
      with self.subTest(operation=operation.__name__):
        await well.set_volume(30)
        await tip.set_volume(initial_tip)
        self.protocol_run.move_to.side_effect = [None, OpentronsError("retraction failed")]

        with self.assertRaisesRegex(OpentronsError, "retraction failed"):
          await operation(well, volume=10)

        self.assertEqual(await well.get_volume(pb.VIEW_COMMITTED), expected_well)
        self.assertEqual(await well.get_volume(), expected_well)
        self.assertEqual(await tip.get_volume(pb.VIEW_COMMITTED), expected_tip)
        self.assertEqual(await tip.get_volume(), expected_tip)

  async def test_mix_alternates_strokes_and_retracts_once(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    tip = await self._tip()
    source = self.plate.get_well("A1")
    await source.set_volume(15)
    await tip.set_volume(5)
    self.protocol_run.reset_mock()

    await self.pipette.mix(source, volume=10, repetitions=3)

    self.assertEqual(await source.get_volume(pb.VIEW_COMMITTED), 15)
    self.assertEqual(await tip.get_volume(pb.VIEW_COMMITTED), 5)
    self.assertEqual(
      self.protocol_run.mock_calls,
      [
        call.move_to("pipette-id", ANY, speed=None, minimum_z_height=120, force_direct=False),
      ]
      + [
        call.aspirate_in_place("pipette-id", 10, 3.78),
        call.dispense_in_place("pipette-id", 10, 7.56),
      ]
      * 3
      + [
        call.get_position("pipette-id"),
        call.move_to(
          "pipette-id",
          Coordinate(30.25, 40.5, 120),
          speed=None,
          minimum_z_height=None,
          force_direct=True,
        ),
      ],
    )

  async def test_concurrent_pickup_waits_then_rejects_a_second_tip(self) -> None:
    entered, release = asyncio.Event(), asyncio.Event()

    async def pick_up_tip(*args: object) -> None:
      """Hold the first pickup while the second operation attempts to start."""
      entered.set()
      await release.wait()

    self.protocol_run.pick_up_tip.side_effect = pick_up_tip
    first = asyncio.create_task(self.pipette.pick_up_tip(self.tips.get_tip_spot("A1")))
    self.addAsyncCleanup(asyncio.wait_for, first, timeout=10)
    self.addCleanup(release.set)
    await asyncio.wait_for(entered.wait(), timeout=10)
    second = asyncio.create_task(self.pipette.pick_up_tip(self.tips.get_tip_spot("A2")))
    try:
      await asyncio.sleep(0)
      self.assertFalse(second.done())
      self.protocol_run.pick_up_tip.assert_awaited_once()
    finally:
      release.set()
      results = await asyncio.wait_for(asyncio.gather(first, second, return_exceptions=True), 10)

    self.assertIsNone(results[0])
    self.assertIsInstance(results[1], RuntimeError)
    self.assertIn("already has a tip", str(results[1]))
    self.protocol_run.pick_up_tip.assert_awaited_once()
    self.assertFalse(await _has_tip(self.tips.get_tip_spot("A1")))
    self.assertTrue(await _has_tip(self.tips.get_tip_spot("A2")))

  async def test_concurrent_dispense_waits_for_aspiration_to_commit(self) -> None:
    await self.pipette.pick_up_tip(self.tips.get_tip_spot("A1"))
    source, destination = self.plate.get_well("A1"), self.plate.get_well("B1")
    await source.set_volume(15)
    entered, release = asyncio.Event(), asyncio.Event()

    async def aspirate(*args: object) -> None:
      """Hold aspiration before its transfer is committed."""
      entered.set()
      await release.wait()

    self.protocol_run.aspirate_in_place.side_effect = aspirate
    first = asyncio.create_task(self.pipette.aspirate(source, volume=10))
    self.addAsyncCleanup(asyncio.wait_for, first, timeout=10)
    self.addCleanup(release.set)
    await asyncio.wait_for(entered.wait(), timeout=10)
    second = asyncio.create_task(self.pipette.dispense(destination, volume=10))
    try:
      await asyncio.sleep(0)
      self.assertFalse(second.done())
      self.protocol_run.dispense_in_place.assert_not_awaited()
    finally:
      release.set()
      await asyncio.wait_for(asyncio.gather(first, second), 10)

    self.assertEqual(await source.get_volume(pb.VIEW_COMMITTED), 5)
    self.assertEqual(await destination.get_volume(pb.VIEW_COMMITTED), 10)
    self.assertEqual(await (await self._tip()).get_volume(pb.VIEW_COMMITTED), 0)

  async def test_concurrent_discard_waits_then_rejects_an_already_returned_tip(self) -> None:
    origin = self.tips.get_tip_spot("A1")
    await self.pipette.pick_up_tip(origin)
    entered, release = asyncio.Event(), asyncio.Event()

    async def drop_tip(*args: object) -> None:
      """Hold the return before releasing ownership of the tip."""
      entered.set()
      await release.wait()

    self.protocol_run.drop_tip.side_effect = drop_tip
    first = asyncio.create_task(self.pipette.return_tip())
    self.addAsyncCleanup(asyncio.wait_for, first, timeout=10)
    self.addCleanup(release.set)
    await asyncio.wait_for(entered.wait(), timeout=10)
    second = asyncio.create_task(self.pipette.discard_tip())
    try:
      await asyncio.sleep(0)
      self.assertFalse(second.done())
      self.protocol_run.discard_tip_in_fixed_trash.assert_not_awaited()
    finally:
      release.set()
      results = await asyncio.wait_for(asyncio.gather(first, second, return_exceptions=True), 10)

    self.assertIsNone(results[0])
    self.assertIsInstance(results[1], RuntimeError)
    self.assertIn("does not have a tip", str(results[1]))
    self.protocol_run.drop_tip.assert_awaited_once()
    self.protocol_run.discard_tip_in_fixed_trash.assert_not_awaited()
    self.assertTrue(await origin.has_tip())
    self.assertFalse(await self.pipette.has_tip())

  async def test_stop_waits_for_movement_and_its_retraction(self) -> None:
    entered, release = asyncio.Event(), asyncio.Event()

    async def move(*args: object, **kwargs: object) -> None:
      """Keep movement in flight while stop waits for the operation lock."""
      entered.set()
      await release.wait()

    self.protocol_run.move_to.side_effect = move
    movement = asyncio.create_task(self.pipette.move_to(Coordinate(100, 100, 100)))
    self.addAsyncCleanup(asyncio.wait_for, movement, timeout=10)
    self.addCleanup(release.set)
    await asyncio.wait_for(entered.wait(), timeout=10)
    stop = asyncio.create_task(self.robot.stop())
    try:
      await asyncio.sleep(0)
      self.assertFalse(stop.done())
      self.protocol_run.stop.assert_not_awaited()
    finally:
      release.set()
      await asyncio.wait_for(asyncio.gather(movement, stop), 10)

    self.assertEqual(
      self.protocol_run.mock_calls,
      [
        call.move_to(
          "pipette-id",
          Coordinate(100, 100, 100),
          speed=None,
          minimum_z_height=None,
          force_direct=False,
        ),
        call.get_position("pipette-id"),
        call.move_to(
          "pipette-id",
          Coordinate(30.25, 40.5, 120),
          speed=None,
          minimum_z_height=None,
          force_direct=True,
        ),
        call.stop(),
      ],
    )
    self.assertIsNone(self.robot._run)


class OT2MultiChannelTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    """Bind real pipettes and resources in a store to mocked run operations."""
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
      "left-pipette-id",
      await PipetteShafts.create(self.deck, "left_pipette", 8),
    )
    self.robot.left_pipette = self.pipette
    self.robot.right_pipette = OT2SingleChannelPipette(
      self.robot,
      "right",
      "p20_single_gen2",
      "right-pipette-id",
      await PipetteShafts.create(self.deck, "right_pipette", 1),
    )
    self.tips = cast(
      handles.TipRack,
      await self.store.create(_TIPS, name="tips", parent=await get_slot_holder(self.deck, 1)),
    )
    self.plate = cast(
      handles.Plate,
      await self.store.create(_PLATE, name="plate", parent=await get_slot_holder(self.deck, 2)),
    )
    self.column = cast(List[handles.TipSpot], self.tips["A1:H1"])
    self.sources = cast(List[handles.Container], self.plate["A1:H1"])
    self.destinations = cast(List[handles.Container], self.plate["A2:H2"])
    for well in self.sources:
      await well.set_volume(15)

  async def _tip_names(self) -> List[str]:
    return [tip.name for tip in await self.pipette.get_tips()]

  async def _tip_volumes(self, view: pb.View = pb.VIEW_PENDING) -> List[float]:
    return [await tip.get_volume(view) for tip in await self.pipette.get_tips()]

  async def test_pickup_rejects_missing_or_mixed_models_before_commands(self) -> None:
    """A tip type is its model, and every nozzle must have a defined matching model."""
    last = self.column[-1]
    for model in ("", "different_tip_model"):
      with self.subTest(model=model):
        last_tip = await last.get_tip()
        assert last_tip is not None
        attributes = await last_tip.attributes()
        await last_tip.delete()
        attributes.model = model
        attributes.ClearField("location")
        await self.store.create(
          pb.ResourceDefinition(
            attributes=attributes,
            initial_state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
          ),
          name=f"{last.name}#{model or 'none'}",
          parent=last,
        )
        self.protocol_run.reset_mock()
        with self.assertRaises(ValueError):
          await self.pipette.pick_up_tips(self.column)
        self.assertEqual(self.protocol_run.mock_calls, [])
        self.assertTrue(all(await _has_tips(self.column)))
        self.assertFalse(await self.pipette.has_tip())

  async def test_pipettes_and_their_tips_hang_from_the_deck(self) -> None:
    """The deck's tree reaches each pipette and the tips it carries."""
    self.assertEqual(await self.pipette.shafts.root.get_parent(), self.deck)
    await self.pipette.pick_up_tips(self.column)
    for tip in await self.pipette.get_tips():
      self.assertTrue(await tip.is_in_subtree_of(self.deck))

  async def test_constructors_reject_models_with_the_wrong_channel_count(self) -> None:
    """A concrete class cannot bind a model whose nozzle count contradicts its API."""
    shafts = await PipetteShafts.create(self.deck, "spare_pipette", 1)
    with self.assertRaisesRegex(ValueError, "8-channel"):
      OT2SingleChannelPipette(self.robot, "left", "p20_multi_gen2", "left-pipette-id", shafts)
    with self.assertRaisesRegex(ValueError, "1-channel"):
      OT2_8ChannelPipette(self.robot, "right", "p20_single_gen2", "right-pipette-id", shafts)

  async def test_single_mount_and_multi_mount_keep_independent_tips(self) -> None:
    """A multi on one mount does not change the other mount's single-channel API."""
    single = self.robot.right_pipette
    assert isinstance(single, OT2SingleChannelPipette)
    self.assertEqual(single.num_channels, 1)
    await asyncio.gather(
      self.pipette.pick_up_tips(self.column), single.pick_up_tip(self.tips.get_tip_spot("A3"))
    )
    await self.pipette.discard_tips()
    self.assertTrue(await single.has_tip())
    self.assertIsNotNone(await single.get_tip())
    await single.return_tip()
    self.assertTrue(await _has_tip(self.tips.get_tip_spot("A3")))
    self.assertFalse(any(await _has_tips(self.column)))
    self.assertEqual(
      self.protocol_run.pick_up_tip.await_args_list,
      [
        call("left-pipette-id", ANY, "A1", ANY),
        call("right-pipette-id", ANY, "A3", ANY),
      ],
    )

  async def test_incomplete_or_misaligned_pickups_send_nothing(self) -> None:
    """Reject undeclared extra tips, repeated, mixed-column, and reversed targets before I/O."""
    self.protocol_run.reset_mock()
    for spots in (
      [],
      self.column[:7],
      [self.column[0]] * 8,
      list(reversed(self.column)),
      self.column[:7] + [self.tips.get_tip_spot("H2")],
    ):
      with self.subTest(spots=spots), self.assertRaises(ValueError):
        await self.pipette.pick_up_tips(spots)
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertTrue(all(await _has_tips(self.column)))

  async def test_missing_last_tip_and_failed_pickup_preserve_the_rack(self) -> None:
    """A missing eighth tip or failed command must not consume the first seven tips."""
    await _set_tips(self.column[-1:], False)
    self.protocol_run.reset_mock()
    with self.assertRaises(NoTipError):
      await self.pipette.pick_up_tips(self.column)
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertTrue(all(await _has_tips(self.column[:-1])))
    await _set_tips(self.column[-1:], True)
    self.protocol_run.pick_up_tip.side_effect = OpentronsError("pick_up_tip failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.pick_up_tips(self.column)
    self.assertTrue(all(await _has_tips(self.column)))
    self.assertFalse(await self.pipette.has_tip())

  async def test_drop_preflight_and_command_failure_roll_back_every_spot(self) -> None:
    """A late occupied destination or command failure preserves all mounted tips."""
    await self.pipette.pick_up_tips(self.column)
    mounted = await self._tip_names()
    destinations = cast(List[handles.TipSpot], self.tips["A2:H2"])
    await _set_tips(destinations[:-1], False)
    self.protocol_run.reset_mock()
    with self.assertRaises(HasTipError):
      await self.pipette.drop_tips(destinations)
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertFalse(any(await _has_tips(destinations[:-1])))
    self.protocol_run.drop_tip.side_effect = OpentronsError("drop_tip failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.return_tips()
    self.assertFalse(any(await _has_tips(self.column)))
    self.assertEqual(await self._tip_names(), mounted)
    self.protocol_run.drop_tip.side_effect = None
    await _set_tips(destinations[-1:], False)
    await self.pipette.drop_tips(destinations)
    self.assertEqual([await _tip_name(spot) for spot in destinations], mounted)

  async def test_last_well_or_tip_capacity_failure_rolls_back_the_whole_transfer(self) -> None:
    """Every nozzle is validated before motion, with earlier staged updates undone."""
    await self.pipette.pick_up_tips(self.column)
    await self.sources[-1].set_volume(0)
    self.protocol_run.reset_mock()
    with self.assertRaises(TooLittleLiquidError):
      await self.pipette.aspirate(self.sources, volume=10)
    self.assertEqual(await _volumes(self.sources), [15] * 7 + [0])
    self.assertEqual(await self._tip_volumes(), [0] * 8)
    await self.sources[-1].set_volume(15)
    await (await self.pipette.get_tips())[-1].set_volume(20)
    with self.assertRaises(TooLittleVolumeError):
      await self.pipette.aspirate(self.sources, volume=10)
    self.assertEqual(await _volumes(self.sources), [15] * 8)
    self.assertEqual(await self._tip_volumes(), [0] * 7 + [20])
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_liquid_command_failures_preserve_all_volumes(self) -> None:
    """A rejected aspiration or dispense rolls back the entire column."""
    await self.pipette.pick_up_tips(self.column)
    for operation, kind, tip_volume in (
      (self.pipette.aspirate, self.protocol_run.aspirate_in_place, 0),
      (self.pipette.dispense, self.protocol_run.dispense_in_place, 10),
    ):
      with self.subTest(kind=kind):
        for tip in await self.pipette.get_tips():
          await tip.set_volume(tip_volume)
        kind.side_effect = OpentronsError("liquid operation failed")
        with self.assertRaises(OpentronsError):
          await operation(self.sources, volume=10)
        self.assertEqual(await _volumes(self.sources), [15] * 8)
        self.assertEqual(await self._tip_volumes(), [tip_volume] * 8)

  async def test_liquid_targets_must_match_the_rigid_head(self) -> None:
    """A partial column or row cannot silently command an eight-nozzle stroke."""
    await self.pipette.pick_up_tips(self.column)
    self.protocol_run.reset_mock()
    for targets in (self.sources[:7], self.plate["A1:A8"]):
      with self.subTest(targets=targets), self.assertRaises(ValueError):
        await self.pipette.aspirate(targets, volume=10)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_mix_commits_each_completed_stroke(self) -> None:
    """A later failed mix stroke retains the liquid moved by earlier completed strokes."""
    await self.pipette.pick_up_tips(self.column)
    await self.pipette.mix(self.sources, volume=5, repetitions=2)
    self.assertEqual(await _volumes(self.sources), [15] * 8)
    self.protocol_run.dispense_in_place.side_effect = OpentronsError("dispense_in_place failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.mix(self.sources, volume=5, repetitions=1)
    self.assertEqual(await _volumes(self.sources), [10] * 8)
    self.assertEqual(await self._tip_volumes(pb.VIEW_COMMITTED), [5] * 8)

  async def test_retraction_failure_keeps_completed_tip_and_liquid_state(self) -> None:
    """A retraction failure must not undo the successful operation preceding it."""
    self.protocol_run.get_position.side_effect = OpentronsError("get_position failed")
    with self.assertRaises(OpentronsError):
      await self.pipette.pick_up_tips(self.column)
    self.assertEqual(len(await self.pipette.get_tips()), 8)
    self.assertFalse(any(await _has_tips(self.column)))
    with self.assertRaises(OpentronsError):
      await self.pipette.aspirate(self.sources, volume=10)
    self.assertEqual(await _volumes(self.sources), [5] * 8)
    self.assertEqual(await self._tip_volumes(pb.VIEW_COMMITTED), [10] * 8)
    with self.assertRaises(OpentronsError):
      await self.pipette.return_tips(allow_nonzero_volume=True)
    self.assertFalse(await self.pipette.has_tip())
    self.assertTrue(all(await _has_tips(self.column)))

  async def test_discard_checks_every_tip_and_retains_tips_on_failure(self) -> None:
    """Liquid in the last tip blocks disposal; a failed drop keeps tip ownership."""
    await self.pipette.pick_up_tips(self.column)
    await (await self.pipette.get_tips())[-1].set_volume(1)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "contains liquid"):
      await self.pipette.discard_tips()
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.protocol_run.discard_tip_in_fixed_trash.side_effect = OpentronsError(
      "discard_tip_in_fixed_trash failed"
    )
    with self.assertRaises(OpentronsError):
      await self.pipette.discard_tips(allow_nonzero_volume=True)
    self.assertEqual(len(await self.pipette.get_tips()), 8)
    self.protocol_run.discard_tip_in_fixed_trash.side_effect = None
    await self.pipette.discard_tips(allow_nonzero_volume=True)
    self.assertFalse(await self.pipette.has_tip())

  async def test_disabled_tracking_still_owns_and_operates_all_tips(self) -> None:
    """Tracking switched off does not change the physical command grouping."""
    await self.tips.set_tip_tracking(False)
    await self.plate.set_volume_tracking(False)
    await self.pipette.pick_up_tips(self.column)
    await self.pipette.aspirate(self.sources, volume=10)
    await self.pipette.dispense(self.destinations, volume=10)
    self.assertEqual(len(await self.pipette.get_tips()), 8)
    self.assertTrue(all(await _has_tips(self.column)))
    self.assertEqual(await _volumes(self.sources), [15] * 8)
    self.assertEqual(await _volumes(self.destinations), [0] * 8)
    await self.pipette.discard_tips()

  async def test_column_pickup_uses_one_stroke_and_preserves_tip_identity(self) -> None:
    original_tips = [await _tip_name(spot) for spot in self.column]
    tip = await self.column[0].get_tip()
    assert tip is not None
    tip_length = (await tip.attributes()).size.z

    await self.pipette.pick_up_tips(self.column)

    self.assertEqual(await self._tip_names(), original_tips)
    self.assertFalse(any(await _has_tips(self.column)))
    self.protocol_run.pick_up_tip.assert_awaited_once_with(
      "left-pipette-id", ANY, "A1", Coordinate(z=tip_length)
    )

  async def test_column_aspiration_transfers_volume_into_every_tip_with_one_stroke(self) -> None:
    await self.pipette.pick_up_tips(self.column)

    await self.pipette.aspirate(self.sources, volume=10)

    self.assertEqual(await _volumes(self.sources), [5] * 8)
    self.assertEqual(await self._tip_volumes(pb.VIEW_COMMITTED), [10] * 8)
    self.protocol_run.aspirate_in_place.assert_awaited_once_with("left-pipette-id", 10, 7.6)

  async def test_column_dispense_uses_requested_flow_rate_for_every_tip(self) -> None:
    await self.pipette.pick_up_tips(self.column)
    for tip in await self.pipette.get_tips():
      await tip.set_volume(10)

    await self.pipette.dispense(self.destinations, volume=10, flow_rate=6)

    self.assertEqual(await _volumes(self.destinations), [10] * 8)
    self.assertEqual(await self._tip_volumes(pb.VIEW_COMMITTED), [0] * 8)
    self.protocol_run.dispense_in_place.assert_awaited_once_with("left-pipette-id", 10, 6)

  async def test_column_return_restores_each_tip_to_its_original_spot(self) -> None:
    original_tips = [await _tip_name(spot) for spot in self.column]
    await self.pipette.pick_up_tips(self.column)

    await self.pipette.return_tips()

    self.assertEqual([await _tip_name(spot) for spot in self.column], original_tips)
    self.assertEqual(await self.pipette.get_tips(), ())
    self.assertFalse(await self.pipette.has_tip())
    self.protocol_run.drop_tip.assert_awaited_once_with(
      "left-pipette-id", ANY, "A1", Coordinate(z=10)
    )


if __name__ == "__main__":
  unittest.main()
