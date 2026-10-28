from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.hamilton.star.server.v1 import x_arm_pb2 as _x_arm_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceConfiguration(_message.Message):
    __slots__ = ("serial_number", "firmware_version", "firmware_date", "pip_type_1000ul", "kb_iswap_installed", "main_front_cover_monitoring_installed", "autoload_installed", "wash_station_1_installed", "wash_station_2_installed", "temp_controlled_carrier_1_installed", "temp_controlled_carrier_2_installed", "num_pip_channels", "left_x_drive_large", "head96_installed", "right_x_drive_large", "pump_station_1_installed", "pump_station_2_installed", "wash_station_1_type_cr", "wash_station_2_type_cr", "left_cover_installed", "right_cover_installed", "additional_front_cover_monitoring_installed", "pump_station_3_installed", "multi_channel_nano_pipettor_installed", "head384_installed", "xl_channels_installed", "tube_gripper_installed", "waste_direction_left", "iswap_gripper_wide", "additional_channel_nano_pipettor_installed", "imaging_channel_installed", "robotic_channel_installed", "channel_order_ox_first", "x0_interface_ham_can", "park_heads_with_iswap_off", "configuration_data_3", "instrument_size_slots", "autoload_size_slots", "tip_waste_x_position", "left_arm", "right_arm", "min_iswap_collision_free_position", "max_iswap_collision_free_position", "left_x_arm_width", "right_x_arm_width", "num_xl_channels", "num_robotic_channels", "min_raster_pitch_pip_channels", "min_raster_pitch_xl_channels", "min_raster_pitch_robotic_channels", "pip_maximal_y_position", "left_arm_min_y_position", "right_arm_min_y_position")
    SERIAL_NUMBER_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_DATE_FIELD_NUMBER: _ClassVar[int]
    PIP_TYPE_1000UL_FIELD_NUMBER: _ClassVar[int]
    KB_ISWAP_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    MAIN_FRONT_COVER_MONITORING_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    AUTOLOAD_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    WASH_STATION_1_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    WASH_STATION_2_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    TEMP_CONTROLLED_CARRIER_1_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    TEMP_CONTROLLED_CARRIER_2_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    NUM_PIP_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    LEFT_X_DRIVE_LARGE_FIELD_NUMBER: _ClassVar[int]
    HEAD96_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    RIGHT_X_DRIVE_LARGE_FIELD_NUMBER: _ClassVar[int]
    PUMP_STATION_1_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    PUMP_STATION_2_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    WASH_STATION_1_TYPE_CR_FIELD_NUMBER: _ClassVar[int]
    WASH_STATION_2_TYPE_CR_FIELD_NUMBER: _ClassVar[int]
    LEFT_COVER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    RIGHT_COVER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_FRONT_COVER_MONITORING_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    PUMP_STATION_3_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    MULTI_CHANNEL_NANO_PIPETTOR_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    HEAD384_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    XL_CHANNELS_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    TUBE_GRIPPER_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    WASTE_DIRECTION_LEFT_FIELD_NUMBER: _ClassVar[int]
    ISWAP_GRIPPER_WIDE_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_CHANNEL_NANO_PIPETTOR_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    IMAGING_CHANNEL_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    ROBOTIC_CHANNEL_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_ORDER_OX_FIRST_FIELD_NUMBER: _ClassVar[int]
    X0_INTERFACE_HAM_CAN_FIELD_NUMBER: _ClassVar[int]
    PARK_HEADS_WITH_ISWAP_OFF_FIELD_NUMBER: _ClassVar[int]
    CONFIGURATION_DATA_3_FIELD_NUMBER: _ClassVar[int]
    INSTRUMENT_SIZE_SLOTS_FIELD_NUMBER: _ClassVar[int]
    AUTOLOAD_SIZE_SLOTS_FIELD_NUMBER: _ClassVar[int]
    TIP_WASTE_X_POSITION_FIELD_NUMBER: _ClassVar[int]
    LEFT_ARM_FIELD_NUMBER: _ClassVar[int]
    RIGHT_ARM_FIELD_NUMBER: _ClassVar[int]
    MIN_ISWAP_COLLISION_FREE_POSITION_FIELD_NUMBER: _ClassVar[int]
    MAX_ISWAP_COLLISION_FREE_POSITION_FIELD_NUMBER: _ClassVar[int]
    LEFT_X_ARM_WIDTH_FIELD_NUMBER: _ClassVar[int]
    RIGHT_X_ARM_WIDTH_FIELD_NUMBER: _ClassVar[int]
    NUM_XL_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    NUM_ROBOTIC_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    MIN_RASTER_PITCH_PIP_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    MIN_RASTER_PITCH_XL_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    MIN_RASTER_PITCH_ROBOTIC_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    PIP_MAXIMAL_Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    LEFT_ARM_MIN_Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    RIGHT_ARM_MIN_Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    serial_number: str
    firmware_version: str
    firmware_date: _types_pb2.Date
    pip_type_1000ul: bool
    kb_iswap_installed: bool
    main_front_cover_monitoring_installed: bool
    autoload_installed: bool
    wash_station_1_installed: bool
    wash_station_2_installed: bool
    temp_controlled_carrier_1_installed: bool
    temp_controlled_carrier_2_installed: bool
    num_pip_channels: int
    left_x_drive_large: bool
    head96_installed: bool
    right_x_drive_large: bool
    pump_station_1_installed: bool
    pump_station_2_installed: bool
    wash_station_1_type_cr: bool
    wash_station_2_type_cr: bool
    left_cover_installed: bool
    right_cover_installed: bool
    additional_front_cover_monitoring_installed: bool
    pump_station_3_installed: bool
    multi_channel_nano_pipettor_installed: bool
    head384_installed: bool
    xl_channels_installed: bool
    tube_gripper_installed: bool
    waste_direction_left: bool
    iswap_gripper_wide: bool
    additional_channel_nano_pipettor_installed: bool
    imaging_channel_installed: bool
    robotic_channel_installed: bool
    channel_order_ox_first: bool
    x0_interface_ham_can: bool
    park_heads_with_iswap_off: bool
    configuration_data_3: int
    instrument_size_slots: int
    autoload_size_slots: int
    tip_waste_x_position: float
    left_arm: _x_arm_pb2.XArmConfiguration
    right_arm: _x_arm_pb2.XArmConfiguration
    min_iswap_collision_free_position: float
    max_iswap_collision_free_position: float
    left_x_arm_width: float
    right_x_arm_width: float
    num_xl_channels: int
    num_robotic_channels: int
    min_raster_pitch_pip_channels: float
    min_raster_pitch_xl_channels: float
    min_raster_pitch_robotic_channels: float
    pip_maximal_y_position: float
    left_arm_min_y_position: float
    right_arm_min_y_position: float
    def __init__(self, serial_number: _Optional[str] = ..., firmware_version: _Optional[str] = ..., firmware_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., pip_type_1000ul: _Optional[bool] = ..., kb_iswap_installed: _Optional[bool] = ..., main_front_cover_monitoring_installed: _Optional[bool] = ..., autoload_installed: _Optional[bool] = ..., wash_station_1_installed: _Optional[bool] = ..., wash_station_2_installed: _Optional[bool] = ..., temp_controlled_carrier_1_installed: _Optional[bool] = ..., temp_controlled_carrier_2_installed: _Optional[bool] = ..., num_pip_channels: _Optional[int] = ..., left_x_drive_large: _Optional[bool] = ..., head96_installed: _Optional[bool] = ..., right_x_drive_large: _Optional[bool] = ..., pump_station_1_installed: _Optional[bool] = ..., pump_station_2_installed: _Optional[bool] = ..., wash_station_1_type_cr: _Optional[bool] = ..., wash_station_2_type_cr: _Optional[bool] = ..., left_cover_installed: _Optional[bool] = ..., right_cover_installed: _Optional[bool] = ..., additional_front_cover_monitoring_installed: _Optional[bool] = ..., pump_station_3_installed: _Optional[bool] = ..., multi_channel_nano_pipettor_installed: _Optional[bool] = ..., head384_installed: _Optional[bool] = ..., xl_channels_installed: _Optional[bool] = ..., tube_gripper_installed: _Optional[bool] = ..., waste_direction_left: _Optional[bool] = ..., iswap_gripper_wide: _Optional[bool] = ..., additional_channel_nano_pipettor_installed: _Optional[bool] = ..., imaging_channel_installed: _Optional[bool] = ..., robotic_channel_installed: _Optional[bool] = ..., channel_order_ox_first: _Optional[bool] = ..., x0_interface_ham_can: _Optional[bool] = ..., park_heads_with_iswap_off: _Optional[bool] = ..., configuration_data_3: _Optional[int] = ..., instrument_size_slots: _Optional[int] = ..., autoload_size_slots: _Optional[int] = ..., tip_waste_x_position: _Optional[float] = ..., left_arm: _Optional[_Union[_x_arm_pb2.XArmConfiguration, _Mapping]] = ..., right_arm: _Optional[_Union[_x_arm_pb2.XArmConfiguration, _Mapping]] = ..., min_iswap_collision_free_position: _Optional[float] = ..., max_iswap_collision_free_position: _Optional[float] = ..., left_x_arm_width: _Optional[float] = ..., right_x_arm_width: _Optional[float] = ..., num_xl_channels: _Optional[int] = ..., num_robotic_channels: _Optional[int] = ..., min_raster_pitch_pip_channels: _Optional[float] = ..., min_raster_pitch_xl_channels: _Optional[float] = ..., min_raster_pitch_robotic_channels: _Optional[float] = ..., pip_maximal_y_position: _Optional[float] = ..., left_arm_min_y_position: _Optional[float] = ..., right_arm_min_y_position: _Optional[float] = ...) -> None: ...

