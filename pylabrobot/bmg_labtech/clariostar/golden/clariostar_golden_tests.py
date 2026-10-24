"""Golden records of what a CLARIOstar Plus does: every frame it writes, step by step, and its own
resource tree (the reader, its plate holder and the plate in it).

The reader is the real driver over a fake FTDI link that answers each write with the next queued
reply; the replies are frames recorded from a CLARIOstar Plus. Each scenario sets up the reader,
moves the drawer and the plate, and reads.
"""

import pathlib
import unittest
from typing import Any, Callable, Dict, List, Optional, Sequence

from pylabrobot.bmg_labtech.clariostar.device import CLARIOstarDevice
from pylabrobot.bmg_labtech.clariostar.driver.features.absorbance_tests import (
  COLUMN_1_DATA_REPLY,
  RUN_REPLY,
  STATUS_MEASURED,
  STATUS_MEASURING,
  VERIFICATION_DATA_REPLY,
)
from pylabrobot.bmg_labtech.clariostar.driver.features.drawer_tests import (
  CLOSE_DRAWER_REPLY,
  OPEN_DRAWER_REPLY,
)
from pylabrobot.bmg_labtech.clariostar.driver.features.fluorescence_tests import (
  BASELINE,
  TEMPERATURE_37_DATA_REPLY,
  load_z_profile_ground_truth,
)
from pylabrobot.bmg_labtech.clariostar.driver.features.luminescence_tests import (
  LUMINESCENCE_DATA_REPLY,
)
from pylabrobot.bmg_labtech.clariostar.driver.features.temperature_controller_tests import (
  MONITOR_REPLY,
)
from pylabrobot.bmg_labtech.clariostar.driver.framing import (
  ftdi_extract_payload,
  ftdi_wrap_payload,
)
from pylabrobot.bmg_labtech.clariostar.driver.master_tests import (
  FIRMWARE_INFO_REPLY,
  INIT_REPLY,
  PARAMETERS_REPLY,
  STATUS_DRAWER_OPEN,
  STATUS_IDLE,
  STATUS_PLATE_DETECTED,
  FakeFTDI,
  load_session_replies,
)
from pylabrobot.lib.absorbance.results import grid_of
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import handles
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import check_golden, snapshot_store

GOLDEN = pathlib.Path(__file__).parent

# The replies, in order, to each command the scenarios send.
SETUP_REPLIES = [
  INIT_REPLY,
  STATUS_IDLE,  # INIT done
  STATUS_IDLE,  # motors on
  STATUS_IDLE,
  PARAMETERS_REPLY,
  STATUS_IDLE,
  FIRMWARE_INFO_REPLY,
  STATUS_IDLE,  # temperature sensors off
  STATUS_IDLE,
  MONITOR_REPLY,
]
OPEN_REPLIES = [STATUS_IDLE, OPEN_DRAWER_REPLY, STATUS_DRAWER_OPEN, STATUS_DRAWER_OPEN]
CLOSE_REPLIES = [STATUS_DRAWER_OPEN, CLOSE_DRAWER_REPLY, STATUS_IDLE, STATUS_IDLE]
# Stop with the drawer in and no plate: no run, sensors off, drawer in, no plate.
STOP_REPLIES = [STATUS_IDLE, STATUS_IDLE, STATUS_IDLE, STATUS_IDLE]
# Stop with the drawer in and a plate in the reader: the drawer opens for it.
STOP_WITH_PLATE_REPLIES = [STATUS_IDLE, STATUS_IDLE, STATUS_IDLE, STATUS_PLATE_DETECTED]
STOP_WITH_PLATE_REPLIES += OPEN_REPLIES

# Where the scenarios put the drawer: made up, the real locations are not measured.
LOCATION_IN = Coordinate(10, 20, 30)
LOCATION_OUT = Coordinate(10, -200, 30)


def run_replies(data: bytes) -> List[bytes]:
  """The replies to a read answered by `data`: idle, the RUN, measuring, measured, the data."""
  return [STATUS_IDLE, RUN_REPLY, STATUS_MEASURING, STATUS_MEASURED, data]


def luminescence_reply(wells: int) -> bytes:
  """The ground truth's luminescence reply cut to its first `wells` counts.

  Not a reader's reply: none of a partial plate is recorded. The count fields (bytes 7-8, 9-10 and
  18-19) are set to `wells`, the counts after them dropped, and the frame checksummed again.
  """
  payload = bytearray(ftdi_extract_payload(LUMINESCENCE_DATA_REPLY))
  for offset in (7, 9, 18):
    payload[offset : offset + 2] = wells.to_bytes(2, "big")
  end_of_counts = 34 + 4 * 96
  payload = payload[: 34 + 4 * wells] + payload[end_of_counts:]
  return ftdi_wrap_payload(bytes(payload))


