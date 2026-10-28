from pylabrobot.hamilton.star.server.v1 import head_pb2 as _head_pb2
from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Head96Configuration(_message.Message):
    __slots__ = ("module", "retract_command", "initialize_command", "tip_presence_command", "position_command", "y_parameter", "z_parameter", "z_end_parameter", "x_offset_parameter", "head_types", "drive_parameters", "first_documented_firmware_year", "firmware_version", "firmware_date", "x_offset", "channel_pitch", "channel_columns", "channel_rows", "body_size_z", "min_x_clear_of_left_side_panel", "min_tool_bottom_z", "supports_clot_monitoring_clld", "head_type", "tip_discard_location", "z_range", "z_drive_mm_per_increment", "y_drive_mm_per_increment", "y_drive_acceleration_mm_per_increment", "z_drive_acceleration_mm_per_increment", "dispensing_drive_mm_per_increment", "dispensing_drive_speed_increments_per_unit", "dispensing_drive_acceleration_increments_per_unit", "z_speed_range_increments", "z_acceleration_range_increments", "predefined_y_position_origin", "predefined_z_position_origin", "predefined_y_slots", "predefined_y_positions_increments", "predefined_z_slots", "predefined_z_positions_increments", "traversal_z_position", "y_drive_current_limit_default", "z_drive_current_limit_default", "current_limit_range", "dispensing_drive_current_limit_range", "y_speed_default_increments", "y_acceleration_default_increments", "z_speed_default_increments", "z_acceleration_default_increments", "y_drive_speed_firmware_reported", "y_drive_acceleration_firmware_reported", "z_drive_speed_firmware_reported", "z_drive_acceleration_firmware_reported", "squeezer_drive_speed_firmware_reported", "squeezer_drive_acceleration_firmware_reported", "stop_disc_type", "instrument_type", "dispensing_drive_uL_per_increment", "squeezer_drive_mm_per_increment", "tip_command_y_range", "dispensing_drive_position_before_rack_pickup", "pipetting_volume_range_increments", "pipetting_speed_range_increments", "pipetting_distance_range_increments", "immersion_depth_range_increments", "surface_following_distance_range_increments", "swap_speed_range_increments", "transport_air_volume_range_increments", "stop_back_volume_range_increments", "side_touch_off_distance_range_increments", "settling_time_range_increments", "mix_cycles_range", "second_section_ratio_range_increments", "lld_sensitivity_range", "limit_curve_index_range", "y_increment_floor")
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
    SQUEEZER_DRIVE_SPEED_FIRMWARE_REPORTED_FIELD_NUMBER: _ClassVar[int]
    SQUEEZER_DRIVE_ACCELERATION_FIRMWARE_REPORTED_FIELD_NUMBER: _ClassVar[int]
    STOP_DISC_TYPE_FIELD_NUMBER: _ClassVar[int]
    INSTRUMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_UL_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    SQUEEZER_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    TIP_COMMAND_Y_RANGE_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_POSITION_BEFORE_RACK_PICKUP_FIELD_NUMBER: _ClassVar[int]
    PIPETTING_VOLUME_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    PIPETTING_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    PIPETTING_DISTANCE_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    STOP_BACK_VOLUME_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    SIDE_TOUCH_OFF_DISTANCE_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    MIX_CYCLES_RANGE_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSITIVITY_RANGE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_RANGE_FIELD_NUMBER: _ClassVar[int]
    Y_INCREMENT_FLOOR_FIELD_NUMBER: _ClassVar[int]
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
    squeezer_drive_speed_firmware_reported: float
    squeezer_drive_acceleration_firmware_reported: float
    stop_disc_type: _types_pb2.StopDiscType
    instrument_type: _types_pb2.Head96InstrumentType
    dispensing_drive_uL_per_increment: float
    squeezer_drive_mm_per_increment: float
    tip_command_y_range: _types_pb2.DoubleRange
    dispensing_drive_position_before_rack_pickup: float
    pipetting_volume_range_increments: _types_pb2.Int32Range
    pipetting_speed_range_increments: _types_pb2.Int32Range
    pipetting_distance_range_increments: _types_pb2.Int32Range
    immersion_depth_range_increments: _types_pb2.Int32Range
    surface_following_distance_range_increments: _types_pb2.Int32Range
    swap_speed_range_increments: _types_pb2.Int32Range
    transport_air_volume_range_increments: _types_pb2.Int32Range
    stop_back_volume_range_increments: _types_pb2.Int32Range
    side_touch_off_distance_range_increments: _types_pb2.Int32Range
    settling_time_range_increments: _types_pb2.Int32Range
    mix_cycles_range: _types_pb2.Int32Range
    second_section_ratio_range_increments: _types_pb2.Int32Range
    lld_sensitivity_range: _types_pb2.Int32Range
    limit_curve_index_range: _types_pb2.Int32Range
    y_increment_floor: int
    def __init__(self, module: _Optional[str] = ..., retract_command: _Optional[str] = ..., initialize_command: _Optional[str] = ..., tip_presence_command: _Optional[str] = ..., position_command: _Optional[str] = ..., y_parameter: _Optional[str] = ..., z_parameter: _Optional[str] = ..., z_end_parameter: _Optional[str] = ..., x_offset_parameter: _Optional[str] = ..., head_types: _Optional[_Mapping[int, str]] = ..., drive_parameters: _Optional[_Mapping[str, int]] = ..., first_documented_firmware_year: _Optional[int] = ..., firmware_version: _Optional[str] = ..., firmware_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., x_offset: _Optional[float] = ..., channel_pitch: _Optional[float] = ..., channel_columns: _Optional[int] = ..., channel_rows: _Optional[int] = ..., body_size_z: _Optional[float] = ..., min_x_clear_of_left_side_panel: _Optional[float] = ..., min_tool_bottom_z: _Optional[float] = ..., supports_clot_monitoring_clld: _Optional[bool] = ..., head_type: _Optional[str] = ..., tip_discard_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., z_range: _Optional[_Union[_types_pb2.DoubleRange, _Mapping]] = ..., z_drive_mm_per_increment: _Optional[float] = ..., y_drive_mm_per_increment: _Optional[float] = ..., y_drive_acceleration_mm_per_increment: _Optional[float] = ..., z_drive_acceleration_mm_per_increment: _Optional[float] = ..., dispensing_drive_mm_per_increment: _Optional[float] = ..., dispensing_drive_speed_increments_per_unit: _Optional[int] = ..., dispensing_drive_acceleration_increments_per_unit: _Optional[int] = ..., z_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., predefined_y_position_origin: _Optional[int] = ..., predefined_z_position_origin: _Optional[int] = ..., predefined_y_slots: _Optional[_Iterable[str]] = ..., predefined_y_positions_increments: _Optional[_Union[_types_pb2.StringInt32Map, _Mapping]] = ..., predefined_z_slots: _Optional[_Iterable[str]] = ..., predefined_z_positions_increments: _Optional[_Union[_types_pb2.StringInt32Map, _Mapping]] = ..., traversal_z_position: _Optional[float] = ..., y_drive_current_limit_default: _Optional[int] = ..., z_drive_current_limit_default: _Optional[int] = ..., current_limit_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., dispensing_drive_current_limit_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_speed_default_increments: _Optional[int] = ..., y_acceleration_default_increments: _Optional[int] = ..., z_speed_default_increments: _Optional[int] = ..., z_acceleration_default_increments: _Optional[int] = ..., y_drive_speed_firmware_reported: _Optional[float] = ..., y_drive_acceleration_firmware_reported: _Optional[float] = ..., z_drive_speed_firmware_reported: _Optional[float] = ..., z_drive_acceleration_firmware_reported: _Optional[float] = ..., squeezer_drive_speed_firmware_reported: _Optional[float] = ..., squeezer_drive_acceleration_firmware_reported: _Optional[float] = ..., stop_disc_type: _Optional[_Union[_types_pb2.StopDiscType, str]] = ..., instrument_type: _Optional[_Union[_types_pb2.Head96InstrumentType, str]] = ..., dispensing_drive_uL_per_increment: _Optional[float] = ..., squeezer_drive_mm_per_increment: _Optional[float] = ..., tip_command_y_range: _Optional[_Union[_types_pb2.DoubleRange, _Mapping]] = ..., dispensing_drive_position_before_rack_pickup: _Optional[float] = ..., pipetting_volume_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., pipetting_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., pipetting_distance_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., immersion_depth_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., surface_following_distance_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., swap_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., transport_air_volume_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., stop_back_volume_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., side_touch_off_distance_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., settling_time_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., mix_cycles_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., second_section_ratio_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., lld_sensitivity_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., limit_curve_index_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_increment_floor: _Optional[int] = ...) -> None: ...

