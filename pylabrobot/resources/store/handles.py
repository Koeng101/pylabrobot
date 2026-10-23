"""Handles: PLR's resources as a store holds them.

A handle is a resource's id, name and kind, and the store it is in. Every read asks the store, so
what a handle answers is what the store holds now, wherever the store is; every change is made in
the store, and every handle to that resource sees it.

What a resource is built with stays as it was built: a plate's wells, a tip rack's spots and a
carrier's sites. A handle to one knows them, so `plate["A1"]` and `carrier[0]` ask nothing.

A handle that moves a resource emits the events PLR's `Resource` emits for the same move,
`resource.unassigned` and `resource.assigned`, while an event bus listens.

Handles are made by a `ResourceStore` (`create`, `get`, `roots`), never directly.
"""

from __future__ import annotations

from typing import (
  TYPE_CHECKING,
  Any,
  Dict,
  Iterable,
  List,
  Mapping,
  Optional,
  Sequence,
  Tuple,
  Type,
  Union,
)

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct

from pylabrobot.events import coordinate_reference, emit_event, is_event_bus_active
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.tree import to_coordinate, to_rotation, to_vec3
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.resources.utils import row_index_to_label
from pylabrobot.utils.positions import expand_string_range

if TYPE_CHECKING:
  from pylabrobot.resources.store.client import ResourceStore

K = pb.ResourceKind

_ANCHOR_X = {
  "l": pb.ANCHOR_X_LEFT,
  "left": pb.ANCHOR_X_LEFT,
  "c": pb.ANCHOR_X_CENTER,
  "center": pb.ANCHOR_X_CENTER,
  "r": pb.ANCHOR_X_RIGHT,
  "right": pb.ANCHOR_X_RIGHT,
}
_ANCHOR_Y = {
  "f": pb.ANCHOR_Y_FRONT,
  "front": pb.ANCHOR_Y_FRONT,
  "c": pb.ANCHOR_Y_CENTER,
  "center": pb.ANCHOR_Y_CENTER,
  "b": pb.ANCHOR_Y_BACK,
  "back": pb.ANCHOR_Y_BACK,
}
_ANCHOR_Z = {
  "b": pb.ANCHOR_Z_BOTTOM,
  "bottom": pb.ANCHOR_Z_BOTTOM,
  "c": pb.ANCHOR_Z_CENTER,
  "center": pb.ANCHOR_Z_CENTER,
  "t": pb.ANCHOR_Z_TOP,
  "top": pb.ANCHOR_Z_TOP,
  "cb": pb.ANCHOR_Z_CAVITY_BOTTOM,
  "cavity_bottom": pb.ANCHOR_Z_CAVITY_BOTTOM,
}


def anchor(x: str = "l", y: str = "f", z: str = "b") -> pb.Anchor:
  """A point of a resource's box, named as `Resource.get_anchor` names it.

  Args:
    x: "l"/"left", "c"/"center" or "r"/"right".
    y: "f"/"front", "c"/"center" or "b"/"back".
    z: "b"/"bottom", "c"/"center", "t"/"top", or "cb"/"cavity_bottom": a container's inside floor.

  Raises:
    ValueError: A name that is none of these.
  """
  try:
    return pb.Anchor(x=_ANCHOR_X[x.lower()], y=_ANCHOR_Y[y.lower()], z=_ANCHOR_Z[z.lower()])
  except KeyError as error:
    raise ValueError(f"no anchor ({x!r}, {y!r}, {z!r})") from error


