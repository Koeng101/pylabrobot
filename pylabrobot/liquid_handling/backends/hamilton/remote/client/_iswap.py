"""Client stubs for iSWAP operations."""

from __future__ import annotations

from typing import Optional

from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend
from pylabrobot.liquid_handling.standard import GripDirection, ResourceDrop, ResourceMove, ResourcePickup
from pylabrobot.resources import Coordinate

from .. import star_service_pb2 as pb2
from ..helpers import (
    coordinate_from_proto,
    coordinate_to_proto,
    grip_direction_to_proto,
    resource_drop_to_proto,
    resource_move_to_proto,
    resource_pickup_to_proto,
)

RotationDriveOrientation = STARBackend.RotationDriveOrientation
WristDriveOrientation = STARBackend.WristDriveOrientation

# ---------------------------------------------------------------------------
# Enum mappings
# ---------------------------------------------------------------------------

_ROT_TO_PROTO = {
    RotationDriveOrientation.LEFT: pb2.ROT_LEFT,
    RotationDriveOrientation.FRONT: pb2.ROT_FRONT,
    RotationDriveOrientation.RIGHT: pb2.ROT_RIGHT,
}
_PROTO_TO_ROT = {v: k for k, v in _ROT_TO_PROTO.items()}

_WRIST_TO_PROTO = {
    WristDriveOrientation.RIGHT: pb2.WRIST_RIGHT,
    WristDriveOrientation.STRAIGHT: pb2.WRIST_STRAIGHT,
    WristDriveOrientation.LEFT: pb2.WRIST_LEFT,
    WristDriveOrientation.REVERSE: pb2.WRIST_REVERSE,
}
_PROTO_TO_WRIST = {v: k for k, v in _WRIST_TO_PROTO.items()}


