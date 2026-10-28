from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ISwapGripperPositions(_message.Message):
    __slots__ = ("home", "extra_1", "closed", "plate_type_1", "plate_type_2", "plate_type_3", "plate_type_4", "plate_type_5", "plate_type_6", "plate_type_7")
    HOME_FIELD_NUMBER: _ClassVar[int]
    EXTRA_1_FIELD_NUMBER: _ClassVar[int]
    CLOSED_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_1_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_2_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_3_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_4_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_5_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_6_FIELD_NUMBER: _ClassVar[int]
    PLATE_TYPE_7_FIELD_NUMBER: _ClassVar[int]
    home: int
    extra_1: int
    closed: int
    plate_type_1: int
    plate_type_2: int
    plate_type_3: int
    plate_type_4: int
    plate_type_5: int
    plate_type_6: int
    plate_type_7: int
    def __init__(self, home: _Optional[int] = ..., extra_1: _Optional[int] = ..., closed: _Optional[int] = ..., plate_type_1: _Optional[int] = ..., plate_type_2: _Optional[int] = ..., plate_type_3: _Optional[int] = ..., plate_type_4: _Optional[int] = ..., plate_type_5: _Optional[int] = ..., plate_type_6: _Optional[int] = ..., plate_type_7: _Optional[int] = ...) -> None: ...

class ISwapZPositions(_message.Message):
    __slots__ = ("home", "parking", "extra_1", "extra_2", "extra_3", "extra_4", "extra_5", "extra_6", "extra_7", "extra_8")
    HOME_FIELD_NUMBER: _ClassVar[int]
    PARKING_FIELD_NUMBER: _ClassVar[int]
    EXTRA_1_FIELD_NUMBER: _ClassVar[int]
    EXTRA_2_FIELD_NUMBER: _ClassVar[int]
    EXTRA_3_FIELD_NUMBER: _ClassVar[int]
    EXTRA_4_FIELD_NUMBER: _ClassVar[int]
    EXTRA_5_FIELD_NUMBER: _ClassVar[int]
    EXTRA_6_FIELD_NUMBER: _ClassVar[int]
    EXTRA_7_FIELD_NUMBER: _ClassVar[int]
    EXTRA_8_FIELD_NUMBER: _ClassVar[int]
    home: int
    parking: int
    extra_1: int
    extra_2: int
    extra_3: int
    extra_4: int
    extra_5: int
    extra_6: int
    extra_7: int
    extra_8: int
    def __init__(self, home: _Optional[int] = ..., parking: _Optional[int] = ..., extra_1: _Optional[int] = ..., extra_2: _Optional[int] = ..., extra_3: _Optional[int] = ..., extra_4: _Optional[int] = ..., extra_5: _Optional[int] = ..., extra_6: _Optional[int] = ..., extra_7: _Optional[int] = ..., extra_8: _Optional[int] = ...) -> None: ...

class ISwapYPositions(_message.Message):
    __slots__ = ("home", "lower_limit", "upper_limit", "parking", "pre_parking", "extra_1", "extra_2", "extra_3", "extra_4", "extra_5")
    HOME_FIELD_NUMBER: _ClassVar[int]
    LOWER_LIMIT_FIELD_NUMBER: _ClassVar[int]
    UPPER_LIMIT_FIELD_NUMBER: _ClassVar[int]
    PARKING_FIELD_NUMBER: _ClassVar[int]
    PRE_PARKING_FIELD_NUMBER: _ClassVar[int]
    EXTRA_1_FIELD_NUMBER: _ClassVar[int]
    EXTRA_2_FIELD_NUMBER: _ClassVar[int]
    EXTRA_3_FIELD_NUMBER: _ClassVar[int]
    EXTRA_4_FIELD_NUMBER: _ClassVar[int]
    EXTRA_5_FIELD_NUMBER: _ClassVar[int]
    home: int
    lower_limit: int
    upper_limit: int
    parking: int
    pre_parking: int
    extra_1: int
    extra_2: int
    extra_3: int
    extra_4: int
    extra_5: int
    def __init__(self, home: _Optional[int] = ..., lower_limit: _Optional[int] = ..., upper_limit: _Optional[int] = ..., parking: _Optional[int] = ..., pre_parking: _Optional[int] = ..., extra_1: _Optional[int] = ..., extra_2: _Optional[int] = ..., extra_3: _Optional[int] = ..., extra_4: _Optional[int] = ..., extra_5: _Optional[int] = ...) -> None: ...

