"""Hamilton heater shakers behind a Connect service.

`heater_shaker_server_app(heater_shakers)` serves heater shakers;
`python -m pylabrobot.hamilton.heater_shaker.server` serves them on the network.
`HamiltonHeaterShaker(name, heater_shaker_server=url, resource_server=url)` drives a served one as
one in this process is driven: the same methods, each call made on the server's heater shaker.
"""

from pylabrobot.hamilton.heater_shaker.server.client import (
  HeaterShakerServer,
  RemoteHamiltonHeaterShaker,
)
from pylabrobot.hamilton.heater_shaker.server.serve import heater_shaker_server_app, serve

__all__ = [
  "HeaterShakerServer",
  "RemoteHamiltonHeaterShaker",
  "heater_shaker_server_app",
  "serve",
]
