"""Flatten any resource tree into prototypes and instances.

A resource is split into its model (what it is, shared by every resource that serializes the
same way, sent once) and its instance (a name, a parent, six floats). The split is derived from
the resource's serialization - what `Resource.serialize()` gives, built from what the store holds
of it - by removing the fields that vary per instance, so no resource type is known here.
"""

import base64
import functools
import inspect
import json
import struct
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from pylabrobot.resources.store import handles
from pylabrobot.resources.store.tree import to_coordinate, to_rotation
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.visualizer.mirror import TreeMirror
from pylabrobot.visualizer.nodes import serialize_node, serialize_node_state

from .grids import describe_bands, describe_grid, metadata_of

# Fields of a serialized resource that describe this one resource rather than its kind. Everything
# else is shared by every resource that serializes the same way, and so belongs to the model.
INSTANCE_FIELDS = frozenset({"name", "location", "rotation", "parent_name", "children"})

# Keys that name one particular thing at any depth: a tip spot carries its prototype tip's name,
# a plate the names of its wells. Links, not kind.
NAME_KEYS = frozenset({"name", "parent_name"})

# Fields a resource may declare about itself that its serialization does not carry, read from
# its metadata.
DECLARED_FIELDS = ("reference_point", "window", "mesh", "reference_glb", "appearance")
RESOURCE_LINK = "<resource>"


def declared_fields(node: pb.ResourceNode) -> Dict[str, Any]:
  """The fields a resource declares about itself in its metadata, by name."""
  metadata = metadata_of(node)
  return {field: metadata[field] for field in DECLARED_FIELDS if metadata.get(field) is not None}


def _model_of(data: Dict[str, Any], names: FrozenSet[str]) -> Dict[str, Any]:
  """The kind-defining part of a serialized resource, with every identity removed.

  Inside nested values a `NAME_KEYS` key is dropped and a string naming a resource in `names`
  becomes `RESOURCE_LINK`. Top-level scalars are kept as they are: a category may read the same
  as a resource's name (a deck called "deck") without referring to it.
  """

  def strip(value: Any) -> Any:
    if isinstance(value, dict):
      return {k: strip(v) for k, v in value.items() if k not in NAME_KEYS}
    if isinstance(value, list):
      return [strip(v) for v in value]
    if isinstance(value, str) and value in names:
      return RESOURCE_LINK
    return value

  return {
    k: (v if not isinstance(v, (dict, list)) else strip(v))
    for k, v in data.items()
    if k not in INSTANCE_FIELDS
  }


@functools.lru_cache(maxsize=None)
def _public_methods(cls: type) -> Tuple[str, ...]:
  """The public operations of a resource class as signatures, sorted, cached per class."""
  signatures = []
  for name in dir(cls):
    if name.startswith("_"):
      continue
    try:
      attribute = getattr(cls, name, None)
    except Exception:
      continue
    if attribute is None or not callable(attribute) or isinstance(attribute, property):
      continue
    try:
      parameters = [p for p in inspect.signature(attribute).parameters if p != "self"]
      signatures.append(f"{name}({', '.join(parameters)})")
    except (ValueError, TypeError):
      signatures.append(f"{name}()")
  return tuple(sorted(signatures))


def _model_class(model: Dict[str, Any]) -> str:
  """The bucket a model is compared within. Two resources of different types are never the same."""
  return str(model.get("type", ""))


def _location_of(data: Dict[str, Any]) -> Tuple[float, float, float]:
  loc = data.get("location") or {}
  return (float(loc.get("x", 0.0)), float(loc.get("y", 0.0)), float(loc.get("z", 0.0)))


def _rotation_of(data: Dict[str, Any]) -> Tuple[float, float, float]:
  rot = data.get("rotation") or {}
  return (float(rot.get("x", 0.0)), float(rot.get("y", 0.0)), float(rot.get("z", 0.0)))


