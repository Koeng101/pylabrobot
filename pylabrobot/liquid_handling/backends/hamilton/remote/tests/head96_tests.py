# mypy: disable-error-code="method-assign"
"""Tests for 96-head movement and query RPCs."""

import unittest.mock

import pytest

from pylabrobot.resources import Coordinate

from .conftest import StarServiceFixture


class TestHead96MovementRPCs:
  @pytest.mark.asyncio
  async def test_initialize_core_96_head(self, star_service: StarServiceFixture):
    star_service.backend.initialize_core_96_head = unittest.mock.AsyncMock()
    await star_service.remote.initialize_core_96_head(trash96_name="tip_rack_01")
    star_service.backend.initialize_core_96_head.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_core_96_head_initialization_status(self, star_service: StarServiceFixture):
    star_service.backend.request_core_96_head_initialization_status = unittest.mock.AsyncMock(
      return_value=True
    )
    result = await star_service.remote.request_core_96_head_initialization_status()
    assert result is True
    star_service.backend.request_core_96_head_initialization_status.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_request_firmware_version(self, star_service: StarServiceFixture):
    star_service.backend.head96_request_firmware_version = unittest.mock.AsyncMock(
      return_value="2024-01-15"
    )
    result = await star_service.remote.head96_request_firmware_version()
    assert result == "2024-01-15"
    star_service.backend.head96_request_firmware_version.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_request_type(self, star_service: StarServiceFixture):
    mock_type = unittest.mock.MagicMock()
    mock_type.value = 3
    star_service.backend.head96_request_type = unittest.mock.AsyncMock(return_value=mock_type)
    result = await star_service.remote.head96_request_type()
    assert result == 3
    star_service.backend.head96_request_type.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_dispensing_drive_and_squeezer_driver_initialize(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.head96_dispensing_drive_and_squeezer_driver_initialize = (
      unittest.mock.AsyncMock()
    )
    await star_service.remote.head96_dispensing_drive_and_squeezer_driver_initialize(
      squeezer_speed=20.0,
      squeezer_acceleration=70.0,
      squeezer_current_limit=10,
      dispensing_drive_current_limit=5,
    )
    star_service.backend.head96_dispensing_drive_and_squeezer_driver_initialize.assert_called_once_with(
      squeezer_speed=20.0,
      squeezer_acceleration=70.0,
      squeezer_current_limit=10,
      dispensing_drive_current_limit=5,
    )

  @pytest.mark.asyncio
  async def test_move_core_96_to_safe_position(self, star_service: StarServiceFixture):
    star_service.backend.move_core_96_to_safe_position = unittest.mock.AsyncMock()
    await star_service.remote.move_core_96_to_safe_position()
    star_service.backend.move_core_96_to_safe_position.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_move_to_z_safety(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_to_z_safety = unittest.mock.AsyncMock()
    await star_service.remote.head96_move_to_z_safety()
    star_service.backend.head96_move_to_z_safety.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_park(self, star_service: StarServiceFixture):
    star_service.backend.head96_park = unittest.mock.AsyncMock()
    await star_service.remote.head96_park()
    star_service.backend.head96_park.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_move_x(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_x = unittest.mock.AsyncMock()
    await star_service.remote.head96_move_x(x=1000)
    star_service.backend.head96_move_x.assert_called_once_with(x=1000)

  @pytest.mark.asyncio
  async def test_head96_move_y(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_y = unittest.mock.AsyncMock()
    await star_service.remote.head96_move_y(y=2000)
    star_service.backend.head96_move_y.assert_called_once_with(
      y=2000, move_up_before=False, move_down_after=False
    )

  @pytest.mark.asyncio
  async def test_head96_move_z(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_z = unittest.mock.AsyncMock()
    await star_service.remote.head96_move_z(z=1500)
    star_service.backend.head96_move_z.assert_called_once_with(z=1500)

  @pytest.mark.asyncio
  async def test_move_core_96_head_to_defined_position(self, star_service: StarServiceFixture):
    star_service.backend.move_core_96_head_to_defined_position = unittest.mock.AsyncMock()
    await star_service.remote.move_core_96_head_to_defined_position(x=100.0, y=200.0, z=300.0)
    star_service.backend.move_core_96_head_to_defined_position.assert_called_once_with(
      x=100.0, y=200.0, z=300.0
    )

  @pytest.mark.asyncio
  async def test_head96_move_to_coordinate(self, star_service: StarServiceFixture):
    star_service.backend.head96_move_to_coordinate = unittest.mock.AsyncMock()
    coord = Coordinate(x=10.0, y=20.0, z=30.0)
    await star_service.remote.head96_move_to_coordinate(coordinate=coord)
    star_service.backend.head96_move_to_coordinate.assert_called_once()
    call_args = star_service.backend.head96_move_to_coordinate.call_args
    assert call_args.kwargs["coordinate"] == Coordinate(x=10.0, y=20.0, z=30.0)

  @pytest.mark.asyncio
  async def test_head96_dispensing_drive_move_to_home_volume(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.head96_dispensing_drive_move_to_home_volume = unittest.mock.AsyncMock()
    await star_service.remote.head96_dispensing_drive_move_to_home_volume()
    star_service.backend.head96_dispensing_drive_move_to_home_volume.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_dispensing_drive_move_to_position(self, star_service: StarServiceFixture):
    star_service.backend.head96_dispensing_drive_move_to_position = unittest.mock.AsyncMock()
    await star_service.remote.head96_dispensing_drive_move_to_position(
      position=50.0, speed=300.0, current_protection_limiter=10
    )
    star_service.backend.head96_dispensing_drive_move_to_position.assert_called_once_with(
      position=50.0, speed=300.0, current_protection_limiter=10
    )

  @pytest.mark.asyncio
  async def test_head96_dispensing_drive_request_position_mm(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.head96_dispensing_drive_request_position_mm = unittest.mock.AsyncMock(
      return_value=12.5
    )
    result = await star_service.remote.head96_dispensing_drive_request_position_mm()
    assert result == 12.5
    star_service.backend.head96_dispensing_drive_request_position_mm.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_dispensing_drive_request_position_uL(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.head96_dispensing_drive_request_position_uL = unittest.mock.AsyncMock(
      return_value=150.0
    )
    result = await star_service.remote.head96_dispensing_drive_request_position_uL()
    assert result == 150.0
    star_service.backend.head96_dispensing_drive_request_position_uL.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_request_tip_presence(self, star_service: StarServiceFixture):
    star_service.backend.head96_request_tip_presence = unittest.mock.AsyncMock(return_value=1)
    result = await star_service.remote.head96_request_tip_presence()
    assert result == 1
    star_service.backend.head96_request_tip_presence.assert_called_once()

  @pytest.mark.asyncio
  async def test_head96_request_position(self, star_service: StarServiceFixture):
    star_service.backend.head96_request_position = unittest.mock.AsyncMock(
      return_value=Coordinate(x=100.0, y=200.0, z=300.0)
    )
    result = await star_service.remote.head96_request_position()
    assert result == Coordinate(x=100.0, y=200.0, z=300.0)
    star_service.backend.head96_request_position.assert_called_once()
