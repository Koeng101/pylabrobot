"""BMG Labtech CLARIOstar plate reader."""

import os
from typing import Literal, Optional, Union

from pylabrobot.io.ftdi import FTDI
from pylabrobot.io.usb import USB
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

from .driver.features.absorbance import Absorbance
from .driver.features.drawer import Drawer
from .driver.features.fluorescence import Fluorescence
from .driver.features.luminescence import Luminescence
from .driver.features.temperature_controller import TemperatureController
from .driver.master import CLARIOstarDriver
from .driver.simulator import CLARIOstarSimulationDriver

# Preliminary: the nominal size, rounded to the cm, the same for the CLARIOstar
# and the CLARIOstar Plus; not yet measured.
SIZE_X = 450.0
SIZE_Y = 510.0
SIZE_Z = 400.0

# The recording a simulated CLARIOstar Plus takes its configuration from, by default.
RECORDING_CLARIOSTAR_PLUS = os.path.join(
  os.path.dirname(__file__),
  "driver",
  "recordings",
  "clariostar_plus_1_35_temperature_controller.json",
)

# The models a factory builds, as the reader reports them (INIT mainboard revision).
MODELS = ("CLARIOstar", "CLARIOstarPlus")


def clariostar_definition(
  name: str, model: str, size_x: float = SIZE_X, size_y: float = SIZE_Y, size_z: float = SIZE_Z
) -> pb.ResourceDefinition:
  """The reader's body and its plate holder, `<name>_plate_holder`, which the drawer carries."""
  plate_holder = build.resource(
    f"{name}_plate_holder",
    Coordinate(127.76, 85.48, 0),
    kind=pb.RESOURCE_KIND_PLATE_HOLDER,
    location=Coordinate.zero(),
    category="plate_holder",
    model="clariostar_plate_holder",
    type_name="PlateHolder",
    holder=pb.HolderSpec(
      child_location=build.vec3(Coordinate.zero()), pedestal_size_z=0, capacity=1
    ),
  )
  return build.resource(
    name,
    Coordinate(size_x, size_y, size_z),
    category="device",
    model=model,
    type_name="CLARIOstarDevice",
    children=[plate_holder],
  )


class CLARIOstarPlateHolder:
  """The drawer's plate holder: a plate goes on or comes off only while the drawer is sensed
  open, and only onto an empty holder. `handle` is the holder in the resource store."""

  def __init__(self, device: "CLARIOstarDevice"):
    """
    Args:
      device: the reader whose drawer carries this plate holder.
    """
    self._device = device

  @property
  def name(self) -> str:
    return f"{self._device.name}_plate_holder"

  @property
  def handle(self) -> handles.PlateHolder:
    """The plate holder in the resource store.

    Raises:
      RuntimeError: if the reader's body is not in its store yet (`CLARIOstarDevice.create_body`).
    """
    holder = self._device.driver.drawer.plate_holder
    if not isinstance(holder, handles.PlateHolder):
      raise RuntimeError(f"{self._device.name} is not in its resource store yet; call setup first")
    return holder

  def _require_drawer_open(self, action: str) -> None:
    """Raise unless the drawer was out when last sensed.

    Raises:
      RuntimeError: if the drawer has not been sensed yet, or was sensed closed.
    """
    drawer_open = self._device.drawer.drawer_open
    if drawer_open is None:
      raise RuntimeError(f"cannot {action}: the drawer has not been sensed; open it first")
    if not drawer_open:
      raise RuntimeError(f"cannot {action}: the drawer is closed; open it first")

  async def get_resource_held(self) -> Optional[handles.Resource]:
    """What the plate holder holds; None when empty."""
    return await self.handle.get_resource_held()

  async def check_can_drop_resource_here(self, resource: handles.Resource) -> None:
    """Raise unless the drawer is open and the holder is empty or already holds `resource`.

    Raises:
      RuntimeError: if the drawer is not sensed open, or the holder holds something else.
    """
    self._require_drawer_open(f"place {resource.name} on {self.name}")
    held = await self.get_resource_held()
    if held is not None and held != resource:
      raise RuntimeError(
        f"Cannot drop resource {resource.name} onto resource holder {self.name} while it already "
        "has a resource. Please remove the resource before dropping a new one."
      )

  async def assign_child_resource(
    self, resource: handles.Resource, location: Optional[Coordinate] = None
  ) -> None:
    """Place `resource`, checked as a drop is (`check_can_drop_resource_here`), at `location` or
    where the holder seats it."""
    await self.check_can_drop_resource_here(resource)
    await self.handle.assign_child_resource(resource, location=location)

  async def unassign_child_resource(self, resource: handles.Resource) -> None:
    """Take `resource` off; only while the drawer is open.

    Raises:
      RuntimeError: if the drawer is not sensed open.
      ValueError: if `resource` is not on the holder.
    """
    self._require_drawer_open(f"remove {resource.name} from {self.name}")
    await self.handle.unassign_child_resource(resource)


