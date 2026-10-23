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
import warnings
from typing import Any, Callable, Dict, List, Optional

from pylabrobot.resources import Coordinate, Plate, PlateCarrier, Resource, TipRack
from pylabrobot.resources.corning import cor_96_wellplate_360uL_Fb
from pylabrobot.resources.hamilton import (
  STARLetDeck,
  hamilton_96_tiprack_300uL,
  hamilton_plate_carrier_L5_ac,
  hamilton_tip_carrier_L5,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources
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
  """A STARlet deck with a plate carrier holding a plate and a tip carrier holding a tip rack,
  watched by a 3D viewer whose messages to one client are recorded step by step."""

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
    self.viewer = Viewer3D(self.deck, open_browser=False, name="golden")
    self.client = RecordingClient()
    self.normalize = Normalizer()
    self.handler: Optional["asyncio.Future[None]"] = None
    self.steps: List[Dict[str, Any]] = []

  async def settle(self) -> None:
    """Let the viewer send what it sends: scene changes wait out a debounce, the rest a turn."""
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
    """Give the viewer this loop, as `start` does, and connect the recording client."""

    async def greet() -> None:
      self.viewer._loop = asyncio.get_running_loop()
      self.handler = asyncio.ensure_future(self.viewer._handler(self.client))  # type: ignore[arg-type]

    await self.step("client connects", greet)

  async def close(self) -> None:
    self.client.closed.set()
    if self.handler is not None:
      await self.handler
    await self.viewer.stop()

  def record(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": snapshot_resources(self.deck)}


class Viewer3DGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.bench = Bench()
    await self.bench.connect()

  async def asyncTearDown(self) -> None:
    await self.bench.close()

  async def test_initial_scene(self) -> None:
    check_golden(self, GOLDEN / "initial_scene.json", self.bench.record())

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
