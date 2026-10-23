"""Tests for container (trough/reservoir) ops on the Flex heads, and for the
robot-level commands that belong to the device rather than to a head.

A bare container holds one volume in the resource store. Pipetting centers the
nozzle array using PLR coordinates and sends an in-place plunger command. Tests
cover coordinates, offsets, per-tip volume accounting and rollback on wire failure.

The robot-level tests pin the wire shape of the device's own commands: the
snake_case params the robot/* family takes (unlike the rest of the API), the
axis-name and version-gate refusals that must send nothing, and the exact
params of the status, comment, wait and reload commands.
"""

import unittest
from typing import Any, List, Optional, Tuple, Union, cast
from unittest.mock import AsyncMock, _Call, patch

from pylabrobot.opentrons.flex.errors import OpentronsError
from pylabrobot.opentrons.flex.flex import Flex
from pylabrobot.opentrons.flex.flex_head import FlexHead1, FlexHead8, FlexHead96
from pylabrobot.opentrons.flex.flex_wire import OFFLINE_API_VERSION
from pylabrobot.opentrons.flex.tests.liquid_test_utils import pipetting_location
from pylabrobot.opentrons.flex.tests.mock_utils import (
  container,
  make_api,
  make_deck,
  make_flex,
  place,
)
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

COMMITTED = pb.VIEW_COMMITTED


def _make_trough(
  name: str = "trough",
  size_x: float = 127.76,
  size_y: float = 85.48,
  max_volume: float = 195000.0,
  turned: bool = False,
  location: Optional[Coordinate] = None,
) -> pb.ResourceDefinition:
  """A single-cavity reservoir, a plain container, mapped to a real Opentrons
  single-cavity load name; ``turned`` turns it a quarter turn about z.

  The default size is that reservoir's OUTER footprint, the convention a PLR
  container carries (its cavity is narrower, and PLR does not model it).
  """
  definition = container(name, size_x, size_y, 31.4, 1.0, max_volume)
  if turned:
    definition.attributes.rotation.z = 90
  if location is not None:
    definition.attributes.location.CopyFrom(build.vec3(location))
  return definition


async def _put(flex: Flex, source: Union[str, pb.ResourceDefinition], slot: str, name: str) -> Any:
  """Make labware in a slot of the Flex's deck."""
  return await place(flex.deck, source, name, slot)


async def _take_tips(rack: handles.TipRack, identifiers: List[str]) -> None:
  """Take tips from spots by hand."""
  await rack.store.commands.update_resources(
    spb.UpdateResourcesRequest(
      updates=[
        spb.ResourceUpdate(
          tip_presence=pb.SetTipPresence(
            spots=[rack.get_tip_spot(i).ref for i in identifiers], present=False
          )
        )
      ]
    )
  )


async def _flex_head1(
  test_case: unittest.IsolatedAsyncioTestCase,
) -> Tuple[Flex, AsyncMock, FlexHead1]:
  """An ``Flex`` with a single-channel head on the right mount, plus
  the api (for command inspection) and the head itself.
  """
  api = make_api(pipettes=[("p1000_single_flex", 1, 1.0, 1000.0, "right")])
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  await flex.setup()
  head = flex.right
  assert isinstance(head, FlexHead1)
  return flex, api, head


async def _flex_head8(
  test_case: unittest.IsolatedAsyncioTestCase,
) -> Tuple[Flex, AsyncMock, FlexHead8]:
  """An ``Flex`` with an 8-channel head on the left mount, plus the
  api (for command inspection) and the head itself.
  """
  api = make_api(pipettes=[("p50_multi_flex", 8, 1.0, 50.0, "left")])
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  await flex.setup()
  head = flex.left
  assert isinstance(head, FlexHead8)
  return flex, api, head


async def _flex_head96(
  test_case: unittest.IsolatedAsyncioTestCase,
) -> Tuple[Flex, AsyncMock, FlexHead96]:
  """An ``Flex`` with a 96-channel head, plus the api (for
  command inspection) and the head itself.
  """
  api = make_api(pipettes=[("p1000_96", 96, 1.0, 1000.0, "left")])
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  await flex.setup()
  head = flex.head96
  assert isinstance(head, FlexHead96)
  return flex, api, head


