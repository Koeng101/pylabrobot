"""A recorder's steps: what each records, and which waits."""

import asyncio
import unittest

from pylabrobot.testing import recorder as recording


class WaitingRecorder(recording.Recorder):
  records_waits = True


class RecorderTests(unittest.IsolatedAsyncioTestCase):
  async def test_a_step_records_its_own_waits_and_not_other_tasks(self):
    rig = WaitingRecorder()
    background_waits = []

    async def background() -> None:
      for _ in range(5):
        await asyncio.sleep(0.5)
        background_waits.append(0.5)

    async def call() -> str:
      rig.sent.append("write a")
      task = asyncio.ensure_future(background())
      await asyncio.sleep(2)
      await task
      return "done"

    await rig.step("call()", call)
    self.assertEqual(background_waits, [0.5] * 5)
    self.assertEqual(
      rig.steps, [{"call": "call()", "result": "done", "sent": ["write a"], "waits": [2]}]
    )

  async def test_a_step_records_what_it_raised(self):
    rig = recording.Recorder()

    async def call() -> None:
      rig.sent.append("write b")
      raise ValueError("refused")

    self.assertIsNone(await rig.step("call()", call))
    self.assertEqual(
      rig.steps, [{"call": "call()", "error": "ValueError: refused", "sent": ["write b"]}]
    )


if __name__ == "__main__":
  unittest.main()