class DriverSetupRequest(_message.Message):
    __slots__ = ("skip_device_initialization", "skip_pipettes", "skip_iswap", "skip_head96", "skip_head384", "skip_autoload")
    SKIP_DEVICE_INITIALIZATION_FIELD_NUMBER: _ClassVar[int]
    SKIP_PIPETTES_FIELD_NUMBER: _ClassVar[int]
    SKIP_ISWAP_FIELD_NUMBER: _ClassVar[int]
    SKIP_HEAD96_FIELD_NUMBER: _ClassVar[int]
    SKIP_HEAD384_FIELD_NUMBER: _ClassVar[int]
    SKIP_AUTOLOAD_FIELD_NUMBER: _ClassVar[int]
    skip_device_initialization: bool
    skip_pipettes: bool
    skip_iswap: bool
    skip_head96: bool
    skip_head384: bool
    skip_autoload: bool
    def __init__(self, skip_device_initialization: _Optional[bool] = ..., skip_pipettes: _Optional[bool] = ..., skip_iswap: _Optional[bool] = ..., skip_head96: _Optional[bool] = ..., skip_head384: _Optional[bool] = ..., skip_autoload: _Optional[bool] = ...) -> None: ...

class DriverSetupResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverFeaturesBelowSafeZRequest(_message.Message):
    __slots__ = ("tolerance",)
    TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    tolerance: float
    def __init__(self, tolerance: _Optional[float] = ...) -> None: ...

