"""The state channel: what a client is told, and what it is deliberately not told again."""

import asyncio
import contextlib
import hashlib
import io
import json
import os
import shutil
import socket
import tempfile
import threading
import unittest
import unittest.mock
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import websockets
from websockets.typing import Origin

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.visualizer3D.facility import facility
from pylabrobot.visualizer3D.server import Viewer3D


def free_ports(count: int) -> List[int]:
  """Distinct ports nothing on this machine listens on, so two suites can run at once."""
  sockets = [socket.socket() for _ in range(count)]
  try:
    for sock in sockets:
      sock.bind(("127.0.0.1", 0))
    return [sock.getsockname()[1] for sock in sockets]
  finally:
    for sock in sockets:
      sock.close()


async def empty_facility(store: Optional[ResourceStore] = None) -> handles.Resource:
  """A facility with nothing in it, of a size every test here can place things in, in a store of
  its own unless one is given."""
  store = store or ResourceStore.in_memory()
  return await store.create(facility("facility", 1000, 1000, 500), name="facility")


async def part(
  parent: handles.Resource,
  name: str,
  location: Coordinate = Coordinate.zero(),
  size: Coordinate = Coordinate(10, 10, 10),
  **definition: Any,
) -> handles.Resource:
  """A plain box put in `parent`; `definition` is what `build.resource` takes besides."""
  return await parent.store.create(
    build.resource(name, size, **definition), name=name, parent=parent, location=location
  )


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


def volumes(plate: handles.Plate, **by_identifier: float) -> List[float]:
  """Every well's volume for `set_well_volumes`: those named, and 0 for the rest."""
  return [by_identifier.get(identifier, 0.0) for identifier in plate.identifiers]


FS_PORT, WS_PORT = free_ports(2)
# Any model file shipped with the package: what it draws does not matter, that it registers does.
MESH_FILE = os.path.join(
  os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
  "hamilton",
  "star",
  "resource_model",
  "starlet_base.glb",
)


class StateChannelTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.facility = await empty_facility()
    self.store = self.facility.store
    plate = await self.store.create(
      "cor_96_wellplate_360uL_Fb",
      name="plate",
      parent=self.facility,
      location=Coordinate(10, 10, 0),
    )
    assert isinstance(plate, handles.Plate)
    self.plate = plate
    self.viewer = Viewer3D(
      self.facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT, name="tests"
    )
    await self.viewer.start()

  async def asyncTearDown(self):
    await self.viewer.stop()
    await self.store.close()

  async def rack(self) -> handles.TipRack:
    """A rack full of tips, beside the plate."""
    rack = await self.store.create(
      "hamilton_96_tiprack_1000uL",
      name="rack",
      parent=self.facility,
      location=Coordinate(300, 10, 0),
    )
    assert isinstance(rack, handles.TipRack)
    return rack

  async def connect(self):
    """Open a client and take the scene and the snapshot it is greeted with."""
    ws = await websockets.connect(self.viewer.ws_url, max_size=None)
    scene = json.loads(await ws.recv())["data"]
    snapshot = json.loads(await ws.recv())["data"]
    return ws, scene, snapshot

  async def next_state(self, ws, timeout: float = 2.0):
    """The next state message, or None if the server stayed quiet."""
    try:
      while True:
        message = json.loads(await asyncio.wait_for(ws.recv(), timeout))
        if message["event"] == "state":
          return message["data"]
    except asyncio.TimeoutError:
      return None

  async def test_snapshot_names_every_publishing_resource(self):
    ws, scene, snapshot = await self.connect()
    try:
      self.assertIn("plate_well_A1", snapshot["of"])
      self.assertEqual(len(snapshot["of"]), 96)  # the wells; the plate itself publishes nothing
      self.assertIn("plate_well_A1", scene["instances"]["names"])
    finally:
      await ws.close()

  async def test_snapshot_leaves_out_locations(self):
    """The scene sent immediately before already places everything, and a position is unique to one
    resource, so carrying it here would give every resource a state of its own."""
    ws, _, snapshot = await self.connect()
    try:
      self.assertEqual(snapshot["locations"], {})
      self.assertEqual(len(snapshot["states"]), 1)  # every empty well; the plate publishes nothing
    finally:
      await ws.close()

  async def test_full_tip_spots_share_one_state(self):
    """A spot's state embeds its tip, and the tip names the spot. That is identity, not state: a
    rack of the same tip is one state on the wire, not ninety-six."""
    rack = await self.rack()
    await self.viewer.caught_up(30)
    ws, _, snapshot = await self.connect()
    try:
      spots = [spot.name for spot in rack.items]
      self.assertEqual(len({snapshot["of"][name] for name in spots}), 1)
      self.assertEqual(len(snapshot["states"]), 3)  # the wells, the spots and the tips
    finally:
      await ws.close()

  async def test_a_tip_in_a_rack_is_greeted_with_what_it_holds(self):
    """The info panel reads a tip's `volume` and `max_volume` from its state, so a client is
    greeted with both."""
    rack = await self.rack()
    tip = await rack.get_tip_spot("A1").get_tip()
    assert tip is not None
    await tip.set_volume(30.0)
    await self.viewer.caught_up(30)
    ws, _, snapshot = await self.connect()
    try:
      state = snapshot["states"][snapshot["of"][tip.name]]
      self.assertEqual(state["volume"], 30.0)
      self.assertEqual(state["max_volume"], (await tip.attributes()).tip.maximal_volume)
    finally:
      await ws.close()

  async def test_a_tip_publishes_what_it_holds(self):
    """A tip's tracker was never published, so the channel panel drew every tip empty."""
    rack = await self.rack()
    tip = await rack.get_tip_spot("A1").get_tip()
    assert tip is not None
    await self.viewer.caught_up(30)
    ws, _, _ = await self.connect()
    try:
      await tip.set_volume(12.5)
      update = await self.next_state(ws)
      self.assertIsNotNone(update)
      self.assertEqual(update["states"][update["of"][tip.name]]["volume"], 12.5)
    finally:
      await ws.close()

  async def test_a_change_names_only_what_changed(self):
    ws, _, _ = await self.connect()
    try:
      await self.plate.get_well("A1").set_volume(150.0)
      update = await self.next_state(ws)
      self.assertIsNotNone(update)
      self.assertEqual(list(update["of"]), ["plate_well_A1"])
    finally:
      await ws.close()

  async def test_a_filled_well_is_not_a_move(self):
    """Every state carries the resource's position, so a well whose volume changed was reported
    as moved: three quarters of a plate fill was positions, and every later snapshot repeated
    them."""
    first, _, _ = await self.connect()
    try:
      await self.plate.set_well_volumes(100.0)
      update = await self.next_state(first)
      self.assertIsNotNone(update)
      self.assertEqual(len(update["of"]), 96)
      self.assertEqual(update["locations"], {})
      second, _, snapshot = await self.connect()
      try:
        self.assertEqual(snapshot["locations"], {})
      finally:
        await second.close()
    finally:
      await first.close()

  async def test_an_unchanged_value_is_not_sent_again(self):
    ws, _, _ = await self.connect()
    try:
      await self.plate.get_well("A1").set_volume(150.0)
      self.assertIsNotNone(await self.next_state(ws))
      # A sentinel changed in the same batch: the message it arrives in is the one A1 would be in.
      await self.plate.set_well_volumes(volumes(self.plate, A1=150.0, B1=10.0))
      update = await self.next_state(ws)
      self.assertIsNotNone(update)
      self.assertEqual(list(update["of"]), ["plate_well_B1"])
    finally:
      await ws.close()

  async def test_a_change_too_small_to_see_is_not_sent(self):
    """State is rounded to what a viewer can show, so a hundredth of a microlitre is not news."""
    ws, _, _ = await self.connect()
    try:
      await self.plate.get_well("A1").set_volume(150.0)
      self.assertIsNotNone(await self.next_state(ws))
      await self.plate.set_well_volumes(volumes(self.plate, A1=150.04, B1=10.0))
      update = await self.next_state(ws)
      self.assertIsNotNone(update)
      self.assertEqual(list(update["of"]), ["plate_well_B1"])
    finally:
      await ws.close()

  async def test_a_discarded_resource_is_no_longer_listened_to(self):
    """A resource taken out of the tree kept its callback, so a discarded plate's every tracker
    change was still serialized and queued for a viewer that could never draw it."""
    kept = await self.store.create(
      "cor_96_wellplate_360uL_Fb",
      name="kept",
      parent=self.facility,
      location=Coordinate(300, 10, 0),
    )
    assert isinstance(kept, handles.Plate)
    await self.viewer.caught_up(30)
    ws, _, _ = await self.connect()
    try:
      await self.plate.unassign()
      await self.next_of(ws, "scene")
      self.assertIsNotNone(await self.next_state(ws))  # the snapshot after the rebuild
      self.assertNotIn(self.plate.get_well("A1").id, self.viewer._subscribed)
      await self.plate.get_well("A1").set_volume(150.0)
      await kept.get_well("A1").set_volume(150.0)
      update = await self.next_state(ws)
      self.assertIsNotNone(update)
      self.assertEqual(list(update["of"]), ["kept_well_A1"])
    finally:
      await ws.close()

  async def test_a_second_client_is_told_everything(self):
    """Suppression is about what one client has seen. A client that has seen nothing gets it all,
    however much the others have already been told."""
    first, _, _ = await self.connect()
    try:
      await self.plate.get_well("A1").set_volume(150.0)
      await self.next_state(first)
      second, _, snapshot = await self.connect()
      try:
        self.assertEqual(len(snapshot["of"]), 96)
      finally:
        await second.close()
    finally:
      await first.close()

  async def test_a_moved_resource_publishes_its_new_position(self):
    """Position reaches a subscriber the same way rotation always has."""
    ws, _, _ = await self.connect()
    try:
      await move_to(self.plate, Coordinate(400, 300, 0))
      update = await self.next_state(ws)
      self.assertIsNotNone(update)
      self.assertIn("plate", update["of"])
      self.assertEqual(update["locations"]["plate"]["x"], 400)
    finally:
      await ws.close()

  async def test_a_resource_moved_under_another_parent_is_moved_not_rebuilt(self):
    """The same names are the same instances: a change of parent is a move, a parent index and six
    floats, applied to the scene the client has. Its new location travels in the move and in no
    state before it, which would be read against the old parent."""
    holder = await part(
      self.facility, "holder", Coordinate(500, 500, 0), size=Coordinate(200, 200, 50)
    )
    # The holder is in the scene a client is greeted with, and the flush its assignment scheduled
    # finds nothing moved since, so it sends nothing: a rebuild was the old behaviour there too.
    await self.viewer.caught_up(30)
    ws, _, _ = await self.connect()
    try:
      await holder.assign_child_resource(self.plate, location=Coordinate(5, 5, 50))
      states, moves = await self.next_of(ws, "moves")
      for state in states:
        self.assertNotIn("plate", state.get("locations", {}), state)
      moved = {move["name"]: move for move in moves["moves"]}
      self.assertIn("plate", moved)
      self.assertEqual(moved["plate"]["parent"], "holder")
      self.assertEqual(moved["plate"]["location"], {"x": 5.0, "y": 5.0, "z": 50.0})
      self.assertEqual(self.viewer.rebuilds, 0)
    finally:
      await ws.close()

  async def test_a_client_arriving_after_a_move_sees_it_in_the_scene(self):
    """The kept scene is moved along with the clients', so a late client is handed it as it stands."""
    holder = await part(
      self.facility, "holder", Coordinate(500, 500, 0), size=Coordinate(200, 200, 50)
    )
    await self.viewer.caught_up(30)
    first, _, _ = await self.connect()
    try:
      await holder.assign_child_resource(self.plate, location=Coordinate(5, 5, 50))
      await self.next_of(first, "moves")
      second, scene, _ = await self.connect()
      try:
        names = scene["instances"]["names"]
        self.assertEqual(names[scene["instances"]["parent"][names.index("plate")]], "holder")
      finally:
        await second.close()
    finally:
      await first.close()

  async def next_of(self, ws, event: str, timeout: float = 2.0):
    """The state messages that arrive before the next message of `event`, and that message."""
    states: List[Dict[str, Any]] = []
    while True:
      message = json.loads(await asyncio.wait_for(ws.recv(), timeout))
      if message["event"] == event:
        return states, message["data"]
      if message["event"] == "state":
        states.append(message["data"])


