import dataclasses
import datetime
import json
import pathlib
import random
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from unittest.mock import DEFAULT, AsyncMock, patch

from pylabrobot.hamilton.protocol.text.framing import assemble_command
from pylabrobot.hamilton.star.device import RECORDING_STAR, RECORDING_STARLET
from pylabrobot.hamilton.star.driver.configuration import read_configuration
from pylabrobot.hamilton.star.driver.errors import STARFirmwareError, check_fw_string_error
from pylabrobot.hamilton.star.driver.features.head96 import Head96, Head96Configuration
from pylabrobot.hamilton.star.driver.features.head384 import Head384, Head384Configuration
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.driver.lld_mode import LLDMode
from pylabrobot.hamilton.star.driver.simulator import STARSimulationDriver
from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles, library
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.serializer import serialize

# The 96-head on the device this package ships a recording of.
RECORDED_HEAD96 = cast(
  Head96Configuration, read_configuration(RECORDING_STAR)["arms"]["left"]["head96"]
)


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


async def make_deck(model: str = "STARLetDeck") -> handles.Deck:
  """A standalone deck of the model, named `test_deck`, in a store of its own."""
  store = ResourceStore.in_process()
  return cast(handles.Deck, await store.create(model, name="test_deck"))


async def make_driver(
  deck_model: str = "STARLetDeck", declared_configuration_json: str = RECORDING_STARLET
) -> Tuple[STARSimulationDriver, handles.Deck]:
  """A simulated device on a deck of its own, not set up."""
  deck = await make_deck(deck_model)
  return (
    STARSimulationDriver(deck=deck, declared_configuration_json=declared_configuration_json),
    deck,
  )


async def make(store: ResourceStore, model: str, name: str, parent: handles.Resource, **kw: Any):
  """A resource of a model, in `parent`."""
  return await store.create(model, name=name, parent=parent, **kw)


async def frameless_rack(
  store: ResourceStore, name: str, parent: Optional[handles.Resource] = None
) -> handles.TipRack:
  """A raised CO-RE II rack of 300 uL filter tips: a rack with no frame, full."""
  tip = pb.ResourceAttributes()
  tip.CopyFrom(library.get_model("hamilton_tip_300uL_filter").definition.attributes)
  spot = build.resource(
    "{name}_tipspot_{identifier}",
    Coordinate(7.2, 7.2, 0),
    kind=pb.RESOURCE_KIND_TIP_SPOT,
    category="tip_spot",
    tip_spot=pb.TipSpotSpec(prototype_tip=tip),
    state=pb.ResourceState(tip_tracking_enabled=True),
  )
  definition = build.resource(
    name,
    Coordinate(122.0, 78.5, 25.5),
    kind=pb.RESOURCE_KIND_TIP_RACK,
    category="tip_rack",
    model="hamilton_96_tiprack_raised_core_ii",
    tip_rack=pb.TipRackSpec(style=pb.TIP_RACK_STYLE_EMBEDDED, frame_height=0.0, sinking_depth=9.5),
    itemized=pb.ItemizedSpec(
      num_items_x=12,
      num_items_y=8,
      grid=pb.ItemGrid(
        item=spot, offset=build.vec3(Coordinate(7.9, 4.15, 25.5)), item_dx=9.0, item_dy=9.0
      ),
    ),
  )
  rack = cast(handles.TipRack, await store.create(definition, name=name, parent=parent))
  await rack.fill()
  return rack


async def tips_on(head: Head96) -> List[Optional[str]]:
  """The name of the tip on each channel of the head, None where there is none."""
  return [
    None if tool is None else tool.attributes.name for tool in (await head._get_tools()).values()
  ]


async def tips_in(rack: handles.TipRack) -> List[Optional[str]]:
  """The name of the tip in each spot of the rack, None where there is none."""
  response = await rack.store.commands.get_resources(
    spb.GetResourcesRequest(resources=[rack.ref], depth=2)
  )
  held = {
    node.parent_id: node.attributes.name
    for node in response.nodes
    if node.attributes.kind == pb.RESOURCE_KIND_TIP
  }
  return [held.get(spot.id) for spot in rack.items]


async def volumes_of(containers: List[handles.Container]) -> Set[float]:
  return {await container.get_volume() for container in containers}


class TestDriveDefaults(unittest.IsolatedAsyncioTestCase):
  """Where the value a move uses when the caller names none comes from: what the head reported,
  falling back to what its firmware documents."""

  async def test_the_defaults_are_what_the_head_reported(self):
    """Discovery reads the four Y and Z drive parameters off the head, and the defaults answer with
    them. Read from a head declaring values its firmware does not, so a default that ignored the
    head and computed the documented one instead could not pass. Four distinct values, so a read
    stored under the wrong name fails this too."""
    declared = dataclasses.replace(
      RECORDED_HEAD96,
      y_drive_speed_firmware_reported=200.0,
      y_drive_acceleration_firmware_reported=300.0,
      z_drive_speed_firmware_reported=50.0,
      z_drive_acceleration_firmware_reported=250.0,
    )
    driver, _ = await make_driver("STARDeck", declaring(head96=declared))
    await driver.setup()

    c = cast(Head96, driver.x_arm.head96).configuration
    self.assertEqual(
      (
        c.y_drive_speed_default,
        c.y_drive_acceleration_default,
        c.z_drive_speed_default,
        c.z_drive_acceleration_default,
      ),
      (200.0, 300.0, 50.0, 250.0),
    )

  async def test_the_96_head_takes_its_squeezer_defaults_too(self):
    """`Head96.discover` reads two drive parameters on top of the Y and Z ones every head shares,
    and its defaults answer with what it reported for them. Apart from the test above because it
    covers the override rather than the base: the 384-head adds no reads of its own.

    Compared to a tenth rather than exactly: the drive counts in increments, so a value that does
    not fall on one comes back as the nearest that does - 400.0 mm/s reads back as 400.01. That is
    what a head does, and what the simulated one does now that its answer crosses the link and is
    decoded rather than handed over whole."""
    declared = dataclasses.replace(
      RECORDED_HEAD96,
      squeezer_drive_speed_firmware_reported=12.0,
      squeezer_drive_acceleration_firmware_reported=50.0,
    )
    driver, _ = await make_driver("STARDeck", declaring(head96=declared))
    await driver.setup()

    c = cast(Head96, driver.x_arm.head96).configuration
    for read, declared_value in zip(
      (
        c.squeezer_drive_speed_default,
        c.squeezer_drive_acceleration_default,
      ),
      (12.0, 50.0),
    ):
      self.assertAlmostEqual(read, declared_value, places=1)

  async def test_a_head_with_firmware_from_before_2010_gets_its_lower_dispensing_acceleration(self):
    declared = dataclasses.replace(RECORDED_HEAD96, firmware_version="1.0S 2008-11-11 (H0)")
    driver, _ = await make_driver("STARDeck", declaring(head96=declared))
    await driver.setup()
    head = cast(Head96, driver.x_arm.head96)
    self.assertEqual(head.default_dispensing_drive_acceleration, 2900.0)

  async def test_a_default_outside_the_range_of_its_drive_is_refused_when_assigned(self):
    driver, _ = await make_driver("STARDeck", RECORDING_STAR)
    await driver.setup()
    head = cast(Head96, driver.x_arm.head96)
    with self.assertRaisesRegex(ValueError, "default_dispensing_drive_speed must be between"):
      head.default_dispensing_drive_speed = 5000.0
    with self.assertRaisesRegex(ValueError, "default_dispensing_drive_acceleration must be"):
      head.default_dispensing_drive_acceleration = 50.0
    self.assertEqual(
      (head.default_dispensing_drive_speed, head.default_dispensing_drive_acceleration),
      (250.0, 17000.0),
    )
    head.default_dispensing_drive_speed = 200.0
    self.assertEqual(head.default_dispensing_drive_speed, 200.0)

  async def test_a_head_that_will_not_say_keeps_what_its_firmware_documents(self):
    """A head that refuses the read leaves discovery with nothing to record, and the defaults fall
    back to the increments its firmware documents rather than the read failing setup. Driven
    through `discover` alone: the rest of setup moves the head, and reads these same parameters to
    do it."""
    driver, _ = await make_driver("STARDeck", RECORDING_STAR)
    head = cast(Head96, cast(XArm, driver.left_x_arm).head96)

    async def refuse(parameter: str) -> float:
      raise RuntimeError("this head does not answer for its drives")

    head.request_drive_parameter = refuse  # type: ignore[method-assign]
    await head.discover()

    c = head.configuration
    self.assertEqual(
      (
        c.y_drive_speed_firmware_reported,
        c.y_drive_acceleration_firmware_reported,
        c.z_drive_speed_firmware_reported,
        c.z_drive_acceleration_firmware_reported,
      ),
      (None, None, None, None),
    )
    self.assertEqual(
      (
        c.y_drive_speed_default,
        c.y_drive_acceleration_default,
        c.z_drive_speed_default,
        c.z_drive_acceleration_default,
      ),
      (390.62, 546.88, 85.0, 400.0),
    )


