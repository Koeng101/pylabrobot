"""Client stubs for 96-head operations."""

from __future__ import annotations

from typing import List

from pylabrobot.resources import Coordinate

from .. import star_service_pb2 as pb2
from ..helpers import coordinate_to_proto, coordinate_from_proto


class Head96ClientMixin:
  """Client stubs for 96-head operations.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # -- initialization --

  async def initialize_core_96_head(
    self, trash96_name: str, z_position_at_the_command_end: float = 245.0,
  ) -> None:
    self._client.initialize_core96_head(
      pb2.InitializeCore96HeadRequest(
        trash96_name=trash96_name,
        z_position_at_the_command_end=z_position_at_the_command_end,
      )
    )

  async def request_core_96_head_initialization_status(self) -> bool:
    resp = self._client.request_core96_head_initialization_status(
      pb2.RequestCore96HeadInitializationStatusRequest()
    )
    return resp.initialized

  async def head96_request_firmware_version(self) -> str:
    resp = self._client.head96_request_firmware_version(
      pb2.Head96RequestFirmwareVersionRequest()
    )
    return resp.date

  async def head96_request_type(self) -> int:
    resp = self._client.head96_request_type(pb2.Head96RequestTypeRequest())
    return resp.head_type

  async def head96_dispensing_drive_and_squeezer_driver_initialize(
    self,
    squeezer_speed: float = 15.0,
    squeezer_acceleration: float = 62.0,
    squeezer_current_limit: int = 15,
    dispensing_drive_current_limit: int = 7,
  ) -> None:
    self._client.head96_dispensing_drive_and_squeezer_driver_initialize(
      pb2.Head96DispensingDriveAndSqueezerDriverInitializeRequest(
        squeezer_speed=squeezer_speed,
        squeezer_acceleration=squeezer_acceleration,
        squeezer_current_limit=squeezer_current_limit,
        dispensing_drive_current_limit=dispensing_drive_current_limit,
      )
    )

  # -- safe position / parking --

  async def move_core_96_to_safe_position(self) -> None:
    self._client.move_core96_to_safe_position(pb2.MoveCore96ToSafePositionRequest())

  async def head96_move_to_z_safety(self) -> None:
    self._client.head96_move_to_z_safety(pb2.Head96MoveToZSafetyRequest())

  async def head96_park(self) -> None:
    self._client.head96_park(pb2.Head96ParkRequest())

  # -- axis moves --

  async def head96_move_x(self, x: float) -> None:
    self._client.head96_move_x(pb2.Head96MoveXRequest(x=x))

  async def head96_move_y(
    self, y: float, move_up_before: bool = False, move_down_after: bool = False,
  ) -> None:
    self._client.head96_move_y(
      pb2.Head96MoveYRequest(
        y=y,
        move_up_before=move_up_before,
        move_down_after=move_down_after,
      )
    )

  async def head96_move_z(self, z: float) -> None:
    self._client.head96_move_z(pb2.Head96MoveZRequest(z=z))

  async def move_core_96_head_to_defined_position(
    self, x: float, y: float, z: float = 342.5,
  ) -> None:
    self._client.move_core96_head_to_defined_position(
      pb2.MoveCore96HeadToDefinedPositionRequest(x=x, y=y, z=z)
    )

  async def head96_move_to_coordinate(self, coordinate: Coordinate) -> None:
    self._client.head96_move_to_coordinate(
      pb2.Head96MoveToCoordinateRequest(coordinate=coordinate_to_proto(coordinate))
    )

  # -- dispensing drive --

  async def head96_dispensing_drive_move_to_home_volume(self) -> None:
    self._client.head96_dispensing_drive_move_to_home_volume(
      pb2.Head96DispensingDriveMoveToHomeVolumeRequest()
    )

  async def head96_dispensing_drive_move_to_position(
    self, position: float, speed: float = 261.1, current_protection_limiter: int = 15,
  ) -> None:
    self._client.head96_dispensing_drive_move_to_position(
      pb2.Head96DispensingDriveMoveToPositionRequest(
        position=position,
        flow_rate=speed,
        current_limit=current_protection_limiter,
      )
    )

  async def head96_dispensing_drive_request_position_mm(self) -> float:
    resp = self._client.head96_dispensing_drive_request_position_mm(
      pb2.Head96DispensingDriveRequestPositionMmRequest()
    )
    return resp.position

  async def head96_dispensing_drive_request_position_uL(self) -> float:
    resp = self._client.head96_dispensing_drive_request_position_ul(
      pb2.Head96DispensingDriveRequestPositionUlRequest()
    )
    return resp.position

  # -- queries --

  async def head96_request_tip_presence(self) -> int:
    resp = self._client.head96_request_tip_presence(
      pb2.Head96RequestTipPresenceRequest()
    )
    return resp.tip_presence

  async def head96_request_position(self) -> Coordinate:
    resp = self._client.head96_request_position(pb2.Head96RequestPositionRequest())
    return coordinate_from_proto(resp.position)

  # -- low-level tip operations --

  async def pick_up_tips_core96(
    self,
    x_position: int,
    x_direction: int,
    y_position: int,
    tip_type_idx: int,
    tip_pickup_method: int = 2,
    z_deposit_position: int = 3425,
    minimum_traverse_height_at_beginning_of_a_command: int = 3425,
    minimum_height_command_end: int = 3425,
  ) -> None:
    self._client.pick_up_tips_core96(
      pb2.PickUpTipsCore96Request(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        tip_type_idx=tip_type_idx,
        tip_pickup_method=tip_pickup_method,
        z_deposit_position=z_deposit_position,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        minimum_height_command_end=minimum_height_command_end,
      )
    )

  async def discard_tips_core96(
    self,
    x_position: int,
    x_direction: int,
    y_position: int,
    z_deposit_position: int = 3425,
    minimum_traverse_height_at_beginning_of_a_command: int = 3425,
    minimum_height_command_end: int = 3425,
  ) -> None:
    self._client.discard_tips_core96(
      pb2.DiscardTipsCore96Request(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        z_deposit_position=z_deposit_position,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        minimum_height_command_end=minimum_height_command_end,
      )
    )

  # -- low-level liquid handling --

  async def aspirate_core_96(
    self,
    aspiration_type: int = 0,
    x_position: int = 0,
    x_direction: int = 0,
    y_positions: int = 0,
    minimum_traverse_height_at_beginning_of_a_command: int = 3425,
    min_z_endpos: int = 3425,
    lld_search_height: int = 3425,
    liquid_surface_no_lld: int = 3425,
    pull_out_distance_transport_air: int = 3425,
    minimum_height: int = 3425,
    second_section_height: int = 0,
    second_section_ratio: int = 3425,
    immersion_depth: int = 0,
    immersion_depth_direction: int = 0,
    surface_following_distance: int = 0,
    aspiration_volumes: int = 0,
    aspiration_speed: int = 1000,
    transport_air_volume: int = 0,
    blow_out_air_volume: int = 200,
    pre_wetting_volume: int = 0,
    lld_mode: int = 1,
    gamma_lld_sensitivity: int = 1,
    swap_speed: int = 100,
    settling_time: int = 5,
    mix_volume: int = 0,
    mix_cycles: int = 0,
    mix_position_from_liquid_surface: int = 250,
    mix_surface_following_distance: int = 0,
    speed_of_mix: int = 1000,
    channel_pattern: List[bool] = [True] * 96,
    limit_curve_index: int = 0,
    tadm_algorithm: bool = False,
    recording_mode: int = 0,
  ) -> None:
    self._client.aspirate_core96(
      pb2.AspirateCore96Request(
        aspiration_type=aspiration_type,
        x_position=x_position,
        x_direction=x_direction,
        y_positions=y_positions,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        min_z_endpos=min_z_endpos,
        lld_search_height=lld_search_height,
        liquid_surface_no_lld=liquid_surface_no_lld,
        pull_out_distance_transport_air=pull_out_distance_transport_air,
        minimum_height=minimum_height,
        second_section_height=second_section_height,
        second_section_ratio=second_section_ratio,
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
        swap_speed=swap_speed,
        settling_time=settling_time,
        mix_volume=mix_volume,
        mix_cycles=mix_cycles,
        mix_position_from_liquid_surface=mix_position_from_liquid_surface,
        mix_surface_following_distance=mix_surface_following_distance,
        speed_of_mix=speed_of_mix,
        channel_pattern=channel_pattern,
        limit_curve_index=limit_curve_index,
        tadm_algorithm=tadm_algorithm,
        recording_mode=recording_mode,
      )
    )

  async def dispense_core_96(
    self,
    dispensing_mode: int = 0,
    x_position: int = 0,
    x_direction: int = 0,
    y_position: int = 0,
    minimum_traverse_height_at_beginning_of_a_command: int = 3425,
    min_z_endpos: int = 3425,
    lld_search_height: int = 3425,
    liquid_surface_no_lld: int = 3425,
    pull_out_distance_transport_air: int = 50,
    minimum_height: int = 3425,
    second_section_height: int = 0,
    second_section_ratio: int = 3425,
    immersion_depth: int = 0,
    immersion_depth_direction: int = 0,
    surface_following_distance: int = 0,
    dispense_volume: int = 0,
    dispense_speed: int = 5000,
    cut_off_speed: int = 250,
    stop_back_volume: int = 0,
    transport_air_volume: int = 0,
    blow_out_air_volume: int = 200,
    lld_mode: int = 1,
    gamma_lld_sensitivity: int = 1,
    swap_speed: int = 100,
    settling_time: int = 5,
    mixing_volume: int = 0,
    mixing_cycles: int = 0,
    mix_position_from_liquid_surface: int = 250,
    mix_surface_following_distance: int = 0,
    speed_of_mixing: int = 1000,
    channel_pattern: List[bool] = [True] * 96,
    limit_curve_index: int = 0,
    tadm_algorithm: bool = False,
    recording_mode: int = 0,
  ) -> None:
    self._client.dispense_core96(
      pb2.DispenseCore96Request(
        dispensing_mode=dispensing_mode,
        x_position=x_position,
        x_direction=x_direction,
        y_positions=y_position,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        min_z_endpos=min_z_endpos,
        lld_search_height=lld_search_height,
        liquid_surface_no_lld=liquid_surface_no_lld,
        pull_out_distance_transport_air=pull_out_distance_transport_air,
        minimum_height=minimum_height,
        second_section_height=second_section_height,
        second_section_ratio=second_section_ratio,
        immersion_depth=immersion_depth,
        immersion_depth_direction=immersion_depth_direction,
        surface_following_distance=surface_following_distance,
        dispense_volumes=dispense_volume,
        dispense_speed=dispense_speed,
        cut_off_speed=cut_off_speed,
        stop_back_volume=stop_back_volume,
        transport_air_volume=transport_air_volume,
        blow_out_air_volume=blow_out_air_volume,
        lld_mode=lld_mode,
        gamma_lld_sensitivity=gamma_lld_sensitivity,
        swap_speed=swap_speed,
        settling_time=settling_time,
        mix_volume=mixing_volume,
        mix_cycles=mixing_cycles,
        mix_position_from_liquid_surface=mix_position_from_liquid_surface,
        mix_surface_following_distance=mix_surface_following_distance,
        speed_of_mix=speed_of_mixing,
        channel_pattern=channel_pattern,
        limit_curve_index=limit_curve_index,
        tadm_algorithm=tadm_algorithm,
        recording_mode=recording_mode,
      )
    )
