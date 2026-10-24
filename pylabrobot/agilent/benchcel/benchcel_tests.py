import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from pylabrobot.agilent.benchcel import (
  BenchCel4R,
  BenchCelLabwareSettings,
  PlateNotchSettings,
  Teachpoint,
  apply_benchcel_labware_settings,
  calculate_benchcel_labware_settings,
  calculate_robot_gripper_offset,
  calculate_sensor_offset,
  calculate_stacker_gripper_offset,
  calculate_stacking_thickness,
)
from pylabrobot.agilent.benchcel.benchcel import (
  BenchCelDeviceError,
  BenchCelProtocolError,
  Frame,
  parse_arm_pose_from_87_payload,
  parse_frame_from_buffer,
  parse_sensor_response,
  split_frames,
)
from pylabrobot.agilent.benchcel.stacks import benchcel_4r_stacks
from pylabrobot.resources import Coordinate
from pylabrobot.resources.store import ResourceStore, build, handles
from pylabrobot.resources.store.v1 import types_pb2 as pb

TEST_TEACHPOINT = Teachpoint(
  theta=89.99874114990234,
  x=-360.8802795410156,
  z=-10.0,
  approach_height=20.0,
  cavity_depth=0.0,
  gripper_open_limit=-1.5,
  respect_approach_height_when_not_holding_plate=True,
  something_above_this_point=False,
  teachpoint_id=0x1F,
  name="test",
)


class _FakeWriter:
  def __init__(self) -> None:
    self.sent = bytearray()
    self.closed = False

  def write(self, data: bytes) -> None:
    self.sent.extend(data)

  async def drain(self) -> None:
    return None

  def close(self) -> None:
    self.closed = True

  async def wait_closed(self) -> None:
    return None


class _FakeReader:
  def __init__(self, chunks: list[bytes]) -> None:
    self._chunks = list(chunks)

  async def read(self, num_bytes: int) -> bytes:
    if not self._chunks:
      return b""
    chunk = self._chunks.pop(0)
    if len(chunk) > num_bytes:
      self._chunks.insert(0, chunk[num_bytes:])
      return chunk[:num_bytes]
    return chunk


async def _make_backend(chunks: list[bytes]) -> tuple[BenchCel4R, _FakeWriter]:
  backend = BenchCel4R(name="benchcel", host="ignored", port=0, timeout=1.0, read_poll_timeout=0.01)
  await backend.create_resources()
  writer = _FakeWriter()
  backend.io._writer = writer  # type: ignore[assignment]
  backend.io._reader = _FakeReader(chunks)  # type: ignore[assignment]
  return backend, writer


async def _plate(
  store: ResourceStore, name: str, size_z: float, size_y: float = 85.48
) -> handles.Plate:
  """A plate with no wells, a root in `store`."""
  plate = await store.create(
    build.resource(
      name,
      Coordinate(127.76, size_y, size_z),
      kind=pb.RESOURCE_KIND_PLATE,
      type_name="Plate",
      plate=pb.PlateSpec(plate_type="skirted"),
      itemized=pb.ItemizedSpec(),
    ),
    name=name,
  )
  assert isinstance(plate, handles.Plate)
  return plate


async def _corning_plate(store: ResourceStore, name: str) -> handles.Plate:
  plate = await store.create("cor_96_wellplate_360uL_Fb", name=name)
  assert isinstance(plate, handles.Plate)
  return plate


def _sensor_payload(stacker_index: int = 2) -> bytes:
  return struct.pack(
    "<BB8H",
    stacker_index,
    0x08,
    45,
    1,
    0,
    240,
    128,
    241,
    0,
    1,
  )