class TestFlexHead1ContainerOps(unittest.IsolatedAsyncioTestCase):
  """FlexHead1 aspirate/dispense accept a bare Container: the container is its
  own robot-side labware addressed at its sole well "A1", and volume is
  tracked against the container's single tracker.
  """

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head1(self)

  async def test_aspirate_positions_container_without_loading_labware(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(1000.0)

    await self.head.pick_up_tips(rack.get_tip_spot("A1"))
    await self.head.aspirate(trough, volume=50)

    load_cmds = [
      c
      for c in self.api.submit_command.await_args_list
      if c.args[1] == "loadLabware" and c.args[2]["loadName"] == "nest_1_reservoir_195ml"
    ]
    self.assertEqual(len(load_cmds), 0, "PLR positioning must not load the container")

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    self.assertNotIn("wellName", aspirate_cmds[0].args[2])
    self.assertNotIn("labwareId", aspirate_cmds[0].args[2])
    # A single nozzle goes to the cavity center: no x/y centering offset,
    # just the default bottom clearance.
    self.assertEqual(
      await pipetting_location(self.api, trough, self.head.channels),
      {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
    )

    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 950.0)

  async def test_dispense_adds_volume_to_container_tracker(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    await self.head.pick_up_tips(rack.get_tip_spot("A1"))
    for tip in await self.head.get_mounted_tips():
      if tip is not None:
        await tip.set_volume(30)
    await self.head.dispense(trough, volume=30)

    dispense_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "dispenseInPlace"
    ]
    self.assertEqual(len(dispense_cmds), 1)
    self.assertNotIn("wellName", dispense_cmds[0].args[2])
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 30.0)

  async def test_aspirate_container_without_tip_rejects_before_any_wire_command(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(1000.0)

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate(trough, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 1000.0)

  async def test_dispense_container_without_tip_rejects_before_any_wire_command(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.dispense(trough, volume=30)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 0.0)

  async def test_wire_failure_rolls_back_container_tracker(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(1000.0)

    await self.head.pick_up_tips(rack.get_tip_spot("A1"))
    with (
      patch.object(
        self.api,
        "submit_command",
        AsyncMock(
          side_effect=[self.api.submit_command.return_value] * 3
          + [RuntimeError("pipetting failed")]
        ),
      ) as submit,
      self.assertRaisesRegex(RuntimeError, "pipetting failed"),
    ):
      await self.head.aspirate(trough, volume=50)

    assert submit.await_args is not None
    self.assertEqual(submit.await_args.args[1], "aspirateInPlace")
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 1000.0)
    self.assertAlmostEqual((await trough.get_volume()), 1000.0)


class TestFlexHead8ContainerOps(unittest.IsolatedAsyncioTestCase):
  """PLR centers the nozzle row; each mounted tip changes the shared tracker."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8(self)

  async def test_reservoir_well_centers_array_for_aspirate_and_dispense(self):
    """A single-well reservoir centers all 8 tips, despite being a Well."""
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    reservoir = cast(
      handles.Plate,
      await _put(self.flex, "cor_axy_1_troughplate_rowVb", "D1", "reservoir"),
    )
    cavity = reservoir.get_well("A1")
    await cavity.set_volume(100000)
    await self.head.pick_up_tips(rack, column=0)
    for operation in (self.head.aspirate_container, self.head.dispense_container):
      with self.subTest(operation=operation.__name__):
        self.api.submit_command.reset_mock()
        await operation(cavity, volume=10)
        moves = [
          c for c in self.api.submit_command.await_args_list if c.args[1] == "moveToCoordinates"
        ]
        self.assertEqual(moves[0].args[2]["coordinates"], {"x": 63.88, "y": 74.24, "z": 109.0})
        self.assertEqual(
          await pipetting_location(self.api, cavity, self.head.channels),
          {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
        )
    self.assertAlmostEqual((await cavity.get_volume(COMMITTED)), 100000)

  async def test_aspirate_container_centers_nozzle_row(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.aspirate_container(trough, volume=50)

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    params = aspirate_cmds[0].args[2]
    self.assertNotIn("wellName", params)
    self.assertEqual(params["volume"], 50)
    # The primary nozzle is positioned so the row centers on the cavity.
    self.assertEqual(
      await pipetting_location(self.api, trough, self.head.channels),
      {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
    )

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    self.assertIn(
      "prepareToAspirate",
      cmd_types,
      "the driver primes above the target before descent",
    )

    # All 8 channels hold a tip, so the single tracker loses 8 * 50.
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 9600.0)
    self.assertAlmostEqual((await trough.get_volume()), 9600.0)

  async def test_aspirate_container_tracker_scales_with_mounted_tips(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(10000.0)

    # Leave only 3 tips in column 0 (rows A, D, H) before the pickup.
    await _take_tips(rack, ["B1", "C1", "E1", "F1", "G1"])

    await self.head.pick_up_tips(rack, column=0)
    self.assertEqual(sum(1 for t in await self.head.get_mounted_tips() if t is not None), 3)

    await self.head.aspirate_container(trough, volume=50)

    # Exactly the 3 tip-holding channels draw 50 each: -150, not -400.
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 9850.0)

  async def test_dispense_container_adds_volume_per_mounted_tip(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    await self.head.pick_up_tips(rack, column=0)
    for tip in await self.head.get_mounted_tips():
      if tip is not None:
        await tip.set_volume(40)
    await self.head.dispense_container(trough, volume=40)

    dispense_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "dispenseInPlace"
    ]
    self.assertEqual(len(dispense_cmds), 1)
    params = dispense_cmds[0].args[2]
    self.assertNotIn("wellName", params)
    self.assertEqual(
      await pipetting_location(self.api, trough, self.head.channels),
      {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
    )
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 320.0)

  async def test_offset_and_liquid_height_merge_into_well_location(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.aspirate_container(
      trough, volume=10, offset=Coordinate(x=2, y=-1, z=0.5), liquid_height=3
    )

    [c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"]
    # Caller offsets shift the centered row; liquid_height replaces clearance.
    self.assertEqual(
      await pipetting_location(self.api, trough, self.head.channels),
      {"origin": "bottom", "offset": {"x": 2, "y": -1, "z": 3.5}},
    )

  async def test_aspirate_container_without_tip_rejects_before_any_wire_command(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(10000.0)

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate_container(trough, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 10000.0)
    self.assertAlmostEqual((await trough.get_volume()), 10000.0)

  async def test_aspirate_container_rejects_cavity_narrower_than_nozzle_row(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    narrow = cast(
      handles.Container,
      await _put(
        self.flex, _make_trough(name="narrow", size_y=40.0, max_volume=50000.0), "C2", "narrow"
      ),
    )
    await narrow.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)

    # 40 mm front-to-back cannot contain the 63 mm nozzle row.
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate_container(narrow, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await narrow.get_volume(COMMITTED)), 10000.0)
    self.assertAlmostEqual((await narrow.get_volume()), 10000.0)

  async def test_wire_failure_rolls_back_container_tracker(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    with (
      patch.object(
        self.api,
        "submit_command",
        AsyncMock(
          side_effect=[self.api.submit_command.return_value] * 3
          + [RuntimeError("pipetting failed")]
        ),
      ) as submit,
      self.assertRaisesRegex(RuntimeError, "pipetting failed"),
    ):
      await self.head.aspirate_container(trough, volume=50)

    assert submit.await_args is not None
    self.assertEqual(submit.await_args.args[1], "aspirateInPlace")
    # The staged 8 * 50 uL is rolled back in full: committed AND pending
    # volume are untouched.
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 10000.0)
    self.assertAlmostEqual((await trough.get_volume()), 10000.0)

  async def test_dispense_container_without_tip_rejects_before_any_wire_command(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.dispense_container(trough, volume=40)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 0.0)

  async def test_dispense_container_wire_failure_rolls_back_container_tracker(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    await self.head.pick_up_tips(rack, column=0)
    with (
      patch.object(
        self.api,
        "submit_command",
        AsyncMock(
          side_effect=[self.api.submit_command.return_value] * 2
          + [RuntimeError("pipetting failed")]
        ),
      ) as submit,
      self.assertRaisesRegex(RuntimeError, "pipetting failed"),
    ):
      for tip in await self.head.get_mounted_tips():
        if tip is not None:
          await tip.set_volume(40)
      await self.head.dispense_container(trough, volume=40)

    assert submit.await_args is not None
    self.assertEqual(submit.await_args.args[1], "dispenseInPlace")
    # The staged 8 * 40 uL is rolled back in full.
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 0.0)
    self.assertAlmostEqual((await trough.get_volume()), 0.0)

  async def test_offset_that_keeps_row_inside_cavity_passes(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    # 85.48 mm front-to-back; 63 mm row + 2*11.24 = 85.48 just fits
    trough = cast(handles.Container, await _put(self.flex, _make_trough(), "C2", "trough"))
    await trough.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.aspirate_container(trough, volume=10, offset=Coordinate(y=11.24))

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    # A lateral-only offset keeps the default bottom clearance: its z is 0
    # because the caller said nothing about z, not to ask for the floor.
    self.assertEqual(
      (await pipetting_location(self.api, trough, self.head.channels))["offset"],
      {"x": 0, "y": 11.24, "z": 1.0},
    )

  async def test_zero_offset_keeps_the_default_bottom_clearance(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.aspirate_container(trough, volume=10, offset=Coordinate.zero())

    [c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"]
    self.assertEqual(
      (await pipetting_location(self.api, trough, self.head.channels))["offset"],
      {"x": 0, "y": 0, "z": 1.0},
      "a no-op offset must not move the tip to the cavity floor",
    )

  async def test_too_small_container_message_names_no_offset_when_none_was_passed(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    narrow = cast(
      handles.Container,
      await _put(
        self.flex, _make_trough(name="narrow", size_y=40.0, max_volume=50000.0), "C2", "narrow"
      ),
    )
    await narrow.set_volume(10000.0)
    await self.head.pick_up_tips(rack, column=0)

    with self.assertRaises(OpentronsError) as no_offset:
      await self.head.aspirate_container(narrow, volume=50)
    self.assertNotIn("offset", str(no_offset.exception))

    with self.assertRaises(OpentronsError) as with_offset:
      await self.head.aspirate_container(narrow, volume=50, offset=Coordinate(y=3))
    self.assertIn("offset", str(with_offset.exception))

  async def test_rotated_cavity_is_guarded_on_the_axis_the_robot_sees(self):
    # 40 x 70 mm rotated a quarter turn is a 70 x 40 mm cavity to the robot,
    # which is the footprint the uploaded definition carries.
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    rotated = cast(
      handles.Container,
      await _put(
        self.flex,
        _make_trough(name="rotated", size_x=40.0, size_y=70.0, max_volume=50000.0, turned=True),
        "C2",
        "rotated",
      ),
    )
    await rotated.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate_container(rotated, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await rotated.get_volume(COMMITTED)), 10000.0)

  async def test_rotated_cavity_deep_enough_for_the_row_is_accepted(self):
    # The mirror case: 110 x 60 mm rotated presents 110 mm front-to-back, so
    # the 63 mm row fits and reading the pre-rotation 60 mm would refuse it.
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    rotated = cast(
      handles.Container,
      await _put(
        self.flex,
        _make_trough(name="rotated", size_x=110.0, size_y=60.0, max_volume=50000.0, turned=True),
        "C2",
        "rotated",
      ),
    )
    await rotated.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.aspirate_container(rotated, volume=50)

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)

  async def test_rotated_parent_rotates_the_cavity_too(self):
    # The guard reads the COMPOSED rotation, so a plain container inside a
    # rotated carrier is guarded on the same axis the robot will see.
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    inner_definition = _make_trough(
      name="inner", size_x=40.0, size_y=70.0, max_volume=50000.0, location=Coordinate.zero()
    )
    carrier_definition = build.resource(
      "carrier",
      Coordinate(70.0, 40.0, 25.0),
      rotation=Rotation(z=90),
      children=[inner_definition],
    )
    await _put(self.flex, carrier_definition, "C2", "carrier")
    inner = cast(handles.Container, await self.flex.deck.get_resource("inner"))
    await inner.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError) as raised:
      await self.head.aspirate_container(inner, volume=50)

    # Name the guard: reading the container's own y (70 mm) would let this
    # through, and it would then fail later for an unrelated reason.
    self.assertEqual(raised.exception.title, "Container too small")
    self.assertEqual(self.api.submit_command.await_count, commands_before)

  async def test_offset_that_shifts_row_past_cavity_wall_rejects_pre_wire(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    # 85.48 front-to-back; 63 mm row + 2*11.5 = 86 overhangs
    trough = cast(handles.Container, await _put(self.flex, _make_trough(), "C2", "trough"))
    await trough.set_volume(10000.0)

    await self.head.pick_up_tips(rack, column=0)
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate_container(trough, volume=10, offset=Coordinate(y=-11.5))

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 10000.0)


class TestFlexHead96ContainerOps(unittest.IsolatedAsyncioTestCase):
  """PLR centers the 96-nozzle grid and tracks total container volume."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head96(self)

  async def test_reservoir_well_centers_array_for_aspirate_and_dispense(self):
    """A single-well reservoir centers all 96 tips, despite being a Well."""
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    reservoir = cast(
      handles.Plate,
      await _put(self.flex, "cor_axy_1_troughplate_rowVb", "D1", "reservoir"),
    )
    cavity = reservoir.get_well("A1")
    await cavity.set_volume(100000)
    await self.head.pick_up_tips(rack)
    for operation in (self.head.aspirate, self.head.dispense):
      with self.subTest(operation=operation.__name__):
        self.api.submit_command.reset_mock()
        await operation(cavity, volume=10)
        moves = [
          c for c in self.api.submit_command.await_args_list if c.args[1] == "moveToCoordinates"
        ]
        self.assertEqual(moves[0].args[2]["coordinates"], {"x": 14.38, "y": 74.24, "z": 109.0})
        self.assertEqual(
          await pipetting_location(self.api, cavity, self.head.channels),
          {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
        )
    self.assertAlmostEqual((await cavity.get_volume(COMMITTED)), 100000)

  async def test_aspirate_container_centers_grid_and_tracks_96_channels(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(100000.0)

    await self.head.pick_up_tips(rack)
    await self.head.aspirate(trough, volume=50)

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    params = aspirate_cmds[0].args[2]
    self.assertNotIn("wellName", params)
    # The primary nozzle is positioned so the grid centers on the cavity.
    self.assertEqual(
      await pipetting_location(self.api, trough, self.head.channels),
      {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
    )

    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 100000.0 - 96 * 50.0)
    self.assertAlmostEqual((await trough.get_volume()), 100000.0 - 96 * 50.0)

  async def test_dispense_container_centers_grid_and_adds_96x(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    await self.head.pick_up_tips(rack)
    for tip in await self.head.get_mounted_tips():
      if tip is not None:
        await tip.set_volume(20)
    await self.head.dispense(trough, volume=20)

    dispense_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "dispenseInPlace"
    ]
    self.assertEqual(len(dispense_cmds), 1)
    params = dispense_cmds[0].args[2]
    self.assertNotIn("wellName", params)
    self.assertEqual(
      await pipetting_location(self.api, trough, self.head.channels),
      {"origin": "bottom", "offset": {"x": 0, "y": 0, "z": 1.0}},
    )
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 96 * 20.0)

  async def test_aspirate_container_without_tip_rejects_before_any_wire_command(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(100000.0)

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate(trough, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 100000.0)

  async def test_aspirate_container_rejects_cavity_smaller_than_grid(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    narrow = cast(
      handles.Container,
      await _put(
        self.flex, _make_trough(name="narrow", size_x=90.0, max_volume=50000.0), "C2", "narrow"
      ),
    )
    await narrow.set_volume(10000.0)

    await self.head.pick_up_tips(rack)

    # 90 mm left-to-right cannot contain the grid's 99 mm x span.
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate(narrow, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await narrow.get_volume(COMMITTED)), 10000.0)

  async def test_wire_failure_rolls_back_container_tracker(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )
    await trough.set_volume(100000.0)

    await self.head.pick_up_tips(rack)
    with (
      patch.object(
        self.api,
        "submit_command",
        AsyncMock(
          side_effect=[self.api.submit_command.return_value] * 3
          + [RuntimeError("pipetting failed")]
        ),
      ) as submit,
      self.assertRaisesRegex(RuntimeError, "pipetting failed"),
    ):
      await self.head.aspirate(trough, volume=50)

    assert submit.await_args is not None
    self.assertEqual(submit.await_args.args[1], "aspirateInPlace")
    # The staged 96 * 50 uL is rolled back in full: committed AND pending
    # volume are untouched.
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 100000.0)
    self.assertAlmostEqual((await trough.get_volume()), 100000.0)

  async def test_aspirate_container_rejects_cavity_shallower_than_grid_y_span(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    shallow = cast(
      handles.Container,
      await _put(
        self.flex, _make_trough(name="shallow", size_y=50.0, max_volume=50000.0), "C2", "shallow"
      ),
    )
    await shallow.set_volume(10000.0)

    await self.head.pick_up_tips(rack)

    # 50 mm front-to-back cannot contain the grid's 63 mm y span.
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate(shallow, volume=50)

    self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await shallow.get_volume(COMMITTED)), 10000.0)

  async def test_offset_that_keeps_grid_inside_cavity_passes(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    # 127.76 x 85.48; grid 99 x 63 plus 2*14.38 / 2*11.24 just fits
    trough = cast(handles.Container, await _put(self.flex, _make_trough(), "C2", "trough"))
    await trough.set_volume(100000.0)

    await self.head.pick_up_tips(rack)
    await self.head.aspirate(trough, volume=10, offset=Coordinate(x=14.38, y=11.24))

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    self.assertEqual(
      (await pipetting_location(self.api, trough, self.head.channels))["offset"],
      {"x": 14.38, "y": 11.24, "z": 1.0},
    )

  async def test_rotated_cavity_is_guarded_on_the_axis_the_robot_sees(self):
    # 107 x 71 mm rotated a quarter turn is 71 mm left-to-right to the robot,
    # too narrow for the grid's 99 mm x span, though unrotated it fits.
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    rotated = cast(
      handles.Container,
      await _put(self.flex, _make_trough(name="rotated", turned=True), "C2", "rotated"),
    )
    await rotated.set_volume(100000.0)

    await self.head.pick_up_tips(rack)
    for op in (
      lambda: self.head.aspirate(rotated, volume=50),
      lambda: self.head.dispense(rotated, volume=50),
    ):
      commands_before = self.api.submit_command.await_count
      with self.assertRaises(OpentronsError):
        await op()
      self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await rotated.get_volume(COMMITTED)), 100000.0)

  async def test_offset_that_shifts_grid_past_cavity_wall_rejects_pre_wire(self):
    rack = cast(handles.TipRack, await _put(self.flex, "flex_96_tiprack_50ul", "C1", "rack"))
    # 127.76 x 85.48: 99 + 2*14.5 and 63 + 2*11.5 both overhang
    trough = cast(handles.Container, await _put(self.flex, _make_trough(), "C2", "trough"))
    await trough.set_volume(100000.0)

    await self.head.pick_up_tips(rack)
    for offset in (Coordinate(x=14.5), Coordinate(y=11.5)):
      commands_before = self.api.submit_command.await_count
      with self.assertRaises(OpentronsError):
        await self.head.aspirate(trough, volume=10, offset=offset)
      self.assertEqual(self.api.submit_command.await_count, commands_before)
    self.assertAlmostEqual((await trough.get_volume(COMMITTED)), 100000.0)


