"""Golden tests of what the QInstruments BioShake does today.

The seam is the BioShake's serial transport: `Serial` is replaced by a fake that records every
call made on it, in order, and answers each written command the way the firmware does. Waits
(`asyncio.sleep`) are recorded rather than slept.
"""

from __future__ import annotations

import pathlib
import types
import unittest
from typing import Any, Callable, Dict, List, Optional
from unittest import mock

from pylabrobot.qinstruments import bioshake as bioshake_module
from pylabrobot.qinstruments.bioshake import (
  BioShake,
  BioShake3000,
  BioShake3000Elm,
  BioShake3000ElmDWP,
  BioShake3000T,
  BioShake3000TElm,
  BioShake5000Elm,
  BioShakeD30Elm,
  BioShakeD30TElm,
  BioShakeQ1,
  BioShakeQ2,
  ColdPlate,
  Heatplate,
)
from pylabrobot.resources.store import handles
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

# What the firmware answers to each query; any other command is acknowledged with "ok".
ANSWERS: Dict[str, str] = {
  "getShakeMinRpm": "200",
  "getShakeMaxRpm": "3000",
  "getShakeAccelerationMin": "0",
  "getShakeAccelerationMax": "30",
  "getTempMin": "0",
  "getTempMax": "99",
  "getTempActual": "36.9",
  "resetDevice": "Initialization complete",
}

# pyserial's constants, so the BioShake builds without pyserial installed.
SERIAL_CONSTANTS = types.SimpleNamespace(EIGHTBITS=8, PARITY_NONE="N", STOPBITS_ONE=1)


class FakeSerial:
  """A serial transport that records every call and answers each written command."""

  def __init__(self, record: "Recorder", **settings: Any):
    self.record = record
    record.serial = self
    record.transport = {key: value for key, value in settings.items()}
    self.answers = dict(ANSWERS)
    self.pending: List[bytes] = []

  async def setup(self) -> None:
    self.record.sent.append("setup")

  async def stop(self) -> None:
    self.record.sent.append("stop")

  async def reset_input_buffer(self) -> None:
    self.record.sent.append("reset_input_buffer")

  async def reset_output_buffer(self) -> None:
    self.record.sent.append("reset_output_buffer")

  async def write(self, data: bytes) -> None:
    self.record.sent.append("write " + data.decode("ascii"))
    command = data.decode("ascii").strip()
    self.pending.append((self.answers.get(command, "ok") + "\r\n").encode("ascii"))

  async def readline(self) -> bytes:
    return self.pending.pop(0) if self.pending else b""


class Recorder(recording.Recorder):
  """Records what the BioShake was sent, step by step, with its resource tree."""

  records_waits = True

  def __init__(self) -> None:
    super().__init__()
    self.transport: Dict[str, Any] = {}
    self.device: Optional[BioShake] = None
    self.serial: FakeSerial

  def build(self, factory: Callable[..., BioShake]) -> BioShake:
    """Build a BioShake from `factory` on the fake transport."""

    def make_serial(**settings: Any) -> FakeSerial:
      return FakeSerial(self, **settings)

    with (
      mock.patch.object(bioshake_module, "HAS_SERIAL", True),
      mock.patch.object(bioshake_module, "serial", SERIAL_CONSTANTS, create=True),
      mock.patch.object(bioshake_module, "Serial", make_serial),
    ):
      self.device = factory("bioshake", "/dev/ttyUSB0")
    return self.device

  async def step(  # type: ignore[override]
    self, call: str, action: recording.Action, resources: bool = False
  ) -> Any:
    """Run one step, recording what was sent, waited, returned or raised, and the tree after it
    when `resources`."""
    value = await super().step(call, action)
    if resources:
      self.steps[-1]["resources"] = await self.snapshot()
    return value

  async def snapshot(self) -> List[Dict[str, Any]]:
    assert self.device is not None
    return await snapshot_store(self.device.store, await self.device.create_body())

  async def plate(self, model: str, name: str) -> handles.Plate:
    """A plate in the BioShake's store, in nothing."""
    assert self.device is not None
    plate = await self.device.store.create(model, name=name)
    assert isinstance(plate, handles.Plate)
    return plate

  async def finish(self) -> Dict[str, Any]:
    return {
      "transport": self.transport,
      "steps": self.steps,
      "resources": await self.snapshot(),
    }


class BioShakeGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_factories(self):
    """Each factory's tree, and the factories that have no resource definition."""
    record: Dict[str, Any] = {}
    for factory in (BioShake3000, BioShake3000Elm, BioShake3000ElmDWP, BioShakeQ1):
      rig = Recorder()
      device = rig.build(factory)
      body = await device.create_body()
      attributes = await body.attributes()
      size, holder = attributes.size, attributes.holder
      record[factory.__name__] = {
        "model": attributes.model,
        "category": attributes.category,
        "size": [size.x, size.y, size.z],
        "supports_shaking": device.supports_shaking,
        "supports_locking": device.supports_locking,
        "supports_temperature_control": device.supports_temperature_control,
        "supports_active_cooling": device.supports_active_cooling,
        "pedestal_size_z": holder.pedestal_size_z,
        "child_location": [
          holder.child_location.x,
          holder.child_location.y,
          holder.child_location.z,
        ],
        "transport": rig.transport,
        "resources": await rig.snapshot(),
      }
    for missing in (
      BioShakeD30Elm,
      BioShake5000Elm,
      BioShake3000T,
      BioShake3000TElm,
      BioShakeD30TElm,
      BioShakeQ2,
      Heatplate,
      ColdPlate,
    ):
      try:
        missing("bioshake", "/dev/ttyUSB0")
        record[missing.__name__] = "built"
      except NotImplementedError as error:
        record[missing.__name__] = f"NotImplementedError: {error}"
    check_golden(self, GOLDEN / "factories.json", record)

  async def test_plates_on_the_bioshake(self):
    """A skirted plate is placed at the child location; a non-skirted one is refused."""
    rig = Recorder()
    bioshake = rig.build(BioShake3000Elm)
    plate = await rig.plate("cor_96_wellplate_360uL_Fb", "plate")
    other = await rig.plate("cor_96_wellplate_360uL_Fb", "other_plate")
    pcr = await rig.plate("Eppendorf_96_wellplate_250ul_Vb", "pcr_plate")

    await rig.step(
      "bioshake.assign_child_resource(pcr_plate)",
      lambda: bioshake.assign_child_resource(pcr),
      resources=True,
    )
    await rig.step(
      "bioshake.assign_child_resource(plate)",
      lambda: bioshake.assign_child_resource(plate),
      resources=True,
    )
    await rig.step(
      "bioshake.assign_child_resource(other_plate, reassign=False)",
      lambda: bioshake.assign_child_resource(other, reassign=False),
      resources=True,
    )
    await rig.step(
      "bioshake.unassign_child_resource(plate)",
      lambda: bioshake.unassign_child_resource(plate),
      resources=True,
    )

    await rig.step(
      "bioshake.resource = other_plate", lambda: bioshake.set_resource(other), resources=True
    )
    check_golden(self, GOLDEN / "plates_on_the_bioshake.json", await rig.finish())

  async def test_shaking_with_a_locked_plate(self):
    """Setup homes the shaker; a plate is locked, shaken and released."""
    rig = Recorder()
    bioshake = rig.build(BioShake3000Elm)
    await bioshake.assign_child_resource(await rig.plate("cor_96_wellplate_360uL_Fb", "plate"))

    await rig.step("setup()", lambda: bioshake.setup())
    await rig.step("lock_plate()", lambda: bioshake.lock_plate())
    await rig.step("start_shaking(speed=1000)", lambda: bioshake.start_shaking(speed=1000))
    await rig.step("stop_shaking()", lambda: bioshake.stop_shaking())
    await rig.step(
      "start_shaking(speed=1200.0, acceleration=5)",
      lambda: bioshake.start_shaking(speed=1200.0, acceleration=5),
    )
    await rig.step("stop_shaking(deceleration=3)", lambda: bioshake.stop_shaking(deceleration=3))
    await rig.step("shake(speed=800, duration=10)", lambda: bioshake.shake(speed=800, duration=10))
    await rig.step("unlock_plate()", lambda: bioshake.unlock_plate())
    await rig.step("home()", lambda: bioshake.home())
    await rig.step("stop()", lambda: bioshake.stop())
    check_golden(self, GOLDEN / "shaking_with_a_locked_plate.json", await rig.finish())

  async def test_refused_shaking(self):
    """Out-of-range and malformed speeds, and a firmware error."""
    rig = Recorder()
    bioshake = rig.build(BioShake3000)

    await rig.step("setup(skip_home=True)", lambda: bioshake.setup(skip_home=True))
    await rig.step("start_shaking(speed=5000)", lambda: bioshake.start_shaking(speed=5000))
    await rig.step("start_shaking(speed=1000.5)", lambda: bioshake.start_shaking(speed=1000.5))
    await rig.step(
      "start_shaking(speed=1000, acceleration=60)",
      lambda: bioshake.start_shaking(speed=1000, acceleration=60),
    )
    await rig.step(
      "stop_shaking(deceleration=0.5)", lambda: bioshake.stop_shaking(deceleration=0.5)
    )
    await rig.step("lock_plate()  # no ELM", lambda: bioshake.lock_plate())
    await rig.step("set_temperature(37)  # no heater", lambda: bioshake.set_temperature(37))
    rig.serial.answers["shakeOn"] = "e3"
    await rig.step(
      "start_shaking(speed=1000)  # device error", lambda: bioshake.start_shaking(1000)
    )
    rig.serial.answers["shakeOn"] = "u -> shakeOn"
    await rig.step(
      "start_shaking(speed=1000)  # unsupported", lambda: bioshake.start_shaking(speed=1000)
    )
    check_golden(self, GOLDEN / "refused_shaking.json", await rig.finish())

  async def test_temperature(self):
    """Q1 setup, heating, reading and switching off; out-of-range and sub-tenth targets."""
    rig = Recorder()
    bioshake = rig.build(BioShakeQ1)

    await rig.step("setup()", lambda: bioshake.setup())
    await rig.step("set_temperature(37)", lambda: bioshake.set_temperature(37))
    await rig.step("set_temperature(37.5)", lambda: bioshake.set_temperature(37.5))
    await rig.step("set_temperature(37.55)", lambda: bioshake.set_temperature(37.55))
    await rig.step("set_temperature(120)", lambda: bioshake.set_temperature(120))
    await rig.step("request_current_temperature()", lambda: bioshake.request_current_temperature())
    await rig.step("deactivate()", lambda: bioshake.deactivate())
    check_golden(self, GOLDEN / "temperature.json", await rig.finish())


if __name__ == "__main__":
  unittest.main()
