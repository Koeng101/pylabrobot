"""Tests for custom Opentrons labware definition building and uploading.

Builder-level tests pin the definition content produced from PLR geometry
(dimensions, well positions and shapes, the shared front-left slot anchoring,
grip height). Flex-level tests drive ``Flex._ensure_labware_loaded``
with an injected ``AsyncMock`` and assert labware without an
official Opentrons definition is uploaded and then loaded by the uploaded
definition's namespace/loadName/version, that the run-scoped caches reset
with the run, and that official-name labware keeps loading with zero uploads.
"""

import unittest
import uuid
from typing import Any, Optional, Tuple, cast
from unittest.mock import AsyncMock, patch

from pylabrobot.opentrons.flex.errors import OpentronsCommandError, OpentronsError
from pylabrobot.opentrons.flex.flex import Flex
from pylabrobot.opentrons.flex.flex_head import FlexHead8
from pylabrobot.opentrons.decks import assign_child_at_slot, get_slot
from pylabrobot.opentrons.flex.tests.mock_utils import make_api, make_deck, make_flex, place
from pylabrobot.opentrons.labware import (
  build_container_definition,
  build_movable_labware_definition,
  build_plate_definition,
  build_tip_rack_definition,
  read_labware,
)
from pylabrobot.opentrons.model import LabwareFacts
from pylabrobot.opentrons.types import CommandInfo
from pylabrobot.resources import (
  Container,
  CrossSectionType,
  Plate,
  Resource,
  ResourceHolder,
  TipRack,
  TipSpot,
  Trough,
  TroughBottomType,
  TubeRack,
  Well,
  WellBottomType,
)
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.store import handles, library
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.definitions import definition_from_resource
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.resources.tip import Tip
from pylabrobot.resources.utils import create_ordered_items_2d


def _plate(
  name: str = "Black Plate-1",
  num_items_x: int = 2,
  num_items_y: int = 2,
  cross_section_type: CrossSectionType = CrossSectionType.CIRCLE,
  bottom_type: WellBottomType = WellBottomType.UNKNOWN,
  material_z_thickness: Optional[float] = 0.5,
) -> Plate:
  """A plate with hand-picked geometry so expected numbers are exact.

  ``material_z_thickness`` is the wall between a well's own bottom and the
  cavity floor liquid ops are anchored at; ``None`` builds the wells without
  one, which is the shape the builder refuses.
  """
  return Plate(
    name=name,
    size_x=127.0,
    size_y=80.0,
    size_z=14.0,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=num_items_x,
      num_items_y=num_items_y,
      dx=10.0,
      dy=8.0,
      dz=1.0,
      item_dx=9.0,
      item_dy=9.0,
      size_x=6.0,
      size_y=6.0,
      size_z=10.0,
      material_z_thickness=material_z_thickness,
      max_volume=360.0,
      cross_section_type=cross_section_type,
      bottom_type=bottom_type,
    ),
  )


def _tip_rack(
  name: str = "hamilton tips 300",
  num_items_x: int = 2,
  num_items_y: int = 2,
  dz: float = 0.0,
) -> TipRack:
  """A tip rack with hand-picked geometry and a pinned prototype tip.

  ``dz`` is where the seated tips' ends sit relative to the rack's own base;
  a negative one models the Hamilton-style racks whose tips hang below it.
  """

  def make_tip(name: str) -> Tip:
    return Tip(
      has_filter=False,
      diameter=5.0,
      size_z=50.0,
      maximal_volume=200.0,
      fitting_depth=8.0,
      name=name,
    )

  return TipRack(
    name=name,
    size_x=120.0,
    size_y=82.0,
    size_z=90.0,
    ordered_items=create_ordered_items_2d(
      TipSpot,
      num_items_x=num_items_x,
      num_items_y=num_items_y,
      dx=10.0,
      dy=8.0,
      dz=dz,
      item_dx=9.0,
      item_dy=9.0,
      size_x=5.0,
      size_y=5.0,
      make_tip=make_tip,
    ),
  )


def _trough(
  name: str = "hamilton trough",
  material_z_thickness: Optional[float] = 1.5,
  bottom_type: TroughBottomType = TroughBottomType.UNKNOWN,
) -> Trough:
  """A single-cavity trough; ``material_z_thickness`` is its floor thickness."""
  return Trough(
    name=name,
    size_x=120.0,
    size_y=80.0,
    size_z=40.0,
    material_z_thickness=material_z_thickness,
    bottom_type=bottom_type,
    max_volume=290000.0,
  )


def _tube_rack(name: str = "tube rack") -> TubeRack:
  """A 12x8 tube rack: deck-assignable and column-shaped, but not pipettable.

  The rack's holders are not wells, so no well-bearing definition can be
  built from it -- the mainstream labware type that reaches the unbuildable
  path through a pipetting op.
  """
  return TubeRack(
    name=name,
    size_x=127.0,
    size_y=86.0,
    size_z=45.0,
    ordered_items=create_ordered_items_2d(
      ResourceHolder,
      num_items_x=12,
      num_items_y=8,
      dx=10.0,
      dy=8.0,
      dz=0.0,
      item_dx=9.0,
      item_dy=9.0,
      size_x=8.0,
      size_y=8.0,
      size_z=40.0,
    ),
  )


