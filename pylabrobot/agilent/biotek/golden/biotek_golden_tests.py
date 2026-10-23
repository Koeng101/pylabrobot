"""Golden tests of what the BioTek RDOP22 readers (Cytation 1/5, Synergy H1) do today.

Each scenario runs a reader against a scripted serial transport and records, per step, every
byte written to the transport (hex, in order) and every camera call, with what the step
returned. The plates live in an in-memory resource store and are snapshotted with `snapshot_store` before
and after: readers take the plate as an argument and must not change it.
"""

from __future__ import annotations

import pathlib
import unittest
import unittest.mock
from typing import Any, Awaitable, Dict, List, Optional, Sequence, Tuple, cast

from pylabrobot.agilent.biotek import Cytation1, Cytation5, CytationImagingConfig, SynergyH1
from pylabrobot.agilent.biotek.cytation.microscope.aravis_camera import AravisCamera
from pylabrobot.agilent.biotek.cytation.microscope.models import (
  ImagingMode,
  ImagingResult,
  Objective,
)
from pylabrobot.agilent.biotek.plate_reader_base import BioTekPlateReaderDriver
from pylabrobot.agilent.biotek.results import (
  AbsorbanceResult,
  FluorescenceResult,
  LuminescenceResult,
)
from pylabrobot.io.ftdi import FTDI
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

# Capability replies (first data byte) by capability number; unlisted ones report "0".
CAPABILITIES = {2000: "1", 2056: "0", 2064: "1", 2138: "1"}
# A valid D (assay) reply: length, data, checksum, status.
ASSAY_REPLY = b"0350000000000000010000000000490300000\x03"
STATUS_OK = b"0000\x03"
# Filter cube replies by slot query: DAPI in slot 1, GFP in slot 2, the others empty. Objective
# queries report a 4x phase objective in the first position only.
FILTER_REPLIES = {b"q1": b"1225100 DAPI ", b"q2": b"1225101 GFP ", b"q3": b"", b"q4": b""}


def _measurement_body(bounds: Tuple[int, int, int, int]) -> bytes:
  """A measurement frame for the one-based, inclusive (row, column) bounds of a D command.

  Each well reads `row / 10 + column / 1000`, so every well of a 384-well plate is distinct.
  """
  min_row, min_col, max_row, max_col = bounds
  rows = []
  for row in range(min_row, max_row + 1):
    rows.append(
      ",".join(
        f"{row:02},{col:02},{row / 10 + col / 1000:+.4f}" for col in range(min_col, max_col + 1)
      )
    )
  return b"01,1,\r000:00:00.0,228," + "\r\n,".join(rows).encode() + b"\r\n228\x1a041\x1a0000\x03"


