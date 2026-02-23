# mypy: disable-error-code="no-any-return,attr-defined"
"""Round-trip serialization tests for all proto <-> Python conversions."""

import pytest

from pylabrobot.liquid_handling.standard import (
  Drop,
  GripDirection,
  Mix,
  Pickup,
  ResourceDrop,
  ResourceMove,
  ResourcePickup,
  SingleChannelAspiration,
  SingleChannelDispense,
)
from pylabrobot.resources import Coordinate, Resource
from pylabrobot.resources.hamilton import HamiltonTip, TipPickupMethod, TipSize
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.tip import Tip

from pylabrobot.liquid_handling.backends.hamilton.remote.helpers import (
  aspiration_from_proto,
  aspiration_to_proto,
  coordinate_from_proto,
  coordinate_to_proto,
  dispense_from_proto,
  dispense_to_proto,
  drop_from_proto,
  drop_to_proto,
  grip_direction_from_proto,
  grip_direction_to_proto,
  mix_from_proto,
  mix_to_proto,
  pickup_from_proto,
  pickup_to_proto,
  resource_drop_from_proto,
  resource_drop_to_proto,
  resource_move_from_proto,
  resource_move_to_proto,
  resource_pickup_from_proto,
  resource_pickup_to_proto,
  rotation_from_proto,
  rotation_to_proto,
  tip_from_proto,
  tip_to_proto,
)


class _FakeDeck:
  """Minimal deck stub for deserialization tests."""

  def __init__(self):
    self._resources = {}

  def add(self, resource: Resource):
    self._resources[resource.name] = resource

  def get_resource(self, name: str) -> Resource:
    return self._resources[name]


def _assert_rotation_eq(a: Rotation, b: Rotation):
  assert a.x == b.x
  assert a.y == b.y
  assert a.z == b.z


class TestCoordinateRoundTrip:
  def test_basic(self):
    c = Coordinate(x=1.5, y=2.5, z=3.5)
    proto = coordinate_to_proto(c)
    restored = coordinate_from_proto(proto)
    assert c == restored

  def test_zero(self):
    c = Coordinate(x=0, y=0, z=0)
    proto = coordinate_to_proto(c)
    restored = coordinate_from_proto(proto)
    assert c == restored

  def test_negative(self):
    c = Coordinate(x=-10.0, y=-20.5, z=-0.1)
    proto = coordinate_to_proto(c)
    restored = coordinate_from_proto(proto)
    assert c == restored


class TestRotationRoundTrip:
  def test_basic(self):
    r = Rotation(x=0, y=0, z=90)
    proto = rotation_to_proto(r)
    restored = rotation_from_proto(proto)
    _assert_rotation_eq(r, restored)

  def test_nonzero(self):
    r = Rotation(x=45, y=30, z=60)
    proto = rotation_to_proto(r)
    restored = rotation_from_proto(proto)
    _assert_rotation_eq(r, restored)


