from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AutoloadConfiguration(_message.Message):
    __slots__ = ("module", "firmware_version", "firmware_date", "autoload_type", "y_positions", "z_positions", "scanner_rotations", "barcode_reading_directions", "barcode_symbologies", "barcode_2d_symbologies", "scan_directions", "x_drive_mm_per_increment", "loading_indicators_installed", "initialization_track", "adjustment_date", "adjusted", "drive_zero_on_the_deck", "reference_point_from_sled_left_edge", "x_drive_range_increments", "x_drive_speed_range_increments", "x_drive_speed_default", "x_drive_acceleration_ramp_range", "x_drive_acceleration_ramp_default", "z_drive_mm_per_increment", "z_drive_range_increments", "z_drive_speed_range_increments", "z_drive_speed_default", "z_drive_acceleration_ramp_range", "z_drive_acceleration_ramp_default", "y_drive_mm_per_increment", "y_drive_range_increments", "y_drive_speed_range_increments", "y_drive_speed_default", "y_drive_acceleration_ramp_range", "y_drive_acceleration_ramp_default", "motor_current_limit_range", "motor_current_limit_default", "acceleration_ramp_increments_per_second_squared")
    class YPositionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class ZPositionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class ScannerRotationsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class BarcodeReadingDirectionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class ScanDirectionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    MODULE_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_DATE_FIELD_NUMBER: _ClassVar[int]
    AUTOLOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Z_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    SCANNER_ROTATIONS_FIELD_NUMBER: _ClassVar[int]
    BARCODE_READING_DIRECTIONS_FIELD_NUMBER: _ClassVar[int]
    BARCODE_SYMBOLOGIES_FIELD_NUMBER: _ClassVar[int]
    BARCODE_2D_SYMBOLOGIES_FIELD_NUMBER: _ClassVar[int]
    SCAN_DIRECTIONS_FIELD_NUMBER: _ClassVar[int]
    X_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    LOADING_INDICATORS_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    INITIALIZATION_TRACK_FIELD_NUMBER: _ClassVar[int]
    ADJUSTMENT_DATE_FIELD_NUMBER: _ClassVar[int]
    ADJUSTED_FIELD_NUMBER: _ClassVar[int]
    DRIVE_ZERO_ON_THE_DECK_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_POINT_FROM_SLED_LEFT_EDGE_FIELD_NUMBER: _ClassVar[int]
    X_DRIVE_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    X_DRIVE_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    X_DRIVE_SPEED_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    X_DRIVE_ACCELERATION_RAMP_RANGE_FIELD_NUMBER: _ClassVar[int]
    X_DRIVE_ACCELERATION_RAMP_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_SPEED_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_ACCELERATION_RAMP_RANGE_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_ACCELERATION_RAMP_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_SPEED_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_ACCELERATION_RAMP_RANGE_FIELD_NUMBER: _ClassVar[int]
    Y_DRIVE_ACCELERATION_RAMP_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    MOTOR_CURRENT_LIMIT_RANGE_FIELD_NUMBER: _ClassVar[int]
    MOTOR_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_RAMP_INCREMENTS_PER_SECOND_SQUARED_FIELD_NUMBER: _ClassVar[int]
    module: str
    firmware_version: str
    firmware_date: _types_pb2.Date
    autoload_type: str
    y_positions: _containers.ScalarMap[str, int]
    z_positions: _containers.ScalarMap[str, int]
    scanner_rotations: _containers.ScalarMap[str, int]
    barcode_reading_directions: _containers.ScalarMap[str, int]
    barcode_symbologies: _types_pb2.StringInt32Map
    barcode_2d_symbologies: _types_pb2.StringInt32Map
    scan_directions: _containers.ScalarMap[str, int]
    x_drive_mm_per_increment: float
    loading_indicators_installed: bool
    initialization_track: int
    adjustment_date: _types_pb2.Date
    adjusted: bool
    drive_zero_on_the_deck: float
    reference_point_from_sled_left_edge: float
    x_drive_range_increments: _types_pb2.Int32Range
    x_drive_speed_range_increments: _types_pb2.Int32Range
    x_drive_speed_default: int
    x_drive_acceleration_ramp_range: _types_pb2.Int32Range
    x_drive_acceleration_ramp_default: int
    z_drive_mm_per_increment: float
    z_drive_range_increments: _types_pb2.Int32Range
    z_drive_speed_range_increments: _types_pb2.Int32Range
    z_drive_speed_default: int
    z_drive_acceleration_ramp_range: _types_pb2.Int32Range
    z_drive_acceleration_ramp_default: int
    y_drive_mm_per_increment: float
    y_drive_range_increments: _types_pb2.Int32Range
    y_drive_speed_range_increments: _types_pb2.Int32Range
    y_drive_speed_default: int
    y_drive_acceleration_ramp_range: _types_pb2.Int32Range
    y_drive_acceleration_ramp_default: int
    motor_current_limit_range: _types_pb2.Int32Range
    motor_current_limit_default: int
    acceleration_ramp_increments_per_second_squared: int
    def __init__(self, module: _Optional[str] = ..., firmware_version: _Optional[str] = ..., firmware_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., autoload_type: _Optional[str] = ..., y_positions: _Optional[_Mapping[str, int]] = ..., z_positions: _Optional[_Mapping[str, int]] = ..., scanner_rotations: _Optional[_Mapping[str, int]] = ..., barcode_reading_directions: _Optional[_Mapping[str, int]] = ..., barcode_symbologies: _Optional[_Union[_types_pb2.StringInt32Map, _Mapping]] = ..., barcode_2d_symbologies: _Optional[_Union[_types_pb2.StringInt32Map, _Mapping]] = ..., scan_directions: _Optional[_Mapping[str, int]] = ..., x_drive_mm_per_increment: _Optional[float] = ..., loading_indicators_installed: _Optional[bool] = ..., initialization_track: _Optional[int] = ..., adjustment_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., adjusted: _Optional[bool] = ..., drive_zero_on_the_deck: _Optional[float] = ..., reference_point_from_sled_left_edge: _Optional[float] = ..., x_drive_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., x_drive_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., x_drive_speed_default: _Optional[int] = ..., x_drive_acceleration_ramp_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., x_drive_acceleration_ramp_default: _Optional[int] = ..., z_drive_mm_per_increment: _Optional[float] = ..., z_drive_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_drive_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_drive_speed_default: _Optional[int] = ..., z_drive_acceleration_ramp_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_drive_acceleration_ramp_default: _Optional[int] = ..., y_drive_mm_per_increment: _Optional[float] = ..., y_drive_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_drive_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_drive_speed_default: _Optional[int] = ..., y_drive_acceleration_ramp_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_drive_acceleration_ramp_default: _Optional[int] = ..., motor_current_limit_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., motor_current_limit_default: _Optional[int] = ..., acceleration_ramp_increments_per_second_squared: _Optional[int] = ...) -> None: ...

class AutoloadRequestFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestFirmwareVersionResponse(_message.Message):
    __slots__ = ("version", "date")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    version: str
    date: _types_pb2.Date
    def __init__(self, version: _Optional[str] = ..., date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ...) -> None: ...

class AutoloadRequestAutoloadTypeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestAutoloadTypeResponse(_message.Message):
    __slots__ = ("autoload_type",)
    AUTOLOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    autoload_type: str
    def __init__(self, autoload_type: _Optional[str] = ...) -> None: ...

class AutoloadRequestAdjustmentStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestAdjustmentStatusResponse(_message.Message):
    __slots__ = ("adjustment_date", "adjusted")
    ADJUSTMENT_DATE_FIELD_NUMBER: _ClassVar[int]
    ADJUSTED_FIELD_NUMBER: _ClassVar[int]
    adjustment_date: _types_pb2.Date
    adjusted: bool
    def __init__(self, adjustment_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., adjusted: _Optional[bool] = ...) -> None: ...

class AutoloadRequestInitSlotRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestInitSlotResponse(_message.Message):
    __slots__ = ("init_slot",)
    INIT_SLOT_FIELD_NUMBER: _ClassVar[int]
    init_slot: int
    def __init__(self, init_slot: _Optional[int] = ...) -> None: ...

class AutoloadRequestAdjustmentValuesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestAdjustmentValuesResponse(_message.Message):
    __slots__ = ("adjustment_values",)
    ADJUSTMENT_VALUES_FIELD_NUMBER: _ClassVar[int]
    adjustment_values: str
    def __init__(self, adjustment_values: _Optional[str] = ...) -> None: ...

class AutoloadRequestModuleConfigurationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestModuleConfigurationResponse(_message.Message):
    __slots__ = ("scanner_mm_per_step", "loading_indicators_installed")
    SCANNER_MM_PER_STEP_FIELD_NUMBER: _ClassVar[int]
    LOADING_INDICATORS_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    scanner_mm_per_step: float
    loading_indicators_installed: bool
    def __init__(self, scanner_mm_per_step: _Optional[float] = ..., loading_indicators_installed: _Optional[bool] = ...) -> None: ...

class AutoloadRequestParameterRequest(_message.Message):
    __slots__ = ("parameter",)
    PARAMETER_FIELD_NUMBER: _ClassVar[int]
    parameter: str
    def __init__(self, parameter: _Optional[str] = ...) -> None: ...

class AutoloadRequestParameterResponse(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: str
    def __init__(self, value: _Optional[str] = ...) -> None: ...

class AutoloadRequestInitializationStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: _Optional[bool] = ...) -> None: ...

class AutoloadDiscoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadDiscoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadInitializeRequest(_message.Message):
    __slots__ = ("park_after",)
    PARK_AFTER_FIELD_NUMBER: _ClassVar[int]
    park_after: bool
    def __init__(self, park_after: _Optional[bool] = ...) -> None: ...

class AutoloadInitializeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestTrackRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestTrackResponse(_message.Message):
    __slots__ = ("track",)
    TRACK_FIELD_NUMBER: _ClassVar[int]
    track: int
    def __init__(self, track: _Optional[int] = ...) -> None: ...

class AutoloadRequestXPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestXPositionResponse(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: float
    def __init__(self, x_position: _Optional[float] = ...) -> None: ...

class AutoloadUpdateLocationByReferencePointRequest(_message.Message):
    __slots__ = ("x",)
    X_FIELD_NUMBER: _ClassVar[int]
    x: float
    def __init__(self, x: _Optional[float] = ...) -> None: ...

class AutoloadUpdateLocationByReferencePointResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadGetReferencePointXRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadGetReferencePointXResponse(_message.Message):
    __slots__ = ("reference_point_x",)
    REFERENCE_POINT_X_FIELD_NUMBER: _ClassVar[int]
    reference_point_x: float
    def __init__(self, reference_point_x: _Optional[float] = ...) -> None: ...

class AutoloadMoveToTrackRequest(_message.Message):
    __slots__ = ("track", "speed", "acceleration_ramp", "current_limit")
    TRACK_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_RAMP_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    track: int
    speed: float
    acceleration_ramp: int
    current_limit: int
    def __init__(self, track: _Optional[int] = ..., speed: _Optional[float] = ..., acceleration_ramp: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class AutoloadMoveToTrackResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadMoveToXPositionRequest(_message.Message):
    __slots__ = ("x", "speed", "acceleration_ramp", "current_limit")
    X_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_RAMP_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    x: float
    speed: float
    acceleration_ramp: int
    current_limit: int
    def __init__(self, x: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration_ramp: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class AutoloadMoveToXPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadMoveXRelativeRequest(_message.Message):
    __slots__ = ("distance", "speed", "acceleration_ramp", "current_limit")
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_RAMP_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    distance: float
    speed: float
    acceleration_ramp: int
    current_limit: int
    def __init__(self, distance: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration_ramp: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class AutoloadMoveXRelativeResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadParkRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadParkResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadWheelRequestZPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadWheelRequestZPositionResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class AutoloadWheelIsAtSafeZRequest(_message.Message):
    __slots__ = ("tolerance",)
    TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    tolerance: float
    def __init__(self, tolerance: _Optional[float] = ...) -> None: ...

class AutoloadWheelIsAtSafeZResponse(_message.Message):
    __slots__ = ("at_safe_z",)
    AT_SAFE_Z_FIELD_NUMBER: _ClassVar[int]
    at_safe_z: bool
    def __init__(self, at_safe_z: _Optional[bool] = ...) -> None: ...

class AutoloadWheelMoveToSafeZRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadWheelMoveToSafeZResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class AutoloadWheelMoveToZPositionRequest(_message.Message):
    __slots__ = ("z_value", "z_named", "speed", "acceleration_ramp", "current_limit")
    Z_VALUE_FIELD_NUMBER: _ClassVar[int]
    Z_NAMED_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_RAMP_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    z_value: float
    z_named: _types_pb2.WheelZPosition
    speed: float
    acceleration_ramp: int
    current_limit: int
    def __init__(self, z_value: _Optional[float] = ..., z_named: _Optional[_Union[_types_pb2.WheelZPosition, str]] = ..., speed: _Optional[float] = ..., acceleration_ramp: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class AutoloadWheelMoveToZPositionResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class AutoloadWheelRequestYPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadWheelRequestYPositionResponse(_message.Message):
    __slots__ = ("y_position",)
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    y_position: float
    def __init__(self, y_position: _Optional[float] = ...) -> None: ...

class AutoloadWheelMoveToYPositionRequest(_message.Message):
    __slots__ = ("y_value", "y_named", "speed", "acceleration_ramp", "current_limit")
    Y_VALUE_FIELD_NUMBER: _ClassVar[int]
    Y_NAMED_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_RAMP_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    y_value: float
    y_named: _types_pb2.WheelYPosition
    speed: float
    acceleration_ramp: int
    current_limit: int
    def __init__(self, y_value: _Optional[float] = ..., y_named: _Optional[_Union[_types_pb2.WheelYPosition, str]] = ..., speed: _Optional[float] = ..., acceleration_ramp: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class AutoloadWheelMoveToYPositionResponse(_message.Message):
    __slots__ = ("y_position",)
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    y_position: float
    def __init__(self, y_position: _Optional[float] = ...) -> None: ...

class AutoloadScannerRequestRotationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadScannerRequestRotationResponse(_message.Message):
    __slots__ = ("rotation",)
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    rotation: _types_pb2.ScannerRotation
    def __init__(self, rotation: _Optional[_Union[_types_pb2.ScannerRotation, str]] = ...) -> None: ...

class AutoloadScannerMoveToPositionRequest(_message.Message):
    __slots__ = ("position", "stop_torque")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    STOP_TORQUE_FIELD_NUMBER: _ClassVar[int]
    position: _types_pb2.ScannerRotation
    stop_torque: bool
    def __init__(self, position: _Optional[_Union[_types_pb2.ScannerRotation, str]] = ..., stop_torque: _Optional[bool] = ...) -> None: ...

class AutoloadScannerMoveToPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadSenseCarrierPresenceOnDeckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadSenseCarrierPresenceOnDeckResponse(_message.Message):
    __slots__ = ("tracks",)
    TRACKS_FIELD_NUMBER: _ClassVar[int]
    tracks: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, tracks: _Optional[_Iterable[int]] = ...) -> None: ...

class AutoloadSenseCarrierPresenceOnSingleLoadingTrayTrackRequest(_message.Message):
    __slots__ = ("track", "park_after")
    TRACK_FIELD_NUMBER: _ClassVar[int]
    PARK_AFTER_FIELD_NUMBER: _ClassVar[int]
    track: int
    park_after: bool
    def __init__(self, track: _Optional[int] = ..., park_after: _Optional[bool] = ...) -> None: ...

class AutoloadSenseCarrierPresenceOnSingleLoadingTrayTrackResponse(_message.Message):
    __slots__ = ("present",)
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    present: bool
    def __init__(self, present: _Optional[bool] = ...) -> None: ...

class AutoloadSenseCarrierPresenceOnLoadingTrayRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadSenseCarrierPresenceOnLoadingTrayResponse(_message.Message):
    __slots__ = ("tracks",)
    TRACKS_FIELD_NUMBER: _ClassVar[int]
    tracks: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, tracks: _Optional[_Iterable[int]] = ...) -> None: ...

class AutoloadRequestLatestBarcodeReadRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadRequestLatestBarcodeReadResponse(_message.Message):
    __slots__ = ("latest_barcode_read",)
    LATEST_BARCODE_READ_FIELD_NUMBER: _ClassVar[int]
    latest_barcode_read: str
    def __init__(self, latest_barcode_read: _Optional[str] = ...) -> None: ...

class AutoloadSetBarcodeScannerEnabledRequest(_message.Message):
    __slots__ = ("enabled", "symbologies", "symbologies_2d", "scan_direction")
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    SYMBOLOGIES_FIELD_NUMBER: _ClassVar[int]
    SYMBOLOGIES_2D_FIELD_NUMBER: _ClassVar[int]
    SCAN_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    symbologies: _types_pb2.BarcodeSymbologyList
    symbologies_2d: _types_pb2.Barcode2DSymbologyList
    scan_direction: _types_pb2.ScanDirection
    def __init__(self, enabled: _Optional[bool] = ..., symbologies: _Optional[_Union[_types_pb2.BarcodeSymbologyList, _Mapping]] = ..., symbologies_2d: _Optional[_Union[_types_pb2.Barcode2DSymbologyList, _Mapping]] = ..., scan_direction: _Optional[_Union[_types_pb2.ScanDirection, str]] = ...) -> None: ...

class AutoloadSetBarcodeScannerEnabledResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadResetBarcodeScannerRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadResetBarcodeScannerResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadSetBarcodeSymbologiesRequest(_message.Message):
    __slots__ = ("symbologies",)
    SYMBOLOGIES_FIELD_NUMBER: _ClassVar[int]
    symbologies: _containers.RepeatedScalarFieldContainer[_types_pb2.BarcodeSymbology]
    def __init__(self, symbologies: _Optional[_Iterable[_Union[_types_pb2.BarcodeSymbology, str]]] = ...) -> None: ...

class AutoloadSetBarcodeSymbologiesResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadLoadCarrierFromTrayAndScanCarrierBarcodeRequest(_message.Message):
    __slots__ = ("track", "barcode_position", "barcode_reading_window_width", "reading_speed")
    TRACK_FIELD_NUMBER: _ClassVar[int]
    BARCODE_POSITION_FIELD_NUMBER: _ClassVar[int]
    BARCODE_READING_WINDOW_WIDTH_FIELD_NUMBER: _ClassVar[int]
    READING_SPEED_FIELD_NUMBER: _ClassVar[int]
    track: int
    barcode_position: float
    barcode_reading_window_width: float
    reading_speed: float
    def __init__(self, track: _Optional[int] = ..., barcode_position: _Optional[float] = ..., barcode_reading_window_width: _Optional[float] = ..., reading_speed: _Optional[float] = ...) -> None: ...

class AutoloadLoadCarrierFromTrayAndScanCarrierBarcodeResponse(_message.Message):
    __slots__ = ("barcode",)
    BARCODE_FIELD_NUMBER: _ClassVar[int]
    barcode: str
    def __init__(self, barcode: _Optional[str] = ...) -> None: ...

class AutoloadUnloadCarrierAfterCarrierBarcodeScanningRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadUnloadCarrierAfterCarrierBarcodeScanningResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadTakeCarrierOutToAutoloadBeltRequest(_message.Message):
    __slots__ = ("track",)
    TRACK_FIELD_NUMBER: _ClassVar[int]
    track: int
    def __init__(self, track: _Optional[int] = ...) -> None: ...

class AutoloadTakeCarrierOutToAutoloadBeltResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadLoadCarrierFromAutoloadBeltRequest(_message.Message):
    __slots__ = ("barcode_reading", "barcode_reading_direction", "reading_position_of_first_barcode", "containers_per_carrier", "distance_between_containers", "width_of_reading_window", "reading_speed", "park_after")
    BARCODE_READING_FIELD_NUMBER: _ClassVar[int]
    BARCODE_READING_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    READING_POSITION_OF_FIRST_BARCODE_FIELD_NUMBER: _ClassVar[int]
    CONTAINERS_PER_CARRIER_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_BETWEEN_CONTAINERS_FIELD_NUMBER: _ClassVar[int]
    WIDTH_OF_READING_WINDOW_FIELD_NUMBER: _ClassVar[int]
    READING_SPEED_FIELD_NUMBER: _ClassVar[int]
    PARK_AFTER_FIELD_NUMBER: _ClassVar[int]
    barcode_reading: bool
    barcode_reading_direction: _types_pb2.BarcodeReadingDirection
    reading_position_of_first_barcode: float
    containers_per_carrier: int
    distance_between_containers: float
    width_of_reading_window: float
    reading_speed: float
    park_after: bool
    def __init__(self, barcode_reading: _Optional[bool] = ..., barcode_reading_direction: _Optional[_Union[_types_pb2.BarcodeReadingDirection, str]] = ..., reading_position_of_first_barcode: _Optional[float] = ..., containers_per_carrier: _Optional[int] = ..., distance_between_containers: _Optional[float] = ..., width_of_reading_window: _Optional[float] = ..., reading_speed: _Optional[float] = ..., park_after: _Optional[bool] = ...) -> None: ...

class AutoloadLoadCarrierFromAutoloadBeltResponse(_message.Message):
    __slots__ = ("container_barcodes",)
    class ContainerBarcodesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: _types_pb2.OptionalString
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[_types_pb2.OptionalString, _Mapping]] = ...) -> None: ...
    CONTAINER_BARCODES_FIELD_NUMBER: _ClassVar[int]
    container_barcodes: _containers.MessageMap[int, _types_pb2.OptionalString]
    def __init__(self, container_barcodes: _Optional[_Mapping[int, _types_pb2.OptionalString]] = ...) -> None: ...

class AutoloadUnloadCarrierRequest(_message.Message):
    __slots__ = ("carrier", "use_loading_indicators", "perform_deck_presence_check", "perform_tray_presence_check", "park_after")
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    USE_LOADING_INDICATORS_FIELD_NUMBER: _ClassVar[int]
    PERFORM_DECK_PRESENCE_CHECK_FIELD_NUMBER: _ClassVar[int]
    PERFORM_TRAY_PRESENCE_CHECK_FIELD_NUMBER: _ClassVar[int]
    PARK_AFTER_FIELD_NUMBER: _ClassVar[int]
    carrier: _types_pb2_1.ResourceRef
    use_loading_indicators: bool
    perform_deck_presence_check: bool
    perform_tray_presence_check: bool
    park_after: bool
    def __init__(self, carrier: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., use_loading_indicators: _Optional[bool] = ..., perform_deck_presence_check: _Optional[bool] = ..., perform_tray_presence_check: _Optional[bool] = ..., park_after: _Optional[bool] = ...) -> None: ...

class AutoloadUnloadCarrierResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadUnloadCarrierFinallyRequest(_message.Message):
    __slots__ = ("track", "park_after")
    TRACK_FIELD_NUMBER: _ClassVar[int]
    PARK_AFTER_FIELD_NUMBER: _ClassVar[int]
    track: int
    park_after: bool
    def __init__(self, track: _Optional[int] = ..., park_after: _Optional[bool] = ...) -> None: ...

class AutoloadUnloadCarrierFinallyResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class AutoloadLoadCarrierRequest(_message.Message):
    __slots__ = ("carrier", "carrier_barcode_reading", "barcode_reading", "barcode_reading_direction", "containers_per_carrier", "reading_position_of_first_barcode", "distance_between_containers", "width_of_reading_window", "reading_speed", "park_after")
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    CARRIER_BARCODE_READING_FIELD_NUMBER: _ClassVar[int]
    BARCODE_READING_FIELD_NUMBER: _ClassVar[int]
    BARCODE_READING_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    CONTAINERS_PER_CARRIER_FIELD_NUMBER: _ClassVar[int]
    READING_POSITION_OF_FIRST_BARCODE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_BETWEEN_CONTAINERS_FIELD_NUMBER: _ClassVar[int]
    WIDTH_OF_READING_WINDOW_FIELD_NUMBER: _ClassVar[int]
    READING_SPEED_FIELD_NUMBER: _ClassVar[int]
    PARK_AFTER_FIELD_NUMBER: _ClassVar[int]
    carrier: _types_pb2_1.ResourceRef
    carrier_barcode_reading: bool
    barcode_reading: bool
    barcode_reading_direction: _types_pb2.BarcodeReadingDirection
    containers_per_carrier: int
    reading_position_of_first_barcode: float
    distance_between_containers: float
    width_of_reading_window: float
    reading_speed: float
    park_after: bool
    def __init__(self, carrier: _Optional[_Union[_types_pb2_1.ResourceRef, _Mapping]] = ..., carrier_barcode_reading: _Optional[bool] = ..., barcode_reading: _Optional[bool] = ..., barcode_reading_direction: _Optional[_Union[_types_pb2.BarcodeReadingDirection, str]] = ..., containers_per_carrier: _Optional[int] = ..., reading_position_of_first_barcode: _Optional[float] = ..., distance_between_containers: _Optional[float] = ..., width_of_reading_window: _Optional[float] = ..., reading_speed: _Optional[float] = ..., park_after: _Optional[bool] = ...) -> None: ...

class AutoloadLoadCarrierResponse(_message.Message):
    __slots__ = ("carrier_barcode", "container_barcodes")
    class ContainerBarcodesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: _types_pb2.OptionalString
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[_types_pb2.OptionalString, _Mapping]] = ...) -> None: ...
    CARRIER_BARCODE_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_BARCODES_FIELD_NUMBER: _ClassVar[int]
    carrier_barcode: str
    container_barcodes: _containers.MessageMap[int, _types_pb2.OptionalString]
    def __init__(self, carrier_barcode: _Optional[str] = ..., container_barcodes: _Optional[_Mapping[int, _types_pb2.OptionalString]] = ...) -> None: ...

class AutoloadLightTracksRequest(_message.Message):
    __slots__ = ("tracks", "blinking")
    TRACKS_FIELD_NUMBER: _ClassVar[int]
    BLINKING_FIELD_NUMBER: _ClassVar[int]
    tracks: _containers.RepeatedScalarFieldContainer[int]
    blinking: _types_pb2.BoolList
    def __init__(self, tracks: _Optional[_Iterable[int]] = ..., blinking: _Optional[_Union[_types_pb2.BoolList, _Mapping]] = ...) -> None: ...

class AutoloadLightTracksResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadClearLoadingIndicatorsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadClearLoadingIndicatorsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AutoloadSetLoadingIndicatorsRequest(_message.Message):
    __slots__ = ("lit", "blinking")
    LIT_FIELD_NUMBER: _ClassVar[int]
    BLINKING_FIELD_NUMBER: _ClassVar[int]
    lit: _containers.RepeatedScalarFieldContainer[bool]
    blinking: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, lit: _Optional[_Iterable[bool]] = ..., blinking: _Optional[_Iterable[bool]] = ...) -> None: ...

class AutoloadSetLoadingIndicatorsResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...
