"""Tests for Head8.

Covers core logic that must survive refactors:
  - _resolve_probe_positions: pitch validation for 96-well columns
  - _validate_container_span: minimum Y-span check for trough path
  - all-8-channel enforcement (ganged head constraint)
  - V1/V2 aspirate/dispense dispatch and LLD/TADM kwargs
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest

from pylabrobot.hamilton.prep import PrepDriver, PrepSimulationDriver
from pylabrobot.hamilton.prep.driver import prep_commands as PrepCmd
from pylabrobot.hamilton.prep.driver.features.head8 import PROBE_PITCH_MM, Head8
from pylabrobot.hamilton.prep.driver.features.pipettes import (
  HEAD8_CLEARANCE_Y,
  Pipettes,
  _build_pipettor_gantry_move_parameters,
  _get_container_segments,
  _get_profile_drop,
)
from pylabrobot.hamilton.prep.driver.model import (
  ContainerFacts,
  Placed,
  locate,
  read_containers,
  ref,
)
from pylabrobot.hamilton.prep.driver.simulator import RECORDING_PREP_HEAD8
from pylabrobot.hamilton.prep.driver.test_helpers import (
  make_plain_deck,
  make_prep_deck,
  parts_of,
  place,
)
from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import TooLittleLiquidError
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_deck(
  name_prefix: Optional[str] = None,
  volume_tracking: bool = False,
) -> Tuple[handles.Deck, handles.TipRack, handles.Plate, handles.Plate]:
  """A Prep deck with a 50 uL rack on spot 3 and plates on spots 0 and 4.

  The plates track volumes only when asked, as PLR's global volume tracking was off by default."""
  deck = await make_prep_deck(name_prefix=name_prefix)
  tip_rack = await place(deck, "hamilton_96_tiprack_50uL_NTR", "ntr", 3)
  src_plate = await place(deck, "cor_axy_96_wellplate_500uL_Ub", "src", 0)
  dst_plate = await place(deck, "cor_axy_96_wellplate_500uL_Ub", "dst", 4)
  assert isinstance(tip_rack, handles.TipRack)
  assert isinstance(src_plate, handles.Plate) and isinstance(dst_plate, handles.Plate)
  if not volume_tracking:
    await src_plate.set_volume_tracking(False)
    await dst_plate.set_volume_tracking(False)
  return deck, tip_rack, src_plate, dst_plate


async def _setup(deck: handles.Deck, **kwargs: Any) -> PrepSimulationDriver:
  p = PrepSimulationDriver(deck=deck, declared_configuration_json=RECORDING_PREP_HEAD8)
  await p.setup(**kwargs)
  assert p.head8 is not None
  return p


def _column(itemized: handles.ItemizedResource, column: int) -> List[Any]:
  """One column of a 96-grid, A to H."""
  return itemized[column * 8 : (column + 1) * 8]


def _make_head8() -> Head8:
  return Head8(None)  # type: ignore[arg-type]


def _facts(name: str, size: Coordinate) -> ContainerFacts:
  """A container of `size`, standing nowhere in particular."""
  zero = Coordinate.zero()
  return ContainerFacts(
    id=b"",
    name=name,
    kind=pb.RESOURCE_KIND_CONTAINER,
    parent_name=name,
    placed=Placed(
      id=b"",
      origin=zero,
      bottom=zero,
      cavity_bottom=zero,
      top=zero,
      center=zero,
      size=size,
      absolute_size=size,
      rotation=Rotation(),
    ),
    spec=pb.ContainerSpec(),
    volume=0.0,
    tracks_volume=False,
  )


async def _wells_and_ys(
  plate: handles.Plate, wells: Sequence[handles.Resource]
) -> Tuple[List[ContainerFacts], List[float]]:
  """The wells as `_resolve_probe_positions` takes them: their facts and absolute cavity ys."""
  deck = await plate.get_root()
  facts = await read_containers(plate.store, ref(deck.id), list(wells))
  absolute = await locate(plate.store, None, [w.id for w in wells], [w.id for w in wells])
  return facts, [absolute[w.id].cavity_bottom.y for w in wells]


async def _tip_names(spots: Sequence[handles.Resource]) -> List[Optional[str]]:
  """The name of the tip each spot holds, None where it holds none."""
  names: List[Optional[str]] = []
  for spot in spots:
    assert isinstance(spot, handles.TipSpot)
    tip = await spot.get_tip()
    names.append(None if tip is None else tip.name)
  return names


async def _mounted_names(head: Head8) -> List[Optional[str]]:
  return [None if t is None else t.name for t in await head.get_mounted_tips()]


async def _take_off(head: Head8, channel: int) -> None:
  """Take the tip off one probe in the model alone, as if it fell."""
  shaft = head.shaft(channel)
  assert isinstance(shaft, handles.TipMountingShaft)
  tool = await shaft.get_tool()
  assert tool is not None
  await tool.delete()


async def _put_lid_on(rack: handles.Resource) -> handles.Resource:
  return await rack.store.create(
    build.resource(
      "lid",
      Coordinate(127.0, 86.0, 10.0),
      kind=pb.RESOURCE_KIND_LID,
      lid=pb.LidSpec(nesting_z_height=2.0),
    ),
    name="lid",
    parent=rack,
  )


async def _volumes(wells: Sequence[handles.Resource]) -> List[float]:
  volumes = []
  for well in wells:
    assert isinstance(well, handles.Container)
    volumes.append(await well.get_volume())
  return volumes


async def _set_volumes(wells: Sequence[handles.Resource], volume: float) -> None:
  for well in wells:
    assert isinstance(well, handles.Container)
    await well.set_volume(volume)