class TestHead96Tips(unittest.IsolatedAsyncioTestCase):
  """As legacy's 96-head tip tests, on the layout they use: a 300 uL filter rack on a STARlet."""

  async def asyncSetUp(self):
    self.driver, self.deck = await make_driver()
    self.store = self.deck.store
    await self.driver.setup()
    self.head = cast(Head96, self.driver.head96)
    self.tip_car = tip_car = cast(
      handles.Carrier,
      await make(self.store, "hamilton_tip_carrier_L5", "tip carrier", self.deck, track=1),
    )
    self.tip_rack = cast(
      handles.TipRack,
      await make(self.store, "hamilton_96_tiprack_300uL_filter", "tip_rack_01", tip_car[1]),
    )
    # A rack without a frame, which the head may be placed past the edge of.
    self.frameless_tip_rack = await frameless_rack(self.store, "frameless_tip_rack", tip_car[3])
    self.trash = await self.deck.get_resource("test_deck_trash_core96")
    self.sent: List[str] = []
    log = self.driver._log_exchange

    def recorded(written: str, read: Optional[str]) -> None:
      if written[:4] in ("C0TT", "H0DQ", "C0EP", "C0ER"):
        self.sent.append(written)
      log(written, read)

    self.driver._log_exchange = recorded  # type: ignore[method-assign]

  async def lid(self, rack: handles.TipRack) -> handles.Resource:
    lid = build.resource(
      "lid",
      Coordinate(127.0, 86.0, 10.0),
      kind=pb.RESOURCE_KIND_LID,
      lid=pb.LidSpec(nesting_z_height=2.0),
    )
    return await self.store.create(lid, name="lid", parent=rack)

  async def test_discarding_with_no_96_trash_names_the_trash_it_looked_for(self):
    await self.head.pick_up_tips(self.tip_rack)
    await self.trash.delete()
    with self.assertRaisesRegex(
      RuntimeError, "no resource named 'test_deck_trash_core96'"
    ) as caught:
      await self.head.discard_tips()
    self.assertNotIn("with_trash96", str(caught.exception))

  async def test_a_covered_rack_is_not_picked_up_from_nor_dropped_into(self):
    lid = await self.lid(self.tip_rack)
    with self.assertRaisesRegex(ValueError, "pick up tips from 'tip_rack_01': it is not available"):
      await self.head.pick_up_tips(self.tip_rack)
    self.assertEqual(self.sent, [])

    await lid.delete()
    await self.head.pick_up_tips(self.tip_rack)
    await self.lid(self.tip_rack)
    self.sent.clear()
    with self.assertRaisesRegex(ValueError, "drop tips into 'tip_rack_01': it is not available"):
      await self.head.drop_tips(self.tip_rack)
    self.assertEqual(self.sent, [])

  async def test_pick_up_and_drop_send_what_legacy_sends(self):
    await self.head.pick_up_tips(self.tip_rack)
    await self.head.drop_tips(self.tip_rack)
    await self.head.pick_up_tips(self.tip_rack)
    await self.head.drop_tips(self.trash)
    self.assertEqual(
      self.sent,
      [
        "C0TTtt01tf1tl0519tv03600tg2tu0",
        "H0DQdq11281dv12926du00000dr878965dw15",
        "C0EPxs01179xd0yh2418tt01wu0za2164zh2450ze2450",
        "C0ERxs01179xd0yh2418za2164zh2450ze2450",
        "H0DQdq11281dv12926du00000dr878965dw15",
        "C0EPxs01179xd0yh2418tt01wu0za2164zh2450ze2450",
        # The trash drop centres the array; legacy put A1 4.5 mm right and 58.5 mm forward of this.
        "C0ERxs00465xd1yh1788za2164zh2450ze2450",
      ],
    )

  async def test_a_pickup_with_tips_on_refuses_before_anything_moves(self):
    await self.head.pick_up_tips(self.tip_rack)
    self.sent.clear()
    with self.assertRaises(RuntimeError):
      await self.head.pick_up_tips(self.tip_rack)
    self.assertEqual(self.sent, [])

  async def test_tips_missing_from_a_rack_are_missing_from_the_head(self):
    rng = random.Random(0)
    for missing in (0, 1, 48, 95):
      with self.subTest(missing=missing):
        empty = set(rng.sample(range(96), missing))
        await self.tip_rack.set_tip_state([i not in empty for i in range(96)])
        tips = await tips_in(self.tip_rack)

        await self.head.pick_up_tips(self.tip_rack)
        self.assertEqual(await tips_on(self.head), tips)
        self.assertEqual(await tips_in(self.tip_rack), [None] * 96)

        await self.head.drop_tips(self.tip_rack)
        self.assertEqual(await tips_in(self.tip_rack), tips)
        self.assertEqual(await tips_on(self.head), [None] * 96)
        await self.tip_rack.fill()

  async def test_tip_commands_travel_in_z_then_in_x_and_y_together_then_only_descend(self):
    every: List[str] = []
    log = self.driver._log_exchange

    def recorded(written: str, read: Optional[str]) -> None:
      every.append(written[:4])
      log(written, read)

    self.driver._log_exchange = recorded  # type: ignore[method-assign]
    for command, tip_command in (
      (self.head.pick_up_tips, "C0EP"),
      (self.head.drop_tips, "C0ER"),
    ):
      every.clear()
      await command(self.frameless_tip_rack)
      # The arm's channels up, then X and Y; the tip command comes after them all.
      order = [every.index(c) for c in ("C0ZA", "X0XP", "H0YA", tip_command)]
      self.assertEqual(order, sorted(order), every)
      # The head is raised, if at all, before X and Y move.
      if "H0ZA" in every:
        self.assertLess(every.index("H0ZA"), every.index("X0XP"), every)
      self.assertNotIn("X0XP", every[every.index(tip_command) :])

  async def test_an_offset_moves_the_head_but_not_which_spot_each_channel_takes_from(self):
    rack = self.frameless_tip_rack
    tips = await tips_in(rack)

    # A correction of a few mm: the head goes 2 mm right, each channel still takes its own spot.
    await self.head.pick_up_tips(rack, offset=Coordinate(2, 0, 0))

    self.assertEqual(await tips_on(self.head), tips)
    plain = await rack.get_item("A1").get_location_wrt(self.deck, "c", "c", "b")
    self.assertIn(f"xs{round((plain.x + 2) * 10):05}", self.sent[-1])

  async def test_a_channel_placed_over_a_spot_takes_only_the_tips_under_the_head(self):
    # Channel H12 over spot D6: channels E7 to H12 stand over spots A1 to D6, the rest past the rack.
    rack = self.frameless_tip_rack
    await rack.set_tip_state([identifier != "A2" for identifier in rack.identifiers])
    in_rack = dict(zip(rack.identifiers, await tips_in(rack)))
    under = {
      f"{'EFGH'[row]}{column + 7}": f"{'ABCD'[row]}{column + 1}"
      for row in range(4)
      for column in range(6)
    }

    await self.head.pick_up_tips(rack, channel="H12", tip_spot="D6")

    # Channel A1 ends 6 columns left and 4 rows behind spot A1 (xs01179 yh4338): -54 mm X, +36 mm Y.
    self.assertEqual(self.sent[-1], "C0EPxs00639xd0yh4698tt01wu0za2310zh2450ze2450")
    for channel, tip in zip(self.head.shafts, await tips_on(self.head)):
      spot = under.get(channel)
      self.assertEqual(tip, None if spot is None else in_rack[spot], channel)

  async def test_tips_dropped_in_the_trash_belong_to_nothing(self):
    await self.head.pick_up_tips(self.tip_rack)
    tips = [tip for tip in await tips_on(self.head) if tip is not None]
    await self.head.drop_tips(self.trash)
    self.assertEqual(await tips_on(self.head), [None] * 96)
    self.assertEqual(await tips_in(self.tip_rack), [None] * 96)
    self.assertFalse(await self.store.find_resources(spb.ResourceFilter(names=tips)))

  def failing_on(self, failed: str):
    answer = self.driver._answer

    async def answering(module: str, command: str, **kwargs: Any):
      if command == failed:
        check_fw_string_error(f"C0{failed}id0001er99/00")
      return await answer(module, command, **kwargs)

    return patch.object(self.driver, "_answer", answering)

  async def test_a_failed_pickup_takes_what_the_firmware_holds_and_reads_where_it_stopped(self):
    # The guard and the travel read no tips; after the failure the firmware holds that they are on.
    held = AsyncMock(side_effect=[False, False, True])
    read_z = AsyncMock(wraps=self.head.request_z_position)
    with self.failing_on("EP"), patch.object(self.head, "request_tip_presence", held):
      with patch.object(self.head, "request_z_position", read_z):
        with self.assertRaises(STARFirmwareError):
          await self.head.pick_up_tips(self.tip_rack)
    self.assertNotIn(None, await tips_on(self.head))
    self.assertEqual(await tips_in(self.tip_rack), [None] * 96)
    read_z.assert_awaited()

  async def test_a_failed_drop_takes_what_the_firmware_holds(self):
    await self.head.pick_up_tips(self.tip_rack)
    held = AsyncMock(return_value=False)
    with self.failing_on("ER"), patch.object(self.head, "request_tip_presence", held):
      with self.assertRaises(STARFirmwareError):
        await self.head.drop_tips(self.tip_rack)
    self.assertEqual(await tips_on(self.head), [None] * 96)
    self.assertNotIn(None, await tips_in(self.tip_rack))

  async def test_the_piston_is_read_after_a_pickup_and_a_drop(self):
    commands: List[str] = []
    log = self.driver._log_exchange

    def every(written: str, read: Optional[str]) -> None:
      commands.append(written[:4])
      log(written, read)

    self.driver._log_exchange = every  # type: ignore[method-assign]
    await self.head.pick_up_tips(self.tip_rack)
    await self.head.drop_tips(self.tip_rack)
    for command in ("C0EP", "C0ER"):
      self.assertIn("H0RD", commands[commands.index(command) :])
    self.assertEqual(commands[-1], "H0RD")

  async def test_return_tips_drops_them_in_the_rack_they_came_from(self):
    """Spots left empty before the pickup stay empty after the return."""
    await self.tip_rack.set_tip_state([i not in (0, 47) for i in range(96)])
    tips = await tips_in(self.tip_rack)
    await self.head.pick_up_tips(self.tip_rack)
    self.sent.clear()
    await self.head.return_tips()
    self.assertEqual(self.sent, ["C0ERxs01179xd0yh2418za2164zh2450ze2450"])
    self.assertEqual(await tips_in(self.tip_rack), tips)
    self.assertEqual(await tips_on(self.head), [None] * 96)

  async def test_a_drop_that_would_let_a_tip_go_beside_the_rack_is_refused(self):
    await self.head.pick_up_tips(self.tip_rack)
    self.sent.clear()
    with self.assertRaisesRegex(ValueError, "would drop a tip beside frameless_tip_rack"):
      await self.head.drop_tips(self.frameless_tip_rack, channel="A1", tip_spot="A10")
    self.assertEqual(self.sent, [])

  async def test_a_drop_that_would_put_a_tip_on_a_tip_is_refused_before_anything_moves(self):
    rack = self.frameless_tip_rack
    await self.head.pick_up_tips(rack, channel="H12", tip_spot="A1")  # one tip, on H12
    self.sent.clear()
    # Spot B1 still holds its tip.
    with self.assertRaisesRegex(ValueError, r"channels \['H12'\] would put a tip on a tip"):
      await self.head.drop_tips(rack, channel="H12", tip_spot="B1")
    self.assertEqual(self.sent, [])
    self.assertIsNotNone((await tips_on(self.head))[95])

  async def test_a_rack_turned_half_round_is_picked_up_whole_with_h12_over_a1(self):
    rack = await frameless_rack(self.store, "turned_rack")
    await rack.rotate(z=180)
    await self.tip_car[4].assign_child_resource(rack)
    by_tip = dict(zip(await tips_in(rack), rack.items))

    await self.head.pick_up_tips(rack, channel="H12", tip_spot="A1")

    for (channel, shaft), tip in zip(self.head.shafts.items(), await tips_on(self.head)):
      # Each tip came from the spot right under its channel.
      spot = by_tip[tip]
      here = await shaft.get_location_wrt(self.deck, "c", "c", "b")
      there = await spot.get_location_wrt(self.deck, "c", "c", "b")
      self.assertAlmostEqual(here.x, there.x, places=1, msg=channel)
      self.assertAlmostEqual(here.y, there.y, places=1, msg=channel)
    self.assertEqual(await tips_in(rack), [None] * 96)

  async def test_with_tip_tracking_off_a_pick_up_leaves_the_rack_and_a_drop_into_it_is_refused(
    self,
  ):
    rack = self.frameless_tip_rack
    await rack.set_tip_tracking(False)
    await self.head.pick_up_tips(rack)
    self.assertNotIn(None, await tips_on(self.head))
    self.assertNotIn(None, await tips_in(rack))
    self.sent.clear()
    with self.assertRaisesRegex(ValueError, "dropping into a tip rack needs tip tracking"):
      await self.head.drop_tips(rack)
    with self.assertRaisesRegex(ValueError, "needs tip tracking"):
      await self.head.return_tips()
    self.assertEqual(self.sent, [])
    await self.head.discard_tips()
    self.assertEqual(await tips_on(self.head), [None] * 96)

  async def test_with_tip_tracking_off_a_rack_modelled_empty_still_hands_out_tips(self):
    rack = self.frameless_tip_rack
    await rack.empty()
    await rack.set_tip_tracking(False)
    await self.head.pick_up_tips(rack)
    self.assertNotIn(None, await tips_on(self.head))

  async def test_a_rack_with_a_frame_takes_the_head_only_channel_a1_over_spot_a1(self):
    with self.assertRaisesRegex(ValueError, "come down on the frame of tip_rack_01"):
      await self.head.pick_up_tips(self.tip_rack, channel="H12", tip_spot="D6")
    self.assertEqual(self.sent, [])
    await self.head.pick_up_tips(self.frameless_tip_rack, channel="H12", tip_spot="D6")
    self.sent.clear()
    with self.assertRaisesRegex(ValueError, "come down on the frame of tip_rack_01"):
      await self.head.drop_tips(self.tip_rack, channel="H12", tip_spot="D6")
    self.assertEqual(self.sent, [])

  async def test_return_tips_puts_them_back_under_the_channels_that_took_them(self):
    rack = self.frameless_tip_rack
    await rack.set_tip_state([identifier != "A2" for identifier in rack.identifiers])
    tips = await tips_in(rack)
    await self.head.pick_up_tips(rack, channel="H12", tip_spot="D6")
    self.sent.clear()
    await self.head.return_tips()
    self.assertEqual(self.sent, ["C0ERxs00639xd0yh4698za2310zh2450ze2450"])
    self.assertEqual(await tips_in(rack), tips)

  async def test_discard_tips_drops_them_in_the_96_trash(self):
    await self.head.pick_up_tips(self.tip_rack)
    self.sent.clear()
    await self.head.discard_tips()
    self.assertEqual(self.sent, ["C0ERxs00465xd1yh1788za2164zh2450ze2450"])
    self.assertEqual(await tips_on(self.head), [None] * 96)

  async def test_with_no_tips_return_refuses_before_anything_is_sent(self):
    with self.assertRaises(RuntimeError):
      await self.head.return_tips()
    self.assertEqual(self.sent, [])

  async def test_return_tips_refuses_tips_from_two_racks(self):
    other_rack = cast(
      handles.TipRack,
      await make(self.store, "hamilton_96_tiprack_300uL_filter", "tip_rack_02", self.tip_car[2]),
    )
    await self.head.pick_up_tips(self.tip_rack)
    # Channel F1 lets its tip go and takes the one in the other rack's spot F1 instead.
    shaft = self.head.shafts["F1"]
    commands = self.store.commands
    dropped = await commands.begin_tool_drop(
      spb.BeginToolDropRequest(
        frame=self.deck.ref, items=[spb.ToolDropItem(shaft=shaft.ref, target=self.trash.ref)]
      )
    )
    picked = await commands.begin_tool_pickup(
      spb.BeginToolPickupRequest(
        frame=self.deck.ref,
        items=[spb.ToolPickupItem(source=other_rack.get_item("F1").ref, shaft=shaft.ref)],
      )
    )
    for operation in (dropped.operation, picked.operation):
      await commands.resolve_operation(
        spb.ResolveOperationRequest(
          operation_id=operation.id, outcomes=[spb.ItemOutcome(item=0, succeeded=True)]
        )
      )
    self.sent.clear()
    with self.assertRaisesRegex(RuntimeError, "did not stand under it in tip_rack_01"):
      await self.head.return_tips()
    self.assertEqual(self.sent, [])

  async def test_a_refused_pickup_moves_nothing(self):
    """An empty rack is refused before anything is sent; an unreachable one after the tip type."""
    with self.assertRaises(ValueError):
      await self.head.pick_up_tips(self.tip_rack, offset=Coordinate(0, 1000, 0))
    self.assertEqual(self.sent, ["C0TTtt01tf1tl0519tv03600tg2tu0"])
    await self.tip_rack.empty()
    self.sent.clear()
    with self.assertRaises(ValueError):
      await self.head.pick_up_tips(self.tip_rack)
    self.assertEqual(self.sent, [])

  async def test_a_failed_command_leaves_the_tips_where_they_were(self):
    answer = self.driver._answer

    def failing(failed: str):
      async def answering(module: str, command: str, **kwargs: Any):
        if command == failed:
          check_fw_string_error(f"{module}{failed}id0001er99/00")
        return await answer(module, command, **kwargs)

      return answering

    with patch.object(self.driver, "_answer", failing("EP")):
      with self.assertRaises(STARFirmwareError):
        await self.head.pick_up_tips(self.tip_rack)
    self.assertNotIn(None, await tips_in(self.tip_rack))
    self.assertEqual(await tips_on(self.head), [None] * 96)

    # The head's Y move on the way over fails: nothing is picked up, and the command never goes.
    self.sent.clear()
    with patch.object(self.driver, "_answer", failing("YA")):
      with self.assertRaises(STARFirmwareError):
        await self.head.pick_up_tips(self.tip_rack)
    self.assertNotIn("C0EP", [written[:4] for written in self.sent])
    self.assertNotIn(None, await tips_in(self.tip_rack))
    self.assertEqual(await tips_on(self.head), [None] * 96)

    await self.head.pick_up_tips(self.tip_rack)
    with patch.object(self.driver, "_answer", failing("ER")):
      with self.assertRaises(STARFirmwareError):
        await self.head.drop_tips(self.tip_rack)
    self.assertNotIn(None, await tips_on(self.head))
    self.assertEqual(await tips_in(self.tip_rack), [None] * 96)

    self.sent.clear()
    with patch.object(self.driver, "_answer", failing("YA")):
      with self.assertRaises(STARFirmwareError):
        await self.head.drop_tips(self.tip_rack)
    self.assertNotIn("C0ER", [written[:4] for written in self.sent])
    self.assertNotIn(None, await tips_on(self.head))
    self.assertEqual(await tips_in(self.tip_rack), [None] * 96)


