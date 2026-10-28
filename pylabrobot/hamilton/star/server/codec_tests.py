"""Every STAR method's arguments and result go over and come back as they were sent."""

import dataclasses
import datetime
import enum
import inspect
import typing
import unittest
from typing import Any, Dict, List, cast
from unittest import mock

from pylabrobot.hamilton.liquid_classes.base import HamiltonLiquidClass
from pylabrobot.hamilton.star import STARlet
from pylabrobot.hamilton.star.server import generate, wire
from pylabrobot.hamilton.star.server.generated_codec import RPCS
from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.resources import (
  azenta_96_wellplate_200uL_Vb_4titudeframestar,
  hamilton_96_tiprack_300uL_filter,
  hamilton_plate_carrier_L5_ac,
  hamilton_tip_carrier_L5,
)
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.v1 import types_pb2 as pb


def _liquid_class() -> HamiltonLiquidClass:
  hints = typing.get_type_hints(HamiltonLiquidClass.__init__)
  values: Dict[str, Any] = {name: 1.5 for name in hints if name not in ("return", "curve")}
  return HamiltonLiquidClass(curve={10.0: 11.5, 50.0: 52.0}, **values)


class _Samples:
  """A value of every type a STAR method takes or returns, its resources from a real deck."""

  def __init__(self, pool: List[handles.Resource]):
    self.pool = pool

  def of(self, t: Any) -> Any:
    inner, optional = generate.strip_optional(t)
    if generate.is_handle(inner):
      return next(h for h in self.pool if isinstance(h, inner))
    if inner is float:
      return 1.25
    if inner is bool:
      return True
    if inner is int:
      return 3
    if inner is str or inner is Any or inner is inspect.Parameter.empty:
      return "ab"
    if typing.get_origin(inner) is typing.Literal:
      return typing.get_args(inner)[-1]
    if isinstance(inner, type) and issubclass(inner, enum.Enum):
      return list(inner)[-1]
    if inner is Coordinate:
      return Coordinate(1.5, 2.5, 3.5)
    if inner is Rotation:
      return Rotation(0, 0, 90.0)
    if inner is datetime.date:
      return datetime.date(2022, 3, 16)
    if inner is Mix:
      return Mix(volume=10.0, repetitions=2, flow_rate=50.0)
    if inner is HamiltonLiquidClass:
      return _liquid_class()
    if inner is pb.ResourceAttributes:
      return pb.ResourceAttributes(name="tip")
    if inner is pb.ResourceNode:
      return pb.ResourceNode(id=b"\x01", attributes=pb.ResourceAttributes(name="tip"))
    if typing.get_origin(inner) is typing.Union:
      return self.of(generate.members(inner)[-1])
    if generate.is_list(inner):
      element = typing.get_args(inner)[0]
      _, element_optional = generate.strip_optional(element)
      return [self.of(element), None if element_optional else self.of(element)]
    if typing.get_origin(inner) is tuple:
      args = typing.get_args(inner)
      if args[-1] is Ellipsis:
        return (self.of(args[0]), self.of(args[0]))
      return tuple(self.of(a) for a in args)
    if typing.get_origin(inner) is dict:
      key, value = typing.get_args(inner)
      key_inner, _ = generate.strip_optional(key)
      sample_key = 1.5 if key_inner is float else self.of(key)
      return {sample_key: self.of(value)}
    if dataclasses.is_dataclass(inner) or typing.is_typeddict(inner):
      values = {name: self.of(field_t) for name, field_t in generate.record_fields(inner)}
      return values if typing.is_typeddict(inner) else inner(**values)
    raise TypeError(f"no sample for {inner}")


