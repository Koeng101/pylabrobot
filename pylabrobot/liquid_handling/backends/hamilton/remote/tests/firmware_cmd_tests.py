"""Firmware command verification tests for the remote STAR backend.

These tests verify that the full pipeline (client serialize -> RPC -> server
deserialize -> backend) produces identical firmware commands to a local
STARBackend, by comparing against the expected command strings from STAR_tests.py.
"""

import re
import unittest.mock
from typing import Literal, cast

import pytest

from pylabrobot.liquid_handling.standard import (
  Drop,
  DropTipRack,
  GripDirection,
  MultiHeadAspirationPlate,
  MultiHeadDispensePlate,
  Pickup,
  PickupTipRack,
  ResourceDrop,
  ResourceMove,
  ResourcePickup,
  SingleChannelAspiration,
  SingleChannelDispense,
)
from pylabrobot.plate_reading import PlateReader
from pylabrobot.plate_reading.chatterbox import PlateReaderChatterboxBackend
from pylabrobot.resources import (
  Coordinate,
  Lid,
  Resource,
  ResourceStack,
  Rotation,
  TIP_CAR_288_C00,
  hamilton_96_tiprack_1000uL,
  no_volume_tracking,
  set_tip_tracking,
)
from pylabrobot.liquid_handling.utils import (
  get_tight_single_resource_liquid_op_offsets,
  get_wide_single_resource_liquid_op_offsets,
)
from pylabrobot.resources.greiner import Greiner_384_wellplate_28ul_Fb
from pylabrobot.resources.plate import Plate

from .conftest import StarServiceFixture


def _any_write_and_read_command_call(cmd):
  return unittest.mock.call(
    id_=unittest.mock.ANY,
    cmd=cmd,
    write_timeout=unittest.mock.ANY,
    read_timeout=unittest.mock.ANY,
    wait=unittest.mock.ANY,
  )


def _reset_backend_state(backend):
  """Reset backend state for deterministic command generation."""
  backend.id_ = 0
  backend._tth2tti.clear()
  backend._write_and_read_command.reset_mock()
  backend._write_and_read_command.return_value = None
  backend._write_and_read_command.side_effect = None
  backend._iswap_parked = True
  backend._core_parked = True


# ---------------------------------------------------------------------------
# Helpers for iSwap / CoRe gripper tests
# ---------------------------------------------------------------------------

def _compute_rotation_applied(pickup_dir, drop_dir):
  """Return rotation in degrees applied by moving from pickup_dir to drop_dir."""
  if pickup_dir == drop_dir:
    return 0
  _lookup = {
    (GripDirection.FRONT, GripDirection.RIGHT): 90,
    (GripDirection.RIGHT, GripDirection.BACK): 90,
    (GripDirection.BACK, GripDirection.LEFT): 90,
    (GripDirection.LEFT, GripDirection.FRONT): 90,
    (GripDirection.FRONT, GripDirection.BACK): 180,
    (GripDirection.BACK, GripDirection.FRONT): 180,
    (GripDirection.LEFT, GripDirection.RIGHT): 180,
    (GripDirection.RIGHT, GripDirection.LEFT): 180,
    (GripDirection.RIGHT, GripDirection.FRONT): 270,
    (GripDirection.BACK, GripDirection.RIGHT): 270,
    (GripDirection.LEFT, GripDirection.BACK): 270,
    (GripDirection.FRONT, GripDirection.LEFT): 270,
  }
  return _lookup[(pickup_dir, drop_dir)]


def _build_resource_drop(
  deck, resource, destination,
  pickup_distance_from_top,
  pickup_direction=GripDirection.FRONT,
  drop_direction=GripDirection.FRONT,
):
  """Build a ResourceDrop matching LiquidHandler.drop_resource logic."""
  rotation = _compute_rotation_applied(pickup_direction, drop_direction)
  abs_rot_z_after = resource.get_absolute_rotation().z + rotation
  dest_rot_z = destination.get_absolute_rotation().z if isinstance(destination, Resource) else 0
  rot_wrt_dest = abs_rot_z_after - dest_rot_z
  rot_wrt_dest_wrt_local = rot_wrt_dest - resource.rotation.z

  if isinstance(destination, ResourceStack):
    child_loc = destination.get_new_child_location(
      resource.rotated(z=rot_wrt_dest_wrt_local)
    ).rotated(destination.get_absolute_rotation())
    to_location = destination.get_location_wrt(deck) + child_loc
  elif isinstance(destination, Plate) and isinstance(resource, Lid):
    child_loc = destination.get_lid_location(
      resource.rotated(z=rot_wrt_dest_wrt_local)
    ).rotated(destination.get_absolute_rotation())
    to_location = destination.get_location_wrt(deck) + child_loc
  elif hasattr(destination, "get_default_child_location"):
    child_loc = destination.get_default_child_location(
      resource.rotated(z=rot_wrt_dest_wrt_local)
    ).rotated(destination.get_absolute_rotation())
    to_location = destination.get_location_wrt(deck) + child_loc
  else:
    to_location = destination.get_location_wrt(deck)

  dest_abs_rot = (
    destination.get_absolute_rotation()
    if isinstance(destination, Resource)
    else Rotation(0, 0, 0)
  )

  return ResourceDrop(
    resource=resource,
    destination=to_location,
    destination_absolute_rotation=dest_abs_rot,
    offset=Coordinate.zero(),
    pickup_distance_from_top=pickup_distance_from_top,
    pickup_direction=pickup_direction,
    direction=drop_direction,
    rotation=rotation,
  )


def _do_move_on_deck(resource, destination, pickup_direction, drop_direction):
  """Update deck state after a move, like LiquidHandler would."""
  rotation = _compute_rotation_applied(pickup_direction, drop_direction)
  abs_rot_z_after = resource.get_absolute_rotation().z + rotation
  dest_rot_z = destination.get_absolute_rotation().z if isinstance(destination, Resource) else 0
  rot_wrt_dest = abs_rot_z_after - dest_rot_z
  resource.rotate(z=rot_wrt_dest - resource.rotation.z)
  resource.unassign()
  if isinstance(destination, ResourceStack):
    destination.assign_child_resource(resource)
  elif isinstance(destination, Plate) and isinstance(resource, Lid):
    destination.assign_child_resource(resource)
  elif hasattr(destination, "assign_child_resource"):
    destination.assign_child_resource(resource)


