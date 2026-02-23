"""RPC handlers for core gripper operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import star_service_pb2 as pb2
from ..helpers import coordinate_from_proto, extract_optional_field

if TYPE_CHECKING:
  from connectrpc.request import RequestContext

  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend


class CoreGripperServerMixin:
  _backend: STARBackend
  """RPC handlers for core gripper operations.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

  async def pick_up_core_gripper_tools(
    self,
    request: pb2.PickUpCoreGripperToolsRequest,
    ctx: RequestContext,
  ) -> pb2.PickUpCoreGripperToolsResponse:
    front_offset = (
      coordinate_from_proto(request.front_offset) if request.HasField("front_offset") else None
    )
    back_offset = (
      coordinate_from_proto(request.back_offset) if request.HasField("back_offset") else None
    )
    await self._backend.pick_up_core_gripper_tools(
      front_channel=request.front_channel,
      front_offset=front_offset,
      back_offset=back_offset,
    )
    return pb2.PickUpCoreGripperToolsResponse()

  async def return_core_gripper_tools(
    self,
    request: pb2.ReturnCoreGripperToolsRequest,
    ctx: RequestContext,
  ) -> pb2.ReturnCoreGripperToolsResponse:
    front_offset = (
      coordinate_from_proto(request.front_offset) if request.HasField("front_offset") else None
    )
    back_offset = (
      coordinate_from_proto(request.back_offset) if request.HasField("back_offset") else None
    )
    await self._backend.return_core_gripper_tools(
      front_offset=front_offset,
      back_offset=back_offset,
    )
    return pb2.ReturnCoreGripperToolsResponse()

  async def core_open_gripper(
    self,
    request: pb2.CoreOpenGripperRequest,
    ctx: RequestContext,
  ) -> pb2.CoreOpenGripperResponse:
    await self._backend.core_open_gripper()
    return pb2.CoreOpenGripperResponse()

  async def core_get_plate(
    self,
    request: pb2.CoreGetPlateRequest,
    ctx: RequestContext,
  ) -> pb2.CoreGetPlateResponse:
    await self._backend.core_get_plate(
      x_position=request.x_position,
      x_direction=request.x_direction,
      y_position=request.y_position,
      y_gripping_speed=request.y_gripping_speed,
      z_position=request.z_position,
      z_speed=request.z_speed,
      open_gripper_position=request.open_gripper_position,
      plate_width=request.plate_width,
      grip_strength=request.grip_strength,
      minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
      minimum_z_position_at_the_command_end=request.minimum_z_position_at_the_command_end,
    )
    return pb2.CoreGetPlateResponse()

  async def core_put_plate(
    self,
    request: pb2.CorePutPlateRequest,
    ctx: RequestContext,
  ) -> pb2.CorePutPlateResponse:
    await self._backend.core_put_plate(
      x_position=request.x_position,
      x_direction=request.x_direction,
      y_position=request.y_position,
      z_position=request.z_position,
      z_press_on_distance=request.z_press_on_distance,
      z_speed=request.z_speed,
      open_gripper_position=request.open_gripper_position,
      minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
      z_position_at_the_command_end=request.z_position_at_the_command_end,
      return_tool=request.return_tool,
    )
    return pb2.CorePutPlateResponse()

  async def core_move_plate_to_position(
    self,
    request: pb2.CoreMovePlateToPositionRequest,
    ctx: RequestContext,
  ) -> pb2.CoreMovePlateToPositionResponse:
    await self._backend.core_move_plate_to_position(
      x_position=request.x_position,
      x_direction=request.x_direction,
      x_acceleration_index=request.x_acceleration_index,
      y_position=request.y_position,
      z_position=request.z_position,
      z_speed=request.z_speed,
      minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
    )
    return pb2.CoreMovePlateToPositionResponse()

  async def core_pick_up_resource(
    self,
    request: pb2.CorePickUpResourceRequest,
    ctx: RequestContext,
  ) -> pb2.CorePickUpResourceResponse:
    resource = self._backend.deck.get_resource(request.resource_name)
    offset = coordinate_from_proto(request.offset)
    kwargs = dict(
      resource=resource,
      pickup_distance_from_top=request.pickup_distance_from_top,
      offset=offset,
      grip_strength=request.grip_strength,
      z_speed=request.z_speed,
      y_gripping_speed=request.y_gripping_speed,
      front_channel=request.front_channel,
    )
    minimum_traverse_height = extract_optional_field(
      request, "minimum_traverse_height_at_beginning_of_a_command"
    )
    if minimum_traverse_height is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = minimum_traverse_height
    minimum_z_end = extract_optional_field(request, "minimum_z_position_at_the_command_end")
    if minimum_z_end is not None:
      kwargs["minimum_z_position_at_the_command_end"] = minimum_z_end
    await self._backend.core_pick_up_resource(**kwargs)  # type: ignore[arg-type]
    return pb2.CorePickUpResourceResponse()

  async def core_move_picked_up_resource(
    self,
    request: pb2.CoreMovePickedUpResourceRequest,
    ctx: RequestContext,
  ) -> pb2.CoreMovePickedUpResourceResponse:
    center = coordinate_from_proto(request.center)
    kwargs = dict(
      center=center,
      acceleration_index=request.acceleration_index,
      z_speed=request.z_speed,
    )
    minimum_traverse_height = extract_optional_field(
      request, "minimum_traverse_height_at_beginning_of_a_command"
    )
    if minimum_traverse_height is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = minimum_traverse_height
    await self._backend.core_move_picked_up_resource(**kwargs)  # type: ignore[arg-type]
    return pb2.CoreMovePickedUpResourceResponse()

  async def core_release_picked_up_resource(
    self,
    request: pb2.CoreReleasePickedUpResourceRequest,
    ctx: RequestContext,
  ) -> pb2.CoreReleasePickedUpResourceResponse:
    location = coordinate_from_proto(request.location)
    resource = self._backend.deck.get_resource(request.resource_name)
    kwargs = dict(
      location=location,
      resource=resource,
      pickup_distance_from_top=request.pickup_distance_from_top,
      return_tool=request.return_tool,
    )
    minimum_traverse_height = extract_optional_field(
      request, "minimum_traverse_height_at_beginning_of_a_command"
    )
    if minimum_traverse_height is not None:
      kwargs["minimum_traverse_height_at_beginning_of_a_command"] = minimum_traverse_height
    z_end = extract_optional_field(request, "z_position_at_the_command_end")
    if z_end is not None:
      kwargs["z_position_at_the_command_end"] = z_end
    await self._backend.core_release_picked_up_resource(**kwargs)  # type: ignore[arg-type]
    return pb2.CoreReleasePickedUpResourceResponse()

  async def core_check_resource_exists_at_location_center(
    self,
    request: pb2.CoreCheckResourceExistsAtLocationCenterRequest,
    ctx: RequestContext,
  ) -> pb2.CoreCheckResourceExistsAtLocationCenterResponse:
    location = coordinate_from_proto(request.location)
    offset = coordinate_from_proto(request.offset)
    resource = self._backend.deck.get_resource(request.resource_name)
    exists = await self._backend.core_check_resource_exists_at_location_center(
      location=location,
      resource=resource,
      gripper_y_margin=request.gripper_y_margin,
      offset=offset,
      minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
      z_position_at_the_command_end=request.z_position_at_the_command_end,
      enable_recovery=request.enable_recovery,
      audio_feedback=request.audio_feedback,
    )
    return pb2.CoreCheckResourceExistsAtLocationCenterResponse(exists=exists)

  async def get_core(
    self,
    request: pb2.GetCoreRequest,
    ctx: RequestContext,
  ) -> pb2.GetCoreResponse:
    await self._backend.get_core(p1=request.p1, p2=request.p2)
    return pb2.GetCoreResponse()

  async def put_core(
    self,
    request: pb2.PutCoreRequest,
    ctx: RequestContext,
  ) -> pb2.PutCoreResponse:
    await self._backend.put_core()
    return pb2.PutCoreResponse()

  async def core_read_barcode_of_picked_up_resource(
    self,
    request: pb2.CoreReadBarcodeOfPickedUpResourceRequest,
    ctx: RequestContext,
  ) -> pb2.CoreReadBarcodeOfPickedUpResourceResponse:
    kwargs = dict(
      rails=request.rails,
      reading_direction=request.reading_direction,
      minimal_z_position=request.minimal_z_position,
      traverse_height_at_beginning_of_a_command=request.traverse_height_at_beginning_of_a_command,
      z_speed=request.z_speed,
      allow_manual_input=request.allow_manual_input,
    )
    labware_description = extract_optional_field(request, "labware_description")
    if labware_description is not None:
      kwargs["labware_description"] = labware_description
    await self._backend.core_read_barcode_of_picked_up_resource(**kwargs)  # type: ignore[arg-type]
    return pb2.CoreReadBarcodeOfPickedUpResourceResponse()
