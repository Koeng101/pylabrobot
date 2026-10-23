"""Golden records of what the Agilent VSpin and its Access2 loader do today.

The seams are the two FTDI connections: every NMC frame written to the VSpin and every framed
command written to the Access2 is recorded in one list, in order, as hex. Fakes answer each
write the way the hardware does: the VSpin's door, door-lock and bucket-lock sensors follow its
output word and the rotor reports the position it was last sent to; the Access2 reports itself
ready, its gripper where it was last sent and its plate sensor as the scenario sets it. Events
emitted through `pylabrobot.events` are recorded with their payloads. The resources are the
loader and the two buckets, each the root of its own tree.

The VSpin's network bring-up is not run: as in the VSpin's own tests, the centrifuge starts
connected, initialized and homed, with the status masks its setup configures, and its bucket-1
calibration is given where it would be read from its calibration file.
"""

from __future__ import annotations

import dataclasses
import pathlib
import struct
import unittest
from typing import Any, Awaitable, Callable, Dict, List
from unittest.mock import patch

from pylabrobot.agilent.vspin import _access2_protocol as protocol
from pylabrobot.agilent.vspin import _nmc
from pylabrobot.agilent.vspin._state import (
  ConnectionState,
  VSpinHomingState,
  VSpinInitializationState,
)
from pylabrobot.agilent.vspin.access2 import Access2
from pylabrobot.agilent.vspin.vspin import VSpin
from pylabrobot.events import EventBus, PLREvent, use_event_bus
from pylabrobot.io.binary import Reader, Writer
from pylabrobot.resources import Plate, Well, create_ordered_items_2d
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent

# The bucket-1 calibration the VSpin reads from its calibration file at construction.
BUCKET_1_REMAINDER = 1234


