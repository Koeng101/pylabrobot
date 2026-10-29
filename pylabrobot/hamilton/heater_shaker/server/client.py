"""A heater shaker served elsewhere, driven as one in this process is.

Every public coroutine is a call to the server. A long call (a shake, a wait for temperature, a
hold) reads the progress the server streams until it says the call is done. What the class holds
without a call (its index, its plate holder, the temperature it was set to) is the server's
description, taken up again whenever a response says it changed.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Awaitable, Dict, Mapping, Optional, Sequence, TypeVar, Union

from connectrpc.client import ResponseMetadata
from connectrpc.errors import ConnectError
from pyqwest import Client

from pylabrobot.hamilton.heater_shaker.heater_shaker import (
  Direction,
  FirmwareLink,
  HamiltonHeaterShaker,
  _resource_server,
)
from pylabrobot.hamilton.heater_shaker.server.errors import from_connect_error
from pylabrobot.hamilton.heater_shaker.server.serve import REVISION_HEADER, heater_shaker_server_app
from pylabrobot.hamilton.heater_shaker.server.v1 import heater_shaker_pb2 as pb
from pylabrobot.hamilton.heater_shaker.server.v1.heater_shaker_connect import (
  HeaterShakerServiceClient,
)
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.asgi_transport import ASGITransport
from pylabrobot.resources.server.client import ResourceServer, _Headers

# The address a heater shaker server held in this process is spoken to at; never dialled.
_IN_PROCESS = "http://heater-shaker.in-process"

R = TypeVar("R")


class HeaterShakerServer:
  """A heater shaker server: where heater shakers are served, and how their calls get there.

  `connect` reaches one served elsewhere; `local` serves heater shakers in this process, without a
  socket, as tests do.
  """

  def __init__(
    self, address: str, http: Optional[Client] = None, headers: Optional[Mapping[str, str]] = None
  ):
    interceptors = [_Headers(headers)] if headers else []
    self.client = HeaterShakerServiceClient(address, http_client=http, interceptors=interceptors)
    # Each heater shaker the server holds, as last described, and which description that was.
    self.described: Dict[str, pb.HeaterShaker] = {}
    self.revision: Optional[str] = None
    self._describing: Optional[asyncio.Lock] = None

  @classmethod
  def connect(cls, url: str, headers: Optional[Mapping[str, str]] = None) -> HeaterShakerServer:
    """A heater shaker server at `url`, "http://127.0.0.1:8082" say.

    Args:
      headers: sent with every call: the credentials the server asks for.
    """
    return cls(url, Client(), headers=headers)

  @classmethod
  def local(cls, heater_shakers: Sequence[HamiltonHeaterShaker]) -> HeaterShakerServer:
    """Heater shakers served in this process, spoken to over Connect without a socket."""
    app = heater_shaker_server_app(heater_shakers)
    return cls(_IN_PROCESS, Client(transport=ASGITransport(app)))

  async def close(self) -> None:
    await self.client.close()

  def _raised(self, error: ConnectError) -> BaseException:
    """What the served heater shaker raised, from the Connect error it came as."""
    return from_connect_error(error) or error

  async def call(self, response: Awaitable[R]) -> R:
    """A call's response, raising what the served heater shaker raised as it raised it."""
    with ResponseMetadata() as meta:
      try:
        result = await response
      except ConnectError as error:
        raise self._raised(error) from None
      finally:
        revision = meta.headers.get(REVISION_HEADER)
    await self._take_up(revision)
    return result

  async def stream(self, progress: AsyncIterator[pb.Progress], what: str) -> None:
    """Read a long call's progress until the server says it is done.

    Raises:
      ConnectionError: If the stream ends before the call is done.
    """
    done = False
    with ResponseMetadata() as meta:
      try:
        async for each in progress:
          done = done or each.done
      except ConnectError as error:
        raise self._raised(error) from None
      finally:
        revision = meta.headers.get(REVISION_HEADER)
    await self._take_up(revision)
    if not done:
      raise ConnectionError(f"the heater shaker server stopped before {what} was done")

  async def _take_up(self, revision: Optional[str]) -> None:
    """Ask for the description again when the server says it changed."""
    if revision is not None and revision != self.revision:
      await self.refresh()

  async def refresh(self) -> None:
    """Take up the description of the heater shakers as the server has it now."""
    if self._describing is None:
      self._describing = asyncio.Lock()
    async with self._describing:
      with ResponseMetadata() as meta:
        try:
          response = await self.client.describe(pb.DescribeRequest())
        except ConnectError as error:
          raise self._raised(error) from None
      self.described = {hs.name: hs for hs in response.heater_shakers}
      self.revision = meta.headers.get(REVISION_HEADER)


def _server(server: Union[str, HeaterShakerServer]) -> HeaterShakerServer:
  return HeaterShakerServer.connect(server) if isinstance(server, str) else server


