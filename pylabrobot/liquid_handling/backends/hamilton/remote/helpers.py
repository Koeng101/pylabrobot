"""Shared serialization helpers for converting between Python objects and protobuf messages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from pylabrobot.liquid_handling.standard import (
  Drop,
  DropTipRack,
  GripDirection,
  Mix,
  MultiHeadAspirationContainer,
  MultiHeadAspirationPlate,
  MultiHeadDispenseContainer,
  MultiHeadDispensePlate,
  Pickup,
  PickupTipRack,
  ResourceDrop,
  ResourceMove,
  ResourcePickup,
  SingleChannelAspiration,
  SingleChannelDispense,
)
from pylabrobot.resources import Coordinate
from pylabrobot.resources.hamilton import HamiltonTip, TipPickupMethod, TipSize
from pylabrobot.resources.rotation import Rotation
from pylabrobot.resources.tip import Tip

from . import star_service_pb2 as pb2

if TYPE_CHECKING:
  from pylabrobot.resources import Deck


# =============================================================================
# Coordinate / Rotation
# =============================================================================


def coordinate_to_proto(c: Coordinate) -> pb2.Coordinate:
  return pb2.Coordinate(x=c.x, y=c.y, z=c.z)


def coordinate_from_proto(msg: pb2.Coordinate) -> Coordinate:
  return Coordinate(x=msg.x, y=msg.y, z=msg.z)


def rotation_to_proto(r: Rotation) -> pb2.Rotation:
  return pb2.Rotation(x=r.x, y=r.y, z=r.z)


def rotation_from_proto(msg: pb2.Rotation) -> Rotation:
  return Rotation(x=msg.x, y=msg.y, z=msg.z)


# =============================================================================
# Tip
# =============================================================================

_TIP_SIZE_TO_PROTO = {
  TipSize.UNDEFINED: pb2.TIP_SIZE_UNDEFINED,
  TipSize.LOW_VOLUME: pb2.LOW_VOLUME,
  TipSize.STANDARD_VOLUME: pb2.STANDARD_VOLUME,
  TipSize.HIGH_VOLUME: pb2.HIGH_VOLUME,
  TipSize.CORE_384_HEAD_TIP: pb2.CORE_384,
  TipSize.XL: pb2.XL,
}

_PROTO_TO_TIP_SIZE = {v: k for k, v in _TIP_SIZE_TO_PROTO.items()}

_PICKUP_METHOD_TO_PROTO = {
  TipPickupMethod.OUT_OF_RACK: pb2.OUT_OF_RACK,
  TipPickupMethod.OUT_OF_WASH_LIQUID: pb2.OUT_OF_WASH_LIQUID,
}

_PROTO_TO_PICKUP_METHOD = {v: k for k, v in _PICKUP_METHOD_TO_PROTO.items()}


def tip_to_proto(tip: Tip) -> pb2.TipData:
  if isinstance(tip, HamiltonTip):
    return pb2.TipData(
      type="HamiltonTip",
      has_filter=tip.has_filter,
      total_tip_length=tip.total_tip_length,
      maximal_volume=tip.maximal_volume,
      fitting_depth=tip.fitting_depth,
      tip_size=_TIP_SIZE_TO_PROTO.get(tip.tip_size, pb2.TIP_SIZE_UNDEFINED),
      pickup_method=_PICKUP_METHOD_TO_PROTO.get(tip.pickup_method, pb2.OUT_OF_RACK),
    )
  return pb2.TipData(
    type="Tip",
    has_filter=tip.has_filter,
    total_tip_length=tip.total_tip_length,
    maximal_volume=tip.maximal_volume,
    fitting_depth=tip.fitting_depth,
  )


def tip_from_proto(msg: pb2.TipData) -> Tip:
  if msg.type == "HamiltonTip":
    return HamiltonTip(
      has_filter=msg.has_filter,
      total_tip_length=msg.total_tip_length,
      maximal_volume=msg.maximal_volume,
      tip_size=_PROTO_TO_TIP_SIZE.get(msg.tip_size, TipSize.UNDEFINED),
      pickup_method=_PROTO_TO_PICKUP_METHOD.get(msg.pickup_method, TipPickupMethod.OUT_OF_RACK),
    )
  return Tip(
    has_filter=msg.has_filter,
    total_tip_length=msg.total_tip_length,
    maximal_volume=msg.maximal_volume,
    fitting_depth=msg.fitting_depth,
  )


# =============================================================================
# Mix
# =============================================================================


def mix_to_proto(mix: Mix) -> pb2.MixData:
  return pb2.MixData(
    volume=mix.volume,
    repetitions=mix.repetitions,
    flow_rate=mix.flow_rate,
  )


def mix_from_proto(msg: pb2.MixData) -> Mix:
  return Mix(
    volume=msg.volume,
    repetitions=msg.repetitions,
    flow_rate=msg.flow_rate,
  )


# =============================================================================
# GripDirection
# =============================================================================

_GRIP_DIR_TO_PROTO = {
  GripDirection.FRONT: pb2.GRIP_FRONT,
  GripDirection.BACK: pb2.GRIP_BACK,
  GripDirection.LEFT: pb2.GRIP_LEFT,
  GripDirection.RIGHT: pb2.GRIP_RIGHT,
}

_PROTO_TO_GRIP_DIR = {v: k for k, v in _GRIP_DIR_TO_PROTO.items()}


def grip_direction_to_proto(d: GripDirection) -> pb2.GripDirectionEnum:
  return _GRIP_DIR_TO_PROTO[d]


def grip_direction_from_proto(d: int) -> GripDirection:
  return _PROTO_TO_GRIP_DIR[d]


# =============================================================================
# Operation messages -> Python dataclasses
# =============================================================================


def pickup_to_proto(op: Pickup) -> pb2.PickupOp:
  return pb2.PickupOp(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
    tip=tip_to_proto(op.tip),
  )


def pickup_from_proto(deck: Deck, msg: pb2.PickupOp) -> Pickup:
  resource = deck.get_resource(msg.resource_name)
  return Pickup(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
    tip=tip_from_proto(msg.tip),
  )


def drop_to_proto(op: Drop) -> pb2.DropOp:
  return pb2.DropOp(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
    tip=tip_to_proto(op.tip),
  )


def drop_from_proto(deck: Deck, msg: pb2.DropOp) -> Drop:
  resource = deck.get_resource(msg.resource_name)
  return Drop(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
    tip=tip_from_proto(msg.tip),
  )


def aspiration_to_proto(op: SingleChannelAspiration) -> pb2.SingleChannelAspirationOp:
  kwargs: dict = dict(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
    tip=tip_to_proto(op.tip),
    volume=op.volume,
  )
  if op.flow_rate is not None:
    kwargs["flow_rate"] = op.flow_rate
  if op.liquid_height is not None:
    kwargs["liquid_height"] = op.liquid_height
  if op.blow_out_air_volume is not None:
    kwargs["blow_out_air_volume"] = op.blow_out_air_volume
  if op.mix is not None:
    kwargs["mix"] = mix_to_proto(op.mix)
  return pb2.SingleChannelAspirationOp(**kwargs)


def aspiration_from_proto(
  deck: Deck, msg: pb2.SingleChannelAspirationOp
) -> SingleChannelAspiration:
  resource = deck.get_resource(msg.resource_name)
  return SingleChannelAspiration(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
    tip=tip_from_proto(msg.tip),
    volume=msg.volume,
    flow_rate=msg.flow_rate if msg.HasField("flow_rate") else None,
    liquid_height=msg.liquid_height if msg.HasField("liquid_height") else None,
    blow_out_air_volume=msg.blow_out_air_volume if msg.HasField("blow_out_air_volume") else None,
    mix=mix_from_proto(msg.mix) if msg.HasField("mix") else None,
  )


def dispense_to_proto(op: SingleChannelDispense) -> pb2.SingleChannelDispenseOp:
  kwargs: dict = dict(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
    tip=tip_to_proto(op.tip),
    volume=op.volume,
  )
  if op.flow_rate is not None:
    kwargs["flow_rate"] = op.flow_rate
  if op.liquid_height is not None:
    kwargs["liquid_height"] = op.liquid_height
  if op.blow_out_air_volume is not None:
    kwargs["blow_out_air_volume"] = op.blow_out_air_volume
  if op.mix is not None:
    kwargs["mix"] = mix_to_proto(op.mix)
  return pb2.SingleChannelDispenseOp(**kwargs)


def dispense_from_proto(deck: Deck, msg: pb2.SingleChannelDispenseOp) -> SingleChannelDispense:
  resource = deck.get_resource(msg.resource_name)
  return SingleChannelDispense(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
    tip=tip_from_proto(msg.tip),
    volume=msg.volume,
    flow_rate=msg.flow_rate if msg.HasField("flow_rate") else None,
    liquid_height=msg.liquid_height if msg.HasField("liquid_height") else None,
    blow_out_air_volume=msg.blow_out_air_volume if msg.HasField("blow_out_air_volume") else None,
    mix=mix_from_proto(msg.mix) if msg.HasField("mix") else None,
  )


# =============================================================================
# 96-head operations
# =============================================================================


def _tips_to_proto(
  tips: Sequence[Optional[Tip]],
) -> tuple[list[pb2.TipData], list[bool]]:
  """Convert a sequence of Optional[Tip] to parallel proto lists."""
  tip_msgs = []
  present = []
  for t in tips:
    if t is not None:
      tip_msgs.append(tip_to_proto(t))
      present.append(True)
    else:
      tip_msgs.append(pb2.TipData())
      present.append(False)
  return tip_msgs, present


def _tips_from_proto(
  tip_msgs: list[pb2.TipData], present: list[bool]
) -> list[Optional[Tip]]:
  """Convert parallel proto lists back to Optional[Tip] sequence."""
  result: list[Optional[Tip]] = []
  for msg, is_present in zip(tip_msgs, present):
    if is_present:
      result.append(tip_from_proto(msg))
    else:
      result.append(None)
  return result


def pickup_tip_rack_to_proto(op: PickupTipRack) -> pb2.PickupTipRackOp:
  tips, present = _tips_to_proto(op.tips)
  return pb2.PickupTipRackOp(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
    tips=tips,
    tip_present=present,
  )


def pickup_tip_rack_from_proto(deck: Deck, msg: pb2.PickupTipRackOp) -> PickupTipRack:
  resource = deck.get_resource(msg.resource_name)
  tips = _tips_from_proto(list(msg.tips), list(msg.tip_present))
  return PickupTipRack(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
    tips=tips,
  )


def drop_tip_rack_to_proto(op: DropTipRack) -> pb2.DropTipRackOp:
  return pb2.DropTipRackOp(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
  )


def drop_tip_rack_from_proto(deck: Deck, msg: pb2.DropTipRackOp) -> DropTipRack:
  resource = deck.get_resource(msg.resource_name)
  return DropTipRack(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
  )


def multi_head_aspiration_plate_to_proto(
  op: MultiHeadAspirationPlate,
) -> pb2.MultiHeadAspirationPlateOp:
  tips, present = _tips_to_proto(op.tips)
  kwargs: dict = dict(
    well_names=[w.name for w in op.wells],
    offset=coordinate_to_proto(op.offset),
    tips=tips,
    tip_present=present,
    volume=op.volume,
  )
  if op.flow_rate is not None:
    kwargs["flow_rate"] = op.flow_rate
  if op.liquid_height is not None:
    kwargs["liquid_height"] = op.liquid_height
  if op.blow_out_air_volume is not None:
    kwargs["blow_out_air_volume"] = op.blow_out_air_volume
  if op.mix is not None:
    kwargs["mix"] = mix_to_proto(op.mix)
  return pb2.MultiHeadAspirationPlateOp(**kwargs)


def multi_head_aspiration_plate_from_proto(
  deck: Deck, msg: pb2.MultiHeadAspirationPlateOp
) -> MultiHeadAspirationPlate:
  wells = [deck.get_resource(name) for name in msg.well_names]
  tips = _tips_from_proto(list(msg.tips), list(msg.tip_present))
  return MultiHeadAspirationPlate(
    wells=wells,
    offset=coordinate_from_proto(msg.offset),
    tips=tips,
    volume=msg.volume,
    flow_rate=msg.flow_rate if msg.HasField("flow_rate") else None,
    liquid_height=msg.liquid_height if msg.HasField("liquid_height") else None,
    blow_out_air_volume=msg.blow_out_air_volume if msg.HasField("blow_out_air_volume") else None,
    mix=mix_from_proto(msg.mix) if msg.HasField("mix") else None,
  )


def multi_head_dispense_plate_to_proto(
  op: MultiHeadDispensePlate,
) -> pb2.MultiHeadDispensePlateOp:
  tips, present = _tips_to_proto(op.tips)
  kwargs: dict = dict(
    well_names=[w.name for w in op.wells],
    offset=coordinate_to_proto(op.offset),
    tips=tips,
    tip_present=present,
    volume=op.volume,
  )
  if op.flow_rate is not None:
    kwargs["flow_rate"] = op.flow_rate
  if op.liquid_height is not None:
    kwargs["liquid_height"] = op.liquid_height
  if op.blow_out_air_volume is not None:
    kwargs["blow_out_air_volume"] = op.blow_out_air_volume
  if op.mix is not None:
    kwargs["mix"] = mix_to_proto(op.mix)
  return pb2.MultiHeadDispensePlateOp(**kwargs)


def multi_head_dispense_plate_from_proto(
  deck: Deck, msg: pb2.MultiHeadDispensePlateOp
) -> MultiHeadDispensePlate:
  wells = [deck.get_resource(name) for name in msg.well_names]
  tips = _tips_from_proto(list(msg.tips), list(msg.tip_present))
  return MultiHeadDispensePlate(
    wells=wells,
    offset=coordinate_from_proto(msg.offset),
    tips=tips,
    volume=msg.volume,
    flow_rate=msg.flow_rate if msg.HasField("flow_rate") else None,
    liquid_height=msg.liquid_height if msg.HasField("liquid_height") else None,
    blow_out_air_volume=msg.blow_out_air_volume if msg.HasField("blow_out_air_volume") else None,
    mix=mix_from_proto(msg.mix) if msg.HasField("mix") else None,
  )


def multi_head_aspiration_container_to_proto(
  op: MultiHeadAspirationContainer,
) -> pb2.MultiHeadAspirationContainerOp:
  tips, present = _tips_to_proto(op.tips)
  kwargs: dict = dict(
    container_name=op.container.name,
    offset=coordinate_to_proto(op.offset),
    tips=tips,
    tip_present=present,
    volume=op.volume,
  )
  if op.flow_rate is not None:
    kwargs["flow_rate"] = op.flow_rate
  if op.liquid_height is not None:
    kwargs["liquid_height"] = op.liquid_height
  if op.blow_out_air_volume is not None:
    kwargs["blow_out_air_volume"] = op.blow_out_air_volume
  if op.mix is not None:
    kwargs["mix"] = mix_to_proto(op.mix)
  return pb2.MultiHeadAspirationContainerOp(**kwargs)


def multi_head_aspiration_container_from_proto(
  deck: Deck, msg: pb2.MultiHeadAspirationContainerOp
) -> MultiHeadAspirationContainer:
  container = deck.get_resource(msg.container_name)
  tips = _tips_from_proto(list(msg.tips), list(msg.tip_present))
  return MultiHeadAspirationContainer(
    container=container,
    offset=coordinate_from_proto(msg.offset),
    tips=tips,
    volume=msg.volume,
    flow_rate=msg.flow_rate if msg.HasField("flow_rate") else None,
    liquid_height=msg.liquid_height if msg.HasField("liquid_height") else None,
    blow_out_air_volume=msg.blow_out_air_volume if msg.HasField("blow_out_air_volume") else None,
    mix=mix_from_proto(msg.mix) if msg.HasField("mix") else None,
  )


def multi_head_dispense_container_to_proto(
  op: MultiHeadDispenseContainer,
) -> pb2.MultiHeadDispenseContainerOp:
  tips, present = _tips_to_proto(op.tips)
  kwargs: dict = dict(
    container_name=op.container.name,
    offset=coordinate_to_proto(op.offset),
    tips=tips,
    tip_present=present,
    volume=op.volume,
  )
  if op.flow_rate is not None:
    kwargs["flow_rate"] = op.flow_rate
  if op.liquid_height is not None:
    kwargs["liquid_height"] = op.liquid_height
  if op.blow_out_air_volume is not None:
    kwargs["blow_out_air_volume"] = op.blow_out_air_volume
  if op.mix is not None:
    kwargs["mix"] = mix_to_proto(op.mix)
  return pb2.MultiHeadDispenseContainerOp(**kwargs)


def multi_head_dispense_container_from_proto(
  deck: Deck, msg: pb2.MultiHeadDispenseContainerOp
) -> MultiHeadDispenseContainer:
  container = deck.get_resource(msg.container_name)
  tips = _tips_from_proto(list(msg.tips), list(msg.tip_present))
  return MultiHeadDispenseContainer(
    container=container,
    offset=coordinate_from_proto(msg.offset),
    tips=tips,
    volume=msg.volume,
    flow_rate=msg.flow_rate if msg.HasField("flow_rate") else None,
    liquid_height=msg.liquid_height if msg.HasField("liquid_height") else None,
    blow_out_air_volume=msg.blow_out_air_volume if msg.HasField("blow_out_air_volume") else None,
    mix=mix_from_proto(msg.mix) if msg.HasField("mix") else None,
  )


# =============================================================================
# Resource handling operations
# =============================================================================


def resource_pickup_to_proto(op: ResourcePickup) -> pb2.ResourcePickupOp:
  return pb2.ResourcePickupOp(
    resource_name=op.resource.name,
    offset=coordinate_to_proto(op.offset),
    pickup_distance_from_top=op.pickup_distance_from_top,
    direction=grip_direction_to_proto(op.direction),
  )


def resource_pickup_from_proto(deck: Deck, msg: pb2.ResourcePickupOp) -> ResourcePickup:
  resource = deck.get_resource(msg.resource_name)
  return ResourcePickup(
    resource=resource,
    offset=coordinate_from_proto(msg.offset),
    pickup_distance_from_top=msg.pickup_distance_from_top,
    direction=grip_direction_from_proto(msg.direction),
  )


def resource_move_to_proto(op: ResourceMove) -> pb2.ResourceMoveOp:
  return pb2.ResourceMoveOp(
    resource_name=op.resource.name,
    location=coordinate_to_proto(op.location),
    gripped_direction=grip_direction_to_proto(op.gripped_direction),
    pickup_distance_from_top=op.pickup_distance_from_top,
    offset=coordinate_to_proto(op.offset),
  )


def resource_move_from_proto(deck: Deck, msg: pb2.ResourceMoveOp) -> ResourceMove:
  resource = deck.get_resource(msg.resource_name)
  return ResourceMove(
    resource=resource,
    location=coordinate_from_proto(msg.location),
    gripped_direction=grip_direction_from_proto(msg.gripped_direction),
    pickup_distance_from_top=msg.pickup_distance_from_top,
    offset=coordinate_from_proto(msg.offset),
  )


def resource_drop_to_proto(op: ResourceDrop) -> pb2.ResourceDropOp:
  return pb2.ResourceDropOp(
    resource_name=op.resource.name,
    destination=coordinate_to_proto(op.destination),
    destination_absolute_rotation=rotation_to_proto(op.destination_absolute_rotation),
    offset=coordinate_to_proto(op.offset),
    pickup_distance_from_top=op.pickup_distance_from_top,
    pickup_direction=grip_direction_to_proto(op.pickup_direction),
    direction=grip_direction_to_proto(op.direction),
    rotation=op.rotation,
  )


def resource_drop_from_proto(deck: Deck, msg: pb2.ResourceDropOp) -> ResourceDrop:
  resource = deck.get_resource(msg.resource_name)
  return ResourceDrop(
    resource=resource,
    destination=coordinate_from_proto(msg.destination),
    destination_absolute_rotation=rotation_from_proto(msg.destination_absolute_rotation),
    offset=coordinate_from_proto(msg.offset),
    pickup_distance_from_top=msg.pickup_distance_from_top,
    pickup_direction=grip_direction_from_proto(msg.pickup_direction),
    direction=grip_direction_from_proto(msg.direction),
    rotation=msg.rotation,
  )


# =============================================================================
# Utility: extract optional kwargs from proto request
# =============================================================================


def extract_optional_list(request, field_name: str) -> Optional[list]:
  """Extract an optional repeated field. Empty repeated = None."""
  val = getattr(request, field_name, [])
  return list(val) if len(val) > 0 else None


def extract_optional_field(request, field_name: str):
  """Extract an optional scalar field. Returns None if not set."""
  if request.HasField(field_name):
    return getattr(request, field_name)
  return None
