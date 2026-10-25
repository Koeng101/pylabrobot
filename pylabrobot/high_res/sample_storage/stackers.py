from typing import Optional

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build
from pylabrobot.resources.store.v1 import types_pb2 as pb

_STACKER_SIZE_X = 112.3
_STACKER_SIZE_Y = 146.6
_SITE_SIZE_X = 85.48
_SITE_SIZE_Y = 127.76


def plate_holder(
  name: str, size: Coordinate, location: Optional[Coordinate] = None
) -> pb.ResourceDefinition:
  """The definition of a plate holder with no pedestal that seats a plate at its origin: a stacker
  slot or a transfer nest.

  Args:
    name: Its name.
    size: Its size.
    location: Where it is in its parent; unset leaves it without a location.
  """
  return build.resource(
    name,
    size,
    kind=pb.RESOURCE_KIND_PLATE_HOLDER,
    location=location,
    category="plate_holder",
    holder=pb.HolderSpec(
      child_location=build.vec3(Coordinate.zero()), pedestal_size_z=0, capacity=1
    ),
  )


def high_res_stacker(
  name: str,
  *,
  zero_offset: float,
  slot_height: float,
  slot_count: int,
) -> pb.ResourceDefinition:
  """The definition of a HighRes sample-store stacker, from its configured dimensions.

  The values correspond to one line returned by the device's
  ``getstackerdimensions`` command. The stacker is a plate carrier whose sites are
  its slots, bottom first; site names use the device's one-based slot numbers.

  Args:
    name: Resource name for the stacker.
    zero_offset: Vertical position of the first slot.
    slot_height: Height and vertical pitch of each slot.
    slot_count: Number of slots in the stacker.

  Returns:
    A plate carrier holding one plate holder for each stacker slot.
  """
  if zero_offset < 0:
    raise ValueError(f"zero_offset must be non-negative; got {zero_offset}.")
  if slot_height <= 0:
    raise ValueError(f"slot_height must be positive; got {slot_height}.")
  if slot_count < 0:
    raise ValueError(f"slot_count must be non-negative; got {slot_count}.")

  return build.resource(
    name,
    Coordinate(_STACKER_SIZE_X, _STACKER_SIZE_Y, zero_offset + slot_height * slot_count),
    kind=pb.RESOURCE_KIND_CARRIER,
    category="plate_carrier",
    model="high_res_stacker",
    metadata={
      "zero_offset": zero_offset,
      "slot_height": slot_height,
      "slot_count": slot_count,
    },
    children=[
      plate_holder(
        f"{name}_slot_{spot + 1}",
        Coordinate(_SITE_SIZE_X, _SITE_SIZE_Y, slot_height),
        location=Coordinate(
          x=(_STACKER_SIZE_X - _SITE_SIZE_X) / 2,
          y=(_STACKER_SIZE_Y - _SITE_SIZE_Y) / 2,
          z=zero_offset + slot_height * spot,
        ),
      )
      for spot in range(slot_count)
    ],
  )