class Resource:
  """A resource in a store.

  Attributes:
    store: The store it is in.
    id: Its id in the store; opaque.
    name: Its name: unique in the store for a root, and within its root otherwise.
    kind: What it is, which decides what the store computes for it.
  """

  def __init__(
    self, store: ResourceStore, node: pb.ResourceNode, children: Sequence[pb.ResourceNode]
  ):
    self.store = store
    self.id = node.id
    self.name = node.attributes.name
    self.kind: pb.ResourceKind = node.attributes.kind

  @property
  def ref(self) -> pb.ResourceRef:
    return pb.ResourceRef(id=self.id)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, Resource) and other.id == self.id and other.store is self.store

  def __hash__(self) -> int:
    return hash(self.id)

  def __repr__(self) -> str:
    return f"{type(self).__name__}({self.name!r})"

  # -- reading -----------------------------------------------------------------------------------

  async def node(self, view: pb.View = pb.VIEW_PENDING) -> pb.ResourceNode:
    """Everything the store holds of it: what it is, its state, its parent and its children."""
    response = await self.store.commands.get_resources(
      spb.GetResourcesRequest(resources=[self.ref], depth=0, view=view)
    )
    return response.nodes[0]

  async def attributes(self) -> pb.ResourceAttributes:
    return (await self.node()).attributes

  async def state(self, view: pb.View = pb.VIEW_PENDING) -> pb.ResourceState:
    return (await self.node(view)).state

  async def _geometry(
    self, frame: Optional[Resource] = None, anchors: Sequence[pb.Anchor] = ()
  ) -> spb.Geometry:
    query = spb.GeometryQuery(resource=self.ref, anchors=anchors)
    if frame is not None:
      query.frame.CopyFrom(frame.ref)
    response = await self.store.commands.resolve_geometry(
      spb.ResolveGeometryRequest(queries=[query])
    )
    geometry = response.results[0]
    if geometry.HasField("issue") and (anchors or not geometry.resource_id):
      raise StoreError(geometry.issue.problem, geometry.issue.message, self.name)
    return geometry

  async def get_size(self) -> Coordinate:
    """Its size along its own axes; a stack's is what it holds."""
    return to_coordinate((await self._geometry()).size)

  async def get_absolute_size(self) -> Coordinate:
    """The size of its box once turned, along its root's axes."""
    return to_coordinate((await self._geometry()).absolute_size)

  async def get_location(self) -> Optional[Coordinate]:
    """Where it is in its parent, along the parent's axes; unset on a root."""
    attributes = await self.attributes()
    return to_coordinate(attributes.location) if attributes.HasField("location") else None

  async def get_rotation(self) -> Rotation:
    """How it is turned in its parent."""
    return to_rotation((await self.attributes()).rotation)

  async def get_absolute_rotation(self) -> Rotation:
    return to_rotation((await self._geometry()).absolute_rotation)

  async def get_absolute_location(self, x: str = "l", y: str = "f", z: str = "b") -> Coordinate:
    """A point of it along the axes its root is turned in; see `anchor`."""
    geometry = await self._geometry(anchors=[anchor(x, y, z)])
    return to_coordinate(geometry.locations[0])

  async def get_location_wrt(
    self, other: Resource, x: str = "l", y: str = "f", z: str = "b"
  ) -> Coordinate:
    """A point of it along `other`'s axes, from `other`'s left front bottom corner."""
    geometry = await self._geometry(frame=other, anchors=[anchor(x, y, z)])
    return to_coordinate(geometry.locations[0])

  async def get_highest_known_point(self) -> float:
    """The highest point of it and everything in it, along its root's axes.

    Raises:
      StoreError: It is in a tree nobody placed, so it has no location.
    """
    return (await self._geometry(anchors=[anchor()])).highest_point

  async def get_metadata(self) -> Dict[str, Any]:
    return json_format.MessageToDict((await self.attributes()).metadata)

  async def get_barcode(self) -> Optional[pb.Barcode]:
    attributes = await self.attributes()
    return attributes.barcode if attributes.HasField("barcode") else None

  async def get_parent(self) -> Optional[Resource]:
    node = await self.node()
    if not node.parent_id:
      return None
    return await self.store.get_by_id(node.parent_id)

  async def get_root(self) -> Resource:
    node = await self.node()
    return self if node.root_id == self.id else await self.store.get_by_id(node.root_id)

  async def get_children(self) -> List[Resource]:
    response = await self.store.commands.get_resources(
      spb.GetResourcesRequest(resources=[self.ref], depth=1)
    )
    return await self.store.make_handles(
      [node for node in response.nodes if node.parent_id == self.id], response.nodes
    )

  async def get_resource(self, name: str) -> Resource:
    """A resource under it by name.

    Raises:
      StoreError: Nothing under it has that name.
    """
    found = await self.find_resources(names=[name])
    if not found:
      raise StoreError(pb.PROBLEM_NOT_FOUND, f"'{self.name}' holds no '{name}'", name)
    return found[0]

  async def find_resources(
    self,
    kinds: Sequence[pb.ResourceKind] = (),
    names: Sequence[str] = (),
    models: Sequence[str] = (),
    categories: Sequence[str] = (),
    name_prefix: str = "",
  ) -> List[Resource]:
    """It and everything under it that matches, in pre-order."""
    return await self.store.find_resources(
      scope=self,
      filter=spb.ResourceFilter(
        kinds=kinds, names=names, models=models, categories=categories, name_prefix=name_prefix
      ),
    )

  async def is_in_subtree_of(self, other: Resource) -> bool:
    found = await other.find_resources(names=[self.name])
    return any(each.id == self.id for each in found)

  # -- changing ----------------------------------------------------------------------------------

  async def assign_child_resource(
    self,
    child: Resource,
    location: Optional[Coordinate] = None,
    track: Optional[int] = None,
    index: Optional[int] = None,
  ) -> None:
    """Put `child` in it, out of wherever it was.

    Args:
      child: What to put in it; it may be in another tree.
      location: Where, relative to it along its axes. With neither this nor `track`, it goes where
        this resource seats it: a holder's child location, the top of a stack, a lid's nesting.
      track: A Hamilton deck's track, from 1.
      index: Its position among the children; unset appends.
    """
    assignment = pb.AssignChild(child=child.ref, parent=self.ref)
    if location is not None:
      assignment.location.CopyFrom(to_vec3(location))
    if track is not None:
      assignment.track = track
    if index is not None:
      assignment.index = index
    before = await _read_for_events(self.store, [child.ref, self.ref])
    response = await self.store.commands.assign_resources(
      spb.AssignResourcesRequest(lock_tokens=self.store.lock_tokens, assignments=[assignment])
    )
    if before is not None:
      _emit_unassigned(before, child.id)
      _emit_assigned(before, response.nodes[0], self.id)

  async def unassign_child_resource(self, child: Resource) -> None:
    """Take `child` out of it; `child` becomes a root with no location.

    Raises:
      ValueError: `child` is not its child.
    """
    parent = await child.get_parent()
    if parent != self:
      raise ValueError(f"'{child.name}' is not in '{self.name}'")
    await child.unassign()

  async def unassign(self) -> None:
    """Take it out of its parent; it becomes a root with no location."""
    before = await _read_for_events(self.store, [self.ref])
    await self.store.commands.unassign_resources(
      spb.UnassignResourcesRequest(lock_tokens=self.store.lock_tokens, resources=[self.ref])
    )
    if before is not None:
      _emit_unassigned(before, self.id)

  async def _update(self, *updates: spb.ResourceUpdate) -> None:
    await self.store.commands.update_resources(
      spb.UpdateResourcesRequest(lock_tokens=self.store.lock_tokens, updates=updates)
    )

  async def rotate(
    self, x: float = 0, y: float = 0, z: float = 0, pivot: Optional[Coordinate] = None
  ) -> None:
    """Turn it by these angles about its parent's axes, in degrees.

    Args:
      pivot: What to turn about, in its own frame; it stays put. Unset turns about its origin.
    """
    change = pb.RotationChange(resource=self.ref, by=pb.Rotation(x=x, y=y, z=z))
    if pivot is not None:
      change.pivot.CopyFrom(to_vec3(pivot))
    await self._update(spb.ResourceUpdate(rotation=change))

  async def rotate_to(
    self,
    x: Optional[float] = None,
    y: Optional[float] = None,
    z: Optional[float] = None,
    pivot: Optional[Coordinate] = None,
  ) -> None:
    """Turn it to these angles about its parent's axes; an axis left unset stays as it is."""
    change = pb.RotationChange(resource=self.ref, to=pb.PartialRotation(x=x, y=y, z=z))
    if pivot is not None:
      change.pivot.CopyFrom(to_vec3(pivot))
    await self._update(spb.ResourceUpdate(rotation=change))

  async def set_metadata(self, metadata: Mapping[str, Any], replace: bool = False) -> None:
    """Merge these keys into its metadata, or replace all of it."""
    struct = Struct()
    struct.update(metadata)
    await self._update(
      spb.ResourceUpdate(
        metadata=pb.SetMetadata(resource=self.ref, metadata=struct, replace=replace)
      )
    )

  async def set_barcode(self, barcode: Optional[pb.Barcode]) -> None:
    change = pb.SetBarcode(resource=self.ref)
    if barcode is not None:
      change.barcode.CopyFrom(barcode)
    await self._update(spb.ResourceUpdate(barcode=change))

  async def get_preferred_pickup_location(self) -> Optional[Coordinate]:
    """Where a gripper should take hold of it, in its own frame; unset when it names none."""
    attributes = await self.attributes()
    if not attributes.HasField("preferred_pickup_location"):
      return None
    return to_coordinate(attributes.preferred_pickup_location)

  async def set_preferred_pickup_location(self, location: Optional[Coordinate]) -> None:
    """Say where a gripper should take hold of it, in its own frame; None clears it."""
    change = pb.SetPreferredPickupLocation(resource=self.ref)
    if location is not None:
      change.location.CopyFrom(to_vec3(location))
    await self._update(spb.ResourceUpdate(preferred_pickup_location=change))

  async def set_volume_tracking(self, enabled: bool) -> None:
    """Track volumes in it and every container and tip under it, or stop."""
    await self._update(
      spb.ResourceUpdate(tracking=pb.SetTracking(scope=self.ref, volume_tracking=enabled))
    )

  async def set_tip_tracking(self, enabled: bool) -> None:
    """Track tips in it and every tip spot under it, or stop."""
    await self._update(
      spb.ResourceUpdate(tracking=pb.SetTracking(scope=self.ref, tip_tracking=enabled))
    )

  async def delete(self) -> None:
    """Remove it and everything under it from the store; leaving a parent, it emits
    `resource.unassigned`."""
    before = await _read_for_events(self.store, [self.ref])
    await self.store.commands.delete_resources(
      spb.DeleteResourcesRequest(lock_tokens=self.store.lock_tokens, resources=[self.ref])
    )
    if before is not None:
      _emit_unassigned(before, self.id)


