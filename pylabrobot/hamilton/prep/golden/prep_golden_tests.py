"""Golden tests of what a simulated Prep does today: the frames it is sent and the resources it
leaves.

Every scenario drives a `Prep(simulation=True)` - a real `PrepSimulationDriver` answering from the
recorded firmware tree through `_SimulatedIO` - on its own `PrepDeck`, through the device's public
API. Each frame the session exchanges is recorded as hex, built with the session's client address
and sequence 0, so a frame does not depend on how many went to its destination before it. The
resources are the device's whole tree, from the device down.

Rewrite the golden files after a change meant to change them:

  PLR_UPDATE_GOLDEN=1 python -m pytest pylabrobot/hamilton/prep/golden
"""

from __future__ import annotations

import asyncio
import dataclasses
import enum
import inspect
import pathlib
import unittest
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Type, Union

from pylabrobot.hamilton.prep import Prep, PrepDevice, PrepSimulationDriver
from pylabrobot.hamilton.prep.driver import prep_commands as PrepCmd
from pylabrobot.hamilton.prep.driver.features.head8 import Head8
from pylabrobot.hamilton.prep.driver.features.pipettes import Pipettes
from pylabrobot.hamilton.prep.driver.master import _ResolvedPrepCommand
from pylabrobot.hamilton.prep.driver.simulator import (
  FIRMWARE_TREE_V1_2_2,
  RECORDING_PREP,
  _DeviceRefuses,
)
from pylabrobot.hamilton.transport.tcp.hoi_error import HoiError
from pylabrobot.hamilton.transport.tcp.messages import HoiParams
from pylabrobot.hamilton.transport.tcp.packets import Address
from pylabrobot.hamilton.transport.tcp.wire_types import U32, Struct
from pylabrobot.legacy.liquid_handling.errors import ChannelizedError
from pylabrobot.lib.liquid_handling.mix import Mix
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.errors import HasTipError, TooLittleVolumeError
from pylabrobot.resources.store import handles, library
from pylabrobot.testing.golden import check_golden, snapshot_changes, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

# Where the simulated session's client sits, and the sequence every recorded frame is built with.
CLIENT = Address(2, 1, 65535)


