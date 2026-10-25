"""What the Prep driver reads of its resources from a resource store, and how it reports back.

Every read here is one or two calls to the store, answering for every resource a command names at
once; the driver plans from the facts it gets back and passes them down, rather than asking again.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from pylabrobot.lib.liquid_handling.channel_positioning import ChannelFootprint
from pylabrobot.lib.liquid_handling.pipette_batch_scheduling import ChannelTarget
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import NoTipError
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError, plr_error
from pylabrobot.resources.store.tree import to_coordinate, to_rotation, to_vec3
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

from . import prep_commands as PrepCmd

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
TOOL_KINDS = frozenset({K.RESOURCE_KIND_TIP, K.RESOURCE_KIND_HEAD_TOOL})


def ref(resource_id: bytes) -> pb.ResourceRef:
  """A resource by its id."""
  return pb.ResourceRef(id=resource_id)


def store_problem(error: StoreError) -> Exception:
  """The exception the driver raises for a store's refusal of what it was asked to stage.

  A tracking problem is raised as PLR's own error for it; a destination that does not take what
  is placed there as a `RuntimeError`, as a resource holder refuses it; anything else as a
  `ValueError`.
  """
  if error.problem == pb.PROBLEM_CANNOT_DROP_HERE:
    return RuntimeError(str(error))
  return plr_error(error, otherwise=ValueError)


async def get_nodes(
  store: ResourceStore,
  refs: Sequence[pb.ResourceRef],
  depth: int = 0,
  ancestors: bool = False,
) -> List[pb.ResourceNode]:
  """Resources as the store holds them now, in one read: each, `depth` below it, and its ancestors
  when asked. A resource reached twice is answered once."""
  if not refs:
    return []
  response = await store.commands.get_resources(
    spb.GetResourcesRequest(resources=refs, depth=depth, ancestors=ancestors)
  )
  return list(response.nodes)


# -- tools ---------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ToolFacts:
  """A tip, or a tool such as a CO-RE grip paddle, as the driver plans with it.

  Attributes:
    id: its id in the store; empty for a tip a spot has not made yet.
    name: its name.
    kind: a tip or a head tool.
    size: its size along its own axes, in mm.
    fitting_depth: how far a shaft goes into it, in mm.
    collar: where it rests on a spot, above its pick-up point, in mm; None when it states none.
    maximal_volume: what it holds at most, in uL.
    nominal_volume: what it is sold to hold, in uL.
    has_filter: whether it carries a filter.
    tip_size: a Hamilton tip's size, by name; empty for anything else.
    model: the model it is made from; empty when it states none.
    volume: what it holds, counting what is staged, in uL.
    tracks_volume: whether its volume is tracked.
  """

  id: bytes
  name: str
  kind: int
  size: Coordinate
  fitting_depth: float
  collar: Optional[float]
  maximal_volume: float
  nominal_volume: float
  has_filter: bool
  tip_size: str
  model: str = ""
  volume: float = 0.0
  tracks_volume: bool = False

  @property
  def is_tip(self) -> bool:
    return self.kind == K.RESOURCE_KIND_TIP

  @property
  def has_collar_height(self) -> bool:
    return self.collar is not None

  @property
  def collar_height(self) -> float:
    """Where it rests on a spot, above its pick-up point, in mm.

    Raises:
      ValueError: If it states none.
    """
    if self.collar is None:
      raise ValueError(f"collar_height is not defined for this tip: {self.name}")
    return self.collar

  @property
  def length(self) -> float:
    """How far it reaches below the shaft carrying it, in mm."""
    return self.size.z - self.fitting_depth

  @property
  def free_volume(self) -> float:
    """How much more it takes, in uL."""
    return self.maximal_volume - self.volume

  @classmethod
  def from_attributes(
    cls,
    attributes: pb.ResourceAttributes,
    resource_id: bytes = b"",
    state: Optional[pb.ResourceState] = None,
  ) -> ToolFacts:
    """A tip or tool from what the store says it is, and its state when it has one."""
    tip = attributes.tip
    volume = state.volume if state is not None and state.HasField("volume") else None
    return cls(
      id=resource_id,
      name=attributes.name,
      kind=attributes.kind,
      size=to_coordinate(attributes.size),
      fitting_depth=attributes.head_tool.fitting_depth,
      collar=tip.collar_height if tip.HasField("collar_height") else None,
      maximal_volume=tip.maximal_volume,
      nominal_volume=tip.nominal_volume,
      has_filter=tip.has_filter,
      tip_size=tip.hamilton.tip_size if tip.HasField("hamilton") else "",
      model=attributes.model,
      volume=0.0 if volume is None else volume.pending_volume,
      tracks_volume=volume is not None and volume.tracking_enabled,
    )

  @classmethod
  def from_node(cls, node: pb.ResourceNode) -> ToolFacts:
    return cls.from_attributes(node.attributes, node.id, node.state)


def tool_length(tool: Optional[ToolFacts]) -> float:
  """How far below the end of a shaft what it carries reaches, in mm.

  The device reports and takes Z there: at a tip's bottom, at the gripper tools' jaws (the length
  they were picked up with), and at the shaft's end when nothing is on it.
  """
  if tool is None:
    return 0.0
  if tool.is_tip:
    return float(tool.length)
  return float(PrepCmd.CO_RE_GRIPPER_TIP_PICKUP_PARAMETERS.length)


def tool_on(node: pb.ResourceNode, by_id: Dict[bytes, pb.ResourceNode]) -> Optional[ToolFacts]:
  """The tip or tool a shaft or spot holds, among nodes read with it; None when it holds none."""
  for child_id in node.child_ids:
    child = by_id.get(child_id)
    if child is not None and child.attributes.kind in TOOL_KINDS:
      return ToolFacts.from_node(child)
  return None


# -- where resources are -------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Placed:
  """Where a resource is, along the deck's axes, from the deck's left front bottom corner.

  Attributes:
    id: its id.
    origin: its left front bottom corner.
    bottom: the centre of its bottom.
    cavity_bottom: the centre of a container's inside floor; its bottom for anything else.
    top: the centre of its top.
    center: its centre.
    size: its size along its own axes.
    absolute_size: its box's size once turned, along the root's axes.
    rotation: how it is turned along the deck's axes.
  """

  id: bytes
  origin: Coordinate
  bottom: Coordinate
  cavity_bottom: Coordinate
  top: Coordinate
  center: Coordinate
  size: Coordinate
  absolute_size: Coordinate
  rotation: Rotation


_ANCHORS = [
  pb.Anchor(x=pb.ANCHOR_X_LEFT, y=pb.ANCHOR_Y_FRONT, z=pb.ANCHOR_Z_BOTTOM),
  pb.Anchor(x=pb.ANCHOR_X_CENTER, y=pb.ANCHOR_Y_CENTER, z=pb.ANCHOR_Z_BOTTOM),
  pb.Anchor(x=pb.ANCHOR_X_CENTER, y=pb.ANCHOR_Y_CENTER, z=pb.ANCHOR_Z_TOP),
  pb.Anchor(x=pb.ANCHOR_X_CENTER, y=pb.ANCHOR_Y_CENTER, z=pb.ANCHOR_Z_CENTER),
]
_CAVITY_BOTTOM = pb.Anchor(x=pb.ANCHOR_X_CENTER, y=pb.ANCHOR_Y_CENTER, z=pb.ANCHOR_Z_CAVITY_BOTTOM)


async def locate(
  store: ResourceStore,
  frame: Optional[pb.ResourceRef],
  ids: Sequence[bytes],
  cavity: Iterable[bytes] = (),
) -> Dict[bytes, Placed]:
  """Where each resource is in `frame`, in one read.

  Args:
    store: the store.
    frame: what the locations are along, from its left front bottom corner: the deck. None
      answers them absolute, along the axes the root is turned in.
    ids: the resources.
    cavity: those among them whose cavity bottom is asked for: containers that state their
      material thickness. Every other resource's is its bottom.

  Raises:
    ValueError: If a resource is not in the frame's tree.
  """
  wanted = list(dict.fromkeys(ids))
  if not wanted:
    return {}
  with_cavity = set(cavity)
  queries = [
    spb.GeometryQuery(
      resource=ref(i), anchors=_ANCHORS + ([_CAVITY_BOTTOM] if i in with_cavity else [])
    )
    for i in wanted
  ]
  if frame is not None:
    for query in queries:
      query.frame.CopyFrom(frame)
  response = await store.commands.resolve_geometry(spb.ResolveGeometryRequest(queries=queries))
  placed: Dict[bytes, Placed] = {}
  for resource_id, geometry in zip(wanted, response.results):
    if geometry.HasField("issue"):
      raise ValueError(geometry.issue.message)
    origin, bottom, top, center = (to_coordinate(v) for v in geometry.locations[:4])
    cavity_bottom = to_coordinate(geometry.locations[4]) if len(geometry.locations) > 4 else bottom
    placed[resource_id] = Placed(
      id=resource_id,
      origin=origin,
      bottom=bottom,
      cavity_bottom=cavity_bottom,
      top=top,
      center=center,
      size=to_coordinate(geometry.size),
      absolute_size=to_coordinate(geometry.absolute_size),
      rotation=to_rotation(geometry.rotation_in_frame),
    )
  return placed


def footprint(name: str, placed: Placed, no_go_zones: Sequence[pb.Box] = ()) -> ChannelFootprint:
  """What placing channels in a resource needs to know of it, as `footprint_of` reads it."""
  center = Coordinate(placed.size.x / 2, placed.size.y / 2, placed.size.z / 2)
  return ChannelFootprint(
    name=name,
    size_y=placed.size.y,
    absolute_size_y=placed.absolute_size.y,
    center_y=center.rotated(placed.rotation).y,
    no_go_zones=tuple((to_coordinate(zone.min), to_coordinate(zone.max)) for zone in no_go_zones),
  )


# -- containers ----------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ContainerFacts:
  """A container as a liquid command plans with it.

  Attributes:
    id: its id.
    name: its name.
    kind: what it is: a well, a trough, a tube, a trash.
    parent_name: what holds it, a plate say; its own name when nothing does.
    placed: where it is on the deck.
    spec: its height-volume data, material thickness, no-go zones and shape.
    volume: what it holds, counting what is staged, in uL.
    tracks_volume: whether its volume is tracked.
  """

  id: bytes
  name: str
  kind: int
  parent_name: str
  placed: Placed
  spec: pb.ContainerSpec
  volume: float
  tracks_volume: bool

  @property
  def ref(self) -> pb.ResourceRef:
    return ref(self.id)

  @property
  def is_well(self) -> bool:
    return self.kind == K.RESOURCE_KIND_WELL

  @property
  def max_volume(self) -> float:
    return self.spec.max_volume if self.spec.HasField("max_volume") else math.inf

  @property
  def free_volume(self) -> float:
    """How much more it takes, in uL."""
    return self.max_volume - self.volume

  @property
  def material_z_thickness(self) -> Optional[float]:
    return self.spec.material_z_thickness if self.spec.HasField("material_z_thickness") else None

  @property
  def cavity_bottom(self) -> Coordinate:
    """The centre of its inside floor, on the deck.

    Raises:
      NotImplementedError: If it states no material thickness, so its floor is not known.
    """
    if self.material_z_thickness is None:
      raise NotImplementedError(
        f"The current operation is not supported for resource named '{self.name}' because "
        "material_z_thickness is not defined."
      )
    return self.placed.cavity_bottom

  @property
  def height_volume_data(self) -> List[Tuple[float, float]]:
    """Its liquid heights and the volumes they hold, lowest first."""
    return sorted((point.height, point.volume) for point in self.spec.height_volume_data)

  @property
  def converts_height_and_volume(self) -> bool:
    """Whether its volume and liquid height convert into one another."""
    return len(self.spec.height_volume_data) >= 2

  def footprint(self) -> ChannelFootprint:
    return footprint(self.name, self.placed, self.spec.no_go_zones)

  def target(self) -> ChannelTarget:
    """What the batch planner needs of it."""
    return ChannelTarget(key=self.id, footprint=self.footprint(), center=self.placed.bottom)


async def read_containers(
  store: ResourceStore, deck: pb.ResourceRef, containers: Sequence[handles.Resource]
) -> List[ContainerFacts]:
  """Each container's facts, in the order given, in two reads of the store.

  Raises:
    ValueError: If one is not a container, or is not on the deck.
  """
  unique = list(dict.fromkeys(c.id for c in containers))
  nodes = await get_nodes(store, [ref(i) for i in unique], ancestors=True)
  by_id = {node.id: node for node in nodes}
  for container in containers:
    if by_id[container.id].attributes.kind not in CONTAINER_KINDS:
      raise ValueError(f"'{container.name}' holds no liquid")
  cavity = [i for i in unique if by_id[i].attributes.container.HasField("material_z_thickness")]
  placed = await locate(store, deck, unique, cavity)
  facts: Dict[bytes, ContainerFacts] = {}
  for i in unique:
    node = by_id[i]
    parent = by_id.get(node.parent_id)
    volume = node.state.volume
    facts[i] = ContainerFacts(
      id=i,
      name=node.attributes.name,
      kind=node.attributes.kind,
      parent_name=node.attributes.name if parent is None else parent.attributes.name,
      placed=placed[i],
      spec=node.attributes.container,
      volume=volume.pending_volume,
      tracks_volume=node.state.HasField("volume") and volume.tracking_enabled,
    )
  return [facts[c.id] for c in containers]


async def heights_from_volumes(
  store: ResourceStore, asked: Sequence[Tuple[ContainerFacts, float]]
) -> List[float]:
  """How high each volume stands in its container, in mm above its cavity bottom, rounded to
  0.01 mm as `get_liquid_height_from_volume` rounds it; 0.0 for nothing. One read of the store.

  Raises:
    RuntimeError: If a container that holds something has no height-volume data.
    ValueError: If a volume lies outside a container's data.
  """
  queries = []
  for container, volume in asked:
    if volume <= 0:
      continue
    if not container.converts_height_and_volume:
      raise RuntimeError(
        f"where {volume} uL stands in {container.name} is not known: the container has no "
        "height-volume functions. Generate a height_volume_data dictionary for it and consider "
        "contributing it back to PyLabRobot :)"
      )
    queries.append(spb.HeightVolumeQuery(container=container.ref, volume=volume))
  results: Iterator[spb.HeightVolumeResult] = iter([])
  if queries:
    response = await store.commands.convert_height_volume(
      spb.ConvertHeightVolumeRequest(queries=queries)
    )
    results = iter(response.results)
  heights = []
  for _, volume in asked:
    if volume <= 0:
      heights.append(0.0)
      continue
    result = next(results)
    if result.HasField("issue"):
      raise ValueError(result.issue.message)
    heights.append(round(result.height, 2))
  return heights


async def volumes_from_heights(
  store: ResourceStore, asked: Sequence[Tuple[ContainerFacts, float]]
) -> List[Optional[float]]:
  """The volume each liquid height above its container's cavity bottom holds, in uL; None where
  the height lies outside the container's data. One read of the store."""
  if not asked:
    return []
  response = await store.commands.convert_height_volume(
    spb.ConvertHeightVolumeRequest(
      queries=[spb.HeightVolumeQuery(container=c.ref, height=h) for c, h in asked]
    )
  )
  return [None if r.HasField("issue") else r.volume for r in response.results]