def comparable(value: Any) -> Any:
  """A value with its resources by id, so a handle and the reference it went over as compare."""
  if isinstance(value, handles.Resource):
    return ("resource", value.id)
  if isinstance(value, (Coordinate, Rotation)):
    return (type(value).__name__, value.x, value.y, value.z)
  if isinstance(value, HamiltonLiquidClass):
    return ("liquid class", comparable(value.serialize()))
  if isinstance(value, (list, tuple)):
    return (type(value).__name__, [comparable(v) for v in value])
  if isinstance(value, dict):
    return {k: comparable(v) for k, v in value.items()}
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return (
      type(value).__name__,
      [(f.name, comparable(dataclasses.asdict(value)[f.name])) for f in dataclasses.fields(value)],
    )
  return value


class RoundTripTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    star = STARlet(simulation=True)
    await star.create_resources()
    deck = star.deck
    assert deck is not None
    server = star.resource_server
    tip_carrier = cast(
      handles.Carrier,
      await deck.assign_child_resource(hamilton_tip_carrier_L5(name="tc"), track=1),
    )
    tips = await tip_carrier[0].assign_child_resource(hamilton_96_tiprack_300uL_filter(name="tips"))
    plate_carrier = cast(
      handles.Carrier,
      await deck.assign_child_resource(hamilton_plate_carrier_L5_ac(name="pc"), track=7),
    )
    plate = await plate_carrier[0].assign_child_resource(
      azenta_96_wellplate_200uL_Vb_4titudeframestar(name="plate")
    )
    assert isinstance(tips, handles.TipRack) and isinstance(plate, handles.Plate)
    trash = next(h for h in await deck.get_children() if isinstance(h, handles.Trash))
    self.server = server
    self.samples = _Samples(
      [tips.get_item("A1"), tips, plate.get_well("A1"), plate, trash, plate_carrier]
    )

  async def test_every_methods_arguments(self):
    self.assertEqual(len(RPCS), sum(len(generate.rpcs(s)) for s in generate.SERVICES))
    for rpc in RPCS:
      name = rpc.method.__name__
      with self.subTest(method=rpc.method.__qualname__, rpc=rpc.service):
        hints = typing.get_type_hints(rpc.method)
        kwargs: Dict[str, Any] = {}
        for p in list(inspect.signature(rpc.method).parameters.values())[1:]:
          if p.kind is p.VAR_KEYWORD:
            kwargs[p.name] = {}
          else:
            kwargs[p.name] = self.samples.of(generate.parameter_type(p, hints))
        request = rpc.encode_request(**kwargs)
        wire_request = rpc.request.FromString(request.SerializeToString())
        target = mock.AsyncMock()
        refs = await wire.refs_in(self.server, wire_request)
        await rpc.call(target, wire_request, refs)
        (call,) = target.method_calls
        self.assertEqual(call[0], name)
        expected = {k: v for k, v in kwargs.items() if not isinstance(v, dict) or v}
        self.assertEqual(comparable(call[2]), comparable(expected))

  async def test_every_methods_result(self):
    for rpc in RPCS:
      result_t = typing.get_type_hints(rpc.method).get("return", inspect.Parameter.empty)
      if result_t is type(None) or not rpc.response.DESCRIPTOR.fields:
        continue
      values: List[Any] = (
        ["the raw reply", {"ab": 1, "cd": "xy", "ef": [1, 2], "gh": ["a", "b"]}, None]
        if result_t is inspect.Parameter.empty
        else [self.samples.of(result_t)]
      )
      for value in values:
        with self.subTest(method=rpc.method.__qualname__, value=value):
          response = rpc.encode_response(value)
          wire_response = rpc.response.FromString(response.SerializeToString())
          self.assertEqual(comparable(rpc.decode_response(wire_response)), comparable(value))


class GeneratedTests(unittest.TestCase):
  def test_the_generated_files_are_what_the_generator_writes(self):
    for path, text in generate.render().items():
      with self.subTest(path=path):
        with open(path, encoding="utf-8") as f:
          self.assertEqual(
            f.read(), text, "run `python -m pylabrobot.hamilton.star.server.generate`"
          )
