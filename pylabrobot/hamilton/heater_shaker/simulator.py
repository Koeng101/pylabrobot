"""A simulated link to Hamilton heater shakers: what they are plugged into, answering for them.

Each module `T<index>` it is sent commands for is a heater shaker of its own. It reaches a
temperature the moment it is told to, and starts and stops shaking at once. Replies have the form
a device's do: `T1TAid0004er00`, with what a read reads after it.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# What a simulated heater shaker reads before it is told to heat, in Celsius.
ROOM_TEMPERATURE = 25.0


@dataclass
class SimulatedHeaterShaker:
  """One simulated heater shaker's state."""

  temperature: float = ROOM_TEMPERATURE
  heating: bool = False
  locked: bool = False
  shaking: bool = False
  lock_initialized: bool = False
  drive_initialized: bool = False


@dataclass
class HeaterShakerSimulator:
  """Something heater shakers are plugged into, simulated.

  Attributes:
    heater_shakers: each simulated heater shaker, by its module, "T1" say.
    sent: every command sent, as module, command and parameters, in order.
  """

  heater_shakers: Dict[str, SimulatedHeaterShaker] = field(default_factory=dict)
  sent: List[Dict[str, Any]] = field(default_factory=list)
  _id: int = 0

  def _answer(self, module: str, command: str, hs: SimulatedHeaterShaker, **kwargs: Any) -> str:
    """What a read reads after the reply's error field; empty for a command that only acts."""
    if command == "LI":
      hs.lock_initialized = True
    elif command == "SI":
      hs.drive_initialized = True
    elif command == "LP":
      hs.locked = str(kwargs["lp"]) == "1"
    elif command == "SB":
      hs.shaking = True
    elif command == "SC":
      hs.shaking = False
    elif command == "TA":
      hs.heating = True
      hs.temperature = int(kwargs["ta"]) / 10
    elif command == "TO":
      hs.heating = False
    elif command == "RD":
      return f"rd{int(hs.shaking)}"
    elif command == "RT":
      reading = f"{round(hs.temperature * 10):+05d}"
      return f"rt{reading} {reading}"
    return ""

  async def send_command(self, module: str, command: str, **kwargs: Any) -> Optional[str]:
    """Answer a command as the heater shaker on `module` would."""
    self.sent.append({"module": module, "command": command, **kwargs})
    hs = self.heater_shakers.setdefault(module, SimulatedHeaterShaker())
    self._id = self._id % 9999 + 1
    reply = f"{module}{command}id{self._id:04d}er00{self._answer(module, command, hs, **kwargs)}"
    logger.debug("simulated heater shaker: %s%s %s -> %s", module, command, kwargs, reply)
    return reply
