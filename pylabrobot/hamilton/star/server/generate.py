"""Write the STAR server's generated code: `python -m pylabrobot.hamilton.star.server.generate`.

Run it, then commit what it writes, whenever a served method's signature or a `.proto` file
changes; `generate_tests.py` fails while the generated files are not what this writes. It writes
three modules, each explicit code for every RPC:

- `generated_codec.py`: each RPC's arguments and result to and from its messages, field by field;
  each configuration and settings message to and from what the features hold.
- `generated_handlers.py`: each service's handlers, every one a call on the served device.
- `generated_remote.py`: the client classes, every public coroutine a call to the server.

How a value goes over follows from the Python method's annotation and the field it lands in, by
rules the `.proto` files are written to:

- An unset field with presence is an argument not given, so the method's default applies. A
  parameter is `Optional` only where its default is None, so None and "not given" are the same.
- A list that may be None is a `...List` message holding `values`; a value in a list or a map that
  may be None is an `Optional...` message holding `value`.
- A union is a oneof, its members in the order the annotation names them, every resource handle
  in it as one `ResourceRef`.
- A literal string, or a Python enum member, is the enum value named by the enum's prefix (its
  `..._UNSPECIFIED` value's, less `UNSPECIFIED`) and the string or the member's name in upper case,
  each run of anything not a letter or a digit as one `_`. Literal numbers are numbers.
- A tuple is a message of as many fields, in order; so is a dict entry whose key a map cannot
  take. A dataclass, a typed dict or a liquid class is a message of its fields, by name.
- A resource handle is a `ResourceRef` by id: the server makes the handle from the resource server
  both ends use.
- A method with no annotated result returns the device's reply, `FirmwareReply`.

This reads the methods' signatures and annotations, and the messages' descriptors, to write the
code; the code it writes reads none of them.
"""

from __future__ import annotations

import ast
import builtins
import collections.abc
import copy
import dataclasses
import enum
import importlib
import importlib.util
import inspect
import keyword
import os
import typing
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from google.protobuf.descriptor import Descriptor, FieldDescriptor, MethodDescriptor

from pylabrobot.hamilton.liquid_classes.base import HamiltonLiquidClass
from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.configuration import DeviceConfiguration
from pylabrobot.hamilton.star.driver.features.autoload import Autoload, AutoloadConfiguration
from pylabrobot.hamilton.star.driver.features.core_grippers import (
  CoreGrippers,
  CoreGrippersConfiguration,
)
from pylabrobot.hamilton.star.driver.features.cover import FrontCover, FrontCoverConfiguration
from pylabrobot.hamilton.star.driver.features.head96 import Head96, Head96Configuration
from pylabrobot.hamilton.star.driver.features.head384 import Head384, Head384Configuration
from pylabrobot.hamilton.star.driver.features.iswap import iSWAP, iSWAPConfiguration
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes, PipettesConfiguration
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.driver.master import STARDriver
from pylabrobot.hamilton.star.server.v1 import (
  autoload_pb2,
  core_grippers_pb2,
  description_pb2,
  driver_pb2,
  front_cover_pb2,
  head96_pb2,
  head384_pb2,
  iswap_pb2,
  pipettes_pb2,
  star_pb2,
  x_arm_pb2,
)
from pylabrobot.resources.server import handles

_NoneType = type(None)
_RES = "pylabrobot.resources.server.v1"
_PKG = "pylabrobot.hamilton.star.server.v1"
_HERE = os.path.dirname(os.path.abspath(__file__))


# -- what is served ------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Service:
  """One service: the class whose methods it serves, and how both ends reach it.

  Attributes:
    name: the service's name in the `.proto`.
    cls: the class whose methods it serves.
    module: the generated module its messages are in.
    short: its name in the generated code: `pipettes` say.
    target: what the server's handlers call its methods on.
    settings: the feature its `<Prefix>Settings` message holds the settings of, when it has one.
  """

  name: str
  cls: type
  module: Any
  short: str
  target: str
  has_settings: bool = False


SERVICES = [
  Service("STARService", STARDevice, star_pb2, "star", "self._served.device"),
  Service("DriverService", STARDriver, driver_pb2, "driver", "self._served.driver()"),
  Service("PipettesService", Pipettes, pipettes_pb2, "pipettes", "self._served.pipettes()", True),
  Service("Head96Service", Head96, head96_pb2, "head96", "self._served.head96()", True),
  Service("Head384Service", Head384, head384_pb2, "head384", "self._served.head384()", True),
  Service("ISwapService", iSWAP, iswap_pb2, "iswap", "self._served.iswap()", True),
  Service(
    "CoreGrippersService",
    CoreGrippers,
    core_grippers_pb2,
    "core_grippers",
    "self._served.core_grippers()",
    True,
  ),
  Service("AutoloadService", Autoload, autoload_pb2, "autoload", "self._served.autoload()"),
  Service("XArmService", XArm, x_arm_pb2, "x_arm", "self._served.x_arm(request.side)", True),
  Service(
    "FrontCoverService", FrontCover, front_cover_pb2, "front_cover", "self._served.front_cover()"
  ),
]

# Methods served by no RPC: a deprecated alias the client inherits as it is, which calls the
# method it stands for.
NOT_SERVED = {(CoreGrippers, "drop_resource")}

# RPCs that call no method: the description the client keeps.
EXTRA_RPCS = {"Describe"}

# The calls that make the device's features anew, after which the settings are put in place again.
SETUP = {("STARService", "setup"), ("DriverService", "setup")}

# Request fields that say which instance a call is for, rather than being an argument.
ROUTING = {"XArmService": ("side",)}

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

# Each configuration a description holds, by the name its functions are generated under.
CONFIGURATIONS: List[Tuple[str, Any, type]] = [
  (
    "device_configuration",
    description_pb2.DriverDescription.DESCRIPTOR.fields_by_name["configuration"].message_type,
    DeviceConfiguration,
  ),
  (
    "pipettes_configuration",
    description_pb2.PipettesDescription.DESCRIPTOR.fields_by_name["configuration"].message_type,
    PipettesConfiguration,
  ),
  (
    "head96_configuration",
    description_pb2.Head96Description.DESCRIPTOR.fields_by_name["configuration"].message_type,
    Head96Configuration,
  ),
  (
    "head384_configuration",
    description_pb2.Head384Description.DESCRIPTOR.fields_by_name["configuration"].message_type,
    Head384Configuration,
  ),
  (
    "iswap_configuration",
    description_pb2.ISwapDescription.DESCRIPTOR.fields_by_name["configuration"].message_type,
    iSWAPConfiguration,
  ),
  (
    "core_grippers_configuration",
    description_pb2.CoreGrippersDescription.DESCRIPTOR.fields_by_name["configuration"].message_type,
    CoreGrippersConfiguration,
  ),
  (
    "autoload_configuration",
    description_pb2.AutoloadDescription.DESCRIPTOR.fields_by_name["configuration"].message_type,
    AutoloadConfiguration,
  ),
  (
    "front_cover_configuration",
    description_pb2.FrontCoverDescription.DESCRIPTOR.fields_by_name["configuration"].message_type,
    FrontCoverConfiguration,
  ),
]

# A method's **kwargs: what they are passed on to. The request carries those parameters' fields.
_FORWARDED: Dict[Tuple[type, str], str] = {
  (Pipettes, "discard_tips"): "drop_tips",
  (Pipettes, "return_tips"): "drop_tips",
  (Head96, "discard_tips"): "drop_tips",
  (Head96, "return_tips"): "drop_tips",
  (Pipettes, "probe_z_using_plld"): "_plld_search",
}


def _members_of(cls: type) -> Dict[str, Any]:
  return dict(inspect.getmembers(cls))


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


def settings_message(service: Service) -> Optional[Descriptor]:
  """The `<Prefix>Settings` message of a service with settings."""
  if not service.has_settings:
    return None
  message: Descriptor = service.module.DESCRIPTOR.message_types_by_name[
    service.name.removesuffix("Service") + "Settings"
  ]
  return message


