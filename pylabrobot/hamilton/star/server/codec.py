"""Python values to and from the STAR server's messages, by the Python method's type hints.

A request has one field per parameter, named as the parameter is; a response holds what the method
returns. How a value goes over follows from its annotation and the field it lands in, by rules the
`.proto` files are written to:

- An unset field with presence is an argument not given, so the method's default applies. A
  parameter is `Optional` only where its default is None, so None and "not given" are the same.
- A list that may be None is a `...List` message holding `values`; a value in a list or a map that
  may be None is an `Optional...` message holding `value`.
- A union is a oneof, its members in the order the annotation names them, every resource handle
  in it as one `ResourceRef`.
- A literal string, or a Python enum member, is the enum value named by the enum's prefix (its
  `..._UNSPECIFIED` value's, less `UNSPECIFIED`) and the string or the member's name in upper case,
  each run of anything not a letter or a digit as one `_`. Literal numbers are numbers.
- A tuple is a message of as many fields, in order; so is a dict entry whose key a map cannot
  take. A dataclass, a typed dict or a liquid class is a message of its fields, by name.
- A resource handle is a `ResourceRef` by id: the server makes the handle from the resource server
  both ends use.
- A method with no annotated result returns the device's reply, `FirmwareReply`.

Messages and descriptors are typed `Any` here: this reads and writes every service's messages by
their descriptors, which no static type describes.
"""

from __future__ import annotations

import collections.abc
import dataclasses
import datetime
import enum
import inspect
import re
import typing
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from google.protobuf.descriptor import FieldDescriptor

from pylabrobot.hamilton.liquid_classes.base import HamiltonLiquidClass
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.client import ResourceServer
from pylabrobot.resources.server.v1 import server_pb2 as spb
from pylabrobot.resources.server.v1 import types_pb2 as pb

_NoneType = type(None)
_RES = "pylabrobot.resources.server.v1"
_PKG = "pylabrobot.hamilton.star.server.v1"


# -- annotations ---------------------------------------------------------------------------------


def strip_optional(t: Any) -> Tuple[Any, bool]:
  """An annotation without its None, and whether it had one."""
  if typing.get_origin(t) is typing.Union:
    args = [a for a in typing.get_args(t) if a is not _NoneType]
    if len(args) < len(typing.get_args(t)):
      return (args[0] if len(args) == 1 else typing.Union[tuple(args)]), True
  return t, False


def is_list(t: Any) -> bool:
  return typing.get_origin(t) in (list, collections.abc.Sequence) or t is list


def is_handle(t: Any) -> bool:
  return isinstance(t, type) and issubclass(t, handles.Resource)


def members(t: Any) -> List[Any]:
  """A union's members as its oneof has them: every resource handle as one."""
  out: List[Any] = []
  for member in typing.get_args(t):
    if is_handle(member) and any(is_handle(m) for m in out):
      continue
    out.append(member)
  return out


def matches(value: Any, t: Any) -> bool:
  """Whether a value is of a union member's type."""
  inner, optional = strip_optional(t)
  if value is None:
    return optional
  if is_handle(inner):
    return isinstance(value, handles.Resource)
  if typing.get_origin(inner) is typing.Literal:
    return value in typing.get_args(inner)
  if is_list(inner):
    return isinstance(value, (list, tuple))
  if inner is float:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
  if inner is str:
    return isinstance(value, str)
  if isinstance(inner, type):
    return isinstance(value, inner)
  return False


def value_suffix(value: Any) -> str:
  """A literal's or an enum member's name as it ends its enum value."""
  return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").upper()


def _enum_prefix(descriptor: Any) -> str:
  return str(descriptor.values[0].name[: -len("UNSPECIFIED")])


def _is_typeddict(t: Any) -> bool:
  return isinstance(t, type) and typing.is_typeddict(t)