class DriverFeaturesBelowSafeZResponse(_message.Message):
    __slots__ = ("features",)
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    features: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, features: _Optional[_Iterable[str]] = ...) -> None: ...

class DriverStopRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverStopResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverSendCommandRequest(_message.Message):
    __slots__ = ("module", "command", "auto_id", "tip_pattern", "write_timeout", "read_timeout", "fmt", "subsystem", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MODULE_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    AUTO_ID_FIELD_NUMBER: _ClassVar[int]
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    WRITE_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    FMT_FIELD_NUMBER: _ClassVar[int]
    SUBSYSTEM_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    module: str
    command: str
    auto_id: bool
    tip_pattern: _types_pb2.BoolList
    write_timeout: int
    read_timeout: int
    fmt: str
    subsystem: str
    parameters: _containers.ScalarMap[str, str]
    def __init__(self, module: _Optional[str] = ..., command: _Optional[str] = ..., auto_id: _Optional[bool] = ..., tip_pattern: _Optional[_Union[_types_pb2.BoolList, _Mapping]] = ..., write_timeout: _Optional[int] = ..., read_timeout: _Optional[int] = ..., fmt: _Optional[str] = ..., subsystem: _Optional[str] = ..., parameters: _Optional[_Mapping[str, str]] = ...) -> None: ...

class DriverSendCommandResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class DriverSendRawCommandRequest(_message.Message):
    __slots__ = ("command", "write_timeout", "read_timeout", "wait")
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    WRITE_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    WAIT_FIELD_NUMBER: _ClassVar[int]
    command: str
    write_timeout: int
    read_timeout: int
    wait: bool
    def __init__(self, command: _Optional[str] = ..., write_timeout: _Optional[int] = ..., read_timeout: _Optional[int] = ..., wait: _Optional[bool] = ...) -> None: ...

class DriverSendRawCommandResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: str
    def __init__(self, reply: _Optional[str] = ...) -> None: ...

class DriverRequestDeviceSerialNumberRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverRequestDeviceSerialNumberResponse(_message.Message):
    __slots__ = ("serial_number",)
    SERIAL_NUMBER_FIELD_NUMBER: _ClassVar[int]
    serial_number: str
    def __init__(self, serial_number: _Optional[str] = ...) -> None: ...

class DriverRequestFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverRequestFirmwareVersionResponse(_message.Message):
    __slots__ = ("version", "date")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    version: str
    date: _types_pb2.Date
    def __init__(self, version: _Optional[str] = ..., date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ...) -> None: ...

class DriverRequestCoverInputStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverRequestCoverInputStatusResponse(_message.Message):
    __slots__ = ("input_1", "input_2", "input_3")
    INPUT_1_FIELD_NUMBER: _ClassVar[int]
    INPUT_2_FIELD_NUMBER: _ClassVar[int]
    INPUT_3_FIELD_NUMBER: _ClassVar[int]
    input_1: bool
    input_2: bool
    input_3: bool
    def __init__(self, input_1: _Optional[bool] = ..., input_2: _Optional[bool] = ..., input_3: _Optional[bool] = ...) -> None: ...

class DriverRequestMaximalRangesOfXDrivesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverRequestMaximalRangesOfXDrivesResponse(_message.Message):
    __slots__ = ("maximal_ranges_of_x_drives",)
    class MaximalRangesOfXDrivesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _types_pb2.DoubleRange
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_types_pb2.DoubleRange, _Mapping]] = ...) -> None: ...
    MAXIMAL_RANGES_OF_X_DRIVES_FIELD_NUMBER: _ClassVar[int]
    maximal_ranges_of_x_drives: _containers.MessageMap[str, _types_pb2.DoubleRange]
    def __init__(self, maximal_ranges_of_x_drives: _Optional[_Mapping[str, _types_pb2.DoubleRange]] = ...) -> None: ...

class DriverRequestWorkingEnvelopesPerArmRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverRequestWorkingEnvelopesPerArmResponse(_message.Message):
    __slots__ = ("working_envelopes_per_arm",)
    class WorkingEnvelopesPerArmEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _types_pb2.WorkingEnvelope
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_types_pb2.WorkingEnvelope, _Mapping]] = ...) -> None: ...
    WORKING_ENVELOPES_PER_ARM_FIELD_NUMBER: _ClassVar[int]
    working_envelopes_per_arm: _containers.MessageMap[str, _types_pb2.WorkingEnvelope]
    def __init__(self, working_envelopes_per_arm: _Optional[_Mapping[str, _types_pb2.WorkingEnvelope]] = ...) -> None: ...

class DriverRequestDeviceConfigurationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverRequestDeviceConfigurationResponse(_message.Message):
    __slots__ = ("configuration",)
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    configuration: DeviceConfiguration
    def __init__(self, configuration: _Optional[_Union[DeviceConfiguration, _Mapping]] = ...) -> None: ...

class DriverRequestInitializationStatusRequest(_message.Message):
    __slots__ = ("module",)
    MODULE_FIELD_NUMBER: _ClassVar[int]
    module: str
    def __init__(self, module: _Optional[str] = ...) -> None: ...

class DriverRequestInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: _Optional[bool] = ...) -> None: ...

class DriverDefineTipNeedleRequest(_message.Message):
    __slots__ = ("tip_type_table_index", "has_filter", "tip_length", "maximum_tip_volume", "tip_size", "pickup_method")
    TIP_TYPE_TABLE_INDEX_FIELD_NUMBER: _ClassVar[int]
    HAS_FILTER_FIELD_NUMBER: _ClassVar[int]
    TIP_LENGTH_FIELD_NUMBER: _ClassVar[int]
    MAXIMUM_TIP_VOLUME_FIELD_NUMBER: _ClassVar[int]
    TIP_SIZE_FIELD_NUMBER: _ClassVar[int]
    PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    tip_type_table_index: int
    has_filter: bool
    tip_length: float
    maximum_tip_volume: float
    tip_size: _types_pb2.TipSize
    pickup_method: _types_pb2.TipPickupMethod
    def __init__(self, tip_type_table_index: _Optional[int] = ..., has_filter: _Optional[bool] = ..., tip_length: _Optional[float] = ..., maximum_tip_volume: _Optional[float] = ..., tip_size: _Optional[_Union[_types_pb2.TipSize, str]] = ..., pickup_method: _Optional[_Union[_types_pb2.TipPickupMethod, str]] = ...) -> None: ...

class DriverDefineTipNeedleResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class DriverGetOrAssignTipTypeIndexRequest(_message.Message):
    __slots__ = ("tip",)
    TIP_FIELD_NUMBER: _ClassVar[int]
    tip: _types_pb2_1.ResourceAttributes
    def __init__(self, tip: _Optional[_Union[_types_pb2_1.ResourceAttributes, _Mapping]] = ...) -> None: ...

class DriverGetOrAssignTipTypeIndexResponse(_message.Message):
    __slots__ = ("tip_type_index",)
    TIP_TYPE_INDEX_FIELD_NUMBER: _ClassVar[int]
    tip_type_index: int
    def __init__(self, tip_type_index: _Optional[int] = ...) -> None: ...

class DriverDiscoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverDiscoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DriverInitializeRequest(_message.Message):
    __slots__ = ("read_timeout",)
    READ_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    read_timeout: int
    def __init__(self, read_timeout: _Optional[int] = ...) -> None: ...

class DriverInitializeResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: _Optional[bool] = ...) -> None: ...
