"""What a store does, over a tree held in memory: every command the protocol names.

`Engine` holds the tree, the models, the operations and the locks, and carries out each request
all or none: a request that fails part way is undone before its error is raised. Every change it
makes is recorded as an undo step, so a staged item rolls back by the same steps, and the store's
committed view is the tree with every unresolved item's steps undone.

The engine knows nothing of transport or persistence. After each request, `drain_changes` says
which resources changed or went, for a server to stream and a database to write.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from functools import partial
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Union

from google.protobuf.timestamp_pb2 import Timestamp

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import geometry as g
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.models import expand_grids
from pylabrobot.resources.store.tree import (
  Node,
  build_tree,
  to_coordinate,
  to_rotation_message,
  to_vec3,
)
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

K = pb.ResourceKind
API_VERSION = "v1"

_ANCHOR_BOTTOM = (pb.ANCHOR_X_CENTER, pb.ANCHOR_Y_CENTER, pb.ANCHOR_Z_BOTTOM)
_ANCHOR_CAVITY = (pb.ANCHOR_X_CENTER, pb.ANCHOR_Y_CENTER, pb.ANCHOR_Z_CAVITY_BOTTOM)
_ANCHOR_TOP = (pb.ANCHOR_X_CENTER, pb.ANCHOR_Y_CENTER, pb.ANCHOR_Z_TOP)

# A lid may be up to this much smaller than what it covers; `LID_UNDERSIZE_TOLERANCE` in PLR.
_LID_UNDERSIZE_TOLERANCE = 1.0
# Resources standing on a Hamilton deck that take no part in its collision check.
_DECK_PARTS = frozenset({"autoload_sled", "autoload_loading_tray"})


def _now() -> Timestamp:
  stamp = Timestamp()
  stamp.GetCurrentTime()
  return stamp


# -- undo steps ----------------------------------------------------------------------------------


@dataclass
class _Snapshot:
  """A resource's attributes and state as they were."""

  node: Node
  attributes: bytes
  state: bytes


@dataclass
class _Reattach:
  """Where a resource hung: its parent (None for a root) and its place among the children."""

  node: Node
  parent: Optional[Node]
  index: int


@dataclass
class _Created:
  """A resource that did not exist."""

  node: Node


@dataclass
class _Removed:
  """A resource that was taken out of the store, and where it hung."""

  node: Node
  parent: Optional[Node]
  index: int


@dataclass
class _Booked:
  """Liquid booked onto a resource's pending volume, not yet committed."""

  node: Node
  delta: float


Step = Union[_Snapshot, _Reattach, _Created, _Removed, _Booked]


@dataclass
class Transfer:
  """A staged item's liquid: what leaves the giver and enters the taker."""

  giver: Optional[Node]
  taker: Optional[Node]
  volume: float


@dataclass
class Item:
  steps: List[Step] = field(default_factory=list)
  transfers: List[Transfer] = field(default_factory=list)
  state: "pb.ItemState" = pb.ITEM_STATE_PENDING
  resolved_at: Optional[Timestamp] = None


@dataclass
class _Operation:
  id: bytes
  root: Node
  kind: str
  holder: str
  created_at: Timestamp
  items: List[Item]

  def message(self) -> pb.Operation:
    return pb.Operation(
      id=self.id,
      root_id=self.root.id,
      kind=self.kind,
      holder=self.holder,
      created_at=self.created_at,
      items=[
        pb.OperationItem(item=i, state=item.state, resolved_at=item.resolved_at)
        for i, item in enumerate(self.items)
      ],
    )

  def unresolved(self) -> bool:
    return any(item.state == pb.ITEM_STATE_PENDING for item in self.items)


@dataclass
class Changes:
  """What a request changed: resources as they are now, resources gone, operations touched."""

  updated: List[Node]
  created: List[Node]
  deleted: List[bytes]
  operations: List[pb.Operation]
  roots: Set[bytes]
  # For each updated node, what about it changed since the changes drained before.
  aspects: Dict[bytes, List[spb.ChangeAspect]]


_ALL_ASPECTS = (
  spb.CHANGE_ASPECT_PLACEMENT,
  spb.CHANGE_ASPECT_STATE,
  spb.CHANGE_ASPECT_ATTRIBUTES,
  spb.CHANGE_ASPECT_CHILDREN,
)


@dataclass(frozen=True)
class _View:
  """A node as a watcher last saw it, by aspect."""

  placement: tuple
  state: bytes
  attributes: bytes
  children: tuple

  def changed_since(self, before: _View) -> List[spb.ChangeAspect]:
    return [
      aspect
      for aspect, now, then in (
        (spb.CHANGE_ASPECT_PLACEMENT, self.placement, before.placement),
        (spb.CHANGE_ASPECT_STATE, self.state, before.state),
        (spb.CHANGE_ASPECT_ATTRIBUTES, self.attributes, before.attributes),
        (spb.CHANGE_ASPECT_CHILDREN, self.children, before.children),
      )
      if now != then
    ]


def _view(node: Node) -> _View:
  attributes = pb.ResourceAttributes()
  attributes.CopyFrom(node.attributes)
  location = attributes.location.SerializeToString() if attributes.HasField("location") else None
  rotation = attributes.rotation.SerializeToString(deterministic=True)
  attributes.ClearField("location")
  attributes.ClearField("rotation")
  parent = node.parent
  return _View(
    placement=(
      parent.id if parent is not None else b"",
      parent.children.index(node) if parent is not None else 0,
      location,
      rotation,
    ),
    state=node.state.SerializeToString(deterministic=True),
    attributes=attributes.SerializeToString(deterministic=True),
    children=tuple(child.id for child in node.children),
  )


