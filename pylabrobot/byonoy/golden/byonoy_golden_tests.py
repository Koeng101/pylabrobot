"""Golden records of what the Byonoy Absorbance 96 and Luminescence 96 do: every HID report they
write, step by step, and their own resource trees (base unit, holders, the plate and the unit on
top).

The readers run over a fake HID link that answers each report the way the readers do, with fixed
values: a status, identity fields, versions, wavelengths and measurement chunks.
"""

import dataclasses
import datetime
import enum
import inspect
import pathlib
import unittest
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from pylabrobot.byonoy import (
  byonoy_a96a,
  byonoy_a96a_parking_unit,
  byonoy_l96,
  byonoy_l96a,
  byonoy_sbs_adapter,
)
from pylabrobot.byonoy.absorbance_96 import ByonoyAbsorbance96
from pylabrobot.byonoy.body import assign_unlocated
from pylabrobot.byonoy.driver import ByonoyDriver
from pylabrobot.io.binary import Reader, Writer
from pylabrobot.io.hid import HID
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

# What the fake reader reports.
WAVELENGTHS = [450, 600, 660]
SUPPORTED_REPORTS = [0x0010, 0x0050, 0x0080, 0x0200, 0x0300, 0x0310, 0x0320, 0x0330, 0x0340]
DATA_FIELDS = {
  0: "device-id",
  1: "Byonoy L96",
  2: "Byonoy",
  3: "SN-0001",
  4: "1.2.3",
  8: "REF-96",
}
# Routing bytes a request that is answered ends with.
ANSWERED_ROUTING = b"\x80\x40"


def _report(*parts: bytes) -> bytes:
  """A 64-byte input report."""
  return b"".join(parts).ljust(64, b"\x00")


def _chunks(report_id: int, header: Callable[[Writer], Writer]) -> List[bytes]:
  """A measurement's 8 result chunks, one row each; well (row, column) reads row + column / 100."""
  chunks = []
  for row in range(8):
    writer = header(Writer().u16(report_id).u8(row).u8(8))
    for column in range(12):
      writer.f32(row + column / 100)
    chunks.append(_report(writer.u8(0).u8(100).finish()))
  return chunks


class FakeByonoyHID(HID):
  """Records every report written and answers it as a Byonoy reader does; reading with nothing
  to read fails instead of waiting."""

  def __init__(self, name: str) -> None:
    super().__init__(human_readable_device_name=name, vid=0x16D0, pid=0)
    self.written: List[bytes] = []
    self._pending: List[bytes] = []

  async def setup(self) -> None: ...

  async def stop(self) -> None: ...

  def _answer(self, report: bytes) -> List[bytes]:
    """The reports the reader sends back for `report`."""
    reader = Reader(report)
    report_id = reader.u16()
    answered = report[62:64] == ANSWERED_ROUTING
    if report_id == 0x0300:
      status = Writer().u16(0x0300).u8(1).u8(1).u8(0).u32(1234).u8(0).u8(1).finish()
      return [_report(status)]
    if report_id == 0x0310:
      environment = Writer().u16(0x0310).i16(2512).i16(456).i16(0).i16(0).i16(16384).finish()
      return [_report(environment)]
    if report_id == 0x0050:
      return [_report(Writer().u16(0x0050).u32(7).finish())]
    if report_id == 0x0080:
      versions = Writer().u16(0x0080)
      for version in (1, 2, 0, 3, 0, 4):
        versions.u32(version)
      return [_report(versions.finish())]
    if report_id == 0x0010 and answered:
      chunks = []
      for seq, ids in enumerate((SUPPORTED_REPORTS[:5], SUPPORTED_REPORTS[5:])):
        writer = Writer().u16(0x0010).u8(seq).u8(2)
        for index in range(29):
          writer.u16(ids[index] if index < len(ids) else 0)
        chunks.append(_report(writer.finish()))
      return chunks
    if report_id == 0x0200 and answered:
      field = reader.u16()
      text = DATA_FIELDS[field].encode()
      return [_report(Writer().u16(0x0200).u16(field).u8(0x02).raw_bytes(text).finish())]
    if report_id == 0x0330:
      writer = Writer().u16(0x0330)
      for index in range(30):
        writer.i16(WAVELENGTHS[index] if index < len(WAVELENGTHS) else 0)
      return [_report(writer.finish())]
    if report_id == 0x0320:
      signal, reference = reader.i16(), reader.i16()
      return _chunks(0x0500, lambda w: w.i16(signal).i16(reference).u32(500))
    if report_id == 0x0340:
      integration = reader.i32()
      return _chunks(0x0600, lambda w: w.u32(integration).u32(500))
    return []

  async def write(self, data: bytes, report_id: bytes = b"\x00") -> None:
    self.written.append(report_id + data)
    self._pending.extend(self._answer(data))

  async def read(self, size: int, timeout: int) -> bytes:
    if not self._pending:
      raise AssertionError("the reader has nothing to send")
    return self._pending.pop(0)