def setting_names(service: Service) -> List[str]:
  message = settings_message(service)
  return [] if message is None else [fd.name for fd in message.fields]


def _key(name: str) -> str:
  return name.replace("_", "").lower()


def _connect_name(service: Service, rpc: str) -> str:
  """The method the generated Connect client and service name an RPC."""
  client = dict(inspect.getmembers(_connect_module(service)))[f"{service.name}Client"]
  return next(name for name, _ in inspect.getmembers(client) if _key(name) == _key(rpc))


def _connect_module(service: Service) -> Any:
  import importlib

  return importlib.import_module(service.module.__name__.replace("_pb2", "_connect"))


@dataclasses.dataclass(frozen=True)
class Rpc:
  service: Service
  method: MethodDescriptor
  python: str
  connect_name: str


def rpcs(service: Service) -> List[Rpc]:
  """A service's RPCs that call a method, in the order of its methods."""
  methods = {_key(name): name for name in served_methods(service.cls)}
  descriptor = service.module.DESCRIPTOR.services_by_name[service.name]
  out: List[Rpc] = []
  for method in descriptor.methods:
    if method.name in EXTRA_RPCS:
      continue
    python = methods.get(_key(method.name))
    if python is None:
      raise LookupError(f"{service.name}.{method.name} calls no method of {service.cls.__name__}")
    out.append(Rpc(service, method, python, _connect_name(service, method.name)))
  missing = set(methods.values()) - {rpc.python for rpc in out}
  if missing:
    raise LookupError(f"{service.name} serves no RPC for {sorted(missing)}")
  return sorted(out, key=lambda rpc: rpc.python)


# -- annotations ---------------------------------------------------------------------------------


def strip_optional(t: Any) -> Tuple[Any, bool]:
  """An annotation without its None, and whether it had one."""
  if typing.get_origin(t) is typing.Union:
    args = [a for a in typing.get_args(t) if a is not _NoneType]
    if len(args) < len(typing.get_args(t)):
      return (args[0] if len(args) == 1 else typing.Union[tuple(args)]), True
  return t, False


def is_list(t: Any) -> bool:
  return typing.get_origin(t) in (list, collections.abc.Sequence) or t is list


def is_handle(t: Any) -> bool:
  return isinstance(t, type) and issubclass(t, handles.Resource)


def members(t: Any) -> List[Any]:
  """A union's members as its oneof has them: every resource handle as one."""
  out: List[Any] = []
  for member in typing.get_args(t):
    if is_handle(member) and any(is_handle(m) for m in out):
      continue
    out.append(member)
  return out


def is_typeddict(t: Any) -> bool:
  return isinstance(t, type) and typing.is_typeddict(t)


def record_fields(t: Any) -> List[Tuple[str, Any]]:
  """A dataclass's, a typed dict's or a liquid class's fields, with their types."""
  if dataclasses.is_dataclass(t):
    hints = typing.get_type_hints(t)
    return [(f.name, hints[f.name]) for f in dataclasses.fields(t)]
  if is_typeddict(t):
    return list(typing.get_type_hints(t).items())
  hints = typing.get_type_hints(t.__init__)
  return [(name, hint) for name, hint in hints.items() if name != "return"]


def is_record(t: Any) -> bool:
  return isinstance(t, type) and (
    dataclasses.is_dataclass(t) or is_typeddict(t) or t is HamiltonLiquidClass
  )


def parameter_type(p: inspect.Parameter, hints: Dict[str, Any]) -> Any:
  if p.name in hints:
    return hints[p.name]
  if p.default is not p.empty and p.default is not None:
    return type(p.default)
  return Any


def _forwarded_hints(cls: type, name: str) -> Dict[str, Any]:
  target = _FORWARDED.get((cls, name))
  if target is None:
    return {}
  return typing.get_type_hints(_members_of(cls)[target])


# -- message shapes ------------------------------------------------------------------------------


def _message_type(fd: FieldDescriptor) -> Descriptor:
  """The message a message field holds."""
  assert fd.message_type is not None, fd.full_name
  return fd.message_type


def _is_map(fd: FieldDescriptor) -> bool:
  return bool(
    fd.is_repeated
    and fd.type == FieldDescriptor.TYPE_MESSAGE
    and _message_type(fd).GetOptions().map_entry
  )


def _is_repeated(fd: FieldDescriptor) -> bool:
  return fd.is_repeated and not _is_map(fd)


def _only_field(d: Descriptor, name: str) -> Optional[FieldDescriptor]:
  return d.fields[0] if len(d.fields) == 1 and d.fields[0].name == name else None


def _real_oneof(d: Descriptor, name: str) -> Any:
  oneof = d.oneofs_by_name.get(name)
  if oneof is None or (len(oneof.fields) == 1 and oneof.name == "_" + oneof.fields[0].name):
    return None
  return oneof


def _union_oneof(d: Descriptor) -> Any:
  """The one oneof a union message is, when it is one."""
  real = [o for o in d.oneofs if not (len(o.fields) == 1 and o.name == "_" + o.fields[0].name)]
  if len(real) == 1 and len(real[0].fields) == len(d.fields):
    return real[0]
  return None


def _enum_prefix(descriptor: Any) -> str:
  return str(descriptor.values[0].name[: -len("UNSPECIFIED")])


def _value_suffix(value: Any) -> str:
  import re

  return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").upper()


def _literal_in(t: Any) -> Any:
  for member in typing.get_args(t):
    if typing.get_origin(member) is typing.Literal:
      return member
  raise TypeError(f"no literal in {t}")


def _attribute(name: str) -> str:
  if keyword.iskeyword(name) or not name.isidentifier():
    raise ValueError(f"field {name!r} cannot be written as an attribute")
  return name


# -- names ---------------------------------------------------------------------------------------

_BUILTINS = {name for name, _ in inspect.getmembers(builtins)}
_LITERALS = {("typing", "Literal"), ("typing_extensions", "Literal")}


@dataclasses.dataclass(frozen=True)
class _Symbol:
  """Where a name comes from: an attribute of a module, or a module itself when `attr` is ""."""

  module: str
  attr: str


class _Source:
  """A module's source: its tree, and where each of its top-level names comes from."""

  def __init__(self, module_name: str):
    module = importlib.import_module(module_name)
    path = inspect.getsourcefile(module)
    assert path is not None
    self.name = module_name
    self.package = module.__package__ or ""
    with open(path, encoding="utf-8") as f:
      self.tree = ast.parse(f.read())
    self.symbols: Dict[str, _Symbol] = {}
    self._collect(self.tree.body)

  def _collect(self, body: Sequence[ast.stmt]) -> None:
    for node in body:
      if isinstance(node, ast.Import):
        for alias in node.names:
          if alias.asname:
            self.symbols[alias.asname] = _Symbol(alias.name, "")
          else:
            top = alias.name.split(".")[0]
            self.symbols[top] = _Symbol(top, "")
      elif isinstance(node, ast.ImportFrom):
        base = (
          importlib.util.resolve_name("." * node.level + (node.module or ""), self.package)
          if node.level
          else node.module or ""
        )
        for alias in node.names:
          if alias.name != "*":
            self.symbols[alias.asname or alias.name] = _Symbol(base, alias.name)
      elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        self.symbols[node.name] = _Symbol(self.name, node.name)
      elif isinstance(node, ast.Assign):
        for target in node.targets:
          if isinstance(target, ast.Name):
            self.symbols[target.id] = _Symbol(self.name, target.id)
      elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        self.symbols[node.target.id] = _Symbol(self.name, node.target.id)
      elif isinstance(node, ast.If):
        self._collect(node.body)
        self._collect(node.orelse)
      elif isinstance(node, ast.Try):
        self._collect(node.body)
        for handler in node.handlers:
          self._collect(handler.body)

  def class_def(self, name: str) -> ast.ClassDef:
    for node in self.tree.body:
      if isinstance(node, ast.ClassDef) and node.name == name:
        return node
    raise LookupError(f"no class {name} in {self.name}")


_SOURCES: Dict[str, _Source] = {}


def _source(module_name: str) -> _Source:
  if module_name not in _SOURCES:
    _SOURCES[module_name] = _Source(module_name)
  return _SOURCES[module_name]


