"""The resource tree as a store holds it in memory: nodes linked to their parents and children."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store.v1 import types_pb2 as pb


def to_coordinate(vector: pb.Vec3) -> Coordinate:
  """A protocol vector as a coordinate."""
  return Coordinate(vector.x, vector.y, vector.z)


def to_vec3(coordinate: Coordinate) -> pb.Vec3:
  """A coordinate as a protocol vector."""
  return pb.Vec3(x=coordinate.x, y=coordinate.y, z=coordinate.z)


def to_rotation(rotation: pb.Rotation) -> Rotation:
  """A protocol rotation as a rotation."""
  return Rotation(x=rotation.x, y=rotation.y, z=rotation.z)


def to_rotation_message(rotation: Rotation) -> pb.Rotation:
  """A rotation as a protocol rotation, by its Euler angles."""
  return pb.Rotation(x=rotation.x, y=rotation.y, z=rotation.z)


@dataclass(eq=False)
class Node:
  """One resource in a tree: what it is, its state, and where it hangs.

  Compared by identity: two nodes are the same only if they are the same object.

  Attributes:
    attributes: what it is, where it is relative to its parent, and its kind's spec.
    state: its volume, tracking flags, jaw width and tip count.
    parent: what it hangs from, or None for a root.
    children: what hangs from it, in order.
    id: the store's id for it; empty until a store gives it one.
  """

  attributes: pb.ResourceAttributes
  state: pb.ResourceState = field(default_factory=pb.ResourceState)
  parent: Optional[Node] = None
  children: List[Node] = field(default_factory=list)
  id: bytes = b""

  @property
  def name(self) -> str:
    return self.attributes.name

  @property
  def kind(self) -> pb.ResourceKind:
    return self.attributes.kind

  @property
  def location(self) -> Optional[Coordinate]:
    """Where it is relative to its parent, or None where that is unknown."""
    if not self.attributes.HasField("location"):
      return None
    return to_coordinate(self.attributes.location)

  @property
  def rotation(self) -> Rotation:
    return to_rotation(self.attributes.rotation)

  def walk(self) -> Iterator[Node]:
    """This node and everything under it, depth first, each before its children."""
    yield self
    for child in self.children:
      yield from child.walk()

  def all_children(self) -> List[Node]:
    """Everything under this node, in `Resource.get_all_children`'s order: its children first,
    then what is under each of them in turn."""
    found = list(self.children)
    for child in self.children:
      found += child.all_children()
    return found

  def root(self) -> Node:
    node = self
    while node.parent is not None:
      node = node.parent
    return node

  def find(self, name: str) -> Optional[Node]:
    """The node called `name` in this subtree, or None."""
    return next((node for node in self.walk() if node.name == name), None)


def build_tree(definition: pb.ResourceDefinition, parent: Optional[Node] = None) -> Node:
  """Nodes for a definition and everything in it, hung from `parent` when given.

  The definition is copied, so the nodes can change without changing it.
  """
  attributes = pb.ResourceAttributes()
  attributes.CopyFrom(definition.attributes)
  state = pb.ResourceState()
  if definition.HasField("initial_state"):
    state.CopyFrom(definition.initial_state)
  node = Node(attributes=attributes, state=state, parent=parent)
  if parent is not None:
    parent.children.append(node)
  for child in definition.children:
    build_tree(child, parent=node)
  return node


def to_definition(node: Node) -> pb.ResourceDefinition:
  """The definition of a node and everything under it, as it is now."""
  definition = pb.ResourceDefinition()
  definition.attributes.CopyFrom(node.attributes)
  if node.state.ByteSize() > 0:
    definition.initial_state.CopyFrom(node.state)
  definition.children.extend(to_definition(child) for child in node.children)
  return definition


def copy_tree(node: Node) -> Node:
  """A copy of a node and everything under it, belonging to no tree."""
  return build_tree(to_definition(node))
