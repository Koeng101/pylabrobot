"""Golden records of what the Inheco SCILA does today: SiLA commands and its drawer tree.

The seam is the SiLA interface's `send_command(command, **parameters)`: every command is recorded
in order with its parameters. The fake answers like the device: drawers open and close as
commanded, and temperature reads give back what was set.
"""

from __future__ import annotations

import pathlib
import unittest
import xml.etree.ElementTree as ET
from typing import Any, Awaitable, Callable, Dict, List, Optional
from unittest.mock import patch

from pylabrobot.inheco.scila import SCILA
from pylabrobot.resources import Plate
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent


def _parameters(values: Dict[str, str]) -> ET.Element:
  """A SiLA response element holding `values` as string parameters."""
  body = "".join(
    f"<Parameter name='{name}'><String>{value}</String></Parameter>"
    for name, value in values.items()
  )
  return ET.fromstring(f"<Response>{body}</Response>")


class _FakeSiLA:
  """Stands in for `InhecoSiLAInterface`: records commands and answers like a SCILA."""

  def __init__(self, client_ip: Optional[str] = None, machine_ip: str = ""):
    self.client_ip = client_ip or "192.168.0.10"
    self.machine_ip = machine_ip
    self.bound_port = 8081
    self.sent: List[Dict[str, Any]] = []
    self.drawers: Dict[int, str] = {1: "Closed", 2: "Closed", 3: "Closed", 4: "Closed"}
    self.prepared: Optional[int] = None
    self.target = 37.0
    self.control = False
    self.errors: Dict[str, str] = {}

  async def setup(self) -> None:
    self.sent.append({"call": "setup"})

  async def close(self) -> None:
    self.sent.append({"call": "close"})

  async def send_command(self, command: str, **parameters: Any) -> Any:
    self.sent.append({"command": command, "parameters": parameters})
    if command in self.errors:
      raise RuntimeError(self.errors.pop(command))
    if command in ("PrepareForInput", "PrepareForOutput"):
      self.prepared = parameters["position"]
    elif command == "OpenDoor" and self.prepared is not None:
      self.drawers[self.prepared] = "Opened"
    elif command == "CloseDoor" and self.prepared is not None:
      self.drawers[self.prepared] = "Closed"
    elif command == "GetStatus":
      return {"GetStatusResponse": {"state": "standBy"}}
    elif command == "GetDoorStatus":
      return _parameters({f"Drawer{i}": state for i, state in self.drawers.items()})
    elif command == "GetLiquidLevel":
      return _parameters({"LiquidLevel": "Ok"})
    elif command == "GetCO2FlowStatus":
      return _parameters({"CO2FlowStatus": "Ok"})
    elif command == "GetValveStatus":
      return _parameters({"H2O": "Closed", "CO2 Normal": "Opened", "CO2 Boost": "Closed"})
    elif command == "SetTemperature":
      self.control = parameters["temperatureControl"]
      self.target = parameters.get("targetTemperature", self.target)
    elif command == "GetTemperature":
      return ET.fromstring(
        "<Response>"
        "<Parameter name='CurrentTemperature'><Float64>36.5</Float64></Parameter>"
        f"<Parameter name='TargetTemperature'><Float64>{self.target}</Float64></Parameter>"
        "<Parameter name='TemperatureControl'><Boolean>"
        f"{'true' if self.control else 'false'}</Boolean></Parameter>"
        "</Response>"
      )
    return None