def to_jsonable(value: Any) -> Any:
  """`value` as JSON can hold it. Timestamps are the placeholder "<timestamp>": they are the time
  of the run."""
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return to_jsonable(dataclasses.asdict(value))
  if isinstance(value, datetime.datetime):
    return "<timestamp>"
  if isinstance(value, enum.Enum):
    return value.name
  if isinstance(value, dict):
    return {str(key): to_jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [to_jsonable(item) for item in value]
  return value


class Recorder:
  """Runs a scenario's steps and records each: the reports written, as hex, what the call
  returned or raised, and the resource tree under `root` when the step changed it."""

  def __init__(self, root: handles.Resource, driver: Optional[ByonoyDriver] = None) -> None:
    self.root = root
    self.io: Optional[FakeByonoyHID] = None
    if driver is not None:
      self.io = FakeByonoyHID(driver.io.human_readable_device_name)
      driver.io = self.io
    self.steps: List[Dict[str, Any]] = []
    self._resources: List[Dict[str, Any]] = []

  async def start(self) -> "Recorder":
    """Take the tree before the first step."""
    self._resources = await snapshot_store(self.root.store, self.root)
    return self

  async def step(self, call: str, action: Callable[[], Union[Any, Awaitable[Any]]]) -> Any:
    """Run `action`; record it as `call`."""
    if self.io is not None:
      self.io.written = []
    returned: Any = None
    entry: Dict[str, Any] = {"call": call}
    try:
      returned = action()
      if inspect.isawaitable(returned):
        returned = await returned
    except Exception as error:  # a refusal is part of the record
      entry["error"] = f"{type(error).__name__}: {error}"
    else:
      entry["result"] = to_jsonable(returned)
    entry["sent"] = [] if self.io is None else [report.hex() for report in self.io.written]
    resources = await snapshot_store(self.root.store, self.root)
    if resources != self._resources:
      entry["resources"] = resources
      self._resources = resources
    self.steps.append(entry)
    return returned

  async def check(self, test: unittest.TestCase, scenario: str) -> None:
    """Compare the record with the scenario's golden file."""
    record = {"steps": self.steps, "resources": await snapshot_store(self.root.store, self.root)}
    check_golden(test, GOLDEN / f"{scenario}.json", record)


async def plate(store: ResourceStore, name: str, model: str = "cor_96_wellplate_360uL_Fb"):
  """A plate of `model` in `store`."""
  created = await store.create(model, name)
  assert isinstance(created, handles.Plate)
  return created


class Absorbance96GoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_illumination_unit_and_plate(self):
    """A plate goes on only without the illumination unit on the base, the unit goes on only over
    a plate that clears it, and nothing goes on the base itself."""
    reader, illumination_unit = await byonoy_a96a("reader")
    assert reader.body is not None
    recorder = await Recorder(reader.body).start()
    store = reader.store
    plate_ = await plate(store, "plate")
    loose = await plate(store, "loose")
    tall = await plate(store, "tall", "cor_96_wellplate_2mL_Vb")
    holder = reader.plate_holder
    unit_holder = reader.illumination_unit_holder
    await recorder.step(
      "plate_holder.check_can_drop_resource_here(plate)  # unit on",
      lambda: holder.check_can_drop_resource_here(plate_),
    )
    await recorder.step(
      "plate_holder.assign_child_resource(plate)  # unit on",
      lambda: holder.assign_child_resource(plate_),
    )
    await recorder.step(
      "plate_holder.unassign_child_resource(plate)",
      lambda: holder.unassign_child_resource(plate_),
    )
    await recorder.step(
      "reader.assign_child_resource(loose)",
      lambda: reader.assign_child_resource(loose, location=None),
    )
    await recorder.step(
      "illumination_unit_holder.unassign_child_resource(illumination_unit)",
      lambda: unit_holder.unassign_child_resource(illumination_unit),
    )
    await recorder.step(
      "plate_holder.assign_child_resource(tall)", lambda: holder.assign_child_resource(tall)
    )
    await recorder.step(
      "illumination_unit_holder.check_can_drop_resource_here(illumination_unit)  # tall plate",
      lambda: unit_holder.check_can_drop_resource_here(illumination_unit),
    )
    await recorder.step(
      "illumination_unit_holder.assign_child_resource(illumination_unit)  # tall plate",
      lambda: unit_holder.assign_child_resource(illumination_unit),
    )
    await recorder.step(
      "illumination_unit_holder.unassign_child_resource(illumination_unit)",
      lambda: unit_holder.unassign_child_resource(illumination_unit),
    )
    await recorder.step(
      "plate_holder.unassign_child_resource(tall)", lambda: holder.unassign_child_resource(tall)
    )
    await recorder.step(
      "plate_holder.assign_child_resource(plate)", lambda: holder.assign_child_resource(plate_)
    )
    await recorder.step(
      "illumination_unit_holder.check_can_drop_resource_here(illumination_unit)",
      lambda: unit_holder.check_can_drop_resource_here(illumination_unit),
    )
    await recorder.step(
      "illumination_unit_holder.assign_child_resource(illumination_unit)",
      lambda: unit_holder.assign_child_resource(illumination_unit),
    )
    await recorder.check(self, "absorbance_96_illumination_unit_and_plate")

  async def test_reads(self):
    """Setup, then absorbance of the whole plate and of column 1."""
    reader, illumination_unit = await byonoy_a96a("reader", assign=False)
    plate_ = await plate(reader.store, "plate")
    await reader.plate_holder.assign_child_resource(plate_)
    await reader.illumination_unit_holder.assign_child_resource(illumination_unit)
    assert reader.body is not None
    recorder = await Recorder(reader.body, reader).start()
    await recorder.step("setup()", reader.setup)
    await recorder.step(
      "read_absorbance(plate, plate.get_all_items(), 600)",
      lambda: reader.read_absorbance(plate_, plate_.items, 600),
    )
    await recorder.step(
      "read_absorbance(plate, plate['A1:H1'], 450)",
      lambda: reader.read_absorbance(plate_, plate_["A1:H1"], 450),
    )
    await recorder.step(
      "read_absorbance(plate, plate.get_all_items(), 500)  # not available",
      lambda: reader.read_absorbance(plate_, plate_.items, 500),
    )
    await recorder.step("stop()", reader.stop)
    await recorder.check(self, "absorbance_96_reads")

  async def test_parts(self):
    """The parking unit, the SBS adapter and a detection unit, as built."""
    store = ResourceStore.in_memory()
    parts = await store.create(build.resource("parts", Coordinate(1000, 1000, 100)), "parts")
    recorder = await Recorder(parts).start()

    async def build_parts() -> None:
      await byonoy_a96a_parking_unit("parking_unit", store=store).create_body()
      adapter = await store.create(byonoy_sbs_adapter("sbs_adapter"), "sbs_adapter")
      await ByonoyAbsorbance96("detection_unit", store=store).create_body()
      for name in ("parking_unit", "sbs_adapter", "detection_unit"):
        part = adapter if name == "sbs_adapter" else await store.get(name)
        await assign_unlocated(parts, part)

    await recorder.step(
      "assign byonoy_a96a_parking_unit, byonoy_sbs_adapter, ByonoyAbsorbance96", build_parts
    )
    await recorder.check(self, "absorbance_96_parts")


class Luminescence96GoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_reader_unit_and_plate(self):
    """A plate goes on only without the reader unit on the base, and nothing goes on the base
    itself."""
    base, reader = await byonoy_l96a("lum")
    assert base.body is not None and reader.body is not None
    reader_body = reader.body
    recorder = await Recorder(base.body).start()
    plate_ = await plate(base.store, "plate")
    loose = await plate(base.store, "loose")
    holder = base.plate_holder
    await recorder.step(
      "plate_holder.check_can_drop_resource_here(plate)  # reader unit on",
      lambda: holder.check_can_drop_resource_here(plate_),
    )
    await recorder.step(
      "plate_holder.assign_child_resource(plate)  # reader unit on",
      lambda: holder.assign_child_resource(plate_),
    )
    await recorder.step(
      "plate_holder.unassign_child_resource(plate)",
      lambda: holder.unassign_child_resource(plate_),
    )
    await recorder.step(
      "base.assign_child_resource(loose)",
      lambda: base.assign_child_resource(loose, location=None),
    )
    await recorder.step(
      "reader_unit_holder.unassign_child_resource(reader)",
      lambda: base.reader_unit_holder.unassign_child_resource(reader_body),
    )
    await recorder.step(
      "plate_holder.check_can_drop_resource_here(plate)",
      lambda: holder.check_can_drop_resource_here(plate_),
    )
    await recorder.step(
      "plate_holder.assign_child_resource(plate)", lambda: holder.assign_child_resource(plate_)
    )
    await recorder.step(
      "reader_unit_holder.assign_child_resource(reader)",
      lambda: base.reader_unit_holder.assign_child_resource(reader_body),
    )
    await recorder.check(self, "luminescence_96_reader_unit_and_plate")

  async def test_commands_and_reads(self):
    """Setup, every request and LED command, and luminescence of the whole plate and of column 1;
    the well mask is in the 0x0340 report."""
    base, reader = await byonoy_l96a("lum", assign=False)
    plate_ = await plate(base.store, "plate")
    await base.plate_holder.assign_child_resource(plate_)
    assert base.body is not None and reader.body is not None
    await base.reader_unit_holder.assign_child_resource(reader.body)
    recorder = await Recorder(base.body, reader).start()
    await recorder.step("setup()", reader.setup)
    await recorder.step("request_status()", reader.request_status)
    await recorder.step("request_environment()", reader.request_environment)
    await recorder.step("request_api_version()", reader.request_api_version)
    await recorder.step("request_supported_reports()", reader.request_supported_reports)
    await recorder.step("request_device_info()", reader.request_device_info)
    await recorder.step("request_versions()", reader.request_versions)
    await recorder.step("set_led_color((0, 128, 255))", lambda: reader.set_led_color((0, 128, 255)))
    await recorder.step(
      "set_led_color((255, 0, 0), 'breathing', low_power=True, force=True, duration_ms=1500)",
      lambda: reader.set_led_color(
        (255, 0, 0), "breathing", low_power=True, force=True, duration_ms=1500
      ),
    )
    await recorder.step(
      "set_led_colors([(1, 2, 3), (4, 5, 6)])",
      lambda: reader.set_led_colors([(1, 2, 3), (4, 5, 6)]),
    )
    await recorder.step("cancel()  # nothing in flight", reader.cancel)
    await recorder.step(
      "read_luminescence(plate, plate.get_all_items())",
      lambda: reader.read_luminescence(plate_, plate_.items),
    )
    await recorder.step(
      "read_luminescence(plate, plate['A1:H1'], integration_time=0.5)",
      lambda: reader.read_luminescence(plate_, plate_["A1:H1"], integration_time=0.5),
    )
    await recorder.step(
      "read_luminescence(plate, plate['A1', 'H12'], mode='rapid')",
      lambda: reader.read_luminescence(plate_, plate_.get_items(["A1", "H12"]), mode="rapid"),
    )
    await recorder.step(
      "read_luminescence(plate, plate.get_all_items(), mode='custom')  # no integration time",
      lambda: reader.read_luminescence(plate_, plate_.items, mode="custom"),
    )
    await recorder.step("stop()", reader.stop)
    await recorder.check(self, "luminescence_96_commands_and_reads")

  async def test_l96_parts(self):
    """The L96 (not automate) base and reader unit, as built and assigned."""
    base, _ = await byonoy_l96("l96")
    assert base.body is not None
    recorder = await Recorder(base.body).start()
    await recorder.check(self, "luminescence_96_l96_parts")


if __name__ == "__main__":
  unittest.main()
