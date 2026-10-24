pylabrobot.revvity package
==========================

Celigo
------

.. currentmodule:: pylabrobot.revvity.celigo

Load the vendor configuration explicitly, construct the instrument, then assign the
plate used for well navigation, a plate handle in a resource store:

.. code-block:: python

   from pylabrobot.revvity import Celigo, CeligoConfig
   from pylabrobot.resources.store import ResourceStore

   store = ResourceStore.in_memory()
   plate = await store.create("cor_96_wellplate_360uL_Fb", name="imaging_plate")

   config = CeligoConfig.from_install("/path/to/Celigo/ConfigFiles")
   celigo = Celigo(config=config)
   celigo.set_plate(plate)

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    Celigo
    AcquisitionResult
    FocusResult
    ControllerInfo
    ControllerStatus
    DetectedMotorAddress
    SelfTestReport

Camera
------

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    CeligoCamera
    CameraFrame
    CameraError

Motion and optics
-----------------

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    Axis
    LinearAxis
    StepperMotor
    MotorController
    FilterWheel
    MagnificationChanger
    Galvo
    GalvoControllerStatus
    Laser

Configuration
-------------

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    CeligoConfig
    CeligoHardwareConfig
    AxisConfig
    LinearAxisConfig
    FilterWheelConfig
    FilterMapEntry
    IOConfig
    AnalogInputConfig
    DigitalIOConfig
    LightingIOConfig
    HardwareDefaultConfig
    NavigationConfig
    CalibrationConfig
    Calibrated2DPolynomialTransform
    ChannelDescriptor
    ExternalCameraControlConfig
    GalvoAxisOpticalCalibration
    GalvoConfig
    GalvoMagnificationCalibration
    GalvoOpticalCalibration
    IlluminationChannelConfig

Coordinates and navigation
--------------------------

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    CoordinateSystems
    well_to_stage_mm

Configuration loaders
---------------------

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    load_channel_descriptors
    load_galvo_calibrations
    load_galvo_optical_calibration
    load_illumination_channels

Errors
------

.. autosummary::
  :toctree: _autosummary
  :nosignatures:
  :recursive:

    CeligoError
