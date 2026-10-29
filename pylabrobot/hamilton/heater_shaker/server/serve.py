"""Serving heater shakers: one Connect application for the heater shakers it holds, by name.

A long call (a shake, a wait for temperature, a hold) streams its progress every few seconds, so
nothing between the server and a client sees an idle call and cuts it. A shake runs on the
server: it finishes, stopping and unlocking the plate, even if the client goes away.
"""

import asyncio
import hashlib
import time
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional, Sequence, Set, TypeVar

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext

from pylabrobot.hamilton.heater_shaker.heater_shaker import Direction, HamiltonHeaterShaker
from pylabrobot.hamilton.heater_shaker.server.errors import to_connect_error
from pylabrobot.hamilton.heater_shaker.server.v1 import heater_shaker_pb2 as pb
from pylabrobot.hamilton.heater_shaker.server.v1.heater_shaker_connect import (
  HeaterShakerServiceASGIApplication,
)
from pylabrobot.resources.server.v1 import types_pb2 as tpb

# An ASGI 3 application.
ASGIApp = Callable[[Dict[str, Any], Any, Any], Awaitable[None]]

# The response header that says which description of the heater shakers is current.
REVISION_HEADER = "heater-shaker-description-revision"

# How often a long call says how far it has got, in seconds.
PROGRESS_INTERVAL = 5.0

T = TypeVar("T")
Ctx = RequestContext[Any, Any]


def _direction(value: int) -> Direction:
  if value == 0:
    return 0
  if value == 1:
    return 1
  raise ValueError(f"direction must be 0 or 1, not {value}")


