"""Fixtures the STAR tests share.

Here rather than beside the driver because nothing the package ships uses them: they exist to
build devices to test against, not to describe a device anything runs on.
"""

from pylabrobot.hamilton.star.driver.features.x_arm import XArmConfiguration
from pylabrobot.resources.store import handles
from pylabrobot.resources.store.client import ResourceStore


async def make_deck(model: str = "STARDeck", name: str = "deck") -> handles.Deck:
  """A deck standing on its own, in a new store held in this process.

  Args:
    model: which deck, by model name.
    name: what to call it; "deck" keeps its built-in parts' short names.
  """
  deck = await ResourceStore.in_process().create(model, name=name)
  assert isinstance(deck, handles.Deck)
  return deck


# An arm that carries nothing: the geometry of a STAR arm with none of its feature bits set. The
# firmware requires the two drives' bits to be disjoint, so a device with two arms has its features
# on one of them and an arm like this as the other. Its firmware is the arm's, since it stands in
# for a real one.
BARE_X_ARM = XArmConfiguration(
  firmware_version="1.4S 2012-04-25",
  width=354.0,
  x_range=(95.0, 1340.2),
  workspace_x_range=(-323.2, 1517.2),
  wrap_size=595.2,
)
