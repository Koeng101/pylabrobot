"""Recording seam for the HighRes sample-store golden tests.

`SimulatedSocket` extends the line-replaying fake of the driver tests with the nest plate sensors
a real store keeps: a successful `pick` occupies its nest, a `place` clears it and a
`nesttransfer` moves it. A test can script one response for a command (an error, an abort, a
timeout after the acknowledgement) to drive a failure path.

`Recorder` runs each step of a scenario and records, per step, every command written to the
store (plus `<setup>`/`<stop>` for the transport opening and closing), the events emitted on the
PLR event bus, what the call returned or raised, the plate transfer left unresolved, and the
resources under the store's body in its resource store when the step changed them.
"""

from __future__ import annotations

import dataclasses
import pathlib
import unittest
from typing import Any, ContextManager, Dict, List, Optional

from pylabrobot.events import PLREvent
from pylabrobot.high_res.sample_storage.driver import HighResSampleStorage
from pylabrobot.high_res.sample_storage.tests.driver_tests import CAPTURES, FakeSocket
from pylabrobot.resources.store import handles
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN_DIRECTORY = pathlib.Path(__file__).parent

# Two stackers of different slot heights, an empty stacker and a gap in the numbering.
STACKER_DIMENSIONS = [
  "1: 10.000 30.000 3",
  "2: 0.000 20.000 4",
  "3: 0.000 22.867 0",
  "5: 5.000 16.000 2",
]


def _envelope(command: str, command_id: int, data: List[str], completion: str = "OK!") -> List[str]:
  return [f"ACK! {command} {command_id}", *data, f"{completion} {command} {command_id}"]


def _data_lines(command: str) -> List[str]:
  """The data lines of a captured response."""
  return CAPTURES[command][1:-1]


class SimulatedSocket(FakeSocket):
  """A store that answers every command, keeping the nest plate sensors."""

  def __init__(self, stacker_dimensions: Optional[List[str]] = None, nests: int = 2):
    super().__init__(CAPTURES)
    self.stacker_dimensions = (
      list(stacker_dimensions) if stacker_dimensions is not None else STACKER_DIMENSIONS
    )
    self.nest_sensors: Dict[int, str] = {nest: "CLEAR" for nest in range(1, nests + 1)}
    self.spatula = "NO_PLATE"
    self.homed = "homed"
    self.scripted: Dict[str, List[str]] = {}
    self.stall_after_ack: List[str] = []
    self.events: List[str] = []
    self._command_id = 0
    self._stalling = False

  def script(self, command: str, data: List[str], completion: str = "OK!") -> None:
    """Answer the next `command` with `data` and `completion` instead of carrying it out."""
    self._command_id += 1
    self.scripted[command] = _envelope(command, 900 + self._command_id, data, completion)

  async def setup(self):
    await super().setup()
    self.events.append("<setup>")

  async def stop(self):
    await super().stop()
    self.events.append("<stop>")

  def _respond(self, command: str) -> List[str]:
    if command in self.scripted:
      return self.scripted.pop(command)
    self._command_id += 1
    words = command.split()
    data: List[str] = []
    if command in ("version", "environmentstatus", "doorstatus", "status"):
      data = _data_lines(command)
    elif command == "getstackerdimensions":
      data = list(self.stacker_dimensions)
    elif command == "neststatus":
      data = [f"{nest}: {state}" for nest, state in sorted(self.nest_sensors.items())]
    elif command == "platestatus":
      data = [self.spatula]
    elif command == "homedstatus":
      data = [self.homed]
    elif words[0] == "pick":
      self.nest_sensors[int(words[3])] = "PLATE_AVAILABLE"
    elif words[0] == "place":
      self.nest_sensors[int(words[3])] = "CLEAR"
    elif words[0] == "nesttransfer":
      self.nest_sensors[int(words[1])] = "CLEAR"
      self.nest_sensors[int(words[2])] = "PLATE_AVAILABLE"
    return _envelope(command, self._command_id, data)

  async def write(self, data: bytes, timeout=None):
    command = data.decode("ascii").rstrip("\r\n")
    self.written.append(command)
    self.events.append(command)
    self._stalling = command in self.stall_after_ack
    if self._stalling:
      self.stall_after_ack.remove(command)
    self._queue = self._respond(command)

  async def readuntil(self, separator: bytes = b"\n", timeout=None) -> bytes:
    if self._stalling and len(self._queue) == 1:
      raise TimeoutError("simulated response timeout")
    return await super().readuntil(separator=separator, timeout=timeout)


def describe(value: Any) -> Any:
  """A call's return value or raised error, made JSON-able. Resources are named."""
  if isinstance(value, BaseException):
    return {"error": type(value).__name__, "message": str(value)}
  if isinstance(value, handles.Resource):
    return value.name
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return describe(dataclasses.asdict(value))
  if isinstance(value, dict):
    return {str(key): describe(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [describe(item) for item in value]
  return value


class Recorder(recording.Recorder):
  """Runs a scenario's steps against a store and records what each one did."""

  def __init__(self, store: HighResSampleStorage, socket: SimulatedSocket):
    super().__init__()
    self.store = store
    self.socket = socket
    self.events = recording.EventLog()
    # Operation ids are random uuids: they are recorded as op1, op2... in order of appearance.
    self.operation_ids = recording.Placeholders("op{}")
    store.io = socket  # type: ignore[assignment]

  def _event(self, event: PLREvent) -> Dict[str, Any]:
    context = dict(event.context)
    if "operation_id" in context:
      context["operation_id"] = self.operation_ids(context["operation_id"])
    return {"name": event.name, "context": describe(context), "data": describe(event.data)}

  def _unresolved(self) -> Optional[Dict[str, Any]]:
    transfer = self.store.unresolved_transfer
    if transfer is None:
      return None
    return {
      "plate": transfer.plate.name,
      "source": transfer.source.name,
      "destination": transfer.destination.name,
      "command": transfer.command,
      "error_type": transfer.error_type,
      "error_message": transfer.error_message,
    }

  def take_sent(self) -> List[Any]:
    """What the socket was sent since the last call."""
    taken = list(self.socket.events)
    self.socket.events.clear()
    return taken

  def patches(self) -> List[ContextManager[Any]]:
    return [self.events.installed()]

  async def step(self, call: str, action: recording.Action) -> Any:  # type: ignore[override]
    """Run `action` (sync or async) as the step `call`; record it, and return what it returned
    or raised."""
    await self.mark()
    self.take_sent()
    self.events.take()
    result, error = await self.outcome(action)
    outcome = result if error is None else error
    entry: Dict[str, Any] = {
      "call": call,
      "sent": self.take_sent(),
      "events": [self._event(event) for event in self.events.take()],
      "result": describe(outcome),
      "unresolved_transfer": self._unresolved(),
    }
    resources = await self.changed()
    if resources is not None:
      entry["resources"] = resources
    self.steps.append(entry)
    return outcome

  async def snapshot(self) -> List[Dict[str, Any]]:
    """The resources under the store's body; none before setup creates it."""
    try:
      body = self.store.body
    except RuntimeError:
      return []
    return await snapshot_store(self.store.store, body)

  async def check(self, test: unittest.TestCase, scenario: str) -> None:
    """Compare the record of the steps so far with the scenario's golden file."""
    record = {"steps": self.steps, "resources": await self.snapshot()}
    check_golden(test, GOLDEN_DIRECTORY / f"{scenario}.json", record)
