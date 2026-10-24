"""Golden tests of what the SpectraMax M5 and 384 Plus send today, for plates of several shapes.

The seam is the serial port: a fake records every command written, in order, exactly as written,
and answers each with ``OK>`` and, for the commands that return data, a payload. Its plate data is shaped by the ``!XPOS`` / ``!YPOS`` the reader was sent, so a read's
result grid follows the plate's geometry as the device was told it.
"""

from __future__ import annotations

import pathlib
import unittest
from typing import Any, Awaitable, Dict, List, Optional, Type, Union

from pylabrobot.molecular_devices.spectramax import (
  KineticSettings,
  ShakeSettings,
  SpectraMax384Plus,
  SpectraMaxError,
  SpectraMaxM5,
  SpectrumSettings,
)
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent


def loading_tray(name: str) -> pb.ResourceDefinition:
  """The plate holder a reader's plate sits in: the scenarios' snapshot root."""
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 0),
    kind=pb.RESOURCE_KIND_PLATE_HOLDER,
    category="plate_holder",
    holder=pb.HolderSpec(child_location=build.vec3(Coordinate.zero()), pedestal_size_z=0),
  )


def strip_plate(name: str) -> pb.ResourceDefinition:
  """A one-column plate of eight wells: PLR's library has none."""
  well = build.resource(
    "{name}_well_{identifier}",
    Coordinate(6, 6, 10),
    kind=pb.RESOURCE_KIND_WELL,
    category="well",
    container=pb.ContainerSpec(),
  )
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 14.2),
    kind=pb.RESOURCE_KIND_PLATE,
    category="plate",
    itemized=pb.ItemizedSpec(
      num_items_x=1,
      num_items_y=8,
      grid=pb.ItemGrid(item=well, offset=build.vec3(Coordinate(10, 7, 1)), item_dx=9, item_dy=9),
    ),
    plate=pb.PlateSpec(plate_type="skirted"),
  )


class FakeSpectraMaxPort:
  """A serial port that records what is written and answers like a SpectraMax.

  Every command is answered with two fields in one line, ``OK><payload>>``, so a command the
  reader expects one or two fields for is answered either way. The payload is empty but for
  ``!STATUS``, ``!TEMP``, ``!ERROR``, ``!OPTION`` and ``!TRANSFER``. A command listed in `fail`
  is answered ``FAIL\\t<code>>`` instead.
  """

  def __init__(self, sent: List[str]) -> None:
    self.sent = sent
    self.fail: Dict[str, int] = {}
    self._pending: List[bytes] = []
    self._columns = 1
    self._rows = 1
    self._wavelength_blocks: List[str] = []
    self._transfers = 0

  async def setup(self) -> None:
    """Open nothing."""

  async def stop(self) -> None:
    """Close nothing."""

  def _plate_data(self) -> str:
    # One block per wavelength, one line per column, one value per row. A1 of the first transfer
    # is a negative value and B1 is saturated, so how the reader's parser treats them is pinned.
    lines = ["1234.5\t25.3", "PLA"]
    for block, header in enumerate(self._wavelength_blocks):
      lines.append(header)
      for column in range(self._columns):
        values = []
        for row in range(self._rows):
          if self._transfers == 0 and block == 0 and column == 0 and row == 0:
            values.append("-0.005")
          elif self._transfers == 0 and block == 0 and column == 0 and row == 1:
            values.append("#SAT")
          else:
            value = self._transfers + block * 0.1 + column * 0.01 + row * 0.001
            values.append(f"{value:.3f}")
        lines.append(f"{column + 1}:\t" + " ".join(values))
    self._transfers += 1
    return "\r\n".join(lines)

  def _payload(self, command: str) -> Optional[str]:
    base, _, arguments = command.partition(" ")
    words = arguments.split()
    if base == "!XPOS":
      self._columns = int(words[-1])
    elif base == "!YPOS":
      self._rows = int(words[-1])
    elif base == "!WAVELENGTH":
      self._wavelength_blocks = [f"L:\t{w.lstrip('F')}" for w in words]
    elif base == "!EXWAVELENGTH":
      self._wavelength_blocks = [f"L:\t{w}\t0" for w in words]
    elif base == "!EMWAVELENGTH":
      excitations = [b.split("\t")[1] for b in self._wavelength_blocks] or ["0"]
      self._wavelength_blocks = [
        f"L:\t{excitations[i % len(excitations)]}\t{w}" for i, w in enumerate(words)
      ]
    elif base == "!CLEAR" and words == ["DATA"]:
      self._columns, self._rows, self._wavelength_blocks, self._transfers = 1, 1, [], 0
    elif base == "!STATUS":
      return "0 IDLE 0 0"
    elif base == "!TEMP" and not words:
      return "37.0 36.8"
    elif base == "!ERROR":
      return "201 0 0"
    elif base == "!OPTION":
      return "M5 2.13"
    elif base == "!TRANSFER":
      return self._plate_data()
    return None

  async def write(self, data: bytes) -> None:
    """Record `data` and queue the answer to it."""
    command = data.decode().rstrip("\r")
    self.sent.append(data.decode())
    base = command.split(" ")[0]
    if command in self.fail or base in self.fail:
      code = self.fail.get(command, self.fail.get(base))
      self._pending.append(f"FAIL\t{code}>".encode())
      return
    payload = self._payload(command)
    self._pending.append(f"OK>{payload or ''}>".encode())

  async def readline(self) -> bytes:
    """The answer to the last command written."""
    if not self._pending:
      raise AssertionError(f"read with no answer pending, after {self.sent[-1:]}")
    return self._pending.pop(0)


