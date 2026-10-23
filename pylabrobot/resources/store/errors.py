"""What a store refuses, said as the protocol says it."""

from __future__ import annotations

from pylabrobot.resources.store.v1 import types_pb2 as pb


class StoreError(Exception):
  """A request the store cannot carry out, with the protocol's name for why.

  Attributes:
    problem: why, as `Issue.problem` carries it.
    resource_name: the resource it is about, or empty.
  """

  def __init__(self, problem: pb.Problem, message: str, resource_name: str = ""):
    super().__init__(message)
    self.problem = problem
    self.resource_name = resource_name
