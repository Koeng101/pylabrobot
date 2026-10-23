"""What the Opentrons drivers read from the resource store, as plain data.

A command reads what it needs in one `GetResources` (a resource, its subtree, its ancestors) and,
where it needs places and sizes, one `ResolveGeometry` with a query per item, then plans from
these values. Nothing here changes the store.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Protocol, Sequence, Tuple, Union

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import (
  HasTipError,
  NoTipError,
  TooLittleLiquidError,
  TooLittleVolumeError,
)
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.tree import to_coordinate, to_rotation
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

K = pb.ResourceKind

TOOL_KINDS = frozenset({K.RESOURCE_KIND_TIP, K.RESOURCE_KIND_HEAD_TOOL})
CONTAINER_KINDS = frozenset(
  {
    K.RESOURCE_KIND_CONTAINER,
    K.RESOURCE_KIND_WELL,
    K.RESOURCE_KIND_TROUGH,
    K.RESOURCE_KIND_TUBE,
    K.RESOURCE_KIND_PETRI_DISH,
    K.RESOURCE_KIND_TRASH,
  }
)
ITEMIZED_KINDS = frozenset(
  {K.RESOURCE_KIND_PLATE, K.RESOURCE_KIND_TIP_RACK, K.RESOURCE_KIND_TUBE_RACK}
)

Ref = Union[handles.Resource, bytes]


class Identified(Protocol):
  """Anything naming a resource in the store: a handle, or `Named`."""

  @property
  def id(self) -> bytes: ...

  @property
  def name(self) -> str: ...


@dataclass(frozen=True)
class Named:
  """A resource by its id and name, as a read returned it."""

  id: bytes
  name: str

  @staticmethod
  def of(node: pb.ResourceNode) -> "Named":
    return Named(node.id, node.attributes.name)


def ref_of(resource: Ref) -> pb.ResourceRef:
  """A reference to a resource given by its handle or its id."""
  return pb.ResourceRef(id=resource if isinstance(resource, bytes) else resource.id)


def id_of(resource: Ref) -> bytes:
  return resource if isinstance(resource, bytes) else resource.id


def anchor(x: str = "l", y: str = "f", z: str = "b") -> pb.Anchor:
  return handles.anchor(x, y, z)


class Tree:
  """The nodes one read returned, by id: each with its parent and children, as far as read."""

  def __init__(self, nodes: Sequence[pb.ResourceNode]):
    self.nodes: Dict[bytes, pb.ResourceNode] = {}
    for node in nodes:
      self.nodes.setdefault(node.id, node)

  def __contains__(self, resource_id: bytes) -> bool:
    return resource_id in self.nodes

  def node(self, resource: Ref) -> pb.ResourceNode:
    return self.nodes[id_of(resource)]

  def parent(self, node: pb.ResourceNode) -> Optional[pb.ResourceNode]:
    """Its parent, when it has one and it was read."""
    return self.nodes.get(node.parent_id) if node.parent_id else None

  def children(self, node: pb.ResourceNode) -> List[pb.ResourceNode]:
    """Its children that were read, in order."""
    return [self.nodes[i] for i in node.child_ids if i in self.nodes]

  def walk(self, node: pb.ResourceNode) -> Iterator[pb.ResourceNode]:
    """It and everything under it that was read, each before its children."""
    yield node
    for child in self.children(node):
      yield from self.walk(child)

  def tool(self, node: pb.ResourceNode) -> Optional[pb.ResourceNode]:
    """The tip or tool a spot or shaft holds, when it holds one."""
    return next((c for c in self.children(node) if c.attributes.kind in TOOL_KINDS), None)

  def ancestors(self, node: pb.ResourceNode) -> List[pb.ResourceNode]:
    """Its parent up to its root, as far as read."""
    found = []
    current = self.parent(node)
    while current is not None:
      found.append(current)
      current = self.parent(current)
    return found


async def read(
  store: ResourceStore,
  resources: Sequence[Ref],
  depth: int = 0,
  ancestors: bool = False,
) -> Tree:
  """Resources, `depth` below each (-1 for everything), and their ancestors when asked: one
  `GetResources`."""
  response = await store.commands.get_resources(
    spb.GetResourcesRequest(
      resources=[ref_of(resource) for resource in resources], depth=depth, ancestors=ancestors
    )
  )
  return Tree(response.nodes)


async def locate(
  store: ResourceStore,
  queries: Sequence[Tuple[Ref, Sequence[pb.Anchor]]],
  frame: Optional[Ref] = None,
) -> List[spb.Geometry]:
  """Where each resource's anchors are in `frame` (absolute when unset), its size once turned and
  its rotation: one `ResolveGeometry`.

  Raises:
    StoreError: A query the store could not answer.
  """
  request = spb.ResolveGeometryRequest()
  for resource, anchors in queries:
    query = request.queries.add(resource=ref_of(resource), anchors=anchors)
    if frame is not None:
      query.frame.CopyFrom(ref_of(frame))
  response = await store.commands.resolve_geometry(request)
  for result in response.results:
    if result.HasField("issue"):
      raise StoreError(result.issue.problem, result.issue.message)
  return list(response.results)


async def highest_point(store: ResourceStore, resource: Ref) -> float:
  """The highest point of a resource and everything on it; a deck's own top does not count."""
  (geometry,) = await locate(store, [(resource, ())])
  return geometry.highest_point


