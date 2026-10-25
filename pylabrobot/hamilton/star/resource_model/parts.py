"""The STAR's own parts, as the store builds them: the body, the panels beside it, the X-arm, the
pipetting channels, the heads, the iSWAP's arm, and the autoload's sled and tray.

Each is a definition for `CreateResources`.
"""

from typing import Optional, Tuple

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build
from pylabrobot.resources.store.v1 import types_pb2 as pb

# Which frame a deck belongs to, from how many tracks it has. The three are the same deck at three
# lengths, so the track count is the only thing that tells them apart - and parts that are cut to
# the frame's length differ between them and need saying which one they are.
FRAME_BY_NUM_TRACKS = {30: "starlet", 54: "star", 76: "starplus"}


def grips(tool: pb.ResourceAttributes) -> bool:
  """Whether a tool is one that grips: its spec says where its grip line is."""
  return tool.head_tool.HasField("grip_line_height")


def grip_line_height(tool: pb.ResourceAttributes) -> float:
  """How far a CoRe gripper tool grips above its bottom, in mm, as its spec says.

  Raises:
    ValueError: Its spec says nothing of a grip line.
  """
  if not grips(tool):
    raise ValueError(f"'{tool.name}' is not a gripper tool whose grip line is known")
  return tool.head_tool.grip_line_height


SHAFT_DIAMETER = 7.0
"""How wide a tip mounting shaft is, in mm."""

SHAFT_LENGTH = 8.0
"""How far a tip mounting shaft reaches below the pipette carrying it, in mm."""

# The X-arm rides at the channel stop-disk safety height, level with the raised stop discs so it
# clears them as it travels. Its depth and height.
X_ARM_Z = 334.7
X_ARM_SIZE_Y = 712.0
X_ARM_SIZE_Z = 140.0

# How far in front of the back of the device the X-arm's own back edge stands, in mm. Measured on
# the manufacturer's model: the chassis reaches to 51.06 and the arm's carriage to 35.56, and the
# chassis's depth there - 785.79 - is what the device resource says to the decimal, so the two
# frames line up and the difference is the arm's own setback.
ARM_BACK_FROM_DEVICE_BACK = 15.5

# Where a carrier's own front edge sits on any Hamilton deck, in mm.
CARRIER_Y = 63.0

# The whole autoload sled, transport and barcode reader. The 316.2 this replaces came off the
# manufacturer's model, whose left end carried a thin tab that the sled does not have; the extra
# 35.3 mm put the part's own corner that far left of where it stands, and everything measured from
# that corner with it.
SLED_SIZE = (280.9, 109.5, 215.3)
# Against a carrier's own front edge, and the deck's work surface.
SLED_AHEAD_OF_CARRIER_Y = 92.7
SLED_ABOVE_DECK_Z = 0.5

# The loading tray, measured against the two things on the deck it lines up with: where the first
# carrier starts, and a carrier's front edge. It insets the same amount from the deck's right edge
# as from its left, which is what sizes it. The height is the tray plate's own top - what a carrier
# stands on, and what its track markings are cut into.
TRAY_FROM_FIRST_CARRIER_X = 104.0
TRAY_FRONT_AHEAD_Y = 380.0
TRAY_BACK_AHEAD_Y = 132.0
TRAY_SIZE_Z = 98.0

# How often a track gets a number on a part that states its own grid: the first, and then every
# fifth.
TRACK_LABEL_EVERY = 5


def shaft_spec() -> pb.TipMountingShaftSpec:
  """What every STAR mounting shaft is: round, and collecting tips by CO-RE."""
  return pb.TipMountingShaftSpec(
    tip_pickup_mode="core", cross_section_type=pb.CROSS_SECTION_TYPE_CIRCLE
  )


def device_body(name: str, size: Coordinate, model: str) -> pb.ResourceDefinition:
  """The device itself: a box everything it carries hangs from.

  Args:
    name: what to call it.
    size: how big it is, in mm.
    model: which device it is.
  """
  return build.resource(name, size, category="device", model=model, type_name="STARDevice")


