import asyncio
import logging
import time
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from pylabrobot.byonoy.body import (
  Holder,
  Unit,
  assign_unlocated,
  body_definition,
  holder_definition,
)
from pylabrobot.byonoy.driver import ABS96_ERROR_NAMES, ByonoyDevice, ByonoyDriver
from pylabrobot.byonoy.results import AbsorbanceResult
from pylabrobot.io.binary import Reader, Writer
from pylabrobot.resources import Coordinate, Rotation
from pylabrobot.resources.store import build, handles
from pylabrobot.resources.store.client import ResourceStore
from pylabrobot.resources.store.v1 import store_pb2 as spb
from pylabrobot.resources.store.v1 import types_pb2 as pb
from pylabrobot.utils.list import reshape_2d

logger = logging.getLogger(__name__)


class _ByonoyAbsorbanceReaderPlateHolder(Holder):
  """Plate holder with interlock: blocks drops while illumination unit is on the base."""

  def __init__(self, base: "ByonoyAbsorbanceBaseUnit"):
    super().__init__(base, base.name + "_plate_holder")
    self._base = base

  async def check_can_drop_resource_here(self, resource: handles.Resource) -> None:
    if await self._base.illumination_unit_holder.get_resource_held() is not None:
      raise RuntimeError(
        f"Cannot drop resource {resource.name} onto plate holder while illumination unit is on "
        "the base. Please remove the illumination unit from the base before dropping a resource."
      )
    await super().check_can_drop_resource_here(resource)


class _ByonoyAbsorbanceIlluminationUnitHolder(Holder):
  """Illumination unit holder: blocks drops onto a plate taller than the unit clears."""

  # The tallest plate, lid included, the illumination unit goes on over.
  MAX_PLATE_SIZE_Z = 16.0

  def __init__(self, base: "ByonoyAbsorbanceBaseUnit"):
    super().__init__(base, base.name + "_illumination_unit_holder")
    self._base = base

  async def check_can_drop_resource_here(self, resource: handles.Resource) -> None:
    plate_holder = self._base.plate_holder.handle
    plate = await self._base.plate_holder.get_resource_held()
    if plate is not None:
      # The plate's highest point and the plate holder's height, in one read.
      response = await plate.store.commands.resolve_geometry(
        spb.ResolveGeometryRequest(
          queries=[
            spb.GeometryQuery(resource=plate.ref),
            spb.GeometryQuery(resource=plate_holder.ref),
          ]
        )
      )
      highest, holder = response.results
      top = highest.highest_point - holder.locations[0].z
      if top > self.MAX_PLATE_SIZE_Z:
        raise RuntimeError(
          f"Cannot drop resource {resource.name} onto {self.name}: {plate.name} stands {top:.2f} mm "
          f"tall, above the {self.MAX_PLATE_SIZE_Z:.2f} mm the illumination unit clears."
        )
    await super().check_can_drop_resource_here(resource)


class ByonoyAbsorbanceBaseUnit(Unit):
  """The base of the Byonoy A96A: its body in a resource store, a plate holder and an
  illumination unit holder."""

  def __init__(
    self,
    name: str,
    size_x: float = 155.26,
    size_y: float = 95.48,
    size_z: float = 18.5,
    rotation: Optional[Rotation] = None,
    category: Optional[str] = None,
    model: Optional[str] = None,
    barcode: Optional[pb.Barcode] = None,
    preferred_pickup_location: Optional[Coordinate] = None,
    store: Optional[ResourceStore] = None,
  ):
    """
    Args:
      name: the name of its body in the resource store.
      store: the resource store its body is in; None makes one in memory.
    """
    Unit.__init__(self, name, store)
    self.size = Coordinate(size_x, size_y, size_z)
    self.rotation = rotation
    self.category = category
    self.model = model
    self.barcode = barcode
    self.preferred_pickup_location = preferred_pickup_location
    self.plate_holder = _ByonoyAbsorbanceReaderPlateHolder(self)
    self.illumination_unit_holder = _ByonoyAbsorbanceIlluminationUnitHolder(self)

  def definition(self) -> pb.ResourceDefinition:
    """The base, its plate holder and its illumination unit holder."""
    plate_holder = holder_definition(
      self.plate_holder.name,
      Coordinate(127.76, 85.48, 0),
      location=Coordinate(x=22.5, y=5.0, z=16.0),
      child_location=Coordinate.zero(),
      kind=pb.RESOURCE_KIND_PLATE_HOLDER,
    )
    illumination_unit_holder = holder_definition(
      self.illumination_unit_holder.name,
      Coordinate(self.size.x, self.size.y, 0),
      location=Coordinate(x=0, y=0, z=14.1),
      child_location=Coordinate.zero(),
    )
    return body_definition(
      self.name,
      self.size,
      self.rotation,
      self.category,
      self.model,
      self.barcode,
      self.preferred_pickup_location,
      children=[plate_holder, illumination_unit_holder],
    )

  async def check_can_drop_resource_here(self, resource: handles.Resource) -> None:
    raise RuntimeError(
      "ByonoyDriver does not support assigning child resources directly. "
      "Use the plate_holder or illumination_unit_holder to assign plates and the "
      "illumination unit, respectively."
    )

  async def assign_child_resource(
    self, resource: handles.Resource, location: Optional[Coordinate]
  ) -> None:
    """Put `resource` on the base itself, at `location`, or with no location when None."""
    body = await self.create_resources()
    if location is None:
      await assign_unlocated(body, resource)
    else:
      await body.assign_child_resource(resource, location=location)


