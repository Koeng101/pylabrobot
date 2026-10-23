"""Golden tests of what the Inheco ThermoShake and CPAC do today.

The seam is the TEC control box's HID transport: `box.io` is replaced by a fake that records every
call made on it, in order (reports as hex), and answers each command with the control box's
modified echo. Waits (`asyncio.sleep`) are recorded rather than slept, and the control box's
clock (`time.time`) advances by a quarter second each time it is read, so a reply that never comes
times out at once.
"""

from __future__ import annotations

import asyncio
import pathlib
import types
import unittest
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from unittest import mock

from pylabrobot.inheco import (
  InhecoCPAC,
  InhecoTECControlBox,
  InhecoThermoShake,
  inheco_cpac_ultraflat,
  inheco_thermoshake,
  inheco_thermoshake_ac,
  inheco_thermoshake_rm,
)
from pylabrobot.inheco import control_box as control_box_module
from pylabrobot.inheco import thermoshake as thermoshake_module
from pylabrobot.resources import (
  Eppendorf_96_wellplate_250ul_Vb,
  Resource,
  cor_96_wellplate_360uL_Fb,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent

# What the control box answers (after the echo and error status) to each command, by the
# command's first four characters with the index removed; any other command answers nothing.
ANSWERS: Dict[str, str] = {
  "RAT": "370",
  "RFV": "SN-0042",
}


class FakeHID:
  """A HID transport that records every call and answers each command with its echo."""

  def __init__(self, record: "Recorder"):
    self.record = record
    self.answers = dict(ANSWERS)
    self.error_status = "0"
    self.written = ""
    self.pending: List[bytes] = []

  async def setup(self) -> None:
    self.record.sent.append("setup")

  async def stop(self) -> None:
    self.record.sent.append("stop")

  async def write(self, data: bytes, report_id: bytes = b"\x00") -> None:
    self.record.sent.append(f"write report_id={report_id.hex()} data={data.hex()}")
    text = data.rstrip(b"\x00#").decode("latin1")
    self.written += text
    if data.endswith(b"#"):
      return
    command = self.written[:-1]  # the last character is the checksum
    self.written = ""
    payload = self.answers.get(command[1:4], "")
    reply = command[:4].lower() + self.error_status + payload + "c"
    self.pending.append(reply.encode("latin1") + b"\x00")

  async def read(self, size: int, timeout: int = 0) -> bytes:
    del size, timeout
    return self.pending.pop(0) if self.pending else b""


class Recorder:
  """Records what the control box was sent, step by step, with the device's resource tree."""

  def __init__(self) -> None:
    self.sent: List[str] = []
    self.waits: List[float] = []
    self.steps: List[Dict[str, Any]] = []
    self.box = InhecoTECControlBox()
    self.hid = FakeHID(self)
    self.box.io = self.hid  # type: ignore[assignment]
    self.root: Optional[Resource] = None
    self.real_sleep = asyncio.sleep
    self.now = 0.0

  def _time(self) -> float:
    self.now += 0.25
    return self.now

  async def _sleep(self, delay: float, result: Any = None) -> Any:
    self.waits.append(delay)
    await self.real_sleep(0)
    return result

  async def step(
    self,
    call: str,
    action: Callable[[], Union[Awaitable[Any], Any]],
    resources: bool = False,
  ) -> None:
    """Run one step, recording what was sent, waited, returned or raised."""
    self.sent, self.waits = [], []
    entry: Dict[str, Any] = {"call": call}
    try:
      with (
        mock.patch.object(thermoshake_module.asyncio, "sleep", self._sleep),
        mock.patch.object(control_box_module, "time", types.SimpleNamespace(time=self._time)),
      ):
        result = action()
        if asyncio.iscoroutine(result):
          result = await result
      entry["result"] = result
    except Exception as error:
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = self.sent
    if self.waits:
      entry["waits"] = self.waits
    if resources:
      assert self.root is not None
      entry["resources"] = snapshot_resources(self.root)
    self.steps.append(entry)

  def finish(self) -> Dict[str, Any]:
    assert self.root is not None
    return {"steps": self.steps, "resources": snapshot_resources(self.root)}


def describe(device: Union[InhecoThermoShake, InhecoCPAC]) -> Dict[str, Any]:
  """A holder's model, size, child location, index and tree."""
  return {
    "model": device.model,
    "category": device.category,
    "size": [device.get_size_x(), device.get_size_y(), device.get_size_z()],
    "child_location": [device.child_location.x, device.child_location.y, device.child_location.z],
    "index": device.index,
    "supports_active_cooling": device.supports_active_cooling,
    "resources": snapshot_resources(device),
  }


class InhecoGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_factories(self):
    """Each factory's holder, the factories without a child location, and refused indices."""
    box = InhecoTECControlBox()
    record: Dict[str, Any] = {
      "inheco_thermoshake": describe(inheco_thermoshake("thermoshake", control_box=box, index=1)),
      "inheco_cpac_ultraflat": describe(inheco_cpac_ultraflat("cpac", control_box=box, index=6)),
    }
    for factory in (inheco_thermoshake_ac, inheco_thermoshake_rm):
      try:
        factory("thermoshake", box, 1)
        record[factory.__name__] = "built"
      except NotImplementedError as error:
        record[factory.__name__] = f"NotImplementedError: {error}"
    for index in (0, 7):
      try:
        inheco_cpac_ultraflat("cpac", control_box=box, index=index)
        record[f"index {index}"] = "built"
      except ValueError as error:
        record[f"index {index}"] = f"ValueError: {error}"
    check_golden(self, GOLDEN / "factories.json", record)

  async def test_plates_on_the_thermoshake(self):
    """The ThermoShake holds any plate at its child location, one at a time."""
    rig = Recorder()
    thermoshake = inheco_thermoshake("thermoshake", control_box=rig.box, index=1)
    rig.root = thermoshake
    plate = cor_96_wellplate_360uL_Fb("plate")
    pcr = Eppendorf_96_wellplate_250ul_Vb("pcr_plate")

    await rig.step(
      "thermoshake.assign_child_resource(pcr_plate)",
      lambda: thermoshake.assign_child_resource(pcr),
      resources=True,
    )
    await rig.step(
      "thermoshake.assign_child_resource(plate, reassign=False)",
      lambda: thermoshake.assign_child_resource(plate, reassign=False),
      resources=True,
    )
    await rig.step(
      "thermoshake.unassign_child_resource(pcr_plate)",
      lambda: thermoshake.unassign_child_resource(pcr),
      resources=True,
    )
    await rig.step(
      "thermoshake.assign_child_resource(plate)",
      lambda: thermoshake.assign_child_resource(plate),
      resources=True,
    )
    check_golden(self, GOLDEN / "plates_on_the_thermoshake.json", rig.finish())

  async def test_thermoshake_heating_and_shaking(self):
    """Heat a plate, shake it in each way, read the temperature and stop."""
    rig = Recorder()
    thermoshake = inheco_thermoshake("thermoshake", control_box=rig.box, index=2)
    rig.root = thermoshake
    thermoshake.assign_child_resource(cor_96_wellplate_360uL_Fb("plate"))

    await rig.step("box.setup()", lambda: rig.box.setup())
    await rig.step("set_temperature(37)", lambda: thermoshake.set_temperature(37))
    await rig.step("set_temperature(37.55)", lambda: thermoshake.set_temperature(37.55))
    await rig.step(
      "request_current_temperature()", lambda: thermoshake.request_current_temperature()
    )
    await rig.step(
      "start_shaking(speed=500, shape=1)", lambda: thermoshake.start_shaking(speed=500, shape=1)
    )
    await rig.step("stop_shaking()", lambda: thermoshake.stop_shaking())
    await rig.step("shake(speed=1000, duration=30)", lambda: thermoshake.shake(1000, 30))
    await rig.step("start_shaking(speed=3000)", lambda: thermoshake.start_shaking(speed=3000))
    await rig.step("set_shaker_shape(6)", lambda: thermoshake.set_shaker_shape(6))
    await rig.step("request_device_info(2)", lambda: thermoshake.request_device_info(2))
    await rig.step("request_device_info(5)", lambda: thermoshake.request_device_info(5))
    await rig.step("stop_temperature_control()", lambda: thermoshake.stop_temperature_control())
    await rig.step("box.set_touchscreen(False)", lambda: rig.box.set_touchscreen(False))
    rig.hid.error_status = "4"
    await rig.step("stop_shaking()  # device error", lambda: thermoshake.stop_shaking())
    rig.hid.error_status = "0"
    await rig.step("box.stop()", lambda: rig.box.stop())
    check_golden(self, GOLDEN / "thermoshake_heating_and_shaking.json", rig.finish())

  async def test_cpac_cooling_a_plate(self):
    """A plate on the CPAC, cooled, read and released."""
    rig = Recorder()
    cpac = inheco_cpac_ultraflat("cpac", control_box=rig.box, index=1)
    rig.root = cpac
    plate = Eppendorf_96_wellplate_250ul_Vb("pcr_plate")

    await rig.step("box.setup()", lambda: rig.box.setup())
    await rig.step(
      "cpac.assign_child_resource(pcr_plate)",
      lambda: cpac.assign_child_resource(plate),
      resources=True,
    )
    await rig.step("set_temperature(4)", lambda: cpac.set_temperature(4))
    await rig.step("request_current_temperature()", lambda: cpac.request_current_temperature())
    await rig.step("request_device_info(1)", lambda: cpac.request_device_info(1))
    await rig.step("stop_temperature_control()", lambda: cpac.stop_temperature_control())
    await rig.step(
      "cpac.unassign_child_resource(pcr_plate)",
      lambda: cpac.unassign_child_resource(plate),
      resources=True,
    )
    await rig.step("box.stop()", lambda: rig.box.stop())
    check_golden(self, GOLDEN / "cpac_cooling_a_plate.json", rig.finish())


if __name__ == "__main__":
  unittest.main()
