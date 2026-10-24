"""Golden tests of what the 2D visualizer sends its browser for each kind of change to the tree.

The seam is the websocket: the visualizer is given the test's event loop and a fake connection
that records every message it is sent, so no server, socket or browser is started.
"""

import asyncio
import json
import pathlib
import unittest
from typing import Any, Dict, List

from pylabrobot.events.golden.events_golden_tests import build_bench, move_to
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store
from pylabrobot.visualizer import Visualizer

GOLDEN = pathlib.Path(__file__).parent


class RecordingSocket:
  """Stands in for the browser's websocket: keeps every message the visualizer sends it."""

  def __init__(self, sent: List[str]) -> None:
    self.sent = sent

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


class Bench(recording.Recorder):
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack, in a
  resource store, watched by a 2D visualizer whose messages are recorded step by step."""

  def __init__(self) -> None:
    super().__init__()
    self.store = ResourceStore.in_memory()
    self.socket = RecordingSocket(self.sent)

  async def build(self) -> None:
    built = await build_bench(self.store)
    self.deck = built["deck"]
    plate_carrier, plate, tips = built["plate_carrier"], built["plate"], built["tips"]
    assert isinstance(plate_carrier, handles.Carrier)
    assert isinstance(plate, handles.Plate) and isinstance(tips, handles.TipRack)
    self.plate_carrier, self.plate, self.tips = plate_carrier, plate, tips
    self.visualizer = Visualizer(self.deck, open_browser=False, name="golden")

  async def attach(self) -> None:
    """Hand the visualizer this loop and the recording socket, as a browser saying "ready" does,
    and have it follow the store."""
    self.visualizer._loop = asyncio.get_running_loop()
    self.visualizer._websocket = self.socket  # type: ignore[assignment]
    await self.visualizer.follow()

  async def step(  # type: ignore[override]
    self, call: str, action: recording.Action, resources: bool = True
  ) -> None:
    """Run `action`, let the visualizer send what it sends, and record it under `call`."""
    self.take_sent()
    await recording.run(action)
    await self.visualizer.caught_up()
    # Sends are scheduled on the loop: a few turns let every one of them run.
    for _ in range(10):
      await asyncio.sleep(0)
    entry: Dict[str, Any] = {
      "call": call,
      "sent": [normalized(message) for message in self.take_sent()],
    }
    if resources:
      entry["resources"] = await snapshot_store(self.store, self.deck)
    self.steps.append(entry)

  async def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": await snapshot_store(self.store, self.deck)}

  async def close(self) -> None:
    await self.visualizer._stop_following()
    await self.store.close()


class VisualizerGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.bench = Bench()
    await self.bench.build()
    await self.bench.attach()

  async def asyncTearDown(self) -> None:
    await self.bench.close()

  async def test_initial_scene(self) -> None:
    bench = self.bench
    await bench.step("browser ready", bench.visualizer._send_resources_and_state, resources=False)
    check_golden(self, GOLDEN / "initial_scene.json", await bench.record())

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
    check_golden(self, GOLDEN / "tree_changes.json", await bench.record())

  async def test_state_changes(self) -> None:
    bench = self.bench
    well = bench.plate.get_well("A1")
    await bench.step("plate['A1'].tracker.set_volume(100)", lambda: well.set_volume(100))
    all_but_a1 = [index != 0 for index in range(bench.tips.num_items)]
    await bench.step("tips['A1'].unassign_tip()", lambda: bench.tips.set_tip_state(all_but_a1))
    await bench.step(
      "plate.set_well_volumes([50] * 96)", lambda: bench.plate.set_well_volumes([50] * 96)
    )
    await bench.step("unassign_tip() on every spot still holding one", bench.tips.empty)
    check_golden(self, GOLDEN / "state_changes.json", await bench.record())


if __name__ == "__main__":
  unittest.main()
