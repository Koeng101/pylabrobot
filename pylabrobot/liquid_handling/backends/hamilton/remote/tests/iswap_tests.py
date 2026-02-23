# mypy: disable-error-code="method-assign"
"""Tests for iSWAP RPCs."""

import unittest.mock

import pytest

from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend
from pylabrobot.resources import Coordinate

from .conftest import StarServiceFixture

RotationDriveOrientation = STARBackend.RotationDriveOrientation
WristDriveOrientation = STARBackend.WristDriveOrientation


class TestIswapRPCs:
  # -----------------------------------------------------------------------
  # Initialization / positioning
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_initialize_iswap(self, star_service: StarServiceFixture):
    star_service.backend.initialize_iswap = unittest.mock.AsyncMock()
    await star_service.remote.initialize_iswap()
    star_service.backend.initialize_iswap.assert_called_once()

  @pytest.mark.asyncio
  async def test_position_components_for_free_iswap_y_range(self, star_service: StarServiceFixture):
    star_service.backend.position_components_for_free_iswap_y_range = unittest.mock.AsyncMock()
    await star_service.remote.position_components_for_free_iswap_y_range()
    star_service.backend.position_components_for_free_iswap_y_range.assert_called_once()

  # -----------------------------------------------------------------------
  # Relative moves
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_move_iswap_x_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_x_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_x_relative(step_size=100)
    star_service.backend.move_iswap_x_relative.assert_called_once_with(
      step_size=100, allow_splitting=False
    )

  @pytest.mark.asyncio
  async def test_move_iswap_x_relative_with_splitting(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_x_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_x_relative(step_size=200, allow_splitting=True)
    star_service.backend.move_iswap_x_relative.assert_called_once_with(
      step_size=200, allow_splitting=True
    )

  @pytest.mark.asyncio
  async def test_move_iswap_y_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_y_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_y_relative(step_size=150)
    star_service.backend.move_iswap_y_relative.assert_called_once_with(
      step_size=150, allow_splitting=False
    )

  @pytest.mark.asyncio
  async def test_move_iswap_y_relative_with_splitting(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_y_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_y_relative(step_size=250, allow_splitting=True)
    star_service.backend.move_iswap_y_relative.assert_called_once_with(
      step_size=250, allow_splitting=True
    )

  @pytest.mark.asyncio
  async def test_move_iswap_z_relative(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_z_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_z_relative(step_size=50)
    star_service.backend.move_iswap_z_relative.assert_called_once_with(
      step_size=50, allow_splitting=False
    )

  @pytest.mark.asyncio
  async def test_move_iswap_z_relative_with_splitting(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_z_relative = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_z_relative(step_size=75, allow_splitting=True)
    star_service.backend.move_iswap_z_relative.assert_called_once_with(
      step_size=75, allow_splitting=True
    )

  # -----------------------------------------------------------------------
  # Absolute moves
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_move_iswap_x(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_x = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_x(x_position=5000)
    star_service.backend.move_iswap_x.assert_called_once_with(x_position=5000)

  @pytest.mark.asyncio
  async def test_move_iswap_y(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_y = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_y(y_position=3000)
    star_service.backend.move_iswap_y.assert_called_once_with(y_position=3000)

  @pytest.mark.asyncio
  async def test_move_iswap_z(self, star_service: StarServiceFixture):
    star_service.backend.move_iswap_z = unittest.mock.AsyncMock()
    await star_service.remote.move_iswap_z(z_position=1500)
    star_service.backend.move_iswap_z.assert_called_once_with(z_position=1500)

  # -----------------------------------------------------------------------
  # Gripper open / close
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_open_not_initialized_gripper(self, star_service: StarServiceFixture):
    star_service.backend.open_not_initialized_gripper = unittest.mock.AsyncMock()
    await star_service.remote.open_not_initialized_gripper()
    star_service.backend.open_not_initialized_gripper.assert_called_once()

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

  # -----------------------------------------------------------------------
  # Park
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_park_iswap(self, star_service: StarServiceFixture):
    star_service.backend.park_iswap = unittest.mock.AsyncMock()
    await star_service.remote.park_iswap()
    star_service.backend.park_iswap.assert_called_once()

  # -----------------------------------------------------------------------
  # Get / Put / Move plate (low-level int params)
  # -----------------------------------------------------------------------

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

  @pytest.mark.asyncio
  async def test_move_plate_to_position(self, star_service: StarServiceFixture):
    star_service.backend.move_plate_to_position = unittest.mock.AsyncMock()
    await star_service.remote.move_plate_to_position(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      y_direction=0,
      z_position=1500,
      z_direction=0,
      grip_direction=1,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      collision_control_level=1,
      acceleration_index_high_acc=4,
      acceleration_index_low_acc=1,
    )
    star_service.backend.move_plate_to_position.assert_called_once_with(
      x_position=1000,
      x_direction=0,
      y_position=2000,
      y_direction=0,
      z_position=1500,
      z_direction=0,
      grip_direction=1,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      collision_control_level=1,
      acceleration_index_high_acc=4,
      acceleration_index_low_acc=1,
    )

  # -----------------------------------------------------------------------
  # Collapse gripper arm
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_collapse_gripper_arm(self, star_service: StarServiceFixture):
    star_service.backend.collapse_gripper_arm = unittest.mock.AsyncMock()
    await star_service.remote.collapse_gripper_arm(
      minimum_traverse_height_at_beginning_of_a_command=3600,
      iswap_fold_up_sequence_at_the_end_of_process=True,
    )
    star_service.backend.collapse_gripper_arm.assert_called_once_with(
      minimum_traverse_height_at_beginning_of_a_command=3600,
      iswap_fold_up_sequence_at_the_end_of_process=True,
    )

  # -----------------------------------------------------------------------
  # Rotation / wrist
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_iswap_rotate(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_rotation_drive = unittest.mock.AsyncMock()
    await star_service.remote.iswap_rotate(
      orientation=RotationDriveOrientation.LEFT,
    )
    star_service.backend.rotate_iswap_rotation_drive.assert_called_once_with(
      orientation=RotationDriveOrientation.LEFT,
    )

  @pytest.mark.asyncio
  async def test_iswap_rotate_front(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_rotation_drive = unittest.mock.AsyncMock()
    await star_service.remote.iswap_rotate(
      orientation=RotationDriveOrientation.FRONT,
    )
    star_service.backend.rotate_iswap_rotation_drive.assert_called_once_with(
      orientation=RotationDriveOrientation.FRONT,
    )

  @pytest.mark.asyncio
  async def test_iswap_rotate_right(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_rotation_drive = unittest.mock.AsyncMock()
    await star_service.remote.iswap_rotate(
      orientation=RotationDriveOrientation.RIGHT,
    )
    star_service.backend.rotate_iswap_rotation_drive.assert_called_once_with(
      orientation=RotationDriveOrientation.RIGHT,
    )

  @pytest.mark.asyncio
  async def test_rotate_iswap_rotation_drive(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_rotation_drive = unittest.mock.AsyncMock()
    await star_service.remote.rotate_iswap_rotation_drive(
      orientation=RotationDriveOrientation.FRONT,
    )
    star_service.backend.rotate_iswap_rotation_drive.assert_called_once_with(
      orientation=RotationDriveOrientation.FRONT,
    )

  @pytest.mark.asyncio
  async def test_rotate_iswap_wrist(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_wrist = unittest.mock.AsyncMock()
    await star_service.remote.rotate_iswap_wrist(
      orientation=WristDriveOrientation.STRAIGHT,
    )
    star_service.backend.rotate_iswap_wrist.assert_called_once_with(
      orientation=WristDriveOrientation.STRAIGHT,
    )

  @pytest.mark.asyncio
  async def test_rotate_iswap_wrist_left(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_wrist = unittest.mock.AsyncMock()
    await star_service.remote.rotate_iswap_wrist(
      orientation=WristDriveOrientation.LEFT,
    )
    star_service.backend.rotate_iswap_wrist.assert_called_once_with(
      orientation=WristDriveOrientation.LEFT,
    )

  @pytest.mark.asyncio
  async def test_rotate_iswap_wrist_right(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_wrist = unittest.mock.AsyncMock()
    await star_service.remote.rotate_iswap_wrist(
      orientation=WristDriveOrientation.RIGHT,
    )
    star_service.backend.rotate_iswap_wrist.assert_called_once_with(
      orientation=WristDriveOrientation.RIGHT,
    )

  @pytest.mark.asyncio
  async def test_rotate_iswap_wrist_reverse(self, star_service: StarServiceFixture):
    star_service.backend.rotate_iswap_wrist = unittest.mock.AsyncMock()
    await star_service.remote.rotate_iswap_wrist(
      orientation=WristDriveOrientation.REVERSE,
    )
    star_service.backend.rotate_iswap_wrist.assert_called_once_with(
      orientation=WristDriveOrientation.REVERSE,
    )

  # -----------------------------------------------------------------------
  # Break / Z-axis
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_iswap_dangerous_release_break(self, star_service: StarServiceFixture):
    star_service.backend.iswap_dangerous_release_break = unittest.mock.AsyncMock()
    await star_service.remote.iswap_dangerous_release_break()
    star_service.backend.iswap_dangerous_release_break.assert_called_once()

  @pytest.mark.asyncio
  async def test_iswap_reengage_break(self, star_service: StarServiceFixture):
    star_service.backend.iswap_reengage_break = unittest.mock.AsyncMock()
    await star_service.remote.iswap_reengage_break()
    star_service.backend.iswap_reengage_break.assert_called_once()

  @pytest.mark.asyncio
  async def test_iswap_initialize_z_axis(self, star_service: StarServiceFixture):
    star_service.backend.iswap_initialize_z_axis = unittest.mock.AsyncMock()
    await star_service.remote.iswap_initialize_z_axis()
    star_service.backend.iswap_initialize_z_axis.assert_called_once()

  # -----------------------------------------------------------------------
  # Request / query RPCs
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_request_iswap_rotation_drive_position_increments(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_iswap_rotation_drive_position_increments = unittest.mock.AsyncMock(
      return_value=4200
    )
    result = await star_service.remote.request_iswap_rotation_drive_position_increments()
    assert result == 4200

  @pytest.mark.asyncio
  async def test_request_iswap_rotation_drive_orientation(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_rotation_drive_orientation = unittest.mock.AsyncMock(
      return_value=RotationDriveOrientation.FRONT
    )
    result = await star_service.remote.request_iswap_rotation_drive_orientation()
    assert result == RotationDriveOrientation.FRONT

  @pytest.mark.asyncio
  async def test_request_iswap_rotation_drive_orientation_left(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_iswap_rotation_drive_orientation = unittest.mock.AsyncMock(
      return_value=RotationDriveOrientation.LEFT
    )
    result = await star_service.remote.request_iswap_rotation_drive_orientation()
    assert result == RotationDriveOrientation.LEFT

  @pytest.mark.asyncio
  async def test_request_iswap_rotation_drive_orientation_right(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_iswap_rotation_drive_orientation = unittest.mock.AsyncMock(
      return_value=RotationDriveOrientation.RIGHT
    )
    result = await star_service.remote.request_iswap_rotation_drive_orientation()
    assert result == RotationDriveOrientation.RIGHT

  @pytest.mark.asyncio
  async def test_request_iswap_wrist_drive_position_increments(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_iswap_wrist_drive_position_increments = unittest.mock.AsyncMock(
      return_value=1234
    )
    result = await star_service.remote.request_iswap_wrist_drive_position_increments()
    assert result == 1234

  @pytest.mark.asyncio
  async def test_request_iswap_wrist_drive_orientation(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_wrist_drive_orientation = unittest.mock.AsyncMock(
      return_value=WristDriveOrientation.STRAIGHT
    )
    result = await star_service.remote.request_iswap_wrist_drive_orientation()
    assert result == WristDriveOrientation.STRAIGHT

  @pytest.mark.asyncio
  async def test_request_iswap_wrist_drive_orientation_left(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_wrist_drive_orientation = unittest.mock.AsyncMock(
      return_value=WristDriveOrientation.LEFT
    )
    result = await star_service.remote.request_iswap_wrist_drive_orientation()
    assert result == WristDriveOrientation.LEFT

  @pytest.mark.asyncio
  async def test_request_iswap_wrist_drive_orientation_reverse(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_iswap_wrist_drive_orientation = unittest.mock.AsyncMock(
      return_value=WristDriveOrientation.REVERSE
    )
    result = await star_service.remote.request_iswap_wrist_drive_orientation()
    assert result == WristDriveOrientation.REVERSE

  @pytest.mark.asyncio
  async def test_request_iswap_in_parking_position(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_in_parking_position = unittest.mock.AsyncMock()
    await star_service.remote.request_iswap_in_parking_position()
    star_service.backend.request_iswap_in_parking_position.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_plate_in_iswap_true(self, star_service: StarServiceFixture):
    star_service.backend.request_plate_in_iswap = unittest.mock.AsyncMock(return_value=True)
    result = await star_service.remote.request_plate_in_iswap()
    assert result is True

  @pytest.mark.asyncio
  async def test_request_plate_in_iswap_false(self, star_service: StarServiceFixture):
    star_service.backend.request_plate_in_iswap = unittest.mock.AsyncMock(return_value=False)
    result = await star_service.remote.request_plate_in_iswap()
    assert result is False

  @pytest.mark.asyncio
  async def test_request_iswap_position(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_position = unittest.mock.AsyncMock(
      return_value=Coordinate(x=100.0, y=200.0, z=300.0)
    )
    result = await star_service.remote.request_iswap_position()
    assert result == Coordinate(x=100.0, y=200.0, z=300.0)

  @pytest.mark.asyncio
  async def test_iswap_rotation_drive_request_y(self, star_service: StarServiceFixture):
    star_service.backend.iswap_rotation_drive_request_y = unittest.mock.AsyncMock(
      return_value=456.5
    )
    result = await star_service.remote.iswap_rotation_drive_request_y()
    assert result == 456.5

  @pytest.mark.asyncio
  async def test_request_iswap_initialization_status_true(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_initialization_status = unittest.mock.AsyncMock(
      return_value=True
    )
    result = await star_service.remote.request_iswap_initialization_status()
    assert result is True

  @pytest.mark.asyncio
  async def test_request_iswap_initialization_status_false(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_initialization_status = unittest.mock.AsyncMock(
      return_value=False
    )
    result = await star_service.remote.request_iswap_initialization_status()
    assert result is False

  @pytest.mark.asyncio
  async def test_request_iswap_version(self, star_service: StarServiceFixture):
    star_service.backend.request_iswap_version = unittest.mock.AsyncMock(return_value="2.1.0")
    result = await star_service.remote.request_iswap_version()
    assert result == "2.1.0"

  @pytest.mark.asyncio
  async def test_get_iswap_version(self, star_service: StarServiceFixture):
    star_service.backend.get_iswap_version = unittest.mock.AsyncMock(return_value="3.0.1")
    result = await star_service.remote.get_iswap_version()
    assert result == "3.0.1"

  # -----------------------------------------------------------------------
  # Slow iSWAP
  # -----------------------------------------------------------------------

  @pytest.mark.asyncio
  async def test_slow_iswap(self, star_service: StarServiceFixture):
    star_service.backend.slow_iswap = unittest.mock.AsyncMock()
    await star_service.remote.slow_iswap(
      wrist_velocity=15000,
      gripper_velocity=10000,
    )
    star_service.backend.slow_iswap.assert_called_once_with(
      wrist_velocity=15000,
      gripper_velocity=10000,
    )

  @pytest.mark.asyncio
  async def test_slow_iswap_defaults(self, star_service: StarServiceFixture):
    star_service.backend.slow_iswap = unittest.mock.AsyncMock()
    await star_service.remote.slow_iswap()
    star_service.backend.slow_iswap.assert_called_once_with(
      wrist_velocity=20000,
      gripper_velocity=20000,
    )
