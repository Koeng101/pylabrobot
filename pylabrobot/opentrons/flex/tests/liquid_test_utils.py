"""Read the pipetting destination from captured coordinate and Z moves."""

from unittest.mock import AsyncMock

from pylabrobot.resources.store import handles


async def pipetting_location(io: AsyncMock, target: handles.Resource, channels: int = 1) -> dict:
  """Express the last pipetting destination relative to a cavity's primary nozzle."""
  commands = io.submit_command.await_args_list
  index = max(i for i, c in enumerate(commands) if c.args[1] == "moveToCoordinates")
  xy = commands[index].args[2]["coordinates"]
  z = xy["z"]
  origin = await target.get_absolute_location(x="c", y="c", z="cavity_bottom")
  return {
    "origin": "bottom",
    "offset": {
      "x": round(xy["x"] - origin.x + (49.5 if channels == 96 else 0), 6),
      "y": round(xy["y"] - origin.y - (31.5 if channels > 1 else 0), 6),
      "z": round(z - origin.z, 6),
    },
  }
