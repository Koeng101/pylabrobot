"""The result of an absorbance measurement, the same for every plate reader, and its data placed
on a plate's grid."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pylabrobot.resources import Plate


@dataclass
class AbsorbanceResult:
  """Optical densities of one wavelength, from one read of a plate.

  Attributes:
    data: optical densities of the measured wells, keyed by well identifier (``"B3"``), row by
      row; wells not measured are not in it.
    wavelength: wavelength in nm.
    temperature: temperature in degrees C, or ``None`` if the reader did not measure one.
    start_timestamp: when the read started.
    end_timestamp: when the read's data was in.
  """

  data: Dict[str, float]
  wavelength: int
  temperature: Optional[float]
  start_timestamp: datetime
  end_timestamp: datetime


@dataclass
class AbsorbanceSpectrumResult:
  """Optical density spectra from one read of a plate.

  Attributes:
    data: each measured well's spectrum, optical density by wavelength in nm in scan order, keyed
      by well identifier (``"B3"``), row by row; wells not measured are not in it.
    temperature: temperature in degrees C, or ``None`` if the reader did not measure one.
    start_timestamp: when the read started.
    end_timestamp: when the read's data was in.
  """

  data: Dict[str, Dict[int, float]]
  temperature: Optional[float]
  start_timestamp: datetime
  end_timestamp: datetime


def get_grid(plate: Plate, data: Dict[str, float]) -> List[List[Optional[float]]]:
  """`grid_of` for a plate held in this process.

  Raises:
    ValueError: As `grid_of`.
  """
  identifiers = [plate.get_child_identifier(well) for well in plate.get_all_items()]
  return grid_of(plate.name, plate.num_items_x, plate.num_items_y, identifiers, data)


def grid_of(
  name: str,
  num_items_x: int,
  num_items_y: int,
  identifiers: Sequence[str],
  data: Dict[str, float],
) -> List[List[Optional[float]]]:
  """`data`, keyed by well identifier, as a [row][column] grid of a plate; None where no value.

  Args:
    name: The plate's name, for messages.
    num_items_x: Its columns.
    num_items_y: Its rows.
    identifiers: Its wells' identifiers, column by column, as its items are ordered.
    data: The values, keyed by well identifier.

  Raises:
    ValueError: if `data` keys a well the plate does not have.
  """
  rows = num_items_y
  position = {
    identifier: (index % rows, index // rows)  # items are column by column
    for index, identifier in enumerate(identifiers)
  }
  unknown = [identifier for identifier in data if identifier not in position]
  if unknown:
    raise ValueError(f"{name} has no wells {unknown}")
  grid: List[List[Optional[float]]] = [[None] * num_items_x for _ in range(rows)]
  for identifier, value in data.items():
    row, column = position[identifier]
    grid[row][column] = value
  return grid


def get_grid_at(
  plate: Plate, result: AbsorbanceSpectrumResult, wavelength: int
) -> List[List[Optional[float]]]:
  """The optical densities of `result` at `wavelength`, as a [row][column] grid of `plate`; None
  where no value.

  Raises:
    ValueError: if `wavelength` was not scanned, or `result` keys a well `plate` does not have.
  """
  if any(wavelength not in spectrum for spectrum in result.data.values()):
    raise ValueError(f"{wavelength} nm was not scanned")
  return get_grid(plate, {well: spectrum[wavelength] for well, spectrum in result.data.items()})
