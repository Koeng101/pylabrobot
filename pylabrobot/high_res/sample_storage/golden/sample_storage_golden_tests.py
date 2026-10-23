"""Golden records of what the HighRes sample stores do today: the commands sent, the events
emitted and the resources left, step by step."""

import random
import unittest
from typing import Callable, Optional, TypeVar

from pylabrobot.high_res.sample_storage import (
  AmbiStore,
  HighResSampleStorage,
  SteriStore,
  TundraStore,
  high_res_stacker,
)
from pylabrobot.high_res.sample_storage.golden.harness import Recorder, SimulatedSocket
from pylabrobot.resources import Coordinate, Lid, Plate, PlateCarrier, PlateHolder, Well
from pylabrobot.testing.golden import snapshot_resources

T = TypeVar("T")


def make_plate(name: str, size_z: float = 14, lid: bool = False) -> Plate:
  well = Well(name=f"{name}_A1", size_x=8, size_y=8, size_z=10)
  plate = Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=size_z,
    ordered_items={"A1": well.at(Coordinate(10, 10, 2))},
  )
  if lid:
    plate.assign_child_resource(
      Lid(name=f"{name}_lid", size_x=127.76, size_y=85.48, size_z=5, nesting_z_height=2)
    )
  return plate


def seeded(seed: int, choose: Callable[[], T]) -> T:
  """`choose` with Python's random generator seeded first."""
  random.seed(seed)
  return choose()


def put_on_tray(
  store: HighResSampleStorage, socket: SimulatedSocket, tray_index: int, plate: Plate
) -> None:
  """An operator puts `plate` on a transfer nest: the model and the nest sensor both have it."""
  store.nests[tray_index].assign_child_resource(plate)
  socket.nest_sensors[tray_index + 1] = "PLATE_AVAILABLE"


def site(store: HighResSampleStorage, name: str) -> PlateHolder:
  holder = store.get_resource(name)
  assert isinstance(holder, PlateHolder)
  return holder


def plate_named(store: HighResSampleStorage, name: str) -> Plate:
  plate = store.get_resource(name)
  assert isinstance(plate, Plate)
  return plate


def restore_summary(restored: HighResSampleStorage, serialized: dict) -> dict:
  """What a store restored from `serialized` holds, and whether it serializes the same."""
  return {
    "resources": snapshot_resources(restored),
    "serializes_the_same": restored.serialize() == serialized,
  }


