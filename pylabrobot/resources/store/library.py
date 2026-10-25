"""PLR's labware as models: one JSON file per model, the proto3 JSON of a `ResourceModel`.

A model's file is in the `models` directory beside the module whose factory it was made from:
`Cor_96_wellplate_360ul_Fb` from `pylabrobot.resources.corning.plates` is
`pylabrobot/resources/corning/models/Cor_96_wellplate_360ul_Fb.json`. Its definition is the
factory's resource built with the name `{name}`, so every name in it follows the instance's, and its
uniform grids of items are given once (see `models`).

The files are what PLR's stores start with (`LIBRARY`). The factories are kept only to write them,
and a test checks they still match:

  python -m pylabrobot.resources.store.library

A deprecated factory that builds another's labware has no file of its own: its name is an alias of
that model, kept in `model_aliases.json`.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import json
import pathlib
import pkgutil
import warnings
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Sequence, Tuple

from google.protobuf import json_format

from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.models import compact_grids
from pylabrobot.resources.store.v1 import types_pb2 as pb

if TYPE_CHECKING:
  from pylabrobot.resources.resource import Resource

MODELS_DIRECTORY = "models"
ROOT = pathlib.Path(__file__).resolve().parent.parent
ALIASES = pathlib.Path(__file__).resolve().parent / "model_aliases.json"


def _factories(deprecated: bool) -> List[Tuple[str, Callable[..., Resource]]]:
  """The labware factories in `pylabrobot.resources` that build from a name alone, by qualified
  name, in order: those that are not deprecated aliases, or only those that are. Definitions that
  refuse to build are left out."""
  import pylabrobot.resources as resources
  from pylabrobot.resources.resource import Resource

  found: Dict[str, Callable[..., Resource]] = {}
  for info in pkgutil.walk_packages(
    resources.__path__, "pylabrobot.resources.", onerror=lambda name: None
  ):
    if info.name.endswith("_tests") or ".store" in info.name:
      continue
    try:
      with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        module = importlib.import_module(info.name)
    except (ImportError, NotImplementedError, DeprecationWarning):
      continue
    for name, function in inspect.getmembers(module, inspect.isfunction):
      if function.__module__ != module.__name__ or name.startswith("_"):
        continue
      parameters = inspect.signature(function).parameters
      if "name" not in parameters or any(
        parameter.default is inspect.Parameter.empty
        for key, parameter in parameters.items()
        if key != "name"
      ):
        continue
      with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        try:
          built = function(name="labware")
          is_alias = False
        except DeprecationWarning:
          is_alias = True
        except Exception:
          continue
      if is_alias != deprecated:
        continue
      if is_alias:
        with warnings.catch_warnings():
          warnings.simplefilter("ignore")
          try:
            built = function(name="labware")
          except Exception:
            continue
      if isinstance(built, Resource):
        found[f"{module.__name__}.{name}"] = function
  return sorted(found.items())


def labware_factories() -> List[Tuple[str, Callable[..., Resource]]]:
  """Every labware factory in `pylabrobot.resources` that builds from a name alone, by its
  qualified name, in order. Deprecated aliases and definitions that refuse to build are left out.
  """
  return _factories(deprecated=False)


def model_from_factory(factory: Callable[..., Resource]) -> pb.ResourceModel:
  """The model a factory builds, named after it, with its docstring as its description."""
  from pylabrobot.resources.store.definitions import definition_from_resource

  with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    definition = definition_from_resource(factory(name="{name}"))
  compact_grids(definition)
  return pb.ResourceModel(
    name=factory.__name__,
    definition=definition,
    description=(inspect.getdoc(factory) or "").strip(),
  )


def model_path(qualified: str) -> pathlib.Path:
  """Where the model of the factory `module.function` is kept."""
  module, name = qualified.rsplit(".", 1)
  package = pathlib.Path(*module.split(".")[2:-1])
  return ROOT / package / MODELS_DIRECTORY / f"{name}.json"


def to_json(model: pb.ResourceModel) -> str:
  """A model as its file holds it."""
  return json.dumps(json_format.MessageToDict(model), indent=2) + "\n"


@functools.lru_cache(maxsize=None)
def _paths() -> Dict[str, pathlib.Path]:
  return {path.stem: path for path in sorted(ROOT.glob(f"**/{MODELS_DIRECTORY}/*.json"))}


@functools.lru_cache(maxsize=None)
def aliases() -> Dict[str, str]:
  """Each deprecated factory's name, and the name of the model it builds."""
  return dict(json.loads(ALIASES.read_text())) if ALIASES.exists() else {}


def get_model_path(name: str) -> pathlib.Path:
  """Where a model of PLR's is kept.

  Raises:
    StoreError: PLR has no model of that name.
  """
  path = _paths().get(name)
  if path is None:
    raise StoreError(pb.PROBLEM_NOT_FOUND, f"no model named '{name}'", name)
  return path


def model_names() -> List[str]:
  """The name of every model PLR has, in order; not its aliases."""
  return sorted(_paths())


@functools.lru_cache(maxsize=None)
def _parsed(name: str) -> pb.ResourceModel:
  return json_format.Parse(get_model_path(name).read_text(), pb.ResourceModel())


def get_model(name: str) -> pb.ResourceModel:
  """A model of PLR's, by its name or an alias of it.

  Raises:
    StoreError: PLR has no model of that name.
  """
  model = pb.ResourceModel()
  model.CopyFrom(_parsed(aliases().get(name, name)))
  return model


class Library:
  """PLR's models, as a store starts with them: each read from its file when first asked for."""

  def names(self) -> Sequence[str]:
    return model_names()

  def get(self, name: str) -> Optional[pb.ResourceModel]:
    if name not in _paths() and name not in aliases():
      return None
    return get_model(name)


LIBRARY = Library()


def write_models() -> int:
  """Write every factory's model to its file, removing files no factory makes, and the aliases the
  deprecated factories are. How many models it wrote."""
  wanted = {}
  for qualified, factory in labware_factories():
    wanted[model_path(qualified)] = to_json(model_from_factory(factory))
  for path in ROOT.glob(f"**/{MODELS_DIRECTORY}/*.json"):
    if path not in wanted:
      path.unlink()
  for path, text in wanted.items():
    path.parent.mkdir(exist_ok=True)
    if not path.exists() or path.read_text() != text:
      path.write_text(text)
  _paths.cache_clear()
  _parsed.cache_clear()
  ALIASES.write_text(json.dumps(alias_targets(), indent=2, sort_keys=True) + "\n")
  aliases.cache_clear()
  return len(wanted)


def alias_targets() -> Dict[str, str]:
  """Each deprecated factory that builds exactly what a model file holds, and that model's name;
  the first by name where several models are alike."""
  by_definition: Dict[bytes, str] = {}
  for name in model_names():
    serialized = _parsed(name).definition.SerializeToString(deterministic=True)
    by_definition.setdefault(serialized, name)
  found = {}
  for _, factory in _factories(deprecated=True):
    definition = model_from_factory(factory).definition
    target = by_definition.get(definition.SerializeToString(deterministic=True))
    if target is not None:
      found[factory.__name__] = target
  return found


if __name__ == "__main__":
  print(f"wrote {write_models()} models")
