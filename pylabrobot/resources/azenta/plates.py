import warnings

from pylabrobot.resources.plate import Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

# Height above the cavity bottom (mm) to volume (uL), linear between points.
_azenta_96_wellplate_200uL_Vb_4titudeframestar_height_volume_data = {
  0.0: 0.0,
  0.02: 1e-06,
  0.06: 1.8e-05,
  0.12: 0.000142,
  0.2: 0.00066,
  0.3: 0.002226,
  0.42: 0.006109,
  0.56: 0.014481,
  0.72: 0.030778,
  0.9: 0.060113,
  1.1: 0.109754,
  1.32: 0.189655,
  1.56: 0.313051,
  1.82: 0.497114,
  2.1: 0.763659,
  2.4: 1.139923,
  2.72: 1.65939,
  3.06: 2.362687,
  3.42: 3.298528,
  3.8: 4.52473,
  4.2: 6.109276,
  4.62: 8.131446,
  5.02: 10.43165,
  5.41: 13.056707,
  5.78: 15.923017,
  6.14: 19.087408,
  6.49: 22.541144,
  6.83: 26.272655,
  7.16: 30.267805,
  7.49: 34.648729,
  7.81: 39.282123,
  8.12: 44.147889,
  8.43: 49.39973,
  8.73: 54.863636,
  9.03: 60.716273,
  9.32: 66.75589,
  9.61: 73.183305,
  10.0: 82.362087,
  14.37: 186.185834,
}


def azenta_96_wellplate_200uL_Vb_4titudeframestar(name: str) -> Plate:
  """Azenta cat. no.: 4ti-0960.
  - Material: Polypropylene wells, polycarbonate frame
  - Sterilization compatibility: ?
  - Chemical resistance: ?
  - Thermal resistance: ?
  - Sealing options: ?
  - Cleanliness: ?
  - Automation compatibility: "Rigid frame eliminates warping and distortion during PCR. Ideal for use with robotic systems.' -> extra  rigid skirt option (4ti-0960/RIG) available.
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=16.1,
    lid=None,
    model="azenta_96_wellplate_200uL_Vb_4titudeframestar",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=11.0,
      dy=8.49,
      dz=0.8,
      item_dx=9,
      item_dy=9,
      size_x=5.5,
      size_y=5.5,
      size_z=15.1,
      bottom_type=WellBottomType.V,
      cross_section_type=CrossSectionType.CIRCLE,
      material_z_thickness=0.73,
      height_volume_data=_azenta_96_wellplate_200uL_Vb_4titudeframestar_height_volume_data,
      max_volume=203.5294,
      name_prefix=name,
    ),
  )


# --------------------------------------------------------------------------- #
# Deprecated function names (backward compatibility)
# --------------------------------------------------------------------------- #


def Azenta4titudeFrameStar_96_wellplate_200ul_Vb(
  name: str, with_lid: bool = False
) -> Plate:  # remove v1b1
  """Deprecated alias for azenta_96_wellplate_200uL_Vb_4titudeframestar().

  This alias will be removed in v1b1.
  Use `azenta_96_wellplate_200uL_Vb_4titudeframestar()` instead.
  """
  warnings.warn(
    "Azenta4titudeFrameStar_96_wellplate_200ul_Vb() is deprecated and will be removed in v1b1. "
    "Use azenta_96_wellplate_200uL_Vb_4titudeframestar() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return azenta_96_wellplate_200uL_Vb_4titudeframestar(name)
