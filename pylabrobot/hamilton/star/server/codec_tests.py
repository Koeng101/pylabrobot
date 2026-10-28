"""Every STAR method's arguments and result go over and come back as they were sent."""

import dataclasses
import datetime
import enum
import inspect
import typing
import unittest
from typing import Any, Dict, List, cast

from pylabrobot.hamilton.liquid_classes.base import HamiltonLiquidClass
from pylabrobot.hamilton.star import STARlet
from pylabrobot.hamilton.star.server import codec, services
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
    inner, optional = codec.strip_optional(t)
    if codec.is_handle(inner):
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
      return self.of(codec.members(inner)[-1])
    if codec.is_list(inner):
      element = typing.get_args(inner)[0]
      _, element_optional = codec.strip_optional(element)
      return [self.of(element), None if element_optional else self.of(element)]
    if typing.get_origin(inner) is tuple:
      args = typing.get_args(inner)
      if args[-1] is Ellipsis:
        return (self.of(args[0]), self.of(args[0]))
      return tuple(self.of(a) for a in args)
    if typing.get_origin(inner) is dict:
      key, value = typing.get_args(inner)
      key_inner, _ = codec.strip_optional(key)
      sample_key = 1.5 if key_inner is float else self.of(key)
      return {sample_key: self.of(value)}
    if dataclasses.is_dataclass(inner) or typing.is_typeddict(inner):
      values = {name: self.of(field_t) for name, field_t in codec._record_fields(inner)}
      return values if typing.is_typeddict(inner) else codec._make_record(inner, values)
    raise TypeError(f"no sample for {inner}")


def comparable(value: Any) -> Any:
  """A value with its resources by id, so a handle and the reference it went over as compare."""
  if isinstance(value, handles.Resource):
    return ("resource", value.id)
  if isinstance(value, codec._Ref):
    return ("resource", value.id)
  if isinstance(value, (Coordinate, Rotation)):
    return (type(value).__name__, value.x, value.y, value.z)
  if isinstance(value, HamiltonLiquidClass):
    return ("liquid class", comparable(vars(value)))
  if isinstance(value, (list, tuple)):
    return (type(value).__name__, [comparable(v) for v in value])
  if isinstance(value, dict):
    return {k: comparable(v) for k, v in value.items()}
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return (type(value).__name__, comparable(vars(value)))
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
    for service in services.SERVICES:
      cls, _ = services.SERVICES[service]
      for name, rpc in services.rpcs(service).items():
        with self.subTest(method=f"{cls.__name__}.{name}"):
          fn = getattr(cls, name)
          hints = typing.get_type_hints(fn)
          kwargs = {}
          for p in list(inspect.signature(fn).parameters.values())[1:]:
            if p.kind in (p.VAR_KEYWORD, p.VAR_POSITIONAL):
              continue
            kwargs[p.name] = self.samples.of(codec._parameter_type(p, hints))
          request = codec.encode_request(cls, name, rpc.request(), (), kwargs)
          wire = rpc.request.FromString(request.SerializeToString())
          decoded = codec.decode_request(cls, name, wire, services.ROUTING.get(service, ()))
          decoded = await codec.resolve(self.server, decoded)
          self.assertEqual(comparable(decoded), comparable(kwargs))

  async def test_every_methods_result(self):
    for service in services.SERVICES:
      cls, _ = services.SERVICES[service]
      for name, rpc in services.rpcs(service).items():
        result_t = typing.get_type_hints(getattr(cls, name)).get("return", inspect.Parameter.empty)
        if result_t is type(None) or not rpc.response.DESCRIPTOR.fields:
          continue
        values: List[Any] = (
          ["the raw reply", {"ab": 1, "cd": "xy", "ef": [1, 2], "gh": ["a", "b"]}, None]
          if result_t is inspect.Parameter.empty
          else [self.samples.of(result_t)]
        )
        for value in values:
          with self.subTest(method=f"{cls.__name__}.{name}", value=value):
            response = codec.encode_response(cls, name, rpc.response(), value)
            wire = rpc.response.FromString(response.SerializeToString())
            self.assertEqual(comparable(codec.decode_response(cls, name, wire)), comparable(value))
