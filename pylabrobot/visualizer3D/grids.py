"""Repeated position grids a resource lays things out on, described as data.

A grid is where the first position is, how far apart they are, how many there are and how they
are labelled. It is read off the resource where it declares one in its metadata, and derived from
a Hamilton deck's tracks otherwise.
"""

import logging
from typing import Any, Dict, List, Optional

from google.protobuf import json_format

from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.utils.linalg import matrix_vector_multiply_3x3
from pylabrobot.visualizer.mirror import TreeMirror

logger = logging.getLogger(__name__)

# How close a child's own y has to be to the rail line to count as standing on it, in mm.
SEATED_TOLERANCE = 0.5

# How often a rail gets a number. Legacy labels the first and then every fifth, which is dense
# enough to count from and sparse enough to read.
DEFAULT_LABEL_EVERY = 5


def metadata_of(node: pb.ResourceNode) -> Dict[str, Any]:
  """A resource's metadata as JSON."""
  if not node.attributes.metadata.fields:
    return {}
  return json_format.MessageToDict(node.attributes.metadata)


def absolute_rotation(node: pb.ResourceNode, tree: TreeMirror) -> Rotation:
  """How a resource is turned along its root's axes: its ancestors' rotations, then its own."""
  chain = [node]
  while chain[-1].parent_id in tree.nodes:
    chain.append(tree.nodes[chain[-1].parent_id])
  turned = Rotation()
  for each in reversed(chain):
    angles = each.attributes.rotation
    turned = turned + Rotation(x=angles.x, y=angles.y, z=angles.z)
  return turned


def absolute_size_y(node: pb.ResourceNode, tree: TreeMirror) -> float:
  """The depth of a resource's box once turned, along its root's axes."""
  size = node.attributes.size
  turned = absolute_rotation(node, tree)
  if (turned.x, turned.y, turned.z) == (0, 0, 0):
    return size.y
  matrix = turned.get_rotation_matrix()
  ys = [
    matrix_vector_multiply_3x3(matrix, [x, y, z])[1]
    for x in (0, size.x)
    for y in (0, size.y)
    for z in (0, size.z)
  ]
  return float(max(ys) - min(ys))


def describe_bands(node: pb.ResourceNode) -> Optional[List[Dict[str, Any]]]:
  """The `access_bands` a resource declares in its metadata, or None.

  Each band is `{"label": str, "from": float, "to": float}` in the resource's own frame, with
  optional `x_from` and `x_to` bounding it along the other axis. A malformed band is logged and
  skipped.
  """
  bands = metadata_of(node).get("access_bands")
  if not bands or not isinstance(bands, list):
    return None
  described: List[Dict[str, Any]] = []
  for band in bands:
    try:
      described.append(
        {
          "label": str(band["label"]),
          "from": float(band["from"]),
          "to": float(band["to"]),
          # Optional: how far the band runs along the other axis. Absent means the whole resource.
          **({"x_from": float(band["x_from"])} if "x_from" in band else {}),
          **({"x_to": float(band["x_to"])} if "x_to" in band else {}),
        }
      )
    except (KeyError, TypeError, ValueError):
      logger.warning("ignoring malformed access band on %s: %r", node.attributes.name, band)
  return described or None


def describe_grid(node: pb.ResourceNode, tree: TreeMirror) -> Optional[Dict[str, Any]]:
  """The repeated grid this resource lays positions on, or None if it lays none.

  A `position_grid` declared in its metadata is returned as is; otherwise a Hamilton deck's grid
  is derived from its tracks.

  Returns:
    A dict in the resource's own frame: `axis`, which way the grid runs; `count`; `spacing` in mm;
    `origin`, the first position as [x, y, z] in mm; `extent`, how far a mark runs across the
    resource in mm; `label_every`, label the first and then every nth; `label`, what one
    position is called.
  """
  # A resource may state its grid, as it states its access bands: a loading tray's markings line
  # up with the deck it feeds, so nothing about itself could derive them.
  declared = metadata_of(node).get("position_grid")
  if isinstance(declared, dict) and declared:
    return dict(declared)

  deck = node.attributes.deck
  if not deck.HasField("hamilton"):
    return None
  tracks = deck.hamilton
  count = tracks.num_tracks
  spacing = tracks.track_pitch
  if count < 2 or spacing <= 0:
    return None
  first = tracks.track_origin

  # A mark runs to the back of what the positions carry, not of the resource: the deepest child
  # seated on the line (sharing its y), or the resource's own depth when nothing stands on it.
  depth = absolute_size_y(node, tree)
  seated: List[float] = []
  for child in tree.children(node):
    location = child.attributes.location
    if not child.attributes.HasField("location") or abs(location.y - first.y) > SEATED_TOLERANCE:
      continue
    seated.append(absolute_size_y(child, tree))

  return {
    "axis": "x",
    "count": count,
    "spacing": round(spacing, 4),
    "origin": [round(first.x, 4), round(first.y, 4), round(first.z, 4)],
    "extent": round(max(seated) if seated else max(depth - first.y, 0.0), 4),
    "label_every": DEFAULT_LABEL_EVERY,
    "label": "track",
  }