def _record_fields(t: Any) -> List[Tuple[str, Any]]:
  """A dataclass's, a typed dict's or a liquid class's fields, with their types."""
  if dataclasses.is_dataclass(t):
    hints = typing.get_type_hints(t)
    return [(f.name, hints[f.name]) for f in dataclasses.fields(t)]
  if _is_typeddict(t):
    return list(typing.get_type_hints(t).items())
  hints = typing.get_type_hints(t.__init__)
  return [(name, hint) for name, hint in hints.items() if name != "return"]


def _is_record(t: Any) -> bool:
  return isinstance(t, type) and (
    dataclasses.is_dataclass(t) or _is_typeddict(t) or t is HamiltonLiquidClass
  )


# -- message shapes ------------------------------------------------------------------------------


def _is_map(fd: Any) -> bool:
  return bool(
    fd.is_repeated
    and fd.type == FieldDescriptor.TYPE_MESSAGE
    and fd.message_type.GetOptions().map_entry
  )


def _is_repeated(fd: Any) -> bool:
  return fd.is_repeated and not _is_map(fd)


def _only_field(d: Any, name: str) -> Optional[FieldDescriptor]:
  return d.fields[0] if len(d.fields) == 1 and d.fields[0].name == name else None


def _real_oneof(d: Any, name: str) -> Any:
  oneof = d.oneofs_by_name.get(name)
  if oneof is None or (len(oneof.fields) == 1 and oneof.name == "_" + oneof.fields[0].name):
    return None
  return oneof


def _union_oneof(d: Any) -> Any:
  """The one oneof a union message is, when it is one."""
  real = [o for o in d.oneofs if not (len(o.fields) == 1 and o.name == "_" + o.fields[0].name)]
  if len(real) == 1 and len(real[0].fields) == len(d.fields):
    return real[0]
  return None


# A placeholder for a resource a request names, until the server makes handles for them all.
@dataclasses.dataclass(frozen=True)
class _Ref:
  id: bytes


# -- to messages ---------------------------------------------------------------------------------


def _scalar(fd: Any, t: Any, value: Any) -> Any:
  if fd.enum_type is not None:
    key = value.name if isinstance(value, enum.Enum) else value
    name = _enum_prefix(fd.enum_type) + value_suffix(key)
    try:
      return fd.enum_type.values_by_name[name].number
    except KeyError:
      raise ValueError(f"{value!r} is not one of {fd.enum_type.name}'s values") from None
  if fd.type in (FieldDescriptor.TYPE_DOUBLE, FieldDescriptor.TYPE_FLOAT):
    return float(value)
  if fd.type == FieldDescriptor.TYPE_BOOL:
    return bool(value)
  if fd.type == FieldDescriptor.TYPE_STRING:
    return value if isinstance(value, str) else str(value)
  if fd.type == FieldDescriptor.TYPE_BYTES:
    return bytes(value)
  return int(value)


def set_field(message: Any, fd: Any, t: Any, value: Any) -> None:
  """Put a value of type `t` in a field; None leaves it unset."""
  if value is None:
    return
  inner, _ = strip_optional(t)
  if _is_map(fd):
    key_t, value_t = typing.get_args(inner)
    value_fd = fd.message_type.fields_by_name["value"]
    target = getattr(message, fd.name)
    for key, item in value.items():
      if value_fd.type == FieldDescriptor.TYPE_MESSAGE:
        fill(target[key], value_t, item)
      else:
        target[key] = _scalar(value_fd, value_t, item)
    return
  if _is_repeated(fd):
    target = getattr(message, fd.name)
    if typing.get_origin(inner) is dict:
      # Entries, for keys a map cannot take.
      key_t, value_t = typing.get_args(inner)
      key_fd, value_fd = fd.message_type.fields
      for key, item in value.items():
        entry = target.add()
        set_field(entry, key_fd, key_t, key)
        set_field(entry, value_fd, value_t, item)
      return
    args = typing.get_args(inner)
    element_t = args[0] if args else Any
    for item in value:
      if fd.type == FieldDescriptor.TYPE_MESSAGE:
        fill(target.add(), element_t, item)
      else:
        target.append(_scalar(fd, element_t, item))
    return
  if fd.type == FieldDescriptor.TYPE_MESSAGE:
    sub = getattr(message, fd.name)
    sub.SetInParent()
    fill(sub, inner, value)
    return
  setattr(message, fd.name, _scalar(fd, inner, value))


