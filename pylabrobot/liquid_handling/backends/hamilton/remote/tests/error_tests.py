"""Tests that errors raised in the server-side backend propagate to the client.

When the real STARBackend raises an exception inside a server RPC handler,
the ConnectRPC framework translates it into a ``ConnectError`` that the
synchronous client raises.  These tests verify that the client does indeed
raise when the backend blows up, across all RPC categories (misc, channel,
head96, iswap).
"""

import unittest.mock

import pytest
from connectrpc.errors import ConnectError

from .conftest import StarServiceFixture


# ============================================================================
# Misc RPCs
# ============================================================================


class TestMiscErrorPropagation:
  """Errors from misc RPCs (cover, firmware, config, x-arm) propagate."""

  # -- RuntimeError --

  @pytest.mark.asyncio
  async def test_lock_cover_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.lock_cover = unittest.mock.AsyncMock(
      side_effect=RuntimeError("cover jam")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.lock_cover()

  @pytest.mark.asyncio
  async def test_unlock_cover_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.unlock_cover = unittest.mock.AsyncMock(
      side_effect=RuntimeError("cover stuck")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.unlock_cover()

  @pytest.mark.asyncio
  async def test_request_firmware_version_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.request_firmware_version = unittest.mock.AsyncMock(
      side_effect=RuntimeError("firmware communication failure")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.request_firmware_version()

  @pytest.mark.asyncio
  async def test_halt_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.halt = unittest.mock.AsyncMock(
      side_effect=RuntimeError("halt failed")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.halt()

  @pytest.mark.asyncio
  async def test_position_left_x_arm_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.position_left_x_arm = unittest.mock.AsyncMock(
      side_effect=RuntimeError("x-arm collision")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.position_left_x_arm(x_position=100)

  # -- ValueError --

  @pytest.mark.asyncio
  async def test_lock_cover_value_error(self, star_service: StarServiceFixture):
    star_service.backend.lock_cover = unittest.mock.AsyncMock(
      side_effect=ValueError("invalid cover state")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.lock_cover()

  @pytest.mark.asyncio
  async def test_set_single_step_mode_value_error(self, star_service: StarServiceFixture):
    star_service.backend.set_single_step_mode = unittest.mock.AsyncMock(
      side_effect=ValueError("bad mode value")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.set_single_step_mode(single_step_mode=True)

  @pytest.mark.asyncio
  async def test_send_hhs_command_value_error(self, star_service: StarServiceFixture):
    star_service.backend.send_hhs_command = unittest.mock.AsyncMock(
      side_effect=ValueError("invalid HHS index")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.send_hhs_command(index=99, command="bad")

  # -- error message preserved --

  @pytest.mark.asyncio
  async def test_error_message_preserved(self, star_service: StarServiceFixture):
    star_service.backend.lock_cover = unittest.mock.AsyncMock(
      side_effect=RuntimeError("cover jam: sensor 3 blocked")
    )
    with pytest.raises(ConnectError, match="cover jam: sensor 3 blocked"):
      await star_service.remote.lock_cover()


# ============================================================================
# Channel RPCs
# ============================================================================


class TestChannelErrorPropagation:
  """Errors from channel RPCs propagate."""

  @pytest.mark.asyncio
  async def test_move_channel_x_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_x = unittest.mock.AsyncMock(
      side_effect=RuntimeError("channel 1 x-axis stuck")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_channel_x(channel=1, x=100.0)

  @pytest.mark.asyncio
  async def test_move_channel_z_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_z = unittest.mock.AsyncMock(
      side_effect=RuntimeError("z-drive timeout")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_channel_z(channel=0, z=50.0)

  @pytest.mark.asyncio
  async def test_move_all_channels_in_z_safety_runtime_error(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.move_all_channels_in_z_safety = unittest.mock.AsyncMock(
      side_effect=RuntimeError("z safety move failed")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_all_channels_in_z_safety()

  @pytest.mark.asyncio
  async def test_move_channel_y_relative_value_error(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_y_relative = unittest.mock.AsyncMock(
      side_effect=ValueError("distance out of range")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_channel_y_relative(channel=0, distance=9999.0)

  @pytest.mark.asyncio
  async def test_position_single_pipetting_channel_in_y_direction_runtime_error(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.position_single_pipetting_channel_in_y_direction = (
      unittest.mock.AsyncMock(side_effect=RuntimeError("y-drive failure"))
    )
    with pytest.raises(ConnectError):
      await star_service.remote.position_single_pipetting_channel_in_y_direction(
        pipetting_channel_index=0, y_position=1000,
      )


# ============================================================================
# Head96 RPCs
# ============================================================================


class TestHead96ErrorPropagation:
  """Errors from 96-head RPCs propagate."""

  @pytest.mark.asyncio
  async def test_move_core_96_to_safe_position_runtime_error(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.move_core_96_to_safe_position = unittest.mock.AsyncMock(
      side_effect=RuntimeError("96-head safe position blocked")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_core_96_to_safe_position()

  @pytest.mark.asyncio
  async def test_head96_park_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.head96_park = unittest.mock.AsyncMock(
      side_effect=RuntimeError("park failed: obstruction detected")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.head96_park()

  @pytest.mark.asyncio
  async def test_head96_move_x_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_x = unittest.mock.AsyncMock(
      side_effect=RuntimeError("96-head x collision")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.head96_move_x(x=500.0)

  @pytest.mark.asyncio
  async def test_head96_move_z_value_error(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_z = unittest.mock.AsyncMock(
      side_effect=ValueError("z position below minimum")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.head96_move_z(z=-10.0)

  @pytest.mark.asyncio
  async def test_head96_dispensing_drive_move_to_position_runtime_error(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.head96_dispensing_drive_move_to_position = (
      unittest.mock.AsyncMock(side_effect=RuntimeError("dispensing drive stall"))
    )
    with pytest.raises(ConnectError):
      await star_service.remote.head96_dispensing_drive_move_to_position(position=100.0)


# ============================================================================
# iSWAP RPCs
# ============================================================================


class TestIswapErrorPropagation:
  """Errors from iSWAP RPCs propagate."""

  @pytest.mark.asyncio
  async def test_initialize_iswap_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.initialize_iswap = unittest.mock.AsyncMock(
      side_effect=RuntimeError("iSWAP initialization timeout")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.initialize_iswap()

  @pytest.mark.asyncio
  async def test_park_iswap_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.park_iswap = unittest.mock.AsyncMock(
      side_effect=RuntimeError("iSWAP park collision")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.park_iswap()

  @pytest.mark.asyncio
  async def test_move_iswap_x_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_x = unittest.mock.AsyncMock(
      side_effect=RuntimeError("iSWAP x out of range")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_iswap_x(x_position=9999.0)

  @pytest.mark.asyncio
  async def test_iswap_open_gripper_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.iswap_open_gripper = unittest.mock.AsyncMock(
      side_effect=RuntimeError("gripper mechanism jammed")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.iswap_open_gripper()

  @pytest.mark.asyncio
  async def test_iswap_close_gripper_value_error(self, star_service: StarServiceFixture):
    star_service.backend.iswap_close_gripper = unittest.mock.AsyncMock(
      side_effect=ValueError("invalid grip strength")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.iswap_close_gripper(grip_strength=-1)

  @pytest.mark.asyncio
  async def test_move_iswap_z_relative_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_z_relative = unittest.mock.AsyncMock(
      side_effect=RuntimeError("z relative move limit exceeded")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.move_iswap_z_relative(step_size=500.0)

  @pytest.mark.asyncio
  async def test_iswap_get_plate_runtime_error(self, star_service: StarServiceFixture):
    star_service.backend.iswap_get_plate = unittest.mock.AsyncMock(
      side_effect=RuntimeError("plate not detected")
    )
    with pytest.raises(ConnectError):
      await star_service.remote.iswap_get_plate()

  @pytest.mark.asyncio
  async def test_iswap_error_message_preserved(self, star_service: StarServiceFixture):
    star_service.backend.initialize_iswap = unittest.mock.AsyncMock(
      side_effect=RuntimeError("encoder fault on axis 2")
    )
    with pytest.raises(ConnectError, match="encoder fault on axis 2"):
      await star_service.remote.initialize_iswap()
