import logging
import math
import os

from zaber_motion import Units
from zaber_motion.ascii import Axis, Connection, Device

from ..py_drive_api import logs_dir
from .ref_variables import RefVariables

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


class BaseAxis(Connection, Device, Axis):
    """
    Base class of LinearAxis and RotaryAxis.

    Attributes
    ----------
    WD : float
        the current projector working distance
    _device : zaber_motion.ascii.Device
        the associated 'device' object
    _axis : zaber_motion.ascii.Axis
        the associated 'axis' object
    sn : int
        the device's serial number
    label : str
        readable label to id axes
    _home : float
        position where homing command will finally send axis
    _wait_move : bool
        determine if axis moves happen async
    settings : dict
        all available settings and thier reported values
    units : zaber_motion.Units
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

    _WD = 470
    _TARGET_TILT = 0
    _ZPOS = 200
    _YPOS = 375
    _YANG = 0
    _XANG = 0

    # initialization function
    def __init__(self, device, WD:float, target_tilt_deg):
        """
        Parameters
        ----------
        device : zaber_motion.ascii.Device
            the device obtained from Connection.get_devices()
        WD : float, optional
            default is 470. the working distance of the scanner.
        tilt: float, optional
            default is 0 degrees.
        """
        BaseAxis._TARGET_TILT = math.radians(target_tilt_deg)
        BaseAxis._WD = WD
        self._WD = BaseAxis._WD
        self._device = device
        self._axis = device.get_axis(1)
        self.label = BaseAxis._get_label(device.name)
        self._home = BaseAxis._get_home(self.label,math.degrees(BaseAxis._XANG),target_tilt_deg)
        self._wait_move = True
        self._settings = {}
        if self.label[-3:] == 'lin':
            self.units = Units.LENGTH_MILLIMETRES
            self._bounds = (-375, 375)
            self._type = 'lin'
        else:
            self.units = Units.ANGLE_RADIANS
            self._bounds = (-2 * math.pi, 2 * math.pi)
            self._type = 'rot'
        return None

    # Finds the home of an axis
    def home_axis(self):
        try:
            wait_move = self._wait_move
        except AttributeError:
            wait_move = True
        super(BaseAxis, self).home(wait_move)
        speed = self._device.settings.get('maxspeed')
        self._device.settings.set('maxspeed', speed * 1.2)
        super(BaseAxis, self).move_absolute(
            self._home, self.units, wait_move)
        home_axis = f'{self} was homed.'
        logger.info(home_axis)
        self._device.settings.set('maxspeed', speed)
        return home_axis

    # method to get/set the units for a move position from an external file.
    def _set_units(self, key):
        if isinstance(key, str):
            key = key.lower()
            if self._type == 'lin':
                if key.find('mm') >= 0:
                    self.units = Units.LENGTH_MILLIMETRES
                    logger.debug(f'{self} changed units to mm.')
            if self._type == 'rot':
                if key.find('deg') >= 0:
                    self.units = Units.ANGLE_DEGREES
                    logger.debug(f'{self} changed units to deg.')
                if key.find('rad') >= 0:
                    self.units = Units.ANGLE_RADIANS
                    logger.debug(f'{self} changed units to rad.')
        if isinstance(key, Units):
            self.units = key
        else:
            self.units = self.units
        return self.units

    # returns the serial number of a Device object
    @staticmethod
    def __get_sn(device):
        sn = device.serial_number
        return sn

    # checks to see if desired move value is witin limits
    # these values are calculated based on solidworks assm.
    def _in_bounds(self, value: float, units: Units):
        checked = False
        if self._type == 'rot':
            if units == Units.ANGLE_DEGREES:
                value = math.radians(value)
            if self.label == 'y_rot' and BaseAxis._ZPOS > 240:
                dist = 590 - BaseAxis._ZPOS
                limit = math.atan(dist / 150)
                if value > -limit and value < limit:
                    _in_bounds = True
                    checked = True
                elif BaseAxis._YPOS < 200 or BaseAxis._YPOS > 420:
                    _in_bounds=True
                    checked=True
                else:
                    _in_bounds = False
                    checked = True
                    logger.warning(f'{self} triggered bounds warning!')
            elif self.label == 'x_rot' and BaseAxis._YPOS > 725:
                dist = 811 - BaseAxis._YPOS
                limit = math.atan(dist / 115)
                if value > -limit and value < limit:
                    _in_bounds = True
                    checked = True
                else:
                    _in_bounds = False
                    checked = True
                    logger.warning(f'{self} triggered bounds warning!')
        elif self._type == 'lin':
            if self.label == 'y_lin' and value > 725:
                dist = 811 - value
                limit = math.atan(dist / 115)
                if BaseAxis._XANG > -limit and BaseAxis._XANG < limit:
                    _in_bounds = True
                    checked = True
                else:
                    _in_bounds = False
                    checked = True
                    logger.warning(f'{self} triggered bounds warning!')
            elif self.label == 'z_lin' and value > 240:
                dist = 590 - value
                limit = math.atan(dist / 150)
                if BaseAxis._YANG > -limit and BaseAxis._XANG < limit:
                    _in_bounds = True
                    checked = True
                else:
                    _in_bounds = False
                    checked = True
                    logger.warning(f'{self} triggered bounds warning!')
        if not checked:
            if value > self._bounds[0] and value < self._bounds[1]:
                _in_bounds = True
                checked = True
            else:
                _in_bounds = False
                logger.warning(f'{self} triggered bounds warning!')
        return _in_bounds

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
            WD = 'MotionAxis failed to set WD. Verify settings are correct.'
            logger.warning(WD)
        return WD

    # check axis current position in current units
    @property
    def position(self):
        pos = self.get_position(self.units)
        message = (f'{self} position query:' + '\n\t\t\t\t' +
                   f'position: {pos}')
        logger.debug(message)
        if self.label == 'x_rot':
            BaseAxis._XANG = pos
        if self.label == 'y_rot':
            BaseAxis._YANG = pos
        if self.label == 'y_lin':
            BaseAxis._YPOS = pos
        if self.label == 'z_lin':
            BaseAxis._ZPOS = pos
        return pos

    # call whenever you want to log current temperature of associated device
    def _log_temp(self):
        temps = [
            'driver.temperature',
            'system.temperature'
        ]
        try:
            m = f'{self} temperature log---' + '\n\t\t\t\t\t'
            for s in temps:
                m = m + f'{s}: {self._device.settings.get(s)}' + '\n\t\t\t\t\t'
        except BaseException:
            pass
        logger.info(m)
        return None

    # return axis label from id for identifying
    # all connected devices, regardless of the order
    # in which they're daisy-chained together.
    @staticmethod
    def _get_label(axis_id):
        if type(axis_id) is int:
            axis_label = {
                3: 'target_tilt'}
        elif type(axis_id) is str:
            axis_label = {
                'X-LRT0500AL-E08C':'z_lin',
                'X-RST120AK-E03':'y_rot',
                'X-LRT0750AL-E08C':'y_lin',
                'X-RSW60A-E03':'x_rot'
            }
        get_label = axis_label.get(axis_id, "Invalid ID")
        return get_label

    # get home position of an axis given its label. define home here
    # these vals used for offsets / lookup values in move functions.
    @staticmethod
    def _get_home(axis_label: str, scanner_tilt_deg=None, target_tilt_deg=None):
        """
        pass target manual tilt position, to get correct approximate
        home positions. 
        tilt is in degrees!
        """
        WD = BaseAxis._WD
        target_tilt = math.radians(target_tilt_deg)
        scanner_tilt = math.radians(scanner_tilt_deg)
        positions = {
            'target_tilt': target_tilt+scanner_tilt,
            'y_lin': 355.1 + WD * math.sin(scanner_tilt),
            'z_lin': 286.511 + WD - (WD * math.cos(scanner_tilt)),
            'x_rot': scanner_tilt-0.04345051714379008,
            'y_rot': 0}
        _get_home = positions.get(axis_label, "Invalid Label")
        return _get_home

    def driver_temperature(self):
        """
        returns the current temperature of device driver in deg-C.
        if it's available
        """
        try:
            temp = self._device.settings.get('driver.temperature')
            self._settings['driver.temperature']=temp
            return temp
        except:
            return None

    def motor_temperature(self):
        """
        returns the current temperature of motor in deg-C.
        if available on device
        """
        try:
            temp = self._device.settings.get('system.temperature')
            self._settings['system.temperature'] = temp
            return temp
        except:
            return None

    # get settings from connected devices using string arguments
    # to return a specific setting like driver temp use the form:
    #       self.settings['device']['driver.temperature']
    @property
    def settings(self):
        if self._settings=={}:
            arg = []
            val = []
            for a in RefVariables.DEV_ARGS:
                try:
                    val.append(self._device.settings.get(a))
                    arg.append(a)
                except BaseException:
                    f'{a} is invalid for this device.'
            self._settings = dict(zip(arg,val))
        else:
            for a in RefVariables.NON_PERSISTENT:
                try:
                    self._settings[a] = self._device.settings.get(a)
                except BaseException:
                    pass
        return self._settings

    # for changing a device setting during a test. settings not saved after
    # powerdown i.e. disconnecting AC power from wall outlet
    def set_setting(self, setting: str, value):
        try:
            self._device.settings.set(setting, value)
            try:
                value = self._device.settings.get(setting)
                self._settings[setting] = value
            except BaseException:
                value = 'SettingError_Not_Set'
            response = f'{self} {setting} set to {value}'
            logger.debug(response)
        except BaseException:
            response = f'{setting} is invalid for {self}!...not set to {value}'
            logger.warning(response)
        return response

    @property
    def target_tilt(self):
        """
        returns current target tilt level in degrees.
        """
        return math.degrees(BaseAxis._TARGET_TILT)

    @target_tilt.setter
    def target_tilt(self, tilt_level):
        """
        set the tilt in degrees for manual target.
        """
        BaseAxis._TARGET_TILT = math.radians(tilt_level)

    # for checking flags on a connected device
    @property
    def warnings(self):
        if self._device.warnings.get_flags() == set():
            warn = f'{self} no flags'
            logger.debug(warn)
        else:
            warn = self._device.warnings.get_flags()
            logger.warning(warn)
        return warn

    # the preferred method of clearing flags on a device. returns flags that
    # were cleared
    def clear_warnings(self):
        flags = self.warnings
        self._device.warnings.clear_flags()
        message = f'{self} cleared the following flags: {flags}'
        logger.info(message)
        return flags

    # axis string representation
    def __str__(self):
        return f'Axis: {self.label}'