# -- containers ----------------------------------------------------------------------------------


class Container(Resource):
  """Something that holds liquid: a well, a trough, a tube, a petri dish, a trash."""

  async def get_volume(self, view: pb.View = pb.VIEW_PENDING) -> float:
    """What it holds, counting staged changes unless asked for what is committed."""
    state = await self.state(view)
    return state.volume.pending_volume if view != pb.VIEW_COMMITTED else state.volume.volume

  async def get_max_volume(self) -> Optional[float]:
    spec = (await self.attributes()).container
    return spec.max_volume if spec.HasField("max_volume") else None

  async def get_free_volume(self) -> float:
    """How much more it takes.

    Raises:
      ValueError: It has no maximum volume.
    """
    node = await self.node()
    spec = node.attributes.container
    if not spec.HasField("max_volume"):
      raise ValueError(f"'{self.name}' has no maximum volume")
    return spec.max_volume - node.state.volume.pending_volume

  async def set_volume(self, volume: float) -> None:
    """Say what it holds, as a person who filled it would."""
    await self._update(spb.ResourceUpdate(volume=pb.SetVolume(resource=self.ref, volume=volume)))

  async def compute_height_from_volume(self, volume: float) -> float:
    """The liquid height above the cavity bottom that `volume` makes."""
    result = await self._convert(spb.HeightVolumeQuery(container=self.ref, volume=volume))
    return result.height

  async def compute_volume_from_height(self, height: float) -> float:
    """The volume a liquid height above the cavity bottom holds."""
    result = await self._convert(spb.HeightVolumeQuery(container=self.ref, height=height))
    return result.volume

  async def _convert(self, query: spb.HeightVolumeQuery) -> spb.HeightVolumeResult:
    response = await self.store.commands.convert_height_volume(
      spb.ConvertHeightVolumeRequest(queries=[query])
    )
    result = response.results[0]
    if result.HasField("issue"):
      raise StoreError(result.issue.problem, result.issue.message, self.name)
    return result


