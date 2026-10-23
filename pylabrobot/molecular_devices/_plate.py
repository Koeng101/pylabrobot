"""What Molecular Devices readers read of a plate, from its resource store, in two calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.tree import to_coordinate
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb


@dataclass
class PlateGeometry:
  """A plate's size, some of its wells' attributes, and points on some of its wells.

  Attributes:
    size: The plate's size along its own axes.
    wells: The attributes of the wells asked for, by identifier.
    points: One per point asked for, in order, in the plate's frame; None where the store could
      not answer, a well without a location say.
  """

  size: Coordinate
  wells: Dict[str, pb.ResourceAttributes]
  points: List[Optional[Coordinate]]


async def read_plate(
  plate: handles.Plate,
  attributes_of: Sequence[str] = (),
  points: Sequence[Tuple[str, pb.Anchor]] = (),
) -> PlateGeometry:
  """Read a plate's size and what is asked of its wells: one `GetResources` for the plate and the
  wells in `attributes_of`, and one `ResolveGeometry` for `points`, each an identifier and an
  anchor of that well, answered in the plate's frame.

  Raises:
    IndexError: The plate has no well of an identifier asked for.
  """
  wanted = [plate.get_item(identifier) for identifier in attributes_of]
  response = await plate.store.commands.get_resources(
    spb.GetResourcesRequest(resources=[plate.ref] + [well.ref for well in wanted], depth=0)
  )
  by_id = {node.id: node.attributes for node in response.nodes}
  located: List[Optional[Coordinate]] = []
  if points:
    queries = [
      spb.GeometryQuery(
        resource=plate.get_item(identifier).ref, frame=plate.ref, anchors=[point_anchor]
      )
      for identifier, point_anchor in points
    ]
    geometry = await plate.store.commands.resolve_geometry(
      spb.ResolveGeometryRequest(queries=queries)
    )
    located = [
      None if result.HasField("issue") else to_coordinate(result.locations[0])
      for result in geometry.results
    ]
  return PlateGeometry(
    size=to_coordinate(by_id[plate.id].size),
    wells={identifier: by_id[well.id] for identifier, well in zip(attributes_of, wanted)},
    points=located,
  )
