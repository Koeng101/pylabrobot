"""RPC handlers for lifecycle operations (Setup, Stop, capability queries)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import star_service_pb2 as pb2

if TYPE_CHECKING:
  from connectrpc.request import RequestContext

  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend


class LifecycleServerMixin:
  _backend: STARBackend
  """RPC handlers for lifecycle operations.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

  async def setup(self, request: pb2.SetupRequest, ctx: RequestContext) -> pb2.SetupResponse:
    await self._backend.setup()
    return pb2.SetupResponse()

  async def stop(self, request: pb2.StopRequest, ctx: RequestContext) -> pb2.StopResponse:
    await self._backend.stop()
    return pb2.StopResponse()

  async def get_num_channels(
    self, request: pb2.GetNumChannelsRequest, ctx: RequestContext
  ) -> pb2.GetNumChannelsResponse:
    return pb2.GetNumChannelsResponse(num_channels=self._backend.num_channels)

  async def get_head96_installed(
    self, request: pb2.GetHead96InstalledRequest, ctx: RequestContext
  ) -> pb2.GetHead96InstalledResponse:
    return pb2.GetHead96InstalledResponse(installed=self._backend.core96_head_installed)  # type: ignore[arg-type]

  async def get_iswap_installed(
    self, request: pb2.GetIswapInstalledRequest, ctx: RequestContext
  ) -> pb2.GetIswapInstalledResponse:
    return pb2.GetIswapInstalledResponse(installed=self._backend.iswap_installed)  # type: ignore[arg-type]

  async def get_iswap_parked(
    self, request: pb2.GetIswapParkedRequest, ctx: RequestContext
  ) -> pb2.GetIswapParkedResponse:
    return pb2.GetIswapParkedResponse(parked=self._backend._iswap_parked)  # type: ignore[arg-type]

  async def get_core_parked(
    self, request: pb2.GetCoreParkedRequest, ctx: RequestContext
  ) -> pb2.GetCoreParkedResponse:
    return pb2.GetCoreParkedResponse(parked=self._backend._core_parked)  # type: ignore[arg-type]
