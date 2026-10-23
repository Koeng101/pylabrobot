import unittest
from typing import Any, List, cast

from pylabrobot.hamilton.star.device import RECORDING_STARLET
from pylabrobot.hamilton.star.driver.features.head import HEAD_REFERENCE_SHAFT
from pylabrobot.hamilton.star.driver.features.head96 import Head96
from pylabrobot.hamilton.star.driver.simulator import STARSimulationDriver
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore


class TestSimulatedHead96MasterCommands(unittest.IsolatedAsyncioTestCase):
  """`C0 EP`, `ER`, `EA`, `ED` and `H0 RD` move and read the simulated 96-head's model."""

  async def asyncSetUp(self):
    store = ResourceStore.in_process()
    self.deck = cast(handles.Deck, await store.create("STARLetDeck", name="deck"))
    self.driver = STARSimulationDriver(
      deck=self.deck, declared_configuration_json=RECORDING_STARLET
    )
    await self.driver.setup()
    self.head = cast(Head96, self.driver.head96)
    tip_car = cast(
      handles.Carrier,
      await store.create("hamilton_tip_carrier_L5", name="tip carrier", parent=self.deck, track=1),
    )
    self.tip_rack = cast(
      handles.TipRack,
      await store.create("hamilton_96_tiprack_300uL_filter", name="tip_rack_01", parent=tip_car[1]),
    )
    tip = await self.tip_rack.get_tip_spot("A1").get_tip()
    assert tip is not None
    attributes = await tip.attributes()
    self.tip_length = attributes.size.z - attributes.head_tool.fitting_depth
    plate_car = cast(
      handles.Carrier,
      await store.create(
        "hamilton_plate_carrier_L5_ac", name="plate carrier", parent=self.deck, track=7
      ),
    )
    self.trough_plate = cast(
      handles.Plate,
      await store.create("agenbio_1_troughplate_190mL_Fl", name="trough", parent=plate_car[3]),
    )

  async def send(self, command: str, **kwargs: Any) -> Any:
    return await self.driver.send_command(module="C0", command=command, **kwargs)

  async def piston(self) -> float:
    resp = await self.driver.send_command(module="H0", command="RD", fmt="rd##### (n)")
    increments = cast(List[int], resp["rd"])[1]
    return self.head.configuration.dispensing_drive_increments_to_uL(increments)

  async def where(self) -> List[float]:
    return [
      await self.head.request_x_position(),
      await self.head.request_y_position(),
      await self.head.request_z_position(),
    ]

  async def spot_a1(self):
    return await self.tip_rack.get_tip_spot("A1").get_location_wrt(self.deck, "c", "c", "b")

  async def test_ep_leaves_a1_over_the_spot_and_the_stop_disc_a_tip_above_ze(self):
    await self.head.pick_up_tips(self.tip_rack, minimum_traverse_height_end=245.0)
    spot = await self.spot_a1()
    x, y, z = await self.where()
    self.assertAlmostEqual(x, spot.x, delta=0.05)
    self.assertAlmostEqual(y, spot.y, delta=0.05)
    self.assertAlmostEqual(z, 245.0 + self.tip_length, delta=0.05)

  async def test_er_leaves_the_stop_disc_at_ze(self):
    await self.head.pick_up_tips(self.tip_rack)
    await self.head.drop_tips(self.tip_rack, minimum_traverse_height_end=250.0)
    spot = await self.spot_a1()
    x, y, z = await self.where()
    self.assertAlmostEqual(x, spot.x, delta=0.05)
    self.assertAlmostEqual(y, spot.y, delta=0.05)
    self.assertAlmostEqual(z, 250.0, delta=0.05)

  async def test_ea_moves_the_head_and_draws_blow_out_volume_and_transport_air(self):
    await self.head.pick_up_tips(self.tip_rack)
    trough = self.trough_plate.get_well(0)
    await trough.set_volume(100_000.0)
    await self.send("EA", xs="03000", xd=0, yh="2500", ze="2200", af="01000", bv="00200", vt="050")
    x, y, z = await self.where()
    self.assertAlmostEqual(x, 300.0, delta=0.05)
    self.assertAlmostEqual(y, 250.0, delta=0.05)
    self.assertAlmostEqual(z, 220.0 + self.tip_length, delta=0.05)
    self.assertAlmostEqual(self.driver.head96_dispensing_drive_uL, 125.0)
    self.assertAlmostEqual(await self.piston(), 125.0, delta=0.05)
    self.assertEqual(await trough.get_volume(), 100_000.0)

  async def test_a_negative_x_is_read_back_negative(self):
    await self.send("EA", xs="00100", xd=1, yh="2500", ze="2200", af="00000", bv="00000")
    self.assertAlmostEqual(await self.head.request_x_position(), -10.0, delta=0.05)

  async def test_ed_partial_pushes_volume_and_transport_air_and_draws_stop_back(self):
    await self.send("EA", xs="03000", xd=0, yh="2500", ze="2200", af="01000", bv="00200")
    await self.send("ED", da=0, xs="03000", xd=0, yh="2500", ze="2300", df="00400", ev="020")
    self.assertAlmostEqual(await self.piston(), 82.0, delta=0.05)
    self.assertAlmostEqual(await self.head.request_z_position(), 230.0, delta=0.05)

  async def test_ed_blow_out_pushes_the_blow_out_air_too(self):
    await self.send("EA", xs="03000", xd=0, yh="2500", ze="2200", af="01000", bv="00200")
    await self.send("ED", da=1, xs="03000", xd=0, yh="2500", ze="2300", df="01000", bv="00200")
    self.assertAlmostEqual(await self.piston(), 0.0, delta=0.05)

  async def test_ed_empty_leaves_nothing_in_the_tip(self):
    await self.send("EA", xs="03000", xd=0, yh="2500", ze="2200", af="01000", bv="00200")
    await self.send("ED", da=4, xs="03000", xd=0, yh="2500", ze="2300", df="00100", bv="00000")
    self.assertAlmostEqual(await self.piston(), 0.0, delta=0.05)

  async def test_the_channel_a1_shaft_is_where_the_command_put_it(self):
    await self.send("EA", xs="03000", xd=0, yh="2500", ze="2200", af="00000", bv="00000")
    shaft = self.head.shafts[HEAD_REFERENCE_SHAFT]
    a1 = await shaft.get_location_wrt(self.deck, "c", "c", "b")
    self.assertAlmostEqual(a1.x, 300.0, delta=0.05)
    self.assertAlmostEqual(a1.y, 250.0, delta=0.05)
    self.assertAlmostEqual(a1.z, 220.0, delta=0.05)


if __name__ == "__main__":
  unittest.main()
