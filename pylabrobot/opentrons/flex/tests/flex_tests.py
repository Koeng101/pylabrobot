"""Tests for Flex device shell + head composition.

Drives ``Flex.setup()`` with an injected ``AsyncMock`` (no
network) reporting a configurable mounted pipette, and asserts discovery
composes the matching head onto the right attribute (``left``/``right``/
``head96``). Labware, tips and liquid live in an in-memory resource store.
"""

import unittest
from typing import List, Tuple, Union
from unittest.mock import AsyncMock, patch

from pylabrobot.opentrons.decks import (
  assign_child_at_slot,
  get_trash_area,
  unassign_child_at_slot,
)
from pylabrobot.opentrons.flex.errors import OpentronsCommandError, OpentronsError
from pylabrobot.opentrons.flex.flex import Flex
from pylabrobot.opentrons.flex.flex_head import FlexHead1, FlexHead8, FlexHead96, _FlexHead
from pylabrobot.opentrons.flex.tests.liquid_test_utils import pipetting_location
from pylabrobot.opentrons.flex.tests.mock_utils import make_api, make_deck, make_flex, place
from pylabrobot.opentrons.types import CommandInfo
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import TooLittleLiquidError
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

_TIPS = "flex_96_tiprack_50ul"
_PLATE = "cor_96_wellplate_360uL_Fb"


async def _flex(
  test_case: unittest.IsolatedAsyncioTestCase,
  pipette: Tuple[str, int, float, float],
  mount: str = "right",
) -> Flex:
  api = make_api(pipette=pipette, mount=mount)
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  return flex


async def _flex_with_api(
  test_case: unittest.IsolatedAsyncioTestCase,
  pipettes: List[Tuple[str, int, float, float, str]],
  **api_kwargs,
) -> Tuple[Flex, AsyncMock]:
  """Build a Flex with fixed API replies and return its mock for assertions."""
  api = make_api(pipettes=pipettes, **api_kwargs)
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  return flex, api


async def _rack(flex: Flex, name: str = "rack", slot: str = "C1") -> handles.TipRack:
  rack = await place(flex.deck, _TIPS, name, slot)
  assert isinstance(rack, handles.TipRack)
  return rack


async def _plate(flex: Flex, name: str = "plate", slot: str = "C2") -> handles.Plate:
  plate = await place(flex.deck, _PLATE, name, slot)
  assert isinstance(plate, handles.Plate)
  return plate


async def _take_tips(spots: List[handles.Resource]) -> None:
  """Take the tips out of spots by hand."""
  await spots[0].store.commands.update_resources(
    spb.UpdateResourcesRequest(
      updates=[
        spb.ResourceUpdate(
          tip_presence=pb.SetTipPresence(spots=[spot.ref for spot in spots], present=False)
        )
      ]
    )
  )


async def _has_tip(spot: handles.Resource) -> bool:
  assert isinstance(spot, handles.TipSpot)
  return await spot.has_tip()


async def _set_tip_volumes(head: _FlexHead, volume: float) -> None:
  """Say what every mounted tip holds."""
  for tip in await head.get_mounted_tips():
    if tip is not None:
      await tip.set_volume(volume)


async def _volume(well: handles.Resource) -> float:
  """What a container holds, committed."""
  assert isinstance(well, handles.Container)
  return await well.get_volume(pb.VIEW_COMMITTED)


async def _used(well: handles.Resource) -> float:
  """What a container holds, counting staged changes."""
  assert isinstance(well, handles.Container)
  return await well.get_volume()


class TestLifecycleHalves(unittest.IsolatedAsyncioTestCase):
  """``setup``/``stop`` are the two halves run together; each half is callable alone.

  The split exists because taking the robot and moving it are separate acts. An
  operator reclaiming the touchscreen wants the session ended and nothing else;
  homing an arm over a deck someone is reaching into is the thing to avoid.
  """

  async def asyncSetUp(self):
    self.api = make_api(pipettes=[("p50_multi_flex", 8, 1.0, 50.0, "left")])
    self.flex = make_flex(deck=await make_deck(), host="localhost", api=self.api)
    self.addAsyncCleanup(self.flex.disconnect)

  async def test_connect_opens_the_link_but_starts_no_run(self):
    """The run is what the robot holds against its touchscreen, so taking the
    robot is create_run's doing, not connect's."""

    await self.flex.connect()
    self.assertIsNone(self.flex.run_id)
    self.assertEqual(
      [c for c in self.api.submit_command.await_args_list if c.args[1] == "home"], []
    )

  async def test_initialize_discovers_without_moving(self):
    """Asking what is mounted must not require moving the robot to find out."""
    await self.flex.connect()
    await self.flex.create_run()

    await self.flex.initialize()
    self.assertIsInstance(self.flex.left, FlexHead8)
    self.assertEqual(
      [c for c in self.api.submit_command.await_args_list if c.args[1] == "home"], []
    )

  async def test_cancel_run_frees_local_control_without_dropping_the_link(self):
    """The operator's 'give me the robot back' action: end the session, stay connected."""
    await self.flex.setup()
    homes_from_setup = len(
      [c for c in self.api.submit_command.await_args_list if c.args[1] == "home"]
    )

    await self.flex.cancel_run()
    self.assertIsNone(self.flex.run_id)
    self.assertEqual(
      len([c for c in self.api.submit_command.await_args_list if c.args[1] == "home"]),
      homes_from_setup,
    )

  async def test_disconnect_ends_the_run_without_homing(self):
    await self.flex.setup()
    homes_from_setup = len(
      [c for c in self.api.submit_command.await_args_list if c.args[1] == "home"]
    )

    await self.flex.disconnect()

    self.assertIsNone(self.flex.run_id)
    self.assertEqual(
      len([c for c in self.api.submit_command.await_args_list if c.args[1] == "home"]),
      homes_from_setup,
    )

  async def test_stop_still_homes_before_releasing(self):
    """The one-call teardown keeps parking the gantry; only disconnect skips it."""
    await self.flex.setup()
    homes_from_setup = len(
      [c for c in self.api.submit_command.await_args_list if c.args[1] == "home"]
    )

    await self.flex.stop()

    self.assertEqual(
      len([c for c in self.api.submit_command.await_args_list if c.args[1] == "home"]),
      homes_from_setup + 1,
    )
    self.assertIsNone(self.flex.run_id)