class ByonoyAbsorbance96(ByonoyAbsorbanceBaseUnit, ByonoyDriver):
  """The Byonoy Absorbance 96 Automate reader unit.

  Inherits the base unit so it owns the ``plate_holder`` and
  ``illumination_unit_holder``. ``ByonoyAbsorbanceBaseUnit`` comes first in the
  MRO so the body's ``name`` wins over the driver's device-name property.
  """

  _ERROR_NAMES = ABS96_ERROR_NAMES
  _DD_IGNORE_ERRORS_IN_CALIBRATION = 0x800E

  def __init__(
    self, name: str = "byonoy_absorbance_96", store: Optional[ResourceStore] = None
  ) -> None:
    # Drawn with the parking unit's housing, which is the same part, until the detection unit is
    # modelled on its own.
    ByonoyAbsorbanceBaseUnit.__init__(
      self, name=name, model="byonoy_a96a_parking_unit", store=store
    )
    ByonoyDriver.__init__(
      self, pid=0x1199, device_type=ByonoyDevice.ABSORBANCE_96, name="Byonoy A96"
    )
    self.available_wavelengths: List[float] = []

  async def request_ignore_errors_in_calibration(self) -> bool:
    """Read the firmware's experimental calibration-error override.

    Field 0x800E is ``state.ignore_errors_in_calibration`` on A96A firmware
    2024-10-23. This internal field is not a stable vendor API.
    """
    payload = Writer().u16(self._DD_IGNORE_ERRORS_IN_CALIBRATION).u8(0).finish()
    response = await self.send_command(report_id=0x0200, payload=payload, routing_info=b"\x80\x40")
    assert response is not None
    r = Reader(response[2:])
    field_index, flags = r.u16(), r.u8()
    if field_index != self._DD_IGNORE_ERRORS_IN_CALIBRATION or flags & 0x0F != 0x01:
      raise RuntimeError("Unexpected field or type for ignore_errors_in_calibration.")
    value = r.u32()
    if value not in (0, 1):
      raise RuntimeError(f"Unexpected ignore_errors_in_calibration value: {value}.")
    return bool(value)

  async def set_ignore_errors_in_calibration(self, enabled: bool) -> None:
    """Set and verify the firmware's experimental calibration-error override.

    Diagnostic use only: suppressing an error does not establish a valid calibration.
    The field address is specific to A96A firmware 2024-10-23. Save the original
    value with :meth:`request_ignore_errors_in_calibration` and restore it in a
    ``finally`` block. Setup only enables this override when explicitly requested.
    """
    if not isinstance(enabled, bool):
      raise TypeError("enabled must be a bool.")
    if self._in_flight_trigger is not None:
      raise RuntimeError("Cannot change calibration-error override during a measurement.")
    payload = Writer().u16(self._DD_IGNORE_ERRORS_IN_CALIBRATION).u8(0).u32(int(enabled)).finish()
    command = self._assemble_command(0x0210, payload, routing_info=b"\x00\x40")
    async with self._io_lock:
      await self.io.write(command)
      deadline = time.monotonic() + 10
      while True:
        if time.monotonic() >= deadline:
          raise TimeoutError("Timed out waiting for calibration-error override acknowledgement.")
        response = await self.io.read(64, timeout=30)
        if len(response) < 6:
          continue
        r = Reader(response)
        if r.u16() != 0x0020 or r.u16() != 0x0210:
          continue
        code = r.u16()
        if code != 0:
          raise RuntimeError(f"Firmware rejected calibration-error override: 0x{code:04x}.")
        break
    if await self.request_ignore_errors_in_calibration() != enabled:
      raise RuntimeError("Calibration-error override readback does not match requested value.")
    if enabled:
      logger.warning(
        "[%s] calibration-error override enabled; calibration may be invalid", self.name
      )

  async def request_available_absorbance_wavelengths(self) -> List[float]:
    response = await self.send_command(
      report_id=0x0330,
      payload=b"\x00" * 60,
      wait_for_response=True,
      routing_info=b"\x80\x40",
    )
    assert response is not None, "Failed to get available wavelengths."
    reader = Reader(response[2:])
    available_wavelengths = [reader.i16() for _ in range(30)]
    return [w for w in available_wavelengths if w != 0]

  async def _run_abs_measurement(self, signal_wl: int, reference_wl: int, is_reference: bool):
    with self._measurement_in_flight(0x0320):
      await self.send_command(
        report_id=0x0010,
        payload=b"\x00" * 60,
        wait_for_response=False,
      )

      payload2 = Writer().u16(7).u8(0).raw_bytes(b"\x00" * 52).finish()
      await self.send_command(
        report_id=0x0200,
        payload=payload2,
        wait_for_response=False,
      )

      payload3 = Writer().i16(signal_wl).i16(reference_wl).u8(int(is_reference)).u8(0).finish()
      await self.send_command(
        report_id=0x0320,
        payload=payload3,
        wait_for_response=False,
        routing_info=b"\x00\x40",
      )

      # Index by seq so out-of-order/dropped chunks surface as None slots
      # rather than silently shifting subsequent rows into the wrong wells.
      rows_by_seq: List[Optional[List[float]]] = []
      flags_by_seq: List[Optional[int]] = []
      expected_chunks: Optional[int] = None
      t0 = time.time()

      while True:
        if self._abort_requested:
          logger.info("[%s] measurement aborted by cancel()", self.name)
          raise asyncio.CancelledError("Absorbance measurement aborted via cancel().")
        if time.time() - t0 > 120:
          logger.error(
            "[%s] measurement timed out after 120s (signal=%d nm, ref=%d nm)",
            self.name,
            signal_wl,
            reference_wl,
          )
          raise TimeoutError("Measurement timeout.")

        chunk = await self.io.read(64, timeout=30)
        if len(chunk) == 0:
          continue

        reader = Reader(chunk)
        report_id = reader.u16()

        if report_id == 0x0500:
          seq = reader.u8()
          seq_len = reader.u8()
          _ = reader.i16()  # signal_wl_nm
          _ = reader.i16()  # reference_wl_nm
          _ = reader.u32()  # duration_ms
          row = [reader.f32() for _ in range(12)]
          flags = reader.u8()
          _ = reader.u8()  # progress (0..100 running %); not surfaced

          if seq_len == 0:
            raise RuntimeError(f"{self.name} firmware sent chunk with seq_len=0")
          if expected_chunks is None:
            expected_chunks = seq_len
            rows_by_seq = [None] * seq_len
            flags_by_seq = [None] * seq_len
          elif seq_len != expected_chunks:
            raise RuntimeError(
              f"{self.name} firmware changed seq_len mid-stream: {expected_chunks} → {seq_len}"
            )
          if not 0 <= seq < seq_len:
            raise RuntimeError(f"{self.name} firmware sent seq={seq} (seq_len={seq_len})")
          rows_by_seq[seq] = row
          flags_by_seq[seq] = flags

          if all(r is not None for r in rows_by_seq):
            break

    if expected_chunks is None:
      raise RuntimeError(f"{self.name} absorbance read produced no chunks")
    chunk_flags: List[int] = [f for f in flags_by_seq if f is not None]
    rows: List[float] = [v for r in rows_by_seq if r is not None for v in r]

    status = await self.request_status()
    if status.error_code != 0:
      raise RuntimeError(
        f"{self.name} firmware error after measurement (signal={signal_wl} nm, "
        f"ref={reference_wl} nm): {self.describe_error_code(status.error_code)} "
        f"(chunk flags: {[f'0x{f:02x}' for f in chunk_flags]})"
      )
    self._warn_chunk_flags(chunk_flags)

    return rows

  async def initialize_measurements(self):
    REFERENCE_WL = 0
    SIGNAL_WL = 660
    await self._run_abs_measurement(
      signal_wl=SIGNAL_WL,
      reference_wl=REFERENCE_WL,
      is_reference=True,
    )

  async def setup(self, *, ignore_errors_in_calibration: bool = False) -> None:
    """Connect and initialize absorbance measurements.

    Args:
      ignore_errors_in_calibration: Temporarily enable the experimental firmware
        override during calibration. The previous setting is restored even if
        calibration fails. Defaults to False, which leaves the setting unchanged.
        This diagnostic option does not establish measurement accuracy and relies
        on an internal field identified on A96A firmware 2024-10-23.
    """
    if not isinstance(ignore_errors_in_calibration, bool):
      raise TypeError("ignore_errors_in_calibration must be a bool.")
    await self.create_resources()
    await ByonoyDriver.setup(self)
    original_override = None
    if ignore_errors_in_calibration:
      original_override = await self.request_ignore_errors_in_calibration()
    try:
      if ignore_errors_in_calibration:
        await self.set_ignore_errors_in_calibration(True)
      await self.initialize_measurements()
    finally:
      if original_override is not None:
        await self.set_ignore_errors_in_calibration(original_override)
    self.available_wavelengths = await self.request_available_absorbance_wavelengths()
    logger.info(
      "[%s] ready, available wavelengths: %s nm",
      self.name,
      self.available_wavelengths,
    )

  async def read_absorbance(
    self,
    plate: handles.Plate,
    wells: Sequence[handles.Resource],
    wavelength: int,
  ) -> List[AbsorbanceResult]:
    if wavelength not in self.available_wavelengths:
      raise ValueError(
        f"Wavelength {wavelength} nm not in available wavelengths {self.available_wavelengths}."
      )

    logger.info(
      "[%s] reading absorbance: plate='%s', wavelength=%d nm, wells=%d/%d",
      self.name,
      plate.name,
      wavelength,
      len(wells),
      plate.num_items,
    )
    rows = await self._run_abs_measurement(
      signal_wl=wavelength,
      reference_wl=0,
      is_reference=False,
    )

    matrix = reshape_2d(rows, (8, 12))

    return [
      AbsorbanceResult(
        data=matrix,
        wavelength=wavelength,
        temperature=None,
        timestamp=datetime.now(),
      )
    ]


