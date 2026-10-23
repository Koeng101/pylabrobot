"""`ResourceStore`: how PLR reaches a resource store, wherever the store is.

`ResourceStore.in_memory()` serves a `MemoryStore` in this process, through the same Connect
protocol a remote store speaks, with no socket. `ResourceStore.connect(url)` reaches a store
anywhere else. A store's refusal arrives as the `StoreError` it raised, with its problem.
"""

from __future__ import annotations

import contextlib
import datetime
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Dict, List, Optional, Sequence, TypeVar, Union

from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from pyqwest import Client
from pyqwest.testing import ASGITransport

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import handles, library
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.memory import ISSUE_TYPE, MemoryStore, asgi_app
from pylabrobot.resources.store.tree import to_vec3
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.resources.store.v1.primitives_connect import ResourcePrimitivesServiceClient
from pylabrobot.resources.store.v1.store_connect import ResourceStoreServiceClient

REQ = TypeVar("REQ")
RES = TypeVar("RES")

_IN_PROCESS = "http://in-process"


def store_error(error: ConnectError) -> StoreError:
  """The `StoreError` a Connect error carries, or one made from its code and message."""
  for detail in error.details:
    if detail.type_name == ISSUE_TYPE:
      issue = pb.Issue.FromString(detail.message_bytes)
      return StoreError(issue.problem, issue.message)
  return StoreError(pb.PROBLEM_UNSPECIFIED, f"{error.code.value}: {error.message}")


class _Refusals:
  """Raises a store's refusals as `StoreError`s, for every call a client makes."""

  async def intercept_unary(
    self,
    call_next: Callable[[REQ, RequestContext], Awaitable[RES]],
    request: REQ,
    ctx: RequestContext,
    /,
  ) -> RES:
    try:
      return await call_next(request, ctx)
    except ConnectError as error:
      raise store_error(error) from error

  async def intercept_server_stream(
    self,
    call_next: Callable[[REQ, RequestContext], AsyncIterator[RES]],
    request: REQ,
    ctx: RequestContext,
    /,
  ) -> AsyncIterator[RES]:
    try:
      async for response in call_next(request, ctx):
        yield response
    except ConnectError as error:
      raise store_error(error) from error


