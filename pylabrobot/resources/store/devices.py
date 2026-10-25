"""How a device reaches its own resources in a store: found there by name, or created once.

A device's resources are created in a store once, when the device is first set up there; from
then on the store knows them, and every device object built for that store finds them by name.
`find_resource` only finds; `find_or_create` creates what is not there yet. What is found by a
device's name must be of the kind and model the device makes, so an unrelated resource that
happens to share the name is refused rather than taken over.
"""

from __future__ import annotations

from typing import Optional

from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb


async def find_resource(
  store: ResourceStore, name: str, kind: pb.ResourceKind, model: str = ""
) -> Optional[handles.Resource]:
  """The resource of this name in `store`, checked to be of this kind and model; None when the
  store has nothing of this name.

  Raises:
    ValueError: The store's resource of this name is of another kind or model: another device's,
      or not a device's at all.
  """
  found = await store.find_resources(spb.ResourceFilter(names=[name]))
  if not found:
    return None
  resource = found[0]
  attributes = await resource.attributes()
  if attributes.kind != kind or attributes.model != model:
    raise ValueError(
      f"the store's '{name}' is a {pb.ResourceKind.Name(attributes.kind)} of model "
      f"'{attributes.model}', not the {pb.ResourceKind.Name(kind)} of model '{model}' asked for"
    )
  return resource


async def find_or_create(
  store: ResourceStore, definition: pb.ResourceDefinition, create: bool = True
) -> handles.Resource:
  """The resource named as `definition` is, from `store`; made from `definition` as a root when
  the store has none and `create`.

  Args:
    store: Where to find it, or make it.
    definition: What it is; its name is what it is found by, and what is found must be of its
      kind and model.
    create: Whether to make it when it is not there.

  Raises:
    LookupError: It is not there, and `create` is False.
    ValueError: The store's resource of its name is of another kind or model.
  """
  attributes = definition.attributes
  found = await find_resource(store, attributes.name, attributes.kind, attributes.model)
  if found is not None:
    return found
  if not create:
    raise LookupError(f"the store has no resource '{attributes.name}'")
  return await store.create(definition, name=attributes.name)


def not_in_store(name: str) -> RuntimeError:
  """What a device raises when its resources are asked for before it has found or created them."""
  return RuntimeError(f"'{name}' is not in a store yet; call create_resources() or setup() first")