class Engine:
  """A store's tree and everything done to it.

  Not safe to call from two threads at once: a server serializes requests.
  """

  def __init__(self, implementation: str = "memory"):
    self.implementation = implementation
    self.instance_id = uuid.uuid4().hex
    self.revision = 0
    self.nodes: Dict[bytes, Node] = {}
    self.roots: Dict[str, Node] = {}
    self.models: Dict[str, pb.ResourceModel] = {}
    self.locks: Dict[bytes, spb.Lock] = {}
    self.operations: Dict[bytes, _Operation] = {}
    self.revisions: Dict[bytes, int] = {}
    # Where each tool was taken from onto a shaft, to put it back.
    self.origins: Dict[bytes, bytes] = {}
    # Where in its origin a tool taken by name stood, to put it back there.
    self.origin_locations: Dict[bytes, Coordinate] = {}
    self._names: Dict[bytes, Dict[str, Node]] = {}
    self._journal: List[Step] = []
    self._touched: Dict[bytes, Node] = {}
    self._created: Dict[bytes, Node] = {}
    self._deleted: Dict[bytes, Node] = {}
    self._touched_operations: Dict[bytes, _Operation] = {}
    self._touched_roots: Set[bytes] = set()
    self._pending_index: Optional[Dict[bytes, List[bytes]]] = None
    # Each node as the changes drained last left it, to say what an update changed.
    self._published: Dict[bytes, _View] = {}

  # -- requests ----------------------------------------------------------------------------------

  def run(self, request: Callable[[], object]) -> object:
    """Carry out a request all or none: undone, and its error raised, if any step fails."""
    self._journal = []
    self._pending_index = None
    try:
      return request()
    except BaseException:
      self._undo(self._journal)
      self._touched.clear()
      self._created.clear()
      self._deleted.clear()
      self._touched_operations.clear()
      self._touched_roots.clear()
      raise
    finally:
      self._journal = []

  def drain_changes(self) -> Optional[Changes]:
    """What the last requests changed, once, and the revision moved on if anything did."""
    if not (self._touched or self._created or self._deleted or self._touched_operations):
      return None
    self.revision += 1
    created = [n for i, n in self._created.items() if i in self.nodes]
    updated = [n for i, n in self._touched.items() if i in self.nodes and i not in self._created]
    deleted = [i for i in self._deleted if i not in self.nodes]
    for node in created + updated:
      self.revisions[node.id] = self.revision
    for node_id in deleted:
      self.revisions.pop(node_id, None)
    aspects: Dict[bytes, List[spb.ChangeAspect]] = {}
    for node in updated:
      view = _view(node)
      before = self._published.get(node.id)
      aspects[node.id] = view.changed_since(before) if before is not None else list(_ALL_ASPECTS)
      self._published[node.id] = view
    for node in created:
      self._published[node.id] = _view(node)
    for node_id in deleted:
      self._published.pop(node_id, None)
    updated = [node for node in updated if aspects[node.id]]
    changes = Changes(
      aspects=aspects,
      updated=updated,
      created=created,
      deleted=deleted,
      operations=[op.message() for op in self._touched_operations.values()],
      roots=set(self._touched_roots),
    )
    self._touched.clear()
    self._created.clear()
    self._deleted.clear()
    self._touched_operations.clear()
    self._touched_roots.clear()
    return changes

  # -- low-level changes, each recorded so it can be undone -------------------------------------

  def _touch(self, node: Node) -> None:
    self._touched[node.id] = node
    self._touched_roots.add(node.root().id)

  def _snapshot(self, node: Node, steps: List[Step]) -> None:
    step = _Snapshot(node, node.attributes.SerializeToString(), node.state.SerializeToString())
    steps.append(step)
    self._journal.append(step)

  def set_attributes(self, node: Node, steps: List[Step], change: Callable[[], None]) -> None:
    self._snapshot(node, steps)
    change()
    self._touch(node)

  def _index_names(self, node: Node, root: Node) -> None:
    names = self._names.setdefault(root.id, {})
    for each in node.walk():
      names[each.name] = each

  def _unindex_names(self, node: Node, root: Node) -> None:
    names = self._names.get(root.id, {})
    for each in node.walk():
      if names.get(each.name) is each:
        del names[each.name]

  def _detach(self, node: Node) -> None:
    """Take a resource out of its parent, to be a root of its own."""
    parent = node.parent
    if parent is None:
      self.roots.pop(node.name, None)
      self._names.pop(node.id, None)
      return
    root = parent.root()
    self._unindex_names(node, root)
    parent.children.remove(node)
    node.parent = None
    self._touch(parent)

  def _attach(self, node: Node, parent: Optional[Node], index: Optional[int]) -> None:
    """Hang a detached resource from `parent` at `index`, or make it a root."""
    if parent is None:
      self.roots[node.name] = node
      self._names[node.id] = {}
      self._index_names(node, node)
      return
    position = len(parent.children) if index is None else min(index, len(parent.children))
    parent.children.insert(position, node)
    node.parent = parent
    self._index_names(node, parent.root())
    self._touch(parent)

  def move(
    self,
    node: Node,
    parent: Optional[Node],
    index: Optional[int],
    location: Optional[Coordinate],
    steps: List[Step],
  ) -> None:
    """Move a resource to `parent` at `location`, or make it a root with no location."""
    old_parent = node.parent
    old_index = old_parent.children.index(node) if old_parent is not None else 0
    step = _Reattach(node, old_parent, old_index)
    steps.append(step)
    self._journal.append(step)
    self._snapshot(node, steps)
    for each in node.walk():
      self._touched_roots.add(each.root().id)
    self._detach(node)
    if location is None:
      node.attributes.ClearField("location")
    else:
      node.attributes.location.CopyFrom(to_vec3(location))
    self._attach(node, parent, index)
    for each in node.walk():
      self._touch(each)

  def _create(self, node: Node, parent: Optional[Node], steps: List[Step]) -> None:
    """Give a new tree ids and put it in the store."""
    for each in node.walk():
      each.id = uuid.uuid4().bytes
      self.nodes[each.id] = each
      self._created[each.id] = each
    self._attach(node, parent, None)
    step = _Created(node)
    steps.append(step)
    self._journal.append(step)
    for each in node.walk():
      self._touch(each)

  def remove(self, node: Node, steps: List[Step]) -> None:
    """Take a resource and everything under it out of the store."""
    parent = node.parent
    index = parent.children.index(node) if parent is not None else 0
    step = _Removed(node, parent, index)
    steps.append(step)
    self._journal.append(step)
    for each in node.walk():
      self._touched_roots.add(each.root().id)
    self._detach(node)
    for each in node.walk():
      self.nodes.pop(each.id, None)
      self._deleted[each.id] = each
      self._touched.pop(each.id, None)

  def book(self, node: Node, delta: float, steps: List[Step]) -> None:
    """Liquid in or out of a resource's pending volume."""
    step = _Booked(node, delta)
    steps.append(step)
    self._journal.append(step)
    node.state.volume.pending_volume += delta
    self._touch(node)

  def _undo(self, steps: Sequence[Step]) -> None:
    for step in reversed(steps):
      if isinstance(step, _Snapshot):
        step.node.attributes.ParseFromString(step.attributes)
        step.node.state.ParseFromString(step.state)
        self._touch(step.node)
      elif isinstance(step, _Reattach):
        self._detach(step.node)
        self._attach(step.node, step.parent, step.index)
        for each in step.node.walk():
          self._touch(each)
      elif isinstance(step, _Created):
        self._detach(step.node)
        for each in step.node.walk():
          self.nodes.pop(each.id, None)
          self._deleted[each.id] = each
          self._created.pop(each.id, None)
          self._touched.pop(each.id, None)
      elif isinstance(step, _Removed):
        for each in step.node.walk():
          self.nodes[each.id] = each
          self._deleted.pop(each.id, None)
        self._attach(step.node, step.parent, step.index)
        for each in step.node.walk():
          self._touch(each)
      else:
        step.node.state.volume.pending_volume -= step.delta
        self._touch(step.node)

  # -- finding resources -------------------------------------------------------------------------

  def named(self, root: Node, name: str) -> Optional[Node]:
    """The resource called `name` in `root`'s tree, or None."""
    return self._names.get(root.id, {}).get(name)

  def resolve(self, ref: pb.ResourceRef) -> Node:
    """The resource a ref names.

    Raises:
      StoreError: Nothing by that id, name or identifier.
    """
    which = ref.WhichOneof("ref")
    if which == "id":
      node = self.nodes.get(ref.id)
      if node is None:
        raise StoreError(pb.PROBLEM_NOT_FOUND, f"no resource with id {ref.id.hex()}")
      return node
    if which == "name":
      if not ref.name.root:
        node = self.roots.get(ref.name.name)
        if node is None:
          raise StoreError(pb.PROBLEM_NOT_FOUND, f"no root named '{ref.name.name}'", ref.name.name)
        return node
      root = self.roots.get(ref.name.root)
      if root is None:
        raise StoreError(pb.PROBLEM_NOT_FOUND, f"no root named '{ref.name.root}'", ref.name.root)
      found = self._names.get(root.id, {}).get(ref.name.name)
      if found is None:
        raise StoreError(
          pb.PROBLEM_NOT_FOUND, f"no '{ref.name.name}' in '{ref.name.root}'", ref.name.name
        )
      return found
    if which == "item":
      parent = self.resolve(ref.item.parent)
      item = next(
        (c for c in parent.children if c.attributes.identifier == ref.item.identifier), None
      )
      if item is None:
        raise StoreError(
          pb.PROBLEM_NOT_FOUND, f"'{parent.name}' has no item '{ref.item.identifier}'", parent.name
        )
      return item
    raise StoreError(pb.PROBLEM_NOT_FOUND, "an empty resource reference")

  def resolve_optional(self, ref: pb.ResourceRef) -> Optional[Node]:
    return self.resolve(ref) if ref.WhichOneof("ref") is not None else None

  # -- what a store says about a resource --------------------------------------------------------

  def pending_operations(self, node: Node) -> List[bytes]:
    """The operations with an unresolved item that changes `node`."""
    if self._pending_index is None:
      index: Dict[bytes, List[bytes]] = {}
      for op in self.operations.values():
        for item in op.items:
          if item.state != pb.ITEM_STATE_PENDING:
            continue
          for step in item.steps:
            ids = index.setdefault(step.node.id, [])
            if op.id not in ids:
              ids.append(op.id)
      self._pending_index = index
    return list(self._pending_index.get(node.id, []))

  def node_message(self, node: Node) -> pb.ResourceNode:
    parent = node.parent
    return pb.ResourceNode(
      id=node.id,
      parent_id=parent.id if parent is not None else b"",
      root_id=node.root().id,
      index=parent.children.index(node) if parent is not None else 0,
      attributes=node.attributes,
      state=node.state,
      child_ids=[child.id for child in node.children],
      pending_operation_ids=self.pending_operations(node),
      revision=self.revisions.get(node.id, self.revision),
    )

  def info(self) -> spb.StoreInfo:
    return spb.StoreInfo(
      api_version=API_VERSION,
      implementation=self.implementation,
      implementation_version="1",
      instance_id=self.instance_id,
      revision=self.revision,
    )

  # -- locks -------------------------------------------------------------------------------------

  def lock_holder(self, root: Node) -> Optional[spb.Lock]:
    return self.locks.get(root.id)

  def acquire_lock(self, root: Node, holder: str) -> Optional[spb.Lock]:
    """A lock on `root` for `holder`, or None when someone else holds it."""
    if root.parent is not None:
      raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{root.name}' is not a root", root.name)
    if root.id in self.locks:
      return None
    lock = spb.Lock(token=uuid.uuid4().bytes, root_id=root.id, holder=holder, acquired_at=_now())
    self.locks[root.id] = lock
    return lock

  def release_lock(self, root: Node, token: bytes, force: bool) -> None:
    lock = self.locks.get(root.id)
    if lock is None:
      return
    if lock.token != token and not force:
      raise StoreError(
        pb.PROBLEM_LOCKED, f"'{root.name}' is locked by {lock.holder}, not this token", root.name
      )
    del self.locks[root.id]

  def check_locks(self, nodes: Iterable[Node], tokens: Sequence[bytes]) -> None:
    """Refuse a change to a root another holder has locked.

    Raises:
      StoreError: A root of one of `nodes` is locked by a token not among `tokens`.
    """
    for node in nodes:
      root = node.root()
      lock = self.locks.get(root.id)
      if lock is not None and lock.token not in tokens:
        raise StoreError(pb.PROBLEM_LOCKED, f"'{root.name}' is locked by {lock.holder}", root.name)

  # -- models ------------------------------------------------------------------------------------

  def put_model(self, model: pb.ResourceModel) -> pb.ResourceModel:
    if not model.name:
      raise StoreError(pb.PROBLEM_NOT_FOUND, "a model needs a name")
    expanded = pb.ResourceDefinition()
    expanded.CopyFrom(model.definition)
    expand_grids(expanded)
    _check_definition(expanded)
    self.models[model.name] = model
    return model

  def get_model(self, name: str) -> pb.ResourceModel:
    model = self.models.get(name)
    if model is None:
      raise StoreError(pb.PROBLEM_NOT_FOUND, f"no model named '{name}'", name)
    return model

  # -- building the tree -------------------------------------------------------------------------

  def create(self, request: spb.CreateResource, tokens: Sequence[bytes]) -> Node:
    """Create a resource from a model or a definition, its grids' items made, and assign it where
    asked.

    Raises:
      StoreError: An unknown model, a grid refused, a name already taken, or an assignment
        refused.
    """
    if request.WhichOneof("source") == "model":
      definition = pb.ResourceDefinition()
      definition.CopyFrom(self.get_model(request.model).definition)
    else:
      definition = pb.ResourceDefinition()
      definition.CopyFrom(request.definition)
    expand_grids(definition)
    _check_definition(definition)
    name = request.name or definition.attributes.name
    _rename(definition, name)
    node = build_tree(definition)
    names = [each.name for each in node.walk()]
    if len(set(names)) != len(names):
      duplicate = next(n for n in names if names.count(n) > 1)
      raise StoreError(
        pb.PROBLEM_NAME_CONFLICT, f"'{duplicate}' appears twice in '{name}'", duplicate
      )
    if name in self.roots:
      raise StoreError(pb.PROBLEM_NAME_CONFLICT, f"a root named '{name}' exists", name)
    steps: List[Step] = []
    self._create(node, None, steps)
    if request.HasField("assign"):
      assign = pb.AssignChild()
      assign.CopyFrom(request.assign)
      assign.child.id = node.id
      self.assign(assign, tokens, steps)
    return node

  def delete(self, node: Node, tokens: Sequence[bytes]) -> None:
    self.check_locks([node], tokens)
    self.remove(node, [])

  def check_names_fit(self, node: Node, parent: Optional[Node]) -> None:
    """Refuse a move that would give a tree two resources of one name.

    Raises:
      StoreError: A name in `node`'s subtree is already used in `parent`'s tree, or among roots.
    """
    if parent is None:
      other = self.roots.get(node.name)
      if other is not None and other is not node:
        raise StoreError(pb.PROBLEM_NAME_CONFLICT, f"a root named '{node.name}' exists", node.name)
      return
    root = parent.root()
    if node.root() is root:
      return
    names = self._names.get(root.id, {})
    for each in node.walk():
      if each.name in names:
        raise StoreError(
          pb.PROBLEM_NAME_CONFLICT, f"'{root.name}' already holds a '{each.name}'", each.name
        )

  def check_assignment(self, child: Node, parent: Node) -> None:
    """The rules a parent puts on what is assigned to it, as PLR's `assign_child_resource` has
    them.

    Raises:
      StoreError: The assignment is refused.
    """
    if g.is_in_subtree_of(parent, child):
      raise StoreError(
        pb.PROBLEM_CANNOT_DROP_HERE,
        f"'{child.name}' cannot go into '{parent.name}', which it holds",
        child.name,
      )
    holder = parent.attributes.holder
    if parent.kind in g.HOLDER_KINDS or holder.accepts or holder.capacity:
      if holder.accepts and child.kind not in holder.accepts:
        raise StoreError(
          pb.PROBLEM_CANNOT_DROP_HERE, f"'{parent.name}' does not take '{child.name}'", child.name
        )
      others = [c for c in parent.children if c is not child]
      if holder.capacity and len(others) >= holder.capacity:
        raise StoreError(
          pb.PROBLEM_CANNOT_DROP_HERE,
          f"'{parent.name}' already holds '{others[0].name}'",
          child.name,
        )
    if parent.kind == K.RESOURCE_KIND_PLATE_HOLDER:
      if child.kind == K.RESOURCE_KIND_PLATE and child.attributes.plate.plate_type != "skirted":
        raise StoreError(
          pb.PROBLEM_CANNOT_DROP_HERE,
          f"plate holder '{parent.name}' takes only skirted plates",
          child.name,
        )
      if child.kind == K.RESOURCE_KIND_RESOURCE_STACK:
        if child.attributes.stack.direction != pb.STACK_DIRECTION_Z or any(
          c.kind != K.RESOURCE_KIND_PLATE for c in child.children
        ):
          raise StoreError(
            pb.PROBLEM_CANNOT_DROP_HERE,
            f"plate holder '{parent.name}' takes only a stack of plates growing in z",
            child.name,
          )
    if parent.kind == K.RESOURCE_KIND_PLATE_ADAPTER and child.kind != K.RESOURCE_KIND_PLATE:
      raise StoreError(
        pb.PROBLEM_WRONG_KIND, f"only plates go onto plate adapter '{parent.name}'", child.name
      )
    if parent.kind == K.RESOURCE_KIND_TIP_SPOT and child.kind == K.RESOURCE_KIND_TIP:
      held = next((c for c in parent.children if c.kind == K.RESOURCE_KIND_TIP), None)
      if held is not None and held is not child:
        raise StoreError(pb.PROBLEM_HAS_TIP, f"'{parent.name}' already holds a tip", child.name)
    if parent.kind == K.RESOURCE_KIND_TIP_MOUNTING_SHAFT and child.kind in g.TOOL_KINDS:
      held = next((c for c in parent.children if c.kind in g.TOOL_KINDS), None)
      if held is not None and held is not child:
        raise StoreError(pb.PROBLEM_HAS_TIP, f"'{parent.name}' already carries a tool", child.name)
    if parent.kind in g.LIDDABLE_KINDS and child.kind == K.RESOURCE_KIND_LID:
      lid = g.lid_of(parent)
      if lid is not None and lid is not child:
        raise StoreError(pb.PROBLEM_LID_ON, f"'{parent.name}' already has a lid", child.name)
      lid_size, parent_size = g.size(child), g.size(parent)
      if (
        lid_size.x < parent_size.x - _LID_UNDERSIZE_TOLERANCE
        or lid_size.y < parent_size.y - _LID_UNDERSIZE_TOLERANCE
      ):
        raise StoreError(
          pb.PROBLEM_CANNOT_DROP_HERE,
          f"lid '{child.name}' is smaller than '{parent.name}' and cannot cover it",
          child.name,
        )

  def check_drop(self, child: Node, destination: Node) -> None:
    """What a destination takes when a resource is placed there, as PLR's
    `check_can_drop_resource_here` has it, on top of the assignment rules.

    Raises:
      StoreError: The destination refuses it.
    """
    if destination.kind == K.RESOURCE_KIND_PLATE and child.kind != K.RESOURCE_KIND_LID:
      raise StoreError(
        pb.PROBLEM_CANNOT_DROP_HERE,
        f"only a lid is placed onto plate '{destination.name}'",
        child.name,
      )
    if destination.kind in g.HOLDER_KINDS:
      others = [c for c in destination.children if c is not child]
      if others:
        raise StoreError(
          pb.PROBLEM_CANNOT_DROP_HERE,
          f"'{destination.name}' already holds '{others[0].name}'",
          child.name,
        )
    self.check_assignment(child, destination)

  def _check_deck_space(self, deck: Node, child: Node, location: Coordinate, track: bool) -> None:
    """A Hamilton deck refuses a resource that would overlap another on it, as PLR's does.

    Raises:
      StoreError: It overlaps, or does not fit at its track.
    """
    if not deck.attributes.deck.HasField("hamilton"):
      return
    if child.kind in (K.RESOURCE_KIND_TRASH,) or child.attributes.category in _DECK_PARTS:
      return
    if child.attributes.category == "core_grippers":
      return

    def footprint(node: Node) -> g.Size:
      s = g.size(node)
      corners = [
        Coordinate(x, y, z).rotated(node.rotation)
        for x in (0, s.x)
        for y in (0, s.y)
        for z in (0, s.z)
      ]
      xs, ys, zs = [c.x for c in corners], [c.y for c in corners], [c.z for c in corners]
      return g.Size(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    size_x, size_y, size_z = footprint(child)
    spec = deck.attributes.deck.hamilton
    if track and location.x + size_x > g.track_location(deck, spec.num_tracks + 1).x:
      raise StoreError(
        pb.PROBLEM_CANNOT_DROP_HERE,
        f"'{child.name}', {size_x} mm wide, does not fit at its track",
        child.name,
      )
    for other in deck.children:
      if other is child or other.attributes.category in _DECK_PARTS or other.location is None:
        continue
      at = other.location
      ox, oy, oz = footprint(other)
      x_overlap = at.x <= location.x < at.x + ox or at.x < location.x + size_x < at.x + ox
      y_overlap = at.y <= location.y < at.y + oy or at.y < location.y + size_y < at.y + oy
      z_overlap = at.z < location.z + size_z and location.z < at.z + oz
      if x_overlap and y_overlap and z_overlap:
        raise StoreError(
          pb.PROBLEM_CANNOT_DROP_HERE,
          f"{location} is already occupied by '{other.name}'",
          child.name,
        )

  def assign(self, request: pb.AssignChild, tokens: Sequence[bytes], steps: List[Step]) -> Node:
    """Put a resource into a parent: where asked, at a track, with no location, or where the
    parent seats it.

    Raises:
      StoreError: A rule of the parent refuses it, its names clash, or the parent does not seat
        children and no location is given.
    """
    child, parent = self.resolve(request.child), self.resolve(request.parent)
    self.check_locks([child, parent], tokens)
    self.check_assignment(child, parent)
    self.check_names_fit(child, parent)
    where = request.WhichOneof("where")
    location: Optional[Coordinate]
    if where == "no_location":
      location = None
    elif where == "location":
      location = to_coordinate(request.location)
    elif where == "track":
      if not parent.attributes.deck.HasField("hamilton"):
        raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{parent.name}' has no tracks", parent.name)
      num_tracks = parent.attributes.deck.hamilton.num_tracks
      if not -4 <= request.track <= num_tracks:
        raise StoreError(
          pb.PROBLEM_OUT_OF_RANGE, f"a track is from -4 to {num_tracks}, not {request.track}"
        )
      location = g.track_location(parent, request.track)
    else:
      seated = g.default_child_location(parent, child)
      if seated is None:
        raise StoreError(
          pb.PROBLEM_NO_LOCATION,
          f"'{parent.name}' does not seat what it is given: give '{child.name}' a location",
          child.name,
        )
      location = seated
    if parent.kind == K.RESOURCE_KIND_DECK and location is not None:
      self._check_deck_space(parent, child, location, track=where == "track")
    index = request.index if request.HasField("index") else None
    self.move(child, parent, index, location, steps)
    self.reseat_stack(parent, steps)
    return child

  def reseat_stack(self, stack: Node, steps: List[Step]) -> None:
    """Sink a stack on a plate holder's pedestal by the plate at its bottom."""
    holder = stack.parent
    if stack.kind != K.RESOURCE_KIND_RESOURCE_STACK or holder is None or not stack.children:
      return
    if holder.kind != K.RESOURCE_KIND_PLATE_HOLDER:
      return
    location = g.holder_child_location(holder, stack.children[0])
    self.set_attributes(stack, steps, lambda: stack.attributes.location.CopyFrom(to_vec3(location)))

  def unassign(self, node: Node, tokens: Sequence[bytes], steps: List[Step]) -> None:
    """Take a resource out of its parent, to be a root with no location.

    Raises:
      StoreError: It is not the top of a stack growing in z, or a root of its name exists.
    """
    parent = node.parent
    if parent is None:
      return
    self.check_locks([node], tokens)
    if (
      parent.kind == K.RESOURCE_KIND_RESOURCE_STACK
      and parent.attributes.stack.direction == pb.STACK_DIRECTION_Z
      and parent.children[-1] is not node
    ):
      raise StoreError(
        pb.PROBLEM_CANNOT_DROP_HERE,
        f"'{node.name}' is not the top of stack '{parent.name}'",
        node.name,
      )
    self.check_names_fit(node, None)
    self.move(node, None, None, None, steps)

  def rotate(self, change: pb.RotationChange, steps: List[Step]) -> Node:
    """Turn a resource by or to angles, about a pivot when given.

    Raises:
      StoreError: A pivot for a resource without a location.
    """
    node = self.resolve(change.resource)
    if change.WhichOneof("rotation") == "by":
      by = change.by
      rotation = g.turned_by(node.rotation, Rotation(by.x, by.y, by.z))
    else:
      to = change.to
      rotation = g.turned_to(
        node.rotation,
        to.x if to.HasField("x") else None,
        to.y if to.HasField("y") else None,
        to.z if to.HasField("z") else None,
      )
    location = node.location
    if change.HasField("pivot"):
      location = g.pivoted_location(node, rotation, to_coordinate(change.pivot))

    def apply() -> None:
      node.attributes.rotation.CopyFrom(to_rotation_message(rotation))
      if location is not None:
        node.attributes.location.CopyFrom(to_vec3(location))

    self.set_attributes(node, steps, apply)
    return node

  def set_volume(self, node: Node, volume: float, steps: List[Step]) -> None:
    """What a resource holds now; liquid booked on it and not yet resolved stays booked."""
    if node.kind not in g.CONTAINER_KINDS and node.kind != K.RESOURCE_KIND_TIP:
      raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{node.name}' holds no liquid", node.name)

    def apply() -> None:
      tracker = node.state.volume
      booked = tracker.pending_volume - tracker.volume
      tracker.volume = volume
      tracker.pending_volume = volume + booked
      if not node.state.HasField("volume"):
        tracker.tracking_enabled = True

    self.set_attributes(node, steps, apply)

  def set_tracking(self, request: pb.SetTracking, steps: List[Step]) -> None:
    scope = self.resolve(request.scope)
    for node in scope.walk():
      holds_liquid = node.kind in g.CONTAINER_KINDS or node.kind == K.RESOURCE_KIND_TIP
      if request.HasField("volume_tracking") and holds_liquid:
        self.set_attributes(
          node,
          steps,
          partial(_set_volume_tracking, node, request.volume_tracking),
        )
      if request.HasField("tip_tracking") and node.kind == K.RESOURCE_KIND_TIP_SPOT:
        self.set_attributes(
          node,
          steps,
          partial(_set_tip_tracking, node, request.tip_tracking),
        )

  def make_tip(self, spot: Node, steps: List[Step]) -> Node:
    """A fresh tip from a spot, named for it, belonging to nothing yet.

    Raises:
      StoreError: The spot does not say what tip it makes.
    """
    if not spot.attributes.tip_spot.HasField("prototype_tip"):
      raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{spot.name}' makes no tips", spot.name)
    made = spot.state.tips_made if spot.state.HasField("tips_made") else 0
    definition = pb.ResourceDefinition(attributes=spot.attributes.tip_spot.prototype_tip)
    definition.attributes.name = f"{spot.name}#{made}"
    definition.attributes.ClearField("location")
    definition.initial_state.volume.CopyFrom(pb.VolumeState(tracking_enabled=True))
    tip = build_tree(definition)
    self.set_attributes(spot, steps, lambda: _set_tips_made(spot, made + 1))
    self._create(tip, None, steps)
    return tip

  def set_tip_presence(self, request: pb.SetTipPresence, steps: List[Step]) -> None:
    for ref in request.spots:
      spot = self.resolve(ref)
      if spot.kind != K.RESOURCE_KIND_TIP_SPOT:
        raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{spot.name}' is not a tip spot", spot.name)
      tip = tool_in(spot)
      if request.present and tip is None:
        made = self.make_tip(spot, steps)
        self.move(made, spot, None, g.resting_location(spot, made), steps)
      elif not request.present and tip is not None:
        self.remove(tip, steps)

  def set_metadata(self, request: pb.SetMetadata, steps: List[Step]) -> None:
    node = self.resolve(request.resource)

    def apply() -> None:
      if request.replace:
        node.attributes.metadata.Clear()
      node.attributes.metadata.update(dict(request.metadata))

    self.set_attributes(node, steps, apply)

  def set_barcode(self, request: pb.SetBarcode, steps: List[Step]) -> None:
    node = self.resolve(request.resource)

    def apply() -> None:
      if request.HasField("barcode"):
        node.attributes.barcode.CopyFrom(request.barcode)
      else:
        node.attributes.ClearField("barcode")

    self.set_attributes(node, steps, apply)

  def set_preferred_pickup_location(
    self, request: pb.SetPreferredPickupLocation, steps: List[Step]
  ) -> None:
    node = self.resolve(request.resource)

    def apply() -> None:
      if request.HasField("location"):
        node.attributes.preferred_pickup_location.CopyFrom(request.location)
      else:
        node.attributes.ClearField("preferred_pickup_location")

    self.set_attributes(node, steps, apply)

  def set_jaw_width(self, gripper: Node, width: float, steps: List[Step]) -> None:
    if gripper.kind != K.RESOURCE_KIND_MECHANICAL_GRIPPER:
      raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{gripper.name}' has no jaws", gripper.name)
    moved = g.jaw_locations(gripper, width)
    self.set_attributes(gripper, steps, lambda: _set_jaw_width(gripper, width))
    for part, location in moved:
      self.set_attributes(part, steps, partial(_set_location, part, location))

  def update(self, update: spb.ResourceUpdate, steps: List[Step]) -> List[Node]:
    which = update.WhichOneof("update")
    if which == "rotation":
      return [self.rotate(update.rotation, steps)]
    if which == "metadata":
      self.set_metadata(update.metadata, steps)
      return [self.resolve(update.metadata.resource)]
    if which == "barcode":
      self.set_barcode(update.barcode, steps)
      return [self.resolve(update.barcode.resource)]
    if which == "tracking":
      self.set_tracking(update.tracking, steps)
      return list(self.resolve(update.tracking.scope).walk())
    if which == "volume":
      node = self.resolve(update.volume.resource)
      self.set_volume(node, update.volume.volume, steps)
      return [node]
    if which == "tip_presence":
      self.set_tip_presence(update.tip_presence, steps)
      return [self.resolve(ref) for ref in update.tip_presence.spots]
    if which == "preferred_pickup_location":
      self.set_preferred_pickup_location(update.preferred_pickup_location, steps)
      return [self.resolve(update.preferred_pickup_location.resource)]
    raise StoreError(pb.PROBLEM_UNSPECIFIED, "an empty update")

  def touched_by(self, update: spb.ResourceUpdate) -> List[Node]:
    """The resources an update changes, for the lock check before it runs."""
    which = update.WhichOneof("update")
    if which == "rotation":
      return [self.resolve(update.rotation.resource)]
    if which == "metadata":
      return [self.resolve(update.metadata.resource)]
    if which == "barcode":
      return [self.resolve(update.barcode.resource)]
    if which == "tracking":
      return [self.resolve(update.tracking.scope)]
    if which == "volume":
      return [self.resolve(update.volume.resource)]
    if which == "tip_presence":
      return [self.resolve(ref) for ref in update.tip_presence.spots]
    if which == "preferred_pickup_location":
      return [self.resolve(update.preferred_pickup_location.resource)]
    return []

  # -- reading -----------------------------------------------------------------------------------

  def committed_view(self) -> Engine:
    """A copy of the store with every unresolved staged item undone."""
    view = Engine(self.implementation)
    copies: Dict[int, Node] = {}

    def copy(node: Node, parent: Optional[Node]) -> Node:
      attributes, state = pb.ResourceAttributes(), pb.ResourceState()
      attributes.CopyFrom(node.attributes)
      state.CopyFrom(node.state)
      made = Node(attributes=attributes, state=state, parent=parent, id=node.id)
      copies[id(node)] = made
      made.children = [copy(child, made) for child in node.children]
      return made

    for root in self.roots.values():
      view_root = copy(root, None)
      view.roots[view_root.name] = view_root
      view._names[view_root.id] = {}
      view._index_names(view_root, view_root)
      for each in view_root.walk():
        view.nodes[each.id] = each

    def mapped(node: Optional[Node]) -> Optional[Node]:
      if node is None:
        return None
      if id(node) not in copies:
        copy(node, None)
      return copies[id(node)]

    pending = [
      step
      for op in sorted(self.operations.values(), key=lambda o: o.created_at.ToNanoseconds())
      for item in op.items
      if item.state == pb.ITEM_STATE_PENDING
      for step in item.steps
    ]
    translated: List[Step] = []
    for step in pending:
      if isinstance(step, _Snapshot):
        node = mapped(step.node)
        assert node is not None
        translated.append(_Snapshot(node, step.attributes, step.state))
      elif isinstance(step, _Reattach):
        node = mapped(step.node)
        assert node is not None
        translated.append(_Reattach(node, mapped(step.parent), step.index))
      elif isinstance(step, _Created):
        node = mapped(step.node)
        assert node is not None
        translated.append(_Created(node))
      elif isinstance(step, _Removed):
        node = mapped(step.node)
        assert node is not None
        translated.append(_Removed(node, mapped(step.parent), step.index))
      else:
        node = mapped(step.node)
        assert node is not None
        translated.append(_Booked(node, step.delta))
    view._undo(translated)
    for node in view.nodes.values():
      node.state.volume.pending_volume = node.state.volume.volume
    view.revision = self.revision
    view.revisions = dict(self.revisions)
    return view

  def geometry(self, query: spb.GeometryQuery, placements: g.Placements) -> spb.Geometry:
    """Everything about where a resource is, for one query; a refusal as its issue.

    Its size and rotations are answered even where it has no location, a root nobody placed;
    only a location asked for is then refused.
    """
    try:
      node = self.resolve(query.resource)
      frame = self.resolve(query.frame) if query.HasField("frame") else None
    except StoreError as refused:
      return spb.Geometry(issue=_issue(refused, -1))
    size, absolute = g.size(node), g.absolute_size(node)
    rotation = g.rotation_wrt(node, frame) if frame is not None else g.absolute_rotation(node)
    geometry = spb.Geometry(
      resource_id=node.id,
      rotation_in_frame=to_rotation_message(rotation),
      absolute_rotation=to_rotation_message(g.absolute_rotation(node)),
      absolute_size=pb.Vec3(x=absolute.x, y=absolute.y, z=absolute.z),
      size=pb.Vec3(x=size.x, y=size.y, z=size.z),
    )
    # Only a root nobody placed has no location; what it holds is located from its origin.
    placed = node.location is not None or frame is not None
    anchors = list(query.anchors) or ([pb.Anchor(x=pb.ANCHOR_X_LEFT)] if placed else [])
    try:
      geometry.locations.extend(
        to_vec3(
          g.location_wrt(node, frame, a.x, a.y, a.z, placements)
          if frame is not None
          else g.absolute_location(node, a.x, a.y, a.z, placements)
        )
        for a in anchors
      )
      geometry.highest_point = g.highest_point(node, placements)
    except StoreError as refused:
      del geometry.locations[:]
      geometry.issue.CopyFrom(_issue(refused, -1))
    return geometry

  def placement(self, node: Node, frame: Node, placements: g.Placements) -> spb.Placement:
    """A container, spot or trash as a command reads it, in `frame`."""
    bottom = g.location_wrt(node, frame, *_ANCHOR_BOTTOM, placements)
    top = g.location_wrt(node, frame, *_ANCHOR_TOP, placements)
    is_container = node.kind in g.CONTAINER_KINDS
    cavity = (
      g.location_wrt(node, frame, *_ANCHOR_CAVITY, placements)
      if is_container and node.attributes.container.HasField("material_z_thickness")
      else bottom
    )
    size = g.absolute_size(node)
    message = spb.Placement(
      resource_id=node.id,
      kind=node.kind,
      bottom=to_vec3(bottom),
      cavity_bottom=to_vec3(cavity),
      top=to_vec3(top),
      absolute_size=pb.Vec3(x=size.x, y=size.y, z=size.z),
      rotation_in_frame=to_rotation_message(g.rotation_wrt(node, frame)),
    )
    if is_container:
      message.container.CopyFrom(node.attributes.container)
    if node.state.HasField("volume"):
      message.volume.CopyFrom(node.state.volume)
    return message

  # -- what a device reports ---------------------------------------------------------------------

  def record_position(self, position: spb.DevicePosition, steps: List[Step]) -> Node:
    node = self.resolve(position.resource)
    if position.HasField("location"):
      partial = position.location
      x = partial.x if partial.HasField("x") else None
      y = partial.y if partial.HasField("y") else None
      z = partial.z if partial.HasField("z") else None
      if position.HasField("frame"):
        frame = self.resolve(position.frame)
        reference = (
          to_coordinate(position.reference_point)
          if position.HasField("reference_point")
          else g.reference_point(node)
        )
        location = g.location_from_reference(node, frame, x, y, z, reference)
      else:
        here = node.location or Coordinate(0, 0, 0)
        location = Coordinate(
          here.x if x is None else x, here.y if y is None else y, here.z if z is None else z
        )
      self.set_attributes(node, steps, lambda: node.attributes.location.CopyFrom(to_vec3(location)))
    if position.HasField("rotation"):
      change = pb.RotationChange()
      change.CopyFrom(position.rotation)
      change.resource.id = node.id
      self.rotate(change, steps)
    if position.HasField("jaw_width"):
      self.set_jaw_width(node, position.jaw_width, steps)
    if position.drive_angles:
      self.set_attributes(
        node, steps, lambda: node.state.drive_angles.update(dict(position.drive_angles))
      )
    return node

  def record_measurement(
    self, measurement: spb.Measurement, index: int, steps: List[Step]
  ) -> spb.MeasurementResult:
    node = self.resolve(measurement.resource)
    which = measurement.WhichOneof("measurement")
    if which in ("volume", "liquid_height"):
      previous = node.state.volume.volume if node.state.HasField("volume") else 0.0
      volume = (
        measurement.volume
        if which == "volume"
        else g.volume_from_height(node, measurement.liquid_height)
      )
      self.set_volume(node, volume, steps)
      return spb.MeasurementResult(previous_volume=previous, volume=volume)
    if which == "tool_present":
      holds = tool_in(node) is not None
      if holds == measurement.tool_present:
        return spb.MeasurementResult()
      sensed = "a tool" if measurement.tool_present else "nothing"
      return spb.MeasurementResult(
        issue=pb.Issue(
          # What the model has wrong: a tool it does not know of, or one that is not there.
          problem=pb.PROBLEM_NO_TIP if measurement.tool_present else pb.PROBLEM_HAS_TIP,
          message=f"'{node.name}' was sensed holding {sensed}; the model disagrees",
          resource_id=node.id,
          item=index,
        )
      )
    if which == "barcode":
      self.set_barcode(
        pb.SetBarcode(resource=pb.ResourceRef(id=node.id), barcode=measurement.barcode), steps
      )
      return spb.MeasurementResult()
    raise StoreError(pb.PROBLEM_UNSPECIFIED, "an empty measurement")

  # -- operations --------------------------------------------------------------------------------

  def stage(self, root: Node, kind: str, holder: str, items: List[Item]) -> _Operation:
    op = _Operation(
      id=uuid.uuid4().bytes, root=root, kind=kind, holder=holder, created_at=_now(), items=items
    )
    self.operations[op.id] = op
    self._touched_operations[op.id] = op
    self._pending_index = None
    return op

  def holder_of(self, root: Node, tokens: Sequence[bytes]) -> str:
    lock = self.locks.get(root.id)
    return lock.holder if lock is not None and lock.token in tokens else ""

  def resolve_operation(
    self, operation_id: bytes, outcomes: Sequence[spb.ItemOutcome], tokens: Sequence[bytes]
  ) -> _Operation:
    """Commit or roll back items of a staged operation.

    Raises:
      StoreError: No such operation, an item out of range, or one already resolved.
    """
    op = self.operations.get(operation_id)
    if op is None:
      raise StoreError(pb.PROBLEM_NOT_FOUND, f"no operation {operation_id.hex()}")
    self.check_locks([op.root], tokens)
    for outcome in outcomes:
      if not 0 <= outcome.item < len(op.items):
        raise StoreError(pb.PROBLEM_OUT_OF_RANGE, f"operation has no item {outcome.item}")
      item = op.items[outcome.item]
      if item.state != pb.ITEM_STATE_PENDING:
        raise StoreError(pb.PROBLEM_OUT_OF_RANGE, f"item {outcome.item} is already resolved")
      steps: List[Step] = []
      if outcome.succeeded and not outcome.HasField("volume"):
        for step in item.steps:
          if isinstance(step, _Booked):
            self.set_attributes(step.node, steps, partial(_commit_booking, step.node, step.delta))
        item.state = pb.ITEM_STATE_COMMITTED
      else:
        self._undo(item.steps)
        if outcome.HasField("volume") and outcome.volume > 0:
          for transfer in item.transfers:
            moved = min(outcome.volume, transfer.volume)
            for node, delta in ((transfer.giver, -moved), (transfer.taker, moved)):
              if node is not None and node.id in self.nodes:
                self.set_attributes(node, steps, partial(_add_committed, node, delta))
        item.state = pb.ITEM_STATE_COMMITTED if outcome.succeeded else pb.ITEM_STATE_ROLLED_BACK
      item.resolved_at = _now()
      self._journal.extend(steps)
      for step in item.steps:
        node = _step_node(step)
        if node.id in self.nodes:
          self._touch(node)
    self._touched_operations[op.id] = op
    self._pending_index = None
    return op


# -- helpers that change a node's fields, named so lambdas stay one expression -------------------


def _set_location(node: Node, location: Coordinate) -> None:
  node.attributes.location.CopyFrom(to_vec3(location))


def _set_volume_tracking(node: Node, enabled: bool) -> None:
  node.state.volume.tracking_enabled = enabled


def _set_tip_tracking(node: Node, enabled: bool) -> None:
  node.state.tip_tracking_enabled = enabled


def _set_tips_made(node: Node, made: int) -> None:
  node.state.tips_made = made


def _set_jaw_width(node: Node, width: float) -> None:
  node.state.jaw_width = width


def _commit_booking(node: Node, delta: float) -> None:
  node.state.volume.volume += delta


def _add_committed(node: Node, delta: float) -> None:
  node.state.volume.volume += delta
  node.state.volume.pending_volume += delta


def _step_node(step: Step) -> Node:
  return step.node


def tool_in(node: Node) -> Optional[Node]:
  """The tool a spot, shaft or holder holds: its first child that is a tip or a tool."""
  return next((c for c in node.children if c.kind in g.TOOL_KINDS), None)


def _issue(error: StoreError, item: int, node: Optional[Node] = None) -> pb.Issue:
  return pb.Issue(
    problem=error.problem,
    message=str(error),
    resource_id=node.id if node is not None else b"",
    item=item,
  )


def _rename(definition: pb.ResourceDefinition, name: str) -> None:
  """Name a definition's root, and put that name where its descendants say `{name}`."""
  definition.attributes.name = name

  def visit(children: Iterable[pb.ResourceDefinition]) -> None:
    for child in children:
      child.attributes.name = child.attributes.name.replace("{name}", name)
      visit(child.children)

  visit(definition.children)


def _check_definition(definition: pb.ResourceDefinition) -> None:
  """Refuse a definition with no kind or no name.

  Raises:
    StoreError: A resource in it has no kind or no name.
  """
  if definition.attributes.kind == K.RESOURCE_KIND_UNSPECIFIED:
    raise StoreError(
      pb.PROBLEM_WRONG_KIND,
      f"'{definition.attributes.name}' has no kind",
      definition.attributes.name,
    )
  for child in definition.children:
    if not child.attributes.name:
      raise StoreError(pb.PROBLEM_NOT_FOUND, "a resource needs a name")
    _check_definition(child)
