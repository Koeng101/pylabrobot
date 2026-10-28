"""Where a volume stands in a container, from its own model."""

import unittest

from pylabrobot.lib.liquid_handling.liquid_height import get_liquid_height_from_volume
from pylabrobot.resources.container import Container


def _container(**functions) -> Container:
  return Container("c", size_x=10, size_y=10, size_z=20, **functions)


class LiquidHeightTests(unittest.TestCase):
  def test_nothing_stands_nowhere(self):
    self.assertEqual(get_liquid_height_from_volume(_container(), 0), 0.0)
    self.assertEqual(get_liquid_height_from_volume(_container(), -5), 0.0)

  def test_a_container_that_converts_says_how_high(self):
    container = _container(compute_height_from_volume=lambda volume: volume / 7)
    self.assertEqual(get_liquid_height_from_volume(container, 50), 7.14)

  def test_data_converts(self):
    container = _container(height_volume_data={0.0: 0.0, 10.0: 100.0, 20.0: 300.0})
    self.assertEqual(get_liquid_height_from_volume(container, 200), 15.0)

  def test_volume_from_height_alone_is_inverted(self):
    container = _container(compute_volume_from_height=lambda height: height * height)
    self.assertEqual(get_liquid_height_from_volume(container, 50), 7.07)

  def test_no_model_refuses(self):
    with self.assertRaises(RuntimeError):
      get_liquid_height_from_volume(_container(), 50)


if __name__ == "__main__":
  unittest.main()
