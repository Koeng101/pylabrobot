"""OT-2 motion preflight with mocked run operations."""

import unittest
from typing import List, Sequence, cast
from unittest.mock import ANY, AsyncMock, create_autospec

from pylabrobot.io.http import HTTP
from pylabrobot.opentrons import OT2, OT2_8ChannelPipette, OT2SingleChannelPipette
from pylabrobot.opentrons.decks import OT2_SLOT_LOCATIONS, create_ot2_deck, get_slot_holder
from pylabrobot.opentrons.heads import PipetteShafts
from pylabrobot.opentrons.labware import LabwareRegistry
from pylabrobot.opentrons.run import OpentronsRun
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore


async def _all_have_tips(spots: Sequence[handles.Resource]) -> bool:
  return all([await cast(handles.TipSpot, spot).has_tip() for spot in spots])


async def _none_have_tips(spots: Sequence[handles.Resource]) -> bool:
  return not any([await cast(handles.TipSpot, spot).has_tip() for spot in spots])


class OT2MotionTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    """Set up both pipette types and a tip rack without connecting to hardware."""
    self.protocol_run = create_autospec(OpentronsRun, instance=True, spec_set=True)
    self.protocol_run.active = True
    self.protocol_run.get_position.return_value = Coordinate(30.25, 40.5, 20)
    self.store = ResourceStore.in_memory()
    self.deck = await create_ot2_deck(self.store)
    self.robot = OT2("ot2.local", deck=self.deck, io=AsyncMock(spec_set=HTTP))
    self.robot._run = self.protocol_run
    self.robot._labware = LabwareRegistry(self.protocol_run)
    self.multi = OT2_8ChannelPipette(
      self.robot,
      "left",
      "p20_multi_gen2",
      "left-id",
      await PipetteShafts.create(self.store, "left_pipette", 8),
    )
    self.single = OT2SingleChannelPipette(
      self.robot,
      "right",
      "p20_single_gen2",
      "right-id",
      await PipetteShafts.create(self.store, "right_pipette", 1),
    )
    self.rack = cast(
      handles.TipRack,
      await self.store.create(
        "opentrons_96_filtertiprack_20ul", name="tips", parent=await get_slot_holder(self.deck, 1)
      ),
    )
    self.column = self.rack["A1:H1"]
    self.primary = await self.column[0].get_location_wrt(self.deck, "c", "c", "b")
    tip = await cast(handles.TipSpot, self.column[0]).get_tip()
    assert tip is not None
    attributes = await tip.attributes()
    self.nozzle_z = self.primary.z + attributes.size.z - attributes.head_tool.fitting_depth

  async def _place_obstacle(
    self, location: Coordinate, height: float, rotation: float = 0
  ) -> handles.Resource:
    """Place an obstacle extending from another slot into the pickup region."""
    obstacle = await self.store.create(
      build.resource("obstacle", Coordinate(20, 20, height), rotation=Rotation(z=rotation)),
      name="obstacle",
    )
    holder = await get_slot_holder(self.deck, 3)
    await holder.assign_child_resource(obstacle, location=location - OT2_SLOT_LOCATIONS[2])
    return obstacle

  async def _tip_names(self, pipette: OT2_8ChannelPipette) -> List[str]:
    return [tip.name for tip in await pipette.tips()]

  async def test_unreachable_tip_commands_send_nothing_on_either_pipette(self) -> None:
    """Reach failures occur before labware loading, command submission, or tip staging."""
    for pipette, pickup, drop, target in (
      (self.multi, self.multi.pick_up_tips, self.multi.drop_tips, self.column),
      (self.single, self.single.pick_up_tip, self.single.drop_tip, self.column[0]),
    ):
      with self.subTest(pipette=pipette.name):
        for offset in (Coordinate(x=1000), Coordinate(y=-1000), Coordinate(z=-1000)):
          with self.subTest(offset=offset):
            self.protocol_run.reset_mock()
            with self.assertRaises(ValueError):
              await pickup(target, offset=offset)  # type: ignore[arg-type,operator]
            self.assertEqual(self.protocol_run.mock_calls, [])
            self.assertFalse(await pipette.has_tip())
            self.assertTrue(await _all_have_tips(self.column))
        await pickup(target)  # type: ignore[arg-type,operator]
        self.protocol_run.reset_mock()
        with self.assertRaises(ValueError):
          await drop(target, offset=Coordinate(x=1000))  # type: ignore[arg-type,operator]
        self.assertEqual(self.protocol_run.mock_calls, [])
        self.assertTrue(await pipette.has_tip())
        await drop(target)  # type: ignore[arg-type,operator]

  async def test_pickup_respects_mount_reach_and_xy_offset(self) -> None:
    """The left mount can reach negative X positions the right mount cannot."""
    robot_x = self.primary.x - OT2_SLOT_LOCATIONS[0].x
    offset = Coordinate(x=-20 - robot_x)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "right mount"):
      await self.single.pick_up_tip(cast(handles.TipSpot, self.column[0]), offset=offset)
    self.assertEqual(self.protocol_run.mock_calls, [])
    await self.multi.pick_up_tips(self.column, offset=offset)  # type: ignore[arg-type]
    self.assertTrue(await self.multi.has_tip())

  async def test_eight_channel_y_reach_uses_head_center(self) -> None:
    """The reference nozzle is 31.5 mm behind the center used for reach checks."""
    self.protocol_run.get_position.return_value = Coordinate(100, 100, 120)
    for y in (31.5, 379.0):
      with self.subTest(y=y):
        self.protocol_run.reset_mock()
        await self.multi.move_to(Coordinate(100, y, 120))
        self.protocol_run.move_to.assert_awaited_once_with(
          "left-id",
          Coordinate(100, y, 120),
          speed=None,
          minimum_z_height=None,
          force_direct=False,
        )
    for y in (20, 31.49, 379.01):
      with self.subTest(y=y):
        self.protocol_run.reset_mock()
        with self.assertRaises(ValueError):
          await self.multi.move_to(Coordinate(100, y, 120))
        self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_single_channel_y_reach_has_no_head_center_offset(self) -> None:
    """Single-channel targets remain bounded directly by Y=0 through Y=347.5."""
    self.protocol_run.get_position.return_value = Coordinate(100, 100, 120)
    for y in (0, 20, 347.5):
      await self.single.move_to(Coordinate(100, y, 120))
    for y in (-0.01, 347.51, 379):
      with self.subTest(y=y):
        self.protocol_run.reset_mock()
        with self.assertRaises(ValueError):
          await self.single.move_to(Coordinate(100, y, 120))
        self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_tip_commands_use_head_center_before_tracker_changes(self) -> None:
    """Pickup and drop apply the same reference offset as explicit moves."""
    robot_y = self.primary.y - OT2_SLOT_LOCATIONS[0].y
    offset = Coordinate(y=20 - robot_y)
    self.protocol_run.reset_mock()
    with self.assertRaises(ValueError):
      await self.multi.pick_up_tips(self.column, offset=offset)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertTrue(await _all_have_tips(self.column))
    await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]
    tips = await self._tip_names(self.multi)
    self.protocol_run.reset_mock()
    with self.assertRaises(ValueError):
      await self.multi.drop_tips(self.column, offset=offset)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertEqual(await self._tip_names(self.multi), tips)
    self.assertTrue(await _none_have_tips(self.column))

  async def test_tall_overlapping_resource_rejects_before_pickup(self) -> None:
    """A tall neighboring resource blocks the entire eight-nozzle footprint."""
    await self._place_obstacle(self.primary + Coordinate(x=-10, y=-50, z=-self.primary.z), 100)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "obstacle"):
      await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    self.assertTrue(await _all_have_tips(self.column))
    self.assertFalse(await self.multi.has_tip())

  async def test_short_resource_below_nozzles_is_cleared(self) -> None:
    """XY overlap alone does not reject labware below the pickup clearance threshold."""
    await self._place_obstacle(
      self.primary + Coordinate(x=-10, y=-50, z=-self.primary.z), self.nozzle_z - 10 - 0.1
    )
    await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]
    self.assertTrue(await self.multi.has_tip())

  async def test_300ul_pickup_clears_short_plate_below_nozzle_engagement(self) -> None:
    """Long tips clear an overlapping short plate despite their bottoms being near the deck."""
    pipette = OT2_8ChannelPipette(
      self.robot,
      "left",
      "p300_multi_gen2",
      "p300-id",
      await PipetteShafts.create(self.store, "p300_pipette", 8),
    )
    rack = cast(
      handles.TipRack,
      await self.store.create(
        "opentrons_96_tiprack_300ul", name="tips300", parent=await get_slot_holder(self.deck, 10)
      ),
    )
    plate = await self.store.create("celltreat_96_wellplate_350uL_Fb", name="short_plate")
    # Extend the plate beneath the full column's front nozzles.
    holder = await get_slot_holder(self.deck, 7)
    await holder.assign_child_resource(plate, location=Coordinate(y=36))

    await pipette.pick_up_tips(rack["A1:H1"])  # type: ignore[arg-type]

    self.assertEqual(len(await pipette.tips()), 8)
    self.assertTrue(await _none_have_tips(rack["A1:H1"]))
    self.protocol_run.pick_up_tip.assert_awaited_once_with("p300-id", ANY, "A1", ANY)

  async def test_z_offset_is_included_in_pickup_clearance(self) -> None:
    """A downward pickup offset can bring the nozzle envelope into a short obstacle."""
    await self._place_obstacle(
      self.primary + Coordinate(x=-10, y=-50, z=-self.primary.z), self.nozzle_z - 10 - 0.1
    )
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "obstacle"):
      await self.multi.pick_up_tips(self.column, offset=Coordinate(z=-1))  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_xy_offset_is_included_in_pickup_clearance(self) -> None:
    """An obstacle outside the nominal footprint can overlap an offset pickup."""
    await self._place_obstacle(self.primary + Coordinate(x=6, y=-50, z=-self.primary.z), 100)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "obstacle"):
      await self.multi.pick_up_tips(self.column, offset=Coordinate(x=2))  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
    await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]

  async def test_rotated_obstacle_uses_its_transformed_corners(self) -> None:
    """A rotated obstacle can extend to the left of its resource origin."""
    await self._place_obstacle(
      self.primary + Coordinate(x=6, y=-10, z=-self.primary.z), 100, rotation=180
    )
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "obstacle"):
      await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_child_overhanging_its_parent_is_checked(self) -> None:
    """A carrier's small bounds cannot hide an attached component in the pickup footprint."""
    parent = await self._place_obstacle(self.primary + Coordinate(x=100), 1)
    await self.store.create(
      build.resource("overhang", Coordinate(20, 20, 100)),
      name="overhang",
      parent=parent,
      location=Coordinate(x=-110, y=-50),
    )
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "overhang"):
      await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])

  async def test_clearance_is_independent_of_world_translation(self) -> None:
    """Head and resource bounds use the same deck-relative frame."""
    world = await self.store.create(build.resource("world", Coordinate(1000, 1000, 1000)), "world")
    await world.assign_child_resource(self.deck, location=Coordinate(400, 500, 600))
    await self._place_obstacle(self.primary + Coordinate(x=-10, y=-50, z=-self.primary.z), 100)
    self.protocol_run.reset_mock()
    with self.assertRaisesRegex(ValueError, "obstacle"):
      await self.multi.pick_up_tips(self.column)  # type: ignore[arg-type]
    self.assertEqual(self.protocol_run.mock_calls, [])
