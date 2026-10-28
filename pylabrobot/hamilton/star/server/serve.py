"""Serving a STAR: one Connect application for every service of one device."""

import asyncio
import hashlib
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from google.protobuf.message import Message

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.features.autoload import Autoload
from pylabrobot.hamilton.star.driver.features.core_grippers import CoreGrippers
from pylabrobot.hamilton.star.driver.features.cover import FrontCover
from pylabrobot.hamilton.star.driver.features.head96 import Head96
from pylabrobot.hamilton.star.driver.features.head384 import Head384
from pylabrobot.hamilton.star.driver.features.iswap import iSWAP
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.driver.master import STARDriver
from pylabrobot.hamilton.star.server import wire
from pylabrobot.hamilton.star.server.description import describe
from pylabrobot.hamilton.star.server.errors import to_connect_error
from pylabrobot.hamilton.star.server.generated_handlers import ASGIApp, applications
from pylabrobot.hamilton.star.server.settings import Settings, put_in_place
from pylabrobot.hamilton.star.server.v1 import description_pb2 as dpb
from pylabrobot.hamilton.star.server.v1 import types_pb2 as tpb
from pylabrobot.resources.server.memory import asgi_app as resource_server_app

# The response header that says which description of the device is current.
REVISION_HEADER = "star-description-revision"

R = TypeVar("R")
F = TypeVar("F")


class Served:
  """One device, served: each call made on the device, and the description of it kept current."""

  def __init__(self, device: STARDevice, settings: Optional[Settings]):
    self.device = device
    self.settings = settings
    self._digest: Optional[bytes] = None
    self.revision = 0

  # -- what a call is made on --

  def driver(self) -> STARDriver:
    return self.device.driver

  def _on_an_arm(self, name: str, pick: Callable[[XArm], Optional[F]]) -> F:
    for arm in self.device.driver.arms:
      feature = pick(arm)
      if feature is not None:
        return feature
    raise ConnectError(Code.FAILED_PRECONDITION, f"the device has no {name}; has setup run?")

  def pipettes(self) -> Pipettes:
    return self._on_an_arm("pipettes", lambda arm: arm.pipettes)

  def head96(self) -> Head96:
    return self._on_an_arm("head96", lambda arm: arm.head96)

  def head384(self) -> Head384:
    return self._on_an_arm("head384", lambda arm: arm.head384)

  def iswap(self) -> iSWAP:
    return self._on_an_arm("iswap", lambda arm: arm.iswap)

  def core_grippers(self) -> CoreGrippers:
    return self._on_an_arm("core_grippers", lambda arm: arm.core_grippers)

  def autoload(self) -> Autoload:
    if self.device.driver.autoload is None:
      raise ConnectError(Code.FAILED_PRECONDITION, "the device has no autoload; has setup run?")
    return self.device.driver.autoload

  def front_cover(self) -> FrontCover:
    if self.device.driver.front_cover is None:
      raise ConnectError(Code.FAILED_PRECONDITION, "the device has no front_cover; has setup run?")
    return self.device.driver.front_cover

  def x_arm(self, side: tpb.XArmSide) -> XArm:
    driver = self.device.driver
    arm: Optional[XArm] = None
    if side == tpb.X_ARM_SIDE_LEFT:
      arm = driver.left_x_arm
    elif side == tpb.X_ARM_SIDE_RIGHT:
      arm = driver.right_x_arm
    if arm is None:
      raise ConnectError(
        Code.FAILED_PRECONDITION, f"the device has no {tpb.XArmSide.Name(side)} X-arm"
      )
    return arm

  # -- making a call --

  async def refs(self, request: Message) -> wire.Refs:
    """The handle of every resource a request names."""
    return await wire.refs_in(self.device.resource_server, request)

  def stamp(self, ctx: RequestContext[Any, Any]) -> None:
    """Say which description is current, moving the revision on when it changed."""
    digest = hashlib.sha256(describe(self.device).SerializeToString(deterministic=True)).digest()
    if digest != self._digest:
      self._digest = digest
      self.revision += 1
    ctx.response_headers[REVISION_HEADER] = str(self.revision)

  async def run(
    self, ctx: RequestContext[Any, Any], call: Callable[[], Awaitable[R]], setup: bool = False
  ) -> R:
    """Make a call, raising what it raised as a Connect error, and say which description is
    current. After a setup, the settings are put in place again."""
    try:
      result = await call()
      if setup:
        put_in_place(self.device, self.settings)
      return result
    except ConnectError:
      raise
    except Exception as error:
      raise to_connect_error(error) from error
    finally:
      self.stamp(ctx)

  async def describe(self, ctx: RequestContext[Any, Any]) -> dpb.Description:
    self.stamp(ctx)
    return describe(self.device)


def star_server_app(device: STARDevice, settings: Optional[Settings] = None) -> ASGIApp:
  """One ASGI application serving every STAR service for a device.

  Args:
    device: the device to serve.
    settings: the defaults the device's features use where a call names none, put in place now
      and after every setup. Those not given keep the defaults in the code.
  """
  put_in_place(device, settings)
  apps = applications(Served(device, settings))

  async def app(scope: Dict[str, Any], receive: Any, send: Any) -> None:
    path = scope.get("path", "") if scope.get("type") == "http" else ""
    for prefix, application in apps.items():
      if path.startswith(prefix):
        await application(scope, receive, send)
        return
    if scope.get("type") == "http":
      await send({"type": "http.response.start", "status": 404, "headers": []})
      await send({"type": "http.response.body", "body": b""})

  return app


async def serve(
  device: STARDevice,
  host: str = "127.0.0.1",
  port: int = 8081,
  resource_port: Optional[int] = None,
  settings: Optional[Settings] = None,
) -> None:
  """Serve a device until cancelled. Needs uvicorn, the `server` extra.

  Args:
    device: the device to serve.
    host: the address to listen on.
    port: the port the STAR server listens on.
    resource_port: a port to serve the device's resource server on as well, when it is held in
      this process; not served when not given.
    settings: as `star_server_app` takes them.

  Raises:
    ValueError: If given a `resource_port` for a resource server that is not held in this process.
  """
  import uvicorn

  apps: List[Tuple[ASGIApp, int]] = [(star_server_app(device, settings), port)]
  if resource_port is not None:
    if device.resource_server.memory is None:
      raise ValueError("only a resource server held in this process can be served with the STAR")
    apps.append((resource_server_app(device.resource_server.memory), resource_port))
  await asyncio.gather(
    *(uvicorn.Server(uvicorn.Config(app, host=host, port=p)).serve() for app, p in apps)
  )
