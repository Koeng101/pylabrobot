"""The `resource.assigned` and `resource.unassigned` events of a sample store's resources.

A sample store reports each change it makes to its resources as PLR's resource tree does: a
resource assigned to a parent, or taken out of one, with references as `handle_reference` gives
them. Parts built together - a stacker and its slots, a plate and its wells - are reported as PLR
builds them: each part assigned to its parent, innermost first, while that parent stands alone.
"""

from typing import Optional, Sequence

from pylabrobot.events import (
  ResourceReference,
  coordinate_reference,
  emit_event,
  handle_reference,
  is_event_bus_active,
)
from pylabrobot.events.bus import ResourceAncestorReference
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.v1 import types_pb2 as pb


def reference(
  attributes: pb.ResourceAttributes, ancestors: Sequence[pb.ResourceAttributes] = ()
) -> ResourceReference:
  """What `handle_reference` gives for a resource with these attributes and ancestors, innermost
  first."""
  result: ResourceReference = {"name": attributes.name, "type": attributes.type_name or "Resource"}
  if attributes.model:
    result["model"] = attributes.model
  rotation = attributes.rotation
  result["rotation"] = {"x": rotation.x, "y": rotation.y, "z": rotation.z}
  ancestor_references = []
  for ancestor in ancestors:
    entry: ResourceAncestorReference = {
      "name": ancestor.name,
      "type": ancestor.type_name or "Resource",
    }
    if ancestor.model:
      entry["model"] = ancestor.model
    ancestor_references.append(entry)
  if ancestor_references:
    result["ancestors"] = ancestor_references
  return result


def _location(attributes: pb.ResourceAttributes) -> Optional[Coordinate]:
  if not attributes.HasField("location"):
    return None
  location = attributes.location
  return Coordinate(location.x, location.y, location.z)


def emit_attached(child: pb.ResourceDefinition, parent: pb.ResourceAttributes) -> None:
  """Report `child` assigned to `parent`, a root."""
  emit_event(
    "resource.assigned",
    resource=reference(child.attributes, [parent]),
    parent=reference(parent),
    location=coordinate_reference(_location(child.attributes)),
  )


def emit_built(definition: pb.ResourceDefinition) -> None:
  """Report everything under `definition` assigned to its parent, as PLR builds it: innermost
  first, each parent standing alone when its parts are assigned to it."""
  if not is_event_bus_active():
    return
  for child in definition.children:
    emit_built(child)
    emit_attached(child, definition.attributes)


async def emit_assigned(resource: handles.Resource) -> None:
  """Report `resource` assigned where it is now."""
  if not is_event_bus_active():
    return
  node = await resource.node()
  parent = await resource.get_parent()
  emit_event(
    "resource.assigned",
    resource=await handle_reference(resource),
    parent=await handle_reference(parent),
    location=coordinate_reference(_location(node.attributes)),
  )


async def emit_unassigned(
  resource: handles.Resource,
  previous_parent: handles.Resource,
  previous_location: Optional[Coordinate],
) -> None:
  """Report `resource` taken out of `previous_parent`, where it was at `previous_location`."""
  if not is_event_bus_active():
    return
  standing_alone = await handle_reference(resource)
  assert standing_alone is not None
  standing_alone.pop("ancestors", None)
  emit_event(
    "resource.unassigned",
    resource=standing_alone,
    previous_parent=await handle_reference(previous_parent),
    previous_location=coordinate_reference(previous_location),
  )
