import unittest

from pylabrobot.inheco.control_box import InhecoTECControlBox
from pylabrobot.inheco.cpac import InhecoCPAC, inheco_cpac_ultraflat
from pylabrobot.resources.coordinate import Coordinate


class InhecoHolderTests(unittest.IsolatedAsyncioTestCase):
  async def test_body_is_found_again_in_its_store(self) -> None:
    box = InhecoTECControlBox()
    first = await inheco_cpac_ultraflat("cpac", control_box=box, index=1)
    body = first.body
    again = await inheco_cpac_ultraflat("cpac", control_box=box, index=1, store=first.store)
    self.assertEqual(again.body, body)
    self.assertEqual(await again.get_resources(), body)

  async def test_resources_are_only_found_by_get_resources(self) -> None:
    cpac = InhecoCPAC(
      index=1,
      name="cpac",
      size_x=1,
      size_y=1,
      size_z=1,
      control_box=InhecoTECControlBox(),
      child_location=Coordinate.zero(),
    )
    with self.assertRaises(RuntimeError):
      cpac.body
    with self.assertRaises(LookupError):
      await cpac.get_resources()
    self.assertEqual(await cpac.create_resources(), await cpac.get_resources())

  async def test_resource_is_set_and_cleared(self) -> None:
    cpac = await inheco_cpac_ultraflat("cpac", control_box=InhecoTECControlBox(), index=1)
    plate = await cpac.store.create("Eppendorf_96_wellplate_250ul_Vb", name="plate")
    await cpac.set_resource(plate)
    self.assertEqual(await cpac.get_resource(), plate)
    await cpac.set_resource(None)
    self.assertIsNone(await cpac.get_resource())
    self.assertIsNone(await plate.get_parent())