def _get_tp_tz_from_calls(backend, cmd_prefix: str):
  """Extract tp and tz values from mock calls matching the command prefix."""
  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import parse_star_fw_string
  for call in backend._write_and_read_command.call_args_list:
    cmd = call.kwargs.get("cmd", "")
    if cmd.startswith(cmd_prefix):
      parsed = parse_star_fw_string(cmd, "tp####tz####")
      return parsed.get("tp"), parsed.get("tz")
  return None, None


# =============================================================================
# Tip handling tests
# =============================================================================

class TestFirmwareCmdTipHandling:
  @pytest.mark.asyncio
  async def test_pick_up_tips_a1_b1(self, star_service: StarServiceFixture):
    """Pick up tips from A1+B1 on channels 0+1. Mirrors STAR_tests.py test_tip_pickup_01."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    spots = [tip_rack.get_item("A1"), tip_rack.get_item("B1")]
    ops = [Pickup(resource=s, offset=Coordinate.zero(), tip=s.get_tip()) for s in spots]
    await star_service.remote.pick_up_tips(ops=ops, use_channels=[0, 1])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0TTid0001tt01tf1tl0519tv03600tg2tu0",
      ),
      _any_write_and_read_command_call(
        "C0TPid0002xp01179 01179 00000&yp2418 2328 0000&tm1 1 0&tt01tp2244tz2164th2450td0",
      ),
    ])

  @pytest.mark.asyncio
  async def test_pick_up_tips_e1_f1_channels_45(self, star_service: StarServiceFixture):
    """Pick up from E1+F1 on channels 4+5. Mirrors STAR_tests.py test_tip_pickup_56."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    spots = [tip_rack.get_item("E1"), tip_rack.get_item("F1")]
    ops = [Pickup(resource=s, offset=Coordinate.zero(), tip=s.get_tip()) for s in spots]
    await star_service.remote.pick_up_tips(ops=ops, use_channels=[4, 5])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0TTid0001tt01tf1tl0519tv03600tg2tu0",
      ),
      _any_write_and_read_command_call(
        "C0TPid0002xp00000 00000 00000 00000 01179 01179 00000&"
        "yp0000 0000 0000 0000 2058 1968 0000&"
        "tm0 0 0 0 1 1 0&tt01tp2244tz2164th2450td0",
      ),
    ])

  @pytest.mark.asyncio
  async def test_drop_tips_e1_f1_channels_45(self, star_service: StarServiceFixture):
    """Drop tips at E1+F1 on channels 4+5. Mirrors STAR_tests.py test_tip_drop_56."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")

    # First pick up tips (to advance id_ counter like STAR_tests.py)
    spots = [tip_rack.get_item("E1"), tip_rack.get_item("F1")]
    pickup_ops = [Pickup(resource=s, offset=Coordinate.zero(), tip=s.get_tip()) for s in spots]
    await star_service.remote.pick_up_tips(ops=pickup_ops, use_channels=[4, 5])

    # Reset mock, set side_effect for drop_tips response parsing
    star_service.backend._write_and_read_command.reset_mock()
    star_service.backend._write_and_read_command.side_effect = [
      "C0TRid0003kz000 000 000 000 000 000 000 000vz000 000 000 000 000 000 000 000"
    ]

    drop_ops = [Drop(resource=s, offset=Coordinate.zero(), tip=s.get_tip()) for s in spots]
    await star_service.remote.drop_tips(ops=drop_ops, use_channels=[4, 5])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0TRid0003xp00000 00000 00000 00000 01179 01179 00000&"
        "yp0000 0000 0000 0000 2058 1968 "
        "0000&tm0 0 0 0 1 1 0&tp2244tz2164th2450te2450ti1",
      ),
    ])


# =============================================================================
# Aspirate / Dispense tests
# =============================================================================

class TestFirmwareCmdAspirateDispense:
  @pytest.mark.asyncio
  async def test_aspirate_single_channel(self, star_service: StarServiceFixture):
    """Aspirate 100uL from plate_01 A1 on channel 0. Mirrors test_single_channel_aspiration."""
    _reset_backend_state(star_service.backend)
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [SingleChannelAspiration(
      resource=well,
      offset=Coordinate.zero(),
      tip=tip,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )]
    await star_service.remote.aspirate(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0ASid0001at0 0&tm1 0&xp02983 00000&yp1457 0000&th2450te2450lp2000 2000&ch000 000&zl1866 "
        "1866&po0100 0100&zu0032 0032&zr06180 06180&zx1866 1866&ip0000 0000&it0 0&fp0000 0000&"
        "av01072 01072&as1000 1000&ta000 000&ba0000 0000&oa000 000&lm0 0&ll1 1&lv1 1&zo000 000&"
        "ld00 00&de0020 0020&wt10 10&mv00000 00000&mc00 00&mp000 000&ms1000 1000&mh0000 0000&"
        "gi000 000&gj0gk0lk0 0&ik0000 0000&sd0500 0500&se0500 0500&sz0300 0300&io0000 0000&",
      ),
    ])

  @pytest.mark.asyncio
  async def test_aspirate_liquid_height(self, star_service: StarServiceFixture):
    """Aspirate with liquid_height=10. Mirrors test_single_channel_aspiration_liquid_height."""
    _reset_backend_state(star_service.backend)
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [SingleChannelAspiration(
      resource=well,
      offset=Coordinate.zero(),
      tip=tip,
      volume=100.0,
      flow_rate=None,
      liquid_height=10.0,
      blow_out_air_volume=None,
      mix=None,
    )]
    await star_service.remote.aspirate(ops=ops, use_channels=[0])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0ASid0001at0 0&tm1 0&xp02983 00000&yp1457 0000&th2450te2450lp2000 2000&ch000 000&zl1966 "
        "1966&po0100 0100&zu0032 0032&zr06180 06180&zx1866 1866&ip0000 0000&it0 0&fp0000 0000&"
        "av01072 01072&as1000 1000&ta000 000&ba0000 0000&oa000 000&lm0 0&ll1 1&lv1 1&zo000 000&"
        "ld00 00&de0020 0020&wt10 10&mv00000 00000&mc00 00&mp000 000&ms1000 1000&mh0000 0000&"
        "gi000 000&gj0gk0lk0 0&ik0000 0000&sd0500 0500&se0500 0500&sz0300 0300&io0000 0000&",
      ),
    ])

  @pytest.mark.asyncio
  async def test_aspirate_multi_channel(self, star_service: StarServiceFixture):
    """3-ch aspirate from A1:B1 on ch 0+1. Mirrors test_multi_channel_aspiration."""
    _reset_backend_state(star_service.backend)
    plate = star_service.deck.get_resource("plate_01")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    wells = [plate.get_item("A1"), plate.get_item("B1")]
    tips = [tip_rack.get_item("A1").get_tip(), tip_rack.get_item("B1").get_tip()]
    ops = [SingleChannelAspiration(
      resource=w, offset=Coordinate.zero(), tip=t,
      volume=100.0, flow_rate=None, liquid_height=None,
      blow_out_air_volume=None, mix=None,
    ) for w, t in zip(wells, tips)]
    await star_service.remote.aspirate(ops=ops, use_channels=[0, 1])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0ASid0001at0 0 0&tm1 1 0&xp02983 02983 00000&yp1457 1367 0000&th2450te2450lp2000 2000 2000&"
        "ch000 000 000&zl1866 1866 1866&po0100 0100 0100&zu0032 0032 0032&zr06180 06180 06180&"
        "zx1866 1866 1866&ip0000 0000 0000&it0 0 0&fp0000 0000 0000&av01072 01072 01072&as1000 1000 "
        "1000&ta000 000 000&ba0000 0000 0000&oa000 000 000&lm0 0 0&ll1 1 1&lv1 1 1&zo000 000 000&"
        "ld00 00 00&de0020 0020 0020&wt10 10 10&mv00000 00000 00000&mc00 00 00&mp000 000 000&"
        "ms1000 1000 1000&mh0000 0000 0000&gi000 000 000&gj0gk0lk0 0 0&ik0000 0000 0000&sd0500 0500 "
        "0500&se0500 0500 0500&sz0300 0300 0300&io0000 0000 0000&",
      ),
    ])

  @pytest.mark.asyncio
  async def test_aspirate_multi_channel_45(self, star_service: StarServiceFixture):
    """7-ch aspirate on ch 4+5. Mirrors test_aspirate56."""
    _reset_backend_state(star_service.backend)
    plate = star_service.deck.get_resource("plate_01")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    wells = [plate.get_item("A1"), plate.get_item("B1")]
    tips = [tip_rack.get_item("E1").get_tip(), tip_rack.get_item("F1").get_tip()]
    ops = [SingleChannelAspiration(
      resource=w, offset=Coordinate.zero(), tip=t,
      volume=100.0, flow_rate=None, liquid_height=None,
      blow_out_air_volume=None, mix=None,
    ) for w, t in zip(wells, tips)]
    await star_service.remote.aspirate(ops=ops, use_channels=[4, 5])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0ASid0001at0 0 0 0 0 0 0&tm0 0 0 0 1 1 0&xp00000 00000 00000 "
        "00000 02983 02983 00000&yp0000 0000 0000 0000 1457 1367 0000&th2450te2450lp2000 2000 2000 "
        "2000 2000 2000 2000&ch000 000 000 000 000 000 000&zl1866 1866 1866 1866 1866 1866 1866&"
        "po0100 0100 0100 0100 0100 0100 0100&zu0032 0032 0032 0032 0032 0032 0032&zr06180 06180 "
        "06180 06180 06180 06180 06180&zx1866 1866 1866 1866 1866 1866 1866&ip0000 0000 0000 0000 "
        "0000 0000 0000&it0 0 0 0 0 0 0&fp0000 0000 0000 0000 0000 0000 0000&av01072 01072 01072 "
        "01072 01072 01072 01072&as1000 1000 1000 1000 1000 1000 1000&ta000 000 000 000 000 000 000&"
        "ba0000 0000 0000 0000 0000 0000 0000&oa000 000 000 000 000 000 000&lm0 0 0 0 0 0 0&ll1 1 1 "
        "1 1 1 1&lv1 1 1 1 1 1 1&zo000 000 000 000 000 000 000&ld00 00 00 00 00 00 00&de0020 0020 "
        "0020 0020 0020 0020 0020&wt10 10 10 10 10 10 10&mv00000 00000 00000 00000 00000 00000 00000&"
        "mc00 00 00 00 00 00 00&mp000 000 000 000 000 000 000&ms1000 1000 1000 1000 1000 1000 1000&"
        "mh0000 0000 0000 0000 0000 0000 0000&gi000 000 000 000 000 000 000&gj0gk0lk0 0 0 0 0 0 0&"
        "ik0000 0000 0000 0000 0000 0000 0000&sd0500 0500 0500 0500 0500 0500 0500&se0500 0500 0500 "
        "0500 0500 0500 0500&sz0300 0300 0300 0300 0300 0300 0300&io0000 0000 0000 0000 0000 0000 0"
        "000&",
      ),
    ])

  @pytest.mark.asyncio
  async def test_dispense_single_channel(self, star_service: StarServiceFixture):
    """Dispense 100uL to plate_01 A1 on channel 0. Mirrors test_single_channel_dispense."""
    _reset_backend_state(star_service.backend)
    plate = star_service.deck.get_resource("plate_01")
    well = plate.get_item("A1")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tip = tip_rack.get_item("A1").get_tip()
    ops = [SingleChannelDispense(
      resource=well,
      offset=Coordinate.zero(),
      tip=tip,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )]
    await star_service.remote.dispense(
      ops=ops, use_channels=[0], jet=[True], blow_out=[True],
    )
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0DSid0001dm1 1&tm1 0&xp02983 00000&yp1457 0000&zx1866 1866&lp2000 2000&zl1866 1866&"
        "po0100 0100&ip0000 0000&it0 0&fp0000 0000&zu0032 0032&zr06180 06180&th2450te2450"
        "dv01072 01072&ds1800 1800&ss0050 0050&rv000 000&ta050 050&ba0300 0300&lm0 0&dj00zo000 000&"
        "ll1 1&lv1 1&de0010 0010&wt00 00&mv00000 00000&mc00 00&mp000 000&ms0010 0010&mh0000 0000&"
        "gi000 000&gj0gk0",
      ),
    ])

  @pytest.mark.asyncio
  async def test_dispense_multi_channel(self, star_service: StarServiceFixture):
    """3-ch dispense to A1:B1 on ch 0+1. Mirrors test_multi_channel_dispense."""
    _reset_backend_state(star_service.backend)
    plate = star_service.deck.get_resource("plate_01")
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    wells = [plate.get_item("A1"), plate.get_item("B1")]
    tips = [tip_rack.get_item("A1").get_tip(), tip_rack.get_item("B1").get_tip()]
    ops = [SingleChannelDispense(
      resource=w, offset=Coordinate.zero(), tip=t,
      volume=100.0, flow_rate=None, liquid_height=None,
      blow_out_air_volume=None, mix=None,
    ) for w, t in zip(wells, tips)]
    await star_service.remote.dispense(
      ops=ops, use_channels=[0, 1], jet=[True, True], blow_out=[True, True],
    )
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0DSid0001dm1 1 1&tm1 1 0&xp02983 02983 00000&yp1457 1367 0000&zx1866 1866 1866&lp2000 2000 "
        "2000&zl1866 1866 1866&po0100 0100 0100&ip0000 0000 0000&it0 0 0&fp0000 0000 0000&zu0032 "
        "0032 0032&zr06180 06180 06180&th2450te2450dv01072 01072 01072&ds1800 1800 1800&"
        "ss0050 0050 0050&rv000 000 000&ta050 050 050&ba0300 0300 0300&lm0 0 0&dj00zo000 000 000&"
        "ll1 1 1&lv1 1 1&de0010 0010 0010&wt00 00 00&mv00000 00000 00000&mc00 00 00&mp000 000 000&"
        "ms0010 0010 0010&mh0000 0000 0000&gi000 000 000&gj0gk0",
      ),
    ])

  @pytest.mark.asyncio
  async def test_aspirate_single_resource(self, star_service: StarServiceFixture):
    """5-ch aspirate to BlueBucket. Mirrors test_aspirate_single_resource."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    bb = star_service.bb
    tips = [tip_rack.get_item(f"{chr(65+i)}1").get_tip() for i in range(5)]
    offsets = get_wide_single_resource_liquid_op_offsets(bb, num_channels=5)
    ops = [SingleChannelAspiration(
      resource=bb, offset=off, tip=t,
      volume=10.0, flow_rate=None, liquid_height=1.0,
      blow_out_air_volume=None, mix=None,
    ) for off, t in zip(offsets, tips)]
    await star_service.remote.aspirate(ops=ops, use_channels=[0, 1, 2, 3, 4])
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0ASid0001at0 0 0 0 0 0&tm1 1 1 1 1 0&xp04865 04865 04865 04865 04865 00000&yp2098 1962 "
        "1825 1688 1552 0000&th2450te2450lp2000 2000 2000 2000 2000 2000&ch000 000 000 000 000 000&"
        "zl1210 1210 1210 1210 1210 1210&po0100 0100 0100 0100 0100 0100&zu0032 0032 0032 0032 0032 "
        "0032&zr06180 06180 06180 06180 06180 06180&zx1200 1200 1200 1200 1200 1200&ip0000 0000 0000 "
        "0000 0000 0000&it0 0 0 0 0 0&fp0000 0000 0000 0000 0000 0000&av00119 00119 00119 00119 "
        "00119 00119&as1000 1000 1000 1000 1000 1000&ta000 000 000 000 000 000&ba0000 0000 0000 0000 "
        "0000 0000&oa000 000 000 000 000 000&lm0 0 0 0 0 0&ll1 1 1 1 1 1&lv1 1 1 1 1 1&zo000 000 000 "
        "000 000 000&ld00 00 00 00 00 00&de0020 0020 0020 0020 0020 0020&wt10 10 10 10 10 10&mv00000 "
        "00000 00000 00000 00000 00000&mc00 00 00 00 00 00&mp000 000 000 000 000 000&ms1000 1000 "
        "1000 1000 1000 1000&mh0000 0000 0000 0000 0000 0000&gi000 000 000 000 000 000&gj0gk0lk0 0 0 "
        "0 0 0&ik0000 0000 0000 0000 0000 0000&sd0500 0500 0500 0500 0500 0500&se0500 0500 0500 0500 "
        "0500 0500&sz0300 0300 0300 0300 0300 0300&io0000 0000 0000 0000 0000 0000&",
      ),
    ])

  @pytest.mark.asyncio
  async def test_dispense_single_resource(self, star_service: StarServiceFixture):
    """5-ch dispense to BlueBucket. Mirrors test_dispense_single_resource."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    bb = star_service.bb
    tips = [tip_rack.get_item(f"{chr(65+i)}1").get_tip() for i in range(5)]
    offsets = get_wide_single_resource_liquid_op_offsets(bb, num_channels=5)
    ops = [SingleChannelDispense(
      resource=bb, offset=off, tip=t,
      volume=10.0, flow_rate=None, liquid_height=1.0,
      blow_out_air_volume=None, mix=None,
    ) for off, t in zip(offsets, tips)]
    await star_service.remote.dispense(
      ops=ops, use_channels=[0, 1, 2, 3, 4],
      jet=[True] * 5, blow_out=[True] * 5,
    )
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0DSid0001dm1 1 1 1 1 1&tm1 1 1 1 1 0&xp04865 04865 04865 04865 04865 00000&yp2098 1962 "
        "1825 1688 1552 0000&zx1200 1200 1200 1200 1200 1200&lp2000 2000 2000 2000 2000 2000&zl1210 "
        "1210 1210 1210 1210 1210&po0100 0100 0100 0100 0100 0100&ip0000 0000 0000 0000 0000 0000&"
        "it0 0 0 0 0 0&fp0000 0000 0000 0000 0000 0000&zu0032 0032 0032 0032 0032 0032&zr06180 06180 "
        "06180 06180 06180 06180&th2450te2450dv00116 00116 00116 00116 00116 00116&ds1800 1800 1800 "
        "1800 1800 1800&ss0050 0050 0050 0050 0050 0050&rv000 000 000 000 000 000&ta050 050 050 050 "
        "050 050&ba0300 0300 0300 0300 0300 0300&lm0 0 0 0 0 0&dj00zo000 000 000 000 000 000&ll1 1 1 "
        "1 1 1&lv1 1 1 1 1 1&de0010 0010 0010 0010 0010 0010&wt00 00 00 00 00 00&mv00000 00000 00000 "
        "00000 00000 00000&mc00 00 00 00 00 00&mp000 000 000 000 000 000&ms0010 0010 0010 0010 0010 "
        "0010&mh0000 0000 0000 0000 0000 0000&gi000 000 000 000 000 000&gj0gk0",
      ),
    ])


# =============================================================================
# 96-head tests
# =============================================================================

class TestFirmwareCmd96Head:
  @pytest.mark.asyncio
  async def test_pick_up_tips96(self, star_service: StarServiceFixture):
    """96-head tip pickup from tip_rack_01. Mirrors test_core_96_tip_pickup."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")
    tips_96 = []
    for row in "ABCDEFGH":
      for col in range(1, 13):
        tips_96.append(tip_rack.get_item(f"{row}{col}").get_tip())
    pickup = PickupTipRack(resource=tip_rack, offset=Coordinate.zero(), tips=tips_96)
    await star_service.remote.pick_up_tips96(pickup=pickup)
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call("C0TTid0001tt01tf1tl0519tv03600tg2tu0"),
      _any_write_and_read_command_call("H0DQid0002dq11281dv13500du00000dr900000dw15"),
      _any_write_and_read_command_call("C0EPid0003xs01179xd0yh2418tt01wu0za2164zh2450ze2450"),
    ])

  @pytest.mark.asyncio
  async def test_drop_tips96(self, star_service: StarServiceFixture):
    """96-head tip drop to tip_rack_01. Mirrors test_core_96_tip_drop."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")

    # Pick up first (to advance id_ counter)
    tips_96 = []
    for row in "ABCDEFGH":
      for col in range(1, 13):
        tips_96.append(tip_rack.get_item(f"{row}{col}").get_tip())
    pickup = PickupTipRack(resource=tip_rack, offset=Coordinate.zero(), tips=tips_96)
    await star_service.remote.pick_up_tips96(pickup=pickup)

    star_service.backend._write_and_read_command.reset_mock()
    drop = DropTipRack(resource=tip_rack, offset=Coordinate.zero())
    await star_service.remote.drop_tips96(drop=drop)
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call("C0ERid0004xs01179xd0yh2418za2164zh2450ze2450"),
    ])

  @pytest.mark.asyncio
  async def test_core_96_tip_discard(self, star_service: StarServiceFixture):
    """96-head discard to waste. Mirrors test_core_96_tip_discard."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")

    # Pick up tips first
    tips_96 = []
    for row in "ABCDEFGH":
      for col in range(1, 13):
        tips_96.append(tip_rack.get_item(f"{row}{col}").get_tip())
    pickup = PickupTipRack(resource=tip_rack, offset=Coordinate.zero(), tips=tips_96)
    await star_service.remote.pick_up_tips96(pickup=pickup)

    star_service.backend._write_and_read_command.reset_mock()
    # discard_tips96 drops to waste — pass z-values matching 300uL filter tips
    await star_service.remote.discard_tips_core96(
      x_position=420, x_direction=1, y_position=1203,
      z_deposit_position=2164,
      minimum_traverse_height_at_beginning_of_a_command=2450,
      minimum_height_command_end=2450,
    )
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call("C0ERid0004xs00420xd1yh1203za2164zh2450ze2450"),
    ])

  @pytest.mark.asyncio
  async def test_aspirate96(self, star_service: StarServiceFixture):
    """96-head aspirate 100uL from plate_01. Mirrors test_core_96_aspirate."""
    _reset_backend_state(star_service.backend)
    tip_rack2 = star_service.deck.get_resource("tip_rack_02")

    # Pick up high volume tips first
    tips_96 = []
    for row in "ABCDEFGH":
      for col in range(1, 13):
        tips_96.append(tip_rack2.get_item(f"{row}{col}").get_tip())
    pickup = PickupTipRack(resource=tip_rack2, offset=Coordinate.zero(), tips=tips_96)
    await star_service.remote.pick_up_tips96(pickup=pickup)
    star_service.backend._write_and_read_command.reset_mock()

    plate = star_service.deck.get_resource("plate_01")
    wells = [plate.get_item(f"{chr(65 + r)}{c + 1}") for r in range(8) for c in range(12)]
    aspiration = MultiHeadAspirationPlate(
      wells=wells,
      offset=Coordinate.zero(),
      tips=tips_96,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    await star_service.remote.aspirate96(aspiration=aspiration, blow_out=True)
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0EAid0004aa0xs02983xd0yh1457zh2450ze2450lz1999zt1866pp0100zm1866zv0032zq06180"
        "iw000ix0fh000af01083ag2500vt050bv00000wv00050cm0cs1bs0020wh10hv00000hc00hp000mj000"
        "hs1200cwFFFFFFFFFFFFFFFFFFFFFFFFcr000cj0cx0"
      ),
    ])

  @pytest.mark.asyncio
  async def test_dispense96(self, star_service: StarServiceFixture):
    """96-head dispense 100uL to plate_01. Mirrors test_core_96_dispense."""
    _reset_backend_state(star_service.backend)
    tip_rack2 = star_service.deck.get_resource("tip_rack_02")
    plate = star_service.deck.get_resource("plate_01")

    # Pick up high volume tips
    tips_96 = []
    for row in "ABCDEFGH":
      for col in range(1, 13):
        tips_96.append(tip_rack2.get_item(f"{row}{col}").get_tip())
    pickup = PickupTipRack(resource=tip_rack2, offset=Coordinate.zero(), tips=tips_96)
    await star_service.remote.pick_up_tips96(pickup=pickup)

    # Aspirate first (like STAR_tests.py)
    wells = [plate.get_item(f"{chr(65 + r)}{c + 1}") for r in range(8) for c in range(12)]
    aspiration = MultiHeadAspirationPlate(
      wells=wells,
      offset=Coordinate.zero(),
      tips=tips_96,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    await star_service.remote.aspirate96(aspiration=aspiration, blow_out=True)
    star_service.backend._write_and_read_command.reset_mock()

    dispense_op = MultiHeadDispensePlate(
      wells=wells,
      offset=Coordinate.zero(),
      tips=tips_96,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    await star_service.remote.dispense96(dispense=dispense_op, blow_out=True)
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0EDid0005da3xs02983xd0yh1457zm1866zv0032zq06180lz1999zt1866pp0100iw000ix0fh000"
        "zh2450ze2450df01083dg1200es0050ev000vt050bv00000cm0cs1ej00bs0020wh00hv00000hc00hp000"
        "mj000hs1200cwFFFFFFFFFFFFFFFFFFFFFFFFcr000cj0cx0"
      ),
    ])

  @pytest.mark.asyncio
  async def test_core_96_dispense_quadrant(self, star_service: StarServiceFixture):
    """384-well quadrant dispense. Mirrors test_core_96_dispense_quadrant."""
    _reset_backend_state(star_service.backend)
    tip_rack2 = star_service.deck.get_resource("tip_rack_02")
    plate = star_service.deck.get_resource("plate_01")
    plt_car = star_service.deck.get_resource("plate carrier")

    # Dynamically assign 384-well plate to plt_car[2]
    plate_384 = Greiner_384_wellplate_28ul_Fb(name="plate_384")
    plt_car[2] = plate_384

    try:
      # Pick up high volume tips
      tips_96 = []
      for row in "ABCDEFGH":
        for col in range(1, 13):
          tips_96.append(tip_rack2.get_item(f"{row}{col}").get_tip())
      pickup = PickupTipRack(resource=tip_rack2, offset=Coordinate.zero(), tips=tips_96)
      await star_service.remote.pick_up_tips96(pickup=pickup)

      # Aspirate from plate_01
      wells = [plate.get_item(f"{chr(65 + r)}{c + 1}") for r in range(8) for c in range(12)]
      aspiration = MultiHeadAspirationPlate(
        wells=wells, offset=Coordinate.zero(), tips=tips_96,
        volume=100.0, flow_rate=None, liquid_height=None,
        blow_out_air_volume=None, mix=None,
      )
      await star_service.remote.aspirate96(aspiration=aspiration, blow_out=True)

      expected = {
        "tl": "C0EDid0005da2xs02959xd0yh3400zm1912zv0032zq06180lz1999zt1912pp0100iw000ix0fh000zh2450ze2450df00060dg1200es0050ev000vt050bv00000cm0cs1ej00bs0020wh50hv00000hc00hp000mj000hs1200cwFFFFFFFFFFFFFFFFFFFFFFFFcr000cj0cx0",
        "tr": "C0EDid0006da2xs03004xd0yh3400zm1912zv0032zq06180lz1999zt1912pp0100iw000ix0fh000zh2450ze2450df00060dg1200es0050ev000vt050bv00000cm0cs1ej00bs0020wh50hv00000hc00hp000mj000hs1200cwFFFFFFFFFFFFFFFFFFFFFFFFcr000cj0cx0",
        "bl": "C0EDid0007da2xs02959xd0yh3355zm1912zv0032zq06180lz1999zt1912pp0100iw000ix0fh000zh2450ze2450df00060dg1200es0050ev000vt050bv00000cm0cs1ej00bs0020wh50hv00000hc00hp000mj000hs1200cwFFFFFFFFFFFFFFFFFFFFFFFFcr000cj0cx0",
        "br": "C0EDid0008da2xs03004xd0yh3355zm1912zv0032zq06180lz1999zt1912pp0100iw000ix0fh000zh2450ze2450df00060dg1200es0050ev000vt050bv00000cm0cs1ej00bs0020wh50hv00000hc00hp000mj000hs1200cwFFFFFFFFFFFFFFFFFFFFFFFFcr000cj0cx0",
      }

      for quadrant, expected_cmd in expected.items():
        quad_wells = plate_384.get_quadrant(cast(Literal["tl", "tr", "bl", "br"], quadrant))
        star_service.backend._write_and_read_command.reset_mock()
        dispense_op = MultiHeadDispensePlate(
          wells=quad_wells, offset=Coordinate.zero(), tips=tips_96,
          volume=6.0, flow_rate=None, liquid_height=None,
          blow_out_air_volume=None, mix=None,
        )
        await star_service.remote.dispense96(dispense=dispense_op)
        star_service.backend._write_and_read_command.assert_has_calls([
          _any_write_and_read_command_call(expected_cmd),
        ])
    finally:
      plate_384.unassign()


