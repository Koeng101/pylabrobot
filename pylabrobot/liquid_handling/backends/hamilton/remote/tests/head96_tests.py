"""Tests for 96-head movement and query RPCs."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestHead96MovementRPCs:
  @pytest.mark.asyncio
  async def test_initialize_core_96_head(self, star_service: StarServiceFixture):
    star_service.backend.initialize_core_96_head = unittest.mock.AsyncMock()
    await star_service.remote.initialize_core_96_head(trash96_name="tip_rack_01")
    star_service.backend.initialize_core_96_head.assert_called_once()

  @pytest.mark.asyncio
  async def test_move_core_96_to_safe_position(self, star_service: StarServiceFixture):
    star_service.backend.move_core_96_to_safe_position = unittest.mock.AsyncMock()
    await star_service.remote.move_core_96_to_safe_position()
    star_service.backend.move_core_96_to_safe_position.assert_called_once()

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
