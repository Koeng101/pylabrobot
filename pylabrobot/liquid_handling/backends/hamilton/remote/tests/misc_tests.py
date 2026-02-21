"""Tests for misc RPCs: firmware queries, cover, config."""

import unittest.mock

import pytest

from .conftest import StarServiceFixture


class TestFirmwareQueryRPCs:
  @pytest.mark.asyncio
  async def test_request_firmware_version(self, star_service: StarServiceFixture):
    star_service.backend.request_firmware_version = unittest.mock.AsyncMock()
    await star_service.remote.request_firmware_version()
    star_service.backend.request_firmware_version.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_device_serial_number(self, star_service: StarServiceFixture):
    star_service.backend.request_device_serial_number = unittest.mock.AsyncMock(
      return_value="SN12345"
    )
    result = await star_service.remote.request_device_serial_number()
    assert result == "SN12345"


class TestCoverRPCs:
  @pytest.mark.asyncio
  async def test_lock_cover(self, star_service: StarServiceFixture):
    star_service.backend.lock_cover = unittest.mock.AsyncMock()
    await star_service.remote.lock_cover()
    star_service.backend.lock_cover.assert_called_once()

  @pytest.mark.asyncio
  async def test_unlock_cover(self, star_service: StarServiceFixture):
    star_service.backend.unlock_cover = unittest.mock.AsyncMock()
    await star_service.remote.unlock_cover()
    star_service.backend.unlock_cover.assert_called_once()


class TestConfigRPCs:
  @pytest.mark.asyncio
  async def test_set_single_step_mode(self, star_service: StarServiceFixture):
    star_service.backend.set_single_step_mode = unittest.mock.AsyncMock()
    await star_service.remote.set_single_step_mode(single_step_mode=True)
    star_service.backend.set_single_step_mode.assert_called_once_with(single_step_mode=True)

  @pytest.mark.asyncio
  async def test_halt(self, star_service: StarServiceFixture):
    star_service.backend.halt = unittest.mock.AsyncMock()
    await star_service.remote.halt()
    star_service.backend.halt.assert_called_once()