# =============================================================================
# iSwap tests
# =============================================================================

class TestFirmwareCmdIswap:
  @pytest.mark.asyncio
  async def test_iswap_move_plate(self, star_service: StarServiceFixture):
    """Move plate_01 to plt_car[2]. Mirrors test_iswap."""
    _reset_backend_state(star_service.backend)
    deck = star_service.deck
    plate = deck.get_resource("plate_01")
    plt_car = deck.get_resource("plate carrier")
    site = plt_car[2]

    pickup_dist = 13.2 - 3.33
    pickup = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop = _build_resource_drop(
      deck, plate, site, pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
    )
    await star_service.remote.pick_up_resource(pickup=pickup)
    await star_service.remote.drop_resource(drop=drop)

    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0PPid0001xs03479xd0yj1142yd0zj1874zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0002xs03479xd0yj3062yd0zj1874zd0th2800te2800gr1go1308ga0gc0",
      ),
    ])
    # Restore deck state
    _do_move_on_deck(plate, site, GripDirection.FRONT, GripDirection.FRONT)
    _do_move_on_deck(plate, plt_car[0], GripDirection.FRONT, GripDirection.FRONT)

  @pytest.mark.asyncio
  async def test_iswap_move_lid(self, star_service: StarServiceFixture):
    """Move plate_01_lid to plate_02. Mirrors test_iswap_move_lid."""
    _reset_backend_state(star_service.backend)
    deck = star_service.deck
    plate = deck.get_resource("plate_01")
    other_plate = deck.get_resource("plate_02")
    lid = plate.lid
    assert lid is not None

    # In STAR_tests.py, other_plate.lid is unassigned first
    other_lid = other_plate.lid
    assert other_lid is not None
    other_lid.unassign()

    try:
      pickup_dist = 5.7 - 3.33
      pickup = ResourcePickup(
        resource=lid, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop = _build_resource_drop(
        deck, lid, other_plate, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
      )
      await star_service.remote.pick_up_resource(pickup=pickup)
      await star_service.remote.drop_resource(drop=drop)

      star_service.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call(
          "C0PPid0001xs03479xd0yj1142yd0zj1950zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0"
        ),
        _any_write_and_read_command_call(
          "C0PRid0002xs03479xd0yj2102yd0zj1950zd0th2800te2800gr1go1308ga0gc0"
        ),
      ])
    finally:
      # Restore: put lid back on plate_01, re-add other_plate lid
      if lid.parent is not None and lid.parent is not plate:
        lid.unassign()
      if lid.parent is None:
        plate.assign_child_resource(lid)
      if other_lid.parent is None:
        other_plate.assign_child_resource(other_lid)

  @pytest.mark.asyncio
  async def test_iswap_stacking_area(self, star_service: StarServiceFixture):
    """Move lid to stack and back. Mirrors test_iswap_stacking_area."""
    _reset_backend_state(star_service.backend)
    deck = star_service.deck
    plate = deck.get_resource("plate_01")
    lid = plate.lid
    assert lid is not None

    stacking_area = ResourceStack("stacking_area", direction="z")
    deck.assign_child_resource(stacking_area, location=Coordinate(6, 414, 226.2 - 3.33))

    try:
      # Move lid to stacking area
      pickup_dist = 5.7 - 3.33
      pickup = ResourcePickup(
        resource=lid, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop = _build_resource_drop(
        deck, lid, stacking_area, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
      )
      await star_service.remote.pick_up_resource(pickup=pickup)
      await star_service.remote.drop_resource(drop=drop)

      star_service.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call(
          "C0PPid0001xs03479xd0yj1142yd0zj1950zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0"
        ),
        _any_write_and_read_command_call(
          "C0PRid0002xs00699xd0yj4567yd0zj2305zd0th2800te2800gr1go1308ga0gc0"
        ),
      ])

      # Move lid from stack to plate
      _do_move_on_deck(lid, stacking_area, GripDirection.FRONT, GripDirection.FRONT)
      star_service.backend._write_and_read_command.reset_mock()
      star_service.backend.id_ = 2  # Continue id sequence

      pickup2 = ResourcePickup(
        resource=lid, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop2 = _build_resource_drop(
        deck, lid, plate, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
      )
      await star_service.remote.pick_up_resource(pickup=pickup2)
      await star_service.remote.drop_resource(drop=drop2)

      star_service.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call(
          "C0PPid0003xs00699xd0yj4567yd0zj2305zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0"
        ),
        _any_write_and_read_command_call(
          "C0PRid0004xs03479xd0yj1142yd0zj1950zd0th2800te2800gr1go1308ga0gc0"
        ),
      ])
    finally:
      # Restore deck
      if lid.parent is not None and lid.parent is not plate:
        lid.unassign()
      if lid.parent is None:
        plate.assign_child_resource(lid)
      stacking_area.unassign()

  @pytest.mark.asyncio
  async def test_iswap_move_with_intermediate(self, star_service: StarServiceFixture):
    """Move plate with intermediate locations. Mirrors test_iswap_move_with_intermediate_locations."""
    _reset_backend_state(star_service.backend)
    deck = star_service.deck
    plate = deck.get_resource("plate_01")
    plt_car = deck.get_resource("plate carrier")
    other_plate = deck.get_resource("plate_02")

    # Unassign plate_02 from plt_car[1] (same as STAR_tests.py)
    other_plate.unassign()
    try:
      pickup_dist = 13.2 - 3.33
      site1 = plt_car[1]

      pickup = ResourcePickup(
        resource=plate, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      await star_service.remote.pick_up_resource(pickup=pickup)

      # Intermediate locations
      int1 = plt_car[2].get_absolute_location() + Coordinate(50, 0, 50)
      int2 = plt_car[3].get_absolute_location() + Coordinate(-50, 0, 50)

      move1 = ResourceMove(
        resource=plate, location=int1,
        gripped_direction=GripDirection.FRONT,
        pickup_distance_from_top=pickup_dist,
        offset=Coordinate.zero(),
      )
      move2 = ResourceMove(
        resource=plate, location=int2,
        gripped_direction=GripDirection.FRONT,
        pickup_distance_from_top=pickup_dist,
        offset=Coordinate.zero(),
      )
      await star_service.remote.move_picked_up_resource(move=move1)
      await star_service.remote.move_picked_up_resource(move=move2)

      drop = _build_resource_drop(
        deck, plate, site1, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
      )
      await star_service.remote.drop_resource(drop=drop)

      star_service.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call(
          "C0PPid0001xs03479xd0yj1142yd0zj1874zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0"
        ),
        _any_write_and_read_command_call(
          "C0PMid0002xs03979xd0yj3062yd0zj2405zd0gr1th2800ga1xe4 1"
        ),
        _any_write_and_read_command_call(
          "C0PMid0003xs02979xd0yj4022yd0zj2405zd0gr1th2800ga1xe4 1"
        ),
        _any_write_and_read_command_call(
          "C0PRid0004xs03479xd0yj2102yd0zj1874zd0th2800te2800gr1go1308ga0gc0"
        ),
      ])
    finally:
      # Restore: move plate back to plt_car[0], reassign plate_02
      if plate.parent is not None and plate.parent.name != "plate carrier-site-0":
        plate.unassign()
      if plate.parent is None:
        plt_car[0] = plate
      if other_plate.parent is None:
        plt_car[1] = other_plate


