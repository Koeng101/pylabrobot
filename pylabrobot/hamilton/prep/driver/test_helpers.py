"""What the Prep's tests build their decks and labware with: a Prep deck in an in-memory store."""

from __future__ import annotations

from typing import Optional

from pylabrobot.hamilton.prep.deck import PrepDeckParts, prep_deck, read_prep_deck
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import types_pb2 as pb


async def make_prep_deck(
  name: str = "deck", name_prefix: Optional[str] = None, **parts: bool
) -> handles.Deck:
  """A Prep deck in a store of its own; `parts` are `prep_deck`'s `with_` flags."""
  store = ResourceStore.in_memory()
  deck = await store.create(prep_deck(name, name_prefix=name_prefix, **parts), name=name)
  assert isinstance(deck, handles.Deck)
  return deck


async def make_plain_deck(name: str = "deck") -> handles.Deck:
  """A deck that is not a Prep's, in a store of its own: nothing is modelled on it."""
  store = ResourceStore.in_memory()
  deck = await store.create(
    build.resource(name, Coordinate(1000, 650, 300), kind=pb.RESOURCE_KIND_DECK), name=name
  )
  assert isinstance(deck, handles.Deck)
  return deck


async def parts_of(deck: handles.Deck) -> PrepDeckParts:
  return await read_prep_deck(deck)


async def place(deck: handles.Deck, model: str, name: str, spot: int) -> handles.Resource:
  """One of PLR's labware models, made on one of a Prep deck's spots, 0 to 7."""
  parts = await read_prep_deck(deck)
  return await deck.store.create(model, name=name, parent=parts.spots[spot])
