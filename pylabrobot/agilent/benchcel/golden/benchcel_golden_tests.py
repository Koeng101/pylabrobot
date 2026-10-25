"""Golden records of what the Agilent BenchCel 4R does today: frames, events and its stacks.

The seam is the TCP socket: every frame written is recorded in order as hex. The fake socket
answers each frame the way the BenchCel does (a `0x69` ACK after motion, sensor and status
replies, a `0x9f` echo after labware settings), or with a `0x02` error frame when a scenario asks
for one. Events emitted through `pylabrobot.events` are recorded with their payloads. The
BenchCel's resources are made in its store before the first step, as `setup` would.
"""

from __future__ import annotations

import pathlib
import struct
import unittest
from typing import Any, ContextManager, Dict, List, Optional

from pylabrobot.agilent.benchcel import (
  BenchCel4R,
  BenchCelLabwareSettings,
  Teachpoint,
  apply_benchcel_labware_settings,
)
from pylabrobot.agilent.benchcel.benchcel import Frame, parse_frame_from_buffer
from pylabrobot.agilent.benchcel.stacks import benchcel_4r_stacks
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import ResourceStore, build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

LOADING_TRAY_TEACHPOINT = 0x1E


class _FakeSocket:
  """Stands in for the BenchCel's `Socket`: records frames and answers like the device."""

  def __init__(self, sent: List[str]) -> None:
    self.sent = sent
    self.errors: Dict[int, str] = {}
    self._received = bytearray()
    self._replies = bytearray()

  async def setup(self) -> None:
    self.sent.append("connect")

  async def stop(self) -> None:
    self.sent.append("disconnect")

  async def write(self, data: bytes, timeout: Optional[float] = None) -> None:
    self._received.extend(data)
    while True:
      frame = parse_frame_from_buffer(self._received)
      if frame is None:
        return
      self.sent.append(frame.hex())
      for reply in self._answer(frame):
        self._replies.extend(reply.to_bytes())

  async def read(self, num_bytes: int = 128, timeout: Optional[float] = None) -> bytes:
    if not self._replies:
      raise TimeoutError("no reply")
    chunk = bytes(self._replies[:num_bytes])
    del self._replies[:num_bytes]
    return chunk

  def _answer(self, frame: Frame) -> List[Frame]:
    command = frame.command_id
    error = self.errors.pop(command, None)
    if command == 0x7D:
      return [] if error is None else [Frame(0x02, error.encode("ascii"))]
    if command == 0x9F:
      return [Frame(0x9F)]
    if error is not None:
      return [Frame(0x02, error.encode("ascii"))]
    if command == 0x73:
      return []
    if command in (0x60, 0x61):
      return [Frame(0x69, bytes([command, frame.payload[1]]))]
    if command == 0x7E:
      index = frame.payload[0]
      return [Frame(0x7E, struct.pack("<BB8H", index, 0x08, 45, 1, 0, 240, 128, 241, 0, 1))]
    if command == 0x87:
      payload = bytearray(66)
      struct.pack_into("<ffff", payload, 4, 90.0, 0.0, 0.0, 0.0)
      struct.pack_into("<f", payload, 12, -120.5)
      struct.pack_into("<f", payload, 20, 35.0)
      struct.pack_into("<f", payload, 28, -1.0)
      return [Frame(0x87, bytes(payload))]
    if command == 0x99:
      bounds = struct.pack("<8f", -115.0, -360.9, -1.5, -1.5, 115.0, 360.9, 104.0, 11.0)
      return [Frame(0x99, bounds)]
    return [Frame(0x69, bytes([command]))]


