"""Client stubs for lifecycle operations (Setup, Stop, capability queries)."""

from __future__ import annotations

from .. import star_service_pb2 as pb2


class LifecycleClientMixin:
  """Client stubs for lifecycle operations.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  async def setup(self) -> None:
    self._client.setup(pb2.SetupRequest())

  async def stop(self) -> None:
    self._client.stop(pb2.StopRequest())

  @property
  def num_channels(self) -> int:
    resp = self._client.get_num_channels(pb2.GetNumChannelsRequest())
    return resp.num_channels

  @property
  def core96_head_installed(self) -> bool:
    resp = self._client.get_head96_installed(pb2.GetHead96InstalledRequest())
    return resp.installed

  @property
  def iswap_installed(self) -> bool:
    resp = self._client.get_iswap_installed(pb2.GetIswapInstalledRequest())
    return resp.installed

  @property
  def iswap_parked(self) -> bool:
    resp = self._client.get_iswap_parked(pb2.GetIswapParkedRequest())
    return resp.parked

  @property
  def core_parked(self) -> bool:
    resp = self._client.get_core_parked(pb2.GetCoreParkedRequest())
    return resp.parked
