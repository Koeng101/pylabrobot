"""Thermo Fisher Scientific  Inc. (and all its brand) plates"""

import logging
import math

from pylabrobot.resources.plate import Lid, Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

logger = logging.getLogger(__name__)

# Please conform with the 'manufacturer-first, then brands' naming principle:

# Thermo Fisher Scientific Inc. (TFS, aka "Thermo")
# ├── Applied Biosystems (AB; brand)
# │   └── MicroAmp
# │      └── EnduraPlate
# ├── Fisher Scientific (FS; brand)
# ├── Invitrogen (INV; brand)
# ├── Ion Torrent (IT; brand)
# ├── Gibco (GIB; brand)
# ├── Thermo Scientific (TS; brand)
# │   ├── Nalgene
# │   ├── Nunc
# │   └── Pierce
# ├── Unity Lab Services (brand, services)
# ├── Patheon (brand, services)
# └── PPD (brand, services)


# # # # # # # # # # Thermo_TS_96_wellplate_1200ul_Rb # # # # # # # # # #


def Thermo_TS_96_wellplate_1200ul_Rb_Lid(name: str) -> Lid:
  raise NotImplementedError("This lid is not currently defined.")
  # See https://github.com/PyLabRobot/pylabrobot/pull/161.
  # return Lid(
  #   name=name,
  #   size_x=127.76,
  #   size_y=85.48,
  #   size_z=5,
  #   nesting_z_height=None, # measure overlap between lid and plate
  #   model="Thermo_TS_96_wellplate_1200ul_Rb_Lid",
  # )


# Height above the cavity bottom (mm) to volume (uL), linear between points.
_Thermo_TS_96_wellplate_1200ul_Rb_height_volume_data = {
  0.0: 0.0,
  0.015: 0.00287691,
  0.045: 0.0258286,
  0.095: 0.11464,
  0.155: 0.303668,
  0.215: 0.581365,
  0.275: 0.946372,
  0.335: 1.397334,
  0.4: 1.981298,
  0.465: 2.66282,
  0.53: 3.440175,
  0.595: 4.311638,
  0.66: 5.275482,
  0.725: 6.329982,
  0.79: 7.473413,
  0.855: 8.704049,
  0.925: 10.124895,
  0.995: 11.642722,
  1.065: 13.255375,
  1.135: 14.960699,
  1.205: 16.756538,
  1.275: 18.640738,
  1.35: 20.755128,
  1.425: 22.965828,
  1.5: 25.270186,
  1.575: 27.665552,
  1.65: 30.149276,
  1.73: 32.892983,
  1.81: 35.730989,
  1.89: 38.660076,
  1.975: 41.868431,
  2.06: 45.172117,
  2.145: 48.567276,
  2.235: 52.257564,
  2.325: 56.041497,
  2.42: 60.13218,
  2.515: 64.316711,
  2.615: 68.816945,
  2.72: 73.640808,
  2.825: 78.558535,
  2.935: 83.803189,
  3.055: 89.623187,
  3.18: 95.78366,
  3.315: 102.535296,
  3.465: 110.138511,
  3.635: 118.8586,
  3.85: 129.997468,
  4.075: 141.723364,
  20.5: 1232.712927,
  20.525: 1234.37349,
}


