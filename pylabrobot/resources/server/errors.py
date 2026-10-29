"""What a resource server refuses, said as the protocol says it, and as PLR raises it."""

from __future__ import annotations

from typing import Dict, Type

from pylabrobot.resources.errors import (
  HasTipError,
  NoTipError,
  TooLittleLiquidError,
  TooLittleVolumeError,
)
from pylabrobot.resources.server.v1 import types_pb2 as pb


class ServerError(ValueError):
  """A request the store cannot carry out, with the protocol's name for why.

  It is a `ValueError`, the exception PLR's resource tree raises for most of what the store
  refuses (a name taken, a holder already full, a plate not skirted), so a refusal reached through
  a handle is caught as PLR's was. `plr_error` turns it into PLR's own exception where that is
  another class.

  Attributes:
    problem: why, as `Issue.problem` carries it.
    resource_name: the resource it is about, or empty.
  """

  def __init__(self, problem: pb.Problem, message: str, resource_name: str = ""):
    super().__init__(message)
    self.problem = problem
    self.resource_name = resource_name


# The exception PLR raises for each tracking problem a server reports.
PLR_ERRORS: Dict[int, Type[Exception]] = {
  pb.PROBLEM_HAS_TIP: HasTipError,
  pb.PROBLEM_NO_TIP: NoTipError,
  pb.PROBLEM_TOO_LITTLE_LIQUID: TooLittleLiquidError,
  pb.PROBLEM_TOO_LITTLE_VOLUME: TooLittleVolumeError,
}


def plr_error(error: ServerError) -> Exception:
  """The exception PLR raises for a server's refusal, carrying the server's message: for a
  tracking problem in `PLR_ERRORS`, PLR's own error for it; for any other, the `ServerError`
  itself. Use it as `raise plr_error(error) from error`."""
  kind = PLR_ERRORS.get(error.problem)
  return error if kind is None else kind(str(error))
