"""Regressions for atomic, two-sided Flex liquid tracking."""

import asyncio
import unittest
from typing import List, cast
from unittest.mock import AsyncMock, patch

from pylabrobot.opentrons import FlexHead8
from pylabrobot.opentrons.flex.tests.mock_utils import make_api, make_deck, make_flex, place
from pylabrobot.opentrons.model import Liquid, read
from pylabrobot.opentrons.tracking import validate_liquid_transfer
from pylabrobot.resources.errors import TooLittleLiquidError
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb


class FlexTransactionTests(unittest.IsolatedAsyncioTestCase):
  """A failed operation must leave every participating volume unchanged."""

  async def asyncSetUp(self):
    """Mount a column with mocked API replies and fill the source wells."""
    self.api = make_api(pipettes=[("p1000_multi_flex", 8, 5, 1000, "left")])
    deck = await make_deck()
    self.flex = make_flex(deck=deck, host="offline", api=self.api)
    self.rack = cast(handles.TipRack, await place(deck, "flex_96_tiprack_50ul", "tips", "D1"))
    self.plate = cast(handles.Plate, await place(deck, "cor_96_wellplate_360uL_Fb", "plate", "B1"))
    await self.flex.setup()
    head = self.flex.left
    assert isinstance(head, FlexHead8)
    self.head: FlexHead8 = head
    await self.head.pick_up_tips(self.rack["A1:H1"])
    for well in self.plate["A1:H1"]:
      await cast(handles.Well, well).set_volume(100)

  async def asyncTearDown(self):
    """Release the mocked run."""
    await self.flex.disconnect()

  async def _tip_volumes(self) -> List[float]:
    return [await t.get_volume() for t in await self.head.get_mounted_tips() if t is not None]

  async def _well_volumes(self, wells: List[handles.Resource]) -> List[float]:
    return [await cast(handles.Well, w).get_volume() for w in wells]

  async def test_validation_does_not_change_the_store(self):
    """Successful and failed validation leave staged volumes as they are and change nothing."""
    store = self.flex.store
    source, destination = self.plate.get_well("A1"), self.plate.get_well("A2")
    await store.commands.begin_liquid_transfer(
      spb.BeginLiquidTransferRequest(
        frame=self.flex.deck.ref,
        direction=spb.TRANSFER_DIRECTION_ASPIRATE,
        items=[
          spb.TransferItem(
            container=source.ref, shaft=pb.ResourceRef(id=self.head.shafts.shafts[0]), volume=10
          )
        ],
      )
    )
    revision = (await store.commands.get_store_info(spb.GetStoreInfoRequest())).revision
    tree = await read(store, [source, destination])
    staged, empty = Liquid.of(tree.node(source)), Liquid.of(tree.node(destination))
    validate_liquid_transfer([staged], [empty], 20)
    with self.assertRaises(TooLittleLiquidError):
      validate_liquid_transfer([staged], [empty], 95)
    self.assertEqual(await source.get_volume(pb.VIEW_COMMITTED), 100)
    self.assertEqual(await source.get_volume(), 90)
    self.assertEqual(await destination.get_volume(), 0)
    self.assertEqual(
      (await store.commands.get_store_info(spb.GetStoreInfoRequest())).revision, revision
    )

  async def test_transfer_tracks_wells_and_tips(self):
    """Both sides of a successful transfer change by the same volume."""
    column = self.plate["A1:H1"]
    await self.head.aspirate(column, volume=20, flow_rate=10)
    self.assertEqual(await self._well_volumes(column), [80] * 8)
    self.assertEqual(await self._tip_volumes(), [20] * 8)
    await self.head.dispense(column, volume=20, flow_rate=10)
    self.assertEqual(await self._well_volumes(column), [100] * 8)
    self.assertEqual(await self._tip_volumes(), [0] * 8)

  async def test_later_staging_failure_rolls_back_earlier_wells(self):
    """An empty later well must not leave earlier wells partly staged."""
    await self.plate.get_well("B1").set_volume(0)
    with self.assertRaises(TooLittleLiquidError):
      await self.head.aspirate(self.plate["A1:H1"], volume=20, flow_rate=10)
    self.assertEqual(await self.plate.get_well("A1").get_volume(), 100)
    self.assertEqual(await self._tip_volumes(), [0] * 8)

  async def test_cancellation_rolls_back_all_volumes(self):
    """Cancellation while issuing a command restores staged bookkeeping."""
    column = self.plate["A1:H1"]
    with patch.object(self.flex, "_execute_command", AsyncMock(side_effect=asyncio.CancelledError)):
      with self.assertRaises(asyncio.CancelledError):
        await self.head.aspirate(column, volume=20, flow_rate=10)
    self.assertEqual(await self._well_volumes(column), [100] * 8)
    self.assertEqual(await self._tip_volumes(), [0] * 8)
