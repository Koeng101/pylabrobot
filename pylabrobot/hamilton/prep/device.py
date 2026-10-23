"""The Prep: the device, and what it knows about its own deck."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from pylabrobot.hamilton.prep.driver.features.calibration import Calibration
from pylabrobot.hamilton.prep.driver.features.core_grippers import CoreGrippers
from pylabrobot.hamilton.prep.driver.features.head8 import Head8
from pylabrobot.hamilton.prep.driver.features.heater_shaker import PrepHamiltonHeaterShaker
from pylabrobot.hamilton.prep.driver.features.lights import Lights
from pylabrobot.hamilton.prep.driver.features.method import MethodLifecycle
from pylabrobot.hamilton.prep.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.prep.driver.features.x_arm import XArm
from pylabrobot.hamilton.prep.driver.master import PrepDriver
from pylabrobot.hamilton.prep.driver.simulator import PrepSimulationDriver
from pylabrobot.hamilton.prep.deck import PREP_DECK_SIZE, PrepDeckParts, prep_deck, read_prep_deck
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError
from pylabrobot.resources.store.tree import to_coordinate
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.hamilton.prep.driver.model import get_nodes, ref

logger = logging.getLogger(__name__)

# How big the device is.
PREP_SIZE_X = 497.0
PREP_SIZE_Y = 575.0
PREP_SIZE_Z = 575.0

# Where the deck sits inside the device, from the device's left front bottom corner to the deck's.
# It also places Prep.glb, so it moves with PREP_FIRST_SLOT_LOCATION.
PREP_DECK_LOCATION = Coordinate(29.20, 88.02, 50.0)

# The device's model with a heater shaker fitted: Prep.glb's frame opened at the back left, where the
# heater shaker stands in place of spot_0_3, without that spot's position labels.
PREP_HEATER_SHAKER_MODEL = "Prep_heater_shaker"


class PrepDevice:
  """The complete modelling and control interface for a Hamilton Prep.

  The device's body is a resource in a resource store, and its deck is the body's child, so
  everything on the deck is a descendant of the device carrying it: one tree, rooted at the body.

  Two tiers over one driver. `prep.driver` speaks to the device in its own terms and stays reachable
  whatever is built on top of it. The device adds what the driver cannot know: where things are.
  """

  def __init__(
    self,
    deck: Optional[handles.Deck],
    driver: PrepDriver,
    name: str = "Generic Prep Device",
    size_x: Optional[float] = None,
    size_y: Optional[float] = None,
    size_z: Optional[float] = None,
    deck_location: Optional[Coordinate] = None,
    model: Optional[str] = None,
    store: Optional[ResourceStore] = None,
  ):
    """
    Args:
      deck: the deck this device carries, in its store. It becomes a child of the device's body,
        so everything assigned to it is a descendant of this device. None builds a Prep deck,
        whose parts' names start with `name`.
      driver: the driver to drive the device through.
      name: what to call this device in the resource tree.
      size_x: how wide the device is, in mm. Defaults to the deck's own width.
      size_y: how deep it is, in mm. Defaults to the deck's own depth.
      size_z: how tall it is, in mm. Defaults to the deck's own height.
      deck_location: where the deck sits inside it. Defaults to the device's own origin.
      model: which device this is. Defaults to the class name, which says only that it is a Prep.
      store: the resource store to model the device in: `deck`'s when a deck is given, a new
        in-memory one when neither is.
    """
    self.name = name
    self.driver = driver
    self.model = model if model is not None else self.__class__.__name__
    self._size = (size_x, size_y, size_z)
    self._deck_location = deck_location if deck_location is not None else Coordinate(0, 0, 0)
    self._deck: Optional[handles.Deck] = deck
    if deck is not None:
      store = deck.store
    self.store = store if store is not None else ResourceStore.in_memory()
    # The device's body in the store; found or made by `create_resources`.
    self.body: Optional[handles.Resource] = None

  @property
  def deck(self) -> handles.Deck:
    """The deck this device carries.

    Raises:
      RuntimeError: If it has not been made yet: `create_resources` or `setup` makes it.
    """
    if self._deck is None:
      raise RuntimeError("the deck is made at setup; call `await prep.create_resources()` first")
    return self._deck

  async def create_resources(self) -> None:
    """Find the device's body and deck in its store, or make them; the driver models into the deck.

    A body already in the store by this device's name is this device, as one reconnecting finds it.
    Repeatable: once found, nothing more is read.
    """
    if self.body is not None:
      return
    try:
      body: Optional[handles.Resource] = await self.store.get(self.name)
    except StoreError as error:
      if error.problem != pb.PROBLEM_NOT_FOUND:
        raise
      body = None
    if body is None:
      deck_size = PREP_DECK_SIZE if self._deck is None else await self._deck.get_absolute_size()
      size_x, size_y, size_z = self._size
      children = []
      if self._deck is None:
        deck = prep_deck(f"{self.name}_deck", name_prefix=self.name)
        deck.attributes.location.CopyFrom(build.vec3(self._deck_location))
        children.append(deck)
      body = await self.store.create(
        build.resource(
          self.name,
          Coordinate(
            deck_size.x if size_x is None else size_x,
            deck_size.y if size_y is None else size_y,
            deck_size.z if size_z is None else size_z,
          ),
          type_name="PrepDevice",
          category="device",
          model=self.model,
          children=children,
        ),
        name=self.name,
      )
      if self._deck is not None:
        await body.assign_child_resource(self._deck, location=self._deck_location)
    if self._deck is None:
      found = await body.find_resources(kinds=[pb.RESOURCE_KIND_DECK])
      deck_found = found[0] if found else None
      if not isinstance(deck_found, handles.Deck):
        raise RuntimeError(f"'{self.name}' carries no deck")
      self._deck = deck_found
    self.body = body
    if self.driver.deck is not None and self.driver.deck != self._deck:
      logger.warning("the driver was given another deck; modelling into this device's instead")
    self.driver.deck = self._deck

  async def deck_parts(self) -> PrepDeckParts:
    """The deck's parts, as they stand in the store now: spots, waste block, waste positions."""
    await self.create_resources()
    return await read_prep_deck(self.deck)

  async def setup(
    self,
    smart: bool = True,
    force_initialize: bool = False,
    skip_device_initialization: bool = False,
    default_minimum_traverse_height: Optional[float] = None,
    use_v1_aspirate_dispense: bool = False,
    enable_safe_speeds: bool = False,
    deck_components_offset: Optional[Coordinate] = None,
  ):
    """Bring the device up.

    Args:
      smart: as `PrepDriver.setup` takes it.
      force_initialize: as `PrepDriver.setup` takes it.
      skip_device_initialization: as `PrepDriver.setup` takes it.
      default_minimum_traverse_height: as `PrepDriver.setup` takes it.
      use_v1_aspirate_dispense: as `PrepDriver.setup` takes it.
      enable_safe_speeds: as `PrepDriver.setup` takes it.
      deck_components_offset: shift every labware spot by this, as `update_deck_components` does.
        None leaves them where they are.
    """
    await self.create_resources()
    await self.driver.setup(
      smart=smart,
      force_initialize=force_initialize,
      skip_device_initialization=skip_device_initialization,
      default_minimum_traverse_height=default_minimum_traverse_height,
      use_v1_aspirate_dispense=use_v1_aspirate_dispense,
      enable_safe_speeds=enable_safe_speeds,
    )
    if self.driver.hs is not None and self.body is not None:
      self.model = PREP_HEATER_SHAKER_MODEL
      # The viewer draws the device from its model; the store keeps the one a heater shaker needs.
      await self.body.set_metadata({"model": PREP_HEATER_SHAKER_MODEL})
    if deck_components_offset is not None:
      await self.update_deck_components(deck_components_offset)

  async def stop(self, skip_raise_to_z_safety: bool = False):
    """Put the device down.

    Args:
      skip_raise_to_z_safety: leave the channels where they stand, instead of raising them to Z safety first.
        The next lateral move will crash a channel that is low.
    """
    await self.driver.stop(skip_raise_to_z_safety=skip_raise_to_z_safety)

  async def update_deck_components(self, offset: Coordinate) -> None:
    """Shift every labware spot by `offset`, in software only: nothing is written to the device.

    Each keeps its place among the deck's children.

    Args:
      offset: how far to move each spot, in mm on the deck.
    """
    parts = await self.deck_parts()
    spots = [ref(spot.id) for spot in parts.spots]
    nodes = await get_nodes(self.store, spots)
    assignments = [
      pb.AssignChild(
        child=ref(node.id),
        parent=ref(node.parent_id),
        location=build.vec3(to_coordinate(node.attributes.location) + offset),
        index=node.index,
      )
      for node in nodes
      if node.attributes.HasField("location") and node.parent_id
    ]
    if assignments:
      await self.store.commands.assign_resources(
        spb.AssignResourcesRequest(lock_tokens=self.store.lock_tokens, assignments=assignments)
      )

  # -- what the device carries ------------------------------------------------------------
  # Read through: they do not exist until setup has run.

  @property
  def x_arm(self) -> Optional[XArm]:
    """The X-arm the pipetting channels ride."""
    return self.driver.x_arm

  @property
  def pipettes(self) -> Optional[Pipettes]:
    """The pipetting channels."""
    return self.driver.pipettes

  @property
  def head8(self) -> Optional[Head8]:
    """The 8-channel head, on a device that has one."""
    return self.driver.head8

  @property
  def heater_shaker(self) -> Optional[PrepHamiltonHeaterShaker]:
    """The heater shaker, on a device that has one."""
    return self.driver.hs

  @property
  def core_grippers(self) -> Optional[CoreGrippers]:
    """The CoRe gripper."""
    return self.driver.core_grippers

  @property
  def lights(self) -> Optional[Lights]:
    """The deck light, on a device that has one."""
    return self.driver.lights

  @property
  def method(self) -> Optional[MethodLifecycle]:
    """The method lifecycle."""
    return self.driver.method

  @property
  def calibration(self) -> Optional[Calibration]:
    """Calibration."""
    return self.driver.calibration

  # -- error lighting --------------------------------------------------------

  async def signal_error(self, duration: Optional[float] = 8.0, wait: bool = False) -> None:
    """Pulse the deck red, if this device has a light to say it with. Never raises.

    Args:
      duration: how many seconds to pulse for, or None to leave the deck pulsing after the error.
      wait: hold until the pulse is over, for a script that exits the moment it raises.
    """
    await self.driver.signal_error(duration=duration, wait=wait)

  @asynccontextmanager
  async def error_lighting(
    self, duration: Optional[float] = 8.0, wait: bool = False
  ) -> AsyncIterator[None]:
    """Pulse the deck red when something inside raises, and let it raise on.

    Args:
      duration: how many seconds to pulse for, or None to leave the deck pulsing after the error,
        until the light is turned off or set to something else.
      wait: as `signal_error`.
    """
    async with self.driver.error_lighting(duration=duration, wait=wait):
      yield

  # -- session ---------------------------------------------------------------

  def __str__(self) -> str:
    return f"{self.name}({self.driver.__class__.__name__})"


