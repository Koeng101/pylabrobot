"""`ResourceStore`: how PLR reaches a resource store, wherever the store is.

`ResourceStore.in_memory()` serves a `MemoryStore` in this process, through the same Connect
protocol a remote store speaks, with no socket. `ResourceStore.connect(url)` reaches a store
anywhere else. A store's refusal arrives as the `StoreError` it raised, with its problem.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Optional, TypeVar

from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from pyqwest import Client
from pyqwest.testing import ASGITransport

from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.memory import ISSUE_TYPE, MemoryStore, asgi_app
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

  Attributes:
    commands: the `ResourceStoreService`, everything PLR uses.
    primitives: the `ResourcePrimitivesService`, low-level changes.
    memory: the store itself, when it is served in this process.
  """

  def __init__(self, address: str, http: Client, memory: Optional[MemoryStore] = None):
    interceptors = [_Refusals()]
    self.commands = ResourceStoreServiceClient(address, http_client=http, interceptors=interceptors)
    self.primitives = ResourcePrimitivesServiceClient(
      address, http_client=http, interceptors=interceptors
    )
    self.memory = memory

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