async def _head_with_tips(
  plate: bool = True, trough: bool = False
) -> Tuple[STARSimulationDriver, handles.Deck, Head96, Dict[str, handles.Plate]]:
  """A STARlet whose 96-head carries 300 uL filter tips, with a plate and a trough on track 7."""
  driver, deck = await make_driver()
  store = deck.store
  await driver.setup()
  head = cast(Head96, driver.head96)
  tip_car = cast(
    handles.Carrier, await make(store, "hamilton_tip_carrier_L5", "tip carrier", deck, track=1)
  )
  tip_rack = cast(
    handles.TipRack,
    await make(store, "hamilton_96_tiprack_300uL_filter", "tip_rack_01", tip_car[1]),
  )
  plate_car = cast(
    handles.Carrier,
    await make(store, "hamilton_plate_carrier_L5_ac", "plate carrier", deck, track=7),
  )
  plates: Dict[str, handles.Plate] = {}
  if plate:
    plates["plate"] = cast(
      handles.Plate, await make(store, "cor_96_wellplate_360uL_Fb", "plate", plate_car[1])
    )
  if trough:
    plates["trough"] = cast(
      handles.Plate, await make(store, "agenbio_1_troughplate_190mL_Fl", "trough", plate_car[3])
    )
  await head.pick_up_tips(tip_rack)
  return driver, deck, head, plates


