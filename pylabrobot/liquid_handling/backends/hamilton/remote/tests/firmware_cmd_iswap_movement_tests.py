"""iSwap movement firmware command tests for the remote STAR backend.

These tests mirror STARIswapMovementTests from STAR_tests.py, verifying that
iSwap plate/lid movements through the remote RPC path produce identical
firmware commands to a local STARBackend.

Requires a separate deck layout (PLT_CAR_L5MD_A00 at rails=15,
PLT_CAR_P3AC_A01 at rails=3) via the star_service_iswap fixture.
"""


import pytest

from pylabrobot.liquid_handling.standard import (
  GripDirection,
  ResourcePickup,
)
from pylabrobot.resources import (
  CellTreat_96_wellplate_350ul_Ub,
  Coordinate,
)

from .conftest import StarServiceIswapFixture
from .firmware_cmd_tests import (
  _any_write_and_read_command_call,
  _build_resource_drop,
  _do_move_on_deck,
  _reset_backend_state,
)


class TestFirmwareCmdIswapMovement:
  @pytest.mark.asyncio
  async def test_simple_movement(self, star_service_iswap: StarServiceIswapFixture):
    """Move plate to plt_car[1] and back. Mirrors STARIswapMovementTests.test_simple_movement."""
    _reset_backend_state(star_service_iswap.backend)
    deck = star_service_iswap.deck
    plate = star_service_iswap.plate
    plt_car = star_service_iswap.plt_car

    pickup_dist = 13.2 - 3.33

    # Move 1: plate from plt_car[0] to plt_car[1]
    site1 = plt_car[1]
    pickup1 = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop1 = _build_resource_drop(
      deck, plate, site1, pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
    )
    await star_service_iswap.remote.pick_up_resource(pickup=pickup1)
    await star_service_iswap.remote.drop_resource(drop=drop1)
    _do_move_on_deck(plate, site1, GripDirection.FRONT, GripDirection.FRONT)

    # Move 2: plate from plt_car[1] to plt_car[0]
    site0 = plt_car[0]
    pickup2 = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop2 = _build_resource_drop(
      deck, plate, site0, pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.FRONT,
    )
    await star_service_iswap.remote.pick_up_resource(pickup=pickup2)
    await star_service_iswap.remote.drop_resource(drop=drop2)
    _do_move_on_deck(plate, site0, GripDirection.FRONT, GripDirection.FRONT)

    star_service_iswap.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0PPid0001xs04829xd0yj1141yd0zj2143zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0002xs04829xd0yj2101yd0zj2143zd0th2800te2800gr1go1308ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PPid0003xs04829xd0yj2101yd0zj2143zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0004xs04829xd0yj1141yd0zj2143zd0th2800te2800gr1go1308ga0gc0"
      ),
    ])

  @pytest.mark.asyncio
  async def test_movement_to_portrait_site_left(self, star_service_iswap: StarServiceIswapFixture):
    """Move plate to portrait site with LEFT drop. Mirrors test_movement_to_portrait_site_left."""
    _reset_backend_state(star_service_iswap.backend)
    deck = star_service_iswap.deck
    plate = star_service_iswap.plate
    plt_car = star_service_iswap.plt_car
    plt_car2 = star_service_iswap.plt_car2

    pickup_dist = 13.2 - 3.33

    # Move 1: plate from plt_car[0] to plt_car2[0] with LEFT drop
    pickup1 = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop1 = _build_resource_drop(
      deck, plate, plt_car2[0], pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.LEFT,
    )
    await star_service_iswap.remote.pick_up_resource(pickup=pickup1)
    await star_service_iswap.remote.drop_resource(drop=drop1)
    _do_move_on_deck(plate, plt_car2[0], GripDirection.FRONT, GripDirection.LEFT)

    # Move 2: plate from plt_car2[0] back to plt_car[0] with LEFT drop
    pickup2 = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop2 = _build_resource_drop(
      deck, plate, plt_car[0], pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.LEFT,
    )
    await star_service_iswap.remote.pick_up_resource(pickup=pickup2)
    await star_service_iswap.remote.drop_resource(drop=drop2)
    _do_move_on_deck(plate, plt_car[0], GripDirection.FRONT, GripDirection.LEFT)

    star_service_iswap.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0PPid0001xs04829xd0yj1141yd0zj2143zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0002xs02317xd0yj1644yd0zj1884zd0th2800te2800gr4go1308ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PPid0003xs02317xd0yj1644yd0zj1884zd0gr1th2800te2800gw4go0881gb0818gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0004xs04829xd0yj1141yd0zj2143zd0th2800te2800gr4go0881ga0gc0",
      ),
    ])

  @pytest.mark.asyncio
  async def test_movement_to_portrait_site_right(self, star_service_iswap: StarServiceIswapFixture):
    """Move plate to portrait site with RIGHT drop. Mirrors test_movement_to_portrait_site_right."""
    _reset_backend_state(star_service_iswap.backend)
    deck = star_service_iswap.deck
    plate = star_service_iswap.plate
    plt_car = star_service_iswap.plt_car
    plt_car2 = star_service_iswap.plt_car2

    pickup_dist = 13.2 - 3.33

    # Move 1: plate from plt_car[0] to plt_car2[0] with RIGHT drop
    pickup1 = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop1 = _build_resource_drop(
      deck, plate, plt_car2[0], pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.RIGHT,
    )
    await star_service_iswap.remote.pick_up_resource(pickup=pickup1)
    await star_service_iswap.remote.drop_resource(drop=drop1)
    _do_move_on_deck(plate, plt_car2[0], GripDirection.FRONT, GripDirection.RIGHT)

    # Move 2: plate from plt_car2[0] back to plt_car[0] with RIGHT drop
    pickup2 = ResourcePickup(
      resource=plate, offset=Coordinate.zero(),
      pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
    )
    drop2 = _build_resource_drop(
      deck, plate, plt_car[0], pickup_dist,
      pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.RIGHT,
    )
    await star_service_iswap.remote.pick_up_resource(pickup=pickup2)
    await star_service_iswap.remote.drop_resource(drop=drop2)
    _do_move_on_deck(plate, plt_car[0], GripDirection.FRONT, GripDirection.RIGHT)

    star_service_iswap.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call(
        "C0PPid0001xs04829xd0yj1141yd0zj2143zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0002xs02317xd0yj1644yd0zj1884zd0th2800te2800gr2go1308ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PPid0003xs02317xd0yj1644yd0zj1884zd0gr1th2800te2800gw4go0881gb0818gt20ga0gc0",
      ),
      _any_write_and_read_command_call(
        "C0PRid0004xs04829xd0yj1141yd0zj2143zd0th2800te2800gr2go0881ga0gc0",
      ),
    ])

  @pytest.mark.asyncio
  async def test_move_lid_across_rotated_resources(self, star_service_iswap: StarServiceIswapFixture):
    """Move lid across rotated plates. Mirrors test_move_lid_across_rotated_resources."""
    _reset_backend_state(star_service_iswap.backend)
    deck = star_service_iswap.deck
    plate = star_service_iswap.plate
    plt_car2 = star_service_iswap.plt_car2

    # Create rotated plates on plt_car2
    plate2 = CellTreat_96_wellplate_350ul_Ub(name="plate2", with_lid=False).rotated(z=270)
    plate3 = CellTreat_96_wellplate_350ul_Ub(name="plate3", with_lid=False).rotated(z=90)
    plt_car2[0] = plate2
    plt_car2[1] = plate3

    lid = plate.lid
    assert lid is not None
    pickup_dist = 5.7 - 3.33

    try:
      # Move 1: lid from plate to plate2 (LEFT drop)
      pickup1 = ResourcePickup(
        resource=lid, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop1 = _build_resource_drop(
        deck, lid, plate2, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.LEFT,
      )
      await star_service_iswap.remote.pick_up_resource(pickup=pickup1)
      await star_service_iswap.remote.drop_resource(drop=drop1)
      _do_move_on_deck(lid, plate2, GripDirection.FRONT, GripDirection.LEFT)

      # Move 2: lid from plate2 to plate3 (BACK drop)
      pickup2 = ResourcePickup(
        resource=lid, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop2 = _build_resource_drop(
        deck, lid, plate3, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.BACK,
      )
      await star_service_iswap.remote.pick_up_resource(pickup=pickup2)
      await star_service_iswap.remote.drop_resource(drop=drop2)
      _do_move_on_deck(lid, plate3, GripDirection.FRONT, GripDirection.BACK)

      # Move 3: lid from plate3 back to plate (LEFT drop)
      pickup3 = ResourcePickup(
        resource=lid, offset=Coordinate.zero(),
        pickup_distance_from_top=pickup_dist, direction=GripDirection.FRONT,
      )
      drop3 = _build_resource_drop(
        deck, lid, plate, pickup_dist,
        pickup_direction=GripDirection.FRONT, drop_direction=GripDirection.LEFT,
      )
      await star_service_iswap.remote.pick_up_resource(pickup=pickup3)
      await star_service_iswap.remote.drop_resource(drop=drop3)
      _do_move_on_deck(lid, plate, GripDirection.FRONT, GripDirection.LEFT)

      star_service_iswap.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call(
          "C0PPid0001xs04829xd0yj1142yd0zj2242zd0gr1th2800te2800gw4go1308gb1245gt20ga0gc0",
        ),
        _any_write_and_read_command_call(
          "C0PRid0002xs02318xd0yj1644yd0zj1983zd0th2800te2800gr4go1308ga0gc0",
        ),
        _any_write_and_read_command_call(
          "C0PPid0003xs02318xd0yj1644yd0zj1983zd0gr1th2800te2800gw4go0885gb0822gt20ga0gc0",
        ),
        _any_write_and_read_command_call(
          "C0PRid0004xs02315xd0yj3104yd0zj1983zd0th2800te2800gr3go0885ga0gc0",
        ),
        _any_write_and_read_command_call(
          "C0PPid0005xs02315xd0yj3104yd0zj1983zd0gr1th2800te2800gw4go0885gb0822gt20ga0gc0",
        ),
        _any_write_and_read_command_call(
          "C0PRid0006xs04829xd0yj1142yd0zj2242zd0th2800te2800gr4go0885ga0gc0",
        ),
      ])
    finally:
      # Clean up: restore lid to plate, remove temp plates
      if lid.parent is not None and lid.parent is not plate:
        lid.unassign()
      if lid.parent is None:
        plate.assign_child_resource(lid)
      plate2.unassign()
      plate3.unassign()
