"""Tests for autoload RPCs."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestAutoloadRPCs:
  @pytest.mark.asyncio
  async def test_initialize_autoload(self, star_service: StarServiceFixture):
    star_service.backend.initialize_autoload = unittest.mock.AsyncMock()
    await star_service.remote.initialize_autoload()
    star_service.backend.initialize_autoload.assert_called_once()

  @pytest.mark.asyncio
  async def test_load_carrier(self, star_service: StarServiceFixture):
    star_service.backend.load_carrier = unittest.mock.AsyncMock()
    carrier = star_service.deck.get_resource("tip carrier")
    await star_service.remote.load_carrier(carrier=carrier)
    star_service.backend.load_carrier.assert_called_once_with(carrier=carrier)

  @pytest.mark.asyncio
  async def test_unload_carrier(self, star_service: StarServiceFixture):
    star_service.backend.unload_carrier = unittest.mock.AsyncMock()
    carrier = star_service.deck.get_resource("tip carrier")
    await star_service.remote.unload_carrier(carrier=carrier)
    star_service.backend.unload_carrier.assert_called_once_with(carrier=carrier)

  @pytest.mark.asyncio
  async def test_park_autoload(self, star_service: StarServiceFixture):
    star_service.backend.park_autoload = unittest.mock.AsyncMock()
    await star_service.remote.park_autoload()
    star_service.backend.park_autoload.assert_called_once()

  @pytest.mark.asyncio
  async def test_move_autoload_to_slot(self, star_service: StarServiceFixture):
    star_service.backend.move_autoload_to_slot = unittest.mock.AsyncMock()
    await star_service.remote.move_autoload_to_slot(slot_number=3)
    star_service.backend.move_autoload_to_slot.assert_called_once_with(slot_number=3)
