"""Tests for pipetting RPCs: tip handling, aspirate, dispense, 96-head ops."""

import unittest.mock

import pytest

from pylabrobot.liquid_handling.standard import (
  Drop,
  DropTipRack,
  MultiHeadAspirationPlate,
  MultiHeadDispensePlate,
  Pickup,
  PickupTipRack,
  SingleChannelAspiration,
  SingleChannelDispense,
)
from pylabrobot.resources import Coordinate

from .conftest import StarServiceFixture


class TestTipHandlingRPCs:
  @pytest.mark.asyncio
  async def test_pick_up_tips(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    spot = tip_rack.get_item("A1")
    tip = spot.get_tip()
    ops = [Pickup(resource=spot, offset=Coordinate.zero(), tip=tip)]
    await star_service.remote.pick_up_tips(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_drop_tips(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    spot = tip_rack.get_item("A1")
    tip = spot.get_tip()
    ops = [Drop(resource=spot, offset=Coordinate.zero(), tip=tip)]
    await star_service.remote.drop_tips(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_pick_up_tips_multiple_channels(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    spots = [tip_rack.get_item(f"A{i+1}") for i in range(3)]
    ops = [Pickup(resource=s, offset=Coordinate.zero(), tip=s.get_tip()) for s in spots]
    await star_service.remote.pick_up_tips(ops=ops, use_channels=[0, 1, 2])
    star_service.backend._write_and_read_command.assert_called()


class TestAspirateDispenseRPCs:
  @pytest.mark.asyncio
  async def test_aspirate_single_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [SingleChannelAspiration(
      resource=well,
      offset=Coordinate.zero(),
      tip=tip,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )]
    await star_service.remote.aspirate(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_dispense_single_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [SingleChannelDispense(
      resource=well,
      offset=Coordinate.zero(),
      tip=tip,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )]
    await star_service.remote.dispense(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_aspirate_with_optional_params(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [SingleChannelAspiration(
      resource=well,
      offset=Coordinate.zero(),
      tip=tip,
      volume=50.0,
      flow_rate=100.0,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )]
    await star_service.remote.aspirate(
      ops=ops,
      use_channels=[0],
      jet=[False],
      blow_out=[False],
      lld_search_height=[30.0],
    )
    star_service.backend._write_and_read_command.assert_called()


class TestProbeRPCs:
  @pytest.mark.asyncio
  async def test_request_tip_presence(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    # request_tip_presence returns a list of ints from firmware response
    star_service.backend.request_tip_presence = unittest.mock.AsyncMock(
      return_value=[0, 0, 0, 0, 0, 0, 0, 0]
    )
    result = await star_service.remote.request_tip_presence()
    assert result == [0, 0, 0, 0, 0, 0, 0, 0]


class Test96HeadPipettingRPCs:
  @pytest.mark.asyncio
  async def test_pick_up_tips96(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tips = [tip_rack.get_item(f"A{i+1}").get_tip() for i in range(8)]
    # pad to 96 with None
    tips_96 = tips + [None] * 88
    pickup = PickupTipRack(
      resource=tip_rack,
      offset=Coordinate.zero(),
      tips=tips_96,
    )
    await star_service.remote.pick_up_tips96(pickup=pickup)
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_drop_tips96(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    drop = DropTipRack(resource=tip_rack, offset=Coordinate.zero())
    await star_service.remote.drop_tips96(drop=drop)
    star_service.backend._write_and_read_command.assert_called()


class TestLowLevelPipRPCs:
  @pytest.mark.asyncio
  async def test_initialize_pip(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    await star_service.remote.initialize_pip()
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_spread_pip_channels(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    await star_service.remote.spread_pip_channels()
    star_service.backend._write_and_read_command.assert_called()