def coordinate(vector: pb.Vec3) -> Coordinate:
  return to_coordinate(vector)


def rotation(message: pb.Rotation) -> Rotation:
  return to_rotation(message)


def size_of(node: pb.ResourceNode) -> Coordinate:
  return to_coordinate(node.attributes.size)


def location_of(node: pb.ResourceNode) -> Optional[Coordinate]:
  attributes = node.attributes
  return to_coordinate(attributes.location) if attributes.HasField("location") else None


def tracks_tips(spot: pb.ResourceNode) -> bool:
  """Whether a spot gives up and takes back tips, as the store has it."""
  state = spot.state
  return not state.HasField("tip_tracking_enabled") or state.tip_tracking_enabled


def tracks_volume(node: pb.ResourceNode) -> bool:
  return node.state.HasField("volume") and node.state.volume.tracking_enabled


# -- liquid --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Liquid:
  """What a container or tip holds and can take, as one command reads it.

  Attributes:
    id: Its id in the store.
    name: Its name.
    volume: What it holds, counting staged changes.
    capacity: What it holds at most.
    tracked: Whether its volume is tracked.
  """

  id: bytes
  name: str
  volume: float
  capacity: float
  tracked: bool

  @staticmethod
  def of(node: pb.ResourceNode) -> Liquid:
    attributes = node.attributes
    capacity = (
      attributes.tip.maximal_volume
      if attributes.kind == K.RESOURCE_KIND_TIP
      else attributes.container.max_volume
    )
    return Liquid(
      id=node.id,
      name=attributes.name,
      volume=node.state.volume.pending_volume,
      capacity=capacity,
      tracked=tracks_volume(node),
    )


# -- tips ----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TipFacts:
  """A tip, mounted or in its spot, or one a spot makes.

  Attributes:
    id: Its id in the store; empty for a tip a spot would make.
    name: Its name.
    model: Its model.
    size: Its size along its own axes.
    fitting_depth: How far it overlaps the shaft it is mounted on.
    maximal_volume: What it holds at most.
    volume: What it holds, counting staged changes.
    tracked: Whether its volume is tracked.
  """

  id: bytes
  name: str
  model: str
  size: Coordinate
  fitting_depth: float
  maximal_volume: float
  volume: float = 0.0
  tracked: bool = True

  @staticmethod
  def of_attributes(
    attributes: pb.ResourceAttributes, node: Optional[pb.ResourceNode] = None
  ) -> TipFacts:
    return TipFacts(
      id=node.id if node is not None else b"",
      name=attributes.name,
      model=attributes.model,
      size=to_coordinate(attributes.size),
      fitting_depth=attributes.head_tool.fitting_depth,
      maximal_volume=attributes.tip.maximal_volume,
      volume=node.state.volume.pending_volume if node is not None else 0.0,
      tracked=tracks_volume(node) if node is not None else True,
    )

  @staticmethod
  def of(node: pb.ResourceNode) -> TipFacts:
    return TipFacts.of_attributes(node.attributes, node)

  @property
  def liquid(self) -> Liquid:
    return Liquid(self.id, self.name, self.volume, self.maximal_volume, self.tracked)


# -- labware -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ItemFacts:
  """An item of a labware: a well or a tip spot.

  Attributes:
    id: Its id in the store.
    name: Its name.
    identifier: Its identifier in the labware, "A1".
    kind: What it is.
    location: Where it is in the labware.
    size: Its size along its own axes.
    absolute_size: Its size once turned, along its root's axes.
    absolute_rotation: How it is turned, along its root's axes.
    container: A well's container spec.
    volume: What a well holds, when it is a container.
    tip: The tip a spot holds, or None.
    prototype: The tip a spot makes, when it says.
    has_tip: Whether a spot holds a tip.
    tracks_tips: Whether a spot gives up and takes back tips.
  """

  id: bytes
  name: str
  identifier: str
  kind: int
  location: Coordinate
  size: Coordinate
  absolute_size: Coordinate
  absolute_rotation: Rotation
  container: Optional[pb.ContainerSpec]
  volume: Optional[Liquid]
  tip: Optional[TipFacts]
  prototype: Optional[TipFacts]
  has_tip: bool
  tracks_tips: bool


