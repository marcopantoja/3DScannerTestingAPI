import logging
import math

from zaber_motion import Units

from .base_axis import BaseAxis

logger = logging.getLogger(__name__)


class RotaryAxis(BaseAxis):

    # initialization function
    def __init__(self, device, label, bounds, interface_id, WD, target_tilt_deg):
        super(RotaryAxis, self).__init__(device, WD, target_tilt_deg)
        self._WD = BaseAxis._WD
        self.units = Units.ANGLE_RADIANS
        self._device = device
        self._axis = device.get_axis(1)
        self._axis_number = self._axis.axis_number
        self._interface_id = interface_id
        self.label = label
        self._type = 'rot'
        self._home = BaseAxis._get_home(self.label, math.degrees(BaseAxis._XANG), target_tilt_deg)
        self._bounds = bounds
        self._wait_move = True
        self._settings = {}
        if self.label == 'x_rot':
            self._direction = 1
        elif self.label == 'y_rot':
            self._direction = -1
        return None

    # move method specific to rotational axes. position is checked
    # to ensure within bounds prior to calling move.
    def move(self, position: float):
        units = self.units
        wait_move = self._wait_move
        if self._in_bounds(position, units):
            if units == Units.ANGLE_DEGREES:
                position = math.radians(position)
            units = Units.ANGLE_RADIANS
            position += self._home
            position *= self._direction
            super(RotaryAxis, self).move_absolute(position, units, wait_move)
            if self.label == 'y_rot':
                BaseAxis._YANG = self.position
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
        units = Units.ANGLE_RADIANS
        pos = float(math.radians(position))
        if self._in_bounds(pos, units):
            self.move(pos)
            move_degrees = f'{self} moved to {self.position}'
            logger.info(move_degrees)
        else:
            move_degrees = f'Failed moving {self} to {position}. Check bounds'
            logger.warning(move_degrees)
        self._log_temp()
        return move_degrees
