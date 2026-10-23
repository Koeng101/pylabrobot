import warnings

from pylabrobot.resources.plate import Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import CrossSectionType, Well, WellBottomType

# Height above the cavity bottom (mm) to volume (uL), linear between points.
_agilent_96_wellplate_150uL_Vb_height_volume_data = {
  0.0: 0.0,
  0.02: 1e-06,
  0.06: 1.5e-05,
  0.12: 0.000119,
  0.2: 0.000549,
  0.3: 0.001853,
  0.42: 0.005085,
  0.56: 0.012052,
  0.72: 0.025616,
  0.9: 0.050031,
  1.1: 0.091345,
  1.32: 0.157845,
  1.56: 0.260545,
  1.82: 0.413735,
  2.1: 0.635574,
  2.4: 0.948729,
  2.72: 1.381069,
  3.06: 1.966404,
  3.42: 2.745281,
  3.8: 3.765818,
  4.2: 5.084596,
  4.62: 6.767597,
  5.06: 8.891194,
  5.48: 11.294063,
  5.89: 14.023436,
  6.28: 16.997595,
  6.66: 20.273617,
  7.03: 23.843748,
  7.39: 27.697582,
  7.74: 31.82229,
  8.09: 36.337422,
  8.43: 41.114146,
  8.76: 46.133974,
  9.09: 51.546621,
  9.41: 57.18438,
  9.72: 63.0242,
  10.03: 69.248656,
  10.33: 75.650101,
  10.63: 82.434374,
  10.93: 89.612591,
  11.22: 96.936452,
  11.51: 104.648864,
  11.79: 112.473436,
  12.07: 120.678627,
  12.35: 129.273474,
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
