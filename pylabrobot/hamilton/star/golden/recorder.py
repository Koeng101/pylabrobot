"""What a simulated STAR is sent, step by step, and what its resources are left as.

The seam is `STARSimulationDriver`: its `_send` assembles every command without an id, so what it
writes is deterministic, and logs it through `_log_exchange`. The recorder wraps both on the
instance, so the subsystem locks and the order commands go out in stay the driver's own.

A command the simulated device answers with an error never reaches `_log_exchange`, so the wrap on
`_send` writes it instead, followed by ` -> ` and the reply the error was raised from.

Only the commands written are recorded, not what the simulator answered: what it answers is taken
from the resource model, and the model is what the snapshots pin.

Commands the device sends from tasks it runs together, with `asyncio.gather`, are recorded per
task rather than as one stream: how such tasks interleave depends on how often each gives way to
the others, a resource server call among them, so only each task's own order is fixed. Where a step
ran tasks together and more than one of them sent something, its `sent` holds, at that point,

  {"concurrently": [{"task": "<coroutine>", "sent": [...]}, ...]}

one entry per task that sent anything, in the order the tasks were made, each `sent` laid out the
same way. Tasks run together of which only one sent anything are recorded inline, since nothing
ran beside it.
"""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union, cast

from pylabrobot.hamilton.protocol.text.framing import assemble_channel_command
from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.errors import STARFirmwareError, check_fw_string_error
from pylabrobot.hamilton.star.driver.simulator import STARSimulationDriver
from pylabrobot.testing import recorder as recording
from pylabrobot.testing.golden import snapshot_changes, snapshot_server

# What a hook given to `STARRecorder.fail` is handed: the command's own parameters.
Hook = Callable[[Dict[str, Any]], None]


class _Sender:
  """What one task sent: commands, and groups of tasks it ran together, in the order they came."""

  def __init__(self, name: str):
    self.name = name
    self.items: List[Union[str, "_Together"]] = []


class _Together:
  """Tasks one task made together, as one `asyncio.gather` makes them."""

  def __init__(self) -> None:
    self.tasks: List["asyncio.Future[Any]"] = []
    self.senders: List[_Sender] = []

  def running(self) -> bool:
    return not all(task.done() for task in self.tasks)


def _laid_out(sender: _Sender) -> List[Any]:
  """What a task sent as a step records it: its commands in order, and, where it ran tasks
  together of which more than one sent anything, what each of them sent."""
  out: List[Any] = []
  for item in sender.items:
    if isinstance(item, str):
      out.append(item)
      continue
    sent = [(member.name, _laid_out(member)) for member in item.senders]
    sent = [(name, commands) for name, commands in sent if commands]
    if len(sent) == 1:
      out.extend(sent[0][1])
    elif sent:
      out.append({"concurrently": [{"task": name, "sent": commands} for name, commands in sent]})
  return out


def described(error: BaseException) -> str:
  """An error as a step records it: its class, and the reply or the message it carries."""
  if isinstance(error, STARFirmwareError):
    return f"{type(error).__name__}: {error.raw_response}"
  return recording.described(error)


class STARRecorder(recording.Recorder):
  """Records each step of a scenario on a simulated STAR: what was sent, what the call returned or
  raised, and what it changed in the device's resource tree.

  A step's resources are the entries `snapshot_store` gives that the step added or changed,
  and the names of the ones it removed; the record ends with the whole tree. Recording the whole
  tree after every step would repeat hundreds of unchanged entries per step.
  """

  def __init__(self, device: STARDevice):
    super().__init__()
    self.device = device
    self.driver = cast(STARSimulationDriver, device.driver)
    self._rules: List[Dict[str, Any]] = []

    # Which task sent each command: every task made from here on is noted with the task that made
    # it, and what a task not noted sends is the step's own.
    self._root = _Sender("step")
    self._senders: Dict["asyncio.Future[Any]", _Sender] = {}
    loop = asyncio.get_running_loop()
    make_task = loop.get_task_factory()

    def noted(
      loop: asyncio.AbstractEventLoop, coro: Coroutine[Any, Any, Any], **kwargs: Any
    ) -> "asyncio.Future[Any]":
      parent = self._sender(loop)
      task: "asyncio.Future[Any]" = (
        make_task(loop, coro, **kwargs)
        if make_task is not None
        else asyncio.Task(coro, loop=loop, **kwargs)
      )
      last = parent.items[-1] if parent.items else None
      together = last if isinstance(last, _Together) and last.running() else _Together()
      if together is not last:
        parent.items.append(together)
      sender = _Sender(coro.__qualname__)
      together.tasks.append(task)
      together.senders.append(sender)
      self._senders[task] = sender
      return task

    # Python 3.11 and later also hand the factory a `context`, which it passes on.
    loop.set_task_factory(noted)  # type: ignore[arg-type]

    log = self.driver._log_exchange

    def logged(written: str, read: Optional[str]) -> None:
      self._sender().items.append(written)
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
        self._sender().items.append(f"{written} -> {error.raw_response}")
        raise

    self.driver._send = sent  # type: ignore[method-assign, assignment]

    answer = self.driver._answer

    async def answered(module: str, command: str, **kwargs: Any) -> Any:
      result = await answer(module, command, **kwargs)
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

  def _sender(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> _Sender:
    """Where a command the current task sends is recorded."""
    task = asyncio.current_task(loop)
    return self._root if task is None else self._senders.get(task, self._root)

  def take_sent(self) -> List[Any]:
    """What was sent since the last call, per task where tasks ran together."""
    taken = _laid_out(self._root)
    self._root = _Sender("step")
    self._senders.clear()
    return taken

  def failed(self, entry: Dict[str, Any], error: BaseException) -> None:
    entry["error"] = described(error)

  async def snapshot(self) -> List[Dict[str, Any]]:
    """The device's tree as the server holds it now."""
    assert self.device.body is not None, "the device's resources have not been made"
    return await snapshot_server(self.device.server, self.device.body)

  async def built(self, call: str) -> None:
    """Record the device as the scenario built it, before anything was sent: the whole tree.

    Args:
      call: how it was built, as a scenario writes it.
    """
    self.steps.append({"call": call, "sent": [], **snapshot_changes([], await self.mark())})

  async def step(self, call: str, action: recording.Action) -> Any:  # type: ignore[override]
    """Run one step and record it.

    Args:
      call: the call, as a scenario writes it.
      action: the call itself.

    Returns:
      What the call returned, or None when it raised: what it raised is recorded instead.
    """
    self.take_sent()
    entry: Dict[str, Any] = {"call": call}
    result, error = await self.outcome(action)
    entry["sent"] = self.take_sent()
    self.add_outcome(entry, result, error)
    entry.update(await self.changes())
    self.steps.append(entry)
    return result

  def record(self) -> Dict[str, Any]:
    """The scenario's record: every step, and the whole tree after the last."""
    return {"steps": self.steps, "resources": self.resources}
