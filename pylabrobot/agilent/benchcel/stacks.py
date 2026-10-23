"""Stacker resources for Agilent BenchCel stackers."""

from typing import List

from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import build
from pylabrobot.resources.store.v1 import types_pb2 as pb


def benchcel_4r_stacks(name_prefix: str = "benchcel_stacker") -> List[pb.ResourceDefinition]:
  """The four LIFO stacks of an Agilent BenchCel 4R, as definitions for a resource store.

  Each stacker is a z-direction resource stack (a single-ended LIFO stack). Stack height is
  computed from each plate's ``stacking_z_height`` as plates are added, so no
  ``num_sites``/``site_pitch``/``site_height`` needs to be supplied. Like PLR's
  ``ResourceStack``, a stack has no location in the BenchCel's body.

  The stacks are named ``{name_prefix}_1`` .. ``{name_prefix}_4`` and are ordered to match the
  human stacker numbers 1-4 used by the device and firmware.
  """
  return [
    build.resource(
      f"{name_prefix}_{i}",
      Coordinate.zero(),
      kind=pb.RESOURCE_KIND_RESOURCE_STACK,
      category="resource_stack",
      type_name="ResourceStack",
      stack=pb.ResourceStackSpec(direction=pb.STACK_DIRECTION_Z),
    )
    for i in range(1, 5)
  ]
