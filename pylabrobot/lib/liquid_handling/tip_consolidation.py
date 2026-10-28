"""Plan tip transfers without executing operations or changing tip trackers.

Callers execute each batch by picking up its origin tips and dropping them at the
corresponding targets with the same channels. Device-specific positioning and
execution remain the caller's responsibility.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Generic, List, Optional, Sequence, Tuple, TypeVar

from pylabrobot.resources import Tip, TipRack, TipSpot

S = TypeVar("S")
T = TypeVar("T")


@dataclass
class TipTransferBatch(Generic[S]):
  """Parallel origin, target, and channel lists for one pickup/drop cycle."""

  origin_tip_spots: List[S]
  target_tip_spots: List[S]
  use_channels: List[int]


@dataclass(frozen=True)
class RackTips(Generic[S, T]):
  """A rack's spots as consolidation needs them, column-major.

  Attributes:
    name: The rack's name.
    spots: Its spots.
    xs: Each spot's X in the rack.
    tips: The tip each spot holds; None where it holds none.
  """

  name: str
  spots: Sequence[S]
  xs: Sequence[float]
  tips: Sequence[Optional[T]]


def _merge_sublists(lists: List[List[S]], max_len: int) -> List[List[S]]:
  """Merge adjacent sublists up to max_len, splitting oversized columns."""
  merged: List[List[S]] = []
  buffer: List[S] = []
  for sublist in lists:
    for start in range(0, len(sublist), max_len):
      chunk = sublist[start : start + max_len]
      if len(buffer) + len(chunk) > max_len:
        merged.append(buffer)
        buffer = []
      buffer.extend(chunk)
  if buffer:
    merged.append(buffer)
  return merged


def rack_tips_of(tip_rack: TipRack) -> RackTips[TipSpot, Tip]:
  """A rack's spots, read from PLR's `Resource` classes."""
  spots = tip_rack.get_all_items()
  xs = []
  for spot in spots:
    if spot.location is None:
      raise ValueError(f"{spot.name} has no location")
    xs.append(spot.location.x)
  tips = [spot.tracker.get_tip() if spot.tracker.has_tip else None for spot in spots]
  return RackTips(name=tip_rack.name, spots=spots, xs=xs, tips=tips)


def plan_tip_consolidation(
  tip_racks: List[TipRack],
  num_channels: int,
  can_pick_up_tip: Callable[[int, Tip], bool],
  use_channels: Optional[List[int]] = None,
) -> List[TipTransferBatch[TipSpot]]:
  """`plan_consolidation` for racks held in this process.

  Raises:
    ValueError: As `plan_consolidation`.
  """
  return plan_consolidation(
    [rack_tips_of(tip_rack) for tip_rack in tip_racks],
    num_channels,
    can_pick_up_tip,
    model_of=lambda tip: tip.model,
    use_channels=use_channels,
  )


def plan_consolidation(
  racks: List[RackTips[S, T]],
  num_channels: int,
  can_pick_up_tip: Callable[[int, T], bool],
  model_of: Callable[[T], Optional[str]],
  use_channels: Optional[List[int]] = None,
) -> List[TipTransferBatch[S]]:
  """Plan consolidation of partially filled racks, grouped by tip model.

  Full and empty racks are ignored. Within each model, racks are filled in order
  of increasing empty spots, preserving input order for ties. With eight or more
  available channels, destination columns are kept together where possible and
  batches contain at most eight tips. Smaller channel selections use consecutive
  chunks of destination spots.

  Args:
    racks: Racks whose tip inventory should be consolidated.
    num_channels: Number of channels on the device.
    can_pick_up_tip: Predicate accepting a channel index and a tip. Used to select
      compatible channels separately for each model when use_channels is omitted.
    model_of: A tip's model; None when it has none.
    use_channels: Explicit channel selection, in execution order. The caller is
      responsible for ensuring these channels can handle the tips.

  Returns:
    Ordered pickup/drop batches. Planning does not mutate resources. Execute the
    plan before making other changes to the supplied racks' tip inventory.

  Raises:
    ValueError: If a partial rack has undefined or mixed tip models, an explicit
      channel selection is invalid, or no channel can handle a required transfer.
  """
  if use_channels is not None:
    if not use_channels or len(set(use_channels)) != len(use_channels):
      raise ValueError("use_channels must contain distinct channels and must not be empty.")
    if any(channel < 0 or channel >= num_channels for channel in use_channels):
      raise ValueError(f"use_channels must be in range [0, {num_channels - 1}].")

  clusters_by_model: Dict[str, List[Tuple[RackTips[S, T], int]]] = {}
  for rack in racks:
    held = [tip for tip in rack.tips if tip is not None]
    if not held or len(held) == len(rack.spots):
      continue

    model = model_of(held[0])
    if model is None or any(model_of(tip) is None for tip in held[1:]):
      raise ValueError("Tip models must be defined for consolidation.")
    if any(model_of(tip) != model for tip in held[1:]):
      raise ValueError(f"Tip rack {rack.name} has mixed tip models, cannot consolidate: {held}")
    clusters_by_model.setdefault(model, []).append((rack, len(rack.spots) - len(held)))

  batches: List[TipTransferBatch[S]] = []
  for rack_list in clusters_by_model.values():
    rack_list.sort(key=lambda entry: entry[1])
    entries = [
      (spot, (rack.name, round(x, 3)), tip)
      for rack, _ in rack_list
      for spot, x, tip in zip(rack.spots, rack.xs, rack.tips)
    ]
    num_tips = sum(1 for _, _, tip in entries if tip is not None)
    origins = [
      (spot, tip)
      for index, (spot, _, tip) in enumerate(entries)
      if tip is not None and index >= num_tips
    ]
    targets = [
      (spot, column)
      for index, (spot, column, tip) in enumerate(entries)
      if tip is None and index < num_tips
    ]
    if not targets:
      continue

    tip = origins[0][1]
    channels = (
      [channel for channel in range(num_channels) if can_pick_up_tip(channel, tip)]
      if use_channels is None
      else list(use_channels)
    )
    if not channels:
      raise ValueError(f"No channel capable of handling tips on deck: {tip}")

    if len(channels) >= 8:
      columns: Dict[Tuple[str, float], List[S]] = {}
      for spot, column in sorted(targets, key=lambda target: target[1]):
        columns.setdefault(column, []).append(spot)
      target_batches = _merge_sublists(list(columns.values()), max_len=8)
    else:
      spots = [spot for spot, _ in targets]
      target_batches = [spots[i : i + len(channels)] for i in range(0, len(spots), len(channels))]

    origin_index = 0
    for target_spots in target_batches:
      count = len(target_spots)
      batches.append(
        TipTransferBatch(
          origin_tip_spots=[spot for spot, _ in origins[origin_index : origin_index + count]],
          target_tip_spots=target_spots,
          use_channels=channels[:count],
        )
      )
      origin_index += count
  return batches
