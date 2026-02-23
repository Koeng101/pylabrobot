"""RemoteSTARBackend client implementation combining all mixins."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..star_service_connect import STARServiceClientSync
from ._autoload import AutoloadClientMixin
from ._channel import ChannelClientMixin
from ._core_gripper import CoreGripperClientMixin
from ._head96 import Head96ClientMixin
from ._iswap import IswapClientMixin
from ._lifecycle import LifecycleClientMixin
from ._misc import MiscClientMixin
from ._pipetting import PipettingClientMixin

if TYPE_CHECKING:
  pass


class RemoteSTARBackend(
  PipettingClientMixin,
  ChannelClientMixin,
  Head96ClientMixin,
  IswapClientMixin,
  CoreGripperClientMixin,
  AutoloadClientMixin,
  MiscClientMixin,
  LifecycleClientMixin,
):
  """ConnectRPC client that acts as a drop-in replacement for STARBackend."""

  def __init__(self, client: STARServiceClientSync):
    super().__init__()
    self._client = client

  @classmethod
  def connect(cls, base_url: str = "http://localhost:8080") -> "RemoteSTARBackend":
    """Create a RemoteSTARBackend connected to a remote STAR service."""
    client = STARServiceClientSync(address=base_url)
    return cls(client)
