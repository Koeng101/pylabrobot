"""The iSWAP: the head its arm turns on, and the links that arm is made of."""

from typing import Optional, Tuple

from pylabrobot.hamilton.star.resource_model.parts import (
  ELBOW_DRIVE_COLUMN_ABOVE_REPORTED_Z,
  GRIPPER_BODY_SIZE,
  GRIPPER_FINGER_LOCATION,
  GRIPPER_FINGER_SIZE,
  GRIPPER_JOINT,
  GRIPPER_PAD_LOCATION,
  GRIPPER_PAD_SIZE,
  LINK_1_BODY_SIZE,
  LINK_1_JOINT,
)
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.end_effector import MechanicalGripper
from pylabrobot.resources.manipulator import LinkBody
from pylabrobot.resources.resource import Resource


class iSWAPHead(Resource):
  """The head the iSWAP's arm hangs from: the column its Y and Z drives ride.

  The drives position this, not the gripper: `reference_point` is the point they report, and where
  the gripper ends up follows from it through the two links and the joint angles. A resource is
  located by its left front bottom corner, so the drives' readings are offset by this point before
  being recorded.

  The arm is its child, so it travels with the head, and where the gripper ends up within that
  follows from the joint angles rather than from where this sits.
  """

  def __init__(
    self,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    reference_point: Coordinate,
    category: str = "iswap_head",
    model: Optional[str] = None,
    elbow_drive_angle: Optional[float] = None,
    wrist_drive_angle: Optional[float] = None,
  ):
    """
    Args:
      name: what to call this one.
      size_x: how wide the drive is, in mm.
      size_y: how deep it is, in mm.
      size_z: how tall it is, in mm.
      reference_point: the point the drives report, from the left front bottom corner.
      category: what kind of resource this is.
      model: which drive this is.
      elbow_drive_angle: the elbow drive's angle as last read, as `serialize` writes it.
      wrist_drive_angle: the wrist drive's angle as last read, as `serialize` writes it.
    """
    super().__init__(
      name=name, size_x=size_x, size_y=size_y, size_z=size_z, category=category, model=model
    )
    self.reference_point = reference_point
    self.elbow_drive_angle: Optional[float] = elbow_drive_angle
    self.wrist_drive_angle: Optional[float] = wrist_drive_angle
    """Which way the elbow drive reports the arm points, in degrees, or None until it is read.

    Kept in the drive's own terms, as it reports them. `rotation` carries the same fact rendered
    for the deck, which is neither the same reference nor the same axis: degrees there are the
    deck angle link 1 lies along, and a resource turns about its own corner while the arm turns
    about `reference_point`. Anything needing the angle a drive would report reads this rather
    than converting `rotation` back."""

  def serialize(self) -> dict:
    return {
      **super().serialize(),
      "reference_point": self.reference_point.serialize(),
      "elbow_drive_angle": self.elbow_drive_angle,
      "wrist_drive_angle": self.wrist_drive_angle,
    }


def iswap_head(
  name: str,
  diameter: float,
  size_z: float,
) -> iSWAPHead:
  """The head, modelled as the column standing above the arm.

  Square in plan, spanning the column's diameter, because a resource is a box. The drives report
  its centre in X and Y, and a point below its base in Z, which is what `reference_point` states.

  Args:
    name: what to call this one.
    diameter: how wide the column is, in mm.
    size_z: how tall to model it, in mm.

  Returns:
    The head.
  """
  return iSWAPHead(
    name=name,
    size_x=diameter,
    size_y=diameter,
    size_z=size_z,
    # The Z drive reports a point below the column's own base - the arm it carries hangs there -
    # so the reference point states that, and the resource lands that far above what is read.
    reference_point=Coordinate(diameter / 2, diameter / 2, -ELBOW_DRIVE_COLUMN_ABOVE_REPORTED_Z),
    model="hamilton_star_iswap_head",
  )


def iswap_gripper(
  name: str,
  tool_center_point: Coordinate,
  jaw_range: Tuple[float, float],
  jaw_width: Optional[float] = None,
) -> MechanicalGripper:
  """The iSWAP's hand: the wrist joint to the centre the clamps hold a rack at.

  Args:
    name: what to call this one.
    tool_center_point: the wrist joint to the grip centre, in mm. Its reach is
      `iSWAPConfiguration.tool_length`; it grips below the wrist, so its z is negative.
    jaw_range: how far apart the jaws stand, closed and open, in mm, as the gripper drive's own
      travel gives it.
    jaw_width: how far apart they stand to begin with, in mm. The width the drive homes and parks
      at, where the stored table has been read.

  Returns:
    The gripper.
  """
  model = "hamilton_star_iswap_gripper"
  fingers = tuple(
    Resource(
      name=f"{name}_finger_{side}",
      size_x=GRIPPER_FINGER_SIZE[0],
      size_y=GRIPPER_FINGER_SIZE[1],
      size_z=GRIPPER_FINGER_SIZE[2],
      category="finger",
      model=f"{model}_finger",
    )
    for side in ("left", "right")
  )
  pads = tuple(
    Resource(
      name=f"{jaw.name}_pad",
      size_x=GRIPPER_PAD_SIZE[0],
      size_y=GRIPPER_PAD_SIZE[1],
      size_z=GRIPPER_PAD_SIZE[2],
      category="pad",
      model=f"{jaw.model}_pad",
    )
    for jaw in fingers
  )
  return MechanicalGripper(
    name=name,
    proximal_joint=GRIPPER_JOINT,
    # From the wrist joint, as the arm reports it and as a tool centre point is stated.
    tool_center_point=tool_center_point,
    body=Resource(
      name=f"{name}_body",
      size_x=GRIPPER_BODY_SIZE[0],
      size_y=GRIPPER_BODY_SIZE[1],
      size_z=GRIPPER_BODY_SIZE[2],
      category="body",
      model=f"{model}_body",
    ),
    body_location=Coordinate.zero(),
    fingers=fingers,
    finger_location=GRIPPER_FINGER_LOCATION,
    pads=pads,
    pad_location=GRIPPER_PAD_LOCATION,
    jaw_range=jaw_range,
    jaw_width=jaw_width,
    model=model,
  )


def iswap_link_1(name: str, length: float) -> LinkBody:
  """The first member: the elbow joint to the wrist joint, with the arm bolted to it.

  Args:
    name: what to call this one.
    length: joint to joint, in mm, as `iSWAPConfiguration.link_1_length` reports it.

  Returns:
    The member.
  """
  member = LinkBody(
    name=name,
    size_x=LINK_1_BODY_SIZE[0],
    size_y=LINK_1_BODY_SIZE[1],
    size_z=LINK_1_BODY_SIZE[2],
    proximal_joint=LINK_1_JOINT,
    # The arm reports the link joint to joint, and this member's frame starts at its corner.
    distal_joint=LINK_1_JOINT + Coordinate(length, 0.0, 0.0),
    category="iswap_link",
    model="hamilton_star_iswap_link_1",
  )
  body = Resource(
    name=f"{member.name}_body",
    size_x=LINK_1_BODY_SIZE[0],
    size_y=LINK_1_BODY_SIZE[1],
    size_z=LINK_1_BODY_SIZE[2],
    category="body",
    model=f"{member.model}_body" if member.model else None,
  )
  member.assign_child_resource(body, location=Coordinate.zero())
  return member
