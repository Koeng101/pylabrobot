# mypy: disable-error-code="method-assign,attr-defined"
"""Tests for misc RPCs: firmware queries, cover, config, HHS, pump, X-arm, special."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestFirmwareQueryRPCs:
  @pytest.mark.asyncio
  async def test_request_firmware_version(self, star_service: StarServiceFixture):
    star_service.backend.request_firmware_version = unittest.mock.AsyncMock()
    await star_service.remote.request_firmware_version()
    star_service.backend.request_firmware_version.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_device_serial_number(self, star_service: StarServiceFixture):
    star_service.backend.request_device_serial_number = unittest.mock.AsyncMock(
      return_value="SN12345"
    )
    result = await star_service.remote.request_device_serial_number()
    assert result == "SN12345"

  @pytest.mark.asyncio
  async def test_request_error_code(self, star_service: StarServiceFixture):
    star_service.backend.request_error_code = unittest.mock.AsyncMock()
    await star_service.remote.request_error_code()
    star_service.backend.request_error_code.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_master_status(self, star_service: StarServiceFixture):
    star_service.backend.request_master_status = unittest.mock.AsyncMock()
    await star_service.remote.request_master_status()
    star_service.backend.request_master_status.assert_called_once()


class TestCoverRPCs:
  @pytest.mark.asyncio
  async def test_lock_cover(self, star_service: StarServiceFixture):
    star_service.backend.lock_cover = unittest.mock.AsyncMock()
    await star_service.remote.lock_cover()
    star_service.backend.lock_cover.assert_called_once()

  @pytest.mark.asyncio
  async def test_unlock_cover(self, star_service: StarServiceFixture):
    star_service.backend.unlock_cover = unittest.mock.AsyncMock()
    await star_service.remote.unlock_cover()
    star_service.backend.unlock_cover.assert_called_once()

  @pytest.mark.asyncio
  async def test_disable_cover_control(self, star_service: StarServiceFixture):
    star_service.backend.disable_cover_control = unittest.mock.AsyncMock()
    await star_service.remote.disable_cover_control()
    star_service.backend.disable_cover_control.assert_called_once()

  @pytest.mark.asyncio
  async def test_enable_cover_control(self, star_service: StarServiceFixture):
    star_service.backend.enable_cover_control = unittest.mock.AsyncMock()
    await star_service.remote.enable_cover_control()
    star_service.backend.enable_cover_control.assert_called_once()

  @pytest.mark.asyncio
  async def test_set_cover_output(self, star_service: StarServiceFixture):
    star_service.backend.set_cover_output = unittest.mock.AsyncMock()
    await star_service.remote.set_cover_output(output=3)
    star_service.backend.set_cover_output.assert_called_once_with(output=3)

  @pytest.mark.asyncio
  async def test_reset_output(self, star_service: StarServiceFixture):
    star_service.backend.reset_output = unittest.mock.AsyncMock()
    await star_service.remote.reset_output(output=5)
    star_service.backend.reset_output.assert_called_once_with(output=5)

  @pytest.mark.asyncio
  async def test_request_cover_open(self, star_service: StarServiceFixture):
    star_service.backend.request_cover_open = unittest.mock.AsyncMock(return_value=True)
    result = await star_service.remote.request_cover_open()
    assert result is True


class TestHHSRPCs:
  @pytest.mark.asyncio
  async def test_send_hhs_command(self, star_service: StarServiceFixture):
    star_service.backend.send_hhs_command = unittest.mock.AsyncMock(return_value="OK")
    result = await star_service.remote.send_hhs_command(index=1, command="START")
    assert result == "OK"
    star_service.backend.send_hhs_command.assert_called_once_with(index=1, command="START")

  @pytest.mark.asyncio
  async def test_check_type_is_hhc(self, star_service: StarServiceFixture):
    star_service.backend.check_type_is_hhc = unittest.mock.AsyncMock()
    await star_service.remote.check_type_is_hhc(device_number=2)
    star_service.backend.check_type_is_hhc.assert_called_once_with(device_number=2)

  @pytest.mark.asyncio
  async def test_initialize_hhc(self, star_service: StarServiceFixture):
    star_service.backend.initialize_hhc = unittest.mock.AsyncMock(return_value="INIT_OK")
    result = await star_service.remote.initialize_hhc(device_number=1)
    assert result == "INIT_OK"
    star_service.backend.initialize_hhc.assert_called_once_with(device_number=1)

  @pytest.mark.asyncio
  async def test_start_temperature_control_at_hhc(self, star_service: StarServiceFixture):
    star_service.backend.start_temperature_control_at_hhc = unittest.mock.AsyncMock()
    await star_service.remote.start_temperature_control_at_hhc(device_number=1, temperature=37.5)
    star_service.backend.start_temperature_control_at_hhc.assert_called_once_with(
      device_number=1, temperature=37.5
    )

  @pytest.mark.asyncio
  async def test_get_temperature_at_hhc(self, star_service: StarServiceFixture):
    star_service.backend.get_temperature_at_hhc = unittest.mock.AsyncMock(
      return_value={"current": 36.8, "target": 37.0}
    )
    result = await star_service.remote.get_temperature_at_hhc(device_number=1)
    assert result == {"current": 36.8, "target": 37.0}
    star_service.backend.get_temperature_at_hhc.assert_called_once_with(device_number=1)

  @pytest.mark.asyncio
  async def test_query_whether_temperature_reached_at_hhc(self, star_service: StarServiceFixture):
    star_service.backend.query_whether_temperature_reached_at_hhc = unittest.mock.AsyncMock()
    await star_service.remote.query_whether_temperature_reached_at_hhc(device_number=1)
    star_service.backend.query_whether_temperature_reached_at_hhc.assert_called_once_with(
      device_number=1
    )

  @pytest.mark.asyncio
  async def test_stop_temperature_control_at_hhc(self, star_service: StarServiceFixture):
    star_service.backend.stop_temperature_control_at_hhc = unittest.mock.AsyncMock()
    await star_service.remote.stop_temperature_control_at_hhc(device_number=1)
    star_service.backend.stop_temperature_control_at_hhc.assert_called_once_with(device_number=1)


class TestConfigRPCs:
  @pytest.mark.asyncio
  async def test_set_single_step_mode(self, star_service: StarServiceFixture):
    star_service.backend.set_single_step_mode = unittest.mock.AsyncMock()
    await star_service.remote.set_single_step_mode(single_step_mode=True)
    star_service.backend.set_single_step_mode.assert_called_once_with(single_step_mode=True)

  @pytest.mark.asyncio
  async def test_halt(self, star_service: StarServiceFixture):
    star_service.backend.halt = unittest.mock.AsyncMock()
    await star_service.remote.halt()
    star_service.backend.halt.assert_called_once()

  @pytest.mark.asyncio
  async def test_trigger_next_step(self, star_service: StarServiceFixture):
    star_service.backend.trigger_next_step = unittest.mock.AsyncMock()
    await star_service.remote.trigger_next_step()
    star_service.backend.trigger_next_step.assert_called_once()

  @pytest.mark.asyncio
  async def test_save_all_cycle_counters(self, star_service: StarServiceFixture):
    star_service.backend.save_all_cycle_counters = unittest.mock.AsyncMock()
    await star_service.remote.save_all_cycle_counters()
    star_service.backend.save_all_cycle_counters.assert_called_once()

  @pytest.mark.asyncio
  async def test_set_not_stop(self, star_service: StarServiceFixture):
    star_service.backend.set_not_stop = unittest.mock.AsyncMock()
    await star_service.remote.set_not_stop(non_stop=True)
    star_service.backend.set_not_stop.assert_called_once_with(non_stop=True)

  @pytest.mark.asyncio
  async def test_configure_node_names(self, star_service: StarServiceFixture):
    star_service.backend.configure_node_names = unittest.mock.AsyncMock()
    await star_service.remote.configure_node_names()
    star_service.backend.configure_node_names.assert_called_once()

  @pytest.mark.asyncio
  async def test_set_deck_data(self, star_service: StarServiceFixture):
    star_service.backend.set_deck_data = unittest.mock.AsyncMock()
    await star_service.remote.set_deck_data(data_index=2, data_stream="abc123")
    star_service.backend.set_deck_data.assert_called_once_with(data_index=2, data_stream="abc123")


class TestXArmRPCs:
  @pytest.mark.asyncio
  async def test_position_left_x_arm(self, star_service: StarServiceFixture):
    star_service.backend.position_left_x_arm = unittest.mock.AsyncMock()
    await star_service.remote.position_left_x_arm(x_position=1000)
    star_service.backend.position_left_x_arm.assert_called_once_with(x_position=1000)

  @pytest.mark.asyncio
  async def test_position_right_x_arm(self, star_service: StarServiceFixture):
    star_service.backend.position_right_x_arm = unittest.mock.AsyncMock()
    await star_service.remote.position_right_x_arm(x_position=2000)
    star_service.backend.position_right_x_arm.assert_called_once_with(x_position=2000)

  @pytest.mark.asyncio
  async def test_request_left_x_arm_position(self, star_service: StarServiceFixture):
    star_service.backend.request_left_x_arm_position = unittest.mock.AsyncMock(return_value=1500.0)
    result = await star_service.remote.request_left_x_arm_position()
    assert result == 1500.0

  @pytest.mark.asyncio
  async def test_request_right_x_arm_position(self, star_service: StarServiceFixture):
    star_service.backend.request_right_x_arm_position = unittest.mock.AsyncMock(return_value=2500.0)
    result = await star_service.remote.request_right_x_arm_position()
    assert result == 2500.0

  @pytest.mark.asyncio
  async def test_request_right_x_arm_last_collision_type(self, star_service: StarServiceFixture):
    star_service.backend.request_right_x_arm_last_collision_type = unittest.mock.AsyncMock(
      return_value=True
    )
    result = await star_service.remote.request_right_x_arm_last_collision_type()
    assert result is True


class TestPumpRPCs:
  @pytest.mark.asyncio
  async def test_request_pump_settings(self, star_service: StarServiceFixture):
    star_service.backend.request_pump_settings = unittest.mock.AsyncMock()
    await star_service.remote.request_pump_settings(pump_station=2)
    star_service.backend.request_pump_settings.assert_called_once_with(pump_station=2)

  @pytest.mark.asyncio
  async def test_initialize_dual_pump_station_valves(self, star_service: StarServiceFixture):
    star_service.backend.initialize_dual_pump_station_valves = unittest.mock.AsyncMock()
    await star_service.remote.initialize_dual_pump_station_valves(pump_station=1)
    star_service.backend.initialize_dual_pump_station_valves.assert_called_once_with(pump_station=1)

  @pytest.mark.asyncio
  async def test_drain_dual_chamber_system(self, star_service: StarServiceFixture):
    star_service.backend.drain_dual_chamber_system = unittest.mock.AsyncMock()
    await star_service.remote.drain_dual_chamber_system(pump_station=1)
    star_service.backend.drain_dual_chamber_system.assert_called_once_with(pump_station=1)


class TestSpecialRPCs:
  @pytest.mark.asyncio
  async def test_violently_shoot_down_tip(self, star_service: StarServiceFixture):
    star_service.backend.violently_shoot_down_tip = unittest.mock.AsyncMock()
    await star_service.remote.violently_shoot_down_tip(channel_idx=3)
    star_service.backend.violently_shoot_down_tip.assert_called_once_with(channel_idx=3)
