"""Tests for iSWAP RPCs."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestIswapRPCs:
  @pytest.mark.asyncio
  async def test_initialize_iswap(self, star_service: StarServiceFixture):
    star_service.backend.initialize_iswap = unittest.mock.AsyncMock()
    await star_service.remote.initialize_iswap()
    star_service.backend.initialize_iswap.assert_called_once()

  @pytest.mark.asyncio
  async def test_park_iswap(self, star_service: StarServiceFixture):
    star_service.backend.park_iswap = unittest.mock.AsyncMock()
    await star_service.remote.park_iswap()
    star_service.backend.park_iswap.assert_called_once()

  @pytest.mark.asyncio
  async def test_iswap_open_gripper(self, star_service: StarServiceFixture):
    star_service.backend.iswap_open_gripper = unittest.mock.AsyncMock()
    await star_service.remote.iswap_open_gripper(open_position=860)
    star_service.backend.iswap_open_gripper.assert_called_once_with(open_position=860)

  @pytest.mark.asyncio
  async def test_iswap_close_gripper(self, star_service: StarServiceFixture):
    star_service.backend.iswap_close_gripper = unittest.mock.AsyncMock()
    await star_service.remote.iswap_close_gripper(grip_strength=5)
    star_service.backend.iswap_close_gripper.assert_called_once_with(
      grip_strength=5, plate_width=0, plate_width_tolerance=0
    )

  @pytest.mark.asyncio
  async def test_move_iswap_x_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_x_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_x_relative(step_size=100)
    star_service.backend.move_iswap_x_relative.assert_called_once_with(
      step_size=100, allow_splitting=False
    )

  @pytest.mark.asyncio
  async def test_iswap_get_plate(self, star_service: StarServiceFixture):
    star_service.backend.iswap_get_plate = unittest.mock.AsyncMock()
    await star_service.remote.iswap_get_plate(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      y_direction=0,
      z_position=1500,
      z_direction=0,
      grip_direction=1,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      z_position_at_the_command_end=3600,
      grip_strength=5,
      open_gripper_position=860,
      plate_width=800,
      plate_width_tolerance=20,
    )
    star_service.backend.iswap_get_plate.assert_called_once()

  @pytest.mark.asyncio
  async def test_iswap_put_plate(self, star_service: StarServiceFixture):
    star_service.backend.iswap_put_plate = unittest.mock.AsyncMock()
    await star_service.remote.iswap_put_plate(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      y_direction=0,
      z_position=1500,
      z_direction=0,
      grip_direction=1,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      z_position_at_the_command_end=3600,
      open_gripper_position=860,
    )
    star_service.backend.iswap_put_plate.assert_called_once()