class FakeReaderIO:
  """A serial transport that answers BioTek commands and records everything it is sent.

  A command byte is answered with ACK; then either its parameters are written, or the reply
  to the bare command is read. `sent` holds writes as hex and other transport calls by name.
  Buffer purges carry no data and are not recorded.
  """

  def __init__(self, sent: List[str], version: str) -> None:
    self.sent = sent
    self.version = version
    self.device_id = "fake"
    self._buffer = bytearray()
    self._command = b""
    self._parameters: Optional[bytes] = None
    self._phase = "idle"
    self._bounds = (1, 1, 1, 1)

  def _reply(self) -> bytes:
    command, parameters = self._command, self._parameters
    if command == b"z":
      assert parameters is not None
      supported = CAPABILITIES.get(int(parameters[:4]), "0")
      return (supported + "0" * 16).encode() + STATUS_OK
    if command == b"e":
      return f"1650200  Version {self.version}   ".encode() + STATUS_OK
    if command == b"C":
      return b"12345678        " + STATUS_OK
    if command == b"h":
      return b"236" + STATUS_OK
    if command == b"&":
      return b"00" + STATUS_OK
    if command == b"i" and parameters in FILTER_REPLIES:
      return FILTER_REPLIES[parameters] + STATUS_OK
    if command == b"i" and parameters is not None and parameters.startswith(b"h"):
      return (b"1320520 " if parameters == b"h2" else b"****") + STATUS_OK
    if command == b"D":
      assert parameters is not None
      self._bounds = (
        int(parameters[6:8]),
        int(parameters[8:10]),
        int(parameters[10:12]),
        int(parameters[12:14]),
      )
      return ASSAY_REPLY
    if command == b"O":
      return STATUS_OK + _measurement_body(self._bounds)
    return STATUS_OK

  async def write(self, data: bytes) -> int:
    self.sent.append(data.hex())
    if self._phase == "acked":
      self._parameters = data
      self._phase = "parameters"
    else:
      self._command = data
      self._parameters = None
      self._phase = "command"
    return len(data)

  async def read(self, length: int) -> bytes:
    if not self._buffer:
      if self._phase == "command":
        self._buffer.extend(b"\x06")
        self._phase = "acked"
      elif self._phase in ("acked", "parameters"):
        self._buffer.extend(self._reply())
        self._phase = "replied"
      else:
        raise AssertionError("the reader read with no reply pending")
    data = bytes(self._buffer[:length])
    del self._buffer[:length]
    return data

  async def usb_purge_rx_buffer(self) -> None:
    self._buffer.clear()

  async def usb_purge_tx_buffer(self) -> None:
    pass

  async def setup(self) -> None:
    self.sent.append("setup()")

  async def stop(self) -> None:
    self.sent.append("stop()")

  async def usb_reset(self) -> None:
    self.sent.append("usb_reset()")

  async def set_latency_timer(self, latency: int) -> None:
    self.sent.append(f"set_latency_timer({latency})")

  async def set_baudrate(self, baudrate: int) -> None:
    self.sent.append(f"set_baudrate({baudrate})")

  async def set_line_property(self, bits: int, stopbits: int, parity: int) -> None:
    self.sent.append(f"set_line_property({bits}, {stopbits}, {parity})")

  async def set_flowctrl(self, flowctrl: int) -> None:
    self.sent.append(f"set_flowctrl({flowctrl})")

  async def set_rts(self, level: bool) -> None:
    self.sent.append(f"set_rts({level})")


class FakeCamera(AravisCamera):
  """A camera that records its calls into the transport's log; frames are numbered names."""

  def __init__(self, sent: List[str]) -> None:
    super().__init__()
    self.sent = sent
    self._frames = 0
    self._exposure = 0.0

  async def setup(self, serial_number: Optional[str] = None) -> None:
    self.sent.append(f"camera.setup({serial_number})")

  async def stop(self) -> None:
    self.sent.append("camera.stop()")

  def start_acquisition(self) -> None:
    self.sent.append("camera.start_acquisition()")

  def stop_acquisition(self) -> None:
    self.sent.append("camera.stop_acquisition()")

  async def set_auto_exposure(self, mode: str) -> None:
    self.sent.append(f"camera.set_auto_exposure({mode})")

  async def set_exposure(self, exposure_ms: float) -> None:
    self.sent.append(f"camera.set_exposure({exposure_ms})")
    self._exposure = exposure_ms

  async def get_exposure(self) -> float:
    return self._exposure

  async def set_auto_gain(self, mode: str) -> None:
    self.sent.append(f"camera.set_auto_gain({mode})")

  async def set_gain(self, gain: float) -> None:
    self.sent.append(f"camera.set_gain({gain})")

  async def trigger(self, timeout_ms: int = 5000) -> Any:
    self._frames += 1
    self.sent.append(f"camera.trigger({timeout_ms})")
    return f"frame{self._frames}"


def _result(value: Any) -> Any:
  """A reader's return value, JSON-able. Result timestamps are the host clock and are left
  out."""
  if isinstance(value, list):
    return [_result(item) for item in value]
  if isinstance(value, AbsorbanceResult):
    return {"wavelength": value.wavelength, "temperature": value.temperature, "data": value.data}
  if isinstance(value, FluorescenceResult):
    return {
      "excitation_wavelength": value.excitation_wavelength,
      "emission_wavelength": value.emission_wavelength,
      "temperature": value.temperature,
      "data": value.data,
    }
  if isinstance(value, LuminescenceResult):
    return {"temperature": value.temperature, "data": value.data}
  if isinstance(value, ImagingResult):
    return {
      "images": value.images,
      "exposure_time": value.exposure_time,
      "focal_height": value.focal_height,
    }
  if isinstance(value, bytes):
    return value.hex()
  return value


