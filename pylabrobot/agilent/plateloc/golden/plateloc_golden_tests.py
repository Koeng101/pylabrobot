"""Golden tests of what the Agilent PlateLoc does today.

The PlateLoc uses no resources. The seam is its serial transport: `Serial` is replaced by a fake
that records every call made on it, in order, and answers each command from a script. Waits
(`asyncio.sleep`) are recorded rather than slept, and the sealer's clock (`time.monotonic`)
advances by a hundredth of a second each time it is read.
"""

from __future__ import annotations

import asyncio
import contextlib
import pathlib
import types
import unittest
from typing import Any, Awaitable, Callable, Dict, Iterator, List
from unittest import mock

from pylabrobot.agilent.plateloc import PlateLoc, PlateLocError, PlateLocStatus
from pylabrobot.agilent.plateloc import plateloc as plateloc_module
from pylabrobot.testing.golden import check_golden

GOLDEN = pathlib.Path(__file__).parent


class FakeSerial:
  """A serial transport that records every call and answers each command.

  A command is answered with the next reply queued for its two-letter code in `answers` (the last
  one repeats), or with an acknowledgement.
  """

  def __init__(self, record: "Recorder", **settings: Any):
    self.record = record
    record.transport = dict(settings)
    self.port = settings["port"]
    self.answers: Dict[str, List[str]] = {}
    self.pending = b""

  async def setup(self) -> None:
    self.record.sent.append("setup")

  async def stop(self) -> None:
    self.record.sent.append("stop")

  async def reset_input_buffer(self) -> None:
    self.record.sent.append("reset_input_buffer")

  async def write(self, data: bytes) -> None:
    self.record.sent.append("write " + data.decode("ascii"))
    code = data.decode("ascii")[:2]
    queue = self.answers.get(code, [f"{code}AK"])
    self.pending = ((queue.pop(0) if len(queue) > 1 else queue[0]) + "\r").encode("ascii")

  async def read(self, num_bytes: int = 1) -> bytes:
    chunk, self.pending = self.pending[:num_bytes], self.pending[num_bytes:]
    return chunk

  @contextlib.contextmanager
  def temporary_timeout(self, timeout: float) -> Iterator[None]:
    yield


class Recorder:
  """Records what the PlateLoc was sent, step by step."""

  def __init__(self) -> None:
    self.sent: List[str] = []
    self.waits: List[float] = []
    self.transport: Dict[str, Any] = {}
    self.steps: List[Dict[str, Any]] = []
    self.now = 0.0
    self.real_sleep = asyncio.sleep

    def make_serial(**settings: Any) -> FakeSerial:
      self.serial = FakeSerial(self, **settings)
      return self.serial

    with (
      mock.patch.object(plateloc_module, "HAS_SERIAL", True),
      mock.patch.object(plateloc_module, "Serial", make_serial),
    ):
      self.plateloc = PlateLoc(port="/dev/ttyUSB0")

  def _monotonic(self) -> float:
    self.now += 0.01
    return self.now

  async def _sleep(self, delay: float, result: Any = None) -> Any:
    self.waits.append(delay)
    await self.real_sleep(0)
    return result

  async def step(self, call: str, action: Callable[[], Awaitable[Any]]) -> None:
    """Run one step, recording what was sent, waited, returned or raised."""
    self.sent, self.waits = [], []
    entry: Dict[str, Any] = {"call": call}
    try:
      with (
        mock.patch.object(plateloc_module.asyncio, "sleep", self._sleep),
        mock.patch.object(
          plateloc_module, "time", types.SimpleNamespace(monotonic=self._monotonic)
        ),
      ):
        result = await action()
      if isinstance(result, PlateLocStatus):
        result = {
          "port": result.port,
          "connected": result.connected,
          "target_temperature": result.target_temperature,
          "stage_position": result.stage_position,
          "cycle_complete": result.cycle_complete,
        }
      entry["result"] = result
    except (PlateLocError, ValueError, TimeoutError) as error:
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = self.sent
    if self.waits:
      entry["waits"] = self.waits
    self.steps.append(entry)


class PlateLocGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_sealing_a_plate(self):
    """Open, close, seal (polling until the cycle completes) and the sealer's refusals."""
    rig = Recorder()
    plateloc = rig.plateloc

    await rig.step("setup()", plateloc.setup)
    await rig.step("open()", plateloc.open)
    await rig.step("close()", plateloc.close)
    rig.serial.answers["CC"] = ["CCNK", "CCNK", "CCAK"]
    await rig.step("seal(temperature=175, duration=1.2)", lambda: plateloc.seal(175, 1.2))
    await rig.step("request_status()", plateloc.request_status)
    await rig.step("seal(temperature=175, duration=20)", lambda: plateloc.seal(175, 20))
    await rig.step("set_sealing_temperature(300)", lambda: plateloc.set_sealing_temperature(300))
    rig.serial.answers["GO"] = ["GONK(Door open)"]
    await rig.step("seal(temperature=170, duration=2)  # rejected", lambda: plateloc.seal(170, 2))
    rig.serial.answers["CL"] = ["SIAK"]
    await rig.step("clear_error()  # wrong reply", plateloc.clear_error)
    rig.serial.answers["AC"] = [""]
    await rig.step("stop_cycle()  # no reply", plateloc.stop_cycle)
    await rig.step("stop()", plateloc.stop)
    check_golden(
      self, GOLDEN / "sealing_a_plate.json", {"transport": rig.transport, "steps": rig.steps}
    )


if __name__ == "__main__":
  unittest.main()