def _definition(resource: Resource) -> pb.ResourceDefinition:
  """The store definition of a PLR resource built here for its hand-picked geometry."""
  return definition_from_resource(resource)


async def _facts(source: Any, name: Optional[str] = None) -> LabwareFacts:
  """A labware as a command reads it, made alone in a fresh store.

  `source` is a model name or a PLR resource; `name` picks a resource inside it.
  """
  store = ResourceStore.in_memory()
  if isinstance(source, str):
    definition = None
    root_name = source
  else:
    definition = _definition(source)
    root_name = source.name
  if definition is not None:
    if not definition.attributes.HasField("location"):
      definition.attributes.location.CopyFrom(pb.Vec3())
    root = await store.create(definition, name=root_name)
  else:
    model = library.get_model(source).definition
    model.attributes.location.CopyFrom(pb.Vec3())
    root = await store.create(model, name="labware")
  target = root if name is None else await store.get(name, root=root)
  return await read_labware(store, target)


class TestDefinitionLoadNames(unittest.IsolatedAsyncioTestCase):
  """Generated definitions have unique identities and readable display names."""

  async def test_same_named_resources_get_distinct_uuid_load_names(self):
    plate = await _facts(_plate(name="Shared name"))
    trough = await _facts(_trough(name="Shared name"))
    stub = await _facts(Resource("Shared name", 100, 90, 20))
    tips = await _facts(_tip_rack(name="Shared name"))
    for kind, build in (
      ("plate", lambda: build_plate_definition(plate)),
      ("container", lambda: build_container_definition(trough)),
      ("stub", lambda: build_movable_labware_definition(stub)),
      ("OT-2 tips", lambda: build_tip_rack_definition(tips)),
      ("Flex tips", lambda: build_tip_rack_definition(tips, for_flex=True)),
    ):
      with self.subTest(kind=kind):
        first = build()
        second = build()
        self.assertNotEqual(first["parameters"]["loadName"], second["parameters"]["loadName"])
        for definition in (first, second):
          load_name = definition["parameters"]["loadName"]
          self.assertEqual(uuid.UUID(load_name).version, 4)
          self.assertEqual(uuid.UUID(load_name).hex, load_name)
          self.assertEqual(definition["metadata"]["displayName"], "Shared name")


