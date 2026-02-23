"""Client stubs for all pipetting RPCs (core LH, low-level pip, TADM/LLD)."""

from __future__ import annotations

from typing import List, Optional, Union

from pylabrobot.liquid_handling.standard import (
  Drop,
  DropTipRack,
  MultiHeadAspirationContainer,
  MultiHeadAspirationPlate,
  MultiHeadDispenseContainer,
  MultiHeadDispensePlate,
  Pickup,
  PickupTipRack,
  SingleChannelAspiration,
  SingleChannelDispense,
)
from pylabrobot.resources import Coordinate
from pylabrobot.resources.hamilton import TipPickupMethod, TipSize

from .. import star_service_pb2 as pb2
from ..helpers import (
  aspiration_to_proto,
  coordinate_to_proto,
  dispense_to_proto,
  drop_tip_rack_to_proto,
  drop_to_proto,
  multi_head_aspiration_container_to_proto,
  multi_head_aspiration_plate_to_proto,
  multi_head_dispense_container_to_proto,
  multi_head_dispense_plate_to_proto,
  pickup_tip_rack_to_proto,
  pickup_to_proto,
)

# Maps from Python enums to proto enums for DefineTipNeedle
_TIP_SIZE_TO_PROTO = {
  TipSize.UNDEFINED: pb2.TIP_SIZE_UNDEFINED,
  TipSize.LOW_VOLUME: pb2.LOW_VOLUME,
  TipSize.STANDARD_VOLUME: pb2.STANDARD_VOLUME,
  TipSize.HIGH_VOLUME: pb2.HIGH_VOLUME,
  TipSize.CORE_384_HEAD_TIP: pb2.CORE_384,
  TipSize.XL: pb2.XL,
}

_PICKUP_METHOD_TO_PROTO = {
  TipPickupMethod.OUT_OF_RACK: pb2.OUT_OF_RACK,
  TipPickupMethod.OUT_OF_WASH_LIQUID: pb2.OUT_OF_WASH_LIQUID,
}


