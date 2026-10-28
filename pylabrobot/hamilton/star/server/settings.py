"""A STAR server's settings: the defaults its device's features use where a call names none.

They are a JSON file holding the `Settings` message (`v1/settings.proto`), read when the server
starts. Anything not in it keeps the default in the code.
"""

from typing import Any, Optional

from google.protobuf import json_format

from pylabrobot.hamilton.star.device import STARDevice
from pylabrobot.hamilton.star.server.v1 import settings_pb2 as spb

Settings = spb.Settings

# The features on an arm, by the field of `Settings` that holds theirs.
_ON_AN_ARM = ("pipettes", "head96", "head384", "iswap", "core_grippers")


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
  for name in _ON_AN_ARM:
    if not settings.HasField(name):
      continue
    for arm in driver.arms:
      _set(getattr(arm, name), getattr(settings, name))
  for side in ("left", "right"):
    field = f"{side}_x_arm"
    if settings.HasField(field):
      _set(getattr(driver, field), getattr(settings, field))


def _set(feature: Any, message: Any) -> None:
  if feature is None:
    return
  for fd, value in message.ListFields():
    setattr(feature, fd.name, value)


__all__ = ["Settings", "put_in_place", "read_settings"]
