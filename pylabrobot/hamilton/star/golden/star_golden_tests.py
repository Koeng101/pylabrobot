"""Golden records of what a simulated STAR does today: what it is sent and what its resources are
left as, scenario by scenario.

Each scenario drives the public API of a simulated device, `STAR(simulation=True)` and its
siblings, and records it through `STARRecorder`. The JSON files beside this one are the records;
`PLR_UPDATE_GOLDEN=1` rewrites them.
"""

import pathlib
import unittest
from typing import Any, Dict, List, cast

from pylabrobot.hamilton.star.device import (
  RECORDING_STAR_HEAD384,
  STAR,
  STARDevice,
  STARlet,
  STARPlus,
)
from pylabrobot.hamilton.star.driver.features.autoload import Autoload
from pylabrobot.hamilton.star.driver.features.core_grippers import CoreGrippers
from pylabrobot.hamilton.star.driver.features.head96 import Head96
from pylabrobot.hamilton.star.driver.features.iswap import iSWAP
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.star.driver.lld_mode import LLDMode
from pylabrobot.hamilton.star.golden.recorder import STARRecorder
from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.server import build, handles
from pylabrobot.testing.golden import check_golden

HERE = pathlib.Path(__file__).parent


class _Scenario(unittest.IsolatedAsyncioTestCase):
  """Tip and volume tracking on, as a protocol that books what it moves runs."""

  async def built(self, device: STARDevice, call: str) -> STARRecorder:
    """Start recording a device whose resources the scenario has built, tracking everything on it.

    Args:
      device: the device, its resources made.
      call: how it was built, as a scenario writes it.
    """
    assert device.body is not None
    await device.body.set_tip_tracking(True)
    await device.body.set_volume_tracking(True)
    recorder = STARRecorder(device)
    await recorder.built(call)
    return recorder

  def check(self, name: str, recorder: STARRecorder) -> None:
    check_golden(self, HERE / f"{name}.json", recorder.record())


class SetupTests(_Scenario):
  """What each frame builds and sends at setup, and at stop."""

  async def _set_up(self, name: str, device: STARDevice, built: str) -> None:
    await device.create_resources()
    recorder = await self.built(device, built)
    await recorder.step("setup()", device.setup())
    await recorder.step("stop()", device.stop())
    self.check(name, recorder)

  async def test_star(self):
    await self._set_up("setup_star", STAR(simulation=True), "STAR(simulation=True)")

  async def test_starlet(self):
    await self._set_up("setup_starlet", STARlet(simulation=True), "STARlet(simulation=True)")

  async def test_starplus(self):
    await self._set_up("setup_starplus", STARPlus(simulation=True), "STARPlus(simulation=True)")

  async def test_star_with_a_384_head(self):
    await self._set_up(
      "setup_star_head384",
      STAR(simulation=True, declared_configuration_json=RECORDING_STAR_HEAD384),
      "STAR(simulation=True, declared_configuration_json=RECORDING_STAR_HEAD384)",
    )

  async def test_a_turned_starlet_with_its_side_panel(self):
    device = STARlet(
      simulation=True, name="turned", extension_housing=False, left_side_panel_installed=True
    )
    room = await device.resource_server.create(
      build.resource("room", Coordinate(9000, 9000, 3000)), name="room"
    )
    await device.create_resources()
    assert device.body is not None
    await device.body.rotate(z=90)
    await room.assign_child_resource(device.body, location=Coordinate(4000, 4000, 0))
    await self._set_up(
      "setup_turned_starlet",
      device,
      "STARlet(simulation=True, name='turned', extension_housing=False, "
      "left_side_panel_installed=True), turned 90 deg in a room at (4000, 4000, 0)",
    )


