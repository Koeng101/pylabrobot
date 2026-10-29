"""Hamilton Heater Shaker (HHS): heats and shakes the plate on it, and locks it in place.

A heater shaker is plugged into a STAR's TCC port or into a Hamilton Heater Shaker Box, and takes
its commands through whichever it is plugged into, addressed to module `T<index>`. It needs only
something that sends those commands (`FirmwareLink`): a STAR's driver, local or served, has that.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Literal, Optional, Protocol, Union

from pylabrobot.resources.hamilton.heater_shakers import HEATER_SHAKER_CATEGORY
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.client import ResourceServer
from pylabrobot.resources.server.v1 import server_pb2 as spb

if TYPE_CHECKING:
  from pylabrobot.hamilton.heater_shaker.server.client import HeaterShakerServer

logger = logging.getLogger(__name__)

# What the firmware takes, as the heater shaker's commands check it.
SPEED_RANGE = (20, 2_000)
ACCELERATION_RANGE = (500, 10_000)
MAXIMUM_TEMPERATURE = 105.0

# How often a wait reads the temperature, in seconds.
POLL_INTERVAL = 1.0

Direction = Literal[0, 1]


class FirmwareLink(Protocol):
  """What a heater shaker is plugged into: it sends a command to a module and returns the reply."""

  async def send_command(self, module: str, command: str, **kwargs: Any) -> Any: ...


def _resource_server(server: Union[str, ResourceServer, None]) -> Optional[ResourceServer]:
  if isinstance(server, str):
    return ResourceServer.connect(server)
  return server


def _temperatures(reply: str) -> tuple[float, float]:
  """The middle and edge temperatures a `RT` reply gives, `...rt+0256 +0257` say, in Celsius."""
  middle, edge = reply.split("rt")[1].split(" ")[:2]
  return float(middle.strip("+")) / 10, float(edge.strip("+")) / 10


class HamiltonHeaterShaker:
  """A Hamilton Heater Shaker.

  Given `heater_shaker_server`, a server or its URL, it is the heater shaker of this name that
  server serves instead, with the same methods, each a call to the server. Then the server decides
  its index and what it is plugged into, and `resource_server` is where its plate holder is.

  Attributes:
    name: its name, and the name of its plate holder in the resource server.
    index: the port it is plugged into: 1 is module `T1`.
    resource: its plate holder: where a plate is put on it. None until setup has found it, and
      when it has no resource server.
    target_temperature: the temperature `set_temperature` set, in Celsius; None when none is.
  """

  def __new__(cls, *args: Any, **kwargs: Any) -> HamiltonHeaterShaker:
    if cls is HamiltonHeaterShaker and kwargs.get("heater_shaker_server") is not None:
      from pylabrobot.hamilton.heater_shaker.server.client import RemoteHamiltonHeaterShaker

      return super().__new__(RemoteHamiltonHeaterShaker)
    return super().__new__(cls)

  def __init__(
    self,
    name: str,
    index: Optional[int] = None,
    interface: Optional[FirmwareLink] = None,
    resource_server: Union[str, ResourceServer, None] = None,
    heater_shaker_server: Union[str, HeaterShakerServer, None] = None,
  ):
    """
    Args:
      name: its name. Its plate holder is the resource of this name in the resource server, made
        from the `hamilton_heater_shaker` model and put on the deck before setup.
      index: the port it is plugged into, from 1.
      interface: what it is plugged into: a STAR's driver (`star.driver`) say.
      resource_server: where its plate holder is, or its URL. Without one it has no resource.
      heater_shaker_server: a heater shaker server, or its URL, serving one of this name.

    Raises:
      ValueError: If not served and not given an index of 1 or more and an interface.
    """
    if index is None or interface is None:
      raise ValueError("a heater shaker needs the index it is plugged into and an interface")
    if index < 1:
      raise ValueError(f"a heater shaker's index is 1 or more, not {index}")
    self.name = name
    self.index: Optional[int] = index
    self.interface = interface
    self.resource_server = _resource_server(resource_server)
    self.resource: Optional[handles.PlateHolder] = None
    self.target_temperature: Optional[float] = None

  async def _send(self, command: str, **kwargs: Any) -> str:
    """Send a command to this heater shaker and return its reply."""
    reply = await self.interface.send_command(module=f"T{self.index}", command=command, **kwargs)
    return str(reply)

  async def _find_resource(self) -> handles.PlateHolder:
    """Its plate holder: the one resource of its name that is a heater shaker.

    Raises:
      ValueError: If there is none, or more than one.
    """
    assert self.resource_server is not None
    found = await self.resource_server.find_resources(
      spb.ResourceFilter(names=[self.name], categories=[HEATER_SHAKER_CATEGORY])
    )
    if not found:
      raise ValueError(
        f"no heater shaker named '{self.name}' in the resource server: put one there, made from "
        f"the 'hamilton_heater_shaker' model, before setup"
      )
    if len(found) > 1:
      raise ValueError(
        f"{len(found)} heater shakers are named '{self.name}' in the resource server"
      )
    resource = found[0]
    if not isinstance(resource, handles.PlateHolder):
      raise ValueError(f"'{self.name}' is a {type(resource).__name__}, not a plate holder")
    return resource

  async def setup(self) -> None:
    """Find its plate holder, then initialize the plate lock and home the shaker drive.

    Run it after setting up what it is plugged into.

    Raises:
      ValueError: If it has a resource server and its plate holder is not there.
    """
    logger.warning(
      "HamiltonHeaterShaker has not been run on a device; please report how it goes, or send a "
      "fix, once you have run it on one."
    )
    if self.resource_server is not None:
      self.resource = await self._find_resource()
    await self._send("LI")
    await self._send("SI")
    logger.info("heater shaker '%s' (T%s) set up", self.name, self.index)

  async def stop(self) -> None:
    """Turn the heating off and stop shaking."""
    await self.deactivate()
    await self.stop_shaking()

  # -- the plate lock ----------------------------------------------------------------------------

  async def lock_plate(self) -> None:
    """Lock the plate in place."""
    await self._send("LP", lp=1)

  async def unlock_plate(self) -> None:
    """Unlock the plate, so it can be taken off."""
    await self._send("LP", lp=0)

  # -- shaking -----------------------------------------------------------------------------------

  async def get_is_shaking(self) -> bool:
    """Whether it is shaking."""
    return (await self._send("RD")).endswith("1")

  async def _start_shaking(
    self, speed: float, direction: Direction, acceleration: int, timeout: Optional[float]
  ) -> None:
    """Start shaking, asking again until it is.

    Raises:
      ValueError: If the speed, direction or acceleration is out of range.
      TimeoutError: If it has not started within `timeout` seconds.
    """
    int_speed = int(speed)
    if not SPEED_RANGE[0] <= int_speed <= SPEED_RANGE[1]:
      raise ValueError(f"speed must be between {SPEED_RANGE[0]} and {SPEED_RANGE[1]}, not {speed}")
    if direction not in (0, 1):
      raise ValueError(f"direction must be 0 or 1, not {direction}")
    if not ACCELERATION_RANGE[0] <= acceleration <= ACCELERATION_RANGE[1]:
      raise ValueError(
        f"acceleration must be between {ACCELERATION_RANGE[0]} and {ACCELERATION_RANGE[1]}, "
        f"not {acceleration}"
      )
    start = time.monotonic()
    while True:
      await self._send(
        "SB", st=direction, sv=str(int_speed).zfill(4), sr=str(acceleration).zfill(5)
      )
      if await self.get_is_shaking():
        return
      if timeout is not None and time.monotonic() - start > timeout:
        raise TimeoutError(f"heater shaker '{self.name}' did not start shaking in {timeout} s")

  async def shake(
    self,
    speed: float,
    duration: Optional[float] = None,
    direction: Direction = 0,
    acceleration: int = 1_000,
    timeout: Optional[float] = 30,
  ) -> None:
    """Lock the plate and shake it.

    Args:
      speed: the speed, in rpm.
      duration: how long to shake, in seconds, after which it stops and unlocks the plate. When
        None it keeps shaking, and this returns once it has started.
      direction: which way it turns: 0 or 1, as the firmware numbers them.
      acceleration: how fast it comes up to speed, in the firmware's increments per second.
      timeout: how long to keep asking it to start, in seconds; None keeps asking.

    Raises:
      ValueError: If the speed, direction or acceleration is out of range.
      TimeoutError: If it has not started within `timeout` seconds.
    """
    await self.lock_plate()
    await self._start_shaking(speed, direction, acceleration, timeout)
    if duration is None:
      return
    await asyncio.sleep(duration)
    await self.stop_shaking()
    await self.unlock_plate()

  async def stop_shaking(self) -> None:
    """Stop shaking, and wait until it has."""
    await self._send("SC")
    await self._send("SW")

  # -- temperature -------------------------------------------------------------------------------

  async def get_temperature(self) -> float:
    """The temperature in the middle of it, in Celsius."""
    return _temperatures(await self._send("RT"))[0]

  async def get_edge_temperature(self) -> float:
    """The temperature at its edge, in Celsius."""
    return _temperatures(await self._send("RT"))[1]

  async def set_temperature(self, temperature: float, passive: bool = False) -> None:
    """Heat to a temperature, and hold it there.

    It cannot cool. Below its temperature, it either waits to cool down by itself (`passive`) or
    refuses.

    Args:
      temperature: the temperature, in Celsius.
      passive: when cooler than it is now, let it cool down by itself rather than refuse.

    Raises:
      ValueError: If the temperature is not above 0 and at most 105, or is below its temperature
        and not `passive`.
    """
    if not 0 < temperature <= MAXIMUM_TEMPERATURE:
      raise ValueError(f"temperature must be above 0 and at most {MAXIMUM_TEMPERATURE}")
    current = await self.get_temperature()
    self.target_temperature = temperature
    if temperature < current:
      if passive:
        return
      raise ValueError(
        "a heater shaker cannot cool: use passive=True to let it cool down by itself, or set a "
        "higher temperature"
      )
    await self._send("TA", ta=f"{round(10 * temperature):04d}")

  async def wait_for_temperature(self, timeout: float = 300.0, tolerance: float = 0.5) -> None:
    """Wait until it is at the temperature `set_temperature` set.

    Args:
      timeout: how long to wait, in seconds.
      tolerance: how close counts, in Celsius.

    Raises:
      RuntimeError: If no temperature has been set.
      TimeoutError: If it is not there within `timeout`.
    """
    if self.target_temperature is None:
      raise RuntimeError("no temperature has been set")
    start = time.monotonic()
    while time.monotonic() - start < timeout:
      if abs(await self.get_temperature() - self.target_temperature) < tolerance:
        return
      await asyncio.sleep(POLL_INTERVAL)
    raise TimeoutError(f"heater shaker '{self.name}' did not reach temperature in {timeout} s")

  async def hold_temperature(self, duration: float) -> None:
    """Hold the temperature it is at for a while, without changing it.

    Args:
      duration: how long, in seconds.

    Raises:
      ValueError: If the duration is negative.
    """
    if duration < 0:
      raise ValueError("a hold's duration cannot be negative")
    await asyncio.sleep(duration)

  async def deactivate(self) -> None:
    """Turn the heating off."""
    self.target_temperature = None
    await self._send("TO")
