"""Example: run a STAR service server that wraps a real STARBackend.

Usage:
  python -m pylabrobot.liquid_handling.backends.hamilton.remote.example.server

The server listens on port 8080 by default. A remote client can connect
to this server and control the STAR as if it were local.
"""

import argparse
import asyncio

import uvicorn

from pylabrobot.liquid_handling.backends.hamilton.remote.server import create_star_app
from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend
from pylabrobot.resources.hamilton import STARLetDeck


async def main(port: int = 8080):
  # 1. Create the real STARBackend and deck
  backend = STARBackend()
  deck = STARLetDeck()
  backend.set_deck(deck)

  # 2. Setup the backend (connects to the machine via USB)
  await backend.setup()

  # 3. Create the ASGI application
  app = create_star_app(backend)

  # 4. Run with uvicorn
  config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
  server = uvicorn.Server(config)
  await server.serve()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="STAR service server")
  parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
  args = parser.parse_args()
  asyncio.run(main(port=args.port))
