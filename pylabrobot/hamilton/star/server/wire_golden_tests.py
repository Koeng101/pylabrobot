"""The STAR's golden scenarios, driven over a STAR server: they must record what they record when
driven in this process, file for file.

Each scenario runs as written. Only the device it builds is served: `STAR`, `STARlet` and
`STARPlus` build the simulated device, serve it in this process, and hand the scenario a client
for it. The recorder watches the served device, which is the one the simulator answers for.
"""

import sys
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
    for name in ("STAR", "STARlet", "STARPlus"):
      patcher = mock.patch.object(golden, name, _served(getattr(golden, name)))
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


for _name, _case in list(vars(golden).items()):
  if (
    isinstance(_case, type)
    and issubclass(_case, golden._Scenario)
    and _case is not golden._Scenario
  ):
    setattr(
      sys.modules[__name__],
      f"OverTheWire{_name}",
      type(f"OverTheWire{_name}", (_OverTheWire, _case), {}),
    )