class Well(Container):
  pass


class Trough(Container):
  pass


class Tube(Container):
  pass


class PetriDish(Container):
  pass


class Trash(Container):
  pass


# -- itemized resources --------------------------------------------------------------------------

Identifiers = Union[str, int, slice, range, Sequence[Union[str, int]]]


class ItemizedResource(Resource):
  """Items laid out in a grid: a plate's wells, a tip rack's spots, a tube rack's tubes.

  Attributes:
    num_items_x: Columns.
    num_items_y: Rows.
  """

  def __init__(
    self, store: ResourceStore, node: pb.ResourceNode, children: Sequence[pb.ResourceNode]
  ):
    super().__init__(store, node, children)
    self.num_items_x = node.attributes.itemized.num_items_x
    self.num_items_y = node.attributes.itemized.num_items_y
    by_id = {child.id: child for child in children}
    items = [by_id[i] for i in node.child_ids if i in by_id and by_id[i].attributes.identifier]
    self._items: List[Resource] = [store.handle_from_node(item, ()) for item in items]
    self._by_identifier = {
      item.attributes.identifier: handle for item, handle in zip(items, self._items)
    }

  @property
  def num_items(self) -> int:
    return len(self._items)

  @property
  def items(self) -> List[Resource]:
    """Every item, column-major: A1, B1, ..., A2, ..."""
    return list(self._items)

  @property
  def identifiers(self) -> List[str]:
    """Every item's identifier, column-major."""
    return list(self._by_identifier)

  def get_item(self, identifier: Union[str, int, Tuple[int, int]]) -> Resource:
    """An item by identifier ("A1"), index (column-major, from 0), or (row, column).

    Raises:
      IndexError: There is no such item.
    """
    if isinstance(identifier, tuple):
      row, column = identifier
      identifier = f"{row_index_to_label(row)}{column + 1}"
    if isinstance(identifier, str):
      item = self._by_identifier.get(identifier)
      if item is None:
        raise IndexError(f"'{self.name}' has no item '{identifier}'")
      return item
    if not 0 <= identifier < len(self._items):
      raise IndexError(f"'{self.name}' has no item {identifier}")
    return self._items[identifier]

  def get_items(self, identifiers: Union[str, Sequence[Union[str, int]]]) -> List[Resource]:
    """Items by a range, "A1:H1", or by identifiers or indices."""
    if isinstance(identifiers, str):
      identifiers = expand_string_range(identifiers)
    return [self.get_item(identifier) for identifier in identifiers]

  def __getitem__(self, identifier: Identifiers) -> List[Resource]:
    """Items as `ItemizedResource.__getitem__` gives them: always a list.

    `plate["A1"]`, `plate["A1:H1"]`, `plate[0]`, `plate[0:8]`, `plate["A1":"A2"]`, `plate[[0, 1]]`.
    """
    if isinstance(identifier, (str, int)):
      if isinstance(identifier, str) and ":" in identifier:
        return self.get_items(identifier)
      return [self.get_item(identifier)]
    if isinstance(identifier, (slice, range)):
      identifiers = list(self._by_identifier)
      start = identifier.start
      stop = identifier.stop
      start = identifiers.index(start) if isinstance(start, str) else (start or 0)
      stop = (
        identifiers.index(stop)
        if isinstance(stop, str)
        else (len(self._items) if stop is None else stop)
      )
      return self.get_items(list(range(start, stop, identifier.step or 1)))
    return self.get_items(list(identifier))


