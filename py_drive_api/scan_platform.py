import json
import logging
import math
import sys
import os
from xml.etree.ElementTree import ElementTree as ET

from zaber_motion import MotionLibException, Units
if __name__=='__main__':__package__='py_drive_api'
from .ui_scripting import UI_Scripting as ui

from .base_axis import BaseAxis
from .linear_axis import LinearAxis
from .poses import Poses
from .rotary_axis import RotaryAxis

logger = logging.getLogger(__name__)

# Class for controlling the MotionAxis devices and for easy setup. use the default
# constructor for this class, and you'll have an object with the available
# 'axes' as attributes. this scan_platform object can be used to control and move everything
# during scripting. use this class for automation.


class ScanPlatform(LinearAxis, RotaryAxis):
    """
    The ScanPlatform class provides a simple way to interface with
    the zaber-motion devices.

    Attributes
    ----------
    WD : float
        a variable to store the current scanner working distance
    device_list : Device
        the zaber-motion Device objects associated with each axis
    xrot : RotaryAxis
        the projector tilt actuator, if connected
    yrot : RotaryAxis
        the turntable actuator, if connected
    ylin : LinearAxis
        the projector height, if connected
    zlin : LinearAxis
        the linear stage actuator, if connected
    axes : dict
        {'axis.label': BaseAxis} for accessing axes from list commands
    settings : dict
        all of the available settings for all available devices
    position : dict
        the current position of all connected devices
    warnings : list
        tuples of any active warnings or flags on connected devices

    Methods
    -------
    home_all()
        for homing all connected axes to their self.home location
    move(axes_positions: dict)
        for moving all axes with one command. dict keys must match
        self.axes.keys() for move to occur.
    turn_around() : None
        preferred method to rotate for scanning ballplate / target.
        for collision avoidance and extreme precaution!
    end() : None
        call at the end of a script for returning actuators
        to positions 'ready to home' at next startup.
    clear_warnings() : tuple
        call to reset warnings on all connected devices at once.
        returns any faults that were cleared.
    set_setting(setting: str, value: float) :
        for changing the settings on connected devices all at once.

    """
    ######################### CLASS MANAGED VARIABLES #########################
    DEFAULT_WORK_DISTANCE = 470 # millimeters
    DEFAULT_TARGET_TILT = -15 # degrees about WX
    DEFAULT_SCANNER_TILT = 0 # degrees about WX

    ################## SPECIAL AND PRIVATE NAMESPACE METHODS ##################
    # method for fine adjustments to position devices in their intended locations.
    # must be positioned close to target position for this to work.
    # iterative process to align calibration target to the intended working distance.
    def __alignScanner(self, attack_angle):
        WD = self.WD
        tilt = self._target_tilt
        print(f'Tilt {math.degrees(tilt)}', f'attack: {math.degrees(attack_angle)}')
        proj_pose = BaseAxis.__readSetup()
        proj_target = {# Based on hardware setup <n o a p> vectors
            'nx':1,  'ny':0,                       'nz':0,
            # 'ox':0,  'oy':-math.cos(attack_angle), 'oz':math.sin(attack_angle),
            # 'ax':0,  'ay':math.sin(attack_angle),  'az':-math.cos(attack_angle),
            'px':0,  'py':-WD * math.sin(attack_angle),     'pz':abs(WD*math.cos(attack_angle))
        }
        proj_pose['ry'] = math.radians(proj_pose['ry'])
        proj_pose['rx'] = math.radians(proj_pose['rx'])
        print("Projector Pose----")
        for p in proj_pose:
            print(f'{p}:  {proj_pose[p]}')
        print("Target Pose-----")
        for p in proj_target:
            print(f'{p}:  {proj_target[p]}')
        for o in self._objects:
            if o.label == 'z_lin':
                adjust = proj_pose['pz'] - proj_target['pz']
                o._home += adjust
            elif o.label == 'y_lin':
                adjust = proj_pose['py'] - proj_target['py']
                o._home += adjust
            elif o.label == 'y_rot':
                adjust = proj_target['ry'] - proj_pose['ry']
                o._home += adjust
            elif o.label == 'x_rot':
                pass
        self.move_attack_angle(attack_angle, 'rad')
        return None
        
    # method to make ScanPlatform object subscriptable for simplified looping process, and
    # for simplified calling associated axes objects
    def __getitem__(self, x):
        item = self.axes[x]
        return item

    # method to make ScanPlatform object iterable for simplified looping through connected
    # axes. iterable is a dictionary with axis.label as keys and axis objects
    # as values.
    def __iter__(self):
        return self.axes.__iter__()

    # initialization of scanplatform object with connected axes, automatically homes
    # the connected devices at startup.
    def __init__(self, connection, scanner_tilt_deg=DEFAULT_SCANNER_TILT, target_tilt_deg=DEFAULT_TARGET_TILT, WD=DEFAULT_WORK_DISTANCE, OMTiltAxisSerialDevice=None):
        """
        Parameters
        ----------
        connection : zaber_motion.ascii.Connection
            the connection variable used to open com port
        WD : float, optional
            defaults to 470, sets the current working distance.
        """
        target_tilt = math.radians(target_tilt_deg)
        self._target_tilt = target_tilt
        BaseAxis._TARGET_TILT = target_tilt
        BaseAxis._WD = WD
        BaseAxis._XANG = math.radians(scanner_tilt_deg)
        self._WD = BaseAxis._WD
        m = 'Looking for devices...'
        print(m)
        logger.debug(m)
        self.device_list = connection.detect_devices()
        self._interface_id = connection.interface_id
        m = f'Found {len(self.device_list)} devices:\n'
        _axis_list = []
        label_list = []
        self._wait_move = True
        self._objects = []
        if OMTiltAxisSerialDevice is not None:
            self.tilt_axis = OMTiltAxisSerialDevice
            label_list.append(self.tilt_axis.label)
            _axis_list.append(self.tilt_axis)
            self._objects.append(self.tilt_axis)
            m += f'Found Oriental Motor Tilt Axis!\n\n'
        print(m)
        logger.debug(m)
        for device in self.device_list:
            name = device.name
            lab = BaseAxis._get_label(name)
            label_list.append(lab)
            if lab is 'y_lin':
                bounds = (0, 750)
                self.yaxis = LinearAxis(
                    device, lab, bounds, self._interface_id, self._WD, target_tilt_deg)
                _axis_list.append(self.yaxis)
                self._objects.append(self.yaxis)
                self.yaxis.set_setting('maxspeed', 200000)
                self.yaxis.set_setting('accel',200)
            elif lab is 'z_lin':
                bounds = (0, 500)
                self.zaxis = LinearAxis(
                    device, lab, bounds, self._interface_id, self._WD, target_tilt_deg)
                _axis_list.append(self.zaxis)
                self._objects.append(self.zaxis)
                self.zaxis.set_setting('maxspeed', 200000) # slower setting here to reduce 
                self.zaxis.set_setting('accel',75)
            elif lab is 'x_rot':
                bounds = (-1.3264502315156905, 0.8028514559173916)
                self.xrot = RotaryAxis(
                    device, lab, bounds, self._interface_id, self._WD, target_tilt_deg)
                _axis_list.append(self.xrot)
                self._objects.append(self.xrot)
                self.xrot.set_setting('maxspeed', 25000)
                self.xrot.set_setting('accel',200)
            elif lab is 'y_rot':
                bounds = (-2 * math.pi, 2 * math.pi)
                self.yrot = RotaryAxis(
                    device, lab, bounds, self._interface_id, self._WD, target_tilt_deg)
                _axis_list.append(self.yrot)
                self._objects.append(self.yrot)
                self.yrot.set_setting('accel',80)
        self.axes = dict(zip(label_list, _axis_list))
        try:
            pass
            # self.home_all()
        except MotionLibException as error:
            print(error)
        self._settings = {}

    #  method for obtaining the position of the linear actuators, to satisfy
    # a given angle of attack w.r.t. the horizontal. use home variables instead of
    # hard coding values, so that alignSequence() can adjust to adequate values.
    def __kinematics(self, attack_angle, angle_units):
        attack_angle = float(attack_angle)
        if angle_units == Units.ANGLE_DEGREES:
            attack_angle = math.radians(attack_angle)
        elif angle_units == 'deg':
            attack_angle = math.radians(attack_angle)
        work_distance = self.WD
        X = self.zaxis._home + (609.73 - (work_distance * math.cos(attack_angle) +
                                          110 * math.cos(attack_angle - 0.070628)))
        if attack_angle > 0:
            Y = self.yaxis._home + (work_distance * math.sin(attack_angle) +
                                    110 * math.sin(attack_angle - 0.070628) + 7.75)
        elif attack_angle < 0:
            Y = self.yaxis._home - (work_distance * math.sin(abs(attack_angle)) +
                                    110 * math.sin(abs(attack_angle) + 0.070628) - 7.75)
        else:
            Y = self.yaxis._home
        return (X, Y)

    @staticmethod
    def __readSetup():
        from xml.etree import ElementTree as ET
        ScanFol = os.path.join(os.getenv("LOCALAPPDATA"), 'SCAN6/Logs')
        hwSetup = os.path.join(ScanFol, 'calibration.log')
        hwSetup = ET.parse(hwSetup).getroot()
        proj_pose = hwSetup.findall('calibrationInfo/projectorModel/pose/')
        p = {}
        for c in proj_pose:
            for a in c.attrib:
                p[f'{c.tag[0]}{a[-1]}'] = float(c.attrib[a])
        return p

    # method to represent scanplatform as string object.
    def __str__(self):
        description = str(['ScanPlatform Device: ' +
                       f'{len(self.device_list)} devices connected.'])
        return (description)

    ###################### CLASS STATIC METHODS ######################
    @staticmethod
    def pose2AD(L, R):
        D = 12
        WD = float(BaseAxis._WD)
        angle = math.atan((R - L) / D)
        if L == R:
            distance = WD + R * 10
        else:
            mid = (L + R) / 2
            distance = WD + mid * 10
        print(f'angle: {angle}, distance: {distance}')
        return (angle, distance)

    ####################### CLASS BOUND METHODS #######################
    def move2pose(self, LR):
        (angle, distance) = self.pose2AD(LR[0], LR[1])
        WD = self.zaxis.WD
        print(f'Distance: {distance}')
        if distance == WD:
            distance = 0
        else:
            distance = WD - distance
        self.yrot.move( angle-self.yrot._home)
        self.zaxis.move( distance)
        if self.wait_move:
            for o in self._objects:
                o.wait_until_idle()
        return f'Moved to pose {LR}'

    # preferred method for homing all axes connected to scanplatform object
    def home_all(self):
        for a in self.axes:
            print(f'homing axis {a}.')
            self.axes[a].home_axis()
        home_all = 'All axes homed.'
        logger.info('\t\t\t' + home_all)
        return home_all

    # preferred method for satisfying a given attack angle
    def move_attack_angle(self, attack_angle: float, units, tilt=None):
        """
        you can provide a tilt value in degrees if changing to a new 
        'world tilt' setting. this will update all of the axes home
        positions for accurate positions, with relative angle refs. 
        """
        if tilt is not None:
            self.target_tilt = tilt
        else:
            tilt = BaseAxis._TARGET_TILT
        X, Y = self.__kinematics(attack_angle, units)
        logger.debug(f'(X,Y) = { (X, Y)}')
        if units == 'deg':
            if self.xrot.units == Units.ANGLE_DEGREES:
                xhome = self.xrot._home
            else:
                xhome = math.degrees(self.xrot._home)
            tilt = math.degrees(tilt)
        elif units == 'rad':
            if self.xrot.units == Units.ANGLE_RADIANS:
                xhome = math.radians(self.xrot._home)
            else:
                xhome = self.xrot._home
            tilt = math.radians(tilt)
        moves = {
            'z_lin': X - self.zaxis._home,
            'x_rot': attack_angle - xhome,
            'y_lin': Y - self.yaxis._home
            }
        if units == 'deg': moves['x_rot'] = math.radians(moves['x_rot'])
        for axis_key in moves:
            logger.debug('attempting move')
            position = moves[axis_key]
            self.axes[axis_key].move(position)
        if units == Units.ANGLE_RADIANS:
            uni = 'rad'
        else:
            uni = 'deg'
        move_attack_angle = f'Successfully moved to ({X}, {Y}) at {attack_angle} {uni}'
        logger.info(move_attack_angle)
        if self.wait_move:
            for o in self._objects:
                o.wait_until_idle()
        return move_attack_angle

    # preferred method for moving the scanplatform axes to satisfy the poses
    # imported from external files. axes positions are given in a dictinary
    # containing the 'key' specifying the type of move or axis to be moved,
    # and the value the axis is to be moved to. this method will call the move()
    # method for the individual axes that must be moved.
    def move(self, axes_positions: dict, relative_positions=False):
        axes = self.axes.keys()
        kin_move = ['attack', 'attack_angle', 'angle', 'anglerad',
                    'attackdeg', 'rad', 'deg']
        unit_labels = ['deg', 'rad', 'mm']
        for key in axes_positions:
            if len(key) > 0:
                logger.debug(f'Key: {key},  axes_pos: {axes_positions}')
                for unit in unit_labels:
                    if key.lower().find(unit) >= 0:
                        move_key = key.lower().replace(unit, '')
                        units = unit
                        break
                    else:
                        move_key = key.lower()
                logger.debug(f'Move Key: {move_key}')
                logger.debug(f'Key: {key}')
                if move_key in axes:
                    try:
                        units = self.axes[move_key]._set_units(key)
                        position = float(axes_positions[key])
                        if relative_positions:
                            if move_key == 'z_lin':
                                if position == BaseAxis._WD:
                                    position = 0
                                else:
                                    position = BaseAxis._WD - position
                            else:
                                position = self.axes[move_key]._home - position
                            logger.debug(
                                f'from scanplatform move>>> {key}: {axes_positions[key]}')
                            self.axes[move_key].move(position)
                        else:
                            self.axes[move_key].move(position)
                    except KeyError:
                        logger.exception(
                            f'Key Error! Check that {move_key} is connected.')
                elif move_key in kin_move:
                    try:
                        attack_angle = float(axes_positions[key])
                        if attack_angle < -38 or attack_angle > 37:
                            logger.warning(
                                f'attack angle {attack_angle} is out of bounds for this method. Valid angles from -38 --> 37 deg.')
                            continue
                        logger.debug(f'Attack angle: {attack_angle}')
                        self.move_attack_angle(attack_angle, units)
                    except UnboundLocalError:
                        try:
                            units = self.axes['x_rot'].units
                            self.move_attack_angle(attack_angle, units)
                        except BaseException:
                            message = (
                                f'Error in move to pose. Check axis key {key}.' +
                                '\n\t\t\t'
                                f'angle: {attack_angle}' +
                                '\t' +
                                f'units: {units}' +
                                '\t' +
                                f'axes positions: {axes_positions}')
                        logger.error(message)
                else:
                    logger.debug('Invalid key. Check "move" argument.')
                    logger.warning('The "move key" {key} is not valid.')
        if self.wait_move:
            for o in self._objects:
                o.wait_until_idle()
        return None

    def new_home(self):
        """
        sets current position to home for all axes
        """
        for o in self._objects:
            o._home = o.position
        
    # use this method for turning table to scan ballplate when ZPOS > 240
    def turn_around(self):
        wait_move = {o: o.wait_move for o in self._objects}
        self.wait_move = False
        try:
            current_pos = {i.label: (i.position - i._home)
                           for i in self._objects}
            self.zaxis.home()
            if self.yrot.units == Units.ANGLE_DEGREES:
                y_angle = math.radians(self.yrot.position)
            else:
                y_angle = self.yrot.position
            if y_angle < 0.5 * math.pi:
                self.yrot.move_degrees(180)
            else:
                self.yrot.move_degrees(0)
            for p in current_pos:
                if p == 'z_lin' or p == 'y_lin':
                    self.axes[p].move(current_pos[p])
        except BaseException:
            turn_around = (
                f'Error in ballplate turn.' +
                f'Failed to move {self.axes[p]} ' +
                f'to position {current_pos[p]}')
            logger.error(turn_around)
        for o in wait_move:
            o.wait_move = wait_move[o]
        return None

    # get in position to calibrate
    def calibrate_position(self, target, custom=None):
        targets = {
            'golden': {
                'y_lin': 284.21781445312484,
                'z_lin': 214.94824609374987,
                'x_rot': -0.032078606236264524,
                'y_rot': 0
            },
            'scan_platform': {
                'y_lin': 372.2570917968748,
                'z_lin': 200,
                'x_rot': 0,
                'y_rot': 0
            },
            'tiltedu': {
                'y_lin': 364.87410058593736,
                'z_lin': 245.94827441406235,
                'x_rot': 0,
                'y_rot': 0
            },
            'tiltedd': {
                'y_lin': 380.7980937499998,
                'z_lin': 245.94827441406235,
                'x_rot': 0,
                'y_rot': 0
            },
            'scan_platform-derive': {
                'y_lin': 354.07426367187486,
                'z_lin': 101.34922460937494,
                'y_rot': 0
            },
            'golden-derive': {
                'y_lin': 30.275609374999984,
                'z_lin': 101.34922460937494,
                'x_rot': -0.3905965053654622,
                'y_rot': 0
            },
            'Optimus-LP': {
                'x_rot': -0.5515254071686861,
                'y_lin': 47.00004589843748, 
                'y_rot': 0.0, 
                'z_lin': 352.91166796874984
                },
            'custom': custom
        }
        for a in targets[target]:
            self.axes[a].move_absolute(targets[target][a], self.axes[a].units)
        m = 'In position...ready to begin calibration.'
        if self.wait_move:
            for o in self._objects:
                o.wait_until_idle()
        logger.info(m)
        return m

    def wait_idle(self):
        for o in self._objects:
            o.wait_until_idle()
        return True

    # get in position to scan ballplate
    def ballplate_position(self, position='mounted', custom=None, wait=True):
        ball_plate = {
            'mounted': {
                'y_lin': 363.1311992187498,
                'z_lin': 122.24871433593742,
                'y_rot': 3.141592653589793
            },
            'unmounted': {
                'y_lin': 464.19082910156226,
                'z_lin': 134.76312304687494,
                'x_rot': -0.032078606236264524,
                'y_rot': 3.141592653589793
            },
            'tilted': { # 
                'y_lin': 364.87410058593736,
                'z_lin': 134.76312304687494,
                'x_rot': 0,
                'y_rot': 3.141592653589793
            },
            'mounted-derive': { # for mounted scan_platform target scanning derive metrology
                'y_lin': 132.20972851562493,
                'z_lin': 152.24869140624992,
                'x_rot': -0.3905965053654622,
                'y_rot': 3.141592653589793
            },
            'Optimus-LP': {
                'x_rot': -0.5515254071686861, 
                'y_lin': 47.00004589843748, 
                'y_rot': 3.141592653589793, 
                'z_lin': 235.24889648437488
            },
            'custom': custom
        }
        for o in self._objects:
            try:
                o.move_absolute(ball_plate[position][o.label], o.units, o.wait_move)
            except KeyError:
                continue
        m = 'Ready to scan ballplate'
        if self.wait_move or wait:
            for o in self._objects:
                o.wait_until_idle()
        return m

    def calibrate(self, calib_paths, target='scan_platform', x_rot=0):
        if calib_paths is not list:
            [calib_paths]
        self.xrot.move_degrees(x_rot)
        self.calibrate_position(target)
        for path in calib_paths:
            for p in Poses.GOLDEN:
                self.move2pose(p)
                logger.info(f"this is pose {p}, capturing views.")
                ret = ui.addCalibrationView()
                logger.debug(f'addCalibrationView>>>  {ret}')
                while ret is False:
                    ret = ui.addCalibrationView()
                    m = (
                        'Failed to add calibration view!' +
                        f'Pose: {p}'
                        f'Path: {path}'
                    )
                    logger.warning(m)
            ui.calibrate(path)
            logger.info('Calibration all done.')
            ret = ui.clearViews()
            while ret is False:
                ret = ui.clearViews()
            logger.debug(f'clearViews>>>  {ret}')
        return None

    # a 'shutdown' process complete method to be called on the ScanPlatform object
    # at the end of any script, to return all axes to positions ready to be homed
    # the next time this device is used. mainly to prevent
    # stall/stopped/collisions
    def end(self):
        try:
            self.yrot.move_degrees(5)
            self.xrot.move_degrees(5)
        except BaseException:
            logger.error(
                'something unexpected occured while completing end-routine')

    # the preferred method of clearing flags on a device. returns flags that
    # were cleared
    def clear_warnings(self):
        flags = self.warnings
        logger.info(flags)
        [self[ax].clear_warnings() for ax in self]
        return flags

    # use this to set multiple settings or values at once. valid uses give a list
    # of settings with corresponding values as in:
    #       self.set_settings('maxspeed',200,000)
    def set_setting(self, settings, values):
        """
        Give new setting to all connected devices that accept it.
        Parameters
        ----------
        settings: str
            specify which setting(s) you'd like changed.
        values:
            specify corresponding value(s) for settings, or one value
            to be written to various settings.
        """
        if len(settings) == len(values):
            for ax in self._objects:
                for s in range(len(settings)):
                    try:
                        ax.set_setting(settings[s], values[s])
                    except BaseException:
                        logger.warning(
                            f'failed setting {ax} {settings[s]} to {values[s]}')
        elif len(values) == 1 and len(settings) > 1:
            for o in self._objects:
                for s in settings:
                    try:
                        o.set_setting(s, values)
                    except BaseException:
                        logger.exception(f'failed setting {o} {s} to {values}')
        else:
            logger.debug('Invalid arguments')
        return None

    def stop(self):
        """
        stop all connected devices.
        """
        try:
            for o in self._objects:
                o.stop()
            return True
        except:
            return False

    def temperatures(self):
        """
        returns a list of tuples with all available temperature 
        readings from all connected axes.
        """
        all_temps = []
        for o in self._objects:
            all_temps.append((f'{o.label}_MotorTemperature_deg-C',o.motor_temperature()))
            all_temps.append((f'{o.label}_DriverTemperature_deg-C',o.driver_temperature()))
        return all_temps

    # call one time after initializing scanplatform object, to adjust home variables to
    # the intended work distance and alignment. Necessary if any attack angle calls
    # or move_attack_angle() otherwise positioning may be off by a lot for
    # larger angles.

    def alignSequence(self, attack_angle=-15, numPoses=2, numTrials=1):
        """
        Call once after initializing ScanPlatform object. Fine align devices to their intended positions.
        Be sure to call again if changing work distance throws off fine alignment.
        Parameters
        -----------
        attack_angle: float
            relative angle between scanner and target. for calculating target positions.
        numPoses: int
            number of poses from Poses.GOLDEN for alignment calibration. min 2 pose!
        numTrials: int
            number of times to repeat iterative alignment sequence. Note calibration
            variation exists, so default is 2 for quick align.
        """
        self.move_attack_angle(attack_angle, 'deg')
        for o in self._objects:
            o._home = o.position
        for _ in range(numTrials):           
            for p in Poses.GOLDEN[:numPoses]:
                self.move2pose(p)
                ui.addCalibrationView()
            ui.calibrate("")
            ui.clearViews()
            self.__alignScanner(math.radians(attack_angle))

    ########################### CLASS PROPERTIES ###########################
    # method for returning the current position of all connected axes.
    @property
    def position(self):
        positions = {p: self.axes[p].position for p in self}
        return positions

    # use this on a scanplatform object to get the available settings of all connected
    # devices in one dictionary. access specific settings as:
    #       self.settings['y_lin']['device']['system.temperature']
    # or for access directly from an attribute since their _settings are updated
    #       self.yaxis.settings['device']['system.temperature']
    @property
    def settings(self):
        devices = []
        settings_dicts = []
        # try:
        devices = [o.label for o in self._objects]
        settings_dicts = [o.settings for o in self._objects]
        # except: print(f'error getting settings from {o}')
        self._settings = {devices[i]: settings_dicts[i]
                          for i in range(len(devices))}
        return self._settings
    @property
    def target_tilt(self):
        return BaseAxis._TARGET_TILT
    
    @target_tilt.setter
    def target_tilt(self, tilt_degrees, realign=False, attack_angle=-15):
        BaseAxis._TARGET_TILT = math.radians(tilt_degrees)
        for o in self._objects:
            o._home = o._get_home(o.label, tilt_degrees)
        if realign:
            self.alignSequence(attack_angle)
        return None

    @property
    def wait_move(self):
        wm = {ax: self[ax].wait_move for ax in self}
        return wm

    @wait_move.setter
    def wait_move(self, value: bool):
        """
        Specify wait move setting for all connected axes.
        Parameters
        ----------
        value: bool
            determines if move calls are blocking or not.
        """
        for ax in self:
            self[ax].wait_move = value
        return None

    # display warnings or flags that are active on a device
    @property
    def warnings(self):
        return [self[ax].warnings for ax in self]

