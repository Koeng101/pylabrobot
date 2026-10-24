"""Golden records of what the manual operator does today: requests and resource moves.

The seam is the operator-action provider: every request the operator is sent is recorded in
order, with the events it emits and the resources under the deck after each step.
"""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import unittest
from typing import Any, Awaitable, Callable, ContextManager, Dict, List, Sequence, Union

from pylabrobot.manual_operator import (
  ManualOperator,
  OperatorActionRequest,
  OperatorActionResult,
)
from pylabrobot.resources import Coordinate, Rotation
from pylabrobot.resources.store import ResourceStore, build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

Outcome = Union[
  OperatorActionResult,
  Callable[[OperatorActionRequest], Union[OperatorActionResult, Awaitable[OperatorActionResult]]],
]


class _Recorder(recording.Recorder):
  """Answers operator requests from a script and records requests, events and resources.

  Operation ids are uuids; they are recorded as `op-1`, `op-2`... in the order they appear.
  """

  def __init__(self, root: handles.Resource):
    super().__init__()
    self.root = root
    self.outcomes: List[Outcome] = []
    self.operator = ManualOperator(self, name="bench_operator")
    self.events = recording.EventLog()

  async def request(self, action: OperatorActionRequest) -> OperatorActionResult:
    """The provider seam: record the request and answer with the next scripted outcome."""
    self.sent.append(
      {
        "operator_name": action.operator_name,
        "action": action.action,
        "title": action.title,
        "instructions": action.instructions,
        "confirmation_text": action.confirmation_text,
        "details": recording.plain(action.details),
        "resources": [resource.name for resource in action.resources],
        "source": None if action.source is None else action.source.name,
        "destination": None if action.destination is None else action.destination.name,
      }
    )
    outcome = self.outcomes.pop(0)
    if isinstance(outcome, OperatorActionResult):
      return outcome
    answer = outcome(action)
    return await answer if inspect.isawaitable(answer) else answer

  def patches(self) -> List[ContextManager[Any]]:
    return [self.events.installed()]

  def jsonable(self, value: Any) -> Any:
    return _result(value)

  def failed(self, entry: Dict[str, Any], error: BaseException) -> None:
    entry["result"] = recording.error_result(error)

  async def begin(self) -> None:
    self.events.take()
    await self.mark()

  async def annotate(self, entry: Dict[str, Any]) -> None:
    entry["events"] = [self.events.summary(event) for event in self.events.take()]
    resources = await self.changed()
    if resources is not None:
      entry["resources"] = resources

  async def step(  # type: ignore[override]
    self, call: str, action: Callable[[], Awaitable[Any]], *outcomes: Outcome
  ) -> Any:
    """Run one call with `outcomes` scripted for its requests, and record it."""
    self.outcomes = list(outcomes)
    return await super().step(call, action)

  async def snapshot(self) -> List[Dict[str, Any]]:
    return await snapshot_store(self.root.store, self.root)

  async def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": await self.snapshot()}


def _result(result: Any) -> Any:
  if isinstance(result, OperatorActionResult):
    return {"status": result.status, "message": result.message, "confirmed_by": result.confirmed_by}
  return recording.plain(result)


@dataclasses.dataclass
class _Bench:
  deck: handles.Resource
  module: handles.ResourceHolder
  nest: handles.ResourceHolder
  shelf: handles.Resource
  plate: handles.Resource


def _holder(
  name: str,
  location: Coordinate,
  child_location: Coordinate,
  accepts: Sequence["pb.ResourceKind"] = (),
) -> pb.ResourceDefinition:
  return build.resource(
    name,
    Coordinate(130, 90, 20),
    kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
    type_name="ResourceHolder",
    category="resource_holder",
    location=location,
    holder=pb.HolderSpec(child_location=build.vec3(child_location), accepts=accepts),
  )


async def _bench(nest_accepts: Sequence["pb.ResourceKind"] = ()) -> _Bench:
  """A deck with a plate module, a handover nest that sets its own child location, a shelf and
  a plate on the module, in a store of their own. A nest that accepts only some kinds refuses
  the plate, which is a plain resource."""
  store = ResourceStore.in_memory()
  deck = await store.create(
    build.resource(
      "deck",
      Coordinate(1000, 600, 10),
      type_name="Resource",
      children=[
        _holder("plate_module", Coordinate(100, 100, 0), Coordinate.zero()),
        _holder("handover_nest", Coordinate(400, 100, 0), Coordinate(1.5, 2.5, 3), nest_accepts),
        build.resource(
          "shelf", Coordinate(300, 100, 5), type_name="Resource", location=Coordinate(600, 300, 50)
        ),
      ],
    ),
    name="deck",
  )
  plate = await _resource(store, "plate", rotation=Rotation(z=90))
  module = await deck.get_resource("plate_module")
  nest = await deck.get_resource("handover_nest")
  shelf = await deck.get_resource("shelf")
  assert isinstance(module, handles.ResourceHolder) and isinstance(nest, handles.ResourceHolder)
  await module.assign_child_resource(plate)
  return _Bench(deck=deck, module=module, nest=nest, shelf=shelf, plate=plate)


async def _resource(
  store: ResourceStore,
  name: str,
  kind: "pb.ResourceKind" = pb.RESOURCE_KIND_RESOURCE,
  rotation: Rotation = Rotation(),
) -> handles.Resource:
  """A plate-sized resource, a root in `store`."""
  return await store.create(
    build.resource(
      name, Coordinate(127.76, 85.48, 14.2), kind=kind, type_name="Resource", rotation=rotation
    ),
    name=name,
  )


class ManualOperatorGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_moves_with_rotation_and_location(self):
    """A plate moved to a nest with a new rotation, then onto a shelf at a given location,
    then back to the module; and a non-moving action naming the plate."""
    bench = await _bench()
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

    check_golden(self, GOLDEN / "moves_with_rotation_and_location.json", await recorder.record())

  async def test_refusals_and_rollback(self):
    """Moves the operator cancels, reports failed, or that the model refuses, leave the plate
    where it was; a destination that fails to take the plate puts it back as it was. The nest
    takes only plates, and the plate moved is a plain resource, so the nest refuses it."""
    bench = await _bench(nest_accepts=[pb.RESOURCE_KIND_PLATE])
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

    other = await _resource(bench.deck.store, "other_plate", kind=pb.RESOURCE_KIND_PLATE)
    await nest.assign_child_resource(other)
    await recorder.step(
      "move_resource(plate, module -> occupied nest)",
      lambda: operator.move_resource(resource=plate, source=module, destination=nest),
    )
    await nest.unassign_child_resource(other)

    await recorder.step(
      "move_resource(plate, module -> nest, destination_rotation=z0) assignment fails",
      lambda: operator.move_resource(
        resource=plate, source=module, destination=nest, destination_rotation=Rotation(z=0)
      ),
      OperatorActionResult.completed(),
    )

    async def move_elsewhere_then_complete(
      _request: OperatorActionRequest,
    ) -> OperatorActionResult:
      await plate.unassign()
      await shelf.assign_child_resource(plate, location=Coordinate(10, 10, 0))
      return OperatorActionResult.completed()

    await recorder.step(
      "move_resource(plate, module -> nest) while the model changes",
      lambda: operator.move_resource(resource=plate, source=module, destination=nest),
      move_elsewhere_then_complete,
    )

    check_golden(self, GOLDEN / "refusals_and_rollback.json", await recorder.record())


if __name__ == "__main__":
  unittest.main()
