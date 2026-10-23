"""The space a site's automation stands in, as a definition a resource store creates.

Its frame is what everything in it resolves against; the tree is the only structure above a
device.
"""

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build
from pylabrobot.resources.store.v1 import types_pb2 as pb


def facility(
  name: str = "facility",
  size_x: float = 10_000.0,
  size_y: float = 10_000.0,
  size_z: float = 3_000.0,
) -> pb.ResourceDefinition:
  """The space a site's automation stands in, and the frame everything in it resolves against.

  Its children are whatever is on the floor: a device, a shuttle between devices, a bench that is
  not automated at all. Create it with `store.create(facility(...), name=...)`.

  Args:
    name: what to call this facility.
    size_x: how wide the space is, in mm.
    size_y: how deep it is, in mm.
    size_z: how tall it is, in mm.
  """
  # A facility is the frame everything else resolves against, so it sits at its own origin.
  return build.resource(
    name,
    Coordinate(size_x, size_y, size_z),
    location=Coordinate.zero(),
    category="facility",
    type_name="Facility",
  )