@dataclass(frozen=True)
class LabwareFacts:
  """A labware and its items, as a command reads them.

  Attributes:
    id: Its id in the store.
    name: Its name.
    kind: What it is.
    type_name: The class it is built as.
    model: Its model.
    size: Its size along its own axes.
    absolute_size: Its size once turned, along its root's axes.
    absolute_rotation: How it is turned, along its root's axes.
    num_items_x: Its columns; 0 for a resource without items.
    num_items_y: Its rows; 0 for a resource without items.
    items: Its items, column-major.
    container: A container's spec.
    volume: What a container holds.
    parent_id: What it is in.
  """

  id: bytes
  name: str
  kind: int
  type_name: str
  model: str
  size: Coordinate
  absolute_size: Coordinate
  absolute_rotation: Rotation
  num_items_x: int
  num_items_y: int
  items: Tuple[ItemFacts, ...]
  container: Optional[pb.ContainerSpec]
  volume: Optional[Liquid]
  parent_id: bytes

  def item(self, identifier: str) -> ItemFacts:
    """An item by identifier.

    Raises:
      IndexError: It has no such item.
    """
    for item in self.items:
      if item.identifier == identifier:
        return item
    raise IndexError(f"'{self.name}' has no item '{identifier}'")

  def index(self, item_id: bytes) -> int:
    return next(i for i, item in enumerate(self.items) if item.id == item_id)


def _item_facts(tree: Tree, node: pb.ResourceNode, geometry: spb.Geometry) -> ItemFacts:
  attributes = node.attributes
  tip_node = tree.tool(node)
  prototype: Optional[TipFacts] = None
  if attributes.HasField("tip_spot") and attributes.tip_spot.HasField("prototype_tip"):
    prototype = TipFacts.of_attributes(attributes.tip_spot.prototype_tip)
  is_container = attributes.kind in CONTAINER_KINDS
  return ItemFacts(
    id=node.id,
    name=attributes.name,
    identifier=attributes.identifier,
    kind=attributes.kind,
    location=location_of(node) or Coordinate.zero(),
    size=size_of(node),
    absolute_size=to_coordinate(geometry.absolute_size),
    absolute_rotation=to_rotation(geometry.absolute_rotation),
    container=attributes.container if is_container else None,
    volume=Liquid.of(node) if is_container else None,
    tip=TipFacts.of(tip_node) if tip_node is not None else None,
    prototype=prototype,
    has_tip=tip_node is not None,
    tracks_tips=tracks_tips(node),
  )


async def read_labware(store: ResourceStore, labware: Ref) -> LabwareFacts:
  """A labware with everything in it and the size and rotation of each, in two calls."""
  tree = await read(store, [labware], depth=2)
  node = tree.node(labware)
  items = (
    [child for child in tree.children(node) if child.attributes.identifier]
    if node.attributes.kind in ITEMIZED_KINDS
    else []
  )
  geometries = await locate(store, [(each.id, ()) for each in [node, *items]])
  attributes = node.attributes
  is_container = attributes.kind in CONTAINER_KINDS
  return LabwareFacts(
    id=node.id,
    name=attributes.name,
    kind=attributes.kind,
    type_name=attributes.type_name,
    model=attributes.model,
    size=size_of(node),
    absolute_size=to_coordinate(geometries[0].absolute_size),
    absolute_rotation=to_rotation(geometries[0].absolute_rotation),
    num_items_x=attributes.itemized.num_items_x,
    num_items_y=attributes.itemized.num_items_y,
    items=tuple(_item_facts(tree, item, geometry) for item, geometry in zip(items, geometries[1:])),
    container=attributes.container if is_container else None,
    volume=Liquid.of(node) if is_container else None,
    parent_id=node.parent_id,
  )


# -- what the store refuses ----------------------------------------------------------------------


def tracking_error(error: StoreError) -> Exception:
  """The exception PLR raises for a tracking problem the store found; the error itself
  otherwise."""
  kinds = {
    pb.PROBLEM_HAS_TIP: HasTipError,
    pb.PROBLEM_NO_TIP: NoTipError,
    pb.PROBLEM_TOO_LITTLE_LIQUID: TooLittleLiquidError,
    pb.PROBLEM_TOO_LITTLE_VOLUME: TooLittleVolumeError,
  }
  kind = kinds.get(error.problem)
  return kind(str(error)) if kind is not None else error


async def resolve(
  store: ResourceStore,
  operation: pb.Operation,
  succeeded: bool,
  items: Optional[Sequence[int]] = None,
) -> None:
  """Commit or roll back items of a staged operation; every item when none are named."""
  indices = range(len(operation.items)) if items is None else items
  outcomes = [spb.ItemOutcome(item=i, succeeded=succeeded) for i in indices]
  if not outcomes:
    return
  await store.commands.resolve_operation(
    spb.ResolveOperationRequest(
      lock_tokens=store.lock_tokens, operation_id=operation.id, outcomes=outcomes
    )
  )
