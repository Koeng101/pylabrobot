"""Client stubs for autoload operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pylabrobot.resources.barcode import Barcode1DSymbology
from pylabrobot.resources.carrier import Carrier

from .. import star_service_pb2 as pb2

# Python Barcode1DSymbology literal -> Proto enum value
_BARCODE_SYMBOLOGY_TO_PROTO: dict[Barcode1DSymbology, int] = {
  "Code 128 (Subset B and C)": pb2.BARCODE_CODE128,
  "Code 39": pb2.BARCODE_CODE39,
  "Codebar": pb2.BARCODE_CODABAR,
  "Code 93": pb2.BARCODE_CODE93,
  "Code 2of5 Interleaved": pb2.BARCODE_CODE25,
  "YESN/EAN 8": pb2.BARCODE_EAN128,
}

if TYPE_CHECKING:
  from ..star_service_connect import STARServiceClientSync


class AutoloadClientMixin:
  _client: STARServiceClientSync
  """Client stubs for autoload operations.

  ``self._client`` is a :class:`STARServiceClientSync` instance.
  """

  # -- initialization --

  async def initialize_autoload(self) -> None:
    self._client.initialize_autoload(pb2.InitializeAutoloadRequest())

  # -- movement --

  async def move_autoload_to_safe_z_position(self) -> None:
    self._client.move_autoload_to_safe_z_position(pb2.MoveAutoloadToSafeZPositionRequest())

  async def move_autoload_to_slot(self, slot_number: int) -> None:
    self._client.move_autoload_to_slot(pb2.MoveAutoloadToSlotRequest(slot_number=slot_number))

  async def move_autoload_to_track(self, track: int) -> None:
    self._client.move_autoload_to_track(pb2.MoveAutoloadToTrackRequest(track=track))

  async def park_autoload(self) -> None:
    self._client.park_autoload(pb2.ParkAutoloadRequest())

  # -- queries --

  async def request_autoload_track(self) -> int:
    resp = self._client.request_autoload_track(pb2.RequestAutoloadTrackRequest())
    return resp.track

  async def request_autoload_type(self) -> str:
    resp = self._client.request_autoload_type(pb2.RequestAutoloadTypeRequest())
    return resp.autoload_type

  async def request_presence_of_carriers_on_deck(self) -> list[int]:
    resp = self._client.request_presence_of_carriers_on_deck(
      pb2.RequestPresenceOfCarriersOnDeckRequest()
    )
    return list(resp.carriers)

  async def request_presence_of_carriers_on_loading_tray(self) -> list[int]:
    resp = self._client.request_presence_of_carriers_on_loading_tray(
      pb2.RequestPresenceOfCarriersOnLoadingTrayRequest()
    )
    return list(resp.carriers)

  async def request_presence_of_single_carrier_on_loading_tray(
    self,
    track: int,
  ) -> bool:
    resp = self._client.request_presence_of_single_carrier_on_loading_tray(
      pb2.RequestPresenceOfSingleCarrierOnLoadingTrayRequest(track=track)
    )
    return resp.present

  # -- carrier operations --

  async def take_carrier_out_to_autoload_belt(self, carrier: Carrier) -> None:
    self._client.take_carrier_out_to_autoload_belt(
      pb2.TakeCarrierOutToAutoloadBeltRequest(carrier_name=carrier.name)
    )

  async def load_carrier(self, carrier: Carrier) -> None:
    self._client.load_carrier(pb2.LoadCarrierRequest(carrier_name=carrier.name))

  async def unload_carrier(self, carrier: Carrier) -> None:
    self._client.unload_carrier(pb2.UnloadCarrierRequest(carrier_name=carrier.name))

  # -- barcode --

  async def set_1d_barcode_type(
    self,
    barcode_symbology: Optional[Barcode1DSymbology],
  ) -> None:
    proto_sym = _BARCODE_SYMBOLOGY_TO_PROTO.get(barcode_symbology, pb2.BARCODE_UNKNOWN)  # type: ignore[arg-type]
    self._client.set_barcode_type(pb2.SetBarcodeTypeRequest(barcode_symbology=proto_sym))

  async def load_carrier_from_tray_and_scan_carrier_barcode(
    self,
    carrier: Carrier,
    carrier_barcode_reading: bool = True,
    barcode_symbology: Optional[Barcode1DSymbology] = None,
    barcode_position: float = 4.3,
    barcode_reading_window_width: float = 38.0,
    reading_speed: float = 128.1,
  ) -> Optional[str]:
    kwargs: dict = dict(
      carrier_name=carrier.name,
      carrier_barcode_reading=carrier_barcode_reading,
      barcode_position=barcode_position,
      barcode_reading_window_width=barcode_reading_window_width,
      reading_speed=reading_speed,
    )
    if barcode_symbology is not None:
      kwargs["barcode_symbology"] = _BARCODE_SYMBOLOGY_TO_PROTO.get(
        barcode_symbology, pb2.BARCODE_UNKNOWN
      )

    resp = self._client.load_carrier_from_tray_and_scan_carrier_barcode(
      pb2.LoadCarrierFromTrayAndScanCarrierBarcodeRequest(**kwargs)
    )

    if resp.HasField("barcode"):
      return resp.barcode
    return None

  # -- monitoring / indicators --

  async def set_carrier_monitoring(self, should_monitor: bool = False) -> None:
    self._client.set_carrier_monitoring(
      pb2.SetCarrierMonitoringRequest(should_monitor=should_monitor)
    )

  async def set_loading_indicators(
    self,
    bit_pattern: List[bool],
    blink_pattern: List[bool],
  ) -> None:
    self._client.set_loading_indicators(
      pb2.SetLoadingIndicatorsRequest(
        bit_pattern=bit_pattern,
        blink_pattern=blink_pattern,
      )
    )

  # -- initialization status queries --

  async def request_instrument_initialization_status(self) -> bool:
    resp = self._client.request_instrument_initialization_status(
      pb2.RequestInstrumentInitializationStatusRequest()
    )
    return resp.initialized

  async def request_autoload_initialization_status(self) -> bool:
    resp = self._client.request_autoload_initialization_status(
      pb2.RequestAutoloadInitializationStatusRequest()
    )
    return resp.initialized