class Head96DiscoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DiscoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96InitializeRequest(_message.Message):
    __slots__ = ("tip_discard_location", "minimum_traverse_height_end", "read_timeout")
    TIP_DISCARD_LOCATION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    tip_discard_location: _types_pb2_1.Vec3
    minimum_traverse_height_end: float
    read_timeout: int
    def __init__(self, tip_discard_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_end: _Optional[float] = ..., read_timeout: _Optional[int] = ...) -> None: ...

class Head96InitializeResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class Head96PickUpTipsRequest(_message.Message):
    __slots__ = ("tip_rack", "offset", "tip_pickup_method", "minimum_traverse_height_end", "minimum_traverse_height_start", "channel", "tip_spot")
    TIP_RACK_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIP_PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    TIP_SPOT_FIELD_NUMBER: _ClassVar[int]
    tip_rack: _types_pb2_1.ResourceRef
    offset: _types_pb2_1.Vec3
    tip_pickup_method: _types_pb2.Head96TipPickupMethod
    minimum_traverse_height_end: float
    minimum_traverse_height_start: float
    channel: str
    tip_spot: str
    def __init__(self, tip_rack: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., tip_pickup_method: _Optional[_Union[_types_pb2.Head96TipPickupMethod, str]] = ..., minimum_traverse_height_end: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., channel: _Optional[str] = ..., tip_spot: _Optional[str] = ...) -> None: ...