class BenchCelFrameTests(unittest.TestCase):
  def test_frame_hex(self):
    self.assertEqual(Frame(0x48, b"\x01").hex(), "48010001")
    self.assertEqual(Frame(0x6A, b"\x01").hex(), "6a010001")

  def test_parse_frame_from_buffer_and_split(self):
    data = bytes.fromhex("6901004869010065")
    frames = split_frames(data)
    self.assertEqual(frames, [Frame(0x69, b"\x48"), Frame(0x69, b"\x65")])

    buffer = bytearray(bytes.fromhex("690100"))
    self.assertIsNone(parse_frame_from_buffer(buffer))
    buffer.extend(b"\x48")
    self.assertEqual(parse_frame_from_buffer(buffer), Frame(0x69, b"\x48"))
    self.assertEqual(buffer, bytearray())

  def test_split_frames_rejects_partial_trailer(self):
    with self.assertRaises(BenchCelProtocolError):
      split_frames(bytes.fromhex("69010048ff02"))


class BenchCelParserTests(unittest.TestCase):
  def test_parse_sensor_response(self):
    status = parse_sensor_response(Frame(0x7E, _sensor_payload(stacker_index=2)))
    self.assertEqual(status.stacker, 3)
    self.assertEqual(status.air_pressure, 45)
    self.assertEqual(status.plate_presence, 128)
    self.assertTrue(status.plate_present())
    self.assertEqual(status.notch_values(), (1, 0, 0, 1))

  def test_parse_arm_pose(self):
    payload = bytearray(66)
    struct.pack_into("<f", payload, 4, 12.5)
    struct.pack_into("<f", payload, 12, -34.25)
    struct.pack_into("<f", payload, 20, 99.0)
    struct.pack_into("<f", payload, 28, -1.0)
    pose = parse_arm_pose_from_87_payload(bytes(payload))
    self.assertAlmostEqual(pose.rotation.z, 12.5)
    self.assertAlmostEqual(pose.location.x, -34.25)
    self.assertAlmostEqual(pose.location.z, 99.0)
    self.assertAlmostEqual(pose.gripper_position, -1.0)


