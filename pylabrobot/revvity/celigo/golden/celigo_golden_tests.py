"""Golden tests of what the Celigo does with a plate today.

The Celigo is not a resource: a plate is given to it (`set_plate`, or per scan), and it reads
the plate's well locations and sizes and its Y size to place the stage. Each scenario drives the
public API against a fake controller board that answers every packet, and records every packet
written to the board (hex) and every camera call, in order, per step. The plate is snapshotted
before and after, to pin that the Celigo leaves it unchanged.
"""

from __future__ import annotations

import pathlib
import re
import struct
import unittest
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from unittest.mock import patch

from pylabrobot.resources.corning.costar.plates import cor_cos_6_wellplate_16800uL_Fb
from pylabrobot.resources.corning.plates import cor_96_wellplate_360uL_Fb
from pylabrobot.resources.greiner.plates import Greiner_384_wellplate_28ul_Fb
from pylabrobot.resources.plate import Plate
from pylabrobot.revvity.celigo.camera import CameraFrame
from pylabrobot.revvity.celigo.celigo import Celigo, ControllerInfo, _fletcher16
from pylabrobot.revvity.celigo.config import (
  Calibrated2DPolynomialTransform,
  CeligoHardwareConfig,
  DigitalIOConfig,
  FilterMapEntry,
  GalvoAxisOpticalCalibration,
  GalvoMagnificationCalibration,
  GalvoOpticalCalibration,
  IlluminationChannelConfig,
  IOConfig,
  LightingIOConfig,
)
from pylabrobot.revvity.celigo.scan import ScanResult
from pylabrobot.revvity.celigo.tests.helpers import (
  make_calibration_config,
  make_filter_wheel_config,
  make_galvo_config,
  make_hardware_default_config,
  make_linear_axis_config,
  make_navigation_config,
  make_test_config,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent

# Every motor reports both opto inputs active: the drawer limits are already reached and the
# dichroic wheel finds physical position one at its home offset.
_LIMIT_FLAGS = 0x0C
_MOTOR_FIRMWARE = "EZHR17EN v7.10"


class FakeControllerBoard:
  """Stands in for the FTDI link to the controller board: logs and answers every packet."""

  def __init__(self, log: List[str]) -> None:
    self.log = log
    self.motor_ticks: Dict[str, int] = {}
    self._pending = bytearray()

  async def write(self, data: bytes) -> int:
    self.log.append(data.hex())
    opcode = data[0]
    sequence = struct.unpack_from(">i", data, 1)[0]
    self._queue_reply(opcode, sequence, self._answer(opcode, bytes(data[11:])))
    return len(data)

  async def read(self, count: int) -> bytes:
    chunk = bytes(self._pending[:count])
    del self._pending[:count]
    return chunk

  async def usb_purge_rx_buffer(self) -> None:
    self.log.append("purge rx")

  async def usb_purge_tx_buffer(self) -> None:
    self.log.append("purge tx")

  def _queue_reply(self, opcode: int, sequence: int, payload: bytes) -> None:
    header = bytearray(12)
    header[1] = opcode
    struct.pack_into(">i", header, 2, sequence)
    struct.pack_into(">i", header, 6, len(payload))
    header[10], header[11] = _fletcher16(bytes(header), 10)
    self._pending += bytes(header) + payload

  def _answer(self, opcode: int, payload: bytes) -> bytes:
    if opcode == 44:  # motor query, NUL-terminated EZStepper command
      text = self._motor_reply(payload.rstrip(b"\x00").decode("ascii")).encode("latin-1")
      return struct.pack(">HH", 0, len(text)) + text
    if opcode == 7:  # galvo move: settled
      return b"\x00\x00"
    if opcode == 12:  # galvo status: both ready, laser idle
      return struct.pack(">BBHHiiiBhh", 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    return b""

  def _motor_reply(self, command: str) -> str:
    address = command[1]
    tokens = command[2:].rstrip("\r")
    ticks = self.motor_ticks.get(address, 0)
    text = ""
    if tokens == "?8":
      text = str(ticks)
    elif tokens == "?4":
      text = str(_LIMIT_FLAGS)
    elif tokens == "?aE":
      text = "1000"
    elif tokens == "&":
      text = _MOTOR_FIRMWARE
    else:
      move = re.search(r"A(-?\d+)", tokens)
      if move is not None:
        self.motor_ticks[address] = int(move.group(1))
    return f"/0`{text}\x03\r\n"


class RecordingCamera:
  """A camera that logs every call and returns black frames of the configured format."""

  def __init__(self, log: List[str]) -> None:
    self.log = log
    self.is_open = False
    self.width = 8
    self.height = 8
    self.bit_depth = 8
    self.exposure_ms = 1.0
    self.gain = 0.0

  async def setup(self) -> None:
    self.log.append("camera setup")
    self.is_open = True

  async def stop(self) -> None:
    self.log.append("camera stop")
    self.is_open = False

  async def set_exposure(self, exposure_ms: float) -> float:
    self.log.append(f"camera set_exposure {exposure_ms}")
    self.exposure_ms = exposure_ms
    return exposure_ms

  async def set_gain(self, gain: float) -> float:
    self.log.append(f"camera set_gain {gain}")
    self.gain = gain
    return gain

  async def set_frame_format(
    self,
    width: int,
    height: int,
    x_offset: Optional[int] = None,
    y_offset: Optional[int] = None,
  ) -> Tuple[int, int]:
    self.log.append(f"camera set_frame_format {width} {height} {x_offset} {y_offset}")
    self.width, self.height = width, height
    return width, height

  async def capture(self, flush_frames: int = 2) -> CameraFrame:
    self.log.append(f"camera capture {flush_frames}")
    return CameraFrame(
      data=bytes(self.width * self.height),
      width=self.width,
      height=self.height,
      bit_depth=self.bit_depth,
      exposure_ms=self.exposure_ms,
      gain=self.gain,
      captured_at=0.0,
    )


def _hardware() -> CeligoHardwareConfig:
  def linear(axis_index: int, max_position: float) -> Any:
    return make_linear_axis_config(
      axis_index=axis_index,
      max_velocity=40,
      max_acceleration=40,
      moving_current_percentage=65,
      holding_current_percentage=20,
      loading_current_percentage=55,
      min_position=0,
      max_position=max_position,
      mm_per_encoder_tick=0.001,
    )

  def lighting(channel: int, name: str) -> LightingIOConfig:
    return LightingIOConfig(
      config_version=1000,
      controller_index=0,
      channel=channel,
      enabled=True,
      invert=False,
      io_name=name,
      min_voltage=0,
      max_voltage=10,
      delay=0.0,
    )

  def digital(bit_index: int, name: str) -> DigitalIOConfig:
    return DigitalIOConfig(
      config_version=1000,
      io_type="Out",
      bit_index=bit_index,
      invert=False,
      enabled=True,
      io_name=name,
    )

  return CeligoHardwareConfig(
    x_axis=linear(1, 150),
    y_axis=linear(2, 110),
    z_axis=linear(3, 5),
    x_galvo=make_galvo_config(min_voltage=-10, max_voltage=10),
    y_galvo=make_galvo_config(controller_index=1, min_voltage=-10, max_voltage=10),
    dichroic_filter_wheel=make_filter_wheel_config(
      axis_index=4,
      max_velocity=4000,
      max_acceleration=4000,
      index_velocity=1000,
      homing_velocity=1000,
      number_of_filters=4,
      encoder_ticks_per_revolution=8000,
      filter_map=[FilterMapEntry(logical_number=n, physical_number=n) for n in range(1, 5)],
    ),
    io=IOConfig(
      analog_ins=[],
      lighting_ios=[lighting(0, "eBrightFieldIntensity"), lighting(2, "eFluorescentIntensity")],
      digital_ios=[digital(4, "FLBit0"), digital(5, "FLBit1"), digital(6, "FLOnOff")],
    ),
  )


def _brightfield() -> IlluminationChannelConfig:
  return IlluminationChannelConfig(
    name="brightfield",
    display_name="Brightfield",
    logical_filter=1,
    bit_value=None,
    intensity_percent=50,
    lighting_io_name="eBrightFieldIntensity",
    strobe=False,
    z_offset_to_brightfield_mm=0.0,
    mm_per_pixel_x_correction_to_brightfield=1.0,
    mm_per_pixel_y_correction_to_brightfield=1.0,
  )


def make_golden_celigo(log: List[str]) -> Celigo:
  """A Celigo on a fake controller board and camera, with an 8x8-pixel, 2 mm field of view."""
  config = make_test_config()
  config.hardware = _hardware()
  config.calibration = make_calibration_config(
    microns_per_pixel_x=250.0,
    microns_per_pixel_y=250.0,
    image_width_pixels=8,
    image_height_pixels=8,
    calibrated_z_position=1.5,
  )
  config.hardware_defaults = make_hardware_default_config(
    default_plate_x_corner_stage_coordinate=2.159,
    default_plate_y_corner_stage_coordinate=3.492,
  )
  config.navigation = make_navigation_config(
    frame_overlap_x_mm=0.1,
    frame_overlap_y_mm=0.1,
    max_galvo_deflection_x_mm=2.0,
    max_galvo_deflection_y_mm=2.0,
  )
  config.channels_by_magnification[config.magnification] = {"brightfield": _brightfield()}
  magnifications = {
    value: GalvoMagnificationCalibration(center_voltage=0.5, frame_size_volts=1.0)
    for value in (3, 5, 10, 20)
  }
  optical_axis = GalvoAxisOpticalCalibration(
    magnifications=magnifications,
    logical_filter_offsets={1: 0.25},
    laser_center_voltage=0.0,
    uv_laser_center_voltage=0.0,
  )
  config.galvo_optical_calibration = GalvoOpticalCalibration(x=optical_axis, y=optical_axis)
  config.galvo_calibrations = {
    1: Calibrated2DPolynomialTransform(
      forward={},
      reverse={"LinearXTerm": (0.5, 0.0), "LinearYTerm": (0.0, 0.5)},
      order=2,
    )
  }
  with (
    patch("pylabrobot.revvity.celigo.celigo.FTDI", return_value=FakeControllerBoard(log)),
    patch("pylabrobot.revvity.celigo.celigo.LumeneraCamera", return_value=RecordingCamera(log)),
  ):
    celigo = Celigo(config=config, fluorescence_warmup_seconds=0)
  # Firmware below 1.3 tunnels plain EZStepper ASCII commands.
  celigo.controller_info = ControllerInfo(
    device_index=0, firmware_version=(1, 2, 0), uart_buffer_length=64
  )
  return celigo


def _frame(frame: CameraFrame) -> Dict[str, Any]:
  # Frames from the fake camera are black; their format is what the scenario shapes.
  return {"width": frame.width, "height": frame.height, "bytes": len(frame.data)}


def _scan_result(result: ScanResult) -> List[Dict[str, Any]]:
  # Timings are wall-clock and are left out.
  return [
    {
      "label": frame.planned.block.label,
      "block": frame.planned.block.index,
      "block_stage_mm": [frame.planned.block.stage_x_mm, frame.planned.block.stage_y_mm],
      "tile": [frame.planned.position.tile_row, frame.planned.position.tile_column],
      "sample_mm": [frame.planned.position.sample_x_mm, frame.planned.position.sample_y_mm],
      "galvo_offset_mm": [
        frame.planned.position.galvo_offset_x_mm,
        frame.planned.position.galvo_offset_y_mm,
      ],
      "actual_stage_mm": list(frame.actual_stage_mm),
      "actual_z_mm": frame.actual_z_mm,
      "galvo_hardware_voltages": list(frame.galvo_hardware_voltages),
      "frame": _frame(frame.frame),
    }
    for frame in result.frames
  ]


class Recorder:
  """Runs scenario steps, recording what each sent and returned."""

  def __init__(self, plate: Plate) -> None:
    self.log: List[str] = []
    self.celigo = make_golden_celigo(self.log)
    self.plate = plate
    self.steps: List[Dict[str, Any]] = []

  async def step(
    self,
    call: str,
    action: Callable[[], Awaitable[Any]],
    shape: Callable[[Any], Any] = lambda value: value,
  ) -> None:
    del self.log[:]
    entry: Dict[str, Any] = {"call": call}
    try:
      entry["result"] = shape(await action())
    except Exception as error:  # the error is part of the record
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = list(self.log)
    self.steps.append(entry)

  async def prepare(self) -> None:
    """Reference the stage and dichroic wheel as setup leaves them."""

    async def reference() -> None:
      for axis in (self.celigo.x_axis, self.celigo.y_axis, self.celigo.z_axis):
        await axis.assume_homed()
      await self.celigo.dichroic_filter.home()

    await self.step("reference stage and dichroic wheel", reference)

  def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": snapshot_resources(self.plate)}


async def _set_plate(celigo: Celigo, plate: Plate) -> None:
  celigo.set_plate(plate)


class CeligoGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def _run_plate_protocol(
    self, plate: Plate, wells: Tuple[str, str, str], scenario: str
  ) -> None:
    first, middle, last = wells
    recorder = Recorder(plate)
    celigo = recorder.celigo
    before = snapshot_resources(plate)
    await recorder.prepare()
    await recorder.step(f"set_plate({plate.name})", lambda: _set_plate(celigo, plate))

    async def well_positions() -> Any:
      return [list(celigo.well_position_mm(name)) for name in wells]

    await recorder.step(f"well_position_mm({first}, {middle}, {last})", well_positions)
    await recorder.step("open_drawer()", celigo.open_drawer)
    await recorder.step(f"close_drawer({first})", lambda: celigo.close_drawer(first))
    await recorder.step(
      f"move_to_well({last}, retract_z=True)",
      lambda: celigo.move_to_well(last, retract_z=True),
      list,
    )
    await recorder.step(
      f"acquire({middle}, brightfield, exposure_ms=5, gain=2)",
      lambda: celigo.acquire(middle, "brightfield", exposure_ms=5, gain=2),
      lambda result: {
        "label": result.label,
        "x_mm": result.x_mm,
        "y_mm": result.y_mm,
        "z_mm": result.z_mm,
        "galvo_hardware_voltages": list(result.galvo_hardware_voltages),
        "frame": _frame(result.frame),
      },
    )
    await recorder.step(
      f"scan_wells(plate, [{first}, {last}], brightfield, block_shape=(2, 2))",
      lambda: celigo.scan_wells(
        plate, [first, last], channel="brightfield", block_shape=(2, 2), exposure_ms=5
      ),
      _scan_result,
    )
    await recorder.step("move_to_well(Z99) (no such well)", lambda: celigo.move_to_well("Z99"))
    record = recorder.record()
    self.assertEqual(record["resources"], before)
    check_golden(self, GOLDEN / f"{scenario}.json", record)

  async def test_96_well_plate_with_lid(self):
    plate = cor_96_wellplate_360uL_Fb(name="plate_96", with_lid=True)
    await self._run_plate_protocol(plate, ("A1", "D6", "H12"), "plate_96_with_lid")

  async def test_384_well_plate(self):
    plate = Greiner_384_wellplate_28ul_Fb(name="plate_384")
    await self._run_plate_protocol(plate, ("A1", "H12", "P24"), "plate_384")

  async def test_6_well_plate(self):
    plate = cor_cos_6_wellplate_16800uL_Fb(name="plate_6")
    await self._run_plate_protocol(plate, ("A1", "B2", "B3"), "plate_6")

  async def test_navigation_without_a_plate_is_refused(self):
    recorder = Recorder(cor_96_wellplate_360uL_Fb(name="plate_96"))
    celigo = recorder.celigo
    await recorder.prepare()
    await recorder.step("close_drawer(A1) (no plate set)", lambda: celigo.close_drawer("A1"))
    await recorder.step("move_to_well(A1) (no plate set)", lambda: celigo.move_to_well("A1"))
    check_golden(self, GOLDEN / "no_plate.json", recorder.record())


if __name__ == "__main__":
  unittest.main()
