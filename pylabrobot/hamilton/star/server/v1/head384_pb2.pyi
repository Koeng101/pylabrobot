from pylabrobot.hamilton.star.server.v1 import head_pb2 as _head_pb2
from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Head384Configuration(_message.Message):
    __slots__ = ("module", "retract_command", "initialize_command", "tip_presence_command", "position_command", "y_parameter", "z_parameter", "z_end_parameter", "x_offset_parameter", "head_types", "drive_parameters", "first_documented_firmware_year", "firmware_version", "firmware_date", "x_offset", "channel_pitch", "channel_columns", "channel_rows", "body_size_z", "min_x_clear_of_left_side_panel", "min_tool_bottom_z", "supports_clot_monitoring_clld", "head_type", "tip_discard_location", "z_range", "z_drive_mm_per_increment", "y_drive_mm_per_increment", "y_drive_acceleration_mm_per_increment", "z_drive_acceleration_mm_per_increment", "dispensing_drive_mm_per_increment", "dispensing_drive_speed_increments_per_unit", "dispensing_drive_acceleration_increments_per_unit", "z_speed_range_increments", "z_acceleration_range_increments", "predefined_y_position_origin", "predefined_z_position_origin", "predefined_y_slots", "predefined_y_positions_increments", "predefined_z_slots", "predefined_z_positions_increments", "traversal_z_position", "y_drive_current_limit_default", "z_drive_current_limit_default", "current_limit_range", "dispensing_drive_current_limit_range", "y_speed_default_increments", "y_acceleration_default_increments", "z_speed_default_increments", "z_acceleration_default_increments", "y_drive_speed_firmware_reported", "y_drive_acceleration_firmware_reported", "z_drive_speed_firmware_reported", "z_drive_acceleration_firmware_reported", "supports_lld_absolute_threshold_check", "y_range_increments", "y_speed_range_increments", "y_acceleration_range_increments", "z_range_increments")
    class HeadTypesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: str
        def __init__(self, key: _Optional[int] = ..., value: _Optional[str] = ...) -> None: ...
    class DriveParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    MODULE_FIELD_NUMBER: _ClassVar[int]
    RETRACT_COMMAND_FIELD_NUMBER: _ClassVar[int]
    INITIALIZE_COMMAND_FIELD_NUMBER: _ClassVar[int]
    TIP_PRESENCE_COMMAND_FIELD_NUMBER: _ClassVar[int]
    POSITION_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Y_PARAMETER_FIELD_NUMBER: _ClassVar[int]
    Z_PARAMETER_FIELD_NUMBER: _ClassVar[int]
    Z_END_PARAMETER_FIELD_NUMBER: _ClassVar[int]
    X_OFFSET_PARAMETER_FIELD_NUMBER: _ClassVar[int]
    HEAD_TYPES_FIELD_NUMBER: _ClassVar[int]
    DRIVE_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    FIRST_DOCUMENTED_FIRMWARE_YEAR_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_DATE_FIELD_NUMBER: _ClassVar[int]
    X_OFFSET_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_PITCH_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ROWS_FIELD_NUMBER: _ClassVar[int]
    BODY_SIZE_Z_FIELD_NUMBER: _ClassVar[int]
    MIN_X_CLEAR_OF_LEFT_SIDE_PANEL_FIELD_NUMBER: _ClassVar[int]
    MIN_TOOL_BOTTOM_Z_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_CLOT_MONITORING_CLLD_FIELD_NUMBER: _ClassVar[int]
    HEAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIP_DISCARD_LOCATION_FIELD_NUMBER: _ClassVar[int]
    Z_RANGE_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_ACCELERATION_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_ACCELERATION_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_SPEED_INCREMENTS_PER_UNIT_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_ACCELERATION_INCREMENTS_PER_UNIT_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    PREDEFINED_Y_POSITION_ORIGIN_FIELD_NUMBER: _ClassVar[int]
    PREDEFINED_Z_POSITION_ORIGIN_FIELD_NUMBER: _ClassVar[int]
    PREDEFINED_Y_SLOTS_FIELD_NUMBER: _ClassVar[int]
    PREDEFINED_Y_POSITIONS_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    PREDEFINED_Z_SLOTS_FIELD_NUMBER: _ClassVar[int]
    PREDEFINED_Z_POSITIONS_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    TRAVERSAL_Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_RANGE_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_CURRENT_LIMIT_RANGE_FIELD_NUMBER: _ClassVar[int]
    Y_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_ACCELERATION_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_SPEED_FIRMWARE_REPORTED_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_ACCELERATION_FIRMWARE_REPORTED_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_SPEED_FIRMWARE_REPORTED_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_ACCELERATION_FIRMWARE_REPORTED_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_LLD_ABSOLUTE_THRESHOLD_CHECK_FIELD_NUMBER: _ClassVar[int]
    Y_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_ACCELERATION_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    module: str
    retract_command: str
    initialize_command: str
    tip_presence_command: str
    position_command: str
    y_parameter: str
    z_parameter: str
    z_end_parameter: str
    x_offset_parameter: str
    head_types: _containers.ScalarMap[int, str]
    drive_parameters: _containers.ScalarMap[str, int]
    first_documented_firmware_year: int
    firmware_version: str
    firmware_date: _types_pb2.Date
    x_offset: float
    channel_pitch: float
    channel_columns: int
    channel_rows: int
    body_size_z: float
    min_x_clear_of_left_side_panel: float
    min_tool_bottom_z: float
    supports_clot_monitoring_clld: bool
    head_type: str
    tip_discard_location: _types_pb2_1.Vec3
    z_range: _types_pb2.DoubleRange
    z_drive_mm_per_increment: float
    y_drive_mm_per_increment: float
    y_drive_acceleration_mm_per_increment: float
    z_drive_acceleration_mm_per_increment: float
    dispensing_drive_mm_per_increment: float
    dispensing_drive_speed_increments_per_unit: int
    dispensing_drive_acceleration_increments_per_unit: int
    z_speed_range_increments: _types_pb2.Int32Range
    z_acceleration_range_increments: _types_pb2.Int32Range
    predefined_y_position_origin: int
    predefined_z_position_origin: int
    predefined_y_slots: _containers.RepeatedScalarFieldContainer[str]
    predefined_y_positions_increments: _types_pb2.StringInt32Map
    predefined_z_slots: _containers.RepeatedScalarFieldContainer[str]
    predefined_z_positions_increments: _types_pb2.StringInt32Map
    traversal_z_position: float
    y_drive_current_limit_default: int
    z_drive_current_limit_default: int
    current_limit_range: _types_pb2.Int32Range
    dispensing_drive_current_limit_range: _types_pb2.Int32Range
    y_speed_default_increments: int
    y_acceleration_default_increments: int
    z_speed_default_increments: int
    z_acceleration_default_increments: int
    y_drive_speed_firmware_reported: float
    y_drive_acceleration_firmware_reported: float
    z_drive_speed_firmware_reported: float
    z_drive_acceleration_firmware_reported: float
    supports_lld_absolute_threshold_check: bool
    y_range_increments: _types_pb2.Int32Range
    y_speed_range_increments: _types_pb2.Int32Range
    y_acceleration_range_increments: _types_pb2.Int32Range
    z_range_increments: _types_pb2.Int32Range
    def __init__(self, module: _Optional[str] = ..., retract_command: _Optional[str] = ..., initialize_command: _Optional[str] = ..., tip_presence_command: _Optional[str] = ..., position_command: _Optional[str] = ..., y_parameter: _Optional[str] = ..., z_parameter: _Optional[str] = ..., z_end_parameter: _Optional[str] = ..., x_offset_parameter: _Optional[str] = ..., head_types: _Optional[_Mapping[int, str]] = ..., drive_parameters: _Optional[_Mapping[str, int]] = ..., first_documented_firmware_year: _Optional[int] = ..., firmware_version: _Optional[str] = ..., firmware_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., x_offset: _Optional[float] = ..., channel_pitch: _Optional[float] = ..., channel_columns: _Optional[int] = ..., channel_rows: _Optional[int] = ..., body_size_z: _Optional[float] = ..., min_x_clear_of_left_side_panel: _Optional[float] = ..., min_tool_bottom_z: _Optional[float] = ..., supports_clot_monitoring_clld: _Optional[bool] = ..., head_type: _Optional[str] = ..., tip_discard_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., z_range: _Optional[_Union[_types_pb2.DoubleRange, _Mapping]] = ..., z_drive_mm_per_increment: _Optional[float] = ..., y_drive_mm_per_increment: _Optional[float] = ..., y_drive_acceleration_mm_per_increment: _Optional[float] = ..., z_drive_acceleration_mm_per_increment: _Optional[float] = ..., dispensing_drive_mm_per_increment: _Optional[float] = ..., dispensing_drive_speed_increments_per_unit: _Optional[int] = ..., dispensing_drive_acceleration_increments_per_unit: _Optional[int] = ..., z_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., predefined_y_position_origin: _Optional[int] = ..., predefined_z_position_origin: _Optional[int] = ..., predefined_y_slots: _Optional[_Iterable[str]] = ..., predefined_y_positions_increments: _Optional[_Union[_types_pb2.StringInt32Map, _Mapping]] = ..., predefined_z_slots: _Optional[_Iterable[str]] = ..., predefined_z_positions_increments: _Optional[_Union[_types_pb2.StringInt32Map, _Mapping]] = ..., traversal_z_position: _Optional[float] = ..., y_drive_current_limit_default: _Optional[int] = ..., z_drive_current_limit_default: _Optional[int] = ..., current_limit_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., dispensing_drive_current_limit_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_speed_default_increments: _Optional[int] = ..., y_acceleration_default_increments: _Optional[int] = ..., z_speed_default_increments: _Optional[int] = ..., z_acceleration_default_increments: _Optional[int] = ..., y_drive_speed_firmware_reported: _Optional[float] = ..., y_drive_acceleration_firmware_reported: _Optional[float] = ..., z_drive_speed_firmware_reported: _Optional[float] = ..., z_drive_acceleration_firmware_reported: _Optional[float] = ..., supports_lld_absolute_threshold_check: _Optional[bool] = ..., y_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ...) -> None: ...

class Head384DiscoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head384DiscoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head384Settings(_message.Message):
    __slots__ = ("default_dispensing_drive_speed", "default_dispensing_drive_acceleration")
    DEFAULT_DISPENSING_DRIVE_SPEED_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_DISPENSING_DRIVE_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    default_dispensing_drive_speed: float
    default_dispensing_drive_acceleration: float
    def __init__(self, default_dispensing_drive_speed: _Optional[float] = ..., default_dispensing_drive_acceleration: _Optional[float] = ...) -> None: ...
