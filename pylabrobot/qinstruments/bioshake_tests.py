import asyncio
import types
import unittest
from typing import Optional
from unittest import mock
from unittest.mock import AsyncMock

from pylabrobot.qinstruments import bioshake as bioshake_module
from pylabrobot.qinstruments.bioshake import BioShake, BioShake3000Elm
from pylabrobot.resources.store.client import ResourceStore


class TestBioShakeReset(unittest.TestCase):
  def test_reset_completes_when_q1_initialization_succeeds(self) -> None:
    bioshake = BioShake.__new__(BioShake)
    bioshake.io = AsyncMock()
    bioshake.io.readline = AsyncMock(return_value=b"Initialization successfully completed.\r\n")

    asyncio.run(bioshake.reset())

    bioshake.io.write.assert_awaited_once_with(b"resetDevice\r")


async def _bioshake(store: Optional[ResourceStore] = None) -> BioShake:
  """A BioShake 3000 elm on a serial transport that is never opened."""
  constants = types.SimpleNamespace(EIGHTBITS=8, PARITY_NONE="N", STOPBITS_ONE=1)
  with (
    mock.patch.object(bioshake_module, "HAS_SERIAL", True),
    mock.patch.object(bioshake_module, "serial", constants, create=True),
    mock.patch.object(bioshake_module, "Serial", mock.MagicMock()),
  ):
    return await BioShake3000Elm("bioshake", "/dev/ttyUSB0", store=store)


class TestBioShakeBody(unittest.IsolatedAsyncioTestCase):
  async def test_body_is_found_again_in_its_store(self) -> None:
    first = await _bioshake()
    body = first.body
    again = await _bioshake(store=first.store)
    self.assertEqual(again.body, body)
    self.assertEqual(await again.get_resources(), body)

  async def test_resource_is_set_and_cleared(self) -> None:
    bioshake = await _bioshake()
    plate = await bioshake.store.create("cor_96_wellplate_360uL_Fb", name="plate")
    await bioshake.set_resource(plate)
    self.assertEqual(await bioshake.get_resource(), plate)
    other = await bioshake.store.create("cor_96_wellplate_360uL_Fb", name="other")
    with self.assertRaises(ValueError):
      await bioshake.set_resource(other)
    await bioshake.set_resource(None)
    self.assertIsNone(await bioshake.get_resource())
