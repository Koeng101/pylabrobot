"""Labware whose wells convert height and volume through `height_volume_data` answer as the
geometry, fit or calibration each definition describes, over every height and volume it answers."""

import unittest
from dataclasses import dataclass
from typing import Callable, List, Optional

from pylabrobot.resources.agenbio.plates import (
  agenbio_1_troughplate_100mL_Fl,
  agenbio_1_troughplate_190mL_Fl,
  agenbio_4_troughplate_75mL_Vb,
  agenbio_96_wellplate_Ub_2200uL,
)
from pylabrobot.resources.agilent.plates import agilent_96_wellplate_150uL_Vb
from pylabrobot.resources.azenta.plates import azenta_96_wellplate_200uL_Vb_4titudeframestar
from pylabrobot.resources.celltreat.plates import (
  celltreat_6_wellplate_16300uL_Fb,
  celltreat_96_wellplate_350uL_Ub,
)
from pylabrobot.resources.corning.axygen.plates import cor_axy_24_wellplate_10mL_Vb
from pylabrobot.resources.corning.costar.plates import (
  cor_cos_6_wellplate_16800uL_Fb,
  cor_cos_12_wellplate_6900uL_Fb,
  cor_cos_24_wellplate_3470uL_Fb,
  cor_cos_48_wellplate_1620uL_Fb,
)
from pylabrobot.resources.corning.falcon.plates import (
  cor_falcon_96_wellplate_275uL_Fb,
  cor_falcon_96_wellplate_340uL_Fb_black,
)
from pylabrobot.resources.corning.plates import cor_96_wellplate_2mL_Vb
from pylabrobot.resources.eppendorf.plates import Eppendorf_96_wellplate_250ul_Vb
from pylabrobot.resources.height_volume_functions import (
  calculate_liquid_height_container_1segment_round_vbottom,
  calculate_liquid_height_in_container_2segments_square_ubottom,
  calculate_liquid_height_in_container_2segments_square_vbottom,
  calculate_liquid_volume_container_1segment_round_vbottom,
  calculate_liquid_volume_container_2segments_round_vbottom,
  calculate_liquid_volume_container_2segments_square_ubottom,
  calculate_liquid_volume_container_2segments_square_vbottom,
  compute_height_from_volume_conical_frustum,
  compute_height_from_volume_cylinder,
  compute_height_from_volume_rectangle,
  compute_volume_from_height_conical_frustum,
  compute_volume_from_height_cylinder,
  compute_volume_from_height_rectangle,
)
from pylabrobot.resources.nest.plates import (
  nest_1_troughplate_185000uL_Vb,
  nest_1_troughplate_195000uL_Vb,
  nest_8_troughplate_22000uL_Vb,
  nest_12_troughplate_15000uL_Vb,
)
from pylabrobot.resources.plate import Plate
from pylabrobot.resources.porvair.plates import (
  Porvair_6_reservoir_47ml_Vb,
  Porvair_24_wellplate_Vb,
)
from pylabrobot.resources.revvity.plates import Revvity_384_wellplate_28ul_Ub
from pylabrobot.resources.thermo_fisher.plates import (
  Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate,
  Thermo_TS_96_wellplate_1200ul_Rb,
  thermo_AB_96_wellplate_300ul_Vb_MicroAmp,
)
from pylabrobot.utils.interpolation import interpolate_1d

HEIGHT_TOLERANCE = 0.01  # mm
STEPS = 1000

ENDURAPLATE_CALIBRATION = {
  0.0: 0.0,
  0.17: 4.0,
  0.77: 8.0,
  2.27: 20.0,
  6.57: 70.0,
  9.17: 120.0,
  11.17: 170.0,
  13.17: 220.0,
  15.17: 260.0,
}
MICROAMP_CALIBRATION = {
  0.0: 0.0,
  1.69: 4.0,
  2.29: 8.0,
  3.89: 20.0,
  5.79: 40.0,
  8.49: 70.0,
  10.59: 120.0,
  12.69: 170.0,
  14.79: 220.0,
  16.59: 260.0,
  17.89: 290.0,
}


def _calibrated(data: dict) -> Callable[[float], float]:
  """Linear through measured points, extended along the last segment, to 0.001."""
  return lambda x: round(interpolate_1d(x, data, bounds_handling="extrapolate"), 3)


def _inverse(data: dict) -> dict:
  return {v: h for h, v in data.items()}


def _rounded(f: Callable[[float], float]) -> Callable[[float], float]:
  return lambda x: round(f(x), 3)


def _eppendorf_250ul_volume(h: float) -> float:
  return max(
    0.89486648 + 2.92455131 * h + 2.03472797 * h**2 + -0.16509371 * h**3 + 0.00675759 * h**4, 0
  )


def _eppendorf_250ul_height(v: float) -> float:
  return max(
    0.118078503
    + 0.133333914 * v
    + -0.000802726227 * v**2
    + 3.29761957e-06 * v**3
    + -5.29119614e-09 * v**4,
    0,
  )