def side_part(
  name: str, size: Coordinate, location: Coordinate, category: str
) -> pb.ResourceDefinition:
  """A part bolted to the side of the chassis: the left side panel, or the extension housing.

  Args:
    name: what to call it.
    size: how big it is, in mm.
    location: where it stands on the device.
    category: which of the two it is, which is also its model's name.
  """
  return build.resource(
    name,
    size,
    location=location,
    category=category,
    model=f"hamilton_star_{category}",
    type_name="Resource",
  )


def x_arm(
  name: str, location: Coordinate, size_x: float, reference_point_from_left: float, model: str
) -> pb.ResourceDefinition:
  """An X-arm, placed where it stands on the deck.

  The arm is wider than the width its drive reports, which begins at the arm's left edge and stops
  short of its right end. So the two are given separately: how much room the part takes, and where
  along it the drive's position refers to, which is stated for anything reading the resource.

  Args:
    name: what to call it.
    location: where its corner stands on the deck.
    size_x: how wide the arm is, in mm, end to end.
    reference_point_from_left: how far along it, from its left edge in mm, the drive's position
      refers to.
    model: which arm this is.
  """
  return build.resource(
    name,
    Coordinate(size_x, X_ARM_SIZE_Y, X_ARM_SIZE_Z),
    location=location,
    category="x_arm",
    model=model,
    type_name="Resource",
    metadata={"reference_point": {"x": reference_point_from_left}},
  )


def pipette_channel(name: str, width: float, size_z: float) -> pb.ResourceDefinition:
  """One pipetting channel, with the tip mounting shaft that hangs off its lower end.

  The shaft hangs its own length below the channel's bottom, not inside it, so it reaches lowest
  and the channel body starts clear of it. It is centred on the channel, the axis a tip is
  collected on. A collected tip becomes a child of the shaft, not of the channel.

  Args:
    name: what to call it; the shaft is named after it.
    width: how wide and deep the channel is, in mm.
    size_z: how tall to model it, in mm.
  """
  shaft = build.resource(
    f"{name}_tip_mounting_shaft",
    Coordinate(SHAFT_DIAMETER, SHAFT_DIAMETER, SHAFT_LENGTH),
    kind=pb.RESOURCE_KIND_TIP_MOUNTING_SHAFT,
    location=Coordinate((width - SHAFT_DIAMETER) / 2, (width - SHAFT_DIAMETER) / 2, -SHAFT_LENGTH),
    category="tip_mounting_shaft",
    type_name="TipMountingShaft",
    tip_mounting_shaft=shaft_spec(),
  )
  return build.resource(
    name,
    Coordinate(width, width, size_z),
    category="pipette_channel",
    model="hamilton_star_pipette_channel",
    type_name="Resource",
    children=[shaft],
  )


def channel_reference_point(width: float) -> Coordinate:
  """Where on a channel the drives report, from its left front bottom corner: the centre of the end
  of the shaft it carries, which hangs a shaft's length below the body.

  Args:
    width: how wide the channel is, in mm.
  """
  return Coordinate(width / 2, width / 2, -SHAFT_LENGTH)


def autoload_sled(name: str, x: float, reference_point_from_left: float) -> pb.ResourceDefinition:
  """The autoload's sled, placed around its carrier-handling wheel.

  The wheel is the point the drive reports, so the sled's own origin is not; saying where the wheel
  sits within it is what lets anything reading the resource put the two together.

  Args:
    name: what to call it.
    x: where the wheel is on the deck, in mm.
    reference_point_from_left: how far the wheel sits from the sled's left edge, in mm.
  """
  return build.resource(
    name,
    Coordinate(*SLED_SIZE),
    location=Coordinate(
      x - reference_point_from_left, CARRIER_Y - SLED_AHEAD_OF_CARRIER_Y, SLED_ABOVE_DECK_Z
    ),
    category="autoload_sled",
    model="hamilton_star_autoload_sled",
    type_name="Resource",
    metadata={"reference_point": {"x": reference_point_from_left}},
  )


