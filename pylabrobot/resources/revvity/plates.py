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
  0.43: 0.025186,
  0.7: 0.108655,
  0.925: 0.250714,
  1.125: 0.451036,
  1.31: 0.712144,
  1.48: 1.026926,
  1.64: 1.397287,
  1.795: 1.832092,
  1.945: 2.330842,
  2.085: 2.871258,
  2.22: 3.465875,
  2.355: 4.137393,
  2.485: 4.861085,
  2.61: 5.632167,
  2.735: 6.480761,
  2.855: 7.371779,
  2.975: 8.340938,
  5.3: 28.224854,
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
      max_volume=28.22485379801409,
      name_prefix=name,
    ),
  )
