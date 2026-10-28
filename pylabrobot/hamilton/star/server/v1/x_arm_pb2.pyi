from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class XArmConfiguration(_message.Message):
    __slots__ = ("pip_installed", "iswap_installed", "head96_installed", "nano_pipettor_installed", "head384_installed", "xl_channels_installed", "tube_gripper_installed", "imaging_channel_installed", "robotic_channel_installed", "gel_card_gripper_installed", "puncher_handler_installed", "width", "large", "x_range", "workspace_x_range", "wrap_size", "firmware_version", "x_mm_per_increment", "x_range_increments", "acceleration_level_range", "large_arm_size_x", "large_arm_reference_from_left")
    PIP_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    ISWAP_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    HEAD96_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    NANO_PIPETTOR_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    HEAD384_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    XL_CHANNELS_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    TUBE_GRIPPER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    IMAGING_CHANNEL_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    ROBOTIC_CHANNEL_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    GEL_CARD_GRIPPER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    PUNCHER_HANDLER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    LARGE_FIELD_NUMBER: _ClassVar[int]
    X_RANGE_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_X_RANGE_FIELD_NUMBER: _ClassVar[int]
    WRAP_SIZE_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    X_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    X_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_LEVEL_RANGE_FIELD_NUMBER: _ClassVar[int]
    LARGE_ARM_SIZE_X_FIELD_NUMBER: _ClassVar[int]
    LARGE_ARM_REFERENCE_FROM_LEFT_FIELD_NUMBER: _ClassVar[int]
    pip_installed: bool
    iswap_installed: bool
    head96_installed: bool
    nano_pipettor_installed: bool
    head384_installed: bool
    xl_channels_installed: bool
    tube_gripper_installed: bool
    imaging_channel_installed: bool
    robotic_channel_installed: bool
    gel_card_gripper_installed: bool
    puncher_handler_installed: bool
    width: float
    large: bool
    x_range: _types_pb2.DoubleRange
    workspace_x_range: _types_pb2.DoubleRange
    wrap_size: float
    firmware_version: str
    x_mm_per_increment: float
    x_range_increments: _types_pb2.Int32Range
    acceleration_level_range: _types_pb2.Int32Range
    large_arm_size_x: float
    large_arm_reference_from_left: float
    def __init__(self, pip_installed: _Optional[bool] = ..., iswap_installed: _Optional[bool] = ..., head96_installed: _Optional[bool] = ..., nano_pipettor_installed: _Optional[bool] = ..., head384_installed: _Optional[bool] = ..., xl_channels_installed: _Optional[bool] = ..., tube_gripper_installed: _Optional[bool] = ..., imaging_channel_installed: _Optional[bool] = ..., robotic_channel_installed: _Optional[bool] = ..., gel_card_gripper_installed: _Optional[bool] = ..., puncher_handler_installed: _Optional[bool] = ..., width: _Optional[float] = ..., large: _Optional[bool] = ..., x_range: _Optional[_Union[_types_pb2.DoubleRange, _Mapping]] = ..., workspace_x_range: _Optional[_Union[_types_pb2.DoubleRange, _Mapping]] = ..., wrap_size: _Optional[float] = ..., firmware_version: _Optional[str] = ..., x_mm_per_increment: _Optional[float] = ..., x_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., acceleration_level_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., large_arm_size_x: _Optional[float] = ..., large_arm_reference_from_left: _Optional[float] = ...) -> None: ...

class XArmRequestFirmwareVersionRequest(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ...) -> None: ...

class XArmRequestFirmwareVersionResponse(_message.Message):
    __slots__ = ("version", "date")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    version: str
    date: _types_pb2.Date
    def __init__(self, version: _Optional[str] = ..., date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ...) -> None: ...

class XArmRequestInitializationStatusRequest(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ...) -> None: ...

class XArmRequestInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: _Optional[bool] = ...) -> None: ...

class XArmDiscoverRequest(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ...) -> None: ...

class XArmDiscoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class XArmInitializeRequest(_message.Message):
    __slots__ = ("side", "current_limit")
    SIDE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    current_limit: int
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ..., current_limit: _Optional[int] = ...) -> None: ...

class XArmInitializeResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class XArmUpdateLocationByReferencePointRequest(_message.Message):
    __slots__ = ("side", "x")
    SIDE_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    x: float
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ..., x: _Optional[float] = ...) -> None: ...

class XArmUpdateLocationByReferencePointResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class XArmGetReferencePointXRequest(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ...) -> None: ...

class XArmGetReferencePointXResponse(_message.Message):
    __slots__ = ("reference_point_x",)
    REFERENCE_POINT_X_FIELD_NUMBER: _ClassVar[int]
    reference_point_x: float
    def __init__(self, reference_point_x: _Optional[float] = ...) -> None: ...

class XArmRequestPositionRequest(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ...) -> None: ...

class XArmRequestPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: float
    def __init__(self, position: _Optional[float] = ...) -> None: ...

class XArmMoveToXPositionRequest(_message.Message):
    __slots__ = ("side", "x", "acceleration_level", "current_limit", "settle_reads")
    SIDE_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    SETTLE_READS_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    x: float
    acceleration_level: int
    current_limit: int
    settle_reads: int
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ..., x: _Optional[float] = ..., acceleration_level: _Optional[int] = ..., current_limit: _Optional[int] = ..., settle_reads: _Optional[int] = ...) -> None: ...

class XArmMoveToXPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class XArmMoveXRelativeRequest(_message.Message):
    __slots__ = ("side", "distance", "acceleration_level", "current_limit")
    SIDE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    side: _types_pb2.XArmSide
    distance: float
    acceleration_level: int
    current_limit: int
    def __init__(self, side: _Optional[_Union[_types_pb2.XArmSide, str]] = ..., distance: _Optional[float] = ..., acceleration_level: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class XArmMoveXRelativeResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class XArmSettings(_message.Message):
    __slots__ = ("default_acceleration_level", "default_current_limit")
    DEFAULT_ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    default_acceleration_level: int
    default_current_limit: int
    def __init__(self, default_acceleration_level: _Optional[int] = ..., default_current_limit: _Optional[int] = ...) -> None: ...