class TestLiquidOpsRequireAMountedTip(unittest.IsolatedAsyncioTestCase):
  """Every liquid op requires a mounted tip, wells and plates as much as
  containers: without one the command describes a tip that is not there and
  the pipette drives its bare NOZZLE roughly a tip length lower. The engine
  rejects a tipless op, but ``dispense`` moves to the well FIRST and checks
  after, so the collision happens before the rejection."""

  @staticmethod
  async def _plate(flex: Flex) -> handles.Plate:
    plate = cast(handles.Plate, await _put(flex, "cor_96_wellplate_360uL_Fb", "C2", "plate"))
    await plate.set_well_volumes(100.0)
    return plate

  async def _assert_refused_pre_wire(self, flex, api, op) -> None:
    commands_before = api.submit_command.await_count
    with self.assertRaises(OpentronsError) as caught:
      await op()
    self.assertEqual(caught.exception.title, "NoTipError")
    self.assertEqual(api.submit_command.await_count, commands_before)

  async def test_head1_well_ops_refuse_without_a_tip(self):
    flex, api, head = await _flex_head1(self)
    well = (await self._plate(flex)).get_well("B3")
    await self._assert_refused_pre_wire(flex, api, lambda: head.aspirate(well, volume=10))
    await self._assert_refused_pre_wire(flex, api, lambda: head.dispense(well, volume=10))
    self.assertAlmostEqual((await well.get_volume(COMMITTED)), 100.0)

  async def test_head8_column_ops_refuse_without_tips(self):
    flex, api, head = await _flex_head8(self)
    plate = await self._plate(flex)
    await self._assert_refused_pre_wire(
      flex, api, lambda: head.aspirate(plate, column=0, volume=10)
    )
    await self._assert_refused_pre_wire(
      flex, api, lambda: head.dispense(plate, column=0, volume=10)
    )
    self.assertAlmostEqual((await plate.get_well("A1").get_volume(COMMITTED)), 100.0)

  async def test_head96_plate_ops_refuse_without_tips(self):
    flex, api, head = await _flex_head96(self)
    plate = await self._plate(flex)
    await self._assert_refused_pre_wire(flex, api, lambda: head.aspirate(plate, volume=10))
    await self._assert_refused_pre_wire(flex, api, lambda: head.dispense(plate, volume=10))
    self.assertAlmostEqual((await plate.get_well("A1").get_volume(COMMITTED)), 100.0)


