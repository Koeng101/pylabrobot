"""Partial-column pipetting must reject modeled adjacent obstacles before motion."""

import unittest
from typing import List, Optional, cast

from pylabrobot.opentrons import FlexHead8
from pylabrobot.opentrons.decks import check_partial_nozzle_clearance, get_slot_holder
from pylabrobot.opentrons.flex.tests.mock_utils import make_api, make_deck, make_flex, place
from pylabrobot.opentrons.model import read
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb


def _box(name: str, x: float, y: float, z: float) -> pb.ResourceDefinition:
  return build.resource(name, Coordinate(x, y, z))


def _empty_rack(name: str) -> pb.ResourceDefinition:
  """A tip rack's body, with no spots."""
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 99),
    kind=pb.RESOURCE_KIND_TIP_RACK,
    type_name="TipRack",
    itemized=pb.ItemizedSpec(),
  )


class PartialClearanceTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    """Pick up four front tips with mocked API replies in a clear D1 slot."""
    self.api = make_api(pipettes=[("p1000_multi_flex", 8, 5, 1000, "left")])
    self.deck = await make_deck()
    self.flex = make_flex("offline", api=self.api, deck=self.deck)
    self.rack = cast(
      handles.TipRack, await place(self.deck, "flex_96_filtertiprack_50ul", "tips", "D1")
    )
    self.plate = cast(
      handles.Plate, await place(self.deck, "cor_96_wellplate_360uL_Fb", "plate", "C2")
    )
    # Liquid is not what these tests are about: the plate's and the tips' volumes go untracked.
    await self.plate.set_volume_tracking(False)
    await self.flex.setup()
    head = self.flex.left_pipette
    assert isinstance(head, FlexHead8)
    self.head: FlexHead8 = head
    await head.pick_up_tips(self.rack["A6:D6"], use_channels=[4, 5, 6, 7])
    await self._untrack_tips()
    self.api.submit_command.reset_mock()

  async def asyncTearDown(self):
    """Release the mocked session."""
    await self.flex.disconnect()

  async def _untrack_tips(self) -> None:
    for tip in await self.head.get_mounted_tips():
      if tip is not None:
        await tip.set_volume_tracking(False)

  async def _mounted_count(self) -> int:
    return sum(t is not None for t in await self.head.get_mounted_tips())

  def _front_wells(self, column: int) -> List[handles.Resource]:
    return self.plate[f"A{column}:D{column}"]

  async def test_modeled_tip_rack_blocks_aspirate_and_dispense_before_motion(self):
    """Physical removal cannot bypass the obstacle still present in the store."""
    await place(self.deck, _empty_rack("1000ul_tips_B2"), "1000ul_tips_B2", "B2")
    for operation in (self.head.aspirate, self.head.dispense):
      with self.subTest(operation=operation.__name__):
        with self.assertRaisesRegex(ValueError, "Collision risk.*C2.*B2"):
          await operation(self._front_wells(1), 1, liquid_height=1)
        self.assertEqual(self.api.submit_command.await_args_list, [])
        self.assertEqual(self.head._nozzle_layout, "PARTIAL")
        self.assertEqual(await self._mounted_count(), 4)

  async def test_clear_slot_preserves_partial_layout_and_positions_primary_well(self):
    """The H1 primary nozzle must be over D1 when front tips cover A1-D1."""
    await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    await self.head.dispense(self._front_wells(2), 1, liquid_height=1)
    types = [c.args[1] for c in self.api.submit_command.await_args_list]
    self.assertNotIn("configureNozzleLayout", types)
    moves = [c for c in self.api.submit_command.await_args_list if c.args[1] == "moveToCoordinates"]
    self.assertEqual(moves[0].args[2]["coordinates"], {"x": 178.3, "y": 154.2, "z": 109.0})
    self.assertEqual(moves[2].args[2]["coordinates"], {"x": 187.3, "y": 154.2, "z": 109.0})
    self.assertEqual(types.count("aspirateInPlace"), 1)
    self.assertEqual(types.count("dispenseInPlace"), 1)

  async def test_incompatible_well_spacing_is_rejected_before_motion(self):
    """Bookkeeping must never describe wells that the nozzles cannot reach."""
    wells = self._front_wells(1)
    wells[1] = self.plate.get_item("B2")
    with self.assertRaisesRegex(ValueError, "9 mm spacing"):
      await self.head.aspirate(wells, 1)
    self.assertEqual(self.api.submit_command.await_args_list, [])

  async def test_clearance_uses_operation_height_and_tip_length(self):
    """The same obstacle clears long tips or a higher target, but not short low tips."""
    await place(self.deck, _box("raised_plate_B2", 127.76, 85.48, 60), "raised_plate_B2", "B2")
    with self.assertRaisesRegex(ValueError, "Collision risk"):
      await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    self.assertEqual(self.api.submit_command.await_args_list, [])
    await self.head.aspirate(self._front_wells(1), 1, liquid_height=35)
    self.api.submit_command.reset_mock()
    await self._lengthen_mounted_tips(95.6)
    await self.head.dispense(self._front_wells(1), 1, liquid_height=1)
    self.assertIn("dispenseInPlace", [c.args[1] for c in self.api.submit_command.await_args_list])

  async def _lengthen_mounted_tips(self, size_z: float) -> None:
    """Swap each mounted tip for one like it but `size_z` long, on the same shaft."""
    store = self.flex.store
    tree = await read(store, [self.head.shafts.root], depth=2)
    for channel, shaft_id in enumerate(self.head.shafts.shafts):
      tip = tree.tool(tree.node(shaft_id))
      if tip is None:
        continue
      definition = pb.ResourceDefinition()
      definition.attributes.CopyFrom(tip.attributes)
      definition.attributes.ClearField("location")
      definition.attributes.size.z = size_z
      definition.initial_state.volume.CopyFrom(
        pb.VolumeState(tracking_enabled=False, volume=tip.state.volume.volume)
      )
      await (await store.get_by_id(tip.id)).delete()
      shaft = await store.get_by_id(shaft_id)
      await store.create(definition, name=f"long_tip_{channel}", parent=shaft)

  async def test_rack_can_clear_at_high_operation_z(self):
    """Tip racks use geometry too; their type alone cannot block a high operation."""
    await place(self.deck, _empty_rack("obstacle_rack_B2"), "obstacle_rack_B2", "B2")
    await self.head.aspirate(self._front_wells(1), 1, liquid_height=1, offset=Coordinate(z=80))
    self.assertIn("aspirateInPlace", [c.args[1] for c in self.api.submit_command.await_args_list])

  async def test_obstacle_absolute_height_includes_elevation(self):
    """A short plate on a tall support is not treated as a short obstacle."""
    await self.flex.store.create(
      _box("plate_on_support_B2", 127.76, 85.48, 14),
      name="plate_on_support_B2",
      parent=await get_slot_holder(self.deck, "B2"),
      location=Coordinate(z=50),
    )
    with self.assertRaisesRegex(ValueError, "Collision risk"):
      await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    self.assertEqual(self.api.submit_command.await_args_list, [])

  async def test_low_plate_clears_short_tips(self):
    """A normal low plate behind C2 must not prevent the partial operation."""
    await place(self.deck, _box("low_plate_B2", 127.76, 85.48, 14.2), "low_plate_B2", "B2")
    await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    self.assertIn("aspirateInPlace", [c.args[1] for c in self.api.submit_command.await_args_list])

  async def test_single_nozzle_uses_the_same_height_check(self):
    """Single and partial columns both reach the geometry guard before motion."""
    mounted = await self.head.shafts.mounted()
    await self.head.shafts.discard([tip for tip in mounted.tips[:7] if tip is not None])
    self.head._nozzle_layout = "SINGLE"
    self.head._single_anchor = "H1"
    await place(self.deck, _box("raised_plate_B2", 127.76, 85.48, 60), "raised_plate_B2", "B2")
    with self.assertRaisesRegex(ValueError, "Collision risk"):
      await self.head.aspirate(self.plate.get_well("A1"), 1, liquid_height=1)
    self.assertEqual(self.api.submit_command.await_args_list, [])
    await self.head.aspirate(self.plate.get_well("A1"), 1, liquid_height=35)

  async def test_touching_nozzle_plane_is_blocked(self):
    """Equality is contact, not clearance."""
    await place(self.deck, _box("contact_B2", 127.76, 85.48, 52), "contact_B2", "B2")
    with self.assertRaisesRegex(ValueError, "Collision risk"):
      await self.head.dispense(self._front_wells(1), 1, liquid_height=1.07)
    self.assertEqual(self.api.submit_command.await_args_list, [])

  async def test_twenty_mm_margin_boundary(self):
    """Reject less than 20 mm, accept exactly 20 mm and greater clearance."""
    await place(self.deck, _box("obstacle_B2", 127.76, 85.48, 60), "obstacle_B2", "B2")
    for gap in (19.9, 20.0, 20.1):
      with self.subTest(gap=gap):
        operation_z: Optional[float] = 60 + gap
        if gap < 20:
          with self.assertRaisesRegex(ValueError, "at least 20mm is required"):
            await check_partial_nozzle_clearance(self.deck, "C2", "H1", 4, operation_z=operation_z)
        else:
          await check_partial_nozzle_clearance(self.deck, "C2", "H1", 4, operation_z=operation_z)

  async def test_facility_placement_preserves_partial_motion_and_collision_checks(self):
    """Offsets must neither move partial tips nor hide an adjacent obstacle."""
    await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    expected = self.api.submit_command.await_args_list[:]
    facility = await self.flex.store.create(_box("facility", 2400, 1000, 0), name="facility")
    await facility.assign_child_resource(self.deck, location=Coordinate(-900, 200, -300))
    await facility.rotate_to(z=90)
    self.api.submit_command.reset_mock()
    await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    self.assertEqual(self.api.submit_command.await_args_list, expected)

    await place(self.deck, _box("obstacle", 127, 85, 99), "obstacle", "B2")
    self.api.submit_command.reset_mock()
    with self.assertRaisesRegex(ValueError, "Collision risk.*C2.*B2"):
      await self.head.aspirate(self._front_wells(1), 1, liquid_height=1)
    self.assertEqual(self.api.submit_command.await_args_list, [])
