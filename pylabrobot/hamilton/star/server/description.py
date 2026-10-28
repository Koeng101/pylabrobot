"""What a client keeps of a served device: the server describes it, and the client takes it up."""

import inspect
import json
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Type, cast

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.configuration import DeviceConfiguration, parse_configuration
from pylabrobot.hamilton.star.driver.features.autoload import Autoload, AutoloadConfiguration
from pylabrobot.hamilton.star.driver.features.core_grippers import (
  CoreGrippers,
  CoreGrippersConfiguration,
)
from pylabrobot.hamilton.star.driver.features.cover import FrontCover, FrontCoverConfiguration
from pylabrobot.hamilton.star.driver.features.head96 import Head96, Head96Configuration
from pylabrobot.hamilton.star.driver.features.head384 import Head384, Head384Configuration
from pylabrobot.hamilton.star.driver.features.iswap import iSWAP, iSWAPConfiguration
from pylabrobot.hamilton.star.driver.features.pipettes import Pipettes, PipettesConfiguration
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.server import codec
from pylabrobot.hamilton.star.server.v1 import description_pb2 as dpb
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.client import ResourceServer
from pylabrobot.resources.server.v1 import types_pb2 as pb

if TYPE_CHECKING:
  from pylabrobot.hamilton.star.server.client import RemoteSTARDevice


# -- the server: describing a device ------------------------------------------------------------


def _ref(target: Any, resource: Optional[handles.Resource]) -> None:
  if resource is not None:
    target.id = resource.id


def describe_settings(message: Any, feature: Any) -> Any:
  """Fill a settings message with what a feature's settings are now; one it cannot say is unset."""
  for fd in message.DESCRIPTOR.fields:
    try:
      value = getattr(feature, fd.name)
    except RuntimeError:
      continue
    if value is not None:
      setattr(message, fd.name, value)
  return message


def apply_settings(feature: Any, message: Any) -> None:
  """Take a feature's settings up as a description has them, past the refusal to assign them."""
  for fd in message.DESCRIPTOR.fields:
    value = getattr(message, fd.name) if message.HasField(fd.name) else None
    if isinstance(inspect.getattr_static(type(feature), fd.name, None), property):
      # A property's value is kept where its setter keeps it.
      object.__setattr__(feature, f"_{fd.name}", value)
    elif value is not None:
      object.__setattr__(feature, fd.name, value)


def describe(device: STARDevice) -> dpb.Description:
  """What a device and its driver hold that a client reads without a call."""
  out = dpb.Description(
    name=device.name,
    model=device.model,
    extension_housing=device.extension_housing,
    left_side_panel_installed=device.left_side_panel_installed,
  )
  for field in ("body", "deck", "left_side_panel", "left_extension_housing"):
    resource = getattr(device, field)
    if resource is not None:
      _ref(getattr(out, field), resource)
  driver = device.driver
  d = out.driver
  d.connected = driver.connected
  if driver.configuration is not None:
    codec.fill(d.configuration, DeviceConfiguration, driver.configuration)
  d.firmware.update(driver.firmware)
  if driver._num_channels is not None:
    d.num_channels = driver._num_channels
  if driver.declared_configuration_json is not None:
    with open(driver.declared_configuration_json, encoding="utf-8") as f:
      d.declared_json = f.read()
  for side, arm in (("left", driver.left_x_arm), ("right", driver.right_x_arm)):
    if arm is not None:
      _describe_arm(getattr(d, f"{side}_x_arm"), arm)
  if driver.autoload is not None:
    d.autoload.SetInParent()
    codec.fill(d.autoload.configuration, AutoloadConfiguration, driver.autoload.configuration)
    if driver.autoload.resource is not None:
      _ref(d.autoload.resource, driver.autoload.resource)
  if driver.front_cover is not None:
    d.front_cover.SetInParent()
    codec.fill(
      d.front_cover.configuration, FrontCoverConfiguration, driver.front_cover.configuration
    )
  return out