def Thermo_TS_96_wellplate_1200ul_Rb(name: str, with_lid: bool = False) -> Plate:
  """Thermo Fisher Scientific/Fisher Scientific cat. no.: AB1127/10243223.
  - Material: Polypropylene (AB-1068, polystyrene).
  - Brand: Thermo Scientific.
  - Sterilization compatibility: Autoclaving (15 minutes at 121°C) or
    Gamma Irradiation.
  - Chemical resistance: to DMSO (100%); Ethanol (100%); Isopropanol (100%).
  - Round well shape designed for optimal sample recovery or square shape to
    maximize sample volume within ANSI footprint design.
  - Each well has an independent sealing rim to prevent cross-contamination
  - U-bottomed wells ideally suited for sample resuspension.
  - Sealing options: Adhesive Seals, Heat Seals, Storage Plate Caps and Cap
    Strips, and Storage Plate Sealing Mats.
  - Cleanliness: 10243223/AB1127: Cleanroom manufacture.
  - ANSI/SLAS-format for compatibility with automated systems.
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=24.0,
    lid=Thermo_TS_96_wellplate_1200ul_Rb_Lid(name + "_lid") if with_lid else None,
    model="Thermo_TS_96_wellplate_1200ul_Rb",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=10.0,
      dy=7.3,
      dz=2.5,  # 2.5. https://github.com/PyLabRobot/pylabrobot/pull/183
      item_dx=9,
      item_dy=9,
      size_x=8.3,
      size_y=8.3,
      size_z=20.5,
      bottom_type=WellBottomType.U,
      material_z_thickness=1.15,
      cross_section_type=CrossSectionType.RECTANGLE,
      height_volume_data=_Thermo_TS_96_wellplate_1200ul_Rb_height_volume_data,
      max_volume=1232.7129266641255,
      name_prefix=name,
    ),
  )


# # # # # # # # # # Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate # # # # # # # # # #


# Calibration data: measured height (mm) → known volume (uL)
_enduraplate_height_to_volume = {
  0.0: 0.0,
  0.17: 4.0,
  0.77: 8.0,
  2.27: 20.0,
  6.57: 70.0,
  9.17: 120.0,
  11.17: 170.0,
  13.17: 220.0,
  15.17: 260.0,
}
_enduraplate_volume_to_height = {v: k for k, v in _enduraplate_height_to_volume.items()}


def Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate_Lid(name: str) -> Lid:
  raise NotImplementedError("This lid is not currently defined.")
  # See https://github.com/PyLabRobot/pylabrobot/pull/161.
  # return Lid(
  #   name=name,
  #   size_x=127.76,
  #   size_y=85.48,
  #   size_z=5,
  #   nesting_z_height=None, # measure overlap between lid and plate
  #   model="Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate_Lid",
  # )


# Height above the cavity bottom (mm) to volume (uL), linear between points: the calibration data,
# continued along its last segment to 21.11 mm, just past 5 % above the well's depth (20.1 mm).
_Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate_height_volume_data = {
  **_enduraplate_height_to_volume,
  21.11: 378.8,
}


def Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate(name: str, with_lid: bool = False) -> Plate:
  """Thermo Fisher Scientific/Fisher Scientific cat. no.: 4483354/15273005 (= with barcode)
  - alternative cat. no.: 16698853 (FS) (= **without** barcode).
  - See `./engineering_diagrams/` directory for more part numbers (different colours).
  - Material: Polycarbonate, Polypropylene
  - Sterilization compatibility: ?
  - Chemical resistance: ?
  - Thermal resistance: ?
  - Cleanliness: 'Certified DNA-, RNAse-, and PCR inhibitor-free with in-process sampling tests'.
  - ANSI/SLAS-format for compatibility with automated systems.
  - optimal pickup_distance_from_top=4 mm (i.e. pickup_distance_from_bottom=size_z-4).
  - total_volume = 300 ul.
  - working_volume = 200 ul (recommended by manufacturer).
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=20.1 + 1.6 - 0.5,  # cavity_depth + material_z_thickness - well_extruding_over_plate
    lid=Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate_Lid(name + "_lid") if with_lid else None,
    model="Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate",
    plate_type="semi-skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=11.63,
      dy=9.95,
      dz=0.0,  # check that plate is semi-skirted
      item_dx=9,
      item_dy=9,
      size_x=5.49,
      size_y=5.49,
      size_z=20.1,
      bottom_type=WellBottomType.V,
      material_z_thickness=1.6,
      cross_section_type=CrossSectionType.CIRCLE,
      height_volume_data=_Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate_height_volume_data,
      max_volume=358.6,
      name_prefix=name,
    ),
  )


# # # # # # # # # # Thermo_Nunc_96_well_plate_1300uL_Rb # # # # # # # # # #


def Thermo_Nunc_96_well_plate_1300uL_Rb(name: str) -> Plate:
  """
  - Part no.: 260252
  - Diagram: https://assets.thermofisher.com/TFS-Assets/LSG/manuals/D03011.pdf
  """

  well_diameter = 8.00  # measured
  return Plate(
    name=name,
    size_x=127.76,  # from definition, A
    size_y=85.47,  # from definition, B
    size_z=31.6,  # from definition, F
    lid=None,
    model=Thermo_Nunc_96_well_plate_1300uL_Rb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=14.4 - well_diameter / 2,  # from definition, H - well_diameter/2
      dy=11.2 - well_diameter / 2,  # from definition, J - well_diameter/2
      dz=1.4,  # from definition, N
      item_dx=9,
      item_dy=9,
      size_x=well_diameter,
      size_y=well_diameter,
      size_z=31.6 - 1.4,  # from definition, F - N
      bottom_type=WellBottomType.U,
      material_z_thickness=31.6 - 29.1 - 1.4,  # from definition, F - L - N
      cross_section_type=CrossSectionType.CIRCLE,
      compute_height_from_volume=lambda liquid_volume: (
        liquid_volume / (math.pi * ((well_diameter / 2) ** 2))
      ),
      name_prefix=name,
    ),
  )


# # # # # # # # # # thermo_AB_96_wellplate_300ul_Vb_MicroAmp # # # # # # # # # #


