from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LLDMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LLD_OFF: _ClassVar[LLDMode]
    LLD_GAMMA: _ClassVar[LLDMode]
    LLD_PRESSURE: _ClassVar[LLDMode]
    LLD_DUAL: _ClassVar[LLDMode]
    LLD_Z_TOUCH_OFF: _ClassVar[LLDMode]

class TipPickupMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUT_OF_RACK: _ClassVar[TipPickupMethod]
    OUT_OF_WASH_LIQUID: _ClassVar[TipPickupMethod]

class TipDropMethodEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PLACE_SHIFT: _ClassVar[TipDropMethodEnum]
    TIP_DROP: _ClassVar[TipDropMethodEnum]

class TipSizeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TIP_SIZE_UNDEFINED: _ClassVar[TipSizeEnum]
    LOW_VOLUME: _ClassVar[TipSizeEnum]
    STANDARD_VOLUME: _ClassVar[TipSizeEnum]
    HIGH_VOLUME: _ClassVar[TipSizeEnum]
    CORE_384: _ClassVar[TipSizeEnum]
    XL: _ClassVar[TipSizeEnum]

class GripDirectionEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GRIP_FRONT: _ClassVar[GripDirectionEnum]
    GRIP_BACK: _ClassVar[GripDirectionEnum]
    GRIP_LEFT: _ClassVar[GripDirectionEnum]
    GRIP_RIGHT: _ClassVar[GripDirectionEnum]

class RotationDriveOrientationEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ROT_LEFT: _ClassVar[RotationDriveOrientationEnum]
    ROT_FRONT: _ClassVar[RotationDriveOrientationEnum]
    ROT_RIGHT: _ClassVar[RotationDriveOrientationEnum]

class WristDriveOrientationEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WRIST_RIGHT: _ClassVar[WristDriveOrientationEnum]
    WRIST_STRAIGHT: _ClassVar[WristDriveOrientationEnum]
    WRIST_LEFT: _ClassVar[WristDriveOrientationEnum]
    WRIST_REVERSE: _ClassVar[WristDriveOrientationEnum]

class Barcode1DSymbologyEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BARCODE_UNKNOWN: _ClassVar[Barcode1DSymbologyEnum]
    BARCODE_CODE128: _ClassVar[Barcode1DSymbologyEnum]
    BARCODE_CODE39: _ClassVar[Barcode1DSymbologyEnum]
    BARCODE_CODABAR: _ClassVar[Barcode1DSymbologyEnum]
    BARCODE_CODE93: _ClassVar[Barcode1DSymbologyEnum]
    BARCODE_CODE25: _ClassVar[Barcode1DSymbologyEnum]
    BARCODE_EAN128: _ClassVar[Barcode1DSymbologyEnum]
LLD_OFF: LLDMode
LLD_GAMMA: LLDMode
LLD_PRESSURE: LLDMode
LLD_DUAL: LLDMode
LLD_Z_TOUCH_OFF: LLDMode
OUT_OF_RACK: TipPickupMethod
OUT_OF_WASH_LIQUID: TipPickupMethod
PLACE_SHIFT: TipDropMethodEnum
TIP_DROP: TipDropMethodEnum
TIP_SIZE_UNDEFINED: TipSizeEnum
LOW_VOLUME: TipSizeEnum
STANDARD_VOLUME: TipSizeEnum
HIGH_VOLUME: TipSizeEnum
CORE_384: TipSizeEnum
XL: TipSizeEnum
GRIP_FRONT: GripDirectionEnum
GRIP_BACK: GripDirectionEnum
GRIP_LEFT: GripDirectionEnum
GRIP_RIGHT: GripDirectionEnum
ROT_LEFT: RotationDriveOrientationEnum
ROT_FRONT: RotationDriveOrientationEnum
ROT_RIGHT: RotationDriveOrientationEnum
WRIST_RIGHT: WristDriveOrientationEnum
WRIST_STRAIGHT: WristDriveOrientationEnum
WRIST_LEFT: WristDriveOrientationEnum
WRIST_REVERSE: WristDriveOrientationEnum
BARCODE_UNKNOWN: Barcode1DSymbologyEnum
BARCODE_CODE128: Barcode1DSymbologyEnum
BARCODE_CODE39: Barcode1DSymbologyEnum
BARCODE_CODABAR: Barcode1DSymbologyEnum
BARCODE_CODE93: Barcode1DSymbologyEnum
BARCODE_CODE25: Barcode1DSymbologyEnum
BARCODE_EAN128: Barcode1DSymbologyEnum

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Coordinate(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class Rotation(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class TipData(_message.Message):
    __slots__ = ("type", "has_filter", "total_tip_length", "maximal_volume", "fitting_depth", "tip_size", "pickup_method")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    HAS_FILTER_FIELD_NUMBER: _ClassVar[int]
    TOTAL_TIP_LENGTH_FIELD_NUMBER: _ClassVar[int]
    MAXIMAL_VOLUME_FIELD_NUMBER: _ClassVar[int]
    FITTING_DEPTH_FIELD_NUMBER: _ClassVar[int]
    TIP_SIZE_FIELD_NUMBER: _ClassVar[int]
    PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    type: str
    has_filter: bool
    total_tip_length: float
    maximal_volume: float
    fitting_depth: float
    tip_size: TipSizeEnum
    pickup_method: TipPickupMethod
    def __init__(self, type: _Optional[str] = ..., has_filter: bool = ..., total_tip_length: _Optional[float] = ..., maximal_volume: _Optional[float] = ..., fitting_depth: _Optional[float] = ..., tip_size: _Optional[_Union[TipSizeEnum, str]] = ..., pickup_method: _Optional[_Union[TipPickupMethod, str]] = ...) -> None: ...

class MixData(_message.Message):
    __slots__ = ("volume", "repetitions", "flow_rate")
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    REPETITIONS_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    volume: float
    repetitions: int
    flow_rate: float
    def __init__(self, volume: _Optional[float] = ..., repetitions: _Optional[int] = ..., flow_rate: _Optional[float] = ...) -> None: ...

class PickupOp(_message.Message):
    __slots__ = ("resource_name", "offset", "tip")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIP_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    tip: TipData
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tip: _Optional[_Union[TipData, _Mapping]] = ...) -> None: ...

class DropOp(_message.Message):
    __slots__ = ("resource_name", "offset", "tip")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIP_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    tip: TipData
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tip: _Optional[_Union[TipData, _Mapping]] = ...) -> None: ...

class SingleChannelAspirationOp(_message.Message):
    __slots__ = ("resource_name", "offset", "tip", "volume", "flow_rate", "liquid_height", "blow_out_air_volume", "mix")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIP_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    tip: TipData
    volume: float
    flow_rate: float
    liquid_height: float
    blow_out_air_volume: float
    mix: MixData
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tip: _Optional[_Union[TipData, _Mapping]] = ..., volume: _Optional[float] = ..., flow_rate: _Optional[float] = ..., liquid_height: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix: _Optional[_Union[MixData, _Mapping]] = ...) -> None: ...

class SingleChannelDispenseOp(_message.Message):
    __slots__ = ("resource_name", "offset", "tip", "volume", "flow_rate", "liquid_height", "blow_out_air_volume", "mix")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIP_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    tip: TipData
    volume: float
    flow_rate: float
    liquid_height: float
    blow_out_air_volume: float
    mix: MixData
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tip: _Optional[_Union[TipData, _Mapping]] = ..., volume: _Optional[float] = ..., flow_rate: _Optional[float] = ..., liquid_height: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix: _Optional[_Union[MixData, _Mapping]] = ...) -> None: ...

class PickupTipRackOp(_message.Message):
    __slots__ = ("resource_name", "offset", "tips", "tip_present")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    TIP_PRESENT_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    tips: _containers.RepeatedCompositeFieldContainer[TipData]
    tip_present: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tips: _Optional[_Iterable[_Union[TipData, _Mapping]]] = ..., tip_present: _Optional[_Iterable[bool]] = ...) -> None: ...

class DropTipRackOp(_message.Message):
    __slots__ = ("resource_name", "offset")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class MultiHeadAspirationPlateOp(_message.Message):
    __slots__ = ("well_names", "offset", "tips", "tip_present", "volume", "flow_rate", "liquid_height", "blow_out_air_volume", "mix")
    WELL_NAMES_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    TIP_PRESENT_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    well_names: _containers.RepeatedScalarFieldContainer[str]
    offset: Coordinate
    tips: _containers.RepeatedCompositeFieldContainer[TipData]
    tip_present: _containers.RepeatedScalarFieldContainer[bool]
    volume: float
    flow_rate: float
    liquid_height: float
    blow_out_air_volume: float
    mix: MixData
    def __init__(self, well_names: _Optional[_Iterable[str]] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tips: _Optional[_Iterable[_Union[TipData, _Mapping]]] = ..., tip_present: _Optional[_Iterable[bool]] = ..., volume: _Optional[float] = ..., flow_rate: _Optional[float] = ..., liquid_height: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix: _Optional[_Union[MixData, _Mapping]] = ...) -> None: ...

class MultiHeadDispensePlateOp(_message.Message):
    __slots__ = ("well_names", "offset", "tips", "tip_present", "volume", "flow_rate", "liquid_height", "blow_out_air_volume", "mix")
    WELL_NAMES_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    TIP_PRESENT_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    well_names: _containers.RepeatedScalarFieldContainer[str]
    offset: Coordinate
    tips: _containers.RepeatedCompositeFieldContainer[TipData]
    tip_present: _containers.RepeatedScalarFieldContainer[bool]
    volume: float
    flow_rate: float
    liquid_height: float
    blow_out_air_volume: float
    mix: MixData
    def __init__(self, well_names: _Optional[_Iterable[str]] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tips: _Optional[_Iterable[_Union[TipData, _Mapping]]] = ..., tip_present: _Optional[_Iterable[bool]] = ..., volume: _Optional[float] = ..., flow_rate: _Optional[float] = ..., liquid_height: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix: _Optional[_Union[MixData, _Mapping]] = ...) -> None: ...

class MultiHeadAspirationContainerOp(_message.Message):
    __slots__ = ("container_name", "offset", "tips", "tip_present", "volume", "flow_rate", "liquid_height", "blow_out_air_volume", "mix")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    TIP_PRESENT_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    offset: Coordinate
    tips: _containers.RepeatedCompositeFieldContainer[TipData]
    tip_present: _containers.RepeatedScalarFieldContainer[bool]
    volume: float
    flow_rate: float
    liquid_height: float
    blow_out_air_volume: float
    mix: MixData
    def __init__(self, container_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tips: _Optional[_Iterable[_Union[TipData, _Mapping]]] = ..., tip_present: _Optional[_Iterable[bool]] = ..., volume: _Optional[float] = ..., flow_rate: _Optional[float] = ..., liquid_height: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix: _Optional[_Union[MixData, _Mapping]] = ...) -> None: ...

class MultiHeadDispenseContainerOp(_message.Message):
    __slots__ = ("container_name", "offset", "tips", "tip_present", "volume", "flow_rate", "liquid_height", "blow_out_air_volume", "mix")
    CONTAINER_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    TIP_PRESENT_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_FIELD_NUMBER: _ClassVar[int]
    container_name: str
    offset: Coordinate
    tips: _containers.RepeatedCompositeFieldContainer[TipData]
    tip_present: _containers.RepeatedScalarFieldContainer[bool]
    volume: float
    flow_rate: float
    liquid_height: float
    blow_out_air_volume: float
    mix: MixData
    def __init__(self, container_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., tips: _Optional[_Iterable[_Union[TipData, _Mapping]]] = ..., tip_present: _Optional[_Iterable[bool]] = ..., volume: _Optional[float] = ..., flow_rate: _Optional[float] = ..., liquid_height: _Optional[float] = ..., blow_out_air_volume: _Optional[float] = ..., mix: _Optional[_Union[MixData, _Mapping]] = ...) -> None: ...

class ResourcePickupOp(_message.Message):
    __slots__ = ("resource_name", "offset", "pickup_distance_from_top", "direction")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_TOP_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    offset: Coordinate
    pickup_distance_from_top: float
    direction: GripDirectionEnum
    def __init__(self, resource_name: _Optional[str] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., pickup_distance_from_top: _Optional[float] = ..., direction: _Optional[_Union[GripDirectionEnum, str]] = ...) -> None: ...