def _rectangle(length: float, width: float):
  return (
    lambda h: compute_volume_from_height_rectangle(h, length, width),
    lambda v: compute_height_from_volume_rectangle(v, length, width),
  )


def _frustum(bottom_radius: float, top_radius: float):
  return (
    lambda h: compute_volume_from_height_conical_frustum(h, bottom_radius, top_radius),
    lambda v: compute_height_from_volume_conical_frustum(v, bottom_radius, top_radius),
  )


def _square_vbottom(x: float, y: float, h_pyramid: float, h_cube: float):
  return (
    lambda h: calculate_liquid_volume_container_2segments_square_vbottom(
      x=x, y=y, h_pyramid=h_pyramid, h_cube=h_cube, liquid_height=h
    ),
    lambda v: calculate_liquid_height_in_container_2segments_square_vbottom(
      x=x, y=y, h_pyramid=h_pyramid, h_cube=h_cube, liquid_volume=v
    ),
  )


@dataclass(frozen=True)
class Reference:
  """A labware definition and the conversions its wells describe.

  Attributes:
    factory: builds the plate or trough from a name.
    volume_from_height: volume (uL) at a liquid height (mm) above the cavity bottom.
    height_from_volume: liquid height (mm) of a volume (uL); `None` for definitions that give
      only volumes.
    top_height: heights from 0 to this are compared.
    max_volume: the wells' maximum volume.
    top_volume: volumes from 0 to this are compared; `None` for `volume_from_height(top_height)`.
    height_tolerance: how far (mm) heights may differ from `height_from_volume`.
  """

  factory: Callable[[str], Plate]
  volume_from_height: Callable[[float], float]
  height_from_volume: Optional[Callable[[float], float]]
  top_height: float
  max_volume: float
  top_volume: Optional[float] = None
  height_tolerance: float = HEIGHT_TOLERANCE


def _reference(
  factory: Callable[[str], Plate],
  conversions,
  top_height: float,
  max_volume: float,
  top_volume: Optional[float] = None,
  height_tolerance: float = HEIGHT_TOLERANCE,
) -> Reference:
  volume_from_height, height_from_volume = conversions
  return Reference(
    factory,
    volume_from_height,
    height_from_volume,
    top_height,
    max_volume,
    top_volume,
    height_tolerance,
  )


