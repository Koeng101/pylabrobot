import warnings

from pylabrobot.resources.plate import Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import CrossSectionType, Well, WellBottomType

# Height above the cavity bottom (mm) to volume (uL), linear between points.
_agilent_96_wellplate_150uL_Vb_height_volume_data = {
  0.0: 0.0,
  0.01: 6.86291e-08,
  0.03: 1.85299e-06,
  0.06: 1.48239e-05,
  0.1: 6.86291e-05,
  0.15: 0.000231623,
  0.21: 0.000635574,
  0.28: 0.00150655,
  0.36: 0.00320196,
  0.45: 0.00625383,
  0.55: 0.0114182,
  0.66: 0.0197306,
  0.78: 0.0325681,
  0.91: 0.0517169,
  1.05: 0.0794468,
  1.2: 0.118591,
  1.36: 0.172634,
  1.53: 0.245801,
  1.71: 0.34316,
  1.9: 0.470727,
  2.1: 0.635574,
  2.31: 0.84595,
  2.53: 1.111399,
  2.76: 1.442899,
  3.0: 1.852987,
  3.245: 2.345053,
  3.485: 2.904804,
  3.715: 3.518722,
  3.94: 4.197563,
  4.155: 4.922907,
  4.365: 5.707702,
  4.57: 6.550239,
  4.77: 7.448412,
  4.965: 8.399749,
  5.16: 9.428827,
  5.35: 10.509206,
  5.535: 11.637546,
  5.72: 12.843892,
  5.9: 14.094984,
  6.08: 15.424791,
  6.255: 16.795405,
  6.43: 18.244899,
  6.6: 19.730603,
  6.77: 21.294848,
  6.935: 22.890113,
  7.1: 24.563124,
  7.26: 26.261432,
  7.42: 28.036272,
  7.58: 29.889329,
  7.735: 31.760659,
  7.89: 33.70851,
  8.045: 35.734416,
  8.195: 37.770734,
  8.345: 39.882977,
  8.495: 42.072537,
  8.645: 44.340802,
  8.79: 46.609578,
  8.935: 48.954455,
  9.08: 51.376687,
  9.225: 53.877529,
  9.365: 56.367905,
  9.505: 58.933863,
  9.645: 61.576535,
  9.785: 64.297049,
  9.925: 67.096535,
  10.06: 69.87189,
  10.195: 72.722741,
  10.33: 75.650101,
  10.465: 78.654984,
  10.6: 81.738402,
  10.73: 84.782792,
  10.86: 87.901852,
  10.99: 91.096486,
  11.12: 94.3676,
  11.25: 97.716098,
  11.38: 101.142884,
  11.51: 104.648864,
  11.635: 108.095524,
  11.76: 111.617043,
  11.885: 115.214226,
  12.01: 118.887877,
  12.135: 122.6388,
  12.26: 126.467799,
  12.385: 130.375678,
  12.5: 134.041287,
}


def agilent_96_wellplate_150uL_Vb(name: str) -> Plate:
  """
  Part number: 5042-8502

  Well Number                  | 96
  Well Form                    | Round
  Well Diameter (A)            | 6.4 mm
  Well Bottom Shape            | Conical
  Well Volume                  | 150 µL
  Well Working Volume          | 120 µL
  Well Depth (B)               | 14.0 mm
  Plate Height (C)             | 15.9 mm
  Plate Width (D)              | 85.5 mm
  Plate Length (E)             | 127.8 mm
  Row Distance (F)             | 9 mm
  Column Distance (G)          | 9 mm
  Row Offset (H)               | 11.2 mm
  Column Offset (I)            | 14.4 mm
  Frame Footprint              | SBS
  Frame Numbering              | Alphanumeric
  Skirted                      | Yes
  Color                        | Clear
  Material                     | Well: polypropylene
                               | Frame: polycarbonate
  Temperature Range            | -80 to 120 °C
  Autoclavable                 | Yes
  Sterile                      | Nonsterile
  Stackable                    | Yes
  Pack Size                    | 25, p/n 5042-8502
  Compatible Closing Mat       | p/n 5067-5154 (not recommended for
                               | chromatography autosamplers)
  Agilent Instrument Definition| Not applicable

  https://www.agilent.com/cs/library/datasheets/public/ds-well-plate-specifications-5994-6035en-agilent.pdf
  """

  diameter = 6.4  # from spec

  well_kwargs = {
    "size_x": diameter,  # from spec
    "size_y": diameter,  # from spec
    "size_z": 14.0,  # from spec
    "bottom_type": WellBottomType.V,
    "cross_section_type": CrossSectionType.CIRCLE,
    "material_z_thickness": 0.88,  # measured using z-probing
    "max_volume": 190,  # measured
    "height_volume_data": _agilent_96_wellplate_150uL_Vb_height_volume_data,
  }

  return Plate(
    name=name,
    size_x=127.8,  # standard
    size_y=85.5,  # standard
    size_z=15.9,  # from spec
    lid=None,
    model=agilent_96_wellplate_150uL_Vb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=14.4 - diameter / 2,  # from spec
      dy=11.2 - diameter / 2,  # from spec
      dz=15.9 - 14.0 - 0.88,  # spec - spec - measured manually
      item_dx=9.0,  # standard
      item_dy=9.0,  # standard
      name_prefix=name,
      **well_kwargs,
    ),
    plate_type="skirted",
  )