# -- tip spots -----------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class SpotFacts:
  """A tip spot as a tip command plans with it.

  Attributes:
    id: its id.
    name: its name.
    placed: where it is on the deck.
    tracks_tips: whether it gives up and takes back tips; one that does not hands out fresh ones.
    tip: the tip it holds; None when it holds none.
    prototype: the tip it makes when it hands out a fresh one.
    rack_name: the rack it is in; its own name when it is in none.
    rack_available: whether a head can reach its rack: placed, with no lid on, and on top of any
      stack it is in.
  """

  id: bytes
  name: str
  placed: Placed
  tracks_tips: bool
  tip: Optional[ToolFacts]
  prototype: Optional[ToolFacts]
  rack_name: str
  rack_available: bool

  @property
  def ref(self) -> pb.ResourceRef:
    return ref(self.id)

  def tip_for_pickup(self) -> ToolFacts:
    """The tip a channel picking up from this spot collects.

    Raises:
      NoTipError: If the spot is tracked and holds no tip.
    """
    if not self.tracks_tips:
      if self.prototype is None:
        raise NoTipError(f"{self.name} makes no tips")
      return self.prototype
    if self.tip is None:
      raise NoTipError(f"{self.name} holds no tip")
    return self.tip

  def target(self) -> ChannelTarget:
    """What the batch planner needs of it: a spot answers as a well does."""
    return ChannelTarget(
      key=self.id, footprint=footprint(self.name, self.placed), center=self.placed.bottom
    )