class _Served:
  """The heater shakers a server holds, each call made on the one it names."""

  def __init__(self, heater_shakers: Sequence[HamiltonHeaterShaker]):
    self.heater_shakers: Dict[str, HamiltonHeaterShaker] = {}
    for hs in heater_shakers:
      if hs.name in self.heater_shakers:
        raise ValueError(f"two heater shakers are named '{hs.name}'")
      self.heater_shakers[hs.name] = hs
    # Calls that keep running when their client has gone, held so they are not collected.
    self._running: Set["asyncio.Task[None]"] = set()
    self._digest: Optional[bytes] = None
    self.revision = 0

  def _description(self) -> pb.DescribeResponse:
    response = pb.DescribeResponse()
    for hs in self.heater_shakers.values():
      assert hs.index is not None
      described = response.heater_shakers.add(name=hs.name, index=hs.index)
      if hs.resource is not None:
        described.resource.CopyFrom(tpb.ResourceRef(id=hs.resource.id))
      if hs.target_temperature is not None:
        described.target_temperature = hs.target_temperature
    return response

  def _stamp(self, ctx: Ctx) -> None:
    """Say which description is current, moving the revision on when it changed."""
    digest = hashlib.sha256(self._description().SerializeToString(deterministic=True)).digest()
    if digest != self._digest:
      self._digest = digest
      self.revision += 1
    ctx.response_headers[REVISION_HEADER] = str(self.revision)

  def _get(self, name: str) -> HamiltonHeaterShaker:
    hs = self.heater_shakers.get(name)
    if hs is None:
      raise ConnectError(Code.NOT_FOUND, f"this server holds no heater shaker named '{name}'")
    return hs

  async def _call(
    self, ctx: Ctx, name: str, call: Callable[[HamiltonHeaterShaker], Awaitable[T]]
  ) -> T:
    """Make a call on the heater shaker named `name`, raising what it raised as a Connect error."""
    hs = self._get(name)
    try:
      return await call(hs)
    except Exception as error:
      raise to_connect_error(error) from error
    finally:
      self._stamp(ctx)

  async def _stream(
    self,
    ctx: Ctx,
    name: str,
    call: Callable[[HamiltonHeaterShaker], Awaitable[None]],
    finish_without_client: bool,
  ) -> AsyncIterator[pb.Progress]:
    """Make a long call, saying how far it has got every `PROGRESS_INTERVAL` seconds, and when it
    is done.

    Args:
      finish_without_client: whether the call runs on when the client goes away.
    """
    hs = self._get(name)
    self._stamp(ctx)
    start = time.monotonic()
    task = asyncio.ensure_future(call(hs))
    try:
      while True:
        done, _ = await asyncio.wait({task}, timeout=PROGRESS_INTERVAL)
        if done:
          break
        yield pb.Progress(elapsed=time.monotonic() - start)
      try:
        task.result()
      except Exception as error:
        raise to_connect_error(error) from error
      yield pb.Progress(elapsed=time.monotonic() - start, done=True)
    finally:
      if not task.done():
        if finish_without_client:
          self._running.add(task)
          task.add_done_callback(self._running.discard)
        else:
          task.cancel()

  # -- the service --

  async def describe(self, request: pb.DescribeRequest, ctx: Ctx) -> pb.DescribeResponse:
    self._stamp(ctx)
    return self._description()

  async def setup(self, request: pb.SetupRequest, ctx: Ctx) -> pb.SetupResponse:
    await self._call(ctx, request.name, lambda hs: hs.setup())
    return pb.SetupResponse()

  async def stop(self, request: pb.StopRequest, ctx: Ctx) -> pb.StopResponse:
    await self._call(ctx, request.name, lambda hs: hs.stop())
    return pb.StopResponse()

  async def lock_plate(self, request: pb.LockPlateRequest, ctx: Ctx) -> pb.LockPlateResponse:
    await self._call(ctx, request.name, lambda hs: hs.lock_plate())
    return pb.LockPlateResponse()

  async def unlock_plate(self, request: pb.UnlockPlateRequest, ctx: Ctx) -> pb.UnlockPlateResponse:
    await self._call(ctx, request.name, lambda hs: hs.unlock_plate())
    return pb.UnlockPlateResponse()

  async def get_is_shaking(
    self, request: pb.GetIsShakingRequest, ctx: Ctx
  ) -> pb.GetIsShakingResponse:
    shaking = await self._call(ctx, request.name, lambda hs: hs.get_is_shaking())
    return pb.GetIsShakingResponse(shaking=shaking)

  def shake(self, request: pb.ShakeRequest, ctx: Ctx) -> AsyncIterator[pb.Progress]:
    duration: Optional[float] = request.duration if request.HasField("duration") else None
    direction: Direction = _direction(request.direction) if request.HasField("direction") else 0
    acceleration = request.acceleration if request.HasField("acceleration") else 1_000
    timeout: Optional[float] = 30
    if request.HasField("timeout"):
      timeout = request.timeout.value if request.timeout.HasField("value") else None
    return self._stream(
      ctx,
      request.name,
      lambda hs: hs.shake(
        request.speed,
        duration,
        direction=direction,
        acceleration=acceleration,
        timeout=timeout,
      ),
      finish_without_client=True,
    )

  async def stop_shaking(self, request: pb.StopShakingRequest, ctx: Ctx) -> pb.StopShakingResponse:
    await self._call(ctx, request.name, lambda hs: hs.stop_shaking())
    return pb.StopShakingResponse()

  async def get_temperature(
    self, request: pb.GetTemperatureRequest, ctx: Ctx
  ) -> pb.GetTemperatureResponse:
    temperature = await self._call(ctx, request.name, lambda hs: hs.get_temperature())
    return pb.GetTemperatureResponse(temperature=temperature)

  async def get_edge_temperature(
    self, request: pb.GetEdgeTemperatureRequest, ctx: Ctx
  ) -> pb.GetEdgeTemperatureResponse:
    temperature = await self._call(ctx, request.name, lambda hs: hs.get_edge_temperature())
    return pb.GetEdgeTemperatureResponse(temperature=temperature)

  async def set_temperature(
    self, request: pb.SetTemperatureRequest, ctx: Ctx
  ) -> pb.SetTemperatureResponse:
    passive = request.passive if request.HasField("passive") else False
    await self._call(
      ctx, request.name, lambda hs: hs.set_temperature(request.temperature, passive=passive)
    )
    return pb.SetTemperatureResponse()

  def wait_for_temperature(
    self, request: pb.WaitForTemperatureRequest, ctx: Ctx
  ) -> AsyncIterator[pb.Progress]:
    timeout = request.timeout if request.HasField("timeout") else 300.0
    tolerance = request.tolerance if request.HasField("tolerance") else 0.5
    return self._stream(
      ctx,
      request.name,
      lambda hs: hs.wait_for_temperature(timeout=timeout, tolerance=tolerance),
      finish_without_client=False,
    )

  def hold_temperature(
    self, request: pb.HoldTemperatureRequest, ctx: Ctx
  ) -> AsyncIterator[pb.Progress]:
    return self._stream(
      ctx,
      request.name,
      lambda hs: hs.hold_temperature(request.duration),
      finish_without_client=False,
    )

  async def deactivate(self, request: pb.DeactivateRequest, ctx: Ctx) -> pb.DeactivateResponse:
    await self._call(ctx, request.name, lambda hs: hs.deactivate())
    return pb.DeactivateResponse()


def heater_shaker_server_app(heater_shakers: Sequence[HamiltonHeaterShaker]) -> ASGIApp:
  """One ASGI application serving these heater shakers, each called by its name.

  Raises:
    ValueError: If two have the same name.
  """
  return HeaterShakerServiceASGIApplication(_Served(heater_shakers))


async def serve(
  heater_shakers: Sequence[HamiltonHeaterShaker], host: str = "127.0.0.1", port: int = 8082
) -> None:
  """Serve heater shakers until cancelled. Needs uvicorn, the `server` extra.

  Args:
    heater_shakers: the heater shakers to serve.
    host: the address to listen on.
    port: the port to listen on.
  """
  import uvicorn

  await uvicorn.Server(
    uvicorn.Config(heater_shaker_server_app(heater_shakers), host=host, port=port)
  ).serve()
