import unittest
from typing import cast
from unittest.mock import AsyncMock

from pylabrobot.opentrons.labware import (
  LabwareRegistry,
  build_tip_rack_definition,
  read_labware,
)
from pylabrobot.opentrons.run import OpentronsRun
from pylabrobot.opentrons.types import LabwareIdentity
from pylabrobot.resources.store import handles, library
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

_RACK = "opentrons_96_filtertiprack_20ul"


async def _rack(store: ResourceStore, name: str = "rack") -> handles.TipRack:
  """A rack alone in the store, at the origin."""
  definition = library.get_model(_RACK).definition
  definition.attributes.location.CopyFrom(pb.Vec3())
  return cast(handles.TipRack, await store.create(definition, name=name))


class LabwareRegistryTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self) -> None:
    self.protocol_run = AsyncMock(spec=OpentronsRun)
    self.registry = LabwareRegistry(self.protocol_run)
    self.store = ResourceStore.in_memory()
    self.rack = await _rack(self.store)
    self.identity = LabwareIdentity("opentrons", "opentrons_96_filtertiprack_20ul", 1)

  async def test_confirmed_move_updates_binding_and_removal_forgets_it(self):
    await self.registry.load(self.rack, "1", self.identity)
    self.registry.record_location(self.rack, "5")
    await self.registry.load(self.rack, "5", self.identity)
    self.protocol_run.load_labware.assert_awaited_once()
    self.registry.remove(self.rack)
    self.assertFalse(self.registry.is_loaded(self.rack))

  async def test_lookup_does_not_load_or_allocate_missing_labware(self) -> None:
    self.assertFalse(self.registry.is_loaded(self.rack))
    with self.assertRaises(KeyError):
      self.registry.get(self.rack)
    self.protocol_run.load_labware.assert_not_awaited()
    self.protocol_run.define_labware.assert_not_awaited()

  async def test_successful_load_is_recorded_once_and_changed_location_is_rejected(self) -> None:
    await self.registry.load(self.rack, "1", self.identity)
    binding = self.registry.get(self.rack)
    await self.registry.load(self.rack, "1", self.identity)
    self.assertIs(self.registry.get(self.rack), binding)
    self.protocol_run.load_labware.assert_awaited_once()
    with self.assertRaisesRegex(ValueError, "loaded in slot 1"):
      await self.registry.load(self.rack, "5", self.identity)
    self.protocol_run.load_labware.assert_awaited_once()
    self.assertEqual(binding.slot, "1")

  async def test_failed_load_does_not_publish_a_binding(self) -> None:
    self.protocol_run.load_labware.side_effect = RuntimeError("load failed")
    with self.assertRaisesRegex(RuntimeError, "load failed"):
      await self.registry.load(self.rack, "1", self.identity)
    self.assertFalse(self.registry.is_loaded(self.rack))

  async def test_distinct_resources_do_not_inherit_each_others_binding(self) -> None:
    await self.registry.load(self.rack, "1", self.identity)
    await self.rack.delete()
    replacement = await _rack(self.store)
    self.assertEqual(replacement.name, self.rack.name)
    self.assertFalse(self.registry.is_loaded(replacement))
    with self.assertRaises(KeyError):
      self.registry.get(replacement)

  async def test_custom_load_uses_the_definition_receipt(self) -> None:
    self.protocol_run.define_labware.return_value = LabwareIdentity("pylabrobot", "uploaded", 2)
    facts = await read_labware(self.store, self.rack)
    definition = build_tip_rack_definition(facts, facts.item("A1").tip, "custom")
    await self.registry.load(self.rack, "5", self.identity, definition)
    binding = self.registry.get(self.rack)
    self.assertEqual(binding.identity, LabwareIdentity("pylabrobot", "uploaded", 2))
    self.protocol_run.load_labware.assert_awaited_once_with(
      binding.identity, "5", binding.labware_id, "rack"
    )


class LabwareConversionTests(unittest.IsolatedAsyncioTestCase):
  async def test_definition_building_does_not_change_the_resource_or_its_tips(self) -> None:
    store = ResourceStore.in_memory()
    rack = await _rack(store)
    request = spb.GetResourcesRequest(resources=[rack.ref], depth=-1)
    before = await store.commands.get_resources(request)
    facts = await read_labware(store, rack)
    tip = facts.item("A1").tip
    first = build_tip_rack_definition(facts, tip, "custom")
    second = build_tip_rack_definition(facts, tip, "custom")
    self.assertEqual(first, second)
    after = await store.commands.get_resources(request)
    self.assertEqual(list(after.nodes), list(before.nodes))
    self.assertEqual(after.revision, before.revision)

  async def test_custom_tip_rack_definition_uses_tip_length_as_well_depth(self) -> None:
    store = ResourceStore.in_memory()
    facts = await read_labware(store, await _rack(store))
    tip = facts.item("A1").tip
    assert tip is not None

    definition = build_tip_rack_definition(facts, tip, "custom")

    self.assertEqual(definition["ordering"][0], [f"{row}1" for row in "ABCDEFGH"])
    self.assertEqual(len(definition["wells"]), 96)
    self.assertEqual(definition["groups"][0]["metadata"], {})
    self.assertEqual(definition["cornerOffsetFromSlot"], {"x": 0, "y": 0, "z": 0})
    self.assertEqual(definition["parameters"]["tipLength"], tip.size.z)
    self.assertEqual(definition["wells"]["A1"]["depth"], tip.size.z)
    self.assertIsInstance(definition["version"], int)