def fill(message: Any, t: Any, value: Any) -> None:
  """Fill a message from a value of type `t`."""
  d = message.DESCRIPTOR
  name = d.full_name
  inner, _ = strip_optional(t)
  if name in (f"{_RES}.Vec3", f"{_RES}.Rotation"):
    message.x, message.y, message.z = value.x, value.y, value.z
    return
  if name == f"{_RES}.ResourceRef":
    message.id = value.id
    return
  if name in (f"{_RES}.ResourceNode", f"{_RES}.ResourceAttributes"):
    message.CopyFrom(value)
    return
  if name == f"{_PKG}.Date":
    message.year, message.month, message.day = value.year, value.month, value.day
    return
  if name == f"{_PKG}.FirmwareReply":
    _fill_reply(message, value)
    return
  oneof = _union_oneof(d)
  if oneof is not None:
    for fd, member in zip(oneof.fields, members(inner)):
      if matches(value, member):
        set_field(message, fd, member, value)
        return
    raise TypeError(f"{value!r} is none of {inner}")
  values = _only_field(d, "values")
  if values is not None and is_list(inner):
    set_field(message, values, inner, value)
    return
  only = _only_field(d, "value")
  if only is not None:
    set_field(message, only, inner, value)
    return
  entries = _only_field(d, "entries")
  if entries is not None and typing.get_origin(inner) is dict:
    set_field(message, entries, inner, value)
    return
  if typing.get_origin(inner) is tuple:
    for fd, item_t, item in zip(d.fields, typing.get_args(inner), value):
      set_field(message, fd, item_t, item)
    return
  if _is_record(inner):
    get = value.get if isinstance(value, dict) else lambda key: getattr(value, key)
    for field_name, field_t in _record_fields(inner):
      set_field(message, d.fields_by_name[field_name], field_t, get(field_name))
    return
  raise TypeError(f"no way to put {inner} in {name}")


def _fill_reply(message: Any, value: Any) -> None:
  if isinstance(value, str):
    message.raw = value
    return
  message.parsed.SetInParent()
  for key, item in value.items():
    target = message.parsed.parameters[key]
    if isinstance(item, bool) or isinstance(item, int):
      target.integer = int(item)
    elif isinstance(item, str):
      target.text = item
    elif all(isinstance(i, str) for i in item) and item:
      target.texts.values.extend(item)
    else:
      target.integers.SetInParent()
      target.integers.values.extend(int(i) for i in item)


# -- from messages -------------------------------------------------------------------------------


def _unscalar(fd: Any, t: Any, raw: Any) -> Any:
  inner, _ = strip_optional(t)
  if fd.enum_type is not None:
    name = fd.enum_type.values_by_number[raw].name[len(_enum_prefix(fd.enum_type)) :]
    if isinstance(inner, type) and issubclass(inner, enum.Enum):
      return next(m for m in inner if value_suffix(m.name) == name)
    literal = inner if typing.get_origin(inner) is typing.Literal else _literal_in(inner)
    return next(v for v in typing.get_args(literal) if value_suffix(v) == name)
  return raw


def _literal_in(t: Any) -> Any:
  for member in typing.get_args(t):
    if typing.get_origin(member) is typing.Literal:
      return member
  raise TypeError(f"no literal in {t}")