class CLARIOstarDevice:
  """The CLARIOstar: its body and plate holder in a resource store, its drawer, and the driver
  that runs it.

  Build one with the `CLARIOstar` or `CLARIOstarPlus` factory. ``use_io`` picks how the reader is
  wired: ``"ftdi"`` (the default) for readers with the FTDI serial bridge, ``"usb"`` for readers
  with native USB. Commands are the same on both. A given ``io`` sets it by its type.

  The body is created in the store at `setup` (or `create_body`), or found there by name: a
  reader already in the store, on a deck say, is the one used.
  """

  def __init__(
    self,
    name: str = "Generic CLARIOstar Device",
    *,
    use_io: Optional[Literal["ftdi", "usb"]] = None,
    device_id: Optional[str] = None,
    io: Optional[Union[FTDI, USB]] = None,
    size_x: float = SIZE_X,
    size_y: float = SIZE_Y,
    size_z: float = SIZE_Z,
    model: Optional[str] = None,
    declared_configuration_json: Optional[str] = None,
    simulation: bool = False,
    store: Optional[ResourceStore] = None,
  ):
    """
    Args:
      name: the name of its body in the resource store.
      use_io: ``"ftdi"`` or ``"usb"``; None takes it from ``io``, or ``"ftdi"``.
      device_id: the FTDI device id, or the USB serial number. None uses the first reader
        found.
      io: an already-built ``FTDI`` or ``USB``, used instead of building one.
      size_x: width, in mm.
      size_y: depth, in mm.
      size_z: height including the feet, in mm.
      model: which reader this is. Defaults to the class name, which says only that it is a
        CLARIOstar.
      declared_configuration_json: a file `save_configuration` wrote, passed to the driver; a
        simulated reader's configuration.
      simulation: build a simulated reader, with no link, from ``declared_configuration_json``.
      store: the resource store its body is in; None makes one in memory.

    Raises:
      ValueError: if ``simulation`` is given without ``declared_configuration_json``, or with
        ``use_io``, ``device_id`` or ``io``.
    """
    self.name = name
    self.model = model if model is not None else self.__class__.__name__
    self.size = Coordinate(size_x, size_y, size_z)
    self.store = store if store is not None else ResourceStore.in_memory()
    self.body: Optional[handles.Resource] = None
    self.driver: CLARIOstarDriver
    if simulation:
      if declared_configuration_json is None:
        raise ValueError("a simulated reader needs declared_configuration_json")
      if use_io is not None or device_id is not None or io is not None:
        raise ValueError("a simulated reader has no link: no use_io, device_id or io")
      self.driver = CLARIOstarSimulationDriver(declared_configuration_json, name=name)
    else:
      self.driver = CLARIOstarDriver(
        use_io=use_io,
        device_id=device_id,
        io=io,
        name=name,
        declared_configuration_json=declared_configuration_json,
      )
    self.plate_holder = CLARIOstarPlateHolder(self)

  def definition(self) -> pb.ResourceDefinition:
    """The reader's body and plate holder, as `create_body` creates them."""
    return clariostar_definition(self.name, self.model, self.size.x, self.size.y, self.size.z)

  async def create_body(self) -> handles.Resource:
    """Find the reader's body in its store by name, or create it there as a root; `setup` does
    this first. The drawer moves the plate holder once its in and out locations are set; neither
    is measured.

    Returns:
      the body.
    """
    if self.body is None:
      found = await self.store.find_resources(
        spb.ResourceFilter(names=[self.name], models=[self.model])
      )
      self.body = found[0] if found else await self.store.create(self.definition(), self.name)
      holder = await self.body.get_resource(self.plate_holder.name)
      self.driver.drawer.plate_holder = holder
    return self.body

  async def check_can_drop_resource_here(self, resource: handles.Resource) -> None:
    """Raise: a plate goes on the plate holder, not on the reader."""
    raise RuntimeError(
      f"cannot place {resource.name} on {self.name}: place it on {self.plate_holder.name}"
    )

  async def assign_child_resource(
    self, resource: handles.Resource, location: Optional[Coordinate] = None
  ) -> None:
    """Raise: a plate goes on the plate holder (`check_can_drop_resource_here`)."""
    await self.check_can_drop_resource_here(resource)

  @property
  def drawer(self) -> Drawer:
    """The drawer."""
    return self.driver.drawer

  @property
  def temperature_controller(self) -> Optional[TemperatureController]:
    """The temperature controller, or None if the reader has none; known after `setup`."""
    return self.driver.temperature_controller

  @property
  def absorbance(self) -> Optional[Absorbance]:
    """Absorbance measurement, or None if the reader has none; known after `setup`."""
    return self.driver.absorbance

  @property
  def fluorescence(self) -> Optional[Fluorescence]:
    """Fluorescence measurement, or None if the reader has none; known after `setup`."""
    return self.driver.fluorescence

  @property
  def luminescence(self) -> Optional[Luminescence]:
    """Luminescence measurement, or None if the reader has none; known after `setup`."""
    return self.driver.luminescence

  async def setup(self) -> None:
    """Find or create the body in the store, connect, initialize the reader (about 13 s), and
    check it is the model this device is.

    Raises:
      RuntimeError: if the reader reports another model than the factory built.
    """
    await self.create_body()
    await self.driver.setup()
    reported = self.driver.configuration.model
    if self.model in MODELS and reported is not None and reported != self.model:
      raise RuntimeError(f"{self.name} was built as a {self.model}, the reader is a {reported}")

  async def stop(self, accept_plate_left_in_device: bool = False) -> None:
    """Stop a running measurement, switch heating off, close the drawer, and disconnect.

    Raises:
      RuntimeError: if a plate is still in the reader, unless `accept_plate_left_in_device`; the
        drawer is opened and the reader stays connected.
    """
    await self.driver.stop(accept_plate_left_in_device=accept_plate_left_in_device)


