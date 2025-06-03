# 3DScannerTestingAPI
Repository to hold 3D scanner api and testing scripts. 

## Installation
Clone repository and run the install_py_drive_api.bat script

Dependencies will be installed if needed:
    zaber-motion
    pythonnet
    pyserial
    pyautogui

setup.py will run to create py whl install file from the files in the py_drive_api directory.

The install bat file will first install setuptools and wheel packages to enable building the whl distribution file, if needed.

Old versions of the api will first be uninstalled and then the newly built version will be installed to the user's or system's "site-packages" directory.

## Supported Hardware
The current version provides support for the zaber actuators via the python "zaber-motion" library that is installed as a dependency.

Also support for the oriental motor actuators via serial modbus 485 commands. pythonnet dependency will allow modbus_controller.py to import common language runtime "clr" in python to define python wrappers for the functions in the oriental motor dll. If the dll is unavailable or unsupported on your system, then oriental.py provides a DriverModbusIO class for basic operations of the actuators.

## Software Compatibility
This api is compatible with scan software versions 6 and 7, and allows developers to issue commands to the windows GUI directly via JSON RPC interface. ui_scripting.py defines the GUI commands available through the python api.

## Included Files
The purpose or function of the various files included in the py_drive_api directory.

### Include
This directory contains any additional files that we want to make available to be packaged in the binary whl file for distribution such as: any calibration pose csv files, dll files for driving actuators, scan setup hardware files, metadata template files, etc.

## Additionally Supported Hardware
We extend the functionality beyond only accessing the zaber-motion actuators.

### oriental_motor
This directory contains files to define the functions that we previously used in test scripts, however they are specifically for oriental motor actuators. Previously, we had accessed various functions through the zaber-motion python api, and since there is no oriental motor api we utilize pythonnet to access the functions via common language runtime wrappers.

#### base_axis
This is the base class for the linear and rotary actuators. The bulk of the function and attribute definitions lies here. This file will define everything that both classes have in common, and then the rotary axis class can override certain functions like "move" to its specific use case in degrees.

#### exception_lib
This file defines exceptions to be thrown for common errors that may occur during runtime.

#### modbus_controller
The modbus controller is the lowest level that the python code reaches. It is a wrapper class that defines the various functions needed to operate the Scan Platform, and specifically it is using the functions available from the oriental motor dll made available in the include folder.

#### oriental
This file is only for backup in the case that the dll for driving motors becomes unavailable. The dll is much more complete and offers more functions, however if incompatible on a system, this file is provided to still afford the most basic functionality.

#### rotary_axis
This file defines the override methods for moving in degrees if an axis is a rotary actuator. This is within the oriental motor directory, since it is specific to that hardware.

#### serial_com
This file defines the communication parameters for sending data as per the modbus 485 protocol, and is responsible for establishing the connection over the COM ports.

#### units
Here we define the conversion factors to enable unit conversions from the raw values that are read from the memory registers on the actuators. We commonly deal with values in degrees or millimeters.

### base_axis
This is the base class for LinearSxis and RotaryAxis classes. There is much overlap and it was implemented using the zaber-motion api prior to the relase of the oriental motor hardware. Thus, more functions may be available via this class, however the most used move and home methods will behave the same across zaber or oriental devices. 

### dev_connection
This class is the main entry point for the api. It defines a context handler in python that safely opens and shuts ports on error or termination. This class is easy to instantiate and will return a ScanPlatform object that has access to all of the necessary / connected actuators and home positions and methods of interest. 

### linear_axis
This class defines the move methods and behavior for a linear actuator from zaber. The units are in mm and the home position is based on the working distance of the scanner as opposed to the zero position of the actuator. 

### poses
This file defines common calibration poses that may be used in a scanner calibration routine.

### ref_variables
This defines the various options available to query the zaber devices for their internal settings.

### rotary_axis
Here we override the move method of the base class to ensure that we are moving in degrees for a rotary axis, and that the 0, or home position, is that direction that is normal to the scanner's optical axis.

### scan_platform
This class is the one that encapsulates the entire scan motion platform, incorporating all of the available axes. The linear and rotary stages are available here. That's 5-axes on the first system and 2-axes on the later system. 

### ui_scripting
This file is the JSON RPC interface for controlling the scan software gui. The software is built to accept only certain relevant functions, such as capturing a scan, measuring an artifact, performing a calibration, capturing calibration views, etc. The various functions available are all shown in this file.

### Scripts
This directory contains various test scripts for testing the hardware / scanner / software setup. 

#### 30poseSetup
This script tests 30 poses for calibration.

#### artefact-views


#### Calibrate-ScanBallPlate-ExportZip

#### Calibrate-ScannBallPlate-NoZip

#### CalibrationsForDays-MOAC

#### calibTransientResponse-ColdStart

#### IMU-metadata-test