class PipettesTests(_Scenario):
  """The eight channels of a STARlet: tips, transfers, probing, and what a failure leaves."""

  async def build(self, built: str, partly_filled_rack: bool = False) -> STARRecorder:
    """A STARlet with a tip rack on track 1 and, beside it, a second rack holding only its last
    ten tips or a plate on track 7 with 200 uL in every well."""
    self.star = STARlet(simulation=True)
    await self.star.create_resources()
    server = self.star.resource_server
    tip_carrier = cast(
      handles.Carrier,
      await server.create(
        "hamilton_tip_carrier_L5", name="tip_carrier", parent=self.star.deck, track=1
      ),
    )
    self.tips = cast(
      handles.TipRack,
      await server.create("hamilton_96_tiprack_300uL_filter", name="tips", parent=tip_carrier[1]),
    )
    if partly_filled_rack:
      self.more_tips = cast(
        handles.TipRack,
        await server.create(
          "hamilton_96_tiprack_300uL_filter", name="more_tips", parent=tip_carrier[2]
        ),
      )
      await self.more_tips.set_tip_state([index >= 86 for index in range(96)])
    else:
      plate_carrier = cast(
        handles.Carrier,
        await server.create(
          "hamilton_plate_carrier_L5_ac", name="plate_carrier", parent=self.star.deck, track=7
        ),
      )
      self.plate = cast(
        handles.Plate,
        await server.create("cor_96_wellplate_360uL_Fb", name="plate", parent=plate_carrier[0]),
      )
      await self.plate.set_well_volumes(200.0)
    return await self.built(self.star, built)

  @property
  def pipettes(self) -> Pipettes:
    assert self.star.pipettes is not None
    return self.star.pipettes

  async def test_a_transfer_protocol(self):
    r = await self.build("STARlet with tips on track 1 and plate on track 7, 200 uL in every well")
    await r.step("setup()", self.star.setup())
    p, tips, plate = self.pipettes, self.tips, self.plate
    await r.step("pick_up_tips(tips['A1:H1'])", p.pick_up_tips(tips.get_tip_spots("A1:H1")))
    await r.step(
      "aspirate(plate['A1:H1'], [50.0] * 8)", p.aspirate(plate.get_wells("A1:H1"), [50.0] * 8)
    )
    await r.step(
      "dispense(plate['A2:H2'], [50.0] * 8)", p.dispense(plate.get_wells("A2:H2"), [50.0] * 8)
    )
    await r.step("drop_tips(tips['A1:H1'])", p.drop_tips(tips.get_tip_spots("A1:H1")))
    await r.step("pick_up_tips(tips['A2:H2'])", p.pick_up_tips(tips.get_tip_spots("A2:H2")))
    await r.step(
      "probe_liquid_heights(plate['A1:D1'])", p.probe_liquid_heights(plate.get_wells("A1:D1"))
    )
    await r.step(
      "probe_liquid_volumes(plate['A1:D1'])", p.probe_liquid_volumes(plate.get_wells("A1:D1"))
    )
    await r.step(
      "aspirate(plate['A3:D3'], [20.0] * 4, lld_mode=LLDMode.CAPACITIVE)",
      p.aspirate(plate.get_wells("A3:D3"), [20.0] * 4, lld_mode=LLDMode.CAPACITIVE),
    )
    await r.step(
      "dispense(plate['A4:D4'], [20.0] * 4)", p.dispense(plate.get_wells("A4:D4"), [20.0] * 4)
    )
    await r.step("empty_tip(0)", p.empty_tip(0))
    await r.step("return_tips()", p.return_tips())
    await r.step(
      "pick_up_tips(tips['A3:B3'], use_channels=[0, 1])",
      p.pick_up_tips(tips.get_tip_spots("A3:B3"), use_channels=[0, 1]),
    )
    await r.step(
      "drop_tips(tips['A1:B1'], use_channels=[0, 1]), both spots holding a tip",
      p.drop_tips(tips.get_tip_spots("A1:B1"), use_channels=[0, 1]),
    )
    await r.step("discard_tips()", p.discard_tips())
    await r.step("stop()", self.star.stop())
    self.check("pipettes_transfer", r)

  async def test_failures_part_way(self):
    r = await self.build("STARlet with tips on track 1 and plate on track 7, 200 uL in every well")
    await r.step("setup()", self.star.setup())
    p, tips, plate, driver = self.pipettes, self.tips, self.plate, r.driver

    def channels_0_1_and_3_hold_their_tips(_: Dict[str, Any]) -> None:
      driver.tips_mounted[:4] = [True, True, False, True]

    r.fail("C0", "TP", "C0TPid0000er99/00 P308/75", before=channels_0_1_and_3_hold_their_tips)
    await r.step(
      "pick_up_tips(tips['A1:D1']), channel 2 meeting no tip",
      p.pick_up_tips(tips.get_tip_spots("A1:D1")),
    )

    def channel_1_drew_nothing(_: Dict[str, Any]) -> None:
      driver.dispensing_drive_uL[1] = 0.0

    r.fail("C0", "AS", "C0ASid0000er99/00", before=channel_1_drew_nothing)
    await r.step(
      "aspirate(plate['A1:B1'], piston_volumes=[50.0, 20.0]), stopping before channel 1 drew",
      p.aspirate(plate.get_wells("A1:B1"), piston_volumes=[50.0, 20.0]),
    )
    await r.step(
      "aspirate(plate['C1'], piston_volumes=[30.0], use_channels=[3])",
      p.aspirate([plate.get_well("C1")], piston_volumes=[30.0], use_channels=[3]),
    )
    await r.step(
      "aspirate(plate['D1'], piston_volumes=[5000.0], use_channels=[3]), past the piston",
      p.aspirate([plate.get_well("D1")], piston_volumes=[5000.0], use_channels=[3]),
    )
    standing = dict(driver.dispensing_drive_uL)

    def channel_3_gave_nothing(_: Dict[str, Any]) -> None:
      driver.dispensing_drive_uL[3] = standing[3]

    r.fail("C0", "DS", "C0DSid0000er99/00", before=channel_3_gave_nothing)
    await r.step(
      "dispense(plate['A2:B2'], piston_volumes=[40.0, 30.0], use_channels=[0, 3]), "
      "stopping before channel 3 gave",
      p.dispense(plate.get_wells("A2:B2"), piston_volumes=[40.0, 30.0], use_channels=[0, 3]),
    )
    await r.step("initialize()", p.initialize())
    await r.step("stop()", self.star.stop())
    self.check("pipettes_failures", r)

  async def test_tip_inventory(self):
    r = await self.build(
      "STARlet with tips and more_tips (its last ten spots filled) on track 1",
      partly_filled_rack=True,
    )
    await r.step("setup()", self.star.setup())
    p, tips = self.pipettes, self.tips
    await r.step(
      "consolidate_tip_inventory([more_tips], use_channels=[1, 3, 5])",
      p.consolidate_tip_inventory([self.more_tips], use_channels=[1, 3, 5]),
    )

    def channel_0_holds_its_tip(_: Dict[str, Any]) -> None:
      r.driver.tips_mounted[:2] = [True, False]

    r.fail("C0", "TP", "C0TPid0000er99/00 P208/75", before=channel_0_holds_its_tip)
    await r.step(
      "probe_tip_presence_via_pickup(tips['A1:B1'], use_channels=[0, 1]), B1 empty on the device",
      p.probe_tip_presence_via_pickup(tips.get_tip_spots("A1:B1"), use_channels=[0, 1]),
    )
    # The inventory picks up two at a time: the third pick-up is E2 and F2.
    r.fail("C0", "TP", "C0TPid0000er99/00 P208/75", before=channel_0_holds_its_tip, skip=2)
    await r.step(
      "probe_tip_inventory(tips['A2:H2'], use_channels=[0, 1]), F2 empty on the device",
      p.probe_tip_inventory(tips.get_tip_spots("A2:H2"), use_channels=[0, 1]),
    )
    await r.step("stop()", self.star.stop())
    self.check("pipettes_tip_inventory", r)


