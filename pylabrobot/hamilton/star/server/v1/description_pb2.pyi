from pylabrobot.hamilton.star.server.v1 import autoload_pb2 as _autoload_pb2
from pylabrobot.hamilton.star.server.v1 import core_grippers_pb2 as _core_grippers_pb2
from pylabrobot.hamilton.star.server.v1 import driver_pb2 as _driver_pb2
from pylabrobot.hamilton.star.server.v1 import front_cover_pb2 as _front_cover_pb2
from pylabrobot.hamilton.star.server.v1 import head384_pb2 as _head384_pb2
from pylabrobot.hamilton.star.server.v1 import head96_pb2 as _head96_pb2
from pylabrobot.hamilton.star.server.v1 import iswap_pb2 as _iswap_pb2
from pylabrobot.hamilton.star.server.v1 import pipettes_pb2 as _pipettes_pb2
from pylabrobot.hamilton.star.server.v1 import x_arm_pb2 as _x_arm_pb2
from pylabrobot.resources.server.v1 import types_pb2 as _types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DescribeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Description(_message.Message):
    __slots__ = ("name", "model", "body", "deck", "left_side_panel", "left_extension_housing", "extension_housing", "left_side_panel_installed", "driver")
    NAME_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    DECK_FIELD_NUMBER: _ClassVar[int]
    LEFT_SIDE_PANEL_FIELD_NUMBER: _ClassVar[int]
    LEFT_EXTENSION_HOUSING_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_HOUSING_FIELD_NUMBER: _ClassVar[int]
    LEFT_SIDE_PANEL_INSTALLED_FIELD_NUMBER: _ClassVar[int]
    DRIVER_FIELD_NUMBER: _ClassVar[int]
    name: str
    model: str
    body: _types_pb2.ResourceRef
    deck: _types_pb2.ResourceRef
    left_side_panel: _types_pb2.ResourceRef
    left_extension_housing: _types_pb2.ResourceRef
    extension_housing: bool
    left_side_panel_installed: bool
    driver: DriverDescription
    def __init__(self, name: _Optional[str] = ..., model: _Optional[str] = ..., body: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., deck: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., left_side_panel: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., left_extension_housing: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., extension_housing: _Optional[bool] = ..., left_side_panel_installed: _Optional[bool] = ..., driver: _Optional[_Union[DriverDescription, _Mapping]] = ...) -> None: ...

class DriverDescription(_message.Message):
    __slots__ = ("connected", "configuration", "firmware", "num_channels", "declared_json", "left_x_arm", "right_x_arm", "autoload", "front_cover")
    class FirmwareEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONNECTED_FIELD_NUMBER: _ClassVar[int]
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_FIELD_NUMBER: _ClassVar[int]
    NUM_CHANNELS_FIELD_NUMBER: _ClassVar[int]
    DECLARED_JSON_FIELD_NUMBER: _ClassVar[int]
    LEFT_X_ARM_FIELD_NUMBER: _ClassVar[int]
    RIGHT_X_ARM_FIELD_NUMBER: _ClassVar[int]
    AUTOLOAD_FIELD_NUMBER: _ClassVar[int]
    FRONT_COVER_FIELD_NUMBER: _ClassVar[int]
    connected: bool
    configuration: _driver_pb2.DeviceConfiguration
    firmware: _containers.ScalarMap[str, str]
    num_channels: int
    declared_json: str
    left_x_arm: XArmDescription
    right_x_arm: XArmDescription
    autoload: AutoloadDescription
    front_cover: FrontCoverDescription
    def __init__(self, connected: _Optional[bool] = ..., configuration: _Optional[_Union[_driver_pb2.DeviceConfiguration, _Mapping]] = ..., firmware: _Optional[_Mapping[str, str]] = ..., num_channels: _Optional[int] = ..., declared_json: _Optional[str] = ..., left_x_arm: _Optional[_Union[XArmDescription, _Mapping]] = ..., right_x_arm: _Optional[_Union[XArmDescription, _Mapping]] = ..., autoload: _Optional[_Union[AutoloadDescription, _Mapping]] = ..., front_cover: _Optional[_Union[FrontCoverDescription, _Mapping]] = ...) -> None: ...

class XArmDescription(_message.Message):
    __slots__ = ("resource", "pipettes", "head96", "head384", "iswap", "core_grippers", "settings")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    PIPETTES_FIELD_NUMBER: _ClassVar[int]
    HEAD96_FIELD_NUMBER: _ClassVar[int]
    HEAD384_FIELD_NUMBER: _ClassVar[int]
    ISWAP_FIELD_NUMBER: _ClassVar[int]
    CORE_GRIPPERS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    resource: _types_pb2.ResourceRef
    pipettes: PipettesDescription
    head96: Head96Description
    head384: Head384Description
    iswap: ISwapDescription
    core_grippers: CoreGrippersDescription
    settings: _x_arm_pb2.XArmSettings
    def __init__(self, resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., pipettes: _Optional[_Union[PipettesDescription, _Mapping]] = ..., head96: _Optional[_Union[Head96Description, _Mapping]] = ..., head384: _Optional[_Union[Head384Description, _Mapping]] = ..., iswap: _Optional[_Union[ISwapDescription, _Mapping]] = ..., core_grippers: _Optional[_Union[CoreGrippersDescription, _Mapping]] = ..., settings: _Optional[_Union[_x_arm_pb2.XArmSettings, _Mapping]] = ...) -> None: ...