class RemoteHamiltonHeaterShaker(HamiltonHeaterShaker):
  """The heater shaker of a name a heater shaker server serves: every public coroutine is a call.

  Its index and plate holder are the server's, known once setup has run.
  """

  def __init__(
    self,
    name: str,
    index: Optional[int] = None,
    interface: Optional[FirmwareLink] = None,
    resource_server: Union[str, ResourceServer, None] = None,
    heater_shaker_server: Union[str, HeaterShakerServer, None] = None,
  ):
    """
    Raises:
      ValueError: If given an index or an interface: the server decides those.
    """
    if heater_shaker_server is None:
      raise ValueError("a served heater shaker needs heater_shaker_server")
    if index is not None or interface is not None:
      raise ValueError(
        "a served heater shaker is what its server makes it: index and interface cannot be given "
        "with heater_shaker_server"
      )
    self.name = name
    self.index = None
    self.resource_server = _resource_server(resource_server)
    self.resource: Optional[handles.PlateHolder] = None
    self.server = _server(heater_shaker_server)

  @property  # type: ignore[override]
  def target_temperature(self) -> Optional[float]:
    """The temperature the server's heater shaker was set to, in Celsius; None when none is."""
    described = self.server.described.get(self.name)
    if described is None or not described.HasField("target_temperature"):
      return None
    return described.target_temperature

  @target_temperature.setter
  def target_temperature(self, value: Optional[float]) -> None:
    raise AttributeError(
      "target_temperature is the served heater shaker's: set_temperature sets it"
    )

  async def _take_up(self) -> None:
    """Take up its index and plate holder from the server's description.

    Raises:
      ValueError: If the server serves none of its name, or it has a plate holder and this has
        no resource server to find it in.
    """
    await self.server.refresh()
    described = self.server.described.get(self.name)
    if described is None:
      raise ValueError(f"the server serves no heater shaker named '{self.name}'")
    self.index = described.index
    if not described.HasField("resource"):
      self.resource = None
      return
    if self.resource_server is None:
      raise ValueError(
        f"heater shaker '{self.name}' has a plate holder: give resource_server to find it"
      )
    resource = await self.resource_server.get_by_id(described.resource.id)
    if not isinstance(resource, handles.PlateHolder):
      raise ValueError(f"heater shaker '{self.name}' is a {type(resource).__name__}")
    self.resource = resource

  async def setup(self) -> None:
    await self.server.call(self.server.client.setup(pb.SetupRequest(name=self.name)))
    await self._take_up()

  async def stop(self) -> None:
    await self.server.call(self.server.client.stop(pb.StopRequest(name=self.name)))

  async def lock_plate(self) -> None:
    await self.server.call(self.server.client.lock_plate(pb.LockPlateRequest(name=self.name)))

  async def unlock_plate(self) -> None:
    await self.server.call(self.server.client.unlock_plate(pb.UnlockPlateRequest(name=self.name)))

  async def get_is_shaking(self) -> bool:
    response = await self.server.call(
      self.server.client.get_is_shaking(pb.GetIsShakingRequest(name=self.name))
    )
    return response.shaking

  async def shake(
    self,
    speed: float,
    duration: Optional[float] = None,
    direction: Direction = 0,
    acceleration: int = 1_000,
    timeout: Optional[float] = 30,
  ) -> None:
    request = pb.ShakeRequest(
      name=self.name, speed=speed, direction=direction, acceleration=acceleration
    )
    if duration is not None:
      request.duration = duration
    request.timeout.SetInParent()
    if timeout is not None:
      request.timeout.value = timeout
    await self.server.stream(self.server.client.shake(request), "the shake")

  async def stop_shaking(self) -> None:
    await self.server.call(self.server.client.stop_shaking(pb.StopShakingRequest(name=self.name)))

  async def get_temperature(self) -> float:
    response = await self.server.call(
      self.server.client.get_temperature(pb.GetTemperatureRequest(name=self.name))
    )
    return response.temperature

  async def get_edge_temperature(self) -> float:
    response = await self.server.call(
      self.server.client.get_edge_temperature(pb.GetEdgeTemperatureRequest(name=self.name))
    )
    return response.temperature

  async def set_temperature(self, temperature: float, passive: bool = False) -> None:
    request = pb.SetTemperatureRequest(name=self.name, temperature=temperature, passive=passive)
    await self.server.call(self.server.client.set_temperature(request))

  async def wait_for_temperature(self, timeout: float = 300.0, tolerance: float = 0.5) -> None:
    request = pb.WaitForTemperatureRequest(name=self.name, timeout=timeout, tolerance=tolerance)
    await self.server.stream(
      self.server.client.wait_for_temperature(request), "the wait for temperature"
    )

  async def hold_temperature(self, duration: float) -> None:
    request = pb.HoldTemperatureRequest(name=self.name, duration=duration)
    await self.server.stream(self.server.client.hold_temperature(request), "the hold")

  async def deactivate(self) -> None:
    await self.server.call(self.server.client.deactivate(pb.DeactivateRequest(name=self.name)))
