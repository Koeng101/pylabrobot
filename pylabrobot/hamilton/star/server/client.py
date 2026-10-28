"""A STAR served elsewhere, driven as one in this process is.

The device, its driver and its features are the same classes, every public coroutine a call to
the STAR server. What their attributes hold - configurations, and the resources their parts are -
is kept from the server's description of the device, taken up again whenever the server says it
changed. Resources are handles on the resource server both ends use.
"""

from __future__ import annotations

import asyncio
import functools
from typing import (
  Any,
  Dict,
  FrozenSet,
  Mapping,
  Optional,
  Sequence,
  Tuple,
  Type,
  TypeVar,
  Union,
  cast,
)

from connectrpc.client import ResponseMetadata
from connectrpc.errors import ConnectError
from pyqwest import Client

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.configuration import DeviceConfiguration
from pylabrobot.hamilton.star.driver.features.autoload import Autoload
from pylabrobot.hamilton.star.driver.features.core_grippers import CoreGrippers
from pylabrobot.hamilton.star.driver.features.cover import FrontCover
from pylabrobot.hamilton.star.driver.features.head96 import Head96
from pylabrobot.hamilton.star.driver.features.head384 import Head384
from pylabrobot.hamilton.star.driver.features.iswap import iSWAP
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.driver.master import STARDriver
from pylabrobot.hamilton.star.server import codec, services
from pylabrobot.hamilton.star.server.description import apply
from pylabrobot.hamilton.star.server.errors import from_connect_error
from pylabrobot.hamilton.star.server.serve import REVISION_HEADER, star_server_app
from pylabrobot.hamilton.star.server.settings import Settings
from pylabrobot.hamilton.star.server.v1 import description_pb2 as dpb
from pylabrobot.hamilton.star.server.v1 import types_pb2 as tpb
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.asgi_transport import ASGITransport
from pylabrobot.resources.server.client import ResourceServer, _Headers

# The address a STAR server held in this process is spoken to at; never dialled.
_IN_PROCESS = "http://star.in-process"


class STARServer:
  """A STAR server: where a device is served, and how its calls get there.

  `connect` reaches one served elsewhere; `local` serves a device in this process, without a
  socket, as tests do.
  """

  def __init__(
    self, address: str, http: Optional[Client] = None, headers: Optional[Mapping[str, str]] = None
  ):
    interceptors = [_Headers(headers)] if headers else []
    self.clients: Dict[str, Any] = {
      service: services.client_class(service)(address, http_client=http, interceptors=interceptors)
      for service in services.SERVICES
    }
    self._rpcs = {service: services.rpcs(service) for service in services.SERVICES}
    self.revision: Optional[str] = None
    self.device: Optional["RemoteSTARDevice"] = None
    self._describing: Optional[asyncio.Lock] = None

  @classmethod
  def connect(cls, url: str, headers: Optional[Mapping[str, str]] = None) -> "STARServer":
    """A STAR server at `url`, "http://127.0.0.1:8081" say.

    Args:
      headers: sent with every call: the credentials the server asks for.
    """
    return cls(url, Client(), headers=headers)

  @classmethod
  def local(cls, device: STARDevice, settings: Optional[Settings] = None) -> "STARServer":
    """A device served in this process, spoken to over Connect without a socket.

    Args:
      settings: as `star_server_app` takes them.
    """
    app = star_server_app(device, settings=settings)
    return cls(_IN_PROCESS, Client(transport=ASGITransport(app)))

  async def close(self) -> None:
    for client in self.clients.values():
      await client.close()

  async def call(
    self,
    service: str,
    cls: type,
    name: str,
    args: Sequence[Any],
    kwargs: Dict[str, Any],
    routing: Optional[Dict[str, Any]] = None,
  ) -> Any:
    """Make a call: `cls.name` with these arguments, on the instance `routing` says."""
    rpc = self._rpcs[service][name]
    request = codec.encode_request(cls, name, rpc.request(), args, kwargs)
    for field, value in (routing or {}).items():
      setattr(request, field, value)
    method = getattr(self.clients[service], rpc.connect_name)
    with ResponseMetadata() as meta:
      try:
        response = await method(request)
      except ConnectError as error:
        raised = from_connect_error(error)
        await self._take_up(meta)
        if raised is None:
          raise
        raise raised from None
    await self._take_up(meta)
    return codec.decode_response(cls, name, response)

  async def _take_up(self, meta: ResponseMetadata) -> None:
    """Ask for the device's description again when the server says it changed."""
    revision = meta.headers.get(REVISION_HEADER)
    if revision is None or revision == self.revision or self.device is None:
      return
    await self.refresh()

  async def refresh(self) -> None:
    """Take up the device's description as the server has it now."""
    if self._describing is None:
      self._describing = asyncio.Lock()
    async with self._describing:
      rpc = services.extra_rpc("STARService", "Describe")
      with ResponseMetadata() as meta:
        description = await getattr(self.clients["STARService"], rpc.connect_name)(
          dpb.DescribeRequest()
        )
      assert self.device is not None
      await apply(self.device, description)
      self.revision = meta.headers.get(REVISION_HEADER)


