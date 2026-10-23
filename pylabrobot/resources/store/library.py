"""PLR's labware as models: one JSON file per model, the proto3 JSON of a `ResourceModel`.

A model's file is in the `models` directory beside the module whose factory it was made from:
`Cor_96_wellplate_360ul_Fb` from `pylabrobot.resources.corning.plates` is
`pylabrobot/resources/corning/models/Cor_96_wellplate_360ul_Fb.json`. Its definition is the
factory's resource built with the name `{name}`, so every name in it follows the instance's, and its
uniform grids of items are given once (see `models`).

The files are written from the factories, and checked against them, while both exist:

  python -m pylabrobot.resources.store.library
"""

from __future__ import annotations

import functools
import importlib
import inspect
import json
import pathlib
import pkgutil
import warnings
from typing import Callable, Dict, List, Tuple

from google.protobuf import json_format

import pylabrobot.resources as resources
from pylabrobot.resources.resource import Resource
from pylabrobot.resources.store.definitions import definition_from_resource
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.models import compact_grids
from pylabrobot.resources.store.v1 import types_pb2 as pb

MODELS_DIRECTORY = "models"
ROOT = pathlib.Path(resources.__file__).parent


def labware_factories() -> List[Tuple[str, Callable[..., Resource]]]:
  """Every labware factory in `pylabrobot.resources` that builds from a name alone, by its
  qualified name, in order. Deprecated aliases and definitions that refuse to build are left out.
  """
  found: Dict[str, Callable[..., Resource]] = {}
  with warnings.catch_warnings():
    warnings.simplefilter("error", DeprecationWarning)
    for info in pkgutil.walk_packages(
      resources.__path__, "pylabrobot.resources.", onerror=lambda name: None
    ):
      if info.name.endswith("_tests") or ".store" in info.name:
        continue
      try:
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
        try:
          built = function(name="labware")
        except Exception:
          continue
        if isinstance(built, Resource):
          found[f"{module.__name__}.{name}"] = function
  return sorted(found.items())


def model_from_factory(factory: Callable[..., Resource]) -> pb.ResourceModel:
  """The model a factory builds, named after it, with its docstring as its description."""
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
  """The name of every model PLR has, in order."""
  return sorted(_paths())


def get_model(name: str) -> pb.ResourceModel:
  """A model of PLR's, by name.

  Raises:
    StoreError: PLR has no model of that name.
  """
  return json_format.Parse(get_model_path(name).read_text(), pb.ResourceModel())


def write_models() -> int:
  """Write every factory's model to its file, removing files no factory makes. How many it wrote."""
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
  return len(wanted)


if __name__ == "__main__":
  print(f"wrote {write_models()} models")
