"""Golden tests of what the BioTek EL406 sends today, for each plate it is given.

The EL406 talks framed binary over FTDI. The seam is a fake FTDI that records every call in
order (serial setup and buffer purges by name, writes as hex) and answers each framed command
with an ACK and a response frame echoing the command, so no hardware or USB is needed.
"""

from __future__ import annotations

import asyncio
import enum
import pathlib
import unittest
from collections.abc import Awaitable
from typing import Any, Dict, List, Optional
from unittest import mock

from pylabrobot.agilent.biotek.el406 import EL406
from pylabrobot.agilent.biotek.el406.enums import (
  EL406Motor,
  EL406MotorHomeType,
  EL406Sensor,
  EL406StepType,
  EL406WasherManifold,
)
from pylabrobot.agilent.biotek.el406.protocol import build_framed_message
from pylabrobot.io.binary import Reader, Writer
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

STATUS_POLL = 0x92
SERIAL_NUMBER = 0x0100

# Data the fake answers a query with, by command. Queries put their value at data byte 2.
QUERY_DATA: Dict[int, bytes] = {
  0xD8: bytes([0, 0, 4]),  # washer manifold: DEEP_PIN_96
  0xBB: bytes([0, 0, 2]),  # syringe manifold: TUBE_32_LARGE_BORE
  0xF6: bytes([0, 0, 1, 8]),  # syringe box: type 1, size 8
  0x0104: bytes([0, 0, 1]),  # peristaltic pump installed
  0xD2: bytes([0, 0, 1]),  # sensor enabled
  0x95: bytes([0, 0, 0]),  # self-check passed
  SERIAL_NUMBER: b"\x00\x00SN406X1\x00",
}


def poll_data(validity: int = 0, state: int = 1, status: int = 0) -> bytes:
  """A STATUS_POLL response's data: validity, state, a 4-byte counter, status."""
  return Writer().u16(validity).u16(state).u32(0).u8(status).finish()


def plate_1536(size_z: float) -> pb.ResourceDefinition:
  """A 1536-well plate (32 x 48) of the given height: PLR's library has none."""
  well = build.resource(
    "{name}_well_{identifier}",
    Coordinate(1.5, 1.5, size_z - 1.5),
    kind=pb.RESOURCE_KIND_WELL,
    category="well",
    container=pb.ContainerSpec(),
    state=pb.ResourceState(volume=pb.VolumeState()),
  )
  return build.resource(
    "{name}",
    Coordinate(127.76, 85.48, size_z),
    kind=pb.RESOURCE_KIND_PLATE,
    category="plate",
    itemized=pb.ItemizedSpec(
      num_items_x=48,
      num_items_y=32,
      grid=pb.ItemGrid(
        item=well, offset=build.vec3(Coordinate(10.0, 7.0, 1.0)), item_dx=2.25, item_dy=2.25
      ),
    ),
    plate=pb.PlateSpec(plate_type="skirted"),
  )


def plate_holder(name: str) -> pb.ResourceDefinition:
  """The carrier a plate sits in, as the EL406 golden records name it."""
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 0),
    kind=pb.RESOURCE_KIND_PLATE_HOLDER,
    category="plate_holder",
    holder=pb.HolderSpec(child_location=build.vec3(Coordinate.zero()), pedestal_size_z=0),
  )


