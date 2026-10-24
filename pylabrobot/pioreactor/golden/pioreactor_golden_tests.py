"""Golden tests of what the Pioreactor does.

The Pioreactor sends no commands: its body is a resource in a store holding one culture vessel.
These scenarios pin its tree, where the vessel sits, what it accepts, and the vessel's volume as
liquid is added and taken.
"""

from __future__ import annotations

import pathlib
import unittest
from typing import Any, Dict, List

from pylabrobot.pioreactor.bioreactors import Pioreactor, pioreactor_20ml
from pylabrobot.resources import Coordinate
from pylabrobot.resources.errors import TooLittleLiquidError, TooLittleVolumeError
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent


class Recorder(recording.Recorder):
  """Records each step's result or error, with the Pioreactor's tree after it."""

  def __init__(self, pioreactor: Pioreactor) -> None:
    super().__init__()
    self.pioreactor = pioreactor

  async def snapshot(self) -> List[Dict[str, Any]]:
    return await snapshot_store(self.pioreactor.store, await self.pioreactor.create_resources())

  async def step(self, call: str, action: recording.Action) -> Any:  # type: ignore[override]
    """Run one step, recording what it returned or raised. The Pioreactor sends nothing."""
    entry: Dict[str, Any] = {"call": call}
    value, error = await self.outcome(action)
    self.add_outcome(entry, value, error)
    entry["resources"] = await self.snapshot()
    self.steps.append(entry)
    return value

  async def finish(self) -> Dict[str, Any]:
    return {"steps": self.steps, "resources": await self.snapshot()}


async def describe(resource: handles.Resource) -> Dict[str, Any]:
  attributes = await resource.attributes()
  size = attributes.size
  return {
    "model": attributes.model or None,
    "category": attributes.category or None,
    "size": [size.x, size.y, size.z],
  }


def container(name: str, kind: pb.ResourceKind = pb.RESOURCE_KIND_CONTAINER):
  """A 23.5 x 23.5 x 57 mm container holding up to 20 mL."""
  return build.resource(
    name,
    Coordinate(23.5, 23.5, 57),
    kind=kind,
    container=pb.ContainerSpec(max_volume=20_000),
    state=pb.ResourceState(volume=pb.VolumeState(tracking_enabled=True)),
  )


async def add_liquid(vessel: handles.Container, volume: float) -> None:
  """A person adds liquid: refused when it does not fit, as a volume tracker refuses it."""
  free = await vessel.get_free_volume()
  if volume - free > 1e-6:
    raise TooLittleVolumeError(f"Not enough space in container: {volume:g}uL > {free:g}uL.")
  await vessel.set_volume(await vessel.get_volume() + volume)


async def remove_liquid(vessel: handles.Container, volume: float) -> None:
  """A person takes liquid: refused when there is not that much, as a volume tracker refuses it."""
  held = await vessel.get_volume()
  if volume - held > 1e-6:
    raise TooLittleLiquidError(f"Container has too little liquid: {volume:g}uL > {held:g}uL.")
  await vessel.set_volume(held - volume)


class PioreactorGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_pioreactor_20ml(self):
    """The 20 mL Pioreactor's tree and its vessel."""
    pioreactor = await pioreactor_20ml("pioreactor")
    body = pioreactor.body
    vessel = await pioreactor.get_vessel()
    spec = (await vessel.attributes()).container
    location = await vessel.get_absolute_location()
    record = {
      "pioreactor": await describe(body),
      "vessel": {
        **await describe(vessel),
        "max_volume": spec.max_volume,
        "material_z_thickness": spec.material_z_thickness,
        "absolute_location": [location.x, location.y, location.z],
      },
      "resources": await snapshot_store(pioreactor.store, body),
    }
    check_golden(self, GOLDEN / "pioreactor_20ml.json", record)

  async def test_vessels_it_accepts(self):
    """It holds one container; anything else, or a second vessel, is refused."""
    pioreactor = Pioreactor(name="pioreactor", size_x=127.74, size_y=85.4, size_z=126.5)
    store = pioreactor.store
    rig = Recorder(pioreactor)
    vessel = await store.create(container("vessel"), name="vessel")
    tube = await store.create(container("tube", pb.RESOURCE_KIND_TUBE), name="tube")
    block = await store.create(build.resource("block", Coordinate(10, 10, 10)), name="block")

    async def vessel_name() -> str:
      return (await pioreactor.get_vessel()).name

    await rig.step("pioreactor.get_vessel()", vessel_name)
    await rig.step(
      "pioreactor.assign_child_resource(block, Coordinate(0, 0, 0))",
      lambda: pioreactor.assign_child_resource(block, Coordinate(0, 0, 0)),
    )
    await rig.step(
      "pioreactor.assign_child_resource(vessel, Coordinate(52.12, 30.95, 76))",
      lambda: pioreactor.assign_child_resource(vessel, Coordinate(52.12, 30.95, 76)),
    )
    await rig.step("pioreactor.get_vessel()", vessel_name)
    await rig.step(
      "pioreactor.assign_child_resource(tube, Coordinate(0, 0, 0))",
      lambda: pioreactor.assign_child_resource(tube, Coordinate(0, 0, 0)),
    )
    await rig.step(
      "pioreactor.unassign_child_resource(vessel)",
      lambda: pioreactor.unassign_child_resource(vessel),
    )
    await rig.step(
      "pioreactor.assign_child_resource(tube, Coordinate(52.12, 30.95, 76))",
      lambda: pioreactor.assign_child_resource(tube, Coordinate(52.12, 30.95, 76)),
    )
    await rig.step("pioreactor.get_vessel()", vessel_name)
    check_golden(self, GOLDEN / "vessels_it_accepts.json", await rig.finish())

  async def test_culture_volume(self):
    """Medium added to and sampled from the vessel is kept on it in the store."""
    pioreactor = await pioreactor_20ml("pioreactor")
    rig = Recorder(pioreactor)
    vessel = await pioreactor.get_vessel()

    await rig.step("vessel.tracker.add_liquid(15000)", lambda: add_liquid(vessel, 15_000))
    await rig.step("vessel.tracker.remove_liquid(1000)", lambda: remove_liquid(vessel, 1_000))
    await rig.step("vessel.tracker.add_liquid(10000)", lambda: add_liquid(vessel, 10_000))
    await rig.step("vessel.tracker.get_used_volume()", vessel.get_volume)
    check_golden(self, GOLDEN / "culture_volume.json", await rig.finish())


if __name__ == "__main__":
  unittest.main()