class Recorder:
  """Runs a reader's steps against the fake transport and collects the golden record."""

  def __init__(self, reader: BioTekPlateReaderDriver, version: str, store: ResourceStore) -> None:
    self.store = store
    self.sent: List[str] = []
    self.io = FakeReaderIO(self.sent, version)
    reader.io = cast(FTDI, self.io)
    self.steps: List[Dict[str, Any]] = []

  async def step(self, call: str, operation: Awaitable[Any]) -> Any:
    """Run one call, recording what it sent and what it returned or raised."""
    self.sent.clear()
    entry: Dict[str, Any] = {"call": call}
    result: Any = None
    try:
      result = await operation
      entry["result"] = _result(result)
    except Exception as error:
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = list(self.sent)
    self.steps.append(entry)
    return result

  async def check(
    self,
    test: unittest.TestCase,
    name: str,
    plates: Sequence[handles.Resource],
    before: List[Any],
  ) -> None:
    """Check the record against `<name>.json`, after checking the plates are unchanged."""
    after = [await snapshot_store(self.store, plate) for plate in plates]
    test.assertEqual(before, after)
    check_golden(
      test,
      GOLDEN / f"{name}.json",
      {"steps": self.steps, "resources": [entry for snapshot in after for entry in snapshot]},
    )


async def _plate(
  store: ResourceStore,
  model: str,
  name: str,
  with_lid: bool = False,
  parent: Optional[handles.Resource] = None,
) -> handles.Plate:
  """A plate of a model in `store`, with the model's lid when asked."""
  location = Coordinate.zero() if parent is not None else None
  plate = await store.create(model, name=name, parent=parent, location=location)
  assert isinstance(plate, handles.Plate)
  if with_lid:
    await store.create(f"{model}_lid", name=f"{name}_lid", parent=plate)
  return plate


def _store(test: unittest.IsolatedAsyncioTestCase) -> ResourceStore:
  """An in-memory store for one test, closed after it."""
  store = ResourceStore.in_memory()
  test.addAsyncCleanup(store.close)
  return store


def _plate_holder(name: str) -> pb.ResourceDefinition:
  """A plate holder the size of the reader's tray, as the golden records name it."""
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 0),
    kind=pb.RESOURCE_KIND_PLATE_HOLDER,
    category="plate_holder",
    holder=pb.HolderSpec(child_location=build.vec3(Coordinate.zero()), pedestal_size_z=0),
  )


def _make(factory: Any) -> Any:
  """Build a reader without the FTDI library; its transport is replaced by the fake."""
  with unittest.mock.patch("pylabrobot.io.ftdi.HAS_PYLIBFTDI", True):
    with unittest.mock.patch("pylabrobot.io.ftdi.HAS_PYUSB", True):
      return factory()