class FakeFTDI:
  """Records every call made to it and answers each framed command written to it.

  A command's answer is ACK, then a frame echoing the command with data from `QUERY_DATA`, the
  next scripted status poll for a STATUS_POLL, or none. `nak` makes the next write of that command
  answered with NAK instead.
  """

  def __init__(self) -> None:
    self.sent: List[str] = []
    self.polls: List[bytes] = []
    self.nak: Optional[int] = None
    self._rx = b""
    self._pending: Optional[tuple[int, int]] = None

  def _answer(self, command: int) -> None:
    if command == self.nak:
      self.nak = None
      self._rx += b"\x15"
      return
    if command == STATUS_POLL:
      data = self.polls.pop(0) if self.polls else poll_data()
    else:
      data = QUERY_DATA.get(command, b"")
    self._rx += b"\x06" + build_framed_message(command, data)

  async def setup(self) -> None:
    self.sent.append("setup")

  async def set_baudrate(self, baudrate: int) -> None:
    self.sent.append(f"set_baudrate {baudrate}")

  async def set_line_property(self, bits: int, stopbits: int, parity: int) -> None:
    self.sent.append(f"set_line_property {bits} {stopbits} {parity}")

  async def set_flowctrl(self, flowctrl: int) -> None:
    self.sent.append(f"set_flowctrl {flowctrl}")

  async def set_rts(self, level: bool) -> None:
    self.sent.append(f"set_rts {level}")

  async def set_dtr(self, level: bool) -> None:
    self.sent.append(f"set_dtr {level}")

  async def usb_purge_rx_buffer(self) -> None:
    self.sent.append("purge_rx")

  async def usb_purge_tx_buffer(self) -> None:
    self.sent.append("purge_tx")

  async def stop(self) -> None:
    self.sent.append("stop")

  async def write(self, data: bytes) -> int:
    self.sent.append(data.hex())
    if self._pending is not None:
      command, _ = self._pending
      self._pending = None
      self._answer(command)
      return len(data)
    reader = Reader(data[2:])
    command = reader.u16()
    reader.u8()
    reader.u16()
    length = reader.u16()
    if length:
      self._pending = (command, length)
    else:
      self._answer(command)
    return len(data)

  async def read(self, num_bytes: int = 1) -> bytes:
    chunk, self._rx = self._rx[:num_bytes], self._rx[num_bytes:]
    return chunk


def as_json(value: Any) -> Any:
  """A call's return value made JSON-able: enums by name."""
  if isinstance(value, dict):
    return {key: as_json(item) for key, item in value.items()}
  if isinstance(value, enum.Enum):
    return value.name
  return value


class EL406Recorder:
  """An EL406 on a fake FTDI, recording each step's writes, result and the plate's state.

  Plates are made in an in-memory store, and put in a plate holder there the way a person loads
  the carrier; the record ends with the holder's state.
  """

  def __init__(self, store: ResourceStore, holder: handles.Resource) -> None:
    self.io = FakeFTDI()
    with mock.patch("pylabrobot.agilent.biotek.el406.el406.FTDI", return_value=self.io):
      self.el406 = EL406(name="el406")
    self.store = store
    self.holder = holder
    self.steps: List[Dict[str, Any]] = []

  async def plate(self, source: Any, name: str, with_lid: bool = False) -> handles.Plate:
    """A plate from a model's name or a definition, with the model's lid when asked."""
    plate = await self.store.create(source, name=name)
    assert isinstance(plate, handles.Plate)
    if with_lid:
      await self.store.create(f"{source}_lid", name=f"{name}_lid", parent=plate)
    return plate

  async def connect(self) -> None:
    """Set up without a reset, before the recorded steps; `test_setup_and_stop` pins setup."""
    await self.el406.setup(skip_reset=True)
    self.io.sent.clear()

  async def load(self, plate: handles.Plate) -> None:
    """Put `plate` in the carrier and tell the EL406 about it."""
    for held in await self.holder.get_children():
      await held.unassign()
    await self.holder.assign_child_resource(plate, location=Coordinate.zero())
    await self.el406.set_plate(plate)

  async def step(self, call: str, operation: Awaitable[Any]) -> None:
    """Run `operation`, recording what was written and what it returned or raised."""
    start = len(self.io.sent)
    entry: Dict[str, Any] = {"call": call}
    try:
      entry["result"] = as_json(await operation)
    except Exception as error:  # the error is part of the record
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = self.io.sent[start:]
    self.steps.append(entry)

  async def check(self, test: unittest.TestCase, scenario: str) -> None:
    """Compare the steps and the carrier's final state with the scenario's golden file."""
    record = {"steps": self.steps, "resources": await snapshot_store(self.store, self.holder)}
    check_golden(test, GOLDEN / f"{scenario}.json", record)