class TestProbeZUsingCLLD(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.driver, self.deck, self.head, _ = await _head_with_tips(plate=False)

    self.sent: List[str] = []
    answer = self.driver.send_command

    async def recorded(module: str, command: str, fmt: Optional[Any] = None, **kwargs: Any):
      if module + command == "H0ZL":
        self.sent.append(assemble_command(module, command, **kwargs))
        return ""
      if module + command == "H0RH":
        return {"rh": 40000}
      return await answer(module=module, command=command, fmt=fmt, **kwargs)

    self.driver.send_command = recorded  # type: ignore[assignment]

  async def test_the_search_is_sent_in_stop_disc_increments(self):
    detected = await self.head.probe_z_using_clld(tip_overhang=50.0)
    self.assertEqual(
      self.sent,
      ["H0ZLzh36100zc67200zi0400zj1lm2gt0010gl0002zv17000zl02000zr060000zw15"],
    )
    self.assertEqual(detected, 150.0)

  async def test_a_2008_head_refuses_a_sensor(self):
    self.head.configuration.firmware_date = datetime.date(2008, 11, 11)
    with self.assertRaises(ValueError):
      await self.head.probe_z_using_clld(tip_overhang=50.0, lld_sensor="A1 or B2")
    self.assertEqual(self.sent, [])


class TestMix(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.driver, self.deck, self.head, plates = await _head_with_tips()
    self.plate = plates["plate"]

    self.sent: List[str] = []
    answer = self.driver.send_command

    async def recorded(module: str, command: str, fmt: Optional[Any] = None, **kwargs: Any):
      if module + command in ("H0PA", "H0PB"):
        self.sent.append(assemble_command(module, command, **kwargs))
        return ""
      return await answer(module=module, command=command, fmt=fmt, **kwargs)

    self.driver.send_command = recorded  # type: ignore[assignment]

  async def test_the_strokes_are_sent_as_legacy_sends_them(self):
    await self.head.mix(self.plate, Mix(volume=100.0, repetitions=2, flow_rate=200.0))
    head = "pmFFFFFFFFFFFFFFFFFFFFFFFF"
    self.assertEqual(
      self.sent,
      [
        f"H0PA{head}dj1da00259dv10341dc00000zd0000zh47710to000",
        f"H0PA{head}dj1da05170dv10341dc00000zd0000zh47730to000",
        f"H0PB{head}db05170dv10341dd0000ze0000zh47730du00000",
        f"H0PA{head}dj1da05170dv10341dc00000zd0000zh47730to000",
        f"H0PB{head}db05170dv10341dd0000ze0000zh47730du00000",
        f"H0PB{head}db00259dv10341dd0000ze0000zh36100du00000",
      ],
    )

  async def test_each_stroke_follows_what_one_draw_takes_from_the_well(self):
    await self.plate.set_well_volumes(300.0)
    await self.head.mix(
      self.plate, Mix(volume=100.0, repetitions=1, flow_rate=200.0, auto_surface_following=True)
    )
    well = self.plate.get_well("A1")
    drop = round(
      await well.compute_height_from_volume(300.0) - await well.compute_height_from_volume(200.0),
      1,
    )
    following = self.head.configuration.z_drive_mm_to_increments(drop)
    self.assertIn(f"zd{following:04}", self.sent[1])
    self.assertIn(f"ze{following:04}", self.sent[2])

  async def test_auto_surface_following_needs_a_surface(self):
    with self.assertRaises(ValueError):
      Mix(
        volume=100.0,
        repetitions=1,
        flow_rate=200.0,
        surface_following_distance=1.0,
        auto_surface_following=True,
      )
    auto = Mix(volume=100.0, repetitions=1, flow_rate=200.0, auto_surface_following=True)
    with self.assertRaises(ValueError):
      await self.head.mix(self.plate, auto, lld_mode=LLDMode.OFF)
    self.assertEqual(self.sent, [])

  async def test_a_failed_stroke_raises_the_head(self):
    answer = self.driver.send_command

    async def failing(module: str, command: str, fmt: Optional[Any] = None, **kwargs: Any):
      if module + command == "H0PB":
        check_fw_string_error("H0PBid0001er99/00")
      return await answer(module, command, fmt=fmt, **kwargs)

    self.driver.send_command = failing  # type: ignore[assignment]
    with self.assertRaises(STARFirmwareError):
      await self.head.mix(self.plate, Mix(volume=100.0, repetitions=1, flow_rate=200.0))
    self.assertEqual(await self.head.request_z_position(), self.head.configuration.z_range[1])

  async def test_a_one_well_plate_gets_the_array_centred_over_it(self):
    store = self.deck.store
    carrier = cast(
      handles.Carrier,
      await make(store, "hamilton_plate_carrier_L5_ac", "trough carrier", self.deck, track=13),
    )
    trough_plate = cast(
      handles.Plate, await make(store, "agenbio_1_troughplate_190mL_Fl", "trough", carrier[0])
    )
    trough = trough_plate.get_well(0)
    centre = await trough.get_location_wrt(self.deck, "c", "c", "b")
    await self.head.mix(trough_plate, Mix(volume=100.0, repetitions=1, flow_rate=200.0))
    c = self.head.configuration
    self.assertAlmostEqual(
      await self.head.request_x_position(), centre.x - c.channel_array_size_x / 2, delta=0.1
    )
    self.assertAlmostEqual(
      await self.head.request_y_position(), centre.y + c.channel_array_size_y / 2, delta=0.1
    )

  async def _record_lld(
    self, rh: Optional[int] = None, zl_error: Optional[str] = None
  ) -> List[str]:
    """Answer H0 ZL and RH as given, and record every PA, PB, ZL, RH and head ZA, in order."""
    answer = self.driver.send_command
    order: List[str] = []

    async def lld(module: str, command: str, fmt: Optional[Any] = None, **kwargs: Any):
      if module == "H0" and command in ("ZL", "RH", "PA", "PB", "ZA"):
        wire = {key: value for key, value in kwargs.items() if len(key) == 2}
        order.append(assemble_command(module, command, **wire))
      if module + command == "H0ZL":
        if zl_error is not None:
          check_fw_string_error(zl_error)
        return ""
      if module + command == "H0RH":
        return {"rh": rh}
      if module + command in ("H0PA", "H0PB"):
        return ""
      return await answer(module, command, fmt=fmt, **kwargs)

    self.driver.send_command = lld  # type: ignore[assignment]
    return order

  async def test_under_clld_the_air_goes_in_first_and_the_head_rises_once(self):
    well = self.plate.get_well("A1")
    bottom = (await well.get_location_wrt(self.deck, "c", "c", "cavity_bottom")).z
    overhang = await self.head.request_tip_overhang()
    c = self.head.configuration
    order = await self._record_lld(rh=c.z_drive_mm_to_increments(bottom + 5.0 + overhang))
    await self.head.mix(
      self.plate,
      Mix(volume=50.0, repetitions=2, flow_rate=100.0),
      lld_mode=LLDMode.CAPACITIVE,
    )
    self.assertEqual(
      [command[2:4] for command in order if command[2:4] != "ZA"],
      ["PA", "ZL", "RH", "PA", "PB", "PA", "PB", "PB"],
    )
    zl = next(command for command in order if command.startswith("H0ZL"))
    self.assertIn(f"zh{c.z_drive_mm_to_increments(bottom + overhang):05}", zl)
    self.assertIn("zi0000", zl)
    # Down from the surface to 2 mm under it, then the strokes; the rise comes before the air out.
    moves = [command for command in order if command.startswith("H0ZA")]
    self.assertIn(f"za{c.z_drive_mm_to_increments(bottom + 3.0 + overhang):05}", moves[-2])
    self.assertTrue(order.index(moves[-1]) < len(order) - 1 and order[-1].startswith("H0PB"))
    self.assertAlmostEqual(await well.get_volume(), await well.compute_volume_from_height(5.0))

  async def test_under_clld_no_liquid_raises_and_the_head_goes_up(self):
    await self._record_lld(zl_error="H0ZLid0001er70")
    with self.assertRaises(RuntimeError):
      await self.head.mix(
        self.plate,
        Mix(volume=50.0, repetitions=1, flow_rate=100.0),
        lld_mode=LLDMode.CAPACITIVE,
      )
    self.assertEqual(await self.head.request_z_position(), self.head.configuration.z_range[1])

  async def test_probe_liquid_height_averages_the_rounds_from_the_cavity_bottom(self):
    well = self.plate.get_well("A1")
    bottom = (await well.get_location_wrt(self.deck, "c", "c", "cavity_bottom")).z
    overhang = await self.head.request_tip_overhang()
    c = self.head.configuration
    order = await self._record_lld(rh=c.z_drive_mm_to_increments(bottom + 4.0 + overhang))
    height = await self.head.probe_liquid_height(self.plate, n_replicates=2)
    self.assertAlmostEqual(height, 4.0, delta=0.01)
    self.assertEqual(
      [command[2:4] for command in order if command[2:4] in ("ZL", "RH")], ["ZL", "RH"] * 2
    )
    self.assertEqual(await self.head.request_z_position(), c.z_range[1])

  async def test_probe_liquid_height_is_zero_where_nothing_is_met(self):
    await self._record_lld(zl_error="H0ZLid0001er70")
    self.assertEqual(await self.head.probe_liquid_height(self.plate), 0.0)

  async def test_probe_liquid_volume_is_the_volume_at_the_height(self):
    well = self.plate.get_well("A1")
    bottom = (await well.get_location_wrt(self.deck, "c", "c", "cavity_bottom")).z
    overhang = await self.head.request_tip_overhang()
    c = self.head.configuration
    await self._record_lld(rh=c.z_drive_mm_to_increments(bottom + 4.0 + overhang))
    volume = await self.head.probe_liquid_volume(self.plate)
    self.assertAlmostEqual(volume, await well.compute_volume_from_height(4.0), delta=1.0)


class TestHead96InSimulation(unittest.IsolatedAsyncioTestCase):
  """The simulator answers the head's searches and strokes from the model, with no stubs."""

  async def asyncSetUp(self):
    self.driver, self.deck, self.head, plates = await _head_with_tips(trough=True)
    self.plate, self.trough_plate = plates["plate"], plates["trough"]

  async def height_of(self, container: handles.Container, volume: float) -> float:
    return float(round(await container.compute_height_from_volume(volume), 2))

  async def a1(self) -> Coordinate:
    return (await self.head._get_target(self.plate, None))[1]

  async def test_the_surface_is_read_from_the_model(self):
    well = self.plate.get_well("A1")
    await well.set_volume(150.0)
    height = await self.head.probe_liquid_height(self.plate)
    self.assertAlmostEqual(height, await self.height_of(well, 150.0), delta=0.02)

  async def test_rh_is_the_stop_disc_zi_below_where_the_head_stops(self):
    await self.plate.get_well("A1").set_volume(150.0)
    # The search does not move in X or Y: the head goes over the plate first.
    a1 = await self.a1()
    await self.head.move_to_xy_position(a1.x, a1.y)
    await self.head.probe_z_using_clld(post_detection_distance=4.0)
    self.assertAlmostEqual(
      await self.head.request_z_position(),
      await self.head.request_last_lld_z_position() + 4.0,
      delta=0.01,
    )

  async def test_the_traverse_height_raises_a_lower_head_and_leaves_a_higher_one(self):
    a1 = await self.a1()
    top = self.head.configuration.z_range[1] - await self.head.request_tip_overhang()
    await self.head.move_tool_bottom_to_z_position(top - 50.0)
    await self.head.move_to_xy_position(a1.x, a1.y, minimum_traverse_height_start=top - 20.0)
    self.assertAlmostEqual((await self.head.request_location()).z, top - 20.0, delta=0.05)
    await self.head.move_to_xy_position(a1.x, a1.y, minimum_traverse_height_start=top - 40.0)
    self.assertAlmostEqual((await self.head.request_location()).z, top - 20.0, delta=0.05)

  async def test_every_drive_setting_reaches_its_move(self):
    a1 = await self.a1()
    moves = dict.fromkeys(("move_to_safe_z", "move_to_x_position", "move_to_y_position"), DEFAULT)
    with patch.multiple(self.head, new_callable=AsyncMock, **moves) as mocked:
      await self.head.move_to_xy_position(
        a1.x,
        a1.y,
        x_acceleration_level=4,
        x_current_limit=5,
        y_speed=100.0,
        y_acceleration=200.0,
        y_current_limit=10,
        z_speed=50.0,
        z_acceleration=300.0,
      )
    mocked["move_to_safe_z"].assert_awaited_once_with(speed=50.0, acceleration=300.0)
    mocked["move_to_x_position"].assert_awaited_once_with(
      a1.x, acceleration_level=4, current_limit=5
    )
    mocked["move_to_y_position"].assert_awaited_once_with(
      a1.y, speed=100.0, acceleration=200.0, current_limit=10
    )

  async def test_an_unreachable_traverse_height_is_refused_as_a_tip_bottom(self):
    a1 = await self.a1()
    with self.assertRaisesRegex(ValueError, "the tool bottom reaches .* not 1000.0"):
      await self.head.move_to_xy_position(a1.x, a1.y, minimum_traverse_height_start=1000.0)

  async def test_mix_rises_at_the_drive_default_not_its_descent_speed(self):
    with patch.object(self.head, "move_to_safe_z", AsyncMock()) as raised:
      await self.head.mix(self.plate, Mix(volume=50.0, repetitions=1, flow_rate=100.0))
    self.assertEqual(raised.await_args_list[0].kwargs, {"speed": None, "acceleration": None})

  async def test_an_unreachable_y_is_refused_before_the_head_is_raised(self):
    a1 = await self.a1()
    top = self.head.configuration.z_range[1] - await self.head.request_tip_overhang()
    await self.head.move_tool_bottom_to_z_position(top - 50.0)
    with self.assertRaises(ValueError):
      await self.head.move_to_xy_position(a1.x, 10_000.0, minimum_traverse_height_start=top - 20.0)
    self.assertAlmostEqual((await self.head.request_location()).z, top - 50.0, delta=0.05)

  async def test_without_tips_probing_and_mixing_are_refused_before_moving(self):
    await self.head.discard_tips()
    x, y = await self.head.request_x_position(), await self.head.request_y_position()
    for command in (
      self.head.probe_liquid_height(self.plate),
      self.head.mix(self.plate, Mix(volume=100.0, repetitions=1, flow_rate=200.0)),
    ):
      with self.assertRaisesRegex(RuntimeError, "pick up tips first"):
        await command
    self.assertEqual(
      (await self.head.request_x_position(), await self.head.request_y_position()), (x, y)
    )

  async def test_an_empty_well_reads_zero(self):
    self.assertEqual(await self.head.probe_liquid_height(self.plate), 0.0)

  async def test_a_one_well_trough_is_found_with_the_array_centred(self):
    trough = self.trough_plate.get_well(0)
    await trough.set_volume(100_000.0)
    height = await self.head.probe_liquid_height(self.trough_plate)
    self.assertAlmostEqual(height, await self.height_of(trough, 100_000.0), delta=0.02)

  async def test_a_sensor_reads_only_its_own_corner(self):
    g11 = self.plate.get_well("G11")
    await g11.set_volume(150.0)
    self.assertEqual(await self.head.probe_liquid_height(self.plate, lld_sensor="A1 or B2"), 0.0)
    height = await self.head.probe_liquid_height(self.plate, lld_sensor="G11 or H12")
    self.assertAlmostEqual(height, await self.height_of(g11, 150.0), delta=0.02)

  async def test_a_mix_moves_the_piston_and_leaves_the_liquid(self):
    trough = self.trough_plate.get_well(0)
    await trough.set_volume(100_000.0)
    mix = Mix(volume=50.0, repetitions=3, flow_rate=100.0, surface_following_distance=1.0)
    await self.head.mix(self.trough_plate, mix, offset=Coordinate(0, 0, 5.0))
    self.assertAlmostEqual(self.driver.head96_dispensing_drive_uL, 0.0, delta=0.05)
    self.assertEqual(await trough.get_volume(), 100_000.0)

  async def test_a_mix_under_clld_runs_end_to_end(self):
    trough = self.trough_plate.get_well(0)
    await trough.set_volume(100_000.0)
    await self.head.mix(
      self.trough_plate,
      Mix(volume=50.0, repetitions=2, flow_rate=100.0),
      lld_mode=LLDMode.CAPACITIVE,
    )
    self.assertAlmostEqual(await trough.get_volume(), 100_000.0, delta=50.0)
    self.assertEqual(await self.head.request_z_position(), self.head.configuration.z_range[1])


class _WireOnly:
  """A driver that records what it is asked to send and answers nothing."""

  def __init__(self) -> None:
    self.sent: List[str] = []

  async def send_command(self, module: str, command: str, **kwargs: Any) -> str:
    wire = {key: value for key, value in kwargs.items() if len(key) == 2}
    self.sent.append(assemble_command(module, command, **wire))
    return ""


async def _get_legacy_wire(command: str, **kwargs: Any) -> str:
  """What legacy's `aspirate_core_96` (`EA`) or `dispense_core_96` (`ED`) assembles for kwargs."""
  from pylabrobot.legacy.liquid_handling.backends.hamilton.STAR_backend import STARBackend
  from pylabrobot.legacy.liquid_handling.backends.hamilton.STAR_chatterbox import (
    _DEFAULT_EXTENDED_CONFIGURATION,
  )

  backend = STARBackend()
  backend._extended_conf = _DEFAULT_EXTENDED_CONFIGURATION
  backend._iswap_parked = True
  sent = AsyncMock(return_value="")
  backend.send_command = sent  # type: ignore[method-assign]
  if command == "EA":
    await backend.aspirate_core_96(**kwargs)
  else:
    await backend.dispense_core_96(**kwargs)
  wire = {key: value for key, value in sent.call_args.kwargs.items() if len(key) == 2}
  return assemble_command(sent.call_args.kwargs["module"], command, **wire)


# Legacy's name for each field, this driver's, and the range legacy accepts.
_EA_FIELDS = [
  ("aspiration_type", "aspiration_type", 0, 2),
  ("y_positions", "y_position", 1080, 5600),
  ("minimum_traverse_height_at_beginning_of_a_command", "minimum_traverse_height_start", 0, 3425),
  ("min_z_endpos", "minimum_z_end_position", 0, 3425),
  ("lld_search_height", "lld_search_height", 0, 3425),
  ("liquid_surface_no_lld", "liquid_surface_no_lld", 0, 3425),
  ("pull_out_distance_transport_air", "pull_out_distance_transport_air", 0, 3425),
  ("second_section_height", "second_section_height", 0, 3425),
  ("second_section_ratio", "second_section_ratio", 0, 10000),
  ("minimum_height", "minimum_height", 0, 3425),
  ("immersion_depth", "immersion_depth", 0, 3600),
  ("immersion_depth_direction", "immersion_depth_direction", 0, 1),
  ("surface_following_distance", "surface_following_distance", 0, 990),
  ("aspiration_volumes", "aspiration_volume", 0, 11500),
  ("aspiration_speed", "aspiration_speed", 3, 5000),
  ("transport_air_volume", "transport_air_volume", 0, 500),
  ("blow_out_air_volume", "blow_out_air_volume", 0, 11500),
  ("pre_wetting_volume", "pre_wetting_volume", 0, 11500),
  ("lld_mode", "lld_mode", 0, 4),
  ("gamma_lld_sensitivity", "clld_sensitivity", 1, 4),
  ("swap_speed", "swap_speed", 3, 1000),
  ("settling_time", "settling_time", 0, 99),
  ("mix_volume", "mix_volume", 0, 11500),
  ("mix_cycles", "mix_cycles", 0, 99),
  ("mix_position_from_liquid_surface", "mix_position_from_liquid_surface", 0, 990),
  ("speed_of_mix", "mix_speed", 3, 5000),
  ("mix_surface_following_distance", "mix_surface_following_distance", 0, 990),
  ("limit_curve_index", "limit_curve_index", 0, 999),
  ("recording_mode", "recording_mode", 0, 2),
]
_ED_FIELDS = [
  ("dispensing_mode", "dispensing_mode", 0, 4),
  ("y_position", "y_position", 1080, 5600),
  ("minimum_height", "minimum_height", 0, 3425),
  ("lld_search_height", "lld_search_height", 0, 3425),
  ("liquid_surface_no_lld", "liquid_surface_no_lld", 0, 3425),
  ("pull_out_distance_transport_air", "pull_out_distance_transport_air", 0, 3425),
  ("immersion_depth", "immersion_depth", 0, 3600),
  ("immersion_depth_direction", "immersion_depth_direction", 0, 1),
  ("surface_following_distance", "surface_following_distance", 0, 990),
  ("second_section_height", "second_section_height", 0, 3425),
  ("second_section_ratio", "second_section_ratio", 0, 10000),
  ("minimum_traverse_height_at_beginning_of_a_command", "minimum_traverse_height_start", 0, 3425),
  ("min_z_endpos", "minimum_z_end_position", 0, 3425),
  ("dispense_volume", "dispense_volume", 0, 11500),
  ("dispense_speed", "dispense_speed", 3, 5000),
  ("cut_off_speed", "cut_off_speed", 3, 5000),
  ("stop_back_volume", "stop_back_volume", 0, 999),
  ("transport_air_volume", "transport_air_volume", 0, 500),
  ("blow_out_air_volume", "blow_out_air_volume", 0, 11500),
  ("lld_mode", "lld_mode", 0, 4),
  ("side_touch_off_distance", "side_touch_off_distance", 0, 45),
  ("gamma_lld_sensitivity", "clld_sensitivity", 1, 4),
  ("swap_speed", "swap_speed", 3, 1000),
  ("settling_time", "settling_time", 0, 99),
  ("mixing_volume", "mix_volume", 0, 11500),
  ("mixing_cycles", "mix_cycles", 0, 99),
  ("mix_position_from_liquid_surface", "mix_position_from_liquid_surface", 0, 990),
  ("speed_of_mixing", "mix_speed", 3, 5000),
  ("mix_surface_following_distance", "mix_surface_following_distance", 0, 990),
  ("limit_curve_index", "limit_curve_index", 0, 999),
  ("recording_mode", "recording_mode", 0, 2),
]


def _get_value_sets(fields: List[Tuple[str, str, int, int]]) -> List[Tuple[dict, dict]]:
  """Three (legacy kwargs, this driver's kwargs) pairs: every field low, then high, then random."""
  rng = random.Random(0)
  pairs = []
  for draw in ("low", "high", "random"):
    legacy: Dict[str, Any] = {}
    ours: Dict[str, Any] = {}
    for legacy_name, name, low, high in fields:
      value = {"low": low, "high": high, "random": rng.randint(low, high)}[draw]
      legacy[legacy_name], ours[name] = value, value
    x = {"low": 0, "high": 30000, "random": rng.randint(1, 30000)}[draw]
    direction = 0 if draw == "low" else 1
    pattern = {
      "low": [False] * 96,
      "high": [True] * 96,
      "random": [rng.random() < 0.5 for _ in range(96)],
    }[draw]
    tadm = draw != "low"
    legacy.update(x_position=x, x_direction=direction, channel_pattern=pattern, tadm_algorithm=tadm)
    ours.update(x_position=-x if direction else x, channel_pattern=pattern, tadm_algorithm=tadm)
    pairs.append((legacy, ours))
  return pairs


class TestHead96AspirateDispenseWire(unittest.IsolatedAsyncioTestCase):
  """`C0 EA` and `C0 ED` go out as legacy's `aspirate_core_96` and `dispense_core_96` send them."""

  async def test_aspirate_is_sent_as_legacy_sends_it(self):
    for legacy, ours in _get_value_sets(_EA_FIELDS):
      with self.subTest(values=ours):
        driver = _WireOnly()
        await Head96(cast(Any, driver))._unchecked_fw_aspirate(**ours)
        self.assertEqual(driver.sent, [await _get_legacy_wire("EA", **legacy)])

  async def test_dispense_is_sent_as_legacy_sends_it(self):
    for legacy, ours in _get_value_sets(_ED_FIELDS):
      with self.subTest(values=ours):
        driver = _WireOnly()
        await Head96(cast(Any, driver))._unchecked_fw_dispense(**ours)
        self.assertEqual(driver.sent, [await _get_legacy_wire("ED", **legacy)])


class TestHead96PistonModel(unittest.IsolatedAsyncioTestCase):
  """`piston_position` follows every stroke, and a failed one is read back from `H0 RD`."""

  async def asyncSetUp(self):
    self.driver, _ = await make_driver()
    await self.driver.setup()
    self.head = cast(Head96, self.driver.head96)
    self.rd = [0, 0]
    self.failing: Optional[str] = None
    answer = self.driver.send_command

    async def stubbed(module: str, command: str, fmt: Optional[Any] = None, **kwargs: Any):
      if module + command == "H0RD":
        return {"rd": list(self.rd)}
      if module + command in ("H0PA", "H0PB", "H0DQ"):
        if module + command == self.failing:
          check_fw_string_error(f"{module}{command}id0001er99/00")
        return ""
      return await answer(module, command, fmt=fmt, **kwargs)

    self.driver.send_command = stubbed  # type: ignore[assignment]

  def as_counted(self, uL: float) -> float:
    c = self.head.configuration
    return c.dispensing_drive_increments_to_uL(c.dispensing_drive_uL_to_increments(uL))

  async def test_the_read_takes_the_hardware_counter(self):
    self.rd = [1, 5170]
    expected = self.head.configuration.dispensing_drive_increments_to_uL(5170)
    self.assertEqual(await self.head.dispensing_drive_request_uL_position(), expected)
    self.assertEqual(self.head.piston_position, expected)

  async def test_initialization_reads_the_piston(self):
    self.rd = [0, 1000]
    await self.head.initialize(tip_discard_location=Coordinate(400.0, 300.0, 200.0))
    expected = self.head.configuration.dispensing_drive_increments_to_uL(1000)
    self.assertEqual(self.head.piston_position, expected)

  async def test_strokes_move_the_model_as_the_drive_counts(self):
    await self.head._aspirate_in_place(100.0)
    self.assertEqual(self.head.piston_position, self.as_counted(100.0))
    await self.head._dispense_in_place(60.0, stop_back_volume=2.0)
    expected = self.as_counted(100.0) - self.as_counted(60.0) + self.as_counted(2.0)
    self.assertAlmostEqual(self.head.piston_position, expected, places=2)
    # Pushing out more than it holds leaves the piston at rest.
    await self.head._dispense_in_place(500.0)
    self.assertEqual(self.head.piston_position, 0.0)

  async def test_the_dispensing_drive_move_records_where_it_was_sent(self):
    await self.head.move_dispensing_drive_to_position(218.19)
    self.assertEqual(self.head.piston_position, self.as_counted(218.19))

  async def test_a_failed_command_reads_the_piston_back(self):
    moves = {
      "H0PA": lambda: self.head._aspirate_in_place(100.0),
      "H0PB": lambda: self.head._dispense_in_place(100.0),
      "H0DQ": lambda: self.head.move_dispensing_drive_to_position(100.0),
    }
    for failing, move in moves.items():
      with self.subTest(command=failing):
        self.failing = failing
        self.rd = [0, 1234]
        self.head.piston_position = 50.0
        with self.assertRaises(STARFirmwareError):
          await move()
        expected = self.head.configuration.dispensing_drive_increments_to_uL(1234)
        self.assertEqual(self.head.piston_position, expected)


class TestDispensingDriveUnits(unittest.IsolatedAsyncioTestCase):
  """`DQ` is written in the units and field widths each head's drive counts in."""

  async def test_the_384_head_counts_speed_in_tens_and_acceleration_in_thousands(self):
    driver = _WireOnly()
    head = Head384(cast(Any, driver), Head384Configuration(head_type="High volume head"))
    with patch("pylabrobot.hamilton.star.driver.features.head.Head.discover", AsyncMock()):
      await head.discover()
    await head.move_dispensing_drive_to_position(10.0)
    increments = head.configuration.dispensing_drive_uL_to_increments(10.0)
    self.assertEqual(driver.sent, [f"D0DQdq{increments:05}dv05000du00000dr9000dw15"])

  async def test_a_2008_96_head_counts_acceleration_in_thousands_in_narrower_fields(self):
    driver = _WireOnly()
    configuration = Head96Configuration(firmware_date=datetime.date(2008, 6, 1))
    head = Head96(cast(Any, driver), configuration)
    head._apply_firmware_generation()
    await head.move_dispensing_drive_to_position(100.0, speed=200.0, current_limit=7)
    self.assertEqual(driver.sent, ["H0DQdq05170dv10341du00000dr150dw7"])
    # Its window reaches 411 thousands, the same field width.
    top = configuration.dispensing_drive_acceleration_range[1]
    self.assertEqual(configuration.dispensing_drive_acceleration_uL_to_increments(top), 411)

  def test_the_384_head_has_no_default_until_its_type_is_known(self):
    head = Head384(cast(Any, _WireOnly()))
    with self.assertRaises(RuntimeError):
      head.default_dispensing_drive_speed

  def test_a_first_generation_head_takes_its_own_resolutions(self):
    for head_type, year, uL, squeezer, acceleration in (
      ("High volume head", 2008, 0.018509877, 0.000459073, 2776.48),
      ("96 head II", 2021, 0.019340933, 0.0002086672009, 17000.0),
      ("96 head TADM", 2021, 0.019340933, 0.0002086672009, 17000.0),
    ):
      with self.subTest(head_type=head_type):
        configuration = Head96Configuration(
          head_type=head_type, firmware_date=datetime.date(year, 6, 1)
        )
        head = Head96(cast(Any, _WireOnly()), configuration)
        head._apply_firmware_generation()
        head._apply_head_type()
        self.assertEqual(configuration.dispensing_drive_uL_per_increment, uL)
        self.assertEqual(configuration.squeezer_drive_mm_per_increment, squeezer)
        self.assertEqual(head.default_dispensing_drive_acceleration, acceleration)


class TestHead96AspirateDispense(unittest.IsolatedAsyncioTestCase):
  """`aspirate` and `dispense` over a plate and a one-well trough, the raw commands recorded."""

  async def asyncSetUp(self):
    self.driver, self.deck, self.head, plates = await _head_with_tips(trough=True)
    self.plate = plates["plate"]
    self.trough = plates["trough"].get_well(0)
    # Where the piston stands is read, never moved: the simulator leaves it where it started.
    await self.head.dispensing_drive_request_uL_position()
    await self.plate.set_well_volumes(200.0)
    self.wells = [cast(handles.Container, well) for well in self.plate.items]

    self.sent: List[Tuple[str, Dict[str, Any]]] = []
    self.failing = False
    # How far a failed command moves the piston before it stops, in uL.
    self.moved_before_failure = 0.0
    self.moved = 0.0

    def recorder(command: str):
      async def record(**kwargs: Any) -> None:
        self.sent.append((command, kwargs))
        if self.failing:
          self.moved = self.moved_before_failure
          check_fw_string_error(f"C0{command}id0001er99/00")

      return record

    async def piston() -> float:
      return self.head.piston_position + self.moved

    self.head._unchecked_fw_aspirate = recorder("EA")  # type: ignore[method-assign]
    self.head._unchecked_fw_dispense = recorder("ED")  # type: ignore[method-assign]
    self.head.dispensing_drive_request_uL_position = piston  # type: ignore[method-assign]

  async def tip_volumes(self) -> Set[float]:
    return {
      tool.state.volume.pending_volume
      for tool in (await self.head._get_tools()).values()
      if tool is not None
    }

  async def well_volumes(self) -> Set[float]:
    return await volumes_of(self.wells)

  async def test_off_over_a_plate_draws_at_the_cavity_bottom_and_books_each_well(self):
    await self.head.aspirate(self.plate, 50.0)
    self.assertEqual(
      self.sent,
      [
        (
          "EA",
          {
            "aspiration_type": 0,
            "x_position": 2533,
            "y_position": 2417,
            "minimum_traverse_height_start": 2450,
            "minimum_z_end_position": 2450,
            "lld_search_height": 2018,
            "liquid_surface_no_lld": 1866,
            "pull_out_distance_transport_air": 100,
            "minimum_height": 1866,
            "second_section_height": 32,
            "second_section_ratio": 6180,
            "immersion_depth": 0,
            "immersion_depth_direction": 0,
            "surface_following_distance": 0,
            # 50 uL, corrected by the water class of a 300 uL CoRe filter tip.
            "aspiration_volume": 534,
            "aspiration_speed": 1000,
            "transport_air_volume": 0,
            "blow_out_air_volume": 0,
            "pre_wetting_volume": 50,
            "lld_mode": 0,
            "clld_sensitivity": 1,
            "swap_speed": 20,
            "settling_time": 10,
            "mix_volume": 0,
            "mix_cycles": 0,
            "mix_position_from_liquid_surface": 0,
            "mix_surface_following_distance": 0,
            "mix_speed": 1000,
            "channel_pattern": [True] * 96,
            "limit_curve_index": 0,
            "tadm_algorithm": False,
            "recording_mode": 0,
          },
        )
      ],
    )
    self.assertEqual(await self.well_volumes(), {150.0})
    self.assertEqual(await self.tip_volumes(), {50.0})
    self.assertEqual(self.head.piston_position, 53.4)

  async def test_off_into_a_trough_centres_the_array_and_books_96_times(self):
    await self.head.aspirate(self.plate, piston_volume=40.0, liquid_height=2.0)
    self.assertEqual(self.sent[0][1]["liquid_surface_no_lld"], 1886)
    await self.head.dispense(self.trough, piston_volume=40.0, jet=True, blow_out=True)
    command, fields = self.sent[1]
    self.assertEqual(command, "ED")
    centre = await self.trough.get_location_wrt(self.deck, "c", "c", "cavity_bottom")
    c = self.head.configuration
    self.assertEqual(
      (fields["dispensing_mode"], fields["x_position"], fields["y_position"]),
      (
        1,
        round((centre.x - c.channel_array_size_x / 2) * 10),
        round((centre.y + c.channel_array_size_y / 2) * 10),
      ),
    )
    self.assertEqual(
      (fields["liquid_surface_no_lld"], fields["minimum_height"], fields["dispense_volume"]),
      (round(centre.z * 10), round(centre.z * 10), 400),
    )
    self.assertEqual(await self.trough.get_volume(), 96 * 40.0)
    self.assertEqual(await self.tip_volumes(), {0.0})
    self.assertEqual(self.head.piston_position, 0.0)

  async def test_a_container_that_states_no_maximum_takes_what_is_dispensed(self):
    trough_plate = cast(handles.Resource, await self.trough.get_parent())
    holder = cast(handles.Resource, await trough_plate.get_parent())
    definition = pb.ResourceDefinition()
    definition.CopyFrom(library.get_model("agenbio_1_troughplate_190mL_Fl").definition)
    definition.attributes.itemized.grid.item.attributes.container.ClearField("max_volume")
    await trough_plate.delete()
    unbounded = cast(
      handles.Plate, await self.deck.store.create(definition, name="trough", parent=holder)
    )
    well = unbounded.get_well(0)
    await well.set_volume_tracking(True)
    await self.head.aspirate(self.plate, piston_volume=40.0, liquid_height=2.0)
    await self.head.dispense(well, piston_volume=40.0, jet=True, blow_out=True)
    self.assertEqual(self.sent[-1][0], "ED")
    self.assertEqual(await well.get_volume(), 96 * 40.0)

  async def test_capacitive_draws_the_air_first_then_under_the_surface_found(self):
    await self.trough.set_volume(100_000.0)
    await self.head.aspirate(
      self.trough,
      piston_volume=20.0,
      lld_mode=LLDMode.CAPACITIVE,
      blow_out_air_volume=10.0,
      auto_surface_following=True,
    )
    fields = self.sent[0][1]
    bottom = (await self.trough.get_location_wrt(self.deck, "c", "c", "cavity_bottom")).z
    height = await self.trough.compute_height_from_volume(100_000.0)
    # The air goes in in place beforehand; the command starts where the search left the tips.
    self.assertEqual(self.driver.head96_dispensing_drive_uL, 10.0)
    self.assertEqual((fields["blow_out_air_volume"], fields["lld_mode"]), (0, 0))
    self.assertAlmostEqual(fields["liquid_surface_no_lld"], (bottom + height) * 10, delta=1)
    self.assertEqual(fields["minimum_traverse_height_start"], fields["liquid_surface_no_lld"])
    self.assertEqual(fields["minimum_height"], round(bottom * 10))
    # 2 mm under it, following it down by what 96 draws of 20 uL take from the trough.
    self.assertEqual(fields["immersion_depth"], 20)
    drop = height - await self.trough.compute_height_from_volume(100_000.0 - 96 * 20.0)
    self.assertAlmostEqual(fields["surface_following_distance"], drop * 10, delta=1)
    # Set to what the search measured, to the Z drive's resolution, then 96 draws booked.
    self.assertAlmostEqual(await self.trough.get_volume(), 100_000.0 - 96 * 20.0, delta=50)
    self.assertEqual(self.head.piston_position, 30.0)

  async def test_capacitive_immersion_and_following_stop_at_the_floor(self):
    await self.trough.set_volume(2_000.0)
    await self.head.aspirate(
      self.trough, piston_volume=20.0, lld_mode=LLDMode.CAPACITIVE, auto_surface_following=True
    )
    fields = self.sent[0][1]
    lowest = (
      fields["liquid_surface_no_lld"]
      - fields["immersion_depth"]
      - fields["surface_following_distance"]
    )
    self.assertGreaterEqual(lowest, fields["minimum_height"])

  async def test_capacitive_follows_nothing_unless_asked(self):
    await self.trough.set_volume(100_000.0)
    await self.head.aspirate(self.trough, piston_volume=20.0, lld_mode=LLDMode.CAPACITIVE)
    self.assertEqual(self.sent[0][1]["surface_following_distance"], 0)

  async def test_auto_surface_following_searches_capacitive_when_no_mode_is_given(self):
    await self.trough.set_volume(100_000.0)
    await self.head.aspirate(self.trough, piston_volume=20.0, auto_surface_following=True)
    fields = self.sent[0][1]
    height = await self.trough.compute_height_from_volume(100_000.0)
    drop = height - await self.trough.compute_height_from_volume(100_000.0 - 96 * 20.0)
    self.assertAlmostEqual(fields["surface_following_distance"], drop * 10, delta=1)

  async def test_auto_surface_following_refused_beside_a_distance_or_without_a_surface(self):
    refused: List[Dict[str, Any]] = [
      {"surface_following_distance": 1.0},
      {"lld_mode": LLDMode.OFF},
    ]
    for kwargs in refused:
      for call in (self.head.aspirate, self.head.dispense):
        with self.subTest(call=call.__name__, **kwargs), self.assertRaises(ValueError):
          await call(self.trough, piston_volume=20.0, auto_surface_following=True, **kwargs)
    self.assertEqual(self.sent, [])

  async def test_auto_surface_following_under_off_follows_from_the_liquid_height(self):
    await self.trough.set_volume(100_000.0)
    await self.head.aspirate(
      self.trough,
      piston_volume=20.0,
      lld_mode=LLDMode.OFF,
      liquid_height=10.0,
      auto_surface_following=True,
    )
    held = await self.trough.compute_volume_from_height(10.0)
    drop = 10.0 - await self.trough.compute_height_from_volume(held - 96 * 20.0)
    self.assertAlmostEqual(self.sent[0][1]["surface_following_distance"], drop * 10, delta=1)

  async def test_a_pre_mix_auto_follows_what_one_draw_takes_from_the_surface_found(self):
    await self.trough.set_volume(100_000.0)
    pre_mix = Mix(volume=10.0, repetitions=2, flow_rate=100.0, auto_surface_following=True)
    await self.head.aspirate(
      self.trough, piston_volume=20.0, lld_mode=LLDMode.CAPACITIVE, pre_mix=pre_mix
    )
    fields = self.sent[0][1]
    height = await self.trough.compute_height_from_volume(100_000.0)
    drop = height - await self.trough.compute_height_from_volume(100_000.0 - 96 * 10.0)
    self.assertAlmostEqual(fields["mix_surface_following_distance"], drop * 10, delta=1)
    self.assertEqual(fields["surface_following_distance"], 0)
    with self.assertRaises(ValueError):
      await self.head.aspirate(self.trough, piston_volume=20.0, pre_mix=pre_mix)

  async def test_capacitive_dispense_into_a_plate_books_each_well(self):
    await self.head.aspirate(self.plate, piston_volume=30.0)
    await self.head.dispense(
      self.plate, piston_volume=30.0, lld_mode=LLDMode.CAPACITIVE, auto_surface_following=True
    )
    fields = self.sent[1][1]
    well = self.plate.get_well("A1")
    bottom = (await well.get_location_wrt(self.deck, "c", "c", "cavity_bottom")).z
    surface = bottom + await well.compute_height_from_volume(170.0)
    self.assertAlmostEqual(fields["liquid_surface_no_lld"], surface * 10, delta=1)
    self.assertEqual(fields["minimum_traverse_height_start"], fields["liquid_surface_no_lld"])
    # Following up by what 30 uL raises the well's surface.
    rise = await well.compute_height_from_volume(200.0) - await well.compute_height_from_volume(
      170.0
    )
    self.assertAlmostEqual(fields["surface_following_distance"], rise * 10, delta=1)
    self.assertEqual(await self.tip_volumes(), {0.0})
    self.assertEqual(await volumes_of(self.wells[1:]), {200.0})

  async def test_no_liquid_under_capacitive_raises_and_the_head_goes_up(self):
    with self.assertRaises(RuntimeError):
      await self.head.aspirate(self.trough, piston_volume=20.0, lld_mode=LLDMode.CAPACITIVE)
    self.assertEqual(self.sent, [])
    self.assertEqual(await self.head.request_z_position(), self.head.configuration.z_range[1])

  async def test_a_failed_command_rolls_back_and_raises_the_head(self):
    self.failing = True
    with self.assertRaises(STARFirmwareError):
      await self.head.aspirate(self.plate, piston_volume=50.0)
    self.assertEqual(await self.well_volumes(), {200.0})
    self.assertEqual(await self.tip_volumes(), {0.0})
    self.assertEqual(self.head.piston_position, 0.0)
    self.assertEqual(await self.head.request_z_position(), self.head.configuration.z_range[1])

  async def test_what_a_failed_command_moved_is_booked_from_the_piston(self):
    self.failing = True
    self.moved_before_failure = 20.0
    with self.assertRaises(STARFirmwareError):
      await self.head.aspirate(self.plate, piston_volume=50.0)
    self.assertEqual(await self.well_volumes(), {180.0})
    self.assertEqual(await self.tip_volumes(), {20.0})

  async def test_refusals_send_nothing_and_move_nothing(self):
    z = await self.head.request_z_position()
    refusals = {
      "pressure": lambda: self.head.aspirate(self.plate, 5.0, lld_mode=LLDMode.PRESSURE),
      "both volumes": lambda: self.head.aspirate(self.plate, 5.0, piston_volume=5.0),
      "a height under cLLD": lambda: self.head.aspirate(
        self.plate, 5.0, liquid_height=2.0, lld_mode=LLDMode.CAPACITIVE
      ),
      "eight wells": lambda: self.head.aspirate(self.plate.get_wells(list(range(8))), 5.0),
      "one well of many": lambda: self.head.aspirate(self.plate.get_well("B1"), 5.0),
      "a fast flow": lambda: self.head.aspirate(self.plate, piston_volume=5.0, flow_rate=900.0),
      "past the piston": lambda: self.head.aspirate(self.plate, piston_volume=5_000.0),
      "an empty piston": lambda: self.head.dispense(self.plate, piston_volume=5.0),
      "z touch": lambda: self.head.dispense(self.plate, 5.0, lld_mode=LLDMode.ZTOUCH),
    }
    for name, refused in refusals.items():
      with self.subTest(name):
        with self.assertRaises(ValueError):
          await refused()
    self.assertEqual(self.sent, [])
    self.assertEqual(await self.head.request_z_position(), z)

  async def test_a_trough_without_room_is_refused(self):
    await self.head.aspirate(self.plate, piston_volume=50.0)
    await self.trough.set_volume(cast(float, await self.trough.get_max_volume()) - 96 * 10.0)
    with self.assertRaises(ValueError):
      await self.head.dispense(self.trough, piston_volume=50.0)
    self.assertEqual(len(self.sent), 1)


if __name__ == "__main__":
  unittest.main()