def _record_send(prep: PrepDriver) -> tuple[list[Any], Any]:
  captured: list[Any] = []
  orig_send = prep.send_command

  async def recording(command, **kw):
    captured.append(command)
    return await orig_send(command, **kw)

  prep.send_command = recording  # type: ignore[method-assign, assignment]
  return captured, orig_send


# ---------------------------------------------------------------------------
# Group 1: _resolve_probe_positions / _validate_container_span
# ---------------------------------------------------------------------------


def test_resolve_probe_positions_valid_96well_column():
  """96-well column A→H has exactly 9mm pitch — should pass and return expected Ys."""

  async def _run() -> None:
    deck = await make_plain_deck()
    plate = await deck.store.create(
      "cor_axy_96_wellplate_500uL_Ub", name="p", parent=deck, location=Coordinate(100, 200, 0)
    )
    assert isinstance(plate, handles.Plate)
    wells, ys_actual = await _wells_and_ys(plate, _column(plate, 0))

    be = _make_head8()
    ys = be._resolve_probe_positions(wells, ys_actual)

    assert len(ys) == 8
    ref_y = ys_actual[0]
    for i, y in enumerate(ys):
      assert y == pytest.approx(ref_y - i * PROBE_PITCH_MM), (
        f"probe {i}: expected {ref_y - i * PROBE_PITCH_MM}, got {y}"
      )

  asyncio.run(_run())


def test_resolve_probe_positions_misaligned_raises():
  """Wells not at 9mm pitch must raise ValueError with a descriptive message."""

  async def _run() -> None:
    deck = await make_plain_deck()
    plate = await deck.store.create(
      "cor_axy_96_wellplate_500uL_Ub", name="p", parent=deck, location=Coordinate(100, 200, 0)
    )
    assert isinstance(plate, handles.Plate)
    col = _column(plate, 0)
    # Swap rows 0 and 1 — now the pitch from well[0] to well[1] is wrong.
    bad_wells = [col[1], col[0]] + list(col[2:])
    wells, ys = await _wells_and_ys(plate, bad_wells)

    be = _make_head8()
    with pytest.raises(ValueError, match="9.0 mm probe pitch"):
      be._resolve_probe_positions(wells, ys)

  asyncio.run(_run())


def test_validate_container_span_sufficient():
  """Container wider than 63mm passes without error."""
  # Cor_Axy_96 is 85.51mm in Y — well above 63mm minimum.
  be = _make_head8()
  be._validate_container_span(_facts("p", Coordinate(127.0, 85.51, 14.82)))  # should not raise


def test_validate_container_span_too_narrow():
  """Container narrower than 63mm raises ValueError."""
  narrow = _facts("narrow_container", Coordinate(100.0, 40.0, 10.0))
  be = _make_head8()
  with pytest.raises(ValueError, match="too narrow"):
    be._validate_container_span(narrow)


# ---------------------------------------------------------------------------
# Group 2: all-8-channel enforcement + Head8 wiring
# ---------------------------------------------------------------------------


def test_partial_channel_pickup_raises_value_error():
  """Head8 rejects pick_up_tips with fewer than all 8 channels."""

  async def _run() -> None:
    deck, tip_rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    spots = _column(tip_rack, 1)[4:]  # E2, F2, G2, H2
    with pytest.raises(ValueError, match="fully-ganged head"):
      await p.head8.pick_up_tips(spots, use_channels=(4, 5, 6, 7))

    await p.stop()

  asyncio.run(_run())


def test_head8_full_flow():
  """pick_up_tips → aspirate → dispense → drop_tips on the simulator."""

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0), volume=20, disable_volume_correction=True
    )
    await p.head8.dispense(
      containers=_column(dst_plate, 0), volume=20, disable_volume_correction=True
    )
    await p.head8.drop_tips(spots)

    await p.stop()

  asyncio.run(_run())


def test_head8_tip_commands_refuse_a_rack_no_head_can_reach():
  """A rack under a lid is not picked up from, nor dropped into, and nothing is sent."""

  async def _run() -> None:
    deck, tip_rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    spots = _column(tip_rack, 0)

    lid = await _put_lid_on(tip_rack)
    sent, _ = _record_send(p)
    with pytest.raises(ValueError, match="pick up tips from 'ntr': it is not available"):
      await p.head8.pick_up_tips(spots)
    assert sent == []

    await lid.delete()
    await p.head8.pick_up_tips(spots)
    await _put_lid_on(tip_rack)
    sent.clear()
    with pytest.raises(ValueError, match="drop tips into 'ntr': it is not available"):
      await p.head8.drop_tips(spots)
    assert sent == []
    await p.stop()

  asyncio.run(_run())


def test_head8_tips_move_between_spots_and_shafts():
  """With tip tracking on, each tip moves off its spot onto its probe's shaft, and back."""

  async def _run() -> None:
    deck, tip_rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    spots = _column(tip_rack, 0)
    tips = await _tip_names(spots)
    assert all(t is not None for t in tips)
    await p.head8.pick_up_tips(spots)
    assert await _tip_names(spots) == [None] * 8
    assert await _mounted_names(p.head8) == tips
    for i, name in enumerate(tips):
      assert name is not None
      tip = await deck.store.get(name, root=await deck.get_root())
      parent = await tip.get_parent()
      assert parent is not None and parent.name == p.head8.shaft(i).name
    await p.head8.drop_tips(spots)
    assert await _tip_names(spots) == tips
    assert all(t is None for t in await p.head8.get_mounted_tips())
    await p.stop()

  asyncio.run(_run())