class TestBuildPlateDefinition(unittest.IsolatedAsyncioTestCase):
  """build_plate_definition maps PLR plate geometry into a wellPlate definition."""

  async def test_identity_and_dimensions(self):
    definition = build_plate_definition(await _facts(_plate()))
    self.assertEqual(definition["namespace"], "pylabrobot")
    self.assertEqual(definition["version"], 1)
    self.assertEqual(definition["schemaVersion"], 2)
    self.assertEqual(definition["metadata"]["displayCategory"], "wellPlate")
    self.assertEqual(definition["metadata"]["displayName"], "Black Plate-1")
    self.assertFalse(definition["parameters"]["isTiprack"])
    self.assertEqual(
      definition["dimensions"],
      {"xDimension": 127.0, "yDimension": 80.0, "zDimension": 14.0},
    )

  async def test_ordering_is_column_major(self):
    definition = build_plate_definition(await _facts(_plate()))
    self.assertEqual(definition["ordering"], [["A1", "B1"], ["A2", "B2"]])

  async def test_corner_offset_is_zero_front_left_anchor(self):
    # PLR and Opentrons schema-2 definitions both anchor labware at the
    # slot's front-left-bottom corner, so no frame conversion applies.
    definition = build_plate_definition(await _facts(_plate()))
    self.assertEqual(definition["cornerOffsetFromSlot"], {"x": 0, "y": 0, "z": 0})

  async def test_well_geometry_carries_depth_volume_and_centers(self):
    definition = build_plate_definition(await _facts(_plate()))
    # A1 (back-left well): origin (10, 17, 1), 6 mm square, so center (13, 20).
    # Its z is the CAVITY floor: the well's own bottom (1.0) plus the 0.5 mm
    # of plastic beneath it, matching how Opentrons reads a well's z.
    self.assertEqual(
      definition["wells"]["A1"],
      {
        "depth": 10.0,
        "x": 13.0,
        "y": 20.0,
        "z": 1.5,
        "shape": "circular",
        "diameter": 6.0,
        "totalLiquidVolume": 360.0,
      },
    )
    # B1 is one 9 mm pitch toward the front: center y = 8 + 3 = 11.
    self.assertEqual(definition["wells"]["B1"]["y"], 11.0)
    self.assertEqual(definition["groups"][0]["wells"], ["A1", "B1", "A2", "B2"])

  async def test_well_z_is_the_cavity_floor_not_the_wells_outer_bottom(self):
    # The default liquid position is 1 mm above a well's z, so a z at the
    # well's outer bottom aims it into the plastic. PLR's corning plate: A1
    # bottom 3.03 + 0.5 mm wall; Opentrons ships z = 3.55 for that plate.
    definition = build_plate_definition(await _facts("cor_96_wellplate_360uL_Fb"))
    self.assertAlmostEqual(definition["wells"]["A1"]["z"], 3.53)
    self.assertAlmostEqual(definition["wells"]["A1"]["depth"], 10.67)
    # z + depth is the real rim, which is what touchTip and liquidProbe ride.
    self.assertAlmostEqual(
      definition["wells"]["A1"]["z"] + definition["wells"]["A1"]["depth"],
      definition["dimensions"]["zDimension"],
    )

  async def test_plate_without_material_thickness_is_refused(self):
    # No cavity floor to anchor liquid ops at, and no safe default: falling
    # back to zero is what aims them at the plastic.
    facts = await _facts(_plate(material_z_thickness=None))
    with self.assertRaises(NotImplementedError) as caught:
      build_plate_definition(facts)
    self.assertIn("material_z_thickness", str(caught.exception))
    self.assertIn("well_A1", str(caught.exception))

  async def test_rotated_plate_is_refused(self):
    # An Opentrons definition positions wells from the slot's front-left
    # corner and cannot express a rotation, so a rotated plate would upload
    # unrotated well coordinates inside a rotated bounding box.
    for angle in (90, 180):
      plate = _plate()
      plate.rotation = Rotation(z=angle)
      facts = await _facts(plate)
      with self.assertRaises(ValueError) as caught:
        build_plate_definition(facts)
      self.assertIn("rotation", str(caught.exception))

  async def test_plate_under_a_rotated_parent_is_refused(self):
    holder = ResourceHolder(name="holder", size_x=130.0, size_y=90.0, size_z=1.0)
    holder.rotation = Rotation(z=90)
    plate = _plate()
    holder.assign_child_resource(plate, location=Coordinate.zero())
    facts = await _facts(holder, name=plate.name)
    with self.assertRaises(ValueError):
      build_plate_definition(facts)

  async def test_rectangular_wells_carry_x_y_dimensions(self):
    facts = await _facts(_plate(cross_section_type=CrossSectionType.RECTANGLE))
    well = build_plate_definition(facts)["wells"]["A1"]
    self.assertEqual(well["shape"], "rectangular")
    self.assertEqual(well["xDimension"], 6.0)
    self.assertEqual(well["yDimension"], 6.0)
    self.assertNotIn("diameter", well)

  async def test_well_bottom_shape_maps_from_plr_bottom_type(self):
    v = await _facts(_plate(bottom_type=WellBottomType.V))
    u = await _facts(_plate(bottom_type=WellBottomType.U))
    self.assertEqual(build_plate_definition(v)["groups"][0]["metadata"], {"wellBottomShape": "v"})
    self.assertEqual(build_plate_definition(u)["groups"][0]["metadata"], {"wellBottomShape": "u"})
    # UNKNOWN falls back to flat, the schema's safest default.
    self.assertEqual(
      build_plate_definition(await _facts(_plate()))["groups"][0]["metadata"],
      {"wellBottomShape": "flat"},
    )

  async def test_format_derives_from_grid(self):
    self.assertEqual(
      build_plate_definition(await _facts(_plate()))["parameters"]["format"], "irregular"
    )
    plate_96 = await _facts(_plate(num_items_x=12, num_items_y=8))
    self.assertEqual(build_plate_definition(plate_96)["parameters"]["format"], "96Standard")
    plate_384 = await _facts(_plate(num_items_x=24, num_items_y=16))
    self.assertEqual(build_plate_definition(plate_384)["parameters"]["format"], "384Standard")

  async def test_grip_height_from_grip_distance(self):
    facts = await _facts(_plate())
    self.assertNotIn("gripHeightFromLabwareBottom", build_plate_definition(facts))
    definition = build_plate_definition(facts, grip_distance_from_top=4.0)
    self.assertEqual(definition["gripHeightFromLabwareBottom"], 10.0)  # 14 - 4
    clamped = build_plate_definition(facts, grip_distance_from_top=20.0)
    self.assertEqual(clamped["gripHeightFromLabwareBottom"], 0.0)


