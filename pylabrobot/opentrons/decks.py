"""The Opentrons decks in a resource store: their definitions, and their slots.

Each slot of a deck is a resource holder named `<deck>_slot_<slot>`: "C1" to "D4" on a Flex, 1 to
12 on an OT-2. Labware is put in a slot by assigning it to the slot's holder, and the slot it is
in is read from the holder it hangs from.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, cast

from pylabrobot.opentrons.model import Tree, anchor, locate, read
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb

K = pb.ResourceKind

Slot = Union[str, int]

# -- the Flex deck -------------------------------------------------------------------------------

# A-D followed by 1-4.
_FLEX_SLOT_PATTERN = re.compile(r"^[A-D][1-4]$")

# Rows from front (D, index 0) to rear (A, index 3).
_FLEX_ROW_ORDER = ["D", "C", "B", "A"]

# Slot corners (mm) from the ot3_standard deck definition v5 cutout positions. The origin is the
# front-left corner of slot D1.
FLEX_SLOT_LOCATIONS: Dict[str, Dict[str, float]] = {
  "D1": {"x": 0.0, "y": 0.0, "z": 0.0},
  "D2": {"x": 164.0, "y": 0.0, "z": 0.0},
  "D3": {"x": 328.0, "y": 0.0, "z": 0.0},
  "C1": {"x": 0.0, "y": 107.0, "z": 0.0},
  "C2": {"x": 164.0, "y": 107.0, "z": 0.0},
  "C3": {"x": 328.0, "y": 107.0, "z": 0.0},
  "B1": {"x": 0.0, "y": 214.0, "z": 0.0},
  "B2": {"x": 164.0, "y": 214.0, "z": 0.0},
  "B3": {"x": 328.0, "y": 214.0, "z": 0.0},
  "A1": {"x": 0.0, "y": 321.0, "z": 0.0},
  "A2": {"x": 164.0, "y": 321.0, "z": 0.0},
  "A3": {"x": 328.0, "y": 321.0, "z": 0.0},
}

# The staging slots, column 4.
FLEX_STAGING_LOCATIONS: Dict[str, Dict[str, float]] = {
  "D4": {"x": 492.0, "y": 0.0, "z": 14.5},
  "C4": {"x": 492.0, "y": 107.0, "z": 14.5},
  "B4": {"x": 492.0, "y": 214.0, "z": 14.5},
  "A4": {"x": 492.0, "y": 321.0, "z": 14.5},
}

# A Flex slot's footprint (mm).
FLEX_SLOT_WIDTH = 128.0
FLEX_SLOT_DEPTH = 86.0

_FLEX_DECK_SIZE = Coordinate(855.0, 582.0, 0.0)

# The clearance z assumed when no operation height is given: measured at 51.3 mm on hardware (tip
# at the bottom of a flat well plate, A1 nozzle to the deck surface).
_DEFAULT_CLEARANCE_Z = 50.0
_MIN_NOZZLE_CLEARANCE = 20.0

# The size of the trash a Flex is given when the robot reports a bin and the deck has none.
FLEX_TRASH_SIZE = Coordinate(FLEX_SLOT_WIDTH, FLEX_SLOT_DEPTH, 82.0)

# -- the OT-2 deck -------------------------------------------------------------------------------

_OT2_SLOT_SIZE = Coordinate(128.0, 86.0, 0.0)

# The fixed trash (opentrons_1_trash_1100ml_fixed) is larger than a slot and overhangs it, so slot
# 12's holder takes the trash footprint.
_OT2_TRASH_SIZE = Coordinate(172.86, 165.86, 82.0)

# The OT-2 slot grid in the robot frame, where slot 1's corner is the origin.
_OT2_BASE_SLOT_LOCATIONS = [
  Coordinate(x=0.0, y=0.0, z=0.0),
  Coordinate(x=132.5, y=0.0, z=0.0),
  Coordinate(x=265.0, y=0.0, z=0.0),
  Coordinate(x=0.0, y=90.5, z=0.0),
  Coordinate(x=132.5, y=90.5, z=0.0),
  Coordinate(x=265.0, y=90.5, z=0.0),
  Coordinate(x=0.0, y=181.0, z=0.0),
  Coordinate(x=132.5, y=181.0, z=0.0),
  Coordinate(x=265.0, y=181.0, z=0.0),
  Coordinate(x=0.0, y=271.5, z=0.0),
  Coordinate(x=132.5, y=271.5, z=0.0),
  Coordinate(x=265.0, y=271.5, z=0.0),
]
# The deck plate corner sits at (-115.65, -68.03) in the robot frame, and is the deck's origin.
_OT2_SLOT_CORNER_OFFSET = Coordinate(x=115.65, y=68.03, z=0.0)

OT2_SLOT_LOCATIONS: List[Coordinate] = [
  base + _OT2_SLOT_CORNER_OFFSET for base in _OT2_BASE_SLOT_LOCATIONS
]

# -- definitions ---------------------------------------------------------------------------------


def _holder(name: str, size: Coordinate, location: Coordinate) -> pb.ResourceDefinition:
  return build.resource(
    name,
    size,
    kind=K.RESOURCE_KIND_RESOURCE_HOLDER,
    location=location,
    category="resource_holder",
    type_name="ResourceHolder",
    holder=pb.HolderSpec(child_location=pb.Vec3(), capacity=1),
  )


def trash(
  name: str, size: Coordinate, location: Optional[Coordinate] = None
) -> pb.ResourceDefinition:
  """A trash: a container that takes anything, its volume tracked."""
  return build.resource(
    name,
    size,
    kind=K.RESOURCE_KIND_TRASH,
    location=location,
    category="trash",
    type_name="Trash",
    container=pb.ContainerSpec(max_volume=math.inf, material_z_thickness=0.0),
    state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
  )


def flex_deck(name: str = "flex_deck") -> pb.ResourceDefinition:
  """The Flex deck: a holder for each of the 12 slots A1-D3 and the 4 staging slots A4-D4."""
  holders = [
    _holder(
      f"{name}_slot_{slot}", Coordinate(FLEX_SLOT_WIDTH, FLEX_SLOT_DEPTH, 0), Coordinate(**loc)
    )
    for slot, loc in {**FLEX_SLOT_LOCATIONS, **FLEX_STAGING_LOCATIONS}.items()
  ]
  return build.resource(
    name,
    _FLEX_DECK_SIZE,
    kind=K.RESOURCE_KIND_DECK,
    location=Coordinate.zero(),
    category="deck",
    type_name="FlexDeck",
    children=holders,
  )


def ot2_deck(name: str = "ot2_deck", with_trash: bool = True) -> pb.ResourceDefinition:
  """The OT-2 deck: a holder for each of the 12 slots, and the fixed trash in slot 12."""
  holders = []
  for i, location in enumerate(OT2_SLOT_LOCATIONS):
    is_trash_slot = i == 11 and with_trash
    holder = _holder(
      f"{name}_slot_{i + 1}", _OT2_TRASH_SIZE if is_trash_slot else _OT2_SLOT_SIZE, location
    )
    if is_trash_slot:
      # The trash opentrons operations address is held in a container of its own.
      container = trash("trash_container", _OT2_TRASH_SIZE, Coordinate.zero())
      container.children.append(trash("trash", _OT2_TRASH_SIZE, Coordinate.zero()))
      holder.children.append(container)
    holders.append(holder)
  return build.resource(
    name,
    Coordinate(624.3, 565.2, 0),
    kind=K.RESOURCE_KIND_DECK,
    location=Coordinate.zero(),
    category="deck",
    type_name="OTDeck",
    children=holders,
  )


async def create_flex_deck(store: ResourceStore, name: str = "flex_deck") -> handles.Deck:
  """Make a Flex deck in a store."""
  return cast(handles.Deck, await store.create(flex_deck(name), name=name))


async def create_ot2_deck(
  store: ResourceStore, name: str = "ot2_deck", with_trash: bool = True
) -> handles.Deck:
  """Make an OT-2 deck in a store."""
  return cast(handles.Deck, await store.create(ot2_deck(name, with_trash), name=name))


# -- slots ---------------------------------------------------------------------------------------


def validate_flex_slot(slot: str) -> str:
  """A Flex slot, upper-cased.

  Raises:
    ValueError: It is not A1-D3 or A4-D4.
  """
  slot = slot.upper()
  if _FLEX_SLOT_PATTERN.match(slot):
    return slot
  raise ValueError(
    f"Invalid slot identifier '{slot}'. "
    f"Must be A1–D3 (standard) or A4–D4 (staging). "
    f"Examples: 'C1', 'A3', 'B4'."
  )


def _validate(slot: Slot) -> Slot:
  if isinstance(slot, str):
    return validate_flex_slot(slot)
  if slot not in range(1, 13):
    raise ValueError("slot must be between 1 and 12")
  return slot


def _slot_from_holder(deck_name: str, holder_name: str) -> Optional[Slot]:
  prefix = f"{deck_name}_slot_"
  if not holder_name.startswith(prefix):
    return None
  slot = holder_name[len(prefix) :]
  return int(slot) if slot.isdigit() else slot


def get_slot_location(slot: str) -> Dict[str, float]:
  """The corner of a Flex slot, in the deck's frame."""
  slot = validate_flex_slot(slot)
  if slot in FLEX_SLOT_LOCATIONS:
    return FLEX_SLOT_LOCATIONS[slot]
  return FLEX_STAGING_LOCATIONS[slot]


