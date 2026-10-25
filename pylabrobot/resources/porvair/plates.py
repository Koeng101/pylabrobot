from typing import Optional

from pylabrobot.resources.plate import Lid, Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

# # # # # # # # # # Porvair_6_reservoir_47ml_Vb # # # # # # # # # #


def Porvair_6_reservoir_47ml_Vb_Lid(name: str) -> Lid:
  raise NotImplementedError("This lid is not currently defined.")
  # See https://github.com/PyLabRobot/pylabrobot/pull/161.
  # return Lid(
  #   name=name,
  #   size_x=127.76,
  #   size_y=85.48,
  #   size_z=5,
  #   nesting_z_height=None, # measure overlap between lid and plate
  #   model="Porvair_6_reservoir_47ml_Vb_Lid",
  # )


#: Porvair_6_reservoir_47ml_Vb
# Height above the cavity bottom (mm) to volume (uL), linear between points.
_Porvair_6_reservoir_47ml_Vb_height_volume_data = {
  0.0: 0.0,
  0.01: 1.6048e-05,
  0.03: 0.000433296,
  0.055: 0.00266999,
  0.09: 0.011699,
  0.135: 0.0394841,
  0.19: 0.110073,
  0.25: 0.25075,
  0.32: 0.525861,
  0.4: 1.027072,
  0.49: 1.888031,
  0.59: 3.295922,
  0.7: 5.504464,
  0.815: 8.687478,
  0.94: 13.329212,
  1.07: 19.65949,
  1.22: 29.140729,
  1.38: 42.175299,
  1.54: 58.611533,
  1.695: 78.150187,
  1.84: 99.97108,
  1.98: 124.570867,
  2.115: 151.828056,
  2.245: 181.580811,
  2.375: 214.986781,
  2.5: 250.75,
  2.62: 288.618915,
  2.74: 330.120584,
  2.855: 373.455838,
  2.97: 420.426676,
  3.08: 468.892261,
  3.19: 520.946308,
  3.295: 574.099505,
  3.4: 630.750592,
  3.505: 691.011035,
  3.605: 751.859554,
  3.705: 816.179256,
  3.805: 884.066428,
  3.905: 955.617359,
  4.0: 1027.072,
  4.095: 1102.002638,
  4.19: 1180.491827,
  4.285: 1262.622123,
  4.38: 1348.47608,
  4.47: 1433.32107,
  4.56: 1521.652359,
  4.65: 1613.540142,
  4.74: 1709.054612,
  4.83: 1808.265964,
  4.915: 1905.423347,
  5.0: 2006.0,
  42.5: 47141.0,
}