def get_field(message: Any, fd: Any, t: Any) -> Any:
  """A field's value as type `t`; an unset field with presence is None."""
  inner, _ = strip_optional(t)
  if _is_map(fd):
    key_t, value_t = typing.get_args(inner)
    value_fd = fd.message_type.fields_by_name["value"]
    out = {}
    for key, item in getattr(message, fd.name).items():
      out[key] = (
        read(item, value_t)
        if value_fd.type == FieldDescriptor.TYPE_MESSAGE
        else _unscalar(value_fd, value_t, item)
      )
    return out
  if _is_repeated(fd):
    items = getattr(message, fd.name)
    if typing.get_origin(inner) is dict:
      key_t, value_t = typing.get_args(inner)
      key_fd, value_fd = fd.message_type.fields
      return {get_field(e, key_fd, key_t): get_field(e, value_fd, value_t) for e in items}
    args = typing.get_args(inner)
    element_t = args[0] if args else Any
    if fd.type == FieldDescriptor.TYPE_MESSAGE:
      out_list = [read(item, element_t) for item in items]
    else:
      out_list = [_unscalar(fd, element_t, item) for item in items]
    if typing.get_origin(inner) is tuple:
      return tuple(out_list)
    return out_list
  if fd.has_presence and not message.HasField(fd.name):
    return None
  if fd.type == FieldDescriptor.TYPE_MESSAGE:
    return read(getattr(message, fd.name), inner)
  return _unscalar(fd, inner, getattr(message, fd.name))


def read(message: Any, t: Any) -> Any:
  """A message as a value of type `t`."""
  d = message.DESCRIPTOR
  name = d.full_name
  inner, _ = strip_optional(t)
  if name == f"{_RES}.Vec3":
    return Coordinate(message.x, message.y, message.z)
  if name == f"{_RES}.Rotation":
    return Rotation(message.x, message.y, message.z)
  if name == f"{_RES}.ResourceRef":
    return _Ref(message.id)
  if name in (f"{_RES}.ResourceNode", f"{_RES}.ResourceAttributes"):
    copy = type(message)()
    copy.CopyFrom(message)
    return copy
  if name == f"{_PKG}.Date":
    return datetime.date(message.year, message.month, message.day)
  if name == f"{_PKG}.FirmwareReply":
    return _read_reply(message)
  oneof = _union_oneof(d)
  if oneof is not None:
    which = message.WhichOneof(oneof.name)
    if which is None:
      return None
    for fd, member in zip(oneof.fields, members(inner)):
      if fd.name == which:
        return get_field(message, fd, member)
  values = _only_field(d, "values")
  if values is not None and is_list(inner):
    return get_field(message, values, inner)
  only = _only_field(d, "value")
  if only is not None:
    return get_field(message, only, inner)
  entries = _only_field(d, "entries")
  if entries is not None and typing.get_origin(inner) is dict:
    return get_field(message, entries, inner)
  if typing.get_origin(inner) is tuple:
    return tuple(
      get_field(message, fd, item_t) for fd, item_t in zip(d.fields, typing.get_args(inner))
    )
  if _is_record(inner):
    values_by_name = {
      field_name: get_field(message, d.fields_by_name[field_name], field_t)
      for field_name, field_t in _record_fields(inner)
    }
    if _is_typeddict(inner):
      return values_by_name
    return _make_record(inner, values_by_name)
  raise TypeError(f"no way to read {inner} from {name}")


def _make_record(cls: Any, values: Dict[str, Any]) -> Any:
  make: Any = cls
  if not dataclasses.is_dataclass(cls):
    return make(**values)
  init = {f.name for f in dataclasses.fields(cls) if f.init}
  record = make(**{k: v for k, v in values.items() if k in init})
  for key, value in values.items():
    if key not in init:
      object.__setattr__(record, key, value)
  return record