class SampleStorageGoldenTests(unittest.IsolatedAsyncioTestCase):
  def recorder(self, store: HighResSampleStorage, socket: Optional[SimulatedSocket] = None):
    return Recorder(store, socket if socket is not None else SimulatedSocket())

  async def test_discovery_and_site_selection(self):
    store = SteriStore(host="10.253.253.253", name="store")
    r = self.recorder(store)
    short, medium, lidded = (
      make_plate("short", 14),
      make_plate("medium", 18),
      make_plate("lidded", 14, lid=True),
    )
    tall, too_tall = make_plate("tall", 25), make_plate("too_tall", 35)

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
    r.check(self, "discovery_and_site_selection")

  async def test_store_and_fetch(self):
    store = SteriStore(host="10.253.253.253", name="store")
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate_a, plate_b, plate_c = (
      make_plate("plate_a"),
      make_plate("plate_b", 18),
      make_plate("plate_c", 14, lid=True),
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
      lambda: store.store_plate(plate_c, site(store, "store_stacker_1_slot_2"), 0),
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
      lambda: store.take_in_plate(1, site=site(store, "store_stacker_5_slot_2")),
    )
    await r.step(
      "take_in_plate(0, site='smallest')", lambda: store.take_in_plate(0, site="smallest")
    )
    serialized = await r.step("serialize()", lambda: store.serialize())
    await r.step(
      "SteriStore.deserialize(serialize())",
      lambda: restore_summary(SteriStore.deserialize(serialized), serialized),
    )
    r.check(self, "store_and_fetch")

  async def test_refusals(self):
    store = TundraStore(host="10.253.253.253", name="store")
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate_a, plate_b, too_tall = (
      make_plate("plate_a"),
      make_plate("plate_b"),
      make_plate("too_tall", 35),
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
    await r.step(
      "operator puts plate_b on tray 0", lambda: store.nests[0].assign_child_resource(plate_b)
    )
    await r.step(
      "store_plate(plate_b, store_stacker_2_slot_1, 0) with nest 1 sensing no plate",
      lambda: store.store_plate(plate_b, site(store, "store_stacker_2_slot_1"), 0),
    )
    socket.nest_sensors[1] = "PLATE_AVAILABLE"
    await r.step(
      "store_plate(plate_b, store_stacker_5_slot_1, 0) to an occupied slot",
      lambda: store.store_plate(plate_b, site(store, "store_stacker_5_slot_1"), 0),
    )
    await r.step(
      "store_plate(plate_b, store_stacker_2_slot_1, 1) from the wrong tray",
      lambda: store.store_plate(plate_b, site(store, "store_stacker_2_slot_1"), 1),
    )
    await r.step(
      "take_in_plate(0, site=store_stacker_5_slot_1) to an occupied slot",
      lambda: store.take_in_plate(0, site=site(store, "store_stacker_5_slot_1")),
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
    r.check(self, "refusals")

  async def test_unresolved_transfers(self):
    store = SteriStore(host="10.253.253.253", name="store")
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate_a, plate_b = make_plate("plate_a"), make_plate("plate_b")

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
      lambda: store.store_plate(plate_a, site(store, "store_stacker_5_slot_1"), 0),
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
    r.check(self, "unresolved_transfers")

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
    r.check(self, "environment")

  async def test_explicit_racks_and_restore(self):
    out_of_order = PlateCarrier(name="out_of_order", size_x=130, size_y=90, size_z=100)
    for spot in (7, 2):
      out_of_order.assign_child_resource(
        PlateHolder(name=f"spot_{spot}", size_x=127.76, size_y=85.48, size_z=20, pedestal_size_z=0),
        location=Coordinate(0, 0, spot * 20),
        spot=spot,
      )
    stacker = high_res_stacker("stacker", zero_offset=0, slot_height=22.867, slot_count=2)
    store = AmbiStore(host="10.253.253.253", name="store", racks={7: out_of_order, 1: stacker})
    socket = SimulatedSocket()
    r = self.recorder(store, socket)
    plate = make_plate("plate")

    await r.step("setup()", lambda: store.setup())
    await r.step("operator puts plate on tray 0", lambda: put_on_tray(store, socket, 0, plate))
    await r.step(
      "store_plate(plate, spot_7, 0)", lambda: store.store_plate(plate, site(store, "spot_7"), 0)
    )
    await r.step(
      "find_smallest_site_for_plate(plate)", lambda: store.find_smallest_site_for_plate(plate)
    )
    serialized = await r.step("serialize()", lambda: store.serialize())
    r.check(self, "explicit_racks")

    restored = AmbiStore.deserialize(serialized)
    socket = SimulatedSocket()
    r = self.recorder(restored, socket)
    await r.step("setup() of AmbiStore.deserialize(serialize())", lambda: restored.setup())
    await r.step(
      "fetch_plate_to_loading_tray('plate', 1)",
      lambda: restored.fetch_plate_to_loading_tray("plate", 1),
    )
    await r.step(
      "store_plate(plate, stacker_slot_2, 1)",
      lambda: restored.store_plate(
        plate_named(restored, "plate"), site(restored, "stacker_slot_2"), 1
      ),
    )
    await r.step("serialize()", lambda: restored.serialize())
    r.check(self, "explicit_racks_restored")


if __name__ == "__main__":
  unittest.main()
