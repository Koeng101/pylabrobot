"""Golden files: what a scenario did, written once and compared on every run.

A device's golden tests run scenarios - setup, then what a protocol does - and record what the
device was sent, in order, and what the resources were left as. Each scenario's record is a JSON
file in the device's `golden/` directory. A run that does something else fails, showing where.

Write or rewrite the files after a change that is meant to change them:

  PLR_UPDATE_GOLDEN=1 python -m pytest pylabrobot/<vendor>/<device>/golden

`snapshot_resources` and `snapshot_store` give the same record for the same resources, one from
PLR's `Resource` classes and one from a resource store, so a scenario recorded from either is
checked against the other.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import unittest
from typing import Any, Dict, List, Optional

from pylabrobot.resources.resource import Resource
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.definitions import definition_from_resource
from pylabrobot.resources.store.handles import Resource as Handle
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

UPDATE_VARIABLE = "PLR_UPDATE_GOLDEN"
# Decimals numbers in a record are kept to: a millionth of a mm or a uL.
DECIMALS = 6


def updating() -> bool:
  """Whether this run writes golden files rather than checking them."""
  return os.environ.get(UPDATE_VARIABLE, "") not in ("", "0")


def _rounded(value: Any) -> Any:
  if isinstance(value, float):
    if math.isnan(value) or math.isinf(value):
      return str(value)
    rounded = round(value, DECIMALS)
    return 0.0 if rounded == 0 else rounded
  if isinstance(value, dict):
    return {key: _rounded(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [_rounded(item) for item in value]
  return value


def to_json(record: Any) -> str:
  """A record as its golden file holds it, numbers rounded."""
  return json.dumps(_rounded(record), indent=2) + "\n"


def check_golden(test: unittest.TestCase, path: pathlib.Path, record: Any) -> None:
  """Fail `test` unless `record` is what the golden file at `path` holds; write it instead when
  updating."""
  text = to_json(record)
  if updating():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return
  if not path.exists():
    test.fail(f"{path} is missing: run with {UPDATE_VARIABLE}=1 to write it")
  test.maxDiff = None
  test.assertEqual(json.loads(text), json.loads(path.read_text()), f"differs from {path}")


def _entry(
  name: str,
  parent: str,
  attributes: pb.ResourceAttributes,
  state: Optional[pb.ResourceState],
) -> Dict[str, Any]:
  entry: Dict[str, Any] = {
    "name": name,
    "parent": parent,
    "kind": pb.ResourceKind.Name(attributes.kind),
  }
  if attributes.HasField("location"):
    location = attributes.location
    entry["location"] = [location.x, location.y, location.z]
  rotation = attributes.rotation
  if (rotation.x, rotation.y, rotation.z) != (0, 0, 0):
    entry["rotation"] = [rotation.x, rotation.y, rotation.z]
  if state is not None and state.HasField("volume"):
    entry["volume"] = state.volume.volume
    if state.volume.pending_volume != state.volume.volume:
      entry["pending_volume"] = state.volume.pending_volume
  if state is not None and state.HasField("jaw_width"):
    entry["jaw_width"] = state.jaw_width
  return entry


def snapshot_resources(root: Resource) -> List[Dict[str, Any]]:
  """Every resource from `root` down, in pre-order: its name, parent, kind, location, rotation,
  volume and jaw width. A tip spot's tip, a holder's plate and a shaft's tip are children."""
  entries: List[Dict[str, Any]] = []

  def visit(definition: pb.ResourceDefinition, parent: str) -> None:
    state = definition.initial_state if definition.HasField("initial_state") else None
    entries.append(_entry(definition.attributes.name, parent, definition.attributes, state))
    for child in definition.children:
      visit(child, definition.attributes.name)

  visit(definition_from_resource(root), "")
  return entries


async def snapshot_store(store: ResourceStore, root: Handle) -> List[Dict[str, Any]]:
  """What `snapshot_resources` gives for the same resources, read from a store."""
  response = await store.commands.get_resources(
    spb.GetResourcesRequest(resources=[root.ref], depth=-1)
  )
  names = {node.id: node.attributes.name for node in response.nodes}
  return [
    _entry(
      node.attributes.name,
      "" if node.id == root.id else names.get(node.parent_id, ""),
      node.attributes,
      node.state,
    )
    for node in response.nodes
  ]