def test_build_pipettor_gantry_move_parameters_maps_rear_front():
  m = _build_pipettor_gantry_move_parameters(10.0, [0, 1], [20.0, 30.0], [40.0, 50.0])
  assert m.gantry_x_position == 10.0
  assert len(m.axis_parameters) == 2
  assert m.axis_parameters[0].channel == PrepCmd.ChannelIndex.RearChannel
  assert m.axis_parameters[0].y_position == 20.0
  assert m.axis_parameters[0].z_position == 40.0
  assert m.axis_parameters[1].channel == PrepCmd.ChannelIndex.FrontChannel
  assert m.axis_parameters[1].y_position == 30.0
  assert m.axis_parameters[1].z_position == 50.0


def test_head8_move_to_position_sends_mph_wire_commands():
  """Head8.move_to_position sends MphMoveToPosition / ViaLane."""

  async def _run() -> None:
    deck, _, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    await p.head8.move_to_position(11.0, 22.5, 99.0)
    direct = [c for c in captured if isinstance(c, PrepCmd.MphMoveToPosition)]
    assert len(direct) == 1
    assert direct[0].x_position == 11.0
    assert direct[0].y_position == 22.5
    assert direct[0].z_position == 99.0

    await p.head8.move_to_position(1.0, 2.0, 3.0, via_lane=True)
    lanes = [c for c in captured if isinstance(c, PrepCmd.MphMoveToPositionViaLane)]
    assert len(lanes) == 1
    assert lanes[0].x_position == 1.0 and lanes[0].y_position == 2.0 and lanes[0].z_position == 3.0

    await p.stop()

  asyncio.run(_run())


def test_pick_up_tips_sends_the_move_over_the_spots_then_the_pickup():
  """The head is taken over the spots before the one MphPickupTips, so it descends straight down."""

  async def _run() -> None:
    deck, tip_rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    await p.head8.pick_up_tips(_column(tip_rack, 0))

    pickups = [i for i, c in enumerate(captured) if isinstance(c, PrepCmd.MphPickupTips)]
    assert len(pickups) == 1
    assert any(isinstance(c, PrepCmd.MphMoveToPosition) for c in captured[: pickups[0]])

    await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize("use_channels", [None, tuple(range(8))])
def test_return_tips_restores_original_column(use_channels):
  """Return the same tips to a non-first column and forward drop options."""

  async def _run() -> None:
    deck, tip_rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      spots = _column(tip_rack, 3)
      tips = await _tip_names(spots)
      await p.head8.pick_up_tips(spots)
      assert await _tip_names(spots) == [None] * 8
      captured, _ = _record_send(p)

      await p.head8.return_tips(
        use_channels=use_channels, seek_speed=12.0, minimum_traverse_height_end=110.0
      )

      (drop,) = [c for c in captured if isinstance(c, PrepCmd.MphDropTips)]
      assert drop.seek_speed == 12.0
      assert drop.final_z == 110.0
      assert await _tip_names(spots) == tips
      assert await _mounted_names(p.head8) == [None] * 8
    finally:
      await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize("invalid_state", ["empty", "partial", "missing_origin", "occupied"])
def test_return_tips_rejects_invalid_state_before_sending(invalid_state):
  """Validate all eight tips and their destinations before sending a command."""
  from pylabrobot.resources.errors import HasTipError

  async def _run() -> None:
    deck, tip_rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      spots = _column(tip_rack, 0)
      if invalid_state != "empty":
        await p.head8.pick_up_tips(spots)
      if invalid_state == "partial":
        await _take_off(p.head8, 7)
      elif invalid_state == "missing_origin":
        await tip_rack.unassign()
      elif invalid_state == "occupied":
        spare = _column(tip_rack, 1)[7]
        assert isinstance(spare, handles.TipSpot)
        tip = await spare.get_tip()
        assert tip is not None
        await spots[7].assign_child_resource(tip)
      mounted = await _mounted_names(p.head8)
      captured, _ = _record_send(p)

      error = HasTipError if invalid_state == "occupied" else RuntimeError
      with pytest.raises(error):
        await p.head8.return_tips()
      assert captured == []
      assert await _mounted_names(p.head8) == mounted
    finally:
      await p.stop()

  asyncio.run(_run())


def test_return_tips_rejects_partial_channel_selection():
  """The ganged head cannot return tips on selected channels only."""
  with pytest.raises(ValueError, match="fully-ganged head"):
    asyncio.run(_make_head8().return_tips(use_channels=[0, 1]))


@pytest.mark.parametrize("use_channels", [None, tuple(range(8))])
@pytest.mark.parametrize(
  "rack_model", ["hamilton_96_tiprack_50uL_NTR", "hamilton_96_tiprack_1000uL"]
)
def test_discard_tips_uses_mph_waste_and_releases_all_tips(use_channels, rack_model):
  """Discard uses the prefixed deck's MPH site and the tip's length, and forwards drop options."""

  async def _run() -> None:
    deck = await make_prep_deck(name_prefix="prep")
    rack = await place(deck, rack_model, "tips", 3)
    assert isinstance(rack, handles.TipRack)
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      spots = _column(rack, 0)
      await p.head8.pick_up_tips(spots)
      tips = await p.head8._require_mounted_tips()
      waste = (await parts_of(deck)).waste_positions["waste_mph"]
      await deck.assign_child_resource(waste, location=Coordinate(280, 100, 70))
      captured, _ = _record_send(p)

      await p.head8.discard_tips(
        use_channels=use_channels,
        seek_speed=12.0,
        z_seek_offset=1.0,
        minimum_traverse_height_end=160.0,
      )

      (drop,) = [c for c in captured if isinstance(c, PrepCmd.MphDropTips)]
      position = drop.tip_position
      assert position.channel == PrepCmd.ChannelIndex.MPHChannel
      assert position.drop_type == PrepCmd.TipDropType.Stall
      assert (position.x_position, position.y_position) == (283.0, 103.0)
      assert position.z_position == pytest.approx(70.0 + tips[0].size.z - tips[0].fitting_depth)
      assert position.z_seek == pytest.approx(73.0 + tips[0].size.z)
      assert drop.seek_speed == 12.0
      assert drop.final_z == 160.0
      assert drop.tip_roll_off_distance == 3.0
      assert await _mounted_names(p.head8) == [None] * 8
      assert await _tip_names(spots) == [None] * 8
      # Into the waste, the tips leave the store.
      gone = await deck.store.find_resources(
        filter=spb.ResourceFilter(names=[tip.name for tip in tips])
      )
      assert gone == []

      captured.clear()
      await p.head8.discard_tips(use_channels=use_channels)
      assert captured == []
    finally:
      await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize("use_channels", [[], [0, 1], list(reversed(range(8)))])