class _Recorder:
  """A SCILA on the fake SiLA interface, recording each step's commands and resources."""

  def __init__(self, gas_mixer_connected: bool = True):
    self.sila = _FakeSiLA()
    self.transport: Dict[str, Optional[str]] = {}
    with patch("pylabrobot.inheco.scila.scila.InhecoSiLAInterface") as interface:
      interface.side_effect = lambda client_ip, machine_ip: self._made(client_ip, machine_ip)
      self.scila = SCILA(
        name="scila",
        scila_ip="169.254.1.117",
        client_ip="169.254.1.2",
        gas_mixer_connected=gas_mixer_connected,
      )
    self.steps: List[Dict[str, Any]] = []
    self.initial = snapshot_resources(self.scila)

  def _made(self, client_ip: Optional[str], machine_ip: str) -> _FakeSiLA:
    self.transport = {"client_ip": client_ip, "machine_ip": machine_ip}
    self.sila.client_ip = client_ip or self.sila.client_ip
    self.sila.machine_ip = machine_ip
    return self.sila

  async def step(self, call: str, action: Callable[[], Awaitable[Any]]) -> Any:
    """Run one call and record what it sent, returned and changed."""
    self.sila.sent = []
    before = snapshot_resources(self.scila)
    record: Dict[str, Any] = {"call": call}
    result: Any = None
    try:
      result = await action()
      record["result"] = result
    except Exception as error:
      record["result"] = {"error": type(error).__name__, "message": str(error)}
    record["sent"] = self.sila.sent
    after = snapshot_resources(self.scila)
    if after != before:
      record["resources"] = after
    self.steps.append(record)
    return result

  def record(self) -> Dict[str, Any]:
    return {
      "transport": self.transport,
      "initial_resources": self.initial,
      "steps": self.steps,
      "resources": snapshot_resources(self.scila),
    }


def _plate(name: str) -> Plate:
  return Plate(name, size_x=127.76, size_y=85.48, size_z=14.2, ordered_items={})


class SCILAGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_setup_and_drawers(self):
    """Set up; open drawer 2, put a plate in it by hand and close it; read the drawers."""
    recorder = _Recorder()
    scila = recorder.scila
    plate = _plate("culture_plate")

    async def place_plate() -> None:
      scila.drawers[2].assign_child_resource(plate)

    await recorder.step("setup()", scila.setup)
    await recorder.step("request_status()", scila.request_status)
    await recorder.step("drawers[2].open()", scila.drawers[2].open)
    await recorder.step("request_drawer_statuses()", scila.request_drawer_statuses)
    await recorder.step("drawers[2].assign_child_resource(plate) by hand", place_plate)
    await recorder.step("drawers[2].close()", scila.drawers[2].close)
    await recorder.step("request_drawer_status(2)", lambda: scila.request_drawer_status(2))
    await recorder.step("request_drawer_status(5)", lambda: scila.request_drawer_status(5))
    await recorder.step("stop()", scila.stop)

    check_golden(self, GOLDEN / "setup_and_drawers.json", recorder.record())

  async def test_temperature_and_status(self):
    """Temperature control on and off, and the status reads."""
    recorder = _Recorder()
    scila = recorder.scila

    await recorder.step("set_temperature(37.0)", lambda: scila.set_temperature(37.0))
    await recorder.step("request_temperature_information()", scila.request_temperature_information)
    await recorder.step("request_current_temperature()", scila.request_current_temperature)
    await recorder.step("request_target_temperature()", scila.request_target_temperature)
    await recorder.step("is_temperature_control_enabled()", scila.is_temperature_control_enabled)
    await recorder.step("deactivate()", scila.deactivate)
    await recorder.step("is_temperature_control_enabled()", scila.is_temperature_control_enabled)
    await recorder.step("request_liquid_level()", scila.request_liquid_level)
    await recorder.step("request_co2_flow_status()", scila.request_co2_flow_status)
    await recorder.step("request_valve_status()", scila.request_valve_status)

    check_golden(self, GOLDEN / "temperature_and_status.json", recorder.record())

  async def test_drawer_warnings(self):
    """A CO2-flow warning on a door command does not fail it, with or without a gas mixer; any
    other door error does."""
    recorder = _Recorder(gas_mixer_connected=True)
    scila = recorder.scila
    warning = "command OpenDoor failed with code 2: 'Warning: CO2 flow NOK'"

    recorder.sila.errors["OpenDoor"] = warning
    await recorder.step("drawers[1].open() with a CO2 warning", scila.drawers[1].open)
    scila.gas_mixer_connected = False
    recorder.sila.errors["CloseDoor"] = warning.replace("OpenDoor", "CloseDoor")
    await recorder.step(
      "drawers[1].close() with a CO2 warning, no gas mixer", scila.drawers[1].close
    )
    recorder.sila.errors["OpenDoor"] = "command OpenDoor failed with code 4: 'Door obstructed'"
    await recorder.step("drawers[3].open() obstructed", scila.drawers[3].open)
    await recorder.step("request_drawer_statuses()", scila.request_drawer_statuses)

    check_golden(self, GOLDEN / "drawer_warnings.json", recorder.record())


if __name__ == "__main__":
  unittest.main()