class _Module:
  """One generated module: its imports, and the code under them."""

  def __init__(self, reserved: Sequence[str] = (), given: Sequence[str] = ()) -> None:
    """
    Args:
      reserved: names the module's own code takes.
      given: names its preamble imports from `typing`.
    """
    self.imports: Dict[Tuple[str, str], str] = {}
    self.names: Set[str] = set(reserved) | set(given)
    self.given = {_Symbol("typing", name): name for name in given}
    self.blocks: List[str] = []

  def symbol(self, symbol: _Symbol, prefer: str) -> str:
    """The local name an import of `symbol` is known by here."""
    if symbol in self.given:
      return self.given[symbol]
    if symbol not in self.imports_by_symbol():
      local = prefer
      n = 2
      while local in self.names:
        local = f"{prefer}_{n}"
        n += 1
      self.imports[(symbol.module, symbol.attr)] = local
      self.names.add(local)
    return self.imports[(symbol.module, symbol.attr)]

  def imports_by_symbol(self) -> Set[_Symbol]:
    return {_Symbol(module, attr) for module, attr in self.imports}

  def name_of(self, obj: Any) -> str:
    """The name a class or enum is known by here, imported from its module."""
    top, _, rest = obj.__qualname__.partition(".")
    local = self.symbol(_Symbol(obj.__module__, top), top)
    return f"{local}.{rest}" if rest else local

  def module_of(self, module_name: str) -> str:
    leaf = module_name.rpartition(".")[2]
    return self.symbol(_Symbol(module_name, ""), leaf)

  def message_class(self, d: Descriptor) -> str:
    """The generated class of a message, from the module of the file it is defined in."""
    alias = self.module_of(d.file.name.removesuffix(".proto").replace("/", ".") + "_pb2")
    names = []
    at: Optional[Descriptor] = d
    while at is not None:
      names.append(at.name)
      at = at.containing_type
    return f"{alias}.{'.'.join(reversed(names))}"

  def enum_class(self, e: Any) -> str:
    """The generated wrapper of an enum, from the module of the file it is defined in."""
    alias = self.module_of(e.file.name.removesuffix(".proto").replace("/", ".") + "_pb2")
    names = [e.name]
    at: Optional[Descriptor] = e.containing_type
    while at is not None:
      names.append(at.name)
      at = at.containing_type
    return f"{alias}.{'.'.join(reversed(names))}"

  def type_text(self, t: Any) -> str:
    """An annotation, as code here."""
    if t is Any or t is inspect.Parameter.empty:
      return "Any"
    if t is None or t is _NoneType:
      return "None"
    origin, args = typing.get_origin(t), typing.get_args(t)
    if origin is typing.Union:
      return f"Union[{', '.join(self.type_text(a) for a in args)}]"
    if origin is typing.Literal:
      return f"Literal[{', '.join(repr(a) for a in args)}]"
    names = {
      list: "List",
      collections.abc.Sequence: "Sequence",
      dict: "Dict",
      collections.abc.Mapping: "Mapping",
      tuple: "Tuple",
    }
    if origin in names:
      inner = ", ".join("..." if a is Ellipsis else self.type_text(a) for a in args)
      return f"{names[origin]}[{inner}]" if args else names[origin]
    if isinstance(t, type):
      return t.__name__ if t.__module__ == "builtins" else self.name_of(t)
    raise TypeError(f"no way to write {t!r}")

  def render(self, docstring: str, preamble: Sequence[str] = ()) -> str:
    lines = [
      "# Generated by `python -m pylabrobot.hamilton.star.server.generate`. DO NOT EDIT.",
      f'"""{docstring}"""',
      "",
      "from __future__ import annotations",
      "",
    ]
    lines.extend(preamble)
    for (module, attr), local in sorted(self.imports.items()):
      if attr == "":
        lines.append(f"import {module} as {local}")
      elif local == attr:
        lines.append(f"from {module} import {attr}")
      else:
        lines.append(f"from {module} import {attr} as {local}")
    for block in self.blocks:
      lines.append("")
      lines.append("")
      lines.append(block.rstrip("\n"))
    return "\n".join(lines) + "\n"