# =============================================================================
# CoRe gripper tests
# =============================================================================

class TestFirmwareCmdCoReGripper:
  @pytest.mark.asyncio
  async def test_move_core(self, star_service: StarServiceFixture):
    """Move plate via CoRe gripper. Mirrors test_move_core."""
    _reset_backend_state(star_service.backend)
    deck = star_service.deck
    plate = deck.get_resource("plate_01")
    plt_car = deck.get_resource("plate carrier")
    other_plate = deck.get_resource("plate_02")

    # Unassign plate_02 from plt_car[1]
    other_plate.unassign()
    try:
      pickup_dist = 13 - 3.33
      site1 = plt_car[1]

      pickup = ResourcePickup(
        resource=plate, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop = _build_resource_drop(
        deck, plate, site1, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
      )
      await star_service.remote.pick_up_resource(
        pickup=pickup, use_arm="core", core_front_channel=7,
      )
      await star_service.remote.drop_resource(
        drop=drop, use_arm="core", return_core_gripper=True,
      )

      star_service.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call(
          "C0ZTid0001xs07975xd0ya1250yb1070pa07pb08tp2350tz2250th2800tt14"
        ),
        _any_write_and_read_command_call(
          "C0ZPid0002xs03479xd0yj1142yv0050zj1876zy0500yo0885yg0825yw15" "th2800te2800"
        ),
        _any_write_and_read_command_call(
          "C0ZRid0003xs03479xd0yj2102zj1876zi000zy0500yo0885th2800te2800"
        ),
        _any_write_and_read_command_call(
          "C0ZSid0004xs07975xd0ya1250yb1070tp2150tz2050th2800te2800"
        ),
      ])
    finally:
      if plate.parent is not None and plate.parent.name != "plate carrier-site-0":
        plate.unassign()
      if plate.parent is None:
        plt_car[0] = plate
      if other_plate.parent is None:
        plt_car[1] = other_plate