class Scene:
  """A flattened resource tree: models, instances, and the measurements of the split."""

  def __init__(self, names: Optional[FrozenSet[str]] = None) -> None:
    self.names_in_tree = names or frozenset()
    # Every model derived this pass, by resource name, so the next pass can skip the work.
    self.derived: Dict[str, Dict[str, Any]] = {}
    self.models: List[Dict[str, Any]] = []
    # Candidate model indices per serialized type: interning compares dicts directly, and a tree
    # has only a handful of distinct models per type, so the scan is short.
    self._candidates: Dict[str, List[int]] = {}
    self.names: List[str] = []
    self.model_of_instance: List[int] = []
    self.parent_of_instance: List[int] = []
    self.transforms: List[float] = []  # 6 floats per instance: x, y, z, rx, ry, rz
    self.legacy_bytes = 0

  def _intern(self, model: Dict[str, Any]) -> int:
    bucket = self._candidates.setdefault(_model_class(model), [])
    for index in bucket:
      if self.models[index] == model:
        return index
    index = len(self.models)
    self.models.append(model)
    bucket.append(index)
    return index

  def add_known(self, node: pb.ResourceNode, parent: int, model: Dict[str, Any]) -> int:
    """Add a resource whose model is already known, without serializing it again.

    Its position is read off its node.
    """
    index = len(self.names)
    name = node.attributes.name
    self.names.append(name)
    model_index = self._intern(model)
    self.model_of_instance.append(model_index)
    self.derived[name] = self.models[model_index]
    self.parent_of_instance.append(parent)
    self.transforms.extend(local_transform(node))
    return index

  def add(
    self,
    data: Dict[str, Any],
    parent: int,
    cls: Optional[type] = None,
    grid: Optional[Dict[str, Any]] = None,
    bands: Optional[List[Dict[str, Any]]] = None,
    declared: Optional[Dict[str, Any]] = None,
  ) -> int:
    """Add one serialized resource, returning its instance index."""
    index = len(self.names)
    resource_name = data["name"]
    self.names.append(resource_name)
    model = _model_of(data, self.names_in_tree)
    if cls is not None:
      model["methods"] = list(_public_methods(cls))
    if grid is not None:
      model["grid"] = grid
    if bands is not None:
      model["bands"] = bands
    for field, value in (declared or {}).items():
      model[field] = value
    # The interned dict, so every instance of one model shares one object.
    model_index = self._intern(model)
    self.model_of_instance.append(model_index)
    self.derived[resource_name] = self.models[model_index]
    self.parent_of_instance.append(parent)
    self.transforms.extend(_location_of(data))
    self.transforms.extend(_rotation_of(data))
    return index

  @property
  def num_instances(self) -> int:
    return len(self.names)

  def serialize(self) -> Dict[str, Any]:
    """The scene message. Transforms ride as base64 little-endian float32, not as JSON numbers."""
    packed = struct.pack(f"<{len(self.transforms)}f", *self.transforms)
    return {
      "models": self.models,
      "instances": {
        "names": self.names,
        "model": self.model_of_instance,
        "parent": self.parent_of_instance,
        "transforms": base64.b64encode(packed).decode("ascii"),
      },
    }

  def stats(self, scene_bytes: int) -> Dict[str, Any]:
    """What the split cost and what it saved, in bytes actually sent."""
    return {
      "instances": self.num_instances,
      "models": len(self.models),
      "legacy_bytes": self.legacy_bytes,
      "scene_bytes": scene_bytes,
      "ratio": round(self.legacy_bytes / scene_bytes, 2) if scene_bytes else 0.0,
    }


def local_transform(node: pb.ResourceNode) -> List[float]:
  """Where a resource is in its parent and how it is turned there: x, y, z, rx, ry, rz, as its
  `Coordinate` and `Rotation` hold them."""
  attributes = node.attributes
  location = to_coordinate(attributes.location)
  rotation = to_rotation(attributes.rotation)
  return [
    float(location.x),
    float(location.y),
    float(location.z),
    float(rotation.x),
    float(rotation.y),
    float(rotation.z),
  ]


def legacy_size(tree: TreeMirror) -> int:
  """The size of the tree serialized as one JSON node per resource, every child listed."""

  def one_node(node: pb.ResourceNode) -> Dict[str, Any]:
    data = serialize_node(node, tree)
    data["children"] = [one_node(child) for child in tree.children(node)]
    return data

  return len(json.dumps(one_node(tree.node(tree.root_id))))


def _links_to(model: Dict[str, Any], names: FrozenSet[str]) -> bool:
  """Whether a nested value of `model` is a link, or a string naming one of `names`."""

  def found(value: Any) -> bool:
    if isinstance(value, dict):
      return any(found(v) for v in value.values())
    if isinstance(value, list):
      return any(found(v) for v in value)
    return isinstance(value, str) and (value == RESOURCE_LINK or value in names)

  return any(found(v) for v in model.values() if isinstance(v, (dict, list)))


