import unittest

from google.protobuf import json_format

from pylabrobot.high_res.sample_storage import high_res_stacker
from pylabrobot.resources.store.v1 import types_pb2 as pb


class HighResStackerTests(unittest.TestCase):
  def test_builds_reported_stacker_geometry(self):
    stacker = high_res_stacker(
      name="stacker_2",
      zero_offset=5,
      slot_height=22.867,
      slot_count=24,
    )
    attributes = stacker.attributes

    self.assertEqual(attributes.kind, pb.RESOURCE_KIND_CARRIER)
    self.assertEqual(len(stacker.children), 24)
    self.assertEqual(attributes.size.x, 112.3)
    self.assertEqual(attributes.size.y, 146.6)
    self.assertAlmostEqual(attributes.size.z, 5 + 22.867 * 24)
    self.assertEqual(attributes.model, "high_res_stacker")
    self.assertEqual(
      json_format.MessageToDict(attributes.metadata),
      {"zero_offset": 5, "slot_height": 22.867, "slot_count": 24},
    )

    first = stacker.children[0].attributes
    last = stacker.children[23].attributes
    self.assertEqual(first.name, "stacker_2_slot_1")
    self.assertEqual(last.name, "stacker_2_slot_24")
    self.assertEqual(first.kind, pb.RESOURCE_KIND_PLATE_HOLDER)
    self.assertEqual(first.size.x, 85.48)
    self.assertEqual(first.size.y, 127.76)
    self.assertEqual(first.size.z, 22.867)
    self.assertEqual(first.holder.pedestal_size_z, 0)
    self.assertTrue(first.HasField("location"))
    self.assertTrue(last.HasField("location"))
    self.assertAlmostEqual(first.location.x, (112.3 - 85.48) / 2)
    self.assertAlmostEqual(first.location.y, (146.6 - 127.76) / 2)
    self.assertEqual(first.location.z, 5)
    self.assertAlmostEqual(last.location.z, 5 + 22.867 * 23)

  def test_allows_disabled_stacker(self):
    stacker = high_res_stacker(
      name="stacker_1",
      zero_offset=0,
      slot_height=28.94,
      slot_count=0,
    )

    self.assertEqual(len(stacker.children), 0)
    self.assertEqual(stacker.attributes.size.z, 0)

  def test_rejects_invalid_geometry(self):
    with self.assertRaisesRegex(ValueError, "zero_offset"):
      high_res_stacker("stacker", zero_offset=-1, slot_height=22.867, slot_count=24)
    with self.assertRaisesRegex(ValueError, "slot_height"):
      high_res_stacker("stacker", zero_offset=0, slot_height=0, slot_count=24)
    with self.assertRaisesRegex(ValueError, "slot_count"):
      high_res_stacker("stacker", zero_offset=0, slot_height=22.867, slot_count=-1)
