"""A STAR served elsewhere, driven as one in this process is.

The device, its driver and its features are the same classes, every public coroutine a call to
the STAR server (`generated_remote.py`). What their attributes hold - configurations, and the
resources their parts are - is kept from the server's description of the device, taken up again
whenever the server says it changed. Resources are handles on the resource server both ends use.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Dict, List, Mapping, Optional, Tuple, TypeVar, Union

from connectrpc.client import ResponseMetadata
from connectrpc.errors import ConnectError
from pyqwest import Client

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.configuration import DeviceConfiguration
from pylabrobot.hamilton.star.driver.features.autoload import Autoload
from pylabrobot.hamilton.star.driver.features.cover import FrontCover
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.server.errors import from_connect_error
from pylabrobot.hamilton.star.server.generated_remote import (
  RemoteAutoload,
  RemoteCoreGrippers,
  RemoteFrontCover,
  RemoteHead96,
  RemoteHead384,
  RemoteISWAP,
  RemotePipettes,
  RemoteXArm,
  STARClients,
  _RemoteSTARDeviceCalls,
  _RemoteSTARDriverCalls,
)
from pylabrobot.hamilton.star.server.serve import REVISION_HEADER, star_server_app
from pylabrobot.hamilton.star.server.settings import Settings
from pylabrobot.hamilton.star.server.v1 import description_pb2 as dpb
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.asgi_transport import ASGITransport
from pylabrobot.resources.server.client import ResourceServer, _Headers

# The address a STAR server held in this process is spoken to at; never dialled.
_IN_PROCESS = "http://star.in-process"

R = TypeVar("R")


class STARServer:
  """A STAR server: where a device is served, and how its calls get there.

  `connect` reaches one served elsewhere; `local` serves a device in this process, without a
  socket, as tests do.
  """

  def __init__(
    self, address: str, http: Optional[Client] = None, headers: Optional[Mapping[str, str]] = None
  ):
    interceptors: List[_Headers] = [_Headers(headers)] if headers else []
    self.clients = STARClients(address, http, interceptors)
    self.revision: Optional[str] = None
    self.device: Optional[RemoteSTARDevice] = None
    self._describing: Optional[asyncio.Lock] = None

  @classmethod
  def connect(cls, url: str, headers: Optional[Mapping[str, str]] = None) -> STARServer:
    """A STAR server at `url`, "http://127.0.0.1:8081" say.

    Args:
      headers: sent with every call: the credentials the server asks for.
    """
    return cls(url, Client(), headers=headers)

  @classmethod
  def local(cls, device: STARDevice, settings: Optional[Settings] = None) -> STARServer:
    """A device served in this process, spoken to over Connect without a socket.

    Args:
      settings: as `star_server_app` takes them.
    """
    app = star_server_app(device, settings)
    return cls(_IN_PROCESS, Client(transport=ASGITransport(app)))

  async def close(self) -> None:
    await self.clients.close()

  async def call(self, response: Awaitable[R]) -> R:
    """A call's response, raising what the served device raised as it raised it; the device's
    description taken up again when the server says it changed."""
    with ResponseMetadata() as meta:
      try:
        result = await response
      except ConnectError as error:
        raised = from_connect_error(error)
        await self._take_up(meta)
        if raised is None:
          raise
        raise raised from None
    await self._take_up(meta)
    return result

  async def _take_up(self, meta: ResponseMetadata) -> None:
    """Ask for the device's description again when the server says it changed."""
    revision = meta.headers.get(REVISION_HEADER)
    if revision is None or revision == self.revision or self.device is None:
      return
    await self.refresh()

  async def refresh(self) -> None:
    """Take up the device's description as the server has it now."""
    from pylabrobot.hamilton.star.server.description import apply

    if self._describing is None:
      self._describing = asyncio.Lock()
    async with self._describing:
      with ResponseMetadata() as meta:
        description = await self.clients.star.describe(dpb.DescribeRequest())
      assert self.device is not None
      await apply(self.device, description)
      self.revision = meta.headers.get(REVISION_HEADER)


class RemoteSTARDriver(_RemoteSTARDriverCalls):
  """A STAR driver served elsewhere. What it holds is the server's driver's, as last described."""

  def __init__(self, star_server: STARServer):
    # Not the driver's own: there is no link here to open.
    self._star_server = star_server
    self.io = None  # type: ignore[assignment]
    self.declared_configuration_json = None
    self.declared: Dict[str, object] = {}
    self._num_channels: Optional[int] = None
    self._connected = False
    self.left_side_panel_installed = False
    self.deck: Optional[handles.Deck] = None
    self.configuration: Optional[DeviceConfiguration] = None
    self.firmware: Dict[str, str] = {}
    self._tip_type_indices: Dict[str, int] = {}
    self.front_cover: Optional[FrontCover] = None
    self.left_x_arm: Optional[XArm] = None
    self.right_x_arm: Optional[XArm] = None
    self.autoload: Optional[Autoload] = None


class RemoteSTARDevice(_RemoteSTARDeviceCalls):
  """A STAR served elsewhere: its body, its deck and what it carries are the server's device's."""

  def __init__(self, star_server: STARServer, resource_server: ResourceServer, model: str):
    # Not the device's own: the server's device holds what it is.
    self._star_server = star_server
    self._expected_model = model
    self.name = ""
    self.model = model
    self.resource_server = resource_server
    self.extension_housing = False
    self.left_side_panel_installed = False
    self.body: Optional[handles.Resource] = None
    self.deck: Optional[handles.Deck] = None
    self.left_side_panel: Optional[handles.Resource] = None
    self.left_extension_housing: Optional[handles.Resource] = None
    self._num_tracks: Optional[int] = None
    self.driver: RemoteSTARDriver = RemoteSTARDriver(star_server)
    star_server.device = self


def remote_device(
  star_server: Union[str, STARServer],
  resource_server: Union[str, ResourceServer, None],
  model: str,
) -> RemoteSTARDevice:
  """A device a STAR server serves.

  Args:
    star_server: the server, or its URL.
    resource_server: the resource server the STAR server keeps the device's resources in, or its
      URL.
    model: the device the caller asked for; the server's has to be one.

  Raises:
    ValueError: If no resource server is given.
  """
  if resource_server is None:
    raise ValueError(
      "a served STAR needs resource_server= as well: the resource server its STAR server uses"
    )
  if isinstance(star_server, str):
    star_server = STARServer.connect(star_server)
  if isinstance(resource_server, str):
    resource_server = ResourceServer.connect(resource_server)
  return RemoteSTARDevice(star_server, resource_server, model)


__all__: Tuple[str, ...] = (
  "RemoteAutoload",
  "RemoteCoreGrippers",
  "RemoteFrontCover",
  "RemoteHead96",
  "RemoteHead384",
  "RemoteISWAP",
  "RemotePipettes",
  "RemoteSTARDevice",
  "RemoteSTARDriver",
  "RemoteXArm",
  "STARServer",
  "remote_device",
)
