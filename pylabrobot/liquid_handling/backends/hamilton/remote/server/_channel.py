"""RPC handlers for channel movement and queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import star_service_pb2 as pb2

if TYPE_CHECKING:
  from connectrpc.request import RequestContext

  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend


class ChannelServerMixin:
  _backend: STARBackend
  """RPC handlers for channel movement and queries.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

  # -- absolute moves --

  async def move_channel_x(
    self, request: pb2.MoveChannelXRequest, ctx: RequestContext
  ) -> pb2.MoveChannelXResponse:
    await self._backend.move_channel_x(request.channel, request.x)
    return pb2.MoveChannelXResponse()

  async def move_channel_y(
    self, request: pb2.MoveChannelYRequest, ctx: RequestContext
  ) -> pb2.MoveChannelYResponse:
    await self._backend.move_channel_y(request.channel, request.y)
    return pb2.MoveChannelYResponse()

  async def move_channel_z(
    self, request: pb2.MoveChannelZRequest, ctx: RequestContext
  ) -> pb2.MoveChannelZResponse:
    await self._backend.move_channel_z(request.channel, request.z)
    return pb2.MoveChannelZResponse()

  # -- relative moves --

  async def move_channel_x_relative(
    self, request: pb2.MoveChannelXRelativeRequest, ctx: RequestContext
  ) -> pb2.MoveChannelXRelativeResponse:
    await self._backend.move_channel_x_relative(request.channel, request.distance)
    return pb2.MoveChannelXRelativeResponse()

  async def move_channel_y_relative(
    self, request: pb2.MoveChannelYRelativeRequest, ctx: RequestContext
  ) -> pb2.MoveChannelYRelativeResponse:
    await self._backend.move_channel_y_relative(request.channel, request.distance)
    return pb2.MoveChannelYRelativeResponse()

  async def move_channel_z_relative(
    self, request: pb2.MoveChannelZRelativeRequest, ctx: RequestContext
  ) -> pb2.MoveChannelZRelativeResponse:
    await self._backend.move_channel_z_relative(request.channel, request.distance)
    return pb2.MoveChannelZRelativeResponse()

  # -- manual / safety --

  async def prepare_for_manual_channel_operation(
    self,
    request: pb2.PrepareForManualChannelOperationRequest,
    ctx: RequestContext,
  ) -> pb2.PrepareForManualChannelOperationResponse:
    await self._backend.prepare_for_manual_channel_operation(request.channel)
    return pb2.PrepareForManualChannelOperationResponse()

  async def move_all_channels_in_z_safety(
    self,
    request: pb2.MoveAllChannelsInZSafetyRequest,
    ctx: RequestContext,
  ) -> pb2.MoveAllChannelsInZSafetyResponse:
    await self._backend.move_all_channels_in_z_safety()
    return pb2.MoveAllChannelsInZSafetyResponse()

  # -- single-channel positioning --

  async def position_single_pipetting_channel_in_y_direction(
    self,
    request: pb2.PositionSinglePipettingChannelInYDirectionRequest,
    ctx: RequestContext,
  ) -> pb2.PositionSinglePipettingChannelInYDirectionResponse:
    await self._backend.position_single_pipetting_channel_in_y_direction(
      pipetting_channel_index=request.pipetting_channel_index,
      y_position=request.y_position,
    )
    return pb2.PositionSinglePipettingChannelInYDirectionResponse()

  async def position_single_pipetting_channel_in_z_direction(
    self,
    request: pb2.PositionSinglePipettingChannelInZDirectionRequest,
    ctx: RequestContext,
  ) -> pb2.PositionSinglePipettingChannelInZDirectionResponse:
    await self._backend.position_single_pipetting_channel_in_z_direction(
      pipetting_channel_index=request.pipetting_channel_index,
      z_position=request.z_position,
    )
    return pb2.PositionSinglePipettingChannelInZDirectionResponse()

  async def position_max_free_y_for_n(
    self,
    request: pb2.PositionMaxFreeYForNRequest,
    ctx: RequestContext,
  ) -> pb2.PositionMaxFreeYForNResponse:
    await self._backend.position_max_free_y_for_n(
      pipetting_channel_index=request.pipetting_channel_index,
    )
    return pb2.PositionMaxFreeYForNResponse()

  # -- single-channel position queries --

  async def request_x_pos_channel_n(
    self,
    request: pb2.RequestXPosChannelNRequest,
    ctx: RequestContext,
  ) -> pb2.RequestXPosChannelNResponse:
    x = await self._backend.request_x_pos_channel_n(
      pipetting_channel_index=request.pipetting_channel_index,
    )
    return pb2.RequestXPosChannelNResponse(x_position=x)

  async def request_y_pos_channel_n(
    self,
    request: pb2.RequestYPosChannelNRequest,
    ctx: RequestContext,
  ) -> pb2.RequestYPosChannelNResponse:
    y = await self._backend.request_y_pos_channel_n(
      pipetting_channel_index=request.pipetting_channel_index,
    )
    return pb2.RequestYPosChannelNResponse(y_position=y)

  async def request_z_pos_channel_n(
    self,
    request: pb2.RequestZPosChannelNRequest,
    ctx: RequestContext,
  ) -> pb2.RequestZPosChannelNResponse:
    z = await self._backend.request_z_pos_channel_n(
      pipetting_channel_index=request.pipetting_channel_index,
    )
    return pb2.RequestZPosChannelNResponse(z_position=z)

  async def request_tip_bottom_z_position(
    self,
    request: pb2.RequestTipBottomZPositionRequest,
    ctx: RequestContext,
  ) -> pb2.RequestTipBottomZPositionResponse:
    z = await self._backend.request_tip_bottom_z_position(
      channel_idx=request.channel_idx,
    )
    return pb2.RequestTipBottomZPositionResponse(z_position=z)

  # -- multi-channel Y queries / positioning --

  async def get_channels_y_positions(
    self,
    request: pb2.GetChannelsYPositionsRequest,
    ctx: RequestContext,
  ) -> pb2.GetChannelsYPositionsResponse:
    positions = await self._backend.get_channels_y_positions()
    return pb2.GetChannelsYPositionsResponse(
      positions=pb2.ChannelFloatMap(entries=positions),
    )

  async def position_channels_in_y_direction(
    self,
    request: pb2.PositionChannelsInYDirectionRequest,
    ctx: RequestContext,
  ) -> pb2.PositionChannelsInYDirectionResponse:
    ys = dict(request.ys.entries)
    await self._backend.position_channels_in_y_direction(
      ys=ys,
      make_space=request.make_space,
    )
    return pb2.PositionChannelsInYDirectionResponse()

  # -- multi-channel Z queries / positioning --

  async def get_channels_z_positions(
    self,
    request: pb2.GetChannelsZPositionsRequest,
    ctx: RequestContext,
  ) -> pb2.GetChannelsZPositionsResponse:
    positions = await self._backend.get_channels_z_positions()
    return pb2.GetChannelsZPositionsResponse(
      positions=pb2.ChannelFloatMap(entries=positions),
    )

  async def position_channels_in_z_direction(
    self,
    request: pb2.PositionChannelsInZDirectionRequest,
    ctx: RequestContext,
  ) -> pb2.PositionChannelsInZDirectionResponse:
    zs = dict(request.zs.entries)
    await self._backend.position_channels_in_z_direction(zs=zs)
    return pb2.PositionChannelsInZDirectionResponse()

  # -- version query --

  async def request_pip_channel_version(
    self,
    request: pb2.RequestPipChannelVersionRequest,
    ctx: RequestContext,
  ) -> pb2.RequestPipChannelVersionResponse:
    version = await self._backend.request_pip_channel_version(
      channel=request.channel,
    )
    return pb2.RequestPipChannelVersionResponse(version=version)
