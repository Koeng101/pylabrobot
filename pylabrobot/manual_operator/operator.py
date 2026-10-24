"""Protocol-facing frontend for awaiting manual operator actions."""

from typing import Any, Dict, Optional, Sequence

from pylabrobot.events import (
  device_reference,
  event_operation,
  handle_reference,
  is_event_bus_active,
)
from pylabrobot.resources import Coordinate, Rotation
from pylabrobot.resources.store import StoreError
from pylabrobot.resources.store.errors import plr_error
from pylabrobot.resources.store.handles import Resource
from pylabrobot.resources.store.tree import to_coordinate, to_rotation
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

from .provider import OperatorActionProvider
from .standard import (
  OperatorActionCancelledError,
  OperatorActionFailedError,
  OperatorActionRequest,
  OperatorActionResult,
)

# Kinds that hold one resource at a time, as PLR's `ResourceHolder` does.
_HOLDER_KINDS = frozenset(
  {
    pb.RESOURCE_KIND_RESOURCE_HOLDER,
    pb.RESOURCE_KIND_PLATE_HOLDER,
    pb.RESOURCE_KIND_EMBEDDED_TIP_RACK_HOLDER,
  }
)


class ManualOperator:
  """Await manual protocol work through a pluggable acknowledgement provider.

  Resources are handles to resources in a resource store; a completed move is made there.
  """

  def __init__(self, provider: OperatorActionProvider, name: str = "operator"):
    if not name.strip():
      raise ValueError("name must not be empty")
    self.name = name
    self.provider = provider

  async def perform(
    self,
    *,
    action: str,
    title: str,
    instructions: str,
    confirmation_text: str = "Confirm action completed",
    details: Optional[Dict[str, Any]] = None,
    resources: Optional[Sequence[Resource]] = None,
    source: Optional[Resource] = None,
    destination: Optional[Resource] = None,
  ) -> OperatorActionResult:
    """Await one operator action and return its successful acknowledgement.

    Providers report a structured outcome. Cancellation and failure become distinct exceptions;
    exceptions raised by the provider itself propagate unchanged.
    """

    request = OperatorActionRequest(
      operator_name=self.name,
      action=action,
      title=title,
      instructions=instructions,
      confirmation_text=confirmation_text,
      details={} if details is None else details,
      resources=resources or (),
      source=source,
      destination=destination,
    )
    operation_data: Dict[str, Any] = {}
    if is_event_bus_active():
      operation_data = {
        "device": device_reference(self, name=self.name),
        "resources": [await handle_reference(resource) for resource in request.resources],
        "manual_action": request.action,
        "title": request.title,
        "instructions": request.instructions,
        "confirmation_text": request.confirmation_text,
        "details": request.details.copy(),
      }
      if source is not None:
        operation_data["source"] = await handle_reference(source)
      if destination is not None:
        operation_data["destination"] = await handle_reference(destination)

    result: Optional[OperatorActionResult] = None

    def completed_data() -> Dict[str, Any]:
      assert result is not None
      data = operation_data.copy()
      if result.message is not None:
        data["result_message"] = result.message
      if result.confirmed_by is not None:
        data["confirmed_by"] = result.confirmed_by
      return data

    with event_operation(
      f"manual_operator.{request.action}",
      completed_data_factory=completed_data,
      **operation_data,
    ):
      result = await self.provider.request(request)

      if not isinstance(result, OperatorActionResult):
        raise TypeError("OperatorActionProvider.request() must return OperatorActionResult")
      if result.status == "cancelled":
        raise OperatorActionCancelledError(request, result)
      if result.status == "failed":
        raise OperatorActionFailedError(request, result)
      if result.status != "completed":
        raise ValueError(f"Unsupported operator action status: {result.status!r}")
    assert result is not None
    return result

  async def move_resource(
    self,
    *,
    resource: Resource,
    source: Resource,
    destination: Resource,
    destination_location: Optional[Coordinate] = None,
    destination_rotation: Optional[Rotation] = None,
    title: Optional[str] = None,
    instructions: Optional[str] = None,
    confirmation_text: str = "Confirm resource moved",
    details: Optional[Dict[str, Any]] = None,
  ) -> OperatorActionResult:
    """Await a manual resource move, then reconcile the resource store.

    The resource remains assigned to ``source`` while the operator action is pending. A completed
    acknowledgement assigns it to ``destination`` in the store, in one assignment; with a
    ``destination_rotation`` it is taken out of ``source``, turned, and assigned, and put back as
    it was if ``destination`` refuses it. Cancellation, reported failure, and provider exceptions
    leave the store unchanged.

    Args:
      resource: Resource physically moved by the operator.
      source: Resource currently containing ``resource``.
      destination: Resource that will contain ``resource`` after the move.
      destination_location: Optional resource location relative to ``destination``. Resource
        holders calculate their normal child location when this is omitted.
      destination_rotation: Optional resource-local rotation to apply before destination
        assignment. It is relative to ``destination``, not an absolute/world rotation. After
        assignment, the store composes the destination's absolute rotation with this local
        rotation.
        For a manual replacement of an automated transfer, pass the destination-local pose the
        automated transfer would produce; do not copy the source local rotation unless it is
        physically correct for ``destination``. This is not inferred from ``destination``.
      title: Provider-facing title. Defaults to ``"Move <resource name>"``.
      instructions: Provider-facing instructions. Defaults to a concise source-to-destination
        instruction.
      confirmation_text: Provider-facing completion acknowledgement text.
      details: Additional transport-safe details for the provider.

    Raises:
      ValueError: ``resource`` is not in ``source``, or ``source`` is ``destination``.
      RuntimeError: ``destination`` holds another resource, the store changed while the move
        was pending, or ``destination`` refused the resource.
    """

    await self._validate_resource_move(
      resource=resource,
      source=source,
      destination=destination,
    )

    requested_rotation: Optional[Rotation] = None
    if destination_rotation is not None:
      requested_rotation = Rotation(
        x=destination_rotation.x,
        y=destination_rotation.y,
        z=destination_rotation.z,
      )

    move_details = {} if details is None else details.copy()
    if destination_location is not None:
      move_details["destination_location"] = destination_location.serialize()
    if requested_rotation is not None:
      move_details["destination_rotation"] = requested_rotation.serialize()

    result = await self.perform(
      action="resource.move",
      title=title or f"Move {resource.name}",
      instructions=instructions
      or f"Move {resource.name} from {source.name} to {destination.name}.",
      confirmation_text=confirmation_text,
      details=move_details,
      resources=[resource],
      source=source,
      destination=destination,
    )

    try:
      node = await self._validate_resource_move(
        resource=resource,
        source=source,
        destination=destination,
      )
    except (RuntimeError, ValueError) as error:
      raise RuntimeError(
        "The PLR resource model changed while the manual move was pending; "
        "the completed physical move was not applied to the model."
      ) from error

    if requested_rotation is None:
      await self._assign(destination, resource, destination_location)
      return result

    previous_location = to_coordinate(node.attributes.location)
    previous_rotation = to_rotation(node.attributes.rotation)
    await resource.unassign()
    try:
      await resource.rotate_to(
        x=requested_rotation.x, y=requested_rotation.y, z=requested_rotation.z
      )
      await self._assign(destination, resource, destination_location)
    except Exception:
      if await resource.get_parent() is not None:
        await resource.unassign()
      await resource.rotate_to(x=previous_rotation.x, y=previous_rotation.y, z=previous_rotation.z)
      await source.assign_child_resource(resource, location=previous_location)
      raise
    return result

  @staticmethod
  async def _assign(
    destination: Resource, resource: Resource, location: Optional[Coordinate]
  ) -> None:
    """Assign ``resource`` to ``destination``, raising the store's refusal as a RuntimeError."""
    try:
      await destination.assign_child_resource(resource, location=location)
    except StoreError as error:
      raise plr_error(error, otherwise=RuntimeError) from error

  @staticmethod
  async def _validate_resource_move(
    *,
    resource: Resource,
    source: Resource,
    destination: Resource,
  ) -> pb.ResourceNode:
    """Refuse a move the store would not make, in one read; the resource as it is now."""
    response = await resource.store.commands.get_resources(
      spb.GetResourcesRequest(resources=[resource.ref, destination.ref], depth=0, ancestors=True)
    )
    by_id = {node.id: node for node in response.nodes}
    node = by_id[resource.id]
    if node.parent_id != source.id:
      current_parent = by_id[node.parent_id].attributes.name if node.parent_id else None
      raise ValueError(
        f"Resource {resource.name!r} is assigned to {current_parent!r}, not source {source.name!r}."
      )
    if source == destination:
      raise ValueError("source and destination must be different resources")
    target = by_id[destination.id]
    if target.attributes.kind in _HOLDER_KINDS and any(
      child_id != resource.id for child_id in target.child_ids
    ):
      raise RuntimeError(
        f"Cannot drop resource {resource.name} onto resource holder {destination.name} while it "
        "already has a resource. Please remove the resource before dropping a new one."
      )
    return node
