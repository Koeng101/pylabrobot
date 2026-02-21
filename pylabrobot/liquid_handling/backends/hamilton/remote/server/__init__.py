"""STARService server implementation combining all mixins."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._autoload import AutoloadServerMixin
from ._channel import ChannelServerMixin
from ._core_gripper import CoreGripperServerMixin
from ._head96 import Head96ServerMixin
from ._iswap import IswapServerMixin
from ._lifecycle import LifecycleServerMixin
from ._misc import MiscServerMixin
from ._pipetting import PipettingServerMixin
from ..star_service_connect import STARServiceASGIApplication

if TYPE_CHECKING:
  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend


class STARServiceImpl(
  PipettingServerMixin,
  ChannelServerMixin,
  Head96ServerMixin,
  IswapServerMixin,
  CoreGripperServerMixin,
  AutoloadServerMixin,
  MiscServerMixin,
  LifecycleServerMixin,
):
  """ConnectRPC service implementation that wraps a real STARBackend."""

  def __init__(self, backend: STARBackend):
    self._backend = backend
    self._deck = backend.deck


def create_star_app(backend: STARBackend) -> STARServiceASGIApplication:
  """Create an ASGI application for the STAR service."""
  return STARServiceASGIApplication(STARServiceImpl(backend))
