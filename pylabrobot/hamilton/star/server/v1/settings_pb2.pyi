from pylabrobot.hamilton.star.server.v1 import core_grippers_pb2 as _core_grippers_pb2
from pylabrobot.hamilton.star.server.v1 import head384_pb2 as _head384_pb2
from pylabrobot.hamilton.star.server.v1 import head96_pb2 as _head96_pb2
from pylabrobot.hamilton.star.server.v1 import iswap_pb2 as _iswap_pb2
from pylabrobot.hamilton.star.server.v1 import pipettes_pb2 as _pipettes_pb2
from pylabrobot.hamilton.star.server.v1 import x_arm_pb2 as _x_arm_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Settings(_message.Message):
    __slots__ = ("pipettes", "head96", "head384", "iswap", "core_grippers", "left_x_arm", "right_x_arm")
    PIPETTES_FIELD_NUMBER: _ClassVar[int]
    HEAD96_FIELD_NUMBER: _ClassVar[int]
    HEAD384_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FIELD_NUMBER: _ClassVar[int]
    CORE_GRIPPERS_FIELD_NUMBER: _ClassVar[int]
    LEFT_X_ARM_FIELD_NUMBER: _ClassVar[int]
    RIGHT_X_ARM_FIELD_NUMBER: _ClassVar[int]
    pipettes: _pipettes_pb2.PipettesSettings
    head96: _head96_pb2.Head96Settings
    head384: _head384_pb2.Head384Settings
    iswap: _iswap_pb2.ISwapSettings
    core_grippers: _core_grippers_pb2.CoreGrippersSettings
    left_x_arm: _x_arm_pb2.XArmSettings
    right_x_arm: _x_arm_pb2.XArmSettings
    def __init__(self, pipettes: _Optional[_Union[_pipettes_pb2.PipettesSettings, _Mapping]] = ..., head96: _Optional[_Union[_head96_pb2.Head96Settings, _Mapping]] = ..., head384: _Optional[_Union[_head384_pb2.Head384Settings, _Mapping]] = ..., iswap: _Optional[_Union[_iswap_pb2.ISwapSettings, _Mapping]] = ..., core_grippers: _Optional[_Union[_core_grippers_pb2.CoreGrippersSettings, _Mapping]] = ..., left_x_arm: _Optional[_Union[_x_arm_pb2.XArmSettings, _Mapping]] = ..., right_x_arm: _Optional[_Union[_x_arm_pb2.XArmSettings, _Mapping]] = ...) -> None: ...