class TestHeadDiscovery(unittest.IsolatedAsyncioTestCase):
  """setup() discovers mounted pipettes and composes the matching head per mount."""

  async def test_eight_channel_left_mount_becomes_flex_head8(self):
    flex = await _flex(self, ("p50_multi_flex", 8, 1.0, 50.0), mount="left")
    await flex.setup()
    self.assertIsInstance(flex.left, FlexHead8)
    self.assertIsNone(flex.right)
    self.assertIsNone(flex.head96)

  async def test_eight_channel_right_mount_becomes_flex_head8(self):
    flex = await _flex(self, ("p50_multi_flex", 8, 1.0, 50.0), mount="right")
    await flex.setup()
    self.assertIsInstance(flex.right, FlexHead8)
    self.assertIsNone(flex.left)
    self.assertIsNone(flex.head96)

  async def test_single_channel_becomes_flex_head1(self):
    flex = await _flex(self, ("p1000_single_flex", 1, 1.0, 1000.0), mount="right")
    await flex.setup()
    self.assertIsInstance(flex.right, FlexHead1)
    self.assertIsNone(flex.left)
    self.assertIsNone(flex.head96)

  async def test_ninety_six_channel_becomes_head96_leaves_mounts_none(self):
    flex = await _flex(self, ("p1000_96", 96, 1.0, 1000.0), mount="left")
    await flex.setup()
    self.assertIsInstance(flex.head96, FlexHead96)
    self.assertIsNone(flex.left)
    self.assertIsNone(flex.right)

  async def test_unsupported_channel_count_raises_opentrons_error(self):
    flex = await _flex(self, ("weird_pipette", 4, 1.0, 100.0), mount="right")
    with self.assertRaises(OpentronsError):
      await flex.setup()

  async def test_load_pipette_failure_raises_flex_command_error(self):
    """A loadPipette failure surfaces the flex OpentronsCommandError -- the same
    shape (a readable ``error_type``) every other command raises -- not the
    package-level variant an inherited ``OpentronsRun.load_pipette`` would give.
    """

    io = make_api(pipette=("p50_multi_flex", 8, 1.0, 50.0), mount="left")
    io.get_command.side_effect = [
      io.get_command.return_value,
      CommandInfo("failed", {}, {"errorType": "PipetteNotFoundError", "detail": "missing pipette"}),
    ]
    flex = make_flex(deck=await make_deck(), host="localhost", api=io)
    self.addAsyncCleanup(flex.disconnect)
    with self.assertRaises(OpentronsCommandError) as ctx:
      await flex.setup()
    self.assertEqual(ctx.exception.error_type, "PipetteNotFoundError")


class TestNoDoubleLoad(unittest.IsolatedAsyncioTestCase):
  """Setup loads each discovered pipette exactly once."""

  async def test_single_pipette_is_loaded_exactly_once(self):
    flex, api = await _flex_with_api(self, [("p50_multi_flex", 8, 1.0, 50.0, "left")])
    await flex.setup()
    self.assertEqual(
      len([c.args[2] for c in api.submit_command.await_args_list if c.args[1] == "loadPipette"]),
      1,
    )


class TestDualMount(unittest.IsolatedAsyncioTestCase):
  """setup() discovers and composes BOTH mounts when two pipettes are present."""

  async def test_left_and_right_mounts_become_distinct_heads(self):
    flex, api = await _flex_with_api(
      self,
      [
        ("p50_multi_flex", 8, 1.0, 50.0, "left"),
        ("p1000_single_flex", 1, 1.0, 1000.0, "right"),
      ],
    )
    api.get_command.side_effect = [
      CommandInfo("succeeded", {}, {}),
      CommandInfo("succeeded", {"pipetteId": "left-pipette"}, {}),
      CommandInfo("succeeded", {"pipetteId": "right-pipette"}, {}),
    ]
    await flex.setup()
    api.get_command.side_effect = None
    self.assertIsInstance(flex.left, FlexHead8)
    self.assertIsInstance(flex.right, FlexHead1)
    assert flex.left is not None and flex.right is not None
    self.assertNotEqual(flex.left.pipette_id, flex.right.pipette_id)
    self.assertEqual(
      len([c.args[2] for c in api.submit_command.await_args_list if c.args[1] == "loadPipette"]),
      2,
    )


