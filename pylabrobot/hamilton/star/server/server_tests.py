"""A STAR driven through a STAR server: the same API, what the server keeps, and what it refuses."""

import asyncio
import importlib.util
import inspect
import json
import os
import socket
import tempfile
import unittest

from google.protobuf import json_format

from pylabrobot.hamilton.star import STAR, STARlet
from pylabrobot.hamilton.star.driver.errors import STARFirmwareError, check_fw_string_error
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.star.server import client, services
from pylabrobot.hamilton.star.server.client import STARServer, remote_device
from pylabrobot.hamilton.star.server.errors import from_connect_error, to_connect_error
from pylabrobot.hamilton.star.server.settings import Settings, read_settings
from pylabrobot.resources import hamilton_96_tiprack_300uL_filter, hamilton_tip_carrier_L5
from pylabrobot.resources.errors import NoTipError
from pylabrobot.resources.server.errors import ServerError
from pylabrobot.resources.server.v1 import types_pb2 as pb

_REMOTE = {
  "STARService": client.RemoteSTARDevice,
  "DriverService": client.RemoteSTARDriver,
  "PipettesService": client.RemotePipettes,
  "Head96Service": client.RemoteHead96,
  "Head384Service": client.RemoteHead384,
  "ISwapService": client.RemoteISWAP,
  "CoreGrippersService": client.RemoteCoreGrippers,
  "AutoloadService": client.RemoteAutoload,
  "XArmService": client.RemoteXArm,
  "FrontCoverService": client.RemoteFrontCover,
}


def _served_starlet():
  device = STARlet(simulation=True)
  return device, remote_device(STARServer.local(device), device.resource_server, "STARlet")


class ApiTests(unittest.TestCase):
  def test_every_method_is_served_with_its_own_signature(self):
    for service, (cls, _) in services.SERVICES.items():
      rpcs = services.rpcs(service)
      remote = _REMOTE[service]
      for name in services.served_methods(cls):
        with self.subTest(method=f"{cls.__name__}.{name}"):
          self.assertIn(name, rpcs)
          self.assertIsNot(getattr(remote, name), getattr(cls, name))
          self.assertEqual(
            inspect.signature(getattr(remote, name)), inspect.signature(getattr(cls, name))
          )
          self.assertEqual(getattr(remote, name).__doc__, getattr(cls, name).__doc__)


class ErrorTests(unittest.TestCase):
  def back(self, error: BaseException) -> BaseException:
    raised = from_connect_error(to_connect_error(error))
    assert raised is not None
    return raised

  def test_a_firmware_error_comes_back_module_by_module(self):
    with self.assertRaises(STARFirmwareError) as caught:
      check_fw_string_error("C0TPid0000er99/00 P308/75")
    error = caught.exception
    (module,) = error.errors
    error.errors[module].message += " (edited after it was raised)"
    raised = self.back(error)
    assert isinstance(raised, STARFirmwareError)
    self.assertEqual(str(raised), str(error))
    self.assertEqual(raised.raw_response, error.raw_response)
    self.assertIs(type(raised.errors[module]), type(error.errors[module]))

  def test_a_refusal_and_plain_errors_come_back_as_they_were(self):
    for error in (
      ServerError(pb.PROBLEM_NO_TIP, "no tip there", "A1"),
      NoTipError("tips_A1 holds no tip"),
      ValueError("channel must be in [0, 7], is 9"),
      KeyError("A13"),
      RuntimeError(),
    ):
      with self.subTest(error=repr(error)):
        raised = self.back(error)
        self.assertIs(type(raised), type(error))
        self.assertEqual(str(raised), str(error))
    refusal = self.back(ServerError(pb.PROBLEM_NO_TIP, "no tip there", "A1"))
    assert isinstance(refusal, ServerError)
    self.assertEqual((refusal.problem, refusal.resource_name), (pb.PROBLEM_NO_TIP, "A1"))


class ServedTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.device, self.star = _served_starlet()
    await self.star.setup()

  async def test_settings_and_constants_are_read_but_not_assigned_on_a_client(self):
    assert self.star.pipettes is not None and self.device.pipettes is not None
    self.assertEqual(
      self.star.pipettes.default_minimum_traverse_height,
      self.device.pipettes.default_minimum_traverse_height,
    )
    with self.assertRaisesRegex(AttributeError, "settings file"):
      self.star.pipettes.default_minimum_traverse_height = 200.0
    with self.assertRaisesRegex(AttributeError, "constant"):
      self.star.pipettes.ztouch_cascade_interval = 0.0

  async def test_what_a_call_changes_on_the_server_reaches_the_client(self):
    assert self.star.iswap is not None and self.device.iswap is not None
    self.device.iswap.configuration.elbow_drive_predefined_increments = None
    await self.star.iswap.request_firmware_version()
    self.assertIsNone(self.star.iswap.configuration.elbow_drive_predefined_increments)
    positions = await self.star.iswap.elbow_drive_request_positions()
    self.assertEqual(self.star.iswap.configuration.elbow_drive_predefined_increments, positions)

  async def test_a_failed_call_raises_what_the_device_raises(self):
    assert self.star.deck is not None and self.star.pipettes is not None
    carrier = await self.star.deck.assign_child_resource(
      hamilton_tip_carrier_L5(name="tc"), track=1
    )
    tips = await carrier[1].assign_child_resource(hamilton_96_tiprack_300uL_filter(name="tips"))
    await self.star.pipettes.pick_up_tips(tips.get_tip_spots("A1:H1"))
    with self.assertRaises(NoTipError):
      await self.star.pipettes.pick_up_tips(tips.get_tip_spots("A1:H1"))


class SettingsTests(unittest.IsolatedAsyncioTestCase):
  async def test_the_servers_settings_are_in_place_after_setup_and_a_client_reads_them(self):
    settings = json_format.ParseDict(
      {
        "pipettes": {"default_minimum_traverse_height": 200.0},
        "head96": {"default_mix_swap_speed": 7.5},
      },
      Settings(),
    )
    device = STARlet(simulation=True)
    star = remote_device(STARServer.local(device, settings), device.resource_server, "STARlet")
    await star.setup()
    assert device.pipettes is not None and device.head96 is not None
    assert star.pipettes is not None and star.head96 is not None
    self.assertEqual(device.pipettes.default_minimum_traverse_height, 200.0)
    self.assertEqual(device.head96.default_mix_swap_speed, 7.5)
    self.assertEqual(star.pipettes.default_minimum_traverse_height, 200.0)
    self.assertEqual(star.head96.default_mix_swap_speed, 7.5)
    # Those not given keep the code's.
    self.assertEqual(star.pipettes.default_z_speed, Pipettes.default_z_speed)

  def test_a_settings_file_names_only_settings(self):
    with tempfile.TemporaryDirectory() as directory:
      path = os.path.join(directory, "settings.json")
      with open(path, "w") as f:
        json.dump({"pipettes": {"default_minimum_traverse_height": 200.0}}, f)
      self.assertEqual(read_settings(path).pipettes.default_minimum_traverse_height, 200.0)
      with open(path, "w") as f:
        json.dump({"pipettes": {"ztouch_cascade_interval": 0.0}}, f)
      with self.assertRaises(ValueError):
        read_settings(path)


class FactoryTests(unittest.IsolatedAsyncioTestCase):
  async def test_what_the_server_decides_is_not_given_with_it(self):
    with self.assertRaises(ValueError):
      STARlet(star_server="http://127.0.0.1:1", simulation=True)

  async def test_the_served_device_is_the_one_asked_for(self):
    device = STARlet(simulation=True)
    star = STAR(star_server=STARServer.local(device), resource_server=device.resource_server)
    with self.assertRaisesRegex(ValueError, "serves a STARlet, not a STAR"):
      await star.setup()


@unittest.skipIf(importlib.util.find_spec("uvicorn") is None, "serving needs uvicorn")
class NetworkTests(unittest.IsolatedAsyncioTestCase):
  async def test_a_device_served_on_a_port(self):
    from pylabrobot.hamilton.star.server.serve import serve

    with socket.socket() as s:
      s.bind(("127.0.0.1", 0))
      port = s.getsockname()[1]
    served = asyncio.create_task(serve(STARlet(simulation=True), port=port, serve_resources=True))
    try:
      for _ in range(100):
        try:
          _, writer = await asyncio.open_connection("127.0.0.1", port)
          writer.close()
          break
        except OSError:
          await asyncio.sleep(0.05)
      star = STARlet(star_server=f"http://127.0.0.1:{port}")
      await star.setup()
      assert star.pipettes is not None
      self.assertEqual(len(await star.pipettes.request_y_positions()), 8)
      await star.stop()
    finally:
      served.cancel()
      await asyncio.gather(served, return_exceptions=True)
