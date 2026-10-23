"""Simulator tests, and the recording it takes its configuration from."""

import os
import unittest

from pylabrobot.bmg_labtech.clariostar.device import (
  RECORDING_CLARIOSTAR_PLUS,
  CLARIOstar,
  CLARIOstarDevice,
  CLARIOstarPlus,
)
from pylabrobot.bmg_labtech.clariostar.driver.configuration import (
  SERIAL_NUMBER_PLACEHOLDER,
  compute_recording_name,
  configuration_from_json,
  configuration_to_json,
  read_configuration,
)
from pylabrobot.bmg_labtech.clariostar.driver.configuration_tests import decoded
from pylabrobot.bmg_labtech.clariostar.driver.features.drawer_tests import set_location, stored
from pylabrobot.bmg_labtech.clariostar.driver.master_tests import (
  PARAMETERS_REPLY,
  STATUS_IDLE,
  FakeFTDI,
  load_session_replies,
  make_driver,
  parse_status,
)
from pylabrobot.resources import Coordinate, Plate
from pylabrobot.resources.store import handles

LOCATION_IN = Coordinate(10, 20, 30)  # made up: the real ones are not measured yet
LOCATION_OUT = Coordinate(10, -200, 30)


async def make_plate(reader: CLARIOstarDevice, name: str) -> handles.Plate:
  """A Bio-Rad 96-well 200 uL plate in the reader's store."""
  return await stored("biorad_96_wellplate_200uL_Vb", reader.store, name)


async def decoded_with_parameters():
  """The configuration the recorded INIT and stored-parameters replies decode to."""
  io = FakeFTDI()
  io.replies = [STATUS_IDLE, PARAMETERS_REPLY]
  configuration = decoded()
  configuration.update_from_parameters(await make_driver(io).request_parameters())
  return configuration


class RecordingTests(unittest.IsolatedAsyncioTestCase):
  async def test_recording_is_the_decoded_replies(self):
    saved = read_configuration(RECORDING_CLARIOSTAR_PLUS)["device"]
    self.assertEqual(saved, configuration_to_json(await decoded_with_parameters()))

  def test_recording_is_named_from_its_contents(self):
    configuration = configuration_from_json(read_configuration(RECORDING_CLARIOSTAR_PLUS)["device"])
    self.assertEqual(
      compute_recording_name(configuration), os.path.basename(RECORDING_CLARIOSTAR_PLUS)
    )

  async def test_read_back_equals_decoded(self):
    configuration = configuration_from_json(read_configuration(RECORDING_CLARIOSTAR_PLUS)["device"])
    expected = await decoded_with_parameters()
    expected.serial_number = SERIAL_NUMBER_PLACEHOLDER
    self.assertEqual(configuration, expected)


class SimulatorTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.reader = CLARIOstarPlus(simulation=True)
    drawer = self.reader.drawer
    drawer.location_in, drawer.location_out = LOCATION_IN, LOCATION_OUT
    await self.reader.setup()

  async def test_setup_reads_the_recording(self):
    configuration = self.reader.driver.configuration
    self.assertEqual(configuration.model, "CLARIOstarPlus")
    self.assertEqual(configuration.serial_number, SERIAL_NUMBER_PLACEHOLDER)
    self.assertTrue((await self.reader.driver.request_status()).motors_enabled)

  async def test_drawer_moves_the_plate_holder(self):
    await self.reader.drawer.open()
    self.assertTrue(await self.reader.drawer.sense_drawer_open())
    self.assertEqual(await self.reader.plate_holder.handle.get_location(), LOCATION_OUT)
    await self.reader.drawer.close()
    self.assertFalse(await self.reader.drawer.sense_drawer_open())
    self.assertEqual(await self.reader.plate_holder.handle.get_location(), LOCATION_IN)

  async def test_drawer_position_is_read_from_the_resource_model(self):
    await set_location(self.reader.plate_holder.handle, LOCATION_OUT)
    self.assertTrue((await self.reader.driver.request_status()).drawer_open)
    await set_location(self.reader.plate_holder.handle, LOCATION_IN)
    self.assertFalse((await self.reader.driver.request_status()).drawer_open)

  async def test_a_plate_goes_on_the_plate_holder_only(self):
    with self.assertRaises(RuntimeError):
      await self.reader.assign_child_resource(
        await make_plate(self.reader, "plate"), location=Coordinate.zero()
      )
    assert self.reader.body is not None
    children = await self.reader.body.get_children()
    self.assertEqual([child.name for child in children], [self.reader.plate_holder.name])

  async def test_a_plate_needs_the_drawer_sensed_open(self):
    holder = self.reader.plate_holder
    plate = await make_plate(self.reader, "plate")
    with self.assertRaises(RuntimeError):  # not sensed yet
      await holder.assign_child_resource(plate)
    await self.reader.drawer.close()
    with self.assertRaises(RuntimeError):  # sensed closed
      await holder.assign_child_resource(plate)
    await self.reader.drawer.open()
    await holder.assign_child_resource(plate)
    self.assertEqual(await holder.get_resource_held(), plate)

  async def test_a_second_plate_is_refused(self):
    await self.reader.drawer.open()
    holder = self.reader.plate_holder
    await holder.assign_child_resource(await make_plate(self.reader, "first"))
    with self.assertRaises(RuntimeError):
      await holder.assign_child_resource(await make_plate(self.reader, "second"))
    children = await holder.handle.get_children()
    self.assertEqual([child.name for child in children], ["first"])

  async def test_a_plate_comes_off_only_with_the_drawer_open(self):
    await self.reader.drawer.open()
    plate = await make_plate(self.reader, "plate")
    holder = self.reader.plate_holder
    await holder.assign_child_resource(plate)
    await self.reader.drawer.close()
    with self.assertRaises(RuntimeError):
      await holder.unassign_child_resource(plate)
    await self.reader.drawer.open()
    await holder.unassign_child_resource(plate)
    self.assertIsNone(await holder.get_resource_held())

  async def test_stop_with_a_plate_inside_opens_the_drawer_and_raises(self):
    await self.reader.drawer.open()
    await self.reader.plate_holder.assign_child_resource(await make_plate(self.reader, "plate"))
    await self.reader.drawer.close()
    with self.assertRaises(RuntimeError):
      await self.reader.stop()
    self.assertTrue(await self.reader.drawer.sense_drawer_open())
    await self.reader.stop(accept_plate_left_in_device=True)

  async def test_stop_switches_heating_off_and_closes_the_drawer(self):
    temperature_controller = self.reader.temperature_controller
    assert temperature_controller is not None
    await temperature_controller.start_temperature_control(37.0)
    await self.reader.drawer.open()
    await self.reader.stop()
    self.assertIsNone(temperature_controller.target_temperature)
    self.assertFalse(await self.reader.drawer.sense_drawer_open())

  async def test_plate_present_needs_a_plate_and_the_drawer_in(self):
    self.assertFalse(await self.reader.drawer.sense_plate_present())
    await self.reader.drawer.open()
    plate = Plate("plate", size_x=127.76, size_y=85.48, size_z=14.0, ordered_items={})
    await self.reader.plate_holder.assign_child_resource(
      await stored(plate, self.reader.store), location=Coordinate.zero()
    )
    simulated = await self.reader.driver.request_status()
    # As the reader answered with the plate on the plate holder and the drawer out.
    real = parse_status(bytes.fromhex(load_session_replies()["status_drawer_out_plate_on_holder"]))
    self.assertEqual(
      (simulated.drawer_open, simulated.plate_detected), (real.drawer_open, real.plate_detected)
    )
    await self.reader.drawer.close()
    self.assertTrue(await self.reader.drawer.sense_plate_present())

  async def test_convenience_requests_answer_from_the_recording(self):
    driver = self.reader.driver
    self.assertTrue(await driver.request_absorbance_available())
    self.assertEqual(await driver.request_fluorescence_channels(), 1)
    self.assertFalse(await driver.request_well_1536_plates_supported())

  async def test_nothing_reaches_a_wire(self):
    driver = self.reader.driver
    with self.assertRaises(NotImplementedError):
      await driver.send_command(driver.CommandFamily.STATUS)
    with self.assertRaises(NotImplementedError):
      await driver.request_parameters()


class SimulatorWithoutLocationsTests(unittest.IsolatedAsyncioTestCase):
  async def test_drawer_falls_back_to_the_last_move(self):
    reader = CLARIOstarPlus(simulation=True)
    await reader.setup()
    await reader.drawer.open()
    self.assertTrue((await reader.driver.request_status()).drawer_open)

  async def test_convenience_request_before_setup_raises(self):
    with self.assertRaises(RuntimeError):
      await CLARIOstarPlus(simulation=True).driver.request_absorbance_available()


# The driver's asyncio.Lock needs an event loop on Python 3.9: build drivers inside one.
class SimulatorConstructionTests(unittest.IsolatedAsyncioTestCase):
  def test_clariostar_has_no_recording(self):
    with self.assertRaises(ValueError):
      CLARIOstar(simulation=True)

  def test_simulation_takes_no_link(self):
    with self.assertRaises(ValueError):
      CLARIOstarPlus(simulation=True, io=FakeFTDI())


if __name__ == "__main__":
  unittest.main()
