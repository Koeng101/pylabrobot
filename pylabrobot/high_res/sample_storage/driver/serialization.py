"""A sample store's racks and nests as PLR's JSON, the form `Resource.serialize` writes, read from
and turned back into the definitions a resource store creates.

The kinds a sample store holds are written and read: plain resources, carriers, holders, plates,
wells, tubes, troughs and other containers, lids, tube racks and resource stacks. Tip racks, tip
spots and tips, petri dishes and plate adapters are not. A container converts volume and height in
the store through its height-volume data alone, so it is written without functions.

A store holds every number as a float; a whole number is written as an int, as PLR writes a size or
a location given as one.
"""

from typing import Any, Dict, Iterable, Optional, Tuple, Union

from google.protobuf import json_format

from pylabrobot.resources.barcode import Barcode
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import build
from pylabrobot.resources.store.v1 import types_pb2 as pb

K = pb.ResourceKind

_KINDS_BY_TYPE = {
  "Resource": K.RESOURCE_KIND_RESOURCE,
  "Carrier": K.RESOURCE_KIND_CARRIER,
  "PlateCarrier": K.RESOURCE_KIND_CARRIER,
  "ResourceHolder": K.RESOURCE_KIND_RESOURCE_HOLDER,
  "PlateHolder": K.RESOURCE_KIND_PLATE_HOLDER,
  "Plate": K.RESOURCE_KIND_PLATE,
  "Container": K.RESOURCE_KIND_CONTAINER,
  "Well": K.RESOURCE_KIND_WELL,
  "Tube": K.RESOURCE_KIND_TUBE,
  "Trough": K.RESOURCE_KIND_TROUGH,
  "Lid": K.RESOURCE_KIND_LID,
  "TubeRack": K.RESOURCE_KIND_TUBE_RACK,
  "ResourceStack": K.RESOURCE_KIND_RESOURCE_STACK,
}
# The class `Resource.serialize` names for each kind; a carrier of plates is a `PlateCarrier`.
_TYPES_BY_KIND = {kind: type_name for type_name, kind in _KINDS_BY_TYPE.items()}
_TYPES_BY_KIND[K.RESOURCE_KIND_CARRIER] = "Carrier"
_CONTAINER_KINDS = (
  K.RESOURCE_KIND_CONTAINER,
  K.RESOURCE_KIND_WELL,
  K.RESOURCE_KIND_TUBE,
  K.RESOURCE_KIND_TROUGH,
)
# Itemized kinds: their items are named in an `ordering` by identifier.
_ITEMIZED_KINDS = (K.RESOURCE_KIND_PLATE, K.RESOURCE_KIND_TUBE_RACK)
_HOLDER_KINDS = (K.RESOURCE_KIND_RESOURCE_HOLDER, K.RESOURCE_KIND_PLATE_HOLDER)
_KNOWN_KINDS = frozenset(_KINDS_BY_TYPE.values())

_BOTTOM_TYPES = {
  pb.WELL_BOTTOM_TYPE_UNSPECIFIED: "unknown",
  pb.WELL_BOTTOM_TYPE_FLAT: "flat",
  pb.WELL_BOTTOM_TYPE_U: "U",
  pb.WELL_BOTTOM_TYPE_V: "V",
}
_STACK_DIRECTIONS = {
  pb.STACK_DIRECTION_X: "x",
  pb.STACK_DIRECTION_Y: "y",
  pb.STACK_DIRECTION_Z: "z",
}
_CROSS_SECTION_TYPES = {
  pb.CROSS_SECTION_TYPE_UNSPECIFIED: "circle",
  pb.CROSS_SECTION_TYPE_CIRCLE: "circle",
  pb.CROSS_SECTION_TYPE_RECTANGLE: "rectangle",
}


def _number(value: float) -> Union[int, float]:
  """A number as PLR writes it: a whole number as an int."""
  return int(value) if value.is_integer() else value


def _coordinate(vector: pb.Vec3) -> Dict[str, Any]:
  return {
    "x": _number(vector.x),
    "y": _number(vector.y),
    "z": _number(vector.z),
    "type": Coordinate.__name__,
  }


def _vec3(data: Dict[str, Any]) -> pb.Vec3:
  return pb.Vec3(x=data["x"], y=data["y"], z=data["z"])


def _container_fields(spec: pb.ContainerSpec) -> Dict[str, Any]:
  height_volume_data = {
    _number(point.height): _number(point.volume) for point in spec.height_volume_data
  }
  return {
    "max_volume": _number(spec.max_volume) if spec.HasField("max_volume") else None,
    "material_z_thickness": (
      _number(spec.material_z_thickness) if spec.HasField("material_z_thickness") else None
    ),
    "compute_volume_from_height": None,
    "compute_height_from_volume": None,
    "height_volume_data": height_volume_data or None,
    "no_go_zones": [[_coordinate(zone.min), _coordinate(zone.max)] for zone in spec.no_go_zones],
  }


