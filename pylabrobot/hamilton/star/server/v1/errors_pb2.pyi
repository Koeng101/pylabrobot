from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ErrorKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERROR_KIND_UNSPECIFIED: _ClassVar[ErrorKind]
    ERROR_KIND_VALUE: _ClassVar[ErrorKind]
    ERROR_KIND_RUNTIME: _ClassVar[ErrorKind]
    ERROR_KIND_TYPE: _ClassVar[ErrorKind]
    ERROR_KIND_NOT_IMPLEMENTED: _ClassVar[ErrorKind]
    ERROR_KIND_INDEX: _ClassVar[ErrorKind]
    ERROR_KIND_KEY: _ClassVar[ErrorKind]
    ERROR_KIND_ASSERTION: _ClassVar[ErrorKind]
    ERROR_KIND_TIMEOUT: _ClassVar[ErrorKind]
    ERROR_KIND_CONNECTION: _ClassVar[ErrorKind]
    ERROR_KIND_HAS_TIP: _ClassVar[ErrorKind]
    ERROR_KIND_NO_TIP: _ClassVar[ErrorKind]
    ERROR_KIND_TOO_LITTLE_LIQUID: _ClassVar[ErrorKind]
    ERROR_KIND_TOO_LITTLE_VOLUME: _ClassVar[ErrorKind]
    ERROR_KIND_RESOURCE_NOT_FOUND: _ClassVar[ErrorKind]
    ERROR_KIND_NO_LOCATION: _ClassVar[ErrorKind]
    ERROR_KIND_CHANNELS_DO_NOT_FIT: _ClassVar[ErrorKind]
    ERROR_KIND_RESOURCE_SERVER: _ClassVar[ErrorKind]
    ERROR_KIND_FIRMWARE: _ClassVar[ErrorKind]

class ModuleErrorKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MODULE_ERROR_KIND_UNSPECIFIED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_COMMAND_SYNTAX: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_HARDWARE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_COMMAND_NOT_COMPLETED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_CLOT_DETECTED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_BARCODE_UNREADABLE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_TIP_TOO_LITTLE_VOLUME: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_TIP_ALREADY_FITTED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_HAMILTON_NO_TIP: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NO_CARRIER: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NOT_COMPLETED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_DISPENSE_WITH_PRESSURE_LLD: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NO_TEACH_IN_SIGNAL: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_LOADING_TRAY: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_SEQUENCED_ASPIRATION_WITH_PRESSURE_LLD: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NOT_ALLOWED_PARAMETER_COMBINATION: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_COVER_CLOSE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_ASPIRATION: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_WASH_FLUID_OR_WASTE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_INCUBATION: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_TADM_MEASUREMENT: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NO_ELEMENT: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_ELEMENT_STILL_HOLDING: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_ELEMENT_LOST: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_ILLEGAL_TARGET_PLATE_POSITION: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_ILLEGAL_USER_ACCESS: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_POSITION_NOT_REACHABLE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_UNEXPECTED_LLD: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_AREA_ALREADY_OCCUPIED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_IMPOSSIBLE_TO_OCCUPY_AREA: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_ANTI_DROP_CONTROL: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_DECAPPER: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_DECAPPER_HANDLING: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_STOP: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_SUBSYSTEM: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_WRONG_CARRIER: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NO_CARRIER_BARCODE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_LIQUID_LEVEL: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NOT_DETECTED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NOT_ASPIRATED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_IMPROPER_DISPENSATION: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_NO_LABWARE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_UNEXPECTED_LABWARE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_WRONG_LABWARE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_BARCODE_MASK: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_BARCODE_NOT_UNIQUE: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_BARCODE_ALREADY_USED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_KIT_LOT_EXPIRED: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_DELIMITER: _ClassVar[ModuleErrorKind]
    MODULE_ERROR_KIND_UNKNOWN_HAMILTON: _ClassVar[ModuleErrorKind]
