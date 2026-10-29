import warnings
from typing import Optional

from pylabrobot.resources.plate import Lid, Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

# # # # # # # # # # cor_axy_24_wellplate_10mL_Vb # # # # # # # # # #


# Height above the cavity bottom (mm) to volume (uL), linear between points.
_cor_axy_24_wellplate_10mL_Vb_height_volume_data = {
  0.0: 0.0,
  0.42: 0.285486,
  0.68: 1.211611,
  0.9: 2.80908,
  1.095: 5.059166,
  1.275: 7.986696,
  1.44: 11.505992,
  1.595: 15.635747,
  1.745: 20.474951,
  1.89: 26.01489,
  2.03: 32.234779,
  2.165: 39.103018,
  2.295: 46.578409,
  2.42: 54.61132,
  2.54: 63.14482,
  2.66: 72.523957,
  2.775: 82.342783,
  2.89: 93.010099,
  3.0: 104.04,
  3.11: 115.909157,
  3.22: 128.648342,
  3.325: 141.648353,
  3.43: 155.495899,
  3.535: 170.217745,
  3.635: 185.075881,
  3.735: 200.774428,
  3.835: 217.336508,
  3.93: 233.891388,
  4.025: 251.266294,
  4.12: 269.481048,
  4.215: 288.555473,
  4.31: 308.509392,
  4.4: 328.242347,
  4.49: 348.799298,
  4.58: 370.197101,
  4.67: 392.452609,
  4.76: 415.582678,
  4.845: 438.245962,
  4.93: 461.718565,
  5.02: 487.446667,
  42.0: 11174.666667,
}


def cor_axy_24_wellplate_10mL_Vb(name: str) -> Plate:
  """
  Corning cat. no.: P-DW-10ML-24-C-S, P-DW-10ML-24-C
  - manufacturer_link: https://ecatalog.corning.com/life-sciences/b2b/UK/en/Genomics-&-Molecular-Biology/Automation-Consumables/Deep-Well-Plate/Axygen%C2%AE-Deep-Well-and-Assay-Plates/p/P-DW-10ML-24-C
  - brand: Axygen
  - distributor: (Fisher Scientific, 12557837)
  - material: Polypropylene
  - sterile: yes
  - autoclavable: yes
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=44.24,
    lid=None,
    model=cor_axy_24_wellplate_10mL_Vb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=6,
      num_items_y=4,
      dx=9.8,
      dy=7.2,
      dz=1.2,
      item_dx=18,
      item_dy=18,
      size_x=17.0,
      size_y=17.0,
      size_z=42,
      material_z_thickness=1.46,
      bottom_type=WellBottomType.V,
      height_volume_data=_cor_axy_24_wellplate_10mL_Vb_height_volume_data,
      max_volume=11174.666666666666,
      cross_section_type=CrossSectionType.RECTANGLE,
      name_prefix=name,
    ),
  )


# # # # # # # # # # cor_axy_96_wellplate_500uL_Ub # # # # # # # # # #


def cor_axy_96_wellplate_500uL_Ub(name: str) -> Plate:
  """
  Axygen 96w Shallow Well Plate 500uL U Bottom
  - Product number: P-96-450V-C-S
  - manufacturer_link: https://ecatalog.corning.com/life-sciences/b2c/US/en/Genomics-&-Molecular-Biology/Automation-Consumables/Deep-Well-Plate/Axygen%C2%AE-Deep-Well-and-Assay-Plates/p/P-96-450V-C-S
  - Spec sheet info: https://www.corning.com/catalog/cls/documents/selection-guides/CLS-A-PSG-001.pdf
  - working volume: 450uL
  - brand: Axygen
  - material: Polypropylene
  - sterile: yes
  """
  return Plate(
    name=name,
    size_x=127.0,  # measured
    size_y=85.51,  # measured
    size_z=14.82,  # measured
    model=cor_axy_96_wellplate_500uL_Ub.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=12,  # from spec
      num_items_y=8,  # from spec
      dx=9.6,  # measured
      dy=7.0,  # measured
      dz=1.2,  # measured
      item_dx=9.0,  # measured
      item_dy=9.0,  # measured
      size_x=8.0,  # measured
      size_y=8.0,  # measured
      size_z=14.82 - 2.57,  # measured
      bottom_type=WellBottomType.U,
      material_z_thickness=1.18,  # measured
      cross_section_type=CrossSectionType.CIRCLE,
      name_prefix=name,
    ),
  )


# # # # # # # # # # cor_axy_1_troughplate_rowVb # # # # # # # # # #

# Liquid height over the cavity bottom (mm) -> volume (uL). The 100 mL point is set by 48 mL drawn
# by hand lowering the surface 5.86 mm, as searched with the 96-head's cLLD.
_cor_axy_1_troughplate_rowVb_height_volume_data = {
  0.0: 0.0,
  4.95: 15_000.0,
  6.4: 30_000.0,
  10.19: 60_000.0,
  15.97: 100_000.0,
  22.07: 150_000.0,
  27.98: 200_000.0,
  34.74: 250_000.0,
  39.98: 290_000.0,
}


def cor_axy_1_troughplate_rowVb(name: str, lid: Optional[Lid] = None) -> Plate:
  """
  Axygen single-well reservoir, 8 V-bottom trenches across the rows
  - Corning cat. no.: RES-SW8-HP-SI
  - brand: Axygen
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=43.5,
    lid=lid,
    model=cor_axy_1_troughplate_rowVb.__name__,
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=1,
      num_items_y=1,
      dx=(127.76 - 116.5) / 2,
      dy=(85.48 - 70.5) / 2,
      dz=3.2,
      item_dx=None,
      item_dy=None,
      name_prefix=name,
      size_x=116.5,
      size_y=70.5,
      size_z=39.98,
      max_volume=290_000,
      bottom_type=WellBottomType.V,
      cross_section_type=CrossSectionType.RECTANGLE,
      height_volume_data=_cor_axy_1_troughplate_rowVb_height_volume_data,
      material_z_thickness=2.0,
    ),
  )


# --------------------------------------------------------------------------- #
# Deprecated function names (backward compatibility)
# --------------------------------------------------------------------------- #


def Cor_Axy_24_wellplate_10mL_Vb(name: str, with_lid: bool = False) -> Plate:  # remove v1b1
  """Deprecated alias for cor_axy_24_wellplate_10mL_Vb().

  This alias will be removed in v1b1.
  Use `cor_axy_24_wellplate_10mL_Vb()` instead.
  """
  warnings.warn(
    "Cor_Axy_24_wellplate_10mL_Vb() is deprecated and will be removed in v1b1. "
    "Use cor_axy_24_wellplate_10mL_Vb() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return cor_axy_24_wellplate_10mL_Vb(name)


def Cor_Axy_96_wellplate_500uL_Ub(name: str, with_lid: bool = False) -> Plate:  # remove v1b1
  """Deprecated alias for cor_axy_96_wellplate_500uL_Ub().

  This alias will be removed in v1b1.
  Use `cor_axy_96_wellplate_500uL_Ub()` instead.
  """
  warnings.warn(
    "Cor_Axy_96_wellplate_500uL_Ub() is deprecated and will be removed in v1b1. "
    "Use cor_axy_96_wellplate_500uL_Ub() instead.",
    DeprecationWarning,
    stacklevel=2,
  )
  return cor_axy_96_wellplate_500uL_Ub(name)