def _jsonable(value: Any) -> Any:
  """A call's result as a golden file holds it."""
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  if isinstance(value, enum.Enum):
    return value.name
  if isinstance(value, Coordinate):
    return [value.x, value.y, value.z]
  if isinstance(value, bytes):
    return value.hex()
  if isinstance(value, dict):
    return {str(key): _jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [_jsonable(item) for item in value]
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return {
      field.name: _jsonable(item)
      for field, item in zip(dataclasses.fields(value), dataclasses.astuple(value))
    }
  return type(value).__name__


def _error(error: Exception) -> Dict[str, Any]:
  """What a step raised: its type and message, and for a channelized error each channel's."""
  record: Dict[str, Any] = {"type": type(error).__name__, "message": str(error)}
  if isinstance(error, ChannelizedError):
    record["channels"] = {
      str(channel): type(failure).__name__ for channel, failure in sorted(error.errors.items())
    }
  return record


class _Recording:
  """A simulated Prep whose every frame is recorded, step by step, with the resources after each.

  Each step's `sent` is every frame the session exchanged during it, in order, each as the
  command's name and the frame's hex. A step that changes the resources records them after it; a
  step that raises what it was expected to records the error instead of a result.
  """

  def __init__(self, prep: PrepDevice, resources: List[Dict[str, Any]]):
    self.prep = prep
    self.steps: List[Dict[str, Any]] = []
    self._sent: List[str] = []
    # The resources as the last step left them; a scenario changes them only through its steps.
    self._resources = resources
    self._watch(prep.driver)

  @classmethod
  async def start(cls, prep: PrepDevice) -> "_Recording":
    """Record `prep` from here, its resources made in its store first."""
    await prep.create_resources()
    return cls(prep, await cls.snapshot(prep))

  @staticmethod
  async def snapshot(prep: PrepDevice) -> List[Dict[str, Any]]:
    """The device's whole tree, from its body down."""
    assert prep.body is not None
    return await snapshot_store(prep.store, prep.body)

  def _watch(self, driver: Any) -> None:
    """Record every frame `driver`'s link exchanges, on each session it opens from here on."""
    io = driver.io
    create = io._create_session

    def create_recorded() -> Any:
      session = create()
      exchange = session.exchange

      async def exchange_recorded(command: Any, *args: Any, **kwargs: Any) -> Any:
        request = command.request if isinstance(command, _ResolvedPrepCommand) else command
        self._sent.append(f"{type(request).__name__} {command.build(CLIENT, 0).hex()}")
        return await exchange(command, *args, **kwargs)

      session.exchange = exchange_recorded
      return session

    io._create_session = create_recorded

  async def forget(self) -> None:
    """Start the record from here: what was sent so far is dropped, and the resources are read."""
    self._sent = []
    self._resources = await self.snapshot(self.prep)

  async def step(
    self,
    call: str,
    action: Callable[[], Any],
    raises: Optional[Type[Exception]] = None,
  ) -> Any:
    """Run one step of the scenario and record it.

    Args:
      call: the step, as the scenario reads.
      action: the step itself; what it returns is awaited when it can be.
      raises: the exception it is expected to end in, recorded rather than raised.
    """
    self._sent = []
    entry: Dict[str, Any] = {"call": call}
    result = None
    try:
      result = action()
      if inspect.isawaitable(result):
        result = await result
    except Exception as error:
      if raises is None or not isinstance(error, raises):
        raise
      result = None
      entry["error"] = _error(error)
    else:
      if raises is not None:
        raise AssertionError(f"{call} was expected to raise {raises.__name__}")
    entry["sent"] = self._sent
    entry["result"] = _jsonable(result)
    after = await self.snapshot(self.prep)
    entry.update(snapshot_changes(self._resources, after))
    self._resources = after
    self.steps.append(entry)
    return result

  def record(self) -> Dict[str, Any]:
    """Every step, and the resources the scenario ended with."""
    return {"steps": self.steps, "resources": self._resources}


async def _set_up(prep: PrepDevice) -> _Recording:
  """Set `prep` up, then record from there: the setup scenario records setup itself."""
  run = await _Recording.start(prep)
  await prep.setup()
  await run.forget()
  return run


async def _labware(prep: PrepDevice, model: str, name: str, spot: int) -> handles.Resource:
  """One of PLR's labware models, made in the device's store on one of its deck's spots."""
  parts = await prep.deck_parts()
  return await prep.store.create(model, name=name, parent=parts[spot])


async def _set_volumes(wells: List[handles.Resource], volume: float) -> None:
  for well in wells:
    assert isinstance(well, handles.Container)
    await well.set_volume(volume)


def _tip_definition(model: str, is_tool: bool = False) -> PrepCmd.TipDefinition:
  """What the firmware holds for a tip of one of PLR's models, picked up by hand."""
  tip = library.get_model(model).definition.attributes
  return PrepCmd.TipDefinition(
    default_values=False,
    id=255,
    volume=tip.tip.maximal_volume,
    length=tip.size.z - tip.head_tool.fitting_depth,
    tip_type=int(PrepCmd.TipTypes.StandardVolume),
    has_filter=tip.tip.has_filter,
    is_needle=False,
    is_tool=is_tool,
    label="Pipettor Custom",
  )


def _refuse(
  driver: PrepSimulationDriver,
  command: Union[Type[Any], Tuple[Type[Any], ...]],
  entries: Callable[[], str],
  times: int = 1,
) -> None:
  """Have the simulated device refuse the next `times` commands of type `command` (or of any of
  the types it gives) with `entries`.

  Each entry is `module.node.object:interface,action,result`, as the device sends them; several are
  joined by `;`.
  """
  answer = driver._answer
  left = [times]

  async def refusing(request: Any, path: str, method: str) -> Any:
    if isinstance(request, command) and left[0] > 0:
      left[0] -= 1
      raise _DeviceRefuses(entries())
    return await answer(request, path, method)

  driver._answer = refusing  # type: ignore[method-assign]


def _find_liquid(driver: PrepSimulationDriver, above_floor: float) -> None:
  """Have every capacitive Z search find liquid `above_floor` mm above the modelled cavity bottom.

  A search is sent to end 1 mm under that bottom. The model moves nowhere for it.
  """
  answer = driver._answer

  async def finding(request: Any, path: str, method: str) -> Any:
    if isinstance(request, PrepCmd.PrepZAxisSeekCapacitiveLld):
      return (
        PrepCmd.PrepZAxisSeekCapacitiveLld.Response(
          lld_detected=True, detect_position=request.position + 1.0 + above_floor
        ),
        "liquid found",
      )
    return await answer(request, path, method)

  driver._answer = finding  # type: ignore[method-assign]


def _device_holds(
  driver: PrepSimulationDriver,
  channels: List[int],
  definition: PrepCmd.TipDefinition,
  until: Type[Any],
  plate_until: Optional[Type[Any]] = None,
) -> None:
  """Have the simulated device sense something on `channels` that the model does not hold, as one
  left holding it by an earlier session does, until it is sent an `until` command.

  The simulator answers from the model alone, so this answers the sleeve sensors and the tip
  definition for it. With `plate_until`, it also records a plate gripped until that command.
  """
  answer = driver._answer
  held = [True, plate_until is not None]

  async def holding(request: Any, path: str, method: str) -> Any:
    if isinstance(request, until):
      held[0] = False
    if plate_until is not None and isinstance(request, plate_until):
      held[1] = False
    if held[0] and isinstance(request, PrepCmd.PrepProbeRequest) and method == "GetTipPresent":
      channel = driver.tree.channel_of(request.dest)
      return HoiParams().add(int(channel in channels), U32), "held from before"
    if held[0] and (
      isinstance(request, PrepCmd.PrepGetTipDefinitionHeld)
      or (isinstance(request, PrepCmd.PrepProbeRequest) and method == "GetTipDefinitionHeld")
    ):
      return HoiParams().add(definition, Struct()), "held from before"
    if held[1] and isinstance(request, PrepCmd.PrepGetPlateHeld):
      return PrepCmd.PrepGetPlateHeld.Response(value=True), "held from before"
    return await answer(request, path, method)

  driver._answer = holding  # type: ignore[method-assign]


def _channel_node(driver: PrepSimulationDriver, channel: int) -> int:
  """The firmware node a channel's Z drive answers from."""
  assert driver.pipettes is not None
  zdrive = driver.pipettes.channels[channel].zdrive
  assert zdrive is not None
  return zdrive.node


class PrepGoldenTests(unittest.TestCase):
  """Scenarios through a simulated Prep, each checked against its golden file."""

  def _check(self, name: str, scenario: Callable[[], Coroutine[Any, Any, Dict[str, Any]]]) -> None:
    check_golden(self, GOLDEN / f"{name}.json", asyncio.run(scenario()))

  # -- setup -----------------------------------------------------------------------------------

  def test_setup_and_stop(self):
    """Setup builds the arm, channels, head and heater shaker seat; a plate on the heater shaker's
    spot moves onto it. The deck components shift in software; stop parks."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      await _labware(prep, "cor_96_wellplate_360uL_Fb", "plate_on_hhs", 3)
      run = await _Recording.start(prep)
      await run.step("setup()", prep.setup)
      await run.step(
        "update_deck_components(Coordinate(1, 2, 0))",
        lambda: prep.update_deck_components(Coordinate(1, 2, 0)),
      )
      await run.step("stop()", prep.stop)
      return run.record()

    self._check("setup_and_stop", scenario)

  # -- pipetting channels: tips ----------------------------------------------------------------

  def test_channel_tips(self):
    """Tips move from spots to shafts and back, between spots, into the waste; an untracked spot
    hands out fresh tips; a channel that already carries one is refused."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      run = await _set_up(prep)
      p = prep.pipettes
      assert p is not None
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'B1'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A1", "B1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.pick_up_tips(tips['C1'], use_channels=[0])",
        lambda: p.pick_up_tips(tips["C1"], use_channels=[0]),
        raises=HasTipError,
      )
      await run.step("pipettes.return_tips()", lambda: p.return_tips())
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'H12'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A1", "H12"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.drop_tips(tips['H12', 'A1'], use_channels=[0, 1])",
        lambda: p.drop_tips(tips["H12", "A1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.pick_up_tips(tips['A2', 'B2'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A2", "B2"], use_channels=[0, 1]),
      )
      await run.step("pipettes.discard_tips()", lambda: p.discard_tips())
      await tips["D1"][0].set_tip_tracking(False)
      await run.step(
        "pipettes.pick_up_tips(tips['D1'], use_channels=[1]), D1 untracked",
        lambda: p.pick_up_tips(tips["D1"], use_channels=[1]),
      )
      await run.step(
        "pipettes.drop_tips(tips['D1'], use_channels=[1]), D1 untracked",
        lambda: p.drop_tips(tips["D1"], use_channels=[1]),
      )
      await run.step(
        "pipettes.pick_up_tips(tips['D1'], use_channels=[0]), D1 untracked",
        lambda: p.pick_up_tips(tips["D1"], use_channels=[0]),
      )
      waste_block = (await prep.deck_parts()).waste_block
      assert waste_block is not None
      await run.step(
        "pipettes.drop_tips([waste_block], use_channels=[0])",
        lambda: p.drop_tips([waste_block], use_channels=[0]),
      )
      return run.record()

    self._check("channel_tips", scenario)

  def test_channel_tip_failures(self):
    """A pick-up the device refuses on one channel mounts only the other's tip; a drop refused on
    one channel leaves its tip on; release_tips lets go of it where it stands."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      run = await _set_up(prep)
      driver = prep.driver
      assert isinstance(driver, PrepSimulationDriver)
      p = prep.pipettes
      assert p is not None
      # Channel 1's node answers 0x0F08, "a tip is not held".
      _refuse(
        driver,
        PrepCmd.PrepPickUpTips,
        lambda: f"0x0001.0x{_channel_node(driver, 1):04X}.0x0100:0x01,0x0009,0x0F08",
      )
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'B1'], use_channels=[0, 1]), channel 1 refused",
        lambda: p.pick_up_tips(tips["A1", "B1"], use_channels=[0, 1]),
        raises=ChannelizedError,
      )
      await run.step(
        "pipettes.pick_up_tips(tips['C1'], use_channels=[1])",
        lambda: p.pick_up_tips(tips["C1"], use_channels=[1]),
      )
      # The first entry answers for the first channel dropping: channel 0.
      _refuse(driver, PrepCmd.PrepDropTips, lambda: "0xE000.0x0001.0x1000:0x01,0x000C,0x0F03")
      await run.step(
        "pipettes.drop_tips(tips['A1', 'C1'], use_channels=[0, 1]), channel 0 refused",
        lambda: p.drop_tips(tips["A1", "C1"], use_channels=[0, 1]),
        raises=ChannelizedError,
      )
      await run.step("pipettes.release_tips()", lambda: p.release_tips())
      return run.record()

    self._check("channel_tip_failures", scenario)

  # -- pipetting channels: liquid --------------------------------------------------------------

  def test_channel_liquid(self):
    """Volumes move from wells to tips and on into other wells; an aspirate with a pre-mix books
    only what it draws; emptying a tip zeroes it."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      source = await _labware(prep, "cor_96_wellplate_360uL_Fb", "source", 0)
      assert isinstance(source, handles.Plate)
      target = await _labware(prep, "cor_96_wellplate_360uL_Fb", "target", 4)
      assert isinstance(target, handles.Plate)
      await _set_volumes(source["A1:B1"], 200.0)
      run = await _set_up(prep)
      p = prep.pipettes
      assert p is not None
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'B1'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A1", "B1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.aspirate(source['A1:B1'], volumes=[50, 30], use_channels=[0, 1])",
        lambda: p.aspirate(source["A1:B1"], volumes=[50.0, 30.0], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.dispense(target['A1', 'C1'], volumes=[20, 30], use_channels=[0, 1])",
        lambda: p.dispense(target["A1", "C1"], volumes=[20.0, 30.0], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.aspirate(source['A1'], volumes=[10], use_channels=[1], pre_mixes=[Mix(...)])",
        lambda: p.aspirate(
          source["A1"],
          volumes=[10.0],
          use_channels=[1],
          pre_mixes=[Mix(volume=20.0, repetitions=2, flow_rate=50.0)],
        ),
      )
      await run.step("pipettes.empty_tip(0)", lambda: p.empty_tip(0))
      await run.step("pipettes.empty_tips()", lambda: p.empty_tips())
      await run.step("pipettes.discard_tips()", lambda: p.discard_tips())
      return run.record()

    self._check("channel_liquid", scenario)

  def test_channel_liquid_failures(self):
    """An aspirate or dispense the device refuses on one channel books the other channel's volume
    only; one asking for more than a well has room for is refused before anything is sent."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      source = await _labware(prep, "cor_96_wellplate_360uL_Fb", "source", 0)
      assert isinstance(source, handles.Plate)
      target = await _labware(prep, "cor_96_wellplate_360uL_Fb", "target", 4)
      assert isinstance(target, handles.Plate)
      await _set_volumes(source["A1:B1"], 200.0)
      run = await _set_up(prep)
      driver = prep.driver
      assert isinstance(driver, PrepSimulationDriver)
      p = prep.pipettes
      assert p is not None
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'B1'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A1", "B1"], use_channels=[0, 1]),
      )
      # The first entry answers for the first channel aspirating: channel 0.
      _refuse(
        driver,
        tuple(Pipettes._ASPIRATE_CMD.values()),
        lambda: "0xE000.0x0001.0x1000:0x01,0x0019,0x0F43",
      )
      await run.step(
        "pipettes.aspirate(source['A1:B1'], volumes=[50, 30], use_channels=[0, 1]), channel 0 "
        "refused",
        lambda: p.aspirate(source["A1:B1"], volumes=[50.0, 30.0], use_channels=[0, 1]),
        raises=ChannelizedError,
      )
      await run.step(
        "pipettes.aspirate(source['A1'], volumes=[40], use_channels=[0])",
        lambda: p.aspirate(source["A1"], volumes=[40.0], use_channels=[0]),
      )
      _refuse(
        driver,
        tuple(Pipettes._DISPENSE_CMD.values()),
        lambda: "0xE000.0x0001.0x1000:0x01,0x001A,0x0F43",
      )
      await run.step(
        "pipettes.dispense(target['A1:B1'], volumes=[20, 10], use_channels=[0, 1]), channel 0 "
        "refused",
        lambda: p.dispense(target["A1:B1"], volumes=[20.0, 10.0], use_channels=[0, 1]),
        raises=ChannelizedError,
      )
      await run.step(
        "pipettes.dispense(target['A1'], volumes=[500], use_channels=[0])",
        lambda: p.dispense(target["A1"], volumes=[500.0], use_channels=[0]),
        raises=TooLittleVolumeError,
      )
      return run.record()

    self._check("channel_liquid_failures", scenario)

  def test_channel_measurements(self):
    """Probing heights and volumes reads them; a capacitive aspirate sets each well to the volume
    measured; a Z-touch without a tip reports what it met."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      source = await _labware(prep, "cor_96_wellplate_360uL_Fb", "source", 0)
      assert isinstance(source, handles.Plate)
      await _set_volumes(source["A1:B1"], 200.0)
      run = await _set_up(prep)
      c1_top = await source["C1"][0].get_location_wrt(prep.deck, "c", "c", "t")
      driver = prep.driver
      assert isinstance(driver, PrepSimulationDriver)
      p = prep.pipettes
      assert p is not None
      _find_liquid(driver, above_floor=5.0)
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'B1'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A1", "B1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.probe_liquid_heights(source['A1:B1'], use_channels=[0, 1])",
        lambda: p.probe_liquid_heights(source["A1:B1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.probe_liquid_volumes(source['A1:B1'], use_channels=[0, 1])",
        lambda: p.probe_liquid_volumes(source["A1:B1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.aspirate(source['A1:B1'], volumes=[20, 20], use_channels=[0, 1], "
        "lld_mode=CAPACITIVE)",
        lambda: p.aspirate(
          source["A1:B1"],
          volumes=[20.0, 20.0],
          use_channels=[0, 1],
          lld_mode=Pipettes.LLDMode.CAPACITIVE,
        ),
      )
      await run.step("pipettes.discard_tips()", lambda: p.discard_tips())
      await run.step(
        "pipettes.move_to_location(source['C1'] top, use_channels=0)",
        lambda: p.move_to_location(
          c1_top + Coordinate(0, 0, 20),
          use_channels=0,
        ),
      )
      await run.step(
        "pipettes.probe_z_using_ztouch(0, allow_without_tip=True)",
        lambda: p.probe_z_using_ztouch(0, allow_without_tip=True),
      )
      return run.record()

    self._check("channel_measurements", scenario)

  # -- moves -----------------------------------------------------------------------------------

  def test_moves(self):
    """Each move writes where the arm, the channels and the head stopped into the model."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      run = await _set_up(prep)
      p, arm, head = prep.pipettes, prep.x_arm, prep.head8
      assert p is not None and arm is not None and head is not None
      await run.step("x_arm.move_to_x_position(150)", lambda: arm.move_to_x_position(150.0))
      await run.step(
        "pipettes.move_to_xy_positions(120, {0: 250, 1: 200})",
        lambda: p.move_to_xy_positions(120.0, {0: 250.0, 1: 200.0}),
      )
      await run.step(
        "pipettes.move_tool_bottom_to_z_positions({0: 120, 1: 130})",
        lambda: p.move_tool_bottom_to_z_positions({0: 120.0, 1: 130.0}),
      )
      await run.step("pipettes.move_to_safe_z()", lambda: p.move_to_safe_z())
      await run.step(
        "pipettes.move_to_location([Coordinate(100, 300, 150), Coordinate(100, 150, 140)], [0, 1])",
        lambda: p.move_to_location(
          [Coordinate(100.0, 300.0, 150.0), Coordinate(100.0, 150.0, 140.0)], use_channels=[0, 1]
        ),
      )
      await run.step("pipettes.request_locations()", lambda: p.request_locations())
      await run.step(
        "head8.move_to_position(200, 150, 160)", lambda: head.move_to_position(200.0, 150.0, 160.0)
      )
      await run.step("head8.move_to_safe_z()", lambda: head.move_to_safe_z())
      await run.step("park_device()", lambda: prep.driver.park_device())
      return run.record()

    self._check("moves", scenario)

  # -- CoRe grippers ---------------------------------------------------------------------------

  def test_core_grippers(self):
    """The tools go onto the channels; a plate is carried to a spot, to a point on the deck, back
    where it came from, and let go of where it is held; the tools go back."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      plate = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "plate", 0)
      run = await _set_up(prep)
      parts = await prep.deck_parts()
      g = prep.core_grippers
      assert g is not None
      await run.step("core_grippers.pick_up_tools()", lambda: g.pick_up_tools())
      await run.step(
        "core_grippers.pick_up_resource(plate, pickup_distance_from_top=5)",
        lambda: g.pick_up_resource(plate, pickup_distance_from_top=5.0),
      )
      await run.step(
        "core_grippers.move_resource_to_xy_position(150, 250)",
        lambda: g.move_resource_to_xy_position(150.0, 250.0),
      )
      await run.step("core_grippers.place_resource(deck[5])", lambda: g.place_resource(parts[5]))
      await run.step(
        "core_grippers.pick_up_resource(plate, pickup_distance_from_top=5)",
        lambda: g.pick_up_resource(plate, pickup_distance_from_top=5.0),
      )
      await run.step(
        "core_grippers.place_resource(Coordinate(200, 150, 0))",
        lambda: g.place_resource(Coordinate(200.0, 150.0, 0.0)),
      )
      await run.step(
        "core_grippers.pick_up_resource(plate, pickup_distance_from_top=5)",
        lambda: g.pick_up_resource(plate, pickup_distance_from_top=5.0),
      )
      await run.step("core_grippers.return_resource()", lambda: g.return_resource())
      await run.step(
        "core_grippers.pick_up_resource(plate, pickup_distance_from_top=5)",
        lambda: g.pick_up_resource(plate, pickup_distance_from_top=5.0),
      )
      await run.step(
        "core_grippers.move_resource_to_xy_position(150, 250)",
        lambda: g.move_resource_to_xy_position(150.0, 250.0),
      )
      await run.step("core_grippers.release_plate()", lambda: g.release_plate())
      await run.step("core_grippers.return_tools()", lambda: g.return_tools())
      return run.record()

    self._check("core_grippers", scenario)

  def test_core_gripper_refusals(self):
    """move_resource mounts the tools, carries the plate and returns them; an occupied destination
    is refused before anything moves; a stop while holding a plate puts it back first."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      plate = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "plate", 0)
      await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "occupant", 4)
      run = await _set_up(prep)
      parts = await prep.deck_parts()
      g = prep.core_grippers
      assert g is not None
      await run.step(
        "core_grippers.move_resource(plate, deck[5], pickup_distance_from_top=5, "
        "return_grippers=True)",
        lambda: g.move_resource(
          plate, parts[5], pickup_distance_from_top=5.0, return_grippers=True
        ),
      )
      await run.step("core_grippers.pick_up_tools()", lambda: g.pick_up_tools())
      await run.step(
        "core_grippers.pick_up_resource(plate, pickup_distance_from_top=5)",
        lambda: g.pick_up_resource(plate, pickup_distance_from_top=5.0),
      )
      await run.step(
        "core_grippers.place_resource(deck[4]), deck[4] occupied",
        lambda: g.place_resource(parts[4]),
        raises=RuntimeError,
      )
      await run.step("stop()", prep.stop)
      return run.record()

    self._check("core_gripper_refusals", scenario)

  # -- 8-channel head --------------------------------------------------------------------------

  def test_head8(self):
    """A column of tips goes onto the head, liquid moves column to column and is mixed, the tips
    go back, and later columns go to the waste."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_50uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      source = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "source", 0)
      assert isinstance(source, handles.Plate)
      target = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "target", 4)
      assert isinstance(target, handles.Plate)
      await _set_volumes(source[0:8], 100.0)
      run = await _set_up(prep)
      parts = await prep.deck_parts()
      head = prep.head8
      assert head is not None
      await run.step("head8.pick_up_tips(tips.column(0))", lambda: head.pick_up_tips(tips[0:8]))
      await run.step(
        "head8.aspirate(source.column(0), volume=20, disable_volume_correction=True)",
        lambda: head.aspirate(source[0:8], volume=20.0, disable_volume_correction=True),
      )
      await run.step(
        "head8.dispense(target.column(0), volume=20, disable_volume_correction=True)",
        lambda: head.dispense(target[0:8], volume=20.0, disable_volume_correction=True),
      )
      await run.step(
        "head8.mix(target.column(0), Mix(volume=10, repetitions=2, flow_rate=40))",
        lambda: head.mix(target[0:8], Mix(volume=10.0, repetitions=2, flow_rate=40.0)),
      )
      await run.step("head8.return_tips()", lambda: head.return_tips())
      await run.step("head8.pick_up_tips(tips.column(1))", lambda: head.pick_up_tips(tips[8:16]))
      await run.step("head8.discard_tips()", lambda: head.discard_tips())
      await run.step("head8.pick_up_tips(tips.column(0))", lambda: head.pick_up_tips(tips[0:8]))
      await run.step(
        "head8.drop_tips([waste_mph] * 8)",
        lambda: head.drop_tips([parts.waste_positions["waste_mph"]] * 8),
      )
      return run.record()

    self._check("head8", scenario)

  def test_head8_failures(self):
    """A refused pick-up leaves every shaft empty; refused on probe 0, an aspirate and a dispense
    book the other probes; a refused drop leaves every tip on."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_50uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      source = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "source", 0)
      assert isinstance(source, handles.Plate)
      target = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "target", 4)
      assert isinstance(target, handles.Plate)
      await _set_volumes(source[0:8], 100.0)
      run = await _set_up(prep)
      driver = prep.driver
      assert isinstance(driver, PrepSimulationDriver)
      head = prep.head8
      assert head is not None
      # Each entry answers for the probe at its place: the first is probe 0.
      refusal = "0xE001.0x0001.0x1000:0x01,0x0001,0x0F43"
      _refuse(driver, PrepCmd.MphPickupTips, lambda: refusal)
      await run.step(
        "head8.pick_up_tips(tips.column(0)), refused",
        lambda: head.pick_up_tips(tips[0:8]),
        raises=HoiError,
      )
      await run.step("head8.pick_up_tips(tips.column(0))", lambda: head.pick_up_tips(tips[0:8]))
      _refuse(driver, tuple(Head8._ASPIRATE_CMD.values()), lambda: refusal)
      await run.step(
        "head8.aspirate(source.column(0), volume=20, disable_volume_correction=True), probe 0 "
        "refused",
        lambda: head.aspirate(source[0:8], volume=20.0, disable_volume_correction=True),
        raises=ChannelizedError,
      )
      await run.step(
        "head8.aspirate(source.column(0), volume=20, disable_volume_correction=True)",
        lambda: head.aspirate(source[0:8], volume=20.0, disable_volume_correction=True),
      )
      _refuse(driver, tuple(Head8._DISPENSE_CMD.values()), lambda: refusal)
      await run.step(
        "head8.dispense(target.column(0), volume=20, disable_volume_correction=True), probe 0 "
        "refused",
        lambda: head.dispense(target[0:8], volume=20.0, disable_volume_correction=True),
        raises=ChannelizedError,
      )
      _refuse(driver, PrepCmd.MphDropTips, lambda: refusal)
      await run.step(
        "head8.drop_tips(tips.column(0)), refused",
        lambda: head.drop_tips(tips[0:8]),
        raises=HoiError,
      )
      return run.record()

    self._check("head8_failures", scenario)

  # -- a session that finds the device holding something ----------------------------------------

  def test_setup_finds_tips_on(self):
    """A device that senses tips the model knows nothing of: setup takes them into the model as
    what the firmware describes and drops them into the waste."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      assert isinstance(prep.driver, PrepSimulationDriver)
      _device_holds(
        prep.driver,
        channels=[0, 1],
        definition=_tip_definition("hamilton_tip_300uL"),
        until=PrepCmd.PrepDropTips,
      )
      run = await _Recording.start(prep)
      await run.step("setup(), tips on both channels", prep.setup)
      return run.record()

    self._check("setup_finds_tips_on", scenario)

  def test_setup_finds_a_plate_held(self):
    """A device that reports the tools on and a plate gripped: setup takes the tools into the model
    and leaves them on; the plate is let go of, and the tools go back."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      driver = prep.driver
      assert isinstance(driver, PrepSimulationDriver)
      # It was set up and gripping before this session: it reports itself initialized.
      driver.initialized = True
      tool = PrepCmd.CO_RE_GRIPPER_TIP_PICKUP_PARAMETERS
      _device_holds(
        driver,
        channels=[0, 1],
        definition=PrepCmd.TipDefinition(
          default_values=False,
          id=255,
          volume=tool.volume,
          length=tool.length,
          tip_type=int(tool.tip_type),
          has_filter=tool.has_filter,
          is_needle=False,
          is_tool=True,
          label="Pipettor Custom",
        ),
        until=PrepCmd.PrepDropTool,
        plate_until=PrepCmd.PrepReleasePlate,
      )
      run = await _Recording.start(prep)
      await run.step("setup(), tools on, a plate gripped", prep.setup)
      g = prep.core_grippers
      assert g is not None
      await run.step("core_grippers.release_plate()", g.release_plate)
      await run.step("core_grippers.return_tools()", g.return_tools)
      return run.record()

    self._check("setup_finds_a_plate_held", scenario)

  def test_setup_with_a_tip_the_device_will_not_drop(self):
    """A device that refuses to drop a tip the model knows nothing of: the refusal arrives as a
    `ChannelizedError`, which the release over the waste is not tried for, so setup warns and
    finishes with the tip it took into the model still on the channel."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      driver = prep.driver
      assert isinstance(driver, PrepSimulationDriver)
      _device_holds(
        driver,
        channels=[0],
        definition=_tip_definition("hamilton_tip_300uL"),
        until=PrepCmd.PrepReleaseTips,
      )
      # The Pipettor forgets what it holds across a power cycle and refuses to drop it.
      _refuse(driver, PrepCmd.PrepDropTips, lambda: "0xE000.0x0001.0x1000:0x01,0x000C,0x0F03")
      run = await _Recording.start(prep)
      await run.step("setup(), a tip on channel 0 the device will not drop", prep.setup)
      return run.record()

    self._check("setup_with_a_tip_the_device_will_not_drop", scenario)

  def test_setup_without_head_or_heater_shaker(self):
    """A device with no 8-channel head and no heater shaker: setup builds the arm and the channels
    alone, and the heater shaker's spot stays a labware spot."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(
        simulation=True,
        declared_configuration_json=RECORDING_PREP,
        firmware_tree_json=FIRMWARE_TREE_V1_2_2,
      )
      await _labware(prep, "cor_96_wellplate_360uL_Fb", "plate", 3)
      run = await _Recording.start(prep)
      await run.step("setup()", prep.setup)
      await run.step("stop()", prep.stop)
      return run.record()

    self._check("setup_without_head_or_heater_shaker", scenario)

  # -- probing ---------------------------------------------------------------------------------

  def test_probes(self):
    """The calibration and edge probes move the channels and write where they stopped; probing every
    holder's edges and a plate with the grippers' Z-touch are refused out of the channels' reach."""

    async def scenario() -> Dict[str, Any]:
      prep = Prep(simulation=True)
      tips = await _labware(prep, "hamilton_96_tiprack_300uL_NTR", "tips", 1)
      assert isinstance(tips, handles.TipRack)
      plate = await _labware(prep, "cor_axy_96_wellplate_500uL_Ub", "plate", 4)
      run = await _set_up(prep)
      p, g = prep.pipettes, prep.core_grippers
      assert p is not None and g is not None
      await run.step(
        "pipettes.pick_up_tips(tips['A1', 'B1'], use_channels=[0, 1])",
        lambda: p.pick_up_tips(tips["A1", "B1"], use_channels=[0, 1]),
      )
      await run.step(
        "pipettes.probe_calibration_block_cct(0, n_replicates=1)",
        lambda: p.probe_calibration_block_cct(0, n_replicates=1),
      )
      await run.step(
        "pipettes.probe_deck_corner_z_offsets(1, n_replicates=1)",
        lambda: p.probe_deck_corner_z_offsets(1, n_replicates=1),
      )
      await run.step(
        "pipettes.probe_all_resourceholder_edges(0, n_replicates=1), the heater shaker's back "
        "edge out of reach",
        lambda: p.probe_all_resourceholder_edges(0, n_replicates=1),
        raises=ValueError,
      )
      await run.step("pipettes.discard_tips()", lambda: p.discard_tips())
      await run.step("core_grippers.pick_up_tools()", lambda: g.pick_up_tools())
      await run.step(
        "core_grippers.probe_resource_exists_using_ztouch(plate), its centre below the tools' "
        "reach",
        lambda: g.probe_resource_exists_using_ztouch(plate),
        raises=ValueError,
      )
      await run.step("core_grippers.return_tools()", lambda: g.return_tools())
      return run.record()

    self._check("probes", scenario)
