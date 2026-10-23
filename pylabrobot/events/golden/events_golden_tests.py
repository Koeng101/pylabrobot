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
  resource_reference,
  use_event_bus,
)
from pylabrobot.resources import Coordinate, Plate, PlateCarrier, Resource, TipRack
from pylabrobot.resources.corning import cor_96_wellplate_360uL_Fb
from pylabrobot.resources.hamilton import (
  STARLetDeck,
  hamilton_96_tiprack_300uL,
  hamilton_plate_carrier_L5_ac,
  hamilton_tip_carrier_L5,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent


class Bench:
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack,
  with an event bus whose events are recorded step by step."""

  def __init__(self) -> None:
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      self.deck: Resource = STARLetDeck(
        name="deck",
        with_trash96=False,
        with_teaching_needle_rack=False,
        core_grippers=None,
      )
      self.plate_carrier: PlateCarrier = hamilton_plate_carrier_L5_ac(name="plate_carrier")
      self.plate: Plate = cor_96_wellplate_360uL_Fb(name="plate")
      self.plate_carrier[0] = self.plate
      self.deck.assign_child_resource(self.plate_carrier, track=1)
      tip_carrier = hamilton_tip_carrier_L5(name="tip_carrier")
      self.tips: TipRack = hamilton_96_tiprack_300uL(name="tips")
      tip_carrier[0] = self.tips
      self.deck.assign_child_resource(tip_carrier, track=8)
    self.bus = EventBus()
    self.events: List[PLREvent] = []
    self.bus.subscribe(self.events.append)
    self.operations: Dict[str, str] = {}
    self.steps: List[Dict[str, Any]] = []

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

  def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": snapshot_resources(self.deck)}


class EventsGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_tree_changes(self) -> None:
    bench = Bench()
    other = cor_96_wellplate_360uL_Fb(name="other_plate")

    def assign_other_plate() -> None:
      bench.plate_carrier[2] = other

    await bench.step("plate_carrier[2] = other_plate", assign_other_plate)
    await bench.step("other_plate.unassign()", other.unassign)

    def move_plate() -> None:
      bench.plate.unassign()
      bench.plate_carrier[1] = bench.plate

    await bench.step("plate.unassign(); plate_carrier[1] = plate", move_plate)
    await bench.step("plate.rotate(z=90)", lambda: bench.plate.rotate(z=90))

    def nudge_plate() -> None:
      bench.plate.location = Coordinate(1, 2, 3)

    await bench.step("plate.location = Coordinate(1, 2, 3)", nudge_plate)
    well = bench.plate.get_well("A1")
    await bench.step("resource_reference(plate['A1'])", lambda: resource_reference(well))
    check_golden(self, GOLDEN / "tree_changes.json", bench.record())

  async def test_state_changes(self) -> None:
    bench = Bench()
    well = bench.plate.get_well("A1")
    await bench.step("plate['A1'].tracker.set_volume(100)", lambda: well.tracker.set_volume(100))
    spot = bench.tips.get_item("A1")

    def take_tip() -> None:
      spot.unassign_tip()

    await bench.step("tips['A1'].unassign_tip()", take_tip)

    def put_tip_back() -> None:
      spot.assign_tip(spot.make_tip())

    await bench.step("tips['A1'].assign_tip(tips['A1'].make_tip())", put_tip_back)
    await bench.step(
      "plate.set_well_volumes([50] * 96)", lambda: bench.plate.set_well_volumes([50] * 96)
    )

    def take_every_tip() -> None:
      for item in bench.tips.get_all_items():
        if item.tip is not None:
          item.unassign_tip()

    await bench.step("unassign_tip() on every spot holding one", take_every_tip)
    check_golden(self, GOLDEN / "state_changes.json", bench.record())

  async def test_operations(self) -> None:
    bench = Bench()
    other = cor_96_wellplate_360uL_Fb(name="other_plate")

    def move_in_operation() -> None:
      with event_operation("carrier.load", plate=resource_reference(other), site=2):
        bench.plate_carrier[2] = other
        emit_event("carrier.loaded", site=2)

    await bench.step("event_operation('carrier.load') around an assignment", move_in_operation)

    def completed_with_final_state() -> None:
      with event_operation(
        "plate.fill",
        completed_data_factory=lambda: {"volume": well.tracker.get_used_volume()},
        well=resource_reference(well),
      ):
        well.tracker.set_volume(20)

    well = bench.plate.get_well("B2")
    await bench.step(
      "event_operation('plate.fill', completed_data_factory=...)", completed_with_final_state
    )

    def failing_operation() -> None:
      with event_operation("carrier.unload", plate=resource_reference(other)):
        other.unassign()
        raise RuntimeError("gripper lost the plate")

    await bench.step("event_operation('carrier.unload') that raises", failing_operation)

    @evented_operation(
      "plate.rotate", lambda plate, z: {"plate": resource_reference(plate), "z": z}
    )
    async def rotate(plate: Plate, z: float) -> str:
      plate.rotate(z=z)
      emit_event("plate.rotated", z=z)
      return plate.name

    await bench.step(
      "evented_operation('plate.rotate')(plate, z=180)", lambda: rotate(bench.plate, z=180)
    )
    check_golden(self, GOLDEN / "operations.json", bench.record())


if __name__ == "__main__":
  unittest.main()