REFERENCES: List[Reference] = [
  _reference(agenbio_96_wellplate_Ub_2200uL, _rectangle(8, 8), 38.2, 2444.8),
  _reference(agenbio_4_troughplate_75mL_Vb, _rectangle(72.0, 26.1), 42.55, 75000),
  _reference(agenbio_1_troughplate_190mL_Fl, _rectangle(70.9, 107.2), 38.32, 190000),
  _reference(agenbio_1_troughplate_100mL_Fl, _rectangle(70.9, 107.2), 25.52, 100000),
  _reference(
    agilent_96_wellplate_150uL_Vb,
    (
      lambda h: calculate_liquid_volume_container_1segment_round_vbottom(
        d=6.4, h_pyramid=12.5, liquid_height=h
      ),
      lambda v: calculate_liquid_height_container_1segment_round_vbottom(
        d=6.4, h_pyramid=12.5, liquid_volume=v
      ),
    ),
    12.5,
    190,
  ),
  _reference(
    azenta_96_wellplate_200uL_Vb_4titudeframestar,
    (
      lambda h: calculate_liquid_volume_container_2segments_round_vbottom(
        d=5.5, h_cone=9.8, h_cylinder=5.3, liquid_height=h
      ),
      None,
    ),
    15.1,
    203.52938905975373,
  ),
  _reference(celltreat_6_wellplate_16300uL_Fb, _frustum(17.35, 17.75), 17.2, 16300),
  _reference(
    celltreat_96_wellplate_350uL_Ub,
    (
      lambda h: compute_volume_from_height_cylinder(h, 3.175),
      lambda v: compute_height_from_volume_cylinder(v, 3.175),
    ),
    10.04,
    300,
  ),
  _reference(
    cor_axy_24_wellplate_10mL_Vb,
    (_square_vbottom(x=17, y=17, h_pyramid=5, h_cube=37)[0], None),
    42,
    11174.666666666666,
  ),
  _reference(cor_cos_6_wellplate_16800uL_Fb, _frustum(35.43 / 2, 34.80 / 2), 17.4, 16800),
  _reference(cor_cos_12_wellplate_6900uL_Fb, _frustum(22.73 / 2, 22.11 / 2), 17.5, 6900),
  _reference(cor_cos_24_wellplate_3470uL_Fb, _frustum(16.26 / 2, 15.62 / 2), 17.4, 3400),
  _reference(cor_cos_48_wellplate_1620uL_Fb, _frustum(11.56 / 2, 11.05 / 2), 17.4, 1620),
  _reference(cor_falcon_96_wellplate_275uL_Fb, _frustum(3.175, 3.425), 14.3, 489.46478236842313),
  _reference(
    cor_falcon_96_wellplate_340uL_Fb_black, _frustum(3.29, 3.48), 10.9, 392.47113820775513
  ),
  _reference(
    cor_96_wellplate_2mL_Vb,
    (
      _square_vbottom(x=7.8, y=7.8, h_pyramid=4.0, h_cube=38.0)[0],
      _rounded(_square_vbottom(x=7.8, y=7.8, h_pyramid=4.0, h_cube=38.0)[1]),
    ),
    42,
    2393.04,
    top_volume=2100,
  ),
  _reference(
    Eppendorf_96_wellplate_250ul_Vb,
    (_eppendorf_250ul_volume, _eppendorf_250ul_height),
    20.3,
    584.560065130625,
    top_volume=262.5,
    # The two fits were made separately and are not each other's inverse; the data follows the
    # volume fit, so its heights are up to 0.24 mm from the height fit.
    height_tolerance=0.24,
  ),
  _reference(nest_12_troughplate_15000uL_Vb, _rectangle(8.2, 71.2), 26.85, 15676.104),
  _reference(nest_8_troughplate_22000uL_Vb, _rectangle(107.5, 8.2), 26.85, 23668.274999999998),
  _reference(nest_1_troughplate_185000uL_Vb, _rectangle(108.0, 72.0), 26.85, 208785.6),
  _reference(nest_1_troughplate_195000uL_Vb, _rectangle(108.0, 72.0), 26.85, 208785.6),
  _reference(
    Porvair_24_wellplate_Vb,
    _square_vbottom(x=8.0, y=35.0, h_pyramid=11.65, h_cube=1.65),
    13.3,
    3500,
  ),
  _reference(
    Porvair_6_reservoir_47ml_Vb,
    (
      _square_vbottom(x=17, y=70.8, h_pyramid=5, h_cube=37.5)[0],
      _rounded(_square_vbottom(x=17, y=70.8, h_pyramid=5, h_cube=37.5)[1]),
    ),
    42.5,
    47141.0,
  ),
  _reference(
    Revvity_384_wellplate_28ul_Ub,
    (
      lambda h: calculate_liquid_volume_container_2segments_round_vbottom(
        d=3.3, h_cone=3, h_cylinder=2.3, liquid_height=h
      ),
      None,
    ),
    5.3,
    28.22485379801409,
  ),
  _reference(
    Thermo_TS_96_wellplate_1200ul_Rb,
    (
      lambda h: calculate_liquid_volume_container_2segments_square_ubottom(
        x=8.15, h_cuboid=16.45, liquid_height=h
      ),
      _rounded(
        lambda v: calculate_liquid_height_in_container_2segments_square_ubottom(
          x=8.15, h_cuboid=16.45, liquid_volume=v
        )
      ),
    ),
    20.5,
    1232.7129266641255,
    top_volume=1234.37,
  ),
  _reference(
    Thermo_AB_96_wellplate_300ul_Vb_EnduraPlate,
    (
      _calibrated(ENDURAPLATE_CALIBRATION),
      _calibrated(_inverse(ENDURAPLATE_CALIBRATION)),
    ),
    20.1 * 1.05,
    358.6,
    top_volume=315,
  ),
  _reference(
    thermo_AB_96_wellplate_300ul_Vb_MicroAmp,
    (_calibrated(MICROAMP_CALIBRATION), _calibrated(_inverse(MICROAMP_CALIBRATION))),
    (23.24 - 0.74) * 1.05,
    413.462,
    top_volume=305,
  ),
]


def _sweep(top: float, bottom: float = 0) -> List[float]:
  return [bottom + (top - bottom) * i / STEPS for i in range(STEPS)] + [top]


class HeightVolumeDataTests(unittest.TestCase):
  def test_max_volume(self):
    for reference in REFERENCES:
      with self.subTest(reference.factory.__name__):
        well = reference.factory("plate").get_well(0)
        self.assertIsNotNone(well.height_volume_data)
        self.assertEqual(well.max_volume, reference.max_volume)

  def test_volume_from_height(self):
    for reference in REFERENCES:
      with self.subTest(reference.factory.__name__):
        well = reference.factory("plate").get_well(0)
        tolerance = max(0.01, 1e-5 * reference.max_volume)
        for height in _sweep(reference.top_height):
          self.assertAlmostEqual(
            well.compute_volume_from_height(height),
            reference.volume_from_height(height),
            delta=tolerance,
            msg=f"at {height} mm",
          )

  def test_height_from_volume(self):
    for reference in REFERENCES:
      height_from_volume = reference.height_from_volume
      if height_from_volume is None:
        continue
      with self.subTest(reference.factory.__name__):
        well = reference.factory("plate").get_well(0)
        top_volume = reference.top_volume
        if top_volume is None:
          top_volume = reference.volume_from_height(reference.top_height)
        # Volumes below what a well holds at height 0 have no height.
        volumes = _sweep(top_volume, bottom=reference.volume_from_height(0))
        if reference.max_volume <= top_volume:
          volumes.append(reference.max_volume)
        for volume in volumes:
          self.assertAlmostEqual(
            well.compute_height_from_volume(volume),
            height_from_volume(volume),
            delta=reference.height_tolerance,
            msg=f"at {volume} uL",
          )


if __name__ == "__main__":
  unittest.main()