def build_scene(
  tree: TreeMirror,
  measure_legacy: bool = False,
  known: Optional[Dict[str, Dict[str, Any]]] = None,
  known_names: Optional[FrozenSet[str]] = None,
) -> Scene:
  """Flatten the tree into models and instances.

  Depth-first, parents before children, so world transforms resolve in one forward pass.

  Args:
    tree: the tree to flatten, from its root.
    measure_legacy: also measure the per-resource tree, for `Scene.legacy_bytes`.
    known: models derived by an earlier pass, by resource name, reused unless stale.
    known_names: the names that pass saw; a model that links to, or names, a resource that has
      since appeared or gone is derived again.
  """
  names = frozenset(tree.names())
  scene = Scene(names=names)
  changed = names ^ (known_names or frozenset())
  models = {id(model): model for model in (known or {}).values()}
  stale = {i for i, model in models.items() if changed and _links_to(model, changed)}
  reuse = {name: model for name, model in (known or {}).items() if id(model) not in stale}

  def walk(node: pb.ResourceNode, parent: int) -> None:
    model = reuse.get(node.attributes.name)
    if model is not None:
      index = scene.add_known(node, parent, model)
    else:
      data = serialize_node(node, tree)
      index = scene.add(
        data,
        parent,
        handles.HANDLE_TYPES[node.attributes.kind],
        describe_grid(node, tree),
        describe_bands(node),
        declared_fields(node),
      )
    for child in tree.children(node):
      walk(child, index)

  walk(tree.node(tree.root_id), -1)
  if measure_legacy:
    scene.legacy_bytes = legacy_size(tree)
  return scene


# A rotation nobody has turned. It is published by every resource that publishes anything at all,
# and on a scene of mostly unrotated geometry it is the single largest repeated value.
IDENTITY_ROTATION = {"type": "Rotation", "x": 0, "y": 0, "z": 0}

# Fields that say which resource a state came from, not what it is: the key already says. A tip
# names the spot it stands in, so without `parent_name` here every full spot's state was distinct.
STATE_IDENTITY_KEYS = frozenset({"name", "thing", "parent_name"})


def _without_identity(value: Any) -> Any:
  """A state value with the fields that name one instance taken out, at any depth."""
  if isinstance(value, dict):
    return {k: _without_identity(v) for k, v in value.items() if k not in STATE_IDENTITY_KEYS}
  if isinstance(value, list):
    return [_without_identity(v) for v in value]
  return value


# What a viewer can see: firmware reports position to 0.1 mm. Rounding rather than thresholding
# makes two values that look the same produce one signature and share one table entry.
STATE_DECIMALS = 1


def _visible(value: Any) -> Any:
  """A state value with changes too small to see rounded away."""
  if isinstance(value, float):
    return round(value, STATE_DECIMALS)
  if isinstance(value, dict):
    return {k: _visible(v) for k, v in value.items()}
  if isinstance(value, list):
    return [_visible(v) for v in value]
  return value


def state_signature(published: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
  """The publishable form of one resource's state, and a key that is equal when it looks equal.

  The key leaves out `location`; the cleaned state keeps it as published.
  """
  cleaned = _visible(
    _without_identity(
      {
        k: v
        for k, v in published.items()
        if k != "location" and not (k == "rotation" and v == IDENTITY_ROTATION)
      }
    )
  )
  key = json.dumps(cleaned, sort_keys=True, default=str)
  if "location" in published:
    cleaned["location"] = published["location"]
  return cleaned, key


def pack_state(states: Dict[str, Tuple[Dict[str, Any], str]], epoch: int = 0) -> Dict[str, Any]:
  """Pack `{name: (cleaned state, key)}` into a table of distinct states plus an index per name.

  Every name that went in comes out, including one whose state cleaned down to nothing. A
  `location` travels under the name in `locations`, not in the shared table.
  """
  distinct: Dict[str, int] = {}
  table: List[Dict[str, Any]] = []
  index: Dict[str, int] = {}
  locations: Dict[str, Any] = {}

  for name, (cleaned, key) in states.items():
    if "location" in cleaned:
      locations[name] = cleaned["location"]
      cleaned = {k: v for k, v in cleaned.items() if k != "location"}
    if key not in distinct:
      distinct[key] = len(table)
      table.append(cleaned)
    index[name] = distinct[key]

  # Addressed by name: instance order is not stable across rebuilds, since setup creates resources
  # lazily and a reassignment reorders a parent's children.
  return {"epoch": epoch, "states": table, "of": index, "locations": locations}


def collect_state(tree: TreeMirror) -> Dict[str, Tuple[Dict[str, Any], str]]:
  """The cleaned state and key of every resource that publishes any, keyed by name.

  A resource whose state cleans down to nothing is left out; a rotation that is not the identity
  counts.
  """
  state: Dict[str, Tuple[Dict[str, Any], str]] = {}
  for node in tree.walk():
    cleaned, key = state_signature(serialize_node_state(node, tree))
    if cleaned:
      state[node.attributes.name] = (cleaned, key)
  return state