class Head96PickUpTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DropTipsRequest(_message.Message):
    __slots__ = ("resource", "offset", "minimum_traverse_height_end", "minimum_traverse_height_start", "channel", "tip_spot")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    TIP_SPOT_FIELD_NUMBER: _ClassVar[int]
    resource: _types_pb2_1.ResourceRef
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_end: float
    minimum_traverse_height_start: float
    channel: str
    tip_spot: str
    def __init__(self, resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_end: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., channel: _Optional[str] = ..., tip_spot: _Optional[str] = ...) -> None: ...

class Head96DropTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96ReturnTipsRequest(_message.Message):
    __slots__ = ("offset", "minimum_traverse_height_end", "minimum_traverse_height_start", "channel", "tip_spot")
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    TIP_SPOT_FIELD_NUMBER: _ClassVar[int]
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_end: float
    minimum_traverse_height_start: float
    channel: str
    tip_spot: str
    def __init__(self, offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_end: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., channel: _Optional[str] = ..., tip_spot: _Optional[str] = ...) -> None: ...

class Head96ReturnTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DiscardTipsRequest(_message.Message):
    __slots__ = ("offset", "minimum_traverse_height_end", "minimum_traverse_height_start", "channel", "tip_spot")
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    TIP_SPOT_FIELD_NUMBER: _ClassVar[int]
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_end: float
    minimum_traverse_height_start: float
    channel: str
    tip_spot: str
    def __init__(self, offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_end: _Optional[float] = ..., minimum_traverse_height_start: _Optional[float] = ..., channel: _Optional[str] = ..., tip_spot: _Optional[str] = ...) -> None: ...

class Head96DiscardTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96RequestLastLldZPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96RequestLastLldZPositionResponse(_message.Message):
    __slots__ = ("last_lld_z_position",)
    LAST_LLD_Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    last_lld_z_position: float
    def __init__(self, last_lld_z_position: _Optional[float] = ...) -> None: ...