class TestNoPipetteMounted(unittest.IsolatedAsyncioTestCase):
  """setup() raises OpentronsError when no pipette is mounted at all."""

  async def test_empty_pipette_list_raises_opentrons_error(self):
    flex, api = await _flex_with_api(self, [])
    with self.assertRaises(OpentronsError):
      await flex.setup()


class TestImpossibleHead96PlusMountCombo(unittest.IsolatedAsyncioTestCase):
  """A 96-channel head cannot physically coexist with a mount pipette."""

  async def test_head96_plus_mount_pipette_raises_opentrons_error(self):
    flex, api = await _flex_with_api(
      self,
      [
        ("p1000_96", 96, 1.0, 1000.0, "left"),
        ("p1000_single_flex", 1, 1.0, 1000.0, "right"),
      ],
    )
    with self.assertRaises(OpentronsError):
      await flex.setup()


class TestGetMountedTips(unittest.IsolatedAsyncioTestCase):
  """get_mounted_tips() returns a list sized to the head's channel count, and a copy."""

  async def test_eight_channel_head_reports_eight_slots(self):
    flex = await _flex(self, ("p50_multi_flex", 8, 1.0, 50.0), mount="left")
    await flex.setup()
    head = flex.left
    assert head is not None
    tips = await head.get_mounted_tips()
    self.assertEqual(len(tips), 8)
    self.assertTrue(all(tip is None for tip in tips))

  async def test_returned_list_is_a_copy(self):
    flex = await _flex(self, ("p1000_single_flex", 1, 1.0, 1000.0), mount="right")
    await flex.setup()
    head = flex.right
    assert head is not None
    tips = await head.get_mounted_tips()
    tips.append(None)  # mutate the returned list; must not affect head state
    self.assertEqual(len(await head.get_mounted_tips()), 1)

  async def test_ninety_six_channel_head_reports_ninety_six_slots(self):
    flex = await _flex(self, ("p1000_96", 96, 1.0, 1000.0), mount="left")
    await flex.setup()
    head = flex.head96
    assert head is not None
    self.assertEqual(len(await head.get_mounted_tips()), 96)


async def _flex_head8(
  test_case: unittest.IsolatedAsyncioTestCase, **api_kwargs
) -> Tuple[Flex, AsyncMock, FlexHead8]:
  """Build a Flex with fixed API replies and return its mock for assertions."""
  flex, api = await _flex_with_api(
    test_case, [("p50_multi_flex", 8, 1.0, 50.0, "left")], **api_kwargs
  )
  await flex.setup()
  head = flex.left
  assert isinstance(head, FlexHead8)
  return flex, api, head


def _names(resources: List[handles.Resource]) -> List[str]:
  return [r.name for r in resources]