class Plate(ItemizedResource):
  def get_well(self, identifier: Union[str, int, Tuple[int, int]]) -> Well:
    well = self.get_item(identifier)
    if not isinstance(well, Well):
      raise TypeError(f"'{well.name}' is not a well")
    return well

  def get_wells(self, identifiers: Union[str, Sequence[Union[str, int]]]) -> List[Well]:
    return [self.get_well(identifier) for identifier in _expand(identifiers)]

  async def get_lid(self) -> Optional[Lid]:
    for child in await self.get_children():
      if isinstance(child, Lid):
        return child
    return None

  async def has_lid(self) -> bool:
    return await self.get_lid() is not None

  async def set_well_volumes(self, volumes: Union[float, Sequence[float]]) -> None:
    """Say what every well holds, column-major; one volume sets them all."""
    if isinstance(volumes, (int, float)):
      volumes = [float(volumes)] * self.num_items
    if len(volumes) != self.num_items:
      raise ValueError(f"'{self.name}' has {self.num_items} wells, not {len(volumes)}")
    await self._update(
      *[
        spb.ResourceUpdate(volume=pb.SetVolume(resource=well.ref, volume=volume))
        for well, volume in zip(self.items, volumes)
      ]
    )


class TipRack(ItemizedResource):
  def get_tip_spot(self, identifier: Union[str, int, Tuple[int, int]]) -> TipSpot:
    spot = self.get_item(identifier)
    if not isinstance(spot, TipSpot):
      raise TypeError(f"'{spot.name}' is not a tip spot")
    return spot

  def get_tip_spots(self, identifiers: Union[str, Sequence[Union[str, int]]]) -> List[TipSpot]:
    return [self.get_tip_spot(identifier) for identifier in _expand(identifiers)]

  async def set_tip_state(self, present: Union[bool, Sequence[bool]]) -> None:
    """Say which spots hold a fresh tip, column-major; one value sets them all.

    Each tip made emits `resource.assigned`, then each tip taken away `resource.unassigned`, as
    `TipSpot.assign_tip` and `unassign_tip` do.
    """
    states = [present] * self.num_items if isinstance(present, bool) else list(present)
    if len(states) != self.num_items:
      raise ValueError(f"'{self.name}' has {self.num_items} spots, not {len(states)}")
    updates = []
    for state in (True, False):
      spots = [spot.ref for spot, each in zip(self.items, states) if each is state]
      if spots:
        updates.append(
          spb.ResourceUpdate(tip_presence=pb.SetTipPresence(spots=spots, present=state))
        )
    refs = [spot.ref for spot in self.items]
    before = await _read_for_events(self.store, refs, depth=1)
    await self._update(*updates)
    if before is None:
      return
    response = await self.store.commands.get_resources(
      spb.GetResourcesRequest(resources=refs, depth=1)
    )
    held, holds = _tools_by_holder(before.values()), _tools_by_holder(response.nodes)
    for state in (True, False):
      for spot, each in zip(self.items, states):
        if each is not state:
          continue
        if state and spot.id not in held and spot.id in holds:
          _emit_assigned(before, holds[spot.id], spot.id)
        elif not state and spot.id in held:
          _emit_unassigned(before, held[spot.id].id)

  async def fill(self) -> None:
    await self.set_tip_state(True)

  async def empty(self) -> None:
    await self.set_tip_state(False)


