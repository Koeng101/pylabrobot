"""A resource tree as a store holds it, kept current by following the store's `Watch` stream.

The tree is read once, with the revision it was read at, and every event after that revision is
applied as it arrives. Every event of one request has the same revision: a request's events are
applied together, and what they did is reported as one batch of changes, named as PLR's resource
callbacks name them - a resource assigned, a resource unassigned, a resource whose state changed -
so a 96-channel pick-up is one batch, not ninety-six.
"""

from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple

from pylabrobot.resources.store import handles
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

logger = logging.getLogger(__name__)


class ChangeKind(enum.Enum):
  """What happened to a resource, as PLR's resource callbacks report it."""

  # It came into the tree, with everything under it.
  ASSIGNED = "assigned"
  # It left the tree, with everything under it.
  UNASSIGNED = "unassigned"
  # Its location, rotation, volume or jaw width changed.
  STATE = "state"


@dataclass(frozen=True)
class Change:
  """One change to the tree.

  Attributes:
    kind: What happened.
    node_id: The resource's id.
    name: Its name.
    resource_kind: What it is.
    subtree: The ids of it and everything under it: as it arrived for `ASSIGNED`, as it left for
      `UNASSIGNED`; empty for `STATE`.
  """

  kind: ChangeKind
  node_id: bytes
  name: str
  resource_kind: pb.ResourceKind
  subtree: Tuple[bytes, ...] = ()


Listener = Callable[[List[Change]], None]


def _placed_differently(before: pb.ResourceNode, after: pb.ResourceNode) -> bool:
  """Whether a resource's location or rotation in its parent changed."""
  a, b = before.attributes, after.attributes
  if a.HasField("location") != b.HasField("location"):
    return True
  return a.location != b.location or a.rotation != b.rotation


def _state_differs(before: pb.ResourceNode, after: pb.ResourceNode) -> bool:
  """Whether what a resource holds or how wide its jaws stand changed."""
  a, b = before.state, after.state
  if a.HasField("volume") != b.HasField("volume") or a.HasField("jaw_width") != b.HasField(
    "jaw_width"
  ):
    return True
  return (a.volume.volume, a.volume.pending_volume, a.jaw_width) != (
    b.volume.volume,
    b.volume.pending_volume,
    b.jaw_width,
  )


