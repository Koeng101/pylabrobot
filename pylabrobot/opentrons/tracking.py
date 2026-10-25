"""Liquid bookkeeping shared by Opentrons pipettes, kept in the resource store."""

import math
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional, Sequence, Tuple

from pylabrobot.opentrons.model import Liquid, Ref, ref_of, resolve
from pylabrobot.resources.errors import TooLittleLiquidError, TooLittleVolumeError
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError, plr_error
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

# How far a volume may exceed what is there before it is refused, as PLR's volume trackers have it.
_TOLERANCE = 1e-6


def validate_liquid_transfer(
  sources: Sequence[Optional[Liquid]],
  destinations: Sequence[Optional[Liquid]],
  volume: float,
) -> None:
  """Check available liquid and capacity without changing anything.

  Each source gives `volume` to the destination beside it. A container given more than once is a
  shared reservoir, every transfer counted against it. ``None``, or an untracked container,
  is not checked.

  Raises:
    ValueError: The lists differ in length, or the volume is not finite and non-negative.
    TooLittleLiquidError: A source holds too little.
    TooLittleVolumeError: A destination has too little room.
  """
  if len(sources) != len(destinations):
    raise ValueError("Each source must have a corresponding destination")
  if not math.isfinite(volume) or volume < 0:
    raise ValueError("volume must be finite and non-negative")
  changes: Dict[bytes, float] = {}
  for source, destination in zip(sources, destinations):
    if source is not None and source.tracked:
      changes[source.id] = changes.get(source.id, 0.0) - volume
      removed = -changes[source.id]
      if removed - source.volume > _TOLERANCE:
        raise TooLittleLiquidError(
          f"Not enough liquid in container: {removed}uL > {source.volume}uL."
        )
    if destination is not None and destination.tracked:
      changes[destination.id] = changes.get(destination.id, 0.0) + volume
      added = changes[destination.id]
      free = destination.capacity - destination.volume
      if added - free > _TOLERANCE:
        raise TooLittleVolumeError(f"Not enough space in container: {added}uL > {free}uL.")


@asynccontextmanager
async def track_liquid_transfer(
  store: ResourceStore,
  frame: Ref,
  aspirate: bool,
  transfers: Sequence[Tuple[bytes, bytes]],
  volume: float,
) -> AsyncIterator[None]:
  """Stage each nozzle's transfer in the store, and settle them together.

  Each transfer is a container and the shaft whose tip takes liquid from it (`aspirate`) or gives
  liquid to it. The store refuses the whole transfer, before the block runs, when a container or
  tip has too little liquid or room. The transfers are committed once the block finishes, and
  rolled back when it raises: rollback restores bookkeeping, not physical state, so a timed-out or
  cancelled hardware command can still require operator reconciliation.

  Raises:
    TooLittleLiquidError: A giver holds too little.
    TooLittleVolumeError: A taker has too little room.
  """
  if not transfers:
    yield
    return
  request = spb.BeginLiquidTransferRequest(
    lock_tokens=store.lock_tokens,
    frame=ref_of(frame),
    direction=spb.TRANSFER_DIRECTION_ASPIRATE if aspirate else spb.TRANSFER_DIRECTION_DISPENSE,
    items=[
      spb.TransferItem(
        container=pb.ResourceRef(id=container), shaft=pb.ResourceRef(id=shaft), volume=volume
      )
      for container, shaft in transfers
    ],
    on_tracking_problem=pb.ON_TRACKING_PROBLEM_REJECT,
  )
  try:
    response = await store.commands.begin_liquid_transfer(request)
  except StoreError as error:
    raise plr_error(error) from error
  try:
    yield
  except BaseException:
    await resolve(store, response.operation, succeeded=False)
    raise
  await resolve(store, response.operation, succeeded=True)