class ResourceMoveOp(_message.Message):
    __slots__ = ("resource_name", "location", "gripped_direction", "pickup_distance_from_top", "offset")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    GRIPPED_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_TOP_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    location: Coordinate
    gripped_direction: GripDirectionEnum
    pickup_distance_from_top: float
    offset: Coordinate
    def __init__(self, resource_name: _Optional[str] = ..., location: _Optional[_Union[Coordinate, _Mapping]] = ..., gripped_direction: _Optional[_Union[GripDirectionEnum, str]] = ..., pickup_distance_from_top: _Optional[float] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class ResourceDropOp(_message.Message):
    __slots__ = ("resource_name", "destination", "destination_absolute_rotation", "offset", "pickup_distance_from_top", "pickup_direction", "direction", "rotation")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_ABSOLUTE_ROTATION_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_TOP_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    destination: Coordinate
    destination_absolute_rotation: Rotation
    offset: Coordinate
    pickup_distance_from_top: float
    pickup_direction: GripDirectionEnum
    direction: GripDirectionEnum
    rotation: float
    def __init__(self, resource_name: _Optional[str] = ..., destination: _Optional[_Union[Coordinate, _Mapping]] = ..., destination_absolute_rotation: _Optional[_Union[Rotation, _Mapping]] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., pickup_distance_from_top: _Optional[float] = ..., pickup_direction: _Optional[_Union[GripDirectionEnum, str]] = ..., direction: _Optional[_Union[GripDirectionEnum, str]] = ..., rotation: _Optional[float] = ...) -> None: ...

class ChannelFloatMap(_message.Message):
    __slots__ = ("entries",)
    class EntriesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: float
        def __init__(self, key: _Optional[int] = ..., value: _Optional[float] = ...) -> None: ...
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.ScalarMap[int, float]
    def __init__(self, entries: _Optional[_Mapping[int, float]] = ...) -> None: ...

class SetupRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetupResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetNumChannelsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetNumChannelsResponse(_message.Message):
    __slots__ = ("num_channels",)
    NUM_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    num_channels: int
    def __init__(self, num_channels: _Optional[int] = ...) -> None: ...

class GetHead96InstalledRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetHead96InstalledResponse(_message.Message):
    __slots__ = ("installed",)
    INSTALLED_FIELD_NUMBER: _ClassVar[int]
    installed: bool
    def __init__(self, installed: bool = ...) -> None: ...

class GetIswapInstalledRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetIswapInstalledResponse(_message.Message):
    __slots__ = ("installed",)
    INSTALLED_FIELD_NUMBER: _ClassVar[int]
    installed: bool
    def __init__(self, installed: bool = ...) -> None: ...

class GetIswapParkedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetIswapParkedResponse(_message.Message):
    __slots__ = ("parked",)
    PARKED_FIELD_NUMBER: _ClassVar[int]
    parked: bool
    def __init__(self, parked: bool = ...) -> None: ...

class GetCoreParkedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetCoreParkedResponse(_message.Message):
    __slots__ = ("parked",)
    PARKED_FIELD_NUMBER: _ClassVar[int]
    parked: bool
    def __init__(self, parked: bool = ...) -> None: ...

class PickUpTipsRequest(_message.Message):
    __slots__ = ("ops", "use_channels", "begin_tip_pick_up_process", "end_tip_pick_up_process", "minimum_traverse_height_at_beginning_of_a_command", "pickup_method")
    OPS_FIELD_NUMBER: _ClassVar[int]
    USE_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    BEGIN_TIP_PICK_UP_PROCESS_FIELD_NUMBER: _ClassVar[int]
    END_TIP_PICK_UP_PROCESS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    ops: _containers.RepeatedCompositeFieldContainer[PickupOp]
    use_channels: _containers.RepeatedScalarFieldContainer[int]
    begin_tip_pick_up_process: float
    end_tip_pick_up_process: float
    minimum_traverse_height_at_beginning_of_a_command: float
    pickup_method: int
    def __init__(self, ops: _Optional[_Iterable[_Union[PickupOp, _Mapping]]] = ..., use_channels: _Optional[_Iterable[int]] = ..., begin_tip_pick_up_process: _Optional[float] = ..., end_tip_pick_up_process: _Optional[float] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., pickup_method: _Optional[int] = ...) -> None: ...

class PickUpTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DropTipsRequest(_message.Message):
    __slots__ = ("ops", "use_channels", "drop_method", "begin_tip_deposit_process", "end_tip_deposit_process", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_end_of_a_command")
    OPS_FIELD_NUMBER: _ClassVar[int]
    USE_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    DROP_METHOD_FIELD_NUMBER: _ClassVar[int]
    BEGIN_TIP_DEPOSIT_PROCESS_FIELD_NUMBER: _ClassVar[int]
    END_TIP_DEPOSIT_PROCESS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_END_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    ops: _containers.RepeatedCompositeFieldContainer[DropOp]
    use_channels: _containers.RepeatedScalarFieldContainer[int]
    drop_method: int
    begin_tip_deposit_process: float
    end_tip_deposit_process: float
    minimum_traverse_height_at_beginning_of_a_command: float
    z_position_at_end_of_a_command: float
    def __init__(self, ops: _Optional[_Iterable[_Union[DropOp, _Mapping]]] = ..., use_channels: _Optional[_Iterable[int]] = ..., drop_method: _Optional[int] = ..., begin_tip_deposit_process: _Optional[float] = ..., end_tip_deposit_process: _Optional[float] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., z_position_at_end_of_a_command: _Optional[float] = ...) -> None: ...

class DropTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AspirateRequest(_message.Message):
    __slots__ = ("ops", "use_channels", "jet", "blow_out", "lld_search_height", "clot_detection_height", "pull_out_distance_transport_air", "second_section_height", "second_section_ratio", "minimum_height", "immersion_depth", "surface_following_distance", "transport_air_volume", "pre_wetting_volume", "lld_mode", "gamma_lld_sensitivity", "dp_lld_sensitivity", "aspirate_position_above_z_touch_off", "detection_height_difference_for_dual_lld", "swap_speed", "settling_time", "mix_position_from_liquid_surface", "mix_surface_following_distance", "limit_curve_index", "use_2nd_section_aspiration", "retract_height_over_2nd_section_to_empty_tip", "dispensation_speed_during_emptying_tip", "dosing_drive_speed_during_2nd_section_search", "z_drive_speed_during_2nd_section_search", "cup_upper_edge", "ratio_liquid_rise_to_tip_deep_in", "immersion_depth_2nd_section", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "liquid_surface_no_lld", "probe_liquid_height", "auto_surface_following_distance", "disable_volume_correction")
    OPS_FIELD_NUMBER: _ClassVar[int]
    USE_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    JET_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    CLOT_DETECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    PRE_WETTING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    DP_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    ASPIRATE_POSITION_ABOVE_Z_TOUCH_OFF_FIELD_NUMBER: _ClassVar[int]
    DETECTION_HEIGHT_DIFFERENCE_FOR_DUAL_LLD_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    USE_2ND_SECTION_ASPIRATION_FIELD_NUMBER: _ClassVar[int]
    RETRACT_HEIGHT_OVER_2ND_SECTION_TO_EMPTY_TIP_FIELD_NUMBER: _ClassVar[int]
    DISPENSATION_SPEED_DURING_EMPTYING_TIP_FIELD_NUMBER: _ClassVar[int]
    DOSING_DRIVE_SPEED_DURING_2ND_SECTION_SEARCH_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_SPEED_DURING_2ND_SECTION_SEARCH_FIELD_NUMBER: _ClassVar[int]
    CUP_UPPER_EDGE_FIELD_NUMBER: _ClassVar[int]
    RATIO_LIQUID_RISE_TO_TIP_DEEP_IN_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_2ND_SECTION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    LIQUID_SURFACE_NO_LLD_FIELD_NUMBER: _ClassVar[int]
    PROBE_LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    AUTO_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VOLUME_CORRECTION_FIELD_NUMBER: _ClassVar[int]
    ops: _containers.RepeatedCompositeFieldContainer[SingleChannelAspirationOp]
    use_channels: _containers.RepeatedScalarFieldContainer[int]
    jet: _containers.RepeatedScalarFieldContainer[bool]
    blow_out: _containers.RepeatedScalarFieldContainer[bool]
    lld_search_height: _containers.RepeatedScalarFieldContainer[float]
    clot_detection_height: _containers.RepeatedScalarFieldContainer[float]
    pull_out_distance_transport_air: _containers.RepeatedScalarFieldContainer[float]
    second_section_height: _containers.RepeatedScalarFieldContainer[float]
    second_section_ratio: _containers.RepeatedScalarFieldContainer[float]
    minimum_height: _containers.RepeatedScalarFieldContainer[float]
    immersion_depth: _containers.RepeatedScalarFieldContainer[float]
    surface_following_distance: _containers.RepeatedScalarFieldContainer[float]
    transport_air_volume: _containers.RepeatedScalarFieldContainer[float]
    pre_wetting_volume: _containers.RepeatedScalarFieldContainer[float]
    lld_mode: _containers.RepeatedScalarFieldContainer[int]
    gamma_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    dp_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    aspirate_position_above_z_touch_off: _containers.RepeatedScalarFieldContainer[float]
    detection_height_difference_for_dual_lld: _containers.RepeatedScalarFieldContainer[float]
    swap_speed: _containers.RepeatedScalarFieldContainer[float]
    settling_time: _containers.RepeatedScalarFieldContainer[float]
    mix_position_from_liquid_surface: _containers.RepeatedScalarFieldContainer[float]
    mix_surface_following_distance: _containers.RepeatedScalarFieldContainer[float]
    limit_curve_index: _containers.RepeatedScalarFieldContainer[int]
    use_2nd_section_aspiration: _containers.RepeatedScalarFieldContainer[bool]
    retract_height_over_2nd_section_to_empty_tip: _containers.RepeatedScalarFieldContainer[float]
    dispensation_speed_during_emptying_tip: _containers.RepeatedScalarFieldContainer[float]
    dosing_drive_speed_during_2nd_section_search: _containers.RepeatedScalarFieldContainer[float]
    z_drive_speed_during_2nd_section_search: _containers.RepeatedScalarFieldContainer[float]
    cup_upper_edge: _containers.RepeatedScalarFieldContainer[float]
    ratio_liquid_rise_to_tip_deep_in: _containers.RepeatedScalarFieldContainer[int]
    immersion_depth_2nd_section: _containers.RepeatedScalarFieldContainer[float]
    minimum_traverse_height_at_beginning_of_a_command: float
    min_z_endpos: float
    liquid_surface_no_lld: _containers.RepeatedScalarFieldContainer[float]
    probe_liquid_height: bool
    auto_surface_following_distance: bool
    disable_volume_correction: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, ops: _Optional[_Iterable[_Union[SingleChannelAspirationOp, _Mapping]]] = ..., use_channels: _Optional[_Iterable[int]] = ..., jet: _Optional[_Iterable[bool]] = ..., blow_out: _Optional[_Iterable[bool]] = ..., lld_search_height: _Optional[_Iterable[float]] = ..., clot_detection_height: _Optional[_Iterable[float]] = ..., pull_out_distance_transport_air: _Optional[_Iterable[float]] = ..., second_section_height: _Optional[_Iterable[float]] = ..., second_section_ratio: _Optional[_Iterable[float]] = ..., minimum_height: _Optional[_Iterable[float]] = ..., immersion_depth: _Optional[_Iterable[float]] = ..., surface_following_distance: _Optional[_Iterable[float]] = ..., transport_air_volume: _Optional[_Iterable[float]] = ..., pre_wetting_volume: _Optional[_Iterable[float]] = ..., lld_mode: _Optional[_Iterable[int]] = ..., gamma_lld_sensitivity: _Optional[_Iterable[int]] = ..., dp_lld_sensitivity: _Optional[_Iterable[int]] = ..., aspirate_position_above_z_touch_off: _Optional[_Iterable[float]] = ..., detection_height_difference_for_dual_lld: _Optional[_Iterable[float]] = ..., swap_speed: _Optional[_Iterable[float]] = ..., settling_time: _Optional[_Iterable[float]] = ..., mix_position_from_liquid_surface: _Optional[_Iterable[float]] = ..., mix_surface_following_distance: _Optional[_Iterable[float]] = ..., limit_curve_index: _Optional[_Iterable[int]] = ..., use_2nd_section_aspiration: _Optional[_Iterable[bool]] = ..., retract_height_over_2nd_section_to_empty_tip: _Optional[_Iterable[float]] = ..., dispensation_speed_during_emptying_tip: _Optional[_Iterable[float]] = ..., dosing_drive_speed_during_2nd_section_search: _Optional[_Iterable[float]] = ..., z_drive_speed_during_2nd_section_search: _Optional[_Iterable[float]] = ..., cup_upper_edge: _Optional[_Iterable[float]] = ..., ratio_liquid_rise_to_tip_deep_in: _Optional[_Iterable[int]] = ..., immersion_depth_2nd_section: _Optional[_Iterable[float]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., min_z_endpos: _Optional[float] = ..., liquid_surface_no_lld: _Optional[_Iterable[float]] = ..., probe_liquid_height: bool = ..., auto_surface_following_distance: bool = ..., disable_volume_correction: _Optional[_Iterable[bool]] = ...) -> None: ...

class AspirateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DispenseRequest(_message.Message):
    __slots__ = ("ops", "use_channels", "lld_search_height", "liquid_surface_no_lld", "pull_out_distance_transport_air", "second_section_height", "second_section_ratio", "minimum_height", "immersion_depth", "surface_following_distance", "cut_off_speed", "stop_back_volume", "transport_air_volume", "lld_mode", "dispense_position_above_z_touch_off", "gamma_lld_sensitivity", "dp_lld_sensitivity", "swap_speed", "settling_time", "mix_position_from_liquid_surface", "mix_surface_following_distance", "limit_curve_index", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "side_touch_off_distance", "jet", "blow_out", "empty", "probe_liquid_height", "auto_surface_following_distance", "disable_volume_correction")
    OPS_FIELD_NUMBER: _ClassVar[int]
    USE_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LIQUID_SURFACE_NO_LLD_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    CUT_OFF_SPEED_FIELD_NUMBER: _ClassVar[int]
    STOP_BACK_VOLUME_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_POSITION_ABOVE_Z_TOUCH_OFF_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    DP_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    SIDE_TOUCH_OFF_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    JET_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    PROBE_LIQUID_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    AUTO_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VOLUME_CORRECTION_FIELD_NUMBER: _ClassVar[int]
    ops: _containers.RepeatedCompositeFieldContainer[SingleChannelDispenseOp]
    use_channels: _containers.RepeatedScalarFieldContainer[int]
    lld_search_height: _containers.RepeatedScalarFieldContainer[float]
    liquid_surface_no_lld: _containers.RepeatedScalarFieldContainer[float]
    pull_out_distance_transport_air: _containers.RepeatedScalarFieldContainer[float]
    second_section_height: _containers.RepeatedScalarFieldContainer[float]
    second_section_ratio: _containers.RepeatedScalarFieldContainer[float]
    minimum_height: _containers.RepeatedScalarFieldContainer[float]
    immersion_depth: _containers.RepeatedScalarFieldContainer[float]
    surface_following_distance: _containers.RepeatedScalarFieldContainer[float]
    cut_off_speed: _containers.RepeatedScalarFieldContainer[float]
    stop_back_volume: _containers.RepeatedScalarFieldContainer[float]
    transport_air_volume: _containers.RepeatedScalarFieldContainer[float]
    lld_mode: _containers.RepeatedScalarFieldContainer[int]
    dispense_position_above_z_touch_off: _containers.RepeatedScalarFieldContainer[float]
    gamma_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    dp_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    swap_speed: _containers.RepeatedScalarFieldContainer[float]
    settling_time: _containers.RepeatedScalarFieldContainer[float]
    mix_position_from_liquid_surface: _containers.RepeatedScalarFieldContainer[float]
    mix_surface_following_distance: _containers.RepeatedScalarFieldContainer[float]
    limit_curve_index: _containers.RepeatedScalarFieldContainer[int]
    minimum_traverse_height_at_beginning_of_a_command: float
    min_z_endpos: float
    side_touch_off_distance: float
    jet: _containers.RepeatedScalarFieldContainer[bool]
    blow_out: _containers.RepeatedScalarFieldContainer[bool]
    empty: _containers.RepeatedScalarFieldContainer[bool]
    probe_liquid_height: bool
    auto_surface_following_distance: bool
    disable_volume_correction: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, ops: _Optional[_Iterable[_Union[SingleChannelDispenseOp, _Mapping]]] = ..., use_channels: _Optional[_Iterable[int]] = ..., lld_search_height: _Optional[_Iterable[float]] = ..., liquid_surface_no_lld: _Optional[_Iterable[float]] = ..., pull_out_distance_transport_air: _Optional[_Iterable[float]] = ..., second_section_height: _Optional[_Iterable[float]] = ..., second_section_ratio: _Optional[_Iterable[float]] = ..., minimum_height: _Optional[_Iterable[float]] = ..., immersion_depth: _Optional[_Iterable[float]] = ..., surface_following_distance: _Optional[_Iterable[float]] = ..., cut_off_speed: _Optional[_Iterable[float]] = ..., stop_back_volume: _Optional[_Iterable[float]] = ..., transport_air_volume: _Optional[_Iterable[float]] = ..., lld_mode: _Optional[_Iterable[int]] = ..., dispense_position_above_z_touch_off: _Optional[_Iterable[float]] = ..., gamma_lld_sensitivity: _Optional[_Iterable[int]] = ..., dp_lld_sensitivity: _Optional[_Iterable[int]] = ..., swap_speed: _Optional[_Iterable[float]] = ..., settling_time: _Optional[_Iterable[float]] = ..., mix_position_from_liquid_surface: _Optional[_Iterable[float]] = ..., mix_surface_following_distance: _Optional[_Iterable[float]] = ..., limit_curve_index: _Optional[_Iterable[int]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., min_z_endpos: _Optional[float] = ..., side_touch_off_distance: _Optional[float] = ..., jet: _Optional[_Iterable[bool]] = ..., blow_out: _Optional[_Iterable[bool]] = ..., empty: _Optional[_Iterable[bool]] = ..., probe_liquid_height: bool = ..., auto_surface_following_distance: bool = ..., disable_volume_correction: _Optional[_Iterable[bool]] = ...) -> None: ...

class DispenseResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PickUpTips96Request(_message.Message):
    __slots__ = ("pickup", "tip_pickup_method", "minimum_height_command_end", "minimum_traverse_height_at_beginning_of_a_command", "experimental_alignment_tipspot_identifier")
    PICKUP_FIELD_NUMBER: _ClassVar[int]
    TIP_PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENTAL_ALIGNMENT_TIPSPOT_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    pickup: PickupTipRackOp
    tip_pickup_method: str
    minimum_height_command_end: float
    minimum_traverse_height_at_beginning_of_a_command: float
    experimental_alignment_tipspot_identifier: str
    def __init__(self, pickup: _Optional[_Union[PickupTipRackOp, _Mapping]] = ..., tip_pickup_method: _Optional[str] = ..., minimum_height_command_end: _Optional[float] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., experimental_alignment_tipspot_identifier: _Optional[str] = ...) -> None: ...

class PickUpTips96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DropTips96Request(_message.Message):
    __slots__ = ("drop", "minimum_height_command_end", "minimum_traverse_height_at_beginning_of_a_command", "experimental_alignment_tipspot_identifier")
    DROP_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENTAL_ALIGNMENT_TIPSPOT_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    drop: DropTipRackOp
    minimum_height_command_end: float
    minimum_traverse_height_at_beginning_of_a_command: float
    experimental_alignment_tipspot_identifier: str
    def __init__(self, drop: _Optional[_Union[DropTipRackOp, _Mapping]] = ..., minimum_height_command_end: _Optional[float] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., experimental_alignment_tipspot_identifier: _Optional[str] = ...) -> None: ...

class DropTips96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Aspirate96Request(_message.Message):
    __slots__ = ("plate", "container", "jet", "blow_out", "use_lld", "pull_out_distance_transport_air", "aspiration_type", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "lld_search_height", "minimum_height", "second_section_height", "second_section_ratio", "immersion_depth", "surface_following_distance", "transport_air_volume", "pre_wetting_volume", "gamma_lld_sensitivity", "swap_speed", "settling_time", "mix_position_from_liquid_surface", "mix_surface_following_distance", "limit_curve_index", "disable_volume_correction")
    PLATE_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    JET_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_FIELD_NUMBER: _ClassVar[int]
    USE_LLD_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    PRE_WETTING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VOLUME_CORRECTION_FIELD_NUMBER: _ClassVar[int]
    plate: MultiHeadAspirationPlateOp
    container: MultiHeadAspirationContainerOp
    jet: bool
    blow_out: bool
    use_lld: bool
    pull_out_distance_transport_air: float
    aspiration_type: int
    minimum_traverse_height_at_beginning_of_a_command: float
    min_z_endpos: float
    lld_search_height: float
    minimum_height: float
    second_section_height: float
    second_section_ratio: float
    immersion_depth: float
    surface_following_distance: float
    transport_air_volume: float
    pre_wetting_volume: float
    gamma_lld_sensitivity: int
    swap_speed: float
    settling_time: float
    mix_position_from_liquid_surface: float
    mix_surface_following_distance: float
    limit_curve_index: int
    disable_volume_correction: bool
    def __init__(self, plate: _Optional[_Union[MultiHeadAspirationPlateOp, _Mapping]] = ..., container: _Optional[_Union[MultiHeadAspirationContainerOp, _Mapping]] = ..., jet: bool = ..., blow_out: bool = ..., use_lld: bool = ..., pull_out_distance_transport_air: _Optional[float] = ..., aspiration_type: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., min_z_endpos: _Optional[float] = ..., lld_search_height: _Optional[float] = ..., minimum_height: _Optional[float] = ..., second_section_height: _Optional[float] = ..., second_section_ratio: _Optional[float] = ..., immersion_depth: _Optional[float] = ..., surface_following_distance: _Optional[float] = ..., transport_air_volume: _Optional[float] = ..., pre_wetting_volume: _Optional[float] = ..., gamma_lld_sensitivity: _Optional[int] = ..., swap_speed: _Optional[float] = ..., settling_time: _Optional[float] = ..., mix_position_from_liquid_surface: _Optional[float] = ..., mix_surface_following_distance: _Optional[float] = ..., limit_curve_index: _Optional[int] = ..., disable_volume_correction: bool = ...) -> None: ...

class Aspirate96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Dispense96Request(_message.Message):
    __slots__ = ("plate", "container", "jet", "empty", "blow_out", "pull_out_distance_transport_air", "use_lld", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "lld_search_height", "minimum_height", "second_section_height", "second_section_ratio", "immersion_depth", "surface_following_distance", "transport_air_volume", "gamma_lld_sensitivity", "swap_speed", "settling_time", "mix_position_from_liquid_surface", "mix_surface_following_distance", "limit_curve_index", "cut_off_speed", "stop_back_volume", "disable_volume_correction")
    PLATE_FIELD_NUMBER: _ClassVar[int]
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    JET_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    USE_LLD_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    CUT_OFF_SPEED_FIELD_NUMBER: _ClassVar[int]
    STOP_BACK_VOLUME_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VOLUME_CORRECTION_FIELD_NUMBER: _ClassVar[int]
    plate: MultiHeadDispensePlateOp
    container: MultiHeadDispenseContainerOp
    jet: bool
    empty: bool
    blow_out: bool
    pull_out_distance_transport_air: float
    use_lld: bool
    minimum_traverse_height_at_beginning_of_a_command: float
    min_z_endpos: float
    lld_search_height: float
    minimum_height: float
    second_section_height: float
    second_section_ratio: float
    immersion_depth: float
    surface_following_distance: float
    transport_air_volume: float
    gamma_lld_sensitivity: int
    swap_speed: float
    settling_time: float
    mix_position_from_liquid_surface: float
    mix_surface_following_distance: float
    limit_curve_index: int
    cut_off_speed: float
    stop_back_volume: float
    disable_volume_correction: bool
    def __init__(self, plate: _Optional[_Union[MultiHeadDispensePlateOp, _Mapping]] = ..., container: _Optional[_Union[MultiHeadDispenseContainerOp, _Mapping]] = ..., jet: bool = ..., empty: bool = ..., blow_out: bool = ..., pull_out_distance_transport_air: _Optional[float] = ..., use_lld: bool = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., min_z_endpos: _Optional[float] = ..., lld_search_height: _Optional[float] = ..., minimum_height: _Optional[float] = ..., second_section_height: _Optional[float] = ..., second_section_ratio: _Optional[float] = ..., immersion_depth: _Optional[float] = ..., surface_following_distance: _Optional[float] = ..., transport_air_volume: _Optional[float] = ..., gamma_lld_sensitivity: _Optional[int] = ..., swap_speed: _Optional[float] = ..., settling_time: _Optional[float] = ..., mix_position_from_liquid_surface: _Optional[float] = ..., mix_surface_following_distance: _Optional[float] = ..., limit_curve_index: _Optional[int] = ..., cut_off_speed: _Optional[float] = ..., stop_back_volume: _Optional[float] = ..., disable_volume_correction: bool = ...) -> None: ...

class Dispense96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializePipRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializePipResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializePipettingChannelsRequest(_message.Message):
    __slots__ = ("x_positions", "y_positions", "begin_of_tip_deposit_process", "end_of_tip_deposit_process", "z_position_at_end_of_a_command", "tip_pattern", "tip_type", "discarding_method")
    X_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    BEGIN_OF_TIP_DEPOSIT_PROCESS_FIELD_NUMBER: _ClassVar[int]
    END_OF_TIP_DEPOSIT_PROCESS_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_END_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    TIP_TYPE_FIELD_NUMBER: _ClassVar[int]
    DISCARDING_METHOD_FIELD_NUMBER: _ClassVar[int]
    x_positions: _containers.RepeatedScalarFieldContainer[int]
    y_positions: _containers.RepeatedScalarFieldContainer[int]
    begin_of_tip_deposit_process: int
    end_of_tip_deposit_process: int
    z_position_at_end_of_a_command: int
    tip_pattern: _containers.RepeatedScalarFieldContainer[bool]
    tip_type: int
    discarding_method: int
    def __init__(self, x_positions: _Optional[_Iterable[int]] = ..., y_positions: _Optional[_Iterable[int]] = ..., begin_of_tip_deposit_process: _Optional[int] = ..., end_of_tip_deposit_process: _Optional[int] = ..., z_position_at_end_of_a_command: _Optional[int] = ..., tip_pattern: _Optional[_Iterable[bool]] = ..., tip_type: _Optional[int] = ..., discarding_method: _Optional[int] = ...) -> None: ...

class InitializePipettingChannelsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PickUpTipFwRequest(_message.Message):
    __slots__ = ("x_positions", "y_positions", "tip_pattern", "tip_type_idx", "begin_tip_pick_up_process", "end_tip_pick_up_process", "minimum_traverse_height_at_beginning_of_a_command", "pickup_method")
    X_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    TIP_TYPE_IDX_FIELD_NUMBER: _ClassVar[int]
    BEGIN_TIP_PICK_UP_PROCESS_FIELD_NUMBER: _ClassVar[int]
    END_TIP_PICK_UP_PROCESS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    x_positions: _containers.RepeatedScalarFieldContainer[int]
    y_positions: _containers.RepeatedScalarFieldContainer[int]
    tip_pattern: _containers.RepeatedScalarFieldContainer[bool]
    tip_type_idx: int
    begin_tip_pick_up_process: int
    end_tip_pick_up_process: int
    minimum_traverse_height_at_beginning_of_a_command: int
    pickup_method: int
    def __init__(self, x_positions: _Optional[_Iterable[int]] = ..., y_positions: _Optional[_Iterable[int]] = ..., tip_pattern: _Optional[_Iterable[bool]] = ..., tip_type_idx: _Optional[int] = ..., begin_tip_pick_up_process: _Optional[int] = ..., end_tip_pick_up_process: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., pickup_method: _Optional[int] = ...) -> None: ...

class PickUpTipFwResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DiscardTipFwRequest(_message.Message):
    __slots__ = ("x_positions", "y_positions", "tip_pattern", "begin_tip_deposit_process", "end_tip_deposit_process", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_end_of_a_command", "discarding_method")
    X_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    BEGIN_TIP_DEPOSIT_PROCESS_FIELD_NUMBER: _ClassVar[int]
    END_TIP_DEPOSIT_PROCESS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_END_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    DISCARDING_METHOD_FIELD_NUMBER: _ClassVar[int]
    x_positions: _containers.RepeatedScalarFieldContainer[int]
    y_positions: _containers.RepeatedScalarFieldContainer[int]
    tip_pattern: _containers.RepeatedScalarFieldContainer[bool]
    begin_tip_deposit_process: int
    end_tip_deposit_process: int
    minimum_traverse_height_at_beginning_of_a_command: int
    z_position_at_end_of_a_command: int
    discarding_method: int
    def __init__(self, x_positions: _Optional[_Iterable[int]] = ..., y_positions: _Optional[_Iterable[int]] = ..., tip_pattern: _Optional[_Iterable[bool]] = ..., begin_tip_deposit_process: _Optional[int] = ..., end_tip_deposit_process: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., z_position_at_end_of_a_command: _Optional[int] = ..., discarding_method: _Optional[int] = ...) -> None: ...

class DiscardTipFwResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AspiratePipRequest(_message.Message):
    __slots__ = ("aspiration_type", "tip_pattern", "x_positions", "y_positions", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "lld_search_height", "clot_detection_height", "liquid_surface_no_lld", "pull_out_distance_transport_air", "second_section_height", "second_section_ratio", "minimum_height", "immersion_depth", "immersion_depth_direction", "surface_following_distance", "aspiration_volumes", "aspiration_speed", "transport_air_volume", "blow_out_air_volume", "pre_wetting_volume", "lld_mode", "gamma_lld_sensitivity", "dp_lld_sensitivity", "aspirate_position_above_z_touch_off", "detection_height_difference_for_dual_lld", "swap_speed", "settling_time", "mix_volume", "mix_cycles", "mix_position_from_liquid_surface", "mix_speed", "mix_surface_following_distance", "limit_curve_index", "tadm_algorithm", "recording_mode", "use_2nd_section_aspiration", "retract_height_over_2nd_section_to_empty_tip", "dispensation_speed_during_emptying_tip", "dosing_drive_speed_during_2nd_section_search", "z_drive_speed_during_2nd_section_search", "cup_upper_edge")
    ASPIRATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    X_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    CLOT_DETECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LIQUID_SURFACE_NO_LLD_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_VOLUMES_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_SPEED_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    PRE_WETTING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    DP_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    ASPIRATE_POSITION_ABOVE_Z_TOUCH_OFF_FIELD_NUMBER: _ClassVar[int]
    DETECTION_HEIGHT_DIFFERENCE_FOR_DUAL_LLD_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_CYCLES_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SPEED_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    TADM_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    RECORDING_MODE_FIELD_NUMBER: _ClassVar[int]
    USE_2ND_SECTION_ASPIRATION_FIELD_NUMBER: _ClassVar[int]
    RETRACT_HEIGHT_OVER_2ND_SECTION_TO_EMPTY_TIP_FIELD_NUMBER: _ClassVar[int]
    DISPENSATION_SPEED_DURING_EMPTYING_TIP_FIELD_NUMBER: _ClassVar[int]
    DOSING_DRIVE_SPEED_DURING_2ND_SECTION_SEARCH_FIELD_NUMBER: _ClassVar[int]
    Z_DRIVE_SPEED_DURING_2ND_SECTION_SEARCH_FIELD_NUMBER: _ClassVar[int]
    CUP_UPPER_EDGE_FIELD_NUMBER: _ClassVar[int]
    aspiration_type: _containers.RepeatedScalarFieldContainer[int]
    tip_pattern: _containers.RepeatedScalarFieldContainer[bool]
    x_positions: _containers.RepeatedScalarFieldContainer[int]
    y_positions: _containers.RepeatedScalarFieldContainer[int]
    minimum_traverse_height_at_beginning_of_a_command: int
    min_z_endpos: int
    lld_search_height: _containers.RepeatedScalarFieldContainer[int]
    clot_detection_height: _containers.RepeatedScalarFieldContainer[int]
    liquid_surface_no_lld: _containers.RepeatedScalarFieldContainer[int]
    pull_out_distance_transport_air: _containers.RepeatedScalarFieldContainer[int]
    second_section_height: _containers.RepeatedScalarFieldContainer[int]
    second_section_ratio: _containers.RepeatedScalarFieldContainer[int]
    minimum_height: _containers.RepeatedScalarFieldContainer[int]
    immersion_depth: _containers.RepeatedScalarFieldContainer[int]
    immersion_depth_direction: _containers.RepeatedScalarFieldContainer[int]
    surface_following_distance: _containers.RepeatedScalarFieldContainer[int]
    aspiration_volumes: _containers.RepeatedScalarFieldContainer[int]
    aspiration_speed: _containers.RepeatedScalarFieldContainer[int]
    transport_air_volume: _containers.RepeatedScalarFieldContainer[int]
    blow_out_air_volume: _containers.RepeatedScalarFieldContainer[int]
    pre_wetting_volume: _containers.RepeatedScalarFieldContainer[int]
    lld_mode: _containers.RepeatedScalarFieldContainer[int]
    gamma_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    dp_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    aspirate_position_above_z_touch_off: _containers.RepeatedScalarFieldContainer[int]
    detection_height_difference_for_dual_lld: _containers.RepeatedScalarFieldContainer[int]
    swap_speed: _containers.RepeatedScalarFieldContainer[int]
    settling_time: _containers.RepeatedScalarFieldContainer[int]
    mix_volume: _containers.RepeatedScalarFieldContainer[int]
    mix_cycles: _containers.RepeatedScalarFieldContainer[int]
    mix_position_from_liquid_surface: _containers.RepeatedScalarFieldContainer[int]
    mix_speed: _containers.RepeatedScalarFieldContainer[int]
    mix_surface_following_distance: _containers.RepeatedScalarFieldContainer[int]
    limit_curve_index: _containers.RepeatedScalarFieldContainer[int]
    tadm_algorithm: bool
    recording_mode: int
    use_2nd_section_aspiration: _containers.RepeatedScalarFieldContainer[bool]
    retract_height_over_2nd_section_to_empty_tip: _containers.RepeatedScalarFieldContainer[int]
    dispensation_speed_during_emptying_tip: _containers.RepeatedScalarFieldContainer[int]
    dosing_drive_speed_during_2nd_section_search: _containers.RepeatedScalarFieldContainer[int]
    z_drive_speed_during_2nd_section_search: _containers.RepeatedScalarFieldContainer[int]
    cup_upper_edge: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, aspiration_type: _Optional[_Iterable[int]] = ..., tip_pattern: _Optional[_Iterable[bool]] = ..., x_positions: _Optional[_Iterable[int]] = ..., y_positions: _Optional[_Iterable[int]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., min_z_endpos: _Optional[int] = ..., lld_search_height: _Optional[_Iterable[int]] = ..., clot_detection_height: _Optional[_Iterable[int]] = ..., liquid_surface_no_lld: _Optional[_Iterable[int]] = ..., pull_out_distance_transport_air: _Optional[_Iterable[int]] = ..., second_section_height: _Optional[_Iterable[int]] = ..., second_section_ratio: _Optional[_Iterable[int]] = ..., minimum_height: _Optional[_Iterable[int]] = ..., immersion_depth: _Optional[_Iterable[int]] = ..., immersion_depth_direction: _Optional[_Iterable[int]] = ..., surface_following_distance: _Optional[_Iterable[int]] = ..., aspiration_volumes: _Optional[_Iterable[int]] = ..., aspiration_speed: _Optional[_Iterable[int]] = ..., transport_air_volume: _Optional[_Iterable[int]] = ..., blow_out_air_volume: _Optional[_Iterable[int]] = ..., pre_wetting_volume: _Optional[_Iterable[int]] = ..., lld_mode: _Optional[_Iterable[int]] = ..., gamma_lld_sensitivity: _Optional[_Iterable[int]] = ..., dp_lld_sensitivity: _Optional[_Iterable[int]] = ..., aspirate_position_above_z_touch_off: _Optional[_Iterable[int]] = ..., detection_height_difference_for_dual_lld: _Optional[_Iterable[int]] = ..., swap_speed: _Optional[_Iterable[int]] = ..., settling_time: _Optional[_Iterable[int]] = ..., mix_volume: _Optional[_Iterable[int]] = ..., mix_cycles: _Optional[_Iterable[int]] = ..., mix_position_from_liquid_surface: _Optional[_Iterable[int]] = ..., mix_speed: _Optional[_Iterable[int]] = ..., mix_surface_following_distance: _Optional[_Iterable[int]] = ..., limit_curve_index: _Optional[_Iterable[int]] = ..., tadm_algorithm: bool = ..., recording_mode: _Optional[int] = ..., use_2nd_section_aspiration: _Optional[_Iterable[bool]] = ..., retract_height_over_2nd_section_to_empty_tip: _Optional[_Iterable[int]] = ..., dispensation_speed_during_emptying_tip: _Optional[_Iterable[int]] = ..., dosing_drive_speed_during_2nd_section_search: _Optional[_Iterable[int]] = ..., z_drive_speed_during_2nd_section_search: _Optional[_Iterable[int]] = ..., cup_upper_edge: _Optional[_Iterable[int]] = ...) -> None: ...

class AspiratePipResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DispensePipRequest(_message.Message):
    __slots__ = ("tip_pattern", "dispensing_mode", "x_positions", "y_positions", "minimum_height", "lld_search_height", "liquid_surface_no_lld", "pull_out_distance_transport_air", "immersion_depth", "immersion_depth_direction", "surface_following_distance", "second_section_height", "second_section_ratio", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "dispense_volumes", "dispense_speed", "cut_off_speed", "stop_back_volume", "transport_air_volume", "blow_out_air_volume", "lld_mode", "side_touch_off_distance", "dispense_position_above_z_touch_off", "gamma_lld_sensitivity", "dp_lld_sensitivity", "swap_speed", "settling_time", "mix_volume", "mix_cycles", "mix_position_from_liquid_surface", "mix_speed", "mix_surface_following_distance", "limit_curve_index", "tadm_algorithm", "recording_mode")
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_MODE_FIELD_NUMBER: _ClassVar[int]
    X_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LIQUID_SURFACE_NO_LLD_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_VOLUMES_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_SPEED_FIELD_NUMBER: _ClassVar[int]
    CUT_OFF_SPEED_FIELD_NUMBER: _ClassVar[int]
    STOP_BACK_VOLUME_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    SIDE_TOUCH_OFF_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_POSITION_ABOVE_Z_TOUCH_OFF_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    DP_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_CYCLES_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SPEED_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    TADM_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    RECORDING_MODE_FIELD_NUMBER: _ClassVar[int]
    tip_pattern: _containers.RepeatedScalarFieldContainer[bool]
    dispensing_mode: _containers.RepeatedScalarFieldContainer[int]
    x_positions: _containers.RepeatedScalarFieldContainer[int]
    y_positions: _containers.RepeatedScalarFieldContainer[int]
    minimum_height: _containers.RepeatedScalarFieldContainer[int]
    lld_search_height: _containers.RepeatedScalarFieldContainer[int]
    liquid_surface_no_lld: _containers.RepeatedScalarFieldContainer[int]
    pull_out_distance_transport_air: _containers.RepeatedScalarFieldContainer[int]
    immersion_depth: _containers.RepeatedScalarFieldContainer[int]
    immersion_depth_direction: _containers.RepeatedScalarFieldContainer[int]
    surface_following_distance: _containers.RepeatedScalarFieldContainer[int]
    second_section_height: _containers.RepeatedScalarFieldContainer[int]
    second_section_ratio: _containers.RepeatedScalarFieldContainer[int]
    minimum_traverse_height_at_beginning_of_a_command: int
    min_z_endpos: int
    dispense_volumes: _containers.RepeatedScalarFieldContainer[int]
    dispense_speed: _containers.RepeatedScalarFieldContainer[int]
    cut_off_speed: _containers.RepeatedScalarFieldContainer[int]
    stop_back_volume: _containers.RepeatedScalarFieldContainer[int]
    transport_air_volume: _containers.RepeatedScalarFieldContainer[int]
    blow_out_air_volume: _containers.RepeatedScalarFieldContainer[int]
    lld_mode: _containers.RepeatedScalarFieldContainer[int]
    side_touch_off_distance: int
    dispense_position_above_z_touch_off: _containers.RepeatedScalarFieldContainer[int]
    gamma_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    dp_lld_sensitivity: _containers.RepeatedScalarFieldContainer[int]
    swap_speed: _containers.RepeatedScalarFieldContainer[int]
    settling_time: _containers.RepeatedScalarFieldContainer[int]
    mix_volume: _containers.RepeatedScalarFieldContainer[int]
    mix_cycles: _containers.RepeatedScalarFieldContainer[int]
    mix_position_from_liquid_surface: _containers.RepeatedScalarFieldContainer[int]
    mix_speed: _containers.RepeatedScalarFieldContainer[int]
    mix_surface_following_distance: _containers.RepeatedScalarFieldContainer[int]
    limit_curve_index: _containers.RepeatedScalarFieldContainer[int]
    tadm_algorithm: bool
    recording_mode: int
    def __init__(self, tip_pattern: _Optional[_Iterable[bool]] = ..., dispensing_mode: _Optional[_Iterable[int]] = ..., x_positions: _Optional[_Iterable[int]] = ..., y_positions: _Optional[_Iterable[int]] = ..., minimum_height: _Optional[_Iterable[int]] = ..., lld_search_height: _Optional[_Iterable[int]] = ..., liquid_surface_no_lld: _Optional[_Iterable[int]] = ..., pull_out_distance_transport_air: _Optional[_Iterable[int]] = ..., immersion_depth: _Optional[_Iterable[int]] = ..., immersion_depth_direction: _Optional[_Iterable[int]] = ..., surface_following_distance: _Optional[_Iterable[int]] = ..., second_section_height: _Optional[_Iterable[int]] = ..., second_section_ratio: _Optional[_Iterable[int]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., min_z_endpos: _Optional[int] = ..., dispense_volumes: _Optional[_Iterable[int]] = ..., dispense_speed: _Optional[_Iterable[int]] = ..., cut_off_speed: _Optional[_Iterable[int]] = ..., stop_back_volume: _Optional[_Iterable[int]] = ..., transport_air_volume: _Optional[_Iterable[int]] = ..., blow_out_air_volume: _Optional[_Iterable[int]] = ..., lld_mode: _Optional[_Iterable[int]] = ..., side_touch_off_distance: _Optional[int] = ..., dispense_position_above_z_touch_off: _Optional[_Iterable[int]] = ..., gamma_lld_sensitivity: _Optional[_Iterable[int]] = ..., dp_lld_sensitivity: _Optional[_Iterable[int]] = ..., swap_speed: _Optional[_Iterable[int]] = ..., settling_time: _Optional[_Iterable[int]] = ..., mix_volume: _Optional[_Iterable[int]] = ..., mix_cycles: _Optional[_Iterable[int]] = ..., mix_position_from_liquid_surface: _Optional[_Iterable[int]] = ..., mix_speed: _Optional[_Iterable[int]] = ..., mix_surface_following_distance: _Optional[_Iterable[int]] = ..., limit_curve_index: _Optional[_Iterable[int]] = ..., tadm_algorithm: bool = ..., recording_mode: _Optional[int] = ...) -> None: ...

class DispensePipResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SpreadPipChannelsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SpreadPipChannelsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveAllPipettingChannelsToDefinedPositionRequest(_message.Message):
    __slots__ = ("tip_pattern", "x_positions", "y_positions", "minimum_traverse_height_at_beginning_of_command", "z_endpos")
    TIP_PATTERN_FIELD_NUMBER: _ClassVar[int]
    X_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    tip_pattern: bool
    x_positions: int
    y_positions: int
    minimum_traverse_height_at_beginning_of_command: int
    z_endpos: int
    def __init__(self, tip_pattern: bool = ..., x_positions: _Optional[int] = ..., y_positions: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_command: _Optional[int] = ..., z_endpos: _Optional[int] = ...) -> None: ...

class MoveAllPipettingChannelsToDefinedPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DefineTipNeedleRequest(_message.Message):
    __slots__ = ("tip_type_table_index", "has_filter", "tip_length", "maximum_tip_volume", "tip_size", "pickup_method")
    TIP_TYPE_TABLE_INDEX_FIELD_NUMBER: _ClassVar[int]
    HAS_FILTER_FIELD_NUMBER: _ClassVar[int]
    TIP_LENGTH_FIELD_NUMBER: _ClassVar[int]
    MAXIMUM_TIP_VOLUME_FIELD_NUMBER: _ClassVar[int]
    TIP_SIZE_FIELD_NUMBER: _ClassVar[int]
    PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    tip_type_table_index: int
    has_filter: bool
    tip_length: int
    maximum_tip_volume: int
    tip_size: TipSizeEnum
    pickup_method: TipPickupMethod
    def __init__(self, tip_type_table_index: _Optional[int] = ..., has_filter: bool = ..., tip_length: _Optional[int] = ..., maximum_tip_volume: _Optional[int] = ..., tip_size: _Optional[_Union[TipSizeEnum, str]] = ..., pickup_method: _Optional[_Union[TipPickupMethod, str]] = ...) -> None: ...

class DefineTipNeedleResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ProbeLiquidHeightsRequest(_message.Message):
    __slots__ = ("container_names", "use_channels", "resource_offsets", "lld_mode", "search_speed", "n_replicates", "move_to_z_safety_after")
    CONTAINER_NAMES_FIELD_NUMBER: _ClassVar[int]
    USE_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    N_REPLICATES_FIELD_NUMBER: _ClassVar[int]
    MOVE_TO_Z_SAFETY_AFTER_FIELD_NUMBER: _ClassVar[int]
    container_names: _containers.RepeatedScalarFieldContainer[str]
    use_channels: _containers.RepeatedScalarFieldContainer[int]
    resource_offsets: _containers.RepeatedCompositeFieldContainer[Coordinate]
    lld_mode: int
    search_speed: float
    n_replicates: int
    move_to_z_safety_after: bool
    def __init__(self, container_names: _Optional[_Iterable[str]] = ..., use_channels: _Optional[_Iterable[int]] = ..., resource_offsets: _Optional[_Iterable[_Union[Coordinate, _Mapping]]] = ..., lld_mode: _Optional[int] = ..., search_speed: _Optional[float] = ..., n_replicates: _Optional[int] = ..., move_to_z_safety_after: bool = ...) -> None: ...

class ProbeLiquidHeightsResponse(_message.Message):
    __slots__ = ("heights",)
    HEIGHTS_FIELD_NUMBER: _ClassVar[int]
    heights: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, heights: _Optional[_Iterable[float]] = ...) -> None: ...

class ProbeLiquidVolumesRequest(_message.Message):
    __slots__ = ("container_names", "use_channels", "resource_offsets", "lld_mode", "search_speed", "n_replicates", "move_to_z_safety_after")
    CONTAINER_NAMES_FIELD_NUMBER: _ClassVar[int]
    USE_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    SEARCH_SPEED_FIELD_NUMBER: _ClassVar[int]
    N_REPLICATES_FIELD_NUMBER: _ClassVar[int]
    MOVE_TO_Z_SAFETY_AFTER_FIELD_NUMBER: _ClassVar[int]
    container_names: _containers.RepeatedScalarFieldContainer[str]
    use_channels: _containers.RepeatedScalarFieldContainer[int]
    resource_offsets: _containers.RepeatedCompositeFieldContainer[Coordinate]
    lld_mode: int
    search_speed: float
    n_replicates: int
    move_to_z_safety_after: bool
    def __init__(self, container_names: _Optional[_Iterable[str]] = ..., use_channels: _Optional[_Iterable[int]] = ..., resource_offsets: _Optional[_Iterable[_Union[Coordinate, _Mapping]]] = ..., lld_mode: _Optional[int] = ..., search_speed: _Optional[float] = ..., n_replicates: _Optional[int] = ..., move_to_z_safety_after: bool = ...) -> None: ...

class ProbeLiquidVolumesResponse(_message.Message):
    __slots__ = ("volumes",)
    VOLUMES_FIELD_NUMBER: _ClassVar[int]
    volumes: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, volumes: _Optional[_Iterable[float]] = ...) -> None: ...

class RequestTipPresenceRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestTipPresenceResponse(_message.Message):
    __slots__ = ("tip_presences",)
    TIP_PRESENCES_FIELD_NUMBER: _ClassVar[int]
    tip_presences: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, tip_presences: _Optional[_Iterable[int]] = ...) -> None: ...

class ChannelsSenseTipPresenceRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ChannelsSenseTipPresenceResponse(_message.Message):
    __slots__ = ("tip_presences",)
    TIP_PRESENCES_FIELD_NUMBER: _ClassVar[int]
    tip_presences: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, tip_presences: _Optional[_Iterable[int]] = ...) -> None: ...

class RequestPipHeightLastLldRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestPipHeightLastLldResponse(_message.Message):
    __slots__ = ("heights",)
    HEIGHTS_FIELD_NUMBER: _ClassVar[int]
    heights: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, heights: _Optional[_Iterable[float]] = ...) -> None: ...

class RequestTadmStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestTadmStatusResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestVolumeInTipRequest(_message.Message):
    __slots__ = ("channel",)
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: int
    def __init__(self, channel: _Optional[int] = ...) -> None: ...

class RequestVolumeInTipResponse(_message.Message):
    __slots__ = ("volume",)
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    volume: float
    def __init__(self, volume: _Optional[float] = ...) -> None: ...

class RequestTipLenOnChannelRequest(_message.Message):
    __slots__ = ("channel_idx",)
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    def __init__(self, channel_idx: _Optional[int] = ...) -> None: ...

class RequestTipLenOnChannelResponse(_message.Message):
    __slots__ = ("length",)
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    length: float
    def __init__(self, length: _Optional[float] = ...) -> None: ...

class RequestProbeZPositionRequest(_message.Message):
    __slots__ = ("channel_idx",)
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    def __init__(self, channel_idx: _Optional[int] = ...) -> None: ...

class RequestProbeZPositionResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class ClldProbeZHeightUsingChannelRequest(_message.Message):
    __slots__ = ("channel_idx", "lowest_reading_position", "highest_reading_position", "channel_speed", "gamma_lld_sensitivity")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    LOWEST_READING_POSITION_FIELD_NUMBER: _ClassVar[int]
    HIGHEST_READING_POSITION_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_SPEED_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    lowest_reading_position: int
    highest_reading_position: int
    channel_speed: int
    gamma_lld_sensitivity: int
    def __init__(self, channel_idx: _Optional[int] = ..., lowest_reading_position: _Optional[int] = ..., highest_reading_position: _Optional[int] = ..., channel_speed: _Optional[int] = ..., gamma_lld_sensitivity: _Optional[int] = ...) -> None: ...

class ClldProbeZHeightUsingChannelResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PlldProbeZHeightUsingChannelRequest(_message.Message):
    __slots__ = ("channel_idx", "lowest_reading_position", "highest_reading_position", "channel_speed", "dp_lld_sensitivity")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    LOWEST_READING_POSITION_FIELD_NUMBER: _ClassVar[int]
    HIGHEST_READING_POSITION_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_SPEED_FIELD_NUMBER: _ClassVar[int]
    DP_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    lowest_reading_position: int
    highest_reading_position: int
    channel_speed: int
    dp_lld_sensitivity: int
    def __init__(self, channel_idx: _Optional[int] = ..., lowest_reading_position: _Optional[int] = ..., highest_reading_position: _Optional[int] = ..., channel_speed: _Optional[int] = ..., dp_lld_sensitivity: _Optional[int] = ...) -> None: ...

class PlldProbeZHeightUsingChannelResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ZtouchProbeZHeightUsingChannelRequest(_message.Message):
    __slots__ = ("channel_idx", "lowest_reading_position", "highest_reading_position", "channel_speed")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    LOWEST_READING_POSITION_FIELD_NUMBER: _ClassVar[int]
    HIGHEST_READING_POSITION_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_SPEED_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    lowest_reading_position: int
    highest_reading_position: int
    channel_speed: int
    def __init__(self, channel_idx: _Optional[int] = ..., lowest_reading_position: _Optional[int] = ..., highest_reading_position: _Optional[int] = ..., channel_speed: _Optional[int] = ...) -> None: ...

class ZtouchProbeZHeightUsingChannelResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PierceFoilRequest(_message.Message):
    __slots__ = ("channel_idx", "x_position", "y_position", "z_start_position", "z_end_position", "z_speed", "minimum_traverse_height")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_START_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_END_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    x_position: int
    y_position: int
    z_start_position: int
    z_end_position: int
    z_speed: int
    minimum_traverse_height: int
    def __init__(self, channel_idx: _Optional[int] = ..., x_position: _Optional[int] = ..., y_position: _Optional[int] = ..., z_start_position: _Optional[int] = ..., z_end_position: _Optional[int] = ..., z_speed: _Optional[int] = ..., minimum_traverse_height: _Optional[int] = ...) -> None: ...

class PierceFoilResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PierceFoilHighLevelRequest(_message.Message):
    __slots__ = ("well_names", "piercing_channels", "hold_down_channels", "move_inwards", "spread", "one_by_one", "distance_from_bottom")
    WELL_NAMES_FIELD_NUMBER: _ClassVar[int]
    PIERCING_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    HOLD_DOWN_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    MOVE_INWARDS_FIELD_NUMBER: _ClassVar[int]
    SPREAD_FIELD_NUMBER: _ClassVar[int]
    ONE_BY_ONE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FROM_BOTTOM_FIELD_NUMBER: _ClassVar[int]
    well_names: _containers.RepeatedScalarFieldContainer[str]
    piercing_channels: _containers.RepeatedScalarFieldContainer[int]
    hold_down_channels: _containers.RepeatedScalarFieldContainer[int]
    move_inwards: float
    spread: str
    one_by_one: bool
    distance_from_bottom: float
    def __init__(self, well_names: _Optional[_Iterable[str]] = ..., piercing_channels: _Optional[_Iterable[int]] = ..., hold_down_channels: _Optional[_Iterable[int]] = ..., move_inwards: _Optional[float] = ..., spread: _Optional[str] = ..., one_by_one: bool = ..., distance_from_bottom: _Optional[float] = ...) -> None: ...

class PierceFoilHighLevelResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StepOffFoilRequest(_message.Message):
    __slots__ = ("channel_idx", "x_position", "y_position", "z_position", "minimum_traverse_height")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    x_position: int
    y_position: int
    z_position: int
    minimum_traverse_height: int
    def __init__(self, channel_idx: _Optional[int] = ..., x_position: _Optional[int] = ..., y_position: _Optional[int] = ..., z_position: _Optional[int] = ..., minimum_traverse_height: _Optional[int] = ...) -> None: ...

class StepOffFoilResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EmptyTipRequest(_message.Message):
    __slots__ = ("channel_idx", "holding_volume", "acceleration", "flow_rate", "current_limit")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    HOLDING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    holding_volume: float
    acceleration: float
    flow_rate: float
    current_limit: int
    def __init__(self, channel_idx: _Optional[int] = ..., holding_volume: _Optional[float] = ..., acceleration: _Optional[float] = ..., flow_rate: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class EmptyTipResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EmptyTipsRequest(_message.Message):
    __slots__ = ("channels", "holding_volume", "acceleration", "flow_rate", "current_limit")
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    HOLDING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    channels: _containers.RepeatedScalarFieldContainer[int]
    holding_volume: float
    acceleration: float
    flow_rate: float
    current_limit: int
    def __init__(self, channels: _Optional[_Iterable[int]] = ..., holding_volume: _Optional[float] = ..., acceleration: _Optional[float] = ..., flow_rate: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class EmptyTipsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveChannelXRequest(_message.Message):
    __slots__ = ("channel", "x")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    channel: int
    x: float
    def __init__(self, channel: _Optional[int] = ..., x: _Optional[float] = ...) -> None: ...

class MoveChannelXResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveChannelYRequest(_message.Message):
    __slots__ = ("channel", "y")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    channel: int
    y: float
    def __init__(self, channel: _Optional[int] = ..., y: _Optional[float] = ...) -> None: ...

class MoveChannelYResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveChannelZRequest(_message.Message):
    __slots__ = ("channel", "z")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    channel: int
    z: float
    def __init__(self, channel: _Optional[int] = ..., z: _Optional[float] = ...) -> None: ...

class MoveChannelZResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveChannelXRelativeRequest(_message.Message):
    __slots__ = ("channel", "distance")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    channel: int
    distance: float
    def __init__(self, channel: _Optional[int] = ..., distance: _Optional[float] = ...) -> None: ...

class MoveChannelXRelativeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveChannelYRelativeRequest(_message.Message):
    __slots__ = ("channel", "distance")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    channel: int
    distance: float
    def __init__(self, channel: _Optional[int] = ..., distance: _Optional[float] = ...) -> None: ...

class MoveChannelYRelativeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveChannelZRelativeRequest(_message.Message):
    __slots__ = ("channel", "distance")
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    channel: int
    distance: float
    def __init__(self, channel: _Optional[int] = ..., distance: _Optional[float] = ...) -> None: ...

class MoveChannelZRelativeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PrepareForManualChannelOperationRequest(_message.Message):
    __slots__ = ("channel",)
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: int
    def __init__(self, channel: _Optional[int] = ...) -> None: ...

class PrepareForManualChannelOperationResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveAllChannelsInZSafetyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveAllChannelsInZSafetyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionSinglePipettingChannelInYDirectionRequest(_message.Message):
    __slots__ = ("pipetting_channel_index", "y_position")
    PIPETTING_CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    pipetting_channel_index: int
    y_position: int
    def __init__(self, pipetting_channel_index: _Optional[int] = ..., y_position: _Optional[int] = ...) -> None: ...

class PositionSinglePipettingChannelInYDirectionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionSinglePipettingChannelInZDirectionRequest(_message.Message):
    __slots__ = ("pipetting_channel_index", "z_position")
    PIPETTING_CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    pipetting_channel_index: int
    z_position: int
    def __init__(self, pipetting_channel_index: _Optional[int] = ..., z_position: _Optional[int] = ...) -> None: ...

class PositionSinglePipettingChannelInZDirectionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionMaxFreeYForNRequest(_message.Message):
    __slots__ = ("pipetting_channel_index",)
    PIPETTING_CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    pipetting_channel_index: int
    def __init__(self, pipetting_channel_index: _Optional[int] = ...) -> None: ...

class PositionMaxFreeYForNResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestXPosChannelNRequest(_message.Message):
    __slots__ = ("pipetting_channel_index",)
    PIPETTING_CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    pipetting_channel_index: int
    def __init__(self, pipetting_channel_index: _Optional[int] = ...) -> None: ...

class RequestXPosChannelNResponse(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: float
    def __init__(self, x_position: _Optional[float] = ...) -> None: ...

class RequestYPosChannelNRequest(_message.Message):
    __slots__ = ("pipetting_channel_index",)
    PIPETTING_CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    pipetting_channel_index: int
    def __init__(self, pipetting_channel_index: _Optional[int] = ...) -> None: ...

class RequestYPosChannelNResponse(_message.Message):
    __slots__ = ("y_position",)
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    y_position: float
    def __init__(self, y_position: _Optional[float] = ...) -> None: ...

class RequestZPosChannelNRequest(_message.Message):
    __slots__ = ("pipetting_channel_index",)
    PIPETTING_CHANNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    pipetting_channel_index: int
    def __init__(self, pipetting_channel_index: _Optional[int] = ...) -> None: ...

class RequestZPosChannelNResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class RequestTipBottomZPositionRequest(_message.Message):
    __slots__ = ("channel_idx",)
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    def __init__(self, channel_idx: _Optional[int] = ...) -> None: ...

class RequestTipBottomZPositionResponse(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class GetChannelsYPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetChannelsYPositionsResponse(_message.Message):
    __slots__ = ("positions",)
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    positions: ChannelFloatMap
    def __init__(self, positions: _Optional[_Union[ChannelFloatMap, _Mapping]] = ...) -> None: ...

class PositionChannelsInYDirectionRequest(_message.Message):
    __slots__ = ("ys", "make_space")
    YS_FIELD_NUMBER: _ClassVar[int]
    MAKE_SPACE_FIELD_NUMBER: _ClassVar[int]
    ys: ChannelFloatMap
    make_space: bool
    def __init__(self, ys: _Optional[_Union[ChannelFloatMap, _Mapping]] = ..., make_space: bool = ...) -> None: ...

class PositionChannelsInYDirectionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetChannelsZPositionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetChannelsZPositionsResponse(_message.Message):
    __slots__ = ("positions",)
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    positions: ChannelFloatMap
    def __init__(self, positions: _Optional[_Union[ChannelFloatMap, _Mapping]] = ...) -> None: ...

class PositionChannelsInZDirectionRequest(_message.Message):
    __slots__ = ("zs",)
    ZS_FIELD_NUMBER: _ClassVar[int]
    zs: ChannelFloatMap
    def __init__(self, zs: _Optional[_Union[ChannelFloatMap, _Mapping]] = ...) -> None: ...

class PositionChannelsInZDirectionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestPipChannelVersionRequest(_message.Message):
    __slots__ = ("channel",)
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: int
    def __init__(self, channel: _Optional[int] = ...) -> None: ...

class RequestPipChannelVersionResponse(_message.Message):
    __slots__ = ("version",)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: str
    def __init__(self, version: _Optional[str] = ...) -> None: ...

class InitializeCore96HeadRequest(_message.Message):
    __slots__ = ("trash96_name", "z_position_at_the_command_end")
    TRASH96_NAME_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    trash96_name: str
    z_position_at_the_command_end: float
    def __init__(self, trash96_name: _Optional[str] = ..., z_position_at_the_command_end: _Optional[float] = ...) -> None: ...

class InitializeCore96HeadResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestCore96HeadInitializationStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestCore96HeadInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: bool = ...) -> None: ...

class Head96RequestFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96RequestFirmwareVersionResponse(_message.Message):
    __slots__ = ("date",)
    DATE_FIELD_NUMBER: _ClassVar[int]
    date: str
    def __init__(self, date: _Optional[str] = ...) -> None: ...

class Head96RequestTypeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96RequestTypeResponse(_message.Message):
    __slots__ = ("head_type",)
    HEAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    head_type: int
    def __init__(self, head_type: _Optional[int] = ...) -> None: ...

class Head96DispensingDriveAndSqueezerDriverInitializeRequest(_message.Message):
    __slots__ = ("squeezer_speed", "squeezer_acceleration", "squeezer_current_limit", "dispensing_drive_current_limit")
    SQUEEZER_SPEED_FIELD_NUMBER: _ClassVar[int]
    SQUEEZER_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    SQUEEZER_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    DISPENSING_DRIVE_CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    squeezer_speed: float
    squeezer_acceleration: float
    squeezer_current_limit: int
    dispensing_drive_current_limit: int
    def __init__(self, squeezer_speed: _Optional[float] = ..., squeezer_acceleration: _Optional[float] = ..., squeezer_current_limit: _Optional[int] = ..., dispensing_drive_current_limit: _Optional[int] = ...) -> None: ...

class Head96DispensingDriveAndSqueezerDriverInitializeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveCore96ToSafePositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveCore96ToSafePositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MoveToZSafetyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MoveToZSafetyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96ParkRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96ParkResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MoveXRequest(_message.Message):
    __slots__ = ("x",)
    X_FIELD_NUMBER: _ClassVar[int]
    x: float
    def __init__(self, x: _Optional[float] = ...) -> None: ...

class Head96MoveXResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MoveYRequest(_message.Message):
    __slots__ = ("y", "move_up_before", "move_down_after")
    Y_FIELD_NUMBER: _ClassVar[int]
    MOVE_UP_BEFORE_FIELD_NUMBER: _ClassVar[int]
    MOVE_DOWN_AFTER_FIELD_NUMBER: _ClassVar[int]
    y: float
    move_up_before: bool
    move_down_after: bool
    def __init__(self, y: _Optional[float] = ..., move_up_before: bool = ..., move_down_after: bool = ...) -> None: ...

class Head96MoveYResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MoveZRequest(_message.Message):
    __slots__ = ("z",)
    Z_FIELD_NUMBER: _ClassVar[int]
    z: float
    def __init__(self, z: _Optional[float] = ...) -> None: ...

class Head96MoveZResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveCore96HeadToDefinedPositionRequest(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class MoveCore96HeadToDefinedPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96MoveToCoordinateRequest(_message.Message):
    __slots__ = ("coordinate",)
    COORDINATE_FIELD_NUMBER: _ClassVar[int]
    coordinate: Coordinate
    def __init__(self, coordinate: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class Head96MoveToCoordinateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispensingDriveMoveToHomeVolumeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispensingDriveMoveToHomeVolumeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispensingDriveMoveToPositionRequest(_message.Message):
    __slots__ = ("position", "flow_rate", "current_limit")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    position: float
    flow_rate: float
    current_limit: int
    def __init__(self, position: _Optional[float] = ..., flow_rate: _Optional[float] = ..., current_limit: _Optional[int] = ...) -> None: ...

class Head96DispensingDriveMoveToPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispensingDriveRequestPositionMmRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispensingDriveRequestPositionMmResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: float
    def __init__(self, position: _Optional[float] = ...) -> None: ...

class Head96DispensingDriveRequestPositionUlRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96DispensingDriveRequestPositionUlResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: float
    def __init__(self, position: _Optional[float] = ...) -> None: ...

class Head96RequestTipPresenceRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96RequestTipPresenceResponse(_message.Message):
    __slots__ = ("tip_presence",)
    TIP_PRESENCE_FIELD_NUMBER: _ClassVar[int]
    tip_presence: int
    def __init__(self, tip_presence: _Optional[int] = ...) -> None: ...

class Head96RequestPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Head96RequestPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: Coordinate
    def __init__(self, position: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class PickUpTipsCore96Request(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "tip_type_idx", "tip_pickup_method", "z_deposit_position", "minimum_traverse_height_at_beginning_of_a_command", "minimum_height_command_end")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    TIP_TYPE_IDX_FIELD_NUMBER: _ClassVar[int]
    TIP_PICKUP_METHOD_FIELD_NUMBER: _ClassVar[int]
    Z_DEPOSIT_POSITION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    tip_type_idx: int
    tip_pickup_method: int
    z_deposit_position: int
    minimum_traverse_height_at_beginning_of_a_command: int
    minimum_height_command_end: int
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., tip_type_idx: _Optional[int] = ..., tip_pickup_method: _Optional[int] = ..., z_deposit_position: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., minimum_height_command_end: _Optional[int] = ...) -> None: ...

class PickUpTipsCore96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DiscardTipsCore96Request(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "z_deposit_position", "minimum_traverse_height_at_beginning_of_a_command", "minimum_height_command_end")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_DEPOSIT_POSITION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    z_deposit_position: int
    minimum_traverse_height_at_beginning_of_a_command: int
    minimum_height_command_end: int
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., z_deposit_position: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., minimum_height_command_end: _Optional[int] = ...) -> None: ...

class DiscardTipsCore96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AspirateCore96Request(_message.Message):
    __slots__ = ("aspiration_type", "x_position", "x_direction", "y_positions", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "lld_search_height", "liquid_surface_no_lld", "pull_out_distance_transport_air", "minimum_height", "second_section_height", "second_section_ratio", "immersion_depth", "immersion_depth_direction", "surface_following_distance", "aspiration_volumes", "aspiration_speed", "transport_air_volume", "blow_out_air_volume", "pre_wetting_volume", "lld_mode", "gamma_lld_sensitivity", "swap_speed", "settling_time", "mix_volume", "mix_cycles", "mix_position_from_liquid_surface", "mix_surface_following_distance", "speed_of_mix", "channel_pattern", "limit_curve_index", "tadm_algorithm", "recording_mode")
    ASPIRATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LIQUID_SURFACE_NO_LLD_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_VOLUMES_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_SPEED_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    PRE_WETTING_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_CYCLES_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    SPEED_OF_MIX_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_PATTERN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    TADM_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    RECORDING_MODE_FIELD_NUMBER: _ClassVar[int]
    aspiration_type: int
    x_position: int
    x_direction: int
    y_positions: int
    minimum_traverse_height_at_beginning_of_a_command: int
    min_z_endpos: int
    lld_search_height: int
    liquid_surface_no_lld: int
    pull_out_distance_transport_air: int
    minimum_height: int
    second_section_height: int
    second_section_ratio: int
    immersion_depth: int
    immersion_depth_direction: int
    surface_following_distance: int
    aspiration_volumes: int
    aspiration_speed: int
    transport_air_volume: int
    blow_out_air_volume: int
    pre_wetting_volume: int
    lld_mode: int
    gamma_lld_sensitivity: int
    swap_speed: int
    settling_time: int
    mix_volume: int
    mix_cycles: int
    mix_position_from_liquid_surface: int
    mix_surface_following_distance: int
    speed_of_mix: int
    channel_pattern: _containers.RepeatedScalarFieldContainer[bool]
    limit_curve_index: int
    tadm_algorithm: bool
    recording_mode: int
    def __init__(self, aspiration_type: _Optional[int] = ..., x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_positions: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., min_z_endpos: _Optional[int] = ..., lld_search_height: _Optional[int] = ..., liquid_surface_no_lld: _Optional[int] = ..., pull_out_distance_transport_air: _Optional[int] = ..., minimum_height: _Optional[int] = ..., second_section_height: _Optional[int] = ..., second_section_ratio: _Optional[int] = ..., immersion_depth: _Optional[int] = ..., immersion_depth_direction: _Optional[int] = ..., surface_following_distance: _Optional[int] = ..., aspiration_volumes: _Optional[int] = ..., aspiration_speed: _Optional[int] = ..., transport_air_volume: _Optional[int] = ..., blow_out_air_volume: _Optional[int] = ..., pre_wetting_volume: _Optional[int] = ..., lld_mode: _Optional[int] = ..., gamma_lld_sensitivity: _Optional[int] = ..., swap_speed: _Optional[int] = ..., settling_time: _Optional[int] = ..., mix_volume: _Optional[int] = ..., mix_cycles: _Optional[int] = ..., mix_position_from_liquid_surface: _Optional[int] = ..., mix_surface_following_distance: _Optional[int] = ..., speed_of_mix: _Optional[int] = ..., channel_pattern: _Optional[_Iterable[bool]] = ..., limit_curve_index: _Optional[int] = ..., tadm_algorithm: bool = ..., recording_mode: _Optional[int] = ...) -> None: ...

class AspirateCore96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DispenseCore96Request(_message.Message):
    __slots__ = ("dispensing_mode", "x_position", "x_direction", "y_positions", "minimum_traverse_height_at_beginning_of_a_command", "min_z_endpos", "lld_search_height", "liquid_surface_no_lld", "pull_out_distance_transport_air", "minimum_height", "second_section_height", "second_section_ratio", "immersion_depth", "immersion_depth_direction", "surface_following_distance", "dispense_volumes", "dispense_speed", "cut_off_speed", "stop_back_volume", "transport_air_volume", "blow_out_air_volume", "lld_mode", "gamma_lld_sensitivity", "swap_speed", "settling_time", "mix_volume", "mix_cycles", "mix_position_from_liquid_surface", "mix_surface_following_distance", "speed_of_mix", "channel_pattern", "limit_curve_index", "tadm_algorithm", "recording_mode")
    DISPENSING_MODE_FIELD_NUMBER: _ClassVar[int]
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MIN_Z_ENDPOS_FIELD_NUMBER: _ClassVar[int]
    LLD_SEARCH_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    LIQUID_SURFACE_NO_LLD_FIELD_NUMBER: _ClassVar[int]
    PULL_OUT_DISTANCE_TRANSPORT_AIR_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    SECOND_SECTION_RATIO_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_FIELD_NUMBER: _ClassVar[int]
    IMMERSION_DEPTH_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_VOLUMES_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_SPEED_FIELD_NUMBER: _ClassVar[int]
    CUT_OFF_SPEED_FIELD_NUMBER: _ClassVar[int]
    STOP_BACK_VOLUME_FIELD_NUMBER: _ClassVar[int]
    TRANSPORT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    BLOW_OUT_AIR_VOLUME_FIELD_NUMBER: _ClassVar[int]
    LLD_MODE_FIELD_NUMBER: _ClassVar[int]
    GAMMA_LLD_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    MIX_VOLUME_FIELD_NUMBER: _ClassVar[int]
    MIX_CYCLES_FIELD_NUMBER: _ClassVar[int]
    MIX_POSITION_FROM_LIQUID_SURFACE_FIELD_NUMBER: _ClassVar[int]
    MIX_SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    SPEED_OF_MIX_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_PATTERN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_CURVE_INDEX_FIELD_NUMBER: _ClassVar[int]
    TADM_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    RECORDING_MODE_FIELD_NUMBER: _ClassVar[int]
    dispensing_mode: int
    x_position: int
    x_direction: int
    y_positions: int
    minimum_traverse_height_at_beginning_of_a_command: int
    min_z_endpos: int
    lld_search_height: int
    liquid_surface_no_lld: int
    pull_out_distance_transport_air: int
    minimum_height: int
    second_section_height: int
    second_section_ratio: int
    immersion_depth: int
    immersion_depth_direction: int
    surface_following_distance: int
    dispense_volumes: int
    dispense_speed: int
    cut_off_speed: int
    stop_back_volume: int
    transport_air_volume: int
    blow_out_air_volume: int
    lld_mode: int
    gamma_lld_sensitivity: int
    swap_speed: int
    settling_time: int
    mix_volume: int
    mix_cycles: int
    mix_position_from_liquid_surface: int
    mix_surface_following_distance: int
    speed_of_mix: int
    channel_pattern: _containers.RepeatedScalarFieldContainer[bool]
    limit_curve_index: int
    tadm_algorithm: bool
    recording_mode: int
    def __init__(self, dispensing_mode: _Optional[int] = ..., x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_positions: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., min_z_endpos: _Optional[int] = ..., lld_search_height: _Optional[int] = ..., liquid_surface_no_lld: _Optional[int] = ..., pull_out_distance_transport_air: _Optional[int] = ..., minimum_height: _Optional[int] = ..., second_section_height: _Optional[int] = ..., second_section_ratio: _Optional[int] = ..., immersion_depth: _Optional[int] = ..., immersion_depth_direction: _Optional[int] = ..., surface_following_distance: _Optional[int] = ..., dispense_volumes: _Optional[int] = ..., dispense_speed: _Optional[int] = ..., cut_off_speed: _Optional[int] = ..., stop_back_volume: _Optional[int] = ..., transport_air_volume: _Optional[int] = ..., blow_out_air_volume: _Optional[int] = ..., lld_mode: _Optional[int] = ..., gamma_lld_sensitivity: _Optional[int] = ..., swap_speed: _Optional[int] = ..., settling_time: _Optional[int] = ..., mix_volume: _Optional[int] = ..., mix_cycles: _Optional[int] = ..., mix_position_from_liquid_surface: _Optional[int] = ..., mix_surface_following_distance: _Optional[int] = ..., speed_of_mix: _Optional[int] = ..., channel_pattern: _Optional[_Iterable[bool]] = ..., limit_curve_index: _Optional[int] = ..., tadm_algorithm: bool = ..., recording_mode: _Optional[int] = ...) -> None: ...

class DispenseCore96Response(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeIswapRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeIswapResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionComponentsForFreeIswapYRangeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionComponentsForFreeIswapYRangeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveIswapXRelativeRequest(_message.Message):
    __slots__ = ("step_size", "allow_splitting")
    STEP_SIZE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_SPLITTING_FIELD_NUMBER: _ClassVar[int]
    step_size: float
    allow_splitting: bool
    def __init__(self, step_size: _Optional[float] = ..., allow_splitting: bool = ...) -> None: ...

class MoveIswapXRelativeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveIswapYRelativeRequest(_message.Message):
    __slots__ = ("step_size", "allow_splitting")
    STEP_SIZE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_SPLITTING_FIELD_NUMBER: _ClassVar[int]
    step_size: float
    allow_splitting: bool
    def __init__(self, step_size: _Optional[float] = ..., allow_splitting: bool = ...) -> None: ...

class MoveIswapYRelativeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveIswapZRelativeRequest(_message.Message):
    __slots__ = ("step_size", "allow_splitting")
    STEP_SIZE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_SPLITTING_FIELD_NUMBER: _ClassVar[int]
    step_size: float
    allow_splitting: bool
    def __init__(self, step_size: _Optional[float] = ..., allow_splitting: bool = ...) -> None: ...

class MoveIswapZRelativeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveIswapXRequest(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: float
    def __init__(self, x_position: _Optional[float] = ...) -> None: ...

class MoveIswapXResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveIswapYRequest(_message.Message):
    __slots__ = ("y_position",)
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    y_position: float
    def __init__(self, y_position: _Optional[float] = ...) -> None: ...

class MoveIswapYResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveIswapZRequest(_message.Message):
    __slots__ = ("z_position",)
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    z_position: float
    def __init__(self, z_position: _Optional[float] = ...) -> None: ...

class MoveIswapZResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OpenNotInitializedGripperRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OpenNotInitializedGripperResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapOpenGripperRequest(_message.Message):
    __slots__ = ("open_position",)
    OPEN_POSITION_FIELD_NUMBER: _ClassVar[int]
    open_position: float
    def __init__(self, open_position: _Optional[float] = ...) -> None: ...

class IswapOpenGripperResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapCloseGripperRequest(_message.Message):
    __slots__ = ("grip_strength", "plate_width", "plate_width_tolerance")
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    grip_strength: int
    plate_width: float
    plate_width_tolerance: float
    def __init__(self, grip_strength: _Optional[int] = ..., plate_width: _Optional[float] = ..., plate_width_tolerance: _Optional[float] = ...) -> None: ...

class IswapCloseGripperResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ParkIswapRequest(_message.Message):
    __slots__ = ("minimum_traverse_height_at_beginning_of_a_command",)
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    minimum_traverse_height_at_beginning_of_a_command: int
    def __init__(self, minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ...) -> None: ...

class ParkIswapResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapGetPlateRequest(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "y_direction", "z_position", "z_direction", "grip_direction", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_the_command_end", "grip_strength", "open_gripper_position", "plate_width", "plate_width_tolerance", "collision_control_level", "acceleration_index_high_acc", "acceleration_index_low_acc", "iswap_fold_up_sequence_at_the_end_of_process")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    GRIP_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    OPEN_GRIPPER_POSITION_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    COLLISION_CONTROL_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_HIGH_ACC_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_LOW_ACC_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FOLD_UP_SEQUENCE_AT_THE_END_OF_PROCESS_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    y_direction: int
    z_position: int
    z_direction: int
    grip_direction: int
    minimum_traverse_height_at_beginning_of_a_command: int
    z_position_at_the_command_end: int
    grip_strength: int
    open_gripper_position: int
    plate_width: int
    plate_width_tolerance: int
    collision_control_level: int
    acceleration_index_high_acc: int
    acceleration_index_low_acc: int
    iswap_fold_up_sequence_at_the_end_of_process: bool
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., y_direction: _Optional[int] = ..., z_position: _Optional[int] = ..., z_direction: _Optional[int] = ..., grip_direction: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., z_position_at_the_command_end: _Optional[int] = ..., grip_strength: _Optional[int] = ..., open_gripper_position: _Optional[int] = ..., plate_width: _Optional[int] = ..., plate_width_tolerance: _Optional[int] = ..., collision_control_level: _Optional[int] = ..., acceleration_index_high_acc: _Optional[int] = ..., acceleration_index_low_acc: _Optional[int] = ..., iswap_fold_up_sequence_at_the_end_of_process: bool = ...) -> None: ...

class IswapGetPlateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapPutPlateRequest(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "y_direction", "z_position", "z_direction", "grip_direction", "z_position_at_the_command_end", "minimum_traverse_height_at_beginning_of_a_command", "open_gripper_position", "grip_strength", "iswap_fold_up_sequence_at_the_end_of_process")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    GRIP_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    OPEN_GRIPPER_POSITION_FIELD_NUMBER: _ClassVar[int]
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FOLD_UP_SEQUENCE_AT_THE_END_OF_PROCESS_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    y_direction: int
    z_position: int
    z_direction: int
    grip_direction: int
    z_position_at_the_command_end: int
    minimum_traverse_height_at_beginning_of_a_command: int
    open_gripper_position: int
    grip_strength: int
    iswap_fold_up_sequence_at_the_end_of_process: bool
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., y_direction: _Optional[int] = ..., z_position: _Optional[int] = ..., z_direction: _Optional[int] = ..., grip_direction: _Optional[int] = ..., z_position_at_the_command_end: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., open_gripper_position: _Optional[int] = ..., grip_strength: _Optional[int] = ..., iswap_fold_up_sequence_at_the_end_of_process: bool = ...) -> None: ...

class IswapPutPlateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MovePlateToPositionRequest(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "y_direction", "z_position", "z_direction", "grip_direction", "minimum_traverse_height_at_beginning_of_a_command", "collision_control_level", "acceleration_index_high_acc", "acceleration_index_low_acc")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    GRIP_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    COLLISION_CONTROL_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_HIGH_ACC_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_LOW_ACC_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    y_direction: int
    z_position: int
    z_direction: int
    grip_direction: int
    minimum_traverse_height_at_beginning_of_a_command: int
    collision_control_level: int
    acceleration_index_high_acc: int
    acceleration_index_low_acc: int
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., y_direction: _Optional[int] = ..., z_position: _Optional[int] = ..., z_direction: _Optional[int] = ..., grip_direction: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., collision_control_level: _Optional[int] = ..., acceleration_index_high_acc: _Optional[int] = ..., acceleration_index_low_acc: _Optional[int] = ...) -> None: ...

class MovePlateToPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CollapseGripperArmRequest(_message.Message):
    __slots__ = ("minimum_traverse_height_at_beginning_of_a_command", "iswap_fold_up_sequence_at_the_end_of_process")
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FOLD_UP_SEQUENCE_AT_THE_END_OF_PROCESS_FIELD_NUMBER: _ClassVar[int]
    minimum_traverse_height_at_beginning_of_a_command: int
    iswap_fold_up_sequence_at_the_end_of_process: bool
    def __init__(self, minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., iswap_fold_up_sequence_at_the_end_of_process: bool = ...) -> None: ...

class CollapseGripperArmResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapRotateRequest(_message.Message):
    __slots__ = ("orientation",)
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    orientation: RotationDriveOrientationEnum
    def __init__(self, orientation: _Optional[_Union[RotationDriveOrientationEnum, str]] = ...) -> None: ...

class IswapRotateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RotateIswapRotationDriveRequest(_message.Message):
    __slots__ = ("orientation",)
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    orientation: RotationDriveOrientationEnum
    def __init__(self, orientation: _Optional[_Union[RotationDriveOrientationEnum, str]] = ...) -> None: ...

class RotateIswapRotationDriveResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RotateIswapWristRequest(_message.Message):
    __slots__ = ("orientation",)
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    orientation: WristDriveOrientationEnum
    def __init__(self, orientation: _Optional[_Union[WristDriveOrientationEnum, str]] = ...) -> None: ...

class RotateIswapWristResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapDangerousReleaseBreakRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapDangerousReleaseBreakResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapReengageBreakRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapReengageBreakResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapInitializeZAxisRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapInitializeZAxisResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapRotationDrivePositionIncrementsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapRotationDrivePositionIncrementsResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: int
    def __init__(self, position: _Optional[int] = ...) -> None: ...

class RequestIswapRotationDriveOrientationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapRotationDriveOrientationResponse(_message.Message):
    __slots__ = ("orientation",)
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    orientation: RotationDriveOrientationEnum
    def __init__(self, orientation: _Optional[_Union[RotationDriveOrientationEnum, str]] = ...) -> None: ...

class RequestIswapWristDrivePositionIncrementsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapWristDrivePositionIncrementsResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: int
    def __init__(self, position: _Optional[int] = ...) -> None: ...

class RequestIswapWristDriveOrientationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapWristDriveOrientationResponse(_message.Message):
    __slots__ = ("orientation",)
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    orientation: WristDriveOrientationEnum
    def __init__(self, orientation: _Optional[_Union[WristDriveOrientationEnum, str]] = ...) -> None: ...

class RequestIswapInParkingPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapInParkingPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestPlateInIswapRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestPlateInIswapResponse(_message.Message):
    __slots__ = ("plate_in_iswap",)
    PLATE_IN_ISWAP_FIELD_NUMBER: _ClassVar[int]
    plate_in_iswap: bool
    def __init__(self, plate_in_iswap: bool = ...) -> None: ...

class RequestIswapPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: Coordinate
    def __init__(self, position: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class IswapRotationDriveRequestYRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapRotationDriveRequestYResponse(_message.Message):
    __slots__ = ("y",)
    Y_FIELD_NUMBER: _ClassVar[int]
    y: float
    def __init__(self, y: _Optional[float] = ...) -> None: ...

class RequestIswapInitializationStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: bool = ...) -> None: ...

class RequestIswapVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestIswapVersionResponse(_message.Message):
    __slots__ = ("version",)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: str
    def __init__(self, version: _Optional[str] = ...) -> None: ...

class GetIswapVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetIswapVersionResponse(_message.Message):
    __slots__ = ("version",)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: str
    def __init__(self, version: _Optional[str] = ...) -> None: ...

class SlowIswapRequest(_message.Message):
    __slots__ = ("wrist_velocity", "gripper_velocity")
    WRIST_VELOCITY_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_VELOCITY_FIELD_NUMBER: _ClassVar[int]
    wrist_velocity: int
    gripper_velocity: int
    def __init__(self, wrist_velocity: _Optional[int] = ..., gripper_velocity: _Optional[int] = ...) -> None: ...

class SlowIswapResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IswapMovePickedUpResourceRequest(_message.Message):
    __slots__ = ("center", "grip_direction", "minimum_traverse_height_at_beginning_of_a_command", "collision_control_level", "acceleration_index_high_acc", "acceleration_index_low_acc")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    GRIP_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    COLLISION_CONTROL_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_HIGH_ACC_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_LOW_ACC_FIELD_NUMBER: _ClassVar[int]
    center: Coordinate
    grip_direction: GripDirectionEnum
    minimum_traverse_height_at_beginning_of_a_command: float
    collision_control_level: int
    acceleration_index_high_acc: int
    acceleration_index_low_acc: int
    def __init__(self, center: _Optional[_Union[Coordinate, _Mapping]] = ..., grip_direction: _Optional[_Union[GripDirectionEnum, str]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., collision_control_level: _Optional[int] = ..., acceleration_index_high_acc: _Optional[int] = ..., acceleration_index_low_acc: _Optional[int] = ...) -> None: ...

class IswapMovePickedUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PickUpResourceRequest(_message.Message):
    __slots__ = ("pickup", "use_arm", "core_front_channel", "iswap_grip_strength", "core_grip_strength", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_the_command_end", "plate_width_tolerance", "open_gripper_position", "hotel_depth", "hotel_clearance_height", "high_speed", "plate_width", "use_unsafe_hotel", "iswap_collision_control_level", "iswap_fold_up_sequence_at_the_end_of_process")
    PICKUP_FIELD_NUMBER: _ClassVar[int]
    USE_ARM_FIELD_NUMBER: _ClassVar[int]
    CORE_FRONT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    ISWAP_GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    CORE_GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    OPEN_GRIPPER_POSITION_FIELD_NUMBER: _ClassVar[int]
    HOTEL_DEPTH_FIELD_NUMBER: _ClassVar[int]
    HOTEL_CLEARANCE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    HIGH_SPEED_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    USE_UNSAFE_HOTEL_FIELD_NUMBER: _ClassVar[int]
    ISWAP_COLLISION_CONTROL_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FOLD_UP_SEQUENCE_AT_THE_END_OF_PROCESS_FIELD_NUMBER: _ClassVar[int]
    pickup: ResourcePickupOp
    use_arm: str
    core_front_channel: int
    iswap_grip_strength: int
    core_grip_strength: int
    minimum_traverse_height_at_beginning_of_a_command: float
    z_position_at_the_command_end: float
    plate_width_tolerance: float
    open_gripper_position: float
    hotel_depth: float
    hotel_clearance_height: float
    high_speed: bool
    plate_width: float
    use_unsafe_hotel: bool
    iswap_collision_control_level: int
    iswap_fold_up_sequence_at_the_end_of_process: bool
    def __init__(self, pickup: _Optional[_Union[ResourcePickupOp, _Mapping]] = ..., use_arm: _Optional[str] = ..., core_front_channel: _Optional[int] = ..., iswap_grip_strength: _Optional[int] = ..., core_grip_strength: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., z_position_at_the_command_end: _Optional[float] = ..., plate_width_tolerance: _Optional[float] = ..., open_gripper_position: _Optional[float] = ..., hotel_depth: _Optional[float] = ..., hotel_clearance_height: _Optional[float] = ..., high_speed: bool = ..., plate_width: _Optional[float] = ..., use_unsafe_hotel: bool = ..., iswap_collision_control_level: _Optional[int] = ..., iswap_fold_up_sequence_at_the_end_of_process: bool = ...) -> None: ...

class PickUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MovePickedUpResourceRequest(_message.Message):
    __slots__ = ("move", "use_arm")
    MOVE_FIELD_NUMBER: _ClassVar[int]
    USE_ARM_FIELD_NUMBER: _ClassVar[int]
    move: ResourceMoveOp
    use_arm: str
    def __init__(self, move: _Optional[_Union[ResourceMoveOp, _Mapping]] = ..., use_arm: _Optional[str] = ...) -> None: ...

class MovePickedUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DropResourceRequest(_message.Message):
    __slots__ = ("drop", "use_arm", "return_core_gripper", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_the_command_end", "open_gripper_position", "hotel_depth", "hotel_clearance_height", "hotel_high_speed", "use_unsafe_hotel", "iswap_collision_control_level", "iswap_fold_up_sequence_at_the_end_of_process")
    DROP_FIELD_NUMBER: _ClassVar[int]
    USE_ARM_FIELD_NUMBER: _ClassVar[int]
    RETURN_CORE_GRIPPER_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    OPEN_GRIPPER_POSITION_FIELD_NUMBER: _ClassVar[int]
    HOTEL_DEPTH_FIELD_NUMBER: _ClassVar[int]
    HOTEL_CLEARANCE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    HOTEL_HIGH_SPEED_FIELD_NUMBER: _ClassVar[int]
    USE_UNSAFE_HOTEL_FIELD_NUMBER: _ClassVar[int]
    ISWAP_COLLISION_CONTROL_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FOLD_UP_SEQUENCE_AT_THE_END_OF_PROCESS_FIELD_NUMBER: _ClassVar[int]
    drop: ResourceDropOp
    use_arm: str
    return_core_gripper: bool
    minimum_traverse_height_at_beginning_of_a_command: float
    z_position_at_the_command_end: float
    open_gripper_position: float
    hotel_depth: float
    hotel_clearance_height: float
    hotel_high_speed: bool
    use_unsafe_hotel: bool
    iswap_collision_control_level: int
    iswap_fold_up_sequence_at_the_end_of_process: bool
    def __init__(self, drop: _Optional[_Union[ResourceDropOp, _Mapping]] = ..., use_arm: _Optional[str] = ..., return_core_gripper: bool = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., z_position_at_the_command_end: _Optional[float] = ..., open_gripper_position: _Optional[float] = ..., hotel_depth: _Optional[float] = ..., hotel_clearance_height: _Optional[float] = ..., hotel_high_speed: bool = ..., use_unsafe_hotel: bool = ..., iswap_collision_control_level: _Optional[int] = ..., iswap_fold_up_sequence_at_the_end_of_process: bool = ...) -> None: ...

class DropResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PickUpCoreGripperToolsRequest(_message.Message):
    __slots__ = ("front_channel", "front_offset", "back_offset")
    FRONT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    FRONT_OFFSET_FIELD_NUMBER: _ClassVar[int]
    BACK_OFFSET_FIELD_NUMBER: _ClassVar[int]
    front_channel: int
    front_offset: Coordinate
    back_offset: Coordinate
    def __init__(self, front_channel: _Optional[int] = ..., front_offset: _Optional[_Union[Coordinate, _Mapping]] = ..., back_offset: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class PickUpCoreGripperToolsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ReturnCoreGripperToolsRequest(_message.Message):
    __slots__ = ("front_offset", "back_offset")
    FRONT_OFFSET_FIELD_NUMBER: _ClassVar[int]
    BACK_OFFSET_FIELD_NUMBER: _ClassVar[int]
    front_offset: Coordinate
    back_offset: Coordinate
    def __init__(self, front_offset: _Optional[_Union[Coordinate, _Mapping]] = ..., back_offset: _Optional[_Union[Coordinate, _Mapping]] = ...) -> None: ...

class ReturnCoreGripperToolsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreOpenGripperRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreOpenGripperResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreGetPlateRequest(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "y_gripping_speed", "z_position", "z_speed", "open_gripper_position", "plate_width", "grip_strength", "minimum_traverse_height_at_beginning_of_a_command", "minimum_z_position_at_the_command_end")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Y_GRIPPING_SPEED_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    OPEN_GRIPPER_POSITION_FIELD_NUMBER: _ClassVar[int]
    PLATE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    y_gripping_speed: int
    z_position: int
    z_speed: int
    open_gripper_position: int
    plate_width: int
    grip_strength: int
    minimum_traverse_height_at_beginning_of_a_command: int
    minimum_z_position_at_the_command_end: int
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., y_gripping_speed: _Optional[int] = ..., z_position: _Optional[int] = ..., z_speed: _Optional[int] = ..., open_gripper_position: _Optional[int] = ..., plate_width: _Optional[int] = ..., grip_strength: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., minimum_z_position_at_the_command_end: _Optional[int] = ...) -> None: ...

class CoreGetPlateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CorePutPlateRequest(_message.Message):
    __slots__ = ("x_position", "x_direction", "y_position", "z_position", "z_press_on_distance", "z_speed", "open_gripper_position", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_the_command_end", "return_tool")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_PRESS_ON_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    OPEN_GRIPPER_POSITION_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    RETURN_TOOL_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    y_position: int
    z_position: int
    z_press_on_distance: int
    z_speed: int
    open_gripper_position: int
    minimum_traverse_height_at_beginning_of_a_command: int
    z_position_at_the_command_end: int
    return_tool: bool
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., y_position: _Optional[int] = ..., z_position: _Optional[int] = ..., z_press_on_distance: _Optional[int] = ..., z_speed: _Optional[int] = ..., open_gripper_position: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ..., z_position_at_the_command_end: _Optional[int] = ..., return_tool: bool = ...) -> None: ...

class CorePutPlateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreMovePlateToPositionRequest(_message.Message):
    __slots__ = ("x_position", "x_direction", "x_acceleration_index", "y_position", "z_position", "z_speed", "minimum_traverse_height_at_beginning_of_a_command")
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    X_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    X_ACCELERATION_INDEX_FIELD_NUMBER: _ClassVar[int]
    Y_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    x_direction: int
    x_acceleration_index: int
    y_position: int
    z_position: int
    z_speed: int
    minimum_traverse_height_at_beginning_of_a_command: int
    def __init__(self, x_position: _Optional[int] = ..., x_direction: _Optional[int] = ..., x_acceleration_index: _Optional[int] = ..., y_position: _Optional[int] = ..., z_position: _Optional[int] = ..., z_speed: _Optional[int] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[int] = ...) -> None: ...

class CoreMovePlateToPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CorePickUpResourceRequest(_message.Message):
    __slots__ = ("resource_name", "pickup_distance_from_top", "offset", "minimum_traverse_height_at_beginning_of_a_command", "minimum_z_position_at_the_command_end", "grip_strength", "z_speed", "y_gripping_speed", "front_channel")
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_TOP_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    GRIP_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    Y_GRIPPING_SPEED_FIELD_NUMBER: _ClassVar[int]
    FRONT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    resource_name: str
    pickup_distance_from_top: float
    offset: Coordinate
    minimum_traverse_height_at_beginning_of_a_command: float
    minimum_z_position_at_the_command_end: float
    grip_strength: int
    z_speed: float
    y_gripping_speed: float
    front_channel: int
    def __init__(self, resource_name: _Optional[str] = ..., pickup_distance_from_top: _Optional[float] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., minimum_z_position_at_the_command_end: _Optional[float] = ..., grip_strength: _Optional[int] = ..., z_speed: _Optional[float] = ..., y_gripping_speed: _Optional[float] = ..., front_channel: _Optional[int] = ...) -> None: ...

class CorePickUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreMovePickedUpResourceRequest(_message.Message):
    __slots__ = ("center", "minimum_traverse_height_at_beginning_of_a_command", "acceleration_index", "z_speed")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_INDEX_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    center: Coordinate
    minimum_traverse_height_at_beginning_of_a_command: float
    acceleration_index: int
    z_speed: float
    def __init__(self, center: _Optional[_Union[Coordinate, _Mapping]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., acceleration_index: _Optional[int] = ..., z_speed: _Optional[float] = ...) -> None: ...

class CoreMovePickedUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreReleasePickedUpResourceRequest(_message.Message):
    __slots__ = ("location", "resource_name", "pickup_distance_from_top", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_the_command_end", "return_tool")
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    PICKUP_DISTANCE_FROM_TOP_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    RETURN_TOOL_FIELD_NUMBER: _ClassVar[int]
    location: Coordinate
    resource_name: str
    pickup_distance_from_top: float
    minimum_traverse_height_at_beginning_of_a_command: float
    z_position_at_the_command_end: float
    return_tool: bool
    def __init__(self, location: _Optional[_Union[Coordinate, _Mapping]] = ..., resource_name: _Optional[str] = ..., pickup_distance_from_top: _Optional[float] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., z_position_at_the_command_end: _Optional[float] = ..., return_tool: bool = ...) -> None: ...

class CoreReleasePickedUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreCheckResourceExistsAtLocationCenterRequest(_message.Message):
    __slots__ = ("location", "resource_name", "gripper_y_margin", "offset", "minimum_traverse_height_at_beginning_of_a_command", "z_position_at_the_command_end", "enable_recovery", "audio_feedback")
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_Y_MARGIN_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_POSITION_AT_THE_COMMAND_END_FIELD_NUMBER: _ClassVar[int]
    ENABLE_RECOVERY_FIELD_NUMBER: _ClassVar[int]
    AUDIO_FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    location: Coordinate
    resource_name: str
    gripper_y_margin: float
    offset: Coordinate
    minimum_traverse_height_at_beginning_of_a_command: float
    z_position_at_the_command_end: float
    enable_recovery: bool
    audio_feedback: bool
    def __init__(self, location: _Optional[_Union[Coordinate, _Mapping]] = ..., resource_name: _Optional[str] = ..., gripper_y_margin: _Optional[float] = ..., offset: _Optional[_Union[Coordinate, _Mapping]] = ..., minimum_traverse_height_at_beginning_of_a_command: _Optional[float] = ..., z_position_at_the_command_end: _Optional[float] = ..., enable_recovery: bool = ..., audio_feedback: bool = ...) -> None: ...

class CoreCheckResourceExistsAtLocationCenterResponse(_message.Message):
    __slots__ = ("exists",)
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    exists: bool
    def __init__(self, exists: bool = ...) -> None: ...

class GetCoreRequest(_message.Message):
    __slots__ = ("p1", "p2")
    P1_FIELD_NUMBER: _ClassVar[int]
    P2_FIELD_NUMBER: _ClassVar[int]
    p1: int
    p2: int
    def __init__(self, p1: _Optional[int] = ..., p2: _Optional[int] = ...) -> None: ...

class GetCoreResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PutCoreRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PutCoreResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CoreReadBarcodeOfPickedUpResourceRequest(_message.Message):
    __slots__ = ("rails", "reading_direction", "minimal_z_position", "traverse_height_at_beginning_of_a_command", "z_speed", "allow_manual_input", "labware_description")
    RAILS_FIELD_NUMBER: _ClassVar[int]
    READING_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    MINIMAL_Z_POSITION_FIELD_NUMBER: _ClassVar[int]
    TRAVERSE_HEIGHT_AT_BEGINNING_OF_A_COMMAND_FIELD_NUMBER: _ClassVar[int]
    Z_SPEED_FIELD_NUMBER: _ClassVar[int]
    ALLOW_MANUAL_INPUT_FIELD_NUMBER: _ClassVar[int]
    LABWARE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    rails: int
    reading_direction: str
    minimal_z_position: float
    traverse_height_at_beginning_of_a_command: float
    z_speed: float
    allow_manual_input: bool
    labware_description: str
    def __init__(self, rails: _Optional[int] = ..., reading_direction: _Optional[str] = ..., minimal_z_position: _Optional[float] = ..., traverse_height_at_beginning_of_a_command: _Optional[float] = ..., z_speed: _Optional[float] = ..., allow_manual_input: bool = ..., labware_description: _Optional[str] = ...) -> None: ...

class CoreReadBarcodeOfPickedUpResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeAutoloadRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeAutoloadResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveAutoloadToSafeZPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveAutoloadToSafeZPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestAutoloadTrackRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestAutoloadTrackResponse(_message.Message):
    __slots__ = ("track",)
    TRACK_FIELD_NUMBER: _ClassVar[int]
    track: int
    def __init__(self, track: _Optional[int] = ...) -> None: ...

class RequestAutoloadTypeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestAutoloadTypeResponse(_message.Message):
    __slots__ = ("autoload_type",)
    AUTOLOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    autoload_type: str
    def __init__(self, autoload_type: _Optional[str] = ...) -> None: ...

class RequestPresenceOfCarriersOnDeckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestPresenceOfCarriersOnDeckResponse(_message.Message):
    __slots__ = ("carriers",)
    CARRIERS_FIELD_NUMBER: _ClassVar[int]
    carriers: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, carriers: _Optional[_Iterable[int]] = ...) -> None: ...

class RequestPresenceOfCarriersOnLoadingTrayRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestPresenceOfCarriersOnLoadingTrayResponse(_message.Message):
    __slots__ = ("carriers",)
    CARRIERS_FIELD_NUMBER: _ClassVar[int]
    carriers: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, carriers: _Optional[_Iterable[int]] = ...) -> None: ...

class RequestPresenceOfSingleCarrierOnLoadingTrayRequest(_message.Message):
    __slots__ = ("track",)
    TRACK_FIELD_NUMBER: _ClassVar[int]
    track: int
    def __init__(self, track: _Optional[int] = ...) -> None: ...

class RequestPresenceOfSingleCarrierOnLoadingTrayResponse(_message.Message):
    __slots__ = ("present",)
    PRESENT_FIELD_NUMBER: _ClassVar[int]
    present: bool
    def __init__(self, present: bool = ...) -> None: ...

class MoveAutoloadToSlotRequest(_message.Message):
    __slots__ = ("slot_number",)
    SLOT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    slot_number: int
    def __init__(self, slot_number: _Optional[int] = ...) -> None: ...

class MoveAutoloadToSlotResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveAutoloadToTrackRequest(_message.Message):
    __slots__ = ("track",)
    TRACK_FIELD_NUMBER: _ClassVar[int]
    track: int
    def __init__(self, track: _Optional[int] = ...) -> None: ...

class MoveAutoloadToTrackResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ParkAutoloadRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ParkAutoloadResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TakeCarrierOutToAutoloadBeltRequest(_message.Message):
    __slots__ = ("carrier_name",)
    CARRIER_NAME_FIELD_NUMBER: _ClassVar[int]
    carrier_name: str
    def __init__(self, carrier_name: _Optional[str] = ...) -> None: ...

class TakeCarrierOutToAutoloadBeltResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetBarcodeTypeRequest(_message.Message):
    __slots__ = ("barcode_symbology",)
    BARCODE_SYMBOLOGY_FIELD_NUMBER: _ClassVar[int]
    barcode_symbology: int
    def __init__(self, barcode_symbology: _Optional[int] = ...) -> None: ...

class SetBarcodeTypeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LoadCarrierFromTrayAndScanCarrierBarcodeRequest(_message.Message):
    __slots__ = ("carrier_name", "carrier_barcode_reading", "barcode_symbology", "barcode_position", "barcode_reading_window_width", "reading_speed")
    CARRIER_NAME_FIELD_NUMBER: _ClassVar[int]
    CARRIER_BARCODE_READING_FIELD_NUMBER: _ClassVar[int]
    BARCODE_SYMBOLOGY_FIELD_NUMBER: _ClassVar[int]
    BARCODE_POSITION_FIELD_NUMBER: _ClassVar[int]
    BARCODE_READING_WINDOW_WIDTH_FIELD_NUMBER: _ClassVar[int]
    READING_SPEED_FIELD_NUMBER: _ClassVar[int]
    carrier_name: str
    carrier_barcode_reading: bool
    barcode_symbology: int
    barcode_position: float
    barcode_reading_window_width: float
    reading_speed: float
    def __init__(self, carrier_name: _Optional[str] = ..., carrier_barcode_reading: bool = ..., barcode_symbology: _Optional[int] = ..., barcode_position: _Optional[float] = ..., barcode_reading_window_width: _Optional[float] = ..., reading_speed: _Optional[float] = ...) -> None: ...

class LoadCarrierFromTrayAndScanCarrierBarcodeResponse(_message.Message):
    __slots__ = ("barcode",)
    BARCODE_FIELD_NUMBER: _ClassVar[int]
    barcode: str
    def __init__(self, barcode: _Optional[str] = ...) -> None: ...

class UnloadCarrierAfterCarcodeBarcardeScanningRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UnloadCarrierAfterCarcodeBarcardeScanningResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetCarrierMonitoringRequest(_message.Message):
    __slots__ = ("should_monitor",)
    SHOULD_MONITOR_FIELD_NUMBER: _ClassVar[int]
    should_monitor: bool
    def __init__(self, should_monitor: bool = ...) -> None: ...

class SetCarrierMonitoringResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LoadCarrierRequest(_message.Message):
    __slots__ = ("carrier_name",)
    CARRIER_NAME_FIELD_NUMBER: _ClassVar[int]
    carrier_name: str
    def __init__(self, carrier_name: _Optional[str] = ...) -> None: ...

class LoadCarrierResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetLoadingIndicatorsRequest(_message.Message):
    __slots__ = ("bit_pattern", "blink_pattern")
    BIT_PATTERN_FIELD_NUMBER: _ClassVar[int]
    BLINK_PATTERN_FIELD_NUMBER: _ClassVar[int]
    bit_pattern: _containers.RepeatedScalarFieldContainer[bool]
    blink_pattern: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, bit_pattern: _Optional[_Iterable[bool]] = ..., blink_pattern: _Optional[_Iterable[bool]] = ...) -> None: ...

class SetLoadingIndicatorsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UnloadCarrierRequest(_message.Message):
    __slots__ = ("carrier_name",)
    CARRIER_NAME_FIELD_NUMBER: _ClassVar[int]
    carrier_name: str
    def __init__(self, carrier_name: _Optional[str] = ...) -> None: ...

class UnloadCarrierResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestInstrumentInitializationStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestInstrumentInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: bool = ...) -> None: ...

class RequestAutoloadInitializationStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestAutoloadInitializationStatusResponse(_message.Message):
    __slots__ = ("initialized",)
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    initialized: bool
    def __init__(self, initialized: bool = ...) -> None: ...

class LockCoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LockCoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UnlockCoverRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UnlockCoverResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DisableCoverControlRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DisableCoverControlResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EnableCoverControlRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EnableCoverControlResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetCoverOutputRequest(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: int
    def __init__(self, output: _Optional[int] = ...) -> None: ...

class SetCoverOutputResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResetOutputRequest(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: int
    def __init__(self, output: _Optional[int] = ...) -> None: ...

class ResetOutputResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestCoverOpenRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestCoverOpenResponse(_message.Message):
    __slots__ = ("open",)
    OPEN_FIELD_NUMBER: _ClassVar[int]
    open: bool
    def __init__(self, open: bool = ...) -> None: ...

class SendHhsCommandRequest(_message.Message):
    __slots__ = ("index", "command")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    index: int
    command: str
    def __init__(self, index: _Optional[int] = ..., command: _Optional[str] = ...) -> None: ...

class SendHhsCommandResponse(_message.Message):
    __slots__ = ("response",)
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: str
    def __init__(self, response: _Optional[str] = ...) -> None: ...

class CheckTypeIsHhcRequest(_message.Message):
    __slots__ = ("device_number",)
    DEVICE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    device_number: int
    def __init__(self, device_number: _Optional[int] = ...) -> None: ...

class CheckTypeIsHhcResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeHhcRequest(_message.Message):
    __slots__ = ("device_number",)
    DEVICE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    device_number: int
    def __init__(self, device_number: _Optional[int] = ...) -> None: ...

class InitializeHhcResponse(_message.Message):
    __slots__ = ("response",)
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: str
    def __init__(self, response: _Optional[str] = ...) -> None: ...

class StartTemperatureControlAtHhcRequest(_message.Message):
    __slots__ = ("device_number", "temperature")
    DEVICE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    device_number: int
    temperature: float
    def __init__(self, device_number: _Optional[int] = ..., temperature: _Optional[float] = ...) -> None: ...

class StartTemperatureControlAtHhcResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetTemperatureAtHhcRequest(_message.Message):
    __slots__ = ("device_number",)
    DEVICE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    device_number: int
    def __init__(self, device_number: _Optional[int] = ...) -> None: ...

class GetTemperatureAtHhcResponse(_message.Message):
    __slots__ = ("current_temperature", "target_temperature")
    CURRENT_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    TARGET_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    current_temperature: float
    target_temperature: float
    def __init__(self, current_temperature: _Optional[float] = ..., target_temperature: _Optional[float] = ...) -> None: ...

class QueryWhetherTemperatureReachedAtHhcRequest(_message.Message):
    __slots__ = ("device_number",)
    DEVICE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    device_number: int
    def __init__(self, device_number: _Optional[int] = ...) -> None: ...

class QueryWhetherTemperatureReachedAtHhcResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopTemperatureControlAtHhcRequest(_message.Message):
    __slots__ = ("device_number",)
    DEVICE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    device_number: int
    def __init__(self, device_number: _Optional[int] = ...) -> None: ...

class StopTemperatureControlAtHhcResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestFirmwareVersionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestFirmwareVersionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestErrorCodeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestErrorCodeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestParameterValueRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestParameterValueResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestDeviceSerialNumberRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestDeviceSerialNumberResponse(_message.Message):
    __slots__ = ("serial_number",)
    SERIAL_NUMBER_FIELD_NUMBER: _ClassVar[int]
    serial_number: str
    def __init__(self, serial_number: _Optional[str] = ...) -> None: ...

class RequestMasterStatusRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestMasterStatusResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestNameOfLastFaultyParameterRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestNameOfLastFaultyParameterResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetSingleStepModeRequest(_message.Message):
    __slots__ = ("single_step_mode",)
    SINGLE_STEP_MODE_FIELD_NUMBER: _ClassVar[int]
    single_step_mode: bool
    def __init__(self, single_step_mode: bool = ...) -> None: ...

class SetSingleStepModeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TriggerNextStepRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TriggerNextStepResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HaltRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HaltResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SaveAllCycleCountersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SaveAllCycleCountersResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetNotStopRequest(_message.Message):
    __slots__ = ("non_stop",)
    NON_STOP_FIELD_NUMBER: _ClassVar[int]
    non_stop: bool
    def __init__(self, non_stop: bool = ...) -> None: ...

class SetNotStopResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConfigureNodeNamesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConfigureNodeNamesResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetDeckDataRequest(_message.Message):
    __slots__ = ("data_index", "data_stream")
    DATA_INDEX_FIELD_NUMBER: _ClassVar[int]
    DATA_STREAM_FIELD_NUMBER: _ClassVar[int]
    data_index: int
    data_stream: str
    def __init__(self, data_index: _Optional[int] = ..., data_stream: _Optional[str] = ...) -> None: ...

class SetDeckDataResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionLeftXArmRequest(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    def __init__(self, x_position: _Optional[int] = ...) -> None: ...

class PositionLeftXArmResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PositionRightXArmRequest(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    def __init__(self, x_position: _Optional[int] = ...) -> None: ...

class PositionRightXArmResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveLeftXArmToPositionWithAllAttachedComponentsInZSafetyPositionRequest(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    def __init__(self, x_position: _Optional[int] = ...) -> None: ...

class MoveLeftXArmToPositionWithAllAttachedComponentsInZSafetyPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MoveRightXArmToPositionWithAllAttachedComponentsInZSafetyPositionRequest(_message.Message):
    __slots__ = ("x_position",)
    X_POSITION_FIELD_NUMBER: _ClassVar[int]
    x_position: int
    def __init__(self, x_position: _Optional[int] = ...) -> None: ...

class MoveRightXArmToPositionWithAllAttachedComponentsInZSafetyPositionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestLeftXArmPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestLeftXArmPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: float
    def __init__(self, position: _Optional[float] = ...) -> None: ...

class RequestRightXArmPositionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestRightXArmPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: float
    def __init__(self, position: _Optional[float] = ...) -> None: ...

class RequestRightXArmLastCollisionTypeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RequestRightXArmLastCollisionTypeResponse(_message.Message):
    __slots__ = ("collision",)
    COLLISION_FIELD_NUMBER: _ClassVar[int]
    collision: bool
    def __init__(self, collision: bool = ...) -> None: ...

class RequestPumpSettingsRequest(_message.Message):
    __slots__ = ("pump_station",)
    PUMP_STATION_FIELD_NUMBER: _ClassVar[int]
    pump_station: int
    def __init__(self, pump_station: _Optional[int] = ...) -> None: ...

class RequestPumpSettingsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeDualPumpStationValvesRequest(_message.Message):
    __slots__ = ("pump_station",)
    PUMP_STATION_FIELD_NUMBER: _ClassVar[int]
    pump_station: int
    def __init__(self, pump_station: _Optional[int] = ...) -> None: ...

class InitializeDualPumpStationValvesResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DrainDualChamberSystemRequest(_message.Message):
    __slots__ = ("pump_station",)
    PUMP_STATION_FIELD_NUMBER: _ClassVar[int]
    pump_station: int
    def __init__(self, pump_station: _Optional[int] = ...) -> None: ...

class DrainDualChamberSystemResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ViolentlyShootDownTipRequest(_message.Message):
    __slots__ = ("channel_idx",)
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    def __init__(self, channel_idx: _Optional[int] = ...) -> None: ...

class ViolentlyShootDownTipResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CanPickUpTipRequest(_message.Message):
    __slots__ = ("channel_idx", "tip")
    CHANNEL_IDX_FIELD_NUMBER: _ClassVar[int]
    TIP_FIELD_NUMBER: _ClassVar[int]
    channel_idx: int
    tip: TipData
    def __init__(self, channel_idx: _Optional[int] = ..., tip: _Optional[_Union[TipData, _Mapping]] = ...) -> None: ...

class CanPickUpTipResponse(_message.Message):
    __slots__ = ("can_pick_up",)
    CAN_PICK_UP_FIELD_NUMBER: _ClassVar[int]
    can_pick_up: bool
    def __init__(self, can_pick_up: bool = ...) -> None: ...