class Head96ProbeZUsingClldRequest(_message.Message):
    __slots__ = ("search_start_position", "search_end_position", "tip_overhang", "approach_speed", "search_speed", "acceleration", "current_limit", "lld_sensor", "detection_edge", "detection_drop", "post_detection_trajectory", "post_detection_distance", "limit_immersion_to_search_end", "move_to_safe_z_position_after")
    SEARCH_START_POSITION_FIELD_NUMBER: _ClassVar[int]
    SEARCH_END_POSITION_FIELD_NUMBER: _ClassVar[int]
    TIP_OVERHANG_FIELD_NUMBER: _ClassVar[int]
    APPROACH_SPEED_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSOR_FIELD_NUMBER: _ClassVar[int]
    DETECTION_EDGE_FIELD_NUMBER: _ClassVar[int]
    DETECTION_DROP_FIELD_NUMBER: _ClassVar[int]
    POST_DETECTION_TRAJECTORY_FIELD_NUMBER: _ClassVar[int]
    POST_DETECTION_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_IMMERSION_TO_SEARCH_END_FIELD_NUMBER: _ClassVar[int]
    MOVE_TO_SAFE_Z_POSITION_AFTER_FIELD_NUMBER: _ClassVar[int]
    search_start_position: float
    search_end_position: float
    tip_overhang: float
    approach_speed: float
    search_speed: float
    acceleration: float
    current_limit: int
    lld_sensor: _types_pb2.LLDSensor
    detection_edge: int
    detection_drop: int
    post_detection_trajectory: int
    post_detection_distance: float
    limit_immersion_to_search_end: bool
    move_to_safe_z_position_after: bool
    def __init__(self, search_start_position: _Optional[float] = ..., search_end_position: _Optional[float] = ..., tip_overhang: _Optional[float] = ..., approach_speed: _Optional[float] = ..., search_speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ..., lld_sensor: _Optional[_Union[_types_pb2.LLDSensor, str]] = ..., detection_edge: _Optional[int] = ..., detection_drop: _Optional[int] = ..., post_detection_trajectory: _Optional[int] = ..., post_detection_distance: _Optional[float] = ..., limit_immersion_to_search_end: _Optional[bool] = ..., move_to_safe_z_position_after: _Optional[bool] = ...) -> None: ...

class Head96ProbeZUsingClldResponse(_message.Message):
    __slots__ = ("height",)
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    height: float
    def __init__(self, height: _Optional[float] = ...) -> None: ...

