from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HeadRequestDriveParameterRequest(_message.Message):
    __slots__ = ("parameter",)
    PARAMETER_FIELD_NUMBER: _ClassVar[int]
    parameter: str
    def __init__(self, parameter: _Optional[str] = ...) -> None: ...

class HeadRequestDriveParameterResponse(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: float
    def __init__(self, value: _Optional[float] = ...) -> None: ...

class HeadSetDriveParameterRequest(_message.Message):
    __slots__ = ("parameter", "value")
    PARAMETER_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    parameter: str
    value: float
    def __init__(self, parameter: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...

class HeadSetDriveParameterResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestFirmwareVersionResponse(_message.Message):
    __slots__ = ("version", "date")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    version: str
    date: _types_pb2.Date
    def __init__(self, version: _Optional[str] = ..., date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ...) -> None: ...

class HeadRequestHardwareRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestHardwareResponse(_message.Message):
    __slots__ = ("hardware",)
    HARDWARE_FIELD_NUMBER: _ClassVar[int]
    hardware: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, hardware: _Optional[_Iterable[str]] = ...) -> None: ...

class HeadRequestHeadTypeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestHeadTypeResponse(_message.Message):
    __slots__ = ("head_type",)
    HEAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    head_type: str
    def __init__(self, head_type: _Optional[str] = ...) -> None: ...

class HeadRequestXOffsetRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestXOffsetResponse(_message.Message):
    __slots__ = ("x_offset",)
    X_OFFSET_FIELD_NUMBER: _ClassVar[int]
    x_offset: float
    def __init__(self, x_offset: _Optional[float] = ...) -> None: ...

class HeadRequestPredefinedYPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestPredefinedYPositionsResponse(_message.Message):
    __slots__ = ("predefined_y_positions",)
    PREDEFINED_Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    predefined_y_positions: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, predefined_y_positions: _Optional[_Iterable[float]] = ...) -> None: ...

class HeadRequestPredefinedZPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestPredefinedZPositionsResponse(_message.Message):
    __slots__ = ("predefined_z_positions",)
    PREDEFINED_Z_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    predefined_z_positions: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, predefined_z_positions: _Optional[_Iterable[float]] = ...) -> None: ...

class HeadRequestTipPresenceRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestTipPresenceResponse(_message.Message):
    __slots__ = ("present",)
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    present: bool
    def __init__(self, present: _Optional[bool] = ...) -> None: ...