class StagedAspirateTests(unittest.IsolatedAsyncioTestCase):
  """A mounted tip's liquid while an aspirate is staged, as the info panel reads it: committed."""

  async def asyncSetUp(self):
    self.facility = await empty_facility()
    self.store = self.facility.store
    source = await self.store.create(
      "cor_96_wellplate_360uL_Fb",
      name="source",
      parent=self.facility,
      location=Coordinate(10, 10, 0),
    )
    rack = await self.store.create(
      "hamilton_96_tiprack_1000uL",
      name="tips",
      parent=self.facility,
      location=Coordinate(300, 10, 0),
    )
    self.shaft = await part(
      self.facility,
      "shaft",
      Coordinate(500, 500, 300),
      size=Coordinate(8, 8, 50),
      kind=pb.RESOURCE_KIND_TIP_MOUNTING_SHAFT,
    )
    assert isinstance(source, handles.Plate) and isinstance(rack, handles.TipRack)
    self.well = source.get_well("A1")
    await self.well.set_volume(200.0)
    self.rack = rack
    fs_port, ws_port = free_ports(2)
    self.viewer = Viewer3D(self.facility, open_browser=False, fs_port=fs_port, ws_port=ws_port)
    await self.viewer.start()
    self.addAsyncCleanup(self.store.close)
    self.addAsyncCleanup(self.viewer.stop)

  async def told(self, ws, name: str, quiet: float = 0.5) -> List[Dict[str, Any]]:
    """Every state a client is told for `name` until the server stays quiet for `quiet` s."""
    told: List[Dict[str, Any]] = []
    try:
      while True:
        message = json.loads(await asyncio.wait_for(ws.recv(), quiet))
        data = message["data"]
        if message["event"] == "state" and name in data["of"]:
          told.append(data["states"][data["of"][name]])
    except asyncio.TimeoutError:
      return told

  async def aspirate_staged(self, ws) -> Tuple[str, List[Dict[str, Any]], pb.Operation]:
    """Mount a tip and stage an aspirate of 50 uL into it, as a driver does before its command.

    Returns the tip's name, what the client was told of it while staged, and the operation.
    """
    commands = self.store.commands
    pickup = await commands.begin_tool_pickup(
      spb.BeginToolPickupRequest(
        frame=self.facility.ref,
        items=[spb.ToolPickupItem(source=self.rack.get_tip_spot("A1").ref, shaft=self.shaft.ref)],
      )
    )
    await commands.resolve_operation(
      spb.ResolveOperationRequest(
        operation_id=pickup.operation.id, outcomes=[spb.ItemOutcome(item=0, succeeded=True)]
      )
    )
    tip = pickup.items[0].tool.attributes.name
    await self.told(ws, tip)  # the pick-up's scene and snapshot
    transfer = await commands.begin_liquid_transfer(
      spb.BeginLiquidTransferRequest(
        frame=self.facility.ref,
        direction=spb.TRANSFER_DIRECTION_ASPIRATE,
        items=[spb.TransferItem(container=self.well.ref, shaft=self.shaft.ref, volume=50.0)],
      )
    )
    return tip, await self.told(ws, tip), transfer.operation

  async def resolve(self, operation: pb.Operation, succeeded: bool) -> None:
    await self.store.commands.resolve_operation(
      spb.ResolveOperationRequest(
        operation_id=operation.id, outcomes=[spb.ItemOutcome(item=0, succeeded=succeeded)]
      )
    )

  async def test_a_mounted_tip_is_told_its_committed_volume(self):
    """While the command runs the tip's booking is pending, and the page shows `volume`: it
    reads the new volume only once the command is done."""
    ws = await websockets.connect(self.viewer.ws_url, max_size=None)
    try:
      tip, during, operation = await self.aspirate_staged(ws)
      await self.resolve(operation, succeeded=True)
      after = await self.told(ws, tip)
    finally:
      await ws.close()
    self.assertEqual([(s["volume"], s["pending_volume"]) for s in during], [(0, 50.0)])
    self.assertEqual([s["volume"] for s in after], [50.0])

  async def test_a_failed_aspirate_leaves_a_mounted_tip_told_what_it_held(self):
    """A failed command rolls the tip's booking back, and the client is told it was: the last
    state it has for the tip is the committed one, pending included."""
    ws = await websockets.connect(self.viewer.ws_url, max_size=None)
    try:
      tip, during, operation = await self.aspirate_staged(ws)
      await self.resolve(operation, succeeded=False)
      after = await self.told(ws, tip)
    finally:
      await ws.close()
    self.assertGreater(during[-1]["pending_volume"], 0)
    self.assertEqual([s["volume"] for s in during + after], [0] * len(during + after))
    self.assertTrue(after, "the rollback told the client nothing")
    self.assertEqual((after[-1]["volume"], after[-1]["pending_volume"]), (0, 0))


