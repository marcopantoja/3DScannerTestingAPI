__package__='py_drive_api'
from math import radians
import logging

from zaber_motion.ascii import Connection
from zaber_motion.exceptions import NoDeviceFoundException

from .scan_platform import ScanPlatform
from .oriental_motor.exception_lib import CommunicationError
from .oriental_motor.modbus_controller import ModbusController as mc
from .oriental_motor.rotary_axis import RotaryAxis as OMRotaryAxis
from .oriental_motor.serial_com import SerialCom as sc
from .ui_scripting import UI_Scripting

logger = logging.getLogger(__name__)
class DevConnection():
    """
    This class allows for easy start when writing
    scripts. 
    Use a context manager with this class to ensure
    that objects are instantiated correctly.
    This will return a ScanPlatform() instance on a connected
    serial com port. 
    """
    def __init__(
        self, 
        working_distance=ScanPlatform.DEFAULT_WORK_DISTANCE, 
        scanner_tilt_deg=ScanPlatform.DEFAULT_SCANNER_TILT, 
        target_tilt_deg=ScanPlatform.DEFAULT_TARGET_TILT
        ):
        self.WD = working_distance
        self.scanner_tilt = scanner_tilt_deg
        self.target_tilt = radians(target_tilt_deg)
        self.dev_controller = None
        self.dago_object = None
        self.tilt_axis = None
        try:
            self.devices = sc.detect_devices()
        except:
            raise ConnectionError('Check connection. Devices were not detected!')
    
    def __close__(self):
        if self.dev_controller is not None: 
            try:
                self.dago_object.xrot.move_absolute(
                    0.1, self.dago_object.xrot.units,False
                ) # makes sure when home is called @next startup no crash with hard stop! Homing only goes in the 'down/negative' rotation direction
            except AttributeError: pass
            self.dev_controller.close()
        if self.tilt_axis is not None: self.tilt_axis.close_port()
        if UI_Scripting.CUSTOM_METADATA: UI_Scripting._scanReferenceDataPath('')
        return True

    def __enter__(self):
        if self.start():
            return self.dago_object

    def __exit__(self, exception_type, exception_value, traceback):
        if self.__close__(): return True
        return False

    def __start_controller(self):
        if self.devices is not None:
            for dev in self.devices:
                try:
                    con = Connection.open_serial_port(dev.device)
                    con.detect_devices(False)
                    self.dev_controller = con
                    logger.info(f'Zaber motion device controller found on port {dev.device}!')
                except NoDeviceFoundException:
                    con.close()
                    port = mc(dev.device)
                    if not port.IsPortOpen(): port.PortOpen()
                    ready = port.ReadInternalOutputIO(3).READY
                    if ready:
                        self.tilt_axis = OMRotaryAxis(port, self.WD, self.scanner_tilt, self.target_tilt)
                        logger.info(f'Oriental motor tilt axis found on port {dev.device}!')
                    else: print(f'alarms: {port.GetAlarm(3)}',f'reset: {port.AlarmReset(3)}')
                    if not ready: port.PortClose()
            return True
        return False

    def __start_connection(self):
        if self.dev_controller is not None:
            self.dago_object = ScanPlatform(
                connection=self.dev_controller, 
                WD=self.WD, 
                scanner_tilt_deg=self.scanner_tilt, 
                target_tilt_deg=self.target_tilt,
                OMTiltAxisSerialDevice=self.tilt_axis)
            return True
        return False
    
    def get_platform(self):
        if self.dago_object is not None:
            return self.dago_object
        return False

    def start(self):
        if self.__start_controller():
            if self.__start_connection():
                return True
        return False

if __name__ == "__main__":
    
    # Example: this is how you can instantiate the scanplatform object 
    # use the context manager to ensure serial port is closed when 
    # the script is finished running! Simply pass the scanner tilt as
    # a string for the correct home position!
    with DevConnection(scanner_tilt_deg=-20,target_tilt_deg=-15) as scan_system:
        scan_system.wait_move = False
        scan_system.home_all()
        scan_system.yrot.move(1.5)
        scan_system.move2pose((3,3))