# =============================================================================
# Miscellaneous tests
# =============================================================================

class TestFirmwareCmdMisc:
  @pytest.mark.asyncio
  async def test_indicator_light(self, star_service: StarServiceFixture):
    """Set loading indicators. Mirrors test_indicator_light."""
    _reset_backend_state(star_service.backend)
    await star_service.remote.set_loading_indicators(
      bit_pattern=[True] * 54, blink_pattern=[False] * 54,
    )
    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0CPid0001cl3FFFFFFFFFFFFFcb00000000000000",
      ),
    ])

  @pytest.mark.asyncio
  async def test_discard_tips(self, star_service: StarServiceFixture):
    """Discard 8 tips to waste. Mirrors test_discard_tips."""
    _reset_backend_state(star_service.backend)
    tip_rack = star_service.deck.get_resource("tip_rack_01")

    # Pick up all 8 tips from A1:H1
    spots = [tip_rack.get_item(f"{chr(65+i)}1") for i in range(8)]
    ops = [Pickup(resource=s, offset=Coordinate.zero(), tip=s.get_tip()) for s in spots]
    await star_service.remote.pick_up_tips(ops=ops, use_channels=list(range(8)))

    star_service.backend._write_and_read_command.side_effect = [
      "C0TRid0003kz000 000 000 000 000 000 000 000vz000 000 000 000 000 000 000 000"
    ]
    star_service.backend._write_and_read_command.reset_mock()

    # Drop tips to waste using the trash resource with tight offsets
    trash = star_service.deck.get_trash_area()
    trash_offsets = get_tight_single_resource_liquid_op_offsets(trash, num_channels=8)
    drop_ops = [
      Drop(resource=trash, offset=off, tip=spots[i].get_tip())
      for i, off in enumerate(trash_offsets)
    ]
    await star_service.remote.drop_tips(ops=drop_ops, use_channels=list(range(8)))

    star_service.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0TRid0003xp08000 08000 08000 08000 08000 08000 08000 08000"
        "yp3427 3337 3247 3157 3067 2977 2887 2797"
        "tm1 1 1 1 1 1 1 1tp1970tz1870th2450te2450ti0",
      ),
    ])


