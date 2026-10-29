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
    ERROR_KIND_TIMEOUT: _ClassVar[ErrorKind]
    ERROR_KIND_KEY: _ClassVar[ErrorKind]
    ERROR_KIND_TYPE: _ClassVar[ErrorKind]
    ERROR_KIND_NOT_IMPLEMENTED: _ClassVar[ErrorKind]
    ERROR_KIND_CONNECTION: _ClassVar[ErrorKind]
ERROR_KIND_UNSPECIFIED: ErrorKind
ERROR_KIND_VALUE: ErrorKind
ERROR_KIND_RUNTIME: ErrorKind
ERROR_KIND_TIMEOUT: ErrorKind
ERROR_KIND_KEY: ErrorKind
ERROR_KIND_TYPE: ErrorKind
ERROR_KIND_NOT_IMPLEMENTED: ErrorKind
ERROR_KIND_CONNECTION: ErrorKind

class Error(_message.Message):
    __slots__ = ("kind", "message", "type_name")
    KIND_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    kind: ErrorKind
    message: str
    type_name: str
    def __init__(self, kind: _Optional[_Union[ErrorKind, str]] = ..., message: _Optional[str] = ..., type_name: _Optional[str] = ...) -> None: ...

class OptionalDouble(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: float
    def __init__(self, value: _Optional[float] = ...) -> None: ...

class Progress(_message.Message):
    __slots__ = ("elapsed", "done")
    ELAPSED_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    elapsed: float
    done: bool
    def __init__(self, elapsed: _Optional[float] = ..., done: _Optional[bool] = ...) -> None: ...

class HeaterShaker(_message.Message):
    __slots__ = ("name", "index", "resource", "target_temperature")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    TARGET_TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    name: str
    index: int
    resource: _types_pb2.ResourceRef
    target_temperature: float
    def __init__(self, name: _Optional[str] = ..., index: _Optional[int] = ..., resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., target_temperature: _Optional[float] = ...) -> None: ...

class DescribeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DescribeResponse(_message.Message):
    __slots__ = ("heater_shakers",)
    HEATER_SHAKERS_FIELD_NUMBER: _ClassVar[int]
    heater_shakers: _containers.RepeatedCompositeFieldContainer[HeaterShaker]
    def __init__(self, heater_shakers: _Optional[_Iterable[_Union[HeaterShaker, _Mapping]]] = ...) -> None: ...

class SetupRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class SetupResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class StopResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LockPlateRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class LockPlateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UnlockPlateRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class UnlockPlateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetIsShakingRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetIsShakingResponse(_message.Message):
    __slots__ = ("shaking",)
    SHAKING_FIELD_NUMBER: _ClassVar[int]
    shaking: bool
    def __init__(self, shaking: _Optional[bool] = ...) -> None: ...

class ShakeRequest(_message.Message):
    __slots__ = ("name", "speed", "duration", "direction", "acceleration", "timeout")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    name: str
    speed: float
    duration: float
    direction: int
    acceleration: int
    timeout: OptionalDouble
    def __init__(self, name: _Optional[str] = ..., speed: _Optional[float] = ..., duration: _Optional[float] = ..., direction: _Optional[int] = ..., acceleration: _Optional[int] = ..., timeout: _Optional[_Union[OptionalDouble, _Mapping]] = ...) -> None: ...

class StopShakingRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class StopShakingResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetTemperatureRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetTemperatureResponse(_message.Message):
    __slots__ = ("temperature",)
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    temperature: float
    def __init__(self, temperature: _Optional[float] = ...) -> None: ...

class GetEdgeTemperatureRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetEdgeTemperatureResponse(_message.Message):
    __slots__ = ("temperature",)
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    temperature: float
    def __init__(self, temperature: _Optional[float] = ...) -> None: ...

class SetTemperatureRequest(_message.Message):
    __slots__ = ("name", "temperature", "passive")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    PASSIVE_FIELD_NUMBER: _ClassVar[int]
    name: str
    temperature: float
    passive: bool
    def __init__(self, name: _Optional[str] = ..., temperature: _Optional[float] = ..., passive: _Optional[bool] = ...) -> None: ...

class SetTemperatureResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class WaitForTemperatureRequest(_message.Message):
    __slots__ = ("name", "timeout", "tolerance")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    TOLERANCE_FIELD_NUMBER: _ClassVar[int]
    name: str
    timeout: float
    tolerance: float
    def __init__(self, name: _Optional[str] = ..., timeout: _Optional[float] = ..., tolerance: _Optional[float] = ...) -> None: ...

class HoldTemperatureRequest(_message.Message):
    __slots__ = ("name", "duration")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    name: str
    duration: float
    def __init__(self, name: _Optional[str] = ..., duration: _Optional[float] = ...) -> None: ...

class DeactivateRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class DeactivateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
