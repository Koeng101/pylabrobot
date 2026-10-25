"""PLR's labware as model files: each is what its factory builds, and nothing else is there."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import unittest
import warnings
from typing import Set

from pylabrobot.resources import Coordinate, Plate, Well, create_ordered_items_2d
from pylabrobot.resources.store import library
from pylabrobot.resources.store.definitions import definition_from_resource
from pylabrobot.resources.store.models import compact_grids, expand_grids, same_definitions
from pylabrobot.resources.store.tree import to_coordinate
from pylabrobot.resources.store.v1 import types_pb2 as pb

SHARDS = 4


class ModelFileTests(unittest.TestCase):
  """Every factory's model file holds what the factory builds."""

  def check_shard(self, shard: int) -> None:
    """One of `SHARDS` shares of the labware, so test runners can spread them over cores."""
    for qualified, factory in library.labware_factories()[shard::SHARDS]:
      with self.subTest(labware=qualified):
        path = library.model_path(qualified)
        self.assertTrue(path.exists(), f"{path} is missing: run the library module to write it")
        self.assertEqual(path.read_text(), library.to_json(library.model_from_factory(factory)))
        with warnings.catch_warnings():
          warnings.simplefilter("ignore")
          built = definition_from_resource(factory(name="{name}"))
        expanded = library.get_model(factory.__name__).definition
        expand_grids(expanded)
        self.assertTrue(same_definitions(expanded, built), "the model makes something else")

  def test_shard_0(self):
    self.check_shard(0)

  def test_shard_1(self):
    self.check_shard(1)

  def test_shard_2(self):
    self.check_shard(2)

  def test_shard_3(self):
    self.check_shard(3)

  def test_every_file_has_its_factory(self):
    # By name, without building: a few factories build only with the network.
    for name in library.model_names():
      with self.subTest(model=name):
        path = library.get_model_path(name)
        package = ".".join(("pylabrobot", "resources") + path.relative_to(library.ROOT).parts[:-2])
        functions: Set[str] = set()
        for info in pkgutil.iter_modules([str(path.parent.parent)], f"{package}."):
          if not info.ispkg and not info.name.endswith("_tests"):
            module = importlib.import_module(info.name)
            functions.update(n for n, _ in inspect.getmembers(module, inspect.isfunction))
        self.assertIn(name, functions, f"{path} has no factory beside it")

  def test_aliases_are_the_deprecated_factories(self):
    self.assertEqual(library.aliases(), library.alias_targets())
    for alias, target in library.aliases().items():
      self.assertEqual(library.get_model(alias).name, target)


class GridTests(unittest.TestCase):
  """Items given once as a grid are made as `create_ordered_items_2d` makes them."""

  def plate(self, name: str, item_dy: float = 9.0) -> Plate:
    wells = create_ordered_items_2d(
      Well,
      num_items_x=3,
      num_items_y=27,
      dx=10.5,
      dy=7.25,
      dz=1.0,
      item_dx=9.0,
      item_dy=item_dy,
      size_x=6,
      size_y=6,
      size_z=10,
      name_prefix=name,
    )
    return Plate(name, size_x=127, size_y=300, size_z=14, ordered_items=wells)

  def test_a_grid_makes_the_items_it_replaced(self):
    definition = definition_from_resource(self.plate("{name}"))
    compact = pb.ResourceDefinition()
    compact.CopyFrom(definition)
    compact_grids(compact)
    grid = compact.attributes.itemized.grid
    self.assertEqual(len(compact.children), 0)
    self.assertEqual(grid.item.attributes.name, "{name}_well_{identifier}")
    self.assertEqual((grid.offset.x, grid.offset.y, grid.offset.z), (10.5, 7.25, 1.0))
    expand_grids(compact)
    self.assertTrue(same_definitions(compact, definition))
    # Rows past "Z" are "AA" on, and row "A" is at the back.
    last = compact.children[26].attributes
    self.assertEqual((last.identifier, last.name), ("AA1", "{name}_well_AA1"))
    self.assertEqual(to_coordinate(last.location), Coordinate(10.5, 7.25, 1.0))
    self.assertEqual(to_coordinate(compact.children[0].attributes.location).y, 7.25 + 26 * 9.0)

  def test_items_not_evenly_spaced_stay_listed(self):
    plate = self.plate("{name}")
    plate.get_well("B2").location = Coordinate(20.0, 200.0, 1.0)
    definition = definition_from_resource(plate)
    compact_grids(definition)
    self.assertFalse(definition.attributes.itemized.HasField("grid"))
    self.assertEqual(len(definition.children), 81)

  def test_items_not_alike_stay_listed(self):
    plate = self.plate("{name}")
    plate.get_well("C3").max_volume = 1.0
    definition = definition_from_resource(plate)
    compact_grids(definition)
    self.assertFalse(definition.attributes.itemized.HasField("grid"))


if __name__ == "__main__":
  unittest.main()
