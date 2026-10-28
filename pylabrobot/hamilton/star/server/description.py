"""What a client keeps of a served device: the server describes it, and the client takes it up."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Type, TypeVar

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.driver.configuration import parse_configuration
from pylabrobot.hamilton.star.driver.features.head import Head
from pylabrobot.hamilton.star.driver.features.x_arm import XArm
from pylabrobot.hamilton.star.server import generated_codec as codec
from pylabrobot.hamilton.star.server import wire
from pylabrobot.hamilton.star.server.generated_remote import (
  RemoteAutoload,
  RemoteCoreGrippers,
  RemoteFrontCover,
  RemoteHead96,
  RemoteHead384,
  RemoteISWAP,
  RemotePipettes,
  RemoteXArm,
)
from pylabrobot.hamilton.star.server.v1 import description_pb2 as dpb
from pylabrobot.resources.server import handles
from pylabrobot.resources.server.v1 import types_pb2 as pb

if TYPE_CHECKING:
  from pylabrobot.hamilton.star.server.client import RemoteSTARDevice, RemoteSTARDriver

H = TypeVar("H", bound=handles.Resource)


# -- the server: describing a device ------------------------------------------------------------


def _ref(target: pb.ResourceRef, resource: Optional[handles.Resource]) -> None:
  if resource is not None:
    target.id = resource.id


def describe(device: STARDevice) -> dpb.Description:
  """What a device and its driver hold that a client reads without a call."""
  out = dpb.Description(
    name=device.name,
    model=device.model,
    extension_housing=device.extension_housing,
    left_side_panel_installed=device.left_side_panel_installed,
  )
  _ref(out.body, device.body)
  _ref(out.deck, device.deck)
  _ref(out.left_side_panel, device.left_side_panel)
  _ref(out.left_extension_housing, device.left_extension_housing)
  driver = device.driver
  d = out.driver
  d.connected = driver.connected
  if driver.configuration is not None:
    codec.fill_device_configuration(d.configuration, driver.configuration)
  d.firmware.update(driver.firmware)
  if driver._num_channels is not None:
    d.num_channels = driver._num_channels
  if driver.declared_configuration_json is not None:
    with open(driver.declared_configuration_json, encoding="utf-8") as f:
      d.declared_json = f.read()
  if driver.left_x_arm is not None:
    _describe_arm(d.left_x_arm, driver.left_x_arm)
  if driver.right_x_arm is not None:
    _describe_arm(d.right_x_arm, driver.right_x_arm)
  if driver.autoload is not None:
    d.autoload.SetInParent()
    codec.fill_autoload_configuration(d.autoload.configuration, driver.autoload.configuration)
    if driver.autoload.resource is not None:
      _ref(d.autoload.resource, driver.autoload.resource)
  if driver.front_cover is not None:
    d.front_cover.SetInParent()
    codec.fill_front_cover_configuration(
      d.front_cover.configuration, driver.front_cover.configuration
    )
  return out


def _describe_head(out: dpb.Head96Description | dpb.Head384Description, head: Head) -> None:
  out.SetInParent()
  if head.resource is not None:
    _ref(out.resource, head.resource)
  for position, shaft in head.shafts.items():
    _ref(out.shafts[position], shaft)


def _describe_arm(out: dpb.XArmDescription, arm: XArm) -> None:
  out.SetInParent()
  if arm.resource is not None:
    _ref(out.resource, arm.resource)
  if arm.pipettes is not None:
    p = out.pipettes
    p.SetInParent()
    codec.fill_pipettes_configuration(p.configuration, arm.pipettes.configuration)
    for resource in arm.pipettes.resources:
      _ref(p.resources.add(), resource)
    for shaft in arm.pipettes.shafts:
      _ref(p.shafts.add(), shaft)
    codec.describe_pipettes_settings(p.settings, arm.pipettes)
  if arm.head96 is not None:
    _describe_head(out.head96, arm.head96)
    codec.fill_head96_configuration(out.head96.configuration, arm.head96.configuration)
    codec.describe_head96_settings(out.head96.settings, arm.head96)
  if arm.head384 is not None:
    _describe_head(out.head384, arm.head384)
    codec.fill_head384_configuration(out.head384.configuration, arm.head384.configuration)
    codec.describe_head384_settings(out.head384.settings, arm.head384)
  if arm.iswap is not None:
    i = out.iswap
    i.SetInParent()
    codec.fill_iswap_configuration(i.configuration, arm.iswap.configuration)
    if arm.iswap.resource is not None:
      _ref(i.resource, arm.iswap.resource)
    if arm.iswap.link_1 is not None:
      _ref(i.link_1, arm.iswap.link_1)
    if arm.iswap.gripper is not None:
      _ref(i.gripper, arm.iswap.gripper)
    codec.describe_iswap_settings(i.settings, arm.iswap)
  if arm.core_grippers is not None:
    out.core_grippers.SetInParent()
    codec.fill_core_grippers_configuration(
      out.core_grippers.configuration, arm.core_grippers.configuration
    )
    codec.describe_core_grippers_settings(out.core_grippers.settings, arm.core_grippers)
  codec.describe_x_arm_settings(out.settings, arm)


# -- the client: taking a description up ------------------------------------------------------


def _get(refs: wire.Refs, given: bool, ref: pb.ResourceRef, kind: Type[H]) -> Optional[H]:
  """The handle a description's field names, as a `kind`; None when the field is unset."""
  return wire.handle(refs, ref, kind) if given else None