async def read_spots(
  store: ResourceStore, deck: pb.ResourceRef, spots: Sequence[handles.Resource]
) -> List[SpotFacts]:
  """Each tip spot's facts, in the order given, in three reads of the store.

  Raises:
    ValueError: If one is not a tip spot, or is not on the deck.
  """
  unique = list(dict.fromkeys(s.id for s in spots))
  nodes = await get_nodes(store, [ref(i) for i in unique], depth=1, ancestors=True)
  by_id = {node.id: node for node in nodes}
  racks = list(
    dict.fromkeys(
      by_id[i].parent_id
      for i in unique
      if by_id[i].parent_id in by_id
      and by_id[by_id[i].parent_id].attributes.kind == K.RESOURCE_KIND_TIP_RACK
    )
  )
  lidded = set()
  if racks:
    rack_children = await get_nodes(store, [ref(r) for r in racks], depth=1)
    lidded = {c.parent_id for c in rack_children if c.attributes.kind == K.RESOURCE_KIND_LID}
  placed = await locate(store, deck, unique)
  facts: Dict[bytes, SpotFacts] = {}
  for i in unique:
    node = by_id[i]
    if node.attributes.kind != K.RESOURCE_KIND_TIP_SPOT:
      raise ValueError(f"'{node.attributes.name}' is not a tip spot")
    rack = by_id.get(node.parent_id)
    available = True
    rack_name = node.attributes.name
    if rack is not None and rack.attributes.kind == K.RESOURCE_KIND_TIP_RACK:
      rack_name = rack.attributes.name
      holder = by_id.get(rack.parent_id)
      available = rack.attributes.HasField("location") and rack.id not in lidded
      if (
        available
        and holder is not None
        and holder.attributes.kind == K.RESOURCE_KIND_RESOURCE_STACK
        and holder.attributes.stack.direction == pb.STACK_DIRECTION_Z
      ):
        available = list(holder.child_ids)[-1] == rack.id
    state = node.state
    spec = node.attributes.tip_spot
    facts[i] = SpotFacts(
      id=i,
      name=node.attributes.name,
      placed=placed[i],
      tracks_tips=not state.HasField("tip_tracking_enabled") or state.tip_tracking_enabled,
      tip=tool_on(node, by_id),
      prototype=(
        ToolFacts.from_attributes(spec.prototype_tip) if spec.HasField("prototype_tip") else None
      ),
      rack_name=rack_name,
      rack_available=available,
    )
  return [facts[s.id] for s in spots]


