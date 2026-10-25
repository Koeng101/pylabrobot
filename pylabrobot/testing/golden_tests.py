"""Golden records: the same snapshot from PLR's classes and from a store, and files checked."""

from __future__ import annotations

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from pylabrobot.resources import Coordinate, TipSpot, Well
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.definitions import definition_from_resource
from pylabrobot.resources.store.tests.scenes import build_all
from pylabrobot.resources.store.tests.store_tests import build_deck
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.testing import golden


class SnapshotTests(unittest.IsolatedAsyncioTestCase):
  async def test_a_store_snapshots_what_plr_s_classes_do(self):
    deck = build_deck()
    well = deck.get_resource("plate_well_A1")
    spot = deck.get_resource("tips_tipspot_A1")
    assert isinstance(well, Well) and isinstance(spot, TipSpot)
    well.tracker.set_volume(50)
    spot.tracker.remove_tip(commit=True)
    deck.get_resource("plate").rotate(z=90)
    deck.get_resource("x_arm").location = Coordinate(512.25, 0, 250)
    store = ResourceStore.in_memory()
    await store.commands.create_resources(
      spb.CreateResourcesRequest(
        resources=[spb.CreateResource(definition=definition_from_resource(deck))]
      )
    )
    handle = await store.get(deck.name)
    ours = await golden.snapshot_store(store, handle)
    theirs = golden.snapshot_resources(deck)
    self.assertEqual(golden.to_json(ours), golden.to_json(theirs))
    entry = next(e for e in theirs if e["name"] == "plate_well_A1")
    self.assertEqual(entry["volume"], 50)
    self.assertFalse(any(e["parent"] == "tips_tipspot_A1" for e in theirs))
    await store.close()


class FastSnapshotTests(unittest.TestCase):
  def test_the_tree_read_directly_is_what_its_definition_says(self):
    for scene in build_all():
      with self.subTest(scene=scene.name):
        root = scene.root
        self.assertEqual(
          golden.to_json(golden.snapshot_resources(root)),
          golden.to_json(golden.snapshot_definition(definition_from_resource(root))),
        )


class FileTests(unittest.TestCase):
  def test_a_file_is_written_when_updating_and_checked_otherwise(self):
    with tempfile.TemporaryDirectory() as directory:
      path = pathlib.Path(directory) / "golden" / "scenario.json"
      with mock.patch.dict(os.environ, {golden.UPDATE_VARIABLE: ""}):
        with self.assertRaises(AssertionError):
          golden.check_golden(self, path, {"sent": ["a"]})
      with mock.patch.dict(os.environ, {golden.UPDATE_VARIABLE: "1"}):
        golden.check_golden(self, path, {"sent": ["a"], "x": 0.1 + 0.2})
      with mock.patch.dict(os.environ, {golden.UPDATE_VARIABLE: ""}):
        golden.check_golden(self, path, {"sent": ["a"], "x": 0.3})
        with self.assertRaises(AssertionError):
          golden.check_golden(self, path, {"sent": ["a", "b"], "x": 0.3})


if __name__ == "__main__":
  unittest.main()
