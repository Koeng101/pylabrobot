"""RPC handlers for iSWAP operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend

from .. import star_service_pb2 as pb2
from ..helpers import (
    coordinate_from_proto,
    coordinate_to_proto,
    extract_optional_field,
    grip_direction_from_proto,
    resource_drop_from_proto,
    resource_move_from_proto,
    resource_pickup_from_proto,
)

RotationDriveOrientation = STARBackend.RotationDriveOrientation
WristDriveOrientation = STARBackend.WristDriveOrientation

if TYPE_CHECKING:
    from connectrpc.request import RequestContext

# ---------------------------------------------------------------------------
# Enum mappings
# ---------------------------------------------------------------------------

_PROTO_TO_ROT = {
    pb2.ROT_LEFT: RotationDriveOrientation.LEFT,
    pb2.ROT_FRONT: RotationDriveOrientation.FRONT,
    pb2.ROT_RIGHT: RotationDriveOrientation.RIGHT,
}
_ROT_TO_PROTO = {v: k for k, v in _PROTO_TO_ROT.items()}

_PROTO_TO_WRIST = {
    pb2.WRIST_RIGHT: WristDriveOrientation.RIGHT,
    pb2.WRIST_STRAIGHT: WristDriveOrientation.STRAIGHT,
    pb2.WRIST_LEFT: WristDriveOrientation.LEFT,
    pb2.WRIST_REVERSE: WristDriveOrientation.REVERSE,
}
_WRIST_TO_PROTO = {v: k for k, v in _PROTO_TO_WRIST.items()}


class IswapServerMixin:
    """RPC handlers for iSWAP operations.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

    # -----------------------------------------------------------------------
    # Initialization / positioning
    # -----------------------------------------------------------------------

    async def initialize_iswap(
        self, request: pb2.InitializeIswapRequest, ctx: RequestContext
    ) -> pb2.InitializeIswapResponse:
        await self._backend.initialize_iswap()
        return pb2.InitializeIswapResponse()

    async def position_components_for_free_iswap_y_range(
        self,
        request: pb2.PositionComponentsForFreeIswapYRangeRequest,
        ctx: RequestContext,
    ) -> pb2.PositionComponentsForFreeIswapYRangeResponse:
        await self._backend.position_components_for_free_iswap_y_range()
        return pb2.PositionComponentsForFreeIswapYRangeResponse()

    # -----------------------------------------------------------------------
    # Relative moves
    # -----------------------------------------------------------------------

    async def move_iswap_x_relative(
        self, request: pb2.MoveIswapXRelativeRequest, ctx: RequestContext
    ) -> pb2.MoveIswapXRelativeResponse:
        await self._backend.move_iswap_x_relative(
            step_size=request.step_size,
            allow_splitting=request.allow_splitting,
        )
        return pb2.MoveIswapXRelativeResponse()

    async def move_iswap_y_relative(
        self, request: pb2.MoveIswapYRelativeRequest, ctx: RequestContext
    ) -> pb2.MoveIswapYRelativeResponse:
        await self._backend.move_iswap_y_relative(
            step_size=request.step_size,
            allow_splitting=request.allow_splitting,
        )
        return pb2.MoveIswapYRelativeResponse()

    async def move_iswap_z_relative(
        self, request: pb2.MoveIswapZRelativeRequest, ctx: RequestContext
    ) -> pb2.MoveIswapZRelativeResponse:
        await self._backend.move_iswap_z_relative(
            step_size=request.step_size,
            allow_splitting=request.allow_splitting,
        )
        return pb2.MoveIswapZRelativeResponse()

    # -----------------------------------------------------------------------
    # Absolute moves
    # -----------------------------------------------------------------------

    async def move_iswap_x(
        self, request: pb2.MoveIswapXRequest, ctx: RequestContext
    ) -> pb2.MoveIswapXResponse:
        await self._backend.move_iswap_x(x_position=request.x_position)
        return pb2.MoveIswapXResponse()

    async def move_iswap_y(
        self, request: pb2.MoveIswapYRequest, ctx: RequestContext
    ) -> pb2.MoveIswapYResponse:
        await self._backend.move_iswap_y(y_position=request.y_position)
        return pb2.MoveIswapYResponse()

    async def move_iswap_z(
        self, request: pb2.MoveIswapZRequest, ctx: RequestContext
    ) -> pb2.MoveIswapZResponse:
        await self._backend.move_iswap_z(z_position=request.z_position)
        return pb2.MoveIswapZResponse()

    # -----------------------------------------------------------------------
    # Gripper open / close
    # -----------------------------------------------------------------------

    async def open_not_initialized_gripper(
        self,
        request: pb2.OpenNotInitializedGripperRequest,
        ctx: RequestContext,
    ) -> pb2.OpenNotInitializedGripperResponse:
        await self._backend.open_not_initialized_gripper()
        return pb2.OpenNotInitializedGripperResponse()

    async def iswap_open_gripper(
        self, request: pb2.IswapOpenGripperRequest, ctx: RequestContext
    ) -> pb2.IswapOpenGripperResponse:
        await self._backend.iswap_open_gripper(
            open_position=extract_optional_field(request, "open_position"),
        )
        return pb2.IswapOpenGripperResponse()

    async def iswap_close_gripper(
        self, request: pb2.IswapCloseGripperRequest, ctx: RequestContext
    ) -> pb2.IswapCloseGripperResponse:
        await self._backend.iswap_close_gripper(
            grip_strength=request.grip_strength,
            plate_width=request.plate_width,
            plate_width_tolerance=request.plate_width_tolerance,
        )
        return pb2.IswapCloseGripperResponse()

    # -----------------------------------------------------------------------
    # Park
    # -----------------------------------------------------------------------

    async def park_iswap(
        self, request: pb2.ParkIswapRequest, ctx: RequestContext
    ) -> pb2.ParkIswapResponse:
        kwargs = {}
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        await self._backend.park_iswap(**kwargs)
        return pb2.ParkIswapResponse()

    # -----------------------------------------------------------------------
    # Get / Put / Move plate (low-level int params)
    # -----------------------------------------------------------------------

    async def iswap_get_plate(
        self, request: pb2.IswapGetPlateRequest, ctx: RequestContext
    ) -> pb2.IswapGetPlateResponse:
        await self._backend.iswap_get_plate(
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_position=request.y_position,
            y_direction=request.y_direction,
            z_position=request.z_position,
            z_direction=request.z_direction,
            grip_direction=request.grip_direction,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            z_position_at_the_command_end=request.z_position_at_the_command_end,
            grip_strength=request.grip_strength,
            open_gripper_position=request.open_gripper_position,
            plate_width=request.plate_width,
            plate_width_tolerance=request.plate_width_tolerance,
            collision_control_level=request.collision_control_level,
            acceleration_index_high_acc=request.acceleration_index_high_acc,
            acceleration_index_low_acc=request.acceleration_index_low_acc,
            iswap_fold_up_sequence_at_the_end_of_process=request.iswap_fold_up_sequence_at_the_end_of_process,
        )
        return pb2.IswapGetPlateResponse()

    async def iswap_put_plate(
        self, request: pb2.IswapPutPlateRequest, ctx: RequestContext
    ) -> pb2.IswapPutPlateResponse:
        await self._backend.iswap_put_plate(
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_position=request.y_position,
            y_direction=request.y_direction,
            z_position=request.z_position,
            z_direction=request.z_direction,
            grip_direction=request.grip_direction,
            z_position_at_the_command_end=request.z_position_at_the_command_end,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            open_gripper_position=request.open_gripper_position,
            iswap_fold_up_sequence_at_the_end_of_process=request.iswap_fold_up_sequence_at_the_end_of_process,
        )
        return pb2.IswapPutPlateResponse()

    async def move_plate_to_position(
        self, request: pb2.MovePlateToPositionRequest, ctx: RequestContext
    ) -> pb2.MovePlateToPositionResponse:
        await self._backend.move_plate_to_position(
            x_position=request.x_position,
            x_direction=request.x_direction,
            y_position=request.y_position,
            y_direction=request.y_direction,
            z_position=request.z_position,
            z_direction=request.z_direction,
            grip_direction=request.grip_direction,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            collision_control_level=request.collision_control_level,
            acceleration_index_high_acc=request.acceleration_index_high_acc,
            acceleration_index_low_acc=request.acceleration_index_low_acc,
        )
        return pb2.MovePlateToPositionResponse()

    # -----------------------------------------------------------------------
    # Collapse gripper arm
    # -----------------------------------------------------------------------

    async def collapse_gripper_arm(
        self, request: pb2.CollapseGripperArmRequest, ctx: RequestContext
    ) -> pb2.CollapseGripperArmResponse:
        await self._backend.collapse_gripper_arm(
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            iswap_fold_up_sequence_at_the_end_of_process=request.iswap_fold_up_sequence_at_the_end_of_process,
        )
        return pb2.CollapseGripperArmResponse()

    # -----------------------------------------------------------------------
    # Rotation / wrist
    # -----------------------------------------------------------------------

    async def iswap_rotate(
        self, request: pb2.IswapRotateRequest, ctx: RequestContext
    ) -> pb2.IswapRotateResponse:
        await self._backend.rotate_iswap_rotation_drive(
            orientation=_PROTO_TO_ROT[request.orientation],
        )
        return pb2.IswapRotateResponse()

    async def rotate_iswap_rotation_drive(
        self,
        request: pb2.RotateIswapRotationDriveRequest,
        ctx: RequestContext,
    ) -> pb2.RotateIswapRotationDriveResponse:
        await self._backend.rotate_iswap_rotation_drive(
            orientation=_PROTO_TO_ROT[request.orientation],
        )
        return pb2.RotateIswapRotationDriveResponse()

    async def rotate_iswap_wrist(
        self, request: pb2.RotateIswapWristRequest, ctx: RequestContext
    ) -> pb2.RotateIswapWristResponse:
        await self._backend.rotate_iswap_wrist(
            orientation=_PROTO_TO_WRIST[request.orientation],
        )
        return pb2.RotateIswapWristResponse()

    # -----------------------------------------------------------------------
    # Break / Z-axis
    # -----------------------------------------------------------------------

    async def iswap_dangerous_release_break(
        self,
        request: pb2.IswapDangerousReleaseBreakRequest,
        ctx: RequestContext,
    ) -> pb2.IswapDangerousReleaseBreakResponse:
        await self._backend.iswap_dangerous_release_break()
        return pb2.IswapDangerousReleaseBreakResponse()

    async def iswap_reengage_break(
        self, request: pb2.IswapReengageBreakRequest, ctx: RequestContext
    ) -> pb2.IswapReengageBreakResponse:
        await self._backend.iswap_reengage_break()
        return pb2.IswapReengageBreakResponse()

    async def iswap_initialize_z_axis(
        self, request: pb2.IswapInitializeZAxisRequest, ctx: RequestContext
    ) -> pb2.IswapInitializeZAxisResponse:
        await self._backend.iswap_initialize_z_axis()
        return pb2.IswapInitializeZAxisResponse()

    # -----------------------------------------------------------------------
    # Request / query RPCs
    # -----------------------------------------------------------------------

    async def request_iswap_rotation_drive_position_increments(
        self,
        request: pb2.RequestIswapRotationDrivePositionIncrementsRequest,
        ctx: RequestContext,
    ) -> pb2.RequestIswapRotationDrivePositionIncrementsResponse:
        position = await self._backend.request_iswap_rotation_drive_position_increments()
        return pb2.RequestIswapRotationDrivePositionIncrementsResponse(position=position)

    async def request_iswap_rotation_drive_orientation(
        self,
        request: pb2.RequestIswapRotationDriveOrientationRequest,
        ctx: RequestContext,
    ) -> pb2.RequestIswapRotationDriveOrientationResponse:
        orientation = await self._backend.request_iswap_rotation_drive_orientation()
        return pb2.RequestIswapRotationDriveOrientationResponse(
            orientation=_ROT_TO_PROTO[orientation],
        )

    async def request_iswap_wrist_drive_position_increments(
        self,
        request: pb2.RequestIswapWristDrivePositionIncrementsRequest,
        ctx: RequestContext,
    ) -> pb2.RequestIswapWristDrivePositionIncrementsResponse:
        position = await self._backend.request_iswap_wrist_drive_position_increments()
        return pb2.RequestIswapWristDrivePositionIncrementsResponse(position=position)

    async def request_iswap_wrist_drive_orientation(
        self,
        request: pb2.RequestIswapWristDriveOrientationRequest,
        ctx: RequestContext,
    ) -> pb2.RequestIswapWristDriveOrientationResponse:
        orientation = await self._backend.request_iswap_wrist_drive_orientation()
        return pb2.RequestIswapWristDriveOrientationResponse(
            orientation=_WRIST_TO_PROTO[orientation],
        )

    async def request_iswap_in_parking_position(
        self,
        request: pb2.RequestIswapInParkingPositionRequest,
        ctx: RequestContext,
    ) -> pb2.RequestIswapInParkingPositionResponse:
        await self._backend.request_iswap_in_parking_position()
        return pb2.RequestIswapInParkingPositionResponse()

    async def request_plate_in_iswap(
        self, request: pb2.RequestPlateInIswapRequest, ctx: RequestContext
    ) -> pb2.RequestPlateInIswapResponse:
        plate_in_iswap = await self._backend.request_plate_in_iswap()
        return pb2.RequestPlateInIswapResponse(plate_in_iswap=plate_in_iswap)

    async def request_iswap_position(
        self, request: pb2.RequestIswapPositionRequest, ctx: RequestContext
    ) -> pb2.RequestIswapPositionResponse:
        position = await self._backend.request_iswap_position()
        return pb2.RequestIswapPositionResponse(
            position=coordinate_to_proto(position),
        )

    async def iswap_rotation_drive_request_y(
        self,
        request: pb2.IswapRotationDriveRequestYRequest,
        ctx: RequestContext,
    ) -> pb2.IswapRotationDriveRequestYResponse:
        y = await self._backend.iswap_rotation_drive_request_y()
        return pb2.IswapRotationDriveRequestYResponse(y=y)

    async def request_iswap_initialization_status(
        self,
        request: pb2.RequestIswapInitializationStatusRequest,
        ctx: RequestContext,
    ) -> pb2.RequestIswapInitializationStatusResponse:
        initialized = await self._backend.request_iswap_initialization_status()
        return pb2.RequestIswapInitializationStatusResponse(initialized=initialized)

    async def request_iswap_version(
        self, request: pb2.RequestIswapVersionRequest, ctx: RequestContext
    ) -> pb2.RequestIswapVersionResponse:
        version = await self._backend.request_iswap_version()
        return pb2.RequestIswapVersionResponse(version=version)

    async def get_iswap_version(
        self, request: pb2.GetIswapVersionRequest, ctx: RequestContext
    ) -> pb2.GetIswapVersionResponse:
        version = await self._backend.get_iswap_version()
        return pb2.GetIswapVersionResponse(version=version)

    # -----------------------------------------------------------------------
    # Slow iSWAP
    # -----------------------------------------------------------------------

    async def slow_iswap(
        self, request: pb2.SlowIswapRequest, ctx: RequestContext
    ) -> pb2.SlowIswapResponse:
        await self._backend.slow_iswap(
            wrist_velocity=request.wrist_velocity,
            gripper_velocity=request.gripper_velocity,
        )
        return pb2.SlowIswapResponse()

    # -----------------------------------------------------------------------
    # iSWAP move picked-up resource (low-level)
    # -----------------------------------------------------------------------

    async def iswap_move_picked_up_resource(
        self,
        request: pb2.IswapMovePickedUpResourceRequest,
        ctx: RequestContext,
    ) -> pb2.IswapMovePickedUpResourceResponse:
        kwargs = {}
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        await self._backend.iswap_move_picked_up_resource(
            center=coordinate_from_proto(request.center),
            grip_direction=grip_direction_from_proto(request.grip_direction),
            collision_control_level=request.collision_control_level,
            acceleration_index_high_acc=request.acceleration_index_high_acc,
            acceleration_index_low_acc=request.acceleration_index_low_acc,
            **kwargs,
        )
        return pb2.IswapMovePickedUpResourceResponse()

    # -----------------------------------------------------------------------
    # High-level resource handling
    # -----------------------------------------------------------------------

    async def pick_up_resource(
        self, request: pb2.PickUpResourceRequest, ctx: RequestContext
    ) -> pb2.PickUpResourceResponse:
        pickup = resource_pickup_from_proto(self._deck, request.pickup)
        kwargs = {}
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        z_end = extract_optional_field(request, "z_position_at_the_command_end")
        if z_end is not None:
            kwargs["z_position_at_the_command_end"] = z_end
        open_pos = extract_optional_field(request, "open_gripper_position")
        if open_pos is not None:
            kwargs["open_gripper_position"] = open_pos
        plate_w = extract_optional_field(request, "plate_width")
        if plate_w is not None:
            kwargs["plate_width"] = plate_w
        await self._backend.pick_up_resource(
            pickup=pickup,
            use_arm=request.use_arm,
            core_front_channel=request.core_front_channel,
            iswap_grip_strength=request.iswap_grip_strength,
            core_grip_strength=request.core_grip_strength,
            plate_width_tolerance=request.plate_width_tolerance,
            hotel_depth=request.hotel_depth,
            hotel_clearance_height=request.hotel_clearance_height,
            high_speed=request.high_speed,
            use_unsafe_hotel=request.use_unsafe_hotel,
            iswap_collision_control_level=request.iswap_collision_control_level,
            iswap_fold_up_sequence_at_the_end_of_process=request.iswap_fold_up_sequence_at_the_end_of_process,
            **kwargs,
        )
        return pb2.PickUpResourceResponse()

    async def move_picked_up_resource(
        self, request: pb2.MovePickedUpResourceRequest, ctx: RequestContext
    ) -> pb2.MovePickedUpResourceResponse:
        move = resource_move_from_proto(self._deck, request.move)
        await self._backend.move_picked_up_resource(
            move=move,
            use_arm=request.use_arm,
        )
        return pb2.MovePickedUpResourceResponse()

    async def drop_resource(
        self, request: pb2.DropResourceRequest, ctx: RequestContext
    ) -> pb2.DropResourceResponse:
        drop = resource_drop_from_proto(self._deck, request.drop)
        kwargs = {}
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        z_end = extract_optional_field(request, "z_position_at_the_command_end")
        if z_end is not None:
            kwargs["z_position_at_the_command_end"] = z_end
        open_pos = extract_optional_field(request, "open_gripper_position")
        if open_pos is not None:
            kwargs["open_gripper_position"] = open_pos
        await self._backend.drop_resource(
            drop=drop,
            use_arm=request.use_arm,
            return_core_gripper=request.return_core_gripper,
            hotel_depth=request.hotel_depth,
            hotel_clearance_height=request.hotel_clearance_height,
            hotel_high_speed=request.hotel_high_speed,
            use_unsafe_hotel=request.use_unsafe_hotel,
            iswap_collision_control_level=request.iswap_collision_control_level,
            iswap_fold_up_sequence_at_the_end_of_process=request.iswap_fold_up_sequence_at_the_end_of_process,
            **kwargs,
        )
        return pb2.DropResourceResponse()
