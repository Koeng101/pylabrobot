import unittest

from pylabrobot.inheco.control_box import InhecoTECControlBox
from pylabrobot.inheco.cpac import inheco_cpac_ultraflat


class InhecoHolderTests(unittest.IsolatedAsyncioTestCase):
  async def test_body_is_found_again_in_its_store(self) -> None:
    box = InhecoTECControlBox()
    first = inheco_cpac_ultraflat("cpac", control_box=box, index=1)
    body = await first.create_body()
    again = inheco_cpac_ultraflat("cpac", control_box=box, index=1, store=first.store)
    self.assertEqual(await again.create_body(), body)

  async def test_resource_is_set_and_cleared(self) -> None:
    cpac = inheco_cpac_ultraflat("cpac", control_box=InhecoTECControlBox(), index=1)
    plate = await cpac.store.create("Eppendorf_96_wellplate_250ul_Vb", name="plate")
    await cpac.set_resource(plate)
    self.assertEqual(await cpac.get_resource(), plate)
    await cpac.set_resource(None)
    self.assertIsNone(await cpac.get_resource())
    self.assertIsNone(await plate.get_parent())