class TestBuildTipRackDefinition(unittest.IsolatedAsyncioTestCase):
  """build_tip_rack_definition maps rack geometry and the prototype tip."""

  async def test_ot2_defaults_keep_diagonal_diameter_and_empty_group_metadata(self):
    rack = await _facts(_tip_rack())
    definition = build_tip_rack_definition(rack, rack.item("A1").prototype, "custom")

    self.assertAlmostEqual(definition["wells"]["A1"]["diameter"], 7.0710678118654755)
    self.assertEqual(definition["metadata"]["displayName"], rack.name)
    self.assertEqual(definition["parameters"]["loadName"], "custom")
    self.assertEqual(definition["groups"][0]["metadata"], {})

  async def test_tip_parameters_come_from_prototype_tip(self):
    definition = build_tip_rack_definition(await _facts(_tip_rack()), for_flex=True)
    self.assertEqual(definition["metadata"]["displayCategory"], "tipRack")
    self.assertEqual(definition["parameters"]["format"], "irregular")  # 2x2 is not an SBS grid
    self.assertTrue(definition["parameters"]["isTiprack"])
    self.assertEqual(definition["parameters"]["tipLength"], 50.0)
    self.assertEqual(definition["parameters"]["tipOverlap"], 8.0)

  async def test_full_rack_format_is_96standard(self):
    rack = await _facts(_tip_rack(num_items_x=12, num_items_y=8))
    definition = build_tip_rack_definition(rack, for_flex=True)
    self.assertEqual(definition["parameters"]["format"], "96Standard")

  async def test_spot_geometry_and_zero_corner_offset(self):
    definition = build_tip_rack_definition(await _facts(_tip_rack()), for_flex=True)
    self.assertEqual(definition["cornerOffsetFromSlot"], {"x": 0, "y": 0, "z": 0})
    self.assertEqual(definition["ordering"], [["A1", "B1"], ["A2", "B2"]])
    # A1 spot origin (10, 17, 0), 5 mm square: center (12.5, 19.5). The depth
    # is the prototype tip's length: a TipSpot has no height of its own, and
    # a pickUpTip descends to z + depth, the seated tip's top.
    self.assertEqual(
      definition["wells"]["A1"],
      {
        "depth": 50.0,
        "x": 12.5,
        "y": 19.5,
        "z": 0.0,
        "shape": "circular",
        "diameter": 5.0,
        "totalLiquidVolume": 200.0,
      },
    )

  async def test_well_depth_reproduces_a_shipped_opentrons_rack(self):
    # PLR builds this rack BY loading Opentrons' own definition, so the
    # rebuilt one must carry that file's numbers back: z 5.39, depth 59.3,
    # tipLength 59.3.
    definition = build_tip_rack_definition(
      await _facts("opentrons_96_filtertiprack_200ul"), for_flex=True
    )
    self.assertAlmostEqual(definition["wells"]["A1"]["z"], 5.39)
    self.assertAlmostEqual(definition["wells"]["A1"]["depth"], 59.3)
    self.assertAlmostEqual(definition["parameters"]["tipLength"], 59.3)

  async def test_rack_whose_tips_hang_below_its_base_is_refused(self):
    # The robot-server's schema declares well z non-negative, so this uploads
    # as a 422 per well; refuse it here, naming the rack and the spot.
    rack = await _facts(_tip_rack(dz=-50.5))
    for for_flex in (False, True):
      with self.subTest(for_flex=for_flex):
        with self.assertRaises(ValueError) as caught:
          build_tip_rack_definition(rack, for_flex=for_flex)
        self.assertIn("hamilton tips 300", str(caught.exception))
        self.assertIn("50.5 mm BELOW", str(caught.exception))

  async def test_rotated_tip_rack_is_refused(self):
    plr_rack = _tip_rack()
    plr_rack.rotation = Rotation(z=90)
    rack = await _facts(plr_rack)
    for for_flex in (False, True):
      with self.subTest(for_flex=for_flex), self.assertRaises(ValueError):
        build_tip_rack_definition(rack, for_flex=for_flex)

  async def test_grip_height_from_grip_distance(self):
    rack = await _facts(_tip_rack())
    self.assertNotIn("gripHeightFromLabwareBottom", build_tip_rack_definition(rack, for_flex=True))
    definition = build_tip_rack_definition(rack, grip_distance_from_top=10.0, for_flex=True)
    self.assertEqual(definition["gripHeightFromLabwareBottom"], 80.0)  # 90 - 10


