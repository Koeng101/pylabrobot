"""Golden tests of what the Micronic RD235 code reader does today.

The seams are the side barcode reader's serial transport (`Serial` is replaced by a fake that
records every call in order and answers the trigger with a rack ID), the flatbed `Scanner` (a fake
that records each acquisition), and `decode_image` (which returns the tube codes a rack image
holds, since decoding a real image needs a real scan). Image paths carry a timestamp, so they are
recorded as `<image_dir>/micronic_<timestamp>.<extension>`. The reader's clock (`time.monotonic`)
advances by a hundredth of a second each time it is read, so a reply that never comes times out at once.
"""

from __future__ import annotations

import asyncio
import pathlib
import re
import tempfile
import types
import unittest
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from unittest import mock

from pylabrobot.micronic import MicronicError, MicronicRD235
from pylabrobot.micronic.code_reader import driver as driver_module
from pylabrobot.micronic.code_reader.driver import DecodeResult, RackScanResult
from pylabrobot.resources import Coordinate
from pylabrobot.resources.barcode import Barcode
from pylabrobot.resources.store import build
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.handles import TubeRack
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

# The tube codes the rack image holds, by position.
TUBES: Dict[str, str] = {"A1": "1000000001", "A2": "1000000002", "B1": "1000000013"}


async def tube_rack(
  store: ResourceStore, name: str, num_items_x: int = 12, num_items_y: int = 8
) -> TubeRack:
  """A rack of `num_items_y` x `num_items_x` holders with tubes in A1, A2 and B1."""
  holder = build.resource(
    f"{name}_resourceholder_{{identifier}}",
    Coordinate(9, 9, 43),
    kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
    category="resource_holder",
    holder=pb.HolderSpec(child_location=build.vec3(Coordinate.zero()), capacity=1),
  )
  definition = build.resource(
    name,
    Coordinate(127.76, 85.48, 45.2),
    kind=pb.RESOURCE_KIND_TUBE_RACK,
    category="tube_rack",
    itemized=pb.ItemizedSpec(
      num_items_x=num_items_x,
      num_items_y=num_items_y,
      grid=pb.ItemGrid(
        item=holder,
        offset=build.vec3(Coordinate(10.38, 7.24, 2)),
        item_dx=9,
        item_dy=9,
      ),
    ),
  )
  rack = await store.create(definition, name=name)
  assert isinstance(rack, TubeRack)
  for position in TUBES:
    tube = build.resource(
      f"{name}_tube_{position}",
      Coordinate(8.5, 8.5, 44.5),
      kind=pb.RESOURCE_KIND_TUBE,
      category="tube",
      container=pb.ContainerSpec(max_volume=1400),
      state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
    )
    await store.create(tube, name=tube.attributes.name, parent=rack.get_item(position))
  return rack


class FakeSerial:
  """A serial transport that records every call and answers each trigger with `reply`."""

  def __init__(self, record: "Recorder", **settings: Any):
    self.record = record
    record.transport = dict(settings)
    self.reply = b"9500017722\r"
    self.pending = b""

  async def setup(self) -> None:
    self.record.sent.append("serial.setup")

  async def stop(self) -> None:
    self.record.sent.append("serial.stop")

  async def reset_input_buffer(self) -> None:
    self.record.sent.append("serial.reset_input_buffer")

  async def write(self, data: bytes) -> None:
    self.record.sent.append("serial.write " + data.decode("ascii"))
    self.pending = self.reply

  async def read(self, num_bytes: int = 1) -> bytes:
    chunk, self.pending = self.pending[:num_bytes], self.pending[num_bytes:]
    return chunk


class FakeScanner:
  """A flatbed scanner that records each acquisition."""

  image_extension = "bmp"

  def __init__(self, record: "Recorder"):
    self.record = record

  async def setup(self) -> None:
    self.record.sent.append("scanner.setup")

  async def stop(self) -> None:
    self.record.sent.append("scanner.stop")

  async def acquire(self, output_path: pathlib.Path, timeout: float) -> Dict[str, object]:
    self.record.sent.append(f"scanner.acquire {self.record.placeholder(output_path)} {timeout}")
    return {"source": "fake"}


def barcode_json(barcode: Optional[Barcode]) -> Optional[Dict[str, Any]]:
  if barcode is None:
    return None
  return {
    "data": barcode.data,
    "symbology": barcode.symbology,
    "position_on_resource": barcode.position_on_resource,
  }


def scan_json(result: RackScanResult) -> Dict[str, Any]:
  return {
    "rack_id": result.rack_id,
    "rack_barcode": barcode_json(result.rack_barcode),
    "entries": [
      [entry.position, entry.tube_id, entry.status, barcode_json(entry.barcode)]
      for entry in result.entries
    ],
  }