def test_discard_tips_rejects_invalid_channel_selection(use_channels):
  """Discarding cannot select or reorder individual channels on the ganged head."""
  with pytest.raises(ValueError, match="fully-ganged head"):
    asyncio.run(_make_head8().discard_tips(use_channels=use_channels))


@pytest.mark.parametrize(
  "invalid_state, message",
  [
    ("partial", "No tips mounted"),
    ("no_deck", "no deck"),
    ("wrong_deck", "PrepDeck"),
    ("no_waste_block", "waste block"),
    ("no_waste_position", "waste_mph"),
  ],
)
def test_discard_tips_rejects_invalid_state_before_sending(invalid_state, message):
  """Invalid tip or waste state leaves all mounted tips in place without sending commands."""

  async def _run() -> None:
    deck, rack, _, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    parts = p.parts
    try:
      await p.head8.pick_up_tips(_column(rack, 0))
      if invalid_state == "partial":
        await _take_off(p.head8, 7)
      elif invalid_state == "no_deck":
        p.deck = None
      elif invalid_state == "wrong_deck":
        # A deck that is not a Prep's: the driver models nothing on it.
        p.deck = await make_plain_deck()
        p.parts = None
      elif invalid_state == "no_waste_block":
        waste_block = (await parts_of(deck)).waste_block
        assert waste_block is not None
        await waste_block.unassign()
      elif invalid_state == "no_waste_position":
        await (await parts_of(deck)).waste_positions["waste_mph"].unassign()
      mounted = await _mounted_names(p.head8)
      captured, _ = _record_send(p)

      with pytest.raises(RuntimeError, match=message):
        await p.head8.discard_tips()
      assert captured == []
      assert await _mounted_names(p.head8) == mounted
    finally:
      p.deck = deck
      p.parts = parts
      await p.stop()

  asyncio.run(_run())


def test_head8_partial_channel_aspirate_raises_value_error():
  """Head8 rejects aspirate with fewer than all 8 channels."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)

    with pytest.raises(ValueError, match="fully-ganged head"):
      await p.head8.aspirate(
        containers=_column(src_plate, 0)[:4],
        volume=10,
        disable_volume_correction=True,
        use_channels=(0, 1, 2, 3),
      )

    await p.stop()

  asyncio.run(_run())


# ---------------------------------------------------------------------------
# Group 3: V2 aspirate/dispense dispatch
# ---------------------------------------------------------------------------


def test_head8_v2_aspirate_sends_mphaspiratenolldmonitoring2():
  """Simulator default (use_v1=False) → V2 command class is sent."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0), volume=10, disable_volume_correction=True
    )

    asp_cmds = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    v1_cmds = [
      c
      for c in captured
      if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring)
      and not isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)
    ]
    assert len(asp_cmds) == 1, f"Expected 1 MphAspirateNoLldMonitoring2, got {len(asp_cmds)}"
    assert len(v1_cmds) == 0, "V1 aspirate command should not be sent when V2 is supported"
    assert len(asp_cmds[0].aspirate_parameters) == 1, (
      "MPH sends a single struct element (probe-0 reference); firmware drives all 8 probes"
    )

    await p.stop()

  asyncio.run(_run())