class Head96Tests(_Scenario):
  """The 96-head of a STARlet: tips, a transfer, a mix, probing, and what a failure leaves."""

  async def test_a_protocol_and_its_failures(self):
    star = STARlet(simulation=True)
    await star.create_resources()
    server = star.resource_server
    tip_carrier = cast(
      handles.Carrier,
      await server.create("hamilton_tip_carrier_L5", name="tip_carrier", parent=star.deck, track=1),
    )
    tips = cast(
      handles.TipRack,
      await server.create("hamilton_96_tiprack_300uL_filter", name="tips", parent=tip_carrier[1]),
    )
    gappy = cast(
      handles.TipRack,
      await server.create("hamilton_96_tiprack_300uL_filter", name="gappy", parent=tip_carrier[2]),
    )
    plate_carrier = cast(
      handles.Carrier,
      await server.create(
        "hamilton_plate_carrier_L5_ac", name="plate_carrier", parent=star.deck, track=7
      ),
    )
    source = cast(
      handles.Plate,
      await server.create("cor_96_wellplate_360uL_Fb", name="source", parent=plate_carrier[1]),
    )
    trough = cast(
      handles.Plate,
      await server.create("agenbio_1_troughplate_190mL_Fl", name="trough", parent=plate_carrier[3]),
    )
    await source.set_well_volumes(200.0)
    await trough.set_well_volumes(100_000.0)
    await gappy.set_tip_state([identifier not in ("A1", "B2") for identifier in gappy.identifiers])
    r = await self.built(
      star, "STARlet with tips and gappy (A1 and B2 empty) on track 1, source and trough on track 7"
    )

    await r.step("setup()", star.setup())
    assert isinstance(star.head96, Head96)
    head = star.head96
    await r.step("pick_up_tips(tips)", head.pick_up_tips(tips))
    await r.step("aspirate(source, 50.0)", head.aspirate(source, 50.0))
    await r.step("dispense(source, 50.0)", head.dispense(source, 50.0))
    await r.step("dispense(source, piston_volume=40.0)", head.dispense(source, piston_volume=40.0))
    await r.step(
      "mix(trough, Mix(volume=50.0, repetitions=3, flow_rate=100.0))",
      head.mix(trough, Mix(volume=50.0, repetitions=3, flow_rate=100.0)),
    )
    await r.step("probe_liquid_height(trough)", head.probe_liquid_height(trough))
    await r.step("probe_liquid_volume(trough)", head.probe_liquid_volume(trough))
    await r.step(
      "aspirate(trough, 20.0, lld_mode=LLDMode.CAPACITIVE)",
      head.aspirate(trough, 20.0, lld_mode=LLDMode.CAPACITIVE),
    )
    await r.step("dispense(trough, 20.0)", head.dispense(trough, 20.0))
    await r.step("move_to_xy_position(300.0, 250.0)", head.move_to_xy_position(300.0, 250.0))
    await r.step("return_tips()", head.return_tips())
    await r.step("pick_up_tips(tips)", head.pick_up_tips(tips))

    def the_piston_stopped_at_20_uL(_: Dict[str, Any]) -> None:
      r.driver.head96_dispensing_drive_uL = 20.0

    r.fail("C0", "EA", "C0EAid0000er99/00", before=the_piston_stopped_at_20_uL)
    await r.step(
      "aspirate(source, piston_volume=50.0), stopping at 20 uL",
      head.aspirate(source, piston_volume=50.0),
    )
    await r.step("discard_tips()", head.discard_tips())
    r.fail("C0", "EP", "C0EPid0000er99/00")
    await r.step("pick_up_tips(gappy), failing", head.pick_up_tips(gappy))
    await r.step("pick_up_tips(gappy)", head.pick_up_tips(gappy))
    await r.step(
      "probe_liquid_height(trough, lld_sensor='A1 or B2'), no tips on those channels",
      head.probe_liquid_height(trough, lld_sensor="A1 or B2"),
    )
    r.fail("C0", "ER", "C0ERid0000er99/00")
    await r.step("drop_tips(gappy), failing", head.drop_tips(gappy))
    await r.step("drop_tips(gappy)", head.drop_tips(gappy))
    await r.step("stop()", star.stop())
    self.check("head96", r)