def CLARIOstar(
  name: str = "CLARIOstar",
  *,
  use_io: Optional[Literal["ftdi", "usb"]] = None,
  device_id: Optional[str] = None,
  io: Optional[Union[FTDI, USB]] = None,
  size_x: float = SIZE_X,
  size_y: float = SIZE_Y,
  size_z: float = SIZE_Z,
  declared_configuration_json: Optional[str] = None,
  simulation: bool = False,
  store: Optional[ResourceStore] = None,
) -> CLARIOstarDevice:
  """A CLARIOstar. No recording of one exists, so simulating one needs a declared configuration."""
  return CLARIOstarDevice(
    name=name,
    use_io=use_io,
    device_id=device_id,
    io=io,
    size_x=size_x,
    size_y=size_y,
    size_z=size_z,
    model=CLARIOstar.__name__,
    declared_configuration_json=declared_configuration_json,
    simulation=simulation,
    store=store,
  )


def CLARIOstarPlus(
  name: str = "CLARIOstarPlus",
  *,
  use_io: Optional[Literal["ftdi", "usb"]] = None,
  device_id: Optional[str] = None,
  io: Optional[Union[FTDI, USB]] = None,
  size_x: float = SIZE_X,
  size_y: float = SIZE_Y,
  size_z: float = SIZE_Z,
  declared_configuration_json: Optional[str] = None,
  simulation: bool = False,
  store: Optional[ResourceStore] = None,
) -> CLARIOstarDevice:
  """A CLARIOstar Plus. Simulated, it defaults to ``RECORDING_CLARIOSTAR_PLUS``."""
  if simulation and declared_configuration_json is None:
    declared_configuration_json = RECORDING_CLARIOSTAR_PLUS
  return CLARIOstarDevice(
    name=name,
    use_io=use_io,
    device_id=device_id,
    io=io,
    size_x=size_x,
    size_y=size_y,
    size_z=size_z,
    model=CLARIOstarPlus.__name__,
    declared_configuration_json=declared_configuration_json,
    simulation=simulation,
    store=store,
  )
