"""A store held in this process and called directly, `ResourceStore.in_process()`.

It answers the command API exactly as the same store does over Connect: every test of
`store_tests` and `handles_tests` runs against it here. What differs is that a request completes
without giving way to other tasks.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import List

from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.tests import handles_tests, store_tests
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb


class _InProcess:
  def make_store(self) -> ResourceStore:
    return ResourceStore.in_process()


class StoreInfoTests(_InProcess, store_tests.StoreInfoTests):
  pass


class TreeTests(_InProcess, store_tests.TreeTests):
  pass


class StackTests(_InProcess, store_tests.StackTests):
  pass


class ToolTests(_InProcess, store_tests.ToolTests):
  pass


class LiquidTests(_InProcess, store_tests.LiquidTests):
  pass


class PlaceTests(_InProcess, store_tests.PlaceTests):
  pass


class DeviceTests(_InProcess, store_tests.DeviceTests):
  pass


class LockTests(_InProcess, store_tests.LockTests):
  pass


class OperationTests(_InProcess, store_tests.OperationTests):
  pass


class WatchTests(_InProcess, store_tests.WatchTests):
  pass


class ReadingTests(_InProcess, handles_tests.ReadingTests):
  pass


class EventTests(_InProcess, handles_tests.EventTests):
  pass


class DeckTests(_InProcess, handles_tests.DeckTests):
  pass


class ChangingTests(_InProcess, handles_tests.ChangingTests):
  pass


class DirectTests(unittest.IsolatedAsyncioTestCase):
  """What being called directly changes."""

  async def test_a_request_does_not_give_way_to_other_tasks(self):
    store = ResourceStore.in_process()
    order: List[str] = []

    async def reads_twice() -> None:
      await store.roots()
      order.append("first read")
      await store.roots()
      order.append("second read")

    async def other() -> None:
      order.append("other task")

    await asyncio.gather(reads_twice(), other())
    self.assertEqual(order, ["first read", "second read", "other task"])

  async def test_a_refusal_is_a_store_error_with_its_problem(self):
    store = ResourceStore.in_process()
    with self.assertRaises(StoreError) as caught:
      await store.commands.get_resources(
        spb.GetResourcesRequest(resources=[pb.ResourceRef(name=pb.NameRef(name="nothing"))])
      )
    self.assertEqual(caught.exception.problem, pb.PROBLEM_NOT_FOUND)


if __name__ == "__main__":
  unittest.main()
