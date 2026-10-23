"""Golden tests of what the ImageXpress Pico does today.

Each scenario drives the public API against a fake gRPC channel and records every call sent, in
order: the RPC path, the lock identifier sent as metadata, the timeout and the request. A
SnapImages request is recorded as its two decoded JSON documents (labware and snap parameters);
every other request as hex. The plate is snapshotted to pin that capturing leaves it unchanged.
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import struct
import unittest
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest

pytest.importorskip("numpy")
pytest.importorskip("grpc")

import numpy as np  # type: ignore[import-not-found]  # noqa: E402

from pylabrobot.io.sila.grpc import (  # noqa: E402
  decode_fields,
  get_field_bytes,
  length_delimited,
  sila_string,
  varint_field,
)
from pylabrobot.molecular_devices.imageXpress.pico import pico as pico_module  # noqa: E402
from pylabrobot.molecular_devices.imageXpress.pico.models import (  # noqa: E402
  Exposure,
  FocalPosition,
  ImagingMode,
  ImagingResult,
  Objective,
)
from pylabrobot.molecular_devices.imageXpress.pico.pico import Pico  # noqa: E402
from pylabrobot.resources import (  # noqa: E402
  Greiner_384_wellplate_28ul_Fb,
  Plate,
  celltreat_24_wellplate_3300uL_Fb,
  celltreat_96_wellplate_350uL_Ub,
  cor_96_wellplate_360uL_Fb,
  cor_cos_6_wellplate_16800uL_Fb,
)
from pylabrobot.testing.golden import check_golden, snapshot_resources  # noqa: E402

HERE = pathlib.Path(__file__).parent

_LOCK_SVC = "sila2.org.silastandard.core.lockcontroller.v1.LockController"
_INST_SVC = "sila2.moldev.com.instruments.instrumentcontroller.v1.InstrumentController"
_SNAP_SVC = "sila2.moldev.com.instruments.snapcontroller.v1.SnapController"
_OBJ_SVC = "sila2.moldev.com.instruments.objectivescontroller.v1.ObjectivesController"
_FC_SVC = "sila2.moldev.com.instruments.filtercubescontroller.v1.FilterCubesController"

# The snap parameters carry the local time; the clock is fixed to this during a scenario.
FIXED_TIME = 1_700_000_000.0


def _sila_string_response(value: str) -> bytes:
  return length_delimited(1, sila_string(value))


def _json_response(value: Dict[str, Any]) -> bytes:
  return _sila_string_response(json.dumps(value))


def _intermediate_response(chunk: bytes, checksum: int) -> bytes:
  metadata = (
    length_delimited(1, varint_field(1, 0))
    + length_delimited(2, varint_field(1, checksum & 0xFFFFFFFFFFFFFFFF))
    + length_delimited(3, varint_field(1, 1))
    + length_delimited(4, varint_field(1, 0))
  )
  return length_delimited(1, length_delimited(1, chunk)) + length_delimited(
    2, length_delimited(1, metadata)
  )


def _snap_event(pixels: List[List[int]], exposure_us: int) -> Dict[str, Any]:
  array = np.array(pixels, dtype=np.uint16)
  return {
    "imageData": {
      "imageBuffer": base64.b64encode(array.tobytes()).decode(),
      "imageBufferInfo": {"width": array.shape[1], "height": array.shape[0]},
      "capturedImageInfo": {"exposureTimeUs": exposure_us},
    }
  }


def _unwrap_sila_string(data: Optional[bytes]) -> str:
  assert data is not None
  value = get_field_bytes(decode_fields(data), 1)
  assert value is not None
  return value.decode("utf-8")


def _decode_request(path: str, request: bytes) -> Any:
  if path == f"/{_SNAP_SVC}/SnapImages":
    fields = decode_fields(request)
    return {
      "labware": json.loads(_unwrap_sila_string(get_field_bytes(fields, 1))),
      "snap": json.loads(_unwrap_sila_string(get_field_bytes(fields, 2))),
    }
  return request.hex()


class _Channel:
  """A fake gRPC channel: answers from a table and records every call."""

  def __init__(self) -> None:
    self.sent: List[Dict[str, Any]] = []
    self.responses: Dict[str, bytes] = {}
    self.stream_responses: Dict[str, List[bytes]] = {}

  def _record(self, path: str, request: bytes, metadata: Any, timeout: Any) -> None:
    entry: Dict[str, Any] = {"rpc": path}
    if metadata is not None:
      entry["lock"] = [value.hex() for _, value in metadata]
    entry["timeout"] = timeout
    entry["request"] = _decode_request(path, request)
    self.sent.append(entry)

  def unary_unary(
    self, path: str, request_serializer: Any = None, response_deserializer: Any = None
  ):
    def handler(request: bytes, metadata: Any = None, timeout: Any = None) -> bytes:
      self._record(path, request, metadata, timeout)
      return self.responses.get(path, b"")

    return handler

  def unary_stream(
    self, path: str, request_serializer: Any = None, response_deserializer: Any = None
  ):
    def handler(request: bytes, metadata: Any = None, timeout: Any = None):
      self._record(path, request, metadata, timeout)
      return iter(self.stream_responses.get(path, []))

    return handler

  def close(self) -> None:
    self.sent.append({"rpc": "close"})


class _Rig:
  """A Pico on a fake channel, and the record of a scenario's steps."""

  def __init__(self, test: unittest.TestCase) -> None:
    self.test = test
    self.channel = _Channel()
    self.steps: List[Dict[str, Any]] = []
    installed_objectives = [{"Id": Objective.O_4X_PL_FL.objective_id}, {"Id": "empty"}]
    self.channel.responses.update(
      {
        f"/{_OBJ_SVC}/Get_InstalledObjectives": _json_response(
          {"objectivesData": installed_objectives}
        ),
        f"/{_FC_SVC}/Get_InstalledFilterCubes": _json_response(
          {"filterCubesData": [{"Id": "DAPI"}, {"Id": "FITC"}]}
        ),
        f"/{_OBJ_SVC}/GetAvailableObjectivesForPosition": _json_response(
          {
            "objectives": [
              {"Id": Objective.O_4X_PL_FL.objective_id},
              {"Id": Objective.O_10X_PL_FL.objective_id},
            ]
          }
        ),
        f"/{_FC_SVC}/Get_CompatibleFilterCubes": _json_response(
          {"filterCubes": [{"Id": "DAPI"}, {"Id": "FITC"}]}
        ),
        f"/{_SNAP_SVC}/SnapImages": _sila_string_response("exec-uuid"),
        f"/{_INST_SVC}/Get_InstrumentConfiguration": _json_response(
          {"InstrumentConfiguration": {"SerialNumber": "0000"}}
        ),
      }
    )
    self.pico = Pico(
      host="127.0.0.1",
      objectives={0: Objective.O_4X_PL_FL, 1: Objective.O_10X_PL_FL},
      filter_cubes={0: ImagingMode.DAPI, 1: ImagingMode.GFP},
    )

  def answer_snap(self, pixels: List[List[int]], exposure_us: int) -> None:
    blob = json.dumps(_snap_event(pixels, exposure_us)).encode("utf-8")
    checksum = struct.unpack("<q", hashlib.md5(blob, usedforsecurity=False).digest()[:8])[0]
    self.channel.stream_responses[f"/{_SNAP_SVC}/SnapImages_Intermediate"] = [
      _intermediate_response(blob, checksum)
    ]

  async def step(self, call: str, coro: Any, plate: Optional[Plate] = None) -> Any:
    start = len(self.channel.sent)
    entry: Dict[str, Any] = {"call": call}
    try:
      with mock.patch.object(pico_module.time, "time", return_value=FIXED_TIME):
        result = await coro
      entry["result"] = _result_json(result)
    except (ValueError, RuntimeError) as error:
      result = None
      entry["error"] = f"{type(error).__name__}: {error}"
    entry["sent"] = self.channel.sent[start:]
    if plate is not None:
      entry["resources"] = snapshot_resources(plate)
    self.steps.append(entry)
    return result

  async def setup(self) -> None:
    with mock.patch("grpc.insecure_channel", return_value=self.channel):
      await self.step("setup()", self.pico.setup())

  def check(self, scenario: str, plate: Optional[Plate] = None) -> None:
    record: Dict[str, Any] = {"steps": self.steps}
    if plate is not None:
      record["resources"] = snapshot_resources(plate)
    check_golden(self.test, HERE / f"{scenario}.json", record)