def _read_reply(message: Any) -> Any:
  which = message.WhichOneof("reply")
  if which == "raw":
    return message.raw
  out: Dict[str, Any] = {}
  for key, item in message.parsed.parameters.items():
    kind = item.WhichOneof("value")
    if kind == "integer":
      out[key] = item.integer
    elif kind == "text":
      out[key] = item.text
    elif kind == "texts":
      out[key] = list(item.texts.values)
    else:
      out[key] = list(item.integers.values)
  return out


# -- requests and responses ----------------------------------------------------------------------


# A method's **kwargs: what they are passed on to. The request carries those parameters' fields.
_FORWARDED: Dict[Tuple[str, str], Tuple[str, str]] = {
  ("Pipettes", "discard_tips"): ("Pipettes", "drop_tips"),
  ("Pipettes", "return_tips"): ("Pipettes", "drop_tips"),
  ("Head96", "discard_tips"): ("Head96", "drop_tips"),
  ("Head96", "return_tips"): ("Head96", "drop_tips"),
  ("Pipettes", "probe_z_using_plld"): ("Pipettes", "_plld_search"),
}


def _hints(fn: Callable[..., Any]) -> Dict[str, Any]:
  return typing.get_type_hints(fn)


def _forwarded_hints(cls: type, name: str) -> Dict[str, Any]:
  target = _FORWARDED.get((cls.__name__, name))
  if target is None:
    return {}
  return _hints(getattr(cls, target[1]))


def _parameter_type(p: inspect.Parameter, hints: Dict[str, Any]) -> Any:
  if p.name in hints:
    return hints[p.name]
  if p.default is not p.empty and p.default is not None:
    return type(p.default)
  return Any


def encode_request(
  cls: type, name: str, request: Any, args: Sequence[Any], kwargs: Dict[str, Any]
) -> Any:
  """Fill a request with a call's arguments, as `cls.name` would be called with them."""
  fn = getattr(cls, name)
  sig = inspect.signature(fn)
  bound = sig.bind(None, *args, **kwargs)
  hints = _hints(fn)
  d = request.DESCRIPTOR
  for p in list(sig.parameters.values())[1:]:
    if p.name not in bound.arguments:
      continue
    value = bound.arguments[p.name]
    if p.kind is p.VAR_KEYWORD:
      if "parameters" in d.fields_by_name and not _forwarded_hints(cls, name):
        for key, item in value.items():
          request.parameters[key] = str(item)
        continue
      forwarded = _forwarded_hints(cls, name)
      for key, item in value.items():
        if key not in d.fields_by_name:
          raise TypeError(f"{name}() got an unexpected keyword argument '{key}'")
        set_field(request, d.fields_by_name[key], forwarded.get(key, Any), item)
      continue
    t = _parameter_type(p, hints)
    _set_parameter(request, d, p.name, t, value)
  return request


def _set_parameter(request: Any, d: Any, name: str, t: Any, value: Any) -> None:
  oneof = _real_oneof(d, name)
  if oneof is not None:
    if value is None:
      return
    inner, _ = strip_optional(t)
    for fd, member in zip(oneof.fields, members(inner)):
      if matches(value, member):
        set_field(request, fd, member, value)
        return
    raise TypeError(f"{name}: {value!r} is none of {inner}")
  set_field(request, d.fields_by_name[name], t, value)


