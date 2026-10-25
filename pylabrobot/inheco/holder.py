from typing import Optional, TypeVar

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, devices, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError, plr_error
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

from .control_box import InhecoTECControlBox
from .temperature_controller import InhecoTemperatureController


class InhecoHolder(InhecoTemperatureController):
  """An Inheco device addressed by index on a control box whose body holds one plate.

  Its body is a resource holder in a resource store: `create_resources` finds it there by name, or
  creates it when the store has none; `get_resources` only finds it. The store refuses a second
  plate while it holds one.

  Attributes:
    name: Its body's name.
    definition: Its body, as it is created in the store.
    store: The store its body is in.
  """

  def __init__(
    self,
    index: int,
    control_box: InhecoTECControlBox,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    child_location: Coordinate,
    category: str,
    model: Optional[str] = None,
    store: Optional[ResourceStore] = None,
  ):
    InhecoTemperatureController.__init__(self, index=index, interface=control_box)
    self.name = name
    self.definition = build.resource(
      name,
      Coordinate(size_x, size_y, size_z),
      kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
      category=category,
      model=model or "",
      holder=pb.HolderSpec(child_location=build.vec3(child_location), capacity=1),
    )
    self.store = store or ResourceStore.in_memory()
    self._body: Optional[handles.ResourceHolder] = None

  @property
  def body(self) -> handles.ResourceHolder:
    """Its body in the store.

    Raises:
      RuntimeError: It is not found or created yet: call `create_resources` first.
    """
    if self._body is None:
      raise devices.not_in_store(self.name)
    return self._body

  async def _find_resources(self, create: bool) -> handles.ResourceHolder:
    if self._body is None:
      body = await devices.find_or_create(self.store, self.definition, create=create)
      assert isinstance(body, handles.ResourceHolder)
      self._body = body
    return self._body

  async def create_resources(self) -> handles.ResourceHolder:
    """Its body in the store: the resource holder of its name if the store has one, else made from
    its definition as a root, to be placed by assigning it."""
    return await self._find_resources(create=True)

  async def get_resources(self) -> handles.ResourceHolder:
    """Its body, found in the store by name; never created.

    Raises:
      LookupError: The store has no resource holder of its name.
    """
    return await self._find_resources(create=False)

  async def assign_child_resource(
    self,
    resource: handles.Resource,
    location: Optional[Coordinate] = None,
    reassign: bool = True,
  ) -> None:
    """Put a plate onto it, at its child location unless given one.

    Args:
      resource: The plate.
      location: Where, relative to its body; unset seats it on the child location.
      reassign: If False, refuse while it holds a plate, or when `resource` is in something.

    Raises:
      ValueError: It refuses the plate.
    """
    body = await self.create_resources()
    if not reassign:
      response = await self.store.commands.get_resources(
        spb.GetResourcesRequest(resources=[body.ref, resource.ref], depth=0)
      )
      held, child = response.nodes[0], response.nodes[-1]
      if held.child_ids:
        raise ValueError("ResourceHolders can only take one child at a time.")
      if child.parent_id:
        raise ValueError(f"Will not assign resource '{resource.name}' that already has a parent.")
    try:
      await body.assign_child_resource(resource, location=location)
    except StoreError as error:
      raise plr_error(error, otherwise=ValueError) from error

  async def unassign_child_resource(self, resource: handles.Resource) -> None:
    """Take a plate off it.

    Raises:
      ValueError: It does not hold `resource`.
    """
    body = await self.create_resources()
    await body.unassign_child_resource(resource)

  async def get_resource(self) -> Optional[handles.Resource]:
    """The plate it holds; unset when it holds none."""
    body = await self.create_resources()
    return await body.get_resource_held()

  async def set_resource(self, resource: Optional[handles.Resource]) -> None:
    """Hold `resource`, refused while it holds another; unset takes off what it holds."""
    if resource is None:
      held = await self.get_resource()
      if held is not None:
        await self.unassign_child_resource(held)
      return
    await self.assign_child_resource(resource, reassign=False)


H = TypeVar("H", bound=InhecoHolder)


async def created(holder: H) -> H:
  """`holder`, once its body is found in its store, or created there."""
  await holder.create_resources()
  return holder