class _Recorder(recording.Recorder):
  """A BenchCel 4R on the fake socket, recording each step's frames, events and resources.

  Operation ids are uuids; they are recorded as `op-1`, `op-2`... in the order they appear.
  """

  def __init__(
    self, store: Optional[ResourceStore] = None, labware: Optional[handles.Plate] = None
  ):
    super().__init__()
    self.store = store or ResourceStore.in_memory()
    self.benchcel = BenchCel4R(
      name="benchcel",
      host="192.168.0.100",
      timeout=1.0,
      read_poll_timeout=0.01,
      loading_tray_teachpoint_id=LOADING_TRAY_TEACHPOINT,
      labware=labware,
      loading_tray_location=Coordinate(-200, 50, 0),
      store=self.store,
    )
    self.socket = _FakeSocket(self.sent)
    self.benchcel.io = self.socket  # type: ignore[assignment]
    self.initial: Optional[List[Dict[str, Any]]] = None
    self.events = recording.EventLog()

  async def start(self) -> None:
    await self.benchcel.create_resources()

  async def snapshot(self) -> List[Dict[str, Any]]:
    return await snapshot_store(self.store, self.benchcel.body)

  def patches(self) -> List[ContextManager[Any]]:
    return [self.events.installed()]

  def jsonable(self, value: Any) -> Any:
    return _result(value)

  def failed(self, entry: Dict[str, Any], error: BaseException) -> None:
    entry["result"] = recording.error_result(error)

  async def annotate(self, entry: Dict[str, Any]) -> None:
    entry["events"] = [self.events.summary(event) for event in self.events.take()]
    resources = await self.changed()
    if resources is not None:
      entry["resources"] = resources

  async def begin(self) -> None:
    self.events.take()
    before = await self.mark()
    if self.initial is None:
      self.initial = before

  async def record(self) -> Dict[str, Any]:
    return {
      "initial_resources": self.initial,
      "steps": self.steps,
      "resources": await self.snapshot(),
    }


def _result(result: Any) -> Any:
  if isinstance(result, handles.Plate):
    return {"plate": result.name}
  if isinstance(result, BenchCelLabwareSettings):
    return result.to_dict()
  if isinstance(result, Coordinate):
    return [result.x, result.y, result.z]
  return recording.plain(result)


async def _plate(store: ResourceStore, name: str, size_z: float = 14.2) -> handles.Plate:
  """An SBS plate with one row of two wells, a root in `store`: enough to show its wells move
  with it."""
  well = build.resource(
    f"{name}_well_{{identifier}}",
    Coordinate(6.9, 6.9, size_z - 1),
    kind=pb.RESOURCE_KIND_WELL,
    category="well",
    container=pb.ContainerSpec(max_volume=360),
    state=pb.ResourceState(volume=pb.VolumeState()),
  )
  plate = await store.create(
    build.resource(
      name,
      Coordinate(127.76, 85.48, size_z),
      kind=pb.RESOURCE_KIND_PLATE,
      category="plate",
      model="assay_plate",
      plate=pb.PlateSpec(plate_type="skirted"),
      itemized=pb.ItemizedSpec(
        num_items_x=2,
        num_items_y=1,
        grid=pb.ItemGrid(item=well, offset=build.vec3(Coordinate(10, 40, 1)), item_dx=9, item_dy=0),
      ),
    ),
    name=name,
  )
  assert isinstance(plate, handles.Plate)
  return plate


async def _bare_plate(store: ResourceStore, name: str) -> handles.Plate:
  """A plate with no wells, which the loading tray cannot take."""
  plate = await store.create(
    build.resource(
      name,
      Coordinate(127.76, 85.48, 14.2),
      kind=pb.RESOURCE_KIND_PLATE,
      category="plate",
      plate=pb.PlateSpec(plate_type="skirted"),
      itemized=pb.ItemizedSpec(),
    ),
    name=name,
  )
  assert isinstance(plate, handles.Plate)
  return plate


async def _sensor(benchcel: BenchCel4R, stack: handles.ResourceStack) -> Dict[str, Any]:
  status = await benchcel.request_stacker_sensor_status(stack)
  return {
    "stacker": status.stacker,
    "air_pressure": status.air_pressure,
    "plate_presence": status.plate_presence,
    "plate_present": status.plate_present(),
    "notch_values": list(status.notch_values()),
  }


