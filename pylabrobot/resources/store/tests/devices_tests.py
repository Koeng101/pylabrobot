"""A device's resources found by name, or created once; and refusals raised as PLR raises them."""

import unittest

from pylabrobot.resources import Coordinate
from pylabrobot.resources.errors import HasTipError, TooLittleLiquidError
from pylabrobot.resources.store import build, devices
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError, plr_error
from pylabrobot.resources.store.v1 import types_pb2 as pb


def body(name: str = "shaker", model: str = "shaker_model") -> pb.ResourceDefinition:
  return build.resource(
    name,
    Coordinate(10, 10, 10),
    kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
    model=model,
    holder=pb.HolderSpec(child_location=build.vec3(Coordinate.zero()), capacity=1),
  )


class FindOrCreateTests(unittest.IsolatedAsyncioTestCase):
  async def test_created_once_then_found(self):
    store = ResourceStore.in_memory()
    made = await devices.find_or_create(store, body())
    self.assertEqual(await devices.find_or_create(store, body()), made)
    self.assertEqual(await devices.find_or_create(store, body(), create=False), made)
    self.assertEqual(len(await store.roots()), 1)

  async def test_only_finding_refuses_what_is_not_there(self):
    store = ResourceStore.in_memory()
    with self.assertRaises(LookupError):
      await devices.find_or_create(store, body(), create=False)
    self.assertEqual(await store.roots(), [])

  async def test_a_resource_of_another_kind_or_model_is_not_taken_over(self):
    store = ResourceStore.in_memory()
    await store.create(build.resource("shaker", Coordinate(1, 1, 1)), name="shaker")
    with self.assertRaisesRegex(ValueError, "not the RESOURCE_KIND_RESOURCE_HOLDER"):
      await devices.find_or_create(store, body())
    other = ResourceStore.in_memory()
    await devices.find_or_create(other, body(model="another_model"))
    with self.assertRaisesRegex(ValueError, "of model 'another_model'"):
      await devices.find_or_create(other, body())


class PLRErrorTests(unittest.TestCase):
  def test_tracking_problems_become_plr_errors(self):
    error = StoreError(pb.PROBLEM_HAS_TIP, "'channel' already carries 'tip'")
    mapped = plr_error(error, otherwise=RuntimeError)
    self.assertIsInstance(mapped, HasTipError)
    self.assertEqual(str(mapped), "'channel' already carries 'tip'")
    self.assertIsInstance(
      plr_error(StoreError(pb.PROBLEM_TOO_LITTLE_LIQUID, "empty")), TooLittleLiquidError
    )

  def test_other_problems_become_the_given_class_or_stay(self):
    error = StoreError(pb.PROBLEM_CANNOT_DROP_HERE, "full")
    self.assertIs(plr_error(error), error)
    self.assertIsInstance(plr_error(error, otherwise=RuntimeError), RuntimeError)

  def test_a_store_error_is_a_value_error(self):
    self.assertIsInstance(StoreError(pb.PROBLEM_NAME_CONFLICT, "taken"), ValueError)


if __name__ == "__main__":
  unittest.main()
