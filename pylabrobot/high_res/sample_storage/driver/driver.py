import asyncio
import logging
import random
from dataclasses import dataclass
from typing import (
  Any,
  Awaitable,
  Callable,
  Dict,
  List,
  Literal,
  Mapping,
  Optional,
  Sequence,
  Set,
  Tuple,
  Union,
  cast,
)

from pylabrobot.events import (
  ResourceReference,
  event_operation,
  handle_reference,
  is_event_bus_active,
)
from pylabrobot.io.socket import Socket
from pylabrobot.resources.barcode import Barcode
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import ResourceNotFoundError
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

from ..stackers import high_res_stacker, plate_holder
from . import tree_events
from .environment import EnvironmentControl
from .errors import (
  HighResSampleStorageAbortedError,
  HighResSampleStorageError,
  HighResSampleStorageFault,
  HighResSampleStorageProtocolError,
  NoFreeSiteError,
  PlateNotFoundError,
  left_unsafe,
)
from .models import ModelInfo, get_model_info
from .protocol import (
  ACK_TOKEN,
  COMPLETION_ABORTED,
  COMPLETION_ERROR,
  COMPLETION_OK,
  COMPLETION_TOKENS,
  parse_kv,
)
from .serialization import (
  definition_from_nodes,
  definition_from_serialized,
  serialize_definition,
  without_children,
)
from .settings import HighResSampleStorageSettings
from .types import (
  DOOR_STATES,
  NEST_STATES,
  DoorState,
  EnvironmentParameter,
  NestState,
  StackerDimensions,
  VersionInfo,
)

logger = logging.getLogger(__name__)

K = pb.ResourceKind

# The transfer nests the device reports are modeled as plate holders of this size.
_NEST_SIZE = Coordinate(127.76, 85.48, 0)


@dataclass(frozen=True)
class UnresolvedPlateTransfer:
  """A plate move whose physical result and PLR state are not reconciled.

  The resource store keeps the plate at its last confirmed location until
  :meth:`HighResSampleStorage.resolve_unresolved_transfer` reconciles it.
  """

  plate: handles.Plate
  source: handles.PlateHolder
  destination: handles.PlateHolder
  command: str
  error_type: str
  error_message: str


def _drop_refusal(resource_name: str, holder_name: str) -> RuntimeError:
  return RuntimeError(
    f"Cannot drop resource {resource_name} onto resource holder {holder_name} while it already "
    "has a resource. Please remove the resource before dropping a new one."
  )


