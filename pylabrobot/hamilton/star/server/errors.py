"""What a served call raised, as a Connect error, and back: the client raises the same class, with
the same message, as the device would have raised in this process."""

import asyncio
import re
from typing import Dict, List, Optional, Tuple, Type

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from protobuf.wkt import Any as AnyMessage

from pylabrobot.hamilton.star.driver import errors as star_errors
from pylabrobot.hamilton.star.driver.errors import STARFirmwareError, STARModuleError
from pylabrobot.hamilton.star.server.v1 import errors_pb2 as epb
from pylabrobot.lib.liquid_handling.errors import ChannelsDoNotFitError
from pylabrobot.resources.errors import (
  HasTipError,
  NoLocationError,
  NoTipError,
  ResourceNotFoundError,
  TooLittleLiquidError,
  TooLittleVolumeError,
)
from pylabrobot.resources.server.errors import ServerError

ERROR_TYPE = "pylabrobot.hamilton.star.server.v1.Error"

# Each kind and the class it is, the subclasses ahead of what they derive from.
_KINDS: List[Tuple[Type[BaseException], int, Code]] = [
  (STARFirmwareError, epb.ERROR_KIND_FIRMWARE, Code.ABORTED),
  (ServerError, epb.ERROR_KIND_RESOURCE_SERVER, Code.FAILED_PRECONDITION),
  (HasTipError, epb.ERROR_KIND_HAS_TIP, Code.FAILED_PRECONDITION),
  (NoTipError, epb.ERROR_KIND_NO_TIP, Code.FAILED_PRECONDITION),
  (TooLittleLiquidError, epb.ERROR_KIND_TOO_LITTLE_LIQUID, Code.FAILED_PRECONDITION),
  (TooLittleVolumeError, epb.ERROR_KIND_TOO_LITTLE_VOLUME, Code.FAILED_PRECONDITION),
  (ResourceNotFoundError, epb.ERROR_KIND_RESOURCE_NOT_FOUND, Code.NOT_FOUND),
  (NoLocationError, epb.ERROR_KIND_NO_LOCATION, Code.FAILED_PRECONDITION),
  (ChannelsDoNotFitError, epb.ERROR_KIND_CHANNELS_DO_NOT_FIT, Code.INVALID_ARGUMENT),
  (NotImplementedError, epb.ERROR_KIND_NOT_IMPLEMENTED, Code.UNIMPLEMENTED),
  (asyncio.TimeoutError, epb.ERROR_KIND_TIMEOUT, Code.DEADLINE_EXCEEDED),
  (TimeoutError, epb.ERROR_KIND_TIMEOUT, Code.DEADLINE_EXCEEDED),
  (ConnectionError, epb.ERROR_KIND_CONNECTION, Code.UNAVAILABLE),
  (KeyError, epb.ERROR_KIND_KEY, Code.INVALID_ARGUMENT),
  (IndexError, epb.ERROR_KIND_INDEX, Code.INVALID_ARGUMENT),
  (AssertionError, epb.ERROR_KIND_ASSERTION, Code.INTERNAL),
  (TypeError, epb.ERROR_KIND_TYPE, Code.INVALID_ARGUMENT),
  (ValueError, epb.ERROR_KIND_VALUE, Code.INVALID_ARGUMENT),
  (RuntimeError, epb.ERROR_KIND_RUNTIME, Code.FAILED_PRECONDITION),
]
_CLASSES: Dict[int, Type[BaseException]] = {}
for _cls, _kind, _ in _KINDS:
  _CLASSES.setdefault(_kind, _cls)


def _snake(name: str) -> str:
  name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
  return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).upper()


def _module_kind_name(cls: type) -> str:
  name = cls.__name__
  return "MODULE_ERROR_KIND_" + _snake(name[: -len("Error")] if name.endswith("Error") else name)


# Each module error class, by the name of its kind.
_MODULE_CLASSES: Dict[str, Type[STARModuleError]] = {
  _module_kind_name(cls): cls
  for cls in vars(star_errors).values()
  if isinstance(cls, type) and issubclass(cls, STARModuleError) and cls is not STARModuleError
}


def _message(error: BaseException) -> str:
  """What the error was made with, so making it again gives the same `str()`."""
  if len(error.args) == 1 and isinstance(error.args[0], str):
    return error.args[0]
  return str(error)


def to_connect_error(error: BaseException) -> ConnectError:
  """An error a call raised, as a Connect error carrying an `Error` detail."""
  detail = epb.Error(message=_message(error))
  code = Code.UNKNOWN
  for cls, kind, kind_code in _KINDS:
    if isinstance(error, cls):
      detail.kind, code = kind, kind_code  # type: ignore[assignment]
      break
  if isinstance(error, STARFirmwareError):
    detail.firmware_reply = error.raw_response
    for module, module_error in error.errors.items():
      detail.module_errors.add(
        module=module,
        kind=epb.ModuleErrorKind.Value(_module_kind_name(type(module_error))),
        message=module_error.message,
        trace_information=module_error.trace_information,
        raw_response=module_error.raw_response,
        raw_module=module_error.raw_module,
      )
  if isinstance(error, ServerError):
    detail.problem = error.problem
    detail.resource_name = error.resource_name
  any_detail = AnyMessage(
    type_url=f"type.googleapis.com/{ERROR_TYPE}", value=detail.SerializeToString()
  )
  return ConnectError(code, str(error), [any_detail])


def from_connect_error(error: ConnectError) -> Optional[BaseException]:
  """The error a call raised, from the Connect error it came as; None when it carries none."""
  for item in error.details:
    if item.type_name != ERROR_TYPE:
      continue
    detail = epb.Error.FromString(item.message_bytes)
    if detail.kind == epb.ERROR_KIND_FIRMWARE:
      modules = {
        m.module: _MODULE_CLASSES[epb.ModuleErrorKind.Name(m.kind)](
          message=m.message,
          trace_information=m.trace_information,
          raw_response=m.raw_response,
          raw_module=m.raw_module,
        )
        for m in detail.module_errors
      }
      firmware = STARFirmwareError(errors=modules, raw_response=detail.firmware_reply)
      # Its message was fixed when it was raised, before anything edited its modules' messages.
      firmware.args = (detail.message,)
      return firmware
    if detail.kind == epb.ERROR_KIND_RESOURCE_SERVER:
      return ServerError(detail.problem, detail.message, detail.resource_name)
    cls = _CLASSES.get(detail.kind, Exception)
    return cls(detail.message) if detail.message else cls()
  return None
