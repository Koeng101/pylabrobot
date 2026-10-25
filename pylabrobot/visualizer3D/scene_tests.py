"""The flattener: what it emits, and that reusing derived models changes nothing about it."""

import json
import unittest
from typing import List

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.visualizer.mirror import TreeMirror
from pylabrobot.visualizer.nodes import serialize_node
from pylabrobot.visualizer3D.facility import facility
from pylabrobot.visualizer3D.scene import (
  Scene,
  _model_of,
  build_scene,
  pack_state,
  state_signature,
)


def canonical(scene: Scene) -> str:
  """The scene as it is sent, in a key order that lets two of them be compared byte for byte."""
  return json.dumps(scene.serialize(), sort_keys=True)


async def mirror_of(root: handles.Resource) -> TreeMirror:
  """The tree under `root`, read once."""
  tree = TreeMirror(root)
  await tree.load()
  return tree


async def facility_with(store: ResourceStore, plates: int) -> handles.Resource:
  """A facility holding `plates` identical plates, side by side."""
  root = await store.create(facility("facility", 10_000, 10_000, 500), name="facility")
  for i in range(plates):
    await store.create(
      "cor_96_wellplate_360uL_Fb",
      name=f"plate_{i}",
      parent=root,
      location=Coordinate(150 * i, 0, 0),
    )
  return root


async def facility_with_a_full_rack(store: ResourceStore) -> handles.Resource:
  """A facility holding a tip rack full of tips: a tip spot serializes without its tip."""
  root = await store.create(facility("facility", 1000, 1000, 500), name="facility")
  await store.create(
    "hamilton_96_tiprack_1000uL", name="rack", parent=root, location=Coordinate(100, 100, 0)
  )
  return root


class SceneTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.store = ResourceStore.in_memory()

  async def asyncTearDown(self) -> None:
    await self.store.close()

  async def test_emits_parents_before_children(self):
    """A client resolves world transforms in one forward pass, which only works in this order."""
    scene = build_scene(await mirror_of(await facility_with(self.store, 2)))
    for index, parent in enumerate(scene.parent_of_instance):
      self.assertLess(parent, index, f"instance {index} is emitted before its parent")

  async def test_identical_resources_share_one_model(self):
    """The whole point of the split: geometry is sent once, however many stand on it."""
    one = build_scene(await mirror_of(await facility_with(self.store, 1)))
    many = build_scene(await mirror_of(await facility_with(ResourceStore.in_memory(), 20)))
    self.assertEqual(len(many.models), len(one.models))
    self.assertEqual(len(many.names), 1 + 20 * 97)  # facility, then plate and its 96 wells

  async def test_a_move_is_seen_through_reused_models(self):
    """Skipping the derive must not change a byte of what is sent: a model is reused, a position
    never is, so moving something must still show up."""
    root = await facility_with(self.store, 3)
    tree = await mirror_of(root)
    first = build_scene(tree)
    names = frozenset(first.names)
    plate = await self.store.get("plate_0", root=root)
    await root.assign_child_resource(plate, location=Coordinate(999, 888, 0))
    await tree.load()
    warm = build_scene(tree, known=first.derived, known_names=names)
    self.assertEqual(canonical(warm), canonical(build_scene(tree)))
    self.assertIn(999.0, warm.transforms)

  async def test_a_racked_tip_hangs_from_its_collar(self):
    """A tip is placed where its spot put it."""
    root = await facility_with_a_full_rack(self.store)
    rack = await self.store.get("rack", root=root)
    assert isinstance(rack, handles.TipRack)
    tip = await rack.get_tip_spot("A1").get_tip()
    assert tip is not None
    location = await tip.get_location()
    assert location is not None

    scene = build_scene(await mirror_of(root))
    index = scene.names.index(tip.name)
    self.assertEqual(
      tuple(scene.transforms[6 * index : 6 * index + 3]), (location.x, location.y, location.z)
    )

  async def test_models_are_not_reused_when_the_names_change(self):
    """Whether a string counts as a reference depends on which names exist, so a changed tree
    invalidates what was derived from the old one."""
    root = await facility_with(self.store, 2)
    tree = await mirror_of(root)
    first = build_scene(tree)
    names = frozenset(first.names)
    # A plate's ordering links its wells by name: with A1 out of the tree, the plate is another.
    await (await self.store.get("plate_0_well_A1", root=root)).unassign()
    await tree.load()
    warm = build_scene(tree, known=first.derived, known_names=names)
    self.assertNotEqual(
      warm.derived["plate_0"], first.derived["plate_0"], "the model kept its link"
    )
    self.assertEqual(canonical(warm), canonical(build_scene(tree)))

  async def test_a_discard_reuses_the_models_that_do_not_link_to_it(self):
    """Any change of names threw every derived model away, so an assign or a discard cost the
    cold build. A model that holds no link is what it was, whichever names exist."""
    root = await facility_with(self.store, 2)
    box = await self.store.create(
      build.resource("box", Coordinate(10, 10, 10)),
      name="box",
      parent=root,
      location=Coordinate(900, 900, 0),
    )
    tree = await mirror_of(root)
    first = build_scene(tree)
    names = frozenset(first.names)
    await box.unassign()
    await tree.load()
    warm = build_scene(tree, known=first.derived, known_names=names)
    self.assertIs(warm.derived["plate_0_well_A1"], first.derived["plate_0_well_A1"])
    self.assertIsNot(warm.derived["plate_0"], first.derived["plate_0"])  # links its wells
    self.assertEqual(canonical(warm), canonical(build_scene(tree)))

  async def test_a_name_that_reappears_is_a_link_again(self):
    """A model derived while a name was gone holds no link to it; put back, it is a link."""
    root = await facility_with(self.store, 1)
    plate = await self.store.get("plate_0", root=root)
    well = await self.store.get("plate_0_well_A1", root=root)
    location = await well.get_location()
    await well.unassign()
    tree = await mirror_of(root)
    first = build_scene(tree)
    names = frozenset(first.names)
    self.assertNotIn("A1", first.derived["plate_0"]["ordering"])
    await plate.assign_child_resource(well, location=location, index=0)
    await tree.load()
    warm = build_scene(tree, known=first.derived, known_names=names)
    self.assertEqual(warm.derived["plate_0"]["ordering"]["A1"], "<resource>")
    self.assertEqual(canonical(warm), canonical(build_scene(tree)))

  async def test_a_model_is_the_resources_own_whatever_its_parent(self):
    """A model is what the resource itself says it is, a spot's tip and a plate's well alike."""
    root = await facility_with_a_full_rack(self.store)
    await self.store.create(
      "cor_96_wellplate_360uL_Fb", name="plate", parent=root, location=Coordinate(300, 100, 0)
    )
    tree = await mirror_of(root)
    scene = build_scene(tree)
    nodes = list(tree.walk())
    self.assertEqual(scene.names, [node.attributes.name for node in nodes])
    names = frozenset(scene.names)
    for node, model_index in zip(nodes, scene.model_of_instance):
      expected = _model_of(serialize_node(node, tree), names)
      model = scene.models[model_index]
      self.assertEqual({k: model[k] for k in expected}, expected, node.attributes.name)

  async def test_the_legacy_size_counts_one_node_per_resource(self):
    """The comparison lists every resource as a node, including the tip its spot serializes
    without."""
    tree = await mirror_of(await facility_with_a_full_rack(self.store))
    scene = build_scene(tree, measure_legacy=True)
    counted: List[str] = []

    def one_node_each(node) -> dict:
      counted.append(node.attributes.name)
      data = serialize_node(node, tree)
      data["children"] = [one_node_each(child) for child in tree.children(node)]
      return data

    self.assertEqual(scene.legacy_bytes, len(json.dumps(one_node_each(tree.node(tree.root_id)))))
    self.assertIn("rack_tipspot_A1#0", counted)


class PackStateTests(unittest.TestCase):
  def test_resources_that_differ_only_in_position_share_one_state(self):
    """A position rode inside the state, so two wells at the same volume were two states, and a
    plate of them that had moved once could never share anything again."""
    at = lambda x: {"x": x, "y": 0.0, "z": 0.0, "type": "Coordinate"}  # noqa: E731
    packed = pack_state(
      {
        "a": state_signature({"volume": 100.0, "location": at(1.0)}),
        "b": state_signature({"volume": 100.0, "location": at(2.0)}),
        "c": state_signature({"volume": 100.0}),
      }
    )
    self.assertEqual(len(packed["states"]), 1)
    self.assertEqual(packed["of"], {"a": 0, "b": 0, "c": 0})
    self.assertEqual(packed["locations"], {"a": at(1.0), "b": at(2.0)})
    self.assertNotIn("location", packed["states"][0])


if __name__ == "__main__":
  unittest.main()
