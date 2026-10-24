"""What the Byonoy units share in the resource store: a body found or created by name, and holders
that check a drop the way the units' holders do."""

from typing import Any, Dict, Optional, Sequence

from pylabrobot.resources import Coordinate, Rotation
from pylabrobot.resources.store import build, devices, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb


def holder_definition(
  name: str,
  size: Coordinate,
  location: Coordinate,
  child_location: Coordinate,
  kind: pb.ResourceKind = pb.RESOURCE_KIND_RESOURCE_HOLDER,
  model: str = "",
) -> pb.ResourceDefinition:
  """A holder of one resource: a plate holder (no pedestal) or a resource holder."""
  plate = kind == pb.RESOURCE_KIND_PLATE_HOLDER
  holder = pb.HolderSpec(child_location=build.vec3(child_location), capacity=1)
  if plate:
    holder.pedestal_size_z = 0
  return build.resource(
    name,
    size,
    kind=kind,
    location=location,
    category="plate_holder" if plate else "resource_holder",
    model=model,
    type_name="PlateHolder" if plate else "ResourceHolder",
    holder=holder,
  )


def body_definition(
  name: str,
  size: Coordinate,
  rotation: Optional[Rotation],
  category: Optional[str],
  model: Optional[str],
  barcode: Optional[pb.Barcode],
  preferred_pickup_location: Optional[Coordinate],
  children: Sequence[pb.ResourceDefinition] = (),
) -> pb.ResourceDefinition:
  """A unit's body, with what hangs from it."""
  attributes: Dict[str, Any] = {}
  if barcode is not None:
    attributes["barcode"] = barcode
  if preferred_pickup_location is not None:
    attributes["preferred_pickup_location"] = build.vec3(preferred_pickup_location)
  return build.resource(
    name,
    size,
    rotation=rotation,
    category=category or "",
    model=model or "",
    children=children,
    **attributes,
  )


async def assign_unlocated(parent: handles.Resource, child: handles.Resource) -> None:
  """Put `child` in `parent` with no location, as `assign_child_resource(child, location=None)`
  does to a parent that seats nothing."""
  await parent.store.commands.assign_resources(
    spb.AssignResourcesRequest(
      lock_tokens=parent.store.lock_tokens,
      assignments=[pb.AssignChild(child=child.ref, parent=parent.ref, no_location=True)],
    )
  )


class Unit:
  """A Byonoy unit: its body in a resource store, and its holders. `create_resources` finds the
  body there by name, or creates it when the store has none; `get_resources` only finds it.

  Attributes:
    store: the resource store its body is in.
  """

  def __init__(self, name: str, store: Optional[ResourceStore]):
    self._name = name
    self.store = store if store is not None else ResourceStore.in_memory()
    self._body: Optional[handles.Resource] = None
    self._parts: Dict[str, handles.Resource] = {}

  @property
  def name(self) -> str:
    """The name of its body."""
    return self._name

  def definition(self) -> pb.ResourceDefinition:
    """Its body and holders, as `create_resources` creates them."""
    raise NotImplementedError

  @property
  def body(self) -> handles.Resource:
    """Its body in the store.

    Raises:
      RuntimeError: if its body is not found or created yet: call `create_resources` first.
    """
    if self._body is None:
      raise devices.not_in_store(self.name)
    return self._body

  async def _find_resources(self, create: bool) -> handles.Resource:
    if self._body is None:
      body = await devices.find_or_create(self.store, self.definition(), create=create)
      self._parts = {child.name: child for child in await body.get_children()}
      self._body = body
    return self._body

  async def create_resources(self) -> handles.Resource:
    """Find its body in its store by name, or create it there as a root.

    Returns:
      the body.

    Raises:
      ValueError: the store's resource of its name is not this unit's kind and model.
    """
    return await self._find_resources(create=True)

  async def get_resources(self) -> handles.Resource:
    """Find its body in its store by name; never create it.

    Returns:
      the body.

    Raises:
      LookupError: the store has nothing of its name.
      ValueError: the store's resource of its name is not this unit's kind and model.
    """
    return await self._find_resources(create=False)

  def part(self, name: str) -> handles.Resource:
    """One of its holders, by name.

    Raises:
      RuntimeError: if its body is not in its store yet.
    """
    if self._body is None:
      raise devices.not_in_store(self.name)
    return self._parts[name]


class Holder:
  """A unit's holder: what is assigned goes in as `assign_child_resource` puts it; a drop is
  checked by `check_can_drop_resource_here`, empty or holding the resource dropped."""

  def __init__(self, unit: Unit, name: str):
    self._unit = unit
    self.name = name

  @property
  def handle(self) -> handles.Resource:
    """The holder in the resource store."""
    return self._unit.part(self.name)

  async def get_resource_held(self) -> Optional[handles.Resource]:
    """What it holds; None when empty."""
    children = await self.handle.get_children()
    return children[0] if children else None

  async def check_can_drop_resource_here(self, resource: handles.Resource) -> None:
    """Raise unless it is empty or already holds `resource`.

    Raises:
      RuntimeError: if it holds something else.
    """
    held = await self.get_resource_held()
    if held is not None and held != resource:
      raise RuntimeError(
        f"Cannot drop resource {resource.name} onto resource holder {self.name} while it already "
        "has a resource. Please remove the resource before dropping a new one."
      )

  async def assign_child_resource(
    self, resource: handles.Resource, location: Optional[Coordinate] = None
  ) -> None:
    """Put `resource` in it, at `location` or where it seats it."""
    await self.handle.assign_child_resource(resource, location=location)

  async def unassign_child_resource(self, resource: handles.Resource) -> None:
    """Take `resource` out of it.

    Raises:
      ValueError: if `resource` is not in it.
    """
    await self.handle.unassign_child_resource(resource)