def _describe_arm(out: dpb.XArmDescription, arm: XArm) -> None:
  out.SetInParent()
  if arm.resource is not None:
    _ref(out.resource, arm.resource)
  if arm.pipettes is not None:
    p = out.pipettes
    p.SetInParent()
    codec.fill(p.configuration, PipettesConfiguration, arm.pipettes.configuration)
    for resource in arm.pipettes.resources:
      _ref(p.resources.add(), resource)
    for shaft in arm.pipettes.shafts:
      _ref(p.shafts.add(), shaft)
    describe_settings(p.settings, arm.pipettes)
  for name, cls in (("head96", Head96Configuration), ("head384", Head384Configuration)):
    head = getattr(arm, name)
    if head is None:
      continue
    h = getattr(out, name)
    h.SetInParent()
    codec.fill(h.configuration, cls, head.configuration)
    if head.resource is not None:
      _ref(h.resource, head.resource)
    for position, shaft in head.shafts.items():
      _ref(h.shafts[position], shaft)
    describe_settings(h.settings, head)
  if arm.iswap is not None:
    i = out.iswap
    i.SetInParent()
    codec.fill(i.configuration, iSWAPConfiguration, arm.iswap.configuration)
    for field in ("resource", "link_1", "gripper"):
      resource = getattr(arm.iswap, field)
      if resource is not None:
        _ref(getattr(i, field), resource)
    describe_settings(i.settings, arm.iswap)
  if arm.core_grippers is not None:
    out.core_grippers.SetInParent()
    codec.fill(
      out.core_grippers.configuration, CoreGrippersConfiguration, arm.core_grippers.configuration
    )
    describe_settings(out.core_grippers.settings, arm.core_grippers)
  describe_settings(out.settings, arm)


# -- the client: taking a description up ------------------------------------------------------


class _Handles:
  """The handles a description names, made in one read of the resource server."""

  def __init__(self, made: Dict[bytes, handles.Resource]):
    self.made = made

  @classmethod
  async def of(cls, server: ResourceServer, description: dpb.Description) -> "_Handles":
    ids = list(dict.fromkeys(_ids(description)))
    if not ids:
      return cls({})
    resolved = await codec.resolve(server, [codec._Ref(i) for i in ids])
    return cls({handle.id: handle for handle in resolved})

  def get(self, message: Any, field: str) -> Any:
    if not message.HasField(field):
      return None
    return self.made[getattr(message, field).id]


def _ids(message: Any) -> Iterator[bytes]:
  """Every resource id in a description, its configurations included."""
  for fd, value in message.ListFields():
    if fd.message_type is None:
      continue
    if fd.message_type.GetOptions().map_entry:
      items = list(value.values())
    elif fd.is_repeated:
      items = list(value)
    else:
      items = [value]
    for item in items:
      if not hasattr(item, "DESCRIPTOR"):
        continue
      if item.DESCRIPTOR.full_name == pb.ResourceRef.DESCRIPTOR.full_name:
        yield item.id
      else:
        yield from _ids(item)