async def _flex_device(
  test_case: unittest.IsolatedAsyncioTestCase,
  api_version: str = OFFLINE_API_VERSION,
) -> Tuple[Flex, AsyncMock]:
  """A set-up ``Flex`` plus its api, for the robot-level
  commands that belong to the device rather than to a head. ``api_version`` is
  what ``/health`` reports, which is what the robot/* version gate reads.
  """
  api = make_api(pipettes=[("p1000_single_flex", 1, 1.0, 1000.0, "right")], api_version=api_version)
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  await flex.setup()
  return flex, api


def _cmds(api: AsyncMock, command_type: str) -> List[_Call]:
  return [c for c in api.submit_command.await_args_list if c.args[1] == command_type]


class TestFlexAxisMotion(unittest.IsolatedAsyncioTestCase):
  """move_axes_to/move_axes_relative send the robot/* family's snake_case
  params and return the axis positions the command reports."""

  async def asyncSetUp(self):
    self.flex, self.api = await _flex_device(self)

  async def test_move_axes_to_sends_snake_case_axis_map_only(self):
    await self.flex.move_axes_to({"x": 100.0, "leftZ": 250.0})

    (cmd,) = _cmds(self.api, "robot/moveAxesTo")
    self.assertEqual(cmd.args[2], {"axis_map": {"x": 100.0, "leftZ": 250.0}})

  async def test_move_axes_to_sends_critical_point_and_speed_snake_case(self):
    await self.flex.move_axes_to({"x": 1.0}, critical_point={"rightZ": 5.0}, speed=40.0)

    (cmd,) = _cmds(self.api, "robot/moveAxesTo")
    self.assertEqual(
      cmd.args[2],
      {"axis_map": {"x": 1.0}, "critical_point": {"rightZ": 5.0}, "speed": 40.0},
    )

  async def test_move_axes_relative_sends_snake_case_axis_map_and_speed(self):
    await self.flex.move_axes_relative({"y": -5.0}, speed=20.0)

    (cmd,) = _cmds(self.api, "robot/moveAxesRelative")
    self.assertEqual(cmd.args[2], {"axis_map": {"y": -5.0}, "speed": 20.0})

  async def test_speed_omitted_when_not_given(self):
    await self.flex.move_axes_relative({"y": -5.0})

    (cmd,) = _cmds(self.api, "robot/moveAxesRelative")
    self.assertNotIn("speed", cmd.args[2])

  async def test_both_moves_return_the_reported_position(self):
    self.api.get_command.return_value.result["position"] = {"x": 11.0, "y": 22.0, "leftZ": 33.0}
    reached = {"x": 11.0, "y": 22.0, "leftZ": 33.0}
    self.assertEqual(await self.flex.move_axes_to({"x": 11.0}), reached)
    self.assertEqual(await self.flex.move_axes_relative({"x": 1.0}), reached)

  async def test_unknown_axis_refused_before_any_wire_command(self):
    for op in (
      lambda: self.flex.move_axes_to({"x": 1.0, "zed": 2.0}),
      lambda: self.flex.move_axes_relative({"zed": 2.0}),
    ):
      commands_before = self.api.submit_command.await_count
      with self.assertRaises(ValueError) as caught:
        await op()
      # The refusal names what was wrong AND what would have been right.
      self.assertIn("zed", str(caught.exception))
      self.assertIn("extensionJaw", str(caught.exception))
      self.assertEqual(self.api.submit_command.await_count, commands_before)

  async def test_unknown_critical_point_axis_refused_before_any_wire_command(self):
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(ValueError):
      await self.flex.move_axes_to({"x": 1.0}, critical_point={"zed": 2.0})

    self.assertEqual(self.api.submit_command.await_count, commands_before)

  async def test_retract_axis_refuses_an_unknown_axis_before_the_wire(self):
    commands_before = self.api.submit_command.await_count
    with self.assertRaises(ValueError):
      await self.flex.retract_axis("zed")

    self.assertEqual(self.api.submit_command.await_count, commands_before)