class TestBuildContainerDefinition(unittest.IsolatedAsyncioTestCase):
  """build_container_definition maps a container to a single-cavity reservoir."""

  async def test_single_a1_cavity_spans_the_container(self):
    definition = build_container_definition(await _facts(_trough()))
    self.assertEqual(definition["namespace"], "pylabrobot")
    self.assertEqual(definition["metadata"]["displayCategory"], "reservoir")
    self.assertEqual(definition["ordering"], [["A1"]])
    self.assertEqual(definition["cornerOffsetFromSlot"], {"x": 0, "y": 0, "z": 0})
    self.assertEqual(
      definition["dimensions"],
      {"xDimension": 120.0, "yDimension": 80.0, "zDimension": 40.0},
    )
    # The cavity floor sits on the 1.5 mm of plastic under it, and the depth
    # loses the same, so the well's top stays at the container's real rim.
    self.assertEqual(
      definition["wells"],
      {
        "A1": {
          "depth": 38.5,
          "x": 60.0,
          "y": 40.0,
          "z": 1.5,
          "shape": "rectangular",
          "xDimension": 120.0,
          "yDimension": 80.0,
          "totalLiquidVolume": 290000.0,
        }
      },
    )
    self.assertEqual(definition["groups"][0]["wells"], ["A1"])

  async def test_cavity_floor_sits_on_the_wall_thickness(self):
    # Pinned against real labware: hamilton_1_trough_60mL_Vb is 65.5 mm tall
    # with a 1.58 mm floor, and every shipped Opentrons reservoir likewise
    # has z + depth == zDimension with a non-zero z.
    definition = build_container_definition(await _facts("hamilton_1_trough_60mL_Vb"))
    well = definition["wells"]["A1"]
    self.assertAlmostEqual(well["z"], 1.58)
    self.assertAlmostEqual(well["depth"], 63.92)
    self.assertAlmostEqual(well["z"] + well["depth"], definition["dimensions"]["zDimension"])

  async def test_container_without_material_thickness_is_refused(self):
    facts = await _facts(_trough(material_z_thickness=None))
    with self.assertRaises(NotImplementedError) as caught:
      build_container_definition(facts)
    self.assertIn("material_z_thickness", str(caught.exception))
    self.assertIn("hamilton trough", str(caught.exception))

  async def test_well_bottom_shape_maps_from_the_troughs_bottom_type(self):
    # The enum's own values are "U"/"V"/"unknown", which the robot-server's
    # Literal["flat", "u", "v"] rejects, so the mapping must lower-case them.
    for bottom_type, expected in (
      (TroughBottomType.V, "v"),
      (TroughBottomType.U, "u"),
      (TroughBottomType.FLAT, "flat"),
      (TroughBottomType.UNKNOWN, "flat"),
    ):
      definition = build_container_definition(await _facts(_trough(bottom_type=bottom_type)))
      self.assertEqual(definition["groups"][0]["metadata"], {"wellBottomShape": expected})
    # A plain Container carries no bottom shape at all.
    plain = Container(name="plain", size_x=10.0, size_y=10.0, size_z=10.0, material_z_thickness=1.0)
    self.assertEqual(
      build_container_definition(await _facts(plain))["groups"][0]["metadata"],
      {"wellBottomShape": "flat"},
    )

  async def test_rotated_cavity_uploads_the_shared_deck_frame_footprint(self):
    # A 90-degree rotation swaps the container's dimensions in the deck frame.
    trough = _trough()
    trough.rotation = Rotation(z=90)
    definition = build_container_definition(await _facts(trough))
    self.assertEqual(definition["dimensions"]["xDimension"], 80.0)
    self.assertEqual(definition["dimensions"]["yDimension"], 120.0)
    self.assertEqual(definition["wells"]["A1"]["xDimension"], 80.0)
    self.assertEqual(definition["wells"]["A1"]["yDimension"], 120.0)

  async def test_center_multichannel_quirk_matches_shipped_reservoirs(self):
    # Every shipped Opentrons 1-well reservoir carries this quirk; the engine
    # centers a multi-channel nozzle array on the cavity because of it, so
    # container ops send no manual centering offsets.
    definition = build_container_definition(await _facts(_trough()))
    self.assertEqual(definition["parameters"]["quirks"], ["centerMultichannelOnWells"])

  async def test_grip_height_from_grip_distance(self):
    facts = await _facts(_trough())
    self.assertNotIn("gripHeightFromLabwareBottom", build_container_definition(facts))
    definition = build_container_definition(facts, grip_distance_from_top=10.0)
    self.assertEqual(definition["gripHeightFromLabwareBottom"], 30.0)  # 40 - 10


class TestBuildMovableLabwareDefinition(unittest.IsolatedAsyncioTestCase):
  """build_movable_labware_definition builds the minimal gripper-move stub."""

  async def test_stub_has_fake_well_and_grip_geometry(self):
    resource = await _facts(Resource(name="lid stack", size_x=100.0, size_y=90.0, size_z=20.0))
    definition = build_movable_labware_definition(resource, grip_distance_from_top=5.0)
    self.assertEqual(definition["namespace"], "pylabrobot")
    self.assertEqual(definition["ordering"], [["A1"]])
    self.assertEqual(definition["cornerOffsetFromSlot"], {"x": 0, "y": 0, "z": 0})
    self.assertEqual(
      definition["wells"]["A1"],
      {
        "depth": 0,
        "x": 50.0,
        "y": 45.0,
        "z": 0,
        "shape": "circular",
        "diameter": 5,
        "totalLiquidVolume": 0,
      },
    )
    self.assertEqual(definition["gripHeightFromLabwareBottom"], 15.0)  # 20 - 5
    self.assertEqual(
      definition["gripperOffsets"],
      {
        "default": {
          "pickUpOffset": {"x": 0, "y": 0, "z": 0},
          "dropOffset": {"x": 0, "y": 0, "z": 0},
        }
      },
    )

  async def test_grip_height_omitted_without_grip_distance(self):
    resource = await _facts(Resource(name="lid stack", size_x=100.0, size_y=90.0, size_z=20.0))
    definition = build_movable_labware_definition(resource)
    self.assertNotIn("gripHeightFromLabwareBottom", definition)

  async def test_grip_height_clamped_at_labware_bottom(self):
    resource = await _facts(Resource(name="shim", size_x=10.0, size_y=10.0, size_z=3.0))
    definition = build_movable_labware_definition(resource, grip_distance_from_top=7.0)
    self.assertEqual(definition["gripHeightFromLabwareBottom"], 0.0)