# Calibration data: measured height (mm) → known volume (uL)
_microamp_height_to_volume = {
  0.0: 0.0,
  1.69: 4.0,
  2.29: 8.0,
  3.89: 20.0,
  5.79: 40.0,
  8.49: 70.0,
  10.59: 120.0,
  12.69: 170.0,
  14.79: 220.0,
  16.59: 260.0,
  17.89: 290.0,
}
_microamp_volume_to_height = {v: k for k, v in _microamp_height_to_volume.items()}


def thermo_AB_96_wellplate_300ul_Vb_MicroAmp_Lid(name: str) -> Lid:
  raise NotImplementedError("This lid is not currently defined.")


# Height above the cavity bottom (mm) to volume (uL), linear between points: the calibration data,
# continued along its last segment to 5 % past the cavity's depth (22.5 mm).
_thermo_AB_96_wellplate_300ul_Vb_MicroAmp_height_volume_data = {
  **_microamp_height_to_volume,
  23.625: 422.346,
}


def thermo_AB_96_wellplate_300ul_Vb_MicroAmp(name: str, with_lid: bool = False) -> Plate:
  """Thermo Fisher Scientific cat. no.: N8010560/4316813 (w/o barcode)
  - alternative cat. no.: 4306737/4326659 (with barcode).
  - See `./engineering_diagrams/` directory for more part numbers.
  - Material: Polypropylene.
  - Sterilization compatibility: ?
  - Chemical resistance: ?
  - Thermal resistance: ?
  - Cleanliness: 'Certified DNA/RNase Free'.
  - Warning: NOT ANSI/SLAS-format!
  - optimal pickup_distance_from_top = 6 mm (i.e. pickup_distance_from_bottom=size_z-6).
  - total_volume = 300 ul.
  - working_volume = 200 ul (recommended by manufacturer).

  https://documents.thermofisher.com/TFS-Assets/LSG/manuals/cms_042421.pdf
  """
  return Plate(
    name=name,
    size_x=125.98,
    size_y=85.85,
    size_z=23.24,
    lid=thermo_AB_96_wellplate_300ul_Vb_MicroAmp_Lid(name + "_lid") if with_lid else None,
    model=thermo_AB_96_wellplate_300ul_Vb_MicroAmp.__name__,
    plate_type="semi-skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=10.6,
      dy=8.59,
      dz=0.0,  # check that plate is semi-skirted
      item_dx=9,
      item_dy=9,
      size_x=5.494,
      size_y=5.494,
      size_z=23.24,
      bottom_type=WellBottomType.V,
      material_z_thickness=0.74,
      cross_section_type=CrossSectionType.CIRCLE,
      height_volume_data=_thermo_AB_96_wellplate_300ul_Vb_MicroAmp_height_volume_data,
      max_volume=413.462,
      name_prefix=name,
    ),
  )


def thermo_AB_384_wellplate_40uL_Vb_MicroAmp(name: str) -> Plate:
  """Thermo Fisher Scientific cat. no.: 4309849, 4326270, 4343814 (with barcode), 4343370 (w/o barcode).

  https://documents.thermofisher.com/TFS-Assets/LSG/manuals/cms_042831.pdf

  The wells sit flush with the plate's own base: section A-A of drawing 4310286 dimensions 9.70
  from the underside to the top face, and the 0.61 below the wells is the wall at their bottom, not
  a standoff. So `dz` is zero because it was drawn that way, not because nobody measured it - and
  on a holder with a pedestal this plate comes to rest on its wells rather than on its skirt.
  """
  logger.info(
    "%s is one of the few skirted plates whose wells sit flush with its own base, so on a holder "
    "with a pedestal it comes to rest on its wells rather than on its skirt.",
    name,
  )
  diameter = 3.17
  return Plate(
    name=name,
    size_x=127.8,
    size_y=85.5,
    size_z=9.70,
    lid=None,
    model=thermo_AB_384_wellplate_40uL_Vb_MicroAmp.__name__,
    plate_type="skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=24,
      num_items_y=16,
      dx=12.15 - diameter / 2,
      dy=9 - diameter / 2,
      dz=0.0,
      item_dx=4.5,
      item_dy=4.5,
      size_x=diameter,
      size_y=diameter,
      size_z=9.70 - 0.61,
      bottom_type=WellBottomType.V,
      material_z_thickness=0.61,
      cross_section_type=CrossSectionType.CIRCLE,
      name_prefix=name,
    ),
  )


# # # # # # # # # # thermo_nunc_1_troughplate_90000uL_Fb_omnitray # # # # # # # # # #