class PipettingClientMixin:
  """Client stubs for pipetting RPCs: core LH interface, low-level pip, and TADM/LLD.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # =========================================================================
  # Core LH interface: PickUpTips, DropTips, Aspirate, Dispense
  # =========================================================================

  async def pick_up_tips(
    self,
    ops: List[Pickup],
    use_channels: List[int],
    begin_tip_pick_up_process: Optional[float] = None,
    end_tip_pick_up_process: Optional[float] = None,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    pickup_method: Optional[TipPickupMethod] = None,
  ) -> None:
    kwargs: dict = dict(
      ops=[pickup_to_proto(op) for op in ops],
      use_channels=use_channels,
    )
    if begin_tip_pick_up_process is not None:
      kwargs["begin_tip_pick_up_process"] = begin_tip_pick_up_process
    if end_tip_pick_up_process is not None:
      kwargs["end_tip_pick_up_process"] = end_tip_pick_up_process
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if pickup_method is not None:
      kwargs["pickup_method"] = pickup_method.value
    self._client.pick_up_tips(pb2.PickUpTipsRequest(**kwargs))

  async def drop_tips(
    self,
    ops: List[Drop],
    use_channels: List[int],
    drop_method: Optional[int] = None,
    begin_tip_deposit_process: Optional[float] = None,
    end_tip_deposit_process: Optional[float] = None,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    z_position_at_end_of_a_command: Optional[float] = None,
  ) -> None:
    kwargs: dict = dict(
      ops=[drop_to_proto(op) for op in ops],
      use_channels=use_channels,
    )
    if drop_method is not None:
      kwargs["drop_method"] = drop_method
    if begin_tip_deposit_process is not None:
      kwargs["begin_tip_deposit_process"] = begin_tip_deposit_process
    if end_tip_deposit_process is not None:
      kwargs["end_tip_deposit_process"] = end_tip_deposit_process
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if z_position_at_end_of_a_command is not None:
      kwargs["z_position_at_end_of_a_command"] = z_position_at_end_of_a_command
    self._client.drop_tips(pb2.DropTipsRequest(**kwargs))

  async def aspirate(
    self,
    ops: List[SingleChannelAspiration],
    use_channels: List[int],
    jet: Optional[List[bool]] = None,
    blow_out: Optional[List[bool]] = None,
    lld_search_height: Optional[List[float]] = None,
    clot_detection_height: Optional[List[float]] = None,
    pull_out_distance_transport_air: Optional[List[float]] = None,
    second_section_height: Optional[List[float]] = None,
    second_section_ratio: Optional[List[float]] = None,
    minimum_height: Optional[List[float]] = None,
    immersion_depth: Optional[List[float]] = None,
    surface_following_distance: Optional[List[float]] = None,
    transport_air_volume: Optional[List[float]] = None,
    pre_wetting_volume: Optional[List[float]] = None,
    lld_mode: Optional[List[int]] = None,
    gamma_lld_sensitivity: Optional[List[int]] = None,
    dp_lld_sensitivity: Optional[List[int]] = None,
    aspirate_position_above_z_touch_off: Optional[List[float]] = None,
    detection_height_difference_for_dual_lld: Optional[List[float]] = None,
    swap_speed: Optional[List[float]] = None,
    settling_time: Optional[List[float]] = None,
    mix_position_from_liquid_surface: Optional[List[float]] = None,
    mix_surface_following_distance: Optional[List[float]] = None,
    limit_curve_index: Optional[List[int]] = None,
    use_2nd_section_aspiration: Optional[List[bool]] = None,
    retract_height_over_2nd_section_to_empty_tip: Optional[List[float]] = None,
    dispensation_speed_during_emptying_tip: Optional[List[float]] = None,
    dosing_drive_speed_during_2nd_section_search: Optional[List[float]] = None,
    z_drive_speed_during_2nd_section_search: Optional[List[float]] = None,
    cup_upper_edge: Optional[List[float]] = None,
    ratio_liquid_rise_to_tip_deep_in: Optional[List[int]] = None,
    immersion_depth_2nd_section: Optional[List[float]] = None,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    min_z_endpos: Optional[float] = None,
    liquid_surface_no_lld: Optional[List[float]] = None,
    probe_liquid_height: bool = False,
    auto_surface_following_distance: bool = False,
    disable_volume_correction: Optional[List[bool]] = None,
  ) -> None:
    kwargs: dict = dict(
      ops=[aspiration_to_proto(op) for op in ops],
      use_channels=use_channels,
      probe_liquid_height=probe_liquid_height,
      auto_surface_following_distance=auto_surface_following_distance,
    )
    if jet is not None:
      kwargs["jet"] = jet
    if blow_out is not None:
      kwargs["blow_out"] = blow_out
    if lld_search_height is not None:
      kwargs["lld_search_height"] = lld_search_height
    if clot_detection_height is not None:
      kwargs["clot_detection_height"] = clot_detection_height
    if pull_out_distance_transport_air is not None:
      kwargs["pull_out_distance_transport_air"] = pull_out_distance_transport_air
    if second_section_height is not None:
      kwargs["second_section_height"] = second_section_height
    if second_section_ratio is not None:
      kwargs["second_section_ratio"] = second_section_ratio
    if minimum_height is not None:
      kwargs["minimum_height"] = minimum_height
    if immersion_depth is not None:
      kwargs["immersion_depth"] = immersion_depth
    if surface_following_distance is not None:
      kwargs["surface_following_distance"] = surface_following_distance
    if transport_air_volume is not None:
      kwargs["transport_air_volume"] = transport_air_volume
    if pre_wetting_volume is not None:
      kwargs["pre_wetting_volume"] = pre_wetting_volume
    if lld_mode is not None:
      kwargs["lld_mode"] = lld_mode
    if gamma_lld_sensitivity is not None:
      kwargs["gamma_lld_sensitivity"] = gamma_lld_sensitivity
    if dp_lld_sensitivity is not None:
      kwargs["dp_lld_sensitivity"] = dp_lld_sensitivity
    if aspirate_position_above_z_touch_off is not None:
      kwargs["aspirate_position_above_z_touch_off"] = aspirate_position_above_z_touch_off
    if detection_height_difference_for_dual_lld is not None:
      kwargs["detection_height_difference_for_dual_lld"] = (
        detection_height_difference_for_dual_lld
      )
    if swap_speed is not None:
      kwargs["swap_speed"] = swap_speed
    if settling_time is not None:
      kwargs["settling_time"] = settling_time
    if mix_position_from_liquid_surface is not None:
      kwargs["mix_position_from_liquid_surface"] = mix_position_from_liquid_surface
    if mix_surface_following_distance is not None:
      kwargs["mix_surface_following_distance"] = mix_surface_following_distance
    if limit_curve_index is not None:
      kwargs["limit_curve_index"] = limit_curve_index
    if use_2nd_section_aspiration is not None:
      kwargs["use_2nd_section_aspiration"] = use_2nd_section_aspiration
    if retract_height_over_2nd_section_to_empty_tip is not None:
      kwargs["retract_height_over_2nd_section_to_empty_tip"] = (
        retract_height_over_2nd_section_to_empty_tip
      )
    if dispensation_speed_during_emptying_tip is not None:
      kwargs["dispensation_speed_during_emptying_tip"] = dispensation_speed_during_emptying_tip
    if dosing_drive_speed_during_2nd_section_search is not None:
      kwargs["dosing_drive_speed_during_2nd_section_search"] = (
        dosing_drive_speed_during_2nd_section_search
      )
    if z_drive_speed_during_2nd_section_search is not None:
      kwargs["z_drive_speed_during_2nd_section_search"] = (
        z_drive_speed_during_2nd_section_search
      )
    if cup_upper_edge is not None:
      kwargs["cup_upper_edge"] = cup_upper_edge
    if ratio_liquid_rise_to_tip_deep_in is not None:
      kwargs["ratio_liquid_rise_to_tip_deep_in"] = ratio_liquid_rise_to_tip_deep_in
    if immersion_depth_2nd_section is not None:
      kwargs["immersion_depth_2nd_section"] = immersion_depth_2nd_section
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if min_z_endpos is not None:
      kwargs["min_z_endpos"] = min_z_endpos
    if liquid_surface_no_lld is not None:
      kwargs["liquid_surface_no_lld"] = liquid_surface_no_lld
    if disable_volume_correction is not None:
      kwargs["disable_volume_correction"] = disable_volume_correction
    self._client.aspirate(pb2.AspirateRequest(**kwargs))

  async def dispense(
    self,
    ops: List[SingleChannelDispense],
    use_channels: List[int],
    lld_search_height: Optional[List[float]] = None,
    liquid_surface_no_lld: Optional[List[float]] = None,
    pull_out_distance_transport_air: Optional[List[float]] = None,
    second_section_height: Optional[List[float]] = None,
    second_section_ratio: Optional[List[float]] = None,
    minimum_height: Optional[List[float]] = None,
    immersion_depth: Optional[List[float]] = None,
    surface_following_distance: Optional[List[float]] = None,
    cut_off_speed: Optional[List[float]] = None,
    stop_back_volume: Optional[List[float]] = None,
    transport_air_volume: Optional[List[float]] = None,
    lld_mode: Optional[List[int]] = None,
    dispense_position_above_z_touch_off: Optional[List[float]] = None,
    gamma_lld_sensitivity: Optional[List[int]] = None,
    dp_lld_sensitivity: Optional[List[int]] = None,
    swap_speed: Optional[List[float]] = None,
    settling_time: Optional[List[float]] = None,
    mix_position_from_liquid_surface: Optional[List[float]] = None,
    mix_surface_following_distance: Optional[List[float]] = None,
    limit_curve_index: Optional[List[int]] = None,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    min_z_endpos: Optional[float] = None,
    side_touch_off_distance: float = 0,
    jet: Optional[List[bool]] = None,
    blow_out: Optional[List[bool]] = None,
    empty: Optional[List[bool]] = None,
    probe_liquid_height: bool = False,
    auto_surface_following_distance: bool = False,
    disable_volume_correction: Optional[List[bool]] = None,
  ) -> None:
    kwargs: dict = dict(
      ops=[dispense_to_proto(op) for op in ops],
      use_channels=use_channels,
      side_touch_off_distance=side_touch_off_distance,
      probe_liquid_height=probe_liquid_height,
      auto_surface_following_distance=auto_surface_following_distance,
    )
    if lld_search_height is not None:
      kwargs["lld_search_height"] = lld_search_height
    if liquid_surface_no_lld is not None:
      kwargs["liquid_surface_no_lld"] = liquid_surface_no_lld
    if pull_out_distance_transport_air is not None:
      kwargs["pull_out_distance_transport_air"] = pull_out_distance_transport_air
    if second_section_height is not None:
      kwargs["second_section_height"] = second_section_height
    if second_section_ratio is not None:
      kwargs["second_section_ratio"] = second_section_ratio
    if minimum_height is not None:
      kwargs["minimum_height"] = minimum_height
    if immersion_depth is not None:
      kwargs["immersion_depth"] = immersion_depth
    if surface_following_distance is not None:
      kwargs["surface_following_distance"] = surface_following_distance
    if cut_off_speed is not None:
      kwargs["cut_off_speed"] = cut_off_speed
    if stop_back_volume is not None:
      kwargs["stop_back_volume"] = stop_back_volume
    if transport_air_volume is not None:
      kwargs["transport_air_volume"] = transport_air_volume
    if lld_mode is not None:
      kwargs["lld_mode"] = lld_mode
    if dispense_position_above_z_touch_off is not None:
      kwargs["dispense_position_above_z_touch_off"] = dispense_position_above_z_touch_off
    if gamma_lld_sensitivity is not None:
      kwargs["gamma_lld_sensitivity"] = gamma_lld_sensitivity
    if dp_lld_sensitivity is not None:
      kwargs["dp_lld_sensitivity"] = dp_lld_sensitivity
    if swap_speed is not None:
      kwargs["swap_speed"] = swap_speed
    if settling_time is not None:
      kwargs["settling_time"] = settling_time
    if mix_position_from_liquid_surface is not None:
      kwargs["mix_position_from_liquid_surface"] = mix_position_from_liquid_surface
    if mix_surface_following_distance is not None:
      kwargs["mix_surface_following_distance"] = mix_surface_following_distance
    if limit_curve_index is not None:
      kwargs["limit_curve_index"] = limit_curve_index
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if min_z_endpos is not None:
      kwargs["min_z_endpos"] = min_z_endpos
    if jet is not None:
      kwargs["jet"] = jet
    if blow_out is not None:
      kwargs["blow_out"] = blow_out
    if empty is not None:
      kwargs["empty"] = empty
    if disable_volume_correction is not None:
      kwargs["disable_volume_correction"] = disable_volume_correction
    self._client.dispense(pb2.DispenseRequest(**kwargs))

  # =========================================================================
  # Core LH interface: 96-head high-level
  # =========================================================================

  async def pick_up_tips96(
    self,
    pickup: PickupTipRack,
    tip_pickup_method: str = "from_rack",
    minimum_height_command_end: Optional[float] = None,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    experimental_alignment_tipspot_identifier: str = "A1",
  ) -> None:
    kwargs: dict = dict(
      pickup=pickup_tip_rack_to_proto(pickup),
      tip_pickup_method=tip_pickup_method,
      experimental_alignment_tipspot_identifier=experimental_alignment_tipspot_identifier,
    )
    if minimum_height_command_end is not None:
      kwargs["minimum_height_command_end"] = minimum_height_command_end
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    self._client.pick_up_tips96(pb2.PickUpTips96Request(**kwargs))

  async def drop_tips96(
    self,
    drop: DropTipRack,
    minimum_height_command_end: Optional[float] = None,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    experimental_alignment_tipspot_identifier: str = "A1",
  ) -> None:
    kwargs: dict = dict(
      drop=drop_tip_rack_to_proto(drop),
      experimental_alignment_tipspot_identifier=experimental_alignment_tipspot_identifier,
    )
    if minimum_height_command_end is not None:
      kwargs["minimum_height_command_end"] = minimum_height_command_end
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    self._client.drop_tips96(pb2.DropTips96Request(**kwargs))

  async def aspirate96(
    self,
    aspiration: Union[MultiHeadAspirationPlate, MultiHeadAspirationContainer],
    jet: bool = False,
    blow_out: bool = False,
    use_lld: bool = False,
    pull_out_distance_transport_air: float = 10,
    aspiration_type: int = 0,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    min_z_endpos: Optional[float] = None,
    lld_search_height: float = 199.9,
    minimum_height: Optional[float] = None,
    second_section_height: float = 3.2,
    second_section_ratio: float = 618.0,
    immersion_depth: float = 0,
    surface_following_distance: float = 0,
    transport_air_volume: float = 5.0,
    pre_wetting_volume: float = 5.0,
    gamma_lld_sensitivity: int = 1,
    swap_speed: float = 2.0,
    settling_time: float = 1.0,
    mix_position_from_liquid_surface: float = 0,
    mix_surface_following_distance: float = 0,
    limit_curve_index: int = 0,
    disable_volume_correction: bool = False,
  ) -> None:
    kwargs: dict = dict(
      jet=jet,
      blow_out=blow_out,
      use_lld=use_lld,
      pull_out_distance_transport_air=pull_out_distance_transport_air,
      aspiration_type=aspiration_type,
      lld_search_height=lld_search_height,
      second_section_height=second_section_height,
      second_section_ratio=second_section_ratio,
      immersion_depth=immersion_depth,
      surface_following_distance=surface_following_distance,
      transport_air_volume=transport_air_volume,
      pre_wetting_volume=pre_wetting_volume,
      gamma_lld_sensitivity=gamma_lld_sensitivity,
      swap_speed=swap_speed,
      settling_time=settling_time,
      mix_position_from_liquid_surface=mix_position_from_liquid_surface,
      mix_surface_following_distance=mix_surface_following_distance,
      limit_curve_index=limit_curve_index,
      disable_volume_correction=disable_volume_correction,
    )
    # oneof aspiration: plate or container
    if isinstance(aspiration, MultiHeadAspirationPlate):
      kwargs["plate"] = multi_head_aspiration_plate_to_proto(aspiration)
    else:
      kwargs["container"] = multi_head_aspiration_container_to_proto(aspiration)
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if min_z_endpos is not None:
      kwargs["min_z_endpos"] = min_z_endpos
    if minimum_height is not None:
      kwargs["minimum_height"] = minimum_height
    self._client.aspirate96(pb2.Aspirate96Request(**kwargs))

  async def dispense96(
    self,
    dispense: Union[MultiHeadDispensePlate, MultiHeadDispenseContainer],
    jet: bool = False,
    empty: bool = False,
    blow_out: bool = False,
    pull_out_distance_transport_air: float = 10,
    use_lld: bool = False,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    min_z_endpos: Optional[float] = None,
    lld_search_height: float = 199.9,
    minimum_height: Optional[float] = None,
    second_section_height: float = 3.2,
    second_section_ratio: float = 618.0,
    immersion_depth: float = 0,
    surface_following_distance: float = 0,
    transport_air_volume: float = 5.0,
    gamma_lld_sensitivity: int = 1,
    swap_speed: float = 2.0,
    settling_time: float = 0,
    mix_position_from_liquid_surface: float = 0,
    mix_surface_following_distance: float = 0,
    limit_curve_index: int = 0,
    cut_off_speed: float = 5.0,
    stop_back_volume: float = 0,
    disable_volume_correction: bool = False,
  ) -> None:
    kwargs: dict = dict(
      jet=jet,
      empty=empty,
      blow_out=blow_out,
      pull_out_distance_transport_air=pull_out_distance_transport_air,
      use_lld=use_lld,
      lld_search_height=lld_search_height,
      second_section_height=second_section_height,
      second_section_ratio=second_section_ratio,
      immersion_depth=immersion_depth,
      surface_following_distance=surface_following_distance,
      transport_air_volume=transport_air_volume,
      gamma_lld_sensitivity=gamma_lld_sensitivity,
      swap_speed=swap_speed,
      settling_time=settling_time,
      mix_position_from_liquid_surface=mix_position_from_liquid_surface,
      mix_surface_following_distance=mix_surface_following_distance,
      limit_curve_index=limit_curve_index,
      cut_off_speed=cut_off_speed,
      stop_back_volume=stop_back_volume,
      disable_volume_correction=disable_volume_correction,
    )
    # oneof dispense_op: plate or container
    if isinstance(dispense, MultiHeadDispensePlate):
      kwargs["plate"] = multi_head_dispense_plate_to_proto(dispense)
    else:
      kwargs["container"] = multi_head_dispense_container_to_proto(dispense)
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if min_z_endpos is not None:
      kwargs["min_z_endpos"] = min_z_endpos
    if minimum_height is not None:
      kwargs["minimum_height"] = minimum_height
    self._client.dispense96(pb2.Dispense96Request(**kwargs))

  # =========================================================================
  # Low-level pip: InitializePip, InitializePipettingChannels, PickUpTipFw,
  #   DiscardTipFw, AspiratePip, DispensePip, SpreadPipChannels,
  #   MoveAllPipettingChannelsToDefinedPosition, DefineTipNeedle
  # =========================================================================

  async def initialize_pip(self) -> None:
    self._client.initialize_pip(pb2.InitializePipRequest())

  async def initialize_pipetting_channels(
    self,
    x_positions: List[int] = [0],
    y_positions: List[int] = [0],
    begin_of_tip_deposit_process: int = 0,
    end_of_tip_deposit_process: int = 0,
    z_position_at_end_of_a_command: int = 3600,
    tip_pattern: List[bool] = [True],
    tip_type: int = 16,
    discarding_method: int = 1,
  ) -> None:
    self._client.initialize_pipetting_channels(
      pb2.InitializePipettingChannelsRequest(
        x_positions=x_positions,
        y_positions=y_positions,
        begin_of_tip_deposit_process=begin_of_tip_deposit_process,
        end_of_tip_deposit_process=end_of_tip_deposit_process,
        z_position_at_end_of_a_command=z_position_at_end_of_a_command,
        tip_pattern=tip_pattern,
        tip_type=tip_type,
        discarding_method=discarding_method,
      )
    )

  async def pick_up_tip(
    self,
    x_positions: List[int],
    y_positions: List[int],
    tip_pattern: List[bool],
    tip_type_idx: int,
    begin_tip_pick_up_process: int = 0,
    end_tip_pick_up_process: int = 0,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    pickup_method: TipPickupMethod = TipPickupMethod.OUT_OF_RACK,
  ) -> None:
    self._client.pick_up_tip_fw(
      pb2.PickUpTipFwRequest(
        x_positions=x_positions,
        y_positions=y_positions,
        tip_pattern=tip_pattern,
        tip_type_idx=tip_type_idx,
        begin_tip_pick_up_process=begin_tip_pick_up_process,
        end_tip_pick_up_process=end_tip_pick_up_process,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        pickup_method=pickup_method.value,
      )
    )

  async def discard_tip(
    self,
    x_positions: List[int],
    y_positions: List[int],
    tip_pattern: List[bool],
    begin_tip_deposit_process: int = 0,
    end_tip_deposit_process: int = 0,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    z_position_at_end_of_a_command: int = 3600,
    discarding_method: int = 1,
  ) -> None:
    self._client.discard_tip_fw(
      pb2.DiscardTipFwRequest(
        x_positions=x_positions,
        y_positions=y_positions,
        tip_pattern=tip_pattern,
        begin_tip_deposit_process=begin_tip_deposit_process,
        end_tip_deposit_process=end_tip_deposit_process,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        z_position_at_end_of_a_command=z_position_at_end_of_a_command,
        discarding_method=discarding_method,
      )
    )

  async def aspirate_pip(
    self,
    aspiration_type: List[int] = [0],
    tip_pattern: List[bool] = [True],
    x_positions: List[int] = [0],
    y_positions: List[int] = [0],
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    min_z_endpos: int = 3600,
    lld_search_height: List[int] = [0],
    clot_detection_height: List[int] = [60],
    liquid_surface_no_lld: List[int] = [3600],
    pull_out_distance_transport_air: List[int] = [50],
    second_section_height: List[int] = [0],
    second_section_ratio: List[int] = [0],
    minimum_height: List[int] = [3600],
    immersion_depth: List[int] = [0],
    immersion_depth_direction: List[int] = [0],
    surface_following_distance: List[int] = [0],
    aspiration_volumes: List[int] = [0],
    aspiration_speed: List[int] = [500],
    transport_air_volume: List[int] = [0],
    blow_out_air_volume: List[int] = [200],
    pre_wetting_volume: List[int] = [0],
    lld_mode: List[int] = [1],
    gamma_lld_sensitivity: List[int] = [1],
    dp_lld_sensitivity: List[int] = [1],
    aspirate_position_above_z_touch_off: List[int] = [5],
    detection_height_difference_for_dual_lld: List[int] = [0],
    swap_speed: List[int] = [100],
    settling_time: List[int] = [5],
    mix_volume: List[int] = [0],
    mix_cycles: List[int] = [0],
    mix_position_from_liquid_surface: List[int] = [250],
    mix_speed: List[int] = [500],
    mix_surface_following_distance: List[int] = [0],
    limit_curve_index: List[int] = [0],
    tadm_algorithm: bool = False,
    recording_mode: int = 0,
    use_2nd_section_aspiration: List[bool] = [False],
    retract_height_over_2nd_section_to_empty_tip: List[int] = [60],
    dispensation_speed_during_emptying_tip: List[int] = [468],
    dosing_drive_speed_during_2nd_section_search: List[int] = [468],
    z_drive_speed_during_2nd_section_search: List[int] = [215],
    cup_upper_edge: List[int] = [3600],
  ) -> None:
    self._client.aspirate_pip(
      pb2.AspiratePipRequest(
        aspiration_type=aspiration_type,
        tip_pattern=tip_pattern,
        x_positions=x_positions,
        y_positions=y_positions,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        min_z_endpos=min_z_endpos,
        lld_search_height=lld_search_height,
        clot_detection_height=clot_detection_height,
        liquid_surface_no_lld=liquid_surface_no_lld,
        pull_out_distance_transport_air=pull_out_distance_transport_air,
        second_section_height=second_section_height,
        second_section_ratio=second_section_ratio,
        minimum_height=minimum_height,
        immersion_depth=immersion_depth,
        immersion_depth_direction=immersion_depth_direction,
        surface_following_distance=surface_following_distance,
        aspiration_volumes=aspiration_volumes,
        aspiration_speed=aspiration_speed,
        transport_air_volume=transport_air_volume,
        blow_out_air_volume=blow_out_air_volume,
        pre_wetting_volume=pre_wetting_volume,
        lld_mode=lld_mode,
        gamma_lld_sensitivity=gamma_lld_sensitivity,
        dp_lld_sensitivity=dp_lld_sensitivity,
        aspirate_position_above_z_touch_off=aspirate_position_above_z_touch_off,
        detection_height_difference_for_dual_lld=detection_height_difference_for_dual_lld,
        swap_speed=swap_speed,
        settling_time=settling_time,
        mix_volume=mix_volume,
        mix_cycles=mix_cycles,
        mix_position_from_liquid_surface=mix_position_from_liquid_surface,
        mix_speed=mix_speed,
        mix_surface_following_distance=mix_surface_following_distance,
        limit_curve_index=limit_curve_index,
        tadm_algorithm=tadm_algorithm,
        recording_mode=recording_mode,
        use_2nd_section_aspiration=use_2nd_section_aspiration,
        retract_height_over_2nd_section_to_empty_tip=retract_height_over_2nd_section_to_empty_tip,
        dispensation_speed_during_emptying_tip=dispensation_speed_during_emptying_tip,
        dosing_drive_speed_during_2nd_section_search=dosing_drive_speed_during_2nd_section_search,
        z_drive_speed_during_2nd_section_search=z_drive_speed_during_2nd_section_search,
        cup_upper_edge=cup_upper_edge,
      )
    )

  async def dispense_pip(
    self,
    tip_pattern: List[bool],
    dispensing_mode: List[int] = [0],
    x_positions: List[int] = [0],
    y_positions: List[int] = [0],
    minimum_height: List[int] = [3600],
    lld_search_height: List[int] = [0],
    liquid_surface_no_lld: List[int] = [3600],
    pull_out_distance_transport_air: List[int] = [50],
    immersion_depth: List[int] = [0],
    immersion_depth_direction: List[int] = [0],
    surface_following_distance: List[int] = [0],
    second_section_height: List[int] = [0],
    second_section_ratio: List[int] = [0],
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    min_z_endpos: int = 3600,
    dispense_volumes: List[int] = [0],
    dispense_speed: List[int] = [500],
    cut_off_speed: List[int] = [250],
    stop_back_volume: List[int] = [0],
    transport_air_volume: List[int] = [0],
    blow_out_air_volume: List[int] = [200],
    lld_mode: List[int] = [1],
    side_touch_off_distance: int = 1,
    dispense_position_above_z_touch_off: List[int] = [5],
    gamma_lld_sensitivity: List[int] = [1],
    dp_lld_sensitivity: List[int] = [1],
    swap_speed: List[int] = [100],
    settling_time: List[int] = [5],
    mix_volume: List[int] = [0],
    mix_cycles: List[int] = [0],
    mix_position_from_liquid_surface: List[int] = [250],
    mix_speed: List[int] = [500],
    mix_surface_following_distance: List[int] = [0],
    limit_curve_index: List[int] = [0],
    tadm_algorithm: bool = False,
    recording_mode: int = 0,
  ) -> None:
    self._client.dispense_pip(
      pb2.DispensePipRequest(
        tip_pattern=tip_pattern,
        dispensing_mode=dispensing_mode,
        x_positions=x_positions,
        y_positions=y_positions,
        minimum_height=minimum_height,
        lld_search_height=lld_search_height,
        liquid_surface_no_lld=liquid_surface_no_lld,
        pull_out_distance_transport_air=pull_out_distance_transport_air,
        immersion_depth=immersion_depth,
        immersion_depth_direction=immersion_depth_direction,
        surface_following_distance=surface_following_distance,
        second_section_height=second_section_height,
        second_section_ratio=second_section_ratio,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        min_z_endpos=min_z_endpos,
        dispense_volumes=dispense_volumes,
        dispense_speed=dispense_speed,
        cut_off_speed=cut_off_speed,
        stop_back_volume=stop_back_volume,
        transport_air_volume=transport_air_volume,
        blow_out_air_volume=blow_out_air_volume,
        lld_mode=lld_mode,
        side_touch_off_distance=side_touch_off_distance,
        dispense_position_above_z_touch_off=dispense_position_above_z_touch_off,
        gamma_lld_sensitivity=gamma_lld_sensitivity,
        dp_lld_sensitivity=dp_lld_sensitivity,
        swap_speed=swap_speed,
        settling_time=settling_time,
        mix_volume=mix_volume,
        mix_cycles=mix_cycles,
        mix_position_from_liquid_surface=mix_position_from_liquid_surface,
        mix_speed=mix_speed,
        mix_surface_following_distance=mix_surface_following_distance,
        limit_curve_index=limit_curve_index,
        tadm_algorithm=tadm_algorithm,
        recording_mode=recording_mode,
      )
    )

  async def spread_pip_channels(self) -> None:
    self._client.spread_pip_channels(pb2.SpreadPipChannelsRequest())

  async def move_all_pipetting_channels_to_defined_position(
    self,
    tip_pattern: bool = True,
    x_positions: int = 0,
    y_positions: int = 0,
    minimum_traverse_height_at_beginning_of_command: int = 3600,
    z_endpos: int = 0,
  ) -> None:
    self._client.move_all_pipetting_channels_to_defined_position(
      pb2.MoveAllPipettingChannelsToDefinedPositionRequest(
        tip_pattern=tip_pattern,
        x_positions=x_positions,
        y_positions=y_positions,
        minimum_traverse_height_at_beginning_of_command=minimum_traverse_height_at_beginning_of_command,
        z_endpos=z_endpos,
      )
    )

  async def define_tip_needle(
    self,
    tip_type_table_index: int,
    has_filter: bool,
    tip_length: int,
    maximum_tip_volume: int,
    tip_size: TipSize,
    pickup_method: TipPickupMethod,
  ) -> None:
    self._client.define_tip_needle(
      pb2.DefineTipNeedleRequest(
        tip_type_table_index=tip_type_table_index,
        has_filter=has_filter,
        tip_length=tip_length,
        maximum_tip_volume=maximum_tip_volume,
        tip_size=_TIP_SIZE_TO_PROTO.get(tip_size, pb2.TIP_SIZE_UNDEFINED),
        pickup_method=_PICKUP_METHOD_TO_PROTO.get(pickup_method, pb2.OUT_OF_RACK),
      )
    )

  # =========================================================================
  # TADM / LLD probing
  # =========================================================================

  async def probe_liquid_heights(
    self,
    containers: List,
    use_channels: Optional[List[int]] = None,
    resource_offsets: Optional[List[Coordinate]] = None,
    lld_mode: int = 1,
    search_speed: float = 10.0,
    n_replicates: int = 1,
    move_to_z_safety_after: bool = True,
  ) -> List[float]:
    kwargs: dict = dict(
      container_names=[c.name for c in containers],
      lld_mode=lld_mode,
      search_speed=search_speed,
      n_replicates=n_replicates,
      move_to_z_safety_after=move_to_z_safety_after,
    )
    if use_channels is not None:
      kwargs["use_channels"] = use_channels
    if resource_offsets is not None:
      kwargs["resource_offsets"] = [coordinate_to_proto(o) for o in resource_offsets]
    resp = self._client.probe_liquid_heights(pb2.ProbeLiquidHeightsRequest(**kwargs))
    return list(resp.heights)

  async def probe_liquid_volumes(
    self,
    containers: List,
    use_channels: Optional[List[int]] = None,
    resource_offsets: Optional[List[Coordinate]] = None,
    lld_mode: int = 1,
    search_speed: float = 10.0,
    n_replicates: int = 1,
    move_to_z_safety_after: bool = True,
  ) -> List[float]:
    kwargs: dict = dict(
      container_names=[c.name for c in containers],
      lld_mode=lld_mode,
      search_speed=search_speed,
      n_replicates=n_replicates,
      move_to_z_safety_after=move_to_z_safety_after,
    )
    if use_channels is not None:
      kwargs["use_channels"] = use_channels
    if resource_offsets is not None:
      kwargs["resource_offsets"] = [coordinate_to_proto(o) for o in resource_offsets]
    resp = self._client.probe_liquid_volumes(pb2.ProbeLiquidVolumesRequest(**kwargs))
    return list(resp.volumes)

  async def request_tip_presence(self) -> List[int]:
    resp = self._client.request_tip_presence(pb2.RequestTipPresenceRequest())
    return list(resp.tip_presences)

  async def channels_sense_tip_presence(self) -> List[int]:
    resp = self._client.channels_sense_tip_presence(pb2.ChannelsSenseTipPresenceRequest())
    return list(resp.tip_presences)

  async def request_pip_height_last_lld(self) -> List[float]:
    resp = self._client.request_pip_height_last_lld(pb2.RequestPipHeightLastLldRequest())
    return list(resp.heights)

  async def request_tadm_status(self) -> None:
    self._client.request_tadm_status(pb2.RequestTadmStatusRequest())

  async def request_volume_in_tip(self, channel: int) -> float:
    resp = self._client.request_volume_in_tip(
      pb2.RequestVolumeInTipRequest(channel=channel)
    )
    return resp.volume

  async def request_tip_len_on_channel(self, channel_idx: int) -> float:
    resp = self._client.request_tip_len_on_channel(
      pb2.RequestTipLenOnChannelRequest(channel_idx=channel_idx)
    )
    return resp.length

  async def request_probe_z_position(self, channel_idx: int) -> float:
    resp = self._client.request_probe_z_position(
      pb2.RequestProbeZPositionRequest(channel_idx=channel_idx)
    )
    return resp.z_position

  async def clld_probe_z_height_using_channel(
    self,
    channel_idx: int,
    lowest_reading_position: Optional[int] = None,
    highest_reading_position: Optional[int] = None,
    channel_speed: Optional[int] = None,
    gamma_lld_sensitivity: Optional[int] = None,
  ) -> None:
    kwargs: dict = dict(channel_idx=channel_idx)
    if lowest_reading_position is not None:
      kwargs["lowest_reading_position"] = lowest_reading_position
    if highest_reading_position is not None:
      kwargs["highest_reading_position"] = highest_reading_position
    if channel_speed is not None:
      kwargs["channel_speed"] = channel_speed
    if gamma_lld_sensitivity is not None:
      kwargs["gamma_lld_sensitivity"] = gamma_lld_sensitivity
    self._client.clld_probe_z_height_using_channel(
      pb2.ClldProbeZHeightUsingChannelRequest(**kwargs)
    )

  async def plld_probe_z_height_using_channel(
    self,
    channel_idx: int,
    lowest_reading_position: Optional[int] = None,
    highest_reading_position: Optional[int] = None,
    channel_speed: Optional[int] = None,
    dp_lld_sensitivity: Optional[int] = None,
  ) -> None:
    kwargs: dict = dict(channel_idx=channel_idx)
    if lowest_reading_position is not None:
      kwargs["lowest_reading_position"] = lowest_reading_position
    if highest_reading_position is not None:
      kwargs["highest_reading_position"] = highest_reading_position
    if channel_speed is not None:
      kwargs["channel_speed"] = channel_speed
    if dp_lld_sensitivity is not None:
      kwargs["dp_lld_sensitivity"] = dp_lld_sensitivity
    self._client.plld_probe_z_height_using_channel(
      pb2.PlldProbeZHeightUsingChannelRequest(**kwargs)
    )

  async def ztouch_probe_z_height_using_channel(
    self,
    channel_idx: int,
    lowest_reading_position: Optional[int] = None,
    highest_reading_position: Optional[int] = None,
    channel_speed: Optional[int] = None,
  ) -> None:
    kwargs: dict = dict(channel_idx=channel_idx)
    if lowest_reading_position is not None:
      kwargs["lowest_reading_position"] = lowest_reading_position
    if highest_reading_position is not None:
      kwargs["highest_reading_position"] = highest_reading_position
    if channel_speed is not None:
      kwargs["channel_speed"] = channel_speed
    self._client.ztouch_probe_z_height_using_channel(
      pb2.ZtouchProbeZHeightUsingChannelRequest(**kwargs)
    )

  async def pierce_foil(
    self,
    channel_idx: int,
    x_position: Optional[int] = None,
    y_position: Optional[int] = None,
    z_start_position: Optional[int] = None,
    z_end_position: Optional[int] = None,
    z_speed: Optional[int] = None,
    minimum_traverse_height: Optional[int] = None,
  ) -> None:
    kwargs: dict = dict(channel_idx=channel_idx)
    if x_position is not None:
      kwargs["x_position"] = x_position
    if y_position is not None:
      kwargs["y_position"] = y_position
    if z_start_position is not None:
      kwargs["z_start_position"] = z_start_position
    if z_end_position is not None:
      kwargs["z_end_position"] = z_end_position
    if z_speed is not None:
      kwargs["z_speed"] = z_speed
    if minimum_traverse_height is not None:
      kwargs["minimum_traverse_height"] = minimum_traverse_height
    self._client.pierce_foil(pb2.PierceFoilRequest(**kwargs))

  async def pierce_foil_high_level(
    self,
    well_names: List[str],
    piercing_channels: List[int],
    hold_down_channels: List[int],
    move_inwards: float,
    spread: str = "wide",
    one_by_one: bool = False,
    distance_from_bottom: float = 20.0,
  ) -> None:
    self._client.pierce_foil_high_level(
      pb2.PierceFoilHighLevelRequest(
        well_names=well_names,
        piercing_channels=piercing_channels,
        hold_down_channels=hold_down_channels,
        move_inwards=move_inwards,
        spread=spread,
        one_by_one=one_by_one,
        distance_from_bottom=distance_from_bottom,
      )
    )

  async def step_off_foil(
    self,
    channel_idx: int,
    x_position: Optional[int] = None,
    y_position: Optional[int] = None,
    z_position: Optional[int] = None,
    minimum_traverse_height: Optional[int] = None,
  ) -> None:
    kwargs: dict = dict(channel_idx=channel_idx)
    if x_position is not None:
      kwargs["x_position"] = x_position
    if y_position is not None:
      kwargs["y_position"] = y_position
    if z_position is not None:
      kwargs["z_position"] = z_position
    if minimum_traverse_height is not None:
      kwargs["minimum_traverse_height"] = minimum_traverse_height
    self._client.step_off_foil(pb2.StepOffFoilRequest(**kwargs))

  async def empty_tip(
    self,
    channel_idx: int,
    holding_volume: float,
    acceleration: float,
    flow_rate: float,
    current_limit: int,
  ) -> None:
    self._client.empty_tip(
      pb2.EmptyTipRequest(
        channel_idx=channel_idx,
        holding_volume=holding_volume,
        acceleration=acceleration,
        flow_rate=flow_rate,
        current_limit=current_limit,
      )
    )

  async def empty_tips(
    self,
    channels: List[int],
    holding_volume: float,
    acceleration: float,
    flow_rate: float,
    current_limit: int,
  ) -> None:
    self._client.empty_tips(
      pb2.EmptyTipsRequest(
        channels=channels,
        holding_volume=holding_volume,
        acceleration=acceleration,
        flow_rate=flow_rate,
        current_limit=current_limit,
      )
    )