def check_racks_available(spots: Sequence[SpotFacts], action: str) -> None:
  """Raise if a head cannot reach a rack behind `spots`, naming each rack once.

  Raises:
    ValueError: If a rack is not available for tip handling.
  """
  for spot in spots:
    if not spot.rack_available:
      raise ValueError(f"Cannot {action} {spot.rack_name!r}: it is not available for tip handling.")


# -- the device's own parts ----------------------------------------------------------------------


class ArmModel:
  """The X-arm and everything it carries - channels, shafts, the 8-channel head, what they hold - as
  one read of the store answers it.

  Locations are along the deck's axes: the arm hangs from the deck unturned, and so does what hangs
  from it down to the shafts.
  """

  def __init__(self, nodes: Sequence[pb.ResourceNode]):
    self.by_id: Dict[bytes, pb.ResourceNode] = {node.id: node for node in nodes}
    self.arm = nodes[0] if nodes else None

  def location(self, resource_id: bytes) -> Optional[Coordinate]:
    """Where a part is in its parent, or None when it is not there or has no location."""
    node = self.by_id.get(resource_id)
    if node is None or not node.attributes.HasField("location"):
      return None
    return to_coordinate(node.attributes.location)

  def on_deck(self, resource_id: bytes) -> Optional[Coordinate]:
    """Where a part's origin is on the deck: its location and every parent's up to the arm's."""
    total = Coordinate.zero()
    current = self.by_id.get(resource_id)
    while current is not None:
      if not current.attributes.HasField("location"):
        return None
      total = total + to_coordinate(current.attributes.location)
      if self.arm is not None and current.id == self.arm.id:
        return total
      current = self.by_id.get(current.parent_id)
    return None

  def tool(self, shaft_id: bytes) -> Optional[ToolFacts]:
    """The tip or tool a shaft carries; None when it carries none."""
    node = self.by_id.get(shaft_id)
    return None if node is None else tool_on(node, self.by_id)

  def lowest(self, resource_id: bytes) -> Optional[float]:
    """The lowest origin of a part and everything under it, along the deck's z."""
    node = self.by_id.get(resource_id)
    here = self.on_deck(resource_id)
    if node is None or here is None:
      return None
    lowest = here.z
    pending = list(node.child_ids)
    while pending:
      child = self.by_id.get(pending.pop())
      if child is None:
        continue
      at = self.on_deck(child.id)
      if at is not None:
        lowest = min(lowest, at.z)
      pending.extend(child.child_ids)
    return lowest