class Recorder(recording.Recorder):
  """Runs a scenario's steps against a CLARIOstar Plus over a fake link and records each step:
  the frames written, as hex, what the call returned or raised, and the reader's tree when the
  step changed it."""

  def __init__(self) -> None:
    super().__init__()
    self.io = FakeFTDI(chunk=4096)
    # As `CLARIOstarPlus` builds it; its body is put in its store at `start`.
    self.reader = CLARIOstarDevice(name="reader", io=self.io, model="CLARIOstarPlus")
    driver = self.reader.driver
    # No waits: the replies are queued.
    driver._PACKET_READ_TIMEOUT = 0.01
    driver._FRAME_STALL_TIMEOUT = 0.05
    driver._RETRY_SETTLE = 0
    driver.default_poll_interval = 0
    driver.drawer.default_poll_interval = 0
    self.store = self.reader.store

  async def start(self) -> None:
    """Put the reader in its store: its tree before the first step."""
    await self.reader.create_resources()
    await self.mark()

  async def snapshot(self) -> List[Dict[str, Any]]:
    """The reader's tree, read from its store."""
    return await snapshot_store(self.store, self.reader.body)

  async def plate(self, name: str) -> handles.Plate:
    """A Corning 96-well 360 uL flat-bottom plate in the reader's store."""
    plate = await self.store.create("cor_96_wellplate_360uL_Fb", name)
    assert isinstance(plate, handles.Plate)
    return plate

  def take_sent(self) -> List[Any]:
    """The frames written since the last call, as hex."""
    written, self.io.written = self.io.written, []
    return [frame.hex() for frame in written]

  async def annotate(self, entry: Dict[str, Any]) -> None:
    entry["unanswered_replies"] = len(self.io.replies)
    resources = await self.changed()
    if resources is not None:
      entry["resources"] = resources

  async def step(  # type: ignore[override]
    self,
    call: str,
    action: recording.Action,
    replies: Sequence[bytes] = (),
    result: Optional[Callable[[Any], Any]] = None,
  ) -> Any:
    """Run `action` with `replies` queued; record it as `call`. `result` makes what it returned
    JSON-able; by default its fields are recorded."""
    self.io.replies = list(replies)
    return await super().step(call, action, result)

  async def check(self, test: unittest.TestCase, scenario: str) -> None:
    """Compare the record with the scenario's golden file."""
    record = {"steps": self.steps, "resources": await self.snapshot()}
    check_golden(test, GOLDEN / f"{scenario}.json", record)

  async def setup_with_plate(self, plate: handles.Plate) -> None:
    """Set up, open the drawer, put `plate` in the plate holder and close the drawer."""
    reader = self.reader
    await self.step("setup()", reader.setup, SETUP_REPLIES)
    await self.step("drawer.open()", reader.drawer.open, OPEN_REPLIES)
    await self.step(
      "plate_holder.assign_child_resource(plate)",
      lambda: reader.plate_holder.assign_child_resource(plate),
    )
    await self.step("drawer.close()", reader.drawer.close, CLOSE_REPLIES)


class CLARIOstarGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_drawer_and_plate(self):
    """The plate goes on or comes off only while the drawer is sensed open; the drawer moves the
    plate holder once its locations are set; stop opens the drawer for a plate left in."""
    recorder = Recorder()
    await recorder.start()
    reader = recorder.reader
    plate = await recorder.plate("plate")
    other = await recorder.plate("other")
    await recorder.step("setup()", reader.setup, SETUP_REPLIES)
    await recorder.step(
      "plate_holder.assign_child_resource(plate)  # drawer not sensed",
      lambda: reader.plate_holder.assign_child_resource(plate),
    )
    await recorder.step(
      "reader.assign_child_resource(plate)",
      lambda: reader.assign_child_resource(plate, location=Coordinate.zero()),
    )
    await recorder.step("drawer.open()  # no locations", reader.drawer.open, OPEN_REPLIES)
    await recorder.step(
      "plate_holder.assign_child_resource(plate)",
      lambda: reader.plate_holder.assign_child_resource(plate),
    )
    await recorder.step(
      "plate_holder.assign_child_resource(other)  # holder full",
      lambda: reader.plate_holder.assign_child_resource(other),
    )
    await recorder.step("drawer.close()", reader.drawer.close, CLOSE_REPLIES)
    await recorder.step(
      "plate_holder.unassign_child_resource(plate)  # drawer closed",
      lambda: reader.plate_holder.unassign_child_resource(plate),
    )

    def set_locations() -> None:
      reader.drawer.location_in = LOCATION_IN
      reader.drawer.location_out = LOCATION_OUT

    await recorder.step("drawer.location_in, drawer.location_out = IN, OUT", set_locations)
    await recorder.step(
      "drawer.sense_drawer_open()", reader.drawer.sense_drawer_open, [STATUS_IDLE]
    )
    await recorder.step("drawer.open()", reader.drawer.open, OPEN_REPLIES)
    await recorder.step(
      "plate_holder.unassign_child_resource(plate)",
      lambda: reader.plate_holder.unassign_child_resource(plate),
    )
    await recorder.step("drawer.close()", reader.drawer.close, CLOSE_REPLIES)
    await recorder.step("stop()", reader.stop, STOP_REPLIES)
    await recorder.check(self, "drawer_and_plate")

  async def test_stop_with_a_plate_left_in(self):
    """Stop refuses with a plate in the reader and opens the drawer for it."""
    recorder = Recorder()
    await recorder.start()
    reader = recorder.reader
    reader.drawer.location_in = LOCATION_IN
    reader.drawer.location_out = LOCATION_OUT
    await recorder.setup_with_plate(await recorder.plate("plate"))
    await recorder.step("stop()", reader.stop, STOP_WITH_PLATE_REPLIES)
    await recorder.check(self, "stop_with_a_plate_left_in")

  async def test_absorbance(self):
    """Absorbance of the whole plate and of column 1, a spectrum of column 1, and a grid."""
    recorder = Recorder()
    await recorder.start()
    reader = recorder.reader
    plate = await recorder.plate("plate")
    await recorder.setup_with_plate(plate)
    absorbance = reader.absorbance
    assert absorbance is not None
    results = await recorder.step(
      "absorbance.measure(wavelengths=[600])",
      lambda: absorbance.measure(wavelengths=[600]),
      run_replies(VERIFICATION_DATA_REPLY),
    )
    await recorder.step(
      "get_grid(plate, results[0].data)",
      lambda: grid_of(
        plate.name, plate.num_items_x, plate.num_items_y, plate.identifiers, results[0].data
      ),
    )
    await recorder.step(
      "absorbance.measure(wells=plate['A1:H1'], wavelengths=[600])",
      lambda: absorbance.measure(wells=plate["A1:H1"], wavelengths=[600]),
      run_replies(COLUMN_1_DATA_REPLY),
    )
    session = load_session_replies()
    await recorder.step(
      "absorbance.measure_spectrum(wells=plate['A1:H1'], 300, 700, 1)",
      lambda: absorbance.measure_spectrum(
        wells=plate["A1:H1"], start_wavelength=300, end_wavelength=700, step_size=1
      ),
      run_replies(bytes.fromhex(session["absorbance_spectrum_page"])),
    )
    await recorder.step("drawer.open()", reader.drawer.open, OPEN_REPLIES)
    await recorder.step(
      "plate_holder.unassign_child_resource(plate)",
      lambda: reader.plate_holder.unassign_child_resource(plate),
    )
    await recorder.step(
      "absorbance.measure(wavelengths=[600])  # no plate",
      lambda: absorbance.measure(wavelengths=[600]),
    )
    await recorder.check(self, "absorbance")

  async def test_fluorescence(self):
    """Fluorescence of the whole plate and of column 1, at the default focal height from the
    wells, and a z-profile of A1."""
    recorder = Recorder()
    await recorder.start()
    reader = recorder.reader
    plate = await recorder.plate("plate")
    await recorder.setup_with_plate(plate)
    fluorescence = reader.fluorescence
    assert fluorescence is not None
    await recorder.step(
      "fluorescence.measure(485/528, gain=1000)",
      lambda: fluorescence.measure(BASELINE, gain=1000),
      run_replies(TEMPERATURE_37_DATA_REPLY),
    )
    session = load_session_replies()
    await recorder.step(
      "fluorescence.measure(485/528, gain=1000, wells=plate['A1:H1'])",
      lambda: fluorescence.measure(BASELINE, gain=1000, wells=plate["A1:H1"]),
      run_replies(bytes.fromhex(session["fluorescence_column_1_reply"])),
    )
    z_profile = load_z_profile_ground_truth()["z_profile_without_target"]
    await recorder.step(
      "fluorescence.measure_z_profile(485/528, well=plate['A1'])",
      lambda: fluorescence.measure_z_profile(BASELINE, well=plate.get_well("A1")),
      [bytes.fromhex(reply) for reply in z_profile["replies"]],
    )
    await recorder.check(self, "fluorescence")

  async def test_luminescence(self):
    """Luminescence of the whole plate and of column 1, at the default focal height from the
    wells."""
    recorder = Recorder()
    await recorder.start()
    reader = recorder.reader
    plate = await recorder.plate("plate")
    await recorder.setup_with_plate(plate)
    luminescence = reader.luminescence
    assert luminescence is not None
    await recorder.step(
      "luminescence.measure()",
      luminescence.measure,
      run_replies(LUMINESCENCE_DATA_REPLY),
    )
    await recorder.step(
      "luminescence.measure(wells=plate['A1:H1'])",
      lambda: luminescence.measure(wells=plate["A1:H1"]),
      run_replies(luminescence_reply(8)),
    )
    await recorder.check(self, "luminescence")


if __name__ == "__main__":
  unittest.main()