async def apply(device: RemoteSTARDevice, description: dpb.Description) -> None:
  """Bring a client's device, its driver and its features in line with a description."""
  if description.model != device._expected_model:
    raise ValueError(
      f"the STAR server serves a {description.model}, not a {device._expected_model}"
    )
  refs = await wire.refs_in(device.resource_server, description)
  Resource = handles.Resource
  device.name = description.name
  device.model = description.model
  device.extension_housing = description.extension_housing
  device.left_side_panel_installed = description.left_side_panel_installed
  device.body = _get(refs, description.HasField("body"), description.body, Resource)
  device.deck = _get(refs, description.HasField("deck"), description.deck, handles.Deck)
  device.left_side_panel = _get(
    refs, description.HasField("left_side_panel"), description.left_side_panel, Resource
  )
  device.left_extension_housing = _get(
    refs,
    description.HasField("left_extension_housing"),
    description.left_extension_housing,
    Resource,
  )

  driver = device.driver
  d = description.driver
  driver.deck = device.deck
  driver.left_side_panel_installed = description.left_side_panel_installed
  driver._connected = d.connected
  driver.configuration = (
    codec.read_device_configuration(d.configuration) if d.HasField("configuration") else None
  )
  driver.firmware = dict(d.firmware)
  driver._num_channels = d.num_channels if d.HasField("num_channels") else None
  driver.declared = parse_configuration(json.loads(d.declared_json)) if d.declared_json else {}

  driver.left_x_arm = _take_up_arm(
    driver, driver.left_x_arm, "left", d.left_x_arm if d.HasField("left_x_arm") else None, refs
  )
  driver.right_x_arm = _take_up_arm(
    driver, driver.right_x_arm, "right", d.right_x_arm if d.HasField("right_x_arm") else None, refs
  )

  if d.HasField("autoload"):
    autoload = (
      driver.autoload if isinstance(driver.autoload, RemoteAutoload) else RemoteAutoload(driver)
    )
    autoload.configuration = codec.read_autoload_configuration(d.autoload.configuration)
    autoload._ready = True
    autoload.resource = _get(
      refs, d.autoload.HasField("resource"), d.autoload.resource, handles.Resource
    )
    driver.autoload = autoload
  else:
    driver.autoload = None
  if d.HasField("front_cover"):
    cover = (
      driver.front_cover
      if isinstance(driver.front_cover, RemoteFrontCover)
      else RemoteFrontCover(driver)
    )
    cover.configuration = codec.read_front_cover_configuration(d.front_cover.configuration)
    cover._ready = True
    driver.front_cover = cover
  else:
    driver.front_cover = None
  if device.deck is not None:
    device._num_tracks = device._num_tracks or (await device.deck.get_hamilton_tracks()).num_tracks


