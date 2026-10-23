from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

from pylabrobot.opentrons.decks import DeckSlots, slot_in
from pylabrobot.opentrons.heads import Mounted, PipetteShafts
from pylabrobot.opentrons.model import (
  Liquid,
  Named,
  Ref,
  TipFacts,
  Tree,
  anchor,
  coordinate,
  locate,
  read,
  tracks_tips,
)
from pylabrobot.opentrons.tracking import track_liquid_transfer, validate_liquid_transfer
from pylabrobot.opentrons.types import Mount
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import HasTipError, NoTipError
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.v1 import types_pb2 as pb

if TYPE_CHECKING:
  from pylabrobot.opentrons.ot2.ot2 import OT2

K = pb.ResourceKind


@dataclass(frozen=True)
class _PipetteSpec:
  minimum_volume: float
  maximum_volume: float
  channels: int
  default_aspiration_flow_rate: float
  default_dispense_flow_rate: float


_PIPETTE_SPECS = {
  "p10_single": _PipetteSpec(1, 10, 1, 5, 10),
  "p10_multi": _PipetteSpec(1, 10, 8, 5, 10),
  "p20_single_gen2": _PipetteSpec(1, 20, 1, 3.78, 7.56),
  "p20_multi_gen2": _PipetteSpec(1, 20, 8, 7.6, 7.6),
  "p50_single": _PipetteSpec(5, 50, 1, 25, 50),
  "p50_multi": _PipetteSpec(5, 50, 8, 25, 50),
  "p300_single": _PipetteSpec(30, 300, 1, 150, 300),
  "p300_multi": _PipetteSpec(30, 300, 8, 150, 300),
  "p300_single_gen2": _PipetteSpec(20, 300, 1, 46.43, 92.86),
  "p300_multi_gen2": _PipetteSpec(20, 300, 8, 94, 94),
  "p1000_single": _PipetteSpec(100, 1000, 1, 500, 1000),
  "p1000_single_gen2": _PipetteSpec(100, 1000, 1, 137.35, 274.7),
}


_COMPATIBLE_TIP_CAPACITIES: Dict[float, set] = {
  10: {10},
  20: {10, 20},
  50: {200},
  300: {200, 300},
  1000: {1000},
}

# The anchor a tip command, and a container's liquid, are located from.
_SPOT_ANCHOR = anchor("c", "c", "b")
_CAVITY_ANCHOR = anchor("c", "c", "cb")
_CORNERS = [anchor(x, y, z) for x in ("l", "r") for y in ("f", "b") for z in ("b", "t")]


def _require_finite_coordinate(name: str, coordinate: Coordinate) -> None:
  if not all(math.isfinite(axis) for axis in coordinate):
    raise ValueError(f"{name} coordinates must be finite")


