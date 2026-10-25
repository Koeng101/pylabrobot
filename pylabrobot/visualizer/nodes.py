"""Resources as a store holds them, in the JSON a browser draws them from.

The pages read `Resource.serialize()` and `Resource.serialize_state()` of PLR's resource classes.
These functions give the same JSON for a resource from what the store holds of it: its kind decides
the fields its class adds, and its type name is the class it was defined as.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union

from google.protobuf import json_format

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.visualizer.mirror import TreeMirror

K = pb.ResourceKind

CONTAINER_KINDS = frozenset(
  {
    K.RESOURCE_KIND_CONTAINER,
    K.RESOURCE_KIND_WELL,
    K.RESOURCE_KIND_TROUGH,
    K.RESOURCE_KIND_TUBE,
    K.RESOURCE_KIND_PETRI_DISH,
    K.RESOURCE_KIND_TRASH,
  }
)
ITEMIZED_KINDS = frozenset(
  {K.RESOURCE_KIND_PLATE, K.RESOURCE_KIND_TIP_RACK, K.RESOURCE_KIND_TUBE_RACK}
)
# What a head mounts: held by a spot or a shaft, drawn as its holder's state by the 2D page.
TOOL_KINDS = frozenset({K.RESOURCE_KIND_TIP, K.RESOURCE_KIND_HEAD_TOOL})

_BOTTOM_TYPES = {
  pb.WELL_BOTTOM_TYPE_FLAT: "flat",
  pb.WELL_BOTTOM_TYPE_U: "U",
  pb.WELL_BOTTOM_TYPE_V: "V",
  pb.WELL_BOTTOM_TYPE_UNSPECIFIED: "unknown",
}
_CROSS_SECTION_TYPES = {
  pb.CROSS_SECTION_TYPE_CIRCLE: "circle",
  pb.CROSS_SECTION_TYPE_RECTANGLE: "rectangle",
}
_PICKUP_METHODS = {
  pb.TIP_PICKUP_METHOD_OUT_OF_RACK: "OUT_OF_RACK",
  pb.TIP_PICKUP_METHOD_OUT_OF_WASH_LIQUID: "OUT_OF_WASH_LIQUID",
}


def coordinate(vector: pb.Vec3) -> Dict[str, Any]:
  """A vector as `Coordinate.serialize` gives it."""
  return Coordinate(vector.x, vector.y, vector.z).serialize()


def rotation(angles: pb.Rotation) -> Dict[str, Any]:
  """A rotation as `Rotation.serialize` gives it."""
  return Rotation(x=angles.x, y=angles.y, z=angles.z).serialize()


def _number(value: float) -> Union[float, str]:
  """A number as PLR's serializer writes it: a float that is not finite as text."""
  if math.isfinite(value):
    return value
  return "nan" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")


def is_rotated(angles: pb.Rotation) -> bool:
  return not (angles.x == 0 and angles.y == 0 and angles.z == 0)


class TipNames:
  """The name each tip spot gives the tip it would make next, per serialization.

  A spot's serialization makes a tip to describe, and each tip made takes the next number: the
  first serialization of a spot that has made one tip names its prototype "<spot>#1", the next
  "<spot>#2". Kept per page, as each page serializes on its own.
  """

  def __init__(self) -> None:
    self._made: Dict[bytes, int] = {}

  def next_name(self, spot: pb.ResourceNode) -> str:
    serialized = self._made.get(spot.id, 0)
    self._made[spot.id] = serialized + 1
    return f"{spot.attributes.name}#{spot.state.tips_made + serialized}"


# Carriers the browser draws by what they carry, by their category.
_CARRIER_TYPES = {
  "tip_carrier": "TipCarrier",
  "plate_carrier": "PlateCarrier",
  "trough_carrier": "TroughCarrier",
  "tube_carrier": "TubeCarrier",
  "mfx_carrier": "MFXCarrier",
}


