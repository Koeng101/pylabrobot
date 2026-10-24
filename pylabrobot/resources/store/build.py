"""Definitions written in Python, for what has no model file: a device's own parts, say.

channel = build.resource(
  "channel_0",
  Coordinate(9, 9, 100),
  kind=pb.RESOURCE_KIND_PIPETTE_CHANNEL,
  location=Coordinate(10, 400, 20),
  pipette_channel=pb.PipetteChannelSpec(reference_point=build.vec3(Coordinate(4.5, 4.5, 0))),
  children=[shaft],
)
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from google.protobuf.struct_pb2 import Struct

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store.tree import to_rotation_message, to_vec3
from pylabrobot.resources.store.v1 import types_pb2 as pb


def vec3(coordinate: Coordinate) -> pb.Vec3:
  return to_vec3(coordinate)


def resource(
  name: str,
  size: Coordinate,
  kind: pb.ResourceKind = pb.RESOURCE_KIND_RESOURCE,
  location: Optional[Coordinate] = None,
  rotation: Optional[Rotation] = None,
  category: str = "",
  model: str = "",
  identifier: str = "",
  metadata: Optional[Mapping[str, Any]] = None,
  children: Sequence[pb.ResourceDefinition] = (),
  state: Optional[pb.ResourceState] = None,
  **specs: Any,
) -> pb.ResourceDefinition:
  """A resource and what hangs from it.

  Args:
    name: Its name; in a model, `{name}` in it becomes the instance's.
    size: Its size along its own axes.
    kind: What it is.
    location: Where it is in its parent; unset on a root.
    rotation: How it is turned in its parent.
    category: PLR's category, "plate_holder" say.
    model: The model it is.
    identifier: Its identifier in an itemized parent, "A1".
    metadata: Anything else about it.
    children: What hangs from it, in order.
    state: What it starts with: a volume, tracking, a jaw width.
    **specs: Its kind's spec, by the `ResourceAttributes` field name: `holder=pb.HolderSpec(...)`.
  """
  attributes = pb.ResourceAttributes(
    name=name,
    kind=kind,
    model=model,
    category=category,
    size=to_vec3(size),
    identifier=identifier,
    rotation=to_rotation_message(rotation or Rotation()),
    **specs,
  )
  if location is not None:
    attributes.location.CopyFrom(to_vec3(location))
  if metadata:
    struct = Struct()
    struct.update(metadata)
    attributes.metadata.CopyFrom(struct)
  definition = pb.ResourceDefinition(attributes=attributes, children=children)
  if state is not None:
    definition.initial_state.CopyFrom(state)
  return definition