class CoreGrippersTests(_Scenario):
  """A plate moved by the CoRe grippers of a STAR, and what a failure leaves."""

  async def test_a_plate_moved_and_returned(self):
    star = STAR(simulation=True)
    await star.create_resources()
    carrier = await star.resource_server.create(
      "hamilton_plate_carrier_L5_ac", name="plate_carrier", parent=star.deck, track=30
    )
    assert isinstance(carrier, handles.Carrier)
    plate = await star.resource_server.create(
      "azenta_96_wellplate_200uL_Vb_4titudeframestar", name="plate", parent=carrier[0]
    )
    r = await self.built(star, "STAR with plate on plate_carrier[0], track 30")

    await r.step("setup()", star.setup())
    assert isinstance(star.core_grippers, CoreGrippers)
    grippers = star.core_grippers
    await r.step("pick_up_tools()", grippers.pick_up_tools())
    await r.step(
      "pick_up_resource(plate, pickup_distance_from_top=5)",
      grippers.pick_up_resource(plate, pickup_distance_from_top=5),
    )
    await r.step("place_resource(plate_carrier[2])", grippers.place_resource(carrier[2]))
    r.fail("C0", "ZP", "C0ZPid0000er99/00")
    await r.step(
      "pick_up_resource(plate, pickup_distance_from_top=5), failing",
      grippers.pick_up_resource(plate, pickup_distance_from_top=5),
    )
    await r.step(
      "pick_up_resource(plate, pickup_distance_from_top=5)",
      grippers.pick_up_resource(plate, pickup_distance_from_top=5),
    )
    r.fail("C0", "ZR", "C0ZRid0000er99/00")
    await r.step(
      "place_resource(Coordinate(400.0, 200.0, 100.0)), failing",
      grippers.place_resource(Coordinate(400.0, 200.0, 100.0)),
    )
    await r.step(
      "place_resource(Coordinate(400.0, 200.0, 100.0))",
      grippers.place_resource(Coordinate(400.0, 200.0, 100.0)),
    )
    await r.step(
      "pick_up_resource(plate, pickup_distance_from_top=5)",
      grippers.pick_up_resource(plate, pickup_distance_from_top=5),
    )
    await r.step("return_resource()", grippers.return_resource())
    await r.step("return_tools()", grippers.return_tools())

    def the_front_channel_senses_nothing(value: Dict[str, List[int]]) -> Dict[str, List[int]]:
      sensed = list(value["rt"])
      sensed[7] = 0
      return {"rt": sensed}

    r.answer("C0", "RT", the_front_channel_senses_nothing)
    await r.step(
      "pick_up_tools(), the front channel sensing nothing after",
      grippers.pick_up_tools(),
    )
    await r.step("stop()", star.stop())
    self.check("core_grippers", r)


