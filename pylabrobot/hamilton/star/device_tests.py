import dataclasses
import json
import pathlib
import tempfile
import unittest
from typing import Callable, List, Optional, Tuple, cast

from pylabrobot.hamilton.star.conftest import BARE_X_ARM, make_deck
from pylabrobot.hamilton.star.device import (
  EXTENSION_HOUSING_SIZE_X,
  RECORDING_STAR,
  RECORDING_STAR_HEAD384,
  STAR,
  STAR_DECK_LOCATION,
  STAR_SIZE_X,
  STARDevice,
  STARlet,
  STARPlus,
)
from pylabrobot.hamilton.star.driver.configuration import (
  DeviceConfiguration,
  read_configuration,
)
from pylabrobot.hamilton.star.driver.simulator import STARSimulationDriver
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.server import build, handles
from pylabrobot.resources.server.client import ResourceServer
from pylabrobot.resources.server.v1 import server_pb2 as spb
from pylabrobot.serializer import serialize

# How many tracks each frame's deck has.
STAR_NUM_TRACKS = 54
STARLET_NUM_TRACKS = 30

# The device this package ships a recording of, read through the one reader there is: tests need a
# device to start from, and this is the one they stand in for.
RECORDED_DEVICE = cast(DeviceConfiguration, read_configuration(RECORDING_STAR)["device"])


def declaring(**parts: object) -> str:
  """The shipped recording with parts swapped out, written where it can be read back.

  A declaration is read from a file and nothing else, so a test that needs a device no recording
  describes writes one. Everything not named here stays as the recorded STAR has it.

  Args:
    parts: `device` for the device itself, or a feature name for something the left arm carries.

  Returns:
    The path it was written to.
  """
  tree = json.loads(pathlib.Path(RECORDING_STAR).read_text())
  for name, part in parts.items():
    assert dataclasses.is_dataclass(part) and not isinstance(part, type)
    if name == "device":
      tree["device"] = serialize(dataclasses.asdict(part))
    else:
      tree["arms"]["left"][name] = serialize(dataclasses.asdict(part))
  written = pathlib.Path(tempfile.mkdtemp()) / "declared.json"
  written.write_text(json.dumps(tree))
  return str(written)


class TestConstruction(unittest.IsolatedAsyncioTestCase):
  """What the device wires up when it is built."""

  async def test_the_device_deck_is_what_gets_modelled(self):
    """The deck the device carries is in its body and is what the driver models into, whether
    the driver was built here or handed in pointing at another deck."""
    star = STAR(simulation=True)
    await star.create_resources()
    assert star.deck is not None and star.body is not None
    self.assertEqual(star.driver.deck, star.deck)
    self.assertIn(star.deck, await star.body.get_children())

    deck = await make_deck()
    supplied = STARDevice(
      deck=deck,
      driver=STARSimulationDriver(
        deck=await make_deck(), declared_configuration_json=RECORDING_STAR
      ),
    )
    self.assertEqual(supplied.driver.deck, deck)

  async def test_needs_something_to_drive(self):
    with self.assertRaises(ValueError):
      STARDevice(deck=await make_deck())

  async def test_a_device_finds_its_resources_again(self):
    """A device built again on the server its resources are in takes them up rather than making
    new ones."""
    first = STAR(simulation=True)
    await first.create_resources()
    again = STAR(simulation=True, server=first.server)
    await again.create_resources()
    self.assertEqual(again.body, first.body)
    self.assertEqual(again.deck, first.deck)
    self.assertEqual(again.left_extension_housing, first.left_extension_housing)