class TubeRack(ItemizedResource):
  pass


class TipSpot(Resource):
  async def get_tip(self) -> Optional[Tip]:
    """The tip it holds; unset when it holds none."""
    for child in await self.get_children():
      if isinstance(child, Tip):
        return child
    return None

  async def has_tip(self) -> bool:
    return await self.get_tip() is not None


class Tip(Resource):
  async def get_volume(self, view: pb.View = pb.VIEW_PENDING) -> float:
    state = await self.state(view)
    return state.volume.pending_volume if view != pb.VIEW_COMMITTED else state.volume.volume

  async def set_volume(self, volume: float) -> None:
    """Say what it holds: 0 once it has been emptied somewhere the model does not hold."""
    await self._update(spb.ResourceUpdate(volume=pb.SetVolume(resource=self.ref, volume=volume)))


class Lid(Resource):
  pass


# -- what other resources sit in -----------------------------------------------------------------


class ResourceHolder(Resource):
  async def get_resource_held(self) -> Optional[Resource]:
    """What it holds; unset when empty."""
    children = await self.get_children()
    return children[0] if children else None


class PlateHolder(ResourceHolder):
  pass


class Carrier(Resource):
  """A carrier: sites, fixed when it is made, that resources go in. `carrier[0]` is a site."""

  def __init__(
    self, store: ResourceStore, node: pb.ResourceNode, children: Sequence[pb.ResourceNode]
  ):
    super().__init__(store, node, children)
    by_id = {child.id: child for child in children}
    self.sites: List[Resource] = [
      store.handle_from_node(by_id[i], ()) for i in node.child_ids if i in by_id
    ]

  @property
  def capacity(self) -> int:
    return len(self.sites)

  def __getitem__(self, index: int) -> Resource:
    return self.sites[index]


