"""A pipette's channels in the resource store: one shaft per channel, which mounts its tip.

Each mounted pipette hangs from the robot's deck, the robot's body in the store, as
`<deck>_<mount>_pipette`, with a tip-mounting shaft per channel, so the tips it holds are in the
deck's tree. Its location on the deck is nominal: where the pipette really is is not tracked, and
queries over what stands on the deck leave pipettes out (`is_pipette`). A tip picked up moves from
its spot onto the channel's shaft; one dropped moves into its spot, or leaves the store for a
trash. Each is staged before the robot is sent the command and resolved once it has answered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, cast

from pylabrobot.opentrons.model import (
  Ref,
  TipFacts,
  read,
  ref_of,
  resolve,
)
from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.errors import StoreError, plr_error
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb

K = pb.ResourceKind

# The nozzle pitch of every multi-channel Opentrons pipette.
_PITCH = 9.0


def is_pipette(node: pb.ResourceNode) -> bool:
  """Whether a deck's child is a mounted pipette rather than something standing on the deck."""
  return node.attributes.kind == K.RESOURCE_KIND_N_CHANNEL_PIPETTE


def pipette_definition(name: str, channels: int) -> pb.ResourceDefinition:
  """A pipette body and its shafts, channel 0 at the back."""
  shafts = [
    build.resource(
      f"{name}_channel_{channel}",
      Coordinate(1, 1, 1),
      kind=K.RESOURCE_KIND_TIP_MOUNTING_SHAFT,
      location=Coordinate(0, (channels - 1 - channel) * _PITCH, 0),
      tip_mounting_shaft=pb.TipMountingShaftSpec(cross_section_type=pb.CROSS_SECTION_TYPE_CIRCLE),
    )
    for channel in range(channels)
  ]
  return build.resource(
    name,
    Coordinate(1, max(channels - 1, 0) * _PITCH + 1, 1),
    kind=K.RESOURCE_KIND_N_CHANNEL_PIPETTE,
    n_channel_pipette=pb.NChannelPipetteSpec(reference_point=pb.Vec3()),
    children=shafts,
  )


@dataclass(frozen=True)
class Mounted:
  """What each channel of a pipette carries, from one read.

  Attributes:
    tips: Each channel's tip, or None.
  """

  tips: Tuple[Optional[TipFacts], ...]

  @property
  def channels(self) -> List[int]:
    """The channels that carry a tip."""
    return [i for i, tip in enumerate(self.tips) if tip is not None]

  @property
  def held(self) -> List[TipFacts]:
    """The tips carried, in channel order."""
    return [tip for tip in self.tips if tip is not None]

  def __len__(self) -> int:
    return len(self.tips)

  def __getitem__(self, channel: int) -> Optional[TipFacts]:
    return self.tips[channel]