def _result_json(result: Any) -> Any:
  if isinstance(result, ImagingResult):
    return {
      "images": [np.asarray(image).tolist() for image in result.images],
      "exposure_time": result.exposure_time,
      "focal_height": result.focal_height,
    }
  return result


async def _capture(
  rig: _Rig,
  plate: Plate,
  row: int,
  column: int,
  mode: ImagingMode = ImagingMode.DAPI,
  objective: Objective = Objective.O_4X_PL_FL,
  exposure_time: Exposure = 15.0,
  focal_height: FocalPosition = 2.5,
) -> None:
  await rig.step(
    f"capture(row={row}, column={column}, mode={mode.name}, objective={objective.name}, "
    f"exposure_time={exposure_time!r}, focal_height={focal_height!r}, plate={plate.name})",
    rig.pico.capture(
      row=row,
      column=column,
      mode=mode,
      objective=objective,
      exposure_time=exposure_time,
      focal_height=focal_height,
      gain=0,
      plate=plate,
    ),
    plate=plate,
  )


class PicoGoldenTests(unittest.IsolatedAsyncioTestCase):
  async def test_setup_door_and_stop(self):
    rig = _Rig(self)
    await rig.setup()
    await rig.step("request_configuration()", rig.pico.request_configuration())
    await rig.step("open_door()", rig.pico.open_door())
    await rig.step("close_door()", rig.pico.close_door())
    await rig.step("enter_objective_maintenance(1)", rig.pico.enter_objective_maintenance(1))
    await rig.step("exit_objective_maintenance()", rig.pico.exit_objective_maintenance())
    await rig.step("stop()", rig.pico.stop())
    rig.check("setup_door_and_stop")

  async def test_capture_96_flat(self):
    rig = _Rig(self)
    plate = cor_96_wellplate_360uL_Fb("plate")
    await rig.setup()
    rig.answer_snap([[1, 2], [3, 4]], exposure_us=15000)
    await _capture(rig, plate, row=0, column=0)
    rig.answer_snap([[5, 6, 7]], exposure_us=8000)
    await _capture(
      rig,
      plate,
      row=7,
      column=11,
      mode=ImagingMode.GFP,
      objective=Objective.O_10X_PL_FL,
      exposure_time="machine-auto",
      focal_height="machine-auto",
    )
    rig.check("capture_96_flat", plate)

  async def test_capture_96_round_bottom_with_lid(self):
    rig = _Rig(self)
    plate = celltreat_96_wellplate_350uL_Ub("plate", with_lid=True)
    await rig.setup()
    rig.answer_snap([[9, 8], [7, 6]], exposure_us=2000)
    await _capture(rig, plate, row=3, column=5, mode=ImagingMode.BRIGHTFIELD, exposure_time=2.0)
    rig.check("capture_96_round_bottom_with_lid", plate)

  async def test_capture_384(self):
    rig = _Rig(self)
    plate = Greiner_384_wellplate_28ul_Fb("plate")
    await rig.setup()
    rig.answer_snap([[10, 20], [30, 40]], exposure_us=15000)
    await _capture(rig, plate, row=15, column=23)
    rig.check("capture_384", plate)

  async def test_capture_24_and_6(self):
    rig = _Rig(self)
    plate_24 = celltreat_24_wellplate_3300uL_Fb("plate_24")
    plate_6 = cor_cos_6_wellplate_16800uL_Fb("plate_6")
    await rig.setup()
    rig.answer_snap([[1]], exposure_us=15000)
    await _capture(rig, plate_24, row=3, column=5)
    rig.answer_snap([[2]], exposure_us=15000)
    await _capture(rig, plate_6, row=1, column=2)
    rig.check("capture_24_and_6", plate_24)

  async def test_capture_refused(self):
    rig = _Rig(self)
    plate = cor_96_wellplate_360uL_Fb("plate")
    await rig.setup()
    await _capture(rig, plate, row=0, column=0, objective=Objective.O_20X_PL_FL)
    await _capture(rig, plate, row=0, column=0, mode=ImagingMode.CY5)
    rig.check("capture_refused", plate)


if __name__ == "__main__":
  unittest.main()
