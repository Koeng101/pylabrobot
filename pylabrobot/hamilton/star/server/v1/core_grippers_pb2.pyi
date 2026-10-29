from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CoreGrippersConfiguration(_message.Message):
    __slots__ = ("grip_strength_range",)
    GRIP_STRENGTH_RANGE_FIELD_NUMBER: _ClassVar[int]
    grip_strength_range: _types_pb2.Int32Range
    def __init__(self, grip_strength_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ...) -> None: ...

class CoreGrippersGetToolsMountedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersGetToolsMountedResponse(_message.Message):
    __slots__ = ("tools_mounted",)
    TOOLS_MOUNTED_FIELD_NUMBER: _ClassVar[int]
    tools_mounted: bool
    def __init__(self, tools_mounted: _Optional[bool] = ...) -> None: ...

class CoreGrippersRequestToolAttachedRequest(_message.Message):
    __slots__ = ("channel",)
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: int
    def __init__(self, channel: _Optional[int] = ...) -> None: ...

class CoreGrippersRequestToolAttachedResponse(_message.Message):
    __slots__ = ("attached",)
    ATTACHED_FIELD_NUMBER: _ClassVar[int]
    attached: bool
    def __init__(self, attached: _Optional[bool] = ...) -> None: ...

class CoreGrippersPickUpToolsAtLocationRequest(_message.Message):
    __slots__ = ("tool_position_x", "tool_position_z", "front_channel_position_y", "rear_channel_position_y", "tool_seek", "minimum_traverse_height_start", "front_channel")
    TOOL_POSITION_X_FIELD_NUMBER: _ClassVar[int]
    TOOL_POSITION_Z_FIELD_NUMBER: _ClassVar[int]
    FRONT_CHANNEL_POSITION_Y_FIELD_NUMBER: _ClassVar[int]
    REAR_CHANNEL_POSITION_Y_FIELD_NUMBER: _ClassVar[int]
    TOOL_SEEK_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    FRONT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    tool_position_x: float
    tool_position_z: float
    front_channel_position_y: float
    rear_channel_position_y: float
    tool_seek: float
    minimum_traverse_height_start: float
    front_channel: int
    def __init__(self, tool_position_x: _Optional[float] = ..., tool_position_z: _Optional[float] = ..., front_channel_position_y: _Optional[float] = ..., rear_channel_position_y: _Optional[float] = ..., tool_seek: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., front_channel: _Optional[int] = ...) -> None: ...

class CoreGrippersPickUpToolsAtLocationResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersDropToolsRequest(_message.Message):
    __slots__ = ("move_to_safe_z_first", "minimum_traverse_height_end")
    MOVE_TO_SAFE_Z_FIRST_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    move_to_safe_z_first: bool
    minimum_traverse_height_end: float
    def __init__(self, move_to_safe_z_first: _Optional[bool] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class CoreGrippersDropToolsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersPickUpToolsRequest(_message.Message):
    __slots__ = ("front_channel",)
    FRONT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    front_channel: int
    def __init__(self, front_channel: _Optional[int] = ...) -> None: ...

class CoreGrippersPickUpToolsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersReturnToolsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersReturnToolsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersPickUpResourceRequest(_message.Message):
    __slots__ = ("resource", "offset", "pickup_distance_from_top", "pickup_distance_from_bottom", "minimum_traverse_height_start", "resource_size_y", "y_clearance", "grip_speed_y", "squeeze_mm", "grip_strength", "z_speed", "z_acceleration", "minimum_traverse_height_end")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_TOP_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_BOTTOM_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_SIZE_Y_FIELD_NUMBER: _ClassVar[int]
    Y_CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    GRIP_SPEED_Y_FIELD_NUMBER: _ClassVar[int]
    SQUEEZE_MM_FIELD_NUMBER: _ClassVar[int]
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    resource: _types_pb2_1.ResourceRef
    offset: _types_pb2_1.Vec3
    pickup_distance_from_top: float
    pickup_distance_from_bottom: float
    minimum_traverse_height_start: float
    resource_size_y: float
    y_clearance: float
    grip_speed_y: float
    squeeze_mm: float
    grip_strength: int
    z_speed: float
    z_acceleration: float
    minimum_traverse_height_end: float
    def __init__(self, resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., pickup_distance_from_top: _Optional[float] = ..., pickup_distance_from_bottom: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., resource_size_y: _Optional[float] = ..., y_clearance: _Optional[float] = ..., grip_speed_y: _Optional[float] = ..., squeeze_mm: _Optional[float] = ..., grip_strength: _Optional[int] = ..., z_speed: _Optional[float] = ..., z_acceleration: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class CoreGrippersPickUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersPlaceResourceRequest(_message.Message):
    __slots__ = ("to_resource", "to_location", "offset", "minimum_traverse_height_start", "x_acceleration_level", "z_speed", "z_acceleration", "press_on_distance", "y_clearance", "minimum_traverse_height_end")
    TO_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    TO_LOCATION_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    X_ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    PRESS_ON_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    Y_CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    to_resource: _types_pb2_1.ResourceRef
    to_location: _types_pb2_1.Vec3
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_start: float
    x_acceleration_level: int
    z_speed: float
    z_acceleration: float
    press_on_distance: float
    y_clearance: float
    minimum_traverse_height_end: float
    def __init__(self, to_resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., to_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_start: _Optional[float] = ..., x_acceleration_level: _Optional[int] = ..., z_speed: _Optional[float] = ..., z_acceleration: _Optional[float] = ..., press_on_distance: _Optional[float] = ..., y_clearance: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class CoreGrippersPlaceResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersReturnResourceRequest(_message.Message):
    __slots__ = ("offset", "minimum_traverse_height_start", "x_acceleration_level", "z_speed", "z_acceleration", "press_on_distance", "y_clearance", "minimum_traverse_height_end")
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    X_ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    PRESS_ON_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    Y_CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_start: float
    x_acceleration_level: int
    z_speed: float
    z_acceleration: float
    press_on_distance: float
    y_clearance: float
    minimum_traverse_height_end: float
    def __init__(self, offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_start: _Optional[float] = ..., x_acceleration_level: _Optional[int] = ..., z_speed: _Optional[float] = ..., z_acceleration: _Optional[float] = ..., press_on_distance: _Optional[float] = ..., y_clearance: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class CoreGrippersReturnResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGrippersProbeResourceExistsUsingZtouchRequest(_message.Message):
    __slots__ = ("location", "resource", "gripper_y_margin", "offset", "minimum_traverse_height_start", "minimum_traverse_height_end", "enable_recovery")
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_Y_MARGIN_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    ENABLE_RECOVERY_FIELD_NUMBER: _ClassVar[int]
    location: _types_pb2_1.Vec3
    resource: _types_pb2_1.ResourceRef
    gripper_y_margin: float
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_start: float
    minimum_traverse_height_end: float
    enable_recovery: bool
    def __init__(self, location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., gripper_y_margin: _Optional[float] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_start: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ..., enable_recovery: _Optional[bool] = ...) -> None: ...

class CoreGrippersProbeResourceExistsUsingZtouchResponse(_message.Message):
    __slots__ = ("exists",)
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    exists: bool
    def __init__(self, exists: _Optional[bool] = ...) -> None: ...

class CoreGrippersSettings(_message.Message):
    __slots__ = ("default_grip_strength", "default_z_speed_with_resource_held", "default_z_acceleration_with_resource_held", "default_minimum_traverse_height")
    DEFAULT_GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_Z_SPEED_WITH_RESOURCE_HELD_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_Z_ACCELERATION_WITH_RESOURCE_HELD_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_MINIMUM_TRAVERSE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    default_grip_strength: int
    default_z_speed_with_resource_held: float
    default_z_acceleration_with_resource_held: float
    default_minimum_traverse_height: float
    def __init__(self, default_grip_strength: _Optional[int] = ..., default_z_speed_with_resource_held: _Optional[float] = ..., default_z_acceleration_with_resource_held: _Optional[float] = ..., default_minimum_traverse_height: _Optional[float] = ...) -> None: ...
