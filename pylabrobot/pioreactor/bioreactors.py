from typing import Optional

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, devices, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError, plr_error
from pylabrobot.resources.store.v1 import types_pb2 as pb

# What a Pioreactor holds as its vessel: any container.
VESSEL_KINDS = (
  pb.RESOURCE_KIND_CONTAINER,
  pb.RESOURCE_KIND_WELL,
  pb.RESOURCE_KIND_TROUGH,
  pb.RESOURCE_KIND_TUBE,
  pb.RESOURCE_KIND_PETRI_DISH,
  pb.RESOURCE_KIND_TRASH,
)


class Pioreactor:
  """A Pioreactor bioreactor unit (https://pioreactor.com).

  Its body is a resource in a resource store holding the culture vessel, a single container:
  `create_resources` finds it there by name, or creates it when the store has none;
  `get_resources` only finds it. The store refuses a second vessel.

  Attributes:
    name: Its body's name.
    definition: Its body and the vessel it is built with, as they are created in the store.
    store: The store its body is in.
  """

  def __init__(
    self,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    model: Optional[str] = None,
    category: Optional[str] = None,
    vessel: Optional[pb.ResourceDefinition] = None,
    store: Optional[ResourceStore] = None,
  ):
    """
    Args:
      vessel: The vessel it is built with, with its location; none when unset.
      store: The store its body is in; a new one in memory when unset.
    """
    self.name = name
    self.definition = build.resource(
      name,
      Coordinate(size_x, size_y, size_z),
      model=model or "",
      category=category or "",
      holder=pb.HolderSpec(accepts=VESSEL_KINDS, capacity=1),
      children=[] if vessel is None else [vessel],
    )
    self.store = store or ResourceStore.in_memory()
    self._body: Optional[handles.Resource] = None

  @property
  def body(self) -> handles.Resource:
    """Its body in the store.

    Raises:
      RuntimeError: It is not found or created yet: call `create_resources` first.
    """
    if self._body is None:
      raise devices.not_in_store(self.name)
    return self._body

  async def _find_resources(self, create: bool) -> handles.Resource:
    if self._body is None:
      self._body = await devices.find_or_create(self.store, self.definition, create=create)
    return self._body

  async def create_resources(self) -> handles.Resource:
    """Its body in the store: the resource of its name if the store has one, else made from its
    definition as a root, to be placed by assigning it."""
    return await self._find_resources(create=True)

  async def get_resources(self) -> handles.Resource:
    """Its body, found in the store by name; never created.

    Raises:
      LookupError: The store has no resource of its name.
    """
    return await self._find_resources(create=False)

  async def assign_child_resource(
    self,
    resource: handles.Resource,
    location: Optional[Coordinate],
    reassign: bool = True,
  ) -> None:
    """Put the culture vessel in it.

    Args:
      resource: The vessel: a container.
      location: Where, relative to its body.
      reassign: If False, refuse a vessel that is in something.

    Raises:
      TypeError: `resource` is not a container.
      ValueError: It holds a vessel already, or `reassign` is False and `resource` is in something.
    """
    if resource.kind not in VESSEL_KINDS:
      raise TypeError("Pioreactor can only hold a Container as a child.")
    body = await self.create_resources()
    if not reassign and (await resource.node()).parent_id:
      raise ValueError(f"Will not assign resource '{resource.name}' that already has a parent.")
    try:
      await body.assign_child_resource(resource, location=location)
    except StoreError as error:
      raise plr_error(error, otherwise=ValueError) from error

  async def unassign_child_resource(self, resource: handles.Resource) -> None:
    """Take the vessel out of it.

    Raises:
      ValueError: It does not hold `resource`.
    """
    body = await self.create_resources()
    await body.unassign_child_resource(resource)

  async def get_vessel(self) -> handles.Container:
    """Its culture vessel.

    Raises:
      ValueError: It holds no vessel.
    """
    body = await self.create_resources()
    children = await body.get_children()
    if not children:
      raise ValueError(f"Pioreactor '{self.name}' has no vessel assigned.")
    vessel = children[0]
    assert isinstance(vessel, handles.Container)
    return vessel


async def pioreactor_20ml(name: str, store: Optional[ResourceStore] = None) -> Pioreactor:
  """Pioreactor 20mL Vessel: https://pioreactor.com/products/pioreactor-20ml

  Builds it and finds its body in `store` by name, creating it there when the store has none (a
  new store in memory when unset).

  Geometry (mm):
  - Outer footprint (on holder): 127.74 x 85.40
  - Total height: 126.5
  - Vessel cavity: Ø 23.5, depth 57.0, centered
  """
  outer_x = 127.74
  outer_y = 85.40
  outer_z = 126.5
  diameter = 23.5
  depth = 57.0
  material_z_thickness = 1.0
  vessel_z = 76.0  # measured: vessel outer base relative to pioreactor bottom

  vessel = build.resource(
    f"{name}_vessel",
    Coordinate(diameter, diameter, depth),
    kind=pb.RESOURCE_KIND_CONTAINER,
    location=Coordinate(
      x=(outer_x - diameter) / 2.0,
      y=(outer_y - diameter) / 2.0,
      z=vessel_z,
    ),
    category="bioreactor_vessel",
    container=pb.ContainerSpec(max_volume=20_000, material_z_thickness=material_z_thickness),
    state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
  )
  pioreactor = Pioreactor(
    name=name,
    size_x=outer_x,
    size_y=outer_y,
    size_z=outer_z,
    model=pioreactor_20ml.__name__,
    category="bioreactor",
    vessel=vessel,
    store=store,
  )
  await pioreactor.create_resources()
  return pioreactor