class ResourceStore:
  """A resource store, in this process or served elsewhere: its command API, and its primitives.

  Resources in it are reached through handles: `create` makes one, `get` finds one by name.

  Attributes:
    commands: the `ResourceStoreService`, everything PLR uses.
    primitives: the `ResourcePrimitivesService`, low-level changes.
    memory: the store itself, when it is served in this process.
    lock_tokens: the locks this client holds, sent with every change it makes.
  """

  def __init__(self, address: str, http: Client, memory: Optional[MemoryStore] = None):
    interceptors = [_Refusals()]
    self.commands = ResourceStoreServiceClient(address, http_client=http, interceptors=interceptors)
    self.primitives = ResourcePrimitivesServiceClient(
      address, http_client=http, interceptors=interceptors
    )
    self.memory = memory
    self.lock_tokens: List[bytes] = []

  @classmethod
  def in_memory(cls, store: Optional[MemoryStore] = None) -> ResourceStore:
    """A store held in this process, spoken to over Connect without a socket."""
    memory = store or MemoryStore()
    http = Client(transport=ASGITransport(asgi_app(memory)))
    return cls(_IN_PROCESS, http, memory)

  @classmethod
  def connect(cls, url: str) -> ResourceStore:
    """A store served at `url`, "http://127.0.0.1:8080" say."""
    return cls(url, Client())

  async def close(self) -> None:
    await self.commands.close()
    await self.primitives.close()

  async def __aenter__(self) -> ResourceStore:
    return self

  async def __aexit__(self, *exc: object) -> None:
    await self.close()

  # -- handles -----------------------------------------------------------------------------------

  def handle_from_node(
    self, node: pb.ResourceNode, children: Sequence[pb.ResourceNode]
  ) -> handles.Resource:
    """The handle for a node; a kind whose handle knows its children needs them all."""
    return handles.HANDLE_TYPES[node.attributes.kind](self, node, children)

  async def make_handles(
    self, nodes: Sequence[pb.ResourceNode], known: Sequence[pb.ResourceNode] = ()
  ) -> List[handles.Resource]:
    """Handles for nodes, asking the store for the children of any that need them and whose
    children are not among `known`."""
    children: Dict[bytes, List[pb.ResourceNode]] = {}
    for node in known:
      children.setdefault(node.parent_id, []).append(node)
    missing = [
      node
      for node in nodes
      if node.attributes.kind in handles.STRUCTURED_KINDS
      and len(children.get(node.id, [])) < len(node.child_ids)
    ]
    if missing:
      response = await self.commands.get_resources(
        spb.GetResourcesRequest(resources=[pb.ResourceRef(id=n.id) for n in missing], depth=1)
      )
      wanted = {node.id for node in missing}
      for node in response.nodes:
        if node.parent_id in wanted:
          children.setdefault(node.parent_id, []).append(node)
    return [self.handle_from_node(node, children.get(node.id, [])) for node in nodes]

  async def _get(self, ref: pb.ResourceRef) -> handles.Resource:
    response = await self.commands.get_resources(spb.GetResourcesRequest(resources=[ref], depth=1))
    return (await self.make_handles(response.nodes[:1], response.nodes[1:]))[0]

  async def get(
    self, name: str, root: Union[str, handles.Resource, None] = None
  ) -> handles.Resource:
    """A resource by name: a root's, or one within `root`.

    Raises:
      StoreError: No resource has that name.
    """
    root_name = root.name if isinstance(root, handles.Resource) else (root or "")
    return await self._get(pb.ResourceRef(name=pb.NameRef(root=root_name, name=name)))

  async def get_by_id(self, resource_id: bytes) -> handles.Resource:
    return await self._get(pb.ResourceRef(id=resource_id))

  async def roots(self) -> List[handles.Resource]:
    """Every root in the store: decks, devices, and resources in nothing."""
    nodes: List[pb.ResourceNode] = []
    token = ""
    while True:
      response = await self.commands.list_roots(spb.ListRootsRequest(page_token=token))
      nodes.extend(response.roots)
      token = response.next_page_token
      if not token:
        return await self.make_handles(nodes)

  async def find_resources(
    self,
    filter: spb.ResourceFilter,
    scope: Optional[handles.Resource] = None,
  ) -> List[handles.Resource]:
    """Every resource that matches, within `scope` or the whole store, in pre-order."""
    request = spb.FindResourcesRequest(filter=filter)
    if scope is not None:
      request.scope.CopyFrom(scope.ref)
    nodes: List[pb.ResourceNode] = []
    while True:
      response = await self.commands.find_resources(request)
      nodes.extend(response.nodes)
      if not response.next_page_token:
        return await self.make_handles(nodes)
      request.page_token = response.next_page_token

  async def create(
    self,
    source: Union[str, pb.ResourceDefinition],
    name: str,
    parent: Optional[handles.Resource] = None,
    location: Optional[Coordinate] = None,
    track: Optional[int] = None,
  ) -> handles.Resource:
    """Make a resource from a model or a definition, and put it in `parent` when given.

    Args:
      source: A model's name - one of PLR's labware, or one the store keeps - or a definition.
      name: What to call it; names in a model follow it.
      parent: What to put it in, emitting `resource.assigned`; unset leaves it a root with no
        location.
      location: Where in `parent`; see `Resource.assign_child_resource`.
      track: A Hamilton deck's track, from 1.
    """
    request = spb.CreateResource(name=name)
    if isinstance(source, pb.ResourceDefinition):
      request.definition.CopyFrom(source)
    elif source in library.model_names():
      request.definition.CopyFrom(library.get_model(source).definition)
    else:
      request.model = source
    if parent is not None:
      request.assign.parent.CopyFrom(parent.ref)
      if location is not None:
        request.assign.location.CopyFrom(to_vec3(location))
      if track is not None:
        request.assign.track = track
    elif location is not None or track is not None:
      raise ValueError("a location needs a parent")
    before = await handles._read_for_events(self, [parent.ref]) if parent is not None else None
    response = await self.commands.create_resources(
      spb.CreateResourcesRequest(lock_tokens=self.lock_tokens, resources=[request])
    )
    if before is not None and parent is not None:
      handles._emit_assigned(before, response.nodes[0], parent.id)
    return (await self.make_handles(response.nodes[:1], response.nodes[1:]))[0]

  @contextlib.asynccontextmanager
  async def lock(
    self, root: handles.Resource, holder: str, wait: Optional[float] = None
  ) -> AsyncIterator[pb.ResourceRef]:
    """Hold a root's lock while the block runs; only this client may change the root meanwhile.

    Args:
      root: A root: a deck, a device.
      holder: Who holds it, for people reading the lock: "star-01 protocol 42".
      wait: How long to wait for another holder to release it, in seconds; unset fails at once.

    Raises:
      StoreError: Another holder has it, and did not release it in time.
    """
    request = spb.AcquireLockRequest(root=root.ref, holder=holder)
    if wait is not None:
      request.wait.FromTimedelta(datetime.timedelta(seconds=wait))
    lock = await self.commands.acquire_lock(request)
    self.lock_tokens.append(lock.token)
    try:
      yield root.ref
    finally:
      self.lock_tokens.remove(lock.token)
      await self.commands.release_lock(spb.ReleaseLockRequest(root=root.ref, token=lock.token))