class IswapClientMixin:
  """Client stubs for iSWAP operations.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # -----------------------------------------------------------------------
  # Initialization / positioning
  # -----------------------------------------------------------------------

  async def initialize_iswap(self) -> None:
    self._client.initialize_iswap(pb2.InitializeIswapRequest())

  async def position_components_for_free_iswap_y_range(self) -> None:
    self._client.position_components_for_free_iswap_y_range(
      pb2.PositionComponentsForFreeIswapYRangeRequest()
    )

  # -----------------------------------------------------------------------
  # Relative moves
  # -----------------------------------------------------------------------

  async def move_iswap_x_relative(
    self, step_size: float, allow_splitting: bool = False,
  ) -> None:
    self._client.move_iswap_x_relative(
      pb2.MoveIswapXRelativeRequest(step_size=step_size, allow_splitting=allow_splitting)
    )

  async def move_iswap_y_relative(
    self, step_size: float, allow_splitting: bool = False,
  ) -> None:
    self._client.move_iswap_y_relative(
      pb2.MoveIswapYRelativeRequest(step_size=step_size, allow_splitting=allow_splitting)
    )

  async def move_iswap_z_relative(
    self, step_size: float, allow_splitting: bool = False,
  ) -> None:
    self._client.move_iswap_z_relative(
      pb2.MoveIswapZRelativeRequest(step_size=step_size, allow_splitting=allow_splitting)
    )

  # -----------------------------------------------------------------------
  # Absolute moves
  # -----------------------------------------------------------------------

  async def move_iswap_x(self, x_position: float) -> None:
    self._client.move_iswap_x(pb2.MoveIswapXRequest(x_position=x_position))

  async def move_iswap_y(self, y_position: float) -> None:
    self._client.move_iswap_y(pb2.MoveIswapYRequest(y_position=y_position))

  async def move_iswap_z(self, z_position: float) -> None:
    self._client.move_iswap_z(pb2.MoveIswapZRequest(z_position=z_position))

  # -----------------------------------------------------------------------
  # Gripper open / close
  # -----------------------------------------------------------------------

  async def open_not_initialized_gripper(self) -> None:
    self._client.open_not_initialized_gripper(pb2.OpenNotInitializedGripperRequest())

  async def iswap_open_gripper(self, open_position: Optional[float] = None) -> None:
    kwargs = {}
    if open_position is not None:
      kwargs["open_position"] = open_position
    self._client.iswap_open_gripper(pb2.IswapOpenGripperRequest(**kwargs))

  async def iswap_close_gripper(
    self,
    grip_strength: int = 5,
    plate_width: float = 0,
    plate_width_tolerance: float = 0,
  ) -> None:
    self._client.iswap_close_gripper(
      pb2.IswapCloseGripperRequest(
        grip_strength=grip_strength,
        plate_width=plate_width,
        plate_width_tolerance=plate_width_tolerance,
      )
    )

  # -----------------------------------------------------------------------
  # Park
  # -----------------------------------------------------------------------

  async def park_iswap(
    self,
    minimum_traverse_height_at_beginning_of_a_command: int = 2840,
  ) -> None:
    kwargs = {}
    kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
      minimum_traverse_height_at_beginning_of_a_command
    )
    self._client.park_iswap(pb2.ParkIswapRequest(**kwargs))

  # -----------------------------------------------------------------------
  # Get / Put / Move plate (low-level int params)
  # -----------------------------------------------------------------------

  async def iswap_get_plate(
    self,
    x_position: int = 0,
    x_direction: int = 0,
    y_position: int = 0,
    y_direction: int = 0,
    z_position: int = 0,
    z_direction: int = 0,
    grip_direction: int = 1,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    z_position_at_the_command_end: int = 3600,
    grip_strength: int = 5,
    open_gripper_position: int = 860,
    plate_width: int = 860,
    plate_width_tolerance: int = 860,
    collision_control_level: int = 1,
    acceleration_index_high_acc: int = 4,
    acceleration_index_low_acc: int = 1,
    iswap_fold_up_sequence_at_the_end_of_process: bool = False,
  ) -> None:
    self._client.iswap_get_plate(
      pb2.IswapGetPlateRequest(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        y_direction=y_direction,
        z_position=z_position,
        z_direction=z_direction,
        grip_direction=grip_direction,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        z_position_at_the_command_end=z_position_at_the_command_end,
        grip_strength=grip_strength,
        open_gripper_position=open_gripper_position,
        plate_width=plate_width,
        plate_width_tolerance=plate_width_tolerance,
        collision_control_level=collision_control_level,
        acceleration_index_high_acc=acceleration_index_high_acc,
        acceleration_index_low_acc=acceleration_index_low_acc,
        iswap_fold_up_sequence_at_the_end_of_process=iswap_fold_up_sequence_at_the_end_of_process,
      )
    )

  async def iswap_put_plate(
    self,
    x_position: int = 0,
    x_direction: int = 0,
    y_position: int = 0,
    y_direction: int = 0,
    z_position: int = 0,
    z_direction: int = 0,
    grip_direction: int = 1,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    z_position_at_the_command_end: int = 3600,
    open_gripper_position: int = 860,
    collision_control_level: int = 1,
    acceleration_index_high_acc: int = 4,
    acceleration_index_low_acc: int = 1,
    iswap_fold_up_sequence_at_the_end_of_process: bool = False,
  ) -> None:
    self._client.iswap_put_plate(
      pb2.IswapPutPlateRequest(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        y_direction=y_direction,
        z_position=z_position,
        z_direction=z_direction,
        grip_direction=grip_direction,
        z_position_at_the_command_end=z_position_at_the_command_end,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        open_gripper_position=open_gripper_position,
        iswap_fold_up_sequence_at_the_end_of_process=iswap_fold_up_sequence_at_the_end_of_process,
      )
    )

  async def move_plate_to_position(
    self,
    x_position: int = 0,
    x_direction: int = 0,
    y_position: int = 0,
    y_direction: int = 0,
    z_position: int = 0,
    z_direction: int = 0,
    grip_direction: int = 1,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    collision_control_level: int = 1,
    acceleration_index_high_acc: int = 4,
    acceleration_index_low_acc: int = 1,
  ) -> None:
    self._client.move_plate_to_position(
      pb2.MovePlateToPositionRequest(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        y_direction=y_direction,
        z_position=z_position,
        z_direction=z_direction,
        grip_direction=grip_direction,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        collision_control_level=collision_control_level,
        acceleration_index_high_acc=acceleration_index_high_acc,
        acceleration_index_low_acc=acceleration_index_low_acc,
      )
    )

  # -----------------------------------------------------------------------
  # Collapse gripper arm
  # -----------------------------------------------------------------------

  async def collapse_gripper_arm(
    self,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
    iswap_fold_up_sequence_at_the_end_of_process: bool = False,
  ) -> None:
    self._client.collapse_gripper_arm(
      pb2.CollapseGripperArmRequest(
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        iswap_fold_up_sequence_at_the_end_of_process=iswap_fold_up_sequence_at_the_end_of_process,
      )
    )

  # -----------------------------------------------------------------------
  # Rotation / wrist
  # -----------------------------------------------------------------------

  async def iswap_rotate(
    self,
    orientation: RotationDriveOrientation,
  ) -> None:
    self._client.iswap_rotate(
      pb2.IswapRotateRequest(orientation=_ROT_TO_PROTO[orientation])
    )

  async def rotate_iswap_rotation_drive(
    self,
    orientation: RotationDriveOrientation,
  ) -> None:
    self._client.rotate_iswap_rotation_drive(
      pb2.RotateIswapRotationDriveRequest(orientation=_ROT_TO_PROTO[orientation])
    )

  async def rotate_iswap_wrist(
    self,
    orientation: WristDriveOrientation,
  ) -> None:
    self._client.rotate_iswap_wrist(
      pb2.RotateIswapWristRequest(orientation=_WRIST_TO_PROTO[orientation])
    )

  # -----------------------------------------------------------------------
  # Break / Z-axis
  # -----------------------------------------------------------------------

  async def iswap_dangerous_release_break(self) -> None:
    self._client.iswap_dangerous_release_break(pb2.IswapDangerousReleaseBreakRequest())

  async def iswap_reengage_break(self) -> None:
    self._client.iswap_reengage_break(pb2.IswapReengageBreakRequest())

  async def iswap_initialize_z_axis(self) -> None:
    self._client.iswap_initialize_z_axis(pb2.IswapInitializeZAxisRequest())

  # -----------------------------------------------------------------------
  # Request / query RPCs
  # -----------------------------------------------------------------------

  async def request_iswap_rotation_drive_position_increments(self) -> int:
    resp = self._client.request_iswap_rotation_drive_position_increments(
      pb2.RequestIswapRotationDrivePositionIncrementsRequest()
    )
    return resp.position

  async def request_iswap_rotation_drive_orientation(self) -> RotationDriveOrientation:
    resp = self._client.request_iswap_rotation_drive_orientation(
      pb2.RequestIswapRotationDriveOrientationRequest()
    )
    return _PROTO_TO_ROT[resp.orientation]

  async def request_iswap_wrist_drive_position_increments(self) -> int:
    resp = self._client.request_iswap_wrist_drive_position_increments(
      pb2.RequestIswapWristDrivePositionIncrementsRequest()
    )
    return resp.position

  async def request_iswap_wrist_drive_orientation(self) -> WristDriveOrientation:
    resp = self._client.request_iswap_wrist_drive_orientation(
      pb2.RequestIswapWristDriveOrientationRequest()
    )
    return _PROTO_TO_WRIST[resp.orientation]

  async def request_iswap_in_parking_position(self) -> None:
    self._client.request_iswap_in_parking_position(
      pb2.RequestIswapInParkingPositionRequest()
    )

  async def request_plate_in_iswap(self) -> bool:
    resp = self._client.request_plate_in_iswap(pb2.RequestPlateInIswapRequest())
    return resp.plate_in_iswap

  async def request_iswap_position(self) -> Coordinate:
    resp = self._client.request_iswap_position(pb2.RequestIswapPositionRequest())
    return coordinate_from_proto(resp.position)

  async def iswap_rotation_drive_request_y(self) -> float:
    resp = self._client.iswap_rotation_drive_request_y(
      pb2.IswapRotationDriveRequestYRequest()
    )
    return resp.y

  async def request_iswap_initialization_status(self) -> bool:
    resp = self._client.request_iswap_initialization_status(
      pb2.RequestIswapInitializationStatusRequest()
    )
    return resp.initialized

  async def request_iswap_version(self) -> str:
    resp = self._client.request_iswap_version(pb2.RequestIswapVersionRequest())
    return resp.version

  async def get_iswap_version(self) -> str:
    resp = self._client.get_iswap_version(pb2.GetIswapVersionRequest())
    return resp.version

  # -----------------------------------------------------------------------
  # Slow iSWAP
  # -----------------------------------------------------------------------

  async def slow_iswap(
    self,
    wrist_velocity: int = 20_000,
    gripper_velocity: int = 20_000,
  ) -> None:
    self._client.slow_iswap(
      pb2.SlowIswapRequest(
        wrist_velocity=wrist_velocity,
        gripper_velocity=gripper_velocity,
      )
    )

  # -----------------------------------------------------------------------
  # iSWAP move picked-up resource (low-level)
  # -----------------------------------------------------------------------

  async def iswap_move_picked_up_resource(
    self,
    center: Coordinate,
    grip_direction: GripDirection,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    collision_control_level: int = 1,
    acceleration_index_high_acc: int = 4,
    acceleration_index_low_acc: int = 1,
  ) -> None:
    kwargs = {}
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    self._client.iswap_move_picked_up_resource(
      pb2.IswapMovePickedUpResourceRequest(
        center=coordinate_to_proto(center),
        grip_direction=grip_direction_to_proto(grip_direction),
        collision_control_level=collision_control_level,
        acceleration_index_high_acc=acceleration_index_high_acc,
        acceleration_index_low_acc=acceleration_index_low_acc,
        **kwargs,
      )
    )

  # -----------------------------------------------------------------------
  # High-level resource handling
  # -----------------------------------------------------------------------

  async def pick_up_resource(
    self,
    pickup: ResourcePickup,
    use_arm: str = "iswap",
    core_front_channel: int = 7,
    iswap_grip_strength: int = 4,
    core_grip_strength: int = 15,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    z_position_at_the_command_end: Optional[float] = None,
    plate_width_tolerance: float = 2.0,
    open_gripper_position: Optional[float] = None,
    hotel_depth: float = 160.0,
    hotel_clearance_height: float = 7.5,
    high_speed: bool = False,
    plate_width: Optional[float] = None,
    use_unsafe_hotel: bool = False,
    iswap_collision_control_level: int = 0,
    iswap_fold_up_sequence_at_the_end_of_process: bool = False,
  ) -> None:
    kwargs = {}
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if z_position_at_the_command_end is not None:
      kwargs["z_position_at_the_command_end"] = z_position_at_the_command_end
    if open_gripper_position is not None:
      kwargs["open_gripper_position"] = open_gripper_position
    if plate_width is not None:
      kwargs["plate_width"] = plate_width
    self._client.pick_up_resource(
      pb2.PickUpResourceRequest(
        pickup=resource_pickup_to_proto(pickup),
        use_arm=use_arm,
        core_front_channel=core_front_channel,
        iswap_grip_strength=iswap_grip_strength,
        core_grip_strength=core_grip_strength,
        plate_width_tolerance=plate_width_tolerance,
        hotel_depth=hotel_depth,
        hotel_clearance_height=hotel_clearance_height,
        high_speed=high_speed,
        use_unsafe_hotel=use_unsafe_hotel,
        iswap_collision_control_level=iswap_collision_control_level,
        iswap_fold_up_sequence_at_the_end_of_process=iswap_fold_up_sequence_at_the_end_of_process,
        **kwargs,
      )
    )

  async def move_picked_up_resource(
    self,
    move: ResourceMove,
    use_arm: str = "iswap",
  ) -> None:
    self._client.move_picked_up_resource(
      pb2.MovePickedUpResourceRequest(
        move=resource_move_to_proto(move),
        use_arm=use_arm,
      )
    )

  async def drop_resource(
    self,
    drop: ResourceDrop,
    use_arm: str = "iswap",
    return_core_gripper: bool = True,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    z_position_at_the_command_end: Optional[float] = None,
    open_gripper_position: Optional[float] = None,
    hotel_depth: float = 160.0,
    hotel_clearance_height: float = 7.5,
    hotel_high_speed: bool = False,
    use_unsafe_hotel: bool = False,
    iswap_collision_control_level: int = 0,
    iswap_fold_up_sequence_at_the_end_of_process: bool = False,
  ) -> None:
    kwargs = {}
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if z_position_at_the_command_end is not None:
      kwargs["z_position_at_the_command_end"] = z_position_at_the_command_end
    if open_gripper_position is not None:
      kwargs["open_gripper_position"] = open_gripper_position
    self._client.drop_resource(
      pb2.DropResourceRequest(
        drop=resource_drop_to_proto(drop),
        use_arm=use_arm,
        return_core_gripper=return_core_gripper,
        hotel_depth=hotel_depth,
        hotel_clearance_height=hotel_clearance_height,
        hotel_high_speed=hotel_high_speed,
        use_unsafe_hotel=use_unsafe_hotel,
        iswap_collision_control_level=iswap_collision_control_level,
        iswap_fold_up_sequence_at_the_end_of_process=iswap_fold_up_sequence_at_the_end_of_process,
        **kwargs,
      )
    )
