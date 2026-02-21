"""Tests for core gripper RPCs."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestCoreGripperRPCs:
  @pytest.mark.asyncio
  async def test_pick_up_core_gripper_tools(self, star_service: StarServiceFixture):
    star_service.backend.pick_up_core_gripper_tools = unittest.mock.AsyncMock()
    await star_service.remote.pick_up_core_gripper_tools(front_channel=7)
    star_service.backend.pick_up_core_gripper_tools.assert_called_once()

  @pytest.mark.asyncio
  async def test_return_core_gripper_tools(self, star_service: StarServiceFixture):
    star_service.backend.return_core_gripper_tools = unittest.mock.AsyncMock()
    await star_service.remote.return_core_gripper_tools()
    star_service.backend.return_core_gripper_tools.assert_called_once()

  @pytest.mark.asyncio
  async def test_core_open_gripper(self, star_service: StarServiceFixture):
    star_service.backend.core_open_gripper = unittest.mock.AsyncMock()
    await star_service.remote.core_open_gripper()
    star_service.backend.core_open_gripper.assert_called_once()

  @pytest.mark.asyncio
  async def test_core_get_plate(self, star_service: StarServiceFixture):
    star_service.backend.core_get_plate = unittest.mock.AsyncMock()
    await star_service.remote.core_get_plate(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      y_gripping_speed=50,
      z_position=1500,
      z_speed=500,
      open_gripper_position=860,
      plate_width=800,
      grip_strength=5,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      minimum_z_position_at_the_command_end=3600,
    )
    star_service.backend.core_get_plate.assert_called_once_with(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      y_gripping_speed=50,
      z_position=1500,
      z_speed=500,
      open_gripper_position=860,
      plate_width=800,
      grip_strength=5,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      minimum_z_position_at_the_command_end=3600,
    )

  @pytest.mark.asyncio
  async def test_core_put_plate(self, star_service: StarServiceFixture):
    star_service.backend.core_put_plate = unittest.mock.AsyncMock()
    await star_service.remote.core_put_plate(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      z_position=1500,
      z_press_on_distance=0,
      z_speed=500,
      open_gripper_position=860,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      z_position_at_the_command_end=3600,
      return_tool=True,
    )
    star_service.backend.core_put_plate.assert_called_once_with(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      z_position=1500,
      z_press_on_distance=0,
      z_speed=500,
      open_gripper_position=860,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      z_position_at_the_command_end=3600,
      return_tool=True,
    )