class TestTipRoundTrip:
  def test_plain_tip(self):
    tip = Tip(
      has_filter=False,
      total_tip_length=95.0,
      maximal_volume=300.0,
      fitting_depth=8.0,
    )
    proto = tip_to_proto(tip)
    restored = tip_from_proto(proto)
    assert isinstance(restored, Tip)
    assert not isinstance(restored, HamiltonTip)
    assert restored.has_filter == tip.has_filter
    assert restored.total_tip_length == tip.total_tip_length
    assert restored.maximal_volume == tip.maximal_volume
    assert restored.fitting_depth == tip.fitting_depth

  def test_hamilton_tip(self):
    tip = HamiltonTip(
      has_filter=True,
      total_tip_length=95.1,
      maximal_volume=1000.0,
      tip_size=TipSize.HIGH_VOLUME,
      pickup_method=TipPickupMethod.OUT_OF_RACK,
    )
    proto = tip_to_proto(tip)
    restored = tip_from_proto(proto)
    assert isinstance(restored, HamiltonTip)
    assert restored.has_filter == tip.has_filter
    assert restored.total_tip_length == tip.total_tip_length
    assert restored.maximal_volume == tip.maximal_volume
    assert restored.tip_size == tip.tip_size
    assert restored.pickup_method == tip.pickup_method

  @pytest.mark.parametrize(
    "tip_size",
    [TipSize.UNDEFINED, TipSize.LOW_VOLUME, TipSize.STANDARD_VOLUME,
     TipSize.HIGH_VOLUME, TipSize.CORE_384_HEAD_TIP, TipSize.XL],
  )
  def test_all_tip_sizes(self, tip_size):
    tip = HamiltonTip(
      has_filter=False,
      total_tip_length=50.0,
      maximal_volume=100.0,
      tip_size=tip_size,
      pickup_method=TipPickupMethod.OUT_OF_RACK,
    )
    proto = tip_to_proto(tip)
    restored = tip_from_proto(proto)
    assert restored.tip_size == tip_size

  def test_pickup_method_out_of_wash(self):
    tip = HamiltonTip(
      has_filter=False,
      total_tip_length=50.0,
      maximal_volume=100.0,
      tip_size=TipSize.STANDARD_VOLUME,
      pickup_method=TipPickupMethod.OUT_OF_WASH_LIQUID,
    )
    proto = tip_to_proto(tip)
    restored = tip_from_proto(proto)
    assert restored.pickup_method == TipPickupMethod.OUT_OF_WASH_LIQUID


class TestMixRoundTrip:
  def test_basic(self):
    mix = Mix(volume=100.0, repetitions=3, flow_rate=50.0)
    proto = mix_to_proto(mix)
    restored = mix_from_proto(proto)
    assert restored.volume == mix.volume
    assert restored.repetitions == mix.repetitions
    assert restored.flow_rate == mix.flow_rate


class TestGripDirectionRoundTrip:
  @pytest.mark.parametrize(
    "direction",
    [GripDirection.FRONT, GripDirection.BACK, GripDirection.LEFT, GripDirection.RIGHT],
  )
  def test_all_directions(self, direction):
    proto = grip_direction_to_proto(direction)
    restored = grip_direction_from_proto(proto)
    assert restored == direction


class TestPickupDropRoundTrip:
  def _make_deck(self):
    deck = _FakeDeck()
    r = Resource(name="spot_A1", size_x=9, size_y=9, size_z=0)
    deck.add(r)
    return deck, r

  def test_pickup_roundtrip(self):
    deck, resource = self._make_deck()
    tip = Tip(has_filter=True, total_tip_length=95.0, maximal_volume=300.0, fitting_depth=8.0)
    op = Pickup(resource=resource, offset=Coordinate(x=1, y=2, z=3), tip=tip)
    proto = pickup_to_proto(op)
    restored = pickup_from_proto(deck, proto)
    assert restored.resource.name == op.resource.name
    assert restored.offset == op.offset
    assert restored.tip.maximal_volume == op.tip.maximal_volume

  def test_drop_roundtrip(self):
    deck, resource = self._make_deck()
    tip = Tip(has_filter=False, total_tip_length=50.0, maximal_volume=100.0, fitting_depth=5.0)
    op = Drop(resource=resource, offset=Coordinate.zero(), tip=tip)
    proto = drop_to_proto(op)
    restored = drop_from_proto(deck, proto)
    assert restored.resource.name == op.resource.name
    assert restored.offset == op.offset