def _jsonable(value: Any) -> Any:
  """`value` with tuples as lists and anything else that is not JSON as its type name."""
  if isinstance(value, dict):
    return {str(key): _jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [_jsonable(item) for item in value]
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  return type(value).__name__


class _FakeVSpinFTDI:
  """Answers NMC frames like the VSpin's PIC-SERVO and PIC-IO modules."""

  def __init__(self, sent: List[str]):
    self.sent = sent
    self.output_word = 0
    self.position = 0
    self._replies = bytearray()

  def _inputs(self) -> int:
    door_open = bool(self.output_word & (1 << _nmc.OUTPUT_DOOR_CYLINDER))
    door_unlocked = bool(self.output_word & (1 << _nmc.OUTPUT_DOOR_LOCK_CYLINDER))
    bucket_locked = bool(self.output_word & (1 << _nmc.OUTPUT_BUCKET_LOCK_CYLINDER))
    inputs = 0
    if door_open:
      inputs |= 1 << _nmc.INPUT_DOOR_OPEN
    if door_unlocked:
      inputs |= 1 << _nmc.INPUT_DOOR_LOCKED
    # Both bucket sensors are active low.
    inputs |= 1 << (_nmc.INPUT_BUCKET_UNLOCKED if bucket_locked else _nmc.INPUT_BUCKET_LOCKED)
    return inputs

  async def write(self, data: bytes) -> int:
    self.sent.append(f"vspin {data.hex()}")
    address, command = data[1], data[2] & 0x0F
    if address == _nmc.PIC_IO_ADDRESS:
      if command == _nmc.CMD_SET_OUTPUT:
        self.output_word = Reader(data[3:5]).u16()
      reply = Writer().u16(self._inputs()).u8(0).finish()
    else:
      if command == _nmc.CMD_LOAD_TRAJECTORY and data[3] & _nmc.LOAD_POSITION:
        self.position = struct.unpack("<i", data[4:8])[0]
      reply = Writer().i32(self.position).u8(0).i16(0).u8(0).i32(0).finish()
    status = _nmc.STATUS_MOVE_DONE
    self._replies.extend(bytes([status]) + reply + bytes([(status + sum(reply)) & 0xFF]))
    return len(data)

  async def read(self, length: int) -> bytes:
    chunk = bytes(self._replies[:length])
    del self._replies[:length]
    return chunk


class _FakeAccess2FTDI:
  """Answers framed commands like the Access2 controller."""

  def __init__(self, sent: List[str]):
    self.sent = sent
    self.gripper = 0.0
    self.plate_sensed = True
    self._replies = bytearray()

  async def setup(self) -> None:
    self.sent.append("access2 open")

  async def stop(self) -> None:
    self.sent.append("access2 close")

  async def set_baudrate(self, baudrate: int) -> None:
    self.sent.append(f"access2 baudrate {baudrate}")

  async def write(self, data: bytes) -> int:
    self.sent.append(f"access2 {data.hex()}")
    inner = protocol.parse_ftdi_frame(data)
    command, payload = inner[0], inner[3:]
    reply = b""
    if command == protocol.GET_STATUS:
      ready = protocol.STATUS_INITIALIZED | protocol.STATUS_HOMED
      done = protocol.AXIS_STATUS_MOVE_DONE
      reply = (
        Writer().u8(ready).u8(0).u8(done).f32(self.gripper).u8(done).f32(100).u8(done).f32(20)
      ).finish()
    elif command == protocol.MOVE_TO_POSITION and payload[0] == protocol.AXIS_GRIPPER:
      self.gripper = Reader(payload[1:5]).f32()
    elif command == protocol.GET_SENSOR_VALUES:
      sensors = 0x03 | protocol.STATUS_OPTICAL_PLATE_SENSOR
      reply = Writer().u32(sensors if self.plate_sensed else protocol.SENSOR_NO_PLATE).finish()
    response = Writer().u8((command + 1) & 0xFF).u16(len(reply) + 1).u8(0).raw_bytes(reply).finish()
    self._replies.extend(protocol.build_ftdi_frame(response))
    return len(data)

  async def read(self, length: int) -> bytes:
    chunk = bytes(self._replies[:length])
    del self._replies[:length]
    return chunk


class _Recorder:
  """A VSpin and its Access2 loader on fake FTDI connections, recording each step's writes,
  events and resources.

  Operation ids are uuids; they are recorded as `op-1`, `op-2`... in the order they appear.
  """

  def __init__(self):
    self.sent: List[str] = []
    with (
      patch("pylabrobot.agilent.vspin.vspin.FTDI", autospec=True),
      patch("pylabrobot.agilent.vspin.access2.FTDI", autospec=True),
      patch(
        "pylabrobot.agilent.vspin.vspin._load_vspin_calibrations",
        return_value=BUCKET_1_REMAINDER,
      ),
    ):
      self.vspin = VSpin(name="centrifuge", device_id="vspin-1")
      self.loader = Access2(name="loader", device_id="access2-1", vspin=self.vspin)
    self.vspin_io = _FakeVSpinFTDI(self.sent)
    self.access2_io = _FakeAccess2FTDI(self.sent)
    self.vspin.io = self.vspin_io  # type: ignore[assignment]
    self.loader.driver.io = self.access2_io  # type: ignore[assignment]
    self.vspin._servo_status_mask = (
      _nmc.SEND_POSITION | _nmc.SEND_ANALOG | _nmc.SEND_VELOCITY | _nmc.SEND_AUXILIARY
    ) | _nmc.SEND_HOME
    self.vspin._io_status_mask = _nmc.SEND_INPUTS | _nmc.SEND_ANALOG_1
    self.vspin._state = dataclasses.replace(
      self.vspin.state,
      connection=ConnectionState.CONNECTED,
      initialization=VSpinInitializationState.INITIALIZED,
      homing=VSpinHomingState.HOMED,
    )
    self.initial = self.snapshot()
    self.steps: List[Dict[str, Any]] = []
    self.events: List[Dict[str, Any]] = []
    self._operation_ids: Dict[str, str] = {}
    self.bus = EventBus()
    self.bus.subscribe(self._on_event)

  def snapshot(self) -> List[Dict[str, Any]]:
    return (
      snapshot_resources(self.loader)
      + snapshot_resources(self.vspin.bucket1)
      + snapshot_resources(self.vspin.bucket2)
    )

  def _on_event(self, event: PLREvent) -> None:
    raw_id = event.context.get("operation_id")
    operation_id = None
    if raw_id is not None:
      operation_id = self._operation_ids.setdefault(raw_id, f"op-{len(self._operation_ids) + 1}")
    self.events.append(
      {
        "name": event.name,
        "operation": event.context.get("operation"),
        "operation_id": operation_id,
        "data": _jsonable(event.data),
      }
    )

  async def step(self, call: str, action: Callable[[], Awaitable[Any]]) -> Any:
    """Run one call and record what it sent, emitted, returned and changed."""
    self.sent.clear()
    self.events = []
    before = self.snapshot()
    record: Dict[str, Any] = {"call": call}
    result: Any = None
    with use_event_bus(self.bus):
      try:
        result = await action()
        record["result"] = _jsonable(result)
      except Exception as error:
        record["result"] = {"error": type(error).__name__, "message": str(error)}
    record["sent"] = list(self.sent)
    record["events"] = self.events
    after = self.snapshot()
    if after != before:
      record["resources"] = after
    self.steps.append(record)
    return result

  def record(self) -> Dict[str, Any]:
    return {"initial_resources": self.initial, "steps": self.steps, "resources": self.snapshot()}


def _plate(name: str) -> Plate:
  """An SBS plate with one row of two wells: enough to show its wells move with it."""
  wells = create_ordered_items_2d(
    Well,
    num_items_x=2,
    num_items_y=1,
    dx=10,
    dy=40,
    dz=1,
    item_dx=9,
    item_dy=None,
    name_prefix=name,
    size_x=6.9,
    size_y=6.9,
    size_z=10,
    max_volume=360,
  )
  return Plate(name, size_x=127.76, size_y=85.48, size_z=14.2, ordered_items=wells)


class VSpinAccess2GoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_load_and_unload_both_buckets(self):
    """The loader set up; a plate loaded into bucket 1 and unloaded, then into bucket 2 with
    per-call settings, a spin refused while it is there, and unloaded."""
    recorder = _Recorder()
    vspin, loader = recorder.vspin, recorder.loader
    plate = _plate("sample_plate")

    async def place_plate() -> None:
      loader.assign_child_resource(plate)

    await recorder.step("loader.setup()", loader.setup)
    await recorder.step("loader.assign_child_resource(plate) by hand", place_plate)
    await recorder.step("vspin.go_to_bucket1()", vspin.go_to_bucket1)
    await recorder.step("loader.load()", loader.load)
    await recorder.step("loader.unload()", loader.unload)
    await recorder.step("vspin.go_to_bucket2()", vspin.go_to_bucket2)
    await recorder.step(
      "loader.load(plate_height=14.2, speeds medium)",
      lambda: loader.load(
        plate_height=14.2,
        source_z_offset=4,
        destination_z_offset=2,
        park_z_offset=1,
        source_speed="medium",
        destination_speed="medium",
      ),
    )
    await recorder.step("vspin.spin(g=2000) refused", lambda: vspin.spin(g=2000, duration=60))
    await recorder.step(
      "loader.unload(plate_height=14.2)", lambda: loader.unload(plate_height=14.2)
    )
    await recorder.step("loader.stop()", loader.stop)

    check_golden(self, GOLDEN / "load_and_unload_both_buckets.json", recorder.record())

  async def test_refused_transfers(self):
    """Loads and unloads refused before the loader moves: none of them moves the plate."""
    recorder = _Recorder()
    vspin, loader = recorder.vspin, recorder.loader
    plate = _plate("sample_plate")
    other = _plate("other_plate")

    async def place(holder_plate: Plate, on: Any) -> None:
      on.assign_child_resource(holder_plate)

    async def take(holder_plate: Plate) -> None:
      holder_plate.unassign()

    await recorder.step("loader.setup()", loader.setup)
    await recorder.step("loader.assign_child_resource(plate) by hand", lambda: place(plate, loader))
    await recorder.step("loader.load() no bucket presented", loader.load)
    await recorder.step("loader.unload() no bucket presented", loader.unload)
    await recorder.step("vspin.go_to_bucket1()", vspin.go_to_bucket1)
    await recorder.step("loader.unload() bucket empty", loader.unload)
    await recorder.step(
      "bucket1.assign_child_resource(other_plate) by hand", lambda: place(other, vspin.bucket1)
    )
    await recorder.step("loader.load() bucket occupied", loader.load)
    await recorder.step("other_plate.unassign() by hand", lambda: take(other))
    await recorder.step("vspin.close_door()", vspin.close_door)
    await recorder.step("loader.load() door closed", loader.load)
    await recorder.step("vspin.open_door()", vspin.open_door)
    await recorder.step(
      "loader.load(gripper_open_position=2, gripper_close_threshold=1)",
      lambda: loader.load(gripper_open_position=2, gripper_close_threshold=1),
    )
    await recorder.step("take plate off the loader by hand", lambda: take(plate))
    await recorder.step("loader.load() loader empty", loader.load)

    check_golden(self, GOLDEN / "refused_transfers.json", recorder.record())

  async def test_loader_finds_no_plate(self):
    """The loader reaches the bucket and finds no plate on unload, then none on the stage on
    load: the plates stay where the model had them, and later transfers are refused."""
    recorder = _Recorder()
    vspin, loader = recorder.vspin, recorder.loader
    plate = _plate("sample_plate")
    spun = _plate("spun_plate")

    async def place(holder_plate: Plate, on: Any) -> None:
      on.assign_child_resource(holder_plate)

    await recorder.step("loader.setup()", loader.setup)
    await recorder.step("vspin.go_to_bucket1()", vspin.go_to_bucket1)
    await recorder.step(
      "bucket1.assign_child_resource(spun_plate) by hand", lambda: place(spun, vspin.bucket1)
    )
    recorder.access2_io.plate_sensed = False
    await recorder.step("loader.unload() no plate sensed", loader.unload)
    await recorder.step("loader.assign_child_resource(plate) by hand", lambda: place(plate, loader))
    await recorder.step("vspin.go_to_bucket2() after the loader fault", vspin.go_to_bucket2)
    await recorder.step("loader.load() after the loader fault", loader.load)
    await recorder.step("loader.unload() after the loader fault", loader.unload)

    check_golden(self, GOLDEN / "loader_finds_no_plate.json", recorder.record())

  async def test_load_finds_no_plate(self):
    """The loader finds no plate on its stage when loading: the plate stays on the loader."""
    recorder = _Recorder()
    vspin, loader = recorder.vspin, recorder.loader
    plate = _plate("sample_plate")

    async def place() -> None:
      loader.assign_child_resource(plate)

    await recorder.step("loader.setup()", loader.setup)
    await recorder.step("vspin.go_to_bucket1()", vspin.go_to_bucket1)
    await recorder.step("loader.assign_child_resource(plate) by hand", place)
    recorder.access2_io.plate_sensed = False
    await recorder.step("loader.load() no plate sensed", loader.load)

    check_golden(self, GOLDEN / "load_finds_no_plate.json", recorder.record())


if __name__ == "__main__":
  unittest.main()
