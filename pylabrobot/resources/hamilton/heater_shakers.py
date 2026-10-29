"""Hamilton heater shakers, as the plate holders they are on a deck."""

from pylabrobot.resources.carrier import PlateHolder
from pylabrobot.resources.coordinate import Coordinate

# The category a heater shaker's plate holder has, by which a heater shaker finds its own.
HEATER_SHAKER_CATEGORY = "heater_shaker"


def hamilton_heater_shaker(name: str) -> PlateHolder:
  """Hamilton Heater Shaker (cat. no. 199027, 199033 or 199034): the plate holder on top of it.

  The footprint and plate position are those PyLabRobot's Hamilton heater shaker guide gives for
  every variant. A plate stands on the top face.
  """
  return PlateHolder(
    name=name,
    size_x=146.2,
    size_y=103.8,
    size_z=74.11,
    child_location=Coordinate(x=9.66, y=9.22, z=74.11),
    pedestal_size_z=0,
    category=HEATER_SHAKER_CATEGORY,
    model=hamilton_heater_shaker.__name__,
  )