class HighResSampleStorage:
  """Base device for HighRes Biosolutions sample stores.

  The TundraStore, SteriStore and AmbiStore are the same machine family behind a
  shared port-1000 API, so all of the implementation lives here and the concrete
  devices are thin subclasses. Each rack is a *stacker* (a vertical column of
  plate slots); plates enter and leave through one of the device's *nests*
  (transfer stations). Fetch and store operations address a particular nest
  with a 0-based ``tray_index``.

  The store's racks and nests are resources in a resource store: :attr:`body` is
  the device in the store, holding one plate carrier per stacker (its sites are
  the stacker's slots) and one plate holder per nest. ``setup()`` creates the
  body, or finds it by name when the store already holds it.

  If a plate move is interrupted without a definitive outcome, the driver
  exposes it through :attr:`unresolved_transfer` and blocks further plate moves,
  homing, and barcode scans until :meth:`resolve_unresolved_transfer` reconciles
  the physical and modeled locations. :meth:`recover` remains available to park an
  unsafe mechanism before reconciliation.

  Subclasses set :attr:`_model_name`; callers can override it with ``model``.
  This configured model selects model-specific behavior. The product name
  reported by the device is logged during setup but is not used as configuration.

  The store exposes a text-based remote-control server over TCP, port 1000.
  Commands are case-sensitive, space-separated, terminated with ``\\r\\n``. Each
  command is answered with an ``ACK!`` echo, optional data lines, then exactly
  one completion line (``OK!`` / ``ABORTED!`` / ``ERROR!``). See the User
  Manual, section "Message Formatting".
  """

  _model_name = "HighResSampleStorage"
  _verification_warning: Optional[str] = None

  def __init__(
    self,
    host: str,
    name: str,
    racks: Optional[Mapping[int, pb.ResourceDefinition]] = None,
    size_x: float = 0,
    size_y: float = 0,
    size_z: float = 0,
    rotation: Optional[Rotation] = None,
    category: Optional[str] = "plate_store",
    model: Optional[str] = None,
    port: int = 1000,
    read_timeout: float = 30.0,
    motion_timeout: float = 240.0,
    nests: Optional[Sequence[pb.ResourceDefinition]] = None,
    barcode: Optional[Barcode] = None,
    preferred_pickup_location: Optional[Coordinate] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    store: Optional[ResourceStore] = None,
    rack_spots: Optional[Mapping[int, Sequence[int]]] = None,
  ) -> None:
    """Create a HighRes sample-store driver and configure its TCP transport.

    Args:
      host: IP address of the store. The factory default is ``192.168.127.60``;
        all HighRes devices also answer on the backdoor ``10.253.253.253``.
      name: The name of the device's body in the resource store.
      racks: Mapping of physical stacker numbers to stacker definitions: plate
        carriers whose sites are the stacker's slots (see :func:`high_res_stacker`).
        When omitted, ``setup()`` reads the configured dimensions from the device and
        creates empty stackers. Passing an empty mapping explicitly configures no
        stackers and disables discovery.
      size_x: The body's size in x.
      size_y: The body's size in y.
      size_z: The body's size in z.
      rotation: The body's rotation.
      category: The body's category.
      port: Remote-control server port (always 1000).
      read_timeout: Timeout (s) for query/status commands.
      motion_timeout: Timeout (s) for long-running motion commands
        (``home``, ``pick``, ``place``, door moves).
      model: Model used for model-specific behavior. Defaults to the concrete
        class's model and is never replaced with the device-reported product name.
      nests: Transfer-nest definitions when restoring serialized state.
      barcode: Optional barcode identifying the store's body.
      preferred_pickup_location: Optional gripper pickup coordinate for the body.
      metadata: Free-form metadata of the body.
      store: The resource store the body is in; a new in-memory store when omitted.
      rack_spots: For a rack whose sites are not spots 0, 1, 2..., each site's
        zero-based spot, in the order of the rack's sites, by stacker number. A
        site's slot on the device is its spot plus one.
    """
    configured_model = model if model is not None else self._model_name
    model_info = get_model_info(configured_model)
    self.name = name
    self.model = configured_model
    self.store = store if store is not None else ResourceStore.in_memory()
    self.body: Optional[handles.Resource] = None
    self._size = Coordinate(size_x, size_y, size_z)
    self._rotation = rotation
    self._category = category
    self._barcode = barcode
    self._preferred_pickup_location = preferred_pickup_location
    self._metadata = dict(metadata) if metadata else None

    # The device reports its configured nest numbers during setup. Their
    # robot-facing coordinates are intentionally undefined relative to the
    # store, so the nests are in the body without locations.
    self.nests: List[handles.PlateHolder] = []
    self._nest_definitions: List[pb.ResourceDefinition] = list(nests or [])
    # Nests given at construction come before the racks in the body; nests read from the device
    # come after them.
    self._nests_restored = bool(self._nest_definitions)

    self._rack_definitions: Dict[int, pb.ResourceDefinition] = {}
    self._rack_spots: Dict[int, List[int]] = {}
    self._racks_by_number: Dict[int, handles.Carrier] = {}
    # Each slot of a configured rack, by the id of its site: (stacker, slot).
    self._slots: Dict[bytes, Tuple[int, int]] = {}
    # Stackers read from the device, whose creation is reported as PLR builds them.
    self._discovered: Set[int] = set()
    self._racks_loaded = racks is not None
    if racks is not None:
      for stacker in racks:
        self._validate_stacker_number(stacker)
      for stacker in sorted(racks):
        self._add_rack(racks[stacker], stacker, (rack_spots or {}).get(stacker))

    # Slide (Y) and lift (Z) positions near zero are retracted. Faulted moves
    # can leave either axis extended even when firmware still reports homed.
    self._retracted_y_max = 50.0
    self._retracted_z_max = 50.0

    self._model_info = model_info
    if self._model_info.has_environment_control:
      self.environment = EnvironmentControl(driver=self)

    self.io = Socket(
      human_readable_device_name="HighRes sample store",
      host=host,
      port=port,
      read_timeout=read_timeout,
      write_timeout=read_timeout,
    )
    self._host = host
    self._port = port
    self._read_timeout = read_timeout
    self._motion_timeout = motion_timeout
    self._transport_invalidated = False
    self._command_lock = asyncio.Lock()
    # A command lock prevents protocol responses from interleaving, but a plate
    # transfer also includes resource validation and bookkeeping on either side
    # of the hardware command. Keep that entire transaction atomic.
    self._transfer_lock = asyncio.Lock()
    self._unresolved_transfer: Optional[UnresolvedPlateTransfer] = None

  @property
  def read_timeout(self) -> float:
    return self._read_timeout

  @property
  def motion_timeout(self) -> float:
    return self._motion_timeout

  @property
  def model_info(self) -> ModelInfo:
    return self._model_info

  @property
  def unresolved_transfer(self) -> Optional[UnresolvedPlateTransfer]:
    """The plate move whose physical outcome must be reconciled, if any."""
    return self._unresolved_transfer

  # --- the body in the resource store -----------------------------------------

  def _body_attributes(self) -> pb.ResourceAttributes:
    """What the body is, without its racks and nests."""
    attributes = build.resource(
      self.name,
      self._size,
      rotation=self._rotation,
      category=self._category or "",
      model=self.model,
      type_name=type(self).__name__,
      metadata=self._metadata,
    ).attributes
    if self._barcode is not None:
      attributes.barcode.CopyFrom(
        pb.Barcode(
          data=self._barcode.data,
          symbology=self._barcode.symbology,
          position_on_resource=self._barcode.position_on_resource,
        )
      )
    if self._preferred_pickup_location is not None:
      attributes.preferred_pickup_location.CopyFrom(build.vec3(self._preferred_pickup_location))
    return attributes

  def _body_definition(self) -> pb.ResourceDefinition:
    """The body with its racks and nests, as setup creates it."""
    racks = list(self._rack_definitions.values())
    nests = self._nest_definitions
    children = nests + racks if self._nests_restored else racks + nests
    return pb.ResourceDefinition(attributes=self._body_attributes(), children=children)

  async def _create_body(self, restoring: bool = False) -> None:
    """Create the body with its racks and nests, and report what was assigned as PLR would.

    Args:
      restoring: Report it as `deserialize` builds it, rather than as setup does.
    """
    definition = self._body_definition()
    response = await self.store.commands.create_resources(
      spb.CreateResourcesRequest(
        lock_tokens=self.store.lock_tokens,
        resources=[spb.CreateResource(definition=definition, name=self.name)],
      )
    )
    await self._attach_body(response.nodes)

    attributes = definition.attributes
    if restoring:
      for rack in self._rack_definitions.values():
        tree_events.emit_built(rack)
      for nest in self._nest_definitions:
        tree_events.emit_built(nest)
      for nest in self._nest_definitions:
        tree_events.emit_attached(nest, attributes)
      for rack in self._rack_definitions.values():
        tree_events.emit_attached(rack, attributes)
      return
    for stacker in sorted(self._discovered):
      tree_events.emit_built(self._rack_definitions[stacker])
      tree_events.emit_attached(self._rack_definitions[stacker], attributes)
    if not self._nests_restored:
      for nest in self._nest_definitions:
        tree_events.emit_attached(nest, attributes)

  async def _find_body(self) -> bool:
    """Find the body in the store by name, with its racks and nests: a device reconnecting.
    Whether it was there."""
    response = await self.store.commands.find_resources(
      spb.FindResourcesRequest(
        filter=spb.ResourceFilter(names=[self.name], type_names=[type(self).__name__])
      )
    )
    if not response.nodes:
      return False
    nodes = await self.store.commands.get_resources(
      spb.GetResourcesRequest(resources=[pb.ResourceRef(id=response.nodes[0].id)], depth=2)
    )
    await self._attach_body(nodes.nodes)
    return True

  async def _attach_body(self, nodes: Sequence[pb.ResourceNode]) -> None:
    """Hold handles to the body, its racks and its nests, from the body's nodes, body first."""
    body_node = nodes[0]
    children = [node for node in nodes if node.parent_id == body_node.id]
    made = await self.store.make_handles([body_node, *children], nodes)
    body, parts = made[0], made[1:]
    by_name = {part.name: part for part in parts}
    racks: Dict[int, handles.Carrier] = {}
    for stacker, definition in self._rack_definitions.items():
      rack = by_name.get(definition.attributes.name)
      if not isinstance(rack, handles.Carrier):
        raise RuntimeError(
          f"'{self.name}' in the resource store holds no stacker "
          f"'{definition.attributes.name}' for stacker {stacker}."
        )
      racks[stacker] = rack
    self.body = body
    self._racks_by_number = racks
    self.nests = [part for part in parts if isinstance(part, handles.PlateHolder)]
    self._slots = {}
    for stacker, rack in racks.items():
      spots = self._rack_spots.get(stacker, list(range(rack.capacity)))
      for site, spot in zip(rack.sites, spots):
        # PLR carrier spots are zero-based; HighRes stacker slots are one-based.
        self._slots[site.id] = (stacker, spot + 1)

  async def _device_reference(self) -> Optional[ResourceReference]:
    """The body as events refer to the device."""
    if self.body is not None:
      return await handle_reference(self.body)
    return tree_events.reference(self._body_attributes())

  async def _operation_data(
    self,
    plate: handles.Resource,
    source: handles.Resource,
    destination: handles.Resource,
  ) -> Dict[str, Any]:
    """What a plate move's operation events carry; nothing when no one listens."""
    if not is_event_bus_active():
      return {}
    return {
      "device": await self._device_reference(),
      "resources": [await handle_reference(plate)],
      "source": await handle_reference(source),
      "destination": await handle_reference(destination),
    }

  async def serialize(self) -> dict:
    """Serialize the connection configuration and modeled inventory.

    An unresolved transfer cannot be serialized safely because restoring only
    the last confirmed resource assignment would discard the recovery block.
    """
    self._require_no_unresolved_transfer()
    parent_name: Optional[str] = None
    if self.body is None:
      definition = self._body_definition()
    else:
      response = await self.store.commands.get_resources(
        spb.GetResourcesRequest(resources=[self.body.ref], depth=-1, ancestors=True)
      )
      definition = definition_from_nodes(self.body.id, response.nodes)
      body_node = next(node for node in response.nodes if node.id == self.body.id)
      parent = next((node for node in response.nodes if node.id == body_node.parent_id), None)
      parent_name = parent.attributes.name if parent is not None else None
    children = {child.attributes.name: child for child in definition.children}
    rack_names = {stacker: rack.attributes.name for stacker, rack in self._rack_definitions.items()}
    nest_names = (
      [nest.name for nest in self.nests]
      if self.body is not None
      else [nest.attributes.name for nest in self._nest_definitions]
    )
    # These fields preserve physical stacker numbers and transfer-nest ordering.
    return {
      **serialize_definition(without_children(definition), parent_name),
      "host": self._host,
      "port": self._port,
      "read_timeout": self.read_timeout,
      "motion_timeout": self.motion_timeout,
      "racks": {
        str(stacker): serialize_definition(children[name], self.name)
        for stacker, name in rack_names.items()
      },
      "nests": [serialize_definition(children[name], self.name) for name in nest_names],
    }

  @classmethod
  async def deserialize(
    cls, data: dict, store: Optional[ResourceStore] = None
  ) -> "HighResSampleStorage":
    """Restore a sample store and its modeled racks and transfer nests.

    A store serialized after setup is restored with its body in the resource store, as setup
    left it; one serialized before setup is restored as it was constructed.

    Args:
      data: What :meth:`serialize` returned.
      store: The resource store to restore the body in; a new in-memory store when omitted.
    """
    racks_data = cast(Dict[str, dict], data.get("racks", {}))
    barcode_data = cast(Optional[dict], data.get("barcode"))
    rotation_data = cast(Optional[dict], data.get("rotation"))
    location_data = cast(Optional[dict], data.get("preferred_pickup_location"))
    nests = [definition_from_serialized(nest) for nest in cast(List[dict], data.get("nests", []))]
    device = cls(
      host=cast(str, data["host"]),
      name=cast(str, data["name"]),
      racks={
        int(stacker): definition_from_serialized(rack_data)
        for stacker, rack_data in racks_data.items()
      },
      size_x=cast(float, data.get("size_x", 0)),
      size_y=cast(float, data.get("size_y", 0)),
      size_z=cast(float, data.get("size_z", 0)),
      rotation=(
        Rotation(rotation_data["x"], rotation_data["y"], rotation_data["z"])
        if rotation_data is not None
        else None
      ),
      category=cast(Optional[str], data.get("category")),
      model=cast(Optional[str], data.get("model")),
      port=cast(int, data.get("port", 1000)),
      read_timeout=cast(float, data.get("read_timeout", 30.0)),
      motion_timeout=cast(float, data.get("motion_timeout", 240.0)),
      nests=nests,
      barcode=(
        Barcode(
          data=barcode_data["data"],
          symbology=barcode_data["symbology"],
          position_on_resource=barcode_data["position_on_resource"],
        )
        if barcode_data is not None
        else None
      ),
      preferred_pickup_location=(
        Coordinate(location_data["x"], location_data["y"], location_data["z"])
        if location_data is not None
        else None
      ),
      metadata=cast(Optional[Mapping[str, Any]], data.get("metadata")),
      store=store,
    )
    if nests:
      await device._create_body(restoring=True)
    return device

  # --- lifecycle ------------------------------------------------------------

  async def setup(self, home: bool = False) -> None:
    if self._verification_warning is not None:
      logger.warning("%s", self._verification_warning)
    await self.io.setup()
    self._transport_invalidated = False
    try:
      await self._setup_connected(home=home)
    except BaseException:
      self._transport_invalidated = True
      await self.io.stop()
      raise

  async def _setup_connected(self, home: bool) -> None:
    version = await self.request_version()
    logger.info(
      "Connected to %s (serial %s, firmware %s)",
      version.product_name,
      version.serial_number,
      version.firmware_version,
    )

    if not self._racks_loaded:
      await self._load_racks_from_device()

    if self._model_info.has_environment_control:
      await self.environment.refresh()

    nest_status = await self.request_nest_status()
    if not nest_status:
      raise RuntimeError("The sample store did not report any nests.")
    if self.body is None:
      await self._find_body()
    if not self.nests:
      if self.body is not None:
        raise RuntimeError(f"'{self.name}' in the resource store holds no transfer nests.")
      nest_numbers = sorted(nest_status)
      expected_nest_numbers = list(range(1, len(nest_numbers) + 1))
      if nest_numbers != expected_nest_numbers:
        raise RuntimeError(
          f"The sample store must report contiguous nest numbers starting at 1; got {nest_numbers}."
        )
      self._nest_definitions = [
        plate_holder(f"{self.name}_nest_{nest_number}", _NEST_SIZE) for nest_number in nest_numbers
      ]
    if self.body is None:
      await self._create_body()
    if home:
      await self.home()

  def _add_rack(
    self, rack: pb.ResourceDefinition, stacker: int, spots: Optional[Sequence[int]] = None
  ) -> None:
    """Configure one rack under its physical stacker number.

    Args:
      rack: The rack's definition: a plate carrier whose sites are the stacker's slots.
      stacker: Its physical stacker number.
      spots: Each site's zero-based spot, in the order of the rack's sites; unset numbers them
        from 0.
    """
    self._validate_stacker_number(stacker)
    if stacker in self._rack_definitions:
      raise ValueError(f"Stacker {stacker} is already configured.")
    if rack.attributes.kind != K.RESOURCE_KIND_CARRIER:
      raise ValueError(f"Rack {rack.attributes.name!r} must be a plate carrier.")
    sites = [site.attributes.name for site in rack.children]
    spot_list = list(spots) if spots is not None else list(range(len(sites)))
    if len(spot_list) != len(sites):
      raise ValueError(
        f"Rack {rack.attributes.name!r} has {len(sites)} sites but {len(spot_list)} spots."
      )
    if len(set(spot_list)) != len(spot_list):
      raise ValueError(f"Rack {rack.attributes.name!r} has a spot more than once: {spot_list}.")
    for spot, site in zip(spot_list, sites):
      if spot < 0:
        raise ValueError(f"Rack site spot must be non-negative; got {spot} for {site!r}.")
    self._rack_definitions[stacker] = rack
    if spots is not None:
      self._rack_spots[stacker] = spot_list

  @staticmethod
  def _validate_stacker_number(stacker: int) -> None:
    if not isinstance(stacker, int) or isinstance(stacker, bool) or stacker < 1:
      raise ValueError(f"Stacker number must be a positive integer; got {stacker!r}.")

  async def _load_racks_from_device(self) -> None:
    """Define empty stackers from ``getstackerdimensions``."""
    dimensions = await self.request_stacker_dimensions()
    if not dimensions:
      raise RuntimeError("The sample store did not report any stacker dimensions.")

    reported_stackers = set()
    for stacker_dimensions in sorted(dimensions, key=lambda value: value.stacker):
      stacker = stacker_dimensions.stacker
      if stacker in reported_stackers:
        raise RuntimeError(f"The sample store reported stacker {stacker} more than once.")
      reported_stackers.add(stacker)
      if stacker_dimensions.slot_count == 0:
        continue
      rack = high_res_stacker(
        name=f"{self.name}_stacker_{stacker}",
        zero_offset=stacker_dimensions.zero_offset,
        slot_height=stacker_dimensions.slot_height,
        slot_count=stacker_dimensions.slot_count,
      )
      self._add_rack(rack, stacker=stacker)
      self._discovered.add(stacker)

    self._racks_loaded = True
    logger.info("Loaded %d configured stackers for %s", len(self._rack_definitions), self.name)

  async def stop(self) -> None:
    logger.info("Stopping %s", self.name)
    try:
      await self.io.stop()
    finally:
      self._transport_invalidated = True

  # --- transport ------------------------------------------------------------

  async def _readline(self, timeout: Optional[float]) -> str:
    raw = await self.io.readuntil(b"\n", timeout=timeout)
    return raw.decode("ascii", errors="replace").rstrip("\r\n")

  async def _send_command(self, command: str, timeout: Optional[float] = None) -> List[str]:
    """Send a command and return its data lines (those between the ``ACK!`` echo
    and the completion line).

    Raises:
      HighResSampleStorageError: if the device replies ``ERROR!``.
      HighResSampleStorageAbortedError: if the device replies ``ABORTED!``.
      HighResSampleStorageProtocolError: if the acknowledgement or completion
        does not correspond exactly to this command.
    """
    if not command or command != command.strip() or "\r" in command or "\n" in command:
      raise ValueError("command must be a non-empty single line without surrounding whitespace")
    if command.partition(" ")[0] in ("pick", "place", "nesttransfer"):
      self._require_no_unresolved_transfer()
    if timeout is None:
      timeout = self._read_timeout
    encoded_command = command.encode("ascii") + b"\r\n"
    async with self._command_lock:
      try:
        await self.io.write(encoded_command)

        data_lines: List[str] = []
        ack = await self._readline(timeout)
        ack_command, command_id = self._parse_envelope(ACK_TOKEN, ack, command)
        if ack_command != command:
          raise HighResSampleStorageProtocolError(
            command, ack, f"ACK echoed command {ack_command!r}"
          )

        while True:
          line = await self._readline(timeout)
          completion_token = next(
            (token for token in COMPLETION_TOKENS if line == token or line.startswith(f"{token} ")),
            None,
          )
          if completion_token is None:
            if line == ACK_TOKEN or line.startswith(f"{ACK_TOKEN} "):
              raise HighResSampleStorageProtocolError(command, line, "received a second ACK")
            data_lines.append(line)
            continue

          completion_command, completion_id = self._parse_envelope(completion_token, line, command)
          if completion_command != command:
            raise HighResSampleStorageProtocolError(
              command, line, f"completion echoed command {completion_command!r}"
            )
          if completion_id != command_id:
            raise HighResSampleStorageProtocolError(
              command,
              line,
              f"completion command ID {completion_id!r} does not match ACK ID {command_id!r}",
            )
          break
      except BaseException:
        # A timeout, cancellation, or malformed envelope can leave unread response
        # lines in the stream. Closing prevents the next command from consuming
        # those stale lines as its own response.
        logger.exception(
          "Invalidating %s connection after incomplete command %r", self.name, command
        )
        self._transport_invalidated = True
        try:
          await self.io.stop()
        except BaseException:
          logger.exception("Failed to close invalid %s connection", self.name)
        raise

    if completion_token == COMPLETION_ERROR:
      # Firmware 3.0.x emits the ``Error <n>: ...`` stack as data lines *before*
      # the ERROR! completion, so they are already collected in data_lines.
      error_lines = [ln for ln in data_lines if ln.startswith("Error")] or data_lines
      raise HighResSampleStorageError(command, error_lines)
    if completion_token == COMPLETION_ABORTED:
      raise HighResSampleStorageAbortedError(command)
    if completion_token != COMPLETION_OK:
      raise HighResSampleStorageProtocolError(command, line, "unknown completion status")
    return data_lines

  async def _reconnect_invalidated_transport(self) -> None:
    """Reconnect after an incomplete response left the command stream unusable."""
    if not self._transport_invalidated:
      return
    logger.info("Reconnecting to %s before transfer reconciliation", self.name)
    await self.io.setup()
    self._transport_invalidated = False

  @staticmethod
  def _parse_envelope(token: str, line: str, command: str) -> Tuple[str, str]:
    prefix = f"{token} "
    if not line.startswith(prefix):
      raise HighResSampleStorageProtocolError(command, line, f"expected {token} envelope")
    echoed_command, separator, command_id = line[len(prefix) :].rpartition(" ")
    if not separator or not echoed_command or not command_id.isdecimal():
      raise HighResSampleStorageProtocolError(
        command, line, f"expected '{token} <command> <numeric command ID>'"
      )
    return echoed_command, command_id

  # --- shared device queries ------------------------------------------------

  async def request_version(self) -> VersionInfo:
    raw = parse_kv(await self._send_command("version"))
    return VersionInfo(
      product_name=raw.get("Product Name"),
      serial_number=raw.get("Serial Number"),
      firmware_version=raw.get("Firmware Version"),
      firmware_build=raw.get("Firmware Build"),
      raw=raw,
    )

  async def request_environment(self) -> Dict[str, EnvironmentParameter]:
    """Parse ``environmentstatus`` into ``{name: EnvironmentParameter}``.

    Each channel reports ``NAME:current/setpoint/limit``; sensor-only channels
    (e.g. the gas tank pressures) report only a current value. Shared by the
    temperature and humidity controls.
    """
    out: Dict[str, EnvironmentParameter] = {}
    for line in await self._send_command("environmentstatus"):
      if ":" not in line:
        continue
      name, _, rest = line.partition(":")
      parts = rest.strip().rstrip(":").split("/")
      try:
        current = float(parts[0])
      except (ValueError, IndexError):
        continue

      def _opt(i: int) -> Optional[float]:
        try:
          return float(parts[i])
        except (ValueError, IndexError):
          return None

      channel = name.strip().upper()
      out[channel] = EnvironmentParameter(
        name=channel, current=current, setpoint=_opt(1), limit=_opt(2)
      )
    return out

  # --- queries --------------------------------------------------------------

  async def request_axis_positions(self) -> Dict[str, float]:
    """Return the ``status`` report: carousel/theta/Y/Z positions."""
    out: Dict[str, float] = {}
    for key, value in parse_kv(await self._send_command("status")).items():
      try:
        out[key] = float(value)
      except ValueError:
        continue
    return out

  async def request_is_homed(self) -> bool:
    lines = await self._send_command("homedstatus")
    return any(line.strip().lower() == "homed" for line in lines)

  async def request_door_status(self) -> Dict[str, DoorState]:
    """Parsed ``doorstatus`` output, keyed by door name."""
    doors: Dict[str, DoorState] = {}
    for name, value in parse_kv(await self._send_command("doorstatus")).items():
      state = value.lower()
      doors[name] = cast(DoorState, state) if state in DOOR_STATES else "unknown"
    return doors

  async def request_nest_status(self) -> Dict[int, NestState]:
    """Parsed ``neststatus`` output, keyed by nest number."""
    nests: Dict[int, NestState] = {}
    for key, value in parse_kv(await self._send_command("neststatus")).items():
      try:
        nest = int(key)
      except ValueError:
        continue
      state = value.lower()
      if state == "plate_available":
        state = "occupied"
      nests[nest] = cast(NestState, state) if state in NEST_STATES else "unknown"
    return nests

  async def request_spatula_is_holding(self) -> bool:
    """Whether a plate is currently held on the spatula (``platestatus``)."""
    lines = await self._send_command("platestatus")
    return not any("NO_PLATE" in line for line in lines)

  async def request_nest_is_holding(self, nest: int) -> bool:
    """Whether a plate is present on ``nest`` (per its plate sensor).

    Firmware ``PLATE_AVAILABLE`` responses are normalized to ``occupied`` by
    :meth:`request_nest_status`; any other non-clear state also counts as holding.
    """
    states = await self.request_nest_status()
    if nest not in states:
      raise ValueError(f"The device did not report nest {nest}.")
    return states[nest] != "clear"

  async def _probe_presence(self, stacker: int, slot: int, to_nest: int = 1) -> bool:
    """Probe whether a plate is present in ``(stacker, slot)`` by attempting a
    pick. Returns ``True`` if a plate was there, ``False`` if the slot is empty.

    SIDE EFFECT: a plate that is found is moved to ``to_nest`` (the only way to
    sense a stacker slot is to pick it). Only safe for non-top slots, where an
    empty pick is graceful; the top slot (24) faults when empty — see
    :meth:`_pick`. For nests, use :meth:`request_nest_is_holding` instead (a
    non-destructive sensor read).
    """
    try:
      await self._pick(stacker, slot, to_nest)
      return True
    except PlateNotFoundError:
      return False

  async def request_stacker_dimensions(self) -> List[StackerDimensions]:
    """Parse ``getstackerdimensions`` (``<stacker>: <zero_offset> <slot_height>
    <slot_count>``)."""
    dims: List[StackerDimensions] = []
    for line in await self._send_command("getstackerdimensions"):
      key, _, rest = line.partition(":")
      try:
        stacker = int(key)
        zero_offset, slot_height, slot_count = rest.split()
        dims.append(
          StackerDimensions(
            stacker=stacker,
            zero_offset=float(zero_offset),
            slot_height=float(slot_height),
            slot_count=int(slot_count),
          )
        )
      except ValueError:
        continue
    return dims

  async def request_settings(self) -> HighResSampleStorageSettings:
    """Read the device's full settings file (``NAME = value`` pairs) into a
    frozen :class:`HighResSampleStorageSettings`."""
    lines = await self._send_command("settings", timeout=self.read_timeout)
    return HighResSampleStorageSettings.from_lines(lines)

  async def request_stacker_barcodes(
    self, stacker: Union[int, Literal["all"]], slot: Optional[int] = None
  ) -> List[str]:
    """Scan a stacker (or a single slot) for barcodes.

    All transfer nests must be clear: firmware 3.0.0.119 otherwise waits for
    an automation door that cannot open and eventually reports a timeout.
    ``EMPTY`` in the returned lines means no readable barcode; it is not a
    plate-presence result.

    Args:
      stacker: Stacker number, or the string ``"all"`` to scan the whole
        inventory.
      slot: Optional single slot to scan.
    """
    if stacker != "all" and (not isinstance(stacker, int) or stacker < 1):
      raise ValueError("stacker must be a positive integer or 'all'.")
    if stacker == "all" and slot is not None:
      raise ValueError("slot cannot be specified when stacker is 'all'.")
    if slot is not None and slot < 1:
      raise ValueError("slot must be a positive integer.")
    self._require_no_unresolved_transfer()

    occupied_nests = [
      nest for nest, state in (await self.request_nest_status()).items() if state != "clear"
    ]
    if occupied_nests:
      raise RuntimeError(
        "Cannot scan barcodes while plates are present on nests "
        + ", ".join(map(str, occupied_nests))
        + "; clear all nests first."
      )

    command = f"barcode {stacker}"
    if slot is not None:
      command += f" {slot}"
    return await self._send_command(command, timeout=self.motion_timeout)

  # --- motion ---------------------------------------------------------------

  async def home(self) -> None:
    """Home the system. The first step closes all doors, which requires the
    pneumatic supply (clean dry air >80 psi); without it this raises
    :class:`HighResSampleStorageError` ("Unable to close all doors")."""
    self._require_no_unresolved_transfer()
    if await self.request_spatula_is_holding():
      raise RuntimeError("Cannot home while the spatula reports that it is holding a plate.")
    logger.info("Homing %s", self.name)
    await self._send_command("home", timeout=self.motion_timeout)
    logger.info("Homed %s", self.name)

  async def request_is_parked(self) -> bool:
    """Whether the machine is genuinely safe to move: homed AND the spatula
    slide/lift axes are retracted.

    Prefer this over :meth:`request_is_homed`. ``homedstatus`` reports homed even while
    the spatula is stuck extended in a stacker after a faulted top-slot pick, so
    it alone is not a safe-state check; this also verifies the slide (Y) and
    lift (Z) axes are near their home positions.
    """
    if not await self.request_is_homed():
      return False
    positions = await self.request_axis_positions()
    y = positions.get("Y axis")
    z = positions.get("Z axis")
    return (
      y is not None
      and z is not None
      and abs(y) < self._retracted_y_max
      and abs(z) < self._retracted_z_max
    )

  async def recover(self) -> bool:
    """Retract the spatula and re-home after a motion fault.

    A faulted command (e.g. an empty-slot ``pick`` in the top few slots) can
    leave the spatula extended. This ALWAYS issues the retract (``spatulaout``)
    + ``home`` — it does not trust ``homedstatus`` to decide whether recovery is
    needed, because that reports homed even while the spatula is stuck extended.
    Automatic recovery is refused while the spatula plate sensor is active,
    because the plate cannot be relocated safely without physical inspection.
    Retries a few times. Returns ``True`` once :meth:`request_is_parked`.
    """
    if await self.request_spatula_is_holding():
      raise RuntimeError(
        "Cannot recover automatically while the spatula reports that it is holding a plate."
      )

    logger.warning("Starting motion recovery for %s", self.name)
    for attempt in range(1, 4):
      for command in ("enable", "spatulaout"):
        try:
          await self._send_command(command, timeout=self.motion_timeout)
        except HighResSampleStorageError as exc:
          logger.warning(
            "Recovery attempt %d: %s failed on %s: %s",
            attempt,
            command,
            self.name,
            exc,
          )
      try:
        await self._send_command("home", timeout=self.motion_timeout)
      except HighResSampleStorageError as exc:
        logger.warning("Recovery attempt %d: home failed on %s: %s", attempt, self.name, exc)
      if await self.request_is_parked():
        logger.info("Motion recovery completed for %s on attempt %d", self.name, attempt)
        return True
    logger.error("Motion recovery failed for %s after 3 attempts", self.name)
    return False

  async def _pick(self, stacker: int, slot: int, nest: int, close_door: bool = True) -> None:
    """Retrieve a plate from ``(stacker, slot)`` to ``nest``.

    ``close_door=False`` re-opens the doors after the transfer (see :meth:`_place`).

    On failure the error is classified; no automatic motion is performed:

    - :class:`PlateNotFoundError` — the slot was empty ("No plate detected")
      and the store retracted cleanly; the machine is safe to keep using.
    - :class:`HighResSampleStorageFault` — the machine was left unsafe (spatula extended
      / unhomed), e.g. an empty *top* slot where the firmware can't complete its
      safe-travel retract. Call :meth:`recover` before any further motion.

    Note: ``homedstatus`` reports homed even when the spatula is stuck extended
    at a top slot, so the error stack and live axis positions are both used to
    determine whether the machine is parked.
    """
    command = f"pick {stacker} {slot} {nest}"
    logger.info(
      "Moving a plate in %s from stacker %d slot %d to nest %d",
      self.name,
      stacker,
      slot,
      nest,
    )
    try:
      await self._send_command(command, timeout=self.motion_timeout)
    except HighResSampleStorageError as exc:
      if left_unsafe(exc.error_lines) or not await self.request_is_parked():
        logger.error("Pick left %s unsafe: %s", self.name, exc)
        raise HighResSampleStorageFault(command, exc.error_lines) from exc
      if any("no plate detected" in line.lower() for line in exc.error_lines):
        logger.warning("No plate found in %s stacker %d slot %d", self.name, stacker, slot)
        raise PlateNotFoundError(command, exc.error_lines) from exc
      logger.error("Pick failed on %s: %s", self.name, exc)
      raise
    if not close_door:
      await self.open_all_doors()

  async def _place(self, stacker: int, slot: int, nest: int, close_door: bool = True) -> None:
    """Place the plate at ``nest`` into ``(stacker, slot)``.

    The store re-seals its doors as part of every transfer, so ``close_door``
    controls only the *end* state: with ``close_door=False`` the doors are
    re-opened after the place, leaving the carousel accessible for a following
    operation (handy when the cold environment doesn't matter). The default
    leaves it sealed.
    """
    command = f"place {stacker} {slot} {nest}"
    logger.info(
      "Moving a plate in %s from nest %d to stacker %d slot %d",
      self.name,
      nest,
      stacker,
      slot,
    )
    try:
      await self._send_command(command, timeout=self.motion_timeout)
    except HighResSampleStorageError as exc:
      if left_unsafe(exc.error_lines) or not await self.request_is_parked():
        logger.error("Place left %s unsafe: %s", self.name, exc)
        raise HighResSampleStorageFault(command, exc.error_lines) from exc
      logger.error("Place failed on %s: %s", self.name, exc)
      raise
    if not close_door:
      await self.open_all_doors()

  @staticmethod
  def _robot_doors_reached(
    doors: Dict[str, DoorState], acceptable_states: Tuple[DoorState, ...]
  ) -> bool:
    robot_doors = [state for name, state in doors.items() if name.casefold() != "user door"]
    return bool(robot_doors) and all(state in acceptable_states for state in robot_doors)

  async def _wait_for_robot_doors(
    self, target: Literal["open", "closed"], moving: Literal["opening", "closing"]
  ) -> bool:
    """Wait for every robot door to reach ``target`` after a firmware error.

    Returns ``False`` immediately if a door reports a contradictory or unknown
    state, or after the configured motion timeout expires.
    """
    deadline = asyncio.get_running_loop().time() + self.motion_timeout
    while True:
      doors = await self.request_door_status()
      if self._robot_doors_reached(doors, acceptable_states=(target,)):
        return True
      if not self._robot_doors_reached(doors, acceptable_states=(target, moving)):
        return False
      remaining = deadline - asyncio.get_running_loop().time()
      if remaining <= 0:
        return False
      await asyncio.sleep(min(0.1, remaining))

  async def open_all_doors(self) -> None:
    """Open every pneumatic robot door.

    Firmware 3.0.0.119 can return ``ERROR!`` after completing this operation.
    In that case the door sensors are the authoritative postcondition; the
    original command error is re-raised unless every robot door reaches open.
    Transitional states are polled up to :attr:`motion_timeout`. The manual user
    door is intentionally excluded.
    """
    try:
      logger.info("Opening robot doors on %s", self.name)
      await self._send_command("openalldoors", timeout=self.motion_timeout)
    except HighResSampleStorageError:
      logger.warning("Open-all-doors returned an error on %s; checking door sensors", self.name)
      if await self._wait_for_robot_doors(target="open", moving="opening"):
        logger.info("Robot doors on %s reached open despite firmware error", self.name)
        return
      raise

  async def close_all_doors(self) -> None:
    """Close every pneumatic robot door.

    As with :meth:`open_all_doors`, accept an erroneous completion only when
    the live door report reaches the requested final state.
    """
    try:
      logger.info("Closing robot doors on %s", self.name)
      await self._send_command("closealldoors", timeout=self.motion_timeout)
    except HighResSampleStorageError:
      logger.warning("Close-all-doors returned an error on %s; checking door sensors", self.name)
      if await self._wait_for_robot_doors(target="closed", moving="closing"):
        logger.info("Robot doors on %s reached closed despite firmware error", self.name)
        return
      raise

  async def clear_abort(self) -> None:
    """Clear an abort state reported by the device.

    Firmware 3.0.0.119 exposes ``clearabort`` but no command for initiating an
    abort, so this is recovery for device- or externally-initiated aborts.
    """
    logger.info("Clearing abort state on %s", self.name)
    await self._send_command("clearabort")

  # --- plate retrieval -------------------------------------------------------

  @property
  def racks(self) -> List[handles.Carrier]:
    return list(self._racks_by_number.values())

  async def _read(
    self, resources: Sequence[handles.Resource], depth: int = 0, ancestors: bool = False
  ) -> Dict[bytes, pb.ResourceNode]:
    """Resources, as the store holds them now, by id; in one call."""
    response = await self.store.commands.get_resources(
      spb.GetResourcesRequest(
        resources=[resource.ref for resource in resources], depth=depth, ancestors=ancestors
      )
    )
    return {node.id: node for node in response.nodes}

  def _sites(self) -> List[handles.Resource]:
    """Every configured stacker slot, by stacker and then by site."""
    return [site for rack in self._racks_by_number.values() for site in rack.sites]

  async def get_num_free_sites(self) -> int:
    nodes = await self._read(self.racks, depth=1)
    return sum(1 for site in self._sites() if not nodes[site.id].child_ids)

  async def _find_stored(
    self, plate_name: str
  ) -> Tuple[handles.PlateHolder, pb.ResourceNode, Dict[bytes, pb.ResourceNode]]:
    """The slot holding a plate of this name, what it holds, and the racks' nodes they were read
    from.

    Raises:
      ResourceNotFoundError: No slot holds a resource of that name.
    """
    nodes = await self._read(self.racks, depth=2)
    for site in self._sites():
      held = nodes[site.id].child_ids
      if held and nodes[held[0]].attributes.name == plate_name:
        return cast(handles.PlateHolder, site), nodes[held[0]], nodes
    raise ResourceNotFoundError(f"Plate {plate_name!r} not found in {self.name!r}.")

  async def get_site_by_plate_name(self, plate_name: str) -> handles.PlateHolder:
    site, _, _ = await self._find_stored(plate_name)
    return site

  async def _find_available_sites_sorted(
    self, plate: handles.Resource
  ) -> List[handles.PlateHolder]:
    nodes = await self._read([plate, *self.racks], depth=1)
    plate_node = nodes[plate.id]
    plate_height = plate_node.attributes.size.z
    lid = next(
      (
        nodes[child]
        for child in plate_node.child_ids
        if nodes[child].attributes.kind == K.RESOURCE_KIND_LID
      ),
      None,
    )
    if lid is not None and lid.attributes.HasField("location"):
      plate_height = max(plate_height, lid.attributes.location.z + lid.attributes.size.z)
    available = [
      cast(handles.PlateHolder, site)
      for site in self._sites()
      if not nodes[site.id].child_ids and nodes[site.id].attributes.size.z >= plate_height
    ]
    if not available:
      raise NoFreeSiteError(
        f"No free site at least {plate_height:g} mm high found for plate {plate.name!r}."
      )
    return sorted(available, key=lambda site: nodes[site.id].attributes.size.z)

  async def _require_nest_states(self, expected: Dict[int, NestState]) -> None:
    """Require exact live sensor states before issuing a transfer command."""
    actual = await self.request_nest_status()
    for nest, expected_state in expected.items():
      actual_state = actual.get(nest)
      if actual_state != expected_state:
        raise RuntimeError(
          f"Cannot transfer plate: nest {nest} must be {expected_state}, "
          f"but its sensor reports {actual_state or 'missing'}."
        )

  def _require_no_unresolved_transfer(self) -> None:
    transfer = self._unresolved_transfer
    if transfer is not None:
      raise RuntimeError(
        f"Plate location is unresolved after transfer command {transfer.command!r}; "
        "recover the machine if necessary, then call resolve_unresolved_transfer() "
        "before another plate move, home, or barcode scan."
      )

  def _record_unresolved_transfer(
    self,
    *,
    plate: handles.Plate,
    source: handles.PlateHolder,
    destination: handles.PlateHolder,
    command: str,
    error: BaseException,
  ) -> None:
    self._unresolved_transfer = UnresolvedPlateTransfer(
      plate=plate,
      source=source,
      destination=destination,
      command=command,
      error_type=type(error).__name__,
      error_message=str(error),
    )
    logger.error(
      "Plate %s transfer via %r is unresolved between %s and %s: %s",
      plate.name,
      command,
      source.name,
      destination.name,
      error,
    )

  @staticmethod
  def _require_can_drop(
    holder: handles.Resource, holder_node: pb.ResourceNode, resource: handles.Resource
  ) -> None:
    """Refuse to put `resource` in a holder that holds something else."""
    held = holder_node.child_ids
    if held and held[0] != resource.id:
      raise _drop_refusal(resource.name, holder.name)

  async def _move_plate(self, plate: handles.Plate, destination: handles.PlateHolder) -> None:
    """Assign a plate to `destination`, as the device moved it; the handle reports the move."""
    await destination.assign_child_resource(plate)

  async def _unassign_plate(self, plate: handles.Plate) -> None:
    """Take a plate out of the store's resources; the handle reports it."""
    previous = await plate.node()
    if not previous.parent_id:
      return
    await plate.unassign()

  async def _execute_plate_transfer(
    self,
    *,
    plate: handles.Plate,
    source: handles.PlateHolder,
    destination: handles.PlateHolder,
    command: str,
    move: Callable[[], Awaitable[object]],
    plate_not_found_is_definitive: bool = False,
  ) -> handles.Plate:
    """Execute one physical move and commit it to the resource store."""
    self._require_no_unresolved_transfer()
    try:
      await move()
    except BaseException as error:
      if not (plate_not_found_is_definitive and isinstance(error, PlateNotFoundError)):
        self._record_unresolved_transfer(
          plate=plate,
          source=source,
          destination=destination,
          command=command,
          error=error,
        )
      raise

    try:
      await self._move_plate(plate, destination)
    except BaseException as error:
      # The device completed the move, but the store could not commit the same state.
      # Keep the transfer unresolved so a caller must reconcile both views.
      self._record_unresolved_transfer(
        plate=plate,
        source=source,
        destination=destination,
        command=command,
        error=error,
      )
      raise
    return plate

  async def resolve_unresolved_transfer(
    self, location: Literal["source", "destination", "unassigned"]
  ) -> handles.Plate:
    """Reconcile an ambiguous plate move without issuing further motion.

    The spatula must be empty. Any source or destination nest is checked against
    its live plate sensor. Stacker slots have no non-destructive presence sensor,
    so selecting a stacker endpoint is explicit operator confirmation that the
    plate was found there. Use ``"unassigned"`` when inspection establishes that
    the plate is outside the modeled source and destination.
    """
    async with self._transfer_lock:
      transfer = self._unresolved_transfer
      if transfer is None:
        raise RuntimeError("There is no unresolved plate transfer.")
      if location not in ("source", "destination", "unassigned"):
        raise ValueError(
          f"location must be 'source', 'destination', or 'unassigned'; got {location!r}."
        )

      await self._reconnect_invalidated_transport()

      target = (
        transfer.source
        if location == "source"
        else transfer.destination
        if location == "destination"
        else None
      )
      in_target = False
      if target is not None:
        nodes = await self._read([transfer.plate, target])
        in_target = nodes[transfer.plate.id].parent_id == target.id
        if not in_target:
          self._require_can_drop(target, nodes[target.id], transfer.plate)

      if await self.request_spatula_is_holding():
        raise RuntimeError(
          "Cannot resolve the plate location while the spatula reports that it is holding a plate."
        )

      expected_nests: Dict[int, NestState] = {}
      for tray_index, nest in enumerate(self.nests):
        if nest in (transfer.source, transfer.destination):
          expected_nests[tray_index + 1] = "occupied" if nest == target else "clear"
      if expected_nests:
        await self._require_nest_states(expected_nests)

      if target is None:
        await self._unassign_plate(transfer.plate)
      elif not in_target:
        await self._move_plate(transfer.plate, target)

      self._unresolved_transfer = None
      logger.info(
        "Resolved plate %s after %r as %s",
        transfer.plate.name,
        transfer.command,
        target.name if target is not None else "unassigned",
      )
      return transfer.plate

  async def find_smallest_site_for_plate(self, plate: handles.Plate) -> handles.PlateHolder:
    return (await self._find_available_sites_sorted(plate))[0]

  async def find_random_site(self, plate: handles.Plate) -> handles.PlateHolder:
    return random.choice(await self._find_available_sites_sorted(plate))

  async def _locate(self, site: handles.Resource) -> Tuple[int, int]:
    """The (stacker, one-based slot) of a configured stacker site.

    Raises:
      ValueError: It is not a slot of a configured stacker.
    """
    slot = self._slots.get(site.id)
    if slot is not None:
      return slot
    nodes = await self._read([site], ancestors=True)
    rack = nodes.get(nodes[site.id].parent_id)
    if rack is None or rack.attributes.kind != K.RESOURCE_KIND_CARRIER:
      raise ValueError(f"Site '{site.name}' is not attached to a plate carrier.")
    stacker = next(
      (number for number, known in self._racks_by_number.items() if known.id == rack.id), None
    )
    if stacker is None:
      raise ValueError(f"Site '{site.name}' is not in a known stacker.")
    raise ValueError(f"Site '{site.name}' is not a known slot in stacker {stacker}.")

  def _nest_for_tray(self, tray_index: int) -> int:
    """Map a 0-based tray index to its one-based device nest number."""
    if not self.nests:
      raise RuntimeError("Nests have not been loaded; call setup() first.")
    if not 0 <= tray_index < len(self.nests):
      raise ValueError(
        f"sample store has trays 0..{len(self.nests) - 1}; got tray_index={tray_index}."
      )
    return tray_index + 1

  async def _plate_handle(
    self, node: pb.ResourceNode, nodes: Dict[bytes, pb.ResourceNode]
  ) -> handles.Plate:
    return cast(handles.Plate, (await self.store.make_handles([node], list(nodes.values())))[0])

  async def fetch_plate_to_loading_tray(
    self, plate: Union[handles.Plate, str], tray_index: int
  ) -> handles.Plate:
    async with self._transfer_lock:
      self._require_no_unresolved_transfer()
      if isinstance(plate, str):
        _, stored, stored_nodes = await self._find_stored(plate)
        if stored.attributes.kind != K.RESOURCE_KIND_PLATE:
          raise ResourceNotFoundError(f"Plate {plate!r} not found in {self.name!r}.")
        plate = await self._plate_handle(stored, stored_nodes)
      nodes = await self._read([plate], ancestors=True)
      parent_node = nodes.get(nodes[plate.id].parent_id)
      if parent_node is None or parent_node.attributes.kind != K.RESOURCE_KIND_PLATE_HOLDER:
        raise ValueError(f"Plate '{plate.name}' is not in a stacker slot.")
      parent = cast(handles.PlateHolder, self.store.handle_from_node(parent_node, ()))
      stacker, slot = await self._locate(parent)
      nest_number = self._nest_for_tray(tray_index)
      nest = self.nests[tray_index]
      self._require_can_drop(nest, (await self._read([nest]))[nest.id], plate)
      await self._require_nest_states({nest_number: "clear"})
      command = f"pick {stacker} {slot} {nest_number}"

      with event_operation(
        "incubator.fetch_plate", **await self._operation_data(plate, parent, nest)
      ):
        return await self._execute_plate_transfer(
          plate=plate,
          source=parent,
          destination=nest,
          command=command,
          move=lambda: self._pick(stacker, slot, nest_number),
          plate_not_found_is_definitive=True,
        )

  async def _plate_on_tray(self, tray_index: int) -> handles.Plate:
    """The plate on a transfer nest.

    Raises:
      ResourceNotFoundError: The nest holds no plate.
    """
    nest = self.nests[tray_index]
    nodes = await self._read([nest], depth=2)
    held = nodes[nest.id].child_ids
    if not held or nodes[held[0]].attributes.kind != K.RESOURCE_KIND_PLATE:
      raise ResourceNotFoundError(f"No plate on tray {tray_index}.")
    return await self._plate_handle(nodes[held[0]], nodes)

  async def take_in_plate(
    self,
    tray_index: int,
    site: Union[handles.PlateHolder, Literal["random", "smallest"]] = "smallest",
  ) -> handles.Plate:
    async with self._transfer_lock:
      self._require_no_unresolved_transfer()
      self._nest_for_tray(tray_index)
      plate = await self._plate_on_tray(tray_index)

      if site == "random":
        destination = await self.find_random_site(plate)
      elif site == "smallest":
        destination = await self.find_smallest_site_for_plate(plate)
      elif isinstance(site, handles.Resource):
        if site not in await self._find_available_sites_sorted(plate):
          raise ValueError(f"Site {site.name!r} is not available for plate {plate.name!r}.")
        destination = site
      else:
        raise ValueError(f"Invalid site: {site!r}")

      nest = self.nests[tray_index]
      with event_operation(
        "incubator.take_in_plate", **await self._operation_data(plate, nest, destination)
      ):
        await self._store_plate(plate, destination, tray_index)
        return plate

  async def store_plate(
    self, plate: handles.Plate, site: handles.PlateHolder, tray_index: int
  ) -> None:
    async with self._transfer_lock:
      self._require_no_unresolved_transfer()
      self._nest_for_tray(tray_index)
      nest = self.nests[tray_index]
      with event_operation(
        "incubator.take_in_plate", **await self._operation_data(plate, nest, site)
      ):
        await self._store_plate(plate, site, tray_index)

  async def transfer_plate_between_nests(
    self, source_tray_index: int, destination_tray_index: int
  ) -> handles.Plate:
    """Move a plate between two transfer nests.

    Tray indices are zero-based and map to the sorted nest numbers reported by
    the device during :meth:`setup`.
    """
    async with self._transfer_lock:
      self._require_no_unresolved_transfer()
      if source_tray_index == destination_tray_index:
        raise ValueError("Source and destination tray indices must be different.")
      source_number = self._nest_for_tray(source_tray_index)
      destination_number = self._nest_for_tray(destination_tray_index)
      source = self.nests[source_tray_index]
      destination = self.nests[destination_tray_index]
      plate = await self._plate_on_tray(source_tray_index)
      self._require_can_drop(destination, (await self._read([destination]))[destination.id], plate)
      await self._require_nest_states({source_number: "occupied", destination_number: "clear"})
      command = f"nesttransfer {source_number} {destination_number}"

      with event_operation(
        "incubator.transfer_plate", **await self._operation_data(plate, source, destination)
      ):
        logger.info(
          "Moving plate %s in %s from nest %d to nest %d",
          plate.name,
          self.name,
          source_number,
          destination_number,
        )
        return await self._execute_plate_transfer(
          plate=plate,
          source=source,
          destination=destination,
          command=command,
          move=lambda: self._send_command(command, timeout=self.motion_timeout),
        )

  async def _store_plate(
    self, plate: handles.Plate, site: handles.PlateHolder, tray_index: int
  ) -> None:
    stacker, slot = await self._locate(site)
    nest_number = self._nest_for_tray(tray_index)
    nest = self.nests[tray_index]
    nodes = await self._read([plate, site])
    if nodes[plate.id].parent_id != nest.id:
      raise ValueError(f"Plate '{plate.name}' is not on tray {tray_index}.")
    self._require_can_drop(site, nodes[site.id], plate)
    await self._require_nest_states({nest_number: "occupied"})
    command = f"place {stacker} {slot} {nest_number}"

    await self._execute_plate_transfer(
      plate=plate,
      source=nest,
      destination=site,
      command=command,
      move=lambda: self._place(stacker, slot, nest_number),
    )