class ArmTests(_Scenario):
  """The iSWAP's pose and jaws, and the X-arm, on a STAR."""

  async def test_iswap_pose_and_jaws(self):
    star = STAR(simulation=True)
    await star.create_resources()
    r = await self.built(star, "STAR(simulation=True)")
    await r.step("setup()", star.setup())
    assert isinstance(star.iswap, iSWAP)
    iswap = star.iswap
    await r.step(
      "elbow_move_to_y_position(400.0), the channels in the way",
      iswap.elbow_move_to_y_position(400.0),
    )
    await r.step(
      "elbow_move_to_y_position(400.0, make_space=True)",
      iswap.elbow_move_to_y_position(400.0, make_space=True),
    )
    await r.step("elbow_move_to_z_position(250.0)", iswap.elbow_move_to_z_position(250.0))
    await r.step(
      "rotate_to_angles(elbow_relative_angle=90.0, gripper_relative_angle=90.0)",
      iswap.rotate_to_angles(elbow_relative_angle=90.0, gripper_relative_angle=90.0),
    )
    await r.step(
      "rotate_to_angles(elbow_absolute_angle='front', gripper_absolute_angle='front')",
      iswap.rotate_to_angles(elbow_absolute_angle="front", gripper_absolute_angle="front"),
    )
    await r.step(
      "rotate_to_angles(elbow_relative_angle=30.0, gripper_relative_angle=-45.0)",
      iswap.rotate_to_angles(elbow_relative_angle=30.0, gripper_relative_angle=-45.0),
    )
    await r.step("gripper_move_to_jaw_position(100.0)", iswap.gripper_move_to_jaw_position(100.0))
    await r.step("gripper_open()", iswap.gripper_open())
    await r.step("gripper_close()", iswap.gripper_close())
    await r.step("elbow_move_to_x_position(500.0)", iswap.elbow_move_to_x_position(500.0))
    await r.step(
      "elbow_move_to_y_position(10000.0), out of reach",
      iswap.elbow_move_to_y_position(10_000.0),
    )
    await r.step("park()", iswap.park())
    await r.step("stop()", star.stop())
    self.check("iswap", r)

  async def test_x_arm(self):
    star = STAR(simulation=True)
    await star.create_resources()
    r = await self.built(star, "STAR(simulation=True)")
    await r.step("setup()", star.setup())
    arm = star.x_arm
    await r.step("move_to_x_position(600.0)", arm.move_to_x_position(600.0))
    await r.step("move_x_relative(-100.0)", arm.move_x_relative(-100.0))
    await r.step("move_to_x_position(10000.0), out of reach", arm.move_to_x_position(10_000.0))
    await r.step("stop()", star.stop())
    self.check("x_arm", r)