def test_head8_aspirate_container_segments_start_at_z_minimum():
  """With container geometry following, segment 0 begins at the z_minimum the command sends."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    await p.head8.pick_up_tips(_column(tip_rack, 0))
    wells = _column(src_plate, 0)
    (first,) = await read_containers(deck.store, ref(deck.id), wells[:1])
    cavity_bottom_z = first.cavity_bottom.z
    profile_top = sum(s.height for s in _get_container_segments(first))
    await p.head8.aspirate(
      containers=wells,
      volume=10,
      disable_volume_correction=True,
      z_minimum=cavity_bottom_z + 1.5,
      liquid_height=3.0,
      lld_mode=Pipettes.LLDMode.OFF,
      auto_surface_following=True,
    )

    asp = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    params = asp[0].aspirate_parameters[0]
    assert params.common.z_minimum == pytest.approx(cavity_bottom_z + 1.5)
    sent_height = sum(s.height for s in params.container_description)
    assert sent_height == pytest.approx(profile_top - 1.5)

    await p.stop()

  asyncio.run(_run())


def test_head8_v2_dispense_sends_mphdispensetnolld2():
  """Simulator default (use_v1=False) → V2 dispense command class is sent."""

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0), volume=10, disable_volume_correction=True
    )
    await p.head8.dispense(
      containers=_column(dst_plate, 0), volume=10, disable_volume_correction=True
    )

    disp_cmds = [c for c in captured if isinstance(c, PrepCmd.MphDispenseNoLld2)]
    v1_cmds = [
      c
      for c in captured
      if isinstance(c, PrepCmd.MphDispenseNoLld) and not isinstance(c, PrepCmd.MphDispenseNoLld2)
    ]
    assert len(disp_cmds) == 1, f"Expected 1 MphDispenseNoLld2, got {len(disp_cmds)}"
    assert len(v1_cmds) == 0, "V1 dispense command should not be sent when V2 is supported"

    await p.stop()

  asyncio.run(_run())


def test_head8_v1_fallback_when_use_v1_flag_set():
  """use_v1_aspirate_dispense=True → V1 command classes are sent for MPH too."""

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck()
    p = await _setup(deck, use_v1_aspirate_dispense=True)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0), volume=10, disable_volume_correction=True
    )
    await p.head8.dispense(
      containers=_column(dst_plate, 0), volume=10, disable_volume_correction=True
    )

    v2_asp = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    v2_disp = [c for c in captured if isinstance(c, PrepCmd.MphDispenseNoLld2)]
    v1_asp = [
      c
      for c in captured
      if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring)
      and not isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)
    ]
    v1_disp = [
      c
      for c in captured
      if isinstance(c, PrepCmd.MphDispenseNoLld) and not isinstance(c, PrepCmd.MphDispenseNoLld2)
    ]

    assert len(v2_asp) == 0, "V2 aspirate should not be sent with use_v1=True"
    assert len(v2_disp) == 0, "V2 dispense should not be sent with use_v1=True"
    assert len(v1_asp) == 1, f"Expected 1 V1 aspirate, got {len(v1_asp)}"
    assert len(v1_disp) == 1, f"Expected 1 V1 dispense, got {len(v1_disp)}"

    await p.stop()

  asyncio.run(_run())


# ---------------------------------------------------------------------------
# Group 4: LLD and TADM dispatch
# ---------------------------------------------------------------------------


def test_head8_aspirate_tadm_sends_mphaspirate_tadm2():
  """tadm= kwargs → MphAspirateTadm2 (v2, no LLD)."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0),
      volume=10,
      disable_volume_correction=True,
      tadm=PrepCmd.TadmParameters.default(),
    )

    tadm_cmds = [c for c in captured if isinstance(c, PrepCmd.MphAspirateTadm2)]
    assert len(tadm_cmds) == 1, f"Expected 1 MphAspirateTadm2, got {len(tadm_cmds)}"
    no_lld_cmds = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    assert len(no_lld_cmds) == 0, "NoLldMonitoring2 should not be sent when tadm= is set"

    await p.stop()

  asyncio.run(_run())


def test_head8_aspirate_clld_sends_mphaspirate_with_lld2():
  """lld_mode=CAPACITIVE → MphAspirateWithLld2 (v2, LLD, no TADM).

  Capacitive seeks leave pLLD on firmware defaults so the dispenser is not
  started at speed 0; cLLD stays explicit so detection still runs.
  """

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0),
      volume=10,
      disable_volume_correction=True,
      lld_mode=Pipettes.LLDMode.CAPACITIVE,
    )

    lld_cmds = [c for c in captured if isinstance(c, PrepCmd.MphAspirateWithLld2)]
    assert len(lld_cmds) == 1, f"Expected 1 MphAspirateWithLld2, got {len(lld_cmds)}"
    params = lld_cmds[0].aspirate_parameters[0]
    assert params.p_lld.default_values is True
    assert params.c_lld.default_values is False
    assert params.c_lld.sensitivity == 3

    await p.stop()

  asyncio.run(_run())


def test_head8_aspirate_pressure_and_dual_are_not_implemented():
  """Pressure LLD has not detected on the Prep: PRESSURE and DUAL refused before sending."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    await p.head8.pick_up_tips(_column(tip_rack, 0))
    captured, _ = _record_send(p)
    for mode in (Pipettes.LLDMode.PRESSURE, Pipettes.LLDMode.DUAL):
      with pytest.raises(NotImplementedError, match=f"{mode.name} LLD is not supported"):
        await p.head8.aspirate(
          containers=_column(src_plate, 0),
          volume=10,
          disable_volume_correction=True,
          lld_mode=mode,
          p_lld=PrepCmd.PLldParameters(
            default_values=False,
            sensitivity=1,
            dispenser_seek_speed=5.0,
            lld_height_difference=0.0,
            detect_mode=0,
          ),
        )
    assert captured == []

    await p.stop()

  asyncio.run(_run())


def test_head8_aspirate_lld_and_tadm_sends_mphaspirate_with_lld_tadm2():
  """lld_mode=CAPACITIVE + tadm= → MphAspirateWithLldTadm2."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0),
      volume=10,
      disable_volume_correction=True,
      lld_mode=Pipettes.LLDMode.CAPACITIVE,
      tadm=PrepCmd.TadmParameters.default(),
    )

    lld_tadm_cmds = [c for c in captured if isinstance(c, PrepCmd.MphAspirateWithLldTadm2)]
    assert len(lld_tadm_cmds) == 1, f"Expected 1 MphAspirateWithLldTadm2, got {len(lld_tadm_cmds)}"

    await p.stop()

  asyncio.run(_run())


def test_head8_dispense_lld_pressure_raises():
  """lld_mode=PRESSURE on dispense raises ValueError — pressure LLD needs aspiration."""

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0), volume=10, disable_volume_correction=True
    )

    with pytest.raises(ValueError, match="PRESSURE"):
      await p.head8.dispense(
        containers=_column(dst_plate, 0),
        volume=10,
        disable_volume_correction=True,
        lld_mode=Pipettes.LLDMode.PRESSURE,
      )

    await p.stop()

  asyncio.run(_run())