# # # # Complete Prep Device Factory Function, for convenience in building a configuration.


def Prep(
  deck: Optional[handles.Deck] = None,
  simulation: bool = False,
  host: Optional[str] = None,
  port: int = 2000,
  declared_configuration_json: Optional[str] = None,
  firmware_tree_json: Optional[str] = None,
  driver: Optional[PrepDriver] = None,
  name: str = "Prep",
  size_x: float = PREP_SIZE_X,
  size_y: float = PREP_SIZE_Y,
  size_z: float = PREP_SIZE_Z,
  simulate_motion_time: bool = False,
  motion_time_scale: float = 0.25,
  store: Optional[ResourceStore] = None,
) -> PrepDevice:
  """A Prep, on a Prep deck.

  Args:
    deck: the deck, in its resource store. If omitted, `setup` builds a Prep deck in `store`,
      its parts' names prefixed with `name`. A supplied deck keeps its existing resource names.
    simulation: whether to build a simulated device, which answers without one being connected.
    host: the address the Prep answers on. Required unless simulating or given a driver.
    port: the port it answers on.
    declared_configuration_json: path to a declared configuration, passed to the driver this builds.
      Read only when this builds one: a driver given outright brings its own. A simulated device
      defaults to the recording of a device with an 8-channel head and a heater shaker.
    firmware_tree_json: path to a recorded firmware tree, for a simulated device to have. Defaults to
      that device's (MLPrep Runtime V3.0.20).
    driver: the driver to drive it through, instead of building one.
    name: what to call it.
    size_x: how wide it is, in mm.
    size_y: how deep it is, in mm.
    size_z: how tall it is, in mm.
    simulate_motion_time: for a simulated device, whether each move takes time at all, so a viewer
      shows every step. Ignored for a real device.
    motion_time_scale: the share of the real device's time a simulated move then takes, a quarter
      by default. 1.0 keeps the real time. Ignored for a real device.
    store: the resource store to model the device in when no deck is given. A new in-memory one
      when None.

  Returns:
    The device, on a Prep deck.
  """
  if driver is None:
    if simulation:
      driver = PrepSimulationDriver(
        deck=deck,
        declared_configuration_json=declared_configuration_json,
        firmware_tree_json=firmware_tree_json,
        simulate_motion_time=simulate_motion_time,
        motion_time_scale=motion_time_scale,
      )
    else:
      driver = PrepDriver(
        deck=deck,
        host=host,
        port=port,
        declared_configuration_json=declared_configuration_json,
      )
  return PrepDevice(
    deck=deck,
    driver=driver,
    name=name,
    size_x=size_x,
    size_y=size_y,
    size_z=size_z,
    deck_location=PREP_DECK_LOCATION,
    model=Prep.__name__,
    store=store,
  )
