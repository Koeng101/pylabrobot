"""Serving a STAR: one Connect application for every service of one device."""

import hashlib
import importlib
from typing import Any, Awaitable, Callable, Dict, Optional, cast

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from google.protobuf.message import Message

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.server import codec, services
from pylabrobot.hamilton.star.server.description import describe
from pylabrobot.hamilton.star.server.errors import to_connect_error
from pylabrobot.hamilton.star.server.settings import Settings, put_in_place
from pylabrobot.hamilton.star.server.v1 import types_pb2 as tpb
from pylabrobot.resources.server.memory import asgi_app as resource_server_app

# An ASGI 3 application.
ASGIApp = Callable[[Dict[str, Any], Any, Any], Awaitable[None]]

# The response header that says which description of the device is current.
REVISION_HEADER = "star-description-revision"

# The feature each feature service calls, by the attribute an arm or the driver holds it as.
_ON_AN_ARM = {
  "PipettesService": "pipettes",
  "Head96Service": "head96",
  "Head384Service": "head384",
  "ISwapService": "iswap",
  "CoreGrippersService": "core_grippers",
}
_ON_THE_DRIVER = {"AutoloadService": "autoload", "FrontCoverService": "front_cover"}

# The calls that make the device's features anew, after which the settings are put in place again.
_SETUP = {("STARService", "setup"), ("DriverService", "setup")}


class _Served:
  """One device, served: each call made on the device, and the description of it kept current."""

  def __init__(self, device: STARDevice, settings: Optional[Settings]):
    self.device = device
    self.settings = settings
    self._digest: Optional[bytes] = None
    self.revision = 0

  def target(self, service: str, request: Message) -> Any:
    """What a call is made on."""
    driver = self.device.driver
    if service == "STARService":
      return self.device
    if service == "DriverService":
      return driver
    if service == "XArmService":
      side = tpb.XArmSide.Name(getattr(request, "side"))
      arm = {"X_ARM_SIDE_LEFT": driver.left_x_arm, "X_ARM_SIDE_RIGHT": driver.right_x_arm}.get(side)
      if arm is None:
        raise ConnectError(Code.FAILED_PRECONDITION, f"the device has no {side} X-arm")
      return arm
    if service in _ON_AN_ARM:
      name = _ON_AN_ARM[service]
      for arm in driver.arms:
        feature = getattr(arm, name)
        if feature is not None:
          return feature
      raise ConnectError(Code.FAILED_PRECONDITION, f"the device has no {name}; has setup run?")
    name = _ON_THE_DRIVER[service]
    feature = getattr(driver, name)
    if feature is None:
      raise ConnectError(Code.FAILED_PRECONDITION, f"the device has no {name}; has setup run?")
    return feature

  def stamp(self, ctx: RequestContext[Any, Any]) -> None:
    """Say which description is current, moving the revision on when it changed."""
    digest = hashlib.sha256(describe(self.device).SerializeToString(deterministic=True)).digest()
    if digest != self._digest:
      self._digest = digest
      self.revision += 1
    ctx.response_headers[REVISION_HEADER] = str(self.revision)

  def handler(self, service: str, rpc: services.Rpc) -> Callable[..., Awaitable[Message]]:
    cls, _ = services.SERVICES[service]
    routing = services.ROUTING.get(service, ())

    async def call(request: Message, ctx: RequestContext[Any, Any]) -> Message:
      try:
        target = self.target(service, request)
        kwargs = codec.decode_request(cls, rpc.method, request, routing)
        kwargs = await codec.resolve(self.device.resource_server, kwargs)
        value = await getattr(target, rpc.method)(**kwargs)
        if (service, rpc.method) in _SETUP:
          put_in_place(self.device, self.settings)
        return cast(Message, codec.encode_response(cls, rpc.method, rpc.response(), value))
      except ConnectError:
        raise
      except Exception as error:
        raise to_connect_error(error) from error
      finally:
        self.stamp(ctx)

    return call

  def describe_handler(self) -> Callable[..., Awaitable[Message]]:
    async def call(request: Message, ctx: RequestContext[Any, Any]) -> Message:
      self.stamp(ctx)
      return describe(self.device)

    return call


class _Service:
  """A service's handlers, by the names the generated application calls them."""

  def __init__(self, handlers: Dict[str, Callable[..., Awaitable[Message]]]):
    self._handlers = handlers

  def __getattr__(self, name: str) -> Callable[..., Awaitable[Message]]:
    try:
      return self._handlers[name]
    except KeyError:
      raise AttributeError(name) from None


def star_server_app(
  device: STARDevice, serve_resources: bool = False, settings: Optional[Settings] = None
) -> ASGIApp:
  """One ASGI application serving every STAR service for a device.

  Args:
    device: the device to serve.
    serve_resources: whether to serve the device's resource server from the same application, so
      one URL reaches both. Only a resource server held in this process can be.
    settings: the defaults the device's features use where a call names none, put in place now
      and after every setup. Those not given keep the defaults in the code.
  """
  put_in_place(device, settings)
  served = _Served(device, settings)
  apps: Dict[str, ASGIApp] = {}
  for service in services.SERVICES:
    handlers = {
      rpc.connect_name: served.handler(service, rpc) for rpc in services.rpcs(service).values()
    }
    for name in services.extra_rpcs(service):
      rpc = services.extra_rpc(service, name)
      handlers[rpc.connect_name] = served.describe_handler()
    module = importlib.import_module(
      services.SERVICES[service][1].__name__.replace("_pb2", "_connect")
    )
    application = getattr(module, f"{service}ASGIApplication")(_Service(handlers))
    apps[f"/{services.descriptor(service).full_name}/"] = application
  resources: Optional[ASGIApp] = None
  if serve_resources:
    if device.resource_server.memory is None:
      raise ValueError("only a resource server held in this process can be served with the STAR")
    resources = resource_server_app(device.resource_server.memory)

  async def app(scope: Dict[str, Any], receive: Any, send: Any) -> None:
    path = scope.get("path", "") if scope.get("type") == "http" else ""
    for prefix, application in apps.items():
      if path.startswith(prefix):
        await application(scope, receive, send)
        return
    if resources is not None:
      await resources(scope, receive, send)
      return
    if scope.get("type") == "http":
      await send({"type": "http.response.start", "status": 404, "headers": []})
      await send({"type": "http.response.body", "body": b""})

  return app


async def serve(
  device: STARDevice,
  host: str = "127.0.0.1",
  port: int = 8081,
  serve_resources: bool = False,
  settings: Optional[Settings] = None,
) -> None:
  """Serve a device until cancelled. Needs uvicorn, the `server` extra.

  Args:
    device: the device to serve.
    host: the address to listen on.
    port: the port to listen on.
    serve_resources: as `star_server_app` takes it.
    settings: as `star_server_app` takes them.
  """
  import uvicorn

  config = uvicorn.Config(star_server_app(device, serve_resources, settings), host=host, port=port)
  await uvicorn.Server(config).serve()
