"""What a Prep deck says of what stands on it."""

import asyncio
import logging

import pytest

from pylabrobot.hamilton.prep.deck import warn_of_resources_above_safe_height
from pylabrobot.hamilton.prep.driver.test_helpers import make_prep_deck, parts_of
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build


def test_a_resource_above_the_safe_height_is_warned_of(caplog: pytest.LogCaptureFixture) -> None:
  async def _run() -> None:
    deck = await make_prep_deck()
    spots = (await parts_of(deck)).spots
    tall = await deck.store.create(
      build.resource("tower", Coordinate(100, 80, 90)), name="tower", parent=spots[0]
    )
    await deck.store.create(
      build.resource("low", Coordinate(100, 80, 20)), name="low", parent=spots[1]
    )
    with caplog.at_level(logging.WARNING, logger="pylabrobot.hamilton.prep.deck"):
      await warn_of_resources_above_safe_height(deck)
    warned = [r.getMessage() for r in caplog.records]
    assert any("'tower'" in message for message in warned), warned
    assert not any("'low'" in message for message in warned), warned

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="pylabrobot.hamilton.prep.deck"):
      await warn_of_resources_above_safe_height(deck, [tall.id])
    assert len(caplog.records) == 1

  asyncio.run(_run())


def test_the_bare_deck_stands_below_the_safe_height(caplog: pytest.LogCaptureFixture) -> None:
  async def _run() -> None:
    deck = await make_prep_deck()
    with caplog.at_level(logging.WARNING, logger="pylabrobot.hamilton.prep.deck"):
      await warn_of_resources_above_safe_height(deck)
    assert caplog.records == []

  asyncio.run(_run())
