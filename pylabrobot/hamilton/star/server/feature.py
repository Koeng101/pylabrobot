"""What every served feature knows: the server its driver calls, and that its settings and
constants are not assigned on a client.

Settings are the server's, from its settings file; constants are the code's. Assigning either on a
client would change nothing the server does, so it is refused once the client has taken the
feature up from the server's description.
"""

from typing import TYPE_CHECKING, Any, Dict, Literal

from pylabrobot.hamilton.star.server.v1 import types_pb2 as tpb

if TYPE_CHECKING:
  from pylabrobot.hamilton.star.server.client import STARServer

SETTING_MESSAGE = (
  "{} is set where the STAR is served, in the STAR server's settings file, not on a client"
)
CONSTANT_MESSAGE = "{} is a constant of the STAR's code, not set on a client"


def x_arm_side(side: Literal["left", "right"]) -> "tpb.XArmSide":
  """The `XArmSide` an arm's side is."""
  return tpb.X_ARM_SIDE_LEFT if side == "left" else tpb.X_ARM_SIDE_RIGHT


class Feature:
  """A served feature.

  Attributes:
    _held: its settings, as the server's description has them.
    _ready: whether it has been taken up from a description; from then on, assigning a setting or
      constant is refused.
  """

  _driver: Any
  _held: Dict[str, Any]
  _ready: bool

  @property
  def _star_server(self) -> "STARServer":
    server: "STARServer" = self._driver._star_server
    return server