class FileServerTests(unittest.IsolatedAsyncioTestCase):
  """The file server keeps quiet about what is not its fault."""

  async def asyncSetUp(self):
    self.facility = await empty_facility()
    self.viewer = Viewer3D(self.facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await self.viewer.start()

  async def asyncTearDown(self):
    await self.viewer.stop()
    await self.facility.store.close()

  async def test_static_files_are_kept_and_revalidated_while_the_page_is_not(self):
    """Every response said `no-store`, so a browser fetched three megabytes of scripts and
    models on every reload. The page carries this run's token and stays uncached; the rest is
    revalidated, and an unchanged file is answered 304 with no body."""
    base = f"http://127.0.0.1:{self.viewer.fs_port}"
    page = await asyncio.to_thread(urllib.request.urlopen, f"{base}/")
    self.assertEqual(page.headers["Cache-Control"], "no-store")
    script = await asyncio.to_thread(urllib.request.urlopen, f"{base}/vendor/three.core.min.js")
    self.assertEqual(script.headers["Cache-Control"], "no-cache")
    again = urllib.request.Request(
      f"{base}/vendor/three.core.min.js",
      headers={"If-Modified-Since": script.headers["Last-Modified"]},
    )
    with self.assertRaises(urllib.error.HTTPError) as unchanged:
      await asyncio.to_thread(urllib.request.urlopen, again)
    self.assertEqual(unchanged.exception.code, 304)

  async def test_the_name_in_the_header_is_text_not_markup(self):
    fs_port, ws_port = free_ports(2)
    viewer = Viewer3D(
      await empty_facility(),
      open_browser=False,
      fs_port=fs_port,
      ws_port=ws_port,
      name="<b>run</b>",
    )
    await viewer.start()
    try:
      page = await asyncio.to_thread(
        lambda: urllib.request.urlopen(f"http://127.0.0.1:{viewer.fs_port}/").read().decode()
      )
    finally:
      await viewer.stop()
    self.assertIn("&lt;b&gt;run&lt;/b&gt;", page)
    self.assertNotIn("<b>run</b>", page)

  async def test_an_idle_connection_is_closed(self):
    """Keep-alive with no timeout held a thread per connection for as long as the other end liked:
    two hundred idle sockets were two hundred threads."""
    fs_port, ws_port = free_ports(2)
    viewer = Viewer3D(await empty_facility(), open_browser=False, fs_port=fs_port, ws_port=ws_port)
    viewer.FS_TIMEOUT_S = 0.2
    await viewer.start()

    def idle() -> bytes:
      with socket.create_connection(("127.0.0.1", viewer.fs_port)) as sock:
        sock.settimeout(5)
        return sock.recv(1)  # nothing is sent, so only the server closing returns

    try:
      self.assertEqual(await asyncio.to_thread(idle), b"")
    finally:
      await viewer.stop()

  async def test_a_download_abandoned_by_the_browser_prints_no_traceback(self):
    """A page left mid-download closes its end of the socket, which the threaded server used to
    report as an exception in the request thread, a full traceback on every reload."""
    captured = io.StringIO()

    def abandon() -> None:
      with socket.create_connection(("127.0.0.1", self.viewer.fs_port)) as sock:
        sock.sendall(b"GET /vendor/three.webgpu.min.js HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        sock.recv(1024)  # the start of the body, then gone

    def request_threads() -> int:
      return sum(thread.name.startswith("Thread-") for thread in threading.enumerate())

    idle = request_threads()
    with contextlib.redirect_stderr(captured):
      await asyncio.to_thread(abandon)
      # The request thread ends once its write fails, having reported by then or not at all.
      deadline = asyncio.get_running_loop().time() + 5
      while request_threads() > idle and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.02)
    self.assertEqual(captured.getvalue(), "")


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
  """A stopped viewer gives its ports back."""

  async def test_a_viewer_started_after_another_stopped_binds_the_same_ports(self):
    """`stop` used to close the file server and leave the websocket server listening, so the next
    viewer in the same process found its port taken and moved up: the ports drifted by one on
    every restart, and a page served by the earlier viewer kept its stale token forever."""
    facility = await empty_facility()
    first = Viewer3D(facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await first.start()
    self.assertEqual((first.fs_port, first.ws_port), (FS_PORT, WS_PORT))
    await first.stop()
    second = Viewer3D(facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await second.start()
    try:
      self.assertEqual((second.fs_port, second.ws_port), (FS_PORT, WS_PORT))
    finally:
      await second.stop()

  async def test_stop_does_not_hold_the_loop(self):
    """Shutting the file server down waited on its serving thread's half-second poll from the
    loop's own thread, so everything else on the loop stood still for that long."""
    facility = await empty_facility()
    viewer = Viewer3D(facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    viewer.FS_POLL_S = 0.5  # a shutdown that waits on the loop would then hold it this long
    await viewer.start()
    loop = asyncio.get_running_loop()
    ticks = [loop.time()]

    async def tick() -> None:
      while True:
        await asyncio.sleep(0.02)
        ticks.append(loop.time())

    ticking = asyncio.ensure_future(tick())
    try:
      await viewer.stop()
    finally:
      ticks.append(loop.time())  # a loop held until here shows as one long gap
      ticking.cancel()
    self.assertLess(max(b - a for a, b in zip(ticks, ticks[1:])), 0.2)

  async def test_a_stopped_viewer_no_longer_listens_to_the_tree(self):
    """`stop` used to leave every state and assignment callback in place, so a stopped viewer
    kept serializing every change for nobody, and each viewer started on a tree in one session
    added its own callbacks to every resource for the life of the tree."""
    facility = await empty_facility()
    box = await part(facility, "part")
    viewer = Viewer3D(facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await viewer.start()
    self.assertIn(box.id, viewer._subscribed)
    await viewer.stop()
    self.assertFalse(viewer._tree.following)
    self.assertEqual(viewer._subscribed, set())
    await move_to(box, Coordinate(1, 2, 3))
    late = await part(facility, "late")
    await asyncio.sleep(2 * viewer._tree.BATCH_WAIT_S)
    self.assertNotIn(late.id, viewer._subscribed)
    self.assertEqual(viewer._pending, {})
    await facility.store.close()

  async def test_a_resource_put_back_is_listened_to_once(self):
    """Every assignment subscribed the resource again, so a tip picked up and put back twenty
    times carried twenty-one callbacks and its every change was serialized twenty-one times."""
    facility = await empty_facility()
    box = await part(facility, "part")
    viewer = Viewer3D(facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await viewer.start()
    try:
      for _ in range(20):
        await box.unassign()
        await facility.assign_child_resource(box, location=Coordinate(0, 0, 0))
      await viewer.caught_up(30)
      self.assertIn(box.id, viewer._subscribed)
      sent: List[str] = []
      viewer._enqueue = lambda name, state: sent.append(name)  # type: ignore[method-assign]
      await move_to(box, Coordinate(1, 2, 3))
      await viewer.caught_up(30)
      self.assertEqual(sent, ["part"])
    finally:
      await viewer.stop()
      await facility.store.close()


class BindTests(unittest.IsolatedAsyncioTestCase):
  """A port that is taken is walked past; any other bind failure is raised at once."""

  async def test_a_host_that_cannot_be_bound_is_raised_at_once(self):
    """Every bind error used to read as a taken port, so an address this machine does not have
    walked up through all sixty-five thousand ports, took seconds, and then overflowed."""
    facility = await empty_facility()
    viewer = Viewer3D(
      facility, host="203.0.113.1", open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT
    )
    with self.assertRaises(OSError):
      await viewer.start()
    self.assertEqual(viewer.ws_port, WS_PORT)

  async def test_an_ipv6_host_serves_both_ports(self):
    """The file server was bound as IPv4 whatever the host, so `::1` bound the websocket and then
    hung forever walking ports for a file server that could never bind one."""
    facility = await empty_facility()
    viewer = Viewer3D(facility, host="::1", open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await viewer.start()
    try:
      self.assertEqual((viewer.fs_port, viewer.ws_port), (FS_PORT, WS_PORT))
    finally:
      await viewer.stop()


class AbandonedLoopTests(unittest.TestCase):
  """A viewer whose loop closed under it leaves the tree alone."""

  def test_a_change_after_the_loop_closed_does_not_raise(self):
    """A script that starts a viewer and returns from `asyncio.run` without stopping it used to
    turn every later location change into `RuntimeError: Event loop is closed`, raised out of the
    resource, and an assignment raised after the child was already attached."""

    async def start_and_forget() -> handles.Resource:
      facility = await empty_facility()
      await part(facility, "part")
      # Its ports stay bound in this process: nothing can stop it once its loop has gone.
      fs_port, ws_port = free_ports(2)
      await Viewer3D(facility, open_browser=False, fs_port=fs_port, ws_port=ws_port).start()
      return facility

    facility = asyncio.run(start_and_forget())

    async def change() -> Optional[str]:
      box = await facility.store.get("part", root=facility)
      await move_to(box, Coordinate(1, 2, 3))
      late = await part(facility, "late")
      parent = await late.get_parent()
      return parent.name if parent is not None else None

    self.assertEqual(asyncio.run(change()), "facility")


class RebuildTests(unittest.IsolatedAsyncioTestCase):
  """A scene rebuilt from reused models is the scene it was."""

  async def test_a_tree_changed_with_nobody_watching_costs_no_rebuild(self):
    """Every structural change rebuilt the scene and packed a full snapshot before finding there
    was no client to send them to: a third of a second on the demo facility, on every assignment
    of a deck laid out before the page was opened. The next client is greeted with a scene built
    for it then, and it holds what was assigned meanwhile."""
    facility = await empty_facility()
    viewer = Viewer3D(facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT)
    await viewer.start()
    try:
      await part(facility, "late")
      await viewer.caught_up(30)
      # Twice the debounce: the rebuild the assignment scheduled has had its chance to run.
      await asyncio.sleep(2 * Viewer3D.SCENE_DEBOUNCE_S)
      self.assertEqual(viewer.rebuilds, 0)
      async with websockets.connect(
        viewer.ws_url, origin=Origin(f"http://127.0.0.1:{viewer.fs_port}")
      ) as ws:
        scene = json.loads(await asyncio.wait_for(ws.recv(), 5))["data"]
        self.assertIn("late", scene["instances"]["names"])
    finally:
      await viewer.stop()
      await facility.store.close()

  async def test_a_model_given_a_mesh_does_not_split_on_the_next_build(self):
    """Registering meshes used to write into the interned model dicts, so on the next build the
    one carrying a mesh no longer matched the twins the scene had kept, and every rebuild grew the
    model table: fifty-three models became sixty-seven on the demo facility."""
    facility = await empty_facility()
    for i in range(3):
      # Declared the way a resource declares what it is drawn with: in its metadata.
      await part(
        facility,
        f"part_{i}",
        Coordinate(100 * i, 0, 0),
        model="part",
        metadata={"mesh": {"path": MESH_FILE, "units": "m", "up": "Z"}},
      )
    viewer = Viewer3D(facility, open_browser=False)
    await viewer.follow()
    try:
      first = viewer._scene_message(rebuild=True)
      second = viewer._scene_message(rebuild=True)
    finally:
      await viewer.stop()
      await facility.store.close()
    self.assertEqual(len(first["models"]), 2)  # the facility and the one part they all share
    self.assertEqual(second["models"], first["models"])


class MeshTests(unittest.IsolatedAsyncioTestCase):
  """The file server hands out a mesh without the token, so which files it will serve is narrow."""

  async def asyncSetUp(self):
    self.facility = await empty_facility()

  async def asyncTearDown(self):
    await self.facility.store.close()

  async def meshes(self, models_root: Optional[str] = None) -> Dict[str, Any]:
    """Each part's mesh as the page is told it, by the part's model name; None drawn as a box."""
    viewer = Viewer3D(self.facility, open_browser=False, models_root=models_root)
    await viewer.follow()
    try:
      models = viewer._scene_message(rebuild=True)["models"]
    finally:
      await viewer.stop()
    self.viewer = viewer
    return {m["model"]: m.get("mesh") for m in models if m.get("model")}

  async def part(self, name: str, **declared: Any) -> None:
    await part(self.facility, name, model=name, metadata=declared)

  async def test_a_mesh_id_does_not_name_its_file(self):
    """The id was the SHA-1 of the file's path, so anyone who could guess a path could fetch it."""
    await self.part("a", mesh={"path": MESH_FILE})
    await self.part("b", mesh={"path": MESH_FILE})
    meshes = await self.meshes()
    mesh_id = meshes["a"]["url"][len("mesh/") :]
    self.assertEqual(meshes["b"]["url"], meshes["a"]["url"])  # one file, one id
    self.assertNotIn(hashlib.sha1(MESH_FILE.encode()).hexdigest()[:16], mesh_id)
    self.assertEqual(self.viewer._mesh_files[mesh_id], os.path.realpath(MESH_FILE))

  async def test_only_a_glb_is_served(self):
    with tempfile.TemporaryDirectory() as directory:
      secret = os.path.join(directory, "secret.txt")
      with open(secret, "w") as f:
        f.write("not a model")
      await self.part("text", mesh={"path": secret})
      self.assertIsNone((await self.meshes())["text"])
      self.assertEqual(self.viewer._mesh_files, {})

  async def test_a_reference_glb_outside_models_root_is_drawn_as_a_box(self):
    with tempfile.TemporaryDirectory() as directory:
      root = os.path.join(directory, "models")
      os.makedirs(root)
      shutil.copy(MESH_FILE, os.path.join(root, "inside.glb"))
      shutil.copy(MESH_FILE, os.path.join(directory, "outside.glb"))
      os.symlink(os.path.join(directory, "outside.glb"), os.path.join(root, "link.glb"))
      await self.part("inside", reference_glb="inside.glb")
      await self.part("absolute", reference_glb=os.path.join(directory, "outside.glb"))
      await self.part("dotdot", reference_glb="../outside.glb")
      await self.part("link", reference_glb="link.glb")
      meshes = await self.meshes(models_root=root)
      self.assertIsNotNone(meshes["inside"])
      for escaping in ("absolute", "dotdot", "link"):
        self.assertIsNone(meshes[escaping], escaping)


class WaitForBrowserTests(unittest.IsolatedAsyncioTestCase):
  """A simulated run is over in milliseconds: it waits for a page that is drawing, or none sees it."""

  async def asyncSetUp(self):
    fs_port, ws_port = free_ports(2)
    self.facility = await empty_facility()
    self.viewer = Viewer3D(self.facility, open_browser=False, fs_port=fs_port, ws_port=ws_port)
    await self.viewer.start()

  async def asyncTearDown(self):
    await self.viewer.stop()
    await self.facility.store.close()

  async def say_hello(self, **data: Any) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
      async with websockets.connect(self.viewer.ws_url, max_size=None) as ws:
        await ws.send(json.dumps({"event": "hello", "data": data}))
        await (await ws.ping())  # answered once the hello before it has been read

  async def test_the_wait_ends_when_a_page_says_it_is_drawing(self):
    waiting = asyncio.ensure_future(self.viewer.wait_for_browser(timeout=5))
    await asyncio.sleep(0.1)
    self.assertFalse(waiting.done())
    await self.say_hello(backend="WebGL2")
    await asyncio.wait_for(waiting, 1)

  async def test_a_page_that_could_not_draw_does_not_end_the_wait(self):
    await self.say_hello(backend=None, error="this browser offers neither WebGPU nor WebGL2")
    with self.assertRaises(asyncio.TimeoutError):
      await self.viewer.wait_for_browser(timeout=0.2)

  async def test_waiting_before_start_is_refused(self):
    with self.assertRaises(RuntimeError):
      await Viewer3D(self.facility, open_browser=False).wait_for_browser(timeout=0.1)


class AccessTests(unittest.IsolatedAsyncioTestCase):
  """Only the page this viewer served, reached by a name this machine answers to, may watch."""

  async def asyncSetUp(self):
    self.facility = await empty_facility()
    self.viewer = Viewer3D(
      self.facility, open_browser=False, fs_port=FS_PORT, ws_port=WS_PORT, name="tests"
    )
    await self.viewer.start()

  async def asyncTearDown(self):
    await self.viewer.stop()
    await self.facility.store.close()

  def ws(self, token: Optional[str]) -> str:
    query = "" if token is None else f"?token={token}"
    return f"ws://127.0.0.1:{self.viewer.ws_port}/{query}"

  async def assert_refused(self, url: str, **kwargs):
    with self.assertRaises(websockets.InvalidStatus) as refused:
      await websockets.connect(url, **kwargs)
    self.assertEqual(refused.exception.response.status_code, 403)

  async def test_a_websocket_without_the_token_is_refused(self):
    await self.assert_refused(self.ws(None))
    await self.assert_refused(self.ws("not-the-token"))

  async def test_a_page_from_another_site_is_refused_even_with_the_token(self):
    await self.assert_refused(self.ws(self.viewer.token), origin="https://example.com")

  async def test_the_served_page_and_a_tunnel_are_let_in(self):
    for origin in (
      f"http://127.0.0.1:{self.viewer.fs_port}",
      "http://localhost:9000",
      f"http://{socket.gethostname()}.local:{self.viewer.fs_port}",
      "http://10.60.2.36:1338",
    ):
      ws = await websockets.connect(
        self.ws(self.viewer.token), origin=Origin(origin), max_size=None
      )
      self.assertEqual(json.loads(await ws.recv())["event"], "scene")
      await ws.close()

  def get(self, host: str) -> int:
    request = urllib.request.Request(
      f"http://127.0.0.1:{self.viewer.fs_port}/", headers={"Host": host}
    )
    try:
      with urllib.request.urlopen(request) as response:
        return int(response.status)
    except urllib.error.HTTPError as error:
      return error.code

  async def test_the_page_is_not_served_to_a_rebound_name(self):
    """DNS rebinding points a hostile name at 127.0.0.1, which would make its page same-origin
    with ours and let it read the token out of the HTML."""
    self.assertEqual(await asyncio.to_thread(self.get, "attacker.example:1338"), 403)

  async def test_the_page_is_served_to_a_known_name_without_the_token(self):
    """The page used to carry the token, so anyone who could reach the file server, a LAN peer
    for one, could watch. Only the link the viewer prints carries it, in a fragment."""
    for host in ("127.0.0.1:1338", "localhost:1338", "[::1]:1338"):
      self.assertEqual(await asyncio.to_thread(self.get, host), 200, host)
    page = await asyncio.to_thread(
      lambda: urllib.request.urlopen(f"http://127.0.0.1:{self.viewer.fs_port}/").read().decode()
    )
    self.assertNotIn(self.viewer.token, page)
    self.assertNotIn("{{", page)
    self.assertTrue(self.viewer.url.endswith(f"/#token={self.viewer.token}"))

  async def test_a_socket_is_heard_once(self):
    """Every hello was kept and printed, so one socket could grow the list and flood the output."""
    hello = json.dumps({"event": "hello", "data": {"backend": "WebGL2"}})
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
      async with websockets.connect(self.ws(self.viewer.token), max_size=None) as ws:
        for _ in range(3):
          await ws.send(hello)
        await ws.send("not json")
        await (await ws.ping())  # answered once everything sent before it has been read
    self.assertEqual(len(self.viewer.clients_seen), 1)
    self.assertEqual(printed.getvalue().count("a browser connected"), 1)

  async def test_a_token_from_another_run_is_refused(self):
    """A page served by an earlier run keeps that run's token, and it must not open this one."""
    other = Viewer3D(self.facility, open_browser=False)
    await self.assert_refused(self.ws(other.token))


if __name__ == "__main__":
  unittest.main()
