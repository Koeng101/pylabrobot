"""A STAR server's settings: the defaults its device's features use where a call names none.

They are a JSON file holding the `Settings` message (`v1/settings.proto`), read when the server
starts. Anything not in it keeps the default in the code.
"""

from typing import Optional

from google.protobuf import json_format

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.server import generated_codec as codec
from pylabrobot.hamilton.star.server.v1 import settings_pb2 as spb

Settings = spb.Settings


def read_settings(path: str) -> spb.Settings:
  """Read a settings file. A field it does not know is an error, so a misspelled one is caught.

  Raises:
    ValueError: If the file is not a `Settings` message.
  """
  with open(path) as f:
    text = f.read()
  try:
    return json_format.Parse(text, spb.Settings())
  except json_format.ParseError as error:
    raise ValueError(f"{path} is not a STAR server's settings: {error}") from error


def put_in_place(device: STARDevice, settings: Optional[spb.Settings]) -> None:
  """Set what `settings` gives on the features the device has now. Those it lacks are skipped.

  Raises:
    ValueError: If a feature refuses a value, as a dispensing drive refuses a speed outside its
      range.
  """
  if settings is None:
    return
  driver = device.driver
  for arm in driver.arms:
    if settings.HasField("pipettes") and arm.pipettes is not None:
      codec.put_pipettes_settings(arm.pipettes, settings.pipettes)
    if settings.HasField("head96") and arm.head96 is not None:
      codec.put_head96_settings(arm.head96, settings.head96)
    if settings.HasField("head384") and arm.head384 is not None:
      codec.put_head384_settings(arm.head384, settings.head384)
    if settings.HasField("iswap") and arm.iswap is not None:
      codec.put_iswap_settings(arm.iswap, settings.iswap)
    if settings.HasField("core_grippers") and arm.core_grippers is not None:
      codec.put_core_grippers_settings(arm.core_grippers, settings.core_grippers)
  if settings.HasField("left_x_arm") and driver.left_x_arm is not None:
    codec.put_x_arm_settings(driver.left_x_arm, settings.left_x_arm)
  if settings.HasField("right_x_arm") and driver.right_x_arm is not None:
    codec.put_x_arm_settings(driver.right_x_arm, settings.right_x_arm)


__all__ = ["Settings", "put_in_place", "read_settings"]
