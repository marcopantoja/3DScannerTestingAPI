import logging
import math

from ..oriental_motor.base_axis import BaseAxis
from ..oriental_motor.units import Units

logger = logging.getLogger(__name__)


class RotaryAxis(BaseAxis):

    # initialization function
    def __init__(self, device, WD:float, scanner_tilt_deg:float, target_tilt:float):
        """
        Parameters
        ----------
        device : serial base
            the device obtained from SerialCom.detect_devices()
        
        WD : float
            the working distance of the scanner.
        
        Methods
        ----------
        move( pos) : 
            move axis to given position in current device units.
        move_degrees( pos) :
            move axis to given position after converting to radians
        """
        operation_setting = BaseAxis.OperationSettings.ROTARY
        self._axis = super(RotaryAxis, self).__init__(device, 3, Units.ANGLE_RADIANS, operation_setting, True, scanner_tilt_deg)
        self._WD = BaseAxis._WD
        self.units = Units.ANGLE_RADIANS
        self._device = device
        self.label = 'target_tilt'
        self._type = 'rot'
        self._home = BaseAxis._get_home(self.label, scanner_tilt_deg, target_tilt)
        self._bounds = (-2*math.pi, 2*math.pi)
        self._settings = operation_setting
        self._csv_logging = False

    def home_axis(self):
        self.move(self._home)
        logger.info(f'{self} is at home')
        return True

    # move method specific to rotational axes. position is checked
    # to ensure within bounds prior to calling move.
    def move(self, position: float):
        """
        Moves rotary axis to 'position' in current units setting.
        """
        units = self.units
        wait_move = self._wait_move
        if self._in_bounds(position, units):
            super(RotaryAxis, self).move_absolute(position, units, wait_move) # flip sign of position to ensure that rotation is CCW for positive!
            if self.label == 'target_tilt':
                BaseAxis._TargetTilt = self.position
            if self.label == 'x_rot':
                BaseAxis._XANG = self.position
            move = f'{self} moved to {self.position}'
            logger.info(move)
        else:
            move = f'Failed moving {self} to {position} due to possible collision'
            logger.warning(move)
        self._log_temp()
        return move

    # method for moving in degrees instead of default radians. this is
    # for simplicity during debugging. convert to radians and use move() method
    # for scripting. avoid this method if possible.
    def move_degrees(self, position: float):
        """
        Move to 'position' in degrees.
        """
        move_degrees = f'{self} moved to {self.position}'
        if self.units is Units.ANGLE_RADIANS:
            pos = float(math.radians(position))
            self.move(pos)
            logger.info(move_degrees)
        elif self.units is Units.ANGLE_DEGREES:
            self.move(position)
        else:
            move_degrees = f'Failed moving {self} to {position}.'
            logger.warning(move_degrees)
        self._log_temp()
        return move_degrees
