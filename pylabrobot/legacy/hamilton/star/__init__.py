"""The v1 Hamilton STAR as it was before it moved onto a resource server, its resources PLR
objects. Kept for the 3D visualizer, which draws PLR resources, until it reads from a
resource server; new code uses `pylabrobot.hamilton.star`."""

from pylabrobot.legacy.hamilton.star.device import STAR, STARDevice, STARlet, STARPlus
from pylabrobot.legacy.hamilton.star.driver.master import STARDriver
from pylabrobot.legacy.hamilton.star.driver.simulator import STARSimulationDriver

__all__ = [
  "STAR",
  "STARDevice",
  "STARDriver",
  "STARlet",
  "STARPlus",
  "STARSimulationDriver",
]