async def apply(device: "RemoteSTARDevice", description: dpb.Description) -> None:
  """Bring a client's device, its driver and its features in line with a description."""
  from pylabrobot.hamilton.star.server import client as remote

  if description.model != device._expected_model:
    raise ValueError(
      f"the STAR server serves a {description.model}, not a {device._expected_model}"
    )
  made = await _Handles.of(device.resource_server, description)
  device.name = description.name
  device.model = description.model
  device.extension_housing = description.extension_housing
  device.left_side_panel_installed = description.left_side_panel_installed
  device.body = made.get(description, "body")
  device.deck = cast(Optional[handles.Deck], made.get(description, "deck"))
  device.left_side_panel = made.get(description, "left_side_panel")
  device.left_extension_housing = made.get(description, "left_extension_housing")

  driver = device.driver
  d = description.driver
  driver.deck = device.deck
  driver.left_side_panel_installed = description.left_side_panel_installed
  driver._connected = d.connected
  driver.configuration = (
    codec.read(d.configuration, DeviceConfiguration) if d.HasField("configuration") else None
  )
  driver.firmware = dict(d.firmware)
  driver._num_channels = d.num_channels if d.HasField("num_channels") else None
  driver.declared = parse_configuration(json.loads(d.declared_json)) if d.declared_json else {}

  for side in ("left", "right"):
    attribute = f"{side}_x_arm"
    if not d.HasField(attribute):
      setattr(driver, attribute, None)
      continue
    arm = getattr(driver, attribute)
    if arm is None:
      arm = remote.RemoteXArm(driver, side=side)
      object.__setattr__(arm, "_ready", True)
      setattr(driver, attribute, arm)
    _apply_arm(arm, getattr(d, attribute), made, remote)
    apply_settings(arm, getattr(d, attribute).settings)

  driver.autoload = _feature(
    driver.autoload, d, "autoload", remote.RemoteAutoload, driver, AutoloadConfiguration
  )
  if driver.autoload is not None:
    driver.autoload.resource = made.get(d.autoload, "resource")
  driver.front_cover = _feature(
    driver.front_cover, d, "front_cover", remote.RemoteFrontCover, driver, FrontCoverConfiguration
  )
  if device.deck is not None:
    device._num_tracks = device._num_tracks or (await device.deck.get_hamilton_tracks()).num_tracks


def _feature(
  current: Any, parent: Any, field: str, cls: Type[Any], driver: Any, config: Any
) -> Any:
  """A feature as a description has it: made when new, its configuration taken up; None when the
  description has none."""
  if not parent.HasField(field):
    return None
  message = getattr(parent, field)
  feature = current if current is not None else cls(driver)
  feature.configuration = codec.read(message.configuration, config)
  # From here on, assigning a setting or constant on it is refused.
  object.__setattr__(feature, "_ready", True)
  return feature


def _apply_arm(arm: XArm, a: dpb.XArmDescription, made: _Handles, remote: Any) -> None:
  driver = arm._driver
  arm.resource = made.get(a, "resource")
  arm.pipettes = _feature(
    arm.pipettes, a, "pipettes", remote.RemotePipettes, driver, PipettesConfiguration
  )
  if arm.pipettes is not None:
    arm.pipettes.resources = [made.made[r.id] for r in a.pipettes.resources]
    arm.pipettes.shafts = [made.made[r.id] for r in a.pipettes.shafts]
    apply_settings(arm.pipettes, a.pipettes.settings)
  for name, cls, config in (
    ("head96", remote.RemoteHead96, Head96Configuration),
    ("head384", remote.RemoteHead384, Head384Configuration),
  ):
    head = _feature(getattr(arm, name), a, name, cls, driver, config)
    setattr(arm, name, head)
    if head is None:
      continue
    h = getattr(a, name)
    head.resource = made.get(h, "resource")
    head.shafts = {position: made.made[r.id] for position, r in h.shafts.items()}
    apply_settings(head, h.settings)
  arm.iswap = _feature(arm.iswap, a, "iswap", remote.RemoteISWAP, driver, iSWAPConfiguration)
  if arm.iswap is not None:
    arm.iswap.resource = made.get(a.iswap, "resource")
    arm.iswap.link_1 = made.get(a.iswap, "link_1")
    arm.iswap.gripper = made.get(a.iswap, "gripper")
    apply_settings(arm.iswap, a.iswap.settings)
  arm.core_grippers = _feature(
    arm.core_grippers,
    a,
    "core_grippers",
    remote.RemoteCoreGrippers,
    driver,
    CoreGrippersConfiguration,
  )
  if arm.core_grippers is not None:
    apply_settings(arm.core_grippers, a.core_grippers.settings)


__all__ = ["apply", "describe"]

# The classes a description's features are made of, for type checkers.
_ = (Autoload, CoreGrippers, FrontCover, Head96, Head384, iSWAP, Pipettes)
