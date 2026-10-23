"""Golden tests of what the 3D viewer sends a client for each kind of change to the tree.

The seam is the client connection: the viewer is given the test's event loop and a fake client
that records every message, greeted by the viewer's own connection handler. No server, socket or
browser is started.
"""

import asyncio
import base64
import json
import pathlib
import struct
import unittest
from typing import Any, Callable, Dict, List, Optional

from pylabrobot.events.golden.events_golden_tests import build_bench, move_to
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.testing.golden import check_golden, snapshot_store
from pylabrobot.visualizer3D import Viewer3D

GOLDEN = pathlib.Path(__file__).parent


class RecordingClient:
  """Stands in for a page's websocket: keeps every message, and stays open until closed."""

  def __init__(self) -> None:
    self.sent: List[str] = []
    self.closed = asyncio.Event()

  async def send(self, message: str) -> None:
    self.sent.append(message)

  def __aiter__(self) -> "RecordingClient":
    return self

  async def __anext__(self) -> str:
    await self.closed.wait()
    raise StopAsyncIteration


class Normalizer:
  """Sent messages as JSON, with what does not describe the tree replaced by placeholders.

  - A mesh is served under a random id per run: each id becomes `mesh/<n>`, numbered by first use.
  - Each model's `methods` come from Python reflection on its class, and the scene's byte counts
    measure the whole message including them: both change with code unrelated to the tree.
  - Transforms are base64 float32 on the wire; they are recorded as the numbers they hold.
  """

  def __init__(self) -> None:
    self.meshes: Dict[str, str] = {}

  def _scene(self, data: Dict[str, Any]) -> None:
    for model in data.get("models", []):
      if "methods" in model:
        model["methods"] = "<methods>"
      mesh = model.get("mesh")
      if isinstance(mesh, dict) and "url" in mesh:
        mesh["url"] = self.meshes.setdefault(mesh["url"], f"mesh/{len(self.meshes)}")
    instances = data.get("instances")
    if isinstance(instances, dict) and isinstance(instances.get("transforms"), str):
      packed = base64.b64decode(instances["transforms"])
      instances["transforms"] = list(struct.unpack(f"<{len(packed) // 4}f", packed))
    stats = data.get("stats")
    if isinstance(stats, dict):
      stats["scene_bytes"] = "<bytes>"
      stats["ratio"] = "<ratio>"

  def __call__(self, message: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = json.loads(message)
    if parsed["event"] == "scene":
      self._scene(parsed["data"])
    return parsed


class Bench:
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack, in a
  resource store, watched by a 3D viewer whose messages to one client are recorded step by step."""

  def __init__(self) -> None:
    self.store = ResourceStore.in_memory()
    self.client = RecordingClient()
    self.normalize = Normalizer()
    self.handler: Optional["asyncio.Future[None]"] = None
    self.steps: List[Dict[str, Any]] = []

  async def build(self) -> None:
    built = await build_bench(self.store)
    self.deck = built["deck"]
    plate_carrier, plate, tips = built["plate_carrier"], built["plate"], built["tips"]
    assert isinstance(plate_carrier, handles.Carrier)
    assert isinstance(plate, handles.Plate) and isinstance(tips, handles.TipRack)
    self.plate_carrier, self.plate, self.tips = plate_carrier, plate, tips
    self.viewer = Viewer3D(self.deck, open_browser=False, name="golden")

  async def settle(self) -> None:
    """Let the viewer send what it sends: scene changes wait out a debounce, the rest a turn."""
    await self.viewer.caught_up(30)
    for _ in range(5):
      await asyncio.sleep(0)
    await asyncio.sleep(Viewer3D.SCENE_DEBOUNCE_S * 2)
    for _ in range(5):
      await asyncio.sleep(0)

  async def step(self, call: str, action: Callable[[], Any]) -> None:
    """Run `action`, let the viewer send what it sends, and record it under `call`."""
    before = len(self.client.sent)
    result = action()
    if asyncio.iscoroutine(result):
      await result
    await self.settle()
    self.steps.append(
      {"call": call, "sent": [self.normalize(m) for m in self.client.sent[before:]]}
    )

  async def connect(self) -> None:
    """Give the viewer this loop, as `start` does, have it follow the store, and connect the
    recording client."""

    async def greet() -> None:
      self.viewer._loop = asyncio.get_running_loop()
      await self.viewer.follow()
      self.handler = asyncio.ensure_future(self.viewer._handler(self.client))  # type: ignore[arg-type]

    await self.step("client connects", greet)

  async def close(self) -> None:
    self.client.closed.set()
    if self.handler is not None:
      await self.handler
    await self.viewer.stop()
    await self.store.close()

  async def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": await snapshot_store(self.store, self.deck)}


class Viewer3DGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.bench = Bench()
    await self.bench.build()
    await self.bench.connect()

  async def asyncTearDown(self) -> None:
    await self.bench.close()

  async def test_initial_scene(self) -> None:
    check_golden(self, GOLDEN / "initial_scene.json", await self.bench.record())

  async def test_tree_changes(self) -> None:
    bench = self.bench
    other = await bench.store.create("cor_96_wellplate_360uL_Fb", name="other_plate")

    await bench.step(
      "plate_carrier[2] = other_plate",
      lambda: bench.plate_carrier[2].assign_child_resource(other),
    )
    await bench.step("other_plate.unassign()", other.unassign)

    # Out of one site and into the other in one request, as PLR's two calls did in one breath:
    # the viewer coalesces what arrives within its debounce, and two requests may not.
    await bench.step(
      "plate.unassign(); plate_carrier[1] = plate",
      lambda: bench.plate_carrier[1].assign_child_resource(bench.plate),
    )
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