def autoload_loading_tray(
  name: str, deck_size_x: float, tracks: pb.HamiltonDeckSpec, frame: Optional[str]
) -> pb.ResourceDefinition:
  """The loading tray the autoload draws carriers from, placed against the deck it serves.

  Its left edge sits 104 mm left of the first carrier and its front edge 380 mm in front of a
  carrier's; it reaches the same 104 mm short of the deck's right edge, so its width follows from
  the deck. Its own track markings line up with the deck's, so a carrier put on the tray at a track
  goes to that same track on the deck; they are stated, since nothing about the tray says where
  they are.

  Args:
    name: what to call it.
    deck_size_x: how wide the deck is, in mm.
    tracks: the deck's tracks.
    frame: which frame the deck is cut for, which names the tray; None leaves it unnamed.
  """
  first = tracks.track_origin.x
  second = first + tracks.track_pitch
  left = first - TRAY_FROM_FIRST_CARRIER_X
  return build.resource(
    name,
    Coordinate(
      deck_size_x - TRAY_FROM_FIRST_CARRIER_X - left,
      TRAY_FRONT_AHEAD_Y - TRAY_BACK_AHEAD_Y,
      TRAY_SIZE_Z,
    ),
    location=Coordinate(left, CARRIER_Y - TRAY_FRONT_AHEAD_Y, 0.0),
    category="autoload_loading_tray",
    model=f"hamilton_{frame}_autoload_loading_tray" if frame else "",
    type_name="Resource",
    metadata={
      "position_grid": {
        "axis": "x",
        "count": tracks.num_tracks,
        "spacing": round(second - first, 4),
        "origin": [round(first - left, 4), 0.0, TRAY_SIZE_Z],
        "extent": round(TRAY_FRONT_AHEAD_Y - TRAY_BACK_AHEAD_Y, 4),
        "label_every": TRACK_LABEL_EVERY,
        "label": "track",
      }
    },
  )


# -- the heads ---------------------------------------------------------------------------------


def _rigid_head(
  name: str,
  columns: int,
  rows: int,
  pitch: float,
  model: str,
  size_x: Optional[float],
  size_y: Optional[float],
  size_z: float,
  dx: Optional[float],
  dy: Optional[float],
  dz: float,
) -> pb.ResourceDefinition:
  """One of the rigid heads: a grid the device knows, in a body it does not.

  What the device tells us is the grid - how many channels, at what pitch. The body around it
  is a measurement of a particular head, never derived from the pitch. Left unmeasured, the resource
  spans the array and nothing more.

  Args:
    name: what to call this one.
    columns: how many channels across.
    rows: how many channels deep.
    pitch: their centre-to-centre spacing, in mm.
    model: which head this is.
    size_x: how wide the head's body is, in mm. None spans the channel array instead.
    size_y: how deep the body is, in mm. None spans the channel array instead.
    size_z: how tall it is, in mm. Zero models it as its channel plane.
    dx: how far channel A1 sits from the body's left edge, in mm. None centres the array.
    dy: how far channel A1 sits from its front edge, in mm. None centres the array.
    dz: how far channel A1 sits above its bottom, in mm.

  Returns:
    The head's definition, a mounting shaft per channel under it.
  """
  array_x, array_y = (columns - 1) * pitch, (rows - 1) * pitch
  size_x = array_x if size_x is None else size_x
  size_y = array_y if size_y is None else size_y
  # Centred in the body unless placed explicitly. A1 is the back row, so it sits a full array
  # depth behind the front margin.
  dx = (size_x - array_x) / 2 if dx is None else dx
  dy = (size_y - array_y) / 2 + array_y if dy is None else dy
  shaft = build.resource(
    f"{name}_tipmountingshaft_{{identifier}}",
    Coordinate(SHAFT_DIAMETER, SHAFT_DIAMETER, SHAFT_LENGTH),
    kind=pb.RESOURCE_KIND_TIP_MOUNTING_SHAFT,
    category="tip_mounting_shaft",
    type_name="TipMountingShaft",
    tip_mounting_shaft=shaft_spec(),
  )
  return build.resource(
    name,
    Coordinate(size_x, size_y, size_z),
    kind=pb.RESOURCE_KIND_N_CHANNEL_PIPETTE,
    category=model,
    model=model,
    type_name="NChannelPipette",
    # Where a tip is picked up: the axis of shaft A1, at the end of it. That end is a shaft's length
    # below the plane the body starts at, which is what the shafts hang from.
    n_channel_pipette=pb.NChannelPipetteSpec(
      reference_point=build.vec3(Coordinate(dx, dy, dz - SHAFT_LENGTH))
    ),
    itemized=pb.ItemizedSpec(
      num_items_x=columns,
      num_items_y=rows,
      grid=pb.ItemGrid(
        item=shaft,
        # A channel position is an axis, and these place a corner, so each shaft is set back by
        # its own radius to leave its axis where the grid says the channel is. The shafts are what
        # reaches lowest, so they hang their own length below the plane the body starts at.
        offset=build.vec3(
          Coordinate(dx - SHAFT_DIAMETER / 2, dy - array_y - SHAFT_DIAMETER / 2, dz - SHAFT_LENGTH)
        ),
        item_dx=pitch,
        item_dy=pitch,
      ),
    ),
  )


