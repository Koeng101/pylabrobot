"""Foil piercing firmware command tests for the remote STAR backend.

These tests mirror STARFoilTests from STAR_tests.py, verifying that the
PierceFoilHighLevel RPC produces identical firmware commands to calling
STARBackend.pierce_foil() directly.

Requires a separate deck layout (tip carrier + AGenBio trough plate)
via the star_service_foil fixture.
"""


import pytest

from .conftest import StarServiceFoilFixture
from .firmware_cmd_tests import (
  _any_write_and_read_command_call,
  _reset_backend_state,
)


class TestFirmwareCmdFoilPiercing:
  @pytest.mark.asyncio
  async def test_pierce_foil_wide(self, star_service_foil: StarServiceFoilFixture):
    """Pierce foil with wide spread. Mirrors STARFoilTests.test_pierce_foil_wide."""
    _reset_backend_state(star_service_foil.backend)
    star_service_foil.backend.id_ = 2  # Match STAR_tests.py (after tip pickup)

    star_service_foil.backend._write_and_read_command.side_effect = [
      "C0JXid0051er00/00",
      "C0RYid0052er00/00ry+1530 +1399 +1297 +1196 +1095 +0994 +0892 +0755",
      "C0JYid0053er00/00",
      "C0RZid0054er00/00rz+2476 +2476 +2476 +2476 +2476 +2476 +2476 +2476",
      "C0JZid0055er00/00",
      "C0RYid0056er00/00ry+1530 +1399 +1297 +1196 +1095 +0994 +0892 +0755",
      "C0JYid0057er00/00",
      "C0KZid0058er00/00",
      "C0KZid0059er00/00",
      "C0RZid0060er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
      "C0RZid0061er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
      "C0JZid0062er00/00",
      "C0ZAid0063er00/00",
    ]

    await star_service_foil.remote.pierce_foil_high_level(
      well_names=["plate_well_A1"],
      piercing_channels=[1, 2, 3, 4, 5, 6],
      hold_down_channels=[0, 7],
      move_inwards=4,
      spread="wide",
      one_by_one=False,
    )

    star_service_foil.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call("C0JXid0003xs03702"),
      _any_write_and_read_command_call("C0RYid0004"),
      _any_write_and_read_command_call("C0JYid0005yp1530 1399 1297 1196 1095 0994 0892 0755"),
      _any_write_and_read_command_call("C0RZid0006"),
      _any_write_and_read_command_call("C0JZid0007zp2476 2083 2083 2083 2083 2083 2083 2476"),
      _any_write_and_read_command_call("C0RYid0008"),
      _any_write_and_read_command_call("C0JYid0009yp1530 1399 1297 1196 1095 0994 0892 0755"),
      _any_write_and_read_command_call("C0KZid0010pn08zj2256"),
      _any_write_and_read_command_call("C0KZid0011pn01zj2256"),
      _any_write_and_read_command_call("C0RZid0012"),
      _any_write_and_read_command_call("C0RZid0013"),
      _any_write_and_read_command_call("C0JZid0014zp2256 2406 2406 2406 2406 2406 2406 2256"),
      _any_write_and_read_command_call("C0ZAid0015"),
    ])

  @pytest.mark.asyncio
  async def test_pierce_foil_tight(self, star_service_foil: StarServiceFoilFixture):
    """Pierce foil with tight spread. Mirrors STARFoilTests.test_pierce_foil_tight."""
    _reset_backend_state(star_service_foil.backend)
    star_service_foil.backend.id_ = 2

    star_service_foil.backend._write_and_read_command.side_effect = [
      "C0JXid0064er00/00",
      "C0RYid0065er00/00ry+1530 +1399 +1297 +1196 +1095 +0994 +0892 +0755",
      "C0JYid0066er00/00",
      "C0RZid0067er00/00rz+2476 +2476 +2476 +2476 +2476 +2476 +2476 +2476",
      "C0JZid0068er00/00",
      "C0RYid0069er00/00ry+1530 +1370 +1280 +1190 +1100 +1010 +0920 +0755",
      "C0JYid0070er00/00",
      "C0KZid0071er00/00",
      "C0KZid0072er00/00",
      "C0RZid0073er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
      "C0RZid0074er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
      "C0JZid0075er00/00",
      "C0ZAid0076er00/00",
    ]

    await star_service_foil.remote.pierce_foil_high_level(
      well_names=["plate_well_A1"],
      piercing_channels=[1, 2, 3, 4, 5, 6],
      hold_down_channels=[0, 7],
      move_inwards=4,
      spread="tight",
      one_by_one=False,
    )

    star_service_foil.backend._write_and_read_command.assert_has_calls([
      _any_write_and_read_command_call("C0JXid0003xs03702"),
      _any_write_and_read_command_call("C0RYid0004"),
      _any_write_and_read_command_call("C0JYid0005yp1530 1370 1280 1190 1100 1010 0920 0755"),
      _any_write_and_read_command_call("C0RZid0006"),
      _any_write_and_read_command_call("C0JZid0007zp2476 2083 2083 2083 2083 2083 2083 2476"),
      _any_write_and_read_command_call("C0RYid0008"),
      _any_write_and_read_command_call("C0JYid0009yp1530 1370 1280 1190 1100 1010 0920 0755"),
      _any_write_and_read_command_call("C0KZid0010pn08zj2256"),
      _any_write_and_read_command_call("C0KZid0011pn01zj2256"),
      _any_write_and_read_command_call("C0RZid0012"),
      _any_write_and_read_command_call("C0RZid0013"),
      _any_write_and_read_command_call("C0JZid0014zp2256 2406 2406 2406 2406 2406 2406 2256"),
      _any_write_and_read_command_call("C0ZAid0015"),
    ])

  @pytest.mark.asyncio
  async def test_pierce_foil_portrait_wide(self, star_service_foil: StarServiceFoilFixture):
    """Portrait foil pierce (wide test name, tight spread). Mirrors test_pierce_foil_portrait_wide."""
    _reset_backend_state(star_service_foil.backend)
    star_service_foil.backend.id_ = 2

    plate = star_service_foil.deck.get_resource("plate")
    plate.rotate(z=90)

    try:
      star_service_foil.backend._write_and_read_command.side_effect = [
        "C0JXid0170er00/00",
        "C0RYid0171er00/00ry+1530 +1399 +1297 +1196 +1095 +0994 +0892 +0755",
        "C0JYid0172er00/00",
        "C0RZid0173er00/00rz+2476 +2476 +2476 +2476 +2476 +2476 +2476 +2476",
        "C0JZid0174er00/00",
        "C0RYid0175er00/00ry+1825 +1735 +1582 +1429 +1275 +1122 +0969 +0755",
        "C0JYid0176er00/00",
        "C0KZid0177er00/00",
        "C0KZid0178er00/00",
        "C0RZid0179er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
        "C0RZid0180er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
        "C0JZid0181er00/00",
        "C0ZAid0182er00/00",
      ]

      await star_service_foil.remote.pierce_foil_high_level(
        well_names=["plate_well_A1"],
        piercing_channels=[1, 2, 3, 4, 5, 6],
        hold_down_channels=[0, 7],
        move_inwards=4,
        spread="tight",
        one_by_one=False,
      )

      star_service_foil.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call("C0JXid0003xs02634"),
        _any_write_and_read_command_call("C0RYid0004"),
        _any_write_and_read_command_call("C0JYid0005yp1667 1577 1487 1397 1307 1217 1127 0755"),
        _any_write_and_read_command_call("C0RZid0006"),
        _any_write_and_read_command_call("C0JZid0007zp2476 2083 2083 2083 2083 2083 2083 2476"),
        _any_write_and_read_command_call("C0RYid0008"),
        _any_write_and_read_command_call("C0JYid0009yp1953 1735 1582 1429 1275 1122 0969 0755"),
        _any_write_and_read_command_call("C0KZid0010pn08zj2256"),
        _any_write_and_read_command_call("C0KZid0011pn01zj2256"),
        _any_write_and_read_command_call("C0RZid0012"),
        _any_write_and_read_command_call("C0RZid0013"),
        _any_write_and_read_command_call("C0JZid0014zp2256 2406 2406 2406 2406 2406 2406 2256"),
        _any_write_and_read_command_call("C0ZAid0015"),
      ])
    finally:
      plate.rotate(z=-90)

  @pytest.mark.asyncio
  async def test_pierce_foil_portrait_tight(self, star_service_foil: StarServiceFoilFixture):
    """Portrait foil pierce tight. Mirrors test_pierce_foil_portrait_tight."""
    _reset_backend_state(star_service_foil.backend)
    star_service_foil.backend.id_ = 2

    plate = star_service_foil.deck.get_resource("plate")
    plate.rotate(z=90)

    try:
      star_service_foil.backend._write_and_read_command.side_effect = [
        "C0JXid0183er00/00",
        "C0RYid0184er00/00ry+1953 +1735 +1582 +1429 +1275 +1122 +0969 +0755",
        "C0JYid0185er00/00",
        "C0RZid0186er00/00rz+2476 +2476 +2476 +2476 +2476 +2476 +2476 +2476",
        "C0JZid0187er00/00",
        "C0RYid0188er00/00ry+1953 +1577 +1487 +1397 +1307 +1217 +1127 +0755",
        "C0JYid0189er00/00",
        "C0KZid0190er00/00",
        "C0KZid0191er00/00",
        "C0RZid0192er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
        "C0RZid0193er00/00rz+2256 +2083 +2083 +2083 +2083 +2083 +2083 +2256",
        "C0JZid0194er00/00",
        "C0ZAid0195er00/00",
      ]

      await star_service_foil.remote.pierce_foil_high_level(
        well_names=["plate_well_A1"],
        piercing_channels=[1, 2, 3, 4, 5, 6],
        hold_down_channels=[0, 7],
        move_inwards=4,
        spread="tight",
        one_by_one=False,
      )

      star_service_foil.backend._write_and_read_command.assert_has_calls([
        _any_write_and_read_command_call("C0JXid0003xs02634"),
        _any_write_and_read_command_call("C0RYid0004"),
        _any_write_and_read_command_call("C0JYid0005yp1953 1577 1487 1397 1307 1217 1127 0755"),
        _any_write_and_read_command_call("C0RZid0006"),
        _any_write_and_read_command_call("C0JZid0007zp2476 2083 2083 2083 2083 2083 2083 2476"),
        _any_write_and_read_command_call("C0RYid0008"),
        _any_write_and_read_command_call("C0JYid0009yp1953 1577 1487 1397 1307 1217 1127 0755"),
        _any_write_and_read_command_call("C0KZid0010pn08zj2256"),
        _any_write_and_read_command_call("C0KZid0011pn01zj2256"),
        _any_write_and_read_command_call("C0RZid0012"),
        _any_write_and_read_command_call("C0RZid0013"),
        _any_write_and_read_command_call("C0JZid0014zp2256 2406 2406 2406 2406 2406 2406 2256"),
        _any_write_and_read_command_call("C0ZAid0015"),
      ])
    finally:
      plate.rotate(z=-90)