def agilent_96_wellplate_150uL_Ub(name: str) -> Plate:
  """Deprecated for agilent_96_wellplate_150uL_Vb. Use that one instead."""
  warnings.warn(
    "agilent_96_wellplate_150uL_Ub is deprecated. Use agilent_96_wellplate_150uL_Vb instead.",
    DeprecationWarning,
  )
  return agilent_96_wellplate_150uL_Vb(name)


def agilent_2_reservoir_144mL_Vb(name: str) -> Plate:
  """Agilent 2 Reservoir 144mL V bottom
  Part Number: 203852-100
  - Max Volume: 144 mL
  Spec: https://www.agilent.com/cs/library/datasheets/public/ds-cell-analysis-5994-4426en-agilent.pdf
  """
  return Plate(
    name=name,
    size_x=127.76,  # from spec
    size_y=85.47,  # from spec
    size_z=44.04,  # from spec
    model="agilent_2_reservoir_144mL_Vb",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=2,  # from spec
      num_items_y=1,  # from spec
      dx=10.66,  # measured
      dy=7.12,  # measured
      dz=2.54,  # measured
      item_dx=54,  # from spec
      item_dy=0,  # from spec
      size_x=53.22,  # from spec
      size_y=71.23,  # from spec
      size_z=39.22,  # from spec
      bottom_type=WellBottomType.V,
      cross_section_type=CrossSectionType.RECTANGLE,
      material_z_thickness=1.15,
      name_prefix=name,
    ),
  )


def agilent_1_troughplate_86mL_Vb(name: str) -> Plate:
  """Agilent 1 Troughplate 86mL V bottom
  Part Number: 201254-100
  - Max Volume: 86 mL
  Spec: https://labrulez.com/pdf/br_microplate_dimension_guide_5994_5247en_agilent_1368d1a796/br-microplate-dimension-guide-5994-5247en-agilent.pdf
  """
  return Plate(
    name=name,
    size_x=127.76,  # from spec
    size_y=85.47,  # from spec
    size_z=19.05,  # from spec
    model="Agilent_1_troughplate_86mL_Vb",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=1,  # from spec
      num_items_y=1,  # from spec
      dx=9.3,  # measured
      dy=6.21,  # measured
      dz=19.05 - 17.91,  # measured
      item_dx=0,  # from spec
      item_dy=0,  # from spec
      size_x=106.22,  # from spec
      size_y=70.46,  # from spec
      size_z=12.7,  # from spec
      bottom_type=WellBottomType.V,
      cross_section_type=CrossSectionType.RECTANGLE,
      material_z_thickness=1.15,
    ),
  )


# --------------------------------------------------------------------------- #
# Deprecated function names (backward compatibility)
# --------------------------------------------------------------------------- #


def Agilent_2_reservoir_144mL_Vb(name: str) -> Plate:  # remove v1b1
  """Deprecated alias for agilent_2_reservoir_144mL_Vb().

  This alias will be removed in v1b1.
  Use `agilent_2_reservoir_144mL_Vb()` instead.
  """
  warnings.warn(
    "Agilent_2_reservoir_144mL_Vb() is deprecated and will be removed in v1b1. "
    "Use agilent_2_reservoir_144mL_Vb() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return agilent_2_reservoir_144mL_Vb(name)