class PipetteShafts:
  """A pipette's shafts in a store, and the tips staged onto and off them.

  Attributes:
    store: The store.
    root: The pipette body, on the deck.
    shafts: Each channel's shaft, by channel.
  """

  def __init__(self, store: ResourceStore, root: handles.Resource, shafts: Sequence[bytes]):
    self.store = store
    self.root = root
    self.shafts = list(shafts)

  @staticmethod
  async def create(deck: handles.Deck, name: str, channels: int) -> PipetteShafts:
    """A fresh pipette body on `deck`: one already of this name there, and what it carried, is
    removed first.

    Args:
      deck: The robot's deck; the pipette is assigned to it at the deck's origin, a nominal
        location.
      name: The pipette body's name, `<deck>_<mount>_pipette`.
      channels: How many channels it has.
    """
    store = deck.store
    for existing in await deck.find_resources(
      kinds=[K.RESOURCE_KIND_N_CHANNEL_PIPETTE], names=[name]
    ):
      await existing.delete()
    response = await store.commands.create_resources(
      spb.CreateResourcesRequest(
        lock_tokens=store.lock_tokens,
        resources=[
          spb.CreateResource(
            definition=pipette_definition(name, channels),
            name=name,
            assign=pb.AssignChild(parent=deck.ref, location=pb.Vec3()),
          )
        ],
      )
    )
    root_node = response.nodes[0]
    root = store.handle_from_node(root_node, ())
    shafts = [
      n.id for n in response.nodes if n.attributes.kind == K.RESOURCE_KIND_TIP_MOUNTING_SHAFT
    ]
    return PipetteShafts(store, root, shafts)

  async def mounted(self) -> Mounted:
    """What each channel carries now: one read."""
    tree = await read(self.store, [self.root], depth=2)
    tips: List[Optional[TipFacts]] = []
    for shaft in self.shafts:
      tool = tree.tool(tree.node(shaft)) if shaft in tree else None
      tips.append(TipFacts.of(tool) if tool is not None else None)
    return Mounted(tuple(tips))

  async def tip_handles(self) -> List[Optional[handles.Tip]]:
    """Each channel's tip as a handle, or None."""
    tree = await read(self.store, [self.root], depth=2)
    found: List[Optional[handles.Tip]] = []
    for shaft in self.shafts:
      tool = tree.tool(tree.node(shaft))
      found.append(
        cast(handles.Tip, self.store.handle_from_node(tool, ())) if tool is not None else None
      )
    return found

  async def begin_pickup(
    self, frame: Ref, items: Sequence[Tuple[bytes, int]]
  ) -> Optional[pb.Operation]:
    """Stage each spot's tip moving onto a channel's shaft, refusing what the model disagrees
    with: a spot holding no tip, a shaft already carrying one.

    Args:
      frame: The deck.
      items: Each spot, and the channel that takes its tip.

    Raises:
      NoTipError: A tracked spot holds no tip.
      HasTipError: A channel already carries one.
    """
    if not items:
      return None
    request = spb.BeginToolPickupRequest(
      lock_tokens=self.store.lock_tokens,
      frame=ref_of(frame),
      items=[
        spb.ToolPickupItem(
          source=pb.ResourceRef(id=spot), shaft=pb.ResourceRef(id=self.shafts[channel])
        )
        for spot, channel in items
      ],
      on_tracking_problem=pb.ON_TRACKING_PROBLEM_REJECT,
    )
    try:
      response = await self.store.commands.begin_tool_pickup(request)
    except StoreError as error:
      raise plr_error(error) from error
    return response.operation

  async def begin_drop(
    self, frame: Ref, items: Sequence[Tuple[int, bytes]]
  ) -> Optional[pb.Operation]:
    """Stage each channel's tip moving into a spot, or out of the store into a trash. A tip that
    still holds liquid is dropped all the same.

    Args:
      frame: The deck.
      items: Each channel, and where its tip goes.
    """
    if not items:
      return None
    request = spb.BeginToolDropRequest(
      lock_tokens=self.store.lock_tokens,
      frame=ref_of(frame),
      items=[
        spb.ToolDropItem(
          shaft=pb.ResourceRef(id=self.shafts[channel]), target=pb.ResourceRef(id=target)
        )
        for channel, target in items
      ],
      on_tracking_problem=pb.ON_TRACKING_PROBLEM_RECORD,
    )
    try:
      response = await self.store.commands.begin_tool_drop(request)
    except StoreError as error:
      raise plr_error(error) from error
    return response.operation

  async def resolve(self, operation: Optional[pb.Operation], succeeded: bool) -> None:
    """Commit what was staged once the robot has done it, or roll it back."""
    if operation is not None:
      await resolve(self.store, operation, succeeded)

  async def discard(self, tips: Sequence[TipFacts]) -> None:
    """Take tips out of the store: they fell where the model holds nothing."""
    if tips:
      await self.store.commands.delete_resources(
        spb.DeleteResourcesRequest(
          lock_tokens=self.store.lock_tokens,
          resources=[pb.ResourceRef(id=tip.id) for tip in tips],
        )
      )
