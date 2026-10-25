"""Barcodes read checked against the store, and barcodes recorded once."""

import unittest
from typing import Any, Dict

from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.barcodes import (
  BarcodeMismatch,
  BarcodeMismatchError,
  barcodes_by_place,
  check_barcodes,
  find_barcode_mismatches,
  initialize_barcodes,
)
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb


def code(data: str) -> pb.Barcode:
  return pb.Barcode(data=data, symbology="DataMatrix", position_on_resource="bottom")


async def rack_with_tubes(store: ResourceStore, tubes: dict) -> handles.TubeRack:
  """A 2 x 1 rack of holders; a tube in each named position, with its barcode when given."""
  holder = build.resource(
    "rack_holder_{identifier}",
    Coordinate(9, 9, 40),
    kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
    holder=pb.HolderSpec(child_location=build.vec3(Coordinate.zero()), capacity=1),
  )
  rack = await store.create(
    build.resource(
      "rack",
      Coordinate(20, 10, 40),
      kind=pb.RESOURCE_KIND_TUBE_RACK,
      itemized=pb.ItemizedSpec(
        num_items_x=2,
        num_items_y=1,
        grid=pb.ItemGrid(item=holder, offset=build.vec3(Coordinate.zero()), item_dx=9, item_dy=9),
      ),
    ),
    name="rack",
  )
  assert isinstance(rack, handles.TubeRack)
  for position, barcode in tubes.items():
    extra: Dict[str, Any] = {} if barcode is None else {"barcode": code(barcode)}
    tube = build.resource(
      f"tube_{position}",
      Coordinate(8, 8, 40),
      kind=pb.RESOURCE_KIND_TUBE,
      container=pb.ContainerSpec(max_volume=1000),
      **extra,
    )
    await store.create(tube, name=f"tube_{position}", parent=rack.get_item(position))
  return rack


class CheckBarcodesTests(unittest.IsolatedAsyncioTestCase):
  async def test_codes_that_agree_pass_and_nothing_is_written(self):
    store = ResourceStore.in_memory()
    rack = await rack_with_tubes(store, {"A1": "111", "A2": None})
    await check_barcodes({rack.get_item("A1"): code("111"), rack.get_item("A2"): code("222")})
    tube = await store.get("tube_A2", root="rack")
    self.assertIsNone(await tube.get_barcode())

  async def test_each_disagreement_is_named(self):
    store = ResourceStore.in_memory()
    rack = await rack_with_tubes(store, {"A1": "111"})
    await rack.set_barcode(code("rack-1"))
    reads = {rack: code("rack-2"), rack.get_item("A1"): None, rack.get_item("A2"): code("333")}
    self.assertEqual(
      await find_barcode_mismatches(reads),
      [
        BarcodeMismatch("rack", "different", "rack-1", "rack-2"),
        BarcodeMismatch("rack_holder_A1", "missing", "111", None),
        BarcodeMismatch("rack_holder_A2", "unexpected", None, "333"),
      ],
    )
    with self.assertRaisesRegex(BarcodeMismatchError, "3 barcode"):
      await check_barcodes(reads)
    self.assertEqual((await rack.get_barcode()).data, "rack-1")  # type: ignore[union-attr]


class InitializeBarcodesTests(unittest.IsolatedAsyncioTestCase):
  async def test_unlabelled_resources_are_labelled_once(self):
    store = ResourceStore.in_memory()
    rack = await rack_with_tubes(store, {"A1": None, "A2": "222"})
    reads = {rack: code("rack-1"), rack.get_item("A1"): code("111"), rack.get_item("A2"): None}
    await initialize_barcodes(barcodes_by_place(reads))
    self.assertEqual((await rack.get_barcode()).data, "rack-1")  # type: ignore[union-attr]
    tube = await store.get("tube_A1", root="rack")
    self.assertEqual((await tube.get_barcode()).data, "111")  # type: ignore[union-attr]
    await initialize_barcodes({rack: code("rack-1")})  # the same again changes nothing

  async def test_a_different_barcode_is_never_written_over(self):
    store = ResourceStore.in_memory()
    rack = await rack_with_tubes(store, {"A1": None, "A2": "222"})
    with self.assertRaises(BarcodeMismatchError) as caught:
      await initialize_barcodes(
        {rack.get_item("A1"): code("111"), rack.get_item("A2"): code("999")}
      )
    self.assertEqual(
      caught.exception.mismatches, [BarcodeMismatch("rack_holder_A2", "different", "222", "999")]
    )
    tube = await store.get("tube_A1", root="rack")
    self.assertIsNone(await tube.get_barcode())  # all or none


if __name__ == "__main__":
  unittest.main()