class ISwapConfiguration(_message.Message):
    __slots__ = ("module", "firmware_version", "firmware_date", "link_1_length", "tool_length", "elbow_x_offset", "elbow_predefined_y_positions_increments", "elbow_predefined_z_positions_increments", "elbow_drive_predefined_increments", "wrist_drive_predefined_increments", "gripper_drive_predefined_increments", "y_range_increments", "y_mm_per_increment", "y_speed_range_increments", "y_speed_default_increments", "y_current_limit_default", "y_acceleration_level_default", "elbow_drive_diameter", "elbow_drive_safety_radius", "elbow_y_min", "elbow_drive_size_z", "z_range_increments", "z_mm_per_increment", "z_speed_range_increments", "z_acceleration_range_increments", "z_speed_default_increments", "z_acceleration_default_increments", "z_current_limit_default", "elbow_z_offset_above_finger", "elbow_range_increments", "elbow_deg_per_increment", "elbow_speed_range_increments", "elbow_acceleration_range_increments", "elbow_speed_default_increments", "elbow_acceleration_default_increments", "elbow_current_limit_default", "wrist_range_increments", "wrist_deg_per_increment", "wrist_speed_range_increments", "wrist_acceleration_range_increments", "wrist_speed_default_increments", "wrist_acceleration_default_increments", "wrist_current_limit_default", "gripper_range_increments", "gripper_mm_per_increment", "gripper_speed_range_increments", "gripper_acceleration_range_increments", "gripper_current_limit_range", "gripper_speed_default_increments", "gripper_acceleration_default_increments", "gripper_current_limit_default", "gripper_close_speed_default_increments", "gripper_nudge_speed_default_increments", "gripper_stop_trigger_default", "gripper_low_pass_filter_default", "gripper_stop_band_range_increments", "gripper_counter_drift_increments")
    MODULE_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_DATE_FIELD_NUMBER: _ClassVar[int]
    LINK_1_LENGTH_FIELD_NUMBER: _ClassVar[int]
    TOOL_LENGTH_FIELD_NUMBER: _ClassVar[int]
    ELBOW_X_OFFSET_FIELD_NUMBER: _ClassVar[int]
    ELBOW_PREDEFINED_Y_POSITIONS_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_PREDEFINED_Z_POSITIONS_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_DRIVE_PREDEFINED_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    WRIST_DRIVE_PREDEFINED_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_DRIVE_PREDEFINED_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Y_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Y_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    Y_ACCELERATION_LEVEL_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    ELBOW_DRIVE_DIAMETER_FIELD_NUMBER: _ClassVar[int]
    ELBOW_DRIVE_SAFETY_RADIUS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_Y_MIN_FIELD_NUMBER: _ClassVar[int]
    ELBOW_DRIVE_SIZE_Z_FIELD_NUMBER: _ClassVar[int]
    Z_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_ACCELERATION_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    Z_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    ELBOW_Z_OFFSET_ABOVE_FINGER_FIELD_NUMBER: _ClassVar[int]
    ELBOW_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_DEG_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    ELBOW_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_ACCELERATION_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_ACCELERATION_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    ELBOW_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    WRIST_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    WRIST_DEG_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    WRIST_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    WRIST_ACCELERATION_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    WRIST_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    WRIST_ACCELERATION_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    WRIST_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_MM_PER_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_SPEED_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_ACCELERATION_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_CURRENT_LIMIT_RANGE_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_ACCELERATION_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_CURRENT_LIMIT_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_CLOSE_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_NUDGE_SPEED_DEFAULT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_STOP_TRIGGER_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_LOW_PASS_FILTER_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_STOP_BAND_RANGE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_COUNTER_DRIFT_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    module: str
    firmware_version: str
    firmware_date: _types_pb2.Date
    link_1_length: float
    tool_length: float
    elbow_x_offset: float
    elbow_predefined_y_positions_increments: ISwapYPositions
    elbow_predefined_z_positions_increments: ISwapZPositions
    elbow_drive_predefined_increments: ISwapElbowPositions
    wrist_drive_predefined_increments: ISwapWristPositions
    gripper_drive_predefined_increments: ISwapGripperPositions
    y_range_increments: _types_pb2.Int32Range
    y_mm_per_increment: float
    y_speed_range_increments: _types_pb2.Int32Range
    y_speed_default_increments: int
    y_current_limit_default: int
    y_acceleration_level_default: int
    elbow_drive_diameter: float
    elbow_drive_safety_radius: float
    elbow_y_min: float
    elbow_drive_size_z: float
    z_range_increments: _types_pb2.Int32Range
    z_mm_per_increment: float
    z_speed_range_increments: _types_pb2.Int32Range
    z_acceleration_range_increments: _types_pb2.Int32Range
    z_speed_default_increments: int
    z_acceleration_default_increments: int
    z_current_limit_default: int
    elbow_z_offset_above_finger: float
    elbow_range_increments: _types_pb2.Int32Range
    elbow_deg_per_increment: float
    elbow_speed_range_increments: _types_pb2.Int32Range
    elbow_acceleration_range_increments: _types_pb2.Int32Range
    elbow_speed_default_increments: int
    elbow_acceleration_default_increments: int
    elbow_current_limit_default: int
    wrist_range_increments: _types_pb2.Int32Range
    wrist_deg_per_increment: float
    wrist_speed_range_increments: _types_pb2.Int32Range
    wrist_acceleration_range_increments: _types_pb2.Int32Range
    wrist_speed_default_increments: int
    wrist_acceleration_default_increments: int
    wrist_current_limit_default: int
    gripper_range_increments: _types_pb2.Int32Range
    gripper_mm_per_increment: float
    gripper_speed_range_increments: _types_pb2.Int32Range
    gripper_acceleration_range_increments: _types_pb2.Int32Range
    gripper_current_limit_range: _types_pb2.Int32Range
    gripper_speed_default_increments: int
    gripper_acceleration_default_increments: int
    gripper_current_limit_default: int
    gripper_close_speed_default_increments: int
    gripper_nudge_speed_default_increments: int
    gripper_stop_trigger_default: int
    gripper_low_pass_filter_default: bool
    gripper_stop_band_range_increments: _types_pb2.Int32Range
    gripper_counter_drift_increments: int
    def __init__(self, module: _Optional[str] = ..., firmware_version: _Optional[str] = ..., firmware_date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ..., link_1_length: _Optional[float] = ..., tool_length: _Optional[float] = ..., elbow_x_offset: _Optional[float] = ..., elbow_predefined_y_positions_increments: _Optional[_Union[ISwapYPositions, _Mapping]] = ..., elbow_predefined_z_positions_increments: _Optional[_Union[ISwapZPositions, _Mapping]] = ..., elbow_drive_predefined_increments: _Optional[_Union[ISwapElbowPositions, _Mapping]] = ..., wrist_drive_predefined_increments: _Optional[_Union[ISwapWristPositions, _Mapping]] = ..., gripper_drive_predefined_increments: _Optional[_Union[ISwapGripperPositions, _Mapping]] = ..., y_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_mm_per_increment: _Optional[float] = ..., y_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., y_speed_default_increments: _Optional[int] = ..., y_current_limit_default: _Optional[int] = ..., y_acceleration_level_default: _Optional[int] = ..., elbow_drive_diameter: _Optional[float] = ..., elbow_drive_safety_radius: _Optional[float] = ..., elbow_y_min: _Optional[float] = ..., elbow_drive_size_z: _Optional[float] = ..., z_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_mm_per_increment: _Optional[float] = ..., z_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., z_speed_default_increments: _Optional[int] = ..., z_acceleration_default_increments: _Optional[int] = ..., z_current_limit_default: _Optional[int] = ..., elbow_z_offset_above_finger: _Optional[float] = ..., elbow_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., elbow_deg_per_increment: _Optional[float] = ..., elbow_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., elbow_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., elbow_speed_default_increments: _Optional[int] = ..., elbow_acceleration_default_increments: _Optional[int] = ..., elbow_current_limit_default: _Optional[int] = ..., wrist_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., wrist_deg_per_increment: _Optional[float] = ..., wrist_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., wrist_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., wrist_speed_default_increments: _Optional[int] = ..., wrist_acceleration_default_increments: _Optional[int] = ..., wrist_current_limit_default: _Optional[int] = ..., gripper_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., gripper_mm_per_increment: _Optional[float] = ..., gripper_speed_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., gripper_acceleration_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., gripper_current_limit_range: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., gripper_speed_default_increments: _Optional[int] = ..., gripper_acceleration_default_increments: _Optional[int] = ..., gripper_current_limit_default: _Optional[int] = ..., gripper_close_speed_default_increments: _Optional[int] = ..., gripper_nudge_speed_default_increments: _Optional[int] = ..., gripper_stop_trigger_default: _Optional[int] = ..., gripper_low_pass_filter_default: _Optional[bool] = ..., gripper_stop_band_range_increments: _Optional[_Union[_types_pb2.Int32Range, _Mapping]] = ..., gripper_counter_drift_increments: _Optional[int] = ...) -> None: ...