class CytationReadTests(unittest.IsolatedAsyncioTestCase):
  """Plate geometry, tray and reads on a Cytation 5, a Cytation 1 and a Synergy H1."""

  async def test_setup_and_tray(self):
    store = _store(self)
    reader: Cytation5 = _make(lambda: Cytation5(name="cytation5", use_cam=False))
    plate = await _plate(store, "cor_96_wellplate_360uL_Fb", "plate_96_lid", with_lid=True)
    before = [await snapshot_store(store, plate)]
    rec = Recorder(reader, version="2.07", store=store)
    await rec.step("setup()", reader.setup())
    await rec.step("open()", reader.open())
    await rec.step("close(plate=plate_96_lid)", reader.close(plate=plate))
    await rec.step("open(slow=True)", reader.open(slow=True))
    await rec.step("close(plate=plate_96_lid)", reader.close(plate=plate))
    await rec.step("close()", reader.close())
    await rec.step("request_current_temperature()", reader.request_current_temperature())
    await rec.check(self, "cytation5_setup_and_tray", [plate], before)

  async def test_plate_geometries(self):
    store = _store(self)
    reader: Cytation1 = _make(lambda: Cytation1(name="cytation1"))
    plates = [
      await _plate(store, "cellvis_96_wellplate_350uL_Fb", "plate_96"),
      await _plate(store, "cor_96_wellplate_360uL_Fb", "plate_96_lid", with_lid=True),
      await _plate(store, "Greiner_384_wellplate_28ul_Fb", "plate_384"),
      await _plate(store, "cellvis_24_wellplate_3600uL_Fb", "plate_24"),
      await _plate(store, "cor_cos_6_wellplate_16800uL_Fb", "plate_6"),
    ]
    before = [await snapshot_store(store, plate) for plate in plates]
    rec = Recorder(reader, version="1.04", store=store)
    for plate in plates:
      await rec.step(f"set_plate({plate.name})", reader.set_plate(plate))
    await rec.step("set_plate(plate_6)", reader.set_plate(plates[-1]))
    reader.clear_plate()
    await rec.step("set_plate(plate_6)", reader.set_plate(plates[-1]))
    await rec.check(self, "cytation1_plate_geometries", plates, before)

  async def test_absorbance(self):
    store = _store(self)
    reader: Cytation5 = _make(lambda: Cytation5(name="cytation5", use_cam=False))
    plate_96 = await _plate(store, "cellvis_96_wellplate_350uL_Fb", "plate_96")
    plate_384 = await _plate(store, "Greiner_384_wellplate_28ul_Fb", "plate_384")
    other = await _plate(store, "cellvis_96_wellplate_350uL_Fb", "other_96")
    before = [await snapshot_store(store, plate_96), await snapshot_store(store, plate_384)]
    rec = Recorder(reader, version="2.07", store=store)
    await rec.step(
      "read_absorbance(plate_96, all wells, 450)",
      reader.read_absorbance(plate_96, plate_96.get_wells(plate_96.identifiers), wavelength=450),
    )
    wells_384 = (
      plate_384.get_wells("A1:B3") + plate_384.get_wells(["P24"]) + plate_384.get_wells(["C2"])
    )
    await rec.step(
      "read_absorbance(plate_384, A1:B3 + P24 + C2, 600)",
      reader.read_absorbance(plate_384, wells_384, wavelength=600),
    )
    await rec.step(
      "read_absorbance(plate_96, wells of other_96, 450)",
      reader.read_absorbance(plate_96, other.get_wells("A1:A2"), wavelength=450),
    )
    await rec.check(self, "cytation5_absorbance", [plate_96, plate_384], before)

  async def test_fluorescence_and_luminescence(self):
    store = _store(self)
    reader: Cytation5 = _make(lambda: Cytation5(name="cytation5", use_cam=False))
    plate_24 = await _plate(store, "cellvis_24_wellplate_3600uL_Fb", "plate_24")
    plate_6 = await _plate(store, "cor_cos_6_wellplate_16800uL_Fb", "plate_6")
    before = [await snapshot_store(store, plate_24), await snapshot_store(store, plate_6)]
    rec = Recorder(reader, version="2.07", store=store)
    await rec.step(
      "read_fluorescence(plate_24, all wells, 485, 528, 7.5)",
      reader.read_fluorescence(
        plate_24, plate_24.get_wells(plate_24.identifiers), 485, 528, focal_height=7.5
      ),
    )
    await rec.step(
      "read_luminescence(plate_6, A1 + B2:B3, 4.5, integration_time=0.4)",
      reader.read_luminescence(
        plate_6,
        plate_6.get_wells(["A1"]) + plate_6.get_wells("B2:B3"),
        focal_height=4.5,
        integration_time=0.4,
      ),
    )
    await rec.step(
      "read_luminescence(plate_24, wells of plate_6, 4.5)",
      reader.read_luminescence(plate_24, plate_6.get_wells(["A1"]), focal_height=4.5),
    )
    await rec.check(self, "cytation5_fluorescence_and_luminescence", [plate_24, plate_6], before)

  async def test_synergy_h1_luminescence_on_a_lidded_plate(self):
    store = _store(self)
    reader: SynergyH1 = _make(lambda: SynergyH1(name="synergy_h1"))
    holder = await store.create(
      _plate_holder("synergy_h1_plate_holder"), name="synergy_h1_plate_holder"
    )
    plate = await _plate(
      store, "cor_96_wellplate_360uL_Fb", "plate_96_lid", with_lid=True, parent=holder
    )
    before = [await snapshot_store(store, holder)]
    rec = Recorder(reader, version="2.07", store=store)
    await rec.step(
      "read_luminescence(plate_96_lid, A1:H2, 10.0, integration_time=1)",
      reader.read_luminescence(
        plate, plate.get_wells("A1:H2"), focal_height=10.0, integration_time=1
      ),
    )
    await rec.step(
      "read_luminescence(plate_96_lid, A1, 12.0)",
      reader.read_luminescence(plate, plate.get_wells(["A1"]), focal_height=12.0),
    )
    await rec.check(self, "synergy_h1_luminescence_lidded", [holder], before)