if __name__=='__main__':
    from .dev_connection import DevConnection
    from .oriental_motor.modbus_controller import ModbusController as mc
    from .oriental_motor.rotary_axis import RotaryAxis as OMRotaryAxis
    from zaber_motion.ascii.connection import Connection
    def start(controller):
        for dev in controller.devices:
                try:
                    con = Connection.open_serial_port(dev.device)
                    con.detect_devices(False)
                    controller.dev_controller = con
                    logger.info(f'Zaber motion device controller found on port {dev.device}!')
                except:
                    con.close()
                    port = mc(dev.device)
                    if not port.IsPortOpen(): port.PortOpen()
                    ready = port.ReadInternalOutputIO(3).READY
                    if ready:
                        controller.tilt_axis = OMRotaryAxis(port, controller.WD, controller.scanner_tilt, controller.target_tilt)
                        logger.info(f'Oriental motor tilt axis found on port {dev.device}!')
                    else: print(f'alarms: {port.GetAlarm(3)}',f'reset: {port.AlarmReset(3)}')
                    if not ready: port.PortClose()
    connection = DevConnection()
    start(connection)
    scan_platform = BaseAxis(connection.dev_controller,OMTiltAxisSerialDevice=connection.tilt_axis)
    scan_platform.wait_move = False
    scan_platform.home_all()
    scan_platform.position