def test_head8_command_version_override_v1():
  """command_version='v1' per-call override forces v1 even when v2 is available."""

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)

    spots = _column(tip_rack, 0)
    await p.head8.pick_up_tips(spots)
    await p.head8.aspirate(
      containers=_column(src_plate, 0),
      volume=10,
      disable_volume_correction=True,
      command_version="v1",
    )
    await p.head8.dispense(
      containers=_column(dst_plate, 0),
      volume=10,
      disable_volume_correction=True,
      command_version="v1",
    )

    v1_asp = [c for c in captured if type(c) is PrepCmd.MphAspirateNoLldMonitoring]
    v2_asp = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    v1_disp = [c for c in captured if type(c) is PrepCmd.MphDispenseNoLld]
    v2_disp = [c for c in captured if isinstance(c, PrepCmd.MphDispenseNoLld2)]

    assert len(v1_asp) == 1, f"Expected 1 V1 aspirate with override, got {len(v1_asp)}"
    assert len(v2_asp) == 0, "V2 aspirate must not be sent with command_version='v1'"
    assert len(v1_disp) == 1, f"Expected 1 V1 dispense with override, got {len(v1_disp)}"
    assert len(v2_disp) == 0, "V2 dispense must not be sent with command_version='v1'"

    await p.stop()

  asyncio.run(_run())


def test_head8_surface_following_distance_scales_or_disables_following():
  """A distance scales the profile so the tip sinks that far; 0 sends none and tube_radius 0."""

  async def _run() -> None:
    deck = await make_prep_deck()
    tip_rack = await place(deck, "hamilton_96_tiprack_50uL_NTR", "ntr", 3)
    plate = await place(deck, "cor_96_wellplate_360uL_Fb", "plate", 0)
    assert isinstance(tip_rack, handles.TipRack) and isinstance(plate, handles.Plate)
    p = await _setup(deck)
    assert p.head8 is not None

    captured, _ = _record_send(p)
    await p.head8.pick_up_tips(_column(tip_rack, 0))
    wells = _column(plate, 0)
    await _set_volumes(wells, 200.0)

    await p.head8.aspirate(
      containers=wells,
      volume=20,
      liquid_height=3.0,
      surface_following_distance=0.5,
      disable_volume_correction=True,
    )
    asp = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    params = asp[0].aspirate_parameters[0]
    assert _get_profile_drop(params.container_description, 3.0, 20.0) == pytest.approx(
      0.5, abs=1e-3
    )

    await p.head8.dispense(
      containers=wells, volume=20, liquid_height=3.0, disable_volume_correction=True
    )
    captured.clear()
    await p.head8.aspirate(
      containers=wells,
      volume=20,
      liquid_height=3.0,
      surface_following_distance=0.0,
      disable_volume_correction=True,
    )
    asp = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    params = asp[0].aspirate_parameters[0]
    assert params.container_description == []
    assert params.common.tube_radius == 0.0


def test_head8_follows_nothing_unless_asked_and_auto_searches_capacitive():
  """By default no profile and tube_radius 0; auto searches CAPACITIVE and sends the profile."""

  async def _run() -> None:
    deck, tip_rack, src_plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    captured, _ = _record_send(p)
    await p.head8.pick_up_tips(_column(tip_rack, 0))
    wells = _column(src_plate, 0)

    await p.head8.aspirate(containers=wells, volume=10, disable_volume_correction=True)
    asp = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    params = asp[0].aspirate_parameters[0]
    assert params.container_description == []
    assert params.common.tube_radius == 0.0

    await p.head8.aspirate(
      containers=wells, volume=10, disable_volume_correction=True, auto_surface_following=True
    )
    lld = [c for c in captured if isinstance(c, PrepCmd.MphAspirateWithLld2)]
    assert len(lld) == 1
    assert lld[0].aspirate_parameters[0].container_description != []
    await p.stop()

  asyncio.run(_run())


def test_head8_auto_surface_following_refused_beside_a_distance_or_without_a_surface():
  """Auto beside a distance, or under OFF without a liquid height, is refused before sending."""

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    await p.head8.pick_up_tips(_column(tip_rack, 0))
    captured, _ = _record_send(p)
    refused: List[Dict[str, Any]] = [
      {"surface_following_distance": 1.0},
      {"lld_mode": Pipettes.LLDMode.OFF},
    ]
    for kwargs in refused:
      for call, wells in (
        (p.head8.aspirate, _column(src_plate, 0)),
        (p.head8.dispense, _column(dst_plate, 0)),
      ):
        with pytest.raises(ValueError, match="auto_surface_following"):
          await call(
            containers=wells,
            volume=10,
            disable_volume_correction=True,
            auto_surface_following=True,
            **kwargs,
          )
    assert captured == []
    await p.stop()

  asyncio.run(_run())


# ---------------------------------------------------------------------------
# Liquid classes
# ---------------------------------------------------------------------------


