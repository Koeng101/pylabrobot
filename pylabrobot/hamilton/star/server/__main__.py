"""Serve a STAR: `python -m pylabrobot.hamilton.star.server --model STARlet --simulation`.

Without `--resource-server`, the device's resources are held in this process and served on their
own port, `--resource-port`; a client is given both URLs. `--settings-json` names
the defaults the device's features use where a call names none (`v1/settings.proto`); without it,
they are the code's. Needs uvicorn, which the `resource-server` extra installs.
"""

import argparse
import asyncio
from typing import Optional, Sequence

from pylabrobot.hamilton.star.device import STAR, STARlet, STARPlus
from pylabrobot.hamilton.star.server.serve import serve
from pylabrobot.hamilton.star.server.settings import read_settings

_MODELS = {"STAR": STAR, "STARlet": STARlet, "STARPlus": STARPlus}


def main(argv: Optional[Sequence[str]] = None) -> None:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--model", choices=sorted(_MODELS), default="STAR", help="which frame")
  parser.add_argument("--name", help="what to call the device; the frame's name when not given")
  parser.add_argument(
    "--simulation", action="store_true", help="serve a simulated device rather than one on USB"
  )
  parser.add_argument(
    "--declared-configuration-json", help="a configuration the device is declared to have"
  )
  parser.add_argument(
    "--resource-server",
    help="the resource server to keep the device's resources in; held here and served on "
    "--resource-port when not given",
  )
  parser.add_argument(
    "--resource-port",
    type=int,
    default=8080,
    help="the port the resource server held here is served on",
  )
  parser.add_argument(
    "--settings-json",
    help="a JSON file of the defaults the device's features use where a call names none; the "
    "code's defaults when not given",
  )
  parser.add_argument("--host", default="127.0.0.1")
  parser.add_argument("--port", type=int, default=8081)
  args = parser.parse_args(argv)

  settings = None if args.settings_json is None else read_settings(args.settings_json)
  factory = _MODELS[args.model]
  kwargs = {} if args.name is None else {"name": args.name}
  device = factory(
    simulation=args.simulation,
    declared_configuration_json=args.declared_configuration_json,
    resource_server=args.resource_server,
    **kwargs,
  )
  asyncio.run(
    serve(
      device,
      host=args.host,
      port=args.port,
      resource_port=args.resource_port if args.resource_server is None else None,
      settings=settings,
    )
  )


if __name__ == "__main__":
  main()