class ISwapPose(_message.Message):
    __slots__ = ("elbow_joint_location", "wrist_joint_location", "gripper_center_location", "gripper_deck_orientation", "joints")
    ELBOW_JOINT_LOCATION_FIELD_NUMBER: _ClassVar[int]
    WRIST_JOINT_LOCATION_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_CENTER_LOCATION_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_DECK_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    JOINTS_FIELD_NUMBER: _ClassVar[int]
    elbow_joint_location: _types_pb2_1.Vec3
    wrist_joint_location: _types_pb2_1.Vec3
    gripper_center_location: _types_pb2_1.Vec3
    gripper_deck_orientation: _types_pb2_1.Rotation
    joints: _containers.RepeatedCompositeFieldContainer[_types_pb2.ISwapJoint]
    def __init__(self, elbow_joint_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., wrist_joint_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., gripper_center_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ..., gripper_deck_orientation: _Optional[_Union[_types_pb2_1.Rotation, _Mapping]] = ..., joints: _Optional[_Iterable[_Union[_types_pb2.ISwapJoint, _Mapping]]] = ...) -> None: ...

class ISwapWristPositions(_message.Message):
    __slots__ = ("home", "right", "straight", "left", "reverse", "parking", "extra_1", "extra_2", "extra_3")
    HOME_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    STRAIGHT_FIELD_NUMBER: _ClassVar[int]
    LEFT_FIELD_NUMBER: _ClassVar[int]
    REVERSE_FIELD_NUMBER: _ClassVar[int]
    PARKING_FIELD_NUMBER: _ClassVar[int]
    EXTRA_1_FIELD_NUMBER: _ClassVar[int]
    EXTRA_2_FIELD_NUMBER: _ClassVar[int]
    EXTRA_3_FIELD_NUMBER: _ClassVar[int]
    home: int
    right: int
    straight: int
    left: int
    reverse: int
    parking: int
    extra_1: int
    extra_2: int
    extra_3: int
    def __init__(self, home: _Optional[int] = ..., right: _Optional[int] = ..., straight: _Optional[int] = ..., left: _Optional[int] = ..., reverse: _Optional[int] = ..., parking: _Optional[int] = ..., extra_1: _Optional[int] = ..., extra_2: _Optional[int] = ..., extra_3: _Optional[int] = ...) -> None: ...

