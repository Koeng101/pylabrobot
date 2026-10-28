"""The STAR behind a Connect service.

`star_server_app(device)` serves a device; `python -m pylabrobot.hamilton.star.server` serves one
on the network. `STARlet(star_server=url)`, and its siblings, drive a served device as one in this
process is driven: the same classes and methods, each call made on the server's device. The
defaults its features use where a call names none are the server's, from a settings file
(`read_settings`); a client reads them and cannot set them.
"""

from pylabrobot.hamilton.star.server.client import (
  RemoteSTARDevice,
  RemoteSTARDriver,
  STARServer,
)
from pylabrobot.hamilton.star.server.serve import serve, star_server_app
from pylabrobot.hamilton.star.server.settings import Settings, read_settings

__all__ = [
  "RemoteSTARDevice",
  "RemoteSTARDriver",
  "STARServer",
  "Settings",
  "read_settings",
  "serve",
  "star_server_app",
]
