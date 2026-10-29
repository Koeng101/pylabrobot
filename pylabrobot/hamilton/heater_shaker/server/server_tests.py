import argparse
import asyncio
import importlib
import inspect
import logging
import unittest
from typing import Dict
from unittest import mock

from pylabrobot.hamilton.heater_shaker import heater_shaker
from pylabrobot.hamilton.heater_shaker.heater_shaker import HamiltonHeaterShaker
from pylabrobot.hamilton.heater_shaker.server import HeaterShakerServer, RemoteHamiltonHeaterShaker
from pylabrobot.hamilton.heater_shaker.server.__main__ import _named_index
from pylabrobot.hamilton.heater_shaker.server.v1 import heater_shaker_pb2 as pb
from pylabrobot.hamilton.heater_shaker.simulator import HeaterShakerSimulator
from pylabrobot.hamilton.star import STARlet
from pylabrobot.hamilton.star.server.client import RemoteSTARDriver, STARServer
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.server.client import ResourceServer


class ParityTests(unittest.TestCase):
  def test_every_public_coroutine_is_a_call(self):
    remote = dict(inspect.getmembers(RemoteHamiltonHeaterShaker, inspect.iscoroutinefunction))
    for name, method in inspect.getmembers(HamiltonHeaterShaker, inspect.iscoroutinefunction):
      if name.startswith("_"):
        continue
      with self.subTest(name):
        self.assertTrue(remote[name].__qualname__.startswith("RemoteHamiltonHeaterShaker."))
        self.assertEqual(inspect.signature(remote[name]), inspect.signature(method))


class ServedTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.resources = ResourceServer.local()
    self.made = await self.resources.create("hamilton_heater_shaker", "hhs_1")
    self.sim = HeaterShakerSimulator()
    served = HamiltonHeaterShaker(
      "hhs_1", index=2, interface=self.sim, resource_server=self.resources
    )
    self.server = HeaterShakerServer.local([served])
    self.hs = HamiltonHeaterShaker(
      "hhs_1", heater_shaker_server=self.server, resource_server=self.resources
    )

  def test_a_served_one_is_what_its_server_makes_it(self):
    self.assertIsInstance(self.hs, RemoteHamiltonHeaterShaker)
    with self.assertRaises(ValueError):
      HamiltonHeaterShaker("hhs_1", index=1, heater_shaker_server=self.server)

  async def test_setup_takes_up_the_servers_index_and_plate_holder(self):
    await self.hs.setup()
    self.assertEqual(self.hs.index, 2)
    self.assertEqual(self.hs.resource, self.made)
    self.assertEqual([c["module"] for c in self.sim.sent], ["T2", "T2"])

  async def test_calls_are_made_on_the_served_heater_shaker(self):
    await self.hs.set_temperature(40)
    self.assertEqual(await self.hs.get_temperature(), 40.0)
    self.assertEqual(await self.hs.get_edge_temperature(), 40.0)
    await self.hs.wait_for_temperature(timeout=1, tolerance=0.1)
    await self.hs.shake(1000, direction=1)
    self.assertTrue(await self.hs.get_is_shaking())
    self.assertEqual([c for c in self.sim.sent if c["command"] == "SB"][-1]["st"], 1)
    await self.hs.stop_shaking()
    await self.hs.unlock_plate()
    await self.hs.lock_plate()
    await self.hs.deactivate()
    self.assertEqual([c["command"] for c in self.sim.sent][-5:], ["SC", "SW", "LP", "LP", "TO"])

  async def test_errors_come_back_as_they_were_raised(self):
    with self.assertRaisesRegex(ValueError, "cannot cool"):
      await self.hs.set_temperature(40)
      await self.hs.set_temperature(30)
    with self.assertRaisesRegex(RuntimeError, "no temperature has been set"):
      await self.hs.deactivate()
      await self.hs.wait_for_temperature()

  async def test_a_name_the_server_does_not_serve_is_refused(self):
    other = HamiltonHeaterShaker("hhs_9", heater_shaker_server=self.server)
    with self.assertRaisesRegex(Exception, "hhs_9"):
      await other.lock_plate()

  async def test_a_plate_holder_needs_a_resource_server_to_be_found(self):
    hs = HamiltonHeaterShaker("hhs_1", heater_shaker_server=self.server)
    with self.assertRaisesRegex(ValueError, "resource_server"):
      await hs.setup()


# The module, which the package's `serve` function shadows.
serve = importlib.import_module("pylabrobot.hamilton.heater_shaker.server.serve")


class _Context:
  """What a handler is given, with its response headers."""

  def __init__(self) -> None:
    self.response_headers: Dict[str, str] = {}


class LongCallTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    patcher = mock.patch.object(serve, "PROGRESS_INTERVAL", 0.01)
    patcher.start()
    self.addCleanup(patcher.stop)
    self.sim = HeaterShakerSimulator()
    self.served_hs = HamiltonHeaterShaker("hhs_1", index=1, interface=self.sim)
    self.server = HeaterShakerServer.local([self.served_hs])
    self.hs = HamiltonHeaterShaker("hhs_1", heater_shaker_server=self.server)

  async def test_a_shake_for_a_duration_streams_until_it_is_done(self):
    await self.hs.shake(speed=900, duration=0.05)
    commands = [c["command"] for c in self.sim.sent]
    self.assertEqual(commands[-3:], ["SC", "SW", "LP"])
    self.assertEqual(self.sim.sent[-1]["lp"], 0)

  async def test_a_shake_finishes_on_the_server_when_its_client_goes(self):
    served = serve._Served([self.served_hs])
    progress = served.shake(pb.ShakeRequest(name="hhs_1", speed=900, duration=0.05), _Context())  # type: ignore[arg-type]
    first = await progress.__anext__()
    self.assertFalse(first.done)
    await progress.aclose()  # type: ignore[attr-defined]
    self.assertNotIn("SC", [c["command"] for c in self.sim.sent])
    await asyncio.sleep(0.2)
    self.assertEqual([c["command"] for c in self.sim.sent][-3:], ["SC", "SW", "LP"])

  async def test_a_wait_is_dropped_when_its_client_goes(self):
    patcher = mock.patch.object(heater_shaker, "POLL_INTERVAL", 0.01)
    patcher.start()
    self.addCleanup(patcher.stop)
    await self.served_hs.set_temperature(40)
    self.sim.heater_shakers["T1"].temperature = 25.0
    served = serve._Served([self.served_hs])
    request = pb.WaitForTemperatureRequest(name="hhs_1", timeout=10)
    progress = served.wait_for_temperature(request, _Context())  # type: ignore[arg-type]
    await progress.__anext__()
    await progress.aclose()  # type: ignore[attr-defined]
    await asyncio.sleep(0.01)
    reads = len(self.sim.sent)
    await asyncio.sleep(0.1)
    self.assertEqual(len(self.sim.sent), reads)

  async def test_a_shake_without_a_timeout_goes_over_as_none(self):
    target = mock.AsyncMock(spec=HamiltonHeaterShaker)
    target.name, target.index = "hhs_1", 1
    target.resource, target.target_temperature = None, None
    served = serve._Served([target])
    request = pb.ShakeRequest(name="hhs_1", speed=900)
    request.timeout.SetInParent()
    async for _ in served.shake(request, _Context()):  # type: ignore[arg-type]
      pass
    self.assertIsNone(target.shake.call_args.kwargs["timeout"])
    async for _ in served.shake(pb.ShakeRequest(name="hhs_1", speed=900), _Context()):  # type: ignore[arg-type]
      pass
    self.assertEqual(target.shake.call_args.kwargs["timeout"], 30)

  async def test_the_temperature_it_was_set_to_is_the_servers(self):
    self.assertIsNone(self.hs.target_temperature)
    await self.hs.set_temperature(40)
    self.assertEqual(self.hs.target_temperature, 40)
    await self.hs.hold_temperature(0.02)
    await self.hs.deactivate()
    self.assertIsNone(self.hs.target_temperature)
    with self.assertRaises(AttributeError):
      self.hs.target_temperature = 30  # type: ignore[misc]


class ThroughASTARServerTests(unittest.IsolatedAsyncioTestCase):
  async def test_commands_go_through_a_served_stars_driver_to_its_module(self):
    star = STARlet(simulation=True)
    await star.setup()
    await star.resource_server.create(
      "hamilton_heater_shaker",
      "hhs_1",
      parent=star.deck,
      location=Coordinate(72.24, 242.28, 107.44),
    )
    driver = RemoteSTARDriver(STARServer.local(star))
    served = HamiltonHeaterShaker(
      "hhs_1", index=1, interface=driver, resource_server=star.resource_server
    )
    hs = HamiltonHeaterShaker(
      "hhs_1",
      heater_shaker_server=HeaterShakerServer.local([served]),
      resource_server=star.resource_server,
    )
    with self.assertLogs("pylabrobot.hamilton.star.driver.simulator", logging.DEBUG - 5) as logs:
      await hs.setup()
      await hs.lock_plate()
    written = [line for line in logs.output if "write" in line]
    self.assertTrue(any("T1LI" in line for line in written))
    self.assertTrue(any("T1LPlp1" in line for line in written))
    self.assertEqual(await hs.resource.get_parent(), star.deck)  # type: ignore[union-attr]


class CommandLineTests(unittest.TestCase):
  def test_a_heater_shaker_is_named_with_its_index(self):
    self.assertEqual(_named_index("hhs_1:1"), ("hhs_1", 1))
    self.assertEqual(_named_index("a:b:2"), ("a:b", 2))
    for text in ("hhs_1", ":1", "hhs_1:x"):
      with self.assertRaises(argparse.ArgumentTypeError):
        _named_index(text)


if __name__ == "__main__":
  unittest.main()