def serialize_definition(
  definition: pb.ResourceDefinition, parent_name: Optional[str] = None
) -> Dict[str, Any]:
  """A resource and everything under it as `Resource.serialize` writes it.

  Args:
    definition: The resource, as a store holds it.
    parent_name: The name of what it is in; unset for a root.

  Raises:
    ValueError: It, or something under it, is of a kind a sample store does not hold.
  """
  attributes = definition.attributes
  kind = attributes.kind
  if kind not in _KNOWN_KINDS:
    raise ValueError(
      f"Cannot serialize '{attributes.name}': a sample store holds no {K.Name(kind)}."
    )
  data: Dict[str, Any] = {
    "name": attributes.name,
    "type": (
      "PlateCarrier"
      if kind == K.RESOURCE_KIND_CARRIER and attributes.category == "plate_carrier"
      else _TYPES_BY_KIND[kind]
    ),
    "size_x": _number(attributes.size.x),
    "size_y": _number(attributes.size.y),
    "size_z": _number(attributes.size.z),
  }
  if attributes.HasField("location"):
    data["location"] = _coordinate(attributes.location)
  rotation = attributes.rotation
  if (rotation.x, rotation.y, rotation.z) != (0, 0, 0):
    data["rotation"] = {
      "x": _number(rotation.x),
      "y": _number(rotation.y),
      "z": _number(rotation.z),
      "type": Rotation.__name__,
    }
  if attributes.category:
    data["category"] = attributes.category
  if attributes.model:
    data["model"] = attributes.model
  if attributes.HasField("barcode"):
    data["barcode"] = Barcode(
      data=attributes.barcode.data,
      symbology=attributes.barcode.symbology,
      position_on_resource=attributes.barcode.position_on_resource,  # type: ignore[arg-type]
    ).serialize()
  if attributes.HasField("preferred_pickup_location"):
    data["preferred_pickup_location"] = _coordinate(attributes.preferred_pickup_location)
  if attributes.metadata.fields:
    data["metadata"] = json_format.MessageToDict(attributes.metadata)
  if definition.children:
    data["children"] = [
      serialize_definition(child, attributes.name) for child in definition.children
    ]
  if parent_name is not None:
    data["parent_name"] = parent_name

  if kind in _CONTAINER_KINDS:
    data.update(_container_fields(attributes.container))
  if kind in (K.RESOURCE_KIND_WELL, K.RESOURCE_KIND_TROUGH):
    data["bottom_type"] = _BOTTOM_TYPES[attributes.container.bottom_type]
  if kind == K.RESOURCE_KIND_WELL:
    data["cross_section_type"] = _CROSS_SECTION_TYPES[attributes.container.cross_section_type]
  if kind in _ITEMIZED_KINDS:
    data["ordering"] = {
      child.attributes.identifier: child.attributes.name
      for child in definition.children
      if child.attributes.identifier
    }
  if kind == K.RESOURCE_KIND_PLATE:
    if attributes.plate.plate_type not in ("", "skirted"):
      data["plate_type"] = attributes.plate.plate_type
    if attributes.plate.HasField("stacking_z_height"):
      data["stacking_z_height"] = _number(attributes.plate.stacking_z_height)
  if kind == K.RESOURCE_KIND_LID:
    data["nesting_z_height"] = _number(attributes.lid.nesting_z_height)
  if kind == K.RESOURCE_KIND_RESOURCE_STACK:
    data["direction"] = _STACK_DIRECTIONS[attributes.stack.direction]
  if kind in _HOLDER_KINDS:
    data["child_location"] = _coordinate(attributes.holder.child_location)
  if kind == K.RESOURCE_KIND_PLATE_HOLDER:
    data["pedestal_size_z"] = _number(attributes.holder.pedestal_size_z)
  return data


def _identifier_position(identifier: str) -> Tuple[int, int]:
  """The zero-based (row, column) of an item identifier such as "B3"."""
  letters = identifier.rstrip("0123456789")
  row = 0
  for letter in letters:
    row = row * 26 + (ord(letter.upper()) - ord("A") + 1)
  return row - 1, int(identifier[len(letters) :]) - 1


