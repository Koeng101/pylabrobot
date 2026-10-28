"""What the generated codec builds on: the messages every service shares, as Python values.

`generated_codec.py` converts each RPC's arguments and result field by field, and calls these for
the messages that are the same everywhere: coordinates, rotations, resource references, dates and
the device's replies. A server makes the handles a request names first (`refs_in`), and the codec
takes each from them as the type its parameter says (`handle`).
"""

from __future__ import annotations

import datetime
import enum
import re
from typing import Any, Dict, List, Mapping, NoReturn, Sequence, Tuple, Type, TypeVar

from google.protobuf.message import Message

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.client import ResourceServer
from pylabrobot.resources.server.v1 import server_pb2 as spb
from pylabrobot.resources.server.v1 import types_pb2 as pb

# The handles a request's resources are, by id.
Refs = Mapping[bytes, handles.Resource]

H = TypeVar("H", bound=handles.Resource)
T = TypeVar("T")
E = TypeVar("E", bound=int)
V = TypeVar("V", str, int)


def missing(field: str) -> NoReturn:
  """Raise for a field a value needs that a message leaves unset."""
  raise ValueError(f"{field} is not set")


def one_of(value: V, allowed: Sequence[V]) -> V:
  """A value that must be one of `allowed`.

  Raises:
    ValueError: If it is not.
  """
  if value not in allowed:
    raise ValueError(f"{value!r} is none of {', '.join(repr(a) for a in allowed)}")
  return value


# -- scalars -------------------------------------------------------------------------------------


def value_suffix(value: Any) -> str:
  """A literal's or an enum member's name as it ends its enum value."""
  return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").upper()


def enum_number(numbers: Mapping[str, E], enum_name: str, value: Any) -> E:
  """The number of the enum value a literal or a Python enum member is, by `numbers`: each
  value's number by its suffix.

  Raises:
    ValueError: If it is none of them.
  """
  key = value.name if isinstance(value, enum.Enum) else value
  try:
    return numbers[value_suffix(key)]
  except KeyError:
    raise ValueError(f"{value!r} is not one of {enum_name}'s values") from None


def text(value: Any) -> str:
  return value if isinstance(value, str) else str(value)


# -- the shared messages -------------------------------------------------------------------------


def fill_xyz(message: Any, value: Any) -> None:
  """A `Vec3` or `Rotation` from anything with x, y and z."""
  message.x, message.y, message.z = value.x, value.y, value.z


def read_vec3(message: pb.Vec3, refs: Refs) -> Coordinate:
  return Coordinate(message.x, message.y, message.z)


def read_rotation(message: pb.Rotation, refs: Refs) -> Rotation:
  return Rotation(message.x, message.y, message.z)


def fill_ref(message: pb.ResourceRef, value: handles.Resource) -> None:
  message.id = value.id


def handle(refs: Refs, ref: pb.ResourceRef, kind: Type[H]) -> H:
  """The handle a reference names, which must be a `kind`.

  Raises:
    TypeError: If it is another kind of resource.
  """
  found = refs[ref.id]
  if not isinstance(found, kind):
    raise TypeError(f"{found!r} is not a {kind.__name__}")
  return found


def handle_of(
  refs: Refs, ref: pb.ResourceRef, kinds: Tuple[Type[handles.Resource], ...]
) -> handles.Resource:
  """The handle a reference names, which must be one of `kinds`.

  Raises:
    TypeError: If it is none of them.
  """
  found = refs[ref.id]
  if not isinstance(found, kinds):
    raise TypeError(f"{found!r} is none of {', '.join(k.__name__ for k in kinds)}")
  return found


def fill_node(message: pb.ResourceNode, value: pb.ResourceNode) -> None:
  message.CopyFrom(value)


def fill_attributes(message: pb.ResourceAttributes, value: pb.ResourceAttributes) -> None:
  message.CopyFrom(value)


def read_node(message: pb.ResourceNode, refs: Refs) -> pb.ResourceNode:
  copy = pb.ResourceNode()
  copy.CopyFrom(message)
  return copy


def read_attributes(message: pb.ResourceAttributes, refs: Refs) -> pb.ResourceAttributes:
  copy = pb.ResourceAttributes()
  copy.CopyFrom(message)
  return copy


def fill_date(message: Any, value: datetime.date) -> None:
  message.year, message.month, message.day = value.year, value.month, value.day


def read_date(message: Any, refs: Refs) -> datetime.date:
  return datetime.date(message.year, message.month, message.day)


def fill_reply(message: Any, value: Any) -> None:
  """A `FirmwareReply`: the reply as the device sent it, or as its format parsed it."""
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


def read_reply(message: Any, refs: Refs) -> Any:
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


# -- resources -----------------------------------------------------------------------------------


def _ids(message: Message, found: List[bytes]) -> None:
  """Every resource id in a message, in the order its fields hold them."""
  if isinstance(message, pb.ResourceRef):
    found.append(message.id)
    return
  for fd, value in message.ListFields():
    if fd.message_type is None:
      continue
    if fd.message_type.GetOptions().map_entry:
      items = list(value.values())
    elif fd.is_repeated:
      items = list(value)
    else:
      items = [value]
    for item in items:
      if isinstance(item, Message):
        _ids(item, found)


async def refs_in(server: ResourceServer, message: Message) -> Dict[bytes, handles.Resource]:
  """The handle of every resource a message names, in one read of the server."""
  ids: List[bytes] = []
  _ids(message, ids)
  if not ids:
    return {}
  unique = list(dict.fromkeys(ids))
  response = await server.commands.get_resources(
    spb.GetResourcesRequest(resources=[pb.ResourceRef(id=i) for i in unique], depth=0)
  )
  made = await server.make_handles(list(response.nodes))
  return {made_handle.id: made_handle for made_handle in made}