class TestAspirationDispenseRoundTrip:
  def _make_deck(self):
    deck = _FakeDeck()
    r = Resource(name="well_A1", size_x=9, size_y=9, size_z=10)
    deck.add(r)
    return deck, r

  def test_aspiration_minimal(self):
    deck, resource = self._make_deck()
    tip = Tip(has_filter=True, total_tip_length=95.0, maximal_volume=300.0, fitting_depth=8.0)
    op = SingleChannelAspiration(
      resource=resource,
      offset=Coordinate.zero(),
      tip=tip,
      volume=100.0,
      flow_rate=None,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    proto = aspiration_to_proto(op)
    restored = aspiration_from_proto(deck, proto)
    assert restored.volume == 100.0
    assert restored.flow_rate is None
    assert restored.liquid_height is None
    assert restored.mix is None

  def test_aspiration_full(self):
    deck, resource = self._make_deck()
    tip = Tip(has_filter=True, total_tip_length=95.0, maximal_volume=300.0, fitting_depth=8.0)
    op = SingleChannelAspiration(
      resource=resource,
      offset=Coordinate(x=0.5, y=0.5, z=0),
      tip=tip,
      volume=50.0,
      flow_rate=100.0,
      liquid_height=5.0,
      blow_out_air_volume=10.0,
      mix=Mix(volume=30.0, repetitions=2, flow_rate=50.0),
    )
    proto = aspiration_to_proto(op)
    restored = aspiration_from_proto(deck, proto)
    assert restored.volume == 50.0
    assert restored.flow_rate == 100.0
    assert restored.liquid_height == 5.0
    assert restored.blow_out_air_volume == 10.0
    assert restored.mix is not None
    assert restored.mix.volume == 30.0
    assert restored.mix.repetitions == 2

  def test_dispense_roundtrip(self):
    deck, resource = self._make_deck()
    tip = Tip(has_filter=False, total_tip_length=50.0, maximal_volume=100.0, fitting_depth=5.0)
    op = SingleChannelDispense(
      resource=resource,
      offset=Coordinate.zero(),
      tip=tip,
      volume=75.0,
      flow_rate=200.0,
      liquid_height=None,
      blow_out_air_volume=None,
      mix=None,
    )
    proto = dispense_to_proto(op)
    restored = dispense_from_proto(deck, proto)
    assert restored.volume == 75.0
    assert restored.flow_rate == 200.0
    assert restored.liquid_height is None


class TestResourceOpsRoundTrip:
  def _make_deck(self):
    deck = _FakeDeck()
    r = Resource(name="plate_01", size_x=127, size_y=85, size_z=14)
    deck.add(r)
    return deck, r

  def test_resource_pickup(self):
    deck, resource = self._make_deck()
    op = ResourcePickup(
      resource=resource,
      offset=Coordinate(x=0, y=0, z=5),
      pickup_distance_from_top=13.0,
      direction=GripDirection.FRONT,
    )
    proto = resource_pickup_to_proto(op)
    restored = resource_pickup_from_proto(deck, proto)
    assert restored.resource.name == "plate_01"
    assert restored.pickup_distance_from_top == 13.0
    assert restored.direction == GripDirection.FRONT

  def test_resource_move(self):
    deck, resource = self._make_deck()
    op = ResourceMove(
      resource=resource,
      location=Coordinate(x=100, y=200, z=50),
      gripped_direction=GripDirection.LEFT,
      pickup_distance_from_top=10.0,
      offset=Coordinate.zero(),
    )
    proto = resource_move_to_proto(op)
    restored = resource_move_from_proto(deck, proto)
    assert restored.location == Coordinate(x=100, y=200, z=50)
    assert restored.gripped_direction == GripDirection.LEFT

  def test_resource_drop(self):
    deck, resource = self._make_deck()
    op = ResourceDrop(
      resource=resource,
      destination=Coordinate(x=50, y=60, z=70),
      destination_absolute_rotation=Rotation(x=0, y=0, z=0),
      offset=Coordinate.zero(),
      pickup_distance_from_top=13.0,
      pickup_direction=GripDirection.FRONT,
      direction=GripDirection.BACK,
      rotation=90.0,
    )
    proto = resource_drop_to_proto(op)
    restored = resource_drop_from_proto(deck, proto)
    assert restored.destination == Coordinate(x=50, y=60, z=70)
    assert restored.pickup_direction == GripDirection.FRONT
    assert restored.direction == GripDirection.BACK
    assert restored.rotation == 90.0
