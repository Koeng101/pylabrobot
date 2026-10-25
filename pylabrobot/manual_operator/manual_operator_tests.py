import asyncio
import unittest
from typing import Awaitable, Callable, Optional, Sequence

from pylabrobot.events import EventBus, PLREvent, use_event_bus
from pylabrobot.manual_operator import (
  ConsoleOperatorActionProvider,
  ManualOperator,
  OperatorActionCancelledError,
  OperatorActionFailedError,
  OperatorActionRequest,
  OperatorActionResult,
)
from pylabrobot.resources import Coordinate, Rotation
from pylabrobot.resources.store import ResourceStore, build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb


class RecordingProvider:
  def __init__(self, result: OperatorActionResult):
    self.result = result
    self.requests: list[OperatorActionRequest] = []

  async def request(self, action: OperatorActionRequest) -> OperatorActionResult:
    self.requests.append(action)
    return self.result


class AsyncCallbackProvider:
  def __init__(self, callback: Callable[[OperatorActionRequest], Awaitable[OperatorActionResult]]):
    self.callback = callback
    self.requests: list[OperatorActionRequest] = []

  async def request(self, action: OperatorActionRequest) -> OperatorActionResult:
    self.requests.append(action)
    return await self.callback(action)


class TestManualOperator(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.store = ResourceStore.in_memory()

  async def asyncTearDown(self):
    await self.store.close()

  async def holder(
    self,
    name: str,
    child_location: Coordinate = Coordinate.zero(),
    parent: Optional[handles.Resource] = None,
    location: Optional[Coordinate] = None,
    accepts: Sequence["pb.ResourceKind"] = (),
  ) -> handles.ResourceHolder:
    holder = await self.store.create(
      build.resource(
        name,
        Coordinate(100, 100, 10),
        kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
        holder=pb.HolderSpec(child_location=build.vec3(child_location), accepts=accepts),
      ),
      name=name,
      parent=parent,
      location=location,
    )
    assert isinstance(holder, handles.ResourceHolder)
    return holder

  async def resource(
    self,
    name: str,
    size: Coordinate = Coordinate(80, 60, 15),
    rotation: Optional[Rotation] = None,
    parent: Optional[handles.Resource] = None,
  ) -> handles.Resource:
    return await self.store.create(
      build.resource(name, size, rotation=rotation), name=name, parent=parent
    )

  async def test_perform_sends_structured_request_and_returns_completion(self):
    provider = RecordingProvider(OperatorActionResult.completed(confirmed_by="operator-1"))
    operator = ManualOperator(provider, name="cell_operator")

    result = await operator.perform(
      action="centrifuge.spin",
      title="Spin sample plate",
      instructions="Spin plate_1 at 300 x g for 180 seconds.",
      confirmation_text="Confirm spin completed",
      details={"relative_centrifugal_force": 300, "duration": 180},
    )

    self.assertEqual(result.confirmed_by, "operator-1")
    self.assertEqual(len(provider.requests), 1)
    request = provider.requests[0]
    self.assertEqual(request.operator_name, "cell_operator")
    self.assertEqual(request.action, "centrifuge.spin")
    self.assertEqual(request.details["duration"], 180)
    self.assertEqual(request.resources, ())
    self.assertIsNone(request.source)
    self.assertIsNone(request.destination)

  async def test_cancelled_result_raises_specific_error(self):
    provider = RecordingProvider(OperatorActionResult.cancelled(message="Protocol stopped"))
    operator = ManualOperator(provider)

    with self.assertRaisesRegex(OperatorActionCancelledError, "Protocol stopped"):
      await operator.perform(action="inspect", title="Inspect plate", instructions="Inspect it.")

  async def test_failed_result_raises_specific_error(self):
    provider = RecordingProvider(OperatorActionResult.failed(message="Plate was damaged"))
    operator = ManualOperator(provider)

    with self.assertRaisesRegex(OperatorActionFailedError, "Plate was damaged"):
      await operator.perform(action="inspect", title="Inspect plate", instructions="Inspect it.")

  async def test_provider_exception_propagates(self):
    class FailingProvider:
      async def request(self, action: OperatorActionRequest) -> OperatorActionResult:
        del action
        raise ConnectionError("provider disconnected")

    with self.assertRaisesRegex(ConnectionError, "provider disconnected"):
      await ManualOperator(FailingProvider()).perform(
        action="inspect", title="Inspect plate", instructions="Inspect it."
      )

  async def test_request_copies_details(self):
    details = {"duration": 60}
    resources = [await self.resource("plate")]
    request = OperatorActionRequest(
      operator_name="operator",
      action="centrifuge.spin",
      title="Spin",
      instructions="Spin the plate.",
      details=details,
      resources=resources,
    )

    details["duration"] = 120
    resources.clear()

    self.assertEqual(request.details["duration"], 60)
    self.assertEqual(len(request.resources), 1)

  async def test_result_rejects_unknown_status(self):
    with self.assertRaisesRegex(ValueError, "Unsupported operator action status"):
      OperatorActionResult(status="unknown")  # type: ignore[arg-type]

  async def test_move_resource_reassigns_only_after_completion(self):
    source = await self.holder("source")
    destination = await self.holder("destination", child_location=Coordinate(4, 5, 6))
    plate = await self.resource("plate", parent=source)
    seen: list[Optional[handles.Resource]] = []

    async def complete_while_model_is_unchanged(
      request: OperatorActionRequest,
    ) -> OperatorActionResult:
      seen.extend(
        [
          await plate.get_parent(),
          await source.get_resource_held(),
          await destination.get_resource_held(),
        ]
      )
      self.assertEqual(request.action, "resource.move")
      return OperatorActionResult.completed(confirmed_by="operator-1")

    provider = AsyncCallbackProvider(complete_while_model_is_unchanged)

    result = await ManualOperator(provider).move_resource(
      resource=plate,
      source=source,
      destination=destination,
    )

    self.assertEqual(seen, [source, plate, None])
    self.assertEqual(result.confirmed_by, "operator-1")
    self.assertIsNone(await source.get_resource_held())
    self.assertEqual(await destination.get_resource_held(), plate)
    self.assertEqual(await plate.get_location(), Coordinate(4, 5, 6))
    request = provider.requests[0]
    self.assertEqual(request.details, {})
    self.assertEqual(request.resources, (plate,))
    self.assertEqual(request.source, source)
    self.assertEqual(request.destination, destination)

  async def test_move_resource_reassigns_between_holders_on_the_same_root(self):
    deck = await self.resource("deck", size=Coordinate(1000, 1000, 10))
    source = await self.holder("plate_module_0", parent=deck, location=Coordinate(0, 0, 0))
    destination = await self.holder("handover_nest", parent=deck, location=Coordinate(200, 0, 0))
    plate = await self.resource("plate", parent=source)

    await ManualOperator(RecordingProvider(OperatorActionResult.completed())).move_resource(
      resource=plate,
      source=source,
      destination=destination,
    )

    self.assertIsNone(await source.get_resource_held())
    self.assertEqual(await destination.get_resource_held(), plate)
    self.assertEqual(await plate.get_parent(), destination)

  async def test_move_resource_uses_explicit_destination_location(self):
    source = await self.holder("source")
    destination = await self.resource("destination", size=Coordinate(100, 100, 10))
    plate = await self.resource("plate", parent=source)
    location = Coordinate(1, 2, 3)
    provider = RecordingProvider(OperatorActionResult.completed())

    await ManualOperator(provider).move_resource(
      resource=plate,
      source=source,
      destination=destination,
      destination_location=location,
      details={"reason": "manual handoff"},
    )

    self.assertEqual(await plate.get_parent(), destination)
    self.assertEqual(await plate.get_location(), location)
    self.assertEqual(provider.requests[0].details["reason"], "manual handoff")
    self.assertEqual(
      provider.requests[0].details["destination_location"],
      {"x": 1, "y": 2, "z": 3, "type": "Coordinate"},
    )

  async def test_move_resource_applies_destination_rotation_before_assignment(self):
    source = await self.holder("source")
    destination = await self.holder("destination", child_location=Coordinate(4, 5, 6))
    plate = await self.resource(
      "plate", size=Coordinate(127, 85, 15), rotation=Rotation(z=90), parent=source
    )
    provider = RecordingProvider(OperatorActionResult.completed())

    await ManualOperator(provider).move_resource(
      resource=plate,
      source=source,
      destination=destination,
      destination_rotation=Rotation(z=0),
    )

    self.assertEqual(await plate.get_parent(), destination)
    self.assertEqual((await plate.get_rotation()).z, 0)
    self.assertEqual(await plate.get_location(), Coordinate(4, 5, 6))
    self.assertEqual(
      provider.requests[0].details["destination_rotation"],
      {"x": 0, "y": 0, "z": 0, "type": "Rotation"},
    )

  async def test_move_resource_cancellation_leaves_model_unchanged(self):
    source = await self.holder("source")
    destination = await self.holder("destination")
    plate = await self.resource("plate", rotation=Rotation(z=90), parent=source)
    provider = RecordingProvider(OperatorActionResult.cancelled())

    with self.assertRaises(OperatorActionCancelledError):
      await ManualOperator(provider).move_resource(
        resource=plate,
        source=source,
        destination=destination,
        destination_rotation=Rotation(z=0),
      )

    self.assertEqual(await source.get_resource_held(), plate)
    self.assertIsNone(await destination.get_resource_held())
    self.assertEqual((await plate.get_rotation()).z, 90)

  async def test_move_resource_restores_original_pose_when_destination_assignment_fails(self):
    deck = await self.resource("deck", size=Coordinate(1000, 1000, 10))
    source = await self.holder("source", parent=deck, location=Coordinate(0, 0, 0))
    # The destination takes only plates; the plate moved is a plain resource.
    destination = await self.holder(
      "destination",
      parent=deck,
      location=Coordinate(200, 0, 0),
      accepts=[pb.RESOURCE_KIND_PLATE],
    )
    plate = await self.resource(
      "plate", size=Coordinate(127, 85, 15), rotation=Rotation(z=90), parent=source
    )
    original_location = await plate.get_location()

    with self.assertRaisesRegex(RuntimeError, "does not take 'plate'"):
      await ManualOperator(RecordingProvider(OperatorActionResult.completed())).move_resource(
        resource=plate,
        source=source,
        destination=destination,
        destination_rotation=Rotation(z=0),
      )

    self.assertEqual(await source.get_resource_held(), plate)
    self.assertEqual(await plate.get_parent(), source)
    self.assertEqual(await plate.get_location(), original_location)
    self.assertEqual((await plate.get_rotation()).z, 90)
    self.assertIsNone(await destination.get_resource_held())

  async def test_move_resource_without_rotation_is_one_assignment_the_store_may_refuse(self):
    source = await self.holder("source")
    destination = await self.holder("destination", accepts=[pb.RESOURCE_KIND_PLATE])
    plate = await self.resource("plate", parent=source)
    event_bus = EventBus()
    events: list[PLREvent] = []
    event_bus.subscribe(events.append)

    with use_event_bus(event_bus):
      with self.assertRaisesRegex(RuntimeError, "does not take 'plate'"):
        await ManualOperator(RecordingProvider(OperatorActionResult.completed())).move_resource(
          resource=plate, source=source, destination=destination
        )

    self.assertEqual(await plate.get_parent(), source)
    self.assertEqual([e.name for e in events if e.name.startswith("resource.")], [])

  async def test_move_resource_rejects_incorrect_source_before_prompt(self):
    actual_source = await self.holder("actual_source")
    stated_source = await self.holder("stated_source")
    destination = await self.holder("destination")
    plate = await self.resource("plate", parent=actual_source)
    provider = RecordingProvider(OperatorActionResult.completed())

    with self.assertRaisesRegex(ValueError, "not source 'stated_source'"):
      await ManualOperator(provider).move_resource(
        resource=plate,
        source=stated_source,
        destination=destination,
      )

    self.assertEqual(provider.requests, [])
    self.assertEqual(await plate.get_parent(), actual_source)

  async def test_move_resource_rejects_occupied_destination_before_prompt(self):
    source = await self.holder("source")
    destination = await self.holder("destination")
    plate = await self.resource("plate", parent=source)
    other_plate = await self.resource("other_plate", parent=destination)
    provider = RecordingProvider(OperatorActionResult.completed())

    with self.assertRaisesRegex(RuntimeError, "already has a resource"):
      await ManualOperator(provider).move_resource(
        resource=plate,
        source=source,
        destination=destination,
      )

    self.assertEqual(provider.requests, [])
    self.assertEqual(await source.get_resource_held(), plate)
    self.assertEqual(await destination.get_resource_held(), other_plate)

  async def test_move_resource_detects_model_change_while_pending(self):
    source = await self.holder("source")
    destination = await self.holder("destination")
    unexpected = await self.holder("unexpected")
    plate = await self.resource("plate", parent=source)

    async def change_model_then_complete(_request: OperatorActionRequest) -> OperatorActionResult:
      await unexpected.assign_child_resource(plate)
      return OperatorActionResult.completed()

    provider = AsyncCallbackProvider(change_model_then_complete)

    with self.assertRaisesRegex(RuntimeError, "model changed while the manual move was pending"):
      await ManualOperator(provider).move_resource(
        resource=plate,
        source=source,
        destination=destination,
      )

    self.assertEqual(await plate.get_parent(), unexpected)
    self.assertIsNone(await destination.get_resource_held())

  async def test_perform_emits_action_specific_lifecycle_events(self):
    plate = await self.resource("plate")
    provider = RecordingProvider(
      OperatorActionResult.completed(message="Spin verified", confirmed_by="operator-1")
    )
    event_bus = EventBus()
    events: list[PLREvent] = []
    event_bus.subscribe(events.append)

    with use_event_bus(event_bus):
      await ManualOperator(provider, name="cell_operator").perform(
        action="centrifuge.spin",
        title="Spin sample plate",
        instructions="Spin plate at 300 x g for 180 seconds.",
        details={"relative_centrifugal_force": 300, "duration": 180},
        resources=[plate],
      )

    self.assertEqual(
      [event.name for event in events],
      [
        "manual_operator.centrifuge.spin.started",
        "manual_operator.centrifuge.spin.completed",
      ],
    )
    self.assertEqual(events[0].context["operation"], "manual_operator.centrifuge.spin")
    self.assertEqual(events[0].context["operation_id"], events[1].context["operation_id"])
    self.assertEqual(
      events[0].data["device"],
      {"name": "cell_operator", "type": "ManualOperator"},
    )
    self.assertEqual(events[0].data["resources"][0]["name"], "plate")
    self.assertEqual(events[0].data["manual_action"], "centrifuge.spin")
    self.assertEqual(events[0].data["details"]["relative_centrifugal_force"], 300)
    self.assertNotIn("confirmed_by", events[0].data)
    self.assertEqual(events[1].data["confirmed_by"], "operator-1")
    self.assertEqual(events[1].data["result_message"], "Spin verified")

  async def test_perform_emits_failed_event_for_reported_failure(self):
    provider = RecordingProvider(OperatorActionResult.failed(message="Inspection failed"))
    event_bus = EventBus()
    events: list[PLREvent] = []
    event_bus.subscribe(events.append)

    with use_event_bus(event_bus):
      with self.assertRaises(OperatorActionFailedError):
        await ManualOperator(provider).perform(
          action="quality_control.inspect",
          title="Inspect sample",
          instructions="Inspect the sample.",
        )

    self.assertEqual(
      [event.name for event in events],
      [
        "manual_operator.quality_control.inspect.started",
        "manual_operator.quality_control.inspect.failed",
      ],
    )
    self.assertEqual(events[1].data["error_type"], "OperatorActionFailedError")
    self.assertEqual(events[1].data["error_message"], "Inspection failed")

  async def test_move_resource_emits_resource_and_endpoint_context(self):
    source = await self.holder("source")
    destination = await self.holder("destination")
    plate = await self.resource("plate", parent=source)
    provider = RecordingProvider(OperatorActionResult.completed())
    event_bus = EventBus()
    events: list[PLREvent] = []
    event_bus.subscribe(events.append)

    with use_event_bus(event_bus):
      await ManualOperator(provider).move_resource(
        resource=plate,
        source=source,
        destination=destination,
        destination_rotation=Rotation(z=90),
      )

    manual_events = [event for event in events if event.name.startswith("manual_operator.")]
    self.assertEqual(
      [event.name for event in manual_events],
      ["manual_operator.resource.move.started", "manual_operator.resource.move.completed"],
    )
    self.assertEqual(manual_events[0].data["resources"][0]["name"], "plate")
    self.assertEqual(manual_events[0].data["source"]["name"], "source")
    self.assertEqual(manual_events[0].data["destination"]["name"], "destination")
    self.assertEqual(
      manual_events[0].data["details"]["destination_rotation"],
      {"x": 0, "y": 0, "z": 90, "type": "Rotation"},
    )
    self.assertEqual(
      manual_events[1].data["details"]["destination_rotation"],
      {"x": 0, "y": 0, "z": 90, "type": "Rotation"},
    )
    self.assertEqual(
      [event.name for event in events if event.name.startswith("resource.")],
      ["resource.unassigned", "resource.assigned"],
    )
    self.assertEqual(await plate.get_parent(), destination)


class TestConsoleOperatorActionProvider(unittest.IsolatedAsyncioTestCase):
  async def test_enter_completes_action_without_blocking_event_loop(self):
    output: list[str] = []

    def input_fn(prompt: str) -> str:
      output.append(prompt)
      return ""

    provider = ConsoleOperatorActionProvider(
      input_fn=input_fn,
      output_fn=output.append,
    )
    request = OperatorActionRequest(
      operator_name="operator",
      action="inspect",
      title="Inspect plate",
      instructions="Check that the plate is seated.",
    )
    event_loop_progressed = asyncio.Event()

    async def mark_progress() -> None:
      await asyncio.sleep(0)
      event_loop_progressed.set()

    progress_task = asyncio.create_task(mark_progress())
    result = await provider.request(request)
    await progress_task

    self.assertTrue(event_loop_progressed.is_set())
    self.assertEqual(result, OperatorActionResult.completed())
    self.assertIn("Inspect plate", output[0])
    self.assertEqual(output[1], "Confirm action completed: ")
