"""The Prep's deck as a resource store holds it: its definition, and its parts found by name.

`prep_deck` builds the deck a Prep carries - eight labware spots, the calibration block, the
waste block with its liquid waste trough, teaching needle and CO-RE gripper holder, the waste bin,
and the three waste positions - as one definition for `ResourceStore.create`. `read_prep_deck`
finds those parts again on a deck in a store.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional, Sequence

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles, library
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

# What a Prep's deck is called among the store's types, so a driver knows one when it is given one.
PREP_DECK_TYPE = "PrepDeck"

# How big the deck is, in mm. Its height is the channels' working volume from the deck surface:
# they travel from 18.03 to 167.5 mm, and the deck configuration reports the same Z range, as read
# off PRPAA1087 on 2026-09-13.
PREP_DECK_SIZE = Coordinate(300.0, 394.0, 167.5)

# Up to this height, in mm, a resource is under a traversing channel whatever tip it carries: the
# stop discs at Z safety, 167.5, less the 87.1 mm a 1000 uL tip reaches below them, with margin.
PREP_SAFE_DECK_HEIGHT = 75.0

# The labware spots' grid, probed on PRPAA1087 on 2026-09-20.
PREP_FIRST_SLOT_LOCATION = Coordinate(-4.20, -1.52, 0.0)
PREP_SPOT_PITCH_X = 140.0
PREP_SPOT_PITCH_Y = 95.0

# The steel block between the two columns, measured off the deck: a 6 x 6 mm top 22 mm up, flaring
# to 8.49 mm below 14 mm. Placed by that top's left front corner, from the deck's origin.
PREP_CALIBRATION_BLOCK_LOCATION = Coordinate(129.55, 183.73, 0.0)

# Where tips are dropped, measured off the block: 12.5 x 292 x 75 mm, standing where the parked
# back tool sits on its nominal centre, x 290.0, y 275.5.
PREP_WASTE_BLOCK_SIZE = Coordinate(12.5, 292.0, 75.0)
PREP_WASTE_BLOCK_LOCATION = Coordinate(282.25, -4.25, 0.0)

# The bin under the tip drop, beside the waste block: its left face on the block's right face, its
# front 35 mm in front of the block's and its top 4 mm below the block's top.
PREP_WASTE_BIN_SIZE = Coordinate(134.0, 280.0, 122.0)
PREP_WASTE_BIN_LOCATION = Coordinate(282.25 + 12.5, -4.25 - 35.0, 75.0 - 4.0 - 122.0)

# The liquid waste trough fills the waste block from the tip drop's back edge, 132.7 mm from the
# block's front, to the teaching needle's front edge, at y 214.29 on the deck, its top level with
# the block's: 25 mm deep.
PREP_TIP_DROP_SIZE_Y = 132.7
PREP_TEACHING_NEEDLE_SITE_Y = 214.29
PREP_LIQUID_WASTE_SIZE_Z = 25.0

# The teaching needle's spot on the waste block: PRPAA1087's 6 x 6 mm deck site, at the height its
# collar rests, as every tip spot's is.
PREP_TEACHING_NEEDLE_LOCATION = Coordinate(4.46, 217.29, 75.75)
PREP_TEACHING_NEEDLE_MODEL = "hamilton_teaching_needle_300uL"

# The CO-RE gripper holder on the waste block: it overhangs the block's left face by 4 mm, its flat
# 40 mm up. The two tools stand 18 mm apart, centred on it.
PREP_CORE_GRIPPER_HOLDER_MODEL = "prep_core_gripper_holder"
PREP_CORE_GRIPPER_HOLDER_LOCATION = Coordinate(-4.0, 249.5, 37.0)
PREP_CORE_GRIPPER_TOOL_SPACING = 18.0

# PRPAA1087's waste sites (DeckConfiguration), by the waste position each is: the driver moves them
# to the connected device's at setup.
PREP_WASTE_POSITIONS = (("waste_rear", 30.0), ("waste_front", 10.0), ("waste_mph", 112.0))
PREP_WASTE_POSITION_X = 287.0
PREP_WASTE_POSITION_Z = 68.4
PREP_WASTE_POSITION_SIZE = Coordinate(6.0, 6.0, 0.0)

PREP_SPOT_MODEL = "hamilton_prep_resourceholder"

# Holder metadata: where each channel's tool stands along the holder's y, from its front.
BACK_CHANNEL_Y_CENTER = "back_channel_y_center"
FRONT_CHANNEL_Y_CENTER = "front_channel_y_center"
# Deck metadata: the prefix its parts' names carry.
NAME_PREFIX = "name_prefix"


def component_name(name: str, name_prefix: Optional[str]) -> str:
  """A deck part's name, qualified with the deck's prefix when it has one."""
  return name if name_prefix is None else f"{name_prefix}_{name}"


def spot_names(name_prefix: Optional[str]) -> List[str]:
  """The eight labware spots' names, column-major: `spot_0_0` first, `spot_1_3` last."""
  return [
    component_name(f"spot_{column}_{row}", name_prefix) for column in range(2) for row in range(4)
  ]


