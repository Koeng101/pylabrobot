"""RPC handlers for 96-head operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import star_service_pb2 as pb2
from ..helpers import coordinate_to_proto, coordinate_from_proto

if TYPE_CHECKING:
    from connectrpc.request import RequestContext

    from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend


class Head96ServerMixin:
    _backend: STARBackend
    """RPC handlers for 96-head operations.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

    # -- initialization --

    async def initialize_core_96_head(
        self, request: pb2.InitializeCore96HeadRequest, ctx: RequestContext
    ) -> pb2.InitializeCore96HeadResponse:
        trash = self._backend.deck.get_resource(request.trash96_name)
        await self._backend.initialize_core_96_head(
            trash96=trash,  # type: ignore[arg-type]
            z_position_at_the_command_end=request.z_position_at_the_command_end,
        )
        return pb2.InitializeCore96HeadResponse()

    async def request_core_96_head_initialization_status(
        self,
        request: pb2.RequestCore96HeadInitializationStatusRequest,
        ctx: RequestContext,
    ) -> pb2.RequestCore96HeadInitializationStatusResponse:
        result = await self._backend.request_core_96_head_initialization_status()
        return pb2.RequestCore96HeadInitializationStatusResponse(initialized=result)

    async def head96_request_firmware_version(
        self,
        request: pb2.Head96RequestFirmwareVersionRequest,
        ctx: RequestContext,
    ) -> pb2.Head96RequestFirmwareVersionResponse:
        result = await self._backend.head96_request_firmware_version()
        return pb2.Head96RequestFirmwareVersionResponse(date=str(result))

    async def head96_request_type(
        self,
        request: pb2.Head96RequestTypeRequest,
        ctx: RequestContext,
    ) -> pb2.Head96RequestTypeResponse:
        result = await self._backend.head96_request_type()
        return pb2.Head96RequestTypeResponse(head_type=result.value)  # type: ignore[union-attr]

    async def head96_dispensing_drive_and_squeezer_driver_initialize(
        self,
        request: pb2.Head96DispensingDriveAndSqueezerDriverInitializeRequest,
        ctx: RequestContext,
    ) -> pb2.Head96DispensingDriveAndSqueezerDriverInitializeResponse:
        await self._backend.head96_dispensing_drive_and_squeezer_driver_initialize(
            squeezer_speed=request.squeezer_speed,
            squeezer_acceleration=request.squeezer_acceleration,
            squeezer_current_limit=request.squeezer_current_limit,
            dispensing_drive_current_limit=request.dispensing_drive_current_limit,
        )
        return pb2.Head96DispensingDriveAndSqueezerDriverInitializeResponse()

    # -- safe position / parking --

    async def move_core_96_to_safe_position(
        self,
        request: pb2.MoveCore96ToSafePositionRequest,
        ctx: RequestContext,
    ) -> pb2.MoveCore96ToSafePositionResponse:
        await self._backend.move_core_96_to_safe_position()
        return pb2.MoveCore96ToSafePositionResponse()

    async def head96_move_to_z_safety(
        self,
        request: pb2.Head96MoveToZSafetyRequest,
        ctx: RequestContext,
    ) -> pb2.Head96MoveToZSafetyResponse:
        await self._backend.head96_move_to_z_safety()
        return pb2.Head96MoveToZSafetyResponse()

    async def head96_park(
        self,
        request: pb2.Head96ParkRequest,
        ctx: RequestContext,
    ) -> pb2.Head96ParkResponse:
        await self._backend.head96_park()
        return pb2.Head96ParkResponse()

    # -- axis moves --

    async def head96_move_x(
        self, request: pb2.Head96MoveXRequest, ctx: RequestContext
    ) -> pb2.Head96MoveXResponse:
        await self._backend.head96_move_x(x=request.x)
        return pb2.Head96MoveXResponse()

    async def head96_move_y(
        self, request: pb2.Head96MoveYRequest, ctx: RequestContext
    ) -> pb2.Head96MoveYResponse:
        await self._backend.head96_move_y(
            y=request.y,
            move_up_before=request.move_up_before,  # type: ignore[call-arg]
            move_down_after=request.move_down_after,
        )
        return pb2.Head96MoveYResponse()

    async def head96_move_z(
        self, request: pb2.Head96MoveZRequest, ctx: RequestContext
    ) -> pb2.Head96MoveZResponse:
        await self._backend.head96_move_z(z=request.z)
        return pb2.Head96MoveZResponse()

    async def move_core_96_head_to_defined_position(
        self,
        request: pb2.MoveCore96HeadToDefinedPositionRequest,
        ctx: RequestContext,
    ) -> pb2.MoveCore96HeadToDefinedPositionResponse:
        await self._backend.move_core_96_head_to_defined_position(
            x=request.x,
            y=request.y,
            z=request.z,
        )
        return pb2.MoveCore96HeadToDefinedPositionResponse()

    async def head96_move_to_coordinate(
        self,
        request: pb2.Head96MoveToCoordinateRequest,
        ctx: RequestContext,
    ) -> pb2.Head96MoveToCoordinateResponse:
        coordinate = coordinate_from_proto(request.coordinate)
        await self._backend.head96_move_to_coordinate(coordinate=coordinate)
        return pb2.Head96MoveToCoordinateResponse()

    # -- dispensing drive --

    async def head96_dispensing_drive_move_to_home_volume(
        self,
        request: pb2.Head96DispensingDriveMoveToHomeVolumeRequest,
        ctx: RequestContext,
    ) -> pb2.Head96DispensingDriveMoveToHomeVolumeResponse:
        await self._backend.head96_dispensing_drive_move_to_home_volume()
        return pb2.Head96DispensingDriveMoveToHomeVolumeResponse()

    async def head96_dispensing_drive_move_to_position(
        self,
        request: pb2.Head96DispensingDriveMoveToPositionRequest,
        ctx: RequestContext,
    ) -> pb2.Head96DispensingDriveMoveToPositionResponse:
        await self._backend.head96_dispensing_drive_move_to_position(
            position=request.position,
            speed=request.flow_rate,
            current_protection_limiter=request.current_limit,
        )
        return pb2.Head96DispensingDriveMoveToPositionResponse()

    async def head96_dispensing_drive_request_position_mm(
        self,
        request: pb2.Head96DispensingDriveRequestPositionMmRequest,
        ctx: RequestContext,
    ) -> pb2.Head96DispensingDriveRequestPositionMmResponse:
        result = await self._backend.head96_dispensing_drive_request_position_mm()
        return pb2.Head96DispensingDriveRequestPositionMmResponse(position=result)

    async def head96_dispensing_drive_request_position_ul(
        self,
        request: pb2.Head96DispensingDriveRequestPositionUlRequest,
        ctx: RequestContext,
    ) -> pb2.Head96DispensingDriveRequestPositionUlResponse:
        result = await self._backend.head96_dispensing_drive_request_position_uL()
        return pb2.Head96DispensingDriveRequestPositionUlResponse(position=result)

    # -- queries --

    async def head96_request_tip_presence(
        self,
        request: pb2.Head96RequestTipPresenceRequest,
        ctx: RequestContext,
    ) -> pb2.Head96RequestTipPresenceResponse:
        result = await self._backend.head96_request_tip_presence()
        return pb2.Head96RequestTipPresenceResponse(tip_presence=result)

    async def head96_request_position(
        self,
        request: pb2.Head96RequestPositionRequest,
        ctx: RequestContext,
    ) -> pb2.Head96RequestPositionResponse:
        result = await self._backend.head96_request_position()
        return pb2.Head96RequestPositionResponse(position=coordinate_to_proto(result))

    # -- low-level tip operations --

    async def pick_up_tips_core96(
        self,
        request: pb2.PickUpTipsCore96Request,
        ctx: RequestContext,
    ) -> pb2.PickUpTipsCore96Response:
        await self._backend.pick_up_tips_core96(
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_position=request.y_position,
            tip_type_idx=request.tip_type_idx,
            tip_pickup_method=request.tip_pickup_method,
            z_deposit_position=request.z_deposit_position,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            minimum_height_command_end=request.minimum_height_command_end,
        )
        return pb2.PickUpTipsCore96Response()

    async def discard_tips_core96(
        self,
        request: pb2.DiscardTipsCore96Request,
        ctx: RequestContext,
    ) -> pb2.DiscardTipsCore96Response:
        await self._backend.discard_tips_core96(
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_position=request.y_position,
            z_deposit_position=request.z_deposit_position,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            minimum_height_command_end=request.minimum_height_command_end,
        )
        return pb2.DiscardTipsCore96Response()

    # -- low-level liquid handling --

    async def aspirate_core96(
        self,
        request: pb2.AspirateCore96Request,
        ctx: RequestContext,
    ) -> pb2.AspirateCore96Response:
        await self._backend.aspirate_core_96(
            aspiration_type=request.aspiration_type,
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_positions=request.y_positions,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            min_z_endpos=request.min_z_endpos,
            lld_search_height=request.lld_search_height,
            liquid_surface_no_lld=request.liquid_surface_no_lld,
            pull_out_distance_transport_air=request.pull_out_distance_transport_air,
            minimum_height=request.minimum_height,
            second_section_height=request.second_section_height,
            second_section_ratio=request.second_section_ratio,
            immersion_depth=request.immersion_depth,
            immersion_depth_direction=request.immersion_depth_direction,
            surface_following_distance=request.surface_following_distance,
            aspiration_volumes=request.aspiration_volumes,
            aspiration_speed=request.aspiration_speed,
            transport_air_volume=request.transport_air_volume,
            blow_out_air_volume=request.blow_out_air_volume,
            pre_wetting_volume=request.pre_wetting_volume,
            lld_mode=request.lld_mode,
            gamma_lld_sensitivity=request.gamma_lld_sensitivity,
            swap_speed=request.swap_speed,
            settling_time=request.settling_time,
            mix_volume=request.mix_volume,
            mix_cycles=request.mix_cycles,
            mix_position_from_liquid_surface=request.mix_position_from_liquid_surface,
            mix_surface_following_distance=request.mix_surface_following_distance,
            speed_of_mix=request.speed_of_mix,
            channel_pattern=list(request.channel_pattern),
            limit_curve_index=request.limit_curve_index,
            tadm_algorithm=request.tadm_algorithm,
            recording_mode=request.recording_mode,
        )
        return pb2.AspirateCore96Response()

    async def dispense_core96(
        self,
        request: pb2.DispenseCore96Request,
        ctx: RequestContext,
    ) -> pb2.DispenseCore96Response:
        await self._backend.dispense_core_96(
            dispensing_mode=request.dispensing_mode,
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_position=request.y_positions,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            min_z_endpos=request.min_z_endpos,
            lld_search_height=request.lld_search_height,
            liquid_surface_no_lld=request.liquid_surface_no_lld,
            pull_out_distance_transport_air=request.pull_out_distance_transport_air,
            minimum_height=request.minimum_height,
            second_section_height=request.second_section_height,
            second_section_ratio=request.second_section_ratio,
            immersion_depth=request.immersion_depth,
            immersion_depth_direction=request.immersion_depth_direction,
            surface_following_distance=request.surface_following_distance,
            dispense_volume=request.dispense_volumes,
            dispense_speed=request.dispense_speed,
            cut_off_speed=request.cut_off_speed,
            stop_back_volume=request.stop_back_volume,
            transport_air_volume=request.transport_air_volume,
            blow_out_air_volume=request.blow_out_air_volume,
            lld_mode=request.lld_mode,
            gamma_lld_sensitivity=request.gamma_lld_sensitivity,
            swap_speed=request.swap_speed,
            settling_time=request.settling_time,
            mixing_volume=request.mix_volume,
            mixing_cycles=request.mix_cycles,
            mix_position_from_liquid_surface=request.mix_position_from_liquid_surface,
            mix_surface_following_distance=request.mix_surface_following_distance,
            speed_of_mixing=request.speed_of_mix,
            channel_pattern=list(request.channel_pattern),
            limit_curve_index=request.limit_curve_index,
            tadm_algorithm=request.tadm_algorithm,
            recording_mode=request.recording_mode,
        )
        return pb2.DispenseCore96Response()
