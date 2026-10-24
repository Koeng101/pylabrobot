"""Golden tests of what the Keyence barcode scanner does today.

The seam is the scanner's serial transport: `Serial` is replaced by a fake that records every call
made on it, in order, and answers each written command from a script. Waits (`asyncio.sleep`) are
recorded rather than slept, and the scanner's clock (`time.time`) advances by a tenth of a second
each time it is read.
"""

from __future__ import annotations

import pathlib
import types
import unittest
from typing import Any, ContextManager, Dict, List
from unittest import mock

from pylabrobot.keyence import KeyenceBarcodeScanner, KeyenceBarcodeScannerError
from pylabrobot.keyence import barcode_scanner as scanner_module
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden

GOLDEN = pathlib.Path(__file__).parent

# pyserial's constants, so the scanner builds without pyserial installed.
SERIAL_CONSTANTS = types.SimpleNamespace(SEVENBITS=7, PARITY_EVEN="E", STOPBITS_ONE=1)


class FakeSerial:
  """A serial transport that records every call and answers each command from `answers`.

  Like `pylabrobot.io.serial.Serial`, a read without a size reads one byte; unread bytes stay
  buffered for later reads.
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

  async def write(self, data: bytes) -> None:
    self.record.sent.append("write " + data.decode("ascii"))
    queue = self.answers.get(data.decode("ascii").strip(), [])
    self.pending += (queue.pop(0) if len(queue) > 1 else (queue[0] if queue else "")).encode()

  async def read(self, num_bytes: int = 1) -> bytes:
    chunk, self.pending = self.pending[:num_bytes], self.pending[num_bytes:]
    return chunk


class Recorder(recording.Recorder):
  """Records what the scanner was sent, step by step."""

  catches = (KeyenceBarcodeScannerError,)
  records_waits = True

  def __init__(self) -> None:
    super().__init__()
    self.transport: Dict[str, Any] = {}

    def make_serial(**settings: Any) -> FakeSerial:
      self.serial = FakeSerial(self, **settings)
      return self.serial

    with (
      mock.patch.object(scanner_module, "HAS_SERIAL", True),
      mock.patch.object(scanner_module, "serial", SERIAL_CONSTANTS, create=True),
      mock.patch.object(scanner_module, "Serial", make_serial),
    ):
      self.scanner = KeyenceBarcodeScanner(port="/dev/ttyUSB0")

  def patches(self) -> List[ContextManager[Any]]:
    clock = types.SimpleNamespace(time=self.clock(0.1))
    return [*super().patches(), mock.patch.object(scanner_module, "time", clock)]

  def finish(self) -> Dict[str, Any]:
    return {"transport": self.transport, "steps": self.steps}


class KeyenceGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_scanning_barcodes(self):
    """Set up once the motor reports on, scan, and the reader's refusals."""
    rig = Recorder()
    scanner = rig.scanner
    rig.serial.answers = {"RMOTOR": ["", "MOTORON"], "LON": ["4006381333931\r"]}

    await rig.step("setup()", scanner.setup)
    await rig.step("scan_barcode()", scanner.scan_barcode)
    await rig.step("scan_barcode(read_time=2)", lambda: scanner.scan_barcode(read_time=2))
    rig.serial.answers["LON"] = ["NG\r"]
    await rig.step("scan_barcode()  # reader off", scanner.scan_barcode)
    rig.serial.answers["LON"] = ["ERR99\r"]
    await rig.step("scan_barcode()  # reader error", scanner.scan_barcode)
    rig.serial.answers["LON"] = ["ERROR\r"]
    await rig.step("scan_barcode()  # no read", scanner.scan_barcode)
    await rig.step("send_command('SSET')", lambda: scanner.send_command("SSET"))
    await rig.step("stop()", scanner.stop)
    check_golden(self, GOLDEN / "scanning_barcodes.json", rig.finish())

  async def test_refused_setup(self):
    """Setup refuses a motor that reports off, and one that never reports."""
    rig = Recorder()
    scanner = rig.scanner

    rig.serial.answers = {"RMOTOR": ["MOTOROFF"]}
    await rig.step("setup()  # motor off", scanner.setup)
    rig.serial.answers = {"RMOTOR": [""]}
    await rig.step("setup()  # no reply", scanner.setup)
    check_golden(self, GOLDEN / "refused_setup.json", rig.finish())


if __name__ == "__main__":
  unittest.main()