def definition_from_serialized(data: Dict[str, Any]) -> pb.ResourceDefinition:
  """The definition of a resource written by `serialize_definition` or `Resource.serialize`.

  Containers start empty, as a deserialized PLR resource does.

  Raises:
    ValueError: It, or something under it, is of a type a sample store does not hold.
  """
  type_name = data["type"]
  kind = _KINDS_BY_TYPE.get(type_name)
  if kind is None:
    raise ValueError(f"Cannot restore '{data['name']}': a sample store holds no {type_name}.")
  children = [definition_from_serialized(child) for child in data.get("children") or []]
  specs: Dict[str, Any] = {}
  state: Optional[pb.ResourceState] = None

  if kind in _CONTAINER_KINDS:
    container = pb.ContainerSpec()
    if data.get("max_volume") is not None:
      container.max_volume = data["max_volume"]
    if data.get("material_z_thickness") is not None:
      container.material_z_thickness = data["material_z_thickness"]
    for height, volume in sorted(
      (float(height), float(volume))
      for height, volume in (data.get("height_volume_data") or {}).items()
    ):
      container.height_volume_data.add(height=height, volume=volume)
    for low, high in data.get("no_go_zones") or []:
      container.no_go_zones.add(min=_vec3(low), max=_vec3(high))
    if kind in (K.RESOURCE_KIND_WELL, K.RESOURCE_KIND_TROUGH):
      bottom_types = {name: value for value, name in _BOTTOM_TYPES.items()}
      container.bottom_type = bottom_types[data.get("bottom_type", "unknown")]
    if kind == K.RESOURCE_KIND_WELL:
      container.cross_section_type = (
        pb.CROSS_SECTION_TYPE_RECTANGLE
        if data.get("cross_section_type") == "rectangle"
        else pb.CROSS_SECTION_TYPE_CIRCLE
      )
    specs["container"] = container
    state = pb.ResourceState(volume=pb.VolumeState())
  if kind in _ITEMIZED_KINDS:
    ordering: Dict[str, str] = data.get("ordering") or {}
    identifiers = {name: identifier for identifier, name in ordering.items()}
    for child in children:
      child.attributes.identifier = identifiers.get(child.attributes.name, "")
    positions = [_identifier_position(identifier) for identifier in ordering]
    specs["itemized"] = pb.ItemizedSpec(
      num_items_x=max((column for _, column in positions), default=-1) + 1,
      num_items_y=max((row for row, _ in positions), default=-1) + 1,
    )
  if kind == K.RESOURCE_KIND_RESOURCE_STACK:
    directions = {name: value for value, name in _STACK_DIRECTIONS.items()}
    specs["stack"] = pb.ResourceStackSpec(direction=directions[data.get("direction", "z")])
  if kind == K.RESOURCE_KIND_PLATE:
    plate = pb.PlateSpec(plate_type=data.get("plate_type", "skirted"))
    if data.get("stacking_z_height") is not None:
      plate.stacking_z_height = data["stacking_z_height"]
    specs["plate"] = plate
  if kind == K.RESOURCE_KIND_LID:
    specs["lid"] = pb.LidSpec(nesting_z_height=data["nesting_z_height"])
  if kind in _HOLDER_KINDS:
    holder = pb.HolderSpec(
      child_location=_vec3(data.get("child_location") or Coordinate.zero().serialize()),
      capacity=1,
    )
    if kind == K.RESOURCE_KIND_PLATE_HOLDER:
      holder.pedestal_size_z = data.get("pedestal_size_z", 0)
    specs["holder"] = holder

  barcode = data.get("barcode")
  if barcode is not None:
    specs["barcode"] = pb.Barcode(
      data=barcode["data"],
      symbology=barcode["symbology"],
      position_on_resource=barcode["position_on_resource"],
    )
  if data.get("preferred_pickup_location") is not None:
    specs["preferred_pickup_location"] = _vec3(data["preferred_pickup_location"])
  location = data.get("location")
  rotation = data.get("rotation")
  return build.resource(
    data["name"],
    Coordinate(data["size_x"], data["size_y"], data["size_z"]),
    kind=kind,
    location=Coordinate(location["x"], location["y"], location["z"]) if location else None,
    rotation=Rotation(rotation["x"], rotation["y"], rotation["z"]) if rotation else None,
    category=data.get("category") or "",
    model=data.get("model") or "",
    metadata=data.get("metadata"),
    children=children,
    state=state,
    **specs,
  )


def definition_from_nodes(root: bytes, nodes: Iterable[pb.ResourceNode]) -> pb.ResourceDefinition:
  """The definition of a resource the store holds, and everything under it, with their state.

  Args:
    root: The resource's id.
    nodes: It and everything under it, as `GetResources` answers them.
  """
  by_id = {node.id: node for node in nodes}

  def visit(node: pb.ResourceNode) -> pb.ResourceDefinition:
    definition = pb.ResourceDefinition(attributes=node.attributes)
    definition.initial_state.CopyFrom(node.state)
    definition.children.extend(visit(by_id[child]) for child in node.child_ids if child in by_id)
    return definition

  return visit(by_id[root])


def without_children(definition: pb.ResourceDefinition) -> pb.ResourceDefinition:
  """A copy of a definition with nothing under it."""
  copy = pb.ResourceDefinition()
  copy.CopyFrom(definition)
  del copy.children[:]
  return copy
