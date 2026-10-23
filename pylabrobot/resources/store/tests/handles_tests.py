"""Handles over the test deck: each answers what PLR's own resource classes answer for the same
deck, and each change is made in the store, where every handle sees it."""

from __future__ import annotations

import unittest

from pylabrobot.resources import Coordinate
from pylabrobot.resources.carrier import PlateCarrier
from pylabrobot.resources.corning.plates import cor_96_wellplate_360uL_Fb
from pylabrobot.resources.plate import Plate as PLRPlate
from pylabrobot.resources.well import Well as PLRWell
from pylabrobot.resources.store import handles as h
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.tests.store_tests import ROOT, StoreTestCase, build_deck
from pylabrobot.resources.store.v1 import types_pb2 as pb


class HandleTestCase(StoreTestCase):
  """The test deck in a store, and the same deck built with PLR's classes beside it."""

  async def asyncSetUp(self) -> None:
    await super().asyncSetUp()
    self.plr = build_deck()
    self.deck = await self.store.get(ROOT)


class ReadingTests(HandleTestCase):
  async def test_a_handle_has_its_kind_and_name(self):
    plate = await self.store.get("plate", root=self.deck)
    self.assertIsInstance(plate, h.Plate)
    self.assertEqual(plate.name, "plate")
    self.assertEqual(plate.kind, pb.RESOURCE_KIND_PLATE)
    self.assertIsInstance(self.deck, h.Deck)
    self.assertEqual(await self.store.get("plate", root=ROOT), plate)

  async def test_items_are_known_without_asking(self):
    plate = await self.store.get("plate", root=self.deck)
    assert isinstance(plate, h.Plate)
    plr = self.plr.get_resource("plate")
    assert isinstance(plr, PLRPlate)
    self.assertEqual(plate.num_items, 96)
    self.assertEqual((plate.num_items_x, plate.num_items_y), (12, 8))
    for key in ("A1", 5, (2, 3), "A1:H1", slice(0, 8), slice("A1", "A2"), [0, 95], range(3)):
      with self.subTest(key=key):
        self.assertEqual([w.name for w in plate[key]], [w.name for w in plr[key]])  # type: ignore
    self.assertEqual(plate.get_well("H12").name, plr.get_well("H12").name)
    self.assertEqual(
      [w.name for w in plate.get_wells("A1:C1")],
      ["plate_well_A1", "plate_well_B1", "plate_well_C1"],
    )
    with self.assertRaises(IndexError):
      plate.get_item("Z99")

  async def test_locations_and_sizes_are_plr_s(self):
    for name in ("plate", "plate_well_C4", "tips_tipspot_H12", "trough", "shaft_2"):
      handle = await self.store.get(name, root=self.deck)
      plr = self.plr.get_resource(name)
      with self.subTest(resource=name):
        for x, y, z in (("l", "f", "b"), ("c", "c", "t"), ("r", "b", "c")):
          ours = await handle.get_absolute_location(x, y, z)
          self.assertEqual(ours, plr.get_absolute_location(x, y, z))
        ours = await handle.get_location_wrt(self.deck, "c", "c", "b")
        self.assertEqual(ours, plr.get_location_wrt(self.plr, "c", "c", "b"))
        self.assertEqual(
          await handle.get_size(), Coordinate(plr.get_size_x(), plr.get_size_y(), plr.get_size_z())
        )
        self.assertEqual(await handle.get_location(), plr.location)

  async def test_the_tree_is_walked_through_the_store(self):
    well = await self.store.get("plate_well_A1", root=self.deck)
    plate = await well.get_parent()
    self.assertIsInstance(plate, h.Plate)
    self.assertEqual(await well.get_root(), self.deck)
    carrier = await self.deck.get_resource("plate_carrier")
    self.assertIsInstance(carrier, h.Carrier)
    assert isinstance(carrier, h.Carrier)
    self.assertEqual(carrier.capacity, 5)
    site = carrier[0]
    self.assertIsInstance(site, h.PlateHolder)
    assert isinstance(site, h.PlateHolder)
    self.assertEqual(await site.get_resource_held(), plate)
    self.assertIsNone(await carrier[4].get_resource_held())  # type: ignore
    self.assertIn(plate, await site.get_children())
    self.assertTrue(await well.is_in_subtree_of(carrier))
    wells = await carrier.find_resources(kinds=[pb.RESOURCE_KIND_WELL])
    self.assertEqual(len(wells), 192)
    with self.assertRaises(StoreError):
      await carrier.get_resource("tips")

  async def test_volumes_and_heights(self):
    plate = await self.store.get("plate", root=self.deck)
    assert isinstance(plate, h.Plate)
    await plate.set_well_volumes([10.0 * i for i in range(96)])
    well = plate.get_well("B1")
    self.assertEqual(await well.get_volume(), 10.0)
    await well.set_volume(100)
    self.assertEqual(await well.get_volume(), 100)
    self.assertEqual(await well.get_free_volume(), 260)
    plr = self.plr.get_resource("plate_well_B1")
    assert isinstance(plr, PLRWell)
    height = await well.compute_height_from_volume(100)
    self.assertAlmostEqual(height, plr.compute_height_from_volume(100), places=6)
    self.assertAlmostEqual(await well.compute_volume_from_height(height), 100, places=6)

  async def test_tips_are_there_until_emptied(self):
    tips = await self.store.get("tips", root=self.deck)
    assert isinstance(tips, h.TipRack)
    spot = tips.get_tip_spot("A1")
    self.assertTrue(await spot.has_tip())
    tip = await spot.get_tip()
    self.assertIsInstance(tip, h.Tip)
    await tips.empty()
    self.assertFalse(await spot.has_tip())
    await tips.set_tip_state([i % 2 == 0 for i in range(96)])
    self.assertTrue(await tips.get_tip_spot(0).has_tip())
    self.assertFalse(await tips.get_tip_spot(1).has_tip())


