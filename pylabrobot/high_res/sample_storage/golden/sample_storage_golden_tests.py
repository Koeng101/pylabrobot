"""Golden records of what the HighRes sample stores do today: the commands sent, the events
emitted and the resources left, step by step."""

import math
import random
import unittest
from typing import Any, Awaitable, Callable, Optional, TypeVar

from pylabrobot.high_res.sample_storage import (
  AmbiStore,
  HighResSampleStorage,
  SteriStore,
  TundraStore,
  high_res_stacker,
)
from pylabrobot.high_res.sample_storage.driver import tree_events
from pylabrobot.high_res.sample_storage.golden.harness import Recorder, SimulatedSocket
from pylabrobot.high_res.sample_storage.stackers import plate_holder
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing.golden import snapshot_store

T = TypeVar("T")


async def make_plate(
  device: HighResSampleStorage, name: str, size_z: float = 14, lid: bool = False
) -> handles.Plate:
  """A one-well plate, standing alone in the device's resource store."""
  children = [
    build.resource(
      f"{name}_A1",
      Coordinate(8, 8, 10),
      kind=pb.RESOURCE_KIND_WELL,
      location=Coordinate(10, 10, 2),
      category="well",
      type_name="Well",
      identifier="A1",
      container=pb.ContainerSpec(
        max_volume=math.pi * 4 * 4 * 10,
        cross_section_type=pb.CROSS_SECTION_TYPE_CIRCLE,
      ),
      state=pb.ResourceState(volume=pb.VolumeState()),
    )
  ]
  if lid:
    children.append(
      build.resource(
        f"{name}_lid",
        Coordinate(127.76, 85.48, 5),
        kind=pb.RESOURCE_KIND_LID,
        location=Coordinate(0, 0, size_z - 2),
        category="lid",
        type_name="Lid",
        lid=pb.LidSpec(nesting_z_height=2),
      )
    )
  definition = build.resource(
    name,
    Coordinate(127.76, 85.48, size_z),
    kind=pb.RESOURCE_KIND_PLATE,
    category="plate",
    type_name="Plate",
    itemized=pb.ItemizedSpec(num_items_x=1, num_items_y=1),
    plate=pb.PlateSpec(plate_type="skirted"),
    children=children,
  )
  plate = await device.store.create(definition, name=name)
  assert isinstance(plate, handles.Plate)
  return plate


def seeded(seed: int, choose: Callable[[], T]) -> T:
  """`choose` with Python's random generator seeded first."""
  random.seed(seed)
  return choose()


async def by_hand(child: handles.Resource, parent: handles.Resource) -> None:
  """An operator puts `child` in `parent`: the store has it there, and it is reported."""
  await parent.assign_child_resource(child)
  await tree_events.emit_assigned(child)


async def put_on_tray(
  device: HighResSampleStorage, socket: SimulatedSocket, tray_index: int, plate: handles.Plate
) -> None:
  """An operator puts `plate` on a transfer nest: the model and the nest sensor both have it."""
  await by_hand(plate, device.nests[tray_index])
  socket.nest_sensors[tray_index + 1] = "PLATE_AVAILABLE"


async def site(device: HighResSampleStorage, name: str) -> handles.PlateHolder:
  assert device.body is not None
  holder = await device.body.get_resource(name)
  assert isinstance(holder, handles.PlateHolder)
  return holder


async def plate_named(device: HighResSampleStorage, name: str) -> handles.Plate:
  assert device.body is not None
  plate = await device.body.get_resource(name)
  assert isinstance(plate, handles.Plate)
  return plate


async def restore_summary(restored: Awaitable[HighResSampleStorage], serialized: dict) -> dict:
  """What a store restored from `serialized` holds, and whether it serializes the same."""
  device = await restored
  assert device.body is not None
  return {
    "resources": await snapshot_store(device.store, device.body),
    "serializes_the_same": await device.serialize() == serialized,
  }


async def store_plate_in(
  device: HighResSampleStorage, plate: handles.Plate, name: str, tray_index: int
) -> Any:
  return await device.store_plate(plate, await site(device, name), tray_index)