def type_name(attributes: pb.ResourceAttributes) -> str:
  """The class the browser draws a resource as: its handle's class, which its kind decides, made
  finer by its model or category for the decks and carriers the browser draws apart."""
  if attributes.kind == pb.RESOURCE_KIND_DECK:
    if attributes.deck.HasField("hamilton"):
      return "HamiltonSTARDeck"
    if attributes.model == "OTDeck":
      return "OTDeck"
  if attributes.kind == pb.RESOURCE_KIND_CARRIER and attributes.category in _CARRIER_TYPES:
    return _CARRIER_TYPES[attributes.category]
  return handles.HANDLE_TYPES[attributes.kind].__name__


def _container_fields(attributes: pb.ResourceAttributes) -> Dict[str, Any]:
  spec = attributes.container
  points = {point.height: point.volume for point in spec.height_volume_data}
  data: Dict[str, Any] = {
    "max_volume": _number(spec.max_volume if spec.HasField("max_volume") else math.inf),
    "material_z_thickness": (
      spec.material_z_thickness if spec.HasField("material_z_thickness") else None
    ),
    "compute_volume_from_height": None,
    "compute_height_from_volume": None,
    "height_volume_data": points or None,
    "no_go_zones": [[coordinate(zone.min), coordinate(zone.max)] for zone in spec.no_go_zones],
  }
  kind = attributes.kind
  if kind == K.RESOURCE_KIND_WELL:
    data["bottom_type"] = _BOTTOM_TYPES[spec.bottom_type]
    data["cross_section_type"] = _CROSS_SECTION_TYPES.get(spec.cross_section_type, "circle")
  elif kind == K.RESOURCE_KIND_TROUGH:
    data["bottom_type"] = _BOTTOM_TYPES[spec.bottom_type]
    if spec.through_base_to_container_base != 0:
      data["through_base_to_container_base"] = spec.through_base_to_container_base
  return data


def _tool_fields(attributes: pb.ResourceAttributes, data: Dict[str, Any]) -> Dict[str, Any]:
  """A head tool's fields; a tip's replace its width and depth with its diameter."""
  tool = attributes.head_tool
  data = {
    **data,
    "fitting_depth": tool.fitting_depth,
    "pick_up_location": (
      coordinate(tool.pick_up_location) if tool.HasField("pick_up_location") else None
    ),
    "is_conductive": tool.is_conductive if tool.HasField("is_conductive") else None,
  }
  if attributes.kind != K.RESOURCE_KIND_TIP:
    return data
  tip = attributes.tip
  diameter = data.pop("size_x")
  data.pop("size_y")
  data = {
    **data,
    "diameter": diameter,
    "has_filter": tip.has_filter,
    "nominal_volume": tip.nominal_volume,
    "maximal_volume": tip.maximal_volume,
    "collar_height": tip.collar_height if tip.HasField("collar_height") else None,
  }
  if tip.HasField("hamilton"):
    data.pop("fitting_depth", None)
    data["pickup_method"] = _PICKUP_METHODS.get(tip.hamilton.pickup_method, "OUT_OF_RACK")
    data["tip_size"] = tip.hamilton.tip_size
  return data


def _deck_fields(attributes: pb.ResourceAttributes, data: Dict[str, Any]) -> Dict[str, Any]:
  """A deck drops its model; a Hamilton deck keeps it, with its tracks and what it was built
  with, which is encoded as its children."""
  data.pop("model", None)
  if not attributes.deck.HasField("hamilton"):
    return data
  if attributes.display_model or attributes.model:
    data["model"] = attributes.display_model or attributes.model
  data["num_tracks"] = attributes.deck.hamilton.num_tracks
  data["with_trash"] = False
  data["with_trash96"] = False
  data["core_grippers"] = None
  if type_name(attributes) == "HamiltonSTARDeck":
    data["with_waste_block"] = False
    data["with_teaching_needle_rack"] = False
  return data