def _renamed(definition: pb.ResourceDefinition, name: str) -> pb.ResourceDefinition:
  """A copy of a model's definition, called `name`, with `{name}` in every name below it replaced."""
  copy = pb.ResourceDefinition()
  copy.CopyFrom(definition)
  copy.attributes.name = name

  def visit(children: Sequence[pb.ResourceDefinition]) -> None:
    for child in children:
      child.attributes.name = child.attributes.name.replace("{name}", name)
      visit(child.children)

  visit(copy.children)
  return copy


def _from_model(model: str, name: str, location: Coordinate) -> pb.ResourceDefinition:
  """One of PLR's models, called `name`, placed at `location` in its parent."""
  definition = _renamed(library.get_model(model).definition, name)
  definition.attributes.location.CopyFrom(build.vec3(location))
  return definition


def _trash(name: str, size: Coordinate, location: Coordinate, **kwargs) -> pb.ResourceDefinition:
  """A trash: it takes whatever is put in it, of any volume."""
  return build.resource(
    name,
    size,
    kind=pb.RESOURCE_KIND_TRASH,
    location=location,
    type_name="Trash",
    container=pb.ContainerSpec(max_volume=float("inf"), material_z_thickness=0.0),
    state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
    **kwargs,
  )


def _teaching_needle_spot(name: str) -> pb.ResourceDefinition:
  """The teaching needle's spot, the needle standing in it: part of the deck, as on a STAR's."""
  needle = library.get_model(PREP_TEACHING_NEEDLE_MODEL).definition
  prototype = pb.ResourceAttributes()
  prototype.CopyFrom(needle.attributes)
  prototype.name = name
  # The needle rests by its collar, centred on the spot, as `TipSpot` seats a tip.
  spot_size = Coordinate(6.0, 6.0, 0.0)
  tip_size = needle.attributes.size
  tip = _renamed(needle, f"{name}#0")
  tip.attributes.location.CopyFrom(
    build.vec3(
      Coordinate(
        spot_size.x / 2 - tip_size.x / 2,
        spot_size.y / 2 - tip_size.y / 2,
        needle.attributes.tip.collar_height - tip_size.z,
      )
    )
  )
  return build.resource(
    name,
    spot_size,
    kind=pb.RESOURCE_KIND_TIP_SPOT,
    location=PREP_TEACHING_NEEDLE_LOCATION,
    type_name="TipSpot",
    category="teaching_needle",
    tip_spot=pb.TipSpotSpec(prototype_tip=prototype),
    children=[tip],
    state=pb.ResourceState(tip_tracking_enabled=True, tips_made=1),
  )


def _core_gripper_holder(name: str) -> pb.ResourceDefinition:
  """The holder the CO-RE grip tools park in, saying where each channel's tool stands in it."""
  holder = _from_model(PREP_CORE_GRIPPER_HOLDER_MODEL, name, PREP_CORE_GRIPPER_HOLDER_LOCATION)
  middle = holder.attributes.size.y / 2
  holder.attributes.metadata.update(
    {
      BACK_CHANNEL_Y_CENTER: middle + PREP_CORE_GRIPPER_TOOL_SPACING / 2,
      FRONT_CHANNEL_Y_CENTER: middle - PREP_CORE_GRIPPER_TOOL_SPACING / 2,
    }
  )
  return holder


