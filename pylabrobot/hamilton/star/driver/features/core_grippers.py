"""The STAR's CoRe grippers: the tools, and what they take."""

from __future__ import annotations

import dataclasses
import logging
import warnings
from contextlib import asynccontextmanager
from typing import (
  TYPE_CHECKING,
  Any,
  AsyncIterator,
  Dict,
  List,
  Optional,
  Sequence,
  Tuple,
  Union,
  cast,
)

from pylabrobot.hamilton.star import resource_model
from pylabrobot.hamilton.star.driver import model
from pylabrobot.hamilton.star.driver.errors import STARFirmwareError
from pylabrobot.hamilton.star.driver.lock import _FirmwareLock
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import HasTipError
from pylabrobot.resources.server import handles, library
from pylabrobot.resources.server.errors import ServerError
from pylabrobot.resources.server.tree import to_coordinate, to_rotation, to_vec3
from pylabrobot.resources.server.v1 import server_pb2 as spb
from pylabrobot.resources.server.v1 import types_pb2 as pb

if TYPE_CHECKING:
  from ..master import STARDriver
  from .pipettes import Pipettes
  from .x_arm import XArm

logger = logging.getLogger(__name__)

# How far below the pick-up window the tools are deposited, in mm: legacy's 235/225 against 215/205.
_DEPOSIT_BELOW_PICK_UP = 20.0
# How far below its top a resource may be gripped, in mm: lower, its top presses into the pipetting
# head the grippers hang from.
_MAX_PICKUP_DISTANCE_FROM_TOP = 20.0

# The tool the channels are taken to carry when they hold tools nothing models: what the grip
# line's reach is checked by.
_DEFAULT_TOOL_MODEL = "hamilton_core_gripper_tool"

# What a resource is put back into as the parent seats it, rather than at a point on the deck.
_HOLDER_KINDS = (
  pb.RESOURCE_KIND_RESOURCE_HOLDER,
  pb.RESOURCE_KIND_PLATE_HOLDER,
  pb.RESOURCE_KIND_EMBEDDED_TIP_RACK_HOLDER,
)


def _center(geometry: spb.Geometry) -> Coordinate:
  """A resource's footprint centre on its bottom, turned as it stands in the frame asked of."""
  size = geometry.size
  return Coordinate(size.x / 2, size.y / 2, 0).rotated(to_rotation(geometry.rotation_in_frame))


def _tool_overhang(tool: pb.ResourceAttributes) -> float:
  """How far a tool's grip line hangs below the stop disc of the channel carrying it, in mm."""
  return tool.size.z - tool.head_tool.fitting_depth - resource_model.grip_line_height(tool)


@dataclasses.dataclass
class CoreGrippersConfiguration:
  """Facts of the grip itself; positions, speeds and accelerations are the pipettes'."""

  grip_strength_range: Tuple[int, int] = (0, 99)


