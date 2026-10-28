from pylabrobot.hamilton.star.server.v1 import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FrontCoverConfiguration(_message.Message):
    __slots__ = ("position_codes",)
    class PositionCodesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    POSITION_CODES_FIELD_NUMBER: _ClassVar[int]
    position_codes: _containers.ScalarMap[str, int]
    def __init__(self, position_codes: _Optional[_Mapping[str, int]] = ...) -> None: ...

class FrontCoverRequestStateRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FrontCoverRequestStateResponse(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: _types_pb2.FrontCoverState
    def __init__(self, state: _Optional[_Union[_types_pb2.FrontCoverState, str]] = ...) -> None: ...

class FrontCoverEnableControlRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FrontCoverEnableControlResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...

class FrontCoverDisableControlRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FrontCoverDisableControlResponse(_message.Message):
    __slots__ = ("reply",)
    REPLY_FIELD_NUMBER: _ClassVar[int]
    reply: _types_pb2.FirmwareReply
    def __init__(self, reply: _Optional[_Union[_types_pb2.FirmwareReply, _Mapping]] = ...) -> None: ...