class Deck(Resource):
  async def get_hamilton_tracks(self) -> pb.HamiltonDeckSpec:
    """A Hamilton deck's tracks.

    Raises:
      StoreError: It is not a Hamilton deck.
    """
    spec = (await self.attributes()).deck
    if not spec.HasField("hamilton"):
      raise StoreError(pb.PROBLEM_WRONG_KIND, f"'{self.name}' has no tracks", self.name)
    return spec.hamilton

  async def track_location(self, track: int) -> Coordinate:
    """Where a Hamilton deck's track starts, in the deck's frame; tracks count from 1."""
    tracks = await self.get_hamilton_tracks()
    origin = to_coordinate(tracks.track_origin)
    return origin + Coordinate((track - 1) * tracks.track_pitch, 0, 0)

  async def track_at(self, x: float) -> int:
    """The Hamilton deck's track an x coordinate in the deck's frame falls on, from 1."""
    tracks = await self.get_hamilton_tracks()
    return int((x - tracks.track_origin.x) / tracks.track_pitch) + 1

  async def tracks_of(self, resource: Resource) -> Tuple[int, int]:
    """The first and last tracks of a Hamilton deck a resource on it covers: where its origin
    is, and where the right of its box, turned as it stands, ends."""
    tracks = await self.get_hamilton_tracks()
    corners = [anchor(x, y, z) for x in "lr" for y in "fb" for z in "bt"]
    geometry = await resource._geometry(frame=self, anchors=[anchor()] + corners)
    left = geometry.locations[0].x
    right = max(location.x for location in geometry.locations[1:])
    pitch, origin = tracks.track_pitch, tracks.track_origin.x
    return int((left - origin) / pitch) + 1, int((right - origin) / pitch)


class PlateAdapter(Resource):
  pass


class ResourceStack(Resource):
  async def get_top_item(self) -> Optional[Resource]:
    """The resource on top; unset when the stack is empty."""
    children = await self.get_children()
    return children[-1] if children else None


class ContainerRack(Resource):
  pass


class PetriDishHolder(Resource):
  pass


class EmbeddedTipRackHolder(Resource):
  pass


# -- devices -------------------------------------------------------------------------------------


class HeadTool(Resource):
  pass


class PipetteChannel(Resource):
  pass


class TipMountingShaft(Resource):
  async def get_tool(self) -> Optional[Resource]:
    """The tip or tool it carries; unset when bare."""
    for child in await self.get_children():
      if isinstance(child, (Tip, HeadTool)):
        return child
    return None


class NChannelPipette(Resource):
  pass


class LinkBody(Resource):
  pass


class MechanicalGripper(Resource):
  async def get_jaw_width(self) -> float:
    return (await self.state()).jaw_width


HANDLE_TYPES: Dict[int, Type[Resource]] = {
  K.RESOURCE_KIND_RESOURCE: Resource,
  K.RESOURCE_KIND_DECK: Deck,
  K.RESOURCE_KIND_CARRIER: Carrier,
  K.RESOURCE_KIND_RESOURCE_HOLDER: ResourceHolder,
  K.RESOURCE_KIND_PLATE_HOLDER: PlateHolder,
  K.RESOURCE_KIND_CONTAINER: Container,
  K.RESOURCE_KIND_WELL: Well,
  K.RESOURCE_KIND_TROUGH: Trough,
  K.RESOURCE_KIND_TUBE: Tube,
  K.RESOURCE_KIND_PETRI_DISH: PetriDish,
  K.RESOURCE_KIND_TRASH: Trash,
  K.RESOURCE_KIND_PLATE: Plate,
  K.RESOURCE_KIND_TIP_RACK: TipRack,
  K.RESOURCE_KIND_TIP_SPOT: TipSpot,
  K.RESOURCE_KIND_TIP: Tip,
  K.RESOURCE_KIND_LID: Lid,
  K.RESOURCE_KIND_PLATE_ADAPTER: PlateAdapter,
  K.RESOURCE_KIND_RESOURCE_STACK: ResourceStack,
  K.RESOURCE_KIND_CONTAINER_RACK: ContainerRack,
  K.RESOURCE_KIND_TUBE_RACK: TubeRack,
  K.RESOURCE_KIND_PETRI_DISH_HOLDER: PetriDishHolder,
  K.RESOURCE_KIND_EMBEDDED_TIP_RACK_HOLDER: EmbeddedTipRackHolder,
  K.RESOURCE_KIND_HEAD_TOOL: HeadTool,
  K.RESOURCE_KIND_PIPETTE_CHANNEL: PipetteChannel,
  K.RESOURCE_KIND_TIP_MOUNTING_SHAFT: TipMountingShaft,
  K.RESOURCE_KIND_N_CHANNEL_PIPETTE: NChannelPipette,
  K.RESOURCE_KIND_LINK_BODY: LinkBody,
  K.RESOURCE_KIND_MECHANICAL_GRIPPER: MechanicalGripper,
}

