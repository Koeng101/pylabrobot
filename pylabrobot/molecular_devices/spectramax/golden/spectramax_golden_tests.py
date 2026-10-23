"""Golden tests of what the SpectraMax M5 and 384 Plus send today, for plates of several shapes.

The seam is the serial port: a fake records every command written, in order, exactly as written,
and answers each with ``OK>`` and, for the commands that return data, a payload. Its plate data is shaped by the ``!XPOS`` / ``!YPOS`` the reader was sent, so a read's
result grid follows the plate's geometry as the device was told it.
"""

from __future__ import annotations

import dataclasses
import pathlib
import unittest
from typing import Any, Awaitable, Dict, List, Optional, Type

from pylabrobot.molecular_devices.spectramax import (
  KineticSettings,
  MolecularDevicesPlateReader,
  ShakeSettings,
  SpectraMax384Plus,
  SpectraMaxError,
  SpectraMaxM5,
  SpectrumSettings,
)
from pylabrobot.resources import (
  Greiner_384_wellplate_28ul_Fb,
  Plate,
  Well,
  cor_96_wellplate_360uL_Fb,
  cor_cos_6_wellplate_16800uL_Fb,
  cor_cos_24_wellplate_3470uL_Fb,
  create_ordered_items_2d,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent


class FakeSpectraMaxPort:
  """A serial port that records what is written and answers like a SpectraMax.

  Every command is answered with two fields in one line, ``OK><payload>>``, so a command the
  reader expects one or two fields for is answered either way. The payload is empty but for
  ``!STATUS``, ``!TEMP``, ``!ERROR``, ``!OPTION`` and ``!TRANSFER``. A command listed in `fail`
  is answered ``FAIL\\t<code>>`` instead.
  """

  def __init__(self) -> None:
    self.sent: List[str] = []
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


def _jsonable(result: Any) -> Any:
  if isinstance(result, list):
    return [_jsonable(item) for item in result]
  if dataclasses.is_dataclass(result) and not isinstance(result, type):
    return dataclasses.asdict(result)
  return result


class SpectraMaxGoldenTests(unittest.IsolatedAsyncioTestCase):
  """Scenarios through the readers' public API, each checked against its golden file."""

  async def asyncSetUp(self) -> None:
    self.port = FakeSpectraMaxPort()
    self.steps: List[Dict[str, Any]] = []
    self.before: List[Dict[str, Any]] = []

  def m5(self) -> SpectraMaxM5:
    """An M5 on the fake port."""
    reader = SpectraMaxM5(name="m5", port="COM1")
    reader.io = self.port  # type: ignore[assignment]
    return reader

  def plus_384(self) -> SpectraMax384Plus:
    """A 384 Plus on the fake port."""
    reader = SpectraMax384Plus(name="plus384", port="COM1")
    reader.io = self.port  # type: ignore[assignment]
    return reader

  async def step(
    self,
    call: str,
    action: Awaitable[Any],
    error: Optional[Type[BaseException]] = None,
  ) -> Any:
    """Run `action` and record what was sent and what it returned, or, when `error` is given,
    that it raised that error. Reads change no resources, so a step records none."""
    start = len(self.port.sent)
    entry: Dict[str, Any] = {"call": call}
    result: Any = None
    if error is None:
      result = await action
      entry["result"] = _jsonable(result)
    else:
      with self.assertRaises(error) as raised:
        await action
      entry["raised"] = f"{type(raised.exception).__name__}: {raised.exception}"
    entry["sent"] = self.port.sent[start:]
    self.steps.append(entry)
    return result

  def check(self, scenario: str, root: Any) -> None:
    """Compare the steps and the resources under `root` with the scenario's golden file, and fail
    unless the resources are as they were when the last plate was loaded: reads change none."""
    resources = snapshot_resources(root)
    if self.before:
      self.assertEqual(resources, self.before)
    record = {"steps": self.steps, "resources": resources}
    check_golden(self, GOLDEN / f"{scenario}.json", record)

  def load(self, reader: MolecularDevicesPlateReader, plate: Plate) -> Plate:
    """Put `plate` on the reader's loading tray and remember the tray's resources, so the reads
    after it can be checked to leave them unchanged."""
    assert isinstance(reader, (SpectraMaxM5, SpectraMax384Plus))
    reader.loading_tray.assign_child_resource(plate)
    self.before = snapshot_resources(reader.loading_tray)
    return plate

  async def test_device_operations(self):
    reader = self.m5()
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
    self.check("device_operations", reader.loading_tray)

  async def test_absorbance_96_with_lid(self):
    reader = self.m5()
    plate = self.load(reader, cor_96_wellplate_360uL_Fb("plate", with_lid=True))
    # The wells passed are a subset; the read covers the whole plate.
    await self.step(
      "read_absorbance(plate, plate['A1:H1'], wavelength=450, wavelengths=[450, (600, True)])",
      reader.read_absorbance(plate, plate["A1:H1"], wavelength=450, wavelengths=[450, (600, True)]),
    )
    self.check("absorbance_96_with_lid", reader.loading_tray)

  async def test_absorbance_384_plus_path_check_and_spectrum(self):
    reader = self.plus_384()
    plate = self.load(reader, Greiner_384_wellplate_28ul_Fb("plate"))
    await self.step(
      "read_absorbance(plate, wells, wavelength=260, path_check=True, speed_read=True,"
      " calibrate='on', carriage_speed='slow', read_order='wavelength')",
      reader.read_absorbance(
        plate,
        plate.get_all_items(),
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
        plate.get_all_items(),
        wavelength=230,
        read_type="spectrum",
        spectrum_settings=SpectrumSettings(start_wavelength=230, step=10, num_steps=3),
      ),
    )
    self.check("absorbance_384_plus", reader.loading_tray)

  async def test_absorbance_24_kinetic_with_shaking(self):
    reader = self.m5()
    plate = self.load(reader, cor_cos_24_wellplate_3470uL_Fb("plate"))
    await self.step(
      "read_absorbance(plate, wells, wavelength=600, read_type='kinetic',"
      " kinetic_settings=KineticSettings(30, 2), shake_settings=ShakeSettings(True, 5, True, 10),"
      " settling_time=200)",
      reader.read_absorbance(
        plate,
        plate.get_all_items(),
        wavelength=600,
        read_type="kinetic",
        kinetic_settings=KineticSettings(interval=30, num_readings=2),
        shake_settings=ShakeSettings(
          before_read=True, before_read_duration=5, between_reads=True, between_reads_duration=10
        ),
        settling_time=200,
      ),
    )
    self.check("absorbance_24_kinetic", reader.loading_tray)

  async def test_fluorescence_6_and_96(self):
    reader = self.m5()
    plate6 = self.load(reader, cor_cos_6_wellplate_16800uL_Fb("plate6"))
    await self.step(
      "read_fluorescence(plate6, wells, excitation_wavelength=485, emission_wavelength=520,"
      " focal_height=5)",
      reader.read_fluorescence(
        plate6,
        plate6.get_all_items(),
        excitation_wavelength=485,
        emission_wavelength=520,
        focal_height=5,
      ),
    )
    self.assertEqual(snapshot_resources(reader.loading_tray), self.before)
    reader.loading_tray.unassign_child_resource(plate6)
    plate96 = self.load(reader, cor_96_wellplate_360uL_Fb("plate96"))
    await self.step(
      "read_fluorescence(plate96, wells, excitation_wavelength=530, emission_wavelength=560,"
      " focal_height=5, cutoff_filters=[9], read_from_bottom=True, pmt_gain='high',"
      " read_type='spectrum', spectrum_settings=SpectrumSettings(550, 10, 2, 'EMSPECTRUM'))",
      reader.read_fluorescence(
        plate96,
        plate96.get_all_items(),
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
    self.check("fluorescence_6_and_96", reader.loading_tray)

  async def test_luminescence_384(self):
    reader = self.m5()
    plate = self.load(reader, Greiner_384_wellplate_28ul_Fb("plate"))
    await self.step(
      "read_luminescence(plate, wells, focal_height=5, emission_wavelengths=[590], pmt_gain=800)",
      reader.read_luminescence(
        plate, plate.get_all_items(), focal_height=5, emission_wavelengths=[590], pmt_gain=800
      ),
    )
    await self.step(
      "read_luminescence(plate, wells, focal_height=5)",
      reader.read_luminescence(plate, plate.get_all_items(), focal_height=5),
      error=ValueError,
    )
    self.check("luminescence_384", reader.loading_tray)

  async def test_polarization_and_time_resolved_96(self):
    reader = self.m5()
    plate = self.load(reader, cor_96_wellplate_360uL_Fb("plate"))
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
    self.check("polarization_and_time_resolved_96", reader.loading_tray)

  async def test_refused_and_failing_reads(self):
    reader = self.m5()
    # A one-column plate: refused after !CLEAR DATA, before any position is sent.
    strip = Plate(
      name="strip",
      size_x=127.76,
      size_y=85.48,
      size_z=14.2,
      ordered_items=create_ordered_items_2d(
        Well,
        num_items_x=1,
        num_items_y=8,
        dx=10,
        dy=7,
        dz=1,
        item_dx=9,
        item_dy=9,
        size_x=6,
        size_y=6,
        size_z=10,
      ),
    )
    self.load(reader, strip)
    await self.step(
      "read_absorbance(strip, wells, wavelength=450)",
      reader.read_absorbance(strip, strip.get_all_items(), wavelength=450),
      error=ValueError,
    )
    reader.loading_tray.unassign_child_resource(strip)
    plate = self.load(reader, cor_96_wellplate_360uL_Fb("plate"))
    # The reader refuses !READ: the read stops there, nothing transferred.
    self.port.fail = {"!READ": 106}
    await self.step(
      "read_absorbance(plate, wells, wavelength=450)  # !READ fails",
      reader.read_absorbance(plate, plate.get_all_items(), wavelength=450),
      error=SpectraMaxError,
    )
    self.port.fail = {}
    await self.step(
      "read_absorbance(plate, wells, wavelength=450, cuvette=True)",
      reader.read_absorbance(plate, plate.get_all_items(), wavelength=450, cuvette=True),
    )
    self.check("refused_and_failing_reads", reader.loading_tray)


if __name__ == "__main__":
  unittest.main()
