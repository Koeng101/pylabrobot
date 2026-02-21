"""Client stubs for firmware queries, config, cover, HHS, pump, X-arm, and special ops."""

from __future__ import annotations

from typing import Dict

from pylabrobot.resources.tip import Tip

from .. import star_service_pb2 as pb2
from ..helpers import tip_to_proto


class MiscClientMixin:
  """Client stubs for firmware queries, config, cover, HHS, pump, X-arm, and special ops.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # =========================================================================
  # Cover
  # =========================================================================

  async def lock_cover(self) -> None:
    self._client.lock_cover(pb2.LockCoverRequest())

  async def unlock_cover(self) -> None:
    self._client.unlock_cover(pb2.UnlockCoverRequest())

  async def disable_cover_control(self) -> None:
    self._client.disable_cover_control(pb2.DisableCoverControlRequest())

  async def enable_cover_control(self) -> None:
    self._client.enable_cover_control(pb2.EnableCoverControlRequest())

  async def set_cover_output(self, output: int = 0) -> None:
    self._client.set_cover_output(pb2.SetCoverOutputRequest(output=output))

  async def reset_output(self, output: int = 0) -> None:
    self._client.reset_output(pb2.ResetOutputRequest(output=output))

  async def request_cover_open(self) -> bool:
    resp = self._client.request_cover_open(pb2.RequestCoverOpenRequest())
    return resp.open

  # =========================================================================
  # HHS (Heater/Shaker)
  # =========================================================================

  async def send_hhs_command(self, index: int, command: str) -> str:
    resp = self._client.send_hhs_command(
      pb2.SendHhsCommandRequest(index=index, command=command)
    )
    return resp.response

  async def check_type_is_hhc(self, device_number: int) -> None:
    self._client.check_type_is_hhc(
      pb2.CheckTypeIsHhcRequest(device_number=device_number)
    )

  async def initialize_hhc(self, device_number: int) -> str:
    resp = self._client.initialize_hhc(
      pb2.InitializeHhcRequest(device_number=device_number)
    )
    return resp.response

  async def start_temperature_control_at_hhc(
    self, device_number: int, temperature: float,
  ) -> None:
    self._client.start_temperature_control_at_hhc(
      pb2.StartTemperatureControlAtHhcRequest(
        device_number=device_number,
        temperature=temperature,
      )
    )

  async def get_temperature_at_hhc(self, device_number: int) -> Dict[str, float]:
    resp = self._client.get_temperature_at_hhc(
      pb2.GetTemperatureAtHhcRequest(device_number=device_number)
    )
    return {
      "current": resp.current_temperature,
      "target": resp.target_temperature,
    }

  async def query_whether_temperature_reached_at_hhc(self, device_number: int) -> None:
    self._client.query_whether_temperature_reached_at_hhc(
      pb2.QueryWhetherTemperatureReachedAtHhcRequest(device_number=device_number)
    )

  async def stop_temperature_control_at_hhc(self, device_number: int) -> None:
    self._client.stop_temperature_control_at_hhc(
      pb2.StopTemperatureControlAtHhcRequest(device_number=device_number)
    )

  # =========================================================================
  # Firmware queries
  # =========================================================================

  async def request_firmware_version(self) -> None:
    self._client.request_firmware_version(pb2.RequestFirmwareVersionRequest())

  async def request_error_code(self) -> None:
    self._client.request_error_code(pb2.RequestErrorCodeRequest())

  async def request_master_status(self) -> None:
    self._client.request_master_status(pb2.RequestMasterStatusRequest())

  async def request_device_serial_number(self) -> str:
    resp = self._client.request_device_serial_number(
      pb2.RequestDeviceSerialNumberRequest()
    )
    return resp.serial_number

  # =========================================================================
  # Configuration
  # =========================================================================

  async def set_single_step_mode(self, single_step_mode: bool = False) -> None:
    self._client.set_single_step_mode(
      pb2.SetSingleStepModeRequest(single_step_mode=single_step_mode)
    )

  async def trigger_next_step(self) -> None:
    self._client.trigger_next_step(pb2.TriggerNextStepRequest())

  async def halt(self) -> None:
    self._client.halt(pb2.HaltRequest())

  async def save_all_cycle_counters(self) -> None:
    self._client.save_all_cycle_counters(pb2.SaveAllCycleCountersRequest())

  async def set_not_stop(self, non_stop: bool) -> None:
    self._client.set_not_stop(pb2.SetNotStopRequest(non_stop=non_stop))

  async def configure_node_names(self) -> None:
    self._client.configure_node_names(pb2.ConfigureNodeNamesRequest())

  async def set_deck_data(self, data_index: int = 0, data_stream: str = "0") -> None:
    self._client.set_deck_data(
      pb2.SetDeckDataRequest(data_index=data_index, data_stream=data_stream)
    )

  # =========================================================================
  # X-arm
  # =========================================================================

  async def position_left_x_arm(self, x_position: int = 0) -> None:
    self._client.position_left_x_arm(
      pb2.PositionLeftXArmRequest(x_position=x_position)
    )

  async def position_right_x_arm(self, x_position: int = 0) -> None:
    self._client.position_right_x_arm(
      pb2.PositionRightXArmRequest(x_position=x_position)
    )

  async def move_left_x_arm_to_position_with_all_attached_components_in_z_safety_position(
    self, x_position: int = 0,
  ) -> None:
    self._client.move_left_x_arm_to_position_with_all_attached_components_in_z_safety_position(
      pb2.MoveLeftXArmToPositionWithAllAttachedComponentsInZSafetyPositionRequest(
        x_position=x_position,
      )
    )

  async def move_right_x_arm_to_position_with_all_attached_components_in_z_safety_position(
    self, x_position: int = 0,
  ) -> None:
    self._client.move_right_x_arm_to_position_with_all_attached_components_in_z_safety_position(
      pb2.MoveRightXArmToPositionWithAllAttachedComponentsInZSafetyPositionRequest(
        x_position=x_position,
      )
    )

  async def request_left_x_arm_position(self) -> float:
    resp = self._client.request_left_x_arm_position(
      pb2.RequestLeftXArmPositionRequest()
    )
    return resp.position

  async def request_right_x_arm_position(self) -> float:
    resp = self._client.request_right_x_arm_position(
      pb2.RequestRightXArmPositionRequest()
    )
    return resp.position

  async def request_right_x_arm_last_collision_type(self) -> bool:
    resp = self._client.request_right_x_arm_last_collision_type(
      pb2.RequestRightXArmLastCollisionTypeRequest()
    )
    return resp.collision

  # =========================================================================
  # Pump
  # =========================================================================

  async def request_pump_settings(self, pump_station: int = 1) -> None:
    self._client.request_pump_settings(
      pb2.RequestPumpSettingsRequest(pump_station=pump_station)
    )

  async def initialize_dual_pump_station_valves(self, pump_station: int = 1) -> None:
    self._client.initialize_dual_pump_station_valves(
      pb2.InitializeDualPumpStationValvesRequest(pump_station=pump_station)
    )

  async def drain_dual_chamber_system(self, pump_station: int = 1) -> None:
    self._client.drain_dual_chamber_system(
      pb2.DrainDualChamberSystemRequest(pump_station=pump_station)
    )

  # =========================================================================
  # Special
  # =========================================================================

  async def violently_shoot_down_tip(self, channel_idx: int) -> None:
    self._client.violently_shoot_down_tip(
      pb2.ViolentlyShootDownTipRequest(channel_idx=channel_idx)
    )

  def can_pick_up_tip(self, channel_idx: int, tip: Tip) -> bool:
    resp = self._client.can_pick_up_tip(
      pb2.CanPickUpTipRequest(
        channel_idx=channel_idx,
        tip=tip_to_proto(tip),
      )
    )
    return resp.can_pick_up