class TestFlexHead8ColumnOps(unittest.IsolatedAsyncioTestCase):
  """Column ops send exactly ONE wire command anchored at the
  column's A-row well; the hardware fans it out to all 8 physical channels;
  liquid and tips are booked only for wells/spots the head actually actuated.
  """

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8(self)

  async def test_pick_up_tips_emits_one_command_and_fans_to_all_8_channels(self):
    rack = await _rack(self.flex)

    await self.head.pick_up_tips(rack, column=0)

    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1)
    self.assertEqual(pickup_cmds[0].args[2]["wellName"], "A1")

    column_spots = rack.items[0:8]
    for spot in column_spots:
      self.assertFalse(await _has_tip(spot))

    tips = await self.head.get_mounted_tips()
    self.assertEqual(sum(1 for t in tips if t is not None), 8)

  async def test_aspirate_emits_one_command_and_only_column_wells_change(self):
    rack = await _rack(self.flex)
    plate = await _plate(self.flex)

    # Pre-load every well with 100uL so aspirating 50uL is valid, and so a
    # baseline exists to prove non-column wells are untouched.
    wells = plate.items
    await plate.set_well_volumes(100.0)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.aspirate(plate, column=2, volume=50)

    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    self.assertNotIn("wellName", aspirate_cmds[0].args[2])

    column_2 = set(_names(wells[16:24]))
    for well in wells:
      expected = 50.0 if well.name in column_2 else 100.0
      self.assertAlmostEqual(await _volume(well), expected, msg=well.name)

  async def test_pick_up_single_tip_configures_nozzle_then_picks_named_well(self):
    rack = await _rack(self.flex)

    await self.head.pick_up_single_tip(rack, well="A2")

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    configure_idx = cmd_types.index("configureNozzleLayout")
    pickup_idx = cmd_types.index("pickUpTip")
    self.assertLess(configure_idx, pickup_idx)
    self.assertEqual(self.api.submit_command.await_args_list[pickup_idx].args[2]["wellName"], "A2")

    tips = await self.head.get_mounted_tips()
    self.assertIsNotNone(tips[7])
    for i in range(7):
      self.assertIsNone(tips[i], msg=f"channel {i}")

  async def test_dispense_emits_one_command_and_only_column_wells_change(self):
    rack = await _rack(self.flex)
    plate = await _plate(self.flex)

    await self.head.pick_up_tips(rack, column=0)
    await _set_tip_volumes(self.head, 30)
    await self.head.dispense(plate, column=5, volume=30)

    dispense_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "dispenseInPlace"
    ]
    self.assertEqual(len(dispense_cmds), 1)
    self.assertNotIn("wellName", dispense_cmds[0].args[2])

    wells = plate.items
    column_5 = set(_names(wells[40:48]))
    for well in wells:
      expected = 30.0 if well.name in column_5 else 0.0
      self.assertAlmostEqual(await _volume(well), expected, msg=well.name)

  async def test_drop_tips_to_rack_returns_tips_and_clears_channels(self):
    rack = await _rack(self.flex)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.drop_tips(rack, column=0)  # return to the column it came from

    drop_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "dropTip"]
    self.assertEqual(len(drop_cmds), 1)
    self.assertEqual(drop_cmds[0].args[2]["wellName"], "A1")

    for spot in rack.items[0:8]:
      self.assertTrue(await _has_tip(spot))

    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  async def test_discard_tips_uses_addressable_area_trash_sequence(self):
    rack = await _rack(self.flex)
    trash = await get_trash_area(self.flex.deck)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.discard_tips(trash)

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    self.assertIn("moveToAddressableAreaForDropTip", cmd_types)
    self.assertIn("dropTipInPlace", cmd_types)
    move_cmd = next(
      c
      for c in self.api.submit_command.await_args_list
      if c.args[1] == "moveToAddressableAreaForDropTip"
    )
    self.assertEqual(move_cmd.args[2]["addressableAreaName"], "movableTrashA3")
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  async def test_single_tip_aspirate_dispense_and_drop_round_trip(self):
    rack = await _rack(self.flex)
    plate = await _plate(self.flex)
    trash = await get_trash_area(self.flex.deck)

    await self.head.pick_up_single_tip(rack, well="A1", primary_nozzle="H1")
    self.assertIsNotNone((await self.head.get_mounted_tips())[7])

    await _set_tip_volumes(self.head, 20)
    await self.head.dispense_single(plate, well="B3", volume=20)
    target = plate.get_well("B3")
    self.assertAlmostEqual(await _volume(target), 20.0)

    # Every other well is untouched (single-tip is a strict None-skip case).
    for well in plate.items:
      if well.name == target.name:
        continue
      self.assertAlmostEqual(await _volume(well), 0.0, msg=well.name)

    await target.set_volume(20.0)  # aspirate needs liquid present
    await self.head.aspirate_single(plate, well="B3", volume=20)
    self.assertAlmostEqual(await _volume(target), 0.0)

    await self.head.drop_single_tip(trash)
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

    # Nozzle layout is restored to ALL, so a subsequent column op needs no
    # extra reset command beyond the ones already issued.
    await self.head.pick_up_tips(rack, column=1)
    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(pickup_cmds[-1].args[2]["wellName"], "A2")


