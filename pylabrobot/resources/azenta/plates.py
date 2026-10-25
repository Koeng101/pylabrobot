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
  0.68: 0.025928,
  1.105: 0.111257,
  1.455: 0.253998,
  1.77: 0.457258,
  2.06: 0.720848,
  2.33: 1.043061,
  2.585: 1.424372,
  2.825: 1.859076,
  3.055: 2.351124,
  3.28: 2.909802,
  3.495: 3.52033,
  3.705: 4.193788,
  3.91: 4.929151,
  4.11: 5.724892,
  4.305: 6.579022,
  4.495: 7.489123,
  4.68: 8.452388,
  4.86: 9.465655,
  5.04: 10.556828,
  5.215: 11.695123,
  5.385: 12.876534,
  5.555: 14.134942,
  5.72: 15.432275,
  5.885: 16.806654,
  6.045: 18.215067,
  6.205: 19.700045,
  6.365: 21.263614,
  6.52: 22.85518,
  6.675: 24.524246,
  6.825: 26.214998,
  6.975: 27.981725,
  7.125: 29.826099,
  7.27: 31.684371,
  7.415: 33.618267,
  7.56: 35.629296,
  7.705: 37.718966,
  7.845: 39.812614,
  7.985: 41.982338,
  8.125: 44.229493,
  8.265: 46.555439,
  8.4: 48.874206,
  8.535: 51.268715,
  8.67: 53.740184,
  8.805: 56.28983,
  8.935: 58.820068,
  9.065: 61.425016,
  9.195: 64.10576,
  9.325: 66.863388,
  9.455: 69.698985,
  9.585: 72.61364,
  9.71: 75.491759,
  9.865: 79.154718,
  15.1: 203.52939,
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
      max_volume=203.52938905975373,
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
