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

  @pytest.mark.asyncio
  async def test_core_move_plate_to_position(self, star_service: StarServiceFixture):
    star_service.backend.core_move_plate_to_position = unittest.mock.AsyncMock()
    await star_service.remote.core_move_plate_to_position(
      x_position=1200,
      x_direction=0,
      x_acceleration_index=4,
      y_position=2500,
      z_position=1800,
      z_speed=500,
      minimum_traverse_height_at_beginning_of_a_command=3600,
    )
    star_service.backend.core_move_plate_to_position.assert_called_once_with(
      x_position=1200,
      x_direction=0,
      x_acceleration_index=4,
      y_position=2500,
      z_position=1800,
      z_speed=500,
      minimum_traverse_height_at_beginning_of_a_command=3600,
    )

  @pytest.mark.asyncio
  async def test_get_core(self, star_service: StarServiceFixture):
    star_service.backend.get_core = unittest.mock.AsyncMock()
    await star_service.remote.get_core(p1=1, p2=2)
    star_service.backend.get_core.assert_called_once_with(p1=1, p2=2)

  @pytest.mark.asyncio
  async def test_put_core(self, star_service: StarServiceFixture):
    star_service.backend.put_core = unittest.mock.AsyncMock()
    await star_service.remote.put_core()
    star_service.backend.put_core.assert_called_once()

  @pytest.mark.asyncio
  async def test_core_read_barcode_of_picked_up_resource(self, star_service: StarServiceFixture):
    star_service.backend.core_read_barcode_of_picked_up_resource = unittest.mock.AsyncMock()
    await star_service.remote.core_read_barcode_of_picked_up_resource(
      rails=5,
      reading_direction="horizontal",
      minimal_z_position=220.0,
      traverse_height_at_beginning_of_a_command=275.0,
      z_speed=128.7,
      allow_manual_input=False,
    )
    star_service.backend.core_read_barcode_of_picked_up_resource.assert_called_once_with(
      rails=5,
      reading_direction="horizontal",
      minimal_z_position=220.0,
      traverse_height_at_beginning_of_a_command=275.0,
      z_speed=128.7,
      allow_manual_input=False,
    )