class EL406GoldenTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    # The driver sleeps between header and data and between polls; the scenarios do not wait.
    real_sleep = asyncio.sleep

    async def no_wait(_: float) -> None:
      await real_sleep(0)

    patcher = mock.patch("pylabrobot.agilent.biotek.el406.el406.asyncio.sleep", no_wait)
    patcher.start()
    self.addCleanup(patcher.stop)
    store = ResourceStore.in_memory()
    self.addAsyncCleanup(store.close)
    holder = await store.create(plate_holder("el406_plate_holder"), name="el406_plate_holder")
    self.r = EL406Recorder(store, holder)
    self.el406 = self.r.el406

  async def test_setup_and_stop(self):
    r = self.r
    await r.step("setup()", self.el406.setup())
    await r.step("stop()", self.el406.stop())
    await r.check(self, "setup_and_stop")

  async def test_queries_and_device_commands(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.step("request_instrument_settings()", el406.request_instrument_settings())
    await r.step("request_serial_number()", el406.request_serial_number())
    await r.step("request_sensor_enabled(VACUUM)", el406.request_sensor_enabled(EL406Sensor.VACUUM))
    await r.step("run_self_check()", el406.run_self_check())
    await r.step(
      "set_washer_manifold(TUBE_192)", el406.set_washer_manifold(EL406WasherManifold.TUBE_192)
    )
    await r.step(
      "home_motors(HOME_MOTOR, CARRIER_Y)",
      el406.home_motors(EL406MotorHomeType.HOME_MOTOR, EL406Motor.CARRIER_Y),
    )
    await r.step("pause()", el406.pause())
    await r.step("resume()", el406.resume())
    await r.step("abort(M_WASH)", el406.abort(EL406StepType.M_WASH))
    await r.step("abort()", el406.abort())
    await r.step("reset()", el406.reset())
    await r.check(self, "queries_and_device_commands")

  async def test_washer_96_well_with_lid(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.load(await r.plate("cor_96_wellplate_360uL_Fb", "plate", with_lid=True))
    await r.step("washer.prime(volume=20000, buffer='B')", el406.washer.prime(20000, buffer="B"))
    await r.step("washer.wash()", el406.washer.wash())
    await r.step(
      "washer.wash(cycles=2, dispense_volume=200, shake_duration=5, soak_duration=10, "
      "final_aspirate=False, bottom_wash=True, bottom_wash_volume=100, move_home_first=True)",
      el406.washer.wash(
        cycles=2,
        dispense_volume=200,
        shake_duration=5,
        soak_duration=10,
        final_aspirate=False,
        bottom_wash=True,
        bottom_wash_volume=100,
        move_home_first=True,
      ),
    )
    await r.step("washer.dispense(150, buffer='C')", el406.washer.dispense(150, buffer="C"))
    await r.step("washer.aspirate()", el406.washer.aspirate())
    await r.step(
      "washer.aspirate(vacuum_filtration=True, vacuum_time=10, secondary_aspirate=True)",
      el406.washer.aspirate(vacuum_filtration=True, vacuum_time=10, secondary_aspirate=True),
    )
    await r.step("washer.auto_clean(duration=120)", el406.washer.auto_clean(duration=120))
    await r.step("shake(10, 'Fast', soak_duration=5)", el406.shake(10, "Fast", soak_duration=5))
    await r.check(self, "washer_96_well_with_lid")

  async def test_washer_384_well(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.load(await r.plate("Greiner_384_wellplate_28ul_Fb", "plate"))
    await r.step("washer.wash()", el406.washer.wash())
    await r.step(
      "washer.wash(wash_format='Sector', sectors=[1, 3])",
      el406.washer.wash(wash_format="Sector", sectors=[1, 3]),
    )
    await r.step("washer.dispense(50)", el406.washer.dispense(50))
    await r.load(await r.plate("biorad_384_wellplate_50uL_Vb", "pcr_plate"))
    await r.step("washer.aspirate() on a low-profile 384", el406.washer.aspirate())
    await r.step("washer.wash() on a low-profile 384", el406.washer.wash())
    await r.check(self, "washer_384_well")

  async def test_one_batch_around_several_steps(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.load(await r.plate("cor_96_wellplate_360uL_Fb", "plate"))

    async def protocol() -> None:
      async with el406.batch():
        await el406.washer.dispense(300)
        await el406.washer.aspirate()
        await el406.shake(5)

    await r.step("batch(): washer.dispense(300), washer.aspirate(), shake(5)", protocol())
    await r.check(self, "one_batch_around_several_steps")

  async def test_syringe_dispenser(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.load(await r.plate("cor_96_wellplate_360uL_Fb", "plate"))
    await r.step("syringe_dispenser.prime(1000)", el406.syringe_dispenser.prime(1000))
    await r.step(
      "syringe_dispenser.prime(500, syringe='B', submerge_duration=120)",
      el406.syringe_dispenser.prime(500, syringe="B", submerge_duration=120),
    )
    await r.step(
      "syringe_dispenser.dispense({1: 50, 2: 50, 3: 100, 12: 50})",
      el406.syringe_dispenser.dispense({1: 50, 2: 50, 3: 100, 12: 50}),
    )
    await r.load(await r.plate(plate_1536(14.0), "plate_1536"))
    await r.step(
      "syringe_dispenser.dispense({48: 5}, offset_z=25.4) on 1536",
      el406.syringe_dispenser.dispense({48: 5}, offset_z=25.4),
    )
    await r.load(await r.plate("Greiner_384_wellplate_28ul_Fb", "plate_384"))
    await r.step(
      "syringe_dispenser.dispense({c: 20 for c in 1..24}, syringe='Both') on 384",
      el406.syringe_dispenser.dispense({c: 20 for c in range(1, 25)}, syringe="Both"),
    )
    await r.check(self, "syringe_dispenser")

  async def test_peristaltic_dispenser(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.load(await r.plate("cor_96_wellplate_360uL_Fb", "plate"))
    await r.step("peristaltic_dispenser.prime()", el406.peristaltic_dispenser.prime())
    await r.step(
      "peristaltic_dispenser.prime(duration=10, flow_rate='Low')",
      el406.peristaltic_dispenser.prime(duration=10, flow_rate="Low"),
    )
    await r.step(
      "peristaltic_dispenser.purge(volume=500, cassette='5uL')",
      el406.peristaltic_dispenser.purge(volume=500, cassette="5uL"),
    )
    await r.step(
      "peristaltic_dispenser.dispense({1: 10, 2: 10, 5: 20})",
      el406.peristaltic_dispenser.dispense({1: 10, 2: 10, 5: 20}),
    )
    await r.load(await r.plate(plate_1536(10.0), "plate_1536"))
    await r.step(
      "peristaltic_dispenser.dispense({1: 2, 48: 2}, rows=[1, 3]) on low-profile 1536",
      el406.peristaltic_dispenser.dispense({1: 2, 48: 2}, rows=[1, 3]),
    )
    await r.step(
      "peristaltic_dispenser.dispense({1: 2}, rows=[5]) on 1536: refused",
      el406.peristaltic_dispenser.dispense({1: 2}, rows=[5]),
    )
    await r.load(await r.plate("Greiner_384_wellplate_28ul_Fb", "plate_384"))
    await r.step(
      "peristaltic_dispenser.dispense({24: 5}, rows=[2]) on 384",
      el406.peristaltic_dispenser.dispense({24: 5}, rows=[2]),
    )
    await r.check(self, "peristaltic_dispenser")

  async def test_plate_types(self):
    r, el406 = self.r, self.el406
    await r.connect()
    plates = [
      ("96-well", await r.plate("cor_96_wellplate_360uL_Fb", "plate_96")),
      ("384-well", await r.plate("Greiner_384_wellplate_28ul_Fb", "plate_384")),
      ("384-well low profile", await r.plate("biorad_384_wellplate_50uL_Vb", "plate_384_pcr")),
      ("1536-well", await r.plate(plate_1536(14.0), "plate_1536")),
      ("1536-well low profile", await r.plate(plate_1536(10.0), "plate_1536_flanged")),
      ("24-well: refused", await r.plate("celltreat_24_wellplate_3300uL_Fb", "plate_24")),
    ]
    for label, plate in plates:
      await r.load(plate)
      await r.step(f"shake(3) on {label}", el406.shake(3))
    await r.check(self, "plate_types")

  async def test_failures(self):
    r, el406 = self.r, self.el406
    await r.connect()
    await r.step("shake(3) with no plate: refused", el406.shake(3))
    await r.load(await r.plate("cor_96_wellplate_360uL_Fb", "plate"))
    # The step runs, then the device reports error 0x1500 when it stops.
    r.io.polls = [poll_data(), poll_data(state=2), poll_data(validity=0x1500, state=4)]
    await r.step("washer.prime() fails on the device", el406.washer.prime())
    r.io.nak = 0xA6
    await r.step("washer.dispense(300) refused with NAK", el406.washer.dispense(300))
    await r.step("shake(0): refused", el406.shake(0))
    el406.clear_plate()
    await r.step("washer.wash() after clear_plate(): refused", el406.washer.wash())
    await r.check(self, "failures")


if __name__ == "__main__":
  unittest.main()