class TestFactories(unittest.IsolatedAsyncioTestCase):
  """Each factory builds one device, on the deck that device has."""

  async def test_each_factory_builds_its_own_deck(self):
    for factory, tracks in ((STAR, STAR_NUM_TRACKS), (STARlet, STARLET_NUM_TRACKS)):
      star = factory(simulation=True)
      await star.create_resources()
      assert star.deck is not None
      self.assertEqual((await star.deck.get_hamilton_tracks()).num_tracks, tracks)

  async def test_extension_housing_stands_to_the_left(self):
    """The housing is a resource beside the chassis, not something that grows the device.

    It bolts to the left, so it sits at a negative x. Growing the device instead would move its
    origin, and everything measured from that origin with it.
    """
    star = STAR(simulation=True)
    await star.create_resources()
    assert star.body is not None and star.deck is not None
    self.assertEqual((await star.body.attributes()).size.x, STAR_SIZE_X)
    self.assertEqual(cast(Coordinate, await star.deck.get_location()).x, STAR_DECK_LOCATION.x)

    housing = await star.body.get_resource(f"{star.name}_left_extension_housing")
    self.assertEqual(cast(Coordinate, await housing.get_location()).x, -EXTENSION_HOUSING_SIZE_X)
    self.assertEqual((await housing.get_absolute_size()).x, EXTENSION_HOUSING_SIZE_X)

  async def test_extension_housing_is_fitted_unless_declined(self):
    async def fitted(star: STARDevice) -> bool:
      await star.create_resources()
      assert star.body is not None
      names = [child.name for child in await star.body.get_children()]
      return f"{star.name}_left_extension_housing" in names

    self.assertTrue(await fitted(STAR(simulation=True)))
    self.assertFalse(await fitted(STAR(simulation=True, extension_housing=False)))

  async def test_default_names_and_left_side_accessors(self):
    star = STAR(simulation=True)
    await star.create_resources()
    assert star.body is not None
    self.assertEqual(star.name, "STAR")
    self.assertEqual(STARlet(simulation=True).name, "STARlet")
    self.assertEqual(STARPlus(simulation=True).name, "STARplus")
    self.assertEqual(
      star.left_extension_housing, await star.body.get_resource("STAR_left_extension_housing")
    )
    self.assertIsNone(star.left_side_panel)

    paneled = STAR(simulation=True, extension_housing=False, left_side_panel_installed=True)
    await paneled.create_resources()
    assert paneled.body is not None
    self.assertEqual(
      paneled.left_side_panel, await paneled.body.get_resource("STAR_left_side_panel")
    )
    self.assertIsNone(paneled.left_extension_housing)


class TestCapabilities(unittest.IsolatedAsyncioTestCase):
  """The device reads its features through the driver, which builds only what discovery
  found. A feature the device does not report is None rather than an object that cannot work."""

  async def test_reads_through_to_the_driver(self):
    star = STAR(simulation=True)
    await star.setup()
    for name in (
      "pipettes",
      "head96",
      "head384",
      "iswap",
      "autoload",
      "left_x_arm",
      "right_x_arm",
    ):
      self.assertIs(getattr(star, name), getattr(star.driver, name), name)

  async def test_absent_capabilities_are_none(self):
    # An arm that carries nothing: what the device reports at device level and what each
    # arm reports about itself agree on a real one, so the fixture makes them agree here.
    bare = dataclasses.replace(
      RECORDED_DEVICE,
      num_pip_channels=0,
      head96_installed=False,
      autoload_installed=False,
      left_arm=BARE_X_ARM,
      right_arm=None,
    )
    star = STARDevice(
      deck=await make_deck(),
      driver=STARSimulationDriver(declared_configuration_json=declaring(device=bare)),
    )
    await star.setup()
    for name in ("pipettes", "head96", "head384", "autoload", "right_x_arm", "front_cover"):
      self.assertIsNone(getattr(star, name), name)


async def _names_under(resource: handles.Resource) -> List[str]:
  """Every name under a resource, itself left out."""
  return [found.name for found in await resource.find_resources() if found != resource]


