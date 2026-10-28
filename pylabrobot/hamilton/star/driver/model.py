"""How the driver reads and writes its resource model, which a resource server holds.

The driver tells the server where its parts are (`record_positions`), asks it where things stand
(`resolve_geometry`, `locations_in`), and stages what a command will change before sending it. What
the server refuses as a tracking problem is raised here as the exception PLR raises for it.
"""

from typing import List, NoReturn, Optional, Sequence

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.hamilton.tip_creators import TipPickupMethod
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.client import ResourceServer
from pylabrobot.resources.server.errors import ServerError, plr_error
from pylabrobot.resources.server.tree import to_coordinate, to_vec3
from pylabrobot.resources.server.v1 import server_pb2 as spb
from pylabrobot.resources.server.v1 import types_pb2 as pb

# How a tip is collected, as the server states it and as the tip type table takes it.
PICKUP_METHODS = {
  pb.TIP_PICKUP_METHOD_UNSPECIFIED: TipPickupMethod.OUT_OF_RACK,
  pb.TIP_PICKUP_METHOD_OUT_OF_RACK: TipPickupMethod.OUT_OF_RACK,
  pb.TIP_PICKUP_METHOD_OUT_OF_WASH_LIQUID: TipPickupMethod.OUT_OF_WASH_LIQUID,
}


def raise_tracking_error(error: ServerError) -> NoReturn:
  """Raise a server's refusal as the exception PLR raises for it, or as it is.

  Args:
    error: what the server refused with.

  Raises:
    HasTipError, NoTipError, TooLittleLiquidError, TooLittleVolumeError: For those problems.
    ServerError: For any other.
  """
  mapped = plr_error(error)
  if mapped is error:
    raise error
  raise mapped from error


# What the server refuses to place a resource for that PLR raised as a `ValueError`: one not under
# the deck, or with no location.
PLACEMENT_PROBLEMS = frozenset({pb.PROBLEM_NOT_IN_FRAME, pb.PROBLEM_NO_LOCATION})


def placement_error(error: ServerError) -> Exception:
  """A server's refusal to say where a resource is, as the exception PLR raised for it.

  Args:
    error: what the server refused with.

  Returns:
    A `ValueError` for a resource not on the deck or with no location, carrying the server's text;
    the error itself for any other problem.
  """
  if error.problem in PLACEMENT_PROBLEMS:
    return ValueError(str(error))
  return error


def ref(resource: handles.Resource) -> pb.ResourceRef:
  return pb.ResourceRef(id=resource.id)


def position(
  resource: handles.Resource,
  x: Optional[float] = None,
  y: Optional[float] = None,
  z: Optional[float] = None,
  frame: Optional[handles.Resource] = None,
  reference_point: Optional[Coordinate] = None,
) -> spb.DevicePosition:
  """Where a part of the device is now, for `record_positions`.

  Args:
    resource: the part.
    x: its x, or None to leave it.
    y: its y, or None to leave it.
    z: its z, or None to leave it.
    frame: what the axes given are measured in; unset, they are its location in its parent.
    reference_point: the point on it the axes give, from its left front bottom corner, when a
      frame is given.
  """
  located = spb.DevicePosition(resource=ref(resource), location=pb.PartialVec3(x=x, y=y, z=z))
  if frame is not None:
    located.frame.CopyFrom(ref(frame))
    if reference_point is not None:
      located.reference_point.CopyFrom(to_vec3(reference_point))
  return located


def turned_to(
  resource: handles.Resource, z: float, pivot: Optional[Coordinate] = None
) -> spb.DevicePosition:
  """A joint turned to an angle about z, about a pivot in its own frame, for `record_positions`.

  Args:
    resource: the part the joint turns.
    z: its angle in its parent, in degrees.
    pivot: what it turns about, in its own frame; its origin when None.
  """
  change = pb.RotationChange(to=pb.PartialRotation(z=z))
  if pivot is not None:
    change.pivot.CopyFrom(to_vec3(pivot))
  return spb.DevicePosition(resource=ref(resource), rotation=change)


def jaws_at(gripper: handles.Resource, width: float) -> spb.DevicePosition:
  """A gripper's jaws standing `width` apart, for `record_positions`."""
  return spb.DevicePosition(resource=ref(gripper), jaw_width=width)


async def record_positions(server: ResourceServer, positions: Sequence[spb.DevicePosition]) -> None:
  """Tell the server where the parts of one move are now, all in one call."""
  if not positions:
    return
  await server.commands.record_device_positions(
    spb.RecordDevicePositionsRequest(positions=positions)
  )


def query(
  resource: handles.Resource,
  frame: Optional[handles.Resource] = None,
  anchors: Sequence[pb.Anchor] = (),
) -> spb.GeometryQuery:
  """One question for `resolve_geometry`: where `resource` is, at each anchor, in `frame`."""
  asked = spb.GeometryQuery(resource=ref(resource), anchors=anchors)
  if frame is not None:
    asked.frame.CopyFrom(ref(frame))
  return asked


async def resolve_geometry(
  server: ResourceServer, queries: Sequence[spb.GeometryQuery]
) -> List[spb.Geometry]:
  """Answer every query in one call.

  Raises:
    ServerError: A query could not be answered.
  """
  if not queries:
    return []
  response = await server.commands.resolve_geometry(spb.ResolveGeometryRequest(queries=queries))
  for answer in response.results:
    if answer.HasField("issue"):
      raise ServerError(answer.issue.problem, answer.issue.message)
  return list(response.results)


async def locations_in(
  resources: Sequence[handles.Resource],
  frame: handles.Resource,
  x: str = "l",
  y: str = "f",
  z: str = "b",
) -> List[Coordinate]:
  """Where a point of each resource is, along `frame`'s axes, in one call.

  Args:
    resources: what to locate, all in one server.
    frame: what the points are measured from.
    x: the point across each, as `handles.anchor` names it.
    y: the point along each.
    z: the point up each.
  """
  if not resources:
    return []
  point = handles.anchor(x, y, z)
  answers = await resolve_geometry(
    frame.server, [query(resource, frame, [point]) for resource in resources]
  )
  return [to_coordinate(answer.locations[0]) for answer in answers]


async def get_nodes(
  server: ResourceServer, resources: Sequence[handles.Resource], depth: int = 0
) -> List[pb.ResourceNode]:
  """What the server holds of each resource, and of what is under it to `depth`, in one call."""
  if not resources:
    return []
  response = await server.commands.get_resources(
    spb.GetResourcesRequest(resources=[ref(r) for r in resources], depth=depth)
  )
  return list(response.nodes)


async def arm_location(server: ResourceServer, arm: handles.Resource) -> Coordinate:
  """Where an X-arm stands on the deck it hangs from, along the deck's axes.

  Read off the arm's own location rather than resolved as geometry: the arm is the deck's child,
  so the two are the same point, and resolving it would walk everything the arm carries.

  Raises:
    ServerError: The arm has no location.
  """
  (node,) = await get_nodes(server, [arm])
  location = location_of(node)
  if location is None:
    raise ServerError(pb.PROBLEM_NO_LOCATION, f"'{arm.name}' has no location", arm.name)
  return location


def location_of(node: pb.ResourceNode) -> Optional[Coordinate]:
  """A node's location in its parent, or None when it has none."""
  attributes = node.attributes
  return to_coordinate(attributes.location) if attributes.HasField("location") else None