def Porvair_6_reservoir_47ml_Vb(name: str, with_lid: bool = False) -> Plate:
  """Porvair cat. no.: 390015.
  - Material: Polypropylene
  - Sterilization compatibility: Autoclaving (15 minutes at 121°C) or Gamma Irradiation
  - Chemical resistance: "High chemical resistance"
  - Temperature resistance: high: -196°C to + 121°C
  - Cleanliness: 390015: Free of detectable DNase, RNase
  - ANSI/SLAS-format for compatibility with automated systems
  - Tolerances: "Uniform external dimensions and tolerances"
  - Each well is segmented into four V bottom wells similar to cor_axy_24_wellplate_10mL_Vb.
  - The bottom can only be reached when using 2 or 4 channels.
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=44,
    lid=Porvair_6_reservoir_47ml_Vb_Lid(name + "_lid") if with_lid else None,
    model="Porvair_6_reservoir_47ml_Vb",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=6,
      num_items_y=1,
      dx=9.3,
      dy=5.7,
      dz=0.97,
      item_dx=18.5,
      item_dy=6.9,
      size_x=16.8,
      size_y=70.8,
      size_z=42.5,
      material_z_thickness=1.4,
      bottom_type=WellBottomType.V,
      cross_section_type=CrossSectionType.RECTANGLE,
      height_volume_data=_Porvair_6_reservoir_47ml_Vb_height_volume_data,
      max_volume=47141.0,
      name_prefix=name,
    ),
  )


# Height above the cavity bottom (mm) to volume (uL), linear between points.
_Porvair_24_wellplate_Vb_height_volume_data = {
  0.0: 0.0,
  0.01: 6.87678e-07,
  0.03: 1.85673e-05,
  0.06: 0.000148538,
  0.1: 0.000687678,
  0.15: 0.00232091,
  0.21: 0.00636858,
  0.28: 0.0150959,
  0.36: 0.0320843,
  0.45: 0.0626646,
  0.55: 0.114412,
  0.66: 0.197705,
  0.78: 0.326339,
  0.91: 0.518214,
  1.05: 0.796073,
  1.2: 1.188307,
  1.36: 1.729823,
  1.53: 2.462971,
  1.71: 3.438533,
  1.9: 4.716781,
  2.08: 6.188351,
  2.255: 7.885415,
  2.425: 9.806638,
  2.585: 11.878636,
  2.74: 14.146096,
  2.895: 16.68517,
  3.045: 19.415421,
  3.19: 22.323227,
  3.33: 25.393211,
  3.47: 28.732496,
  3.605: 32.21816,
  3.74: 35.974911,
  3.87: 39.858213,
  4.0: 44.011371,
  4.125: 48.26772,
  4.25: 52.790007,
  4.375: 57.58629,
  4.495: 62.455978,
  4.615: 67.592738,
  4.735: 73.003701,
  4.85: 78.453106,
  4.965: 84.167162,
  5.08: 90.152145,
  5.19: 96.136211,
  5.3: 102.379389,
  5.41: 108.887173,
  5.52: 115.665052,
  5.63: 122.71852,
  5.735: 129.713504,
  5.84: 136.969373,
  5.945: 144.490902,
  6.05: 152.282869,
  6.155: 160.350049,
  6.255: 168.293316,
  6.355: 176.494668,
  6.455: 184.958232,
  6.555: 193.688133,
  6.655: 202.688498,
  6.755: 211.963453,
  6.85: 221.032757,
  6.945: 230.357139,
  7.04: 239.940137,
  7.135: 249.78529,
  7.23: 259.896133,
  7.325: 270.276205,
  7.42: 280.929044,
  7.515: 291.858187,
  7.605: 302.470191,
  7.695: 313.336363,
  7.785: 324.459711,
  7.875: 335.843242,
  7.965: 347.489964,
  8.055: 359.402886,
  8.145: 371.585015,
  8.235: 384.039359,
  8.325: 396.768926,
  8.415: 409.776725,
  8.5: 422.320053,
  8.585: 435.116772,
  8.67: 448.169418,
  8.755: 461.480524,
  8.84: 475.052624,
  8.925: 488.888251,
  9.01: 502.98994,
  9.095: 517.360224,
  9.18: 532.001638,
  9.265: 546.916715,
  9.35: 562.10799,
  9.435: 577.577996,
  9.515: 592.39489,
  9.595: 607.463045,
  9.675: 622.784574,
  9.755: 638.361589,
  9.835: 654.196202,
  9.915: 670.290527,
  9.995: 686.646675,
  10.075: 703.266759,
  10.155: 720.152892,
  10.235: 737.307186,
  10.315: 754.731754,
  10.395: 772.428709,
  10.475: 790.400162,
  10.555: 808.648227,
  10.635: 827.175016,
  10.71: 844.798897,
  10.785: 862.671348,
  10.86: 880.79411,
  10.935: 899.168922,
  11.01: 917.797526,
  11.085: 936.681663,
  11.16: 955.823073,
  11.235: 975.223496,
  11.31: 994.884674,
  11.385: 1014.808347,
  11.46: 1034.996256,
  11.535: 1055.450142,
  11.61: 1076.171744,
  12.05: 1199.333333,
  13.3: 1549.333334,
}


def Porvair_24_wellplate_Vb(name: str, lid: Optional[Lid] = None) -> Plate:
  """
  Porvair cat. no.: 390108
  - Material: Polypropylene
  - Tissue culture treated: No
  """

  well_kwargs = {
    "size_x": 8.0,
    "size_y": 35.0,
    "size_z": 13.30,
    # reality: multifaceted pyramid, v bottom pyramid is a good approximation
    "bottom_type": WellBottomType.V,
    "height_volume_data": _Porvair_24_wellplate_Vb_height_volume_data,
    "material_z_thickness": 1.0,  # measured
    "cross_section_type": CrossSectionType.RECTANGLE,
    "max_volume": 3500,  # according to porvair spec
  }

  return Plate(
    name=name,
    size_x=127.5,  # measured
    size_y=85.3,  # measured
    size_z=19.2,  # measured
    lid=lid,
    model=Porvair_24_wellplate_Vb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=2,
      dx=9.90,  # measured
      dy=6.85,  # measured
      dz=5.8,  # measured and calibrated manually
      item_dx=9.05,
      item_dy=36,
      name_prefix=name,
      **well_kwargs,
    ),
  )