def _waste_block(name_prefix: Optional[str], with_core_grippers: bool) -> pb.ResourceDefinition:
  """The waste block, and what stands on it: the trough, the teaching needle, the tool holder."""
  # As wide as the block, from the tip drop's back edge to the needle's front edge; its volume is
  # the box's.
  liquid_waste_size = Coordinate(
    PREP_WASTE_BLOCK_SIZE.x,
    PREP_TEACHING_NEEDLE_SITE_Y - (-3.0 + PREP_TIP_DROP_SIZE_Y),
    PREP_LIQUID_WASTE_SIZE_Z,
  )
  liquid_waste = build.resource(
    component_name("liquid_waste_container", name_prefix),
    liquid_waste_size,
    kind=pb.RESOURCE_KIND_TROUGH,
    location=Coordinate(
      0.0, PREP_TIP_DROP_SIZE_Y, PREP_WASTE_BLOCK_SIZE.z - PREP_LIQUID_WASTE_SIZE_Z
    ),
    type_name="Trough",
    category="trough",
    container=pb.ContainerSpec(
      max_volume=liquid_waste_size.x * liquid_waste_size.y * liquid_waste_size.z,
      through_base_to_container_base=0.0,
    ),
    state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
  )
  children = [liquid_waste, _teaching_needle_spot(component_name("teaching_needle", name_prefix))]
  if with_core_grippers:
    children.append(_core_gripper_holder(component_name("core_grippers", name_prefix)))
  return _trash(
    component_name("waste_block", name_prefix),
    PREP_WASTE_BLOCK_SIZE,
    PREP_WASTE_BLOCK_LOCATION,
    model="hamilton_prep_wasteblock",
    category="trash",
    children=children,
  )


def prep_deck(
  name: str = "deck",
  name_prefix: Optional[str] = None,
  with_spots: bool = True,
  with_calibration_block: bool = True,
  with_waste_block: bool = True,
  with_waste_bin: bool = True,
  with_waste_positions: bool = True,
  with_core_grippers: bool = True,
) -> pb.ResourceDefinition:
  """The deck a Prep carries, as a definition for `ResourceStore.create`.

  Args:
    name: what to call the deck.
    name_prefix: what its parts' names start with, without the underscore: `Prep` names the waste
      block `Prep_waste_block`. None leaves the parts' names bare.
    with_spots: whether to build the eight labware spots.
    with_calibration_block: whether to build the calibration block.
    with_waste_block: whether to build the waste block, with its trough and teaching needle.
    with_waste_bin: whether to build the waste bin.
    with_waste_positions: whether to build the three waste positions.
    with_core_grippers: whether the waste block carries the CO-RE gripper holder and its tools.

  Returns:
    The deck's definition.
  """
  children: List[pb.ResourceDefinition] = []
  if with_spots:
    for column in range(2):
      for row in range(4):
        location = Coordinate(
          PREP_FIRST_SLOT_LOCATION.x + column * PREP_SPOT_PITCH_X,
          PREP_FIRST_SLOT_LOCATION.y + row * PREP_SPOT_PITCH_Y,
          0.0,
        )
        spot = component_name(f"spot_{column}_{row}", name_prefix)
        children.append(_from_model(PREP_SPOT_MODEL, spot, location))
  if with_calibration_block:
    children.append(
      build.resource(
        component_name("calibration_block", name_prefix),
        Coordinate(6.0, 6.0, 22.0),
        location=PREP_CALIBRATION_BLOCK_LOCATION,
        type_name="Resource",
        category="calibration_block",
        model="hamilton_prep_calibration_block",
      )
    )
  if with_waste_block:
    children.append(_waste_block(name_prefix, with_core_grippers))
  if with_waste_bin:
    # Its handle reaches 22 mm in front of it, as the model shows.
    children.append(
      build.resource(
        component_name("waste_bin", name_prefix),
        PREP_WASTE_BIN_SIZE,
        location=PREP_WASTE_BIN_LOCATION,
        type_name="Resource",
        category="waste_bin",
        model="hamilton_prep_waste_bin",
      )
    )
  if with_waste_positions:
    for waste, y in PREP_WASTE_POSITIONS:
      children.append(
        _trash(
          component_name(waste, name_prefix),
          PREP_WASTE_POSITION_SIZE,
          Coordinate(PREP_WASTE_POSITION_X, y, PREP_WASTE_POSITION_Z),
          category="waste_position",
        )
      )
  return build.resource(
    name,
    PREP_DECK_SIZE,
    kind=pb.RESOURCE_KIND_DECK,
    type_name=PREP_DECK_TYPE,
    category="deck",
    metadata=None if name_prefix is None else {NAME_PREFIX: name_prefix},
    children=children,
  )


