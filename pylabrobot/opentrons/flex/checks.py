"""Compute the Flex travel clearance from the deck's resources."""

from pylabrobot.opentrons.model import anchor, locate, read
from pylabrobot.resources.store import handles

# OT-3 DEFAULT_GENERAL_ARC_Z_MARGIN (motion_planning/waypoints.py:12).
_DEFAULT_ARC_MARGIN = 10.0

# Every Flex tip rack (flex_96_tiprack_50ul / 200ul / 1000ul, and the filter rack)
# models to this z (tips included). The travel plane never drops below a tip rack,
# even on a deck the model shows as empty -- a rack physically present but not in
# the model (or not yet loaded on the robot) must still be cleared.
_FLEX_TIPRACK_HEIGHT = 99.0


async def traversal_z(deck: handles.Deck, arc_margin: float = _DEFAULT_ARC_MARGIN) -> float:
  """The tip-safe travel plane (tip-end / critical-point frame), from the resource model.

  The higher of: the tallest labware top on the deck plus ``arc_margin``, and an
  unconditional tip-rack floor (``_FLEX_TIPRACK_HEIGHT`` + ``arc_margin``). The floor
  means travel is always above a tip rack even when the deck model shows none -- a
  rack physically present but unmodeled, or not yet loaded on the robot, is still
  cleared. Two reads of the store; no robot round-trip.
  """
  # Highest points are along the root's axes and the deck may stand in a room, so each of the
  # deck's children is measured from the deck's own bottom. The deck itself does not count.
  tree = await read(deck.store, [deck], depth=1)
  children = tree.children(tree.node(deck))
  geometries = await locate(deck.store, [(deck, [anchor()])] + [(c.id, ()) for c in children])
  floor = geometries[0].locations[0].z
  tops = [g.highest_point - floor for g in geometries[1:]]
  computed = (max(tops) if tops else 0.0) + arc_margin
  return max(computed, _FLEX_TIPRACK_HEIGHT + arc_margin)