class HeadUpdateLocationByReferencePointRequest(_message.Message):
    __slots__ = ("y", "z")
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    y: float
    z: float
    def __init__(self, y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class HeadUpdateLocationByReferencePointResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadGetReferencePointLocationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadGetReferencePointLocationResponse(_message.Message):
    __slots__ = ("reference_point_location",)
    REFERENCE_POINT_LOCATION_FIELD_NUMBER: _ClassVar[int]
    reference_point_location: _types_pb2_1.Vec3
    def __init__(self, reference_point_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ...) -> None: ...

class HeadRequestYPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestYPositionResponse(_message.Message):
    __slots__ = ("y_position",)
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    y_position: float
    def __init__(self, y_position: _Optional[float] = ...) -> None: ...

class HeadRequestZPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestZPositionResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class HeadRequestLocationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestLocationResponse(_message.Message):
    __slots__ = ("location",)
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    location: _types_pb2_1.Vec3
    def __init__(self, location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ...) -> None: ...

class HeadRequestTipOverhangRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestTipOverhangResponse(_message.Message):
    __slots__ = ("tip_overhang",)
    TIP_OVERHANG_FIELD_NUMBER: _ClassVar[int]
    tip_overhang: float
    def __init__(self, tip_overhang: _Optional[float] = ...) -> None: ...

class HeadRequestXPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadRequestXPositionResponse(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: float
    def __init__(self, x_position: _Optional[float] = ...) -> None: ...

class HeadMoveToXPositionRequest(_message.Message):
    __slots__ = ("x", "acceleration_level", "current_limit", "settle_reads")
    X_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    SETTLE_READS_FIELD_NUMBER: _ClassVar[int]
    x: float
    acceleration_level: int
    current_limit: int
    settle_reads: int
    def __init__(self, x: _Optional[float] = ..., acceleration_level: _Optional[int] = ..., current_limit: _Optional[int] = ..., settle_reads: _Optional[int] = ...) -> None: ...

class HeadMoveToXPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class HeadMoveToYPositionRequest(_message.Message):
    __slots__ = ("y", "speed", "acceleration", "current_limit", "read_timeout")
    Y_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    y: float
    speed: float
    acceleration: float
    current_limit: int
    read_timeout: int
    def __init__(self, y: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ..., read_timeout: _Optional[int] = ...) -> None: ...

class HeadMoveToYPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class HeadMoveToXyPositionRequest(_message.Message):
    __slots__ = ("x", "y", "minimum_traverse_height_start", "x_acceleration_level", "x_current_limit", "y_speed", "y_acceleration", "y_current_limit", "z_speed", "z_acceleration")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    X_ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    X_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    Y_SPEED_FIELD_NUMBER: _ClassVar[int]
    Y_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    Y_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    minimum_traverse_height_start: float
    x_acceleration_level: int
    x_current_limit: int
    y_speed: float
    y_acceleration: float
    y_current_limit: int
    z_speed: float
    z_acceleration: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., x_acceleration_level: _Optional[int] = ..., x_current_limit: _Optional[int] = ..., y_speed: _Optional[float] = ..., y_acceleration: _Optional[float] = ..., y_current_limit: _Optional[int] = ..., z_speed: _Optional[float] = ..., z_acceleration: _Optional[float] = ...) -> None: ...

class HeadMoveToXyPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadProbeZMaxRequest(_message.Message):
    __slots__ = ("read_timeout",)
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    read_timeout: int
    def __init__(self, read_timeout: _Optional[int] = ...) -> None: ...

class HeadProbeZMaxResponse(_message.Message):
    __slots__ = ("z_max",)
    Z_MAX_FIELD_NUMBER: _ClassVar[int]
    z_max: float
    def __init__(self, z_max: _Optional[float] = ...) -> None: ...

class HeadMoveStopDiscToZPositionRequest(_message.Message):
    __slots__ = ("z", "speed", "acceleration", "current_limit", "read_timeout")
    Z_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    z: float
    speed: float
    acceleration: float
    current_limit: int
    read_timeout: int
    def __init__(self, z: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ..., read_timeout: _Optional[int] = ...) -> None: ...

class HeadMoveStopDiscToZPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class HeadMoveToolBottomToZPositionRequest(_message.Message):
    __slots__ = ("z", "speed", "acceleration", "current_limit", "read_timeout")
    Z_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    z: float
    speed: float
    acceleration: float
    current_limit: int
    read_timeout: int
    def __init__(self, z: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ..., read_timeout: _Optional[int] = ...) -> None: ...

class HeadMoveToolBottomToZPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class HeadMoveToSafeZRequest(_message.Message):
    __slots__ = ("speed", "acceleration")
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    speed: float
    acceleration: float
    def __init__(self, speed: _Optional[float] = ..., acceleration: _Optional[float] = ...) -> None: ...

class HeadMoveToSafeZResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class HeadDispensingDriveRequestULPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadDispensingDriveRequestULPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: float
    def __init__(self, position: _Optional[float] = ...) -> None: ...

class HeadGetPistonPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HeadGetPistonPositionResponse(_message.Message):
    __slots__ = ("piston_position",)
    PISTON_POSITION_FIELD_NUMBER: _ClassVar[int]
    piston_position: float
    def __init__(self, piston_position: _Optional[float] = ...) -> None: ...

class HeadMoveDispensingDriveToPositionRequest(_message.Message):
    __slots__ = ("volume", "speed", "stop_speed", "acceleration", "current_limit", "read_timeout")
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    STOP_SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    volume: float
    speed: float
    stop_speed: float
    acceleration: float
    current_limit: int
    read_timeout: int
    def __init__(self, volume: _Optional[float] = ..., speed: _Optional[float] = ..., stop_speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ..., read_timeout: _Optional[int] = ...) -> None: ...

class HeadMoveDispensingDriveToPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class HeadParkRequest(_message.Message):
    __slots__ = ("speed", "acceleration")
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    speed: float
    acceleration: float
    def __init__(self, speed: _Optional[float] = ..., acceleration: _Optional[float] = ...) -> None: ...

class HeadParkResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class HeadInitializeRequest(_message.Message):
    __slots__ = ("tip_discard_location", "minimum_traverse_height_end", "read_timeout")
    TIP_DISCARD_LOCATION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    tip_discard_location: _types_pb2_1.Vec3
    minimum_traverse_height_end: float
    read_timeout: int
    def __init__(self, tip_discard_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_end: _Optional[float] = ..., read_timeout: _Optional[int] = ...) -> None: ...

class HeadInitializeResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...