class CytationMicroscopeTests(unittest.IsolatedAsyncioTestCase):
  """Capture tiling from the first well's size, on a Cytation 5 with a fake camera."""

  async def test_captures_on_several_plates(self):
    store = _store(self)
    config = CytationImagingConfig(
      filters=[ImagingMode.DAPI, ImagingMode.GFP, None, None],
      objectives=[Objective.O_4X_PL_FL, Objective.O_10X_PL_FL, Objective.O_20X_PL_FL, None],
    )
    reader: Cytation5 = _make(
      lambda: Cytation5(name="cytation5", use_cam=False, imaging_config=config)
    )
    plate_96 = await _plate(store, "cellvis_96_wellplate_350uL_Fb", "plate_96")
    plate_384 = await _plate(store, "Greiner_384_wellplate_28ul_Fb", "plate_384")
    plate_24 = await _plate(store, "cellvis_24_wellplate_3600uL_Fb", "plate_24")
    plates = [plate_96, plate_384, plate_24]
    before = [await snapshot_store(store, plate) for plate in plates]
    rec = Recorder(reader, version="2.07", store=store)
    reader.microscope.camera = FakeCamera(rec.sent)
    await rec.step("setup()", reader.setup())
    await rec.step(
      "capture(plate_96, B3, brightfield, 4x, coverage=full)",
      reader.microscope.capture(
        row=2,
        column=3,
        mode=ImagingMode.BRIGHTFIELD,
        objective=Objective.O_4X_PL_FL,
        exposure_time=5,
        focal_height=3.0,
        gain=10,
        plate=plate_96,
        coverage="full",
      ),
    )
    await rec.step(
      "capture(plate_384, P24, GFP, 10x, coverage=full)",
      reader.microscope.capture(
        row=16,
        column=24,
        mode=ImagingMode.GFP,
        objective=Objective.O_10X_PL_FL,
        exposure_time=20,
        focal_height=2.5,
        gain="machine-auto",
        plate=plate_384,
        coverage="full",
        led_intensity=6,
      ),
    )
    await rec.step(
      "capture(plate_24, A1, DAPI, 20x, coverage=(2, 3), center=(0.5, -0.25))",
      reader.microscope.capture(
        row=1,
        column=1,
        mode=ImagingMode.DAPI,
        objective=Objective.O_20X_PL_FL,
        exposure_time="machine-auto",
        focal_height=4.0,
        gain=1,
        plate=plate_24,
        coverage=(2, 3),
        center_position=(0.5, -0.25),
      ),
    )
    await rec.step(
      "capture(plate_24, A1, phase contrast, 20x)",
      reader.microscope.capture(
        row=1,
        column=1,
        mode=ImagingMode.PHASE_CONTRAST,
        objective=Objective.O_20X_PL_FL,
        exposure_time=10,
        focal_height=4.0,
        gain=1,
        plate=plate_24,
      ),
    )
    await rec.step("stop()", reader.stop())
    await rec.check(self, "cytation5_microscope_captures", plates, before)


if __name__ == "__main__":
  unittest.main()