class _Rename(ast.NodeTransformer):
  """An annotation or default from a method's source, its names as the generated module has them."""

  def __init__(
    self, module: _Module, source: _Source, cls: ast.ClassDef, owner: str, annotation: bool
  ):
    self.module, self.source, self.annotation = module, source, annotation
    self.owner = owner
    self.class_names = {
      t.id
      for node in cls.body
      if isinstance(node, (ast.Assign, ast.AnnAssign))
      for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
      if isinstance(t, ast.Name)
    }

  def resolve(self, name: str) -> str:
    symbol = self.source.symbols.get(name)
    if symbol is not None:
      return self.module.symbol(symbol, name)
    if name in self.class_names:
      return f"{self.owner}.{name}"
    if name in _BUILTINS:
      return name
    raise LookupError(f"{name} in {self.source.name} comes from nowhere")

  def is_literal(self, node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
      symbol = self.source.symbols.get(node.id)
      return symbol is not None and (symbol.module, symbol.attr) in _LITERALS
    return isinstance(node, ast.Attribute) and node.attr == "Literal"

  def visit_Name(self, node: ast.Name) -> ast.expr:
    return ast.copy_location(ast.parse(self.resolve(node.id), mode="eval").body, node)

  def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
    if self.is_literal(node.value):
      node.value = self.visit(node.value)
      return node
    return self.generic_visit(node)  # type: ignore[return-value]

  def visit_Constant(self, node: ast.Constant) -> ast.expr:
    if self.annotation and isinstance(node.value, str):
      return self.visit(ast.parse(node.value, mode="eval").body)  # type: ignore[no-any-return]
    return node


@dataclasses.dataclass
class _Parameter:
  name: str
  kind: str  # "positional", "keyword", "var_keyword"
  annotation: str
  default: Optional[str]


@dataclasses.dataclass
class _Signature:
  """A method's signature as code in a generated module: its overloads, then its own."""

  self_name: str
  parameters: List[_Parameter]
  overloads: List[str]
  arguments: str
  returns: Optional[str]


def _signature(module: _Module, cls: type, name: str) -> _Signature:
  fn = inspect.unwrap(_members_of(cls)[name])
  source = _source(fn.__module__)
  owner_name = fn.__qualname__.split(".")[0]
  class_node = source.class_def(owner_name)
  owner = module.symbol(_Symbol(fn.__module__, owner_name), owner_name)
  defs = [
    node
    for node in class_node.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn.__name__
  ]

  def write(node: Any) -> Tuple[ast.arguments, Optional[str]]:
    args = copy.deepcopy(node.args)
    annotate = _Rename(module, source, class_node, owner, annotation=True)
    default = _Rename(module, source, class_node, owner, annotation=False)
    every = (
      args.posonlyargs + args.args + args.kwonlyargs + [a for a in (args.vararg, args.kwarg) if a]
    )
    for a in every:
      if a.annotation is not None:
        a.annotation = annotate.visit(a.annotation)
    args.defaults = [default.visit(d) for d in args.defaults]
    args.kw_defaults = [None if d is None else default.visit(d) for d in args.kw_defaults]
    returns = (
      None if node.returns is None else ast.unparse(annotate.visit(copy.deepcopy(node.returns)))
    )
    return args, returns

  overloads = []
  for node in defs[:-1]:
    args, returns = write(node)
    overloads.append(f"async def {name}({ast.unparse(args)}) -> {returns}: ...")
  args, returns = write(defs[-1])
  if args.posonlyargs or args.vararg:
    raise NotImplementedError(f"{cls.__name__}.{name} takes positional-only or *args")
  positional = args.args[1:]
  defaults: List[Optional[ast.expr]] = [None] * (len(args.args) - len(args.defaults)) + list(
    args.defaults
  )
  parameters = []
  for a, d in zip(args.args[1:], defaults[1:]):
    parameters.append(
      _Parameter(
        a.arg,
        "positional",
        "Any" if a.annotation is None else ast.unparse(a.annotation),
        None if d is None else ast.unparse(d),
      )
    )
  for a, kd in zip(args.kwonlyargs, args.kw_defaults):
    parameters.append(
      _Parameter(
        a.arg,
        "keyword",
        "Any" if a.annotation is None else ast.unparse(a.annotation),
        None if kd is None else ast.unparse(kd),
      )
    )
  if args.kwarg is not None:
    parameters.append(_Parameter(args.kwarg.arg, "var_keyword", "Any", None))
  del positional
  return _Signature(args.args[0].arg, parameters, overloads, ast.unparse(args), returns)


# -- the codec -----------------------------------------------------------------------------------

_REFS = "wire.Refs"


class _Codec:
  """The codec module: a function per message and type, and functions per RPC."""

  def __init__(self) -> None:
    self.m = _Module(
      reserved=["wire", "dataclasses", "Rpc", "RPCS"],
      given=[
        "Any",
        "Callable",
        "Dict",
        "List",
        "Literal",
        "Mapping",
        "Optional",
        "Sequence",
        "Tuple",
        "Type",
        "Union",
        "cast",
      ],
    )
    self.counter = 0
    self.fills: Dict[Tuple[str, str], str] = {}
    self.reads: Dict[Tuple[str, str], str] = {}
    self.enums: Dict[str, str] = {}
    self.decodings: Dict[Tuple[str, str], str] = {}
    # The read functions that may give None: those of unions.
    self.optional_reads: Set[str] = set()

  def fresh(self, stem: str) -> str:
    self.counter += 1
    return f"{stem}_{self.counter}"

  # -- scalars --

  def scalar(self, fd: FieldDescriptor, t: Any, v: str) -> str:
    if fd.enum_type is not None:
      return f"wire.enum_number({self.enum_table(fd.enum_type)}, {fd.enum_type.name!r}, {v})"
    if fd.type in (FieldDescriptor.TYPE_DOUBLE, FieldDescriptor.TYPE_FLOAT):
      return f"float({v})"
    if fd.type == FieldDescriptor.TYPE_BOOL:
      return f"bool({v})"
    if fd.type == FieldDescriptor.TYPE_STRING:
      return f"wire.text({v})"
    if fd.type == FieldDescriptor.TYPE_BYTES:
      return f"bytes({v})"
    return f"int({v})"

  def enum_table(self, descriptor: Any) -> str:
    """A table of an enum's numbers by their names' suffixes."""
    key = descriptor.full_name
    if key not in self.enums:
      name = self.fresh("_ENUM")
      prefix = _enum_prefix(descriptor)
      enum_class = self.m.enum_class(descriptor)
      # An enum's values are constants beside it: in its module, or in the message it is in.
      values_at = enum_class.rpartition(".")[0]
      entries = ", ".join(
        f"{v.name[len(prefix) :]!r}: {values_at}.{v.name}" for v in descriptor.values
      )
      self.m.blocks.append(
        f"# {descriptor.full_name}'s values, by their names' suffixes.\n"
        f"{name}: Dict[str, {enum_class}] = {{{entries}}}\n"
      )
      self.enums[key] = name
    return self.enums[key]

  def unscalar(self, fd: FieldDescriptor, t: Any, raw: str) -> str:
    if fd.enum_type is None:
      inner, _ = strip_optional(t)
      if typing.get_origin(inner) is typing.Literal:
        allowed = tuple(typing.get_args(inner))
        return f"cast({self.m.type_text(inner)}, wire.one_of({raw}, {allowed!r}))"
      return raw
    inner, _ = strip_optional(t)
    key = (fd.enum_type.full_name, repr(inner))
    if key not in self.decodings:
      prefix = _enum_prefix(fd.enum_type)
      entries: List[str] = []
      if isinstance(inner, type) and issubclass(inner, enum.Enum):
        value_type = self.m.name_of(inner)
        for v in fd.enum_type.values:
          found = [m for m in inner if _value_suffix(m.name) == v.name[len(prefix) :]]
          if found:
            entries.append(f"{v.number}: {value_type}.{found[0].name}")
      else:
        literal = inner if typing.get_origin(inner) is typing.Literal else _literal_in(inner)
        value_type = self.m.type_text(literal)
        for v in fd.enum_type.values:
          found_values = [
            x for x in typing.get_args(literal) if _value_suffix(x) == v.name[len(prefix) :]
          ]
          if found_values:
            entries.append(f"{v.number}: {found_values[0]!r}")
      name = self.fresh("_VALUES")
      self.m.blocks.append(
        f"# What {fd.enum_type.full_name}'s numbers are, as {value_type}.\n"
        f"{name}: Dict[int, {value_type}] = {{{', '.join(entries)}}}\n"
      )
      self.decodings[key] = name
    return f"{self.decodings[key]}[{raw}]"

  # -- to messages --

  def set_field(
    self, fd: FieldDescriptor, t: Any, msg: str, v: str, out: List[str], ind: str
  ) -> None:
    """Statements that put `v`, of type `t`, in `msg`'s field; None leaves it unset."""
    inner, optional = strip_optional(t)
    field = f"{msg}.{_attribute(fd.name)}"
    if optional or inner is Any:
      out.append(f"{ind}if {v} is not None:")
      ind = ind + "  "
    if _is_map(fd):
      key_t, value_t = typing.get_args(inner)
      value_fd = _message_type(fd).fields_by_name["value"]
      key, item = self.fresh("key"), self.fresh("item")
      out.append(f"{ind}for {key}, {item} in {v}.items():")
      if value_fd.type == FieldDescriptor.TYPE_MESSAGE:
        fill = self.fill_function(_message_type(value_fd), value_t)
        out.append(f"{ind}  {fill}({field}[{key}], {item})")
      else:
        out.append(f"{ind}  {field}[{key}] = {self.scalar(value_fd, value_t, item)}")
      return
    if _is_repeated(fd):
      if typing.get_origin(inner) is dict:
        key_t, value_t = typing.get_args(inner)
        key_fd, value_fd = _message_type(fd).fields
        key, item, entry = self.fresh("key"), self.fresh("item"), self.fresh("entry")
        out.append(f"{ind}for {key}, {item} in {v}.items():")
        out.append(f"{ind}  {entry} = {field}.add()")
        self.set_field(key_fd, key_t, entry, key, out, ind + "  ")
        self.set_field(value_fd, value_t, entry, item, out, ind + "  ")
        return
      args = typing.get_args(inner)
      element_t = args[0] if args else Any
      item = self.fresh("item")
      out.append(f"{ind}for {item} in {v}:")
      if fd.type == FieldDescriptor.TYPE_MESSAGE:
        fill = self.fill_function(_message_type(fd), element_t)
        out.append(f"{ind}  {fill}({field}.add(), {item})")
      else:
        out.append(f"{ind}  {field}.append({self.scalar(fd, element_t, item)})")
      return
    if fd.type == FieldDescriptor.TYPE_MESSAGE:
      fill = self.fill_function(_message_type(fd), inner)
      out.append(f"{ind}{field}.SetInParent()")
      out.append(f"{ind}{fill}({field}, {v})")
      return
    out.append(f"{ind}{field} = {self.scalar(fd, inner, v)}")

  def condition(self, t: Any, v: str) -> str:
    """Whether `v` is of a union member's type."""
    inner, optional = strip_optional(t)
    if is_handle(inner):
      check = f"isinstance({v}, {self.m.name_of(handles.Resource)})"
    elif typing.get_origin(inner) is typing.Literal:
      check = f"{v} in {tuple(typing.get_args(inner))!r}"
    elif is_list(inner):
      check = f"isinstance({v}, (list, tuple))"
    elif inner is float:
      check = f"isinstance({v}, (int, float)) and not isinstance({v}, bool)"
    elif inner is str:
      check = f"isinstance({v}, str)"
    elif isinstance(inner, type):
      check = f"isinstance({v}, {self.m.name_of(inner)})"
    else:
      check = "False"
    return f"({v} is None or ({check}))" if optional else f"({check})"

  def fill_function(self, d: Descriptor, t: Any) -> str:
    """The name of a function that fills a `d` from a value of type `t`."""
    inner, _ = strip_optional(t)
    name = d.full_name
    special = {
      f"{_RES}.Vec3": "fill_xyz",
      f"{_RES}.Rotation": "fill_xyz",
      f"{_RES}.ResourceRef": "fill_ref",
      f"{_RES}.ResourceNode": "fill_node",
      f"{_RES}.ResourceAttributes": "fill_attributes",
      f"{_PKG}.Date": "fill_date",
      f"{_PKG}.FirmwareReply": "fill_reply",
    }
    if name in special:
      return f"wire.{special[name]}"
    oneof = _union_oneof(d)
    values = _only_field(d, "values")
    only = _only_field(d, "value")
    entries = _only_field(d, "entries")
    # A wrapper or a union takes None as it is: an empty message.
    value_t = t if strip_optional(t)[1] and (oneof or only or values) else inner
    key = (name, repr(value_t))
    if key in self.fills:
      return self.fills[key]
    fn = self.fresh(f"_fill_{d.name}")
    self.fills[key] = fn
    body: List[str] = []
    ind = "  "
    if oneof is not None:
      if value_t is not inner:
        body += [f"{ind}if value is None:", f"{ind}  return"]
      for fd, member in zip(oneof.fields, members(inner)):
        body.append(f"{ind}if {self.condition(member, 'value')}:")
        self.set_field(fd, member, "message", "value", body, ind + "  ")
        body.append(f"{ind}  return")
      body.append(f'{ind}raise TypeError(f"{{value!r}} is none of {self.m.type_text(inner)}")')
    elif values is not None and is_list(inner):
      self.set_field(values, value_t, "message", "value", body, ind)
    elif only is not None:
      self.set_field(only, value_t, "message", "value", body, ind)
    elif entries is not None and typing.get_origin(inner) is dict:
      self.set_field(entries, inner, "message", "value", body, ind)
    elif typing.get_origin(inner) is tuple:
      for i, (fd, item_t) in enumerate(zip(d.fields, typing.get_args(inner))):
        self.set_field(fd, item_t, "message", f"value[{i}]", body, ind)
    elif is_record(inner):
      for field_name, field_t in record_fields(inner):
        get = f"value[{field_name!r}]" if is_typeddict(inner) else f"value.{field_name}"
        self.set_field(d.fields_by_name[field_name], field_t, "message", get, body, ind)
    else:
      raise TypeError(f"no way to put {inner} in {name}")
    self.m.blocks.append(
      f"def {fn}(message: {self.m.message_class(d)}, value: {self.m.type_text(value_t)}) -> None:\n"
      + "\n".join(body or ["  pass"])
      + "\n"
    )
    return fn

  # -- from messages --

  def handle(self, t: Any, ref: str) -> str:
    """An expression for the handle a `ResourceRef` names, as the handle type `t` says."""
    inner, _ = strip_optional(t)
    if is_handle(inner):
      return f"wire.handle(refs, {ref}, {self.m.name_of(inner)})"
    kinds = [m for m in typing.get_args(inner) if is_handle(m)]
    names = ", ".join(self.m.name_of(k) for k in kinds)
    return (
      f"cast({self.m.type_text(typing.Union[tuple(kinds)])}, "
      f"wire.handle_of(refs, {ref}, ({names},)))"
    )

  def get_field(self, fd: FieldDescriptor, t: Any, msg: str, presence: bool = True) -> str:
    """An expression for `msg`'s field as type `t`; an unset field with presence is None."""
    inner, _ = strip_optional(t)
    field = f"{msg}.{_attribute(fd.name)}"

    def one(message_type: Descriptor, item_t: Any, item: str) -> str:
      if message_type.full_name == f"{_RES}.ResourceRef" and (
        is_handle(strip_optional(item_t)[0])
        or any(is_handle(m) for m in typing.get_args(strip_optional(item_t)[0]))
      ):
        return self.handle(item_t, item)
      fn = self.read_function(message_type, item_t)
      if fn in self.optional_reads and not strip_optional(item_t)[1]:
        fn = self.given_function(fn, message_type, item_t)
      return f"{fn}({item}, refs)"

    if _is_map(fd):
      key_t, value_t = typing.get_args(inner)
      value_fd = _message_type(fd).fields_by_name["value"]
      key, item = self.fresh("key"), self.fresh("item")
      value = (
        one(_message_type(value_fd), value_t, item)
        if value_fd.type == FieldDescriptor.TYPE_MESSAGE
        else self.unscalar(value_fd, value_t, item)
      )
      key_inner, _ = strip_optional(key_t)
      key_value = key
      if typing.get_origin(key_inner) is typing.Literal:
        allowed = tuple(typing.get_args(key_inner))
        key_value = f"cast({self.m.type_text(key_inner)}, wire.one_of({key}, {allowed!r}))"
      return f"{{{key_value}: {value} for {key}, {item} in {field}.items()}}"
    if _is_repeated(fd):
      if typing.get_origin(inner) is dict:
        key_t, value_t = typing.get_args(inner)
        key_fd, value_fd = _message_type(fd).fields
        entry = self.fresh("entry")
        return (
          f"{{{self.get_field(key_fd, key_t, entry)}: {self.get_field(value_fd, value_t, entry)}"
          f" for {entry} in {field}}}"
        )
      args = typing.get_args(inner)
      element_t = args[0] if args else Any
      item = self.fresh("item")
      if fd.type == FieldDescriptor.TYPE_MESSAGE:
        each = one(_message_type(fd), element_t, item)
      else:
        each = self.unscalar(fd, element_t, item)
      listed = f"[{each} for {item} in {field}]"
      return f"tuple({listed})" if typing.get_origin(inner) is tuple else listed
    if fd.type == FieldDescriptor.TYPE_MESSAGE:
      value = one(_message_type(fd), t, field)
    else:
      value = self.unscalar(fd, inner, field)
    if fd.has_presence and presence:
      if strip_optional(t)[1] or t is Any:
        return f"({value} if {msg}.HasField({fd.name!r}) else None)"
      return f"({value} if {msg}.HasField({fd.name!r}) else wire.missing({fd.full_name!r}))"
    return value

  def given_function(self, fn: str, d: Descriptor, t: Any) -> str:
    """A reader like `fn` for a union that must hold a value: it raises when it holds none."""
    given = f"{fn}_given"
    if given not in self.reads.values():
      self.reads[(d.full_name, f"given {t!r}")] = given
      self.m.blocks.append(
        f"def {given}(message: {self.m.message_class(d)}, refs: {_REFS}) -> "
        f"{self.m.type_text(strip_optional(t)[0])}:\n"
        f"  value = {fn}(message, refs)\n"
        "  if value is None:\n"
        f'    raise ValueError("a {d.full_name} that must hold a value holds none")\n'
        "  return value\n"
      )
    return given

  def read_function(self, d: Descriptor, t: Any) -> str:
    """The name of a function that reads a `d` as a value of type `t`."""
    inner, _ = strip_optional(t)
    name = d.full_name
    special = {
      f"{_RES}.Vec3": "read_vec3",
      f"{_RES}.Rotation": "read_rotation",
      f"{_RES}.ResourceNode": "read_node",
      f"{_RES}.ResourceAttributes": "read_attributes",
      f"{_PKG}.Date": "read_date",
      f"{_PKG}.FirmwareReply": "read_reply",
    }
    if name in special:
      return f"wire.{special[name]}"
    key = (name, repr(inner))
    if key in self.reads:
      return self.reads[key]
    fn = self.fresh(f"_read_{d.name}")
    self.reads[key] = fn
    body: List[str] = []
    oneof = _union_oneof(d)
    values = _only_field(d, "values")
    only = _only_field(d, "value")
    entries = _only_field(d, "entries")
    returns = self.m.type_text(t if oneof is not None else inner)
    if oneof is not None:
      body.append(f"  which = message.WhichOneof({oneof.name!r})")
      body.append("  if which is None:")
      body.append("    return None")
      handle_members = [m for m in typing.get_args(inner) if is_handle(m)]
      for fd, member in zip(oneof.fields, members(inner)):
        member_t = typing.Union[tuple(handle_members)] if is_handle(member) else member
        body.append(f"  if which == {fd.name!r}:")
        body.append(f"    return {self.get_field(fd, member_t, 'message', presence=False)}")
      body.append(f'  raise TypeError("no way to read {self.m.type_text(inner)} from {name}")')
      returns = self.m.type_text(typing.Optional[inner])
      self.optional_reads.add(fn)
    elif values is not None and is_list(inner):
      body.append(f"  return {self.get_field(values, inner, 'message')}")
    elif only is not None:
      body.append(f"  return {self.get_field(only, t, 'message')}")
      returns = self.m.type_text(t)
    elif entries is not None and typing.get_origin(inner) is dict:
      body.append(f"  return {self.get_field(entries, inner, 'message')}")
    elif typing.get_origin(inner) is tuple:
      items = [
        self.get_field(fd, item_t, "message")
        for fd, item_t in zip(d.fields, typing.get_args(inner))
      ]
      body.append(f"  return ({', '.join(items)}{',' if len(items) == 1 else ''})")
    elif is_record(inner):
      fields = [
        (field_name, self.get_field(d.fields_by_name[field_name], field_t, "message"))
        for field_name, field_t in record_fields(inner)
      ]
      if is_typeddict(inner):
        body.append("  return {")
        body.extend(f"    {field_name!r}: {value}," for field_name, value in fields)
        body.append("  }")
      else:
        if dataclasses.is_dataclass(inner) and any(not f.init for f in dataclasses.fields(inner)):
          raise NotImplementedError(f"{inner} has fields set outside its __init__")
        body.append(f"  return {self.m.name_of(inner)}(")
        body.extend(f"    {field_name}={value}," for field_name, value in fields)
        body.append("  )")
    else:
      raise TypeError(f"no way to read {inner} from {name}")
    self.m.blocks.append(
      f"def {fn}(message: {self.m.message_class(d)}, refs: {_REFS}) -> {returns}:\n"
      + "\n".join(body)
      + "\n"
    )
    return fn

  # -- requests and responses --

  def request_functions(self, rpc: Rpc) -> Tuple[str, str]:
    """Write the functions that make an RPC's request, and that make the call it asks for."""
    service, cls, name = rpc.service, rpc.service.cls, rpc.python
    fn = _members_of(cls)[name]
    sig = inspect.signature(fn)
    hints = typing.get_type_hints(fn)
    written = _signature(self.m, cls, name)
    d = rpc.method.input_type
    request_cls = self.m.message_class(d)
    stem = f"{service.short}_{name}"
    forwarded = _forwarded_hints(cls, name)
    routing = ROUTING.get(service.name, ())
    parameters = list(sig.parameters.values())[1:]
    by_name = {p.name: p for p in written.parameters}

    # The client's: the request a call makes.
    params = ", ".join(
      f"{p.name}: Dict[str, Any]" if p.kind == "var_keyword" else f"{p.name}: {p.annotation}"
      for p in written.parameters
    )
    enc = [f"def encode_{stem}_request({'*, ' + params if params else ''}) -> {request_cls}:"]
    enc.append(f'  """A call to {cls.__name__}.{name}, as its request."""')
    enc.append(f"  request = {request_cls}()")
    for p in parameters:
      if p.kind is p.VAR_KEYWORD:
        key, item = self.fresh("key"), self.fresh("item")
        enc.append(f"  for {key}, {item} in {p.name}.items():")
        if "parameters" in d.fields_by_name and not forwarded:
          enc.append(f"    request.parameters[{key}] = str({item})")
          continue
        for i, fd in enumerate(d.fields):
          enc.append(f"    {'if' if i == 0 else 'elif'} {key} == {fd.name!r}:")
          self.set_field(fd, forwarded.get(fd.name, Any), "request", item, enc, "      ")
        enc.append("    else:")
        enc.append(
          f"      raise TypeError(f\"{name}() got an unexpected keyword argument '{{{key}}}'\")"
        )
        continue
      t = parameter_type(p, hints)
      oneof = _real_oneof(d, p.name)
      if oneof is not None:
        inner, optional = strip_optional(t)
        ind = "  "
        if optional:
          enc.append(f"  if {p.name} is not None:")
          ind = "    "
        for i, (fd, member) in enumerate(zip(oneof.fields, members(inner))):
          enc.append(f"{ind}{'if' if i == 0 else 'elif'} {self.condition(member, p.name)}:")
          self.set_field(fd, member, "request", p.name, enc, ind + "  ")
        enc.append(f"{ind}else:")
        enc.append(
          f'{ind}  raise TypeError(f"{p.name}: {{{p.name}!r}} is none of {self.m.type_text(inner)}")'
        )
        continue
      self.set_field(d.fields_by_name[p.name], t, "request", p.name, enc, "  ")
    enc.append("  return request")
    self.m.blocks.append("\n".join(enc) + "\n")

    # The server's: the call a request asks for.
    target = self.m.name_of(cls)
    returns = written.returns or "Any"
    call = [
      f"async def call_{stem}(target: {target}, request: {request_cls}, refs: {_REFS}) -> {returns}:"
    ]
    call.append(f'  """The call to {cls.__name__}.{name} a request asks for."""')
    passed: List[str] = []
    for p in parameters:
      if p.kind is p.VAR_KEYWORD:
        continue
      local = f"a_{p.name}"
      w = by_name[p.name]
      t = parameter_type(p, hints)
      passed.append(f"{p.name}={local}")
      oneof = _real_oneof(d, p.name)
      call.append(f"  {local}: {w.annotation}")
      if oneof is not None:
        inner, _ = strip_optional(t)
        which = self.fresh("which")
        call.append(f"  {which} = request.WhichOneof({p.name!r})")
        handle_members = [m for m in typing.get_args(inner) if is_handle(m)]
        for i, (fd, member) in enumerate(zip(oneof.fields, members(inner))):
          member_t = typing.Union[tuple(handle_members)] if is_handle(member) else member
          call.append(f"  {'if' if i == 0 else 'elif'} {which} == {fd.name!r}:")
          call.append(f"    {local} = {self.get_field(fd, member_t, 'request', presence=False)}")
        call.append("  else:")
        if w.default is None:
          call.append(f'    raise TypeError("{name}() missing required argument: {p.name!r}")')
        else:
          call.append(f"    {local} = {w.default}")
        continue
      fd = d.fields_by_name[p.name]
      value = self.get_field(fd, t, "request", presence=False)
      if fd.has_presence:
        call.append(f"  if request.HasField({p.name!r}):")
        call.append(f"    {local} = {value}")
        call.append("  else:")
        if w.default is None:
          call.append(f'    raise TypeError("{name}() missing required argument: {p.name!r}")')
        else:
          call.append(f"    {local} = {w.default}")
      elif w.default is None:
        call.append(f"  {local} = {value}")
      else:
        call.append(f"  {local} = {value}")
        call.append(f"  if not {local}:")
        call.append(f"    {local} = {w.default}")
    if any(p.kind is p.VAR_KEYWORD for p in parameters):
      named = {p.name for p in parameters}
      call.append("  extra: Dict[str, Any] = {}")
      if not forwarded and "parameters" in d.fields_by_name:
        call.append("  extra.update(request.parameters)")
      for fd in d.fields:
        if fd.name in named or fd.name in routing or fd.name not in forwarded:
          continue
        value = self.get_field(fd, forwarded[fd.name], "request", presence=False)
        if fd.has_presence:
          call.append(f"  if request.HasField({fd.name!r}):")
          call.append(f"    extra[{fd.name!r}] = {value}")
        else:
          call.append(f"  extra[{fd.name!r}] = {value}")
      passed.append("**extra")
    call.append(f"  return await target.{name}({', '.join(passed)})")
    self.m.blocks.append("\n".join(call) + "\n")
    return f"encode_{stem}_request", f"call_{stem}"

  def response_functions(self, rpc: Rpc) -> Tuple[str, str]:
    """Write the functions that make an RPC's response, and that read it; their names."""
    service, cls, name = rpc.service, rpc.service.cls, rpc.python
    fn = _members_of(cls)[name]
    t = typing.get_type_hints(fn).get("return", inspect.Parameter.empty)
    d = rpc.method.output_type
    response_cls = self.m.message_class(d)
    stem = f"{service.short}_{name}"
    value_type = self.m.type_text(t)
    enc = [f"def encode_{stem}_response(value: {value_type}) -> {response_cls}:"]
    enc.append(f'  """What {cls.__name__}.{name} returned, as its response."""')
    enc.append(f"  response = {response_cls}()")
    dec = [f"def decode_{stem}_response(response: {response_cls}) -> {value_type}:"]
    dec.append(f'  """What {cls.__name__}.{name} returned, from its response."""')
    dec.append("  refs: wire.Refs = {}")
    if not d.fields:
      dec.append("  return None")
    elif t is inspect.Parameter.empty:
      self.set_field(d.fields[0], Any, "response", "value", enc, "  ")
      dec.append(f"  return {self.get_field(d.fields[0], Any, 'response')}")
    else:
      inner, _ = strip_optional(t)
      if is_typeddict(inner):
        enc.append(f"  {self.fill_function(d, inner)}(response, value)")
        dec.append(f"  return {self.read_function(d, inner)}(response, refs)")
      elif typing.get_origin(inner) is tuple and len(d.fields) > 1:
        ind = "  "
        if inner is not t:
          enc.append("  if value is not None:")
          ind = "    "
        items = []
        for i, (fd, item_t) in enumerate(zip(d.fields, typing.get_args(inner))):
          self.set_field(fd, item_t, "response", f"value[{i}]", enc, ind)
          items.append(self.get_field(fd, item_t, "response"))
        dec.append(f"  return ({', '.join(items)},)")
      else:
        self.set_field(d.fields[0], t, "response", "value", enc, "  ")
        dec.append(f"  return {self.get_field(d.fields[0], t, 'response')}")
    enc.append("  return response")
    self.m.blocks.append("\n".join(enc) + "\n")
    self.m.blocks.append("\n".join(dec) + "\n")
    return f"encode_{stem}_response", f"decode_{stem}_response"

  # -- settings and configurations --

  def settings_functions(self, service: Service) -> None:
    message = settings_message(service)
    assert message is not None
    cls = service.cls
    msg_cls, feature = self.m.message_class(message), self.m.name_of(cls)
    describe = [
      f"def describe_{service.short}_settings(message: {msg_cls}, feature: {feature}) -> None:"
    ]
    describe.append(
      f'  """Fill a {message.name} with a {cls.__name__}\'s settings; one it cannot say'
    )
    describe.append('  is left unset."""')
    put = [f"def put_{service.short}_settings(feature: {feature}, message: {msg_cls}) -> None:"]
    put.append(f'  """Set what a {message.name} gives on a {cls.__name__}."""')
    for fd in message.fields:
      attr = _attribute(fd.name)
      describe += [
        "  try:",
        f"    {attr} = feature.{attr}",
        "  except RuntimeError:",
        "    pass",
        "  else:",
        f"    if {attr} is not None:",
        f"      message.{attr} = {attr}",
      ]
      given = f"message.HasField({attr!r})" if fd.has_presence else f"message.{attr}"
      put += [f"  if {given}:", f"    feature.{attr} = message.{attr}"]
    self.m.blocks.append("\n".join(describe) + "\n")
    self.m.blocks.append("\n".join(put) + "\n")

  def configuration_functions(self, stem: str, d: Descriptor, t: type) -> None:
    fill, read = self.fill_function(d, t), self.read_function(d, t)
    msg_cls, value_cls = self.m.message_class(d), self.m.name_of(t)
    self.m.blocks.append(
      f"def fill_{stem}(message: {msg_cls}, value: {value_cls}) -> None:\n"
      f'  """A {d.name} from a {t.__name__}."""\n'
      f"  {fill}(message, value)\n"
    )
    self.m.blocks.append(
      f"def read_{stem}(message: {msg_cls}) -> {value_cls}:\n"
      f'  """A {d.name} as a {t.__name__}."""\n'
      f"  return {read}(message, {{}})\n"
    )


def _codec() -> Tuple[str, Dict[Tuple[str, str], Tuple[str, str, str, str]]]:
  codec = _Codec()
  functions: Dict[Tuple[str, str], Tuple[str, str, str, str]] = {}
  for service in SERVICES:
    for rpc in rpcs(service):
      encode_request, call = codec.request_functions(rpc)
      encode_response, decode_response = codec.response_functions(rpc)
      functions[(service.name, rpc.python)] = (
        encode_request,
        call,
        encode_response,
        decode_response,
      )
    if service.has_settings:
      codec.settings_functions(service)
  for stem, d, t in CONFIGURATIONS:
    codec.configuration_functions(stem, d, t)

  table = [
    "@dataclasses.dataclass(frozen=True)",
    "class Rpc:",
    '  """One RPC: the method it calls, its messages, and the functions that convert them."""',
    "",
    "  service: str",
    "  method: Callable[..., Any]",
    "  request: Type[Any]",
    "  response: Type[Any]",
    "  encode_request: Callable[..., Any]",
    "  call: Callable[..., Any]",
    "  encode_response: Callable[..., Any]",
    "  decode_response: Callable[..., Any]",
    "",
    "",
    "# Every RPC that calls a method.",
    "RPCS: List[Rpc] = [",
  ]
  for service in SERVICES:
    cls = codec.m.name_of(service.cls)
    for rpc in rpcs(service):
      er, call, es, ds = functions[(service.name, rpc.python)]
      table.append(
        f"  Rpc({service.name!r}, {cls}.{rpc.python}, "
        f"{codec.m.message_class(rpc.method.input_type)}, "
        f"{codec.m.message_class(rpc.method.output_type)}, {er}, {call}, {es}, {ds}),"
      )
  table.append("]")
  codec.m.blocks.append("\n".join(table) + "\n")
  text = codec.m.render(
    "Each STAR RPC's arguments and result to and from its messages, field by field.",
    preamble=[
      "import dataclasses",
      "from typing import (",
      "  Any,",
      "  Callable,",
      "  Dict,",
      "  List,",
      "  Literal,",
      "  Mapping,",
      "  Optional,",
      "  Sequence,",
      "  Tuple,",
      "  Type,",
      "  Union,",
      "  cast,",
      ")",
      "",
      "from pylabrobot.hamilton.star.server import wire",
    ],
  )
  return text, functions


def _handlers(functions: Dict[Tuple[str, str], Tuple[str, str, str, str]]) -> str:
  m = _Module(
    reserved=["codec", "Served", "Ctx", "ASGIApp"], given=["Any", "Awaitable", "Callable", "Dict"]
  )
  apps: List[str] = []
  for service in SERVICES:
    prefix = service.name.removesuffix("Service")
    lines = [f"class {prefix}Handlers:"]
    lines.append(f'  """{service.name}: each RPC a call on the served {service.cls.__name__}."""')
    lines.append("")
    lines.append("  def __init__(self, served: Served) -> None:")
    lines.append("    self._served = served")
    descriptor = service.module.DESCRIPTOR.services_by_name[service.name]
    for method in descriptor.methods:
      if method.name in EXTRA_RPCS:
        req, res = m.message_class(method.input_type), m.message_class(method.output_type)
        lines.append("")
        lines.append(
          f"  async def {_connect_name(service, method.name)}(self, request: {req}, ctx: Ctx) -> {res}:"
        )
        lines.append("    return await self._served.describe(ctx)")
    for rpc in rpcs(service):
      er, call, es, ds = functions[(service.name, rpc.python)]
      req, res = m.message_class(rpc.method.input_type), m.message_class(rpc.method.output_type)
      setup = (service.name, rpc.python) in SETUP
      lines += [
        "",
        f"  async def {rpc.connect_name}(self, request: {req}, ctx: Ctx) -> {res}:",
        f"    async def run() -> {res}:",
        f"      target = {service.target}",
        "      refs = await self._served.refs(request)",
      ]
      result = typing.get_type_hints(_members_of(service.cls)[rpc.python]).get("return")
      if result is _NoneType:
        lines += [
          f"      await codec.{call}(target, request, refs)",
          f"      return codec.{es}(None)",
        ]
      else:
        lines.append(f"      return codec.{es}(await codec.{call}(target, request, refs))")
      lines += [
        "",
        f"    return await self._served.run(ctx, run{', setup=True' if setup else ''})",
      ]
    m.blocks.append("\n".join(lines) + "\n")
    connect = m.module_of(_connect_module(service).__name__)
    full = descriptor.full_name
    apps.append(
      f'    "/{full}/": {connect}.{service.name}ASGIApplication({prefix}Handlers(served)),'
    )
  m.blocks.append(
    "def applications(served: Served) -> Dict[str, ASGIApp]:\n"
    '  """Each service\'s application, by the path its calls start with."""\n'
    "  return {\n" + "\n".join(apps) + "\n  }\n"
  )
  return m.render(
    "Each STAR service's handlers: every RPC a call on the device a server serves.",
    preamble=[
      "from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict",
      "",
      "from connectrpc.request import RequestContext",
      "",
      "from pylabrobot.hamilton.star.server import generated_codec as codec",
      "",
      "if TYPE_CHECKING:",
      "  from pylabrobot.hamilton.star.server.serve import Served",
      "",
      "# An ASGI 3 application.",
      "ASGIApp = Callable[[Dict[str, Any], Any, Any], Awaitable[None]]",
      "Ctx = RequestContext[Any, Any]",
    ],
  )


def _setting_property(
  m: _Module, service: Service, name: str, base: str, constant: bool
) -> List[str]:
  static = inspect.getattr_static(service.cls, name, None)
  if isinstance(static, property):
    hint = typing.get_type_hints(static.fget).get("return", Any)
  else:
    hint = typing.get_type_hints(service.cls).get(name, Any)
  t = m.type_text(hint)
  message = "_CONSTANT" if constant else "_SETTING"
  lines = ["", "  @property", f"  def {name}(self) -> {t}:"]
  if isinstance(static, property):
    lines.append(f"    return super().{name}")
  else:
    lines.append(f"    held: {t} = self._held.get({name!r}, {base}.{name})")
    lines.append("    return held")
  lines += [
    "",
    f"  @{name}.setter",
    f"  def {name}(self, value: {t}) -> None:",
    "    if self._ready:",
    f"      raise AttributeError({message}.format({name!r}))",
  ]
  lines.append(
    f"    self._{name} = value"
    if isinstance(static, property)
    else f"    self._held[{name!r}] = value"
  )
  return lines


def _remote(functions: Dict[Tuple[str, str], Tuple[str, str, str, str]]) -> str:
  m = _Module(
    reserved=[
      "codec",
      "Feature",
      "_CONSTANT",
      "_SETTING",
      "x_arm_side",
      "STARServer",
      "TYPE_CHECKING",
    ],
    given=[
      "Any",
      "Callable",
      "Dict",
      "List",
      "Literal",
      "Mapping",
      "Optional",
      "Sequence",
      "Tuple",
      "Union",
      "overload",
    ],
  )
  clients = ["class STARClients:", '  """A Connect client for every STAR service."""', ""]
  clients.append("  def __init__(self, address: str, http: Any, interceptors: Any) -> None:")
  for service in SERVICES:
    connect = m.module_of(_connect_module(service).__name__)
    clients.append(
      f"    self.{service.short} = {connect}.{service.name}Client("
      "address, http_client=http, interceptors=interceptors)"
    )
  clients += ["", "  async def close(self) -> None:"]
  clients += [f"    await self.{service.short}.close()" for service in SERVICES]
  m.blocks.append("\n".join(clients) + "\n")

  for service in SERVICES:
    base = m.name_of(service.cls)
    is_feature = service.cls not in (STARDevice, STARDriver)
    # The client's name for each class: `Remote` and the class's name, capitalised.
    capitalised = service.cls.__name__[0].upper() + service.cls.__name__[1:]
    class_name = f"Remote{capitalised}" if is_feature else f"_Remote{capitalised}Calls"
    parents = f"Feature, {base}" if is_feature else base
    lines = [f"class {class_name}({parents}):"]
    lines.append(f'  """{service.cls.__name__}, every method the server serves a call to it."""')
    if not is_feature:
      lines += ["", "  _star_server: STARServer"]
    if is_feature:
      lines += [
        "",
        "  def __init__(self, *args: Any, **kwargs: Any) -> None:",
        "    self._held: Dict[str, Any] = {}",
        "    self._ready = False",
        "    super().__init__(*args, **kwargs)",
      ]
    for rpc in rpcs(service):
      er, call, es, ds = functions[(service.name, rpc.python)]
      written = _signature(m, service.cls, rpc.python)
      lines.append("")
      for overload_text in written.overloads:
        lines += ["  @overload", f"  {overload_text}", ""]
      returns = f" -> {written.returns}" if written.returns else ""
      lines.append(f"  async def {rpc.python}({written.arguments}){returns}:")
      passed = ", ".join(f"{p.name}={p.name}" for p in written.parameters)
      lines.append(f"    request = codec.{er}({passed})")
      for field in ROUTING.get(service.name, ()):
        lines.append(f"    request.{field} = x_arm_side(self.{field})")
      lines.append(
        f"    response = await self._star_server.call(self._star_server.clients.{service.short}"
        f".{rpc.connect_name}(request))"
      )
      lines.append(f"    return codec.{ds}(response)")
      lines.append("")
      lines.append(f"  {rpc.python}.__doc__ = {base}.{rpc.python}.__doc__")
    if is_feature:
      settings = setting_names(service)
      for name in settings:
        lines += _setting_property(m, service, name, base, constant=False)
      for name in sorted(CONSTANTS.get(service.cls, frozenset()) - set(settings)):
        lines += _setting_property(m, service, name, base, constant=True)
      message = settings_message(service)
      if message is not None:
        lines += ["", f"  def _apply_settings(self, message: {m.message_class(message)}) -> None:"]
        lines.append('    """Take the settings up as a description has them."""')
        for fd in message.fields:
          attr = _attribute(fd.name)
          given = f"message.HasField({attr!r})" if fd.has_presence else f"message.{attr}"
          if isinstance(inspect.getattr_static(service.cls, attr, None), property):
            # A property's value is kept where its setter keeps it.
            lines.append(f"    self._{attr} = message.{attr} if {given} else None")
          else:
            lines += [f"    if {given}:", f"      self._held[{attr!r}] = message.{attr}"]
    m.blocks.append("\n".join(lines) + "\n")
  return m.render(
    "The STAR's classes, every public coroutine a call to a STAR server.",
    preamble=[
      "from typing import (",
      "  TYPE_CHECKING,",
      "  Any,",
      "  Callable,",
      "  Dict,",
      "  List,",
      "  Literal,",
      "  Mapping,",
      "  Optional,",
      "  Sequence,",
      "  Tuple,",
      "  Union,",
      "  overload,",
      ")",
      "",
      "from pylabrobot.hamilton.star.server import generated_codec as codec",
      "from pylabrobot.hamilton.star.server.feature import CONSTANT_MESSAGE as _CONSTANT",
      "from pylabrobot.hamilton.star.server.feature import SETTING_MESSAGE as _SETTING",
      "from pylabrobot.hamilton.star.server.feature import Feature, x_arm_side",
      "",
      "if TYPE_CHECKING:",
      "  from pylabrobot.hamilton.star.server.client import STARServer",
    ],
  )


def render() -> Dict[str, str]:
  """Each generated file's contents, by its path."""
  codec, functions = _codec()
  return {
    os.path.join(_HERE, "generated_codec.py"): codec,
    os.path.join(_HERE, "generated_handlers.py"): _handlers(functions),
    os.path.join(_HERE, "generated_remote.py"): _remote(functions),
  }


def main() -> None:
  for path, text in render().items():
    with open(path, "w", encoding="utf-8") as f:
      f.write(text)
    print(f"wrote {os.path.relpath(path)}")


if __name__ == "__main__":
  main()
