"""PLR geometry and safe sequencing for Flex liquid operations."""

import unittest
from typing import cast
from unittest.mock import AsyncMock, patch

from pylabrobot.opentrons import FlexHead8
from pylabrobot.opentrons.decks import get_slot_holder
from pylabrobot.opentrons.flex.tests.mock_utils import make_api, make_deck, make_flex, place
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles, library


class PipettingPrimitivesTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    """Mount tips with mocked API replies; leave the plate unregistered."""
    self.api = make_api(pipettes=[("p1000_multi_flex", 8, 5, 1000, "left")])
    self.deck = await make_deck()
    self.flex = make_flex("offline", api=self.api, deck=self.deck)
    self.rack = cast(
      handles.TipRack, await place(self.deck, "flex_96_filtertiprack_50ul", "tips", "D1")
    )
    self.plate = cast(
      handles.Plate, await place(self.deck, "cor_96_wellplate_360uL_Fb", "plate", "C2")
    )
    # Volumes are not what these tests are about.
    await self.plate.set_volume_tracking(False)
    await self.rack.set_volume_tracking(False)
    await self.flex.setup()
    head = self.flex.left_pipette
    assert isinstance(head, FlexHead8)
    self.head: FlexHead8 = head
    await self.head.pick_up_tips(self.rack["A1:H1"])
    self.api.submit_command.reset_mock()

  async def asyncTearDown(self):
    """Close the mocked run without issuing cleanup movement."""
    await self.flex.disconnect()

  async def test_plr_column_position_without_server_labware(self):
    """Position from cavity geometry and prime above the plate, before descent."""
    with patch.object(self.flex, "_ensure_labware_loaded", AsyncMock(side_effect=AssertionError)):
      await self.head.aspirate(self.plate["A1:H1"], 1, flow_rate=1, liquid_height=12.67)
    commands = self.api.submit_command.await_args_list
    self.assertEqual(
      [c.args[1] for c in commands],
      [
        "moveToCoordinates",
        "prepareToAspirate",
        "moveToCoordinates",
        "aspirateInPlace",
        "savePosition",
        "moveRelative",
      ],
    )
    self.assertEqual(commands[0].args[2]["coordinates"], {"x": 178.3, "y": 181.2, "z": 109.0})
    self.assertEqual(commands[0].args[2]["minimumZHeight"], 109.0)
    self.assertEqual(commands[2].args[2]["coordinates"], {"x": 178.3, "y": 181.2, "z": 16.2})
    self.assertEqual(commands[2].args[2]["minimumZHeight"], 16.2)
    self.assertEqual(commands[3].args[2]["volume"], 1)
    self.assertEqual(commands[-1].args[2]["axis"], "z")

  async def test_dispense_uses_updated_plr_location_and_cavity_floor(self):
    """PLR placement and caller offsets determine XYZ, without a robot load."""
    holder = await get_slot_holder(self.deck, "C2")
    await holder.assign_child_resource(self.plate, location=Coordinate(z=60))
    await self.head.dispense(self.plate["A2:H2"], 1, offset=Coordinate(x=2, y=-1, z=0.5))
    commands = self.api.submit_command.await_args_list
    self.assertEqual(
      [c.args[1] for c in commands],
      [
        "moveToCoordinates",
        "moveToCoordinates",
        "dispenseInPlace",
        "savePosition",
        "moveRelative",
      ],
    )
    self.assertEqual(commands[0].args[2]["coordinates"], {"x": 189.3, "y": 180.2, "z": 109.0})
    self.assertAlmostEqual(commands[1].args[2]["coordinates"]["z"], 60 + 3.53 + 1 + 0.5)

  async def test_missing_cavity_floor_is_rejected_before_motion(self):
    """Never guess a cavity floor from an Opentrons load name."""
    definition = library.get_model("cor_96_wellplate_360uL_Fb").definition
    definition.attributes.itemized.grid.item.attributes.container.ClearField("material_z_thickness")
    holder = await get_slot_holder(self.deck, "C2")
    await self.plate.unassign()
    plate = cast(
      handles.Plate, await self.flex.store.create(definition, name="floorless", parent=holder)
    )
    await plate.set_volume_tracking(False)
    with self.assertRaisesRegex(ValueError, "material_z_thickness"):
      await self.head.aspirate(plate["A1:H1"], 1)
    self.assertEqual(self.api.submit_command.await_args_list, [])

  async def test_facility_placement_does_not_change_robot_commands(self):
    """Facility translations and rotations must not reach robot motion commands."""
    await self.head.aspirate(self.plate["A1:H1"], 1, liquid_height=4)
    expected = self.api.submit_command.await_args_list[:]
    facility = await self.flex.store.create(
      build.resource("facility", Coordinate(2400, 1000, 0)), name="facility"
    )
    await facility.assign_child_resource(self.deck, location=Coordinate(-900, 200, 300))
    for angle in (0, 90):
      with self.subTest(angle=angle):
        await facility.rotate_to(z=angle)
        self.api.submit_command.reset_mock()
        await self.head.aspirate(self.plate["A1:H1"], 1, liquid_height=4)
        self.assertEqual(self.api.submit_command.await_args_list, expected)

  async def test_single_nozzle_reach_ignores_facility_translation(self):
    """The reach envelope is fixed to the deck, including its front row."""
    expected = await self.head.reachable_single_nozzles(self.rack, "H1")
    self.assertEqual(expected, ("H1",))
    facility = await self.flex.store.create(
      build.resource("facility", Coordinate(2400, 1000, 0)), name="facility"
    )
    await facility.assign_child_resource(self.deck, location=Coordinate(-900, 1000, 300))
    self.assertEqual(await self.head.reachable_single_nozzles(self.rack, "H1"), expected)
