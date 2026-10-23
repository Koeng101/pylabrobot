"""Golden tests of what the 2D visualizer sends its browser for each kind of change to the tree.

The seam is the websocket: the visualizer is given the test's event loop and a fake connection
that records every message it is sent, so no server, socket or browser is started.
"""

import asyncio
import json
import pathlib
import unittest
import warnings
from typing import Any, Callable, Dict, List

from pylabrobot.resources import Coordinate, Plate, PlateCarrier, Resource, TipRack
from pylabrobot.resources.corning import cor_96_wellplate_360uL_Fb
from pylabrobot.resources.hamilton import (
  STARLetDeck,
  hamilton_96_tiprack_300uL,
  hamilton_plate_carrier_L5_ac,
  hamilton_tip_carrier_L5,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources
from pylabrobot.visualizer import Visualizer

GOLDEN = pathlib.Path(__file__).parent


class RecordingSocket:
  """Stands in for the browser's websocket: keeps every message the visualizer sends it."""

  def __init__(self) -> None:
    self.sent: List[str] = []

  async def send(self, message: str) -> None:
    self.sent.append(message)


def normalized(message: str) -> Dict[str, Any]:
  """A sent message as JSON, with what does not describe the tree replaced by placeholders.

  The format version is the package's, and each class's method signatures come from Python
  reflection on the class: both change with code unrelated to what the tree did.
  """
  data: Dict[str, Any] = json.loads(message)
  data["version"] = "<version>"
  registry = data["data"].get("method_registry")
  if isinstance(registry, dict):
    data["data"]["method_registry"] = {type_name: "<methods>" for type_name in registry}
  return data


class Bench:
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack,
  watched by a 2D visualizer whose messages are recorded step by step."""

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
    self.socket = RecordingSocket()
    self.visualizer = Visualizer(self.deck, open_browser=False, name="golden")
    self.steps: List[Dict[str, Any]] = []

  async def attach(self) -> None:
    """Hand the visualizer this loop and the recording socket, as a browser saying "ready" does."""
    self.visualizer._loop = asyncio.get_running_loop()
    self.visualizer._websocket = self.socket  # type: ignore[assignment]

  async def step(self, call: str, action: Callable[[], Any], resources: bool = True) -> None:
    """Run `action`, let the visualizer send what it sends, and record it under `call`."""
    before = len(self.socket.sent)
    result = action()
    if asyncio.iscoroutine(result):
      await result
    # Sends are scheduled on the loop: a few turns let every one of them run.
    for _ in range(10):
      await asyncio.sleep(0)
    entry: Dict[str, Any] = {
      "call": call,
      "sent": [normalized(message) for message in self.socket.sent[before:]],
    }
    if resources:
      entry["resources"] = snapshot_resources(self.deck)
    self.steps.append(entry)

  def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": snapshot_resources(self.deck)}


class VisualizerGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.bench = Bench()
    await self.bench.attach()

  async def test_initial_scene(self) -> None:
    bench = self.bench
    await bench.step("browser ready", bench.visualizer._send_resources_and_state, resources=False)
    check_golden(self, GOLDEN / "initial_scene.json", bench.record())

  async def test_tree_changes(self) -> None:
    bench = self.bench
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
    check_golden(self, GOLDEN / "tree_changes.json", bench.record())

  async def test_state_changes(self) -> None:
    bench = self.bench
    well = bench.plate.get_well("A1")
    await bench.step("plate['A1'].tracker.set_volume(100)", lambda: well.tracker.set_volume(100))
    spot = bench.tips.get_item("A1")
    await bench.step("tips['A1'].unassign_tip()", spot.unassign_tip)
    await bench.step(
      "plate.set_well_volumes([50] * 96)", lambda: bench.plate.set_well_volumes([50] * 96)
    )

    def take_every_tip() -> None:
      for item in bench.tips.get_all_items():
        if item.tip is not None:
          item.unassign_tip()

    await bench.step("unassign_tip() on every spot still holding one", take_every_tip)
    check_golden(self, GOLDEN / "state_changes.json", bench.record())


if __name__ == "__main__":
  unittest.main()
