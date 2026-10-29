"""Recording a golden scenario step by step: what each step sent, waited, returned or raised.

A device's golden tests replace its transport with a fake that appends what it is sent to a
`Recorder`'s `sent`, and run each call of a scenario through `Recorder.step`, which records it as
one entry of `steps`:

  {"call": ..., "result": ... | "error": ..., "sent": [...], "waits": [...]}

`waits` is there only when the step waited. A device's tests add what else a step records
(resources, events) by overriding `annotate`, and `begin` to note what that is compared with;
they change how a value or an error is recorded by overriding `jsonable` or `failed`. A device
whose entries are laid out differently builds them from `outcome`, `add_outcome` and `take_sent`.

`snapshot`, `mark`, `changed` and `changes` follow the resources a device's record pins between
steps. `EventLog` records the events a step emits, and `Placeholders` stands in for the values,
such as uuids, that differ from run to run.

Waits are not slept: while `instant_sleeps` is in force, `asyncio.sleep` returns at once,
everywhere. A recorder that `records_waits` has it in force during each step and records a wait
only when the step's own task makes it. Work the step leaves to other tasks, such as a resource
server's, waits as often as the machine's speed has it do, so recording it would make the record
vary from run to run.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import datetime
import enum
import inspect
from typing import (
  Any,
  Awaitable,
  Callable,
  ContextManager,
  Dict,
  Iterator,
  List,
  Optional,
  Tuple,
  Type,
  Union,
)
from unittest import mock

from pylabrobot.events import EventBus, PLREvent, use_event_bus
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.server import handles
from pylabrobot.testing.golden import snapshot_changes

# A step's call: a coroutine already made, or a function that returns a value or an awaitable.
Action = Union[Awaitable[Any], Callable[[], Any]]


async def run(action: Action) -> Any:
  """Run a step's call: call it when it is a function, and await what it gives when it can be."""
  value = action() if callable(action) else action
  if inspect.isawaitable(value):
    value = await value
  return value


def described(error: BaseException) -> str:
  """An error as a step records it: `<class name>: <message>`."""
  return f"{type(error).__name__}: {error}"