@dataclass(frozen=True)
class DeckSlots:
  """A deck's slots and what is in each, from one read.

  Attributes:
    deck: The deck.
    holders: Each slot's holder.
    occupants: What each slot holds, or None.
  """

  deck: handles.Deck
  holders: Dict[Slot, pb.ResourceNode]
  occupants: Dict[Slot, Optional[pb.ResourceNode]]

  @staticmethod
  async def read(deck: handles.Deck) -> DeckSlots:
    tree = await read(deck.store, [deck], depth=2)
    holders: Dict[Slot, pb.ResourceNode] = {}
    occupants: Dict[Slot, Optional[pb.ResourceNode]] = {}
    for holder in tree.children(tree.node(deck)):
      slot = _slot_from_holder(deck.name, holder.attributes.name)
      if slot is None:
        continue
      holders[slot] = holder
      children = tree.children(holder)
      occupants[slot] = children[0] if children else None
    return DeckSlots(deck, holders, occupants)

  def slot_of(self, resource_id: bytes) -> Optional[Slot]:
    """The slot a resource is in, held directly by its holder."""
    for slot, occupant in self.occupants.items():
      if occupant is not None and occupant.id == resource_id:
        return slot
    return None

  def slot_of_holder(self, holder_id: bytes) -> Optional[Slot]:
    for slot, holder in self.holders.items():
      if holder.id == holder_id:
        return slot
    return None

  def occupant(self, slot: Slot) -> Optional[pb.ResourceNode]:
    return self.occupants[_validate(slot)]

  def trash(self) -> Optional[pb.ResourceNode]:
    """The first trash a slot holds."""
    return next(
      (
        n
        for n in self.occupants.values()
        if n is not None and n.attributes.kind == K.RESOURCE_KIND_TRASH
      ),
      None,
    )


