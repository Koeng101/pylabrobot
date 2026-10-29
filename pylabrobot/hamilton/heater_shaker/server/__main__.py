"""Serve heater shakers: `python -m pylabrobot.hamilton.heater_shaker.server --simulation
--heater-shaker hhs_1:1`.

Each `--heater-shaker NAME:INDEX` is one heater shaker, plugged into port INDEX of what they are
plugged into: the STAR a STAR server serves (`--star-server`), or a simulated one
(`--simulation`). With `--resource-server`, each one's plate holder is the resource of its name
there. Needs uvicorn, which the `resource-server` extra installs.
"""

import argparse
import asyncio
from typing import List, Optional, Sequence, Tuple

from pylabrobot.hamilton.heater_shaker.heater_shaker import FirmwareLink, HamiltonHeaterShaker
from pylabrobot.hamilton.heater_shaker.server.serve import serve
from pylabrobot.hamilton.heater_shaker.simulator import HeaterShakerSimulator


def _named_index(text: str) -> Tuple[str, int]:
  name, sep, index = text.rpartition(":")
  if not sep or not name or not index.isdigit():
    raise argparse.ArgumentTypeError(f"expected NAME:INDEX, hhs_1:1 say, not '{text}'")
  return name, int(index)


def _interface(args: argparse.Namespace) -> FirmwareLink:
  if args.simulation:
    return HeaterShakerSimulator()
  # A STAR server's driver sends each command on to the STAR the heater shakers are plugged into.
  from pylabrobot.hamilton.star.server.client import RemoteSTARDriver, STARServer

  return RemoteSTARDriver(STARServer.connect(args.star_server))


def main(argv: Optional[Sequence[str]] = None) -> None:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument(
    "--heater-shaker",
    type=_named_index,
    action="append",
    required=True,
    metavar="NAME:INDEX",
    help="a heater shaker to serve: its name and the port it is plugged into; may be repeated",
  )
  link = parser.add_mutually_exclusive_group(required=True)
  link.add_argument(
    "--star-server", help="the STAR server serving the STAR the heater shakers are plugged into"
  )
  link.add_argument("--simulation", action="store_true", help="serve simulated heater shakers")
  parser.add_argument(
    "--resource-server", help="the resource server the heater shakers' plate holders are in"
  )
  parser.add_argument("--host", default="127.0.0.1")
  parser.add_argument("--port", type=int, default=8082)
  args = parser.parse_args(argv)

  interface = _interface(args)
  heater_shakers: List[HamiltonHeaterShaker] = [
    HamiltonHeaterShaker(
      name=name, index=index, interface=interface, resource_server=args.resource_server
    )
    for name, index in args.heater_shaker
  ]
  asyncio.run(serve(heater_shakers, host=args.host, port=args.port))


if __name__ == "__main__":
  main()
