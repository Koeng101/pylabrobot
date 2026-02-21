"""Shared fixtures for remote STAR backend tests.

Creates a server-side STARBackend with mocked I/O, wraps it in the
ConnectRPC ASGI app, runs uvicorn in a background thread, and provides
a RemoteSTARBackend client connected to it.
"""

from __future__ import annotations

import threading
import time
import unittest.mock
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
import uvicorn

from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend
from pylabrobot.liquid_handling.backends.hamilton.remote.client import RemoteSTARBackend
from pylabrobot.liquid_handling.backends.hamilton.remote.server import create_star_app
from pylabrobot.liquid_handling.backends.hamilton.remote.star_service_connect import (
  STARServiceClientSync,
)
from pylabrobot.resources import (
  PLT_CAR_L5AC_A00,
  TIP_CAR_480_A00,
  Coordinate,
  Container,
  Cor_96_wellplate_360ul_Fb,
  Lid,
  hamilton_96_tiprack_300uL_filter,
  hamilton_96_tiprack_1000uL_filter,
)
from pylabrobot.resources.hamilton import STARLetDeck

_PORT = 18765


@dataclass
class StarServiceFixture:
  """Holds both ends of the remote STAR setup for testing."""

  backend: STARBackend
  remote: RemoteSTARBackend
  deck: STARLetDeck


class _ServerThread:
  """Run uvicorn in a background thread."""

  def __init__(self, app, port: int):
    self.port = port
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    self._server = uvicorn.Server(config)
    self._thread = threading.Thread(target=self._server.run, daemon=True)

  def start(self):
    self._thread.start()
    time.sleep(0.8)

  def stop(self):
    self._server.should_exit = True
    self._thread.join(timeout=3)


def _make_mocked_backend() -> tuple[STARBackend, STARLetDeck]:
  """Create a STARBackend with mocked I/O, matching STAR_tests.py setup."""
  backend = STARBackend(read_timeout=1)
  backend._write_and_read_command = unittest.mock.AsyncMock(return_value=None)
  backend.io = unittest.mock.AsyncMock()
  backend.io.setup = unittest.mock.AsyncMock()
  backend.io.write = unittest.mock.MagicMock()
  backend.io.read = unittest.mock.MagicMock()

  # Backend state
  backend._num_channels = 8
  backend.iswap_installed = True
  backend.core96_head_installed = True
  backend._core_parked = True
  backend._iswap_parked = True

  # Extended configuration (normally loaded during setup via request_extended_configuration)
  backend._extended_conf = {
    "ka": 0, "ke": 0,
    "xt": 54,       # number of tracks/rails
    "xa": 30,       # right X-arm configuration
    "xw": 13130,    # tip eject waste X position
    "xl": 0, "xn": 0, "xr": 0, "xo": 0,
    "xm": 0, "xx": 0, "xu": 0, "xv": 0,
    "kc": 0, "kr": 0, "ys": 0,
    "kl": 0, "km": 0, "ym": 0, "yu": 0, "yx": 0,
  }

  # Build deck with resources (matching STAR_tests.py layout)
  deck = STARLetDeck()

  tip_car = TIP_CAR_480_A00(name="tip carrier")
  tip_car[1] = hamilton_96_tiprack_300uL_filter(name="tip_rack_01")
  tip_car[2] = hamilton_96_tiprack_1000uL_filter(name="tip_rack_02")
  deck.assign_child_resource(tip_car, rails=1)

  plt_car = PLT_CAR_L5AC_A00(name="plate carrier")
  plate = Cor_96_wellplate_360ul_Fb(name="plate_01")
  lid = Lid(
    name="plate_01_lid",
    size_x=plate.get_size_x(),
    size_y=plate.get_size_y(),
    size_z=10,
    nesting_z_height=10,
  )
  plate.assign_child_resource(lid)
  plt_car[0] = plate

  other_plate = Cor_96_wellplate_360ul_Fb(name="plate_02")
  lid2 = Lid(
    name="plate_02_lid",
    size_x=other_plate.get_size_x(),
    size_y=other_plate.get_size_y(),
    size_z=10,
    nesting_z_height=10,
  )
  other_plate.assign_child_resource(lid2)
  plt_car[1] = other_plate
  deck.assign_child_resource(plt_car, rails=9)

  backend.set_deck(deck)
  # Skip actual setup — mock it
  backend.setup = unittest.mock.AsyncMock()

  return backend, deck


@pytest.fixture(scope="module")
def star_service():
  """Module-scoped fixture: mocked STARBackend + server + RemoteSTARBackend client."""
  backend, deck = _make_mocked_backend()
  app = create_star_app(backend)

  server_thread = _ServerThread(app, port=_PORT)
  server_thread.start()

  try:
    client = STARServiceClientSync(address=f"http://127.0.0.1:{_PORT}")
    remote = RemoteSTARBackend(client)
    yield StarServiceFixture(backend=backend, remote=remote, deck=deck)
  finally:
    server_thread.stop()
