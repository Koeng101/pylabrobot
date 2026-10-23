"""A fake Opentrons robot server and a step recorder for the Flex and OT-2 golden tests.

`FakeRobotServer` is the device's `HTTP` transport with the network replaced: every request a
device makes reaches `_make_request`, which records it and answers as a robot server would. The
golden record is therefore the exact HTTP traffic, method, path and JSON body, in order.

`Recorder` runs one public call per step and records what was sent, what the call returned or
raised, the resources under the deck afterwards (when they changed), and the tips each pipette
holds, which live on the pipette objects rather than in the resource tree.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from pylabrobot.io.http import HTTP
from pylabrobot.resources import Container, Resource, Tip, TipSpot
from pylabrobot.testing.golden import snapshot_resources

# Labware load names, and the OT-2's labware ids, are `uuid.uuid4().hex`. Each distinct one is
# replaced by `<uuid-N>`, numbered in order of first appearance within a scenario.
_UUID = re.compile(r"\b[0-9a-f]{32}\b")


@dataclass
class _Failure:
  """A command the server reports as failed when its status is read."""

  command_type: str
  error_type: str
  detail: str


class FakeRobotServer(HTTP):
  """An Opentrons robot server, answered in-process, recording every request in order.

  Commands succeed at once. Runs, pipettes, labware and commands get counter-based ids. The
  tip-presence sensor follows the pickups and drops sent to each pipette. `fail_next`,
  `answer_tip_presence` and `answer_liquid_probe` set the answers a scenario needs.
  """

  def __init__(
    self,
    health: Dict[str, Any],
    instruments: Optional[List[Dict[str, Any]]] = None,
    mounted: Optional[Dict[str, Dict[str, Any]]] = None,
    fixtures: Optional[List[Dict[str, Any]]] = None,
    position: Tuple[float, float, float] = (100.0, 100.0, 100.0),
  ) -> None:
    super().__init__(human_readable_device_name="fake robot server", base_url="http://robot.test")
    self.health = health
    self.instruments = instruments or []
    self.mounted = mounted or {}
    self.fixtures = fixtures or []
    self.position = position
    self.sent: List[Dict[str, Any]] = []
    self._counters: Dict[str, int] = {}
    self._commands: Dict[str, Dict[str, Any]] = {}
    self._failures: List[_Failure] = []
    self._tip_presence: Dict[str, str] = {}
    self._tip_presence_answers: List[str] = []
    self._liquid_probe_answers: List[Optional[float]] = []

  def fail_next(self, command_type: str, error_type: str, detail: str = "failed") -> None:
    """Report the next command of `command_type` as failed with `error_type`."""
    self._failures.append(_Failure(command_type, error_type, detail))

  def answer_tip_presence(self, status: str) -> None:
    """Answer the next `getTipPresence` with `status` instead of the tracked state."""
    self._tip_presence_answers.append(status)

  def answer_liquid_probe(self, z: Optional[float]) -> None:
    """Answer the next liquid probe with liquid at `z`, or with no liquid found when None."""
    self._liquid_probe_answers.append(z)

  def take_sent(self) -> List[Dict[str, Any]]:
    """The requests recorded since the last call, removed from the log."""
    sent, self.sent = self.sent, []
    return sent

  def _next_id(self, kind: str) -> str:
    self._counters[kind] = self._counters.get(kind, 0) + 1
    return f"{kind}-{self._counters[kind]}"

  def _command_result(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """The result a successful command of this type reports."""
    pipette = params.get("pipetteId")
    if command_type == "loadPipette":
      return {"pipetteId": f"pipette-{params['mount']}"}
    if command_type == "loadLabware":
      return {"labwareId": params.get("labwareId") or self._next_id("labware")}
    if command_type == "savePosition":
      x, y, z = self.position
      return {"positionId": "position", "position": {"x": x, "y": y, "z": z}}
    if command_type == "pickUpTip" and isinstance(pipette, str):
      self._tip_presence[pipette] = "present"
    if command_type in {"dropTip", "dropTipInPlace", "unsafe/dropTipInPlace"}:
      if isinstance(pipette, str):
        self._tip_presence[pipette] = "absent"
    if command_type == "getTipPresence" and isinstance(pipette, str):
      if self._tip_presence_answers:
        return {"status": self._tip_presence_answers.pop(0)}
      return {"status": self._tip_presence.get(pipette, "absent")}
    if command_type in {"liquidProbe", "tryLiquidProbe"}:
      probed = self._liquid_probe_answers.pop(0) if self._liquid_probe_answers else None
      # The server leaves `z_position` out of the result when no liquid was found.
      return {} if probed is None else {"z_position": probed}
    return {}

  def _submit(self, run_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    data = body["data"]
    command_type, params = data["commandType"], data["params"]
    command_id = self._next_id("command")
    failure = next((f for f in self._failures if f.command_type == command_type), None)
    if failure is not None:
      self._failures.remove(failure)
      command = {
        "id": command_id,
        "status": "failed",
        "error": {"errorType": failure.error_type, "detail": failure.detail},
      }
    else:
      command = {
        "id": command_id,
        "status": "succeeded",
        "result": self._command_result(command_type, params),
      }
    self._commands[command_id] = command
    return {"data": {"id": command_id}}

  def _answer(self, method: str, path: str, body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    parts = path.strip("/").split("/")
    if (method, path) == ("GET", "/health"):
      return self.health
    if (method, path) == ("GET", "/instruments"):
      return {"data": self.instruments}
    if (method, path) == ("GET", "/deck_configuration"):
      return {"data": {"cutoutFixtures": self.fixtures}}
    if (method, path) == ("GET", "/pipettes"):
      return self.mounted
    if (method, path) in {("GET", "/modules"), ("GET", "/runs")}:
      return {"data": []}
    if (method, path) == ("POST", "/runs"):
      return {"data": {"id": self._next_id("run"), "status": "idle"}}
    if (method, path) == ("POST", "/robot/home"):
      return {}
    if parts[0] == "runs" and len(parts) == 2 and method == "GET":
      return {"data": {"id": parts[1], "status": "stopped"}}
    if parts[0] == "runs" and parts[2:] == ["actions"] and method == "POST":
      return {}
    if parts[0] == "runs" and parts[2:] == ["commands"] and method == "POST":
      assert body is not None
      return self._submit(parts[1], body)
    if parts[0] == "runs" and parts[2:3] == ["commands"] and method == "GET":
      return {"data": self._commands[parts[3]]}
    if parts[0] == "runs" and parts[2:] == ["labware_definitions"] and method == "POST":
      assert body is not None
      definition = body["data"]
      load_name = definition["parameters"]["loadName"]
      uri = f"{definition['namespace']}/{load_name}/{definition['version']}"
      return {"data": {"definitionUri": uri}}
    raise AssertionError(f"the fake robot server has no answer for {method} {path}")

  def _make_request(
    self, method: str, path: str, data: Optional[Dict[str, Any]]
  ) -> Tuple[int, str]:
    """Record the request and answer it, as the network would."""
    # A JSON round trip, so the record holds what went on the wire rather than live objects.
    body = json.loads(json.dumps(data)) if data is not None else None
    request: Dict[str, Any] = {"request": f"{method} {path}"}
    if body is not None:
      request["body"] = body
    self.sent.append(request)
    return 200, json.dumps(self._answer(method, path, body))


def _fingerprint(root: Resource) -> List[Any]:
  """Everything `snapshot_resources` reads, gathered cheaply.

  A snapshot goes through the resource store's definitions and takes about a second for a
  deck with a few labware on it, so it is only taken when this fingerprint changed. The
  fingerprint covers at least what a snapshot records, so an unchanged fingerprint means an
  unchanged snapshot.
  """
  entries: List[Any] = []
  for resource in [root, *root.get_all_children()]:
    parent = resource.parent.name if resource.parent is not None else ""
    location = resource.location
    rotation = resource.rotation
    entry: List[Any] = [
      resource.name,
      parent,
      None if location is None else (location.x, location.y, location.z),
      (rotation.x, rotation.y, rotation.z),
    ]
    if isinstance(resource, Container):
      entry += [resource.tracker.volume, resource.tracker.pending_volume]
    if isinstance(resource, TipSpot) and resource.has_tip():
      tip = resource.get_tip()
      entry += [id(tip), tip.name, tip.tracker.volume, tip.tracker.pending_volume]
    entries.append(entry)
  return entries


class Recorder:
  """Run a scenario's steps and build its golden record.

  Args:
    server: The transport the device under test talks through.
    root: The resource tree to snapshot, the device's deck.
    mounted: Reads the tips each pipette holds, by pipette name, as JSON-able values.
  """

  def __init__(
    self,
    server: FakeRobotServer,
    root: Resource,
    mounted: Callable[[], Dict[str, Any]],
  ) -> None:
    self.server = server
    self.root = root
    self.mounted = mounted
    self.steps: List[Dict[str, Any]] = []
    self._uuids: Dict[str, str] = {}
    self._fingerprint = _fingerprint(root)
    self._resources = snapshot_resources(root)

  def _normalised(self, value: Any) -> Any:
    if isinstance(value, str):
      return _UUID.sub(self._placeholder, value)
    if isinstance(value, dict):
      return {self._normalised(key): self._normalised(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
      return [self._normalised(item) for item in value]
    return value

  def _placeholder(self, match: "re.Match[str]") -> str:
    found = match.group(0)
    if found not in self._uuids:
      self._uuids[found] = f"<uuid-{len(self._uuids) + 1}>"
    return self._uuids[found]

  def _add_resources(self, entry: Dict[str, Any]) -> None:
    """Add the resource snapshot to `entry` when the resources changed since the last one."""
    fingerprint = _fingerprint(self.root)
    if fingerprint == self._fingerprint:
      return
    self._fingerprint = fingerprint
    resources = snapshot_resources(self.root)
    if resources != self._resources:
      entry["resources"] = resources
      self._resources = resources

  async def step(self, call: str, operation: Awaitable[Any]) -> Any:
    """Run one call, recording what it sent, returned or raised, and the state it left.

    An exception the call raises is recorded as the step's `error` and not re-raised, so a
    refused or failed operation is pinned like any other.
    """
    self.server.take_sent()
    entry: Dict[str, Any] = {"call": call}
    result: Any = None
    try:
      result = await operation
      entry["result"] = jsonable(result)
    except Exception as error:  # noqa: BLE001 - a raised error is part of the record
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = self.server.take_sent()
    self._add_resources(entry)
    entry["mounted"] = self.mounted()
    self.steps.append(self._normalised(entry))
    return result

  def arrange(self, description: str, change: Callable[[], None]) -> None:
    """Change the resources by hand, as an operator would, recorded as its own step."""
    change()
    entry: Dict[str, Any] = {"arrange": description}
    self._add_resources(entry)
    self.steps.append(self._normalised(entry))

  def record(self) -> Dict[str, Any]:
    """The scenario's golden record: its steps and the resources at the end."""
    return {"steps": self.steps, "resources": self._normalised(snapshot_resources(self.root))}


def jsonable(value: Any) -> Any:
  """A call's return value as JSON: dataclasses and coordinates as their fields."""
  if value is None or isinstance(value, (bool, int, float, str)):
    return value
  if isinstance(value, dict):
    return {str(key): jsonable(item) for key, item in value.items()}
  if isinstance(value, (list, tuple)):
    return [jsonable(item) for item in value]
  return repr(value)


def tip_state(tip: Optional[Tip]) -> Optional[Dict[str, Any]]:
  """A mounted tip: its name and the liquid volume it holds."""
  if tip is None:
    return None
  return {"tip": tip.name, "volume": tip.tracker.get_used_volume()}
