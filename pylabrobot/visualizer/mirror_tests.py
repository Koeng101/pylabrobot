"""A mirror follows the store: one batch per request, named as PLR's resource callbacks name it."""

import asyncio
import logging
import time
import unittest
from typing import List

from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.visualizer.mirror import Change, ChangeKind, TreeMirror


class TreeMirrorTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.store = ResourceStore.in_memory()
    self.root = await self.store.create(build.resource("root", Coordinate(500, 500, 100)), "root")
    self.holder = await self.store.create(
      build.resource("holder", Coordinate(200, 200, 10)),
      "holder",
      parent=self.root,
      location=Coordinate(250, 0, 0),
    )
    plate = await self.store.create(
      "cor_96_wellplate_360uL_Fb", name="plate", parent=self.root, location=Coordinate(0, 0, 0)
    )
    assert isinstance(plate, handles.Plate)
    self.plate = plate
    self.mirror = TreeMirror(self.root)
    self.batches: List[List[Change]] = []
    self.mirror.subscribe(self.batches.append)
    await self.mirror.start()

  async def asyncTearDown(self) -> None:
    await self.mirror.stop()
    await self.store.close()

  async def test_the_tree_is_read_once(self):
    self.assertEqual(len(self.mirror.nodes), 3 + 96)
    self.assertEqual(self.mirror.names()[:3], ["root", "holder", "plate"])
    self.assertEqual(self.mirror.parent_name(self.mirror.node(self.plate.id)), "root")

  async def test_one_request_is_one_batch(self):
    await self.plate.set_well_volumes([50] * 96)
    await self.mirror.caught_up()
    self.assertEqual(len(self.batches), 1)
    self.assertEqual([c.kind for c in self.batches[0]], [ChangeKind.STATE] * 96)
    well = self.mirror.node(self.plate.get_well("A1").id)
    self.assertEqual(well.state.volume.volume, 50)

  async def test_a_move_to_another_parent_is_unassigned_placed_and_assigned(self):
    await self.holder.assign_child_resource(self.plate, location=Coordinate(1, 1, 1))
    await self.mirror.caught_up()
    kinds = [(c.kind, c.name) for c in self.batches[-1] if c.name == "plate"]
    self.assertEqual(
      kinds,
      [
        (ChangeKind.UNASSIGNED, "plate"),
        (ChangeKind.STATE, "plate"),
        (ChangeKind.ASSIGNED, "plate"),
      ],
    )
    self.assertEqual(self.mirror.parent_name(self.mirror.node(self.plate.id)), "holder")

  async def test_what_arrives_brings_what_is_under_it(self):
    other = await self.store.create("cor_96_wellplate_360uL_Fb", name="other")
    await self.holder.assign_child_resource(other, location=Coordinate(0, 0, 0))
    await self.mirror.caught_up()
    assigned = [c for c in self.batches[-1] if c.kind == ChangeKind.ASSIGNED]
    self.assertEqual([c.name for c in assigned], ["other"])
    self.assertEqual(len(assigned[0].subtree), 97)
    self.assertIn(other.id, self.mirror.nodes)
    self.assertEqual(len(self.mirror.nodes), 3 + 96 + 97)

  async def test_what_leaves_takes_what_is_under_it(self):
    await self.plate.unassign()
    await self.mirror.caught_up()
    (change,) = self.batches[-1]
    self.assertEqual(
      (change.kind, change.name, len(change.subtree)), (ChangeKind.UNASSIGNED, "plate", 97)
    )
    self.assertEqual(len(self.mirror.nodes), 2)

  async def test_a_turn_is_a_state_change(self):
    await self.plate.rotate(z=90)
    await self.mirror.caught_up()
    self.assertEqual([(c.kind, c.name) for c in self.batches[-1]], [(ChangeKind.STATE, "plate")])

  async def test_a_change_elsewhere_in_the_store_is_not_waited_for(self):
    elsewhere = await self.store.create(
      build.resource("elsewhere", Coordinate(5, 5, 5)), "elsewhere"
    )
    await elsewhere.rotate(z=90)
    started = time.monotonic()
    await self.mirror.caught_up(timeout=10)
    self.assertLess(time.monotonic() - started, 5)

  async def test_stopping_logs_nothing(self):
    with self.assertLogs("pylabrobot.visualizer.mirror", level="DEBUG") as logs:
      logging.getLogger("pylabrobot.visualizer.mirror").debug("only this")
      await self.mirror.stop()
      await self.mirror.start()
      await self.mirror.stop()
      await asyncio.sleep(0.1)
    self.assertEqual(len(logs.records), 1)