async def _flex_with_api(
  test_case: unittest.IsolatedAsyncioTestCase,
  api: Optional[AsyncMock] = None,
) -> Tuple[Flex, AsyncMock]:
  api = api or make_api(pipette=("p1000_single_flex", 1, 1.0, 1000.0), mount="right")
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  return flex, api


async def _flex_head8_with_gripper(
  test_case: unittest.IsolatedAsyncioTestCase,
) -> Tuple[Flex, AsyncMock, FlexHead8]:
  """A set-up Flex with an 8-channel head AND a gripper, so one bench can
  drive both the gripper-intent and pipetting-intent load paths."""
  api = make_api(pipettes=[("p50_multi_flex", 8, 1.0, 50.0, "left")], gripper=True)
  flex = make_flex(deck=await make_deck(), host="localhost", api=api)
  test_case.addAsyncCleanup(flex.disconnect)
  await flex.setup()
  head = flex.left
  assert isinstance(head, FlexHead8)
  return flex, api, head


def _load_labware_commands(api: AsyncMock) -> list:
  return [c for c in api.submit_command.await_args_list if c.args[1] == "loadLabware"]


async def _put(flex: Flex, resource: Resource, slot: str) -> Any:
  """Make a PLR-built resource in a slot of the Flex's deck."""
  return await place(flex.deck, _definition(resource), resource.name, slot)


async def _mount_tips(flex: Flex, head: FlexHead8) -> None:
  """Pick up a column of tips, so a liquid op reaches past the mounted-tip guard."""
  rack = await place(flex.deck, "flex_96_tiprack_50ul", f"tips for {head.mount}", "D1")
  await head.pick_up_tips(rack, column=0)


class TestUnbuildableLabwareGuard(unittest.IsolatedAsyncioTestCase):
  """Labware no well-bearing definition can be built from is gripper-movable
  but never pipettable: the movable stub's single fake well is zero-depth and
  sits at the labware's own bottom, so pipetting it would drive a tip at the
  deck. Pipetting callers are refused before any wire command."""

  async def asyncSetUp(self):
    self.flex, self.api, self.head = await _flex_head8_with_gripper(self)

  async def test_pipetting_a_tube_rack_raises_before_any_wire_command(self):
    rack = await _put(self.flex, _tube_rack(), "C1")
    await _mount_tips(self.flex, self.head)

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      # An untyped script can hand a rack to a Plate parameter; that is
      # exactly the caller this guard exists for.
      await self.head.aspirate(rack, column=0, volume=20)

    self.assertEqual(self.api.define_labware.await_count, 0)
    self.assertEqual(self.api.submit_command.await_count, commands_before)

  async def test_gripper_move_of_the_same_rack_still_works(self):
    rack = await _put(self.flex, _tube_rack(), "C1")
    gripper = self.flex.gripper
    assert gripper is not None

    await gripper.move_labware(rack, "C2")

    self.assertEqual(self.api.define_labware.await_count, 1)
    self.assertEqual(
      [c.args[1] for c in self.api.define_labware.await_args_list][0]["wells"]["A1"]["depth"], 0
    )
    self.assertEqual(await get_slot(self.flex.deck, rack), "C2")

  async def test_pipetting_after_a_gripper_move_still_raises_on_the_load_cache_hit(self):
    # The load cache returns before any type dispatch, so the stub-loaded
    # labware is recorded separately for the pipetting refusal to see it.
    rack = await _put(self.flex, _tube_rack(), "C1")
    gripper = self.flex.gripper
    assert gripper is not None
    await gripper.move_labware(rack, "C2")
    await _mount_tips(self.flex, self.head)

    commands_before = self.api.submit_command.await_count
    with self.assertRaises(OpentronsError):
      await self.head.aspirate(rack, column=0, volume=20)

    self.assertEqual(self.api.submit_command.await_count, commands_before)

  async def test_off_deck_clears_the_stub_record(self):
    rack = await _put(self.flex, _tube_rack(), "C1")
    gripper = self.flex.gripper
    assert gripper is not None
    await gripper.move_labware(rack, "C2")
    self.assertIn(rack.id, self.flex._stub_labware)

    await self.flex.labware_moved_off_deck(rack)
    self.assertNotIn(rack.id, self.flex._stub_labware)