def test_head8_takes_the_tips_class_and_refuses_what_one_piston_cannot_do():
  """Per probe through the resolver, as `Pipettes`: a missing class, 8 different ones and a class
  beside `disable_volume_correction` are refused before sending; the class corrects the piston."""
  from pylabrobot.hamilton.star.liquid_classes.mapping import (
    StandardVolume_Water_DispenseSurface_Part,
    Tip_50ul_Water_DispenseSurface_Empty,
  )

  async def _run() -> None:
    deck, tip_rack, src_plate, dst_plate = await _make_deck(volume_tracking=True)
    p = await _setup(deck)
    assert p.head8 is not None
    await p.head8.pick_up_tips(_column(tip_rack, 0))
    captured, _ = _record_send(p)
    wells = _column(src_plate, 0)
    water = Tip_50ul_Water_DispenseSurface_Empty
    other = StandardVolume_Water_DispenseSurface_Part
    for kwargs, refusal in (
      ({}, "no liquid class is known for channel 0's tip.*blow_out=True, which has one"),
      ({"hamilton_liquid_classes": [water] * 7 + [other]}, "give one liquid class for all"),
      ({"hamilton_liquid_classes": [water] * 7}, "a single HLC or length-8 list"),
      ({"hamilton_liquid_classes": water, "disable_volume_correction": True}, "as given"),
    ):
      with pytest.raises(ValueError, match=refusal):
        await p.head8.aspirate(containers=wells, volume=50, liquid_height=2.0, **kwargs)
    assert not [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    await _set_volumes(wells, 100.0)
    await p.head8.aspirate(containers=wells, volume=50, blow_out=True)
    await p.head8.dispense(containers=_column(dst_plate, 0), volume=50, blow_out=True)
    (aspirate,) = [c for c in captured if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)]
    (dispense,) = [c for c in captured if isinstance(c, PrepCmd.MphDispenseNoLld2)]
    assert aspirate.aspirate_parameters[0].common.liquid_volume == pytest.approx(54.2)
    assert aspirate.aspirate_parameters[0].aspirate.blowout_volume == pytest.approx(1.0)
    assert dispense.dispense_parameters[0].common.liquid_volume == pytest.approx(54.2)
    # The wells and tips book the liquid, not the corrected piston volume.
    assert await _volumes(wells) == [pytest.approx(50.0)] * 8
    assert await _volumes(_column(dst_plate, 0)) == [pytest.approx(50.0)] * 8
    await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize("lld", [False, True])
@pytest.mark.parametrize("tadm", [False, True])
def test_head8_pre_mix_encoded_in_all_aspiration_variants(version, lld, tadm):
  async def _run():
    deck, rack, plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      await p.head8.pick_up_tips(_column(rack, 0))
      captured, _ = _record_send(p)
      await p.head8.aspirate(
        containers=_column(plate, 0),
        volume=5,
        pre_mix=Mix(volume=20, repetitions=3, flow_rate=40),
        mix_position_from_liquid_surface=2,
        disable_volume_correction=True,
        lld_mode=Pipettes.LLDMode.CAPACITIVE if lld else Pipettes.LLDMode.OFF,
        tadm=PrepCmd.TadmParameters.default() if tadm else None,
        command_version=version,
      )
      command_type = Head8._ASPIRATE_CMD[(lld, tadm, version == "v2")]
      commands: list[Any] = [c for c in captured if isinstance(c, command_type)]
      assert len(commands) == 1
      block = commands[0].aspirate_parameters[0].mix
      assert (block.volume, block.cycles, block.speed, block.z_offset) == (20, 3, 40, 2)
      assert not block.default_values
    finally:
      await p.stop()


def test_the_head_pushes_the_channels_forward_to_its_clearance():
  """The head sent forward leaves the rear channel its clearance in front of probe 0."""

  async def _run() -> None:
    deck, *_ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None and p.pipettes is not None
    await p.head8.move_to_position(150.0, 250.0, 167.5)
    head = await p.head8.get_reference_point_location()
    rear = await p.pipettes.get_reference_point_location(0)
    assert head is not None and rear is not None
    assert (head.x, head.y) == (pytest.approx(150.0), pytest.approx(250.0))
    assert rear.y == pytest.approx(250.0 - HEAD8_CLEARANCE_Y)
    await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize("repetitions", [1, 5])
@pytest.mark.parametrize("fail_mix", [False, True])
def test_head8_mix_cycles_and_volume_tracking(version, repetitions, fail_mix):
  async def _run():
    deck, rack, plate, _ = await _make_deck(volume_tracking=True)
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      await p.head8.pick_up_tips(_column(rack, 0))
      wells = _column(plate, 0)
      await _set_volumes(wells, 100)
      captured = []
      orig_send = p.send_command
      asp_type = Head8._ASPIRATE_CMD[(False, False, version == "v2")]
      disp_type = Head8._DISPENSE_CMD[(False, version == "v2")]

      async def recording(command, **kwargs):
        captured.append(command)
        if fail_mix and isinstance(command, asp_type):
          raise RuntimeError("mix failed")
        return await orig_send(command, **kwargs)

      p.send_command = recording  # type: ignore[method-assign]

      async def run_mix():
        assert p.head8 is not None
        await p.head8.mix(
          containers=wells,
          mix=Mix(volume=20, repetitions=repetitions, flow_rate=40),
          command_version=version,
        )

      if fail_mix:
        with pytest.raises(RuntimeError, match="mix failed"):
          await run_mix()
      else:
        await run_mix()
      asp: list[Any] = [c for c in captured if isinstance(c, asp_type)]
      disp: list[Any] = [c for c in captured if isinstance(c, disp_type)]
      assert len(asp) == 1
      assert disp == []
      a = asp[0].aspirate_parameters[0]
      assert a.mix.cycles == repetitions
      assert not a.mix.default_values
      assert a.mix.volume == 20
      assert a.mix.speed == 40
      assert a.common.liquid_volume == 0
      assert a.common.transport_air_volume == 0
      assert a.aspirate.prewet_volume == a.aspirate.blowout_volume == 0
      assert await _volumes(wells) == [100] * 8
      assert [t.volume for t in await p.head8._require_mounted_tips()] == [0] * 8
    finally:
      await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize(
  "spec, message",
  [
    (Mix(volume=0, repetitions=2, flow_rate=40), "volume"),
    (Mix(volume=float("nan"), repetitions=2, flow_rate=40), "volume"),
    (Mix(volume=20, repetitions=0, flow_rate=40), "repetitions"),
    (Mix(volume=20, repetitions=256, flow_rate=40), "repetitions"),
    (Mix(volume=20, repetitions=2, flow_rate=0), "flow_rate"),
    (Mix(volume=20, repetitions=2, flow_rate=float("inf")), "flow_rate"),
    (Mix(volume=20, repetitions=2, flow_rate=40, auto_surface_following=True), "surface following"),
    (
      Mix(volume=20, repetitions=2, flow_rate=40, surface_following_distance=1),
      "surface following",
    ),
    (Mix(volume=100, repetitions=2, flow_rate=40), "capacity"),
  ],
)
def test_head8_mix_rejects_invalid_spec_before_sending(spec, message):
  async def _run():
    deck, rack, plate, _ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      await p.head8.pick_up_tips(_column(rack, 0))
      captured, _ = _record_send(p)
      with pytest.raises(ValueError, match=message):
        await p.head8.mix(containers=_column(plate, 0), mix=spec)
      assert captured == []
    finally:
      await p.stop()

  asyncio.run(_run())