async def _pose(benchcel: BenchCel4R) -> Dict[str, Any]:
  pose = await benchcel.request_arm_pose()
  return {
    "location": [pose.location.x, pose.location.y, pose.location.z],
    "rotation_z": pose.rotation.z,
    "gripper_position": pose.gripper_position,
  }


class BenchCelGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_downstack_and_upstack(self):
    """Plates downstacked to the loading tray, upstacked onto other stacks, and moved between
    stacks; with the arm, clamp and status commands of a run."""
    recorder = _Recorder()
    await recorder.start()
    benchcel, store = recorder.benchcel, recorder.store
    stacks = benchcel.stacks
    for name in ("plate_1", "plate_2", "plate_3"):
      await stacks[0].assign_child_resource(await _plate(store, name))
    await stacks[2].assign_child_resource(await _plate(store, "plate_4", size_z=20))

    await recorder.step("setup()", benchcel.setup)
    await recorder.step(
      "request_stacker_sensor_status(stacks[0])",
      lambda: _sensor(benchcel, stacks[0]),
    )
    await recorder.step("request_arm_pose()", lambda: _pose(benchcel))
    await recorder.step("move_to_stacker(stacks[0])", lambda: benchcel.move_to_stacker(stacks[0]))
    await recorder.step("downstack(stacks[0])", lambda: benchcel.downstack(stacks[0]))
    await recorder.step("upstack(stacks[3])", lambda: benchcel.upstack(stacks[3]))
    await recorder.step("downstack(stacks[2])", lambda: benchcel.downstack(stacks[2]))
    await recorder.step(
      "move_plate_between_stacks(stacks[0], stacks[1])",
      lambda: benchcel.move_plate_between_stacks(stacks[0], stacks[1]),
    )
    await recorder.step("upstack(stacks[0])", lambda: benchcel.upstack(stacks[0]))
    await recorder.step(
      "open_stacker_clamps(stacks[1])", lambda: benchcel.open_stacker_clamps(stacks[1])
    )
    await recorder.step(
      "close_stacker_clamps(stacks[1])", lambda: benchcel.close_stacker_clamps(stacks[1])
    )
    await recorder.step(
      "move_to_teachpoint(0x1e)", lambda: benchcel.move_to_teachpoint(LOADING_TRAY_TEACHPOINT)
    )
    await recorder.step("stop()", benchcel.stop)

    check_golden(self, GOLDEN / "downstack_and_upstack.json", await recorder.record())

  async def test_refused_and_failed_transfers(self):
    """Transfers the BenchCel refuses before sending anything, and transfers the device fails
    part way: none of them changes the stacks or the tray."""
    recorder = _Recorder()
    await recorder.start()
    benchcel, store = recorder.benchcel, recorder.store
    stacks = benchcel.stacks
    await stacks[0].assign_child_resource(await _plate(store, "plate_1"))
    await stacks[0].assign_child_resource(await _plate(store, "plate_2"))
    # A stack of the same name as stacker 2's, outside the BenchCel.
    foreign = await store.create(benchcel_4r_stacks()[1], name=stacks[1].name)
    assert isinstance(foreign, handles.ResourceStack)

    await recorder.step("downstack(stacks[1]) empty", lambda: benchcel.downstack(stacks[1]))
    await recorder.step("upstack(stacks[1]) tray empty", lambda: benchcel.upstack(stacks[1]))
    await recorder.step("downstack(foreign stack)", lambda: benchcel.downstack(foreign))
    await recorder.step(
      "move_plate_between_stacks(stacks[0], stacks[0])",
      lambda: benchcel.move_plate_between_stacks(stacks[0], stacks[0]),
    )
    await recorder.step(
      "move_plate_between_stacks(stacks[2], stacks[3]) empty",
      lambda: benchcel.move_plate_between_stacks(stacks[2], stacks[3]),
    )

    recorder.socket.errors[0x63] = "Z position out of bounds"
    await recorder.step("downstack(stacks[0]) place fails", lambda: benchcel.downstack(stacks[0]))
    recorder.socket.errors[0x62] = "No plate detected"
    await recorder.step("downstack(stacks[0]) pick fails", lambda: benchcel.downstack(stacks[0]))
    await recorder.step("downstack(stacks[0])", lambda: benchcel.downstack(stacks[0]))
    await recorder.step("downstack(stacks[0]) tray occupied", lambda: benchcel.downstack(stacks[0]))
    recorder.socket.errors[0x63] = "Gripper closed on nothing"
    await recorder.step("upstack(stacks[2]) place fails", lambda: benchcel.upstack(stacks[2]))

    async def forget_teachpoint() -> None:
      benchcel.loading_tray_teachpoint_id = None

    await recorder.step("loading_tray_teachpoint_id = None", forget_teachpoint)
    await recorder.step("upstack(stacks[2]) no teachpoint", lambda: benchcel.upstack(stacks[2]))
    benchcel.loading_tray_teachpoint_id = LOADING_TRAY_TEACHPOINT

    await recorder.step("upstack(stacks[2])", lambda: benchcel.upstack(stacks[2]))
    await stacks[3].assign_child_resource(await _bare_plate(store, "bare_plate"))
    await recorder.step(
      "downstack(stacks[3]) a plate the tray cannot take", lambda: benchcel.downstack(stacks[3])
    )

    check_golden(self, GOLDEN / "refused_and_failed_transfers.json", await recorder.record())

  async def test_labware(self):
    """Labware settings from a plate at construction and pushed to the device; the pickup
    location they give a plate, and a plate of another size refused."""
    store = ResourceStore.in_memory()
    labware_plate = await store.create("cor_96_wellplate_360uL_Fb", name="labware_plate")
    assert isinstance(labware_plate, handles.Plate)
    recorder = _Recorder(store, labware=labware_plate)
    await recorder.start()
    benchcel = recorder.benchcel
    deep = await _plate(store, "deep_plate", size_z=44.0)
    assay = await store.create("cor_96_wellplate_360uL_Fb", name="assay")
    assert isinstance(assay, handles.Plate)

    async def settings() -> Any:
      return benchcel.labware_settings

    async def apply(plate: handles.Plate, labware: Optional[BenchCelLabwareSettings] = None) -> Any:
      await apply_benchcel_labware_settings(plate, labware)
      return await plate.get_preferred_pickup_location()

    async def pickup(plate: handles.Plate) -> Any:
      return await plate.get_preferred_pickup_location()

    await recorder.step("labware_settings at construction", settings)
    await recorder.step("set_labware(deep_plate)", lambda: benchcel.set_labware(deep))
    await recorder.step("labware_settings", settings)
    recorder.socket.errors[0x7D] = "Gripper hold positions too close"
    await recorder.step("set_labware(assay) refused", lambda: benchcel.set_labware(assay))
    await recorder.step("labware_settings", settings)
    await recorder.step("apply_benchcel_labware_settings(assay)", lambda: apply(assay))
    await recorder.step(
      "apply_benchcel_labware_settings(assay, deep_plate settings) refused",
      lambda: apply(assay, benchcel.labware_settings),
    )
    await recorder.step("assay.preferred_pickup_location", lambda: pickup(assay))
    await recorder.step(
      "apply_benchcel_labware_settings(deep_plate, deep_plate settings)",
      lambda: apply(deep, benchcel.labware_settings),
    )
    await recorder.step(
      "set_teachpoint(0x1e)",
      lambda: benchcel.set_teachpoint(
        Teachpoint(
          theta=89.99874114990234,
          x=-360.8802795410156,
          z=-10.0,
          approach_height=20.0,
          cavity_depth=0.0,
          gripper_open_limit=-1.5,
          respect_approach_height_when_not_holding_plate=True,
          something_above_this_point=False,
          teachpoint_id=LOADING_TRAY_TEACHPOINT,
          name="loading_tray",
        )
      ),
    )

    check_golden(self, GOLDEN / "labware.json", await recorder.record())


if __name__ == "__main__":
  unittest.main()
