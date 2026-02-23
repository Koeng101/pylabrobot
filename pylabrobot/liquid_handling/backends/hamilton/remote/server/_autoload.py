"""RPC handlers for autoload operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pylabrobot.resources.barcode import Barcode1DSymbology

from .. import star_service_pb2 as pb2
from ..helpers import extract_optional_field

if TYPE_CHECKING:
  from connectrpc.request import RequestContext

  from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend

# Proto enum value -> Python Barcode1DSymbology literal
_PROTO_TO_BARCODE_SYMBOLOGY: dict[int, Barcode1DSymbology] = {
  pb2.BARCODE_CODE128: "Code 128 (Subset B and C)",
  pb2.BARCODE_CODE39: "Code 39",
  pb2.BARCODE_CODABAR: "Codebar",
  pb2.BARCODE_CODE93: "Code 93",
  pb2.BARCODE_CODE25: "Code 2of5 Interleaved",
  pb2.BARCODE_EAN128: "YESN/EAN 8",
}


class AutoloadServerMixin:
  _backend: STARBackend
  """RPC handlers for autoload operations.

  ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
  """

  async def initialize_autoload(
    self, request: pb2.InitializeAutoloadRequest, ctx: RequestContext
  ) -> pb2.InitializeAutoloadResponse:
    await self._backend.initialize_autoload()
    return pb2.InitializeAutoloadResponse()

  async def move_autoload_to_safe_z_position(
    self,
    request: pb2.MoveAutoloadToSafeZPositionRequest,
    ctx: RequestContext,
  ) -> pb2.MoveAutoloadToSafeZPositionResponse:
    await self._backend.move_autoload_to_safe_z_position()
    return pb2.MoveAutoloadToSafeZPositionResponse()

  async def request_autoload_track(
    self, request: pb2.RequestAutoloadTrackRequest, ctx: RequestContext
  ) -> pb2.RequestAutoloadTrackResponse:
    track = await self._backend.request_autoload_track()
    return pb2.RequestAutoloadTrackResponse(track=track)

  async def request_autoload_type(
    self, request: pb2.RequestAutoloadTypeRequest, ctx: RequestContext
  ) -> pb2.RequestAutoloadTypeResponse:
    autoload_type = await self._backend.request_autoload_type()
    return pb2.RequestAutoloadTypeResponse(autoload_type=autoload_type)

  async def request_presence_of_carriers_on_deck(
    self,
    request: pb2.RequestPresenceOfCarriersOnDeckRequest,
    ctx: RequestContext,
  ) -> pb2.RequestPresenceOfCarriersOnDeckResponse:
    carriers = await self._backend.request_presence_of_carriers_on_deck()
    return pb2.RequestPresenceOfCarriersOnDeckResponse(carriers=carriers)

  async def request_presence_of_carriers_on_loading_tray(
    self,
    request: pb2.RequestPresenceOfCarriersOnLoadingTrayRequest,
    ctx: RequestContext,
  ) -> pb2.RequestPresenceOfCarriersOnLoadingTrayResponse:
    carriers = await self._backend.request_presence_of_carriers_on_loading_tray()
    return pb2.RequestPresenceOfCarriersOnLoadingTrayResponse(carriers=carriers)

  async def request_presence_of_single_carrier_on_loading_tray(
    self,
    request: pb2.RequestPresenceOfSingleCarrierOnLoadingTrayRequest,
    ctx: RequestContext,
  ) -> pb2.RequestPresenceOfSingleCarrierOnLoadingTrayResponse:
    present = await self._backend.request_presence_of_single_carrier_on_loading_tray(
      track=request.track,
    )
    return pb2.RequestPresenceOfSingleCarrierOnLoadingTrayResponse(present=present)

  async def move_autoload_to_slot(
    self, request: pb2.MoveAutoloadToSlotRequest, ctx: RequestContext
  ) -> pb2.MoveAutoloadToSlotResponse:
    await self._backend.move_autoload_to_slot(slot_number=request.slot_number)
    return pb2.MoveAutoloadToSlotResponse()

  async def move_autoload_to_track(
    self, request: pb2.MoveAutoloadToTrackRequest, ctx: RequestContext
  ) -> pb2.MoveAutoloadToTrackResponse:
    await self._backend.move_autoload_to_track(track=request.track)
    return pb2.MoveAutoloadToTrackResponse()

  async def park_autoload(
    self, request: pb2.ParkAutoloadRequest, ctx: RequestContext
  ) -> pb2.ParkAutoloadResponse:
    await self._backend.park_autoload()
    return pb2.ParkAutoloadResponse()

  async def take_carrier_out_to_autoload_belt(
    self,
    request: pb2.TakeCarrierOutToAutoloadBeltRequest,
    ctx: RequestContext,
  ) -> pb2.TakeCarrierOutToAutoloadBeltResponse:
    carrier = self._backend.deck.get_resource(request.carrier_name)
    await self._backend.take_carrier_out_to_autoload_belt(carrier=carrier)  # type: ignore[arg-type]
    return pb2.TakeCarrierOutToAutoloadBeltResponse()

  async def set_barcode_type(
    self, request: pb2.SetBarcodeTypeRequest, ctx: RequestContext
  ) -> pb2.SetBarcodeTypeResponse:
    symbology = _PROTO_TO_BARCODE_SYMBOLOGY.get(request.barcode_symbology)
    await self._backend.set_1d_barcode_type(barcode_symbology=symbology)
    return pb2.SetBarcodeTypeResponse()

  async def load_carrier_from_tray_and_scan_carrier_barcode(
    self,
    request: pb2.LoadCarrierFromTrayAndScanCarrierBarcodeRequest,
    ctx: RequestContext,
  ) -> pb2.LoadCarrierFromTrayAndScanCarrierBarcodeResponse:
    carrier = self._backend.deck.get_resource(request.carrier_name)

    barcode_symbology_int = extract_optional_field(request, "barcode_symbology")
    barcode_symbology = (
      _PROTO_TO_BARCODE_SYMBOLOGY.get(barcode_symbology_int)
      if barcode_symbology_int is not None
      else None
    )

    barcode = await self._backend.load_carrier_from_tray_and_scan_carrier_barcode(
      carrier=carrier,  # type: ignore[arg-type]
      carrier_barcode_reading=request.carrier_barcode_reading,
      barcode_symbology=barcode_symbology,
      barcode_position=request.barcode_position,
      barcode_reading_window_width=request.barcode_reading_window_width,
      reading_speed=request.reading_speed,
    )

    if barcode is not None:
      return pb2.LoadCarrierFromTrayAndScanCarrierBarcodeResponse(barcode=barcode.data)
    return pb2.LoadCarrierFromTrayAndScanCarrierBarcodeResponse()

  async def set_carrier_monitoring(
    self, request: pb2.SetCarrierMonitoringRequest, ctx: RequestContext
  ) -> pb2.SetCarrierMonitoringResponse:
    await self._backend.set_carrier_monitoring(should_monitor=request.should_monitor)
    return pb2.SetCarrierMonitoringResponse()

  async def load_carrier(
    self, request: pb2.LoadCarrierRequest, ctx: RequestContext
  ) -> pb2.LoadCarrierResponse:
    carrier = self._backend.deck.get_resource(request.carrier_name)
    await self._backend.load_carrier(carrier=carrier)  # type: ignore[arg-type]
    return pb2.LoadCarrierResponse()

  async def set_loading_indicators(
    self, request: pb2.SetLoadingIndicatorsRequest, ctx: RequestContext
  ) -> pb2.SetLoadingIndicatorsResponse:
    await self._backend.set_loading_indicators(
      bit_pattern=list(request.bit_pattern),
      blink_pattern=list(request.blink_pattern),
    )
    return pb2.SetLoadingIndicatorsResponse()

  async def unload_carrier(
    self, request: pb2.UnloadCarrierRequest, ctx: RequestContext
  ) -> pb2.UnloadCarrierResponse:
    carrier = self._backend.deck.get_resource(request.carrier_name)
    await self._backend.unload_carrier(carrier=carrier)  # type: ignore[arg-type]
    return pb2.UnloadCarrierResponse()

  async def request_instrument_initialization_status(
    self,
    request: pb2.RequestInstrumentInitializationStatusRequest,
    ctx: RequestContext,
  ) -> pb2.RequestInstrumentInitializationStatusResponse:
    initialized = await self._backend.request_instrument_initialization_status()
    return pb2.RequestInstrumentInitializationStatusResponse(initialized=initialized)

  async def request_autoload_initialization_status(
    self,
    request: pb2.RequestAutoloadInitializationStatusRequest,
    ctx: RequestContext,
  ) -> pb2.RequestAutoloadInitializationStatusResponse:
    initialized = await self._backend.request_autoload_initialization_status()
    return pb2.RequestAutoloadInitializationStatusResponse(initialized=initialized)
