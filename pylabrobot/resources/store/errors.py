"""What a store refuses, said as the protocol says it, and as PLR raises it."""

from __future__ import annotations

from typing import Dict, Optional, Type

from pylabrobot.resources.errors import (
  HasTipError,
  NoTipError,
  TooLittleLiquidError,
  TooLittleVolumeError,
)
from pylabrobot.resources.store.v1 import types_pb2 as pb


class StoreError(ValueError):
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


# The exception PLR raises for each tracking problem a store reports.
PLR_ERRORS: Dict[int, Type[Exception]] = {
  pb.PROBLEM_HAS_TIP: HasTipError,
  pb.PROBLEM_NO_TIP: NoTipError,
  pb.PROBLEM_TOO_LITTLE_LIQUID: TooLittleLiquidError,
  pb.PROBLEM_TOO_LITTLE_VOLUME: TooLittleVolumeError,
}


def plr_error(error: StoreError, otherwise: Optional[Type[Exception]] = None) -> Exception:
  """The exception PLR raises for a store's refusal, carrying the store's message.

  A tracking problem in `PLR_ERRORS` becomes PLR's own error for it: `HasTipError`, `NoTipError`,
  `TooLittleLiquidError`, `TooLittleVolumeError`. Any other problem becomes `otherwise`, or stays
  the `StoreError` itself when `otherwise` is unset.

  Use it as `raise plr_error(error) from error`.

  Args:
    error: What the store refused with.
    otherwise: The exception for every other problem: `ValueError` for a holder refusing what
      is put in it, say.
  """
  kind = PLR_ERRORS.get(error.problem, otherwise)
  return error if kind is None else kind(str(error))