def _take_up_arm(
  driver: RemoteSTARDriver,
  current: Optional[XArm],
  side: str,
  a: Optional[dpb.XArmDescription],
  refs: wire.Refs,
) -> Optional[RemoteXArm]:
  """An X-arm as a description has it: made when new; None when the description has none."""
  if a is None:
    return None
  if isinstance(current, RemoteXArm):
    arm = current
  else:
    arm = RemoteXArm(driver, side="left" if side == "left" else "right")
    arm._ready = True
  arm.resource = _get(refs, a.HasField("resource"), a.resource, handles.Resource)

  if a.HasField("pipettes"):
    pipettes = arm.pipettes if isinstance(arm.pipettes, RemotePipettes) else RemotePipettes(driver)
    pipettes.configuration = codec.read_pipettes_configuration(a.pipettes.configuration)
    pipettes._ready = True
    pipettes.resources = [wire.handle(refs, r, handles.Resource) for r in a.pipettes.resources]
    pipettes.shafts = [wire.handle(refs, r, handles.TipMountingShaft) for r in a.pipettes.shafts]
    pipettes._apply_settings(a.pipettes.settings)
    arm.pipettes = pipettes
  else:
    arm.pipettes = None

  if a.HasField("head96"):
    head96 = arm.head96 if isinstance(arm.head96, RemoteHead96) else RemoteHead96(driver)
    head96.configuration = codec.read_head96_configuration(a.head96.configuration)
    head96._ready = True
    head96.resource = _get(
      refs, a.head96.HasField("resource"), a.head96.resource, handles.NChannelPipette
    )
    head96.shafts = {
      position: wire.handle(refs, r, handles.TipMountingShaft)
      for position, r in a.head96.shafts.items()
    }
    head96._apply_settings(a.head96.settings)
    arm.head96 = head96
  else:
    arm.head96 = None

  if a.HasField("head384"):
    head384 = arm.head384 if isinstance(arm.head384, RemoteHead384) else RemoteHead384(driver)
    head384.configuration = codec.read_head384_configuration(a.head384.configuration)
    head384._ready = True
    head384.resource = _get(
      refs, a.head384.HasField("resource"), a.head384.resource, handles.NChannelPipette
    )
    head384.shafts = {
      position: wire.handle(refs, r, handles.TipMountingShaft)
      for position, r in a.head384.shafts.items()
    }
    head384._apply_settings(a.head384.settings)
    arm.head384 = head384
  else:
    arm.head384 = None

  if a.HasField("iswap"):
    iswap = arm.iswap if isinstance(arm.iswap, RemoteISWAP) else RemoteISWAP(driver)
    iswap.configuration = codec.read_iswap_configuration(a.iswap.configuration)
    iswap._ready = True
    iswap.resource = _get(refs, a.iswap.HasField("resource"), a.iswap.resource, handles.Resource)
    iswap.link_1 = _get(refs, a.iswap.HasField("link_1"), a.iswap.link_1, handles.LinkBody)
    iswap.gripper = _get(
      refs, a.iswap.HasField("gripper"), a.iswap.gripper, handles.MechanicalGripper
    )
    iswap._apply_settings(a.iswap.settings)
    arm.iswap = iswap
  else:
    arm.iswap = None

  if a.HasField("core_grippers"):
    core_grippers = (
      arm.core_grippers
      if isinstance(arm.core_grippers, RemoteCoreGrippers)
      else RemoteCoreGrippers(driver)
    )
    core_grippers.configuration = codec.read_core_grippers_configuration(
      a.core_grippers.configuration
    )
    core_grippers._ready = True
    core_grippers._apply_settings(a.core_grippers.settings)
    arm.core_grippers = core_grippers
  else:
    arm.core_grippers = None

  arm._apply_settings(a.settings)
  return arm


__all__ = ["apply", "describe"]
