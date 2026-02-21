"""Client stubs for channel movement and queries."""

from __future__ import annotations

from typing import Dict

from .. import star_service_pb2 as pb2


class ChannelClientMixin:
  """Client stubs for channel movement and queries.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # -- absolute moves --

  async def move_channel_x(self, channel: int, x: float) -> None:
    self._client.move_channel_x(pb2.MoveChannelXRequest(channel=channel, x=x))

  async def move_channel_y(self, channel: int, y: float) -> None:
    self._client.move_channel_y(pb2.MoveChannelYRequest(channel=channel, y=y))

  async def move_channel_z(self, channel: int, z: float) -> None:
    self._client.move_channel_z(pb2.MoveChannelZRequest(channel=channel, z=z))

  # -- relative moves --

  async def move_channel_x_relative(self, channel: int, distance: float) -> None:
    self._client.move_channel_x_relative(
      pb2.MoveChannelXRelativeRequest(channel=channel, distance=distance)
    )

  async def move_channel_y_relative(self, channel: int, distance: float) -> None:
    self._client.move_channel_y_relative(
      pb2.MoveChannelYRelativeRequest(channel=channel, distance=distance)
    )

  async def move_channel_z_relative(self, channel: int, distance: float) -> None:
    self._client.move_channel_z_relative(
      pb2.MoveChannelZRelativeRequest(channel=channel, distance=distance)
    )

  # -- manual / safety --

  async def prepare_for_manual_channel_operation(self, channel: int) -> None:
    self._client.prepare_for_manual_channel_operation(
      pb2.PrepareForManualChannelOperationRequest(channel=channel)
    )

  async def move_all_channels_in_z_safety(self) -> None:
    self._client.move_all_channels_in_z_safety(pb2.MoveAllChannelsInZSafetyRequest())

  # -- single-channel positioning --

  async def position_single_pipetting_channel_in_y_direction(
    self, pipetting_channel_index: int, y_position: int,
  ) -> None:
    self._client.position_single_pipetting_channel_in_y_direction(
      pb2.PositionSinglePipettingChannelInYDirectionRequest(
        pipetting_channel_index=pipetting_channel_index,
        y_position=y_position,
      )
    )

  async def position_single_pipetting_channel_in_z_direction(
    self, pipetting_channel_index: int, z_position: int,
  ) -> None:
    self._client.position_single_pipetting_channel_in_z_direction(
      pb2.PositionSinglePipettingChannelInZDirectionRequest(
        pipetting_channel_index=pipetting_channel_index,
        z_position=z_position,
      )
    )

  async def position_max_free_y_for_n(self, pipetting_channel_index: int) -> None:
    self._client.position_max_free_y_for_n(
      pb2.PositionMaxFreeYForNRequest(pipetting_channel_index=pipetting_channel_index)
    )

  # -- single-channel position queries --

  async def request_x_pos_channel_n(self, pipetting_channel_index: int) -> float:
    resp = self._client.request_x_pos_channel_n(
      pb2.RequestXPosChannelNRequest(pipetting_channel_index=pipetting_channel_index)
    )
    return resp.x_position

  async def request_y_pos_channel_n(self, pipetting_channel_index: int) -> float:
    resp = self._client.request_y_pos_channel_n(
      pb2.RequestYPosChannelNRequest(pipetting_channel_index=pipetting_channel_index)
    )
    return resp.y_position

  async def request_z_pos_channel_n(self, pipetting_channel_index: int) -> float:
    resp = self._client.request_z_pos_channel_n(
      pb2.RequestZPosChannelNRequest(pipetting_channel_index=pipetting_channel_index)
    )
    return resp.z_position

  async def request_tip_bottom_z_position(self, channel_idx: int) -> float:
    resp = self._client.request_tip_bottom_z_position(
      pb2.RequestTipBottomZPositionRequest(channel_idx=channel_idx)
    )
    return resp.z_position

  # -- multi-channel Y queries / positioning --

  async def get_channels_y_positions(self) -> Dict[int, float]:
    resp = self._client.get_channels_y_positions(pb2.GetChannelsYPositionsRequest())
    return dict(resp.positions.entries)

  async def position_channels_in_y_direction(
    self, ys: Dict[int, float], make_space: bool = True,
  ) -> None:
    self._client.position_channels_in_y_direction(
      pb2.PositionChannelsInYDirectionRequest(
        ys=pb2.ChannelFloatMap(entries=ys),
        make_space=make_space,
      )
    )

  # -- multi-channel Z queries / positioning --

  async def get_channels_z_positions(self) -> Dict[int, float]:
    resp = self._client.get_channels_z_positions(pb2.GetChannelsZPositionsRequest())
    return dict(resp.positions.entries)

  async def position_channels_in_z_direction(self, zs: Dict[int, float]) -> None:
    self._client.position_channels_in_z_direction(
      pb2.PositionChannelsInZDirectionRequest(
        zs=pb2.ChannelFloatMap(entries=zs),
      )
    )

  # -- version query --

  async def request_pip_channel_version(self, channel: int) -> str:
    resp = self._client.request_pip_channel_version(
      pb2.RequestPipChannelVersionRequest(channel=channel)
    )
    return resp.version