async def get_slot_holder(deck: handles.Deck, slot: Slot) -> handles.ResourceHolder:
  """The holder of a slot, the destination labware is assigned to."""
  slot = _validate(slot)
  # Found under the deck rather than by root name: the deck may stand inside a larger tree.
  holder = await deck.get_resource(f"{deck.name}_slot_{slot}")
  return cast(handles.ResourceHolder, holder)


async def assign_child_at_slot(deck: handles.Deck, resource: handles.Resource, slot: Slot) -> None:
  """Put a resource in a slot.

  Raises:
    ValueError: The slot is not one of the deck's, or it is occupied.
  """
  slot = _validate(slot)
  slots = await DeckSlots.read(deck)
  occupant = slots.occupant(slot)
  if occupant is not None:
    if isinstance(slot, str):
      raise ValueError(f"Slot {slot} is already occupied by '{occupant.attributes.name}'.")
    raise ValueError(f"Spot {slot} is already occupied")
  holder = deck.store.handle_from_node(slots.holders[slot], ())
  await holder.assign_child_resource(resource)


async def unassign_child_at_slot(deck: handles.Deck, slot: Slot) -> None:
  """Take what a slot holds out of it; it becomes a root of its own."""
  occupant = (await DeckSlots.read(deck)).occupant(slot)
  if occupant is not None:
    await deck.store.handle_from_node(occupant, ()).unassign()


async def get_slot(deck: handles.Deck, resource: handles.Resource) -> Optional[Slot]:
  """The slot a resource is in, or None when no slot holds it directly."""
  tree = await read(deck.store, [resource], ancestors=True)
  return slot_in(deck, tree, tree.node(resource))


def slot_in(deck: handles.Deck, tree: Tree, node: pb.ResourceNode) -> Optional[Slot]:
  """The slot a resource read with its ancestors is in, or None when no slot holds it directly."""
  holder = tree.parent(node)
  if holder is None or holder.parent_id != deck.id:
    return None
  return _slot_from_holder(deck.name, holder.attributes.name)


async def get_resource_at_slot(deck: handles.Deck, slot: Slot) -> Optional[handles.Resource]:
  """What a slot holds, or None."""
  occupant = (await DeckSlots.read(deck)).occupant(slot)
  if occupant is None:
    return None
  return await deck.store.get_by_id(occupant.id)