def _attributes_data(
  attributes: pb.ResourceAttributes, parent_name: Optional[str]
) -> Dict[str, Any]:
  """What `Resource.serialize` gives for what a resource is, without its children."""
  data: Dict[str, Any] = {
    "name": attributes.name,
    "type": type_name(attributes),
    "size_x": attributes.size.x,
    "size_y": attributes.size.y,
    "size_z": attributes.size.z,
  }
  if attributes.HasField("location"):
    data["location"] = coordinate(attributes.location)
  if is_rotated(attributes.rotation):
    data["rotation"] = rotation(attributes.rotation)
  if attributes.category:
    data["category"] = attributes.category
  # What it is drawn as: its own `model`, unless it is drawn as another.
  if attributes.display_model or attributes.model:
    data["model"] = attributes.display_model or attributes.model
  if attributes.HasField("barcode"):
    data["barcode"] = {
      "data": attributes.barcode.data,
      "symbology": attributes.barcode.symbology,
      "position_on_resource": attributes.barcode.position_on_resource,
    }
  if attributes.HasField("preferred_pickup_location"):
    data["preferred_pickup_location"] = coordinate(attributes.preferred_pickup_location)
  if attributes.metadata.fields:
    data["metadata"] = json_format.MessageToDict(attributes.metadata)
  if parent_name is not None:
    data["parent_name"] = parent_name
  return data


def _kind_fields(
  attributes: pb.ResourceAttributes, data: Dict[str, Any], items: Dict[str, str]
) -> Dict[str, Any]:
  """The fields a resource's class adds to `Resource.serialize`."""
  kind = attributes.kind
  if kind in CONTAINER_KINDS:
    data.update(_container_fields(attributes))
    if kind == K.RESOURCE_KIND_PETRI_DISH:
      diameter, height = data.pop("size_x"), data.pop("size_z")
      data.pop("size_y")
      data["diameter"], data["height"] = diameter, height
  if kind in ITEMIZED_KINDS:
    data["ordering"] = items
  if kind == K.RESOURCE_KIND_PLATE:
    if attributes.plate.plate_type not in ("", "skirted"):
      data["plate_type"] = attributes.plate.plate_type
    if attributes.plate.HasField("stacking_z_height"):
      data["stacking_z_height"] = attributes.plate.stacking_z_height
  if kind == K.RESOURCE_KIND_TIP_RACK:
    rack = attributes.tip_rack
    frame_height = rack.frame_height if rack.HasField("frame_height") else None
    if rack.style == pb.TIP_RACK_STYLE_EMBEDDED:
      data["sinking_depth"] = rack.sinking_depth
      data["frame_height"] = frame_height
    elif rack.style in (pb.TIP_RACK_STYLE_STANDING, pb.TIP_RACK_STYLE_NESTED):
      data["frame_height"] = frame_height
      data["stacking_z_height"] = (
        rack.stacking_z_height if rack.HasField("stacking_z_height") else None
      )
  if kind in TOOL_KINDS:
    data = _tool_fields(attributes, data)
  if kind == K.RESOURCE_KIND_LID:
    data["nesting_z_height"] = attributes.lid.nesting_z_height
  if attributes.HasField("holder"):
    data["child_location"] = coordinate(attributes.holder.child_location)
    if attributes.holder.HasField("pedestal_size_z"):
      data["pedestal_size_z"] = attributes.holder.pedestal_size_z
  if kind == K.RESOURCE_KIND_PLATE_ADAPTER:
    spec = attributes.plate_adapter
    data.update(
      {
        "dx": spec.dx,
        "dy": spec.dy,
        "dz": spec.dz,
        "adapter_hole_size_x": spec.adapter_hole_size_x,
        "adapter_hole_size_y": spec.adapter_hole_size_y,
        "adapter_hole_dx": spec.adapter_hole_dx,
        "adapter_hole_dy": spec.adapter_hole_dy,
        "plate_z_offset": spec.plate_z_offset,
      }
    )
  if kind == K.RESOURCE_KIND_TIP_MOUNTING_SHAFT:
    data["tip_pickup_mode"] = attributes.tip_mounting_shaft.tip_pickup_mode
    data["cross_section_type"] = "circle"
  if kind == K.RESOURCE_KIND_N_CHANNEL_PIPETTE:
    data["reference_point"] = coordinate(attributes.n_channel_pipette.reference_point)
    data["independent_channel_actuation"] = (
      attributes.n_channel_pipette.independent_channel_actuation
    )
  if kind == K.RESOURCE_KIND_LINK_BODY:
    link = attributes.link_body
    data["proximal_joint"] = coordinate(link.proximal_joint)
    data["distal_joint"] = coordinate(link.distal_joint) if link.HasField("distal_joint") else None
  if kind == K.RESOURCE_KIND_MECHANICAL_GRIPPER:
    gripper = attributes.mechanical_gripper
    data.update(
      {
        "proximal_joint": coordinate(gripper.proximal_joint),
        "jaw_range": [gripper.jaw_width_min, gripper.jaw_width_max],
        "tool_center_point": coordinate(gripper.tool_center_point),
        "body": gripper.body,
        "fingers": list(gripper.fingers),
        "pads": list(gripper.pads),
        "jaws": list(gripper.jaws),
      }
    )
  if kind == K.RESOURCE_KIND_DECK:
    data = _deck_fields(attributes, data)
  return data