class Recorder(recording.Recorder):
  """Records what each step sent and returned, or that it raised the error it was meant to."""

  def failed(self, entry: Dict[str, Any], error: BaseException) -> None:
    entry["raised"] = recording.described(error)

  async def step(  # type: ignore[override]
    self, call: str, action: Awaitable[Any], error: Optional[Type[BaseException]] = None
  ) -> Any:
    """Run `action` and record what was sent and what it returned, or, when `error` is given,
    that it raised that error. Reads change no resources, so a step records none."""
    self.catches = () if error is None else (error,)
    result = await super().step(call, action)
    if error is not None and "raised" not in self.steps[-1]:
      raise AssertionError(f"{error.__name__} not raised by {call}")
    return result


class SpectraMaxGoldenTests(unittest.IsolatedAsyncioTestCase):
  """Scenarios through the readers' public API, each checked against its golden file."""

  async def asyncSetUp(self) -> None:
    self.recorder = Recorder()
    self.port = FakeSpectraMaxPort(self.recorder.sent)
    self.before: List[Dict[str, Any]] = []
    self.store = ResourceStore.in_memory()
    self.tray: Optional[handles.Resource] = None

  async def asyncTearDown(self) -> None:
    await self.store.close()

  async def m5(self) -> SpectraMaxM5:
    """An M5 on the fake port, and its loading tray in the store."""
    reader = SpectraMaxM5(name="m5", port="COM1")
    reader.io = self.port  # type: ignore[assignment]
    self.tray = await self.store.create(loading_tray("m5_loading_tray"), name="m5_loading_tray")
    return reader

  async def plus_384(self) -> SpectraMax384Plus:
    """A 384 Plus on the fake port, and its loading tray in the store."""
    reader = SpectraMax384Plus(name="plus384", port="COM1")
    reader.io = self.port  # type: ignore[assignment]
    self.tray = await self.store.create(
      loading_tray("plus384_loading_tray"), name="plus384_loading_tray"
    )
    return reader

  async def step(
    self,
    call: str,
    action: Awaitable[Any],
    error: Optional[Type[BaseException]] = None,
  ) -> Any:
    return await self.recorder.step(call, action, error)

  async def check(self, scenario: str) -> None:
    """Compare the steps and the resources under the loading tray with the scenario's golden file,
    and fail unless the resources are as they were when the last plate was loaded: reads change
    none."""
    assert self.tray is not None
    resources = await snapshot_store(self.store, self.tray)
    if self.before:
      self.assertEqual(resources, self.before)
    record = {"steps": self.recorder.steps, "resources": resources}
    check_golden(self, GOLDEN / f"{scenario}.json", record)

  async def load(
    self, model: Union[str, pb.ResourceDefinition], name: str, lid: Optional[str] = None
  ) -> handles.Plate:
    """Make a plate on the reader's loading tray, with a lid of the model `lid` when given, and
    remember the tray's resources, so the reads after it can be checked to leave them unchanged."""
    assert self.tray is not None
    plate = await self.store.create(model, name=name, parent=self.tray)
    assert isinstance(plate, handles.Plate)
    if lid is not None:
      await self.store.create(lid, name=f"{name}_lid", parent=plate)
    self.before = await snapshot_store(self.store, self.tray)
    return plate

  async def test_device_operations(self):
    reader = await self.m5()
    await self.step("setup()", reader.setup())
    await self.step("open()", reader.open())
    await self.step("close()", reader.close())
    await self.step("request_status()", reader.request_status())
    await self.step("read_error_log()", reader.read_error_log())
    await self.step("clear_error_log()", reader.clear_error_log())
    await self.step("request_firmware_version()", reader.request_firmware_version())
    await self.step("start_shake()", reader.start_shake())
    await self.step("stop_shake()", reader.stop_shake())
    await self.step("request_temperature()", reader.request_temperature())
    await self.step("request_current_temperature()", reader.request_current_temperature())
    await self.step("set_temperature(37)", reader.set_temperature(37))
    await self.step("set_temperature(50)", reader.set_temperature(50), error=ValueError)
    await self.step("deactivate()", reader.deactivate())
    await self.step("wait_for_idle()", reader.wait_for_idle())
    await self.step("stop()", reader.stop())
    await self.check("device_operations")

  async def test_absorbance_96_with_lid(self):
    reader = await self.m5()
    plate = await self.load(
      "cor_96_wellplate_360uL_Fb", "plate", lid="cor_96_wellplate_360uL_Fb_lid"
    )
    # The wells passed are a subset; the read covers the whole plate.
    await self.step(
      "read_absorbance(plate, plate['A1:H1'], wavelength=450, wavelengths=[450, (600, True)])",
      reader.read_absorbance(
        plate, plate.get_wells("A1:H1"), wavelength=450, wavelengths=[450, (600, True)]
      ),
    )
    await self.check("absorbance_96_with_lid")

  async def test_absorbance_384_plus_path_check_and_spectrum(self):
    reader = await self.plus_384()
    plate = await self.load("Greiner_384_wellplate_28ul_Fb", "plate")
    await self.step(
      "read_absorbance(plate, wells, wavelength=260, path_check=True, speed_read=True,"
      " calibrate='on', carriage_speed='slow', read_order='wavelength')",
      reader.read_absorbance(
        plate,
        plate.get_wells(plate.identifiers),
        wavelength=260,
        path_check=True,
        speed_read=True,
        calibrate="on",
        carriage_speed="slow",
        read_order="wavelength",
      ),
    )
    await self.step(
      "read_absorbance(plate, wells, wavelength=230, read_type='spectrum',"
      " spectrum_settings=SpectrumSettings(230, 10, 3))",
      reader.read_absorbance(
        plate,
        plate.get_wells(plate.identifiers),
        wavelength=230,
        read_type="spectrum",
        spectrum_settings=SpectrumSettings(start_wavelength=230, step=10, num_steps=3),
      ),
    )
    await self.check("absorbance_384_plus")

  async def test_absorbance_24_kinetic_with_shaking(self):
    reader = await self.m5()
    plate = await self.load("cor_cos_24_wellplate_3470uL_Fb", "plate")
    await self.step(
      "read_absorbance(plate, wells, wavelength=600, read_type='kinetic',"
      " kinetic_settings=KineticSettings(30, 2), shake_settings=ShakeSettings(True, 5, True, 10),"
      " settling_time=200)",
      reader.read_absorbance(
        plate,
        plate.get_wells(plate.identifiers),
        wavelength=600,
        read_type="kinetic",
        kinetic_settings=KineticSettings(interval=30, num_readings=2),
        shake_settings=ShakeSettings(
          before_read=True, before_read_duration=5, between_reads=True, between_reads_duration=10
        ),
        settling_time=200,
      ),
    )
    await self.check("absorbance_24_kinetic")

  async def test_fluorescence_6_and_96(self):
    reader = await self.m5()
    plate6 = await self.load("cor_cos_6_wellplate_16800uL_Fb", "plate6")
    await self.step(
      "read_fluorescence(plate6, wells, excitation_wavelength=485, emission_wavelength=520,"
      " focal_height=5)",
      reader.read_fluorescence(
        plate6,
        plate6.get_wells(plate6.identifiers),
        excitation_wavelength=485,
        emission_wavelength=520,
        focal_height=5,
      ),
    )
    assert self.tray is not None
    self.assertEqual(await snapshot_store(self.store, self.tray), self.before)
    await self.tray.unassign_child_resource(plate6)
    plate96 = await self.load("cor_96_wellplate_360uL_Fb", "plate96")
    await self.step(
      "read_fluorescence(plate96, wells, excitation_wavelength=530, emission_wavelength=560,"
      " focal_height=5, cutoff_filters=[9], read_from_bottom=True, pmt_gain='high',"
      " read_type='spectrum', spectrum_settings=SpectrumSettings(550, 10, 2, 'EMSPECTRUM'))",
      reader.read_fluorescence(
        plate96,
        plate96.get_wells(plate96.identifiers),
        excitation_wavelength=530,
        emission_wavelength=560,
        focal_height=5,
        cutoff_filters=[9],
        read_from_bottom=True,
        pmt_gain="high",
        read_type="spectrum",
        spectrum_settings=SpectrumSettings(
          start_wavelength=550, step=10, num_steps=2, excitation_emission_type="EMSPECTRUM"
        ),
      ),
    )
    await self.check("fluorescence_6_and_96")

  async def test_luminescence_384(self):
    reader = await self.m5()
    plate = await self.load("Greiner_384_wellplate_28ul_Fb", "plate")
    await self.step(
      "read_luminescence(plate, wells, focal_height=5, emission_wavelengths=[590], pmt_gain=800)",
      reader.read_luminescence(
        plate,
        plate.get_wells(plate.identifiers),
        focal_height=5,
        emission_wavelengths=[590],
        pmt_gain=800,
      ),
    )
    await self.step(
      "read_luminescence(plate, wells, focal_height=5)",
      reader.read_luminescence(plate, plate.get_wells(plate.identifiers), focal_height=5),
      error=ValueError,
    )
    await self.check("luminescence_384")

  async def test_polarization_and_time_resolved_96(self):
    reader = await self.m5()
    plate = await self.load("cor_96_wellplate_360uL_Fb", "plate")
    await self.step(
      "read_fluorescence_polarization(plate, [485], [535], [7])",
      reader.read_fluorescence_polarization(plate, [485], [535], [7]),
    )
    await self.step(
      "read_time_resolved_fluorescence(plate, [340], [615], [13], delay_time=50,"
      " integration_time=400, read_type='kinetic', kinetic_settings=KineticSettings(60, 2))",
      reader.read_time_resolved_fluorescence(
        plate,
        [340],
        [615],
        [13],
        delay_time=50,
        integration_time=400,
        read_type="kinetic",
        kinetic_settings=KineticSettings(interval=60, num_readings=2),
      ),
    )
    await self.check("polarization_and_time_resolved_96")

  async def test_refused_and_failing_reads(self):
    reader = await self.m5()
    # A one-column plate: refused after !CLEAR DATA, before any position is sent.
    strip = await self.load(strip_plate("strip"), "strip")
    await self.step(
      "read_absorbance(strip, wells, wavelength=450)",
      reader.read_absorbance(strip, strip.get_wells(strip.identifiers), wavelength=450),
      error=ValueError,
    )
    assert self.tray is not None
    await self.tray.unassign_child_resource(strip)
    plate = await self.load("cor_96_wellplate_360uL_Fb", "plate")
    # The reader refuses !READ: the read stops there, nothing transferred.
    self.port.fail = {"!READ": 106}
    await self.step(
      "read_absorbance(plate, wells, wavelength=450)  # !READ fails",
      reader.read_absorbance(plate, plate.get_wells(plate.identifiers), wavelength=450),
      error=SpectraMaxError,
    )
    self.port.fail = {}
    await self.step(
      "read_absorbance(plate, wells, wavelength=450, cuvette=True)",
      reader.read_absorbance(
        plate, plate.get_wells(plate.identifiers), wavelength=450, cuvette=True
      ),
    )
    await self.check("refused_and_failing_reads")


if __name__ == "__main__":
  unittest.main()