@pytest.mark.parametrize("read_timeout", [None, 123])
def test_head8_pre_mix_timeout_and_transient_volume_validation(read_timeout):
  async def _run():
    deck, rack, plate, _ = await _make_deck(volume_tracking=True)
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      await p.head8.pick_up_tips(_column(rack, 0))
      wells = _column(plate, 0)
      await _set_volumes(wells, 10)
      captured = []
      orig_send = p.send_command

      async def recording(command, **kwargs):
        captured.append((command, kwargs))
        return await orig_send(command, **kwargs)

      p.send_command = recording  # type: ignore[method-assign]
      spec = Mix(volume=20, repetitions=10, flow_rate=5)
      with pytest.raises(TooLittleLiquidError, match="too little liquid"):
        await p.head8.aspirate(containers=wells, volume=5, pre_mix=spec)
      assert captured == []
      await _set_volumes(wells, 100)
      await p.head8.aspirate(
        containers=wells,
        volume=5,
        pre_mix=spec,
        lld_mode=Pipettes.LLDMode.OFF,
        disable_volume_correction=True,
        read_timeout=read_timeout,
      )
      timeouts = [
        kw["read_timeout"]
        for c, kw in captured
        if isinstance(c, PrepCmd.MphAspirateNoLldMonitoring2)
      ]
      assert timeouts == [
        read_timeout if read_timeout is not None else p.default_read_timeout + 100
      ]
      assert await _volumes(wells) == [95] * 8
      assert [t.volume for t in await p.head8._require_mounted_tips()] == [5] * 8
      captured.clear()
      with pytest.raises(ValueError, match="empty tips"):
        await p.head8.mix(containers=wells, mix=spec)
      assert captured == []
    finally:
      await p.stop()

  asyncio.run(_run())


def test_head8_mix_shared_container_requires_eight_draws_and_returns_them():
  async def _run():
    deck, rack, _, _ = await _make_deck()
    trough = await deck.store.create(
      build.resource(
        "trough",
        Coordinate(30, 80, 30),
        kind=pb.RESOURCE_KIND_CONTAINER,
        container=pb.ContainerSpec(max_volume=30 * 80 * 30, material_z_thickness=1),
        state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
      ),
      name="trough",
      parent=deck,
      location=Coordinate(100, 100, 0),
    )
    assert isinstance(trough, handles.Container)
    p = await _setup(deck)
    assert p.head8 is not None
    try:
      await p.head8.pick_up_tips(_column(rack, 0))
      captured, _ = _record_send(p)
      await trough.set_volume(100)
      spec = Mix(volume=20, repetitions=3, flow_rate=40)
      with pytest.raises(TooLittleLiquidError):
        await p.head8.mix(containers=[trough], mix=spec)
      assert captured == []
      await trough.set_volume(500)
      await p.head8.mix(containers=[trough], mix=spec)
      assert await trough.get_volume() == 500
      assert [t.volume for t in await p.head8._require_mounted_tips()] == [0] * 8
    finally:
      await p.stop()


def test_a_channel_sent_into_the_heads_clearance_is_refused_unless_it_may_make_space():
  """Without make_space nothing moves; with it the head goes back just far enough."""

  async def _run() -> None:
    deck, *_ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None and p.pipettes is not None
    await p.head8.move_to_position(150.0, 150.0, 167.5)
    captured, _ = _record_send(p)
    with pytest.raises(ValueError, match="make_space=True moves the head back"):
      await p.pipettes.move_to_xy_positions(150.0, {0: 300.0, 1: 280.0})
    assert not [c for c in captured if isinstance(c, PrepCmd.PrepMoveToPosition)]

    await p.pipettes.move_to_xy_positions(150.0, {0: 300.0, 1: 280.0}, make_space=True)
    head = await p.head8.get_reference_point_location()
    rear = await p.pipettes.get_reference_point_location(0)
    assert head is not None and rear is not None
    assert head.y == pytest.approx(300.0 + HEAD8_CLEARANCE_Y)
    assert rear.y == pytest.approx(300.0)
    await p.stop()

  asyncio.run(_run())


def test_move_to_safe_z_raises_the_head_where_it_stands():
  """Straight up to the traverse height, with the tips' length taken off what probe 0 carries."""

  async def _run() -> None:
    deck, tip_rack, *_ = await _make_deck()
    p = await _setup(deck)
    assert p.head8 is not None
    await p.head8.pick_up_tips(_column(tip_rack, 0))
    await p.head8.move_to_position(150.0, 250.0, 100.0)
    captured, _ = _record_send(p)
    tip = await p.head8.get_mounted_tip(0)
    assert tip is not None
    z = await p.head8.move_to_safe_z()
    assert z == pytest.approx(167.5 - (tip.size.z - tip.fitting_depth))
    moves = [c for c in captured if isinstance(c, PrepCmd.MphMoveToPosition)]
    assert [(m.x_position, m.y_position) for m in moves] == [(150.0, 250.0)]
    at = await p.head8.get_reference_point_location()
    assert at is not None and at.z == pytest.approx(z)
    await p.stop()

  asyncio.run(_run())