class Head96ProbeLiquidHeightRequest(_message.Message):
    __slots__ = ("resource_resource", "resource_each", "offset", "lld_sensor", "search_speed", "n_replicates", "minimum_traverse_height_start", "minimum_traverse_height_end")
    RESOURCE_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_EACH_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSOR_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    N_REPLICATES_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    resource_resource: _types_pb2_1.ResourceRef
    resource_each: _types_pb2.ResourceRefList
    offset: _types_pb2_1.Vec3
    lld_sensor: _types_pb2.LLDSensor
    search_speed: float
    n_replicates: int
    minimum_traverse_height_start: float
    minimum_traverse_height_end: float
    def __init__(self, resource_resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., resource_each: _Optional[_Union[_types_pb2.ResourceRefList, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., lld_sensor: _Optional[_Union[_types_pb2.LLDSensor, str]] = ..., search_speed: _Optional[float] = ..., n_replicates: _Optional[int] = ..., minimum_traverse_height_start: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class Head96ProbeLiquidHeightResponse(_message.Message):
    __slots__ = ("height",)
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    height: float
    def __init__(self, height: _Optional[float] = ...) -> None: ...

class Head96ProbeLiquidVolumeRequest(_message.Message):
    __slots__ = ("resource_resource", "resource_each", "offset", "lld_sensor", "search_speed", "n_replicates", "minimum_traverse_height_start", "minimum_traverse_height_end")
    RESOURCE_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_EACH_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSOR_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    N_REPLICATES_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    resource_resource: _types_pb2_1.ResourceRef
    resource_each: _types_pb2.ResourceRefList
    offset: _types_pb2_1.Vec3
    lld_sensor: _types_pb2.LLDSensor
    search_speed: float
    n_replicates: int
    minimum_traverse_height_start: float
    minimum_traverse_height_end: float
    def __init__(self, resource_resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., resource_each: _Optional[_Union[_types_pb2.ResourceRefList, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., lld_sensor: _Optional[_Union[_types_pb2.LLDSensor, str]] = ..., search_speed: _Optional[float] = ..., n_replicates: _Optional[int] = ..., minimum_traverse_height_start: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class Head96ProbeLiquidVolumeResponse(_message.Message):
    __slots__ = ("volume",)
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    volume: float
    def __init__(self, volume: _Optional[float] = ...) -> None: ...

class Head96AspirateRequest(_message.Message):
    __slots__ = ("resource_resource", "resource_each", "volume", "offset", "liquid_height", "lld_mode", "flow_rate", "hamilton_liquid_class", "jet", "blow_out", "piston_volume", "lld_sensor", "search_speed", "approach_speed", "blow_out_air_volume", "immersion_depth", "minimum_allowed_z_position_during", "pre_wetting_volume", "pre_mix", "mix_position_from_liquid_surface", "surface_following_distance", "auto_surface_following", "second_section_height", "second_section_ratio", "settling_time", "swap_speed", "pull_out_distance_transport_air", "transport_air_volume", "limit_curve_index", "minimum_traverse_height_start", "minimum_traverse_height_end")
    RESOURCE_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_EACH_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    HAMILTON_LIQUID_CLASS_FIELD_NUMBER: _ClassVar[int]
    JET_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_FIELD_NUMBER: _ClassVar[int]
    PISTON_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSOR_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    APPROACH_SPEED_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_ALLOWED_Z_POSITION_DURING_FIELD_NUMBER: _ClassVar[int]
    PRE_WETTING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    PRE_MIX_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    AUTO_SURFACE_FOLLOWING_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    resource_resource: _types_pb2_1.ResourceRef
    resource_each: _types_pb2.ResourceRefList
    volume: float
    offset: _types_pb2_1.Vec3
    liquid_height: float
    lld_mode: _types_pb2.LLDMode
    flow_rate: float
    hamilton_liquid_class: _types_pb2.LiquidClass
    jet: bool
    blow_out: bool
    piston_volume: float
    lld_sensor: _types_pb2.LLDSensor
    search_speed: float
    approach_speed: float
    blow_out_air_volume: float
    immersion_depth: float
    minimum_allowed_z_position_during: float
    pre_wetting_volume: float
    pre_mix: _types_pb2.Mix
    mix_position_from_liquid_surface: float
    surface_following_distance: float
    auto_surface_following: bool
    second_section_height: float
    second_section_ratio: float
    settling_time: float
    swap_speed: float
    pull_out_distance_transport_air: float
    transport_air_volume: float
    limit_curve_index: int
    minimum_traverse_height_start: float
    minimum_traverse_height_end: float
    def __init__(self, resource_resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., resource_each: _Optional[_Union[_types_pb2.ResourceRefList, _Mapping]] = ..., volume: _Optional[float] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., liquid_height: _Optional[float] = ..., lld_mode: _Optional[_Union[_types_pb2.LLDMode, str]] = ..., flow_rate: _Optional[float] = ..., hamilton_liquid_class: _Optional[_Union[_types_pb2.LiquidClass, _Mapping]] = ..., jet: _Optional[bool] = ..., blow_out: _Optional[bool] = ..., piston_volume: _Optional[float] = ..., lld_sensor: _Optional[_Union[_types_pb2.LLDSensor, str]] = ..., search_speed: _Optional[float] = ..., approach_speed: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., immersion_depth: _Optional[float] = ..., minimum_allowed_z_position_during: _Optional[float] = ..., pre_wetting_volume: _Optional[float] = ..., pre_mix: _Optional[_Union[_types_pb2.Mix, _Mapping]] = ..., mix_position_from_liquid_surface: _Optional[float] = ..., surface_following_distance: _Optional[float] = ..., auto_surface_following: _Optional[bool] = ..., second_section_height: _Optional[float] = ..., second_section_ratio: _Optional[float] = ..., settling_time: _Optional[float] = ..., swap_speed: _Optional[float] = ..., pull_out_distance_transport_air: _Optional[float] = ..., transport_air_volume: _Optional[float] = ..., limit_curve_index: _Optional[int] = ..., minimum_traverse_height_start: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class Head96AspirateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispenseRequest(_message.Message):
    __slots__ = ("resource_resource", "resource_each", "volume", "offset", "liquid_height", "lld_mode", "flow_rate", "hamilton_liquid_class", "jet", "blow_out", "empty", "piston_volume", "lld_sensor", "search_speed", "approach_speed", "side_touch_off_distance", "immersion_depth", "minimum_allowed_z_position_during", "transport_air_volume", "cut_off_speed", "stop_back_volume", "surface_following_distance", "auto_surface_following", "second_section_height", "second_section_ratio", "blow_out_air_volume", "post_mix", "mix_position_from_liquid_surface", "settling_time", "swap_speed", "pull_out_distance_transport_air", "limit_curve_index", "minimum_traverse_height_start", "minimum_traverse_height_end")
    RESOURCE_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_EACH_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    HAMILTON_LIQUID_CLASS_FIELD_NUMBER: _ClassVar[int]
    JET_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    PISTON_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSOR_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    APPROACH_SPEED_FIELD_NUMBER: _ClassVar[int]
    SIDE_TOUCH_OFF_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_ALLOWED_Z_POSITION_DURING_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    CUT_OFF_SPEED_FIELD_NUMBER: _ClassVar[int]
    STOP_BACK_VOLUME_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    AUTO_SURFACE_FOLLOWING_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    POST_MIX_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    resource_resource: _types_pb2_1.ResourceRef
    resource_each: _types_pb2.ResourceRefList
    volume: float
    offset: _types_pb2_1.Vec3
    liquid_height: float
    lld_mode: _types_pb2.LLDMode
    flow_rate: float
    hamilton_liquid_class: _types_pb2.LiquidClass
    jet: bool
    blow_out: bool
    empty: bool
    piston_volume: float
    lld_sensor: _types_pb2.LLDSensor
    search_speed: float
    approach_speed: float
    side_touch_off_distance: float
    immersion_depth: float
    minimum_allowed_z_position_during: float
    transport_air_volume: float
    cut_off_speed: float
    stop_back_volume: float
    surface_following_distance: float
    auto_surface_following: bool
    second_section_height: float
    second_section_ratio: float
    blow_out_air_volume: float
    post_mix: _types_pb2.Mix
    mix_position_from_liquid_surface: float
    settling_time: float
    swap_speed: float
    pull_out_distance_transport_air: float
    limit_curve_index: int
    minimum_traverse_height_start: float
    minimum_traverse_height_end: float
    def __init__(self, resource_resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., resource_each: _Optional[_Union[_types_pb2.ResourceRefList, _Mapping]] = ..., volume: _Optional[float] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., liquid_height: _Optional[float] = ..., lld_mode: _Optional[_Union[_types_pb2.LLDMode, str]] = ..., flow_rate: _Optional[float] = ..., hamilton_liquid_class: _Optional[_Union[_types_pb2.LiquidClass, _Mapping]] = ..., jet: _Optional[bool] = ..., blow_out: _Optional[bool] = ..., empty: _Optional[bool] = ..., piston_volume: _Optional[float] = ..., lld_sensor: _Optional[_Union[_types_pb2.LLDSensor, str]] = ..., search_speed: _Optional[float] = ..., approach_speed: _Optional[float] = ..., side_touch_off_distance: _Optional[float] = ..., immersion_depth: _Optional[float] = ..., minimum_allowed_z_position_during: _Optional[float] = ..., transport_air_volume: _Optional[float] = ..., cut_off_speed: _Optional[float] = ..., stop_back_volume: _Optional[float] = ..., surface_following_distance: _Optional[float] = ..., auto_surface_following: _Optional[bool] = ..., second_section_height: _Optional[float] = ..., second_section_ratio: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., post_mix: _Optional[_Union[_types_pb2.Mix, _Mapping]] = ..., mix_position_from_liquid_surface: _Optional[float] = ..., settling_time: _Optional[float] = ..., swap_speed: _Optional[float] = ..., pull_out_distance_transport_air: _Optional[float] = ..., limit_curve_index: _Optional[int] = ..., minimum_traverse_height_start: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class Head96DispenseResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MixRequest(_message.Message):
    __slots__ = ("resource_resource", "resource_each", "mix", "offset", "minimum_traverse_height_start", "lld_mode", "lld_sensor", "search_speed", "descent_speed", "blow_out_air_volume", "mix_position_from_liquid_surface", "swap_speed", "settling_time", "minimum_traverse_height_end")
    RESOURCE_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_EACH_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_START_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    LLD_SENSOR_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    DESCENT_SPEED_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_END_FIELD_NUMBER: _ClassVar[int]
    resource_resource: _types_pb2_1.ResourceRef
    resource_each: _types_pb2.ResourceRefList
    mix: _types_pb2.Mix
    offset: _types_pb2_1.Vec3
    minimum_traverse_height_start: float
    lld_mode: _types_pb2.LLDMode
    lld_sensor: _types_pb2.LLDSensor
    search_speed: float
    descent_speed: float
    blow_out_air_volume: float
    mix_position_from_liquid_surface: float
    swap_speed: float
    settling_time: float
    minimum_traverse_height_end: float
    def __init__(self, resource_resource: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., resource_each: _Optional[_Union[_types_pb2.ResourceRefList, _Mapping]] = ..., mix: _Optional[_Union[_types_pb2.Mix, _Mapping]] = ..., offset: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., minimum_traverse_height_start: _Optional[float] = ..., lld_mode: _Optional[_Union[_types_pb2.LLDMode, str]] = ..., lld_sensor: _Optional[_Union[_types_pb2.LLDSensor, str]] = ..., search_speed: _Optional[float] = ..., descent_speed: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix_position_from_liquid_surface: _Optional[float] = ..., swap_speed: _Optional[float] = ..., settling_time: _Optional[float] = ..., minimum_traverse_height_end: _Optional[float] = ...) -> None: ...

class Head96MixResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96Settings(_message.Message):
    __slots__ = ("default_clld_search_speed", "default_clld_acceleration", "default_clld_detection_edge", "default_clld_detection_drop", "default_clld_post_detection_distance", "default_mix_descent_speed", "default_mix_swap_speed", "default_mix_blow_out_air_volume", "default_mix_position_from_liquid_surface", "default_aspirate_immersion_depth", "default_dispensing_drive_speed", "default_dispensing_drive_acceleration")
    DEFAULT_CLLD_SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CLLD_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CLLD_DETECTION_EDGE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CLLD_DETECTION_DROP_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CLLD_POST_DETECTION_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_MIX_DESCENT_SPEED_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_MIX_SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_MIX_BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_ASPIRATE_IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_DISPENSING_DRIVE_SPEED_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_DISPENSING_DRIVE_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    default_clld_search_speed: float
    default_clld_acceleration: float
    default_clld_detection_edge: int
    default_clld_detection_drop: int
    default_clld_post_detection_distance: float
    default_mix_descent_speed: float
    default_mix_swap_speed: float
    default_mix_blow_out_air_volume: float
    default_mix_position_from_liquid_surface: float
    default_aspirate_immersion_depth: float
    default_dispensing_drive_speed: float
    default_dispensing_drive_acceleration: float
    def __init__(self, default_clld_search_speed: _Optional[float] = ..., default_clld_acceleration: _Optional[float] = ..., default_clld_detection_edge: _Optional[int] = ..., default_clld_detection_drop: _Optional[int] = ..., default_clld_post_detection_distance: _Optional[float] = ..., default_mix_descent_speed: _Optional[float] = ..., default_mix_swap_speed: _Optional[float] = ..., default_mix_blow_out_air_volume: _Optional[float] = ..., default_mix_position_from_liquid_surface: _Optional[float] = ..., default_aspirate_immersion_depth: _Optional[float] = ..., default_dispensing_drive_speed: _Optional[float] = ..., default_dispensing_drive_acceleration: _Optional[float] = ...) -> None: ...
