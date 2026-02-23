# mypy: disable-error-code="method-assign,attr-defined"
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

  @pytest.mark.asyncio
  async def test_move_autoload_to_safe_z_position(self, star_service: StarServiceFixture):
    star_service.backend.move_autoload_to_safe_z_position = unittest.mock.AsyncMock()
    await star_service.remote.move_autoload_to_safe_z_position()
    star_service.backend.move_autoload_to_safe_z_position.assert_called_once()

  @pytest.mark.asyncio
  async def test_move_autoload_to_track(self, star_service: StarServiceFixture):
    star_service.backend.move_autoload_to_track = unittest.mock.AsyncMock()
    await star_service.remote.move_autoload_to_track(track=5)
    star_service.backend.move_autoload_to_track.assert_called_once_with(track=5)

  @pytest.mark.asyncio
  async def test_request_autoload_track(self, star_service: StarServiceFixture):
    star_service.backend.request_autoload_track = unittest.mock.AsyncMock(return_value=7)
    result = await star_service.remote.request_autoload_track()
    star_service.backend.request_autoload_track.assert_called_once()
    assert result == 7

  @pytest.mark.asyncio
  async def test_request_autoload_type(self, star_service: StarServiceFixture):
    star_service.backend.request_autoload_type = unittest.mock.AsyncMock(
      return_value="iSWAP"
    )
    result = await star_service.remote.request_autoload_type()
    star_service.backend.request_autoload_type.assert_called_once()
    assert result == "iSWAP"

  @pytest.mark.asyncio
  async def test_request_presence_of_carriers_on_deck(self, star_service: StarServiceFixture):
    star_service.backend.request_presence_of_carriers_on_deck = unittest.mock.AsyncMock(
      return_value=[1, 3, 5]
    )
    result = await star_service.remote.request_presence_of_carriers_on_deck()
    star_service.backend.request_presence_of_carriers_on_deck.assert_called_once()
    assert result == [1, 3, 5]

  @pytest.mark.asyncio
  async def test_request_presence_of_carriers_on_loading_tray(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_presence_of_carriers_on_loading_tray = (
      unittest.mock.AsyncMock(return_value=[2, 4])
    )
    result = await star_service.remote.request_presence_of_carriers_on_loading_tray()
    star_service.backend.request_presence_of_carriers_on_loading_tray.assert_called_once()
    assert result == [2, 4]

  @pytest.mark.asyncio
  async def test_request_presence_of_single_carrier_on_loading_tray(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_presence_of_single_carrier_on_loading_tray = (
      unittest.mock.AsyncMock(return_value=True)
    )
    result = await star_service.remote.request_presence_of_single_carrier_on_loading_tray(
      track=10
    )
    star_service.backend.request_presence_of_single_carrier_on_loading_tray.assert_called_once_with(
      track=10
    )
    assert result is True

  @pytest.mark.asyncio
  async def test_set_carrier_monitoring(self, star_service: StarServiceFixture):
    star_service.backend.set_carrier_monitoring = unittest.mock.AsyncMock()
    await star_service.remote.set_carrier_monitoring(should_monitor=True)
    star_service.backend.set_carrier_monitoring.assert_called_once_with(should_monitor=True)

  @pytest.mark.asyncio
  async def test_set_loading_indicators(self, star_service: StarServiceFixture):
    star_service.backend.set_loading_indicators = unittest.mock.AsyncMock()
    bit_pattern = [True, False, True, False]
    blink_pattern = [False, True, False, True]
    await star_service.remote.set_loading_indicators(
      bit_pattern=bit_pattern, blink_pattern=blink_pattern
    )
    star_service.backend.set_loading_indicators.assert_called_once_with(
      bit_pattern=bit_pattern, blink_pattern=blink_pattern
    )

  @pytest.mark.asyncio
  async def test_request_instrument_initialization_status(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_instrument_initialization_status = (
      unittest.mock.AsyncMock(return_value=True)
    )
    result = await star_service.remote.request_instrument_initialization_status()
    star_service.backend.request_instrument_initialization_status.assert_called_once()
    assert result is True

  @pytest.mark.asyncio
  async def test_request_autoload_initialization_status(
    self, star_service: StarServiceFixture
  ):
    star_service.backend.request_autoload_initialization_status = (
      unittest.mock.AsyncMock(return_value=False)
    )
    result = await star_service.remote.request_autoload_initialization_status()
    star_service.backend.request_autoload_initialization_status.assert_called_once()
    assert result is False
