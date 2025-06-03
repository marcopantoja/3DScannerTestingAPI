# Modbus RTU implementation through 'direct data operation'
############### COMMUNICATION  SETTINGS ##################
"""
Baud: default(115,200) --- 7                *** modbus -1
Byte & word order --- even/h-big-endian     *** modbus 0
Com Parity: EVEN --- 1                      *** modbus even
Com Stop Bit: ONE --- 0                     *** modbus 1 bit
TX Waiting: 3ms --- 30                      *** modbus 30
Silent Int: varies/auto --- 0               *** modbus 0
"""
import sys
from time import sleep, time

from serial.tools.list_ports_windows import comports
from .modbus_controller import ModbusController
from ..oriental_motor.units import Units


class SerialCom():
    """
    This class is for interfacing with the serial device connected
    on a com port. This will invoke methods from the ModbusController
    class.

    Attributes
    -----------
    com_device:  ModbusController
        the controller object that is instantiated with a com port,
        and then opened before being passed to Dagobah.
    
    address:  int
        the slave address of the associated Modbus RTU device
    
    units: oriental_motor.units, Units
        the units setting for converting values to/from native 
        device units.
    
    op_settings:  dict
        the dictionary containing settings for speed, accel,
        decel, trigger, datanum. at least for proper functioning.
    
    Methods
    ----------
    close_port()        :  
        return  error code

    detect_devices()    :  
        return  list with connected serial devices

    get_position()      :  
        param   units to receive reading, native units if none
        return  position or error code

    home()              : 
        param   wait_move
        return error code
    
    is_ready()          :
        return  bool if device is ready to receive commands
    
    jog()               :
        param   direction: str
        return error code

    move_absolute()     :
        param   pos
        param   units
        param   wait
        return error_code

    move_relative()     :
        param   pos
        param   units
        param   wait
        return error_code

    stop()              :
        return error_code

    wait_until_idle()   :
        return error_code
    """
    # attach this object to dagobah axis class for handling serial requests to - from 
    # computer / devices 
    def __init__(self, controller:ModbusController, 
                slave_addr, units:Units, operation_settings, wait):
        """
        initialize serial object for passing data to and from slaves. 
        modbus rtu protocol
        """
        self.com_device = controller
        self._wait_move = wait
        self.address = slave_addr
        self.units = units
        self.op_settings = operation_settings

    def close_port(self):
        """
        close this device's connection.
        """
        return self.com_device.PortClose()

    # initialize serial com with devices 
    @staticmethod
    def detect_devices():
        """
        returns list of connected devices on com ports
        """
        dev_list = [i for i in comports() 
                    if i.description.lower().find('serial')>=0]
        if len(dev_list)>0:
            return dev_list
        else:
            return None

    def driver_temperature(self):
        """
        returns the current driver temperature in deg-C.
        """
        return self.com_device.SendReadHolding(self.address, 0x00F8, 2) / 10 # divide val by 10 because 1=0.1 deg-C

    # Command Position, Feedback Position
    # Pulse request function
    def get_position(self, units):
        """
        query device and return current position in units specified,
        or in current device units if none specified.
        """
        position = self.com_device.ReadActualPosition(self.address, units)
        if position is None:
            print(f'No position returned. Port Open: {self.com_device.IsPortOpen()}')
        position = ModbusController._convert_value(units, position, False)
        return position

    # serial home command ABZO sensor home position detect
    # return to home operation
    def home(self, wait_move=True):
        """
        send device to 'home' position through serial move. 
        waits for operation to finish if wait_move = True (default)
        """
        self.com_device.Home(self.address)
        if wait_move: 
            end_move = self.com_device.ReadInternalOutputIO(
                self.address).HOME_END
            while not end_move:
                end_move = self.com_device.ReadInternalOutputIO(
                    self.address).HOME_END
        return True

    def inverter_voltage(self):
        """
        shows the inverter voltage of the driver in volts.
        """
        return self.com_device.SendReadHolding(
            slave_addr=self.address,
            register_addr=0x146,
            num_registers=2
        ) / 10 # conversion factor. 1=0.1 V

    def is_moving(self):
        """
        reads position, and determines if axis is moving based on deviation.
        """
        p1 = self.get_position(self.units)
        sleep(0.001)
        if self.get_position(self.units)==p1:
            return False
        else:
            return True

    def is_ready(self):
        """
        Reads internal IO to check if device is showing ready flag.
        """
        return self.com_device.ReadInternalOutputIO(self.address).READY

    def jog(self, direction:str):
        """
        jog the motor in the direction specified.
        param:direction
            'f' -- forward
            'r' -- reverse
        """
        speed = self.op_settings['speed']
        if direction is 'f':
            direction = speed
        elif direction is 'r':
            direction = -speed
        self.com_device.MoveVelocity(
            self.address, 
            direction,
            self.op_settings['accel'], 
            self.op_settings['decel'])

    def motor_temperature(self):
        """
        returns the current motor temperature in deg-C.
        """
        return self.com_device.SendReadHolding(
            slave_addr=self.address,
            register_addr=0x00FA,
            num_registers=2
        ) / 10 # divide by ten because 1=0.1 deg-C

    # direct data operation type 1: absolute positioning
    def move_absolute(self, pos, units=None, wait=None):
        """
        send serial move command to move device to 'pos'
        """
        if units is None: units = self.units
        if wait is None: wait = self._wait_move
        if units is not Units.NATIVE_UNITS:
            pos = ModbusController._convert_value(units, pos)
        self.com_device.MoveAbsolute(
            slave_addr=self.address,
            position=pos,
            velocity=self.op_settings['speed'],
            accel=self.op_settings['accel'],
            decel=self.op_settings['decel']
        )
        if wait:
            self.wait_until_idle()
        return True

    # direct data operation type 3: feedback based incremental positioning
    def move_relative(self, pos, units=None, wait=None):
        """
        send serial move command to move 'pos' units, 
        relative to current position.
        """
        if units is None: units = self.units
        if wait is None: wait = self._wait_move
        if units is not Units.NATIVE_UNITS:
            pos = ModbusController._convert_value(units, pos)
        self.com_device.MoveRelative(
            self.address,
            pos,
            self.op_settings['speed'],
            self.op_settings['accel'],
            self.op_settings['decel']
        )
        if wait:
            self.wait_until_idle()
        return True

    def stop(self):
        """
        immediately stop device.
        """
        return self.com_device.Stop(self.address)

    def supply_voltage(self):
        """
        shows the power supply voltage of the DC input
        driver in volts.
        """
        return self.com_device.SendReadHolding(
            slave_addr=self.address,
            register_addr=0x148,
            num_registers=2
        ) / 10 # conversion factor. 1=0.1 V

    def torque_monitor(self):
        """
        returns the current torque with the ratio against
        the maximum holding torque.
        """
        return self.com_device.SendReadHolding(
            slave_addr=self.address,
            register_addr=0x00D6,
            num_registers=2
        ) / 10 # shown as percentage value

    def wait_until_idle(self, timeout=None):
        """
        poll device until it has READY output.
        Params:
        timeout given in seconds. If none is specified, then infinite.
        """
        start = time()
        while not self.com_device.ReadInternalOutputIO(self.address).READY:
            if timeout is not None:
                if time()-start>timeout: break
        return True

if __name__=='__main__':
    controller = ModbusController(
        port=SerialCom.detect_devices()[0]
    )
#     controller.mdbslib.PortOpen(
#         controller.port,
#         115200,
#         2,
#         1)
#     print(controller.ReadActualPosition(1, Units.LENGTH_MILLIMETRES))
#     print(controller.ReadInternalOutputIO(2))

#     #home linear
#     controller.Home(1)
#     #home rotary
#     controller.Home(2)