def byonoy_sbs_adapter(name: str) -> pb.ResourceDefinition:
  """A Byonoy SBS adapter: a resource holder, to create in a store."""
  return build.resource(
    name,
    Coordinate(127.76, 85.48, 17.0),
    kind=pb.RESOURCE_KIND_RESOURCE_HOLDER,
    category="resource_holder",
    model="byonoy_a96a_sbs_adapter",
    holder=pb.HolderSpec(
      child_location=build.vec3(
        Coordinate(x=-(155.26 - 127.76) / 2, y=-(95.48 - 85.48) / 2, z=17.0)
      ),
      capacity=1,
    ),
  )


def byonoy_a96a_illumination_unit(name: str) -> pb.ResourceDefinition:
  """A Byonoy A96A illumination unit, to create in a store."""
  size_x = 155.26
  size_y = 95.48
  return build.resource(
    name,
    Coordinate(size_x, size_y, 42.898),
    model="byonoy_a96a_illumination_unit",
    preferred_pickup_location=build.vec3(Coordinate(x=size_x / 2, y=size_y / 2, z=29.5)),
  )


async def byonoy_a96a_detection_unit(
  name: str, store: Optional[ResourceStore] = None
) -> ByonoyAbsorbance96:
  """A Byonoy A96A detection unit, its body found in `store` by name or created there (a new
  store in memory when None)."""
  unit = ByonoyAbsorbance96(name=name, store=store)
  await unit.create_resources()
  return unit


async def byonoy_a96a_parking_unit(
  name: str, store: Optional[ResourceStore] = None
) -> ByonoyAbsorbanceBaseUnit:
  """A Byonoy A96A detection unit holder (base only, no backend), its body found in `store` by
  name or created there (a new store in memory when None)."""
  unit = ByonoyAbsorbanceBaseUnit(name=name, model="byonoy_a96a_parking_unit", store=store)
  await unit.create_resources()
  return unit


async def byonoy_a96a(
  name: str, assign: bool = True, store: Optional[ResourceStore] = None
) -> Tuple[ByonoyAbsorbance96, handles.Resource]:
  """Create a full Byonoy A96A setup (reader + illumination unit) in `store` (a new one in
  memory when None); the illumination unit goes on the reader when `assign`."""
  reader = await byonoy_a96a_detection_unit(name=name, store=store)
  unit_name = name + "_illumination_unit"
  illumination_unit = await reader.store.create(byonoy_a96a_illumination_unit(unit_name), unit_name)
  if assign:
    await reader.illumination_unit_holder.assign_child_resource(illumination_unit)
  return reader, illumination_unit