class Recorder:
  """Records what the reader was sent, step by step, and the rack's tree."""

  def __init__(self, image_dir: str, store: ResourceStore, rack: TubeRack) -> None:
    self.sent: List[str] = []
    self.steps: List[Dict[str, Any]] = []
    self.transport: Dict[str, Any] = {}
    self.image_dir = image_dir
    self.store = store
    self.rack = rack
    self.decoded: Dict[str, DecodeResult] = {
      position: DecodeResult(tube_id=tube_id, method="fake") for position, tube_id in TUBES.items()
    }
    self.decode_error: Optional[Exception] = None
    self.now = 0.0

    def make_serial(**settings: Any) -> FakeSerial:
      self.serial = FakeSerial(self, **settings)
      return self.serial

    with mock.patch.object(driver_module, "Serial", make_serial):
      self.reader = MicronicRD235(
        scanner=FakeScanner(self),  # type: ignore[arg-type]
        serial_port="/dev/ttyUSB0",
        image_dir=image_dir,
      )

  def placeholder(self, path: pathlib.Path) -> str:
    name = re.sub(r"micronic_\d{8}_\d{6}_\d{6}", "micronic_<timestamp>", path.name)
    return f"<image_dir>/{name}" if str(path.parent) == self.image_dir else str(path)

  def _monotonic(self) -> float:
    self.now += 0.01
    return self.now

  def _decode_image(self, image_path: pathlib.Path) -> Tuple[Dict[str, Any], Dict[str, object]]:
    self.sent.append(f"decode_image {self.placeholder(image_path)}")
    if self.decode_error is not None:
      raise self.decode_error
    return dict(self.decoded), {"decodedWells": len(self.decoded)}

  async def step(self, call: str, action: Callable[[], Awaitable[Any]]) -> None:
    """Run one step, recording what was sent, returned or raised. The reader never changes the
    rack, so its tree is recorded once, at the end."""
    self.sent = []
    entry: Dict[str, Any] = {"call": call}
    try:
      with (
        mock.patch.object(driver_module, "decode_image", self._decode_image),
        mock.patch.object(driver_module, "time", types.SimpleNamespace(monotonic=self._monotonic)),
      ):
        result = await action()
      entry["result"] = scan_json(result) if isinstance(result, RackScanResult) else result
    except (MicronicError, asyncio.TimeoutError) as error:
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = self.sent
    last = self.reader.last_image_path
    entry["last_image_path"] = None if last is None else self.placeholder(last)
    self.steps.append(entry)

  async def finish(self) -> Dict[str, Any]:
    return {
      "transport": self.transport,
      "steps": self.steps,
      "resources": await snapshot_store(self.store, self.rack),
    }


class MicronicGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_scanning_a_rack(self):
    """Set up, read the rack ID, scan the whole rack twice and stop."""
    with tempfile.TemporaryDirectory() as image_dir:
      store = ResourceStore.in_memory()
      rack = await tube_rack(store, "rack")
      rig = Recorder(image_dir, store, rack)
      reader = rig.reader

      await rig.step("setup()", reader.setup)
      await rig.step("scan_rack_id()", reader.scan_rack_id)
      await rig.step("scan_rack(rack)", lambda: reader.scan_rack(rack))
      rig.serial.reply = b"?\r"
      await rig.step("scan_rack(rack)  # no rack ID", lambda: reader.scan_rack(rack))
      await rig.step("stop()", reader.stop)
      check_golden(self, GOLDEN / "scanning_a_rack.json", await rig.finish())

  async def test_refused_racks_and_failed_reads(self):
    """A rack that is not 8x12 is refused before anything is sent; a failed decode is raised."""
    with tempfile.TemporaryDirectory() as image_dir:
      store = ResourceStore.in_memory()
      rack = await tube_rack(store, "rack")
      small = await tube_rack(store, "small_rack", num_items_x=6, num_items_y=4)
      rig = Recorder(image_dir, store, rack)
      reader = rig.reader

      await rig.step("setup()", reader.setup)
      await rig.step("scan_rack(small_rack)", lambda: reader.scan_rack(small))
      rig.decode_error = MicronicError("Only 3 DataMatrix codes were found in the full image.")
      await rig.step("scan_rack(rack)  # decode fails", lambda: reader.scan_rack(rack))
      rig.decode_error = None
      rig.serial.reply = b""
      await rig.step("scan_rack_id()  # no reply", reader.scan_rack_id)
      await rig.step("stop()", reader.stop)
      check_golden(self, GOLDEN / "refused_racks_and_failed_reads.json", await rig.finish())


if __name__ == "__main__":
  unittest.main()
