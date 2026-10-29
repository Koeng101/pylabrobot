import unittest

from pylabrobot.hamilton.heater_shaker.heater_shaker import HamiltonHeaterShaker, _temperatures
from pylabrobot.hamilton.heater_shaker.simulator import HeaterShakerSimulator
from pylabrobot.resources.server.client import ResourceServer


def _commands(sim: HeaterShakerSimulator):
  return [(c["module"], c["command"]) for c in sim.sent]


class HeaterShakerTests(unittest.IsolatedAsyncioTestCase):
  def setUp(self):
    self.sim = HeaterShakerSimulator()
    self.hs = HamiltonHeaterShaker("hhs", index=2, interface=self.sim)

  def test_it_needs_an_index_and_an_interface(self):
    with self.assertRaises(ValueError):
      HamiltonHeaterShaker("hhs", interface=self.sim)
    with self.assertRaises(ValueError):
      HamiltonHeaterShaker("hhs", index=1)
    with self.assertRaises(ValueError):
      HamiltonHeaterShaker("hhs", index=0, interface=self.sim)

  async def test_setup_initializes_the_lock_and_the_drive_on_its_module(self):
    await self.hs.setup()
    self.assertEqual(_commands(self.sim), [("T2", "LI"), ("T2", "SI")])
    self.assertIsNone(self.hs.resource)

  async def test_a_shake_for_a_duration_locks_shakes_stops_and_unlocks(self):
    await self.hs.shake(speed=800, duration=0)
    self.assertEqual([c["command"] for c in self.sim.sent], ["LP", "SB", "RD", "SC", "SW", "LP"])
    self.assertEqual(self.sim.sent[0]["lp"], 1)
    self.assertEqual(
      {k: self.sim.sent[1][k] for k in ("st", "sv", "sr")}, {"st": 0, "sv": "0800", "sr": "01000"}
    )
    self.assertEqual(self.sim.sent[-1]["lp"], 0)
    self.assertFalse(await self.hs.get_is_shaking())

  async def test_a_shake_without_a_duration_keeps_shaking(self):
    await self.hs.shake(speed=1200)
    self.assertTrue(await self.hs.get_is_shaking())
    await self.hs.stop()
    self.assertFalse(await self.hs.get_is_shaking())

  async def test_a_shake_out_of_range_is_refused_before_it_starts(self):
    with self.assertRaises(ValueError):
      await self.hs.shake(speed=5000)
    with self.assertRaises(ValueError):
      await self.hs.shake(speed=800, acceleration=100)
    self.assertNotIn("SB", [c["command"] for c in self.sim.sent])

  async def test_it_heats_but_does_not_cool(self):
    await self.hs.set_temperature(37)
    self.assertEqual(self.sim.sent[-1]["ta"], "0370")
    await self.hs.wait_for_temperature()
    self.assertEqual(await self.hs.get_temperature(), 37.0)
    with self.assertRaises(ValueError):
      await self.hs.set_temperature(30)
    sent = len(self.sim.sent)
    await self.hs.set_temperature(30, passive=True)
    self.assertNotIn("TA", [c["command"] for c in self.sim.sent[sent:]])
    with self.assertRaises(ValueError):
      await self.hs.set_temperature(120)

  async def test_a_wait_needs_a_temperature_set(self):
    with self.assertRaises(RuntimeError):
      await self.hs.wait_for_temperature()
    await self.hs.set_temperature(37)
    await self.hs.deactivate()
    with self.assertRaises(RuntimeError):
      await self.hs.wait_for_temperature()

  async def test_the_temperature_it_was_set_to_is_kept_until_it_is_turned_off(self):
    self.assertIsNone(self.hs.target_temperature)
    await self.hs.set_temperature(37)
    self.assertEqual(self.hs.target_temperature, 37)
    await self.hs.deactivate()
    self.assertIsNone(self.hs.target_temperature)

  async def test_a_hold_waits_and_sends_nothing(self):
    await self.hs.hold_temperature(0)
    self.assertEqual(self.sim.sent, [])
    with self.assertRaises(ValueError):
      await self.hs.hold_temperature(-1)

  async def test_a_shake_without_a_timeout_starts(self):
    await self.hs.shake(speed=800, timeout=None)
    self.assertTrue(await self.hs.get_is_shaking())

  def test_a_temperature_reply_gives_the_middle_and_the_edge(self):
    self.assertEqual(_temperatures("T1RTid0001er00rt+0256 +0257"), (25.6, 25.7))


class PlateHolderTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.server = ResourceServer.local()
    self.sim = HeaterShakerSimulator()

  async def test_setup_finds_its_plate_holder_by_its_name(self):
    made = await self.server.create("hamilton_heater_shaker", "hhs_1")
    hs = HamiltonHeaterShaker("hhs_1", index=1, interface=self.sim, resource_server=self.server)
    await hs.setup()
    self.assertEqual(hs.resource, made)

  async def test_setup_without_its_plate_holder_fails_before_it_sends_anything(self):
    hs = HamiltonHeaterShaker("hhs_1", index=1, interface=self.sim, resource_server=self.server)
    with self.assertRaisesRegex(ValueError, "hhs_1"):
      await hs.setup()
    self.assertEqual(self.sim.sent, [])

  async def test_a_resource_of_its_name_that_is_not_a_heater_shaker_is_not_its_own(self):
    await self.server.create("PLT_CAR_L5AC_A00", "hhs_1")
    hs = HamiltonHeaterShaker("hhs_1", index=1, interface=self.sim, resource_server=self.server)
    with self.assertRaises(ValueError):
      await hs.setup()


if __name__ == "__main__":
  unittest.main()
