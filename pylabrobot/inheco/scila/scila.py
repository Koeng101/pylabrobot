import logging
from typing import Any, Dict, Literal, Optional

from pylabrobot.inheco.transport.sila import InhecoSiLAInterface, get_params
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

logger = logging.getLogger(__name__)


DrawerStatus = Literal["Opened", "Closed"]


class SCILADrawerLoadingTray:
  """One of the SCILA's four drawers: a loading tray that opens and closes.

  Its holder in the SCILA's store is `resource`, there once the SCILA's resources are made.
  """

  def __init__(
    self,
    scila: "SCILA",
    drawer_id: int,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    child_location: Coordinate = Coordinate.zero(),
    category: str = "loading_tray",
    model: Optional[str] = None,
  ):
    if drawer_id not in {1, 2, 3, 4}:
      raise ValueError(f"Invalid drawer ID: {drawer_id}. Must be 1, 2, 3, or 4.")
    self.name = name
    self.size = Coordinate(size_x, size_y, size_z)
    self.child_location = child_location
    self.category = category
    self.model = model
    self._scila = scila
    self._drawer_id = drawer_id
    self._resource: Optional[handles.ResourceHolder] = None

  def definition(self, location: Coordinate) -> pb.ResourceDefinition:
    """The drawer's holder, at `location` in the SCILA's body."""
    return build.resource(
      self.name,
      self.size,
      kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
      location=location,
      category=self.category,
      model=self.model or "",
      type_name="SCILADrawerLoadingTray",
      holder=pb.HolderSpec(child_location=build.vec3(self.child_location)),
    )

  @property
  def resource(self) -> handles.ResourceHolder:
    """The drawer's holder in the store.

    Raises:
      RuntimeError: The SCILA's resources are not made yet: call `SCILA.setup` first.
    """
    if self._resource is None:
      raise RuntimeError(f"'{self.name}' is not in a store yet; set the SCILA up first")
    return self._resource

  async def assign_child_resource(
    self, resource: handles.Resource, location: Optional[Coordinate] = None
  ) -> None:
    """Put a resource in the drawer, as a person loading it does."""
    await self.resource.assign_child_resource(resource, location=location)

  async def get_resource_held(self) -> Optional[handles.Resource]:
    """What the drawer holds; None when it is empty."""
    return await self.resource.get_resource_held()

  async def open(self):
    await self._scila.send_command("PrepareForInput", position=self._drawer_id)
    try:
      await self._scila.send_command("OpenDoor")
    except RuntimeError as e:
      self._handle_warning("open", e)

  async def close(self):
    await self._scila.send_command("PrepareForOutput", position=self._drawer_id)
    try:
      await self._scila.send_command("CloseDoor")
    except RuntimeError as e:
      self._handle_warning("close", e)

  def _handle_warning(self, action: str, e: RuntimeError) -> None:
    if "warning" not in str(e).lower():
      raise e
    # SCILA emits a non-fatal CO2-flow warning when the gas mixer is absent or unhealthy.
    # When the user has declared no gas mixer is connected, silence it; otherwise surface
    # the warning so a real CO2 problem isn't hidden.
    if self._scila.gas_mixer_connected:
      logger.warning("drawer %d %s: %s", self._drawer_id, action, e)


