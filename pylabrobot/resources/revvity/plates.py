from pylabrobot.resources.plate import Lid, Plate
from pylabrobot.resources.utils import create_ordered_items_2d
from pylabrobot.resources.well import (
  CrossSectionType,
  Well,
  WellBottomType,
)

# # # # # # # # # # Revvity_384_wellplate_28ul_Ub # # # # # # # # # #


def Revvity_384_wellplate_28ul_Ub_Lid(name: str) -> Lid:
  raise NotImplementedError("This lid is not currently defined.")
  # See https://github.com/PyLabRobot/pylabrobot/pull/161.
  # return Lid(
  #   name=name,
  #   size_x=127.76,
  #   size_y=85.48,
  #   size_z=None,           # measure the total z height
  #   nesting_z_height=None, # measure overlap between lid and plate
  #   model="Revvity_384_wellplate_28ul_Ub_Lid",
  # )


#: Revvity_384_wellplate_28ul_Ub
# Height above the cavity bottom (mm) to volume (uL), linear between points.
_Revvity_384_wellplate_28ul_Ub_height_volume_data = {
  0.0: 0.0,
  0.02: 3e-06,
  0.06: 6.8e-05,
  0.12: 0.000547,
  0.2: 0.002534,
  0.3: 0.008553,
  0.42: 0.023469,
  0.56: 0.055631,
  0.72: 0.118236,
  0.9: 0.230931,
  1.1: 0.421631,
  1.32: 0.728578,
  1.55: 1.179639,
  1.77: 1.756604,
  1.98: 2.458949,
  2.17: 3.236929,
  2.36: 4.163801,
  2.54: 5.191049,
  2.71: 6.304663,
  2.88: 7.567135,
  3.07: 9.151695,
  4.3: 19.671868,
}


def Revvity_384_wellplate_28ul_Ub(name: str, with_lid: bool = False) -> Plate:
  """Revvity cat. no.: 6008280. nickname "ProxiPlate-384 Plus"
  - Material: Polystyrene
  - Colour: white
  - "shallow-well"
  - Sterilization compatibility: ?
  - Chemical resistance:?
  - Thermal resistance: ?
  - Surface treatment: non-treated
  - Sealing options: ?
  - Cleanliness: non-sterile
  - Automation compatibility: not specifically declared
  - Total volume = 28 ul
  """
  return Plate(
    name=name,
    size_x=127.76,
    size_y=85.48,
    size_z=14.35,
    lid=Revvity_384_wellplate_28ul_Ub_Lid(name + "_lid") if with_lid else None,
    model="Revvity_384_wellplate_28ul_Ub",
    ordered_items=create_ordered_items_2d(
      Well,
      num_items_x=24,
      num_items_y=16,
      dx=8.83,
      dy=5.69,
      dz=8.2,
      item_dx=4.5,
      item_dy=4.5,
      size_x=3.3,
      size_y=3.3,
      size_z=5.3,
      bottom_type=WellBottomType.U,
      material_z_thickness=1.0,
      cross_section_type=CrossSectionType.CIRCLE,
      height_volume_data=_Revvity_384_wellplate_28ul_Ub_height_volume_data,
      max_volume=28.2249,
      name_prefix=name,
    ),
  )
