"""Read-only transfer checks account for shared and untracked containers."""

import unittest

from pylabrobot.opentrons.model import Liquid
from pylabrobot.opentrons.tracking import validate_liquid_transfer
from pylabrobot.resources.errors import TooLittleLiquidError, TooLittleVolumeError


def _liquid(name: str, capacity: float, volume: float = 0, tracked: bool = True) -> Liquid:
  return Liquid(id=name.encode(), name=name, volume=volume, capacity=capacity, tracked=tracked)


class TransferValidationTests(unittest.TestCase):
  """Preflight checks must respect per-channel transfers without changing anything."""

  def test_shared_source_checks_total_draw(self):
    """Two nozzles drawing from one reservoir consume their combined volume."""
    source = _liquid("source", 100, 80)
    tips = [_liquid(f"tip{i}", 100) for i in range(2)]
    with self.assertRaises(TooLittleLiquidError):
      validate_liquid_transfer([source, source], list(tips), 50)
    self.assertEqual(source.volume, 80)
    self.assertEqual([tip.volume for tip in tips], [0, 0])

  def test_shared_destination_checks_total_dispense(self):
    """Two nozzles dispensing to one well share its remaining capacity."""
    tips = [_liquid(f"tip{i}", 100, 50) for i in range(2)]
    destination = _liquid("destination", 80)
    with self.assertRaises(TooLittleVolumeError):
      validate_liquid_transfer(list(tips), [destination, destination], 50)
    self.assertEqual(destination.volume, 0)
    self.assertEqual([tip.volume for tip in tips], [50, 50])

  def test_container_on_both_sides_uses_net_change(self):
    """Liquid received by an earlier nozzle is available to a later nozzle."""
    first = _liquid("first", 100, 50)
    second = _liquid("second", 100)
    validate_liquid_transfer([first, second], [second, first], 50)
    self.assertEqual(first.volume, 50)
    self.assertEqual(second.volume, 0)

  def test_untracked_containers_skip_volume_limits(self):
    """Untracked containers do not constrain a transfer, on either side."""
    source = _liquid("source", 100, tracked=False)
    destination = _liquid("destination", 100)
    validate_liquid_transfer([source], [destination], 50)
    destination = _liquid("destination", 100, tracked=False)
    validate_liquid_transfer([source], [destination], 200)
    validate_liquid_transfer([None], [None], 200)
