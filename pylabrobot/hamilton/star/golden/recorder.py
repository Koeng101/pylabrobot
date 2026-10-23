"""What a simulated STAR is sent, step by step, and what its resources are left as.

The seam is `STARSimulationDriver`: its `_send` assembles every command without an id, so what it
writes is deterministic, and logs it through `_log_exchange`. The recorder wraps both on the
instance, so the subsystem locks and the order commands go out in stay the driver's own.

A command the simulated device answers with an error never reaches `_log_exchange`, so the wrap on
`_send` writes it instead, followed by ` -> ` and the reply the error was raised from.

Only the commands written are recorded, not what the simulator answered: what it answers is taken
from the resource model, and the model is what the snapshots pin.
"""

import dataclasses
import enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, cast

from pylabrobot.hamilton.protocol.text.framing import assemble_channel_command
from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.errors import STARFirmwareError, check_fw_string_error
from pylabrobot.hamilton.star.driver.simulator import STARSimulationDriver
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.resource import Resource
from pylabrobot.testing.golden import snapshot_changes, snapshot_resources

# What a hook given to `STARRecorder.fail` is handed: the command's own parameters.
Hook = Callable[[Dict[str, Any]], None]


def jsonable(value: Any) -> Any:
  """A call's result as a golden file can hold it."""
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  if isinstance(value, enum.Enum):
    return value.name
  if isinstance(value, Coordinate):
    return [value.x, value.y, value.z]
  if isinstance(value, Resource):
    return value.name
  if dataclasses.is_dataclass(value) and not isinstance(value, type):
    return jsonable(dataclasses.asdict(value))
  if isinstance(value, dict):
    return {str(key): jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [jsonable(item) for item in value]
  return type(value).__name__


def described(error: BaseException) -> str:
  """An error as a step records it: its class, and the reply or the message it carries."""
  if isinstance(error, STARFirmwareError):
    return f"{type(error).__name__}: {error.raw_response}"
  return f"{type(error).__name__}: {error}"


class STARRecorder:
  """Records each step of a scenario on a simulated STAR: what was sent, what the call returned or
  raised, and what it changed in the device's resource tree.

  A step's resources are the entries `snapshot_resources` gives that the step added or changed,
  and the names of the ones it removed; the record ends with the whole tree. Recording the whole
  tree after every step would repeat hundreds of unchanged entries per step.
  """

  def __init__(self, device: STARDevice):
    self.device = device
    self.driver = cast(STARSimulationDriver, device.driver)
    self.steps: List[Dict[str, Any]] = []
    self._sent: List[str] = []
    self._snapshot = snapshot_resources(device)
    self._rules: List[Dict[str, Any]] = []

    log = self.driver._log_exchange

    def logged(written: str, read: Optional[str]) -> None:
      self._sent.append(written)
      log(written, read)

    self.driver._log_exchange = logged  # type: ignore[method-assign]

    send = self.driver._send

    async def sent(module: str, command: str, **kwargs: Any) -> Any:
      try:
        return await send(module, command, **kwargs)
      except STARFirmwareError as error:
        # Assembled as `_send` assembles it, since a refused command is not logged.
        parameters = {
          key: value
          for key, value in kwargs.items()
          if key not in ("auto_id", "tip_pattern", "write_timeout", "read_timeout", "fmt")
        }
        carries_a_list = any(isinstance(value, list) for value in parameters.values())
        written = assemble_channel_command(
          module=module,
          command=command,
          id_=None,
          tip_pattern=kwargs.get("tip_pattern"),
          num_channels=self.driver.num_channels if carries_a_list else 0,
          **parameters,
        )
        self._sent.append(f"{written} -> {error.raw_response}")
        raise

    self.driver._send = sent  # type: ignore[method-assign, assignment]

    answer = self.driver._answer

    async def answered(module: str, command: str, **kwargs: Any) -> Any:
      result = await answer(module, command, **kwargs)
      if (module, command) == ("C0", "TR"):
        # `tips_mounted` stands for a tip the device holds that the model does not; a `fail` hook
        # sets it for the channels a failed pick-up left holding one. A drop lets them go.
        for channel, involved in enumerate(kwargs.get("tm", [])):
          if int(involved):
            self.driver.tips_mounted[channel] = False
      for rule in self._rules:
        if rule["times"] == 0 or (module, command) != (rule["module"], rule["command"]):
          continue
        if rule["skip"] > 0:
          rule["skip"] -= 1
          continue
        rule["times"] -= 1
        if rule["before"] is not None:
          rule["before"](kwargs)
        if rule["reply"] is not None:
          check_fw_string_error(rule["reply"])
        if rule["rewrite"] is not None and result is not None:
          value, source = result
          result = rule["rewrite"](value), source
      return result

    self.driver._answer = answered  # type: ignore[method-assign]

  def fail(
    self,
    module: str,
    command: str,
    reply: str,
    before: Optional[Hook] = None,
    skip: int = 0,
  ) -> None:
    """Have the simulated device answer one command with an error.

    The simulator answers it first, so the model moves as a device that ran the command would;
    `before` then puts right whatever the device got only part way through; and the error is
    raised from `reply`, as the driver parses a real one.

    Args:
      module: the module the command is addressed to.
      command: the two-letter command code.
      reply: the firmware's reply, carrying the error.
      before: called with the command's parameters before the error is raised.
      skip: how many of the command to let through first.
    """
    self._rules.append(
      {
        "module": module,
        "command": command,
        "reply": reply,
        "before": before,
        "rewrite": None,
        "skip": skip,
        "times": 1,
      }
    )

  def answer(self, module: str, command: str, rewrite: Callable[[Any], Any]) -> None:
    """Have the simulated device answer the next of a read with something other than the model.

    Args:
      module: the module the read is addressed to.
      command: the two-letter command code.
      rewrite: given what the simulator answered, returns what the device answers instead.
    """
    self._rules.append(
      {
        "module": module,
        "command": command,
        "reply": None,
        "before": None,
        "rewrite": rewrite,
        "skip": 0,
        "times": 1,
      }
    )

  def built(self, call: str) -> None:
    """Record the device as the scenario built it, before anything was sent: the whole tree.

    Args:
      call: how it was built, as a scenario writes it.
    """
    self.steps.append({"call": call, "sent": [], **snapshot_changes([], self._snapshot)})

  async def step(self, call: str, action: Awaitable[Any]) -> Any:
    """Run one step and record it.

    Args:
      call: the call, as a scenario writes it.
      action: the call itself.

    Returns:
      What the call returned, or None when it raised: what it raised is recorded instead.
    """
    self._sent = []
    entry: Dict[str, Any] = {"call": call}
    result: Any = None
    try:
      result = await action
      entry["sent"] = self._sent
      entry["result"] = jsonable(result)
    except Exception as error:
      entry["sent"] = self._sent
      entry["error"] = described(error)
    snapshot = snapshot_resources(self.device)
    entry.update(snapshot_changes(self._snapshot, snapshot))
    self._snapshot = snapshot
    self.steps.append(entry)
    return result

  def record(self) -> Dict[str, Any]:
    """The scenario's record: every step, and the whole tree after the last."""
    return {"steps": self.steps, "resources": self._snapshot}
