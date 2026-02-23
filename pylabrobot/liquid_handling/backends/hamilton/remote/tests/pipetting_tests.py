# mypy: disable-error-code="method-assign,attr-defined"
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
from pylabrobot.resources.hamilton import TipPickupMethod, TipSize

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
    ops = [
      SingleChannelAspiration(
        resource=well,
        offset=Coordinate.zero(),
        tip=tip,
        volume=100.0,
        flow_rate=None,
        liquid_height=None,
        blow_out_air_volume=None,
        mix=None,
      )
    ]
    await star_service.remote.aspirate(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_dispense_single_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [
      SingleChannelDispense(
        resource=well,
        offset=Coordinate.zero(),
        tip=tip,
        volume=100.0,
        flow_rate=None,
        liquid_height=None,
        blow_out_air_volume=None,
        mix=None,
      )
    ]
    await star_service.remote.dispense(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_called()

  @pytest.mark.asyncio
  async def test_aspirate_with_optional_params(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [
      SingleChannelAspiration(
        resource=well,
        offset=Coordinate.zero(),
        tip=tip,
        volume=50.0,
        flow_rate=100.0,
        liquid_height=None,
        blow_out_air_volume=None,
        mix=None,
      )
    ]
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

  @pytest.mark.asyncio
  async def test_probe_liquid_heights(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.probe_liquid_heights = unittest.mock.AsyncMock(return_value=[15.5, 16.2])
    plate = star_service.deck.get_resource("plate_01")
    well_a1 = plate.get_item("A1")
    well_a2 = plate.get_item("A2")
    result = await star_service.remote.probe_liquid_heights(
      containers=[well_a1, well_a2],
      use_channels=[0, 1],
    )
    assert result == [15.5, 16.2]
    star_service.backend.probe_liquid_heights.assert_called_once()

  @pytest.mark.asyncio
  async def test_probe_liquid_heights_with_offsets(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.probe_liquid_heights = unittest.mock.AsyncMock(return_value=[12.0])
    plate = star_service.deck.get_resource("plate_01")
    well_a1 = plate.get_item("A1")
    result = await star_service.remote.probe_liquid_heights(
      containers=[well_a1],
      use_channels=[0],
      resource_offsets=[Coordinate(x=0.5, y=0.5, z=0.0)],
      lld_mode=1,
      search_speed=5.0,
      n_replicates=3,
      move_to_z_safety_after=False,
    )
    assert result == [12.0]
    star_service.backend.probe_liquid_heights.assert_called_once()

  @pytest.mark.asyncio
  async def test_probe_liquid_volumes(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.probe_liquid_volumes = unittest.mock.AsyncMock(return_value=[200.0, 150.5])
    plate = star_service.deck.get_resource("plate_01")
    well_a1 = plate.get_item("A1")
    well_a2 = plate.get_item("A2")
    result = await star_service.remote.probe_liquid_volumes(
      containers=[well_a1, well_a2],
      use_channels=[0, 1],
    )
    assert result == [200.0, 150.5]
    star_service.backend.probe_liquid_volumes.assert_called_once()

  @pytest.mark.asyncio
  async def test_probe_liquid_volumes_with_offsets(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.probe_liquid_volumes = unittest.mock.AsyncMock(return_value=[100.0])
    plate = star_service.deck.get_resource("plate_01")
    well_a1 = plate.get_item("A1")
    result = await star_service.remote.probe_liquid_volumes(
      containers=[well_a1],
      use_channels=[0],
      resource_offsets=[Coordinate(x=0.0, y=0.0, z=1.0)],
      lld_mode=1,
      search_speed=8.0,
      n_replicates=2,
      move_to_z_safety_after=True,
    )
    assert result == [100.0]
    star_service.backend.probe_liquid_volumes.assert_called_once()

  @pytest.mark.asyncio
  async def test_channels_sense_tip_presence(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.channels_sense_tip_presence = unittest.mock.AsyncMock(
      return_value=[1, 1, 0, 0, 0, 0, 0, 0]
    )
    result = await star_service.remote.channels_sense_tip_presence()
    assert result == [1, 1, 0, 0, 0, 0, 0, 0]
    star_service.backend.channels_sense_tip_presence.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_pip_height_last_lld(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.request_pip_height_last_lld = unittest.mock.AsyncMock(
      return_value=[10.5, 11.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    )
    result = await star_service.remote.request_pip_height_last_lld()
    assert result == [10.5, 11.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    star_service.backend.request_pip_height_last_lld.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_tadm_status(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.request_tadm_status = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.request_tadm_status()
    star_service.backend.request_tadm_status.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_volume_in_tip(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.request_volume_in_tip = unittest.mock.AsyncMock(return_value=75.5)
    result = await star_service.remote.request_volume_in_tip(channel=0)
    assert result == 75.5
    star_service.backend.request_volume_in_tip.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_tip_len_on_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.request_tip_len_on_channel = unittest.mock.AsyncMock(return_value=95.0)
    result = await star_service.remote.request_tip_len_on_channel(channel_idx=2)
    assert result == 95.0
    star_service.backend.request_tip_len_on_channel.assert_called_once()

  @pytest.mark.asyncio
  async def test_request_probe_z_position(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.request_probe_z_position = unittest.mock.AsyncMock(return_value=120.3)
    result = await star_service.remote.request_probe_z_position(channel_idx=0)
    assert result == 120.3
    star_service.backend.request_probe_z_position.assert_called_once()


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

  @pytest.mark.asyncio
  async def test_aspirate96(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.aspirate96 = unittest.mock.AsyncMock(return_value=None)
    plate = star_service.deck.get_resource("plate_01")
    wells = [plate.get_item(f"A{i+1}") for i in range(8)]
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tips = [tip_rack.get_item(f"A{i+1}").get_tip() for i in range(8)]
    tips_96 = tips + [None] * 88
    aspiration = MultiHeadAspirationPlate(
      wells=wells,
      offset=Coordinate.zero(),
      tips=tips_96,
      volume=50.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    await star_service.remote.aspirate96(aspiration=aspiration)
    star_service.backend.aspirate96.assert_called_once()

  @pytest.mark.asyncio
  async def test_dispense96(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.dispense96 = unittest.mock.AsyncMock(return_value=None)
    plate = star_service.deck.get_resource("plate_01")
    wells = [plate.get_item(f"A{i+1}") for i in range(8)]
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tips = [tip_rack.get_item(f"A{i+1}").get_tip() for i in range(8)]
    tips_96 = tips + [None] * 88
    dispense_op = MultiHeadDispensePlate(
      wells=wells,
      offset=Coordinate.zero(),
      tips=tips_96,
      volume=50.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    await star_service.remote.dispense96(dispense=dispense_op)
    star_service.backend.dispense96.assert_called_once()


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

  @pytest.mark.asyncio
  async def test_initialize_pipetting_channels(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.initialize_pipetting_channels = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.initialize_pipetting_channels(
      x_positions=[100, 200],
      y_positions=[300, 400],
      begin_of_tip_deposit_process=10,
      end_of_tip_deposit_process=20,
      z_position_at_end_of_a_command=3600,
      tip_pattern=[True, True],
      tip_type=16,
      discarding_method=1,
    )
    star_service.backend.initialize_pipetting_channels.assert_called_once()

  @pytest.mark.asyncio
  async def test_pick_up_tip_fw(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.pick_up_tip = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.pick_up_tip(
      x_positions=[1000],
      y_positions=[2000],
      tip_pattern=[True],
      tip_type_idx=4,
      begin_tip_pick_up_process=0,
      end_tip_pick_up_process=0,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      pickup_method=TipPickupMethod.OUT_OF_RACK,
    )
    star_service.backend.pick_up_tip.assert_called_once()

  @pytest.mark.asyncio
  async def test_discard_tip_fw(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.discard_tip = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.discard_tip(
      x_positions=[1000],
      y_positions=[2000],
      tip_pattern=[True],
      begin_tip_deposit_process=0,
      end_tip_deposit_process=0,
      minimum_traverse_height_at_beginning_of_a_command=3600,
      z_position_at_end_of_a_command=3600,
      discarding_method=1,
    )
    star_service.backend.discard_tip.assert_called_once()

  @pytest.mark.asyncio
  async def test_aspirate_pip(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.aspirate_pip = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.aspirate_pip(
      aspiration_type=[0],
      tip_pattern=[True],
      x_positions=[1000],
      y_positions=[2000],
      aspiration_volumes=[500],
    )
    star_service.backend.aspirate_pip.assert_called_once()

  @pytest.mark.asyncio
  async def test_dispense_pip(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.dispense_pip = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.dispense_pip(
      tip_pattern=[True],
      dispensing_mode=[0],
      x_positions=[1000],
      y_positions=[2000],
      dispense_volumes=[500],
    )
    star_service.backend.dispense_pip.assert_called_once()

  @pytest.mark.asyncio
  async def test_move_all_pipetting_channels_to_defined_position(
    self, star_service: StarServiceFixture
  ):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.move_all_pipetting_channels_to_defined_position = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.move_all_pipetting_channels_to_defined_position(
      tip_pattern=True,
      x_positions=1000,
      y_positions=2000,
      minimum_traverse_height_at_beginning_of_command=3600,
      z_endpos=500,
    )
    star_service.backend.move_all_pipetting_channels_to_defined_position.assert_called_once()

  @pytest.mark.asyncio
  async def test_define_tip_needle(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.define_tip_needle = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.define_tip_needle(
      tip_type_table_index=4,
      has_filter=True,
      tip_length=950,
      maximum_tip_volume=300,
      tip_size=TipSize.STANDARD_VOLUME,
      pickup_method=TipPickupMethod.OUT_OF_RACK,
    )
    star_service.backend.define_tip_needle.assert_called_once()


class TestLLDProbeRPCs:
  @pytest.mark.asyncio
  async def test_clld_probe_z_height_using_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.clld_probe_z_height_using_channel = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.clld_probe_z_height_using_channel(
      channel_idx=0,
      lowest_reading_position=500,
      highest_reading_position=3500,
      channel_speed=100,
      gamma_lld_sensitivity=4,
    )
    star_service.backend.clld_probe_z_height_using_channel.assert_called_once()

  @pytest.mark.asyncio
  async def test_clld_probe_z_height_defaults(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.clld_probe_z_height_using_channel = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.clld_probe_z_height_using_channel(channel_idx=2)
    star_service.backend.clld_probe_z_height_using_channel.assert_called_once()

  @pytest.mark.asyncio
  async def test_plld_probe_z_height_using_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.plld_probe_z_height_using_channel = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.plld_probe_z_height_using_channel(
      channel_idx=1,
      lowest_reading_position=600,
      highest_reading_position=3400,
      channel_speed=80,
      dp_lld_sensitivity=3,
    )
    star_service.backend.plld_probe_z_height_using_channel.assert_called_once()

  @pytest.mark.asyncio
  async def test_plld_probe_z_height_defaults(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.plld_probe_z_height_using_channel = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.plld_probe_z_height_using_channel(channel_idx=3)
    star_service.backend.plld_probe_z_height_using_channel.assert_called_once()

  @pytest.mark.asyncio
  async def test_ztouch_probe_z_height_using_channel(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.ztouch_probe_z_height_using_channel = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.ztouch_probe_z_height_using_channel(
      channel_idx=0,
      lowest_reading_position=400,
      highest_reading_position=3600,
      channel_speed=120,
    )
    star_service.backend.ztouch_probe_z_height_using_channel.assert_called_once()

  @pytest.mark.asyncio
  async def test_ztouch_probe_z_height_defaults(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.ztouch_probe_z_height_using_channel = unittest.mock.AsyncMock(
      return_value=None
    )
    await star_service.remote.ztouch_probe_z_height_using_channel(channel_idx=5)
    star_service.backend.ztouch_probe_z_height_using_channel.assert_called_once()


class TestFoilRPCs:
  @pytest.mark.asyncio
  async def test_pierce_foil(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.move_channel_x = unittest.mock.AsyncMock(return_value=None)
    star_service.backend.position_single_pipetting_channel_in_y_direction = unittest.mock.AsyncMock(
      return_value=None
    )
    star_service.backend.move_channel_z = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.pierce_foil(
      channel_idx=0,
      x_position=1000,
      y_position=2000,
      z_start_position=3000,
      z_end_position=500,
    )
    star_service.backend.move_channel_x.assert_called()
    star_service.backend.move_channel_z.assert_called()

  @pytest.mark.asyncio
  async def test_pierce_foil_defaults(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.move_channel_x = unittest.mock.AsyncMock(return_value=None)
    star_service.backend.position_single_pipetting_channel_in_y_direction = unittest.mock.AsyncMock(
      return_value=None
    )
    star_service.backend.move_channel_z = unittest.mock.AsyncMock(return_value=None)
    # Only required param is channel_idx
    await star_service.remote.pierce_foil(channel_idx=1)
    # With no optional positions, the backend move methods should not be called
    # (the server only calls them when optional fields are present)

  @pytest.mark.asyncio
  async def test_step_off_foil(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.move_channel_x = unittest.mock.AsyncMock(return_value=None)
    star_service.backend.position_single_pipetting_channel_in_y_direction = unittest.mock.AsyncMock(
      return_value=None
    )
    star_service.backend.move_channel_z = unittest.mock.AsyncMock(return_value=None)
    star_service.backend.move_all_channels_in_z_safety = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.step_off_foil(
      channel_idx=0,
      x_position=1000,
      y_position=2000,
      z_position=500,
    )
    star_service.backend.move_channel_x.assert_called()
    star_service.backend.move_all_channels_in_z_safety.assert_called()

  @pytest.mark.asyncio
  async def test_step_off_foil_defaults(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.move_channel_x = unittest.mock.AsyncMock(return_value=None)
    star_service.backend.position_single_pipetting_channel_in_y_direction = unittest.mock.AsyncMock(
      return_value=None
    )
    star_service.backend.move_channel_z = unittest.mock.AsyncMock(return_value=None)
    star_service.backend.move_all_channels_in_z_safety = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.step_off_foil(channel_idx=2)
    star_service.backend.move_all_channels_in_z_safety.assert_called()


class TestEmptyTipRPCs:
  @pytest.mark.asyncio
  async def test_empty_tip(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.empty_tip = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.empty_tip(
      channel_idx=0,
      holding_volume=100.0,
      acceleration=5.0,
      flow_rate=50.0,
      current_limit=200,
    )
    star_service.backend.empty_tip.assert_called_once()

  @pytest.mark.asyncio
  async def test_empty_tips(self, star_service: StarServiceFixture):
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend.empty_tips = unittest.mock.AsyncMock(return_value=None)
    await star_service.remote.empty_tips(
      channels=[0, 1, 2],
      holding_volume=150.0,
      acceleration=4.0,
      flow_rate=60.0,
      current_limit=250,
    )
    star_service.backend.empty_tips.assert_called_once()