# Kinds whose handle knows its children, which are fixed when it is made.
STRUCTURED_KINDS = frozenset(
  kind
  for kind, handle_type in HANDLE_TYPES.items()
  if issubclass(handle_type, (ItemizedResource, Carrier))
)


# -- events --------------------------------------------------------------------------------------
# `resource.unassigned` when a resource leaves a parent, and `resource.assigned` when it enters
# one, with the payloads PLR's `Resource` gives them. Read only while an event bus listens.


async def _read_for_events(
  store: ResourceStore, refs: Sequence[pb.ResourceRef], depth: int = 0
) -> Optional[Dict[bytes, pb.ResourceNode]]:
  """The resources, `depth` levels below them, and their ancestors, as they are before a move;
  None when nothing listens."""
  if not is_event_bus_active():
    return None
  response = await store.commands.get_resources(
    spb.GetResourcesRequest(resources=refs, depth=depth, ancestors=True)
  )
  return {node.id: node for node in response.nodes}


def _reference(
  node: pb.ResourceNode, by_id: Mapping[bytes, pb.ResourceNode], parent_id: bytes
) -> Dict[str, Any]:
  """`resource_reference` of a resource, with `parent_id` and its ancestors as its ancestry."""
  attributes = node.attributes
  reference: Dict[str, Any] = {
    "name": attributes.name,
    "type": attributes.type_name or HANDLE_TYPES[attributes.kind].__name__,
  }
  if attributes.model:
    reference["model"] = attributes.model
  rotation = attributes.rotation
  reference["rotation"] = {"x": rotation.x, "y": rotation.y, "z": rotation.z}
  ancestors: List[Dict[str, Any]] = []
  while parent_id:
    parent = by_id[parent_id]
    ancestor: Dict[str, Any] = {
      "name": parent.attributes.name,
      "type": parent.attributes.type_name or "Resource",
    }
    if parent.attributes.model:
      ancestor["model"] = parent.attributes.model
    ancestors.append(ancestor)
    parent_id = parent.parent_id
  if ancestors:
    reference["ancestors"] = ancestors
  return reference


def _location(node: pb.ResourceNode) -> Optional[Dict[str, Any]]:
  if not node.attributes.HasField("location"):
    return None
  return dict(coordinate_reference(to_coordinate(node.attributes.location)) or {})


def _emit_unassigned(before: Mapping[bytes, pb.ResourceNode], resource_id: bytes) -> None:
  node = before[resource_id]
  if not node.parent_id:
    return
  parent = before[node.parent_id]
  emit_event(
    "resource.unassigned",
    resource=_reference(node, before, b""),
    previous_parent=_reference(parent, before, parent.parent_id),
    previous_location=_location(node),
  )


def _emit_assigned(
  before: Mapping[bytes, pb.ResourceNode], node: pb.ResourceNode, parent_id: bytes
) -> None:
  parent = before[parent_id]
  emit_event(
    "resource.assigned",
    resource=_reference(node, before, parent_id),
    parent=_reference(parent, before, parent.parent_id),
    location=_location(node),
  )


def _tools_by_holder(nodes: Iterable[pb.ResourceNode]) -> Dict[bytes, pb.ResourceNode]:
  """Each tip or tool among `nodes`, by the id of what holds it."""
  return {
    node.parent_id: node
    for node in nodes
    if node.attributes.kind in (K.RESOURCE_KIND_TIP, K.RESOURCE_KIND_HEAD_TOOL)
  }


def _expand(identifiers: Union[str, Sequence[Union[str, int]]]) -> List[Union[str, int]]:
  if isinstance(identifiers, str):
    return list(expand_string_range(identifiers))
  return list(identifiers)