async def take_in_plate_to(device: HighResSampleStorage, tray_index: int, name: str) -> Any:
  return await device.take_in_plate(tray_index, site=await site(device, name))


class SampleStorageGoldenTests(unittest.IsolatedAsyncioTestCase):
  def recorder(self, device: HighResSampleStorage, socket: Optional[SimulatedSocket] = None):
    return Recorder(device, socket if socket is not None else SimulatedSocket())

  async def test_discovery_and_site_selection(self):
    store = SteriStore(host="10.253.253.253", name="store")
    r = self.recorder(store)
    short, medium, lidded = (
      await make_plate(store, "short", 14),
      await make_plate(store, "medium", 18),
      await make_plate(store, "lidded", 14, lid=True),
    )
    tall, too_tall = await make_plate(store, "tall", 25), await make_plate(store, "too_tall", 35)

    await r.step("setup()", lambda: store.setup())
    await r.step(
      "find_smallest_site_for_plate(short)", lambda: store.find_smallest_site_for_plate(short)
    )
    await r.step(
      "find_smallest_site_for_plate(medium)", lambda: store.find_smallest_site_for_plate(medium)
    )
    await r.step(
      "find_smallest_site_for_plate(lidded)", lambda: store.find_smallest_site_for_plate(lidded)
    )
    await r.step(
      "find_smallest_site_for_plate(tall)", lambda: store.find_smallest_site_for_plate(tall)
    )
    await r.step(
      "find_smallest_site_for_plate(too_tall)", lambda: store.find_smallest_site_for_plate(too_tall)
    )
    await r.step(
      "random.seed(0); find_random_site(short)",
      lambda: seeded(0, lambda: store.find_random_site(short)),
    )
    await r.step(
      "random.seed(1); find_random_site(short)",
      lambda: seeded(1, lambda: store.find_random_site(short)),
    )
    await r.step(
      "random.seed(2); find_random_site(short)",
      lambda: seeded(2, lambda: store.find_random_site(short)),
    )
    await r.step(
      "random.seed(0); find_random_site(tall)",
      lambda: seeded(0, lambda: store.find_random_site(tall)),
    )
    await r.step("get_num_free_sites()", lambda: store.get_num_free_sites())
    await r.step("racks", lambda: store.racks)
    await r.step("serialize()", lambda: store.serialize())
    await r.step("setup() again", lambda: store.setup())
    await r.check(self, "discovery_and_site_selection")

  async def test_store_and_fetch(self):
    store = SteriStore(host="10.253.253.253", name="store")
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate_a, plate_b, plate_c = (
      await make_plate(store, "plate_a"),
      await make_plate(store, "plate_b", 18),
      await make_plate(store, "plate_c", 14, lid=True),
    )

    await r.step("setup()", lambda: store.setup())
    await r.step("operator puts plate_a on tray 0", lambda: put_on_tray(store, socket, 0, plate_a))
    await r.step("take_in_plate(0)", lambda: store.take_in_plate(0))
    await r.step("operator puts plate_b on tray 1", lambda: put_on_tray(store, socket, 1, plate_b))
    await r.step(
      "random.seed(3); take_in_plate(1, site='random')",
      lambda: seeded(3, lambda: store.take_in_plate(1, site="random")),
    )
    await r.step("operator puts plate_c on tray 0", lambda: put_on_tray(store, socket, 0, plate_c))
    await r.step(
      "store_plate(plate_c, store_stacker_1_slot_2, 0)",
      lambda: store_plate_in(store, plate_c, "store_stacker_1_slot_2", 0),
    )
    await r.step("get_num_free_sites()", lambda: store.get_num_free_sites())
    await r.step(
      "get_site_by_plate_name('plate_b')", lambda: store.get_site_by_plate_name("plate_b")
    )
    await r.step(
      "get_site_by_plate_name('missing')", lambda: store.get_site_by_plate_name("missing")
    )
    await r.step(
      "fetch_plate_to_loading_tray('plate_a', 0)",
      lambda: store.fetch_plate_to_loading_tray("plate_a", 0),
    )
    await r.step(
      "transfer_plate_between_nests(0, 1)", lambda: store.transfer_plate_between_nests(0, 1)
    )
    await r.step(
      "fetch_plate_to_loading_tray(plate_b, 0)",
      lambda: store.fetch_plate_to_loading_tray(plate_b, 0),
    )
    await r.step(
      "take_in_plate(1, site=store_stacker_5_slot_2)",
      lambda: take_in_plate_to(store, 1, "store_stacker_5_slot_2"),
    )
    await r.step(
      "take_in_plate(0, site='smallest')", lambda: store.take_in_plate(0, site="smallest")
    )
    serialized = await r.step("serialize()", lambda: store.serialize())
    await r.step(
      "SteriStore.deserialize(serialize())",
      lambda: restore_summary(SteriStore.deserialize(serialized), serialized),
    )
    await r.check(self, "store_and_fetch")

  async def test_refusals(self):
    store = TundraStore(host="10.253.253.253", name="store")
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate_a, plate_b, too_tall = (
      await make_plate(store, "plate_a"),
      await make_plate(store, "plate_b"),
      await make_plate(store, "too_tall", 35),
    )

    await r.step("setup()", lambda: store.setup())
    await r.step("operator puts plate_a on tray 0", lambda: put_on_tray(store, socket, 0, plate_a))
    await r.step("take_in_plate(0)", lambda: store.take_in_plate(0))
    socket.nest_sensors[1] = "PLATE_AVAILABLE"
    await r.step(
      "fetch_plate_to_loading_tray(plate_a, 0) with nest 1 sensing a plate",
      lambda: store.fetch_plate_to_loading_tray(plate_a, 0),
    )
    socket.nest_sensors[1] = "CLEAR"
    await r.step("take_in_plate(0) with no plate on tray 0", lambda: store.take_in_plate(0))
    await r.step(
      "fetch_plate_to_loading_tray(plate_a, 2)",
      lambda: store.fetch_plate_to_loading_tray(plate_a, 2),
    )
    await r.step(
      "fetch_plate_to_loading_tray(plate_b, 0) with plate_b nowhere",
      lambda: store.fetch_plate_to_loading_tray(plate_b, 0),
    )
    socket.script("pick 5 1 1", ["Error 1: 42: No plate detected"], completion="ERROR!")
    await r.step(
      "fetch_plate_to_loading_tray(plate_a, 0) finding no plate",
      lambda: store.fetch_plate_to_loading_tray(plate_a, 0),
    )
    await r.step("operator puts plate_b on tray 0", lambda: by_hand(plate_b, store.nests[0]))
    await r.step(
      "store_plate(plate_b, store_stacker_2_slot_1, 0) with nest 1 sensing no plate",
      lambda: store_plate_in(store, plate_b, "store_stacker_2_slot_1", 0),
    )
    socket.nest_sensors[1] = "PLATE_AVAILABLE"
    await r.step(
      "store_plate(plate_b, store_stacker_5_slot_1, 0) to an occupied slot",
      lambda: store_plate_in(store, plate_b, "store_stacker_5_slot_1", 0),
    )
    await r.step(
      "store_plate(plate_b, store_stacker_2_slot_1, 1) from the wrong tray",
      lambda: store_plate_in(store, plate_b, "store_stacker_2_slot_1", 1),
    )
    await r.step(
      "take_in_plate(0, site=store_stacker_5_slot_1) to an occupied slot",
      lambda: take_in_plate_to(store, 0, "store_stacker_5_slot_1"),
    )
    await r.step(
      "transfer_plate_between_nests(0, 0)", lambda: store.transfer_plate_between_nests(0, 0)
    )
    await r.step(
      "transfer_plate_between_nests(1, 0) from an empty tray",
      lambda: store.transfer_plate_between_nests(1, 0),
    )
    await r.step(
      "operator puts too_tall on tray 1", lambda: put_on_tray(store, socket, 1, too_tall)
    )
    await r.step(
      "transfer_plate_between_nests(1, 0) to an occupied tray",
      lambda: store.transfer_plate_between_nests(1, 0),
    )
    await r.step(
      "take_in_plate(1) with a plate too tall for any slot", lambda: store.take_in_plate(1)
    )
    await r.check(self, "refusals")

  async def test_unresolved_transfers(self):
    store = SteriStore(host="10.253.253.253", name="store")
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate_a, plate_b = await make_plate(store, "plate_a"), await make_plate(store, "plate_b")

    await r.step("setup()", lambda: store.setup())
    await r.step("operator puts plate_a on tray 0", lambda: put_on_tray(store, socket, 0, plate_a))
    await r.step("take_in_plate(0)", lambda: store.take_in_plate(0))

    # An aborted pick: the plate stays in its slot until resolved.
    socket.script("pick 5 1 1", [], completion="ABORTED!")
    await r.step(
      "fetch_plate_to_loading_tray(plate_a, 0) aborted",
      lambda: store.fetch_plate_to_loading_tray(plate_a, 0),
    )
    await r.step("serialize() while unresolved", lambda: store.serialize())
    await r.step("home() while unresolved", lambda: store.home())
    await r.step(
      "request_stacker_barcodes(2) while unresolved", lambda: store.request_stacker_barcodes(2)
    )
    await r.step("take_in_plate(0) while unresolved", lambda: store.take_in_plate(0))
    await r.step(
      "resolve_unresolved_transfer('source')", lambda: store.resolve_unresolved_transfer("source")
    )
    await r.step(
      "resolve_unresolved_transfer('source') again",
      lambda: store.resolve_unresolved_transfer("source"),
    )

    # The pick's completion never arrives: the connection is closed, then reopened to resolve.
    socket.stall_after_ack.append("pick 5 1 1")
    await r.step(
      "fetch_plate_to_loading_tray(plate_a, 0) timing out after the acknowledgement",
      lambda: store.fetch_plate_to_loading_tray(plate_a, 0),
    )
    await r.step(
      "resolve_unresolved_transfer('destination')",
      lambda: store.resolve_unresolved_transfer("destination"),
    )

    # A failed place: the nest sensor must agree before the plate can be resolved to the slot.
    socket.script("place 5 1 1", ["Error 1: 44: Place failed"], completion="ERROR!")
    await r.step(
      "store_plate(plate_a, store_stacker_5_slot_1, 0) failing",
      lambda: store_plate_in(store, plate_a, "store_stacker_5_slot_1", 0),
    )
    await r.step(
      "resolve_unresolved_transfer('destination') with nest 1 sensing a plate",
      lambda: store.resolve_unresolved_transfer("destination"),
    )
    socket.nest_sensors[1] = "CLEAR"
    await r.step(
      "resolve_unresolved_transfer('destination') with nest 1 clear",
      lambda: store.resolve_unresolved_transfer("destination"),
    )

    # A pick that leaves the machine unsafe: recovery parks it but leaves the transfer unresolved.
    socket.script(
      "pick 5 1 2",
      ["Error 1: 42: Z height is unsafe for rotation, check machine"],
      completion="ERROR!",
    )
    await r.step(
      "fetch_plate_to_loading_tray(plate_a, 1) faulting",
      lambda: store.fetch_plate_to_loading_tray(plate_a, 1),
    )
    await r.step("recover()", lambda: store.recover())
    socket.spatula = "PLATE_AVAILABLE"
    await r.step(
      "resolve_unresolved_transfer('unassigned') with a plate on the spatula",
      lambda: store.resolve_unresolved_transfer("unassigned"),
    )
    socket.spatula = "NO_PLATE"
    await r.step(
      "resolve_unresolved_transfer('unassigned')",
      lambda: store.resolve_unresolved_transfer("unassigned"),
    )

    # An aborted nest transfer, resolved to its destination once both sensors agree.
    await r.step("operator puts plate_b on tray 1", lambda: put_on_tray(store, socket, 1, plate_b))
    socket.script("nesttransfer 2 1", [], completion="ABORTED!")
    await r.step(
      "transfer_plate_between_nests(1, 0) aborted", lambda: store.transfer_plate_between_nests(1, 0)
    )
    await r.step(
      "resolve_unresolved_transfer('destination') with the sensors unchanged",
      lambda: store.resolve_unresolved_transfer("destination"),
    )
    socket.nest_sensors[1], socket.nest_sensors[2] = "PLATE_AVAILABLE", "CLEAR"
    await r.step(
      "resolve_unresolved_transfer('destination')",
      lambda: store.resolve_unresolved_transfer("destination"),
    )
    await r.step("serialize()", lambda: store.serialize())
    await r.check(self, "unresolved_transfers")

  async def test_environment(self):
    store = SteriStore(host="10.253.253.253", name="store")
    r = self.recorder(store)
    environment = store.environment

    await r.step("setup()", lambda: store.setup())
    await r.step("request_environment()", lambda: store.request_environment())
    await r.step("request_current_temperature()", lambda: environment.request_current_temperature())
    await r.step("request_target_humidity()", lambda: environment.request_target_humidity())
    await r.step("set_temperature(37)", lambda: environment.set_temperature(37))
    await r.step("set_temperature(101)", lambda: environment.set_temperature(101))
    await r.step("set_humidity(0.9)", lambda: environment.set_humidity(0.9))
    await r.step("set_co2(0.05)", lambda: environment.set_co2(0.05))
    await r.step("set_o2(0.1)", lambda: environment.set_o2(0.1))
    await r.step("start_temperature_control()", lambda: environment.start_temperature_control())
    await r.step("stop_co2_control()", lambda: environment.stop_co2_control())
    await r.step("request_tank_pressures()", lambda: environment.request_tank_pressures())
    await r.check(self, "environment")

  async def test_explicit_racks_and_restore(self):
    out_of_order = build.resource(
      "out_of_order",
      Coordinate(130, 90, 100),
      kind=pb.RESOURCE_KIND_CARRIER,
      category="plate_carrier",
      type_name="PlateCarrier",
      children=[
        plate_holder(
          f"spot_{spot}", Coordinate(127.76, 85.48, 20), location=Coordinate(0, 0, spot * 20)
        )
        for spot in (7, 2)
      ],
    )
    stacker = high_res_stacker("stacker", zero_offset=0, slot_height=22.867, slot_count=2)
    store = AmbiStore(
      host="10.253.253.253",
      name="store",
      racks={7: out_of_order, 1: stacker},
      rack_spots={7: [7, 2]},
    )
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate = await make_plate(store, "plate")

    await r.step("setup()", lambda: store.setup())
    await r.step("operator puts plate on tray 0", lambda: put_on_tray(store, socket, 0, plate))
    await r.step("store_plate(plate, spot_7, 0)", lambda: store_plate_in(store, plate, "spot_7", 0))
    await r.step(
      "find_smallest_site_for_plate(plate)", lambda: store.find_smallest_site_for_plate(plate)
    )
    serialized = await r.step("serialize()", lambda: store.serialize())
    await r.check(self, "explicit_racks")

    restored = await AmbiStore.deserialize(serialized)
    socket = SimulatedSocket()
    r = self.recorder(restored, socket)
    await r.step("setup() of AmbiStore.deserialize(serialize())", lambda: restored.setup())
    await r.step(
      "fetch_plate_to_loading_tray('plate', 1)",
      lambda: restored.fetch_plate_to_loading_tray("plate", 1),
    )

    async def store_restored_plate() -> None:
      await restored.store_plate(
        await plate_named(restored, "plate"), await site(restored, "stacker_slot_2"), 1
      )

    await r.step("store_plate(plate, stacker_slot_2, 1)", store_restored_plate)
    await r.step("serialize()", lambda: restored.serialize())
    await r.check(self, "explicit_racks_restored")


if __name__ == "__main__":
  unittest.main()
