from __future__ import annotations

import abc
import logging
from typing import Optional

from pylabrobot.agilent.biotek.plate_reader_base import BioTekPlateReaderDriver

logger = logging.getLogger(__name__)


class _CytationBase(BioTekPlateReaderDriver, metaclass=abc.ABCMeta):
  """Shared base for Cytation 1 and Cytation 5 devices.

  Owns the serial connection, the loading tray, and the reads and temperature control
  inherited from the BioTek base. Model-specific hardware (the Cytation 5's camera) is
  added by the subclass.
  """

  _model_name: str  # set by subclass

  def __init__(
    self,
    name: str,
    device_id: Optional[str] = None,
  ):
    super().__init__(
      device_id=device_id,
      human_readable_device_name=self._model_name,
    )
    self.name = name