ERROR_KIND_UNSPECIFIED: ErrorKind
ERROR_KIND_VALUE: ErrorKind
ERROR_KIND_RUNTIME: ErrorKind
ERROR_KIND_TYPE: ErrorKind
ERROR_KIND_NOT_IMPLEMENTED: ErrorKind
ERROR_KIND_INDEX: ErrorKind
ERROR_KIND_KEY: ErrorKind
ERROR_KIND_ASSERTION: ErrorKind
ERROR_KIND_TIMEOUT: ErrorKind
ERROR_KIND_CONNECTION: ErrorKind
ERROR_KIND_HAS_TIP: ErrorKind
ERROR_KIND_NO_TIP: ErrorKind
ERROR_KIND_TOO_LITTLE_LIQUID: ErrorKind
ERROR_KIND_TOO_LITTLE_VOLUME: ErrorKind
ERROR_KIND_RESOURCE_NOT_FOUND: ErrorKind
ERROR_KIND_NO_LOCATION: ErrorKind
ERROR_KIND_CHANNELS_DO_NOT_FIT: ErrorKind
ERROR_KIND_RESOURCE_SERVER: ErrorKind
ERROR_KIND_FIRMWARE: ErrorKind
MODULE_ERROR_KIND_UNSPECIFIED: ModuleErrorKind
MODULE_ERROR_KIND_COMMAND_SYNTAX: ModuleErrorKind
MODULE_ERROR_KIND_HARDWARE: ModuleErrorKind
MODULE_ERROR_KIND_COMMAND_NOT_COMPLETED: ModuleErrorKind
MODULE_ERROR_KIND_CLOT_DETECTED: ModuleErrorKind
MODULE_ERROR_KIND_BARCODE_UNREADABLE: ModuleErrorKind
MODULE_ERROR_KIND_TIP_TOO_LITTLE_VOLUME: ModuleErrorKind
MODULE_ERROR_KIND_TIP_ALREADY_FITTED: ModuleErrorKind
MODULE_ERROR_KIND_HAMILTON_NO_TIP: ModuleErrorKind
MODULE_ERROR_KIND_NO_CARRIER: ModuleErrorKind
MODULE_ERROR_KIND_NOT_COMPLETED: ModuleErrorKind
MODULE_ERROR_KIND_DISPENSE_WITH_PRESSURE_LLD: ModuleErrorKind
MODULE_ERROR_KIND_NO_TEACH_IN_SIGNAL: ModuleErrorKind
MODULE_ERROR_KIND_LOADING_TRAY: ModuleErrorKind
MODULE_ERROR_KIND_SEQUENCED_ASPIRATION_WITH_PRESSURE_LLD: ModuleErrorKind
MODULE_ERROR_KIND_NOT_ALLOWED_PARAMETER_COMBINATION: ModuleErrorKind
MODULE_ERROR_KIND_COVER_CLOSE: ModuleErrorKind
MODULE_ERROR_KIND_ASPIRATION: ModuleErrorKind
MODULE_ERROR_KIND_WASH_FLUID_OR_WASTE: ModuleErrorKind
MODULE_ERROR_KIND_INCUBATION: ModuleErrorKind
MODULE_ERROR_KIND_TADM_MEASUREMENT: ModuleErrorKind
MODULE_ERROR_KIND_NO_ELEMENT: ModuleErrorKind
MODULE_ERROR_KIND_ELEMENT_STILL_HOLDING: ModuleErrorKind
MODULE_ERROR_KIND_ELEMENT_LOST: ModuleErrorKind
MODULE_ERROR_KIND_ILLEGAL_TARGET_PLATE_POSITION: ModuleErrorKind
MODULE_ERROR_KIND_ILLEGAL_USER_ACCESS: ModuleErrorKind
MODULE_ERROR_KIND_POSITION_NOT_REACHABLE: ModuleErrorKind
MODULE_ERROR_KIND_UNEXPECTED_LLD: ModuleErrorKind
MODULE_ERROR_KIND_AREA_ALREADY_OCCUPIED: ModuleErrorKind
MODULE_ERROR_KIND_IMPOSSIBLE_TO_OCCUPY_AREA: ModuleErrorKind
MODULE_ERROR_KIND_ANTI_DROP_CONTROL: ModuleErrorKind
MODULE_ERROR_KIND_DECAPPER: ModuleErrorKind
MODULE_ERROR_KIND_DECAPPER_HANDLING: ModuleErrorKind
MODULE_ERROR_KIND_STOP: ModuleErrorKind
MODULE_ERROR_KIND_SUBSYSTEM: ModuleErrorKind
MODULE_ERROR_KIND_WRONG_CARRIER: ModuleErrorKind
MODULE_ERROR_KIND_NO_CARRIER_BARCODE: ModuleErrorKind
MODULE_ERROR_KIND_LIQUID_LEVEL: ModuleErrorKind
MODULE_ERROR_KIND_NOT_DETECTED: ModuleErrorKind
MODULE_ERROR_KIND_NOT_ASPIRATED: ModuleErrorKind
MODULE_ERROR_KIND_IMPROPER_DISPENSATION: ModuleErrorKind
MODULE_ERROR_KIND_NO_LABWARE: ModuleErrorKind
MODULE_ERROR_KIND_UNEXPECTED_LABWARE: ModuleErrorKind
MODULE_ERROR_KIND_WRONG_LABWARE: ModuleErrorKind
MODULE_ERROR_KIND_BARCODE_MASK: ModuleErrorKind
MODULE_ERROR_KIND_BARCODE_NOT_UNIQUE: ModuleErrorKind
MODULE_ERROR_KIND_BARCODE_ALREADY_USED: ModuleErrorKind
MODULE_ERROR_KIND_KIT_LOT_EXPIRED: ModuleErrorKind
MODULE_ERROR_KIND_DELIMITER: ModuleErrorKind
MODULE_ERROR_KIND_UNKNOWN_HAMILTON: ModuleErrorKind

class Error(_message.Message):
    __slots__ = ("kind", "message", "firmware_reply", "module_errors", "problem", "resource_name")
    KIND_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_REPLY_FIELD_NUMBER: _ClassVar[int]
    MODULE_ERRORS_FIELD_NUMBER: _ClassVar[int]
    PROBLEM_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    kind: ErrorKind
    message: str
    firmware_reply: str
    module_errors: _containers.RepeatedCompositeFieldContainer[ModuleError]
    problem: _types_pb2.Problem
    resource_name: str
    def __init__(self, kind: _Optional[_Union[ErrorKind, str]] = ..., message: _Optional[str] = ..., firmware_reply: _Optional[str] = ..., module_errors: _Optional[_Iterable[_Union[ModuleError, _Mapping]]] = ..., problem: _Optional[_Union[_types_pb2.Problem, str]] = ..., resource_name: _Optional[str] = ...) -> None: ...

class ModuleError(_message.Message):
    __slots__ = ("module", "kind", "message", "trace_information", "raw_response", "raw_module")
    MODULE_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TRACE_INFORMATION_FIELD_NUMBER: _ClassVar[int]
    RAW_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    RAW_MODULE_FIELD_NUMBER: _ClassVar[int]
    module: str
    kind: ModuleErrorKind
    message: str
    trace_information: int
    raw_response: str
    raw_module: str
    def __init__(self, module: _Optional[str] = ..., kind: _Optional[_Union[ModuleErrorKind, str]] = ..., message: _Optional[str] = ..., trace_information: _Optional[int] = ..., raw_response: _Optional[str] = ..., raw_module: _Optional[str] = ...) -> None: ...
