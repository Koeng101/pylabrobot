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
  0.02: 1e-05,
  0.06: 0.000274,
  0.12: 0.00219,
  0.2: 0.01014,
  0.3: 0.034222,
  0.42: 0.093907,
  0.56: 0.222593,
  0.72: 0.473092,
  0.9: 0.924007,
  1.1: 1.687043,
  1.3: 2.784697,
  1.49: 4.192825,
  1.67: 5.903334,
  1.84: 7.895896,
  2.0: 10.14,
  2.15: 12.59689,
  2.3: 15.421672,
  2.44: 18.412699,
  2.58: 21.767426,
  2.72: 25.506724,
  2.85: 29.341516,
  2.98: 33.542603,
  3.11: 38.126693,
  3.23: 42.712553,
  3.35: 47.652138,
  3.47: 52.958587,
  3.59: 58.645044,
  3.71: 64.724648,
  3.82: 70.654212,
  3.93: 76.935294,
  4.12: 88.4208,
  40.75: 2316.99,
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