class PipettesDescription(_message.Message):
    __slots__ = ("configuration", "resources", "shafts", "settings")
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    SHAFTS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    configuration: _pipettes_pb2.PipettesConfiguration
    resources: _containers.RepeatedCompositeFieldContainer[_types_pb2.ResourceRef]
    shafts: _containers.RepeatedCompositeFieldContainer[_types_pb2.ResourceRef]
    settings: _pipettes_pb2.PipettesSettings
    def __init__(self, configuration: _Optional[_Union[_pipettes_pb2.PipettesConfiguration, _Mapping]] = ..., resources: _Optional[_Iterable[_Union[_types_pb2.ResourceRef, _Mapping]]] = ..., shafts: _Optional[_Iterable[_Union[_types_pb2.ResourceRef, _Mapping]]] = ..., settings: _Optional[_Union[_pipettes_pb2.PipettesSettings, _Mapping]] = ...) -> None: ...

class Head96Description(_message.Message):
    __slots__ = ("configuration", "resource", "shafts", "settings")
    class ShaftsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _types_pb2.ResourceRef
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    SHAFTS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    configuration: _head96_pb2.Head96Configuration
    resource: _types_pb2.ResourceRef
    shafts: _containers.MessageMap[str, _types_pb2.ResourceRef]
    settings: _head96_pb2.Head96Settings
    def __init__(self, configuration: _Optional[_Union[_head96_pb2.Head96Configuration, _Mapping]] = ..., resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., shafts: _Optional[_Mapping[str, _types_pb2.ResourceRef]] = ..., settings: _Optional[_Union[_head96_pb2.Head96Settings, _Mapping]] = ...) -> None: ...

class Head384Description(_message.Message):
    __slots__ = ("configuration", "resource", "shafts", "settings")
    class ShaftsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _types_pb2.ResourceRef
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    SHAFTS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    configuration: _head384_pb2.Head384Configuration
    resource: _types_pb2.ResourceRef
    shafts: _containers.MessageMap[str, _types_pb2.ResourceRef]
    settings: _head384_pb2.Head384Settings
    def __init__(self, configuration: _Optional[_Union[_head384_pb2.Head384Configuration, _Mapping]] = ..., resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., shafts: _Optional[_Mapping[str, _types_pb2.ResourceRef]] = ..., settings: _Optional[_Union[_head384_pb2.Head384Settings, _Mapping]] = ...) -> None: ...

class ISwapDescription(_message.Message):
    __slots__ = ("configuration", "resource", "link_1", "gripper", "settings")
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    LINK_1_FIELD_NUMBER: _ClassVar[int]
    GRIPPER_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    configuration: _iswap_pb2.ISwapConfiguration
    resource: _types_pb2.ResourceRef
    link_1: _types_pb2.ResourceRef
    gripper: _types_pb2.ResourceRef
    settings: _iswap_pb2.ISwapSettings
    def __init__(self, configuration: _Optional[_Union[_iswap_pb2.ISwapConfiguration, _Mapping]] = ..., resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., link_1: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., gripper: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ..., settings: _Optional[_Union[_iswap_pb2.ISwapSettings, _Mapping]] = ...) -> None: ...

class CoreGrippersDescription(_message.Message):
    __slots__ = ("configuration", "settings")
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    configuration: _core_grippers_pb2.CoreGrippersConfiguration
    settings: _core_grippers_pb2.CoreGrippersSettings
    def __init__(self, configuration: _Optional[_Union[_core_grippers_pb2.CoreGrippersConfiguration, _Mapping]] = ..., settings: _Optional[_Union[_core_grippers_pb2.CoreGrippersSettings, _Mapping]] = ...) -> None: ...

class AutoloadDescription(_message.Message):
    __slots__ = ("configuration", "resource")
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    configuration: _autoload_pb2.AutoloadConfiguration
    resource: _types_pb2.ResourceRef
    def __init__(self, configuration: _Optional[_Union[_autoload_pb2.AutoloadConfiguration, _Mapping]] = ..., resource: _Optional[_Union[_types_pb2.ResourceRef, _Mapping]] = ...) -> None: ...

class FrontCoverDescription(_message.Message):
    __slots__ = ("configuration",)
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    configuration: _front_cover_pb2.FrontCoverConfiguration
    def __init__(self, configuration: _Optional[_Union[_front_cover_pb2.FrontCoverConfiguration, _Mapping]] = ...) -> None: ...
