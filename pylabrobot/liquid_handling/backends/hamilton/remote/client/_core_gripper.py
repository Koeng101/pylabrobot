"""Client stubs for core gripper operations."""

from __future__ import annotations

from typing import Optional

from pylabrobot.resources import Coordinate, Resource

from .. import star_service_pb2 as pb2
from ..helpers import coordinate_to_proto


class CoreGripperClientMixin:
  """Client stubs for core gripper operations.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # -- tool management --

  async def pick_up_core_gripper_tools(
    self,
    front_channel: int,
    front_offset: Optional[Coordinate] = None,
    back_offset: Optional[Coordinate] = None,
  ) -> None:
    kwargs: dict = dict(front_channel=front_channel)
    if front_offset is not None:
      kwargs["front_offset"] = coordinate_to_proto(front_offset)
    if back_offset is not None:
      kwargs["back_offset"] = coordinate_to_proto(back_offset)
    self._client.pick_up_core_gripper_tools(
      pb2.PickUpCoreGripperToolsRequest(**kwargs)
    )

  async def return_core_gripper_tools(
    self,
    front_offset: Optional[Coordinate] = None,
    back_offset: Optional[Coordinate] = None,
  ) -> None:
    kwargs: dict = {}
    if front_offset is not None:
      kwargs["front_offset"] = coordinate_to_proto(front_offset)
    if back_offset is not None:
      kwargs["back_offset"] = coordinate_to_proto(back_offset)
    self._client.return_core_gripper_tools(
      pb2.ReturnCoreGripperToolsRequest(**kwargs)
    )

  async def core_open_gripper(self) -> None:
    self._client.core_open_gripper(pb2.CoreOpenGripperRequest())

  # -- low-level plate commands --

  async def core_get_plate(
    self,
    x_position: int = 0,
    x_direction: int = 0,
    y_position: int = 0,
    y_gripping_speed: int = 50,
    z_position: int = 0,
    z_speed: int = 500,
    open_gripper_position: int = 0,
    plate_width: int = 0,
    grip_strength: int = 15,
    minimum_traverse_height_at_beginning_of_a_command: int = 2750,
    minimum_z_position_at_the_command_end: int = 2750,
  ) -> None:
    self._client.core_get_plate(
      pb2.CoreGetPlateRequest(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        y_gripping_speed=y_gripping_speed,
        z_position=z_position,
        z_speed=z_speed,
        open_gripper_position=open_gripper_position,
        plate_width=plate_width,
        grip_strength=grip_strength,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        minimum_z_position_at_the_command_end=minimum_z_position_at_the_command_end,
      )
    )

  async def core_put_plate(
    self,
    x_position: int = 0,
    x_direction: int = 0,
    y_position: int = 0,
    z_position: int = 0,
    z_press_on_distance: int = 0,
    z_speed: int = 500,
    open_gripper_position: int = 0,
    minimum_traverse_height_at_beginning_of_a_command: int = 2750,
    z_position_at_the_command_end: int = 2750,
    return_tool: bool = True,
  ) -> None:
    self._client.core_put_plate(
      pb2.CorePutPlateRequest(
        x_position=x_position,
        x_direction=x_direction,
        y_position=y_position,
        z_position=z_position,
        z_press_on_distance=z_press_on_distance,
        z_speed=z_speed,
        open_gripper_position=open_gripper_position,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        z_position_at_the_command_end=z_position_at_the_command_end,
        return_tool=return_tool,
      )
    )

  async def core_move_plate_to_position(
    self,
    x_position: int = 0,
    x_direction: int = 0,
    x_acceleration_index: int = 4,
    y_position: int = 0,
    z_position: int = 0,
    z_speed: int = 500,
    minimum_traverse_height_at_beginning_of_a_command: int = 3600,
  ) -> None:
    self._client.core_move_plate_to_position(
      pb2.CoreMovePlateToPositionRequest(
        x_position=x_position,
        x_direction=x_direction,
        x_acceleration_index=x_acceleration_index,
        y_position=y_position,
        z_position=z_position,
        z_speed=z_speed,
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
      )
    )

  # -- high-level resource commands --

  async def core_pick_up_resource(
    self,
    resource: Resource,
    pickup_distance_from_top: float,
    offset: Coordinate = Coordinate.zero(),
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    minimum_z_position_at_the_command_end: Optional[float] = None,
    grip_strength: int = 15,
    z_speed: float = 50.0,
    y_gripping_speed: float = 5.0,
    front_channel: int = 7,
  ) -> None:
    kwargs: dict = dict(
      resource_name=resource.name,
      pickup_distance_from_top=pickup_distance_from_top,
      offset=coordinate_to_proto(offset),
      grip_strength=grip_strength,
      z_speed=z_speed,
      y_gripping_speed=y_gripping_speed,
      front_channel=front_channel,
    )
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if minimum_z_position_at_the_command_end is not None:
      kwargs["minimum_z_position_at_the_command_end"] = minimum_z_position_at_the_command_end
    self._client.core_pick_up_resource(
      pb2.CorePickUpResourceRequest(**kwargs)
    )

  async def core_move_picked_up_resource(
    self,
    center: Coordinate,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    acceleration_index: int = 4,
    z_speed: float = 50.0,
  ) -> None:
    kwargs: dict = dict(
      center=coordinate_to_proto(center),
      acceleration_index=acceleration_index,
      z_speed=z_speed,
    )
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    self._client.core_move_picked_up_resource(
      pb2.CoreMovePickedUpResourceRequest(**kwargs)
    )

  async def core_release_picked_up_resource(
    self,
    location: Coordinate,
    resource: Resource,
    pickup_distance_from_top: float,
    minimum_traverse_height_at_beginning_of_a_command: Optional[float] = None,
    z_position_at_the_command_end: Optional[float] = None,
    return_tool: bool = True,
  ) -> None:
    kwargs: dict = dict(
      location=coordinate_to_proto(location),
      resource_name=resource.name,
      pickup_distance_from_top=pickup_distance_from_top,
      return_tool=return_tool,
    )
    if minimum_traverse_height_at_beginning_of_a_command is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = (
        minimum_traverse_height_at_beginning_of_a_command
      )
    if z_position_at_the_command_end is not None:
      kwargs["z_position_at_the_command_end"] = z_position_at_the_command_end
    self._client.core_release_picked_up_resource(
      pb2.CoreReleasePickedUpResourceRequest(**kwargs)
    )

  async def core_check_resource_exists_at_location_center(
    self,
    location: Coordinate,
    resource: Resource,
    gripper_y_margin: float = 0.5,
    offset: Coordinate = Coordinate.zero(),
    minimum_traverse_height_at_beginning_of_a_command: float = 275.0,
    z_position_at_the_command_end: float = 275.0,
    enable_recovery: bool = True,
    audio_feedback: bool = True,
  ) -> bool:
    resp = self._client.core_check_resource_exists_at_location_center(
      pb2.CoreCheckResourceExistsAtLocationCenterRequest(
        location=coordinate_to_proto(location),
        resource_name=resource.name,
        gripper_y_margin=gripper_y_margin,
        offset=coordinate_to_proto(offset),
        minimum_traverse_height_at_beginning_of_a_command=minimum_traverse_height_at_beginning_of_a_command,
        z_position_at_the_command_end=z_position_at_the_command_end,
        enable_recovery=enable_recovery,
        audio_feedback=audio_feedback,
      )
    )
    return resp.exists

  # -- deprecated wrappers --

  async def get_core(self, p1: int, p2: int) -> None:
    self._client.get_core(pb2.GetCoreRequest(p1=p1, p2=p2))

  async def put_core(self) -> None:
    self._client.put_core(pb2.PutCoreRequest())

  # -- barcode reading --

  async def core_read_barcode_of_picked_up_resource(
    self,
    rails: int,
    reading_direction: str = "horizontal",
    minimal_z_position: float = 220.0,
    traverse_height_at_beginning_of_a_command: float = 275.0,
    z_speed: float = 128.7,
    allow_manual_input: bool = False,
    labware_description: Optional[str] = None,
  ) -> None:
    kwargs: dict = dict(
      rails=rails,
      reading_direction=reading_direction,
      minimal_z_position=minimal_z_position,
      traverse_height_at_beginning_of_a_command=traverse_height_at_beginning_of_a_command,
      z_speed=z_speed,
      allow_manual_input=allow_manual_input,
    )
    if labware_description is not None:
      kwargs["labware_description"] = labware_description
    self._client.core_read_barcode_of_picked_up_resource(
      pb2.CoreReadBarcodeOfPickedUpResourceRequest(**kwargs)
    )