class CoreGrippers:
  """The CoRe grip tools a pair of channels carries, and what they take."""

  # Grip strength index, 0 (low) to 99 (high).
  default_grip_strength: int = 15
  # Z speed while a resource is held, in mm/s.
  default_z_speed_with_resource_held: float = 50.0
  # Z acceleration while a resource is held, in mm/s2; 800 jolts a plate.
  default_z_acceleration_with_resource_held: float = 150.0
  # Height the channels travel at and are left at around a tool command, in mm.
  default_minimum_traverse_height: float = 280.0

  def __init__(
    self, driver: "STARDriver", configuration: Optional[CoreGrippersConfiguration] = None
  ) -> None:
    """
    Args:
      driver: the driver to send commands through.
      configuration: the grip's device facts. Defaults to `CoreGrippersConfiguration()`.
    """
    self._driver = driver
    self.configuration = configuration or CoreGrippersConfiguration()
    self._tools_mounted = False
    self._back_channel: Optional[int] = None
    self._front_channel: Optional[int] = None
    # x, rear y, front y, seek z and end z of the pick-up the channels hold the tools from, in mm.
    self._tools_taken_from: Optional[Tuple[float, float, float, float, float]] = None
    # The channels the model has the tools on, in the order the tools stood in their holder, which
    # is the order they go back in.
    self._parked_from: List[int] = []
    self._grip_height: Optional[float] = None
    self._holding_resource_width: Optional[float] = None
    self._held_resource: Optional[handles.Resource] = None
    # What the held resource was taken from: its parent, its location there, and whether the parent
    # is a holder, which takes it back as it seats a child.
    self._taken_from: Optional[Tuple[handles.Resource, Optional[Coordinate], bool]] = None

  # -- what carries them ---------------------------------------------------------------------------

  @property
  def arm(self) -> "XArm":
    """The arm carrying these grippers."""
    return next(a for a in self._driver.arms if a.core_grippers is self)

  @property
  def _pipettes(self) -> "Pipettes":
    """The channels that carry the tools.

    Raises:
      RuntimeError: If the arm has no pipettes.
    """
    pipettes = self.arm.pipettes
    if pipettes is None:
      raise RuntimeError("no pipettes to carry the grippers; have you called `star.setup()`?")
    return pipettes

  @property
  def _deck(self) -> handles.Deck:
    """The deck positions are measured from.

    Raises:
      RuntimeError: If the driver was given no deck.
    """
    if self._driver.deck is None:
      raise RuntimeError("the CoRe grippers are placed from the deck; this driver was given none")
    return self._driver.deck

  async def _holder(self) -> Tuple[handles.Resource, pb.ResourceNode]:
    """The CO-RE gripper holder the deck carries, and its node: one whose spec says where each
    channel takes its tool.

    Raises:
      TypeError: If the deck carries none.
    """
    deck = self._deck
    found = await deck.find_resources(categories=["core_grippers"])
    nodes = await model.get_nodes(deck.server, found) if found else []
    for holder, node in zip(found, nodes):
      if len(node.attributes.holder.channel_y_centers) == 2:
        return holder, node
    raise TypeError("the deck carries no CO-RE gripper holder")

  # -- state ---------------------------------------------------------------------------------------

  async def get_tools_mounted(self) -> bool:
    """Whether the tools are on the channels."""
    return self._tools_mounted

  async def request_tool_attached(self, channel: int) -> bool:
    """Whether the device senses something on `channel` (`C0 RT`).

    Args:
      channel: which channel, 0-indexed from the back.

    Raises:
      ValueError: If the channel does not exist.
    """
    self._pipettes._require_channel(channel)
    return bool((await self._pipettes.sense_tip_presence())[channel])

  def _require_mounted(self) -> Tuple[int, int]:
    """Raise unless the channels hold the tools, taken by either pick-up.

    Returns:
      The back and front channel.

    Raises:
      RuntimeError: If they do not.
    """
    if self._tools_taken_from is None or self._back_channel is None or self._front_channel is None:
      raise RuntimeError(
        "the CoRe gripper tools are not on the channels. Call "
        "`await star.core_grippers.pick_up_tools()` or `pick_up_tools_at_location()` first, or use "
        "`async with star.core_grippers.mounted():`."
      )
    return self._back_channel, self._front_channel

  def _clear_held_state(self) -> None:
    self._holding_resource_width = None
    self._grip_height = None
    self._held_resource = None
    self._taken_from = None

  async def _tools_on(self, channels: List[int]) -> List[Optional[pb.ResourceNode]]:
    """What the model has on each of these channels' shafts, in one read; None where nothing."""
    shafts = [self._pipettes.shaft(channel) for channel in channels]
    found: List[Optional[pb.ResourceNode]] = [None] * len(channels)
    modelled = [shaft for shaft in shafts if shaft is not None]
    if not modelled:
      return found
    index = {shaft.id: i for i, shaft in enumerate(shafts) if shaft is not None}
    for node in await model.get_nodes(modelled[0].server, modelled, depth=1):
      i = index.get(node.parent_id)
      kind = node.attributes.kind
      if (
        i is not None
        and found[i] is None
        and kind in (pb.RESOURCE_KIND_TIP, pb.RESOURCE_KIND_HEAD_TOOL)
      ):
        found[i] = node
    return found

  async def _front_tool(self) -> Optional[handles.Resource]:
    """The tool the model has on the front channel, or None while it has none."""
    if self._front_channel is None:
      return None
    (tool,) = await self._tools_on([self._front_channel])
    return None if tool is None else self._deck.server.handle_from_node(tool, ())

  async def _hang_held_resource_on_the_front_tool(self) -> None:
    """Hang the held resource from the front tool where the fingers hold it, so it rides with them.

    Its centre at the fingers' centre, its bottom `_grip_height` below the grip line - the front
    channel's stop disc less the tool's overhang. Nothing happens while nothing models them.
    """
    held, grip_height = self._held_resource, self._grip_height
    if held is None or grip_height is None or self._front_channel is None:
      return
    (tool,) = await self._tools_on([self._front_channel])
    if tool is None or not resource_model.grips(tool.attributes):
      return
    points = await self._pipettes.get_reference_point_locations()
    back, front = points[cast(int, self._back_channel)], points[self._front_channel]
    if back is None or front is None:
      return
    deck = self._deck
    handle = deck.server.handle_from_node(tool, ())
    held_at, tool_at = await model.resolve_geometry(
      deck.server, [model.query(held, deck), model.query(handle, deck)]
    )
    grip_line = front.z - _tool_overhang(tool.attributes)
    center = _center(held_at)
    lfb = Coordinate(
      front.x - center.x,
      (back.y + front.y) / 2 - center.y,
      grip_line - grip_height,
    )
    await handle.assign_child_resource(held, location=lfb - to_coordinate(tool_at.locations[0]))

  # ----------------------------------------
  # Movement
  # ----------------------------------------

  # -- with a resource held ------------------------------------------------------------------------

  async def _unchecked_fw_move_resource(
    self,
    x_position: int,
    x_acceleration_level: int,
    y_position: int,
    z_position: int,
    z_speed: int,
    minimum_traverse_height_start: int,
  ):
    """Send the held plate's move as it is given, in tenths of a millimetre. `C0 ZM`.

    Args:
      x_position: the plate centre's x; negative sends `xd1`.
      x_acceleration_level: 1 to 5.
      y_position: the plate centre's y.
      z_position: the plate's height.
      z_speed: in tenths of a mm/s.
      minimum_traverse_height_start: how high the channels travel first.
    """
    return await self._driver.send_command(
      module="C0",
      command="ZM",
      subsystem=_FirmwareLock.CHANNELS,
      read_timeout=120,
      xs=f"{abs(x_position):05}",
      xd=int(x_position < 0),
      xg=f"{x_acceleration_level}",
      yj=f"{y_position:04}",
      zj=f"{z_position:04}",
      zy=f"{z_speed:04}",
      th=f"{minimum_traverse_height_start:04}",
    )

  # ----------------------------------------
  # Tools
  # ----------------------------------------

  # -- firmware ------------------------------------------------------------------------------------

  async def _unchecked_fw_pick_up_tools(
    self,
    x_position: int,
    back_channel_y: int,
    front_channel_y: int,
    begin_z: int,
    end_z: int,
    minimum_traverse_height_start: int,
    back_channel: int,
    front_channel: int,
    tip_type_index: int,
  ):
    """Send the tool pick-up as it is given, in tenths of a millimetre. `C0 ZT`.

    Args:
      x_position: the tools' x; negative sends `xd1`.
      back_channel_y: y of the tool the back channel takes.
      front_channel_y: y of the tool the front channel takes.
      begin_z: where the pick-up begins.
      end_z: where it ends.
      minimum_traverse_height_start: how high the channels travel first.
      back_channel: the back channel, 0-indexed.
      front_channel: the front channel, 0-indexed.
      tip_type_index: the tip type table entry the tools are picked up as.
    """
    return await self._driver.send_command(
      module="C0",
      command="ZT",
      subsystem=_FirmwareLock.CHANNELS,
      read_timeout=120,
      xs=f"{abs(x_position):05}",
      xd=int(x_position < 0),
      ya=f"{back_channel_y:04}",
      yb=f"{front_channel_y:04}",
      pa=f"{back_channel + 1:02}",
      pb=f"{front_channel + 1:02}",
      tp=f"{begin_z:04}",
      tz=f"{end_z:04}",
      th=f"{minimum_traverse_height_start:04}",
      tt=f"{tip_type_index:02}",
    )

  async def _unchecked_fw_drop_tools(
    self,
    x_position: int,
    back_channel_y: int,
    front_channel_y: int,
    begin_z: int,
    end_z: int,
    minimum_traverse_height_start: int,
    minimum_traverse_height_end: int,
  ):
    """Send the tool discard as it is given, in tenths of a millimetre. `C0 ZS`.

    Sends no `pa`/`pb`, as legacy: the firmware returns the tools from the channels holding them.

    Args:
      x_position: the holder's x; negative sends `xd1`.
      back_channel_y: y of the back channel's tool in the holder.
      front_channel_y: y of the front channel's tool in the holder.
      begin_z: where the deposit begins.
      end_z: where it ends.
      minimum_traverse_height_start: how high the channels travel first.
      minimum_traverse_height_end: where the channels are left.
    """
    return await self._driver.send_command(
      module="C0",
      command="ZS",
      subsystem=_FirmwareLock.CHANNELS,
      read_timeout=120,
      xs=f"{abs(x_position):05}",
      xd=int(x_position < 0),
      ya=f"{back_channel_y:04}",
      yb=f"{front_channel_y:04}",
      tp=f"{begin_z:04}",
      tz=f"{end_z:04}",
      th=f"{minimum_traverse_height_start:04}",
      te=f"{minimum_traverse_height_end:04}",
    )

  async def _move_to_safe_z_after_failure(self) -> None:
    """`pipettes.move_to_safe_z`, logged not raised, so the command's error is the one seen."""
    try:
      await self._pipettes.move_to_safe_z()
    except Exception:
      logger.warning("could not raise the channels to safe Z after the failure")

  async def pick_up_tools_at_location(
    self,
    tool_position_x: float,
    tool_position_z: float,
    front_channel_position_y: float,
    rear_channel_position_y: float,
    *,
    tool_seek: Optional[float] = None,
    minimum_traverse_height_start: Optional[float] = None,
    front_channel: Optional[int] = None,
  ) -> None:
    """Pick up the tools (`C0 ZT`) as tip type 14; to safe Z only if it fails.

    What it picks up is not modelled: `pick_up_tools` takes the deck's tools in the model too.

    Args:
      tool_position_x: the tools' x, in mm.
      tool_position_z: where the pick-up ends, in mm.
      front_channel_position_y: y of the front channel's tool, in mm.
      rear_channel_position_y: y of the back channel's tool, in mm.
      tool_seek: where the pick-up begins, in mm. `tool_position_z + 10` when None.
      minimum_traverse_height_start: how high the channels travel first, in mm.
        `default_minimum_traverse_height` when None.
      front_channel: 0-indexed; the back tool goes on `front_channel - 1`. The front-most when None.

    Raises:
      RuntimeError: If the channels already hold tools, or the iSWAP is not parked.
      HasTipError: If either channel carries something.
      ValueError: If a position, height or the front channel is out of range.
    """
    pipettes = self._pipettes
    if self._tools_taken_from is not None:
      raise RuntimeError("the channels already hold the tools; `drop_tools()` first")
    if front_channel is None:
      front_channel = pipettes.num_channels - 1
    pipettes._require_channel(front_channel)
    if front_channel == 0:
      raise ValueError(
        "front_channel must be 1 or more: the back tool goes on the channel behind it"
      )
    back_channel = front_channel - 1

    if tool_seek is None:
      tool_seek = tool_position_z + 10.0
    if minimum_traverse_height_start is None:
      minimum_traverse_height_start = self.default_minimum_traverse_height
    if not tool_seek > tool_position_z:
      raise ValueError(f"tool_seek ({tool_seek}) must be above tool_position_z ({tool_position_z})")
    pipettes._check_reachable("x", tool_position_x)
    for y in (rear_channel_position_y, front_channel_position_y):
      pipettes._check_reachable("y", y)
    for z in (tool_seek, tool_position_z, minimum_traverse_height_start):
      pipettes._check_reachable("z", z)
    spacing = pipettes._min_spacing_between(back_channel, front_channel)
    if rear_channel_position_y - front_channel_position_y < spacing:
      raise ValueError(
        f"the rear tool must be at least {spacing} mm behind the front one; got rear "
        f"{rear_channel_position_y}, front {front_channel_position_y}"
      )
    carried = await self._tools_on([back_channel, front_channel])
    for channel, tool in zip((back_channel, front_channel), carried):
      if tool is not None:
        raise HasTipError(f"channel {channel} already carries something")
    await pipettes._require_iswap_parked()

    from ..master import CORE_GRIPPER_TIP_TYPE_INDEX

    try:
      await self._unchecked_fw_pick_up_tools(
        x_position=round(tool_position_x * 10),
        back_channel_y=round(rear_channel_position_y * 10),
        front_channel_y=round(front_channel_position_y * 10),
        begin_z=round(tool_seek * 10),
        end_z=round(tool_position_z * 10),
        minimum_traverse_height_start=round(minimum_traverse_height_start * 10),
        back_channel=back_channel,
        front_channel=front_channel,
        tip_type_index=CORE_GRIPPER_TIP_TYPE_INDEX,
      )
    except BaseException:
      await self._move_to_safe_z_after_failure()
      raise
    finally:
      await pipettes._record_after_command()
    # No safe Z on success: ZT leaves the tools' lowest point at `th`, the traverse height.
    self._back_channel, self._front_channel = back_channel, front_channel
    self._tools_taken_from = (
      tool_position_x,
      rear_channel_position_y,
      front_channel_position_y,
      tool_seek,
      tool_position_z,
    )

  async def drop_tools(
    self,
    *,
    move_to_safe_z_first: bool = True,
    minimum_traverse_height_end: Optional[float] = None,
  ) -> None:
    """Put the tools back where `pick_up_tools_at_location` took them (`C0 ZS`), then safe Z.

    Args:
      move_to_safe_z_first: raise to `default_minimum_traverse_height` before travelling; False
        travels at the height the channels stand.
      minimum_traverse_height_end: where to leave the channels, in mm.
        `default_minimum_traverse_height` when None.

    Raises:
      RuntimeError: If no pick-up is remembered, or the iSWAP is not parked.
      ValueError: If a height is out of range.
    """
    self._require_mounted()
    if self._held_resource is not None:
      raise RuntimeError(
        f"the grippers hold {self._held_resource.name}: place it first with `place_resource` "
        "or `return_resource`, then return the tools"
      )
    pipettes = self._pipettes
    # Set with the channel pair, which `_require_mounted` has checked.
    x, rear_y, front_y, seek, end = cast(Tuple[float, ...], self._tools_taken_from)
    start = self.default_minimum_traverse_height if move_to_safe_z_first else 0.0
    if minimum_traverse_height_end is None:
      minimum_traverse_height_end = self.default_minimum_traverse_height
    heights = [seek - _DEPOSIT_BELOW_PICK_UP, end - _DEPOSIT_BELOW_PICK_UP]
    for z in heights + [minimum_traverse_height_end] + ([start] if move_to_safe_z_first else []):
      pipettes._check_reachable("z", z)
    await pipettes._require_iswap_parked()

    try:
      await self._unchecked_fw_drop_tools(
        x_position=round(x * 10),
        back_channel_y=round(rear_y * 10),
        front_channel_y=round(front_y * 10),
        begin_z=round(heights[0] * 10),
        end_z=round(heights[1] * 10),
        minimum_traverse_height_start=round(start * 10),
        minimum_traverse_height_end=round(minimum_traverse_height_end * 10),
      )
    except BaseException:
      await self._move_to_safe_z_after_failure()
      raise
    finally:
      await pipettes._record_after_command()
    await pipettes.move_to_safe_z()
    self._tools_taken_from = None
    self._back_channel = self._front_channel = None

  # -- mounting ------------------------------------------------------------------------------------

  async def _park_tools(self) -> None:
    """Put the tools back where they stood in their holder in the model, in the order they stood.

    Recorded once the device has let go of them: each tool was taken by naming it, so it goes back
    to its origin, where it stood.
    """
    channels, self._parked_from = self._parked_from, []
    shafts = [shaft for ch in channels if (shaft := self._pipettes.shaft(ch)) is not None]
    if not shafts:
      return
    server = self._deck.server
    response = await server.commands.begin_tool_drop(
      spb.BeginToolDropRequest(
        frame=self._deck.ref,
        items=[spb.ToolDropItem(shaft=shaft.ref, origin=True) for shaft in shafts],
        on_tracking_problem=pb.ON_TRACKING_PROBLEM_RECORD,
      )
    )
    await server.commands.resolve_operation(
      spb.ResolveOperationRequest(
        operation_id=response.operation.id,
        outcomes=[spb.ItemOutcome(item=i, succeeded=True) for i in range(len(shafts))],
      )
    )

  async def _mount_tools(
    self, tools: Sequence[handles.Resource], channels: Dict[bytes, int]
  ) -> None:
    """Take the tools out of their holder and onto the channels' shafts in the model, one tool each.

    Recorded once the device has taken them. Each is named, so it is that tool that is taken, and
    dropped back to its origin it goes back where it stood.

    Args:
      tools: the tools, in the order the holder holds them.
      channels: the channel each tool goes on, by the tool's id.
    """
    items = []
    for tool in tools:
      channel = channels.get(tool.id)
      shaft = None if channel is None else self._pipettes.shaft(channel)
      if channel is not None and shaft is not None:
        items.append(spb.ToolPickupItem(source=tool.ref, shaft=shaft.ref))
        self._parked_from.append(channel)
    if not items:
      return
    server = self._deck.server
    response = await server.commands.begin_tool_pickup(
      spb.BeginToolPickupRequest(
        frame=self._deck.ref,
        items=items,
        on_tracking_problem=pb.ON_TRACKING_PROBLEM_RECORD,
      )
    )
    await server.commands.resolve_operation(
      spb.ResolveOperationRequest(
        operation_id=response.operation.id,
        outcomes=[spb.ItemOutcome(item=i, succeeded=True) for i in range(len(items))],
      )
    )

  async def pick_up_tools(self, front_channel: Optional[int] = None) -> None:
    """Take the tools out of the deck's holder and onto two channels.

    Args:
      front_channel: as `pick_up_tools_at_location` takes it.

    Raises:
      RuntimeError: If already mounted, or a channel senses nothing once the pick-up has run.
      TypeError: If the deck carries no holder, or the holder no tools.
    """
    if self._tools_mounted:
      raise RuntimeError("the CoRe gripper tools are already mounted")
    holder, holder_node = await self._holder()
    tools = await holder.get_children(handles.HeadTool)
    if not tools:
      raise TypeError("the holder carries no CO-RE grip tools to pick up")

    # As legacy: the holder's centre x, its channel y centres, and a 10 mm window below the tops.
    deck = self._deck
    queries = [model.query(holder, deck, [handles.anchor("c", "f", "b")])]
    for tool in tools:
      queries.append(
        model.query(tool, deck, [handles.anchor("l", "f", "t"), handles.anchor("c", "c", "b")])
      )
    located = await model.resolve_geometry(deck.server, queries)
    back_y, front_y = holder_node.attributes.holder.channel_y_centers
    loc = to_coordinate(located[0].locations[0])
    top = max(answer.locations[0].z for answer in located[1:])
    await self.pick_up_tools_at_location(
      tool_position_x=loc.x,
      tool_position_z=top - 10.0,
      front_channel_position_y=loc.y + front_y,
      rear_channel_position_y=loc.y + back_y,
      tool_seek=top,
      front_channel=front_channel,
    )
    pair = (cast(int, self._back_channel), cast(int, self._front_channel))

    # A taken tool rides where the channel rides, as a tip does. The back channel takes the rear
    # tool.
    centre_y = {tool.id: answer.locations[1].y for tool, answer in zip(tools, located[1:])}
    rear_first = sorted(tools, key=lambda tool: centre_y[tool.id])
    channels = {tool.id: channel for channel, tool in zip(pair, reversed(rear_first))}
    await self._mount_tools(tools, channels)
    taken = [channel for channel in pair if channel in channels.values()]
    await self._pipettes._record_where_they_stopped("z")

    # The command returning is not the tools being on: asked of the device, once per mount.
    presence = await self._pipettes.sense_tip_presence()
    missing = [channel for channel in taken if not presence[channel]]
    if missing:
      await self._park_tools()
      await self._pipettes._record_where_they_stopped("z")
      raise RuntimeError(
        f"the pick-up ran, but {'channel' if len(missing) == 1 else 'channels'} "
        f"{', '.join(str(c) for c in missing)} sense nothing. The tools are back in their holder "
        "in the model; check the device before running anything."
      )
    self._tools_mounted = True

  async def return_tools(self) -> None:
    """Put the tools back in their holder, if mounted.

    A drop that fails leaves the channels holding them, and the model says so.
    """
    if not self._tools_mounted:
      return
    await self.drop_tools()
    self._tools_mounted = False
    await self._park_tools()
    await self._pipettes._record_where_they_stopped("z")

  @asynccontextmanager
  async def mounted(self, front_channel: Optional[int] = None) -> AsyncIterator["CoreGrippers"]:
    """The tools on for as long as the block runs, and returned on the way out.

    Args:
      front_channel: as `pick_up_tools` takes it.
    """
    await self.pick_up_tools(front_channel=front_channel)
    try:
      yield self
    finally:
      await self.return_tools()

  # ----------------------------------------
  # Resources
  # ----------------------------------------

  # -- firmware ------------------------------------------------------------------------------------

  async def _unchecked_fw_pick_up_resource(
    self,
    x_position: int,
    y_position: int,
    y_gripping_speed: int,
    z_position: int,
    z_speed: int,
    open_gripper_position: int,
    plate_width: int,
    grip_strength: int,
    minimum_traverse_height_start: int,
    minimum_z_position_end: int,
  ):
    """Send the plate pick-up as it is given, in tenths of a millimetre. `C0 ZP`.

    Args:
      x_position: the plate centre's x; negative sends `xd1`.
      y_position: the plate centre's y.
      y_gripping_speed: in tenths of a mm/s.
      z_position: the gripping height.
      z_speed: in tenths of a mm/s.
      open_gripper_position: the jaws' opening before they close.
      plate_width: the width they close to.
      grip_strength: 0 (low) to 99 (high).
      minimum_traverse_height_start: how high the channels travel first.
      minimum_z_position_end: where the channels are left.
    """
    return await self._driver.send_command(
      module="C0",
      command="ZP",
      subsystem=_FirmwareLock.CHANNELS,
      read_timeout=120,
      xs=f"{abs(x_position):05}",
      xd=int(x_position < 0),
      yj=f"{y_position:04}",
      yv=f"{y_gripping_speed:04}",
      zj=f"{z_position:04}",
      zy=f"{z_speed:04}",
      yo=f"{open_gripper_position:04}",
      yg=f"{plate_width:04}",
      yw=f"{grip_strength:02}",
      th=f"{minimum_traverse_height_start:04}",
      te=f"{minimum_z_position_end:04}",
    )

  async def _unchecked_fw_place_resource(
    self,
    x_position: int,
    y_position: int,
    z_position: int,
    press_on_distance: int,
    z_speed: int,
    open_gripper_position: int,
    minimum_traverse_height_start: int,
    minimum_z_position_end: int,
    x_acceleration_level: Optional[int] = None,
  ):
    """Send the plate put-down as it is given, in tenths of a millimetre. `C0 ZR`.

    Args:
      x_position: the plate centre's x; negative sends `xd1`.
      y_position: the plate centre's y.
      z_position: the deposit height.
      press_on_distance: how far past the deposit height to press, 0 to 999.
      z_speed: in tenths of a mm/s.
      open_gripper_position: the fingers' opening to let go.
      minimum_traverse_height_start: how high the channels travel first.
      minimum_z_position_end: where the channels are left.
      x_acceleration_level: 1 to 5; not sent when None.
    """
    parameters: Dict[str, Any] = {"xs": f"{abs(x_position):05}", "xd": int(x_position < 0)}
    if x_acceleration_level is not None:
      parameters["xg"] = f"{x_acceleration_level}"
    parameters.update(
      yj=f"{y_position:04}",
      zj=f"{z_position:04}",
      zi=f"{press_on_distance:03}",
      zy=f"{z_speed:04}",
      yo=f"{open_gripper_position:04}",
      th=f"{minimum_traverse_height_start:04}",
      te=f"{minimum_z_position_end:04}",
    )
    return await self._driver.send_command(
      module="C0", command="ZR", subsystem=_FirmwareLock.CHANNELS, read_timeout=120, **parameters
    )

  async def _unchecked_fw_release_plate(self):
    """Open the gripper and let go of whatever it holds. `C0 ZO`."""
    return await self._driver.send_command(
      module="C0", command="ZO", subsystem=_FirmwareLock.CHANNELS
    )

  # -- by resource ---------------------------------------------------------------------------------

  async def _check_held_move(
    self,
    xyz: Coordinate,
    traverse_heights: Tuple[float, float],
    z_speed: float,
    z_acceleration: float,
  ) -> None:
    """Raise unless a pick-up or place at `xyz` stays within the channels' reach and drive windows.

    `xyz.z` is the fingers' grip line, which rides below the stop disc by the tool's length outside
    the channel: it reaches the stop discs' window shifted down by that, and no lower than the
    tool's bottom on the deck. The traverse heights are the channels' own.

    Raises:
      ValueError: If a position, height, speed or acceleration is out of range.
    """
    pipettes = self._pipettes
    pipettes._check_reachable("x", xyz.x)
    pipettes._check_reachable("y", xyz.y)
    for z in traverse_heights:
      pipettes._check_reachable("z", z)
    c = pipettes.configuration
    (front,) = await self._tools_on([cast(int, self._front_channel)])
    if front is not None and resource_model.grips(front.attributes):
      tool = front.attributes
    else:
      tool = library.get_model(_DEFAULT_TOOL_MODEL).definition.attributes
    lowest = round(c.z_range[0] + resource_model.grip_line_height(tool), 2)
    highest = round(c.z_range[1] - _tool_overhang(tool), 2)
    if not lowest <= xyz.z <= highest:
      raise ValueError(
        f"the grip line reaches {lowest} to {highest} mm with the tools on, not {xyz.z}"
      )
    for checked, (low, high), name in (
      (z_speed, c.z_speed_range, "z_speed"),
      (z_acceleration, c.z_acceleration_range, "z_acceleration"),
    ):
      if not low <= checked <= high:
        raise ValueError(f"{name} must be between {low} and {high}, is {checked}")

  async def _resolve(self, operation: pb.Operation, succeeded: bool) -> None:
    """Commit or roll back a staged move of one resource."""
    server = self._deck.server
    await server.commands.resolve_operation(
      spb.ResolveOperationRequest(
        operation_id=operation.id,
        outcomes=[spb.ItemOutcome(item=0, succeeded=succeeded)],
      )
    )

  async def pick_up_resource(
    self,
    resource: handles.Resource,
    offset: Coordinate = Coordinate.zero(),
    pickup_distance_from_top: Optional[float] = None,
    pickup_distance_from_bottom: Optional[float] = None,
    *,
    minimum_traverse_height_start: Optional[float] = None,
    resource_size_y: Optional[float] = None,
    y_clearance: float = 1.5,
    grip_speed_y: float = 5.0,
    squeeze_mm: float = 1.5,
    grip_strength: Optional[int] = None,
    z_speed: Optional[float] = None,
    z_acceleration: Optional[float] = None,
    minimum_traverse_height_end: Optional[float] = None,
  ) -> None:
    """Grip a resource where the tree has it, and hold it on the front tool in the model (`C0 ZP`).

    The fingers open to `resource_size_y` plus `y_clearance` either side over its centre, come down
    to the grip height, and close to `resource_size_y` less `squeeze_mm` either side.

    Args:
      resource: what to grip.
      offset: added to the grip point, in mm.
      pickup_distance_from_top: how far below its top the fingers close, in mm, at most
        `_MAX_PICKUP_DISTANCE_FROM_TOP`. Exactly one of the two is given.
      pickup_distance_from_bottom: how far above its bottom the fingers close, in mm. Exactly one of
        the two is given.
      minimum_traverse_height_start: the height to travel to it at, in mm.
        `default_minimum_traverse_height` when None.
      resource_size_y: its size in y, the width the fingers grip, in mm, centred on the grip point.
        None reads it from the resource.
      y_clearance: how far each finger stands from the resource as it comes down, in mm.
      grip_speed_y: how fast the fingers close, in mm/s.
      squeeze_mm: how far past its walls each finger closes, in mm.
      grip_strength: 0 (low) to 99 (high). `default_grip_strength` when None.
      z_speed: how fast the channels move in Z, in mm/s. `default_z_speed_with_resource_held` when
        None.
      z_acceleration: the Z drives' acceleration for the command, in mm/s2, then the pipettes'
        default. `default_z_acceleration_with_resource_held` when None.
      minimum_traverse_height_end: the height to leave it at once gripped, in mm.
        `default_minimum_traverse_height` when None.

    Raises:
      RuntimeError: If the tools are not picked up, something is already held, or the iSWAP is not
        parked.
      ValueError: If a position, height, width, speed, acceleration or strength is out of range,
        neither or both pickup distances are given, the grip is more than
        `_MAX_PICKUP_DISTANCE_FROM_TOP` below its top, or `resource` is not on the deck.
    """
    back, front = self._require_mounted()
    if self._held_resource is not None:
      raise RuntimeError(f"the grippers already hold {self._held_resource.name}; place it first")
    pipettes = self._pipettes
    deck = self._deck
    if minimum_traverse_height_start is None:
      minimum_traverse_height_start = self.default_minimum_traverse_height
    if minimum_traverse_height_end is None:
      minimum_traverse_height_end = self.default_minimum_traverse_height
    if grip_strength is None:
      grip_strength = self.default_grip_strength
    if z_speed is None:
      z_speed = self.default_z_speed_with_resource_held
    if z_acceleration is None:
      z_acceleration = self.default_z_acceleration_with_resource_held

    try:
      (located,) = await model.resolve_geometry(deck.server, [model.query(resource, deck)])
    except ServerError as error:
      raise ValueError(f"{resource.name} is not on the deck: {error}") from error
    if resource_size_y is None:
      resource_size_y = located.absolute_size.y
    size_z = located.absolute_size.z
    if pickup_distance_from_top is not None and pickup_distance_from_bottom is None:
      grip_height = size_z - pickup_distance_from_top
    elif pickup_distance_from_bottom is not None and pickup_distance_from_top is None:
      grip_height = pickup_distance_from_bottom
    else:
      raise ValueError(
        "exactly one of pickup_distance_from_top and pickup_distance_from_bottom must be given, "
        f"got {pickup_distance_from_top} and {pickup_distance_from_bottom}"
      )
    if not 0 <= grip_height <= size_z:
      raise ValueError(
        f"the grip must lie within {resource.name}'s height, 0 to {size_z} mm above its bottom, "
        f"is {grip_height} mm"
      )
    from_top = size_z - grip_height
    if from_top > _MAX_PICKUP_DISTANCE_FROM_TOP:
      raise ValueError(
        f"the grip must be at most {_MAX_PICKUP_DISTANCE_FROM_TOP} mm below {resource.name}'s "
        f"top, is {from_top} mm: gripped lower, its top is pressed into the pipetting head the "
        "grippers hang from."
      )
    location = to_coordinate(located.locations[0])
    grip = location + _center(located)
    grip = Coordinate(grip.x, grip.y, grip.z + grip_height) + offset
    await self._check_held_move(
      grip, (minimum_traverse_height_start, minimum_traverse_height_end), z_speed, z_acceleration
    )
    weakest, strongest = self.configuration.grip_strength_range
    if not weakest <= grip_strength <= strongest:
      raise ValueError(
        f"grip_strength must be between {weakest} and {strongest}, is {grip_strength}"
      )
    slowest, fastest = pipettes.configuration.y_speed_range
    if not slowest <= grip_speed_y <= fastest:
      raise ValueError(f"grip_speed_y must be between {slowest} and {fastest}, is {grip_speed_y}")
    if y_clearance < 0 or squeeze_mm < 0:
      raise ValueError(
        f"y_clearance and squeeze_mm must be 0 or more, are {y_clearance} and {squeeze_mm}"
      )
    closed = resource_size_y - 2 * squeeze_mm
    if closed <= 0:
      raise ValueError(f"the fingers would close to {closed} mm; squeeze_mm is too large")
    await pipettes._require_iswap_parked()

    response = await deck.server.commands.get_resources(
      spb.GetResourcesRequest(resources=[resource.ref], ancestors=True)
    )
    taken_from: Optional[Tuple[handles.Resource, Optional[Coordinate], bool]] = None
    if len(response.nodes) > 1:
      parent = response.nodes[1]
      taken_from = (
        deck.server.handle_from_node(parent, ()),
        model.location_of(response.nodes[0]),
        parent.attributes.kind in _HOLDER_KINDS,
      )

    # The resource moves onto the front tool as the fingers close on it; staged when there is a
    # modelled tool to carry it.
    tool = await self._front_tool()
    staged: Optional[pb.Operation] = None
    if tool is not None:
      grip_from = spb.Grip(distance_from_bottom=grip_height)
      staged = (
        await deck.server.commands.begin_resource_pickup(
          spb.BeginResourcePickupRequest(
            frame=deck.ref,
            resource=resource.ref,
            carrier=tool.ref,
            grip=grip_from,
          )
        )
      ).operation
    succeeded = False
    try:
      async with pipettes._temporary_z_drive_profile(
        acceleration=z_acceleration, channels=[back, front]
      ):
        await self._unchecked_fw_pick_up_resource(
          x_position=round(grip.x * 10),
          y_position=round(grip.y * 10),
          y_gripping_speed=round(grip_speed_y * 10),
          z_position=round(grip.z * 10),
          z_speed=round(z_speed * 10),
          open_gripper_position=round((resource_size_y + 2 * y_clearance) * 10),
          plate_width=round(closed * 10),
          grip_strength=grip_strength,
          minimum_traverse_height_start=round(minimum_traverse_height_start * 10),
          minimum_z_position_end=round(minimum_traverse_height_end * 10),
        )
      succeeded = True
    finally:
      if staged is not None:
        await self._resolve(staged, succeeded)
      await pipettes._record_after_command()
    self._grip_height = grip_height
    self._holding_resource_width = resource_size_y
    self._held_resource = resource
    self._taken_from = taken_from
    await self._hang_held_resource_on_the_front_tool()

  async def place_resource(
    self,
    to: Union[handles.Resource, Coordinate],
    offset: Coordinate = Coordinate.zero(),
    *,
    minimum_traverse_height_start: Optional[float] = None,
    x_acceleration_level: Optional[int] = None,
    z_speed: Optional[float] = None,
    z_acceleration: Optional[float] = None,
    press_on_distance: float = 0.0,
    y_clearance: float = 1.5,
    minimum_traverse_height_end: Optional[float] = None,
  ) -> None:
    """Place the held resource, and the tree follows once it is let go (`C0 ZR`).

    Args:
      to: where it goes: the resource it goes into, e.g. a plate carrier site, or a `Coordinate`,
        the deck position its centre-centre-bottom goes to, where it joins the deck.
      offset: added to where it is let go, in mm.
      minimum_traverse_height_start: the height to carry it at, in mm.
        `default_minimum_traverse_height` when None.
      x_acceleration_level: 1 to 5. Not sent when None.
      z_speed: how fast the channels move in Z, in mm/s. `default_z_speed_with_resource_held` when
        None.
      z_acceleration: the Z drives' acceleration for the command, in mm/s2, then the pipettes'
        default. `default_z_acceleration_with_resource_held` when None.
      press_on_distance: how far past where it is let go to press it down, 0 to 99.9 mm.
      y_clearance: how far each finger opens past the resource's walls to let go, in mm.
      minimum_traverse_height_end: where to leave the channels, in mm.
        `default_minimum_traverse_height` when None.

    Raises:
      RuntimeError: If nothing is held, the iSWAP is not parked, or the destination refuses it.
      ValueError: If a position, height, speed, acceleration, level or distance is out of range, a
        `Coordinate` falls inside a resource on the deck, or it cannot be placed into the
        destination as that is.
    """
    held, grip_height = self._held_resource, self._grip_height
    if held is None or grip_height is None or self._holding_resource_width is None:
      raise RuntimeError("Not holding anything; pick_up_resource first")
    pipettes = self._pipettes
    deck = self._deck
    back, front = cast(int, self._back_channel), cast(int, self._front_channel)
    if minimum_traverse_height_start is None:
      minimum_traverse_height_start = self.default_minimum_traverse_height
    if minimum_traverse_height_end is None:
      minimum_traverse_height_end = self.default_minimum_traverse_height
    if z_speed is None:
      z_speed = self.default_z_speed_with_resource_held
    if z_acceleration is None:
      z_acceleration = self.default_z_acceleration_with_resource_held

    request = spb.BeginResourcePlaceRequest(
      frame=deck.ref,
      resource=held.ref,
      grip=spb.Grip(distance_from_bottom=grip_height),
    )
    if isinstance(to, Coordinate):
      # The centre-bottom goes to `to`, so the resource's own origin goes this far from it.
      (located,) = await model.resolve_geometry(deck.server, [model.query(held, deck)])
      center = _center(located)
      request.destination_location.CopyFrom(to_vec3(to - Coordinate(center.x, center.y, 0)))
    else:
      request.destination_resource.CopyFrom(to.ref)
    try:
      staged = await deck.server.commands.begin_resource_place(request)
    except ServerError as error:
      # The arms move, and what they carry goes with them: only what stands on the deck is in the
      # way of a coordinate, and only what the destination takes goes into it.
      if isinstance(to, Coordinate) or error.problem == pb.PROBLEM_WRONG_KIND:
        raise ValueError(str(error)) from error
      raise RuntimeError(str(error)) from error

    succeeded = False
    try:
      release = to_coordinate(staged.grip_location) + offset
      await self._check_held_move(
        release,
        (minimum_traverse_height_start, minimum_traverse_height_end),
        z_speed,
        z_acceleration,
      )
      if x_acceleration_level is not None and not 1 <= x_acceleration_level <= 5:
        raise ValueError(f"x_acceleration_level must be between 1 and 5, is {x_acceleration_level}")
      if not 0 <= press_on_distance <= 99.9:
        raise ValueError(f"press_on_distance must be between 0 and 99.9, is {press_on_distance}")
      if y_clearance < 0:
        raise ValueError(f"y_clearance must be 0 or more, is {y_clearance}")
      await pipettes._require_iswap_parked()

      try:
        async with pipettes._temporary_z_drive_profile(
          acceleration=z_acceleration, channels=[back, front]
        ):
          await self._unchecked_fw_place_resource(
            x_position=round(release.x * 10),
            y_position=round(release.y * 10),
            z_position=round(release.z * 10),
            press_on_distance=round(press_on_distance * 10),
            z_speed=round(z_speed * 10),
            open_gripper_position=round((self._holding_resource_width + 2 * y_clearance) * 10),
            minimum_traverse_height_start=round(minimum_traverse_height_start * 10),
            minimum_z_position_end=round(minimum_traverse_height_end * 10),
            x_acceleration_level=x_acceleration_level,
          )
        succeeded = True
      finally:
        await pipettes._record_after_command()
    finally:
      await self._resolve(staged.operation, succeeded)
    self._clear_held_state()

  async def drop_resource(self, *args: Any, **kwargs: Any) -> None:
    """Deprecated: use `place_resource`."""
    warnings.warn(
      "`drop_resource` is deprecated and will be removed in the release after next; use "
      "`place_resource`.",
      DeprecationWarning,
      stacklevel=2,
    )
    await self.place_resource(*args, **kwargs)

  async def return_resource(
    self,
    offset: Coordinate = Coordinate.zero(),
    *,
    minimum_traverse_height_start: Optional[float] = None,
    x_acceleration_level: Optional[int] = None,
    z_speed: Optional[float] = None,
    z_acceleration: Optional[float] = None,
    press_on_distance: float = 0.0,
    y_clearance: float = 1.5,
    minimum_traverse_height_end: Optional[float] = None,
  ) -> None:
    """Put the held resource back where :meth:`pick_up_resource` took it from.

    Args:
      offset: as :meth:`place_resource` takes it, and every other argument too.

    Raises:
      RuntimeError: If nothing is held, or it was not taken from a parent in the tree.
    """
    if self._taken_from is None or self._held_resource is None:
      raise RuntimeError(
        "nothing to return it to: return_resource needs a pick_up_resource of a resource that "
        "had a parent."
      )
    kwargs: Dict[str, Any] = {
      "offset": offset,
      "minimum_traverse_height_start": minimum_traverse_height_start,
      "x_acceleration_level": x_acceleration_level,
      "z_speed": z_speed,
      "z_acceleration": z_acceleration,
      "press_on_distance": press_on_distance,
      "y_clearance": y_clearance,
      "minimum_traverse_height_end": minimum_traverse_height_end,
    }
    parent, location, is_holder = self._taken_from
    if is_holder:
      await self.place_resource(parent, **kwargs)
      return
    # Anywhere else it stood is a point on the deck.
    deck = self._deck
    # The deck itself is not asked where it is: it is the frame, and a question about it reads
    # everything on it.
    queries = [model.query(self._held_resource, deck)]
    if parent != deck:
      queries.append(model.query(parent, deck))
    located = await model.resolve_geometry(deck.server, queries)
    center = _center(located[0])
    origin = to_coordinate(located[1].locations[0]) if parent != deck else Coordinate.zero()
    lfb = origin + (location or Coordinate.zero())
    await self.place_resource(lfb + Coordinate(center.x, center.y, 0), **kwargs)

  # -- probing ------------------------------------------------------------------------------------

  async def probe_resource_exists_using_ztouch(
    self,
    location: Coordinate,
    resource: handles.Resource,
    gripper_y_margin: float = 1.0,
    offset: Coordinate = Coordinate.zero(),
    minimum_traverse_height_start: Optional[float] = None,
    minimum_traverse_height_end: Optional[float] = None,
    enable_recovery: bool = True,
  ) -> bool:
    """Push the open jaws down onto `resource`'s centre: stalling on it is finding it (`C0 ZP`).

    Args:
      location: where the resource's left-front-bottom is, in deck coordinates.
      resource: the resource to check for.
      gripper_y_margin: how far inside each of its front and back walls the jaws come down, in mm.
      offset: added to its centre, in mm.
      minimum_traverse_height_start: how high the channels travel first, in mm.
        `default_minimum_traverse_height` when None.
      minimum_traverse_height_end: where to leave the channels, in mm.
        `default_minimum_traverse_height` when None.
      enable_recovery: ask on the console whether to check again when it is not found.

    Returns:
      True if found.

    Raises:
      RuntimeError: If the tools are not picked up.
      ValueError: If the jaw width is out of range, the check is aborted, or ZP fails otherwise.
    """
    back, front = self._require_mounted()
    pipettes = self._pipettes
    if minimum_traverse_height_start is None:
      minimum_traverse_height_start = self.default_minimum_traverse_height
    if minimum_traverse_height_end is None:
      minimum_traverse_height_end = self.default_minimum_traverse_height

    (located,) = await model.resolve_geometry(resource.server, [model.query(resource)])
    size = located.size
    center = location + Coordinate(size.x / 2, size.y / 2, size.z / 2) + offset
    y_width_to_gripper_bump = located.absolute_size.y - gripper_y_margin * 2
    min_width = pipettes._min_spacing_between(back, front)
    max_width = round(located.absolute_size.y)
    if not min_width <= y_width_to_gripper_bump <= max_width:
      raise ValueError(
        f"width between channels must be between {min_width} and {max_width} mm, is "
        f"{y_width_to_gripper_bump}"
      )

    resource_found = False
    try_counter = 0
    try:
      while not resource_found:
        try:
          await self._unchecked_fw_pick_up_resource(
            x_position=round(center.x * 10),
            y_position=round(center.y * 10),
            y_gripping_speed=50,
            z_position=round(center.z * 10),
            z_speed=600,
            open_gripper_position=round(y_width_to_gripper_bump * 10),
            plate_width=round(y_width_to_gripper_bump * 10),
            grip_strength=20,
            minimum_traverse_height_start=round(minimum_traverse_height_start * 10),
            minimum_z_position_end=round(minimum_traverse_height_end * 10),
          )
        except STARFirmwareError as exc:
          # Trace 62 is the channels' Z drive stalling: the jaws came down on the resource.
          for module_error in exc.errors.values():
            if module_error.trace_information == 62:
              resource_found = True
            else:
              raise ValueError(f"Unexpected error encountered: {exc}") from exc
        else:
          if enable_recovery:
            print(
              f"\nWARNING: Resource '{resource.name}' not found at center"
              f" location {(center.x, center.y, center.z)} during check no {try_counter}."
            )
            user_prompt = input(
              "Have you checked resource is present?"
              "\n [ yes ] -> machine will check location again"
              "\n [ abort ] -> machine will abort run\n Answer:"
            )
            if user_prompt == "yes":
              try_counter += 1
            elif user_prompt == "abort":
              raise ValueError(
                f"Resource '{resource.name}' not found at center"
                f" location {(center.x, center.y, center.z)}"
                " & error not resolved -> aborted resource movement."
              )
          else:
            return False
    finally:
      await pipettes._record_after_command()

    return True
