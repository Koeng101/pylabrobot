from pylabrobot.hamilton.star.server.v1 import description_pb2 as _description_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class STARCreateResourcesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class STARCreateResourcesResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class STARSetupRequest(_message.Message):
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

class STARSetupResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class STARStopRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class STARStopResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