class BenchCelLabwareSettingsTests(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.store = ResourceStore.in_memory()

  async def asyncTearDown(self):
    await self.store.close()

  async def test_calculated_labware_maps_gripper_offset_to_pickup_location(self):
    plate = await _plate(self.store, "plate", size_z=10.4)
    settings = await calculate_benchcel_labware_settings(plate, name="low-profile")
    self.assertEqual(settings.name, "low-profile")
    self.assertAlmostEqual(settings.stacking_thickness, 8.9)
    self.assertAlmostEqual(settings.effective_plate_height(), 10.4)
    self.assertAlmostEqual(settings.robot_gripper_offset, 5.0)
    self.assertAlmostEqual(settings.robot_pickup_distance_from_top(), 5.4)
    self.assertAlmostEqual(settings.stacker_gripper_offset, 4.0)
    self.assertAlmostEqual(settings.sensor_offset, 7.0)

    returned = await apply_benchcel_labware_settings(plate, settings)
    self.assertEqual(returned, settings)
    self.assertEqual(await plate.get_preferred_pickup_location(), Coordinate(63.88, 42.74, 5.0))

  def test_calculation_helpers_match_observed_example_classes(self):
    self.assertAlmostEqual(calculate_stacking_thickness(14.6), 13.1)
    self.assertAlmostEqual(calculate_stacking_thickness(44.04), 42.54)
    self.assertAlmostEqual(calculate_stacking_thickness(10.4, nesting_overlap=1.3), 9.1)
    self.assertAlmostEqual(calculate_robot_gripper_offset(14.6), 8.0)
    self.assertAlmostEqual(calculate_robot_gripper_offset(10.4), 5.0)
    self.assertAlmostEqual(calculate_stacker_gripper_offset(10.4, 5.0), 4.0)
    self.assertAlmostEqual(calculate_stacker_gripper_offset(14.6, 8.0), 5.0)
    self.assertAlmostEqual(calculate_stacker_gripper_offset(44.04, 8.0), 6.0)
    self.assertAlmostEqual(calculate_sensor_offset(10.4), 7.0)
    self.assertAlmostEqual(calculate_sensor_offset(14.6), 8.0)
    self.assertAlmostEqual(calculate_sensor_offset(44.04), 40.04)

  async def test_stacking_thickness_estimated_from_height(self):
    plate = await _plate(self.store, "plate", size_z=14.6)
    settings = await calculate_benchcel_labware_settings(plate)
    self.assertAlmostEqual(settings.stacking_thickness, calculate_stacking_thickness(14.6))

  async def test_explicit_stacking_thickness_overrides_estimate(self):
    plate = await _plate(self.store, "plate", size_z=14.6)
    settings = await calculate_benchcel_labware_settings(plate, stacking_thickness=11.0)
    self.assertAlmostEqual(settings.stacking_thickness, 11.0)

  async def test_labware_profile_validates_plate_height(self):
    source = await _plate(self.store, "plate", size_z=10.4)
    settings = await calculate_benchcel_labware_settings(source)
    wrong_height = await _plate(self.store, "wrong_height", size_z=5.4)
    with self.assertRaisesRegex(ValueError, "expected 10.400 mm"):
      await settings.apply_to_plate(wrong_height)
    self.assertIsNone(await wrong_height.get_preferred_pickup_location())

  async def test_labware_settings_from_a_lidded_plate(self):
    plate = await _corning_plate(self.store, "lidded")
    settings = await BenchCelLabwareSettings.from_plate(plate)
    self.assertFalse(settings.can_be_lidded)
    self.assertEqual(settings.name, "cor_96_wellplate_360uL_Fb")
    lid = await self.store.create(
      build.resource(
        "lid", Coordinate(127.76, 85.48, 8), kind=pb.RESOURCE_KIND_LID, lid=pb.LidSpec()
      ),
      name="lid",
    )
    await plate.assign_child_resource(lid)
    self.assertTrue((await BenchCelLabwareSettings.from_plate(plate)).can_be_lidded)

  async def test_device_payload_matches_vworks_capture(self):
    # Greiner 781101 settings captured from VWorks (0x7d payload).
    settings = BenchCelLabwareSettings(
      name="781101",
      plate_size_x=127.76,
      plate_size_y=85.48,
      plate_size_z=14.4,
      stacking_thickness=12.76,
      robot_gripper_offset=8.0,
      stacker_gripper_offset=5.0,
      sensor_offset=8.0,
      gripper_open_position=-1.0,
      gripper_holding_plate_position=8.0,
      gripper_holding_stack_position=8.5,
      orientation_sensor_threshold=100,
      sensor_intensity=50,
      plate_presence_threshold=225,
      notch_settings=PlateNotchSettings(
        check_orientation=True,
        a1_notch=True,
        top_right_notch=False,
        bottom_left_notch=True,
        bottom_right_notch=False,
      ),
    )
    expected = (
      "f6284c41000000410000a040000000410100010064003200000080bf00000041000008410166"
      "66664100000000000000000000000000000000000000000000000000000000010000000000e100"
    )
    self.assertEqual(settings.to_device_payload().hex(), expected)
    self.assertEqual(len(settings.to_device_payload()), 77)

  async def test_device_payload_round_trip(self):
    plate = await _plate(self.store, "plate", size_z=14.4)
    settings = await calculate_benchcel_labware_settings(plate, name="rt")
    decoded = BenchCelLabwareSettings.from_device_payload(settings.to_device_payload())
    self.assertAlmostEqual(decoded.stacking_thickness, settings.stacking_thickness, places=3)
    self.assertAlmostEqual(decoded.plate_size_z, settings.plate_size_z, places=3)
    self.assertAlmostEqual(decoded.robot_gripper_offset, settings.robot_gripper_offset, places=3)
    self.assertEqual(decoded.plate_presence_threshold, settings.plate_presence_threshold)
    self.assertEqual(decoded.notch_settings.a1_notch, settings.notch_settings.a1_notch)

  async def test_benchcel_4r_stacks_are_lifo_resource_stacks(self):
    definitions = benchcel_4r_stacks()
    self.assertEqual(len(definitions), 4)
    self.assertTrue(all(d.attributes.stack.direction == pb.STACK_DIRECTION_Z for d in definitions))
    stacks = [
      await self.store.create(definition, name=definition.attributes.name)
      for definition in definitions
    ]
    self.assertTrue(all(isinstance(s, handles.ResourceStack) for s in stacks))
    stack = stacks[0]
    assert isinstance(stack, handles.ResourceStack)
    # Plates can be tracked on a stack (LIFO): the last one added is the accessible (top) plate.
    for name in ("p0", "p1"):
      await stack.assign_child_resource(await _plate(self.store, name, size_z=14.6))
    self.assertEqual(len(await stack.get_children()), 2)
    top = await stack.get_top_item()
    assert top is not None
    self.assertEqual(top.name, "p1")
    self.assertEqual(await top.get_location(), Coordinate(0, 0, 14.6))

  async def test_parse_labware_xml(self):
    xml = """<?xml version='1.0' encoding='ASCII'?>
<Velocity11 file='BenchCel ActiveX Settings'>
  <Labware>
    <Name>Example</Name>
    <StackingThickness>12.34</StackingThickness>
    <OrientationSensorThreshold>100</OrientationSensorThreshold>
    <PlatePresenceThreshold>225</PlatePresenceThreshold>
    <SensorIntensity>50</SensorIntensity>
    <ErrorCorrectionOffset>0.0</ErrorCorrectionOffset>
    <RobotGripperOffset>8.0</RobotGripperOffset>
    <StackerGripperOffset>5.0</StackerGripperOffset>
    <SensorOffset>8.0</SensorOffset>
    <GripperOpenPosition>-1.0</GripperOpenPosition>
    <GripperHoldingPlatePosition>8.0</GripperHoldingPlatePosition>
    <GripperHoldingStackPosition>8.5</GripperHoldingStackPosition>
    <PlateNotchesOrientationOptions>
      <CheckOrientation>Yes</CheckOrientation>
      <A1Notch>Yes</A1Notch>
      <TopRightNotch>No</TopRightNotch>
      <BottomLeftNotch>Yes</BottomLeftNotch>
      <BottomRightNotch>No</BottomRightNotch>
    </PlateNotchesOrientationOptions>
    <CanBeLidded>No</CanBeLidded>
    <CanBeSealed>No</CanBeSealed>
  </Labware>
  <StackSettings>
    <PlatePresenceThreshold>50</PlatePresenceThreshold>
    <RackPresenceThreshold>3</RackPresenceThreshold>
    <AdditionalReleaseHeight>2.0</AdditionalReleaseHeight>
    <LowPressureWarning>30</LowPressureWarning>
    <TiltMargin Enabled='No'>2.0</TiltMargin>
  </StackSettings>
</Velocity11>
"""
    with tempfile.TemporaryDirectory() as td:
      path = Path(td) / "example.xml"
      path.write_text(xml, encoding="ascii")
      settings = BenchCelLabwareSettings.from_xml_file(
        path,
        identifier="example",
        plate_size_x=127.76,
        plate_size_y=85.48,
        plate_size_z=14.4,
      )
    self.assertEqual(settings.identifier, "example")
    self.assertEqual(settings.name, "Example")
    self.assertAlmostEqual(settings.stacking_thickness, 12.34)
    self.assertEqual(settings.stack_plate_presence_threshold, 50)
    self.assertTrue(settings.notch_settings.a1_notch)


class BenchCelFactoryTests(unittest.IsolatedAsyncioTestCase):
  async def test_factory_creates_device_with_four_stacks(self):
    benchcel = BenchCel4R(name="bc", host="192.168.0.100")
    self.assertIsInstance(benchcel, BenchCel4R)
    self.assertEqual(benchcel.host, "192.168.0.100")
    with self.assertRaises(RuntimeError):
      benchcel.stacks  # noqa: B018
    await benchcel.create_resources()
    self.assertEqual(len(benchcel.stacks), 4)
    self.assertTrue(all(isinstance(s, handles.ResourceStack) for s in benchcel.stacks))
    self.assertEqual(benchcel.model, "Agilent BenchCel 4R")
    self.assertEqual((await benchcel.body.attributes()).model, "Agilent BenchCel 4R")
    self.assertEqual(
      [child.name for child in await benchcel.body.get_children()],
      ["bc_tray", "bc_stacker_1", "bc_stacker_2", "bc_stacker_3", "bc_stacker_4"],
    )

  async def test_setup_again_finds_the_resources(self):
    benchcel = BenchCel4R(name="bc", host="192.168.0.100")
    await benchcel.create_resources()
    again = BenchCel4R(name="bc", host="192.168.0.100", store=benchcel.store)
    await again.create_resources()
    self.assertEqual(again.body, benchcel.body)
    self.assertEqual(again.loading_tray, benchcel.loading_tray)
    self.assertEqual(again.stacks, benchcel.stacks)
    self.assertEqual(len(await benchcel.store.roots()), 1)

  async def test_get_resources_finds_but_never_makes(self):
    benchcel = BenchCel4R(name="bc", host="192.168.0.100")
    with self.assertRaises(LookupError):
      await benchcel.get_resources()
    await benchcel.create_resources()
    again = BenchCel4R(name="bc", host="192.168.0.100", store=benchcel.store)
    self.assertEqual(await again.get_resources(), benchcel.body)
    self.assertEqual(again.stacks, benchcel.stacks)

  async def test_factory_records_labware_settings(self):
    store = ResourceStore.in_memory()
    plate = await _plate(store, "plate", size_z=44.04, size_y=85.47)
    benchcel = BenchCel4R(name="bc", host="192.168.0.100", labware=plate, store=store)
    self.assertIsNone(benchcel.labware_settings)
    await benchcel.create_resources()
    assert benchcel.labware_settings is not None
    self.assertEqual(benchcel.labware_settings.name, "plate")
    # no stacking_z_height on the plate -> estimated pitch (44.04 - 1.5)
    self.assertAlmostEqual(benchcel.labware_settings.stacking_thickness, 42.54)


class BenchCelWireTests(unittest.IsolatedAsyncioTestCase):
  async def test_lower_level_home_command_writes_expected_frame(self):
    backend, writer = await _make_backend([b"\x69", b"\x01\x00\x48"])
    ack = await backend._send_home_command()
    self.assertEqual(writer.sent.hex(), "48010001")
    self.assertEqual(ack, Frame(0x69, b"\x48"))

  async def test_home_reconnects_and_confirms_status(self):
    backend, _ = await _make_backend([])
    backend._write_frame = AsyncMock()  # type: ignore[method-assign]
    backend._wait_for_command_ack = AsyncMock()  # type: ignore[method-assign]
    backend.io.stop = AsyncMock()  # type: ignore[method-assign]
    backend.io.setup = AsyncMock()  # type: ignore[method-assign]
    backend._read_until = AsyncMock(return_value=Frame(0x87))  # type: ignore[method-assign]

    await backend.home()

    first_frame = backend._write_frame.await_args_list[0].args[0]
    self.assertEqual(first_frame, Frame(0x47, b"\x01"))
    backend.io.stop.assert_awaited_once()
    backend.io.setup.assert_awaited_once()

  async def test_move_to_stacker_writes_expected_frame(self):
    backend, writer = await _make_backend([Frame(0x69, b"\x65").to_bytes()])
    await backend.move_to_stacker(backend.stacks[2])
    self.assertEqual(writer.sent.hex(), "650a0001020000204100000000")

  async def test_set_teachpoint_writes_captured_shape(self):
    backend, writer = await _make_backend([])
    await backend.set_teachpoint(TEST_TEACHPOINT)
    self.assertEqual(
      writer.sent.hex(),
      "731b001f5bffb342ad70b4c3000020c100010000a041000000000000c0bf",
    )

  async def test_device_error_raises(self):
    payload = b"X position out of bounds"
    frame = Frame(0x02, payload).to_bytes()
    backend, writer = await _make_backend([frame])
    with self.assertRaises(BenchCelDeviceError) as cm:
      await backend._move_x_relative(500)
    self.assertEqual(writer.sent.hex(), Frame(0x66, struct.pack("<Bf", 1, 500.0)).hex())
    self.assertEqual(cm.exception.message, "X position out of bounds")

  async def test_request_stacker_sensor_status(self):
    response = Frame(0x7E, _sensor_payload(stacker_index=2)).to_bytes()
    backend, writer = await _make_backend([response])
    status = await backend.request_stacker_sensor_status(backend.stacks[2])
    self.assertEqual(writer.sent.hex(), "7e010002")
    self.assertEqual(status.stacker, 3)
    self.assertEqual(status.plate_presence, 128)

  async def test_request_axis_limits(self):
    payload = struct.pack("<8f", -115.0, -360.9, -1.5, -1.5, 115.0, 360.9, 104.0, 11.0)
    backend, writer = await _make_backend([Frame(0x99, payload).to_bytes()])
    limits = await backend.request_axis_limits()
    self.assertEqual(writer.sent.hex(), "990000")
    self.assertAlmostEqual(limits["theta"][0], -115.0)
    self.assertAlmostEqual(limits["x"][1], 360.9, places=3)
    self.assertAlmostEqual(limits["gripper"][1], 11.0)

  async def test_open_and_close_stacker_clamps(self):
    backend, writer = await _make_backend(
      [
        Frame(0x69, b"\x67").to_bytes(),
        Frame(0x69, b"\x67").to_bytes(),
      ]
    )
    await backend.open_stacker_clamps(backend.stacks[0])
    await backend.close_stacker_clamps(backend.stacks[0])
    self.assertEqual(writer.sent.hex(), "67020000016702000000")

  async def test_stacker_primitives_match_vworks_captures(self):
    # Wire bytes confirmed against VWorks packet captures of the Downstack,
    # Upstack, Load, and Unload buttons on stacker 3 (zero-based index 0x02):
    #   Downstack -> 0x62  01 02 00 01            ACK 0x69 62
    #   Upstack   -> 0x63  01 02 00 01            ACK 0x69 63
    #   Load      -> 0x60  01 02                  ACK 0x69 60 02
    #   Unload    -> 0x61  01 02 00 00 00 00      ACK 0x69 61 02
    backend, writer = await _make_backend(
      [
        Frame(0x69, b"\x62").to_bytes(),
        Frame(0x69, b"\x63").to_bytes(),
        Frame(0x69, b"\x60\x02").to_bytes(),
        Frame(0x69, b"\x61\x02").to_bytes(),
      ]
    )
    await backend._pick_from_stacker(3)
    await backend._place_on_stacker(3)
    await backend._load_stacker(3)
    await backend._unload_stacker(3)
    self.assertEqual(
      writer.sent.hex(),
      "62040001020001"  # downstack stacker 3
      "63040001020001"  # upstack stacker 3
      "6002000102"  # load stacker 3
      "610600010200000000",  # unload stacker 3
    )


class BenchCelStackerMappingTests(unittest.IsolatedAsyncioTestCase):
  async def test_transfers_require_a_configured_teachpoint(self):
    # No loading_tray_teachpoint_id.
    backend = BenchCel4R(name="benchcel", host="ignored", stacks=benchcel_4r_stacks())
    await backend.create_resources()
    stacks = backend.stacks
    self.assertIsNone(backend.loading_tray_teachpoint_id)

    with self.assertRaisesRegex(ValueError, "teachpoint"):
      await backend.downstack(stacks[0])
    with self.assertRaisesRegex(ValueError, "teachpoint"):
      await backend.upstack(stacks[0])

  async def test_downstack_maps_stack_to_stacker(self):
    backend = BenchCel4R(
      name="benchcel",
      host="ignored",
      stacks=benchcel_4r_stacks(),
      loading_tray_teachpoint_id=0x1E,
    )
    await backend.create_resources()
    stacks = backend.stacks
    plate = await _corning_plate(backend.store, "plate")
    await stacks[2].assign_child_resource(plate)

    sent: list[Frame] = []

    async def fake_send(frame: Frame, **kwargs) -> Frame:
      sent.append(frame)
      return Frame(0x69, kwargs.get("ack_payload") or bytes([frame.command_id]))

    backend._send_frame_expect_ack_no_lock = fake_send  # type: ignore[method-assign]
    # stacks[2] is human stacker 3 (zero-based index 0x02)
    returned = await backend.downstack(stacks[2])

    self.assertEqual(
      [f.hex() for f in sent],
      ["6a010001", "62040001020001", "630400011e0001"],
    )
    self.assertEqual(returned, plate)
    self.assertEqual(await backend.loading_tray.get_resource_held(), plate)
    self.assertNotIn(plate, await stacks[2].get_children())

  async def test_upstack_maps_stack_to_stacker(self):
    backend = BenchCel4R(
      name="benchcel",
      host="ignored",
      stacks=benchcel_4r_stacks(),
      loading_tray_teachpoint_id=0x1E,
    )
    await backend.create_resources()
    stacks = backend.stacks
    plate = await _corning_plate(backend.store, "plate")
    await backend.loading_tray.assign_child_resource(plate)

    sent: list[Frame] = []

    async def fake_send(frame: Frame, **kwargs) -> Frame:
      sent.append(frame)
      return Frame(0x69, kwargs.get("ack_payload") or bytes([frame.command_id]))

    backend._send_frame_expect_ack_no_lock = fake_send  # type: ignore[method-assign]
    # stacks[0] is human stacker 1 (zero-based index 0x00)
    await backend.upstack(stacks[0])

    self.assertEqual(
      [f.hex() for f in sent],
      ["6a010001", "620400011e0001", "63040001000001"],
    )
    self.assertIsNone(await backend.loading_tray.get_resource_held())
    self.assertEqual(await stacks[0].get_top_item(), plate)

  async def test_transfer_rejects_foreign_stack_with_same_name(self):
    backend = BenchCel4R(name="benchcel", host="ignored", loading_tray_teachpoint_id=0x1E)
    await backend.create_resources()
    foreign_stack = await backend.store.create(
      benchcel_4r_stacks(name_prefix="benchcel_stacker")[0], name=backend.stacks[0].name
    )
    assert isinstance(foreign_stack, handles.ResourceStack)

    with self.assertRaisesRegex(ValueError, "not configured"):
      await backend.downstack(foreign_stack)

  async def test_move_plate_between_stacks_updates_resource_state(self):
    backend = BenchCel4R(name="benchcel", host="ignored", stacks=benchcel_4r_stacks())
    await backend.create_resources()
    stacks = backend.stacks
    plate = await _corning_plate(backend.store, "plate")
    await stacks[0].assign_child_resource(plate)
    sent: list[Frame] = []

    async def fake_send(frame: Frame, **kwargs) -> Frame:
      sent.append(frame)
      return Frame(0x69, kwargs.get("ack_payload") or bytes([frame.command_id]))

    backend._send_frame_expect_ack_no_lock = fake_send  # type: ignore[method-assign]

    returned = await backend.move_plate_between_stacks(stacks[0], stacks[3])

    self.assertEqual(returned, plate)
    self.assertNotIn(plate, await stacks[0].get_children())
    self.assertEqual(await stacks[3].get_top_item(), plate)
    self.assertEqual(
      [frame.hex() for frame in sent],
      ["6a010001", "62040001000001", "63040001030001"],
    )


if __name__ == "__main__":
  unittest.main()
