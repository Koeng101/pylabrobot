from pylabrobot.resources.plate import Lid, Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

# # # # # # # # # # Eppendorf_96_wellplate_250ul_Vb # # # # # # # # # #


# results_measurement_fitting_dict = {
#     "Volume (ul)": [0, 4, 8, 20, 70, 120, 170, 220, 260],
#     "Observed Height (mm)": [0, 0.45, 1.45, 2.55, 6.45, 9.05, 11.6, 13.15, 14.349],
#     "Predicted Height (mm)": [0.118, 0.637, 1.139, 2.49, 6.516, 9.177, 11.359, 13.31, 14.291],
#     "Relative Deviation (%)": [0, 41.525, -21.793, -2.365, 1.024, 1.399, -2.078, 1.216, -0.408]
# }


def Eppendorf_96_wellplate_250ul_Vb_Lid(name: str) -> Lid:
  raise NotImplementedError("This lid is not currently defined.")
  # See https://github.com/PyLabRobot/pylabrobot/pull/161.
  # return Lid(
  #   name=name,
  #   size_x=123.0,
  #   size_y=81.0,
  #   size_z=5,
  #   nesting_z_height=None, # measure overlap between lid and plate
  #   model="Eppendorf_96_wellplate_250ul_Vb_Lid",
  # )


# Height above the cavity bottom (mm) to volume (uL), linear between points.
_Eppendorf_96_wellplate_250ul_Vb_height_volume_data = {
  0.0: 0.894866,
  0.26: 1.789927,
  0.57: 3.193083,
  0.91: 5.121391,
  1.26: 7.496918,
  1.63: 10.400677,
  2.02: 13.856706,
  2.44: 17.985973,
  2.88: 22.715587,
  3.35: 28.171169,
  3.85: 34.37749,
  4.39: 41.489316,
  4.96: 49.402775,
  5.56: 58.13779,
  6.17: 67.414526,
  6.78: 77.08188,
  7.37: 86.816436,
  7.93: 96.434706,
  8.46: 105.917483,
  8.96: 115.24792,
  9.42: 124.207525,
  9.86: 133.160365,
  10.27: 141.883089,
  10.66: 150.562039,
  11.03: 159.178618,
  11.38: 167.708142,
  11.72: 176.380735,
  12.04: 184.922703,
  12.35: 193.57821,
  12.65: 202.339,
  12.94: 211.193841,
  13.22: 220.12855,
  13.49: 229.126072,
  13.75: 238.166594,
  14.0: 247.227704,
  14.25: 256.669831,
  14.49: 266.111588,
  14.73: 275.941734,
  14.96: 285.744378,
  15.19: 295.938464,
  15.41: 306.071925,
  15.63: 316.595592,
  15.84: 327.019843,
  16.05: 337.8289,
  16.25: 348.49451,
  16.45: 359.53558,
  16.65: 370.965397,
  16.84: 382.196138,
  17.03: 393.801783,
  17.22: 405.794376,
  17.4: 417.523819,
  17.58: 429.622144,
  17.76: 442.100116,
  17.94: 454.968673,
  18.11: 467.490955,
  18.28: 480.38103,
  18.3: 481.922135,
}


def Eppendorf_96_wellplate_250ul_Vb(name: str, with_lid: bool = False) -> Plate:
  """Eppendorf cat. no.: 0030133374
  - Material: polycarbonate (frame), polypropylene (wells).
  - part of the twin.tec(R) product line.
  - 'Can be divided into 4 segments of 24 wells each to prevent waste and save money'.
  - Colour: clear.
  - Sterilization compatibility & Thermal resistance: read cpnsumables manual in
    `./engineering_diagrams/`
  - Chemical resistance: ?
  - Cleanliness: ?
  - Automation compatibility: inconsistent information -> says ANSI/SLAS 1-2004 and 4-2004
    compatible, however, engineering_diagram shows footprint is NOT 1-2004 compatible?
  - Plate (apparently) used for NEB's 96-well-format chemically competent cells...
  - total_volume = 250 ul.
  """
  return Plate(
    name=name,
    size_x=123.0,
    size_y=81.0,
    size_z=20.3,
    lid=Eppendorf_96_wellplate_250ul_Vb_Lid(name + "_lid") if with_lid else None,
    model="Eppendorf_96_wellplate_250ul_Vb",
    plate_type="non-skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=6.76,
      dy=8.26,
      dz=0.0,  # check that plate is non-skirted
      item_dx=9,
      item_dy=9,
      size_x=5.48,
      size_y=5.48,
      size_z=19.5,
      bottom_type=WellBottomType.V,
      material_z_thickness=1.2,  # engineering_diagram says 0.8 but could not replicate
      cross_section_type=CrossSectionType.CIRCLE,
      height_volume_data=_Eppendorf_96_wellplate_250ul_Vb_height_volume_data,
      max_volume=584.5601,
      name_prefix=name,
    ),
  )


