from typing import Optional

from pylabrobot.resources.coordinate import Coordinate
from pylabrobot.resources.store.client import ResourceStore

from .control_box import InhecoTECControlBox
from .holder import InhecoHolder, created


class InhecoCPAC(InhecoHolder):
  """Inheco CPAC: a temperature-controlled plate holder addressed by index on a control box. It
  holds any plate, one at a time."""

  def __init__(
    self,
    index: int,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    control_box: InhecoTECControlBox,
    child_location: Coordinate,
    category: str = "temperature_controller",
    model: Optional[str] = None,
    store: Optional[ResourceStore] = None,
  ):
    InhecoHolder.__init__(
      self,
      index=index,
      control_box=control_box,
      name=name,
      size_x=size_x,
      size_y=size_y,
      size_z=size_z,
      child_location=child_location,
      category=category,
      model=model,
      store=store,
    )


async def inheco_cpac_ultraflat(
  name: str,
  control_box: InhecoTECControlBox,
  index: int,
  store: Optional[ResourceStore] = None,
) -> InhecoCPAC:
  """Inheco CPAC Ultraflat
  7000166, 7000190, 7000165

  https://www.inheco.com/data/pdf/cpac-brochure-1013-1032-34.pdf

  Example:
    >>> from pylabrobot.inheco import inheco_cpac_ultraflat
    >>> await box.setup()
    >>> cpac = await inheco_cpac_ultraflat("cpac", control_box=box, index=1)
    >>> await cpac.set_temperature(37.0)
    >>> await cpac.request_current_temperature()
    37.0
  """

  return await created(
    InhecoCPAC(
      name=name,
      control_box=control_box,
      index=index,
      size_x=113,  # from spec
      size_y=89,  # from spec
      size_z=129,  # from spec
      child_location=Coordinate(x=8, y=11, z=77),  # x from spec, y and z measured
      model=inheco_cpac_ultraflat.__name__,
      store=store,
    )
  )
