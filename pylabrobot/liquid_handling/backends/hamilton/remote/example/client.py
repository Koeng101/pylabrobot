"""Example: connect to a remote STAR service and run a simple protocol.

Usage:
  python -m pylabrobot.liquid_handling.backends.hamilton.remote.example.client

Assumes a server is running on localhost:8080 (see server.py).
"""

import argparse
import asyncio

from pylabrobot.liquid_handling.backends.hamilton.remote.client import RemoteSTARBackend
from pylabrobot.resources import Coordinate
from pylabrobot.resources.hamilton import STARLetDeck, TIP_CAR_480_A00, hamilton_96_tiprack_300uL_filter


async def main(url: str = "http://localhost:8080"):
  # 1. Connect to the remote STAR
  remote = RemoteSTARBackend.connect(url)
  await remote.setup()

  print(f"Connected to STAR at {url}")
  print(f"  Channels: {remote.num_channels}")
  print(f"  96-head installed: {remote.core96_head_installed}")
  print(f"  iSWAP installed: {remote.iswap_installed}")

  # 2. Use the remote backend just like a local one
  #    Example: move channel 0 to a position
  await remote.move_channel_x(channel=0, x=100.0)

  # 3. Query channel positions
  y_positions = await remote.get_channels_y_positions()
  print(f"  Y positions: {y_positions}")

  # 4. Stop when done
  await remote.stop()
  print("Disconnected.")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="STAR service client")
  parser.add_argument("--url", default="http://localhost:8080", help="Server URL")
  args = parser.parse_args()
  asyncio.run(main(url=args.url))