# =============================================================================
# Tip size tests
# =============================================================================

class TestFirmwareCmdTipSizes:
  @pytest.mark.asyncio
  async def test_10uL_tips(self, star_service: StarServiceFixture):
    """10uL tip pickup/drop Z positions. Mirrors test_10uL_tips."""
    _reset_backend_state(star_service.backend)
    from pylabrobot.resources.hamilton.tip_racks import hamilton_96_tiprack_10uL
    tip_car = star_service.deck.get_resource("tip carrier")
    tip_rack = hamilton_96_tiprack_10uL("tips_10uL")
    tip_car[0] = tip_rack
    try:
      spot = tip_rack.get_item("A1")
      ops = [Pickup(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.pick_up_tips(ops=ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TP")
      assert tp == 2224
      assert tz == 2164

      star_service.backend._write_and_read_command.reset_mock()
      star_service.backend._write_and_read_command.return_value = (
        "C0TRid0001kz000 000 000 000 000 000 000 000vz000 000 000 000 000 000 000 000"
      )
      drop_ops = [Drop(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.drop_tips(ops=drop_ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TR")
      assert tp == 2224
      assert tz == 2144
    finally:
      tip_rack.unassign()

  @pytest.mark.asyncio
  async def test_50uL_tips(self, star_service: StarServiceFixture):
    """50uL tip pickup/drop Z positions. Mirrors test_50uL_tips."""
    _reset_backend_state(star_service.backend)
    from pylabrobot.resources.hamilton.tip_racks import hamilton_96_tiprack_50uL
    tip_car = star_service.deck.get_resource("tip carrier")
    tip_rack = hamilton_96_tiprack_50uL("tips_50uL")
    tip_car[0] = tip_rack
    try:
      spot = tip_rack.get_item("A1")
      ops = [Pickup(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.pick_up_tips(ops=ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TP")
      assert tp == 2248
      assert tz == 2168

      star_service.backend._write_and_read_command.reset_mock()
      star_service.backend._write_and_read_command.return_value = (
        "C0TRid0001kz000 000 000 000 000 000 000 000vz000 000 000 000 000 000 000 000"
      )
      drop_ops = [Drop(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.drop_tips(ops=drop_ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TR")
      assert tp == 2248
      assert tz == 2168
    finally:
      tip_rack.unassign()

  @pytest.mark.asyncio
  async def test_300uL_tips(self, star_service: StarServiceFixture):
    """300uL tip pickup/drop Z positions. Mirrors test_300uL_tips."""
    _reset_backend_state(star_service.backend)
    from pylabrobot.resources.hamilton.tip_racks import hamilton_96_tiprack_300uL
    tip_car = star_service.deck.get_resource("tip carrier")
    tip_rack = hamilton_96_tiprack_300uL("tips_300uL")
    tip_car[0] = tip_rack
    try:
      spot = tip_rack.get_item("A1")
      ops = [Pickup(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.pick_up_tips(ops=ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TP")
      assert tp == 2244
      assert tz == 2164

      star_service.backend._write_and_read_command.reset_mock()
      star_service.backend._write_and_read_command.return_value = (
        "C0TRid0001kz000 000 000 000 000 000 000 000vz000 000 000 000 000 000 000 000"
      )
      drop_ops = [Drop(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.drop_tips(ops=drop_ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TR")
      assert tp == 2244
      assert tz == 2164
    finally:
      tip_rack.unassign()

  @pytest.mark.asyncio
  async def test_1000uL_tips(self, star_service: StarServiceFixture):
    """1000uL tip pickup/drop Z positions. Mirrors test_1000uL_tips."""
    _reset_backend_state(star_service.backend)
    tip_car = star_service.deck.get_resource("tip carrier")
    tip_rack = hamilton_96_tiprack_1000uL("tips_1000uL")
    tip_car[0] = tip_rack
    try:
      spot = tip_rack.get_item("A1")
      ops = [Pickup(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.pick_up_tips(ops=ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TP")
      assert tp == 2266
      assert tz == 2166

      star_service.backend._write_and_read_command.reset_mock()
      star_service.backend._write_and_read_command.return_value = (
        "C0TRid0001kz000 000 000 000 000 000 000 000vz000 000 000 000 000 000 000 000"
      )
      drop_ops = [Drop(resource=spot, offset=Coordinate.zero(), tip=spot.get_tip())]
      await star_service.remote.drop_tips(ops=drop_ops, use_channels=[0])
      tp, tz = _get_tp_tz_from_calls(star_service.backend, "C0TR")
      assert tp == 2266
      assert tz == 2186
    finally:
      tip_rack.unassign()
