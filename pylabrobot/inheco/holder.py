from typing import Optional

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

from .control_box import InhecoTECControlBox
from .temperature_controller import InhecoTemperatureController


class InhecoHolder(InhecoTemperatureController):
  """An Inheco device addressed by index on a control box whose body holds one plate.

  Its body is a resource holder in a resource store: `create_body` makes it there, or finds it by
  name. The store refuses a second plate while it holds one.

  Attributes:
    name: Its body's name.
    definition: Its body, as it is created in the store.
    store: The store its body is in.
    body: Its body in the store, once created or found.
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
    self.body: Optional[handles.ResourceHolder] = None

  async def create_body(self) -> handles.ResourceHolder:
    """Its body in the store: the resource holder of its name if the store has one, else made from
    its definition as a root, to be placed by assigning it."""
    if self.body is None:
      found = await self.store.find_resources(
        spb.ResourceFilter(kinds=[pb.RESOURCE_KIND_RESOURCE_HOLDER], names=[self.name])
      )
      body = found[0] if found else await self.store.create(self.definition, name=self.name)
      assert isinstance(body, handles.ResourceHolder)
      self.body = body
    return self.body

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
    body = await self.create_body()
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
      raise ValueError(str(error)) from error

  async def unassign_child_resource(self, resource: handles.Resource) -> None:
    """Take a plate off it.

    Raises:
      ValueError: It does not hold `resource`.
    """
    body = await self.create_body()
    await body.unassign_child_resource(resource)

  async def get_resource(self) -> Optional[handles.Resource]:
    """The plate it holds; unset when it holds none."""
    body = await self.create_body()
    return await body.get_resource_held()

  async def set_resource(self, resource: Optional[handles.Resource]) -> None:
    """Hold `resource`, refused while it holds another; unset takes off what it holds."""
    if resource is None:
      held = await self.get_resource()
      if held is not None:
        await self.unassign_child_resource(held)
      return
    await self.assign_child_resource(resource, reassign=False)
