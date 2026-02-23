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
  AGenBio_1_troughplate_190000uL_Fl,
  CellTreat_96_wellplate_350ul_Ub,
  PLT_CAR_L5AC_A00,
  PLT_CAR_L5MD_A00,
  PLT_CAR_P3AC_A01,
  TIP_CAR_480_A00,
  Coordinate,
  Container,
  Cor_96_wellplate_360ul_Fb,
  Lid,
  hamilton_96_tiprack_300uL_filter,
  hamilton_96_tiprack_1000uL,
  hamilton_96_tiprack_1000uL_filter,
)
from pylabrobot.resources.hamilton import STARLetDeck

_PORT = 18765
_PORT_ISWAP = 18766
_PORT_FOIL = 18767


@dataclass
class StarServiceFixture:
  """Holds both ends of the remote STAR setup for testing."""

  backend: STARBackend
  remote: RemoteSTARBackend
  deck: STARLetDeck
  bb: Container  # BlueBucket


@dataclass
class StarServiceIswapFixture:
  """Fixture for iSwap movement tests with a different deck layout."""

  backend: STARBackend
  remote: RemoteSTARBackend
  deck: STARLetDeck
  plt_car: PLT_CAR_L5MD_A00
  plt_car2: PLT_CAR_P3AC_A01
  plate: CellTreat_96_wellplate_350ul_Ub


@dataclass
class StarServiceFoilFixture:
  """Fixture for foil piercing tests with a different deck layout."""

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


def _init_backend_state(backend: STARBackend) -> None:
  """Set common backend state for mocked testing."""
  backend._write_and_read_command = unittest.mock.AsyncMock(return_value=None)
  backend.io = unittest.mock.AsyncMock()
  backend.io.setup = unittest.mock.AsyncMock()
  backend.io.write = unittest.mock.MagicMock()
  backend.io.read = unittest.mock.MagicMock()

  backend._num_channels = 8
  backend.iswap_installed = True
  backend.core96_head_installed = True
  backend._core_parked = True
  backend._iswap_parked = True

  backend._extended_conf = {
    "ka": 0, "ke": 0,
    "xt": 54, "xa": 30, "xw": 13130,
    "xl": 0, "xn": 0, "xr": 0, "xo": 0,
    "xm": 0, "xx": 0, "xu": 0, "xv": 0,
    "kc": 0, "kr": 0, "ys": 0,
    "kl": 0, "km": 0, "ym": 0, "yu": 0, "yx": 0,
  }
  backend.setup = unittest.mock.AsyncMock()


class BlueBucket(Container):
  def __init__(self, name: str):
    super().__init__(
      name,
      size_x=123,
      size_y=82,
      size_z=75,
      category="bucket",
      max_volume=123 * 82 * 75,
      material_z_thickness=1,
    )


def _make_mocked_backend() -> tuple[STARBackend, STARLetDeck, Container]:
  """Create a STARBackend with mocked I/O, matching STAR_tests.py setup."""
  backend = STARBackend(read_timeout=1)
  _init_backend_state(backend)

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

  bb = BlueBucket(name="blue bucket")
  deck.assign_child_resource(bb, location=Coordinate(425, 141.5, 120 - 1))

  backend.set_deck(deck)
  return backend, deck, bb


def _make_iswap_movement_backend() -> tuple[
  STARBackend, STARLetDeck, PLT_CAR_L5MD_A00, PLT_CAR_P3AC_A01,
  CellTreat_96_wellplate_350ul_Ub,
]:
  """Deck: PLT_CAR_L5MD_A00 at rails=15, PLT_CAR_P3AC_A01 at rails=3."""
  backend = STARBackend()
  _init_backend_state(backend)

  deck = STARLetDeck()
  plt_car = PLT_CAR_L5MD_A00(name="plt_car")
  plt_car[0] = plate = CellTreat_96_wellplate_350ul_Ub(name="plate", with_lid=True)
  deck.assign_child_resource(plt_car, rails=15)

  plt_car2 = PLT_CAR_P3AC_A01(name="plt_car2")
  deck.assign_child_resource(plt_car2, rails=3)

  backend.set_deck(deck)
  return backend, deck, plt_car, plt_car2, plate


def _make_foil_backend() -> tuple[STARBackend, STARLetDeck]:
  """Deck for foil piercing: tip carrier + plate carrier + AGenBio trough plate."""
  backend = STARBackend()
  _init_backend_state(backend)

  deck = STARLetDeck()

  tip_carrier = TIP_CAR_480_A00(name="tip_carrier")
  tip_carrier[1] = hamilton_96_tiprack_1000uL(name="tip_rack")
  deck.assign_child_resource(tip_carrier, rails=1)

  plt_carrier = PLT_CAR_L5AC_A00(name="plt_carrier")
  plt_carrier[0] = AGenBio_1_troughplate_190000uL_Fl(name="plate")
  deck.assign_child_resource(plt_carrier, rails=10)

  backend.set_deck(deck)
  return backend, deck


@pytest.fixture(scope="module")
def star_service():
  """Module-scoped fixture: mocked STARBackend + server + RemoteSTARBackend client."""
  backend, deck, bb = _make_mocked_backend()
  app = create_star_app(backend)

  server_thread = _ServerThread(app, port=_PORT)
  server_thread.start()

  try:
    client = STARServiceClientSync(address=f"http://127.0.0.1:{_PORT}")
    remote = RemoteSTARBackend(client)
    yield StarServiceFixture(backend=backend, remote=remote, deck=deck, bb=bb)
  finally:
    server_thread.stop()


@pytest.fixture(scope="module")
def star_service_iswap():
  """Module-scoped fixture for iSwap movement tests."""
  backend, deck, plt_car, plt_car2, plate = _make_iswap_movement_backend()
  app = create_star_app(backend)

  server_thread = _ServerThread(app, port=_PORT_ISWAP)
  server_thread.start()

  try:
    client = STARServiceClientSync(address=f"http://127.0.0.1:{_PORT_ISWAP}")
    remote = RemoteSTARBackend(client)
    yield StarServiceIswapFixture(
      backend=backend, remote=remote, deck=deck,
      plt_car=plt_car, plt_car2=plt_car2, plate=plate,
    )
  finally:
    server_thread.stop()


@pytest.fixture(scope="module")
def star_service_foil():
  """Module-scoped fixture for foil piercing tests."""
  backend, deck = _make_foil_backend()
  app = create_star_app(backend)

  server_thread = _ServerThread(app, port=_PORT_FOIL)
  server_thread.start()

  try:
    client = STARServiceClientSync(address=f"http://127.0.0.1:{_PORT_FOIL}")
    remote = RemoteSTARBackend(client)
    yield StarServiceFoilFixture(backend=backend, remote=remote, deck=deck)
  finally:
    server_thread.stop()
