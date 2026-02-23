# mypy: disable-error-code="method-assign"
"""Tests for channel movement and query RPCs."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestChannelMovementRPCs:
  @pytest.mark.asyncio
  async def test_move_channel_x(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_x = unittest.mock.AsyncMock()
    await star_service.remote.move_channel_x(channel=0, x=100.0)
    star_service.backend.move_channel_x.assert_called_once_with(0, 100.0)

  @pytest.mark.asyncio
  async def test_move_channel_y(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_y = unittest.mock.AsyncMock()
    await star_service.remote.move_channel_y(channel=0, y=200.0)
    star_service.backend.move_channel_y.assert_called_once_with(0, 200.0)

  @pytest.mark.asyncio
  async def test_move_channel_z(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_z = unittest.mock.AsyncMock()
    await star_service.remote.move_channel_z(channel=0, z=50.0)
    star_service.backend.move_channel_z.assert_called_once_with(0, 50.0)

  @pytest.mark.asyncio
  async def test_move_channel_x_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_x_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_channel_x_relative(channel=0, distance=10.0)
    star_service.backend.move_channel_x_relative.assert_called_once_with(0, 10.0)

  @pytest.mark.asyncio
  async def test_move_channel_y_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_y_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_channel_y_relative(channel=0, distance=10.0)
    star_service.backend.move_channel_y_relative.assert_called_once_with(0, 10.0)

  @pytest.mark.asyncio
  async def test_move_channel_z_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_channel_z_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_channel_z_relative(channel=0, distance=5.0)
    star_service.backend.move_channel_z_relative.assert_called_once_with(0, 5.0)

  @pytest.mark.asyncio
  async def test_move_all_channels_in_z_safety(self, star_service: StarServiceFixture):
    star_service.backend.move_all_channels_in_z_safety = unittest.mock.AsyncMock()
    await star_service.remote.move_all_channels_in_z_safety()
    star_service.backend.move_all_channels_in_z_safety.assert_called_once()

  @pytest.mark.asyncio
  async def test_prepare_for_manual_channel_operation(self, star_service: StarServiceFixture):
    star_service.backend.prepare_for_manual_channel_operation = unittest.mock.AsyncMock()
    await star_service.remote.prepare_for_manual_channel_operation(channel=2)
    star_service.backend.prepare_for_manual_channel_operation.assert_called_once_with(2)

  @pytest.mark.asyncio
  async def test_position_single_pipetting_channel_in_z_direction(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.position_single_pipetting_channel_in_z_direction = (
      unittest.mock.AsyncMock()
    )
    await star_service.remote.position_single_pipetting_channel_in_z_direction(
      pipetting_channel_index=3, z_position=1500
    )
    star_service.backend.position_single_pipetting_channel_in_z_direction.assert_called_once_with(
      pipetting_channel_index=3, z_position=1500
    )

  @pytest.mark.asyncio
  async def test_position_max_free_y_for_n(self, star_service: StarServiceFixture):
    star_service.backend.position_max_free_y_for_n = unittest.mock.AsyncMock()
    await star_service.remote.position_max_free_y_for_n(pipetting_channel_index=4)
    star_service.backend.position_max_free_y_for_n.assert_called_once_with(
      pipetting_channel_index=4
    )

  @pytest.mark.asyncio
  async def test_position_channels_in_y_direction(self, star_service: StarServiceFixture):
    star_service.backend.position_channels_in_y_direction = unittest.mock.AsyncMock()
    await star_service.remote.position_channels_in_y_direction(
      ys={0: 100.0, 1: 200.0}, make_space=True
    )
    star_service.backend.position_channels_in_y_direction.assert_called_once_with(
      ys={0: 100.0, 1: 200.0}, make_space=True
    )

  @pytest.mark.asyncio
  async def test_position_channels_in_z_direction(self, star_service: StarServiceFixture):
    star_service.backend.position_channels_in_z_direction = unittest.mock.AsyncMock()
    await star_service.remote.position_channels_in_z_direction(zs={0: 50.0, 2: 75.0})
    star_service.backend.position_channels_in_z_direction.assert_called_once_with(
      zs={0: 50.0, 2: 75.0}
    )


class TestChannelQueryRPCs:
  @pytest.mark.asyncio
  async def test_request_x_pos_channel_n(self, star_service: StarServiceFixture):
    star_service.backend.request_x_pos_channel_n = unittest.mock.AsyncMock(return_value=123.5)
    result = await star_service.remote.request_x_pos_channel_n(pipetting_channel_index=0)
    assert result == 123.5
    star_service.backend.request_x_pos_channel_n.assert_called_once_with(pipetting_channel_index=0)

  @pytest.mark.asyncio
  async def test_request_y_pos_channel_n(self, star_service: StarServiceFixture):
    star_service.backend.request_y_pos_channel_n = unittest.mock.AsyncMock(return_value=456.0)
    result = await star_service.remote.request_y_pos_channel_n(pipetting_channel_index=1)
    assert result == 456.0

  @pytest.mark.asyncio
  async def test_request_z_pos_channel_n(self, star_service: StarServiceFixture):
    star_service.backend.request_z_pos_channel_n = unittest.mock.AsyncMock(return_value=78.9)
    result = await star_service.remote.request_z_pos_channel_n(pipetting_channel_index=2)
    assert result == 78.9

  @pytest.mark.asyncio
  async def test_request_tip_bottom_z_position(self, star_service: StarServiceFixture):
    star_service.backend.request_tip_bottom_z_position = unittest.mock.AsyncMock(
      return_value=12.3
    )
    result = await star_service.remote.request_tip_bottom_z_position(channel_idx=5)
    assert result == 12.3
    star_service.backend.request_tip_bottom_z_position.assert_called_once_with(channel_idx=5)

  @pytest.mark.asyncio
  async def test_position_single_pipetting_channel_in_y_direction(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.position_single_pipetting_channel_in_y_direction = (
      unittest.mock.AsyncMock()
    )
    await star_service.remote.position_single_pipetting_channel_in_y_direction(
      pipetting_channel_index=1, y_position=2000
    )
    star_service.backend.position_single_pipetting_channel_in_y_direction.assert_called_once_with(
      pipetting_channel_index=1, y_position=2000
    )

  @pytest.mark.asyncio
  async def test_get_channels_y_positions(self, star_service: StarServiceFixture):
    star_service.backend.get_channels_y_positions = unittest.mock.AsyncMock(
      return_value={0: 100.0, 1: 200.0}
    )
    result = await star_service.remote.get_channels_y_positions()
    assert result == {0: 100.0, 1: 200.0}

  @pytest.mark.asyncio
  async def test_get_channels_z_positions(self, star_service: StarServiceFixture):
    star_service.backend.get_channels_z_positions = unittest.mock.AsyncMock(
      return_value={0: 50.0, 3: 80.5}
    )
    result = await star_service.remote.get_channels_z_positions()
    assert result == {0: 50.0, 3: 80.5}

  @pytest.mark.asyncio
  async def test_request_pip_channel_version(self, star_service: StarServiceFixture):
    star_service.backend.request_pip_channel_version = unittest.mock.AsyncMock(
      return_value="A1.02"
    )
    result = await star_service.remote.request_pip_channel_version(channel=0)
    assert result == "A1.02"