def decode_request(
  cls: type, name: str, request: Any, routing: Sequence[str] = ()
) -> Dict[str, Any]:
  """A request's arguments, as keyword arguments to `cls.name`. Resources are `_Ref`s until
  `resolve` makes handles of them."""
  fn = getattr(cls, name)
  sig = inspect.signature(fn)
  hints = _hints(fn)
  d = request.DESCRIPTOR
  out: Dict[str, Any] = {}
  named = set()
  for p in list(sig.parameters.values())[1:]:
    if p.kind is p.VAR_KEYWORD:
      continue
    named.add(p.name)
    t = _parameter_type(p, hints)
    oneof = _real_oneof(d, p.name)
    if oneof is not None:
      which = request.WhichOneof(p.name)
      if which is None:
        continue
      inner, _ = strip_optional(t)
      for fd, member in zip(oneof.fields, members(inner)):
        if fd.name == which:
          out[p.name] = get_field(request, fd, member)
      continue
    fd = d.fields_by_name[p.name]
    if fd.has_presence:
      if request.HasField(p.name):
        out[p.name] = get_field(request, fd, t)
      continue
    value = get_field(request, fd, t)
    if p.default is p.empty or value:
      out[p.name] = value
  if any(p.kind is p.VAR_KEYWORD for p in sig.parameters.values()):
    forwarded = _forwarded_hints(cls, name)
    if not forwarded and "parameters" in d.fields_by_name:
      out.update(dict(request.parameters))
    for fd in d.fields:
      if fd.name in named or fd.name in routing or fd.name not in forwarded:
        continue
      if fd.has_presence and not request.HasField(fd.name):
        continue
      out[fd.name] = get_field(request, fd, forwarded[fd.name])
  return out


def _result_type(cls: type, name: str) -> Any:
  fn = getattr(cls, name)
  return _hints(fn).get("return", inspect.Parameter.empty)


def encode_response(cls: type, name: str, response: Any, value: Any) -> Any:
  """Fill a response with what `cls.name` returned."""
  t = _result_type(cls, name)
  d = response.DESCRIPTOR
  if not d.fields:
    return response
  if t is inspect.Parameter.empty:
    set_field(response, d.fields[0], Any, value)
    return response
  inner, _ = strip_optional(t)
  if _is_typeddict(inner):
    fill(response, inner, value)
  elif typing.get_origin(inner) is tuple and len(d.fields) > 1:
    if value is not None:
      for fd, item_t, item in zip(d.fields, typing.get_args(inner), value):
        set_field(response, fd, item_t, item)
  else:
    set_field(response, d.fields[0], t, value)
  return response


def decode_response(cls: type, name: str, response: Any) -> Any:
  """What `cls.name` returned, from its response."""
  t = _result_type(cls, name)
  d = response.DESCRIPTOR
  if not d.fields:
    return None
  if t is inspect.Parameter.empty:
    return get_field(response, d.fields[0], Any)
  inner, _ = strip_optional(t)
  if _is_typeddict(inner):
    return read(response, inner)
  if typing.get_origin(inner) is tuple and len(d.fields) > 1:
    return tuple(
      get_field(response, fd, item_t) for fd, item_t in zip(d.fields, typing.get_args(inner))
    )
  return get_field(response, d.fields[0], t)


# -- resources -----------------------------------------------------------------------------------


def _refs_in(value: Any, found: List[bytes]) -> None:
  if isinstance(value, _Ref):
    found.append(value.id)
  elif isinstance(value, (list, tuple)):
    for item in value:
      _refs_in(item, found)
  elif isinstance(value, dict):
    for item in value.values():
      _refs_in(item, found)


def _replaced(value: Any, made: Dict[bytes, handles.Resource]) -> Any:
  if isinstance(value, _Ref):
    return made[value.id]
  if isinstance(value, list):
    return [_replaced(item, made) for item in value]
  if isinstance(value, tuple):
    return tuple(_replaced(item, made) for item in value)
  if isinstance(value, dict):
    return {key: _replaced(item, made) for key, item in value.items()}
  return value


async def resolve(server: ResourceServer, value: Any) -> Any:
  """`value` with every resource reference in it made a handle, in one read of the server."""
  ids: List[bytes] = []
  _refs_in(value, ids)
  if not ids:
    return value
  unique = list(dict.fromkeys(ids))
  response = await server.commands.get_resources(
    spb.GetResourcesRequest(resources=[pb.ResourceRef(id=i) for i in unique], depth=0)
  )
  made = await server.make_handles(list(response.nodes))
  return _replaced(value, {handle.id: handle for handle in made})