class TestFlexHead8PrepareToAspirate(unittest.IsolatedAsyncioTestCase):
  """The driver primes at traversal height before entering the well."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8(self)
    self.rack = await _rack(self.flex)
    self.plate = await _plate(self.flex)
    await self.plate.set_well_volumes(100.0)

  async def test_prepare_is_sent_before_each_aspiration(self):
    await self.head.pick_up_tips(self.rack, column=0)
    await self.head.aspirate(self.plate, column=0, volume=10)
    await self.head.dispense(self.plate, column=1, volume=10)
    await self.head.aspirate(self.plate, column=1, volume=10)

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    self.assertEqual(cmd_types.count("aspirateInPlace"), 2)
    self.assertIn("prepareToAspirate", cmd_types)

  async def test_a_well_addressed_aspirate_still_works_with_the_plunger_pushed_past_bottom(self):
    """The whole reason the driver can stay out of it: after a blow-out the
    driver primes above the target before the in-place aspiration."""
    await self.head.pick_up_tips(self.rack, column=0)
    await self.head.blow_out()
    await self.head.aspirate(self.plate, column=0, volume=10)

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    self.assertEqual(cmd_types.count("aspirateInPlace"), 1)
    self.assertIn("prepareToAspirate", cmd_types)

  async def test_prepare_to_aspirate_sends_one_command_carrying_only_the_pipette(self):
    await self.head.pick_up_tips(self.rack, column=0)
    await self.head.prepare_to_aspirate()

    prepares = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "prepareToAspirate"
    ]
    self.assertEqual(len(prepares), 1)
    self.assertEqual(prepares[0].args[2], {"pipetteId": self.head.pipette_id})

  async def test_prepare_to_aspirate_without_a_tip_raises_before_the_wire(self):
    n_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.prepare_to_aspirate()
    self.assertEqual(self.api.submit_command.await_count, n_before)


class TestFlexHead8PickupOrigin(unittest.IsolatedAsyncioTestCase):
  """Tip-pickup offsets must use wellLocation.origin == 'top',
  not the 'bottom' origin used for aspirate/dispense."""

  async def test_pick_up_tips_offset_uses_top_origin(self):
    flex, api, head = await _flex_head8(self)
    rack = await _rack(flex)

    await head.pick_up_tips(rack, column=0, offset=Coordinate(x=0, y=0, z=1))

    pickup_cmds = [c for c in api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1)
    self.assertEqual(pickup_cmds[0].args[2]["wellLocation"]["origin"], "top")

  async def test_aspirate_offset_still_uses_bottom_origin(self):
    flex, api, head = await _flex_head8(self)
    rack = await _rack(flex)
    plate = await _plate(flex)
    await plate.set_well_volumes(100.0)

    await head.pick_up_tips(rack, column=0)
    await head.aspirate(plate, column=0, volume=10, offset=Coordinate(x=0, y=0, z=1))

    location = await pipetting_location(api, plate.get_well("A1"))
    self.assertEqual(location["offset"]["z"], 2.0)


class TestFlexHead8TransactionalTrackers(unittest.IsolatedAsyncioTestCase):
  """Infeasible liquid operations must raise BEFORE any wire
  command is sent, and must not leave volumes changed."""

  async def test_infeasible_aspirate_raises_before_wire_command_and_leaves_trackers_unchanged(self):
    flex, api, head = await _flex_head8(self)
    rack = await _rack(flex)
    plate = await _plate(flex)

    # Column 0 wells are left at 0uL -- aspirating 50uL is infeasible.
    await head.pick_up_tips(rack, column=0)

    with self.assertRaises(TooLittleLiquidError):
      await head.aspirate(plate, column=0, volume=50)

    aspirate_cmds = [
      c for c in api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 0, "no aspirate wire command may be sent")

    for well in plate.items[0:8]:
      self.assertAlmostEqual(await _volume(well), 0.0)
      self.assertAlmostEqual(await _used(well), 0.0)


class TestFlexHead8DoublePickupGuard(unittest.IsolatedAsyncioTestCase):
  """Picking up onto an already-occupied channel must raise
  OpentronsError rather than silently overwrite head state."""

  async def test_pick_up_tips_onto_occupied_channels_raises(self):
    flex, api, head = await _flex_head8(self)
    rack = await _rack(flex)

    await head.pick_up_tips(rack, column=0)
    with self.assertRaises(OpentronsError):
      await head.pick_up_tips(rack, column=1)

    pickup_cmds = [c for c in api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1, "the second (invalid) pickup must not reach the wire")

  async def test_pick_up_single_tip_onto_occupied_channel_raises(self):
    flex, api, head = await _flex_head8(self)
    rack = await _rack(flex)

    await head.pick_up_single_tip(rack, well="A1", primary_nozzle="H1")
    with self.assertRaises(OpentronsError):
      # Same anchor, so the same channel, whatever row the well is in.
      await head.pick_up_single_tip(rack, well="A2", primary_nozzle="H1")


class TestFlexHead8EnsureAllModeReset(unittest.IsolatedAsyncioTestCase):
  """Column pickup resets the nozzle layout to ALL after a single tip is cleared."""

  async def test_column_op_after_single_pickup_resets_nozzle_layout(self):
    flex, api, head = await _flex_head8(self)
    rack = await _rack(flex)

    await head.pick_up_single_tip(rack, well="A1")
    # Clear the mounted tip so the occupied-channel guard allows us to
    # exercise the nozzle-layout reset.
    await head.shafts.discard((await head.shafts.mounted()).held)
    self.assertEqual(head._nozzle_layout, "SINGLE")

    await head.pick_up_tips(rack, column=1)

    cmd_types = [c.args[1] for c in api.submit_command.await_args_list]
    configure_indices = [i for i, t in enumerate(cmd_types) if t == "configureNozzleLayout"]
    pickup_indices = [i for i, t in enumerate(cmd_types) if t == "pickUpTip"]
    # The reset configureNozzleLayout (the one before the column pickUpTip)
    # must come before that pickUpTip.
    self.assertGreater(len(configure_indices), 1)
    self.assertLess(configure_indices[-1], pickup_indices[-1])
    self.assertEqual(
      api.submit_command.await_args_list[configure_indices[-1]].args[2]["configurationParams"][
        "style"
      ],
      "ALL",
    )


class TestFlexHead8SingleOpFlowRateAndNoneSkip(unittest.IsolatedAsyncioTestCase):
  """Single-tip liquid operations accept a flow_rate override,
  and a partially-filled column pickup leaves missing-tip
  channels' wells untouched (None-skip) on a later column aspirate."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8(self)

  async def test_aspirate_single_and_dispense_single_accept_flow_rate_override(self):
    rack = await _rack(self.flex)
    plate = await _plate(self.flex)

    await self.head.pick_up_single_tip(rack, well="A1", primary_nozzle="H1")
    await _set_tip_volumes(self.head, 20)
    await self.head.dispense_single(plate, well="A1", volume=20, flow_rate=99.0)
    await self.head.aspirate_single(plate, well="A1", volume=20, flow_rate=88.0)

    dispense_cmd = next(
      c for c in self.api.submit_command.await_args_list if c.args[1] == "dispenseInPlace"
    )
    aspirate_cmd = next(
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    )
    self.assertEqual(dispense_cmd.args[2]["flowRate"], 99.0)
    self.assertEqual(aspirate_cmd.args[2]["flowRate"], 88.0)

  async def test_partially_filled_column_pickup_skips_missing_tip_wells_on_aspirate(self):
    rack = await _rack(self.flex)
    plate = await _plate(self.flex)

    # Empty out channels B (index 1) and G (index 6) of column 0 before pickup.
    column_0_spots = rack.items[0:8]
    await _take_tips([column_0_spots[1], column_0_spots[6]])

    await plate.set_well_volumes(100.0)

    await self.head.pick_up_tips(rack, column=0)
    tips = await self.head.get_mounted_tips()
    self.assertIsNone(tips[1])
    self.assertIsNone(tips[6])

    await self.head.aspirate(plate, column=0, volume=20)

    wells = plate.items[0:8]
    for i, well in enumerate(wells):
      expected = 100.0 if i in (1, 6) else 80.0
      self.assertAlmostEqual(await _volume(well), expected, msg=f"channel {i}")