class TestComponentNames(unittest.IsolatedAsyncioTestCase):
  """Named devices can share a tree before and after discovery."""

  async def test_device_components_are_unique_and_reused(self):
    """Every built-in component, including nested head and iSWAP parts, belongs to its name."""
    server = ResourceServer.local()
    bench = await server.create(
      build.resource("bench", Coordinate(10000, 2000, 2000)), name="bench"
    )
    cases: Tuple[Tuple[Callable[..., STARDevice], str, Optional[str], bool], ...] = (
      (STAR, "star_a", None, False),
      (STAR, "star_b", RECORDING_STAR_HEAD384, False),
      (STARlet, "starlet", None, True),
      (STARPlus, "starplus", None, False),
    )
    for index, (factory, name, recording, side_panel) in enumerate(cases):
      with self.subTest(name=name):
        star = factory(
          name=name,
          simulation=True,
          declared_configuration_json=recording,
          extension_housing=not side_panel,
          left_side_panel_installed=side_panel,
          server=server,
        )
        await star.create_resources()
        assert star.deck is not None and star.body is not None
        self.assertEqual(star.deck.name, f"{name}_deck")
        self.assertTrue(all(n.startswith(f"{name}_") for n in await _names_under(star.body)))
        await bench.assign_child_resource(star.body, location=Coordinate(index * 2500, 0, 0))
        try:
          await star.setup()
          components = await _names_under(star.body)
          self.assertTrue(all(n.startswith(f"{name}_") for n in components))
          for component in components:
            found = await bench.get_resource(component)
            self.assertTrue(await found.is_in_subtree_of(star.body))
          assert star.pipettes is not None
          self.assertEqual(star.pipettes.resources[0].name, f"{name}_pipette_channel_0")
          if star.head96 is not None:
            self.assertEqual(
              star.head96.configuration.tip_discard_location,
              await star.head96._position_centred_in(
                await star.deck.get_resource(f"{name}_deck_trash_core96")
              ),
            )
          ids = [found.id for found in await star.body.find_resources()]
          await star.stop()
          await star.setup()
          self.assertEqual([found.id for found in await star.body.find_resources()], ids)
        finally:
          await star.stop()

  async def test_supplied_deck_and_labware_keep_their_names(self):
    """Discovery uses the device name without renaming caller-owned deck resources."""
    deck = await make_deck(name="custom_deck")
    labware = await deck.server.create(
      build.resource("user_labware", Coordinate(100, 100, 10)),
      name="user_labware",
      parent=deck,
      track=1,
    )
    existing_names = await _names_under(deck)
    star = STAR(name="star_a", deck=deck, simulation=True)
    try:
      await star.setup()
      assert star.body is not None
      self.assertEqual(star.deck, deck)
      self.assertEqual(await star.body.get_resource("user_labware"), labware)
      under = await _names_under(star.body)
      for name in existing_names:
        self.assertIn(name, under)
      assert star.x_arm.resource is not None
      self.assertEqual(star.x_arm.resource.name, "star_a_left_x_arm")
      self.assertIn("custom_deck_trash_core96", under)
    finally:
      await star.stop()


class TestTurnedDevice(unittest.IsolatedAsyncioTestCase):
  """A device turned in the room sets up as one standing square."""

  async def test_a_turned_device_puts_its_parts_where_an_upright_one_does(self):
    for factory in (STARlet, STARPlus):
      for angle in (90, -90, 37.5):
        with self.subTest(device=factory.__name__, angle=angle):
          placed = []
          for rotation in (0, angle):
            device = factory(simulation=True, name="device")
            room = await device.server.create(
              build.resource("room", Coordinate(9000, 9000, 3000), location=Coordinate.zero()),
              name="room",
            )
            await device.create_resources()
            assert device.body is not None
            await device.body.rotate(z=rotation)
            await room.assign_child_resource(device.body, location=Coordinate(4000, 4000, 0))
            await device.setup()
            response = await device.server.commands.get_resources(
              spb.GetResourcesRequest(resources=[device.body.ref], depth=-1)
            )
            placed.append(
              {
                node.attributes.name: (
                  node.attributes.location.x,
                  node.attributes.location.y,
                  node.attributes.location.z,
                  node.attributes.size.x,
                  node.attributes.size.y,
                  node.attributes.size.z,
                )
                for node in response.nodes[1:]
                if node.attributes.HasField("location")
              }
            )
            await device.stop()
          upright, turned = placed
          self.assertEqual(turned.keys(), upright.keys())
          for name, where in upright.items():
            for got, expected in zip(turned[name], where):
              self.assertAlmostEqual(got, expected, 3, name)