class ChangingTests(HandleTestCase):
  async def test_labware_is_made_from_plr_s_models(self):
    carrier = await self.deck.get_resource("plate_carrier")
    assert isinstance(carrier, h.Carrier)
    plate = await self.store.create("cor_96_wellplate_360uL_Fb", name="fresh", parent=carrier[2])
    self.assertIsInstance(plate, h.Plate)
    assert isinstance(plate, h.Plate)
    self.assertEqual(plate.get_well("H12").name, "fresh_well_H12")
    plr_carrier = self.plr.get_resource("plate_carrier")
    assert isinstance(plr_carrier, PlateCarrier)
    plr_carrier[2] = cor_96_wellplate_360uL_Fb(name="fresh")
    self.assertEqual(
      await plate.get_well("H12").get_absolute_location("c", "c", "cavity_bottom"),
      self.plr.get_resource("fresh_well_H12").get_absolute_location("c", "c", "cavity_bottom"),
    )

  async def test_a_plate_moves_by_hand(self):
    plate = await self.store.get("plate", root=self.deck)
    carrier = await self.deck.get_resource("plate_carrier")
    assert isinstance(carrier, h.Carrier)
    await carrier[3].assign_child_resource(plate)
    self.assertEqual(await plate.get_parent(), carrier[3])
    await plate.unassign()
    self.assertIsNone(await plate.get_parent())
    self.assertIsNone(await plate.get_location())
    self.assertIn(plate, await self.store.roots())
    await self.deck.assign_child_resource(plate, location=Coordinate(600, 100, 0))
    self.assertEqual(await plate.get_location(), Coordinate(600, 100, 0))

  async def test_turning_and_metadata(self):
    plate = await self.store.get("plate", root=self.deck)
    await plate.unassign()
    await plate.rotate(z=90)
    self.assertEqual((await plate.get_rotation()).z, 90)
    await plate.rotate_to(z=0)
    self.assertEqual((await plate.get_rotation()).z, 0)
    await plate.set_metadata({"owner": "lab"})
    await plate.set_metadata({"run": 3})
    self.assertEqual(await plate.get_metadata(), {"owner": "lab", "run": 3})
    await plate.set_barcode(pb.Barcode(data="123", symbology="code128"))
    barcode = await plate.get_barcode()
    assert barcode is not None
    self.assertEqual(barcode.data, "123")

  async def test_a_locked_deck_refuses_other_clients(self):
    other = ResourceStore.in_memory(self.store.memory)
    plate = await self.store.get("plate", root=self.deck)
    theirs = await other.get("plate", root=ROOT)
    async with self.store.lock(self.deck, holder="test"):
      await plate.set_metadata({"mine": True})
      with self.assertRaises(StoreError) as caught:
        await theirs.set_metadata({"theirs": True})
      self.assertEqual(caught.exception.problem, pb.PROBLEM_LOCKED)
    await theirs.set_metadata({"theirs": True})
    await other.close()

  async def test_deleting_takes_everything_under_it(self):
    plate = await self.store.get("plate", root=self.deck)
    await plate.delete()
    with self.assertRaises(StoreError):
      await self.store.get("plate_well_A1", root=self.deck)


if __name__ == "__main__":
  unittest.main()
