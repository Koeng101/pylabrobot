"""The STAR's golden scenarios, driven over a STAR server: they must record what they record when
driven in this process, file for file.

Each scenario runs as written. Only the device it builds is served: `STAR`, `STARlet` and
`STARPlus` build the simulated device, serve it in this process, and hand the scenario a client
for it. The recorder watches the served device, which is the one the simulator answers for.
"""

import unittest
from typing import Any, Callable, Dict
from unittest import mock

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.golden import star_golden_tests as golden
from pylabrobot.hamilton.star.golden.recorder import STARRecorder
from pylabrobot.hamilton.star.server.client import RemoteSTARDevice, STARServer, remote_device

# The device each client stands for.
_SERVED: Dict[int, STARDevice] = {}


def _served(factory: Callable[..., STARDevice]) -> Callable[..., RemoteSTARDevice]:
  def make(*args: Any, **kwargs: Any) -> RemoteSTARDevice:
    device = factory(*args, **kwargs)
    client = remote_device(STARServer.local(device), device.resource_server, device.model)
    _SERVED[id(client)] = device
    return client

  return make


class _OverTheWire(unittest.IsolatedAsyncioTestCase):
  def setUp(self) -> None:
    super().setUp()
    for patcher in (
      mock.patch.object(golden, "STAR", _served(golden.STAR)),
      mock.patch.object(golden, "STARlet", _served(golden.STARlet)),
      mock.patch.object(golden, "STARPlus", _served(golden.STARPlus)),
    ):
      patcher.start()
      self.addCleanup(patcher.stop)

  async def built(self, device: Any, call: str) -> STARRecorder:
    served = _SERVED[id(device)]
    assert served.body is not None
    await served.body.set_tip_tracking(True)
    await served.body.set_volume_tracking(True)
    recorder = STARRecorder(served)
    await recorder.built(call)
    return recorder


class OverTheWireSetupTests(_OverTheWire, golden.SetupTests):
  pass


class OverTheWirePipettesTests(_OverTheWire, golden.PipettesTests):
  pass


class OverTheWireHead96Tests(_OverTheWire, golden.Head96Tests):
  pass


class OverTheWireCoreGrippersTests(_OverTheWire, golden.CoreGrippersTests):
  pass


class OverTheWireArmTests(_OverTheWire, golden.ArmTests):
  pass


class OverTheWireAutoloadTests(_OverTheWire, golden.AutoloadTests):
  pass