def eppendorf_96_wellplate_500ul_Vb(name: str) -> Plate:
  """Eppendorf Deepwell Plate 96/500uL, cat. no.: 951032107

  https://archive.vn/WCuMF
  """

  material_z_thickness = 1.05  # measured with ztouch_probe_z_height_using_channel
  well_diameter_top = 7.0  # from spec

  return Plate(
    name=name,
    size_x=127.8,  # w
    size_y=85.5,  # l
    size_z=27.1,  # h
    lid=None,
    model=eppendorf_96_wellplate_500ul_Vb.__name__,
    plate_type="skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=14.4 - well_diameter_top / 2,  # P1 - well width / 2
      dy=11.2 - well_diameter_top / 2,  # P3 - well width / 2
      dz=2.1 - material_z_thickness,  # b - material_z_thickness
      item_dx=9.0,
      item_dy=9.0,
      size_x=well_diameter_top,
      size_y=well_diameter_top,
      size_z=21.4 + 2.6,  # well depth: h1 + h2
      bottom_type=WellBottomType.V,
      material_z_thickness=material_z_thickness,
      cross_section_type=CrossSectionType.CIRCLE,
      compute_volume_from_height=None,
      compute_height_from_volume=None,
      name_prefix=name,
    ),
  )


def eppendorf_96_wellplate_1000ul_Vb(name: str) -> Plate:
  """Eppendorf Deepwell Plate 96/1000uL, cat. no.: 951032921

  https://archive.vn/uMRwv
  """

  material_z_thickness = 1.05  # measured with ztouch_probe_z_height_using_channel
  well_diameter_top = 7.0  # from spec

  return Plate(
    name=name,
    size_x=127.8,  # w
    size_y=85.5,  # l
    size_z=44.1,  # h
    lid=None,
    model=eppendorf_96_wellplate_1000ul_Vb.__name__,
    plate_type="skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=14.4 - well_diameter_top / 2,  # P1 - well width / 2
      dy=11.2 - well_diameter_top / 2,  # P3 - well width / 2
      dz=3.2 - material_z_thickness,  # b - material_z_thickness
      item_dx=9.0,  # P2: well spacing in x
      item_dy=9.0,  # P4: well spacing in y
      size_x=well_diameter_top,  # well top diameter
      size_y=well_diameter_top,
      size_z=38.7 + 2.4,  # well depth: h1 + h2
      bottom_type=WellBottomType.V,
      material_z_thickness=material_z_thickness,
      cross_section_type=CrossSectionType.CIRCLE,
      compute_volume_from_height=None,
      compute_height_from_volume=None,
      name_prefix=name,
    ),
  )


def eppendorf_96_wellplate_2000ul_vb(name: str) -> Plate:
  """Eppendorf Deepwell Plate 96/2000 µL

  https://archive.vn/wSbxT
  """

  material_z_thickness = 1.3  # measured with ztouch_probe_z_height_using_channel
  well_diameter_top = 8.2  # from spec (d)

  return Plate(
    name=name,
    size_x=127.8,  # l
    size_y=85.5,  # w
    size_z=44.1,  # h
    lid=None,
    model=eppendorf_96_wellplate_2000ul_vb.__name__,
    plate_type="skirted",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=14.4 - well_diameter_top / 2,  # P1 - well width / 2
      dy=11.2 - well_diameter_top / 2,  # P3 - well width / 2
      dz=1.5 - material_z_thickness,  # b - material_z_thickness (2000 µL spec)
      item_dx=9.0,  # P2
      item_dy=9.0,  # P4
      size_x=well_diameter_top,
      size_y=well_diameter_top,
      size_z=38.1 + 3.1,  # h1 + h2 (2000 µL spec)
      bottom_type=WellBottomType.V,
      material_z_thickness=material_z_thickness,
      cross_section_type=CrossSectionType.RECTANGLE,
      compute_volume_from_height=None,
      compute_height_from_volume=None,
      name_prefix=name,
    ),
  )