async def get_trash_area(deck: handles.Deck) -> handles.Trash:
  """The trash a slot of the deck holds.

  Raises:
    ValueError: No slot holds a trash.
  """
  found = (await DeckSlots.read(deck)).trash()
  if found is None:
    raise ValueError("No trash area configured on this deck.")
  return cast(handles.Trash, deck.store.handle_from_node(found, ()))


# -- clearance -----------------------------------------------------------------------------------


async def check_partial_nozzle_clearance(
  deck: handles.Deck,
  slot: str,
  primary_nozzle: str,
  mounted_count: int,
  operation_z: Optional[float] = None,
) -> None:
  """Reserve the slot beside unused nozzles of a partial 8-channel layout.

  Front-anchored layouts reserve the rear slot; rear-anchored layouts reserve the front one. A tip
  rack there is refused unless an operation height is given, and anything there is refused unless
  the unused nozzle ends clear its top by 20 mm. `operation_z` is the absolute height of the
  unused nozzle ends; without it a conservative pickup height is assumed.

  Raises:
    ValueError: The layout is not partial, the nozzle is neither A1 nor H1, or the neighbour is
      too close.
  """
  if not 1 <= mounted_count < 8:
    raise ValueError("Partial layouts require between one and seven mounted tips")
  if primary_nozzle not in ("A1", "H1"):
    raise ValueError(f"Unsupported partial primary nozzle: {primary_nozzle}")
  slot = validate_flex_slot(slot)
  row, column = slot[0], slot[1]
  row_index = _FLEX_ROW_ORDER.index(row)
  if primary_nozzle == "H1":
    # The front nozzle leaves the others reaching toward the rear.
    if row_index + 1 >= len(_FLEX_ROW_ORDER):
      return
    danger_slot = f"{_FLEX_ROW_ORDER[row_index + 1]}{column}"
  else:
    if row_index - 1 < 0:
      return
    danger_slot = f"{_FLEX_ROW_ORDER[row_index - 1]}{column}"

  resource = (await DeckSlots.read(deck)).occupant(danger_slot)
  if resource is None:
    return
  direction = "behind" if primary_nozzle == "H1" else "in front of"
  name = resource.attributes.name

  if operation_z is None and resource.attributes.kind == K.RESOURCE_KIND_TIP_RACK:
    raise ValueError(
      f"Collision risk: partial-tip operation at {slot} "
      f"with nozzle {primary_nozzle} — the {8 - mounted_count} unused nozzles "
      f"extend into slot {danger_slot}, which contains tip rack "
      f"'{name}'. Inactive nozzles would engage tips. "
      f"Move the tip rack or use a different nozzle direction."
    )

  corners = [anchor(x, y, z) for x in ("l", "r") for y in ("f", "b") for z in ("b", "t")]
  (geometry,) = await locate(deck.store, [(resource.id, corners)], frame=deck)
  resource_z = max(location.z for location in geometry.locations)
  clearance_z = operation_z if operation_z is not None else _DEFAULT_CLEARANCE_Z
  gap = clearance_z - resource_z
  if gap < _MIN_NOZZLE_CLEARANCE:
    raise ValueError(
      f"Collision risk: partial-tip operation at {slot} "
      f"with nozzle {primary_nozzle} — the {8 - mounted_count} unused nozzles "
      f"extend into slot {danger_slot} at Z={clearance_z:.0f}mm, "
      f"which contains '{name}' (height {resource_z:.0f}mm). "
      f"Clearance is {gap:.1f}mm; at least {_MIN_NOZZLE_CLEARANCE:.0f}mm is required. "
      f"Move '{name}' to a different slot, or use a slot with "
      f"no tall labware {direction} it."
    )


async def check_single_nozzle_clearance(
  deck: handles.Deck,
  slot: str,
  primary_nozzle: str = "H1",
  operation_z: Optional[float] = None,
) -> None:
  """The partial-layout clearance check for a single mounted tip."""
  await check_partial_nozzle_clearance(deck, slot, primary_nozzle, 1, operation_z)


async def check_deck_clearance(deck: handles.Deck, slot: str, operation: str = "move") -> None:
  """Refuse a pipetting operation at a slot that holds no labware.

  Raises:
    ValueError: The operation needs labware and the slot holds none.
  """
  slot = validate_flex_slot(slot)
  if (await DeckSlots.read(deck)).occupant(slot) is None and operation in (
    "pick_up_tips",
    "aspirate",
    "dispense",
  ):
    raise ValueError(
      f"Cannot {operation} at slot {slot}: no labware assigned. "
      f"Use assign_child_at_slot(deck, resource, slot='{slot}') first."
    )
