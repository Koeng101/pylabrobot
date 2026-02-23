"""RPC handlers for firmware queries, config, cover, HHS, pump, X-arm, and special ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import star_service_pb2 as pb2
from ..helpers import tip_from_proto

if TYPE_CHECKING:
  from connectrpc.request import RequestContext

  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend


class MiscServerMixin:
  _backend: STARBackend
  """RPC handlers for firmware queries, config, cover, HHS, pump, X-arm, and special ops.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

  # =========================================================================
  # Cover
  # =========================================================================

  async def lock_cover(
    self, request: pb2.LockCoverRequest, ctx: RequestContext
  ) -> pb2.LockCoverResponse:
    await self._backend.lock_cover()
    return pb2.LockCoverResponse()

  async def unlock_cover(
    self, request: pb2.UnlockCoverRequest, ctx: RequestContext
  ) -> pb2.UnlockCoverResponse:
    await self._backend.unlock_cover()
    return pb2.UnlockCoverResponse()

  async def disable_cover_control(
    self, request: pb2.DisableCoverControlRequest, ctx: RequestContext
  ) -> pb2.DisableCoverControlResponse:
    await self._backend.disable_cover_control()
    return pb2.DisableCoverControlResponse()

  async def enable_cover_control(
    self, request: pb2.EnableCoverControlRequest, ctx: RequestContext
  ) -> pb2.EnableCoverControlResponse:
    await self._backend.enable_cover_control()
    return pb2.EnableCoverControlResponse()

  async def set_cover_output(
    self, request: pb2.SetCoverOutputRequest, ctx: RequestContext
  ) -> pb2.SetCoverOutputResponse:
    await self._backend.set_cover_output(output=request.output)
    return pb2.SetCoverOutputResponse()

  async def reset_output(
    self, request: pb2.ResetOutputRequest, ctx: RequestContext
  ) -> pb2.ResetOutputResponse:
    await self._backend.reset_output(output=request.output)
    return pb2.ResetOutputResponse()

  async def request_cover_open(
    self, request: pb2.RequestCoverOpenRequest, ctx: RequestContext
  ) -> pb2.RequestCoverOpenResponse:
    is_open = await self._backend.request_cover_open()
    return pb2.RequestCoverOpenResponse(open=is_open)

  # =========================================================================
  # HHS (Heater/Shaker)
  # =========================================================================

  async def send_hhs_command(
    self, request: pb2.SendHhsCommandRequest, ctx: RequestContext
  ) -> pb2.SendHhsCommandResponse:
    response = await self._backend.send_hhs_command(
      index=request.index,
      command=request.command,
    )
    return pb2.SendHhsCommandResponse(response=response)

  async def check_type_is_hhc(
    self, request: pb2.CheckTypeIsHhcRequest, ctx: RequestContext
  ) -> pb2.CheckTypeIsHhcResponse:
    await self._backend.check_type_is_hhc(device_number=request.device_number)
    return pb2.CheckTypeIsHhcResponse()

  async def initialize_hhc(
    self, request: pb2.InitializeHhcRequest, ctx: RequestContext
  ) -> pb2.InitializeHhcResponse:
    response = await self._backend.initialize_hhc(device_number=request.device_number)
    return pb2.InitializeHhcResponse(response=response)

  async def start_temperature_control_at_hhc(
    self, request: pb2.StartTemperatureControlAtHhcRequest, ctx: RequestContext
  ) -> pb2.StartTemperatureControlAtHhcResponse:
    await self._backend.start_temperature_control_at_hhc(
      device_number=request.device_number,
      temperature=request.temperature,  # type: ignore[call-arg]
    )
    return pb2.StartTemperatureControlAtHhcResponse()

  async def get_temperature_at_hhc(
    self, request: pb2.GetTemperatureAtHhcRequest, ctx: RequestContext
  ) -> pb2.GetTemperatureAtHhcResponse:
    result = await self._backend.get_temperature_at_hhc(
      device_number=request.device_number,
    )
    return pb2.GetTemperatureAtHhcResponse(
      current_temperature=result["current"],
      target_temperature=result["target"],
    )

  async def query_whether_temperature_reached_at_hhc(
    self,
    request: pb2.QueryWhetherTemperatureReachedAtHhcRequest,
    ctx: RequestContext,
  ) -> pb2.QueryWhetherTemperatureReachedAtHhcResponse:
    await self._backend.query_whether_temperature_reached_at_hhc(
      device_number=request.device_number,
    )
    return pb2.QueryWhetherTemperatureReachedAtHhcResponse()

  async def stop_temperature_control_at_hhc(
    self, request: pb2.StopTemperatureControlAtHhcRequest, ctx: RequestContext
  ) -> pb2.StopTemperatureControlAtHhcResponse:
    await self._backend.stop_temperature_control_at_hhc(
      device_number=request.device_number,
    )
    return pb2.StopTemperatureControlAtHhcResponse()

  # =========================================================================
  # Firmware queries
  # =========================================================================

  async def request_firmware_version(
    self, request: pb2.RequestFirmwareVersionRequest, ctx: RequestContext
  ) -> pb2.RequestFirmwareVersionResponse:
    await self._backend.request_firmware_version()
    return pb2.RequestFirmwareVersionResponse()

  async def request_error_code(
    self, request: pb2.RequestErrorCodeRequest, ctx: RequestContext
  ) -> pb2.RequestErrorCodeResponse:
    await self._backend.request_error_code()
    return pb2.RequestErrorCodeResponse()

  async def request_master_status(
    self, request: pb2.RequestMasterStatusRequest, ctx: RequestContext
  ) -> pb2.RequestMasterStatusResponse:
    await self._backend.request_master_status()
    return pb2.RequestMasterStatusResponse()

  async def request_device_serial_number(
    self, request: pb2.RequestDeviceSerialNumberRequest, ctx: RequestContext
  ) -> pb2.RequestDeviceSerialNumberResponse:
    serial_number = await self._backend.request_device_serial_number()
    return pb2.RequestDeviceSerialNumberResponse(serial_number=serial_number)

  # =========================================================================
  # Configuration
  # =========================================================================

  async def set_single_step_mode(
    self, request: pb2.SetSingleStepModeRequest, ctx: RequestContext
  ) -> pb2.SetSingleStepModeResponse:
    await self._backend.set_single_step_mode(
      single_step_mode=request.single_step_mode,
    )
    return pb2.SetSingleStepModeResponse()

  async def trigger_next_step(
    self, request: pb2.TriggerNextStepRequest, ctx: RequestContext
  ) -> pb2.TriggerNextStepResponse:
    await self._backend.trigger_next_step()
    return pb2.TriggerNextStepResponse()

  async def halt(self, request: pb2.HaltRequest, ctx: RequestContext) -> pb2.HaltResponse:
    await self._backend.halt()
    return pb2.HaltResponse()

  async def save_all_cycle_counters(
    self, request: pb2.SaveAllCycleCountersRequest, ctx: RequestContext
  ) -> pb2.SaveAllCycleCountersResponse:
    await self._backend.save_all_cycle_counters()
    return pb2.SaveAllCycleCountersResponse()

  async def set_not_stop(
    self, request: pb2.SetNotStopRequest, ctx: RequestContext
  ) -> pb2.SetNotStopResponse:
    await self._backend.set_not_stop(non_stop=request.non_stop)
    return pb2.SetNotStopResponse()

  async def configure_node_names(
    self, request: pb2.ConfigureNodeNamesRequest, ctx: RequestContext
  ) -> pb2.ConfigureNodeNamesResponse:
    await self._backend.configure_node_names()
    return pb2.ConfigureNodeNamesResponse()

  async def set_deck_data(
    self, request: pb2.SetDeckDataRequest, ctx: RequestContext
  ) -> pb2.SetDeckDataResponse:
    await self._backend.set_deck_data(
      data_index=request.data_index,
      data_stream=request.data_stream,
    )
    return pb2.SetDeckDataResponse()

  # =========================================================================
  # X-arm
  # =========================================================================

  async def position_left_x_arm(
    self, request: pb2.PositionLeftXArmRequest, ctx: RequestContext
  ) -> pb2.PositionLeftXArmResponse:
    await self._backend.position_left_x_arm(x_position=request.x_position)  # type: ignore[attr-defined]
    return pb2.PositionLeftXArmResponse()

  async def position_right_x_arm(
    self, request: pb2.PositionRightXArmRequest, ctx: RequestContext
  ) -> pb2.PositionRightXArmResponse:
    await self._backend.position_right_x_arm(x_position=request.x_position)  # type: ignore[attr-defined]
    return pb2.PositionRightXArmResponse()

  async def move_left_x_arm_to_position_with_all_attached_components_in_z_safety_position(
    self,
    request: pb2.MoveLeftXArmToPositionWithAllAttachedComponentsInZSafetyPositionRequest,
    ctx: RequestContext,
  ) -> pb2.MoveLeftXArmToPositionWithAllAttachedComponentsInZSafetyPositionResponse:
    await (
      self._backend.move_left_x_arm_to_position_with_all_attached_components_in_z_safety_position(
        x_position=request.x_position,
      )
    )
    return pb2.MoveLeftXArmToPositionWithAllAttachedComponentsInZSafetyPositionResponse()

  async def move_right_x_arm_to_position_with_all_attached_components_in_z_safety_position(
    self,
    request: pb2.MoveRightXArmToPositionWithAllAttachedComponentsInZSafetyPositionRequest,
    ctx: RequestContext,
  ) -> pb2.MoveRightXArmToPositionWithAllAttachedComponentsInZSafetyPositionResponse:
    await (
      self._backend.move_right_x_arm_to_position_with_all_attached_components_in_z_safety_position(
        x_position=request.x_position,
      )
    )
    return pb2.MoveRightXArmToPositionWithAllAttachedComponentsInZSafetyPositionResponse()

  async def request_left_x_arm_position(
    self, request: pb2.RequestLeftXArmPositionRequest, ctx: RequestContext
  ) -> pb2.RequestLeftXArmPositionResponse:
    position = await self._backend.request_left_x_arm_position()
    return pb2.RequestLeftXArmPositionResponse(position=position)

  async def request_right_x_arm_position(
    self, request: pb2.RequestRightXArmPositionRequest, ctx: RequestContext
  ) -> pb2.RequestRightXArmPositionResponse:
    position = await self._backend.request_right_x_arm_position()
    return pb2.RequestRightXArmPositionResponse(position=position)

  async def request_right_x_arm_last_collision_type(
    self, request: pb2.RequestRightXArmLastCollisionTypeRequest, ctx: RequestContext
  ) -> pb2.RequestRightXArmLastCollisionTypeResponse:
    collision = await self._backend.request_right_x_arm_last_collision_type()
    return pb2.RequestRightXArmLastCollisionTypeResponse(collision=collision)

  # =========================================================================
  # Pump
  # =========================================================================

  async def request_pump_settings(
    self, request: pb2.RequestPumpSettingsRequest, ctx: RequestContext
  ) -> pb2.RequestPumpSettingsResponse:
    await self._backend.request_pump_settings(pump_station=request.pump_station)
    return pb2.RequestPumpSettingsResponse()

  async def initialize_dual_pump_station_valves(
    self, request: pb2.InitializeDualPumpStationValvesRequest, ctx: RequestContext
  ) -> pb2.InitializeDualPumpStationValvesResponse:
    await self._backend.initialize_dual_pump_station_valves(
      pump_station=request.pump_station,
    )
    return pb2.InitializeDualPumpStationValvesResponse()

  async def drain_dual_chamber_system(
    self, request: pb2.DrainDualChamberSystemRequest, ctx: RequestContext
  ) -> pb2.DrainDualChamberSystemResponse:
    await self._backend.drain_dual_chamber_system(
      pump_station=request.pump_station,
    )
    return pb2.DrainDualChamberSystemResponse()

  # =========================================================================
  # Special
  # =========================================================================

  async def violently_shoot_down_tip(
    self, request: pb2.ViolentlyShootDownTipRequest, ctx: RequestContext
  ) -> pb2.ViolentlyShootDownTipResponse:
    await self._backend.violently_shoot_down_tip(channel_idx=request.channel_idx)  # type: ignore[attr-defined]
    return pb2.ViolentlyShootDownTipResponse()

  async def can_pick_up_tip(
    self, request: pb2.CanPickUpTipRequest, ctx: RequestContext
  ) -> pb2.CanPickUpTipResponse:
    tip = tip_from_proto(request.tip)
    result = self._backend.can_pick_up_tip(
      channel_idx=request.channel_idx,
      tip=tip,
    )
    return pb2.CanPickUpTipResponse(can_pick_up=result)
