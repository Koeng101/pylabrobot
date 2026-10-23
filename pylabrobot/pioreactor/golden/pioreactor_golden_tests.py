"""Golden tests of what the Pioreactor does today.

The Pioreactor sends no commands: it is a resource holding one culture vessel. These scenarios pin
its tree, where the vessel sits, what it accepts, and the vessel's volume as liquid is tracked.
"""

from __future__ import annotations

import pathlib
import unittest
from typing import Any, Callable, Dict, List

from pylabrobot.pioreactor.bioreactors import Pioreactor, pioreactor_20ml
from pylabrobot.resources import Container, Coordinate, Resource, Tube
from pylabrobot.testing.golden import check_golden, snapshot_resources

GOLDEN = pathlib.Path(__file__).parent


class Recorder:
  """Records each step's result or error, with the Pioreactor's tree after it."""

  def __init__(self, root: Resource) -> None:
    self.root = root
    self.steps: List[Dict[str, Any]] = []

  def step(self, call: str, action: Callable[[], Any]) -> None:
    entry: Dict[str, Any] = {"call": call}
    try:
      entry["result"] = action()
    except Exception as error:
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["resources"] = snapshot_resources(self.root)
    self.steps.append(entry)

  def finish(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": snapshot_resources(self.root)}


def describe(resource: Resource) -> Dict[str, Any]:
  return {
    "model": resource.model,
    "category": resource.category,
    "size": [resource.get_size_x(), resource.get_size_y(), resource.get_size_z()],
  }


class PioreactorGoldenTests(unittest.TestCase):
  def test_pioreactor_20ml(self):
    """The 20 mL Pioreactor's tree and its vessel."""
    pioreactor = pioreactor_20ml("pioreactor")
    vessel = pioreactor.vessel
    record = {
      "pioreactor": describe(pioreactor),
      "vessel": {
        **describe(vessel),
        "max_volume": vessel.max_volume,
        "material_z_thickness": vessel.material_z_thickness,
        "absolute_location": [
          vessel.get_absolute_location().x,
          vessel.get_absolute_location().y,
          vessel.get_absolute_location().z,
        ],
      },
      "resources": snapshot_resources(pioreactor),
    }
    check_golden(self, GOLDEN / "pioreactor_20ml.json", record)

  def test_vessels_it_accepts(self):
    """It holds one container; anything else, or a second vessel, is refused."""
    pioreactor = Pioreactor(name="pioreactor", size_x=127.74, size_y=85.4, size_z=126.5)
    rig = Recorder(pioreactor)
    vessel = Container(name="vessel", size_x=23.5, size_y=23.5, size_z=57, max_volume=20_000)
    tube = Tube(name="tube", size_x=23.5, size_y=23.5, size_z=57, max_volume=20_000)
    block = Resource(name="block", size_x=10, size_y=10, size_z=10)

    rig.step("pioreactor.vessel", lambda: pioreactor.vessel.name)
    rig.step(
      "pioreactor.assign_child_resource(block, Coordinate(0, 0, 0))",
      lambda: pioreactor.assign_child_resource(block, Coordinate(0, 0, 0)),
    )
    rig.step(
      "pioreactor.assign_child_resource(vessel, Coordinate(52.12, 30.95, 76))",
      lambda: pioreactor.assign_child_resource(vessel, Coordinate(52.12, 30.95, 76)),
    )
    rig.step("pioreactor.vessel", lambda: pioreactor.vessel.name)
    rig.step(
      "pioreactor.assign_child_resource(tube, Coordinate(0, 0, 0))",
      lambda: pioreactor.assign_child_resource(tube, Coordinate(0, 0, 0)),
    )
    rig.step(
      "pioreactor.unassign_child_resource(vessel)",
      lambda: pioreactor.unassign_child_resource(vessel),
    )
    rig.step(
      "pioreactor.assign_child_resource(tube, Coordinate(52.12, 30.95, 76))",
      lambda: pioreactor.assign_child_resource(tube, Coordinate(52.12, 30.95, 76)),
    )
    rig.step("pioreactor.vessel", lambda: pioreactor.vessel.name)
    check_golden(self, GOLDEN / "vessels_it_accepts.json", rig.finish())

  def test_culture_volume(self):
    """Medium added to and sampled from the vessel is tracked on it."""
    pioreactor = pioreactor_20ml("pioreactor")
    rig = Recorder(pioreactor)
    tracker = pioreactor.vessel.tracker

    def add_medium() -> None:
      tracker.add_liquid(15_000)
      tracker.commit()

    def take_sample() -> None:
      tracker.remove_liquid(1_000)
      tracker.commit()

    def overfill() -> None:
      tracker.add_liquid(10_000)
      tracker.commit()

    rig.step("vessel.tracker.add_liquid(15000)", add_medium)
    rig.step("vessel.tracker.remove_liquid(1000)", take_sample)
    rig.step("vessel.tracker.add_liquid(10000)", overfill)
    rig.step("vessel.tracker.get_used_volume()", tracker.get_used_volume)
    check_golden(self, GOLDEN / "culture_volume.json", rig.finish())


if __name__ == "__main__":
  unittest.main()