def head96(
  name: str,
  size_x: Optional[float] = 160.0,
  size_y: Optional[float] = 120.0,
  size_z: float = 0.0,
  dx: Optional[float] = None,
  dy: Optional[float] = None,
  dz: float = 0.0,
) -> pb.ResourceDefinition:
  """The 96-head: 96 channels on a 12 by 8 grid at 9 mm, moving as one.

  The drives report channel A1, so that is what its reference point is. The body is measured, and
  the channel array sits centred in it - which is where the margins on every side come from.

  Args:
    name: what to call this one.
    size_x: how wide the head's body is, in mm. None spans the channel array instead.
    size_y: how deep the body is, in mm. None spans the channel array instead.
    size_z: how tall it is, from its stop disc to its top, in mm. Zero leaves it unmodelled.
    dx: how far channel A1 sits from the body's left edge, in mm. None centres the array.
    dy: how far channel A1 sits from its front edge, in mm. None centres the array.
    dz: how far channel A1 sits above its bottom, in mm.

  Returns:
    The head's definition.
  """
  return _rigid_head(name, 12, 8, 9.0, "head96", size_x, size_y, size_z, dx, dy, dz)


def head384(
  name: str,
  size_x: Optional[float] = 160.0,
  size_y: Optional[float] = 120.0,
  size_z: float = 0.0,
  dx: Optional[float] = None,
  dy: Optional[float] = None,
  dz: float = 0.0,
) -> pb.ResourceDefinition:
  """The 384-head: 384 channels on a 24 by 16 grid at 4.5 mm, moving as one.

  Measured from channel A1, and sharing the 96-head's body, which the two are built around. Its
  array is denser, so it leaves wider margins in the same envelope.

  Args:
    name: what to call this one.
    size_x: how wide the head's body is, in mm. None spans the channel array instead.
    size_y: how deep the body is, in mm. None spans the channel array instead.
    size_z: how tall it is, from its collar bearing to its top, in mm. Zero leaves it unmodelled.
    dx: how far channel A1 sits from the body's left edge, in mm. None centres the array.
    dy: how far channel A1 sits from its front edge, in mm. None centres the array.
    dz: how far channel A1 sits above its bottom, in mm.

  Returns:
    The head's definition.
  """
  return _rigid_head(name, 24, 16, 4.5, "head384", size_x, size_y, size_z, dx, dy, dz)


# -- the iSWAP ---------------------------------------------------------------------------------

