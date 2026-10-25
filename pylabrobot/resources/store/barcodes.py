"""Barcodes read by a reader, checked against those a store records, and barcodes recorded once.

A barcode is printed on a plate or a tube: the store records it as an attribute of that resource,
for tracking. A reader never writes what it reads over what is recorded. What it reads is checked
against the store instead, so a tube that was moved, swapped or taken away is noticed:

  reads = {rack: rack_code, rack.get_item("A1"): tube_code, rack.get_item("A2"): None}
  await check_barcodes(reads)   # raises BarcodeMismatchError on any disagreement

Barcodes are put into the store once, for resources that have none yet, with `initialize_barcodes`
(or when the resource is created: `ResourceAttributes.barcode` in its definition). Recording a
barcode over a different one is refused.

Each key of `reads` and of `initialize_barcodes`' mapping is a resource the reader looked at. A
holder (a rack position, a plate holder) stands for what it holds; any other resource (a rack, a
plate, a tube) stands for itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Mapping, Optional, Sequence

from pylabrobot.resources.store import handles
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

# What stands for the resource it holds, when a reader looks at it.
HOLDER_KINDS = (pb.RESOURCE_KIND_RESOURCE_HOLDER, pb.RESOURCE_KIND_PLATE_HOLDER)


@dataclass(frozen=True)
class BarcodeMismatch:
  """One place where what a reader read disagrees with what the store records.

  Attributes:
    place: The name of the resource the reader looked at.
    problem: "different": another barcode is recorded than was read; "missing": a resource with a
      recorded barcode is there, and none was read (it is gone, or its code was unreadable);
      "unexpected": a barcode was read where the store holds nothing.
    recorded: The barcode the store records there, or None.
    read: The barcode read there, or None.
  """

  place: str
  problem: Literal["different", "missing", "unexpected"]
  recorded: Optional[str]
  read: Optional[str]

  def __str__(self) -> str:
    if self.problem == "different":
      return f"{self.place}: read '{self.read}', the store records '{self.recorded}'"
    if self.problem == "missing":
      return f"{self.place}: nothing read, the store records '{self.recorded}'"
    return f"{self.place}: read '{self.read}', the store holds nothing there"


class BarcodeMismatchError(Exception):
  """Barcodes read disagree with the barcodes a store records.

  Attributes:
    mismatches: Each disagreement, in the order the places were given.
  """

  def __init__(self, mismatches: Sequence[BarcodeMismatch]):
    self.mismatches = list(mismatches)
    super().__init__(
      f"{len(self.mismatches)} barcode(s) disagree with the store: "
      + "; ".join(str(m) for m in self.mismatches)
    )


async def _labelled(
  places: Sequence[handles.Resource],
) -> List[Optional[pb.ResourceNode]]:
  """What carries the barcode at each place, as the store holds it now, in one read: the place
  itself, or for a holder what it holds (None when it holds nothing)."""
  if not places:
    return []
  store = places[0].store
  response = await store.commands.get_resources(
    spb.GetResourcesRequest(resources=[place.ref for place in places], depth=1)
  )
  by_id = {node.id: node for node in response.nodes}
  labelled: List[Optional[pb.ResourceNode]] = []
  for place in places:
    node = by_id[place.id]
    if node.attributes.kind in HOLDER_KINDS:
      held = [by_id[i] for i in node.child_ids if i in by_id]
      labelled.append(held[0] if held else None)
    else:
      labelled.append(node)
  return labelled


def _recorded(node: pb.ResourceNode) -> Optional[str]:
  return node.attributes.barcode.data if node.attributes.HasField("barcode") else None


async def find_barcode_mismatches(
  reads: Mapping[handles.Resource, Optional[pb.Barcode]],
) -> List[BarcodeMismatch]:
  """How the barcodes read disagree with those the store records; empty when they agree.

  A resource with no recorded barcode agrees with whatever is read on it: it is not labelled in
  the store yet (see `initialize_barcodes`).

  Args:
    reads: Each place the reader looked at, and the barcode it read there (None for none).
  """
  places = list(reads)
  mismatches: List[BarcodeMismatch] = []
  for place, node in zip(places, await _labelled(places)):
    barcode = reads[place]
    read = barcode.data if barcode is not None and barcode.data else None
    if node is None:
      if read is not None:
        mismatches.append(BarcodeMismatch(place.name, "unexpected", None, read))
      continue
    recorded = _recorded(node)
    if recorded is None:
      continue
    if read is None:
      mismatches.append(BarcodeMismatch(place.name, "missing", recorded, None))
    elif read != recorded:
      mismatches.append(BarcodeMismatch(place.name, "different", recorded, read))
  return mismatches


async def check_barcodes(reads: Mapping[handles.Resource, Optional[pb.Barcode]]) -> None:
  """Check barcodes a reader read against those the store records; the store is not changed.

  Args:
    reads: Each place the reader looked at, and the barcode it read there (None for none).

  Raises:
    BarcodeMismatchError: A barcode read differs from the one recorded, a resource with a
      recorded barcode was not read, or a barcode was read where the store holds nothing.
  """
  mismatches = await find_barcode_mismatches(reads)
  if mismatches:
    raise BarcodeMismatchError(mismatches)


async def initialize_barcodes(barcodes: Mapping[handles.Resource, pb.Barcode]) -> None:
  """Record barcodes on resources that have none yet, all in one change.

  A resource that already records the same barcode is left as it is. Nothing is recorded when any
  of them would be refused.

  Args:
    barcodes: Each place, and the barcode printed on what is there.

  Raises:
    BarcodeMismatchError: A resource records another barcode ("different"), or a holder holds
      nothing to label ("unexpected").
  """
  places = list(barcodes)
  mismatches: List[BarcodeMismatch] = []
  updates: List[spb.ResourceUpdate] = []
  for place, node in zip(places, await _labelled(places)):
    barcode = barcodes[place]
    if node is None:
      mismatches.append(BarcodeMismatch(place.name, "unexpected", None, barcode.data))
      continue
    recorded = _recorded(node)
    if recorded is None:
      updates.append(
        spb.ResourceUpdate(
          barcode=pb.SetBarcode(resource=pb.ResourceRef(id=node.id), barcode=barcode)
        )
      )
    elif recorded != barcode.data:
      mismatches.append(BarcodeMismatch(place.name, "different", recorded, barcode.data))
  if mismatches:
    raise BarcodeMismatchError(mismatches)
  if updates:
    store = places[0].store
    await store.commands.update_resources(
      spb.UpdateResourcesRequest(lock_tokens=store.lock_tokens, updates=updates)
    )


def barcodes_by_place(
  reads: Mapping[handles.Resource, Optional[pb.Barcode]],
) -> Dict[handles.Resource, pb.Barcode]:
  """The places where something was read, for `initialize_barcodes`."""
  return {place: barcode for place, barcode in reads.items() if barcode is not None}
