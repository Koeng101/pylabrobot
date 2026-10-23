"""Golden tests of the events the bus emits as the resource tree changes and operations run.

The seam is a listener on an `EventBus` installed for the test: every event it is given is
recorded, in order.
"""

import asyncio
import pathlib
import unittest
import warnings
from typing import Any, Callable, Dict, List

from pylabrobot.events import (
  EventBus,
  PLREvent,
  emit_event,
  event_operation,
  evented_operation,
  handle_reference,
  use_event_bus,
)
from pylabrobot.resources import Coordinate
from pylabrobot.resources.hamilton import STARLetDeck
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.definitions import definition_from_resource
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent


async def build_bench(store: ResourceStore) -> Dict[str, handles.Resource]:
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack."""
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    plr_deck = STARLetDeck(
      name="deck",
      with_trash96=False,
      with_teaching_needle_rack=False,
      core_grippers=None,
    )
  deck = await store.create(definition_from_resource(plr_deck), name="deck")
  plate_carrier = await store.create(
    "hamilton_plate_carrier_L5_ac", name="plate_carrier", parent=deck, track=1
  )
  assert isinstance(plate_carrier, handles.Carrier)
  plate = await store.create("cor_96_wellplate_360uL_Fb", name="plate", parent=plate_carrier[0])
  tip_carrier = await store.create(
    "hamilton_tip_carrier_L5", name="tip_carrier", parent=deck, track=8
  )
  assert isinstance(tip_carrier, handles.Carrier)
  tips = await store.create("hamilton_96_tiprack_300uL", name="tips", parent=tip_carrier[0])
  return {"deck": deck, "plate_carrier": plate_carrier, "plate": plate, "tips": tips}


async def move_to(resource: handles.Resource, location: Coordinate) -> None:
  """Put a resource somewhere else in its parent, as setting `location` does."""
  await resource.store.commands.record_device_positions(
    spb.RecordDevicePositionsRequest(
      positions=[
        spb.DevicePosition(
          resource=resource.ref,
          location=pb.PartialVec3(x=location.x, y=location.y, z=location.z),
        )
      ]
    )
  )


class Bench:
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack, in a
  resource store, with an event bus whose events are recorded step by step."""

  def __init__(self) -> None:
    self.store = ResourceStore.in_memory()
    self.bus = EventBus()
    self.events: List[PLREvent] = []
    self.bus.subscribe(self.events.append)
    self.operations: Dict[str, str] = {}
    self.steps: List[Dict[str, Any]] = []

  async def build(self) -> None:
    built = await build_bench(self.store)
    self.deck = built["deck"]
    plate_carrier, plate, tips = built["plate_carrier"], built["plate"], built["tips"]
    assert isinstance(plate_carrier, handles.Carrier)
    assert isinstance(plate, handles.Plate) and isinstance(tips, handles.TipRack)
    self.plate_carrier, self.plate, self.tips = plate_carrier, plate, tips

  def _event(self, event: PLREvent) -> Dict[str, Any]:
    """An event as recorded: its timestamp left out, and each operation id, a random uuid,
    replaced by `<operation-n>`, numbered by first appearance."""
    context = dict(event.context)
    if "operation_id" in context:
      operation_id = context["operation_id"]
      context["operation_id"] = self.operations.setdefault(
        operation_id, f"<operation-{len(self.operations)}>"
      )
    return {"sequence": event.sequence, "name": event.name, "context": context, "data": event.data}

  async def step(self, call: str, action: Callable[[], Any]) -> None:
    """Run `action` with the bus installed, and record the events it emitted under `call`."""
    before = len(self.events)
    entry: Dict[str, Any] = {"call": call}
    with use_event_bus(self.bus):
      try:
        result = action()
        if asyncio.iscoroutine(result):
          result = await result
        entry["result"] = result
      except Exception as error:  # the failure is part of what is recorded
        entry["raised"] = f"{type(error).__name__}: {error}"
    entry["sent"] = [self._event(event) for event in self.events[before:]]
    self.steps.append(entry)

  async def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": await snapshot_store(self.store, self.deck)}


class EventsGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.bench = Bench()
    await self.bench.build()

  async def asyncTearDown(self) -> None:
    await self.bench.store.close()

  async def test_tree_changes(self) -> None:
    bench = self.bench
    other = await bench.store.create("cor_96_wellplate_360uL_Fb", name="other_plate")

    await bench.step(
      "plate_carrier[2] = other_plate",
      lambda: bench.plate_carrier[2].assign_child_resource(other),
    )
    await bench.step("other_plate.unassign()", other.unassign)

    async def move_plate() -> None:
      await bench.plate.unassign()
      await bench.plate_carrier[1].assign_child_resource(bench.plate)

    await bench.step("plate.unassign(); plate_carrier[1] = plate", move_plate)
    await bench.step("plate.rotate(z=90)", lambda: bench.plate.rotate(z=90))
    await bench.step(
      "plate.location = Coordinate(1, 2, 3)", lambda: move_to(bench.plate, Coordinate(1, 2, 3))
    )
    well = bench.plate.get_well("A1")
    await bench.step("resource_reference(plate['A1'])", lambda: handle_reference(well))
    check_golden(self, GOLDEN / "tree_changes.json", await bench.record())

  async def test_state_changes(self) -> None:
    bench = self.bench
    well = bench.plate.get_well("A1")
    await bench.step("plate['A1'].tracker.set_volume(100)", lambda: well.set_volume(100))
    all_but_a1 = [index != 0 for index in range(bench.tips.num_items)]
    await bench.step("tips['A1'].unassign_tip()", lambda: bench.tips.set_tip_state(all_but_a1))
    await bench.step("tips['A1'].assign_tip(tips['A1'].make_tip())", bench.tips.fill)
    await bench.step(
      "plate.set_well_volumes([50] * 96)", lambda: bench.plate.set_well_volumes([50] * 96)
    )
    await bench.step("unassign_tip() on every spot holding one", bench.tips.empty)
    check_golden(self, GOLDEN / "state_changes.json", await bench.record())

  async def test_operations(self) -> None:
    bench = self.bench
    other = await bench.store.create("cor_96_wellplate_360uL_Fb", name="other_plate")

    async def move_in_operation() -> None:
      with event_operation("carrier.load", plate=await handle_reference(other), site=2):
        await bench.plate_carrier[2].assign_child_resource(other)
        emit_event("carrier.loaded", site=2)

    await bench.step("event_operation('carrier.load') around an assignment", move_in_operation)

    async def completed_with_final_state() -> None:
      volume: Dict[str, float] = {}
      with event_operation(
        "plate.fill",
        completed_data_factory=lambda: volume,
        well=await handle_reference(well),
      ):
        await well.set_volume(20)
        volume["volume"] = await well.get_volume()

    well = bench.plate.get_well("B2")
    await bench.step(
      "event_operation('plate.fill', completed_data_factory=...)", completed_with_final_state
    )

    async def failing_operation() -> None:
      with event_operation("carrier.unload", plate=await handle_reference(other)):
        await other.unassign()
        raise RuntimeError("gripper lost the plate")

    await bench.step("event_operation('carrier.unload') that raises", failing_operation)

    plate_reference = await handle_reference(bench.plate)

    @evented_operation("plate.rotate", lambda plate, z: {"plate": plate_reference, "z": z})
    async def rotate(plate: handles.Plate, z: float) -> str:
      await plate.rotate(z=z)
      emit_event("plate.rotated", z=z)
      return plate.name

    await bench.step(
      "evented_operation('plate.rotate')(plate, z=180)", lambda: rotate(bench.plate, z=180)
    )
    check_golden(self, GOLDEN / "operations.json", await bench.record())


if __name__ == "__main__":
  unittest.main()