class _OT2Pipette(ABC):
  """Shared motion, command sequencing, and transactional tracking for mounted OT-2 pipettes.

  The tips a pipette holds are on its shafts in the resource store (``shafts``); the spots they
  were picked up from are kept here, for ``return_tips``.
  """

  def __init__(
    self,
    robot: OT2,
    mount: Mount,
    name: str,
    pipette_id: str,
    shafts: PipetteShafts,
  ):
    try:
      spec = _PIPETTE_SPECS[name]
    except KeyError as error:
      raise ValueError(f"Unsupported OT-2 pipette {name!r}") from error

    if spec.channels != self.num_channels:
      raise ValueError(f"{name} requires a {spec.channels}-channel pipette class")

    self.robot = robot
    self._run = robot._require_run()
    self.mount = mount
    self.name = name
    self.pipette_id = pipette_id
    self._spec = spec
    self.shafts = shafts
    self._tip_origins: Tuple[handles.Resource, ...] = ()

  @property
  def minimum_volume(self) -> float:
    """Minimum supported transfer volume, in µL."""
    return self._spec.minimum_volume

  @property
  def maximum_volume(self) -> float:
    """Maximum supported transfer volume, in µL."""
    return self._spec.maximum_volume

  @property
  @abstractmethod
  def num_channels(self) -> int:
    """Number of nozzles exposed by this pipette class."""
    ...

  @property
  def store(self):
    return self.robot.store

  @property
  def deck(self) -> handles.Deck:
    return self.robot.deck

  async def has_tip(self) -> bool:
    """Whether the pipette holds a tip, as the resource store has it."""
    return bool((await self.shafts.mounted()).held)

  async def get_mounted_tips(self) -> List[Optional[handles.Tip]]:
    """Each nozzle's tip as the resource store holds it, or None."""
    return await self.shafts.tip_handles()

  def _require_active(self) -> None:
    if self.robot._require_run() is not self._run:
      raise RuntimeError("This pipette belongs to an earlier OT-2 run; use the current pipette")

  def _require_tips(self, mounted: Mounted) -> List[TipFacts]:
    """Return the mounted tips, requiring at least one tip."""
    if not mounted.held:
      raise RuntimeError(f"The {self.mount} pipette does not have a tip")
    return mounted.held

  def _validate_targets(
    self, targets: Sequence[handles.Resource], tree: Tree, mounted: Optional[Mounted]
  ) -> None:
    """Require one target per nozzle."""
    if len(targets) != self.num_channels:
      raise ValueError(f"{self.name} requires {self.num_channels} targets in nozzle order")

  def _validate_nozzle_positions(self, positions: Sequence[Coordinate]) -> None:
    """Require finite target coordinates."""
    for position in positions:
      _require_finite_coordinate("target", position)

  async def _tip_rack(self, tip_spots: Sequence[handles.Resource], tree: Tree) -> pb.ResourceNode:
    """Validate tip spots, read with their ancestors in ``tree``, and return their rack."""
    self._validate_targets(tip_spots, tree, None)
    rack = tree.parent(tree.node(tip_spots[0]))
    if rack is None or rack.attributes.kind != K.RESOURCE_KIND_TIP_RACK:
      raise ValueError("tip spots must be assigned to a tip rack")
    if slot_in(self.deck, tree, rack) is None:
      raise ValueError("tip rack must be assigned directly to an OT-2 deck slot")
    return rack

  def _validate_volume(self, volume: float) -> float:
    volume = float(volume)
    if not self.minimum_volume <= volume <= self.maximum_volume:
      raise ValueError(
        f"volume must be between {self.minimum_volume:g} and {self.maximum_volume:g} µL "
        f"for {self.name}"
      )
    return volume

  def can_use_tip(self, tip: TipFacts) -> bool:
    """Whether the tip capacity is supported by this pipette."""
    return tip.maximal_volume in _COMPATIBLE_TIP_CAPACITIES[self.maximum_volume]

  def _validate_position(self, location: Coordinate) -> None:
    """Check the reference nozzle target in the robot frame before staging an operation."""
    _require_finite_coordinate("location", location)
    if location.z < 0:
      raise ValueError("location.z must be non-negative")
    # Nozzle alignment fixes every target relative to the reference nozzle.
    # Checking its offset therefore checks the common head center for the whole selection.
    channel_offset = self.robot.geometry.channel_y_offsets()[0] if self.num_channels == 8 else 0.0
    if not self.robot.geometry.can_reach_position(self.mount, location, channel_offset):
      bounds = self.robot.geometry.single_channel_reach(self.mount)
      raise ValueError(
        f"{location} with nozzle Y offset {channel_offset:g} is outside the "
        f"{self.mount} mount's reachable x/y region {bounds}"
      )

  async def _move_to(
    self,
    location: Coordinate,
    speed: Optional[float] = None,
    minimum_z_height: Optional[float] = None,
    force_direct: bool = False,
  ) -> None:
    self._validate_position(location)
    if speed is not None and (not math.isfinite(speed) or speed <= 0):
      raise ValueError("speed must be finite and greater than zero")
    if minimum_z_height is not None and (
      not math.isfinite(minimum_z_height) or minimum_z_height < 0
    ):
      raise ValueError("minimum_z_height must be finite and non-negative")

    await self._run.move_to(
      self.pipette_id,
      location,
      speed=speed,
      minimum_z_height=minimum_z_height,
      force_direct=force_direct,
    )

  async def move_to(
    self,
    location: Coordinate,
    speed: Optional[float] = None,
    minimum_z_height: Optional[float] = None,
    force_direct: bool = False,
  ) -> None:
    """Move to an absolute robot-frame coordinate, then retract to at least traversal height."""
    async with self.robot._operation_lock:
      self._require_active()
      await self._move_to(
        location=location,
        speed=speed,
        minimum_z_height=minimum_z_height,
        force_direct=force_direct,
      )
      await self._retract_to_traversal_height()

  async def _spot_locations(self, spots: Sequence[Ref]) -> List[Coordinate]:
    """Each spot's centre bottom in the deck frame: one read."""
    geometries = await locate(self.store, [(spot, [_SPOT_ANCHOR]) for spot in spots], self.deck)
    return [coordinate(g.locations[0]) for g in geometries]

  def _tip_command_location(self, spot_location: Coordinate, offset: Coordinate) -> Coordinate:
    """Convert a tip command's well-bottom offset to the reference nozzle's robot position."""
    return self.robot._deck_to_robot_frame(spot_location + offset)

  async def _check_tip_pickup(
    self, tip_spots: Sequence[handles.Resource], tree: Tree, tip: TipFacts, offset: Coordinate
  ) -> None:
    """Check the pickup target before loading labware or changing tips."""
    (location,) = await self._spot_locations(tip_spots[:1])
    self._validate_position(self._tip_command_location(location, offset + Coordinate(z=tip.size.z)))

  @staticmethod
  def _tip_to_take(tree: Tree, spot: handles.Resource) -> TipFacts:
    """The tip a spot gives: the one it holds, or a fresh one when it does not track tips.

    Raises:
      NoTipError: It tracks tips and holds none.
    """
    node = tree.node(spot)
    held = tree.tool(node)
    if held is not None:
      return TipFacts.of(held)
    if tracks_tips(node) or not node.attributes.tip_spot.HasField("prototype_tip"):
      raise NoTipError(f"{node.attributes.name} holds no tip")
    return TipFacts.of_attributes(node.attributes.tip_spot.prototype_tip)

  async def _pick_up_tips(
    self,
    tip_spots: Sequence[handles.Resource],
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Pick up one tip per nozzle with one command, then retract to traversal height."""
    async with self.robot._operation_lock:
      self._require_active()
      if (await self.shafts.mounted()).held:
        raise RuntimeError(f"The {self.mount} pipette already has a tip")
      tip_spots = tuple(tip_spots)
      tree = await read(self.store, tip_spots, depth=1, ancestors=True)
      rack = await self._tip_rack(tip_spots, tree)
      tips = tuple(self._tip_to_take(tree, spot) for spot in tip_spots)
      tip = tips[0]
      if not self.can_use_tip(tip):
        raise ValueError(f"{self.name} cannot use a {tip.maximal_volume:g} µL-capacity tip")
      if any(not other.model for other in tips):
        raise ValueError("Tip models must be defined for comparison.")
      if any(other.model != tip.model for other in tips):
        raise ValueError("All nozzles must use the same tip type")
      offset = offset or Coordinate.zero()
      _require_finite_coordinate("offset", offset)
      await self._check_tip_pickup(tip_spots, tree, tip, offset)
      operation = await self.shafts.begin_pickup(
        self.deck, [(spot.id, channel) for channel, spot in enumerate(tip_spots)]
      )
      try:
        await self.robot._load_tip_rack(Named.of(rack), tip, tree)
        binding = self.robot._require_labware().get(Named.of(rack))
        await self._run.pick_up_tip(
          self.pipette_id,
          binding.labware_id,
          tree.node(tip_spots[0]).attributes.identifier,
          offset + Coordinate(z=tip.size.z),
        )
      except BaseException:
        await self.shafts.resolve(operation, succeeded=False)
        raise

      await self.shafts.resolve(operation, succeeded=True)
      self._tip_origins = tip_spots
      await self._retract_to_traversal_height()

  async def _drop_tips(
    self,
    tip_spots: Sequence[handles.Resource],
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Drop all mounted tips into a rack with one command, then retract."""
    async with self.robot._operation_lock:
      self._require_active()
      await self._drop_tips_locked(tuple(tip_spots), offset, allow_nonzero_volume)

  def _check_tip_volumes(self, mounted: Mounted, allow_nonzero_volume: bool) -> List[TipFacts]:
    """Require mounted tips and reject disposal of liquid unless explicitly allowed."""
    tips = self._require_tips(mounted)
    if not allow_nonzero_volume:
      if any(tip.tracked and tip.volume > 0 for tip in tips):
        raise ValueError("A mounted tip still contains liquid")
    return tips

  async def _drop_tips_locked(
    self,
    tip_spots: Sequence[handles.Resource],
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Drop tips while the robot's operation lock is held."""
    mounted = await self.shafts.mounted()
    tips = self._check_tip_volumes(mounted, allow_nonzero_volume)
    tree = await read(self.store, tip_spots, depth=1, ancestors=True)
    self._validate_targets(tip_spots, tree, mounted)
    rack = await self._tip_rack(tip_spots, tree)
    tip = tips[0]
    offset = offset or Coordinate.zero()
    _require_finite_coordinate("offset", offset)
    (location,) = await self._spot_locations(tip_spots[:1])
    self._validate_position(self._tip_command_location(location, offset + Coordinate(z=10)))
    for spot in tip_spots:
      node = tree.node(spot)
      if tracks_tips(node) and tree.tool(node) is not None:
        raise HasTipError(f"{node.attributes.name} already has a tip.")
    operation = await self.shafts.begin_drop(
      self.deck, [(channel, spot.id) for spot, channel in zip(tip_spots, mounted.channels)]
    )
    try:
      await self.robot._load_tip_rack(Named.of(rack), tip, tree)
      binding = self.robot._require_labware().get(Named.of(rack))
      await self._run.drop_tip(
        self.pipette_id,
        binding.labware_id,
        tree.node(tip_spots[0]).attributes.identifier,
        offset + Coordinate(z=10),
      )
    except BaseException:
      await self.shafts.resolve(operation, succeeded=False)
      raise

    await self.shafts.resolve(operation, succeeded=True)
    self._tip_origins = ()
    await self._retract_to_traversal_height()

  async def _retract_to_traversal_height(self) -> None:
    """Raise the nozzle or mounted tip from its reported position under the operation lock."""
    position = await self._run.get_position(self.pipette_id)
    _require_finite_coordinate("position", position)
    if position.z < self.robot.traversal_height:
      await self._move_to(
        Coordinate(position.x, position.y, self.robot.traversal_height),
        force_direct=True,
      )

  async def _return_tips(
    self,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Return all mounted tips to their pickup positions, then retract."""
    async with self.robot._operation_lock:
      self._require_active()
      if not self._tip_origins:
        raise RuntimeError("The mounted tip's origin is unknown")
      await self._drop_tips_locked(self._tip_origins, offset, allow_nonzero_volume)

  async def _fixed_trash(self) -> Optional[handles.Resource]:
    """The deck's fixed trash, where the store puts discarded tips; None when the deck has none."""
    try:
      trash: handles.Resource = await self.store.get("trash", root=self.deck)
      return trash
    except StoreError as error:
      if error.problem != pb.PROBLEM_NOT_FOUND:
        raise
      return None

  async def _discard_tips(
    self,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Discard all mounted tips into fixed trash and retract to traversal height."""
    async with self.robot._operation_lock:
      self._require_active()
      mounted = await self.shafts.mounted()
      tips = self._check_tip_volumes(mounted, allow_nonzero_volume)
      offset = offset or Coordinate.zero()
      _require_finite_coordinate("offset", offset)
      trash = await self._fixed_trash()
      operation = None
      if trash is not None and trash.kind == K.RESOURCE_KIND_TRASH:
        operation = await self.shafts.begin_drop(
          self.deck, [(channel, trash.id) for channel in mounted.channels]
        )
      try:
        await self._run.discard_tip_in_fixed_trash(self.pipette_id, offset + Coordinate(z=10))
      except BaseException:
        await self.shafts.resolve(operation, succeeded=False)
        raise
      if operation is not None:
        await self.shafts.resolve(operation, succeeded=True)
      else:
        await self.shafts.discard(tips)
      self._tip_origins = ()
      await self._retract_to_traversal_height()

  async def _liquid_targets(
    self,
    containers: Sequence[handles.Resource],
    offset: Coordinate,
    liquid_height: float,
    mounted: Mounted,
  ) -> Tuple[List[Liquid], Coordinate]:
    """Resolve one container per nozzle and the reference nozzle's liquid position."""
    tree = await read(self.store, containers)
    self._validate_targets(containers, tree, mounted)
    _require_finite_coordinate("offset", offset)
    if not math.isfinite(liquid_height) or liquid_height < 0:
      raise ValueError("liquid_height must be finite and non-negative")
    geometries = await locate(
      self.store, [(c, [_CAVITY_ANCHOR]) for c in containers], frame=self.deck
    )
    locations = [
      self.robot._deck_to_robot_frame(
        coordinate(g.locations[0]) + offset + Coordinate(z=liquid_height)
      )
      for g in geometries
    ]
    self._validate_nozzle_positions(locations)
    self._validate_position(locations[0])
    return [Liquid.of(tree.node(c)) for c in containers], locations[0]

  def _transfers(self, containers: Sequence[Liquid], mounted: Mounted) -> List[Tuple[bytes, bytes]]:
    return [
      (container.id, self.shafts.shafts[channel])
      for container, channel in zip(containers, mounted.channels)
    ]

  async def _aspirate(
    self,
    containers: Sequence[handles.Resource],
    volume: float,
    flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Aspirate ``volume`` per mounted tip from its container, then retract."""
    async with self.robot._operation_lock:
      self._require_active()
      mounted = await self.shafts.mounted()
      tips = [tip.liquid for tip in self._require_tips(mounted)]
      volume = self._validate_volume(volume)
      flow_rate = self._spec.default_aspiration_flow_rate if flow_rate is None else float(flow_rate)
      if not math.isfinite(flow_rate) or flow_rate <= 0:
        raise ValueError("flow_rate must be finite and greater than zero")
      offset = offset or Coordinate.zero()
      liquids, location = await self._liquid_targets(containers, offset, liquid_height, mounted)

      validate_liquid_transfer(list(liquids), list(tips), volume)
      transfers = self._transfers(liquids, mounted)
      async with track_liquid_transfer(self.store, self.deck, True, transfers, volume):
        await self._move_to(
          location,
          minimum_z_height=self.robot.traversal_height,
        )
        await self._run.aspirate_in_place(self.pipette_id, volume, flow_rate)
      await self._retract_to_traversal_height()

  async def _dispense(
    self,
    containers: Sequence[handles.Resource],
    volume: float,
    flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Dispense ``volume`` per mounted tip into its container, then retract."""
    async with self.robot._operation_lock:
      self._require_active()
      mounted = await self.shafts.mounted()
      tips = [tip.liquid for tip in self._require_tips(mounted)]
      volume = self._validate_volume(volume)
      flow_rate = self._spec.default_dispense_flow_rate if flow_rate is None else float(flow_rate)
      if not math.isfinite(flow_rate) or flow_rate <= 0:
        raise ValueError("flow_rate must be finite and greater than zero")
      offset = offset or Coordinate.zero()
      liquids, location = await self._liquid_targets(containers, offset, liquid_height, mounted)

      validate_liquid_transfer(list(tips), list(liquids), volume)
      transfers = self._transfers(liquids, mounted)
      async with track_liquid_transfer(self.store, self.deck, False, transfers, volume):
        await self._move_to(
          location,
          minimum_z_height=self.robot.traversal_height,
        )
        await self._run.dispense_in_place(self.pipette_id, volume, flow_rate)
      await self._retract_to_traversal_height()

  async def _mix(
    self,
    containers: Sequence[handles.Resource],
    volume: float,
    repetitions: int,
    aspiration_flow_rate: Optional[float] = None,
    dispense_flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Mix ``volume`` per mounted tip in its container, then retract."""
    async with self.robot._operation_lock:
      self._require_active()
      mounted = await self.shafts.mounted()
      tips = [tip.liquid for tip in self._require_tips(mounted)]
      volume = self._validate_volume(volume)
      if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
      aspiration_flow_rate = (
        self._spec.default_aspiration_flow_rate
        if aspiration_flow_rate is None
        else float(aspiration_flow_rate)
      )
      dispense_flow_rate = (
        self._spec.default_dispense_flow_rate
        if dispense_flow_rate is None
        else float(dispense_flow_rate)
      )
      if (
        not math.isfinite(aspiration_flow_rate)
        or not math.isfinite(dispense_flow_rate)
        or aspiration_flow_rate <= 0
        or dispense_flow_rate <= 0
      ):
        raise ValueError("flow rates must be finite and greater than zero")

      offset = offset or Coordinate.zero()
      liquids, location = await self._liquid_targets(containers, offset, liquid_height, mounted)
      transfers = self._transfers(liquids, mounted)
      for repetition in range(repetitions):
        if repetition == 0:
          validate_liquid_transfer(list(liquids), list(tips), volume)
        async with track_liquid_transfer(self.store, self.deck, True, transfers, volume):
          if repetition == 0:
            await self._move_to(location, minimum_z_height=self.robot.traversal_height)
          await self._run.aspirate_in_place(self.pipette_id, volume, aspiration_flow_rate)
        async with track_liquid_transfer(self.store, self.deck, False, transfers, volume):
          await self._run.dispense_in_place(self.pipette_id, volume, dispense_flow_rate)
      await self._retract_to_traversal_height()


class OT2SingleChannelPipette(_OT2Pipette):
  """A single-channel OT-2 pipette, discovered and created by :meth:`OT2.setup`."""

  @property
  def num_channels(self) -> int:
    """One independently addressed nozzle."""
    return 1

  async def tip(self) -> Optional[handles.Tip]:
    """The single-channel mounted tip, or ``None`` when no tip is mounted."""
    return (await self.get_mounted_tips())[0]

  async def pick_up_tip(
    self,
    tip_spot: handles.TipSpot,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Pick up one tip from a tip rack and retract to at least traversal height."""
    await self._pick_up_tips([tip_spot], offset)

  async def drop_tip(
    self,
    tip_spot: handles.TipSpot,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Drop into a tip-rack position and retract vertically to at least traversal height."""
    await self._drop_tips([tip_spot], offset, allow_nonzero_volume)

  async def return_tip(
    self,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Return the mounted single tip to its pickup position, then retract."""
    await self._return_tips(offset, allow_nonzero_volume)

  async def discard_tip(
    self,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Discard a single tip into fixed trash and retract to traversal height."""
    await self._discard_tips(offset, allow_nonzero_volume)

  async def aspirate(
    self,
    container: handles.Container,
    volume: float,
    flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Aspirate ``volume`` from a container, then retract."""
    await self._aspirate([container], volume, flow_rate, liquid_height, offset)

  async def dispense(
    self,
    container: handles.Container,
    volume: float,
    flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Dispense ``volume`` into a container, then retract."""
    await self._dispense([container], volume, flow_rate, liquid_height, offset)

  async def mix(
    self,
    container: handles.Container,
    volume: float,
    repetitions: int,
    aspiration_flow_rate: Optional[float] = None,
    dispense_flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Mix ``volume`` in a container, then retract."""
    await self._mix(
      [container],
      volume,
      repetitions,
      aspiration_flow_rate,
      dispense_flow_rate,
      liquid_height,
      offset,
    )


class OT2_8ChannelPipette(_OT2Pipette):
  """An eight-channel OT-2 pipette with a rigid nozzle layout.

  Instances are discovered and created by :meth:`OT2.setup`. Pickup targets run
  consecutively from nozzle 0 toward nozzle 7. Subsequent targets match the mounted
  tips in nozzle order. Volume, flow rate, liquid height, and offset
  apply equally to every mounted tip.
  """

  @property
  def num_channels(self) -> int:
    """Eight nozzles at 9 mm pitch."""
    return 8

  async def tips(self) -> Tuple[handles.Tip, ...]:
    """Mounted tips in nozzle order, or an empty tuple when no tips are mounted."""
    return tuple(tip for tip in await self.get_mounted_tips() if tip is not None)

  def _validate_targets(
    self, targets: Sequence[handles.Resource], tree: Tree, mounted: Optional[Mounted]
  ) -> None:
    """Require pickup targets or one target per mounted tip on the same resource."""
    if not 1 <= len(targets) <= self.num_channels:
      raise ValueError("Eight-channel operations require between 1 and 8 targets")
    if mounted is not None and mounted.held and len(targets) != len(mounted.held):
      raise ValueError("Targets must match all mounted tips in nozzle order")
    if len({target.id for target in targets}) != len(targets):
      raise ValueError("Each nozzle must address a distinct target")
    parent = tree.node(targets[0]).parent_id
    if any(tree.node(target).parent_id != parent for target in targets):
      raise ValueError("All targets must belong to the same resource")

  def _validate_nozzle_positions(self, positions: Sequence[Coordinate]) -> None:
    """Require targets to align with the rigid head's 9 mm back-to-front pitch."""
    super()._validate_nozzle_positions(positions)
    channel_offsets = self.robot.geometry.channel_y_offsets()
    for position, channel_offset in zip(positions, channel_offsets):
      expected = positions[0] + Coordinate(y=channel_offset - channel_offsets[0])
      if any(abs(actual - target) > 0.01 for actual, target in zip(position, expected)):
        raise ValueError("Targets must align in nozzle order at 9 mm pitch and equal height")

  async def _tip_rack(self, tip_spots: Sequence[handles.Resource], tree: Tree) -> pb.ResourceNode:
    """Validate a column aligned with the selected or mounted nozzles and return its rack."""
    rack = await super()._tip_rack(tip_spots, tree)
    if rack.attributes.itemized.num_items_y != self.num_channels:
      raise ValueError("Eight-channel tip operations require an eight-row tip rack")
    column = tree.node(tip_spots[0]).attributes.identifier[1:]
    if any(tree.node(spot).attributes.identifier[1:] != column for spot in tip_spots):
      raise ValueError("Eight-channel tip operations require a single rack column")
    self._validate_nozzle_positions(await self._spot_locations(tip_spots))
    return rack

  async def _check_head8_pickup(self, tip_spots: Sequence[handles.Resource], tree: Tree) -> None:
    """Reject occupied tip spots under undeclared nozzles below a contiguous selection.

    The supplied tips implicitly address channels 0 through len(tip_spots)-1.
    Every other nozzle within the rack also picks up any tip beneath it.
    """
    channel_offsets = self.robot.geometry.channel_y_offsets()
    head8_pitch = channel_offsets[0] - channel_offsets[1]
    num_nozzles = self.num_channels
    use_channels = list(range(len(tip_spots)))

    rack = tree.parent(tree.node(tip_spots[0]))
    if (
      rack is None
      or rack.attributes.kind != K.RESOURCE_KIND_TIP_RACK
      or any(tree.node(s).parent_id != rack.id for s in tip_spots)
    ):
      raise ValueError("OT-2 8-channel pickup must come from a single tip rack.")

    rack_tree = await read(self.store, [rack.id], depth=2)
    all_spots = [c for c in rack_tree.children(rack_tree.node(rack.id)) if c.attributes.identifier]
    locations = dict(
      zip(
        [spot.id for spot in all_spots],
        await self._spot_locations([spot.id for spot in all_spots]),
      )
    )

    col_x = locations[tip_spots[0].id].x
    if any(abs(locations[s.id].x - col_x) > 0.5 for s in tip_spots):
      raise ValueError(
        "OT-2 8-channel pickup must be within a single column (all tipspots must share x)."
      )

    col_spots = [s for s in all_spots if abs(locations[s.id].x - col_x) < 0.5]
    top_y = max(locations[s.id].y for s in col_spots)

    def row_of(y: float) -> int:
      """Map a tip spot's Y coordinate to its row in this column."""
      return int(round((top_y - y) / head8_pitch))

    spot_by_row = {row_of(locations[s.id].y): s for s in col_spots}

    # The declared tipspots must run consecutively down the column in channel order.
    offsets = {row_of(locations[spot.id].y) - ch for spot, ch in zip(tip_spots, use_channels)}
    if len(offsets) != 1:
      raise ValueError(
        "OT-2 8-channel pickup tipspots must run consecutively down the column in channel order "
        "(channel 0 = topmost well, then one row per channel at 9 mm pitch). The given tipspots "
        "do not line up 1:1 with the channels."
      )
    top_row = offsets.pop()

    # The head also grabs occupied tipspots below the selection within its eight-nozzle reach.
    used = set(use_channels)
    extras: List[pb.ResourceNode] = []
    for nozzle in range(num_nozzles):
      if nozzle in used:
        continue
      spot = spot_by_row.get(nozzle + top_row)
      if spot is not None and rack_tree.tool(spot) is not None:
        extras.append(spot)
    if extras:
      where = ", ".join(spot.attributes.name for spot in extras)
      raise ValueError(
        f"OT-2 8-channel pickup would also grab undeclared tips at {where}. The head fills "
        f"from channel 0 down toward row H, and these occupied tipspots sit below your "
        f"selection within its 8-nozzle reach, so the hardware would pick them up too. "
        f"Extend the selection down to include them or clear those spots first."
      )

  async def _check_tip_pickup(
    self, tip_spots: Sequence[handles.Resource], tree: Tree, tip: TipFacts, offset: Coordinate
  ) -> None:
    """Reject labware overlapping the pickup footprint near the bare nozzle height.

    The full nozzle span is padded by 5 mm in XY and 10 mm vertically. This is a
    conservative destination check, not a swept-path or complete pipette-body model.
    """
    await super()._check_tip_pickup(tip_spots, tree, tip, offset)
    await self._check_head8_pickup(tip_spots, tree)
    (spot_location,) = await self._spot_locations(tip_spots[:1])
    primary = spot_location + offset
    nozzle_z = primary.z + tip.size.z - tip.fitting_depth
    x_min, x_max = primary.x - 5, primary.x + 5
    channel_offsets = self.robot.geometry.channel_y_offsets()
    y_min = primary.y + channel_offsets[-1] - channel_offsets[0] - 5
    y_max = primary.y + 5
    rack_id = tree.node(tip_spots[0]).parent_id
    slots = await DeckSlots.read(self.deck)
    labwares = [n for n in slots.occupants.values() if n is not None and n.id != rack_id]
    if not labwares:
      return
    contents = await read(self.store, [n.id for n in labwares], depth=-1)
    resources = [each for labware in labwares for each in contents.walk(contents.node(labware.id))]
    geometries = await locate(
      self.store, [(each.id, _CORNERS) for each in resources], frame=self.deck
    )
    for resource, geometry in zip(resources, geometries):
      corners = [coordinate(location) for location in geometry.locations]
      for corner in corners:
        _require_finite_coordinate("surrounding resource", corner)
      if (
        max(c.x for c in corners) >= x_min
        and min(c.x for c in corners) <= x_max
        and max(c.y for c in corners) >= y_min
        and min(c.y for c in corners) <= y_max
        and max(c.z for c in corners) >= nozzle_z - 10
      ):
        raise ValueError(
          f"Eight-channel pickup footprint overlaps resource {resource.attributes.name!r}"
        )

  async def pick_up_tips(
    self,
    tip_spots: Sequence[handles.Resource],
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Pick up consecutive tips using nozzles starting at 0, then retract.

    Occupied tip spots under the remaining nozzles always reject the pickup.
    """
    await self._pick_up_tips(tip_spots, offset)

  async def drop_tips(
    self,
    tip_spots: Sequence[handles.Resource],
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Drop all mounted tips into a rack with one command, then retract."""
    await self._drop_tips(tip_spots, offset, allow_nonzero_volume)

  async def return_tips(
    self,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Return all mounted tips to their pickup positions, then retract."""
    await self._return_tips(offset, allow_nonzero_volume)

  async def discard_tips(
    self,
    offset: Optional[Coordinate] = None,
    allow_nonzero_volume: bool = False,
  ) -> None:
    """Discard all mounted tips into fixed trash and retract to traversal height."""
    await self._discard_tips(offset, allow_nonzero_volume)

  async def aspirate(
    self,
    containers: Sequence[handles.Resource],
    volume: float,
    flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Aspirate ``volume`` per mounted tip from containers in nozzle order, then retract."""
    await self._aspirate(tuple(containers), volume, flow_rate, liquid_height, offset)

  async def dispense(
    self,
    containers: Sequence[handles.Resource],
    volume: float,
    flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Dispense ``volume`` per mounted tip into containers in nozzle order, then retract."""
    await self._dispense(tuple(containers), volume, flow_rate, liquid_height, offset)

  async def mix(
    self,
    containers: Sequence[handles.Resource],
    volume: float,
    repetitions: int,
    aspiration_flow_rate: Optional[float] = None,
    dispense_flow_rate: Optional[float] = None,
    liquid_height: float = 0,
    offset: Optional[Coordinate] = None,
  ) -> None:
    """Mix ``volume`` per mounted tip in containers in nozzle order, then retract."""
    await self._mix(
      tuple(containers),
      volume,
      repetitions,
      aspiration_flow_rate,
      dispense_flow_rate,
      liquid_height,
      offset,
    )
