"""Which Python class each of the STAR server's services fronts, and which RPC each method is."""

import dataclasses
import importlib
import inspect
from typing import Dict, FrozenSet, List, Type, cast

from google.protobuf import message_factory
from google.protobuf.descriptor import MethodDescriptor, ServiceDescriptor
from google.protobuf.message import Message

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.features.autoload import Autoload
from pylabrobot.hamilton.star.driver.features.core_grippers import CoreGrippers
from pylabrobot.hamilton.star.driver.features.cover import FrontCover
from pylabrobot.hamilton.star.driver.features.head96 import Head96
from pylabrobot.hamilton.star.driver.features.head384 import Head384
from pylabrobot.hamilton.star.driver.features.iswap import iSWAP
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.driver.master import STARDriver
from pylabrobot.hamilton.star.server.v1 import (
  autoload_pb2,
  core_grippers_pb2,
  driver_pb2,
  front_cover_pb2,
  head96_pb2,
  head384_pb2,
  iswap_pb2,
  pipettes_pb2,
  star_pb2,
  x_arm_pb2,
)

# Each service, the class whose methods it serves, and the module its descriptor is in.
SERVICES = {
  "STARService": (STARDevice, star_pb2),
  "DriverService": (STARDriver, driver_pb2),
  "PipettesService": (Pipettes, pipettes_pb2),
  "Head96Service": (Head96, head96_pb2),
  "Head384Service": (Head384, head384_pb2),
  "ISwapService": (iSWAP, iswap_pb2),
  "CoreGrippersService": (CoreGrippers, core_grippers_pb2),
  "AutoloadService": (Autoload, autoload_pb2),
  "XArmService": (XArm, x_arm_pb2),
  "FrontCoverService": (FrontCover, front_cover_pb2),
}

# Methods served by no RPC: a deprecated alias the client inherits as it is, which calls the
# method it stands for.
NOT_SERVED = {(CoreGrippers, "drop_resource")}

# RPCs that call no method: the description the client keeps.
EXTRA_RPCS = {"Describe"}

# What a feature holds as a constant: fixed in the code, neither settings nor sent anywhere. A
# client refuses to have them assigned, as it would change nothing the server does.
CONSTANTS: Dict[type, FrozenSet[str]] = {
  Pipettes: frozenset(
    {
      "search_start_clearance",
      "well_search_start_clearance",
      "search_limit_below_cavity_bottom",
      "ztouch_search_limit_below_cavity_bottom",
      "ztouch_cascade_interval",
      "ztouch_aspirate_height_above_bottom",
      "ztouch_dispense_height_above_bottom",
    }
  ),
  Head96: frozenset({"search_start_clearance", "mix_swap_start_clearance"}),
}

# Request fields that say which instance a call is for, rather than being an argument.
ROUTING = {"XArmService": ("side",)}


@dataclasses.dataclass(frozen=True)
class Rpc:
  """One RPC, and the method it calls."""

  service: str
  name: str
  method: str
  connect_name: str
  request: Type[Message]
  response: Type[Message]


def _key(name: str) -> str:
  return name.replace("_", "").lower()


def served_methods(cls: type) -> List[str]:
  """The methods of a class that the server serves: every public coroutine, but those not served.

  For the device, only those that are its own: what it carries is reached through its driver.
  """
  if cls is STARDevice:
    return ["create_resources", "setup", "stop"]
  return [
    name
    for name, fn in inspect.getmembers(cls, inspect.iscoroutinefunction)
    if not name.startswith("_") and (cls, name) not in NOT_SERVED
  ]


def descriptor(service: str) -> ServiceDescriptor:
  return cast(ServiceDescriptor, SERVICES[service][1].DESCRIPTOR.services_by_name[service])


def rpcs(service: str) -> Dict[str, Rpc]:
  """A service's RPCs, by the name of the method each calls."""
  cls, _ = SERVICES[service]
  methods = {_key(name): name for name in served_methods(cls)}
  out: Dict[str, Rpc] = {}
  for method in descriptor(service).methods:
    if method.name in EXTRA_RPCS:
      continue
    python = methods.get(_key(method.name))
    if python is None:
      raise LookupError(f"{service}.{method.name} calls no method of {cls.__name__}")
    out[python] = _rpc(service, method, python)
  return out


def extra_rpcs(service: str) -> List[str]:
  """A service's RPCs that call no method."""
  return [m.name for m in descriptor(service).methods if m.name in EXTRA_RPCS]


def extra_rpc(service: str, name: str) -> Rpc:
  method = descriptor(service).methods_by_name[name]
  return _rpc(service, method, "")


def client_class(service: str) -> type:
  """The generated Connect client for a service."""
  module = importlib.import_module(SERVICES[service][1].__name__.replace("_pb2", "_connect"))
  return cast(type, getattr(module, f"{service}Client"))


def _rpc(service: str, method: MethodDescriptor, python: str) -> Rpc:
  # As the generated client names it.
  connect_name = next(
    name for name in vars(client_class(service)) if _key(name) == _key(method.name)
  )
  return Rpc(
    service=service,
    name=method.name,
    method=python,
    connect_name=connect_name,
    request=message_factory.GetMessageClass(method.input_type),
    response=message_factory.GetMessageClass(method.output_type),
  )


def setting_names(service: str) -> List[str]:
  """The settings of what a service calls: the fields of its `<Prefix>Settings` message; nothing,
  for a service with none."""
  message = SERVICES[service][1].DESCRIPTOR.message_types_by_name.get(
    service.removesuffix("Service") + "Settings"
  )
  return [] if message is None else [fd.name for fd in message.fields]
