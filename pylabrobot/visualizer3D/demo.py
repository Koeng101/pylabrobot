"""A facility with a simulated STARlet on a bench, in a resource store.

Run it:

    python -m pylabrobot.visualizer3D.demo

The run sets the STARlet up, fills a plate, then moves liquid from it to another plate through the
store, a column at a time. `model_demo` shares the facility built here. Moving parts of the device
are drawn where its driver records them in the store.
"""

import asyncio
import logging
from typing import Dict, List, Tuple

from pylabrobot.hamilton.star import STARDevice, STARlet
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore

from .facility import facility
from .server import Viewer3D

# How high the bench the deck stands on is.
BENCH_HEIGHT = 880.0

# What goes on the deck: a carrier model, its name, the track it stands on, and what each of its
# sites holds, by model and name.
LAYOUT: List[Tuple[str, str, int, List[Tuple[str, str]]]] = [
  (
    "hamilton_tip_carrier_L5",
    "tip_carrier",
    1,
    [
      # Filtered and unfiltered side by side, so the filter in a tip can be told apart.
      ("hamilton_96_tiprack_1000uL", "tips_0"),
      ("hamilton_96_tiprack_1000uL_filter", "tips_1"),
      ("hamilton_96_tiprack_300uL_filter", "tips_2"),
    ],
  ),
  (
    "hamilton_plate_carrier_L5_ac",
    "source_carrier",
    7,
    [("cor_96_wellplate_360uL_Fb", f"source_{slot}") for slot in range(5)],
  ),
  (
    "hamilton_plate_carrier_L5_ac",
    "destination_carrier",
    13,
    [("cor_96_wellplate_360uL_Fb", f"destination_{slot}") for slot in range(5)],
  ),
  (
    "hamilton_tip_carrier_L5_ntr_a00",
    "ntr_carrier",
    19,
    [
      ("hamilton_96_tiprack_10uL_NTR", "ntr_10uL"),
      ("hamilton_96_tiprack_50uL_NTR", "ntr_50uL"),
      ("hamilton_96_tiprack_300uL_NTR", "ntr_300uL"),
    ],
  ),
]


async def build_facility(
  store: ResourceStore, *, bare: bool = False
) -> Tuple[handles.Resource, STARDevice]:
  """A facility with a simulated STARlet standing on a bench, with labware on its deck.

  The STARlet is not set up: `setup()` builds its channels, heads and arm in the store.

  Args:
    store: The store to build it in.
    bare: the STARlet alone at the origin, with nothing else to look at.

  Returns:
    The facility, and the STARlet in it.
  """
  star = STARlet(simulation=True, store=store)
  await star.create_resources()
  body, deck = star.body, star.deck
  assert body is not None and deck is not None
  if bare:
    root = await store.create(facility("facility", 2000, 1200, 1000), name="facility")
    await root.assign_child_resource(body, location=Coordinate.zero())
    return root, star

  root = await store.create(facility("facility", 2600, 1400, 1000), name="facility")
  await root.assign_child_resource(body, location=Coordinate(0, 0, BENCH_HEIGHT))
  # A bench: no deck, no driver, the same cartesian space.
  await store.create(
    build.resource("bench", Coordinate(900, 600, BENCH_HEIGHT), category="bench"),
    name="bench",
    parent=root,
    location=Coordinate(0, 0, 0),
  )
  for model, name, track, sites in LAYOUT:
    carrier = await store.create(model, name=name, parent=deck, track=track)
    assert isinstance(carrier, handles.Carrier)
    for site, (labware, labware_name) in enumerate(sites):
      await store.create(labware, name=labware_name, parent=carrier[site])
  return root, star


async def plates(root: handles.Resource, *names: str) -> Dict[str, handles.Plate]:
  """Plates in the facility, by name."""
  found: Dict[str, handles.Plate] = {}
  for name in names:
    plate = await root.store.get(name, root=root)
    if not isinstance(plate, handles.Plate):
      raise TypeError(f"'{name}' is not a plate")
    found[name] = plate
  return found


async def run(root: handles.Resource) -> None:
  """Move liquid around so the state channel has something to carry: a plate filled, then half of
  each well moved to the other plate, a column at a time."""
  found = await plates(root, "source_0", "destination_0")
  source, destination = found["source_0"], found["destination_0"]

  held = [300.0] * source.num_items
  moved = [0.0] * destination.num_items
  await source.set_well_volumes(held)
  await asyncio.sleep(2.0)

  rows = source.num_items_y
  for column in range(source.num_items_x):
    for index in range(column * rows, (column + 1) * rows):
      taken = min(150.0, held[index])
      held[index] -= taken
      moved[index] += taken
    await source.set_well_volumes(held)
    await destination.set_well_volumes(moved)
    await asyncio.sleep(0.45)

  print("run complete; the viewer stays up")


async def main() -> None:
  logging.disable(logging.WARNING)
  store = ResourceStore.in_memory()
  root, star = await build_facility(store)
  await star.setup()

  viewer = Viewer3D(root, name="demo.py")
  await viewer.start()

  await viewer.wait_for_browser()  # nothing moves before a page is drawing
  await run(root)
  await asyncio.Event().wait()


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    pass