class SCILA:
  """Inheco SCILA incubator: four drawers and temperature control, over SiLA.

  Owns the SiLA HTTP/SOAP connection and exposes the device's operations directly. Its body and
  its four drawers are resources in `store`; `setup` makes them there, or finds them when they
  are already there.

  Example:
    >>> from pylabrobot.inheco.scila import SCILA
    >>> scila = SCILA(name="scila", scila_ip="169.254.1.117")
    >>> await scila.setup()
    >>> await scila.set_temperature(37.0)
    >>> await scila.drawers[2].open()
  """

  def __init__(
    self,
    name: str,
    scila_ip: str,
    client_ip: Optional[str] = None,
    gas_mixer_connected: bool = True,
    size_x: float = 0.0,  # TODO: measure
    size_y: float = 0.0,  # TODO: measure
    size_z: float = 0.0,  # TODO: measure
    store: Optional[ResourceStore] = None,
  ):
    """
    Args:
      name: The name of the SCILA's body in the store; its drawers are `{name}_drawer_{id}`.
      scila_ip: The SCILA's IP address.
      client_ip: The local IP address the SCILA sends events to.
      gas_mixer_connected: Whether a gas mixer is connected; without one, CO2-flow warnings are
        not logged.
      size_x: Body width in millimeters.
      size_y: Body depth in millimeters.
      size_z: Body height in millimeters.
      store: The resource store its body and drawers are in; a new in-memory store by default.
    """
    self.name = name
    self.size = Coordinate(size_x, size_y, size_z)
    self.store = store or ResourceStore.in_memory()
    self._sila_interface = InhecoSiLAInterface(client_ip=client_ip, machine_ip=scila_ip)
    self.gas_mixer_connected = gas_mixer_connected
    self._body: Optional[handles.Resource] = None

    self.drawers: Dict[int, SCILADrawerLoadingTray] = {}
    for drawer_id in range(1, 5):
      self.drawers[drawer_id] = SCILADrawerLoadingTray(
        scila=self,
        drawer_id=drawer_id,
        name=f"{name}_drawer_{drawer_id}",
        size_x=0.0,  # TODO: measure
        size_y=0.0,  # TODO: measure
        size_z=0.0,  # TODO: measure
        child_location=Coordinate.zero(),  # TODO: measure
      )

  # -- resources --

  def definition(self) -> pb.ResourceDefinition:
    """The SCILA's body with its four drawers."""
    return build.resource(
      self.name,
      self.size,
      model="Inheco SCILA",
      type_name="SCILA",
      children=[
        drawer.definition(location=Coordinate.zero())  # TODO: measure
        for drawer in self.drawers.values()
      ],
    )

  @property
  def body(self) -> handles.Resource:
    """The SCILA's body in the store.

    Raises:
      RuntimeError: Its resources are not made yet: call `setup` first.
    """
    if self._body is None:
      raise RuntimeError(f"'{self.name}' is not in a store yet; call setup() first")
    return self._body

  async def create_resources(self) -> handles.Resource:
    """Make the SCILA's body and drawers in its store, or find them there by name.

    Called by `setup`. Place the body on a deck by assigning it: `deck.assign_child_resource`.
    """
    found = await self.store.find_resources(
      spb.ResourceFilter(names=[self.name], type_names=["SCILA"])
    )
    body = found[0] if found else await self.store.create(self.definition(), name=self.name)
    response = await self.store.commands.get_resources(
      spb.GetResourcesRequest(resources=[body.ref], depth=1)
    )
    held = await self.store.make_handles(
      [node for node in response.nodes if node.parent_id == body.id]
    )
    by_name = {handle.name: handle for handle in held}
    for drawer in self.drawers.values():
      holder = by_name.get(drawer.name)
      if not isinstance(holder, handles.ResourceHolder):
        raise RuntimeError(f"'{self.name}' in the store has no drawer '{drawer.name}'")
      drawer._resource = holder
    self._body = body
    return body

  # -- lifecycle --

  async def setup(self) -> None:
    await self.create_resources()
    await self._sila_interface.setup()
    await self._reset_and_initialize()
    logger.info("[SCILA %s] connected", self._sila_interface.machine_ip)

  async def stop(self) -> None:
    await self._sila_interface.close()
    logger.info("[SCILA %s] connection closed", self._sila_interface.machine_ip)

  async def send_command(self, command: str, **kwargs) -> Any:
    """Send a SiLA command and return the parsed response."""
    return await self._sila_interface.send_command(command, **kwargs)

  async def _reset_and_initialize(self) -> None:
    event_uri = f"http://{self._sila_interface.client_ip}:{self._sila_interface.bound_port}/"
    await self.send_command(
      command="Reset", deviceId="MyController", eventReceiverURI=event_uri, simulationMode=False
    )
    await self.send_command("Initialize")

  # -- status queries --

  async def request_status(self) -> str:
    resp = await self.send_command("GetStatus")
    return resp.get("GetStatusResponse", {}).get("state", "Unknown")  # type: ignore

  async def request_liquid_level(self) -> str:
    root = await self.send_command("GetLiquidLevel")
    return get_params(root, ["LiquidLevel"])["LiquidLevel"]  # type: ignore

  # -- drawers --

  async def request_drawer_statuses(self) -> Dict[int, DrawerStatus]:
    root = await self.send_command("GetDoorStatus")
    params = get_params(root, ["Drawer1", "Drawer2", "Drawer3", "Drawer4"])
    return {i: params[f"Drawer{i}"] for i in range(1, 5)}  # type: ignore

  async def request_drawer_status(self, drawer_id: int) -> DrawerStatus:
    if drawer_id not in {1, 2, 3, 4}:
      raise ValueError(f"Invalid drawer ID: {drawer_id}. Must be 1, 2, 3, or 4.")
    positions = await self.request_drawer_statuses()
    return positions[drawer_id]

  # -- CO2 / valves --

  async def request_co2_flow_status(self) -> str:
    root = await self.send_command("GetCO2FlowStatus")
    return get_params(root, ["CO2FlowStatus"])["CO2FlowStatus"]  # type: ignore

  async def request_valve_status(self) -> dict[str, str]:
    root = await self.send_command("GetValveStatus")
    return get_params(root, ["H2O", "CO2 Normal", "CO2 Boost"])  # type: ignore

  # -- temperature control --

  @property
  def supports_active_cooling(self) -> bool:
    return False

  async def request_temperature_information(self) -> dict[str, Any]:
    root = await self.send_command("GetTemperature")
    return get_params(root, ["CurrentTemperature", "TargetTemperature", "TemperatureControl"])  # type: ignore

  async def set_temperature(self, temperature: float) -> None:
    logger.info(
      "[SCILA %s] set temperature: target=%.1f C",
      self._sila_interface.machine_ip,
      temperature,
    )
    await self.send_command(
      "SetTemperature", targetTemperature=temperature, temperatureControl=True
    )

  async def request_current_temperature(self) -> float:
    temp: float = (await self.request_temperature_information())["CurrentTemperature"]  # type: ignore[index]
    logger.info("[SCILA %s] read temperature: actual=%.1f C", self._sila_interface.machine_ip, temp)
    return temp

  async def deactivate(self) -> None:
    logger.info("[SCILA %s] deactivate temperature control", self._sila_interface.machine_ip)
    await self.send_command("SetTemperature", temperatureControl=False)

  async def request_target_temperature(self) -> float:
    return (await self.request_temperature_information())["TargetTemperature"]  # type: ignore

  async def is_temperature_control_enabled(self) -> bool:
    return (await self.request_temperature_information())["TemperatureControl"]  # type: ignore

  # -- serialization --

  def serialize(self) -> dict[str, Any]:
    return {
      "type": "SCILA",
      "name": self.name,
      "size_x": self.size.x,
      "size_y": self.size.y,
      "size_z": self.size.z,
      "scila_ip": self._sila_interface.machine_ip,
      "client_ip": self._sila_interface.client_ip,
      "gas_mixer_connected": self.gas_mixer_connected,
    }