# The material each part of the arm is made of, measured on the manufacturer's own model: its
# size, and where the joint it turns on sits inside it. A member's origin is a corner, as any
# resource's is, so the joint is somewhere within it rather than at the corner, and the arm turns
# about the joint rather than about the corner.
#
# The heights are what makes the arm an arm rather than a flat plate: it steps down from the drive
# to the plate it holds. They are measured against the height the Z drive reports, which is the
# same plane `elbow_z_offset_above_finger` is measured from - and the model agrees with
# it independently, since the pads' underside comes out exactly that far below. Link 1's joint is
# below its member because the elbow drive's column stands under the arm.
LINK_1_BODY_SIZE = (163.4, 25.5, 15.3)
LINK_1_JOINT = Coordinate(12.7, 12.75, -20.3)
GRIPPER_BODY_SIZE = (59.0, 90.0, 20.3)
GRIPPER_JOINT = Coordinate(13.0, 45.0, 0.0)
# A finger has no Y of its own: the jaw width stands it where it stands.
GRIPPER_FINGER_SIZE = (135.0, 7.0, 8.0)
GRIPPER_FINGER_LOCATION = GRIPPER_JOINT + Coordinate(6.5, 0.0, 4.0)
# From the finger it is fixed to, as a child's location always is.
GRIPPER_PAD_SIZE = (37.0, 4.0, 17.0)
GRIPPER_PAD_LOCATION = Coordinate(109.0, 1.5, -17.0)

# How far the elbow drive's own column stands above the height the Z drive reports, in mm. The
# arm hangs below that: the drive reports where the material it carries is, not where its column
# begins. The column stands on link 1 with nothing between them, so this follows link 1's own top
# rather than being stated again - the two cannot drift apart.
ELBOW_DRIVE_COLUMN_ABOVE_REPORTED_Z = -LINK_1_JOINT.z + LINK_1_BODY_SIZE[2]

# The head's two rotation drives, by the names its state's `drive_angles` keeps their angles under.
# Kept in the drives' own terms, as they report them: the links' rotations carry the same facts
# rendered for the deck, which is neither the same reference nor the same axis.
ELBOW_DRIVE = "elbow"
WRIST_DRIVE = "wrist"


def iswap_head_reference_point(diameter: float) -> Coordinate:
  """The point the iSWAP's Y and Z drives report, from the head's left front bottom corner.

  The drives report the column's centre in X and Y, and a point below its base in Z: the arm it
  carries hangs there, so the resource lands that far above what is read.

  Args:
    diameter: how wide the column is, in mm.
  """
  return Coordinate(diameter / 2, diameter / 2, -ELBOW_DRIVE_COLUMN_ABOVE_REPORTED_Z)


def iswap_head(name: str, diameter: float, size_z: float) -> pb.ResourceDefinition:
  """The head the iSWAP's arm hangs from, modelled as the column its Y and Z drives ride.

  Square in plan, spanning the column's diameter, because a resource is a box. The drives position
  this, not the gripper: where the gripper ends up follows from it through the links and the joint
  angles. The arm is its child, so it travels with the head.

  Args:
    name: what to call this one.
    diameter: how wide the column is, in mm.
    size_z: how tall to model it, in mm.

  Returns:
    The head's definition.
  """
  return build.resource(
    name,
    Coordinate(diameter, diameter, size_z),
    category="iswap_head",
    model="hamilton_star_iswap_head",
    type_name="iSWAPHead",
  )


