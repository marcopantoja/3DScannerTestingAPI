import logging
import math
import os
from datetime import datetime as dt

from ...py_drive_api import logs_dir
from ..oriental_motor.serial_com import SerialCom
from ..oriental_motor.units import Units

if __name__=="__main__":__package__='py_drive_api'


direntries = os.listdir(logs_dir)
log_path = os.path.join(logs_dir, 'logs')
if 'logs' not in direntries:
    os.makedirs(log_path)
Logs = {
    'INFO.log': logging.INFO,
    'WARNING.log': logging.WARNING,
    'DEBUG.log': logging.DEBUG
}
levels = [Logs[l] for l in Logs]
log_files = [os.path.join(log_path, f) for f in Logs]
h = 0
handlers = []
for log_file in log_files:
    handler = logging.FileHandler(log_file, mode='a')
    handler.setLevel(levels[h])
    handlers.append(handler)
logging.basicConfig(
    format='%(asctime)s %(module)s \t\t%(message)s',
    datefmt='%y%m%d %H%M%S',
    style='%',
    level=logging.NOTSET,
    handlers=handlers
)
logger = logging.getLogger(__name__)
# generic axis class used for methods applicable to all devices


class BaseAxis( SerialCom):
    """
    Base class of LinearAxis and RotaryAxis.

    Attributes
    ----------
    WD : float
        the current projector working distance
    _device : ModbusController
        the associated 'device' object for serial com
    label : str
        readable label to id axes
    _home : float
        position where homing command will finally send axis
    _wait_move : bool
        determine if axis moves happen async
    settings : dict
        all available settings and thier reported values
    units : Units
        units for device to interpret move commands, etc.
    bounds : tuple
        upper and lower limits of this axis to avoid collision
    type : str
        'lin' or 'rot' denoting the axis type

    Methods
    -------
    home_axis() : str
        returns message indicating which axis was homed, logs event.
    wait_move(async: bool)
        setter for the _wait_move attribute
    set_setting(setting: str, value)
        to change a specified setting to 'value' on associated device
    clear_warnings()
        returns any warnings that were cleared and logs event
    """
    class OperationSettings:
        """
        create default settings for rotary or linear devices
        """
        ROTARY = {
            'speed':6000,
            'accel':7000,
            'decel':5000,
            'current':100,
            'trigger':1,        # not used unless with direct data drive
            'datanum':0         # ^^
        }

        LINEAR = {
            'speed':2000,
            'accel':8000,
            'decel':7000,
            'current':100,
            'trigger':1,        # not used unless with direct data drive
            'datanum':0         # ^^
        }

    _WD = 470
    _ZPOS = 0
    _YPOS = 0
    _YANG = 0
    _XANG = 0
    _TargetTilt = 0

    # initialization function
    def __init__(self, comport, slave_addr:int, units:Units, operation_setting, wait_move:bool, scanner_tilt_deg:float):
        """
        Parameters
        ----------
        device : serial base
            the device obtained from SerialCom.detect_devices()
        WD : float, optional
            default is 470. the working distance of the scanner.
        csv_log : boolean
            defaults to False. Turn on to save a list of temp/position data for each axis. Remember to call export_csv_log() or data is lost!
        """
        self.serial_com = super(BaseAxis, self).__init__(comport, slave_addr, units, operation_setting, True)
        self._WD = BaseAxis._WD
        self._device = comport
        self.units = units
        self._type = None
        self._bounds = (None, None)
        self.label = 'None'
        self._home = BaseAxis._get_home(self.label, scanner_tilt_deg, slave_addr)
        self._settings = {None:None}
        self._csv_logging = False
        self.temp_log = {} # for storing time-stamped temperature data
        self.position_log = {} # for storing time-stamped position data
        if __name__=='__main__':self.__setup_LinearTest()

    def __setup_LinearTest(self):
        self.units = Units.LENGTH_MILLIMETRES
        self._type = 'lin'
        self.label = 'z_lin'
        self._bounds = (0, 550)
        self._settings = BaseAxis.OperationSettings.LINEAR

    def _clear_logs(self):
        self._temp_log = {}
        self.position_log = {}
        return True

    @property
    def csv_log(self):
        return self._csv_logging
    
    @csv_log.setter
    def csv_log(self, value:bool):
        self._csv_logging = value
        return True

    # Finds the home of an axis
    def home_axis(self):
        try:
            wait_move = self._wait_move
        except AttributeError:
            wait_move = True
        super(BaseAxis, self).home(wait_move)
        self.move_absolute(self._home, self.units, wait_move)
        home_axis = f'{self} was homed.'
        logger.info(home_axis)
        return True

    # method to get/set the units for a move position from an external file.
    def _set_units(self, key):
        if isinstance(key, str):
            key = key.lower()
            if self._type == 'lin':
                if key == 'mm' and self.units != Units.LENGTH_MILLIMETRES:
                    self.units = Units.LENGTH_MILLIMETRES
                    logger.debug(f'{self} changed units to mm.')
                    return True
            if self._type == 'rot':
                if key == 'deg' and self.units != Units.ANGLE_DEGREES:
                    self.units = Units.ANGLE_DEGREES
                    logger.debug(f'{self} changed units to deg.')
                    return True
                if key == 'rad' and self.units != Units.ANGLE_RADIANS:
                    self.units = Units.ANGLE_RADIANS
                    logger.debug(f'{self} changed units to rad.')
                    return True
        if isinstance(key, Units) and self.units != key:
            self.units = key
            return True
        return False
    
    def _monitor(self):
        """
        continuous monitoring of axis position and torque
        output to avoid collisions. Port will be closed upon detection
        of possible problems.
        """
        if not self._in_bounds(self.get_position(self.units), self.units):
            raise Exception("Out of bounds motion detected!")
        if not self.torque_monitor() <= 10:
            raise Exception("Excessive torque output detected!")
        return True

    # checks to see if desired move value is within limits
    # these values are calculated based on solidworks assm.

    # when z_lin at max position of 550 mm:
    #   max y rotation to +/- 51 deg to avoid collisions

    # when z_lin is less than position 390 mm:
    #   y free to rotate with no chance of collision

    # when moving z, check current y rotation to determine allowable z-values
    def _in_bounds(self, value: float, units: Units):
        if self._type == 'rot':
            if self.label == 'target_tilt': return True
            if units == Units.ANGLE_DEGREES:
                value = math.radians(value)
            if BaseAxis._ZPOS > 450:
                dist = 610 - BaseAxis._ZPOS
                limit = math.atan(dist / 160)
                if value > -limit and value < limit:
                    return True
                else:
                    logger.warning(f'{self} triggered bounds warning!')
                    return False
            else:
                return True
        elif self._type == 'lin':
            if abs(BaseAxis._YANG) > math.radians(50):
                if value > 450:
                    dist = 610 - value
                    limit = math.atan(dist / 160)
                    if BaseAxis._YANG > -limit and BaseAxis._YANG < limit:
                        return True
                    else:
                        logger.warning(f'{self} triggered bounds warning!')
                        return False
        if value > self._bounds[0] and value < self._bounds[1]: # for no type generic axis class
            return True
        else:
            logger.warning(f'{self} triggered bounds warning!')
            return False

    # current setting for axis 'self.' returns True if
    # asynchronous axis movements, and false if moving
    # synchronously
    @property
    def wait_move(self):
        return self._wait_move

    # set wait_move var on an axis
    @wait_move.setter
    def wait_move(self, value: bool):
        self._wait_move = value
        logger.debug(f'{self} set wait move to {value}')
        return None

    # check working distance
    @property
    def WD(self):
        return BaseAxis._WD

    # set working distance
    @WD.setter
    def WD(self, value: float):
        BaseAxis._WD = value
        try:
            BaseAxis._WD = value
            WD = f'Working Distance set to {value}'
            logger.info(WD)
        except BaseException:
            WD = 'ScanPlatform failed to set WD. Verify settings are correct.'
            logger.warning(WD)
        return WD

    # check axis current position in current units
    @property
    def position(self):
        pos = self.get_position(self.units)
        if self.label == 'x_rot':
            BaseAxis._XANG = pos
        if self.label == 'y_rot':
            BaseAxis._YANG = pos
        if self.label == 'y_lin':
            BaseAxis._YPOS = pos
        if self.label == 'z_lin':
            BaseAxis._ZPOS = pos
        if self.label == 'target_tilt':
            if self.units is Units.ANGLE_RADIANS:
                pos = self.get_position(10) * 0.017453292519943295
            BaseAxis._TargetTilt = pos
        message = (f'{self} position query:' + '\n\t\t\t\t' +
                   f'position: {pos}')
        logger.debug(message)
        if self.csv_log: self.position_log[dt.now().strftime('%y-%m-%d_%H:%M:%S')] = pos
        return pos

    # call whenever you want to log current temperature of associated device
    def _log_temp(self):
        m = f'{self} temperature log---' + '\n\t\t\t\t\t'
        temps = {}
        try:
            t = self.motor_temperature()
            temps['MotorTempDegC'] = t
            m += f'Motor: {t}' + '\n\t\t\t\t\t'
            t = self.driver_temperature()
            temps['DriverTempDegC'] = t
            m += f'Driver: {t}' + '\n\t\t\t\t\t'
        except:
            pass
        if self.csv_log: self._all_temps[dt.now().strftime('%y-%m-%d_%H:%M:%S')] = temps
        logger.info(m)
        return temps

    # creates the dict if it doesn't exist already
    @property
    def _all_temps(self):
        try:
            return self._temp_log
        except AttributeError:
            return {}

    # return axis label from serial number for identifying
    # all connected devices, regardless of the order
    # in which they're daisy-chained together.
    @staticmethod
    def _get_label(serial_num: int):
        serial_num2axis = {
            'z_lin':[61425, 00000, 1],
            'y_rot':[61436, 22233, 2]}
        for lbl in serial_num2axis:
            if serial_num in serial_num2axis[lbl]:
                get_label = lbl
                break
        return get_label

    # get home position of an axis given its label. define home here
    # these vals used for offsets / lookup values in move functions.
    # if scanner_tilt_deg is provided this will give same home as Markus in David6
    @staticmethod
    def _get_home(axis_label: str, scanner_tilt_deg=None, target_tilt=None, slave_addr=None):
        if axis_label is None and slave_addr is not None: axis_label = {1:'z_lin',2:'y_rot',3:'target_tilt'}[slave_addr]
        positions = {
            'target_tilt':target_tilt+math.radians(scanner_tilt_deg)
        }        
        return positions.get(axis_label, "Invalid Label")

    # get settings from connected devices using string arguments
    # to return a specific setting like driver temp use the form:
    #       self.settings['device']['driver.temperature']
    @property
    def settings(self):
        return self._settings

    # for changing a device setting during a test.
    def set_setting(self, setting: str, value:int):
        try:
            self._settings[setting] = value
            response = f'{self} {setting} set to {value}'
            logger.debug(response)
        except:
            response = f'failed to set {setting} to {value} on {self}'
            logger.warning(response)
        return response

    # for checking flags on a connected device
    @property
    def warnings(self):
        if self.com_device.GetAlarm(self.address):
            warn = f'{self} no flags'
            logger.debug(warn)
        else:
            warn = self.com_device.GetAlarm(self.address)
            logger.warning(warn)
        return warn

    # the preferred method of clearing flags on a device. returns flags that
    # were cleared
    def clear_warnings(self):
        flags = self.warnings
        self.com_device.AlarmReset(self.address)
        message = f'{self} cleared the following flags: {flags}'
        logger.info(message)
        return flags

    # axis string representation
    def __str__(self):
        return f'Axis: {self.label}'
