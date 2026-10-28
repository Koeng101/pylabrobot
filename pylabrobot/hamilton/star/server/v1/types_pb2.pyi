from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Barcode2DSymbology(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BARCODE_2D_SYMBOLOGY_UNSPECIFIED: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_DATA_MATRIX: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_QR_CODE: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_MAXI_CODE: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_AZTEC: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_PDF_417: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_MICRO_PDF_417: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_GS1_DATABAR: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_EAN_UCC_COMP: _ClassVar[Barcode2DSymbology]
    BARCODE_2D_SYMBOLOGY_ANY_2D: _ClassVar[Barcode2DSymbology]

class BarcodeReadingDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BARCODE_READING_DIRECTION_UNSPECIFIED: _ClassVar[BarcodeReadingDirection]
    BARCODE_READING_DIRECTION_VERTICAL: _ClassVar[BarcodeReadingDirection]
    BARCODE_READING_DIRECTION_HORIZONTAL: _ClassVar[BarcodeReadingDirection]

class BarcodeSymbology(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BARCODE_SYMBOLOGY_UNSPECIFIED: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_ISBT_STANDARD: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_CODE_128_SUBSET_B_AND_C: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_CODE_39: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_CODEBAR: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_CODE_2OF5_INTERLEAVED: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_UPC_A_E: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_YESN_EAN_8: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_CODE_93: _ClassVar[BarcodeSymbology]
    BARCODE_SYMBOLOGY_ANY_1D: _ClassVar[BarcodeSymbology]

class FrontCoverState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FRONT_COVER_STATE_UNSPECIFIED: _ClassVar[FrontCoverState]
    FRONT_COVER_STATE_OPEN: _ClassVar[FrontCoverState]
    FRONT_COVER_STATE_CLOSED: _ClassVar[FrontCoverState]

class Head96InstrumentType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HEAD96_INSTRUMENT_TYPE_UNSPECIFIED: _ClassVar[Head96InstrumentType]
    HEAD96_INSTRUMENT_TYPE_LEGACY: _ClassVar[Head96InstrumentType]
    HEAD96_INSTRUMENT_TYPE_FM_STAR: _ClassVar[Head96InstrumentType]

class Head96TipPickupMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HEAD96_TIP_PICKUP_METHOD_UNSPECIFIED: _ClassVar[Head96TipPickupMethod]
    HEAD96_TIP_PICKUP_METHOD_FROM_RACK: _ClassVar[Head96TipPickupMethod]
    HEAD96_TIP_PICKUP_METHOD_FROM_WASTE: _ClassVar[Head96TipPickupMethod]
    HEAD96_TIP_PICKUP_METHOD_FULL_BLOWOUT: _ClassVar[Head96TipPickupMethod]

class ISwapAxis(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ISWAP_AXIS_UNSPECIFIED: _ClassVar[ISwapAxis]
    ISWAP_AXIS_X: _ClassVar[ISwapAxis]
    ISWAP_AXIS_Y: _ClassVar[ISwapAxis]
    ISWAP_AXIS_Z: _ClassVar[ISwapAxis]
    ISWAP_AXIS_ELBOW: _ClassVar[ISwapAxis]
    ISWAP_AXIS_WRIST: _ClassVar[ISwapAxis]
    ISWAP_AXIS_GRIPPER: _ClassVar[ISwapAxis]

class LLDMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LLD_MODE_UNSPECIFIED: _ClassVar[LLDMode]
    LLD_MODE_OFF: _ClassVar[LLDMode]
    LLD_MODE_CAPACITIVE: _ClassVar[LLDMode]
    LLD_MODE_PRESSURE: _ClassVar[LLDMode]
    LLD_MODE_DUAL: _ClassVar[LLDMode]
    LLD_MODE_ZTOUCH: _ClassVar[LLDMode]

class LLDSensor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LLD_SENSOR_UNSPECIFIED: _ClassVar[LLDSensor]
    LLD_SENSOR_A1_OR_B2: _ClassVar[LLDSensor]
    LLD_SENSOR_G11_OR_H12: _ClassVar[LLDSensor]
    LLD_SENSOR_ANY: _ClassVar[LLDSensor]
    LLD_SENSOR_ALL: _ClassVar[LLDSensor]

class PipetteChannelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PIPETTE_CHANNEL_TYPE_UNSPECIFIED: _ClassVar[PipetteChannelType]
    PIPETTE_CHANNEL_TYPE_ML_STAR: _ClassVar[PipetteChannelType]
    PIPETTE_CHANNEL_TYPE_ML_STAR_RPC: _ClassVar[PipetteChannelType]

class PipetteHeadType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PIPETTE_HEAD_TYPE_UNSPECIFIED: _ClassVar[PipetteHeadType]
    PIPETTE_HEAD_TYPE_ML_STAR: _ClassVar[PipetteHeadType]
    PIPETTE_HEAD_TYPE_ML_STAR_PLE: _ClassVar[PipetteHeadType]
    PIPETTE_HEAD_TYPE_ML_STAR_RPC: _ClassVar[PipetteHeadType]

class PressureADC(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PRESSURE_ADC_UNSPECIFIED: _ClassVar[PressureADC]
    PRESSURE_ADC_RENESAS_X9268: _ClassVar[PressureADC]
    PRESSURE_ADC_ANALOG_DEVICES_AD5263: _ClassVar[PressureADC]

class PressureLLDMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PRESSURE_LLD_MODE_UNSPECIFIED: _ClassVar[PressureLLDMode]
    PRESSURE_LLD_MODE_LIQUID: _ClassVar[PressureLLDMode]
    PRESSURE_LLD_MODE_FOAM: _ClassVar[PressureLLDMode]

class ScanDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SCAN_DIRECTION_UNSPECIFIED: _ClassVar[ScanDirection]
    SCAN_DIRECTION_VERTICAL: _ClassVar[ScanDirection]
    SCAN_DIRECTION_HORIZONTAL: _ClassVar[ScanDirection]
    SCAN_DIRECTION_OMNIDIRECTIONAL: _ClassVar[ScanDirection]
    SCAN_DIRECTION_VERTICAL_AND_HORIZONTAL: _ClassVar[ScanDirection]

class ScannerRotation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SCANNER_ROTATION_UNSPECIFIED: _ClassVar[ScannerRotation]
    SCANNER_ROTATION_VERTICAL: _ClassVar[ScannerRotation]
    SCANNER_ROTATION_HORIZONTAL: _ClassVar[ScannerRotation]
    SCANNER_ROTATION_UNDEFINED: _ClassVar[ScannerRotation]

class StopDiscType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STOP_DISC_TYPE_UNSPECIFIED: _ClassVar[StopDiscType]
    STOP_DISC_TYPE_CORE_I: _ClassVar[StopDiscType]
    STOP_DISC_TYPE_CORE_II: _ClassVar[StopDiscType]

class TADMOperation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TADM_OPERATION_UNSPECIFIED: _ClassVar[TADMOperation]
    TADM_OPERATION_ASPIRATE: _ClassVar[TADMOperation]
    TADM_OPERATION_DISPENSE: _ClassVar[TADMOperation]
    TADM_OPERATION_OTHER: _ClassVar[TADMOperation]

class TADMStorageLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TADM_STORAGE_LEVEL_UNSPECIFIED: _ClassVar[TADMStorageLevel]
    TADM_STORAGE_LEVEL_NONE: _ClassVar[TADMStorageLevel]
    TADM_STORAGE_LEVEL_ERRORS_ONLY: _ClassVar[TADMStorageLevel]
    TADM_STORAGE_LEVEL_ALL: _ClassVar[TADMStorageLevel]

class TipDropMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TIP_DROP_METHOD_UNSPECIFIED: _ClassVar[TipDropMethod]
    TIP_DROP_METHOD_PLACE_SHIFT: _ClassVar[TipDropMethod]
    TIP_DROP_METHOD_DROP: _ClassVar[TipDropMethod]

class TipPickupMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TIP_PICKUP_METHOD_UNSPECIFIED: _ClassVar[TipPickupMethod]
    TIP_PICKUP_METHOD_OUT_OF_RACK: _ClassVar[TipPickupMethod]
    TIP_PICKUP_METHOD_OUT_OF_WASH_LIQUID: _ClassVar[TipPickupMethod]

class TipSize(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TIP_SIZE_UNSPECIFIED: _ClassVar[TipSize]
    TIP_SIZE_UNDEFINED: _ClassVar[TipSize]
    TIP_SIZE_LOW_VOLUME: _ClassVar[TipSize]
    TIP_SIZE_STANDARD_VOLUME: _ClassVar[TipSize]
    TIP_SIZE_HIGH_VOLUME: _ClassVar[TipSize]
    TIP_SIZE_CORE_384_HEAD_TIP: _ClassVar[TipSize]
    TIP_SIZE_XL: _ClassVar[TipSize]

class WheelYPosition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WHEEL_YPOSITION_UNSPECIFIED: _ClassVar[WheelYPosition]
    WHEEL_YPOSITION_LOADING_TRAY: _ClassVar[WheelYPosition]
    WHEEL_YPOSITION_CARRIER_IDENTIFICATION: _ClassVar[WheelYPosition]
    WHEEL_YPOSITION_DECK: _ClassVar[WheelYPosition]

class WheelZPosition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WHEEL_ZPOSITION_UNSPECIFIED: _ClassVar[WheelZPosition]
    WHEEL_ZPOSITION_BELOW: _ClassVar[WheelZPosition]
    WHEEL_ZPOSITION_ABOVE: _ClassVar[WheelZPosition]

class XArmSide(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    X_ARM_SIDE_UNSPECIFIED: _ClassVar[XArmSide]
    X_ARM_SIDE_LEFT: _ClassVar[XArmSide]
    X_ARM_SIDE_RIGHT: _ClassVar[XArmSide]

class XProbeDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    XPROBE_DIRECTION_UNSPECIFIED: _ClassVar[XProbeDirection]
    XPROBE_DIRECTION_LEFT: _ClassVar[XProbeDirection]
    XPROBE_DIRECTION_RIGHT: _ClassVar[XProbeDirection]

class YProbeDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    YPROBE_DIRECTION_UNSPECIFIED: _ClassVar[YProbeDirection]
    YPROBE_DIRECTION_FORWARD: _ClassVar[YProbeDirection]
    YPROBE_DIRECTION_BACKWARD: _ClassVar[YProbeDirection]
BARCODE_2D_SYMBOLOGY_UNSPECIFIED: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_DATA_MATRIX: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_QR_CODE: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_MAXI_CODE: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_AZTEC: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_PDF_417: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_MICRO_PDF_417: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_GS1_DATABAR: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_EAN_UCC_COMP: Barcode2DSymbology
BARCODE_2D_SYMBOLOGY_ANY_2D: Barcode2DSymbology
BARCODE_READING_DIRECTION_UNSPECIFIED: BarcodeReadingDirection
BARCODE_READING_DIRECTION_VERTICAL: BarcodeReadingDirection
BARCODE_READING_DIRECTION_HORIZONTAL: BarcodeReadingDirection
BARCODE_SYMBOLOGY_UNSPECIFIED: BarcodeSymbology
BARCODE_SYMBOLOGY_ISBT_STANDARD: BarcodeSymbology
BARCODE_SYMBOLOGY_CODE_128_SUBSET_B_AND_C: BarcodeSymbology
BARCODE_SYMBOLOGY_CODE_39: BarcodeSymbology
BARCODE_SYMBOLOGY_CODEBAR: BarcodeSymbology
BARCODE_SYMBOLOGY_CODE_2OF5_INTERLEAVED: BarcodeSymbology
BARCODE_SYMBOLOGY_UPC_A_E: BarcodeSymbology
BARCODE_SYMBOLOGY_YESN_EAN_8: BarcodeSymbology
BARCODE_SYMBOLOGY_CODE_93: BarcodeSymbology
BARCODE_SYMBOLOGY_ANY_1D: BarcodeSymbology
FRONT_COVER_STATE_UNSPECIFIED: FrontCoverState
FRONT_COVER_STATE_OPEN: FrontCoverState
FRONT_COVER_STATE_CLOSED: FrontCoverState
HEAD96_INSTRUMENT_TYPE_UNSPECIFIED: Head96InstrumentType
HEAD96_INSTRUMENT_TYPE_LEGACY: Head96InstrumentType
HEAD96_INSTRUMENT_TYPE_FM_STAR: Head96InstrumentType
HEAD96_TIP_PICKUP_METHOD_UNSPECIFIED: Head96TipPickupMethod
HEAD96_TIP_PICKUP_METHOD_FROM_RACK: Head96TipPickupMethod
HEAD96_TIP_PICKUP_METHOD_FROM_WASTE: Head96TipPickupMethod
HEAD96_TIP_PICKUP_METHOD_FULL_BLOWOUT: Head96TipPickupMethod
ISWAP_AXIS_UNSPECIFIED: ISwapAxis
ISWAP_AXIS_X: ISwapAxis
ISWAP_AXIS_Y: ISwapAxis
ISWAP_AXIS_Z: ISwapAxis
ISWAP_AXIS_ELBOW: ISwapAxis
ISWAP_AXIS_WRIST: ISwapAxis
ISWAP_AXIS_GRIPPER: ISwapAxis
LLD_MODE_UNSPECIFIED: LLDMode
LLD_MODE_OFF: LLDMode
LLD_MODE_CAPACITIVE: LLDMode
LLD_MODE_PRESSURE: LLDMode
LLD_MODE_DUAL: LLDMode
LLD_MODE_ZTOUCH: LLDMode
LLD_SENSOR_UNSPECIFIED: LLDSensor
LLD_SENSOR_A1_OR_B2: LLDSensor
LLD_SENSOR_G11_OR_H12: LLDSensor
LLD_SENSOR_ANY: LLDSensor
LLD_SENSOR_ALL: LLDSensor
PIPETTE_CHANNEL_TYPE_UNSPECIFIED: PipetteChannelType
PIPETTE_CHANNEL_TYPE_ML_STAR: PipetteChannelType
PIPETTE_CHANNEL_TYPE_ML_STAR_RPC: PipetteChannelType
PIPETTE_HEAD_TYPE_UNSPECIFIED: PipetteHeadType
PIPETTE_HEAD_TYPE_ML_STAR: PipetteHeadType
PIPETTE_HEAD_TYPE_ML_STAR_PLE: PipetteHeadType
PIPETTE_HEAD_TYPE_ML_STAR_RPC: PipetteHeadType
PRESSURE_ADC_UNSPECIFIED: PressureADC
PRESSURE_ADC_RENESAS_X9268: PressureADC
PRESSURE_ADC_ANALOG_DEVICES_AD5263: PressureADC
PRESSURE_LLD_MODE_UNSPECIFIED: PressureLLDMode
PRESSURE_LLD_MODE_LIQUID: PressureLLDMode
PRESSURE_LLD_MODE_FOAM: PressureLLDMode
SCAN_DIRECTION_UNSPECIFIED: ScanDirection
SCAN_DIRECTION_VERTICAL: ScanDirection
SCAN_DIRECTION_HORIZONTAL: ScanDirection
SCAN_DIRECTION_OMNIDIRECTIONAL: ScanDirection
SCAN_DIRECTION_VERTICAL_AND_HORIZONTAL: ScanDirection
SCANNER_ROTATION_UNSPECIFIED: ScannerRotation
SCANNER_ROTATION_VERTICAL: ScannerRotation
SCANNER_ROTATION_HORIZONTAL: ScannerRotation
SCANNER_ROTATION_UNDEFINED: ScannerRotation
STOP_DISC_TYPE_UNSPECIFIED: StopDiscType
STOP_DISC_TYPE_CORE_I: StopDiscType
STOP_DISC_TYPE_CORE_II: StopDiscType
TADM_OPERATION_UNSPECIFIED: TADMOperation
TADM_OPERATION_ASPIRATE: TADMOperation
TADM_OPERATION_DISPENSE: TADMOperation
TADM_OPERATION_OTHER: TADMOperation
TADM_STORAGE_LEVEL_UNSPECIFIED: TADMStorageLevel
TADM_STORAGE_LEVEL_NONE: TADMStorageLevel
TADM_STORAGE_LEVEL_ERRORS_ONLY: TADMStorageLevel
TADM_STORAGE_LEVEL_ALL: TADMStorageLevel
TIP_DROP_METHOD_UNSPECIFIED: TipDropMethod
TIP_DROP_METHOD_PLACE_SHIFT: TipDropMethod
TIP_DROP_METHOD_DROP: TipDropMethod
TIP_PICKUP_METHOD_UNSPECIFIED: TipPickupMethod
TIP_PICKUP_METHOD_OUT_OF_RACK: TipPickupMethod
TIP_PICKUP_METHOD_OUT_OF_WASH_LIQUID: TipPickupMethod
TIP_SIZE_UNSPECIFIED: TipSize
TIP_SIZE_UNDEFINED: TipSize
TIP_SIZE_LOW_VOLUME: TipSize
TIP_SIZE_STANDARD_VOLUME: TipSize
TIP_SIZE_HIGH_VOLUME: TipSize
TIP_SIZE_CORE_384_HEAD_TIP: TipSize
TIP_SIZE_XL: TipSize
WHEEL_YPOSITION_UNSPECIFIED: WheelYPosition
WHEEL_YPOSITION_LOADING_TRAY: WheelYPosition
WHEEL_YPOSITION_CARRIER_IDENTIFICATION: WheelYPosition
WHEEL_YPOSITION_DECK: WheelYPosition
WHEEL_ZPOSITION_UNSPECIFIED: WheelZPosition
WHEEL_ZPOSITION_BELOW: WheelZPosition
WHEEL_ZPOSITION_ABOVE: WheelZPosition
X_ARM_SIDE_UNSPECIFIED: XArmSide
X_ARM_SIDE_LEFT: XArmSide
X_ARM_SIDE_RIGHT: XArmSide
XPROBE_DIRECTION_UNSPECIFIED: XProbeDirection
XPROBE_DIRECTION_LEFT: XProbeDirection
XPROBE_DIRECTION_RIGHT: XProbeDirection
YPROBE_DIRECTION_UNSPECIFIED: YProbeDirection
YPROBE_DIRECTION_FORWARD: YProbeDirection
YPROBE_DIRECTION_BACKWARD: YProbeDirection

class ISwapJoint(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: ISwapAxis
    value: float
    def __init__(self, key: _Optional[_Union[ISwapAxis, str]] = ..., value: _Optional[float] = ...) -> None: ...

class LiquidClass(_message.Message):
    __slots__ = ("curve", "aspiration_flow_rate", "aspiration_mix_flow_rate", "aspiration_air_transport_volume", "aspiration_blow_out_volume", "aspiration_swap_speed", "aspiration_settling_time", "aspiration_over_aspirate_volume", "aspiration_clot_retract_height", "dispense_flow_rate", "dispense_mode", "dispense_mix_flow_rate", "dispense_air_transport_volume", "dispense_blow_out_volume", "dispense_swap_speed", "dispense_settling_time", "dispense_stop_flow_rate", "dispense_stop_back_volume")
    CURVE_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_MIX_FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_AIR_TRANSPORT_VOLUME_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_BLOW_OUT_VOLUME_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_OVER_ASPIRATE_VOLUME_FIELD_NUMBER: _ClassVar[int]
    ASPIRATION_CLOT_RETRACT_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_MODE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_MIX_FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_AIR_TRANSPORT_VOLUME_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_BLOW_OUT_VOLUME_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_SWAP_SPEED_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_SETTLING_TIME_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_STOP_FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    DISPENSE_STOP_BACK_VOLUME_FIELD_NUMBER: _ClassVar[int]
    curve: _containers.RepeatedCompositeFieldContainer[LiquidClassCurveEntry]
    aspiration_flow_rate: float
    aspiration_mix_flow_rate: float
    aspiration_air_transport_volume: float
    aspiration_blow_out_volume: float
    aspiration_swap_speed: float
    aspiration_settling_time: float
    aspiration_over_aspirate_volume: float
    aspiration_clot_retract_height: float
    dispense_flow_rate: float
    dispense_mode: float
    dispense_mix_flow_rate: float
    dispense_air_transport_volume: float
    dispense_blow_out_volume: float
    dispense_swap_speed: float
    dispense_settling_time: float
    dispense_stop_flow_rate: float
    dispense_stop_back_volume: float
    def __init__(self, curve: _Optional[_Iterable[_Union[LiquidClassCurveEntry, _Mapping]]] = ..., aspiration_flow_rate: _Optional[float] = ..., aspiration_mix_flow_rate: _Optional[float] = ..., aspiration_air_transport_volume: _Optional[float] = ..., aspiration_blow_out_volume: _Optional[float] = ..., aspiration_swap_speed: _Optional[float] = ..., aspiration_settling_time: _Optional[float] = ..., aspiration_over_aspirate_volume: _Optional[float] = ..., aspiration_clot_retract_height: _Optional[float] = ..., dispense_flow_rate: _Optional[float] = ..., dispense_mode: _Optional[float] = ..., dispense_mix_flow_rate: _Optional[float] = ..., dispense_air_transport_volume: _Optional[float] = ..., dispense_blow_out_volume: _Optional[float] = ..., dispense_swap_speed: _Optional[float] = ..., dispense_settling_time: _Optional[float] = ..., dispense_stop_flow_rate: _Optional[float] = ..., dispense_stop_back_volume: _Optional[float] = ...) -> None: ...

class LiquidClassCurveEntry(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: float
    value: float
    def __init__(self, key: _Optional[float] = ..., value: _Optional[float] = ...) -> None: ...

class Mix(_message.Message):
    __slots__ = ("volume", "repetitions", "flow_rate", "surface_following_distance", "auto_surface_following")
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    REPETITIONS_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_FIELD_NUMBER: _ClassVar[int]
    SURFACE_FOLLOWING_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    AUTO_SURFACE_FOLLOWING_FIELD_NUMBER: _ClassVar[int]
    volume: float
    repetitions: int
    flow_rate: float
    surface_following_distance: float
    auto_surface_following: bool
    def __init__(self, volume: _Optional[float] = ..., repetitions: _Optional[int] = ..., flow_rate: _Optional[float] = ..., surface_following_distance: _Optional[float] = ..., auto_surface_following: _Optional[bool] = ...) -> None: ...

class ReferencePointYZ(_message.Message):
    __slots__ = ("y", "z")
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    y: float
    z: float
    def __init__(self, y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class TipDestination(_message.Message):
    __slots__ = ("resource", "location")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    resource: _types_pb2.ResourceRef
    location: _types_pb2.Vec3
    def __init__(self, resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., location: _Optional[_Union[_types_pb2.Vec3, _Mapping]] = ...) -> None: ...

class WorkingEnvelope(_message.Message):
    __slots__ = ("wrap_size", "workspace")
    WRAP_SIZE_FIELD_NUMBER: _ClassVar[int]
    WORKSPACE_FIELD_NUMBER: _ClassVar[int]
    wrap_size: float
    workspace: DoubleRange
    def __init__(self, wrap_size: _Optional[float] = ..., workspace: _Optional[_Union[DoubleRange, _Mapping]] = ...) -> None: ...

class FirmwareReply(_message.Message):
    __slots__ = ("raw", "parsed")
    RAW_FIELD_NUMBER: _ClassVar[int]
    PARSED_FIELD_NUMBER: _ClassVar[int]
    raw: str
    parsed: ParsedReply
    def __init__(self, raw: _Optional[str] = ..., parsed: _Optional[_Union[ParsedReply, _Mapping]] = ...) -> None: ...

class ParsedReply(_message.Message):
    __slots__ = ("parameters",)
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: FirmwareValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[FirmwareValue, _Mapping]] = ...) -> None: ...
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    parameters: _containers.MessageMap[str, FirmwareValue]
    def __init__(self, parameters: _Optional[_Mapping[str, FirmwareValue]] = ...) -> None: ...

class FirmwareValue(_message.Message):
    __slots__ = ("integer", "text", "integers", "texts")
    INTEGER_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    INTEGERS_FIELD_NUMBER: _ClassVar[int]
    TEXTS_FIELD_NUMBER: _ClassVar[int]
    integer: int
    text: str
    integers: Int64List
    texts: StringList
    def __init__(self, integer: _Optional[int] = ..., text: _Optional[str] = ..., integers: _Optional[_Union[Int64List, _Mapping]] = ..., texts: _Optional[_Union[StringList, _Mapping]] = ...) -> None: ...

class Barcode2DSymbologyList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[Barcode2DSymbology]
    def __init__(self, values: _Optional[_Iterable[_Union[Barcode2DSymbology, str]]] = ...) -> None: ...

class BarcodeSymbologyList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[BarcodeSymbology]
    def __init__(self, values: _Optional[_Iterable[_Union[BarcodeSymbology, str]]] = ...) -> None: ...

class BoolList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, values: _Optional[_Iterable[bool]] = ...) -> None: ...

class Date(_message.Message):
    __slots__ = ("year", "month", "day")
    YEAR_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    DAY_FIELD_NUMBER: _ClassVar[int]
    year: int
    month: int
    day: int
    def __init__(self, year: _Optional[int] = ..., month: _Optional[int] = ..., day: _Optional[int] = ...) -> None: ...

class DoubleList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, values: _Optional[_Iterable[float]] = ...) -> None: ...

class DoubleRange(_message.Message):
    __slots__ = ("min", "max")
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    min: float
    max: float
    def __init__(self, min: _Optional[float] = ..., max: _Optional[float] = ...) -> None: ...

class Int32List(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, values: _Optional[_Iterable[int]] = ...) -> None: ...

class Int32Range(_message.Message):
    __slots__ = ("min", "max")
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    min: int
    max: int
    def __init__(self, min: _Optional[int] = ..., max: _Optional[int] = ...) -> None: ...

class Int64List(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, values: _Optional[_Iterable[int]] = ...) -> None: ...

class LLDModeList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[LLDMode]
    def __init__(self, values: _Optional[_Iterable[_Union[LLDMode, str]]] = ...) -> None: ...

class LiquidClassList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[LiquidClass]
    def __init__(self, values: _Optional[_Iterable[_Union[LiquidClass, _Mapping]]] = ...) -> None: ...

class OptionalDouble(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: float
    def __init__(self, value: _Optional[float] = ...) -> None: ...

class OptionalDoubleList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[OptionalDouble]
    def __init__(self, values: _Optional[_Iterable[_Union[OptionalDouble, _Mapping]]] = ...) -> None: ...

class OptionalMix(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: Mix
    def __init__(self, value: _Optional[_Union[Mix, _Mapping]] = ...) -> None: ...

class OptionalMixList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[OptionalMix]
    def __init__(self, values: _Optional[_Iterable[_Union[OptionalMix, _Mapping]]] = ...) -> None: ...

class OptionalResourceNode(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: _types_pb2.ResourceNode
    def __init__(self, value: _Optional[_Union[_types_pb2.ResourceNode, _Mapping]] = ...) -> None: ...

class OptionalString(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: str
    def __init__(self, value: _Optional[str] = ...) -> None: ...

class OptionalVec3(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: _types_pb2.Vec3
    def __init__(self, value: _Optional[_Union[_types_pb2.Vec3, _Mapping]] = ...) -> None: ...

class ResourceRefList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[_types_pb2.ResourceRef]
    def __init__(self, values: _Optional[_Iterable[_Union[_types_pb2.ResourceRef, _Mapping]]] = ...) -> None: ...

class StringInt32Map(_message.Message):
    __slots__ = ("entries",)
    class EntriesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.ScalarMap[str, int]
    def __init__(self, entries: _Optional[_Mapping[str, int]] = ...) -> None: ...

class StringList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class Vec3List(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[_types_pb2.Vec3]
    def __init__(self, values: _Optional[_Iterable[_Union[_types_pb2.Vec3, _Mapping]]] = ...) -> None: ...
