import logging

from zaber_motion import Units
from math import degrees

from .base_axis import BaseAxis

logger = logging.getLogger(__name__)


class LinearAxis(BaseAxis):
    """
    This class is for controlling linear zaber-motion actuators.

    Attributes
    ----------
    units : zaber_motion.Units
        default is mm.
    WD : float
        the current working distance
    label : str
        the string identifier given to each axis
    sn : int
        the serial number of this device
    wait_move : bool
        default = True. all movements async
    settings : dict
        all available settings of this device
    position : float
        returns and logs the current position of this axis

    Methods
    -------
    move(position: float)
        move to the specified position in the current device units
    home_axis()
        returns this axis to its self.home location. see base class.
    """

    # initialization function
    def __init__(self, device, label: str,
                 bounds: tuple, interface_id, WD: float, target_tilt_deg):
        """
        Parameters
        ----------
        device : zaber_motion.ascii.Device
            the device obtained from Connection.get_devices()
        label : str
            the device's identifying string. ('y_lin'/'z_lin')
        bounds : tuple
            the lower and upper limits of this axis for
            collision avoidance.
        interface_id : zaber_motion.ascii.Connection
            the connection.interface_id
        WD : float
            the working distance of the scanner.
        """

        super(LinearAxis, self).__init__(device, WD, target_tilt_deg)
        self.units = Units.LENGTH_MILLIMETRES
        self._WD = BaseAxis._WD
        self._device = device
        self._axis = device.get_axis(1)
        self._axis_number = self._axis.axis_number
        self._interface_id = interface_id
        self.label = label
        self._type = 'lin'
        self._home = BaseAxis._get_home(self.label, degrees(BaseAxis._XANG), target_tilt_deg)
        self._bounds = bounds
        self._wait_move = True
        self._settings = {}
        return None

    # move method specific to linear axes with default units and
    # check bounds implemented before calling move. note that
    # the current position of any axis is stored after move.
    def move(self, position):
        units = self.units
        wait_move = self._wait_move
        position = float(position)
        if position < 0:
            position = self._home - abs(position)
        elif position > 0:
            position = self._home + position
        else:
            position = self._home
        if self._in_bounds(position, units):
            self.move_absolute(position, units, wait_move)
            pos = self.position
            move = f'{self} moved to {pos}'
            logging.info(move)
        else:
            move = f'Failed moving {self} to {position}. Check bounds'
            logger.warning(move)
        self._log_temp()
        return move