def jsonable(value: Any) -> Any:
  """A value as a golden file holds it.

  Enums, integer ones too, are recorded by name, coordinates as `[x, y, z]`, resource handles by
  name, dataclasses by their fields, bytes as hex and times as `"<timestamp>"` (they are the time
  of the run). Anything else JSON cannot hold is recorded as its class's name.
  """
  if isinstance(value, enum.Enum):
    return value.name
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  if isinstance(value, datetime.datetime):
    return "<timestamp>"
  if isinstance(value, bytes):
    return value.hex()
  if isinstance(value, Coordinate):
    return [value.x, value.y, value.z]
  if isinstance(value, handles.Resource):
    return value.name
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return jsonable(dataclasses.asdict(value))
  if isinstance(value, dict):
    return {str(key): jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [jsonable(item) for item in value]
  return type(value).__name__


def plain(value: Any) -> Any:
  """`value` with tuples as lists and anything else that is not JSON as its class's name."""
  if isinstance(value, dict):
    return {str(key): plain(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [plain(item) for item in value]
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  return type(value).__name__


def error_result(error: BaseException) -> Dict[str, str]:
  """An error as a step that records it in place of its result does: its class and message."""
  return {"error": type(error).__name__, "message": str(error)}


class Placeholders:
  """Stand-ins for values that differ from run to run, such as uuids: each distinct value becomes
  `template` formatted with its number, numbered in order of first appearance from `start`."""

  def __init__(self, template: str, start: int = 1) -> None:
    self.template = template
    self.start = start
    self.given: Dict[str, str] = {}

  def __call__(self, value: str) -> str:
    if value not in self.given:
      self.given[value] = self.template.format(len(self.given) + self.start)
    return self.given[value]


class EventLog:
  """An event bus that keeps every event it is given, for steps to record.

  `installed` makes it the bus events are emitted on.
  """

  def __init__(self) -> None:
    self.bus = EventBus()
    self.events: List[PLREvent] = []
    self.bus.subscribe(self.events.append)
    self.operation_ids = Placeholders("op-{}")

  def installed(self) -> ContextManager[Any]:
    """Emit events on this log's bus while in force."""
    return use_event_bus(self.bus)

  def take(self) -> List[PLREvent]:
    """The events given since the last call."""
    taken, self.events[:] = list(self.events), []
    return taken

  def summary(self, event: PLREvent) -> Dict[str, Any]:
    """An event as most devices record it: its name, operation, operation id (as `op-<n>`) and
    data, anything in the data that JSON cannot hold given as its class's name."""
    operation_id = event.context.get("operation_id")
    return {
      "name": event.name,
      "operation": event.context.get("operation"),
      "operation_id": None if operation_id is None else self.operation_ids(operation_id),
      "data": plain(event.data),
    }


class Recorder:
  """Records a scenario's steps: what each sent, waited, returned or raised.

  Attributes:
    sent: what the fake transport was sent during the current step, appended to by the fake.
    waits: the delays the current step's task slept for, when `records_waits`.
    steps: every step recorded so far.
    now: the time `clock` gives.
    catches: the errors a step records rather than raises.
    records_waits: whether a step records its waits, with `instant_sleeps` in force while its
      call runs.
  """

  catches: Tuple[Type[BaseException], ...] = (Exception,)
  records_waits = False

  def __init__(self) -> None:
    self.sent: List[Any] = []
    self.waits: List[float] = []
    self.steps: List[Dict[str, Any]] = []
    self.now = 0.0
    self.resources: List[Dict[str, Any]] = []
    # The task a step runs in: the device's own waits are made there.
    self.step_task: Optional["asyncio.Task[Any]"] = None
    self._real_sleep = asyncio.sleep

  def clock(self, tick: float) -> Callable[[], float]:
    """A clock for the device to read in place of its own: each read advances `now` by `tick`, so
    a timeout waiting for a reply that never comes runs out at once."""

    def read() -> float:
      self.now += tick
      return self.now

    return read

  async def sleep(self, delay: float, result: Any = None) -> Any:
    """`asyncio.sleep`, sleeping for none and recording the delay when `records_waits` and the
    step's task sleeps."""
    if self.records_waits and asyncio.current_task() is self.step_task:
      self.waits.append(delay)
    await self._real_sleep(0)
    return result

  def instant_sleeps(self) -> ContextManager[Any]:
    """Replace `asyncio.sleep` with `sleep` while in force."""
    return mock.patch("asyncio.sleep", self.sleep)

  def patches(self) -> List[ContextManager[Any]]:
    """What is in force while a step's call runs: `instant_sleeps` when `records_waits`, and what
    a device's recorder adds."""
    return [self.instant_sleeps()] if self.records_waits else []

  @contextlib.contextmanager
  def _patched(self) -> Iterator[None]:
    with contextlib.ExitStack() as stack:
      for patch in self.patches():
        stack.enter_context(patch)
      yield

  async def outcome(self, action: Action) -> Tuple[Any, Optional[BaseException]]:
    """Run a step's call with `patches` in force: what it returned, or the error it raised when
    that is one of `catches`."""
    self.step_task = asyncio.current_task()
    try:
      with self._patched():
        return await run(action), None
    except self.catches as error:
      return None, error
    finally:
      self.step_task = None

  def take_sent(self) -> List[Any]:
    """What was sent since the last call, which starts a new step's record."""
    taken, self.sent[:] = list(self.sent), []
    return taken

  def jsonable(self, value: Any) -> Any:
    """A step's return value as its record holds it."""
    return jsonable(value)

  def failed(self, entry: Dict[str, Any], error: BaseException) -> None:
    """Record in `entry` that the step raised `error`."""
    entry["error"] = described(error)

  def add_outcome(
    self,
    entry: Dict[str, Any],
    value: Any,
    error: Optional[BaseException],
    result: Optional[Callable[[Any], Any]] = None,
  ) -> None:
    """Record in `entry` what `outcome` gave: the value made JSON-able (after `result` picks what
    of it is recorded), or, through `failed`, the error."""
    if error is None:
      entry["result"] = self.jsonable(value if result is None else result(value))
    else:
      self.failed(entry, error)

  async def begin(self) -> None:
    """Called as a step starts, before its call runs."""

  async def annotate(self, entry: Dict[str, Any]) -> None:
    """Add what else a step records to its `entry`, after what it sent and waited."""

  async def snapshot(self) -> List[Dict[str, Any]]:
    """The resources the record follows, as `snapshot_store` gives them; a device's recorder
    says which."""
    raise NotImplementedError

  async def mark(self) -> List[Dict[str, Any]]:
    """Take the resources as they are now as the ones `changed` and `changes` compare with."""
    self.resources = await self.snapshot()
    return self.resources

  async def changed(self) -> Optional[List[Dict[str, Any]]]:
    """The resources, when they differ from the last ones marked or returned; None otherwise."""
    after = await self.snapshot()
    if after == self.resources:
      return None
    self.resources = after
    return after

  async def changes(self) -> Dict[str, Any]:
    """What changed in the resources since the last ones marked, as `snapshot_changes` gives it;
    the resources now are marked."""
    before = self.resources
    return snapshot_changes(before, await self.mark())

  async def step(
    self, call: str, action: Action, result: Optional[Callable[[Any], Any]] = None
  ) -> Any:
    """Run one step of a scenario and record it.

    Args:
      call: the call, as the scenario writes it.
      action: the call itself.
      result: picks what of the call's return value is recorded, made JSON-able by `jsonable`.

    Returns:
      What the call returned, or None when it raised: what it raised is recorded instead.
    """
    self.take_sent()
    self.waits = []
    await self.begin()
    entry: Dict[str, Any] = {"call": call}
    value, error = await self.outcome(action)
    self.add_outcome(entry, value, error, result)
    entry["sent"] = self.take_sent()
    if self.waits:
      entry["waits"] = self.waits
    await self.annotate(entry)
    self.steps.append(entry)
    return value
