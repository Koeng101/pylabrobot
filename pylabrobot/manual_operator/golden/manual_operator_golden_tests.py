"""Golden records of what the manual operator does today: requests and resource moves.

The seam is the operator-action provider: every request the operator is sent is recorded in
order, with the events it emits and the resources under the deck after each step.
"""

from __future__ import annotations

import dataclasses
import pathlib
import unittest
from typing import Any, Awaitable, Callable, Dict, List, Union

from pylabrobot.events import EventBus, PLREvent, use_event_bus
from pylabrobot.manual_operator import (
  ManualOperator,
  OperatorActionRequest,
  OperatorActionResult,
)
from pylabrobot.resources import Coordinate, Resource, ResourceHolder, Rotation
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent

Outcome = Union[OperatorActionResult, Callable[[OperatorActionRequest], OperatorActionResult]]


def _jsonable(value: Any) -> Any:
  """`value` with tuples as lists and anything else that is not JSON as its type name."""
  if isinstance(value, dict):
    return {str(key): _jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [_jsonable(item) for item in value]
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  return type(value).__name__


class _Recorder:
  """Answers operator requests from a script and records requests, events and resources.

  Operation ids are uuids; they are recorded as `op-1`, `op-2`... in the order they appear.
  """

  def __init__(self, root: Resource):
    self.root = root
    self.outcomes: List[Outcome] = []
    self.sent: List[Dict[str, Any]] = []
    self.events: List[Dict[str, Any]] = []
    self.steps: List[Dict[str, Any]] = []
    self.operator = ManualOperator(self, name="bench_operator")
    self._operation_ids: Dict[str, str] = {}
    self.bus = EventBus()
    self.bus.subscribe(self._on_event)

  async def request(self, action: OperatorActionRequest) -> OperatorActionResult:
    """The provider seam: record the request and answer with the next scripted outcome."""
    self.sent.append(
      {
        "operator_name": action.operator_name,
        "action": action.action,
        "title": action.title,
        "instructions": action.instructions,
        "confirmation_text": action.confirmation_text,
        "details": _jsonable(action.details),
        "resources": [resource.name for resource in action.resources],
        "source": None if action.source is None else action.source.name,
        "destination": None if action.destination is None else action.destination.name,
      }
    )
    outcome = self.outcomes.pop(0)
    if isinstance(outcome, OperatorActionResult):
      return outcome
    return outcome(action)

  def _on_event(self, event: PLREvent) -> None:
    raw_id = event.context.get("operation_id")
    operation_id = None
    if raw_id is not None:
      operation_id = self._operation_ids.setdefault(raw_id, f"op-{len(self._operation_ids) + 1}")
    self.events.append(
      {
        "name": event.name,
        "operation": event.context.get("operation"),
        "operation_id": operation_id,
        "data": _jsonable(event.data),
      }
    )

  async def step(self, call: str, action: Callable[[], Awaitable[Any]], *outcomes: Outcome) -> Any:
    """Run one call with `outcomes` scripted for its requests, and record it."""
    self.outcomes = list(outcomes)
    self.sent = []
    self.events = []
    before = snapshot_resources(self.root)
    record: Dict[str, Any] = {"call": call}
    result: Any = None
    with use_event_bus(self.bus):
      try:
        result = await action()
        record["result"] = _result(result)
      except Exception as error:
        record["result"] = {"error": type(error).__name__, "message": str(error)}
    record["sent"] = self.sent
    record["events"] = self.events
    after = snapshot_resources(self.root)
    if after != before:
      record["resources"] = after
    self.steps.append(record)
    return result

  def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": snapshot_resources(self.root)}


def _result(result: Any) -> Any:
  if isinstance(result, OperatorActionResult):
    return {"status": result.status, "message": result.message, "confirmed_by": result.confirmed_by}
  return _jsonable(result)


@dataclasses.dataclass
class _Bench:
  deck: Resource
  module: ResourceHolder
  nest: ResourceHolder
  shelf: Resource
  plate: Resource


def _bench() -> _Bench:
  """A deck with a plate module, a handover nest that sets its own child location, a shelf and
  a plate on the module."""
  deck = Resource("deck", size_x=1000, size_y=600, size_z=10)
  module = ResourceHolder("plate_module", size_x=130, size_y=90, size_z=20)
  nest = ResourceHolder(
    "handover_nest", size_x=130, size_y=90, size_z=20, child_location=Coordinate(1.5, 2.5, 3)
  )
  shelf = Resource("shelf", size_x=300, size_y=100, size_z=5)
  deck.assign_child_resource(module, location=Coordinate(100, 100, 0))
  deck.assign_child_resource(nest, location=Coordinate(400, 100, 0))
  deck.assign_child_resource(shelf, location=Coordinate(600, 300, 50))
  plate = Resource("plate", size_x=127.76, size_y=85.48, size_z=14.2, rotation=Rotation(z=90))
  module.assign_child_resource(plate)
  return _Bench(deck=deck, module=module, nest=nest, shelf=shelf, plate=plate)


class ManualOperatorGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_moves_with_rotation_and_location(self):
    """A plate moved to a nest with a new rotation, then onto a shelf at a given location,
    then back to the module; and a non-moving action naming the plate."""
    bench = _bench()
    plate, module, nest, shelf = bench.plate, bench.module, bench.nest, bench.shelf
    recorder = _Recorder(bench.deck)
    operator = recorder.operator

    await recorder.step(
      "move_resource(plate, module -> nest, destination_rotation=z0)",
      lambda: operator.move_resource(
        resource=plate, source=module, destination=nest, destination_rotation=Rotation(z=0)
      ),
      OperatorActionResult.completed(message="Moved", confirmed_by="operator-1"),
    )
    await recorder.step(
      "move_resource(plate, nest -> shelf, destination_location=(20, 5, 0), z180, details)",
      lambda: operator.move_resource(
        resource=plate,
        source=nest,
        destination=shelf,
        destination_location=Coordinate(20, 5, 0),
        destination_rotation=Rotation(z=180),
        title="Park the plate",
        instructions="Put the plate on the shelf, A1 back right.",
        confirmation_text="Plate parked",
        details={"reason": "manual handoff"},
      ),
      OperatorActionResult.completed(),
    )
    await recorder.step(
      "move_resource(plate, shelf -> module)",
      lambda: operator.move_resource(resource=plate, source=shelf, destination=module),
      OperatorActionResult.completed(confirmed_by="operator-2"),
    )
    await recorder.step(
      "perform(centrifuge.spin, resources=[plate])",
      lambda: operator.perform(
        action="centrifuge.spin",
        title="Spin the plate",
        instructions="Spin the plate at 300 x g for 180 seconds.",
        details={"relative_centrifugal_force": 300, "duration": 180},
        resources=[plate],
      ),
      OperatorActionResult.completed(message="Spun", confirmed_by="operator-1"),
    )

    check_golden(self, GOLDEN / "moves_with_rotation_and_location.json", recorder.record())

  async def test_refusals_and_rollback(self):
    """Moves the operator cancels, reports failed, or that the model refuses, leave the plate
    where it was; a destination that fails to take the plate puts it back as it was."""
    bench = _bench()
    plate, module, nest, shelf = bench.plate, bench.module, bench.nest, bench.shelf
    recorder = _Recorder(bench.deck)
    operator = recorder.operator

    await recorder.step(
      "move_resource(plate, module -> nest) cancelled",
      lambda: operator.move_resource(
        resource=plate, source=module, destination=nest, destination_rotation=Rotation(z=0)
      ),
      OperatorActionResult.cancelled(message="Protocol stopped"),
    )
    await recorder.step(
      "move_resource(plate, module -> nest) failed",
      lambda: operator.move_resource(resource=plate, source=module, destination=nest),
      OperatorActionResult.failed(message="Plate was dropped", confirmed_by="operator-1"),
    )
    await recorder.step(
      "move_resource(plate, nest -> shelf) from the wrong source",
      lambda: operator.move_resource(resource=plate, source=nest, destination=shelf),
    )
    await recorder.step(
      "move_resource(plate, module -> module)",
      lambda: operator.move_resource(resource=plate, source=module, destination=module),
    )

    other = Resource("other_plate", size_x=127.76, size_y=85.48, size_z=14.2)
    nest.assign_child_resource(other)
    await recorder.step(
      "move_resource(plate, module -> occupied nest)",
      lambda: operator.move_resource(resource=plate, source=module, destination=nest),
    )
    nest.unassign_child_resource(other)

    def fail_assignment(resource: Resource) -> None:
      raise RuntimeError(f"nest refused {resource.name}")

    nest.register_will_assign_resource_callback(fail_assignment)
    await recorder.step(
      "move_resource(plate, module -> nest, destination_rotation=z0) assignment fails",
      lambda: operator.move_resource(
        resource=plate, source=module, destination=nest, destination_rotation=Rotation(z=0)
      ),
      OperatorActionResult.completed(),
    )
    nest.deregister_will_assign_resource_callback(fail_assignment)

    def move_elsewhere_then_complete(_request: OperatorActionRequest) -> OperatorActionResult:
      plate.unassign()
      shelf.assign_child_resource(plate, location=Coordinate(10, 10, 0))
      return OperatorActionResult.completed()

    await recorder.step(
      "move_resource(plate, module -> nest) while the model changes",
      lambda: operator.move_resource(resource=plate, source=module, destination=nest),
      move_elsewhere_then_complete,
    )

    check_golden(self, GOLDEN / "refusals_and_rollback.json", recorder.record())


if __name__ == "__main__":
  unittest.main()