class TestCustomLabwareLoadFlow(unittest.IsolatedAsyncioTestCase):
  """_ensure_labware_loaded uploads a definition for labware with no official name."""

  async def test_plate_without_official_name_uploads_then_loads(self):
    flex, api = await _flex_with_api(self)
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")
    await flex._ensure_labware_loaded(plate)

    self.assertEqual(api.define_labware.await_count, 1)
    definition = [c.args[1] for c in api.define_labware.await_args_list][0]
    load_cmds = _load_labware_commands(api)
    self.assertEqual(len(load_cmds), 1)
    params = load_cmds[0].args[2]
    # loadLabware must reference exactly the uploaded definition's identity.
    self.assertEqual(params["namespace"], definition["namespace"])
    self.assertEqual(params["loadName"], definition["parameters"]["loadName"])
    self.assertEqual(params["version"], definition["version"])
    self.assertEqual(params["namespace"], "pylabrobot")
    self.assertEqual(params["version"], 1)
    self.assertEqual(params["location"], {"slotName": "C1"})

  async def test_load_into_a_staging_slot_uses_the_addressable_area_form(self):
    # The robot-server's DeckSlotName covers only the A1-D3 grid, so the
    # column-4 staging slots ride a different location key.
    flex, api = await _flex_with_api(self)
    await flex.setup()
    plate = await _put(flex, _plate(), "A4")
    await flex._ensure_labware_loaded(plate)

    params = _load_labware_commands(api)[0].args[2]
    self.assertEqual(params["location"], {"addressableAreaName": "A4"})

  async def test_second_use_hits_cache_no_second_upload_or_load(self):
    flex, api = await _flex_with_api(self)
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")
    first = await flex._ensure_labware_loaded(plate)
    second = await flex._ensure_labware_loaded(plate)

    self.assertEqual(first, second)
    self.assertEqual(api.define_labware.await_count, 1)
    self.assertEqual(len(_load_labware_commands(api)), 1)

  async def test_reload_after_off_deck_reuploads_definition(self):
    # The definition-identity cache is evicted with the departed labware: a
    # different same-named resource re-added later must not inherit the old
    # geometry, so the re-add re-uploads.
    flex, api = await _flex_with_api(self)
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")
    await flex._ensure_labware_loaded(plate)
    await flex.labware_moved_off_deck(plate)
    self.assertIsNone(flex._require_labware().definition(plate))

    await assign_child_at_slot(flex.deck, plate, "D2")
    await flex._ensure_labware_loaded(plate)

    self.assertEqual(api.define_labware.await_count, 2)
    load_cmds = _load_labware_commands(api)
    self.assertEqual(len(load_cmds), 2)
    self.assertEqual(load_cmds[1].args[2]["location"], {"slotName": "D2"})
    self.assertNotEqual(load_cmds[0].args[2]["loadName"], load_cmds[1].args[2]["loadName"])

  async def test_second_setup_clears_run_scoped_caches(self):
    # labwareIds and uploaded definitions are both run-scoped server-side, so
    # a new run (new setup) must re-upload and re-load.
    flex, api = await _flex_with_api(self)
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")
    await flex._ensure_labware_loaded(plate)
    self.assertEqual(api.define_labware.await_count, 1)

    await flex.disconnect()
    await flex.setup()  # new run
    self.assertFalse(flex._require_labware().is_loaded(plate))
    self.assertIsNone(flex._require_labware().definition(plate))

    await flex._ensure_labware_loaded(plate)
    self.assertEqual(api.define_labware.await_count, 2)
    self.assertEqual(len(_load_labware_commands(api)), 2)

  async def test_failed_upload_leaves_caches_clean_and_retry_works(self):
    flex, api = await _flex_with_api(
      self, make_api(pipette=("p1000_single_flex", 1, 1.0, 1000.0), mount="right")
    )
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")

    with (
      patch.object(api, "define_labware", AsyncMock(side_effect=RuntimeError("upload failed"))),
      self.assertRaises(RuntimeError),
    ):
      await flex._ensure_labware_loaded(plate)
    self.assertIsNone(flex._require_labware().definition(plate))
    self.assertFalse(flex._require_labware().is_loaded(plate))

    await flex._ensure_labware_loaded(plate)
    self.assertEqual(api.define_labware.await_count, 1)
    self.assertEqual(len(_load_labware_commands(api)), 1)
    self.assertTrue(flex._require_labware().is_loaded(plate))

  async def test_failed_load_leaves_no_labware_id_and_retry_reuses_definition(self):
    flex, api = await _flex_with_api(
      self, make_api(pipette=("p1000_single_flex", 1, 1.0, 1000.0), mount="right")
    )
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")

    with (
      patch.object(
        api,
        "get_command",
        AsyncMock(return_value=CommandInfo("failed", {}, {"detail": "load failed"})),
      ),
      self.assertRaises(OpentronsCommandError),
    ):
      await flex._ensure_labware_loaded(plate)
    self.assertFalse(flex._require_labware().is_loaded(plate))

    await flex._ensure_labware_loaded(plate)
    # The upload succeeded the first time, so the retry re-loads without a
    # duplicate upload.
    self.assertEqual(api.define_labware.await_count, 1)
    self.assertEqual(len(_load_labware_commands(api)), 2)
    self.assertTrue(flex._require_labware().is_loaded(plate))

  async def test_definition_cache_hit_logs_the_ignored_grip_distance(self):
    # The upload survives a failed load, so the retry reuses the stored
    # definition -- and the grip height it already carries.
    flex, api = await _flex_with_api(
      self, make_api(pipette=("p1000_single_flex", 1, 1.0, 1000.0), mount="right")
    )
    await flex.setup()
    plate = await _put(flex, _plate(), "C1")
    with (
      patch.object(
        api,
        "get_command",
        AsyncMock(return_value=CommandInfo("failed", {}, {"detail": "load failed"})),
      ),
      self.assertRaises(OpentronsCommandError),
    ):
      await flex._ensure_labware_loaded(plate, grip_distance_from_top=4.0)

    with self.assertLogs("pylabrobot.opentrons.flex.flex", level="WARNING") as logs:
      await flex._ensure_labware_loaded(plate, grip_distance_from_top=8.0)

    self.assertEqual(api.define_labware.await_count, 1)
    self.assertEqual(
      [c.args[1] for c in api.define_labware.await_args_list][0]["gripHeightFromLabwareBottom"],
      10.0,
    )
    self.assertTrue(any("grip_distance_from_top=8.0" in line for line in logs.output))

  async def test_official_tip_rack_loads_with_zero_uploads(self):
    for model, load_name in (
      ("flex_96_tiprack_50ul", "opentrons_flex_96_tiprack_50ul"),
      ("flex_96_filtertiprack_50ul", "opentrons_flex_96_filtertiprack_50ul"),
      ("flex_96_tiprack_200ul", "opentrons_flex_96_tiprack_200ul"),
      ("flex_96_tiprack_1000ul", "opentrons_flex_96_tiprack_1000ul"),
    ):
      for with_tips in (False, True):
        with self.subTest(load_name=load_name, with_tips=with_tips):
          flex, api = await _flex_with_api(self)
          await flex.setup()
          rack = cast(handles.TipRack, await place(flex.deck, model, "rack", "C1"))
          if not with_tips:
            await rack.empty()
          self.assertEqual(rack.num_items, 96)
          self.assertTrue(
            all([await cast(handles.TipSpot, s).has_tip() == with_tips for s in rack.items])
          )
          await flex._ensure_labware_loaded(rack)

          api.define_labware.assert_not_awaited()
          load_cmds = _load_labware_commands(api)
          self.assertEqual(len(load_cmds), 1)
          params = load_cmds[0].args[2]
          self.assertEqual(params["namespace"], "opentrons")
          self.assertEqual(params["loadName"], load_name)
          self.assertEqual(params["version"], 1)

  async def test_container_uploads_single_cavity_definition(self):
    flex, api = await _flex_with_api(self)
    await flex.setup()
    trough = await _put(flex, _trough(), "B1")
    await flex._ensure_labware_loaded(trough)

    self.assertEqual(api.define_labware.await_count, 1)
    definition = [c.args[1] for c in api.define_labware.await_args_list][0]
    self.assertEqual(list(definition["wells"]), ["A1"])
    params = _load_labware_commands(api)[0].args[2]
    self.assertEqual(params["namespace"], "pylabrobot")
    self.assertEqual(params["loadName"], definition["parameters"]["loadName"])

  async def test_tip_rack_without_official_name_uploads_tiprack_definition(self):
    flex, api = await _flex_with_api(self)
    await flex.setup()
    rack = await _put(flex, _tip_rack(), "C1")
    await flex._ensure_labware_loaded(rack)

    self.assertEqual(api.define_labware.await_count, 1)
    definition = api.define_labware.await_args.args[1]
    self.assertTrue(definition["parameters"]["isTiprack"])
    params = _load_labware_commands(api)[0].args[2]
    self.assertEqual(params["loadName"], definition["parameters"]["loadName"])

  async def test_bare_resource_uploads_movable_stub(self):
    # A resource that is not a Plate/TipRack/Container routes to the
    # non-pipettable movable stub, which only allow_stub callers may ask for.
    flex, api = await _flex_with_api(self)
    await flex.setup()
    widget = await _put(flex, Resource(name="widget", size_x=100.0, size_y=90.0, size_z=20.0), "C1")
    await flex._ensure_labware_loaded(widget, allow_stub=True, grip_distance_from_top=5.0)

    self.assertEqual(api.define_labware.await_count, 1)
    definition = [c.args[1] for c in api.define_labware.await_args_list][0]
    self.assertEqual(definition["ordering"], [["A1"]])
    self.assertEqual(definition["wells"]["A1"]["depth"], 0)
    self.assertEqual(definition["gripHeightFromLabwareBottom"], 15.0)  # 20 - 5
    params = _load_labware_commands(api)[0].args[2]
    self.assertEqual(params["namespace"], "pylabrobot")
    self.assertEqual(params["loadName"], definition["parameters"]["loadName"])