class TestFlexAxisMotionVersionGate(unittest.IsolatedAsyncioTestCase):
  """The robot/* moveAxes commands need robot software 8.2.0+; retractAxis
  predates that family and is not gated."""

  async def asyncSetUp(self):
    self.flex, self.api = await _flex_device(self, api_version="8.1.0")

  async def test_old_release_refuses_both_moves_and_sends_nothing(self):
    for op in (
      lambda: self.flex.move_axes_to({"x": 1.0}),
      lambda: self.flex.move_axes_relative({"x": 1.0}),
    ):
      with self.assertRaises(OpentronsError) as caught:
        await op()
      self.assertIn("8.2.0", str(caught.exception))

    robot_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1].startswith("robot/")
    ]
    self.assertEqual(robot_cmds, [])

  async def test_retract_axis_is_not_gated(self):
    await self.flex.retract_axis("leftZ")
    self.assertEqual(len(_cmds(self.api, "retractAxis")), 1)


class TestFlexRobotCommands(unittest.IsolatedAsyncioTestCase):
  """The device's one-shot commands: exact params, no extras."""

  async def asyncSetUp(self):
    self.flex, self.api = await _flex_device(self)

  async def test_retract_axis(self):
    await self.flex.retract_axis("extensionJaw")

    (cmd,) = _cmds(self.api, "retractAxis")
    self.assertEqual(cmd.args[2], {"axis": "extensionJaw"})

  async def test_set_status_bar(self):
    await self.flex.set_status_bar("disco")

    (cmd,) = _cmds(self.api, "setStatusBar")
    self.assertEqual(cmd.args[2], {"animation": "disco"})

  async def test_set_rail_lights_carries_the_boolean_both_ways(self):
    await self.flex.set_rail_lights(True)
    await self.flex.set_rail_lights(False)

    cmds = _cmds(self.api, "setRailLights")
    self.assertEqual([c.args[2] for c in cmds], [{"on": True}, {"on": False}])

  async def test_add_comment(self):
    await self.flex.add_comment("starting plate 3")

    (cmd,) = _cmds(self.api, "comment")
    self.assertEqual(cmd.args[2], {"message": "starting plate 3"})

  async def test_wait_for_duration(self):
    await self.flex.wait_for_duration(2.5)

    (cmd,) = _cmds(self.api, "waitForDuration")
    self.assertEqual(cmd.args[2], {"seconds": 2.5})

  async def test_reload_labware_names_the_id_the_labware_was_loaded_under(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    await self.flex.reload_labware(trough)

    (_load_cmd,) = _cmds(self.api, "loadLabware")
    (reload_cmd,) = _cmds(self.api, "reloadLabware")
    self.assertEqual(reload_cmd.args[2], {"labwareId": "labware"})

  async def test_reload_labware_of_loaded_labware_does_not_load_it_again(self):
    trough = cast(
      handles.Container,
      await _put(self.flex, _make_trough(), "C2", "trough"),
    )

    await self.flex.reload_labware(trough)
    await self.flex.reload_labware(trough)

    self.assertEqual(len(_cmds(self.api, "loadLabware")), 1)
    self.assertEqual(len(_cmds(self.api, "reloadLabware")), 2)


if __name__ == "__main__":
  unittest.main()