T = TypeVar("T")


def _remote(base: Type[T], service: str) -> Type[T]:
  """`base`, every method the server serves a call to it."""

  def make(name: str) -> Any:
    fn = getattr(base, name)

    @functools.wraps(fn)
    async def method(self: Any, *args: Any, **kwargs: Any) -> Any:
      return await self._star_server.call(service, base, name, args, kwargs, self._routing())

    return method

  namespace: Dict[str, Any] = {name: make(name) for name in services.served_methods(base)}
  namespace["__doc__"] = f"{base.__doc__ or ''}\n\nServed by a STAR server."
  namespace["_service"] = service
  namespace["_fixed"] = frozenset(services.setting_names(service)) | services.CONSTANTS.get(
    base, frozenset()
  )
  return cast(Type[T], type(f"Remote{base.__name__}", (base,), namespace))


class _Feature:
  """What every served feature knows: the server its driver calls, and that its settings and
  constants are not assigned here.

  Settings are the server's, from its settings file; constants are the code's. Assigning either on
  a client would change nothing the server does, so it is refused.
  """

  _driver: Any
  _service: str
  _fixed: FrozenSet[str]

  @property
  def _star_server(self) -> STARServer:
    return cast(STARServer, self._driver._star_server)

  def _routing(self) -> Dict[str, Any]:
    return {}

  def __setattr__(self, name: str, value: Any) -> None:
    if name in self._fixed and self.__dict__.get("_ready"):
      raise AttributeError(
        f"{name} is set where the STAR is served, in the STAR server's settings file, not on a "
        "client"
        if name in services.setting_names(self._service)
        else f"{name} is a constant of the STAR's code, not set on a client"
      )
    super().__setattr__(name, value)


class RemotePipettes(_Feature, _remote(Pipettes, "PipettesService")):  # type: ignore[misc]
  pass


class RemoteHead96(_Feature, _remote(Head96, "Head96Service")):  # type: ignore[misc]
  pass


class RemoteHead384(_Feature, _remote(Head384, "Head384Service")):  # type: ignore[misc]
  pass


class RemoteISWAP(_Feature, _remote(iSWAP, "ISwapService")):  # type: ignore[misc]
  pass


class RemoteCoreGrippers(_Feature, _remote(CoreGrippers, "CoreGrippersService")):  # type: ignore[misc]
  pass


class RemoteAutoload(_Feature, _remote(Autoload, "AutoloadService")):  # type: ignore[misc]
  pass


class RemoteFrontCover(_Feature, _remote(FrontCover, "FrontCoverService")):  # type: ignore[misc]
  pass


class RemoteXArm(_Feature, _remote(XArm, "XArmService")):  # type: ignore[misc]
  def _routing(self) -> Dict[str, Any]:
    return {"side": tpb.X_ARM_SIDE_LEFT if self.side == "left" else tpb.X_ARM_SIDE_RIGHT}


class RemoteSTARDriver(_remote(STARDriver, "DriverService")):  # type: ignore[misc]
  """A STAR driver served elsewhere. What it holds is the server's driver's, as last described."""

  def __init__(self, star_server: STARServer):
    # Not the driver's own: there is no link here to open.
    self._star_server = star_server
    self.io = None  # type: ignore[assignment]
    self.declared_configuration_json = None
    self.declared: Dict[str, Any] = {}
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

  def _routing(self) -> Dict[str, Any]:
    return {}


class RemoteSTARDevice(_remote(STARDevice, "STARService")):  # type: ignore[misc]
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
    self.driver = RemoteSTARDriver(star_server)
    star_server.device = self

  def _routing(self) -> Dict[str, Any]:
    return {}


def remote_device(
  star_server: Union[str, STARServer],
  resource_server: Union[str, ResourceServer, None],
  model: str,
) -> RemoteSTARDevice:
  """A device a STAR server serves.

  Args:
    star_server: the server, or its URL.
    resource_server: the resource server the device's resources are in, or its URL. Defaults to the
      STAR server's URL, where a server started with its resources serves them too.
    model: the device the caller asked for; the server's has to be one.
  """
  if isinstance(star_server, str):
    url: Optional[str] = star_server
    star_server = STARServer.connect(star_server)
  else:
    url = None
  if resource_server is None:
    if url is None:
      raise ValueError("give the resource server: there is no STAR server URL to default to")
    resource_server = url
  if isinstance(resource_server, str):
    resource_server = ResourceServer.connect(resource_server)
  return RemoteSTARDevice(star_server, resource_server, model)


__all__: Tuple[str, ...] = (
  "RemoteSTARDevice",
  "RemoteSTARDriver",
  "STARServer",
  "remote_device",
)
