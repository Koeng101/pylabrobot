"""Vertical clearance after completed Flex tip and liquid operations."""

import unittest
from typing import cast
from unittest.mock import AsyncMock, patch

from pylabrobot.opentrons import FlexHead1, FlexHead8, FlexHead96
from pylabrobot.opentrons.errors import OpentronsProtocolError
from pylabrobot.opentrons.flex.tests.mock_utils import make_api, make_deck, make_flex, place
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles


class FlexTraversalTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.io = make_api(
      pipettes=[("p1000_multi_flex", 8, 5, 1000, "left")],
      saved_position={"x": 14, "y": 74, "z": 20},
    )
    deck = await make_deck()
    self.flex = make_flex("offline", api=self.io, deck=deck)
    self.rack = cast(handles.TipRack, await place(deck, "flex_96_filtertiprack_50ul", "tips", "D1"))
    self.plate = cast(handles.Plate, await place(deck, "cor_96_wellplate_360uL_Fb", "plate", "B1"))
    await self.flex.setup()
    head = self.flex.left_pipette
    assert isinstance(head, FlexHead8)
    self.head = head

  async def asyncTearDown(self):
    await self.flex.disconnect()

  async def assert_vertical_retraction(self):
    """The final command must address Z alone, to the computed clearance."""
    self.assertEqual(self.io.submit_command.await_args_list[-2].args[1], "savePosition")
    self.io.submit_command.assert_awaited_with(
      "run",
      "moveRelative",
      {
        "pipetteId": self.head.pipette_id,
        "axis": "z",
        "distance": await self.flex.traversal_height() - 20,
      },
    )

  async def _fill_column(self, volume: float) -> None:
    for well in self.plate["A1:H1"]:
      assert isinstance(well, handles.Well)
      await well.set_volume(volume)

  async def test_pickup_retracts_after_tip_verification(self):
    await self.head.pick_up_tips(self.rack["A1:H1"])
    await self.assert_vertical_retraction()
    self.assertEqual(self.io.submit_command.await_args_list[-3].args[1], "getTipPresence")
    self.assertEqual(sum(t is not None for t in await self.head.get_mounted_tips()), 8)

  async def test_move_to_safe_z_without_tips(self):
    await self.head.move_to_safe_z()
    await self.assert_vertical_retraction()

  async def test_single_channel_move_to_safe_z_without_tips(self):
    io = make_api(pipettes=[("p1000_single_flex", 1, 1, 1000, "left")])
    flex = make_flex("offline", api=io)
    try:
      await flex.setup()
      head = flex.left_pipette
      assert isinstance(head, FlexHead1)
      await head.move_to_safe_z()
      self.assertEqual(io.submit_command.await_args_list[-1].args[1], "moveRelative")
      self.assertEqual(io.submit_command.await_args_list[-1].args[2]["axis"], "z")
    finally:
      await flex.disconnect()

  async def test_public_retraction_rejects_nonfinite_position(self):
    self.io.get_command.return_value.result["position"] = {"x": 14, "y": 74, "z": float("nan")}
    self.io.submit_command.reset_mock()
    with self.assertRaisesRegex(OpentronsProtocolError, "Invalid position"):
      await self.head.move_to_safe_z()
    self.assertEqual(self.io.submit_command.await_count, 1)
    self.assertEqual(self.io.submit_command.await_args.args[1], "savePosition")

  async def test_aspirate_dispense_and_rack_return_retract(self):
    await self.head.pick_up_tips(self.rack["A1:H1"])
    await self._fill_column(40)
    await self.head.aspirate(self.plate["A1:H1"], volume=20)
    await self.assert_vertical_retraction()
    await self.head.dispense(self.plate["A1:H1"], volume=20)
    await self.assert_vertical_retraction()
    await self.head.drop_tips(self.rack, column=0)
    await self.assert_vertical_retraction()

  async def test_does_not_lower_a_head_already_above_clearance(self):
    self.io.get_command.return_value.result["position"] = {"x": 14, "y": 74, "z": 250}
    await self.head.pick_up_tips(self.rack["A1:H1"])
    self.assertEqual(self.io.submit_command.await_args_list[-1].args[1], "savePosition")
    self.assertFalse(
      any(c.args[1] == "moveRelative" for c in self.io.submit_command.await_args_list)
    )

  async def test_tall_labware_raises_clearance(self):
    await place(
      self.flex.deck, build.resource("obstacle", Coordinate(100, 70, 150)), "obstacle", "C2"
    )
    self.assertGreater(await self.flex.traversal_height(), 150)
    await self.head.pick_up_tips(self.rack["A1:H1"])
    await self.assert_vertical_retraction()

  async def test_failed_retraction_preserves_successful_pickup_state(self):
    with patch.object(
      self.head, "move_to_safe_z", AsyncMock(side_effect=RuntimeError("lift failed"))
    ):
      with self.assertRaisesRegex(RuntimeError, "lift failed"):
        await self.head.pick_up_tips(self.rack["A1:H1"])
    for spot in self.rack["A1:H1"]:
      assert isinstance(spot, handles.TipSpot)
      self.assertFalse(await spot.has_tip())
    self.assertTrue(all(t is not None for t in await self.head.get_mounted_tips()))

  async def test_failed_retraction_preserves_successful_aspiration_state(self):
    await self.head.pick_up_tips(self.rack["A1:H1"])
    await self._fill_column(40)
    with patch.object(
      self.head, "move_to_safe_z", AsyncMock(side_effect=RuntimeError("lift failed"))
    ):
      with self.assertRaisesRegex(RuntimeError, "lift failed"):
        await self.head.aspirate(self.plate["A1:H1"], volume=20)
    for well in self.plate["A1:H1"]:
      assert isinstance(well, handles.Well)
      self.assertEqual(await well.get_volume(), 20)
    for tip in await self.head.get_mounted_tips():
      assert tip is not None
      self.assertEqual(await tip.get_volume(), 20)

  async def test_other_head_sizes_retract_after_pickup(self):
    for channels, name in ((1, "p1000_single_flex"), (96, "p1000_96")):
      with self.subTest(channels=channels):
        io = make_api(pipettes=[(name, channels, 1, 1000, "left")])
        deck = await make_deck()
        flex = make_flex("offline", api=io, deck=deck)
        rack = cast(handles.TipRack, await place(deck, "flex_96_filtertiprack_50ul", "tips", "D1"))
        try:
          await flex.setup()
          head = flex.head96 if channels == 96 else flex.left_pipette
          if isinstance(head, FlexHead1):
            await head.pick_up_tips(rack.get_tip_spot("A1"))
          else:
            assert isinstance(head, FlexHead96)
            await head.pick_up_tips(rack)
          self.assertEqual(io.submit_command.await_args_list[-1].args[1], "moveRelative")
          self.assertEqual(io.submit_command.await_args_list[-1].args[2]["axis"], "z")
        finally:
          await flex.disconnect()
