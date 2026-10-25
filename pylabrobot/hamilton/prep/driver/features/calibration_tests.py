"""The squeeze-tip calibrations, planned from the tip spots the store holds."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, List, cast

import pytest

from pylabrobot.hamilton.prep.driver import prep_commands as PrepCmd
from pylabrobot.hamilton.prep.driver.features.calibration import CalibrationSession
from pylabrobot.hamilton.prep.driver.model import ref
from pylabrobot.hamilton.prep.driver.test_helpers import make_prep_deck, place
from pylabrobot.resources.errors import NoTipError
from pylabrobot.resources.store import handles


async def _session(deck: handles.Deck, sent: List[Any]) -> CalibrationSession:
  """A started session on a stand-in for the calibration façade, capturing what it sends."""

  async def send_command(command: Any, read_timeout: Any = None) -> None:
    sent.append(command)

  cal = SimpleNamespace(
    _driver=SimpleNamespace(store=deck.store, send_command=send_command),
    _require_deck=lambda: ref(deck.id),
    num_channels=2,
    _channel_enum=lambda channel: channel,
    head8_installed=True,
  )
  session = CalibrationSession(cast(Any, cal), report_after_command=False)
  session._started = True

  async def values(read_timeout: Any = None) -> None:
    return None

  session._get_calibration_values = values  # type: ignore[method-assign, assignment]
  return session


async def _rack(deck: handles.Deck) -> handles.TipRack:
  rack = await place(deck, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
  assert isinstance(rack, handles.TipRack)
  return rack


@pytest.mark.parametrize("mph", [False, True])
def test_an_untracked_spot_calibrates_with_the_tip_it_would_hand_out(mph: bool) -> None:
  async def _run() -> None:
    deck = await make_prep_deck()
    rack = await _rack(deck)
    await rack.set_tip_tracking(False)
    sent: List[Any] = []
    session = await _session(deck, sent)
    spots = rack["A1:B1"]
    if mph:
      await session.calibrate_squeeze_tips_mph(spots[0])
    else:
      await session.calibrate_squeeze_tips(spots)
    (command,) = sent
    assert isinstance(command, PrepCmd.PrepCalibrateSqueezeTips)
    assert len(command.channels) == (1 if mph else 2)

  asyncio.run(_run())


def test_an_empty_tracked_spot_is_refused_as_holding_no_tip() -> None:
  async def _run() -> None:
    deck = await make_prep_deck()
    rack = await _rack(deck)
    await rack.empty()
    sent: List[Any] = []
    session = await _session(deck, sent)
    with pytest.raises(NoTipError):
      await session.calibrate_squeeze_tips(rack["A1"])
    assert sent == []

  asyncio.run(_run())