async def read_arm(store: ResourceStore, arm_id: bytes, depth: int = 3) -> ArmModel:
  """The arm, its channels and head, their shafts and what each carries, in one read of the store.

  Args:
    depth: how far below the arm to read; 3 reaches what the shafts carry, -1 everything, a plate
      the gripper tools hold included.
  """
  return ArmModel(await get_nodes(store, [ref(arm_id)], depth=depth))


# -- what the device reports ---------------------------------------------------------------------


def position(
  resource_id: bytes,
  x: Optional[float] = None,
  y: Optional[float] = None,
  z: Optional[float] = None,
  frame: Optional[pb.ResourceRef] = None,
  reference_point: Optional[Coordinate] = None,
) -> spb.DevicePosition:
  """Where a part of a device is now: in its parent, or with its reference point in `frame`.

  An axis left None stays as it is.
  """
  where = spb.DevicePosition(resource=ref(resource_id), location=pb.PartialVec3(x=x, y=y, z=z))
  if frame is not None:
    where.frame.CopyFrom(frame)
  if reference_point is not None:
    where.reference_point.CopyFrom(to_vec3(reference_point))
  return where


async def record_positions(store: ResourceStore, positions: Sequence[spb.DevicePosition]) -> None:
  """Record where parts of a device are, all of them at once: what one move left them as."""
  if positions:
    await store.commands.record_device_positions(
      spb.RecordDevicePositionsRequest(lock_tokens=store.lock_tokens, positions=positions)
    )


async def resolve(store: ResourceStore, operation: pb.Operation, succeeded: Sequence[bool]) -> None:
  """Commit each item of a staged operation that the device carried out, and roll back the rest."""
  if not operation.id:
    return
  await store.commands.resolve_operation(
    spb.ResolveOperationRequest(
      lock_tokens=store.lock_tokens,
      operation_id=operation.id,
      outcomes=[spb.ItemOutcome(item=i, succeeded=ok) for i, ok in enumerate(succeeded)],
    )
  )