class AutoloadTests(_Scenario):
  """A carrier loaded and unloaded by the autoload of a STAR."""

  async def test_load_and_unload(self):
    star = STAR(simulation=True)
    await star.create_resources()
    carrier = await star.resource_server.create(
      "hamilton_plate_carrier_L5_ac", name="carrier", parent=star.deck, track=20
    )
    r = await self.built(star, "STAR with carrier on track 20")
    await r.step("setup()", star.setup())
    assert isinstance(star.autoload, Autoload)
    autoload = star.autoload
    await r.step("move_to_track(10)", autoload.move_to_track(10))
    await r.step("load_carrier(carrier), the tray sensing none", autoload.load_carrier(carrier))

    # The simulated tray is always empty: this one senses the carrier, after asking as usual. The
    # simulator's own autoload, which is the device's unless the device is served elsewhere.
    simulated = r.driver.autoload
    assert simulated is not None
    sense = simulated.sense_carrier_presence_on_single_loading_tray_track

    async def on_the_tray(track: int, park_after: bool = True) -> bool:
      await sense(track, park_after=park_after)
      return True

    simulated.sense_carrier_presence_on_single_loading_tray_track = on_the_tray  # type: ignore[method-assign]
    await r.step(
      "load_carrier(carrier, barcode_reading=True), the tray sensing it",
      autoload.load_carrier(carrier, barcode_reading=True),
    )
    simulated.sense_carrier_presence_on_single_loading_tray_track = sense  # type: ignore[method-assign]
    await r.step("unload_carrier(carrier)", autoload.unload_carrier(carrier))
    await r.step("park()", autoload.park())
    await r.step("stop()", star.stop())
    self.check("autoload", r)


if __name__ == "__main__":
  unittest.main()