class TreeMirror:
  """A resource and everything under it, as the store holds them now.

  Attributes:
    root: The resource the tree starts at.
    store: The store it is in.
    nodes: Every resource in the tree, by id.
    revision: The store revision the tree is current to.
  """

  # How long a batch waits for more events of its revision once none are waiting.
  BATCH_WAIT_S = 0.05
  # How long `stop` waits for the stream it cancelled to end.
  STOP_WAIT_S = 1.0

  def __init__(self, root: handles.Resource):
    self.root = root
    self.store = root.store
    self.nodes: Dict[bytes, pb.ResourceNode] = {}
    self.revision = 0
    self._root_parent_name: Optional[str] = None
    self._listeners: List[Listener] = []
    self._tasks: List["asyncio.Future[None]"] = []
    self._waiters: List[Tuple[int, "asyncio.Future[None]"]] = []

  # -- reading the tree --------------------------------------------------------------------------

  @property
  def root_id(self) -> bytes:
    return self.root.id

  @property
  def following(self) -> bool:
    return bool(self._tasks)

  def node(self, node_id: bytes) -> pb.ResourceNode:
    return self.nodes[node_id]

  def children(self, node: pb.ResourceNode) -> List[pb.ResourceNode]:
    """A resource's children in the tree, in order."""
    return [self.nodes[child] for child in node.child_ids if child in self.nodes]

  def parent_name(self, node: pb.ResourceNode) -> Optional[str]:
    """The name of what a resource hangs from, or None for a resource that hangs from nothing."""
    parent = self.nodes.get(node.parent_id)
    if parent is not None:
      return parent.attributes.name
    return self._root_parent_name if node.id == self.root_id else None

  def walk(self, node: Optional[pb.ResourceNode] = None) -> Iterator[pb.ResourceNode]:
    """A resource and everything under it, parents before children; the whole tree by default."""
    start = node if node is not None else self.nodes[self.root_id]
    stack = [start]
    while stack:
      current = stack.pop()
      yield current
      stack.extend(reversed(self.children(current)))

  def names(self) -> List[str]:
    """Every name in the tree, in pre-order."""
    return [node.attributes.name for node in self.walk()]

  # -- following the store -----------------------------------------------------------------------

  def subscribe(self, listener: Listener) -> Callable[[], None]:
    """Call `listener` with each batch of changes; returns what stops it."""
    self._listeners.append(listener)

    def unsubscribe() -> None:
      if listener in self._listeners:
        self._listeners.remove(listener)

    return unsubscribe

  async def load(self) -> None:
    """Read the tree, and the revision it is current to, in one call."""
    response = await self.store.commands.get_resources(
      spb.GetResourcesRequest(resources=[self.root.ref], depth=-1, ancestors=True)
    )
    by_id = {node.id: node for node in response.nodes}
    root = by_id[self.root_id]
    parent = by_id.get(root.parent_id)
    self._root_parent_name = parent.attributes.name if parent is not None else None
    self.nodes = {}
    for node in self._subtree_of(root, by_id):
      self.nodes[node.id] = node
    self.revision = response.revision

  @staticmethod
  def _subtree_of(
    node: pb.ResourceNode, by_id: Dict[bytes, pb.ResourceNode]
  ) -> Iterator[pb.ResourceNode]:
    stack = [node]
    while stack:
      current = stack.pop()
      yield current
      stack.extend(by_id[child] for child in reversed(current.child_ids) if child in by_id)

  async def start(self) -> None:
    """Read the tree and follow every change made to it after."""
    if self.following:
      return
    await self.load()
    queue: "asyncio.Queue[spb.ResourceEvent]" = asyncio.Queue()
    self._tasks = [
      asyncio.ensure_future(self._read(queue, self.revision)),
      asyncio.ensure_future(self._apply_batches(queue)),
    ]

  async def stop(self) -> None:
    """Stop following; the tree stays as it was last seen."""
    tasks, self._tasks = self._tasks, []
    for task in tasks:
      task.cancel()
    # A stream being torn down may wait on the store's side; it is not waited for long.
    if tasks:
      await asyncio.wait(tasks, timeout=self.STOP_WAIT_S)
    for _, waiter in self._waiters:
      if not waiter.done():
        waiter.set_result(None)
    self._waiters = []

  async def _read(self, queue: "asyncio.Queue[spb.ResourceEvent]", after: int) -> None:
    try:
      async for event in self.store.commands.watch(
        spb.WatchRequest(roots=[self.root.ref], after_revision=after)
      ):
        queue.put_nowait(event)
    except asyncio.CancelledError:
      raise
    except Exception:
      # Cancelling the stream on `stop` ends it with the store's refusal: nothing went wrong.
      if self._tasks:
        logger.exception("stopped following the store for '%s'", self.root.name)

  async def _apply_batches(self, queue: "asyncio.Queue[spb.ResourceEvent]") -> None:
    pending: Optional[spb.ResourceEvent] = None
    while True:
      batch = [pending if pending is not None else await queue.get()]
      pending = None
      while True:
        if queue.empty():
          try:
            event = await asyncio.wait_for(queue.get(), self.BATCH_WAIT_S)
          except asyncio.TimeoutError:
            break
        else:
          event = queue.get_nowait()
        if event.revision != batch[0].revision:
          pending = event
          break
        batch.append(event)
      try:
        await self.apply(batch)
      except Exception:
        logger.exception("could not apply revision %d to '%s'", batch[0].revision, self.root.name)

  async def caught_up(self, timeout: float = 5.0) -> None:
    """Wait until every change the store has made by now is applied, or `timeout` s pass: a change
    that touched nothing in this tree never arrives."""
    info = await self.store.commands.get_store_info(spb.GetStoreInfoRequest())
    if self.revision >= info.revision or not self.following:
      return
    waiter: "asyncio.Future[None]" = asyncio.get_running_loop().create_future()
    self._waiters.append((info.revision, waiter))
    try:
      await asyncio.wait_for(asyncio.shield(waiter), timeout)
    except asyncio.TimeoutError:
      pass

  # -- applying a revision -----------------------------------------------------------------------

  async def apply(self, events: Sequence[spb.ResourceEvent]) -> List[Change]:
    """Apply the events of one revision, tell every listener what they did, and return it."""
    incoming: Dict[bytes, pb.ResourceNode] = {}
    order: List[bytes] = []
    aspects: Dict[bytes, Set[int]] = {}
    deleted: List[bytes] = []
    for event in events:
      which = event.WhichOneof("event")
      if which == "created" or which == "updated":
        node = event.created if which == "created" else event.updated
        if node.id not in incoming:
          order.append(node.id)
        incoming[node.id] = node
        if which == "updated":
          aspects.setdefault(node.id, set()).update(event.changed)
      elif which == "deleted":
        deleted.append(event.deleted)

    old = self.nodes
    gone = set(deleted)
    known = {i: n for i, n in {**old, **incoming}.items() if i not in gone}
    # A resource that arrived brings what is under it, which no event names: read it once.
    missing = [
      child
      for node_id, node in known.items()
      if self._in_tree(node_id, known, {})
      for child in node.child_ids
      if child not in known and child not in gone
    ]
    if missing:
      response = await self.store.commands.get_resources(
        spb.GetResourcesRequest(resources=[pb.ResourceRef(id=i) for i in missing], depth=-1)
      )
      for node in response.nodes:
        known.setdefault(node.id, node)

    memo: Dict[bytes, bool] = {}
    tree = {i: n for i, n in known.items() if self._in_tree(i, known, memo)}
    changes = self._changes(old, tree, incoming, order, aspects, deleted)
    self.nodes = tree
    self.revision = max(self.revision, events[0].revision) if events else self.revision
    for listener in list(self._listeners):
      try:
        listener(changes)
      except Exception:
        logger.exception("a listener to '%s' failed", self.root.name)
    still_waiting = []
    for revision, waiter in self._waiters:
      if self.revision >= revision:
        if not waiter.done():
          waiter.set_result(None)
      else:
        still_waiting.append((revision, waiter))
    self._waiters = still_waiting
    return changes

  def _in_tree(self, node_id: bytes, known: Dict[bytes, pb.ResourceNode], memo: Dict) -> bool:
    """Whether a resource hangs, through resources in `known`, from the root."""
    path = []
    current = node_id
    result = False
    while True:
      if current in memo:
        result = memo[current]
        break
      if current == self.root_id:
        result = current in known
        break
      node = known.get(current)
      if node is None or not node.parent_id:
        break
      path.append(current)
      current = node.parent_id
    for each in path:
      memo[each] = result
    memo[node_id] = result
    return result

  @staticmethod
  def _ids_under(node_id: bytes, nodes: Dict[bytes, pb.ResourceNode]) -> Tuple[bytes, ...]:
    found = []
    stack = [node_id]
    while stack:
      current = stack.pop()
      if current not in nodes:
        continue
      found.append(current)
      stack.extend(reversed(nodes[current].child_ids))
    return tuple(found)

  def _changes(
    self,
    old: Dict[bytes, pb.ResourceNode],
    tree: Dict[bytes, pb.ResourceNode],
    incoming: Dict[bytes, pb.ResourceNode],
    order: List[bytes],
    aspects: Dict[bytes, Set[int]],
    deleted: List[bytes],
  ) -> List[Change]:
    """What the events did, in the order PLR's callbacks report it: a resource that moves to
    another parent is unassigned, has its location set, and is assigned."""
    changes: List[Change] = []

    def change(kind: ChangeKind, node: pb.ResourceNode, nodes: Dict) -> None:
      subtree = self._ids_under(node.id, nodes) if kind != ChangeKind.STATE else ()
      changes.append(Change(kind, node.id, node.attributes.name, node.attributes.kind, subtree))

    for node_id in order:
      was, now = node_id in old, node_id in tree
      node = incoming[node_id]
      if was and not now:
        if old[node_id].parent_id in tree:
          change(ChangeKind.UNASSIGNED, old[node_id], old)
      elif now and not was:
        if node.parent_id in old:
          change(ChangeKind.STATE, node, tree)
          change(ChangeKind.ASSIGNED, node, tree)
      elif was and now:
        before = old[node_id]
        changed = aspects.get(node_id, set())
        if before.parent_id != node.parent_id:
          change(ChangeKind.UNASSIGNED, before, old)
          change(ChangeKind.STATE, node, tree)
          change(ChangeKind.ASSIGNED, node, tree)
        elif (spb.CHANGE_ASPECT_PLACEMENT in changed and _placed_differently(before, node)) or (
          spb.CHANGE_ASPECT_STATE in changed and _state_differs(before, node)
        ):
          change(ChangeKind.STATE, node, tree)
    for node_id in deleted:
      if node_id in old and old[node_id].parent_id in tree:
        change(ChangeKind.UNASSIGNED, old[node_id], old)
    return changes