def thermo_nunc_1_troughplate_90000uL_Fb_omnitray(name: str) -> Plate:
  """
  https://assets.fishersci.com/TFS-Assets/LSG/manuals/D03023.pdf

  - Brand: Thermo Scientific / Nunc
  - Part no.: 165218, 140156, 242811, 264728
  """

  return Plate(
    name=name,
    size_x=127.76,  # from spec
    size_y=85.47,  # from spec
    size_z=14.5,  # from spec
    lid=None,  # TODO: define a matching Lid if you use one with this tray
    model=thermo_nunc_1_troughplate_90000uL_Fb_omnitray.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=1,
      num_items_y=1,
      dx=(127.76 - 123.7) / 2,  # from spec
      dy=(85.47 - 81.3) / 2,  # from spec
      dz=14.5 - 11.7 - 2.5,  # from spec: plate_z - well_z - material_z_thickness
      item_dx=9.0,
      item_dy=9.0,
      size_x=123.7,  # from spec
      size_y=81.3,  # from spec
      size_z=11.7,  # from spec
      bottom_type=WellBottomType.FLAT,
      material_z_thickness=2.5,  # from spec
      cross_section_type=CrossSectionType.RECTANGLE,
      # compute_volume_from_height=None,
      # compute_height_from_volume=None,
      name_prefix=name,
    ),
  )


# # # # # # # # # # Thermo_TS_Nunc_96_wellplate_300uL_Fb # # # # # # # # # #


def Thermo_TS_Nunc_96_wellplate_300uL_Fb(name: str, with_lid: bool = False) -> Plate:
  """Thermo Scientific™ Nunc™ 96-Well Optical-Bottom Microplate, black, TC surface
  - Product Number: 165305
  - Max Volume: 400 uL
  - working volume: 50-300uL (in practice, although spec sheet says 50-200uL))
  - Manufacturer link: https://www.fishersci.com/shop/products/nunc-microwell-96-well-cell-culture-treated-flat-bottom-microplate/1256670#
  - Spec sheet info: https://documents.thermofisher.com/TFS-Assets/LCD/Schematics-%26-Diagrams/1653xx_0713.pdf
  """
  return Plate(
    name=name,
    size_x=127.76,  # from spec
    size_y=85.47,  # from spec
    size_z=14.86,  # from spec
    model="Thermo_TS_Nunc_96_wellplate_300uL_Fb",
    lid=Thermo_TS_Nunc_96_wellplate_300uL_Fb_Lid(name + "_lid") if with_lid else None,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,  # from spec
      num_items_y=8,  # from spec
      dx=11.095,  # from spec
      dy=8.025,  # from spec
      dz=1.98,  # from spec
      item_dx=9,  # from spec
      item_dy=9,  # from spec
      size_x=6.45,  # from spec
      size_y=6.45,  # from spec
      size_z=12.1,  # from spec
      bottom_type=WellBottomType.FLAT,  # flat bottom wells
      material_z_thickness=2.2,  # from spec
      name_prefix=name,
    ),
  )


def Thermo_TS_Nunc_96_wellplate_300uL_Fb_Lid(name: str) -> Lid:
  return Lid(
    name=name,
    size_x=127.25,  # from spec
    size_y=85.3,  # from spec
    size_z=9.1,  # from spec
    nesting_z_height=16.7 - 14.86,  # from spec: lid+plate_z - plate_z
    model="Thermo_TS_Nunc_96_assay_300uL_Fb_Lid",
  )


# # # # # # # # # # thermo_TS_nalgene_1_troughplate_300mL_Fb # # # # # # # # # #


def thermo_TS_nalgene_1_troughplate_300mL_Fb(name: str) -> Plate:
  """Thermo Fisher Scientific Nalgene 300mL Flat Bottom Reservoir
  - Product Number: 12001300 (non-sterile), 12001301 (sterile)
  - 1-well reservoir with SBS footprint
  - Max Volume: 300 mL
  - manufacturer_link: https://www.fishersci.com/shop/products/nalgene-disposable-polypropylene-robotic-reservoirs/12565572
  - Spec sheet info: https://assets.fishersci.com/TFS-Assets/LCD/Schematics-&-Diagrams/120013XX_0405.PDF
  """
  return Plate(
    name=name,
    size_x=127.8,  # from spec
    size_y=85.5,  # from spec
    size_z=39.9,  # from spec
    model=thermo_TS_nalgene_1_troughplate_300mL_Fb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=1,  # from spec
      num_items_y=1,  # from spec
      dx=(127.8 - 123.8) / 2,  # from spec
      dy=(85.5 - 82.1) / 2,  # from spec
      dz=3.3,  # from spec
      item_dx=0,  # from spec
      item_dy=0,  # from spec
      size_x=123.8,  # from spec
      size_y=82.1,  # from spec
      size_z=39.9 - 3.3 - 1.15,  # from spec/calculated
      bottom_type=WellBottomType.FLAT,  # from spec
      cross_section_type=CrossSectionType.RECTANGLE,  # rectangle wells
      material_z_thickness=1.15,  # measured.
      name_prefix=name,
    ),
  )
