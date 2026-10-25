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
  0.14: 1.343734,
  0.28: 1.869681,
  0.425: 2.49287,
  0.57: 3.193083,
  0.72: 3.995542,
  0.87: 4.874468,
  1.025: 5.859939,
  1.185: 6.956284,
  1.345: 8.129681,
  1.51: 9.417044,
  1.68: 10.821946,
  1.855: 12.347663,
  2.035: 13.997176,
  2.22: 15.773161,
  2.41: 17.677997,
  2.605: 19.713766,
  2.805: 21.882271,
  3.01: 24.18505,
  3.22: 26.623402,
  3.435: 29.198413,
  3.66: 31.973525,
  3.89: 34.89038,
  4.125: 37.949507,
  4.37: 41.218948,
  4.62: 44.63491,
  4.875: 48.198025,
  5.135: 51.909216,
  5.4: 55.769812,
  5.67: 59.781672,
  5.945: 63.947323,
  6.22: 68.192198,
  6.495: 72.516212,
  6.765: 76.839412,
  7.035: 81.241376,
  7.3: 85.640852,
  7.555: 89.951215,
  7.805: 94.253743,
  8.05: 98.547739,
  8.285: 102.742613,
  8.515: 106.924649,
  8.74: 111.09329,
  8.955: 115.152599,
  9.165: 119.193442,
  9.37: 123.214734,
  9.57: 127.215182,
  9.765: 131.193264,
  9.955: 135.147197,
  10.14: 139.074923,
  10.32: 142.974094,
  10.495: 146.842069,
  10.665: 150.675907,
  10.83: 154.472373,
  10.995: 158.346515,
  11.155: 162.180748,
  11.31: 165.971065,
  11.465: 169.839208,
  11.615: 173.659675,
  11.76: 177.427708,
  11.905: 181.272177,
  12.045: 185.059258,
  12.185: 188.922843,
  12.32: 192.723399,
  12.455: 196.600029,
  12.59: 200.555238,
  12.72: 204.440617,
  12.85: 208.403568,
  12.975: 212.289468,
  13.1: 216.251444,
  13.225: 220.291691,
  13.345: 224.246039,
  13.465: 228.276593,
  13.585: 232.385397,
  13.7: 236.398351,
  13.815: 240.486938,
  13.93: 244.653045,
  14.04: 248.71232,
  14.15: 252.845972,
  14.26: 257.055727,
  14.37: 261.343331,
  14.475: 265.510295,
  14.58: 269.751366,
  14.685: 274.068128,
  14.79: 278.462179,
  14.895: 282.93514,
  14.995: 287.269967,
  15.095: 291.679288,
  15.195: 296.164553,
  15.295: 300.727228,
  15.395: 305.368794,
  15.49: 309.852719,
  15.585: 314.410494,
  15.68: 319.043429,
  15.775: 323.75285,
  15.87: 328.540093,
  15.965: 333.40651,
  16.055: 338.091069,
  16.145: 342.849081,
  16.235: 347.681729,
  16.325: 352.590204,
  16.415: 357.575709,
  16.505: 362.639457,
  16.59: 367.494832,
  16.675: 372.42213,
  16.76: 377.422398,
  16.845: 382.496694,
  16.93: 387.646083,
  17.015: 392.871638,
  17.1: 398.174442,
  17.185: 403.555585,
  17.27: 409.016165,
  17.35: 414.229094,
  17.43: 419.514301,
  17.51: 424.872723,
  17.59: 430.305304,
  17.67: 435.812995,
  17.75: 441.396751,
  17.83: 447.057536,
  17.91: 452.796321,
  17.99: 458.614081,
  18.065: 464.140833,
  18.14: 469.738676,
  18.215: 475.408433,
  18.29: 481.150928,
  18.365: 486.966994,
  18.44: 492.857465,
  18.515: 498.823183,
  18.59: 504.864994,
  18.665: 510.983751,
  18.74: 517.180309,
  18.815: 523.45553,
  18.89: 529.810281,
  18.96: 535.813905,
  19.03: 541.888282,
  19.1: 548.034127,
  19.17: 554.252162,
  19.24: 560.543112,
  19.31: 566.907705,
  19.38: 573.346673,
  19.45: 579.860754,
  19.52: 586.450686,
  19.59: 593.117215,
  19.66: 599.861089,
  19.73: 606.683059,
  19.8: 613.583881,
  19.87: 620.564315,
  19.935: 627.118099,
  20.0: 633.741801,
  20.065: 640.436038,
  20.13: 647.20143,
  20.195: 654.038601,
  20.26: 660.948176,
  20.3: 665.236483,
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
      max_volume=584.560065130625,
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
