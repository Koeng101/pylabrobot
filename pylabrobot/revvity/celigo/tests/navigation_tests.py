"""Tests for plate/well navigation and the FOV galvo grid."""

import unittest

from pylabrobot.revvity.celigo.coordinates import CoordinateSystems
from pylabrobot.revvity.celigo.navigation import (
  effective_fov_mm,
  fields_of_view_per_field_of_reference,
  galvo_field_of_view_offsets_mm,
  well_to_sample_mm,
  well_to_stage_mm,
)
from pylabrobot.revvity.celigo.tests.helpers import (
  make_calibration_config,
  make_hardware_default_config,
  make_navigation_config,
  make_plate,
)


def _coords():
  calib = make_calibration_config(
    microns_per_pixel_x=1.05456,
    microns_per_pixel_y=1.05444,
    image_width_pixels=2048,
    image_height_pixels=2048,
    stage_x_scale=1.0,
    stage_y_scale=1.0,
  )
  hw = make_hardware_default_config(
    default_plate_x_corner_stage_coordinate=2.159,
    default_plate_y_corner_stage_coordinate=3.492,
  )
  return calib, hw, CoordinateSystems.from_config(calib, hw)


class TestPlateNavigation(unittest.IsolatedAsyncioTestCase):
  async def test_well_sample_position_uses_plate_geometry_without_stage_calibration(self):
    plate = await make_plate()
    x, y = await well_to_sample_mm(plate, "A1")
    self.assertAlmostEqual(x, 14.3)
    self.assertAlmostEqual(y, 11.28)

  async def test_plr_plate_uses_its_resource_geometry(self):
    _, _, cs = _coords()
    plate = await make_plate()
    a1 = await well_to_stage_mm(plate, "A1", cs)
    a2 = await well_to_stage_mm(plate, "A2", cs)
    b1 = await well_to_stage_mm(plate, "B1", cs)
    self.assertAlmostEqual(a1[0], 16.459)
    self.assertAlmostEqual(a1[1], 14.772)
    self.assertAlmostEqual(a2[0] - a1[0], 9.0)
    self.assertAlmostEqual(b1[1] - a1[1], 9.0)

  async def test_out_of_range(self):
    _, _, cs = _coords()
    plate = await make_plate()
    with self.assertRaises(ValueError):
      await well_to_stage_mm(plate, "I1", cs)

  async def test_single_well_plate_uses_its_actual_well_center(self):
    _, _, cs = _coords()
    plate = await make_plate("VWR_1_troughplate_195000uL_Ub", "reservoir")
    x, y = await well_to_stage_mm(plate, "A1", cs)
    well = plate.get_well("A1")
    location = await well.get_location()
    self.assertIsNotNone(location)
    assert location is not None
    well_size = await well.get_size()
    plate_size = (await plate.attributes()).size
    self.assertAlmostEqual(x, location.x + well_size.x / 2 + 2.159)
    self.assertAlmostEqual(
      y,
      plate_size.y - (location.y + well_size.y / 2) + 3.492,
    )

  async def test_well_names_beyond_z_use_plr_lookup(self):
    _, _, cs = _coords()
    plate = await make_plate("DeepWell_Greiner_1536_Well", "plate")
    aa1 = await well_to_stage_mm(plate, "AA1", cs)
    well = plate.get_well("AA1")
    location = await well.get_location()
    self.assertIsNotNone(location)
    assert location is not None
    self.assertAlmostEqual(aa1[0], location.x + (await well.get_size()).x / 2 + 2.159)


class TestWellToStage(unittest.IsolatedAsyncioTestCase):
  async def test_a1_stage_position(self):
    _, _, cs = _coords()
    plate = await make_plate()
    x, y = await well_to_stage_mm(plate, "A1", cs)
    # this config has no calibrated corner offset, so stage = sample + default corner:
    self.assertAlmostEqual(x, 16.459)
    self.assertAlmostEqual(y, 14.772)

  async def test_adjacent_wells_differ_by_pitch(self):
    _, _, cs = _coords()
    plate = await make_plate()
    a1 = await well_to_stage_mm(plate, "A1", cs)
    a2 = await well_to_stage_mm(plate, "A2", cs)
    b1 = await well_to_stage_mm(plate, "B1", cs)
    self.assertAlmostEqual(a2[0] - a1[0], 9.0)
    self.assertAlmostEqual(b1[1] - a1[1], 9.0)


class TestFovGrid(unittest.TestCase):
  def setUp(self):
    self.calib, self.hw, self.cs = _coords()
    self.nav = make_navigation_config(
      frame_overlap_x_mm=0.1,
      frame_overlap_y_mm=0.1,
      max_galvo_deflection_x_mm=4.5,
      max_galvo_deflection_y_mm=4.5,
    )

  def test_effective_fov(self):
    ex, _ = effective_fov_mm(self.calib, self.nav)
    # 2048 * 1.05456 / 1000 = ~2.16 mm, minus 0.2 overlap
    self.assertAlmostEqual(ex, 2048 * 1.05456 / 1000.0 - 0.2, places=4)

  def test_fovs_per_for(self):
    nx, ny = fields_of_view_per_field_of_reference(self.calib, self.nav)
    self.assertEqual((nx, ny), (4, 4))  # floor(2*4.5/1.96) == 4

  def test_offsets_count_and_centered(self):
    offsets = galvo_field_of_view_offsets_mm(self.calib, self.nav)
    self.assertEqual(len(offsets), 16)  # 4x4
    # symmetric about origin -> mean ~ 0
    mx = sum(o[0] for o in offsets) / len(offsets)
    my = sum(o[1] for o in offsets) / len(offsets)
    self.assertAlmostEqual(mx, 0.0, places=9)
    self.assertAlmostEqual(my, 0.0, places=9)

  def test_serpentine_rows_reverse(self):
    offsets = galvo_field_of_view_offsets_mm(self.calib, self.nav)
    # first row left->right (increasing x), second row right->left (decreasing x)
    row0 = offsets[0:4]
    row1 = offsets[4:8]
    self.assertTrue(row0[0][0] < row0[-1][0])
    self.assertTrue(row1[0][0] > row1[-1][0])


if __name__ == "__main__":
  unittest.main()
