"""Corning plates."""

import warnings

from pylabrobot.resources.plate import Lid, Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

# # # # # # # # # # cor_96_wellplate_360uL_Fb # # # # # # # # # #

# Well tapers from 6.35 mm (bottom) to 6.86 mm (top) over 10.67 mm depth.
_cor_96_wellplate_360uL_Fb_height_volume_data = {
  0.0: 0.0,
  0.45: 20.0,  # "dead volume" to cover the full flat bottom and ensure LLD detectability
  1.69: 50.0,
  3.22: 100.0,
  4.72: 150.0,
  6.19: 200.0,
  7.72: 250.0,
  8.99: 300.0,
  10.62: 350.0,
  10.95: 360.0,
}


def cor_96_wellplate_360uL_Fb(name: str, with_lid: bool = False) -> Plate:
  """
  Corning cat. no.s: 3603
  - manufacturer_link: https://ecatalog.corning.com/life-sciences/b2b/UK/en/Microplates/
    Assay-Microplates/96-Well-Microplates/Corning%C2%AE-96-well-Black-Clear-and-White-Clear-
    Bottom-Polystyrene-Microplates/p/3603
  - brand: Corning
  - distributor: (Fisher Scientific, 10530753)
  - material: Polypropylene
  - tc_treated: Yes
  - tech_drawing: tech_drawings/Cor_96_wellplate_360ul_Fb.pdf
  - sterile: yes
  - notes:
      - Well bottom (i.e. material_z_thickness) is 60% thinner than conventional polystyrene
        microplates, resulting in lower background fluorescence & enabling readings down to 340 nm.
      - Opaque walls prevent well-to-well cross-talk.
  """

  # This used to be Cos_96_EZWash in the Esvelt lab

  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=14.2,
    lid=cor_96_wellplate_360uL_Fb_lid(name=name + "_lid") if with_lid else None,
    model=cor_96_wellplate_360uL_Fb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=10.87,  # 14.3-6.86/2
      dy=7.77,  # 11.2-6.86/2
      dz=3.03,
      item_dx=9.0,
      item_dy=9.0,
      size_x=6.86,  # top
      size_y=6.86,  # top
      size_z=10.67,
      material_z_thickness=0.5,
      bottom_type=WellBottomType.FLAT,
      cross_section_type=CrossSectionType.CIRCLE,
      max_volume=360,
      height_volume_data=_cor_96_wellplate_360uL_Fb_height_volume_data,
      name_prefix=name,
    ),
  )


def cor_96_wellplate_360uL_Fb_lid(name: str) -> Lid:
  """
  - brand: Corning
  """

  return Lid(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=8.9,  # measure the total z height
    nesting_z_height=7.6,  # measure overlap between lid and plate
    model=cor_96_wellplate_360uL_Fb_lid.__name__,
  )


# # # # # # # # # # cor_96_wellplate_2mL_Vb # # # # # # # # # #


# Height above the cavity bottom (mm) to volume (uL), linear between points.
_cor_96_wellplate_2mL_Vb_height_volume_data = {
  0.0: 0.0,
  0.01: 1.2675e-06,
  0.03: 3.42225e-05,
  0.055: 0.00021088,
  0.09: 0.000924007,
  0.135: 0.00311853,
  0.19: 0.00869378,
  0.25: 0.0198047,
  0.32: 0.0415334,
  0.4: 0.08112,
  0.49: 0.14912,
  0.59: 0.260318,
  0.7: 0.434752,
  0.815: 0.686153,
  0.94: 1.052765,
  1.07: 1.552742,
  1.21: 2.245454,
  1.35: 3.118525,
  1.48: 4.108971,
  1.605: 5.240504,
  1.725: 6.506018,
  1.84: 7.895896,
  1.955: 9.470835,
  2.065: 11.161129,
  2.17: 12.951712,
  2.275: 14.924238,
  2.375: 16.980044,
  2.475: 19.216468,
  2.57: 21.515297,
  2.665: 23.990517,
  2.76: 26.64865,
  2.85: 29.341516,
  2.94: 32.209943,
  3.03: 35.259476,
  3.12: 38.495658,
  3.205: 41.728432,
  3.29: 45.137309,
  3.375: 48.726958,
  3.46: 52.50205,
  3.54: 56.228663,
  3.62: 60.127574,
  3.7: 64.202677,
  3.78: 68.457868,
  3.86: 72.897038,
  3.94: 77.524082,
  4.025: 82.641,
  42.0: 2393.04,
}


def cor_96_wellplate_2mL_Vb(name: str) -> Plate:
  """
  Corning cat. no.: 3960
  - manufacturer_link: https://ecatalog.corning.com/life-sciences/b2b/UK/en/Genomics-%26-
    Molecular-Biology/Automation-Consumables/Deep-Well-Plate/Corning%C2%AE-96-well-
    Polypropylene-Storage-Blocks/p/3960
  - brand: Corning
  - distributor: (Fisher Scientific, 10708212)
  - material: Polypropylene
  - sterile: yes
  - notes:
      - features uniform skirt heights for greater robotic gripping surface.
  """
  return Plate(
    name=name,
    size_x=127.0,
    size_y=86.0,
    size_z=43.5,
    lid=None,
    model=cor_96_wellplate_2mL_Vb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,
      num_items_y=8,
      dx=9.6,
      dy=7.0,
      dz=1.2,
      item_dx=9.0,
      item_dy=9.0,
      size_x=8.0,
      size_y=8.0,
      size_z=42.0,
      bottom_type=WellBottomType.V,
      material_z_thickness=1.25,
      cross_section_type=CrossSectionType.RECTANGLE,
      height_volume_data=_cor_96_wellplate_2mL_Vb_height_volume_data,
      max_volume=2393.04,
      name_prefix=name,
    ),
  )


# --------------------------------------------------------------------------- #
# Deprecated function names (backward compatibility)
# --------------------------------------------------------------------------- #


def Cor_96_wellplate_2mL_Vb(name: str, with_lid: bool = False) -> Plate:  # remove v1b1
  """Deprecated alias for cor_96_wellplate_2mL_Vb().

  This alias will be removed in v1b1.
  Use `cor_96_wellplate_2mL_Vb()` instead.
  """
  warnings.warn(
    "Cor_96_wellplate_2mL_Vb() is deprecated and will be removed in v1b1. "
    "Use cor_96_wellplate_2mL_Vb() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return cor_96_wellplate_2mL_Vb(name)


def Cor_96_wellplate_360ul_Fb(name: str, with_lid: bool = False) -> Plate:  # remove v1b1
  """Deprecated alias for cor_96_wellplate_360uL_Fb().

  This alias will be removed in v1b1.
  Use `cor_96_wellplate_360uL_Fb()` instead.
  """
  warnings.warn(
    "Cor_96_wellplate_360ul_Fb() is deprecated and will be removed in v1b1. "
    "Use cor_96_wellplate_360uL_Fb() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return cor_96_wellplate_360uL_Fb(name, with_lid)


def Cor_96_wellplate_360ul_Fb_Lid(name: str) -> Lid:  # remove v1b1
  """Deprecated alias for cor_96_wellplate_360uL_Fb_lid().

  This alias will be removed in v1b1.
  Use `cor_96_wellplate_360uL_Fb_lid()` instead.
  """
  warnings.warn(
    "Cor_96_wellplate_360ul_Fb_Lid() is deprecated and will be removed in v1b1. "
    "Use cor_96_wellplate_360uL_Fb_lid() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return cor_96_wellplate_360uL_Fb_lid(name)
