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
  0.02: 3.1e-05,
  0.06: 0.000832,
  0.12: 0.006659,
  0.2: 0.030827,
  0.3: 0.10404,
  0.42: 0.285486,
  0.56: 0.676707,
  0.72: 1.438249,
  0.86: 2.450936,
  0.99: 3.738885,
  1.11: 5.269938,
  1.23: 7.170541,
  1.34: 9.271521,
  1.45: 11.747368,
  1.55: 14.349332,
  1.65: 17.309655,
  1.75: 20.651458,
  1.84: 24.004355,
  1.93: 27.701833,
  2.02: 31.760745,
  2.11: 36.197947,
  2.2: 41.030293,
  2.28: 45.671063,
  2.36: 50.6492,
  2.44: 55.976541,
  2.52: 61.664924,
  2.6: 67.726187,
  2.68: 74.172166,
  2.75: 80.137292,
  2.82: 86.413959,
  2.89: 93.010099,
  2.96: 99.933641,
  3.03: 107.192516,
  3.1: 114.794653,
  3.17: 122.747983,
  3.24: 131.060436,
  3.31: 139.739943,
  3.38: 148.794432,
  3.45: 158.231835,
  3.52: 168.060081,
  3.59: 178.287102,
  3.65: 187.376522,
  3.71: 196.769738,
  3.77: 206.471746,
  3.83: 216.487538,
  3.89: 226.822109,
  3.95: 237.480452,
  4.01: 248.467561,
  4.07: 259.788431,
  4.13: 271.448055,
  4.19: 283.451427,
  4.25: 295.803542,
  4.31: 308.509392,
  4.37: 321.573972,
  4.43: 335.002276,
  4.49: 348.799298,
  4.55: 362.970032,
  4.61: 377.519471,
  4.67: 392.452609,
  4.73: 407.774442,
  4.79: 423.489961,
  4.84: 436.890563,
  4.89: 450.570918,
  4.94: 464.533914,
  4.99: 478.782443,
  40.54: 10752.726667,
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
      max_volume=11174.6667,
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
