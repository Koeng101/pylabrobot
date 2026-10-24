"""Golden tests of what the generic serial line barcode scanner does today.

The seam is the scanner's serial transport: `scanner.io` is replaced by a fake that records every
call made on it, in order, and hands out the bytes the scanner sends one read at a time.
"""

from __future__ import annotations

import contextlib
import pathlib
import unittest
from typing import Iterator, List

from pylabrobot.generic import SerialBarcodeScanner
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden

GOLDEN = pathlib.Path(__file__).parent


class FakeSerial:
  """A serial transport that records every call and returns `incoming` one read at a time."""

  def __init__(self, record: "Recorder"):
    self.record = record
    self.port = "/dev/ttyACM0"
    self.incoming: List[bytes] = []

  async def setup(self) -> None:
    self.record.sent.append("setup")

  async def stop(self) -> None:
    self.record.sent.append("stop")

  async def reset_input_buffer(self) -> None:
    self.record.sent.append("reset_input_buffer")

  async def write(self, data: bytes) -> None:
    self.record.sent.append("write " + data.hex())

  async def read(self, num_bytes: int = 1) -> bytes:
    self.record.sent.append(f"read {num_bytes}")
    return self.incoming.pop(0) if self.incoming else b""

  @contextlib.contextmanager
  def temporary_timeout(self, timeout: float) -> Iterator[None]:
    self.record.sent.append("temporary_timeout")
    yield


class Recorder(recording.Recorder):
  """Records what the scanner was sent, step by step."""

  catches = (ValueError,)

  def __init__(self, scanner: SerialBarcodeScanner) -> None:
    super().__init__()
    self.serial = FakeSerial(self)
    self.scanner = scanner
    scanner.io = self.serial  # type: ignore[assignment]


class SerialBarcodeScannerGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_scanning_barcodes(self):
    """A triggered scanner: scans, a read that times out, a line read and refusals."""
    rig = Recorder(
      SerialBarcodeScanner(
        port="/dev/ttyACM0", trigger_command=b"\x16T\r", untrigger_command=b"\x16U\r"
      )
    )
    scanner = rig.scanner

    await rig.step("setup()", scanner.setup)
    await rig.step("reset_input_buffer()", scanner.reset_input_buffer)
    rig.serial.incoming = [b"A", b"B", b"1", b"\r", b"\n"]
    await rig.step(
      "scan_barcode(read_time=1, symbology='Code 128 (Subset B and C)', "
      "position_on_resource='right')",
      lambda: scanner.scan_barcode(
        read_time=1, symbology="Code 128 (Subset B and C)", position_on_resource="right"
      ),
    )
    await rig.step("read_line()  # the leftover newline", scanner.read_line)
    await rig.step("scan_barcode()  # nothing arrives", scanner.scan_barcode)
    await rig.step("scan_barcode(read_time=-1)", lambda: scanner.scan_barcode(read_time=-1))
    rig.serial.incoming = [b"X", b"\xff", b"\n"]
    await rig.step("read_line(timeout=2)", lambda: scanner.read_line(timeout=2))
    await rig.step("write(b'\\x16T\\r')", lambda: scanner.write(b"\x16T\r"))
    await rig.step("stop()", scanner.stop)
    check_golden(self, GOLDEN / "scanning_barcodes.json", {"steps": rig.steps})

  async def test_line_length_limit(self):
    """An untriggered scanner stops reading a line at its length limit."""
    rig = Recorder(SerialBarcodeScanner(port="/dev/ttyACM0", max_line_length=4))
    scanner = rig.scanner
    rig.serial.incoming = [b"1", b"2", b"3", b"4", b"5", b"\r"]

    await rig.step("scan_barcode()", scanner.scan_barcode)
    await rig.step("scan_barcode()  # the rest of the line", scanner.scan_barcode)
    check_golden(self, GOLDEN / "line_length_limit.json", {"steps": rig.steps})


if __name__ == "__main__":
  unittest.main()