class ISwapElbowPositions(_message.Message):
    __slots__ = ("home", "left", "front", "right", "parking", "extra_1", "extra_2", "extra_3", "extra_4")
    HOME_FIELD_NUMBER: _ClassVar[int]
    LEFT_FIELD_NUMBER: _ClassVar[int]
    FRONT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    PARKING_FIELD_NUMBER: _ClassVar[int]
    EXTRA_1_FIELD_NUMBER: _ClassVar[int]
    EXTRA_2_FIELD_NUMBER: _ClassVar[int]
    EXTRA_3_FIELD_NUMBER: _ClassVar[int]
    EXTRA_4_FIELD_NUMBER: _ClassVar[int]
    home: int
    left: int
    front: int
    right: int
    parking: int
    extra_1: int
    extra_2: int
    extra_3: int
    extra_4: int
    def __init__(self, home: _Optional[int] = ..., left: _Optional[int] = ..., front: _Optional[int] = ..., right: _Optional[int] = ..., parking: _Optional[int] = ..., extra_1: _Optional[int] = ..., extra_2: _Optional[int] = ..., extra_3: _Optional[int] = ..., extra_4: _Optional[int] = ...) -> None: ...

class ISwapRequestFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapRequestFirmwareVersionResponse(_message.Message):
    __slots__ = ("version", "date")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    version: str
    date: _types_pb2.Date
    def __init__(self, version: _Optional[str] = ..., date: _Optional[_Union[_types_pb2.Date, _Mapping]] = ...) -> None: ...

class ISwapElbowRequestXOffsetRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestXOffsetResponse(_message.Message):
    __slots__ = ("x_offset",)
    X_OFFSET_FIELD_NUMBER: _ClassVar[int]
    x_offset: float
    def __init__(self, x_offset: _Optional[float] = ...) -> None: ...

class ISwapElbowDriveRequestPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowDriveRequestPositionsResponse(_message.Message):
    __slots__ = ("positions",)
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    positions: ISwapElbowPositions
    def __init__(self, positions: _Optional[_Union[ISwapElbowPositions, _Mapping]] = ...) -> None: ...

class ISwapWristDriveRequestPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapWristDriveRequestPositionsResponse(_message.Message):
    __slots__ = ("positions",)
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    positions: ISwapWristPositions
    def __init__(self, positions: _Optional[_Union[ISwapWristPositions, _Mapping]] = ...) -> None: ...

class ISwapElbowRequestYStopsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestYStopsResponse(_message.Message):
    __slots__ = ("y_stops",)
    class YStopsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    Y_STOPS_FIELD_NUMBER: _ClassVar[int]
    y_stops: _containers.ScalarMap[str, float]
    def __init__(self, y_stops: _Optional[_Mapping[str, float]] = ...) -> None: ...

class ISwapRequestLink1LengthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapRequestLink1LengthResponse(_message.Message):
    __slots__ = ("link_1_length",)
    LINK_1_LENGTH_FIELD_NUMBER: _ClassVar[int]
    link_1_length: float
    def __init__(self, link_1_length: _Optional[float] = ...) -> None: ...

class ISwapRequestToolCenterPointXyLengthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapRequestToolCenterPointXyLengthResponse(_message.Message):
    __slots__ = ("tool_center_point_xy_length",)
    TOOL_CENTER_POINT_XY_LENGTH_FIELD_NUMBER: _ClassVar[int]
    tool_center_point_xy_length: float
    def __init__(self, tool_center_point_xy_length: _Optional[float] = ...) -> None: ...

class ISwapElbowRequestPredefinedZPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestPredefinedZPositionsResponse(_message.Message):
    __slots__ = ("predefined_z_positions",)
    class PredefinedZPositionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    PREDEFINED_Z_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    predefined_z_positions: _containers.ScalarMap[str, float]
    def __init__(self, predefined_z_positions: _Optional[_Mapping[str, float]] = ...) -> None: ...

class ISwapGripperDriveRequestWidthsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperDriveRequestWidthsResponse(_message.Message):
    __slots__ = ("widths",)
    class WidthsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    WIDTHS_FIELD_NUMBER: _ClassVar[int]
    widths: _containers.ScalarMap[str, float]
    def __init__(self, widths: _Optional[_Mapping[str, float]] = ...) -> None: ...

class ISwapDiscoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapDiscoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapDeclareFrontLimitRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapDeclareFrontLimitResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapInitializeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapInitializeResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapElbowDriveUpdateAngleRequest(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...

class ISwapElbowDriveUpdateAngleResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowGetReferencePointLocationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowGetReferencePointLocationResponse(_message.Message):
    __slots__ = ("reference_point_location",)
    REFERENCE_POINT_LOCATION_FIELD_NUMBER: _ClassVar[int]
    reference_point_location: _types_pb2_1.Vec3
    def __init__(self, reference_point_location: _Optional[_Union[_types_pb2_1.Vec3, _Mapping]] = ...) -> None: ...

class ISwapWristDriveGetAngleRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapWristDriveGetAngleResponse(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...

class ISwapElbowDriveGetAngleRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowDriveGetAngleResponse(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...

class ISwapWristDriveUpdateAngleRequest(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...

class ISwapWristDriveUpdateAngleResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperUpdateWidthRequest(_message.Message):
    __slots__ = ("width",)
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    width: float
    def __init__(self, width: _Optional[float] = ...) -> None: ...

class ISwapGripperUpdateWidthResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapUpdateLocationByReferencePointRequest(_message.Message):
    __slots__ = ("y", "z")
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    y: float
    z: float
    def __init__(self, y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class ISwapUpdateLocationByReferencePointResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestXPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestXPositionResponse(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: float
    def __init__(self, x_position: _Optional[float] = ...) -> None: ...

class ISwapElbowMoveToXPositionRequest(_message.Message):
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

class ISwapElbowMoveToXPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapElbowRequestYPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestYPositionResponse(_message.Message):
    __slots__ = ("y_position",)
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    y_position: float
    def __init__(self, y_position: _Optional[float] = ...) -> None: ...

class ISwapElbowMoveToYPositionRequest(_message.Message):
    __slots__ = ("y", "make_space", "speed", "acceleration_level", "current_limit")
    Y_FIELD_NUMBER: _ClassVar[int]
    MAKE_SPACE_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    y: float
    make_space: bool
    speed: float
    acceleration_level: int
    current_limit: int
    def __init__(self, y: _Optional[float] = ..., make_space: _Optional[bool] = ..., speed: _Optional[float] = ..., acceleration_level: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapElbowMoveToYPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapMakeSpaceRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapMakeSpaceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestZPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowRequestZPositionResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class ISwapElbowMoveToZPositionRequest(_message.Message):
    __slots__ = ("z", "speed", "acceleration", "current_limit")
    Z_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    z: float
    speed: float
    acceleration: float
    current_limit: int
    def __init__(self, z: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapElbowMoveToZPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapElbowMoveToSafeZHeightRequest(_message.Message):
    __slots__ = ("speed", "acceleration", "current_limit")
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    speed: float
    acceleration: float
    current_limit: int
    def __init__(self, speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapElbowMoveToSafeZHeightResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class ISwapRotateToAnglesRequest(_message.Message):
    __slots__ = ("elbow_relative_angle_name", "elbow_relative_angle_value", "elbow_absolute_angle_name", "elbow_absolute_angle_value", "gripper_relative_angle_name", "gripper_relative_angle_value", "gripper_absolute_angle_name", "gripper_absolute_angle_value", "raise_features", "make_space", "elbow_speed", "wrist_speed", "elbow_acceleration", "wrist_acceleration", "elbow_current_limit", "wrist_current_limit")
    ELBOW_RELATIVE_ANGLE_NAME_FIELD_NUMBER: _ClassVar[int]
    ELBOW_RELATIVE_ANGLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    ELBOW_ABSOLUTE_ANGLE_NAME_FIELD_NUMBER: _ClassVar[int]
    ELBOW_ABSOLUTE_ANGLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_RELATIVE_ANGLE_NAME_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_RELATIVE_ANGLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_ABSOLUTE_ANGLE_NAME_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_ABSOLUTE_ANGLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    RAISE_FEATURES_FIELD_NUMBER: _ClassVar[int]
    MAKE_SPACE_FIELD_NUMBER: _ClassVar[int]
    ELBOW_SPEED_FIELD_NUMBER: _ClassVar[int]
    WRIST_SPEED_FIELD_NUMBER: _ClassVar[int]
    ELBOW_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    WRIST_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    ELBOW_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    WRIST_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    elbow_relative_angle_name: str
    elbow_relative_angle_value: float
    elbow_absolute_angle_name: str
    elbow_absolute_angle_value: float
    gripper_relative_angle_name: str
    gripper_relative_angle_value: float
    gripper_absolute_angle_name: str
    gripper_absolute_angle_value: float
    raise_features: bool
    make_space: bool
    elbow_speed: float
    wrist_speed: float
    elbow_acceleration: float
    wrist_acceleration: float
    elbow_current_limit: int
    wrist_current_limit: int
    def __init__(self, elbow_relative_angle_name: _Optional[str] = ..., elbow_relative_angle_value: _Optional[float] = ..., elbow_absolute_angle_name: _Optional[str] = ..., elbow_absolute_angle_value: _Optional[float] = ..., gripper_relative_angle_name: _Optional[str] = ..., gripper_relative_angle_value: _Optional[float] = ..., gripper_absolute_angle_name: _Optional[str] = ..., gripper_absolute_angle_value: _Optional[float] = ..., raise_features: _Optional[bool] = ..., make_space: _Optional[bool] = ..., elbow_speed: _Optional[float] = ..., wrist_speed: _Optional[float] = ..., elbow_acceleration: _Optional[float] = ..., wrist_acceleration: _Optional[float] = ..., elbow_current_limit: _Optional[int] = ..., wrist_current_limit: _Optional[int] = ...) -> None: ...

class ISwapRotateToAnglesResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapElbowDriveRequestAngleRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapElbowDriveRequestAngleResponse(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...

class ISwapElbowDriveRotateToAngleRequest(_message.Message):
    __slots__ = ("angle_name", "angle_value", "speed", "acceleration", "current_limit")
    ANGLE_NAME_FIELD_NUMBER: _ClassVar[int]
    ANGLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    angle_name: str
    angle_value: float
    speed: float
    acceleration: float
    current_limit: int
    def __init__(self, angle_name: _Optional[str] = ..., angle_value: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapElbowDriveRotateToAngleResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapWristDriveRequestAngleRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapWristDriveRequestAngleResponse(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...

class ISwapWristDriveRotateToAngleRequest(_message.Message):
    __slots__ = ("angle_name", "angle_value", "speed", "acceleration", "current_limit")
    ANGLE_NAME_FIELD_NUMBER: _ClassVar[int]
    ANGLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    angle_name: str
    angle_value: float
    speed: float
    acceleration: float
    current_limit: int
    def __init__(self, angle_name: _Optional[str] = ..., angle_value: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapWristDriveRotateToAngleResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapGripperRequestCountersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperRequestCountersResponse(_message.Message):
    __slots__ = ("firmware_counter", "encoder_counter")
    FIRMWARE_COUNTER_FIELD_NUMBER: _ClassVar[int]
    ENCODER_COUNTER_FIELD_NUMBER: _ClassVar[int]
    firmware_counter: int
    encoder_counter: int
    def __init__(self, firmware_counter: _Optional[int] = ..., encoder_counter: _Optional[int] = ...) -> None: ...

class ISwapGripperRequestLatestForceAppliedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperRequestLatestForceAppliedResponse(_message.Message):
    __slots__ = ("latest_force_applied",)
    class LatestForceAppliedEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    LATEST_FORCE_APPLIED_FIELD_NUMBER: _ClassVar[int]
    latest_force_applied: _containers.ScalarMap[str, int]
    def __init__(self, latest_force_applied: _Optional[_Mapping[str, int]] = ...) -> None: ...

class ISwapGripperRequestWidthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperRequestWidthResponse(_message.Message):
    __slots__ = ("width",)
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    width: float
    def __init__(self, width: _Optional[float] = ...) -> None: ...

class ISwapRequestPlateGrippedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapRequestPlateGrippedResponse(_message.Message):
    __slots__ = ("gripped",)
    GRIPPED_FIELD_NUMBER: _ClassVar[int]
    gripped: bool
    def __init__(self, gripped: _Optional[bool] = ...) -> None: ...

class ISwapGetGrippedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGetGrippedResponse(_message.Message):
    __slots__ = ("gripped",)
    GRIPPED_FIELD_NUMBER: _ClassVar[int]
    gripped: bool
    def __init__(self, gripped: _Optional[bool] = ...) -> None: ...

class ISwapGripperMoveToJawPositionRequest(_message.Message):
    __slots__ = ("width", "speed", "acceleration", "current_limit")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    width: float
    speed: float
    acceleration: float
    current_limit: int
    def __init__(self, width: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapGripperMoveToJawPositionResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapGripperOpenRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperOpenResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapGripperCloseRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapGripperCloseResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapGripperCloseWithForceSensedWidthWindowRequest(_message.Message):
    __slots__ = ("width", "grip_strength", "width_tolerance")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    WIDTH_TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    width: float
    grip_strength: int
    width_tolerance: float
    def __init__(self, width: _Optional[float] = ..., grip_strength: _Optional[int] = ..., width_tolerance: _Optional[float] = ...) -> None: ...

class ISwapGripperCloseWithForceSensedWidthWindowResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapGripperProbeForObjectRequest(_message.Message):
    __slots__ = ("expected_width", "band", "stop_trigger", "current_limit")
    EXPECTED_WIDTH_FIELD_NUMBER: _ClassVar[int]
    BAND_FIELD_NUMBER: _ClassVar[int]
    STOP_TRIGGER_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    expected_width: float
    band: float
    stop_trigger: int
    current_limit: int
    def __init__(self, expected_width: _Optional[float] = ..., band: _Optional[float] = ..., stop_trigger: _Optional[int] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapGripperProbeForObjectResponse(_message.Message):
    __slots__ = ("width",)
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    width: float
    def __init__(self, width: _Optional[float] = ...) -> None: ...

class ISwapInitializeGripperDriveRequest(_message.Message):
    __slots__ = ("current_limit",)
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    current_limit: int
    def __init__(self, current_limit: _Optional[int] = ...) -> None: ...

class ISwapInitializeGripperDriveResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapRecoverGripperDriveRequest(_message.Message):
    __slots__ = ("attempts", "nudge", "current_limit")
    ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    NUDGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    attempts: int
    nudge: float
    current_limit: int
    def __init__(self, attempts: _Optional[int] = ..., nudge: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class ISwapRecoverGripperDriveResponse(_message.Message):
    __slots__ = ("recovered",)
    RECOVERED_FIELD_NUMBER: _ClassVar[int]
    recovered: bool
    def __init__(self, recovered: _Optional[bool] = ...) -> None: ...

class ISwapRequestJointStateRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapRequestJointStateResponse(_message.Message):
    __slots__ = ("joint_state",)
    JOINT_STATE_FIELD_NUMBER: _ClassVar[int]
    joint_state: _containers.RepeatedCompositeFieldContainer[_types_pb2.ISwapJoint]
    def __init__(self, joint_state: _Optional[_Iterable[_Union[_types_pb2.ISwapJoint, _Mapping]]] = ...) -> None: ...

class ISwapRequestPoseRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ISwapRequestPoseResponse(_message.Message):
    __slots__ = ("pose",)
    POSE_FIELD_NUMBER: _ClassVar[int]
    pose: ISwapPose
    def __init__(self, pose: _Optional[_Union[ISwapPose, _Mapping]] = ...) -> None: ...

class ISwapRequestIsParkedRequest(_message.Message):
    __slots__ = ("tolerance_increments",)
    TOLERANCE_INCREMENTS_FIELD_NUMBER: _ClassVar[int]
    tolerance_increments: int
    def __init__(self, tolerance_increments: _Optional[int] = ...) -> None: ...

class ISwapRequestIsParkedResponse(_message.Message):
    __slots__ = ("parked",)
    PARKED_FIELD_NUMBER: _ClassVar[int]
    parked: bool
    def __init__(self, parked: _Optional[bool] = ...) -> None: ...

class ISwapParkRequest(_message.Message):
    __slots__ = ("traverse_height",)
    TRAVERSE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    traverse_height: float
    def __init__(self, traverse_height: _Optional[float] = ...) -> None: ...

class ISwapParkResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class ISwapSettings(_message.Message):
    __slots__ = ("default_minimum_traverse_height",)
    DEFAULT_MINIMUM_TRAVERSE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    default_minimum_traverse_height: float
    def __init__(self, default_minimum_traverse_height: _Optional[float] = ...) -> None: ...