def serialize_node(
  node: pb.ResourceNode,
  tree: TreeMirror,
  tip_names: Optional[TipNames] = None,
  recursive: bool = False,
) -> Dict[str, Any]:
  """What `Resource.serialize` gives for a resource in the tree.

  Args:
    node: The resource.
    tree: The tree it is in, for its parent's name and its children.
    tip_names: Names for the tips spots describe; unset names each the spot's next tip.
    recursive: Also serialize its children, under `children`, as `Resource.serialize` does.
  """
  attributes = node.attributes
  children = tree.children(node)
  data = _attributes_data(attributes, tree.parent_name(node))
  if recursive and children:
    data["children"] = [serialize_node(child, tree, tip_names, recursive) for child in children]
  items = {
    child.attributes.identifier: child.attributes.name
    for child in children
    if child.attributes.identifier
  }
  data = _kind_fields(attributes, data, items)
  if attributes.kind == K.RESOURCE_KIND_TIP_SPOT:
    prototype = pb.ResourceAttributes()
    prototype.CopyFrom(attributes.tip_spot.prototype_tip)
    prototype.name = (
      tip_names.next_name(node)
      if tip_names is not None
      else f"{attributes.name}#{node.state.tips_made}"
    )
    prototype.ClearField("location")
    data["prototype_tip"] = _kind_fields(prototype, _attributes_data(prototype, None), {})
    data.pop("children", None)
  return data


def _tracker(node: pb.ResourceNode, thing: str, max_volume: Union[float, str]) -> Dict[str, Any]:
  volume = node.state.volume
  return {
    "volume": volume.volume,
    "pending_volume": volume.pending_volume,
    "thing": thing,
    "max_volume": max_volume,
  }


def _tip_tracker(tip: pb.ResourceNode) -> Dict[str, Any]:
  return _tracker(tip, tip.attributes.name, tip.attributes.tip.maximal_volume)


def serialize_node_state(node: pb.ResourceNode, tree: TreeMirror) -> Dict[str, Any]:
  """What `Resource.serialize_state` gives for a resource in the tree."""
  attributes = node.attributes
  state: Dict[str, Any] = {"rotation": rotation(attributes.rotation)}
  if attributes.HasField("location"):
    state["location"] = coordinate(attributes.location)
  kind = attributes.kind
  if kind in CONTAINER_KINDS:
    spec = attributes.container
    max_volume = _number(spec.max_volume if spec.HasField("max_volume") else math.inf)
    state.update(_tracker(node, f"{attributes.name}_volume_tracker", max_volume))
  elif kind == K.RESOURCE_KIND_TIP:
    state.update(_tip_tracker(node))
  elif kind == K.RESOURCE_KIND_TIP_SPOT:
    tips = [child for child in tree.children(node) if child.attributes.kind == K.RESOURCE_KIND_TIP]
    tip = serialize_node(tips[0], tree) if tips else None
    state["tip"] = tip
    state["tip_state"] = _tip_tracker(tips[0]) if tips else None
    state["pending_tip"] = serialize_node(tips[0], tree) if tips else None
  elif kind == K.RESOURCE_KIND_MECHANICAL_GRIPPER:
    state["jaw_width"] = node.state.jaw_width
  return state


def drawn_children(node: pb.ResourceNode, tree: TreeMirror) -> List[pb.ResourceNode]:
  """The children the 2D page draws: all but a held tool, which it shows as its holder's state."""
  return [child for child in tree.children(node) if child.attributes.kind not in TOOL_KINDS]