@dataclasses.dataclass
class PrepDeckParts:
  """A Prep deck's parts, as they stand in a store. A part the deck was built without is None.

  Attributes:
    deck: the deck.
    name_prefix: what its parts' names start with, or None.
    spots: the labware spots, column-major: `spot_0_0` first, `spot_1_3` last.
    calibration_block: the steel block between the two columns.
    waste_block: where tips are dropped.
    waste_bin: the bin beside the waste block.
    liquid_waste_container: the liquid waste trough on the waste block.
    teaching_needle_spot: where the teaching needle stands.
    core_gripper_holder: the CO-RE gripper holder on the waste block.
    waste_positions: the waste sites, keyed as the driver names them: `waste_rear`,
      `waste_front`, `waste_mph`.
  """

  deck: handles.Deck
  name_prefix: Optional[str]
  spots: List[handles.ResourceHolder]
  calibration_block: Optional[handles.Resource]
  waste_block: Optional[handles.Trash]
  waste_bin: Optional[handles.Resource]
  liquid_waste_container: Optional[handles.Trough]
  teaching_needle_spot: Optional[handles.TipSpot]
  core_gripper_holder: Optional[handles.Resource]
  waste_positions: Dict[str, handles.Trash]

  def __getitem__(self, index: int) -> handles.ResourceHolder:
    """Labware spot by index 0-7, column-major."""
    return self.spots[index]


def is_prep_deck(attributes: pb.ResourceAttributes) -> bool:
  """Whether a deck is a Prep's, by the type it was made as."""
  return attributes.type_name == PREP_DECK_TYPE


def name_prefix_of(attributes: pb.ResourceAttributes) -> Optional[str]:
  """The prefix a Prep deck's parts' names start with, or None."""
  value = attributes.metadata.fields.get(NAME_PREFIX)
  return value.string_value if value is not None and value.string_value else None


async def read_prep_deck(deck: handles.Deck) -> PrepDeckParts:
  """A Prep deck's parts, found by name: two reads of the store.

  Args:
    deck: the deck, in its store.
  """
  prefix = name_prefix_of(await deck.attributes())
  names = {
    part: component_name(part, prefix)
    for part in (
      "calibration_block",
      "waste_block",
      "waste_bin",
      "liquid_waste_container",
      "teaching_needle",
      "core_grippers",
    )
  }
  wastes = {waste: component_name(waste, prefix) for waste, _ in PREP_WASTE_POSITIONS}
  spots = spot_names(prefix)
  found = {
    part.name: part
    for part in await deck.store.find_resources(
      scope=deck,
      filter=spb.ResourceFilter(names=[*names.values(), *wastes.values(), *spots]),
    )
  }

  waste_block = found.get(names["waste_block"])
  liquid_waste = found.get(names["liquid_waste_container"])
  needle = found.get(names["teaching_needle"])
  return PrepDeckParts(
    deck=deck,
    name_prefix=prefix,
    spots=[part for name in spots if isinstance(part := found.get(name), handles.ResourceHolder)],
    calibration_block=found.get(names["calibration_block"]),
    waste_block=waste_block if isinstance(waste_block, handles.Trash) else None,
    waste_bin=found.get(names["waste_bin"]),
    liquid_waste_container=liquid_waste if isinstance(liquid_waste, handles.Trough) else None,
    teaching_needle_spot=needle if isinstance(needle, handles.TipSpot) else None,
    core_gripper_holder=found.get(names["core_grippers"]),
    waste_positions={
      waste: part
      for waste, name in wastes.items()
      if isinstance(part := found.get(name), handles.Trash)
    },
  )