def iswap_link_1(name: str, length: float, location: Coordinate) -> pb.ResourceDefinition:
  """The first member: the elbow joint to the wrist joint, with the arm bolted to it.

  Args:
    name: what to call this one.
    length: joint to joint, in mm, as `iSWAPConfiguration.link_1_length` reports it.
    location: where its corner stands on the head.

  Returns:
    The member's definition, its body under it.
  """
  model = "hamilton_star_iswap_link_1"
  size = Coordinate(*LINK_1_BODY_SIZE)
  body = build.resource(
    f"{name}_body",
    size,
    location=Coordinate.zero(),
    category="body",
    model=f"{model}_body",
    type_name="Resource",
  )
  return build.resource(
    name,
    size,
    kind=pb.RESOURCE_KIND_LINK_BODY,
    location=location,
    category="iswap_link",
    model=model,
    type_name="LinkBody",
    link_body=pb.LinkBodySpec(
      proximal_joint=build.vec3(LINK_1_JOINT),
      # The arm reports the link joint to joint, and this member's frame starts at its corner.
      distal_joint=build.vec3(LINK_1_JOINT + Coordinate(length, 0.0, 0.0)),
    ),
    children=[body],
  )


def iswap_link_1_distal_joint(length: float) -> Coordinate:
  """Where link 1's far joint, the wrist, sits from the member's corner."""
  return LINK_1_JOINT + Coordinate(length, 0.0, 0.0)


def iswap_gripper(
  name: str,
  tool_center_point: Coordinate,
  jaw_range: Tuple[float, float],
  location: Coordinate,
  jaw_width: Optional[float] = None,
) -> pb.ResourceDefinition:
  """The iSWAP's hand: the wrist joint to the centre the clamps hold a rack at.

  Args:
    name: what to call this one.
    tool_center_point: the wrist joint to the grip centre, in mm. Its reach is
      `iSWAPConfiguration.tool_length`; it grips below the wrist, so its z is negative.
    jaw_range: how far apart the jaws stand, closed and open, in mm, as the gripper drive's own
      travel gives it.
    location: where its corner stands on link 1.
    jaw_width: how far apart they stand to begin with, in mm. Open, when not given.

  Returns:
    The gripper's definition: its body, and its two fingers each with a pad.
  """
  model = "hamilton_star_iswap_gripper"
  width = jaw_range[1] if jaw_width is None else jaw_width
  grip_y = GRIPPER_JOINT.y + tool_center_point.y
  fingers = []
  for side, facing in (("left", 1.0), ("right", -1.0)):
    edge = grip_y + facing * width / 2.0
    corner = edge if facing > 0 else edge - GRIPPER_FINGER_SIZE[1]
    finger_name = f"{name}_finger_{side}"
    pad = build.resource(
      f"{finger_name}_pad",
      Coordinate(*GRIPPER_PAD_SIZE),
      location=GRIPPER_PAD_LOCATION,
      category="pad",
      model=f"{model}_finger_pad",
      type_name="Resource",
    )
    fingers.append(
      build.resource(
        finger_name,
        Coordinate(*GRIPPER_FINGER_SIZE),
        location=Coordinate(GRIPPER_FINGER_LOCATION.x, corner, GRIPPER_FINGER_LOCATION.z),
        category="finger",
        model=f"{model}_finger",
        type_name="Resource",
        children=[pad],
      )
    )
  body = build.resource(
    f"{name}_body",
    Coordinate(*GRIPPER_BODY_SIZE),
    location=Coordinate.zero(),
    category="body",
    model=f"{model}_body",
    type_name="Resource",
  )
  return build.resource(
    name,
    Coordinate(*GRIPPER_BODY_SIZE),
    kind=pb.RESOURCE_KIND_MECHANICAL_GRIPPER,
    location=location,
    category="mechanical_gripper",
    model=model,
    type_name="MechanicalGripper",
    mechanical_gripper=pb.MechanicalGripperSpec(
      proximal_joint=build.vec3(GRIPPER_JOINT),
      # From the wrist joint, as the arm reports it and as a tool centre point is stated.
      tool_center_point=build.vec3(tool_center_point),
      jaw_width_min=jaw_range[0],
      jaw_width_max=jaw_range[1],
      body=f"{name}_body",
      fingers=[f"{name}_finger_left", f"{name}_finger_right"],
      pads=[f"{name}_finger_left_pad", f"{name}_finger_right_pad"],
    ),
    state=pb.ResourceState(jaw_width=width),
    children=[body, *fingers],
  )