class TestFlexHead8HardwareTipPresence(unittest.IsolatedAsyncioTestCase):
  """The getTipPresence command verifies pickup seating and tip clearance."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8(self)

  async def test_has_tip_on_hardware_true_after_successful_pickup(self):
    self.api.get_command.return_value.result["status"] = "present"
    rack = await _rack(self.flex)

    await self.head.pick_up_tips(rack, column=0)

    self.assertTrue(await self.head.has_tip_on_hardware())

  async def test_reported_failed_pickup_raises_and_leaves_no_tracker_mutation(self):
    self.api.get_command.return_value.result["status"] = "absent"
    rack = await _rack(self.flex)

    with self.assertRaises(OpentronsError):
      await self.head.pick_up_tips(rack, column=0)

    # The pickUpTip wire command WAS sent (the sensor is what caught the
    # failure, not a pre-wire guard) -- but nothing downstream persisted.
    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1)

    for spot in rack.items[0:8]:
      self.assertTrue(await _has_tip(spot), msg=f"{spot.name} pickup must not have been committed")

    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  async def test_reported_failed_pickup_single_tip_raises_and_leaves_no_tracker_mutation(self):
    self.api.get_command.return_value.result["status"] = "absent"
    rack = await _rack(self.flex)

    with self.assertRaises(OpentronsError):
      await self.head.pick_up_single_tip(rack, well="A1", primary_nozzle="H1")

    self.assertTrue(await rack.get_tip_spot("A1").has_tip())
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  async def test_has_tip_on_hardware_false_after_drop_tips(self):
    rack = await _rack(self.flex)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.drop_tips(rack, column=0)

    self.api.get_command.return_value.result["status"] = "absent"
    self.assertFalse(await self.head.has_tip_on_hardware())

  async def test_has_tip_on_hardware_false_after_discard_tips(self):
    rack = await _rack(self.flex)
    trash = await get_trash_area(self.flex.deck)

    await self.head.pick_up_tips(rack, column=0)
    await self.head.discard_tips(trash)

    self.api.get_command.return_value.result["status"] = "absent"
    self.assertFalse(await self.head.has_tip_on_hardware())

  async def test_tip_presence_is_read_as_a_run_command_never_over_the_instruments_route(self):
    """The tip check must not touch ``GET /instruments`` once a run is live.

    That REST read re-caches the attached pipettes, which clears the run's
    record of the attached tip, so the next pipetting command fails with
    "cannot perform PREPARE_ASPIRATE without a tip attached". Reproduced
    against the Opentrons robot-server simulator.
    """
    rack = await _rack(self.flex)
    with patch.object(self.flex._api, "get_instruments", new_callable=AsyncMock) as get_instruments:
      await self.head.pick_up_tips(rack, column=0)
      await self.head.drop_tips(rack, column=0)

    get_instruments.assert_not_awaited()
    self.assertIn("getTipPresence", [c.args[1] for c in self.api.submit_command.await_args_list])

  async def test_reported_stuck_tip_after_drop_logs_warning(self):
    self.api.get_command.return_value.result["status"] = "present"
    rack = await _rack(self.flex)

    await self.head.pick_up_tips(rack, column=0)
    with self.assertLogs("pylabrobot.opentrons.flex.flex_head", level="WARNING") as log_ctx:
      await self.head.drop_tips(rack, column=0)

    self.assertTrue(any("stuck" in msg.lower() or "clear" in msg.lower() for msg in log_ctx.output))
    # The drop still commits -- the confirm step only warns, never raises.
    for spot in rack.items[0:8]:
      self.assertTrue(await _has_tip(spot))
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))


async def _flex_head1(
  test_case: unittest.IsolatedAsyncioTestCase, **api_kwargs
) -> Tuple[Flex, AsyncMock, FlexHead1]:
  """Build a Flex with fixed API replies and return its mock for assertions."""
  flex, api = await _flex_with_api(
    test_case, [("p1000_single_flex", 1, 1.0, 1000.0, "right")], **api_kwargs
  )
  await flex.setup()
  head = flex.right
  assert isinstance(head, FlexHead1)
  return flex, api, head


async def _flex_head96(
  test_case: unittest.IsolatedAsyncioTestCase, **api_kwargs
) -> Tuple[Flex, AsyncMock, FlexHead96]:
  """Build a Flex with fixed API replies and return its mock for assertions."""
  flex, api = await _flex_with_api(test_case, [("p1000_96", 96, 1.0, 1000.0, "left")], **api_kwargs)
  await flex.setup()
  head = flex.head96
  assert isinstance(head, FlexHead96)
  return flex, api, head


class TestFlexHead1Ops(unittest.IsolatedAsyncioTestCase):
  """FlexHead1 (single-channel, well-addressed) reuses the FlexHead8
  transactional stage -> wire -> verify -> commit/rollback flow and hardware
  tip-presence machinery, addressing exactly one well/tip spot per command
  instead of a whole column.
  """

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head1(self)

  async def test_pick_up_tips_and_aspirate_emit_one_command_each(self):
    rack = await _rack(self.flex, "rack1")
    plate = await _plate(self.flex, "plate1")

    target_well = plate.get_well("B3")
    await target_well.set_volume(100.0)

    await self.head.pick_up_tips(rack.get_tip_spot("A1"))

    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1)
    self.assertEqual(pickup_cmds[0].args[2]["wellName"], "A1")
    self.assertIsNotNone((await self.head.get_mounted_tips())[0])
    self.assertEqual(len(await self.head.get_mounted_tips()), 1)

    await self.head.aspirate(target_well, volume=10)

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    aspirate_indices = [i for i, t in enumerate(cmd_types) if t == "aspirateInPlace"]
    self.assertEqual(len(aspirate_indices), 1)
    self.assertIn("prepareToAspirate", cmd_types, "the driver primes before descent")
    self.assertNotIn(
      "wellName", self.api.submit_command.await_args_list[aspirate_indices[0]].args[2]
    )

    # Exactly 1 well booked -- every other well on the plate is untouched.
    for well in plate.items:
      expected = 90.0 if well.name == target_well.name else 0.0
      self.assertAlmostEqual(await _volume(well), expected, msg=well.name)

  async def test_double_pickup_onto_occupied_channel_raises(self):
    rack = await _rack(self.flex, "rack1")

    await self.head.pick_up_tips(rack.get_tip_spot("A1"))
    with self.assertRaises(OpentronsError):
      await self.head.pick_up_tips(rack.get_tip_spot("A2"))

    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1, "the second (invalid) pickup must not reach the wire")

  async def test_reported_failed_pickup_raises_and_leaves_no_tracker_mutation(self):
    self.api.get_command.return_value.result["status"] = "absent"
    rack = await _rack(self.flex, "rack1")

    with self.assertRaises(OpentronsError):
      await self.head.pick_up_tips(rack.get_tip_spot("A1"))

    # The pickUpTip wire command WAS sent (the sensor is what caught the
    # failure, not a pre-wire guard) -- but nothing downstream persisted.
    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1)
    self.assertTrue(await rack.get_tip_spot("A1").has_tip(), "pickup must not have been committed")
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  async def test_drop_tips_to_rack_and_discard_to_trash(self):
    rack = await _rack(self.flex, "rack1")
    trash = await get_trash_area(self.flex.deck)

    await self.head.pick_up_tips(rack.get_tip_spot("A1"))
    await self.head.drop_tips(rack.get_tip_spot("A1"))
    self.assertTrue(await rack.get_tip_spot("A1").has_tip())
    self.assertIsNone((await self.head.get_mounted_tips())[0])

    await self.head.pick_up_tips(rack.get_tip_spot("A2"))
    await self.head.discard_tips(trash)
    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    self.assertIn("moveToAddressableAreaForDropTip", cmd_types)
    self.assertIn("dropTipInPlace", cmd_types)
    self.assertIsNone((await self.head.get_mounted_tips())[0])

  def test_docstring_does_not_claim_hardware_validation(self):
    doc = FlexHead1.__doc__ or ""
    self.assertNotIn("Validated on real", doc)


class TestFlexHead96Ops(unittest.IsolatedAsyncioTestCase):
  """FlexHead96 (96 fixed nozzles, whole-plate-addressed) reuses the
  FlexHead8 transactional stage -> wire -> verify -> commit/rollback flow and
  hardware tip-presence machinery, fanning ONE command out to all 96
  channels anchored at well "A1".
  """

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head96(self)

  async def test_pick_up_tips_configures_all_nozzles_and_picks_at_a1(self):
    rack = await _rack(self.flex, "rack96")

    await self.head.pick_up_tips(rack)

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    configure_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "configureNozzleLayout"
    ]
    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(configure_cmds), 1)
    self.assertEqual(configure_cmds[0].args[2]["configurationParams"]["style"], "ALL")
    self.assertEqual(len(pickup_cmds), 1)
    self.assertEqual(pickup_cmds[0].args[2]["wellName"], "A1")
    self.assertLess(cmd_types.index("configureNozzleLayout"), cmd_types.index("pickUpTip"))

    tips = await self.head.get_mounted_tips()
    self.assertEqual(len(tips), 96)
    self.assertTrue(all(t is not None for t in tips))
    for spot in rack.items:
      self.assertFalse(await _has_tip(spot))

  async def test_aspirate_emits_one_command_and_tracks_all_96_wells(self):
    rack = await _rack(self.flex, "rack96")
    plate = await _plate(self.flex, "plate96")
    await plate.set_well_volumes(100.0)

    await self.head.pick_up_tips(rack)
    await self.head.aspirate(plate, volume=50)

    cmd_types = [c.args[1] for c in self.api.submit_command.await_args_list]
    aspirate_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "aspirateInPlace"
    ]
    self.assertEqual(len(aspirate_cmds), 1)
    self.assertNotIn("wellName", aspirate_cmds[0].args[2])
    self.assertIn("prepareToAspirate", cmd_types, "the driver primes before descent")

    wells = plate.items
    self.assertEqual(len(wells), 96)
    for well in wells:
      self.assertAlmostEqual(await _volume(well), 50.0, msg=well.name)

  async def test_dispense_and_drop_tips_round_trip(self):
    rack = await _rack(self.flex, "rack96")
    plate = await _plate(self.flex, "plate96")

    await self.head.pick_up_tips(rack)
    await _set_tip_volumes(self.head, 30)
    await self.head.dispense(plate, volume=30)

    dispense_cmds = [
      c for c in self.api.submit_command.await_args_list if c.args[1] == "dispenseInPlace"
    ]
    self.assertEqual(len(dispense_cmds), 1)
    self.assertNotIn("wellName", dispense_cmds[0].args[2])
    for well in plate.items:
      self.assertAlmostEqual(await _volume(well), 30.0, msg=well.name)

    await self.head.drop_tips(rack)
    drop_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "dropTip"]
    self.assertEqual(len(drop_cmds), 1)
    self.assertEqual(drop_cmds[0].args[2]["wellName"], "A1")
    for spot in rack.items:
      self.assertTrue(await _has_tip(spot))
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  async def test_reported_failed_pickup_raises_and_leaves_no_tracker_mutation(self):
    self.api.get_command.return_value.result["status"] = "absent"
    rack = await _rack(self.flex, "rack96")

    with self.assertRaises(OpentronsError):
      await self.head.pick_up_tips(rack)

    # The pickUpTip wire command WAS sent (the sensor is what caught the
    # failure, not a pre-wire guard) -- but nothing downstream persisted.
    pickup_cmds = [c for c in self.api.submit_command.await_args_list if c.args[1] == "pickUpTip"]
    self.assertEqual(len(pickup_cmds), 1)
    for spot in rack.items:
      self.assertTrue(await _has_tip(spot), msg=f"{spot.name} pickup must not have been committed")
    self.assertTrue(all(t is None for t in await self.head.get_mounted_tips()))

  def test_docstring_does_not_claim_hardware_validation(self):
    doc = FlexHead96.__doc__ or ""
    self.assertNotIn("Validated on real", doc)


class TrashAddressableAreaTests(unittest.IsolatedAsyncioTestCase):
  """A Flex takes a movable trash in any of eight slots, not just A3."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8(self)

  async def _move_trash(self, slot: Union[str, int]) -> handles.Trash:
    trash = await get_trash_area(self.flex.deck)
    await unassign_child_at_slot(self.flex.deck, "A3")
    await assign_child_at_slot(self.flex.deck, trash, slot)
    return trash

  async def test_the_drop_follows_the_trash_to_another_slot(self):
    rack = await _rack(self.flex)
    trash = await self._move_trash("B3")

    await self.head.pick_up_tips(rack, column=0)
    await self.head.discard_tips(trash)

    move_cmd = next(
      c
      for c in self.api.submit_command.await_args_list
      if c.args[1] == "moveToAddressableAreaForDropTip"
    )
    self.assertEqual(move_cmd.args[2]["addressableAreaName"], "movableTrashB3")

  async def test_a_trash_outside_a_trash_slot_is_refused(self):
    trash = await self._move_trash("C2")
    with self.assertRaises(OpentronsError):
      await self.head._trash_addressable_area(trash)


if __name__ == "__main__":
  unittest.main()
