"""
This class defines methods from the Orientalmotor Modbus dll Library
not all methods from this dll are defined here.
"""
import sys
from os.path import join

import clr
omr_lib_base = join(sys.base_prefix,'Lib','site-packages','py_drive_api','include')
libpaths = [omr_lib_base,join(omr_lib_base,'x64')]
[sys.path.append(path) for path in libpaths]
clr.AddReference('omrlib')
clr.AddReference('System')
from Omrlib import PRODUCT
from Omrlib.Communication import Modbus
from Omrlib.Communication.ModbusInfo import (ErrorCode, ExceptionCode,
                                             FrameInfo, SendReceiveData)
from Omrlib.Products.AZSeries import AzInternalIO
from System.IO.Ports import Parity as PARITY
from System.IO.Ports import StopBits as STOPBITS

if __package__!='py_drive_api.oriental_motor': __package__='py_drive_api.oriental_motor'
from ..oriental_motor.units import Units


class ModbusController():

    def __init__(self, port):
        try:
            self.mdbslib = Modbus(PRODUCT.AZ)
        except:
            from shutil import copy
            if self.mdbslib.GetArchitecture()==64:
                copy(
                    src=join(libpaths[0], 'mdbslib.dll'),
                    dst=join(omr_lib_base, 'mdbslib.dll')
                )
            else:
                copy(
                    src=join(libpaths[0], 'mdbslib.dll'),
                    dst=join(omr_lib_base, 'mdbslib.dll')
                )
            self.mdbslib = Modbus(PRODUCT.AZ)
        self.port = port

    @staticmethod
    def _convert_value(units:Units, value, to_device=True): # bool to device units: True / from device units: False
        """
        convert a value to device units from current axes units
        """
        if to_device:
            return value * units
        else:
            return value / units

    def AlarmReset(self, slave_addr):
        error_code = self.mdbslib.AlarmReset(slave_addr)
        return error_code

    def GetAlarm(self, slave_addr):
        error_code, alarm = self.mdbslib.GetAlarm(slave_addr, int())
        if not error_code:
            return alarm
        return alarm

    def Home(self, slave_addr):
        error_code = self.mdbslib.Home(slave_addr)
        if not error_code:
            return error_code

    def IsPortOpen(self):
        return self.mdbslib.IsPortOpen()
    
    def MoveAbsolute(self, slave_addr, position, velocity, accel, decel=None, units=None):
        if decel is None: decel = accel
        if units is not None: position = ModbusController._convert_value(units, position)
        error_code = self.mdbslib.MoveAbsolute(slave_addr, position, velocity, accel, decel)
        return error_code

    def MoveRelative(self, slave_addr, position, velocity, accel, decel=None, units=None):
        if decel is None: decel = accel
        if units is not None: position = ModbusController._convert_value(units, position)
        error_code = self.mdbslib.MoveRelative(slave_addr, position, velocity, accel, decel)
        return error_code

    def MoveVelocity(self, slave_addr, velocity, accel, decel=None):
        if decel is None: decel = accel
        error_code = self.mdbslib.MoveVelocity(slave_addr, velocity, accel, decel)
        return error_code
    
    def PortClose(self):
        return self.mdbslib.PortClose()

    def PortOpen(self):
        port = self.port
        baudrate = 115200
        parity = PARITY.Even
        stopbits = STOPBITS.One
        error_code = self.mdbslib.PortOpen(port, baudrate, parity, stopbits)
        return error_code
    
    def ReadActualPosition(self, slave_addr, units):
        error_code, position = self.mdbslib.ReadActualPosition(slave_addr, int())
        if position is not None: 
            position = ModbusController._convert_value(units, position, False)
        if error_code:
            return position
        else:
            return error_code
    
    def ReadCommandPosition(self, slave_addr, units=None):
        error_code, position = self.mdbslib.ReadCommandPosition(slave_addr, int())
        if units is not None: 
            position = ModbusController._convert_value(units, position, False)
        if error_code:
            return position
        else:
            return error_code

    def ReadInternalOutputIO(self, slave_addr):
        error_code, IO_output = self.mdbslib.ReadInternalOutPutIO(slave_addr, AzInternalIO())
        if error_code:
            return IO_output
        else:
            return error_code

    def ReadParameter(self, slave_addr, register):
        error_code, param_value = self.mdbslib.ReadParameter(slave_addr, register, int())
        if error_code:
            return param_value
        else:
            return error_code
    
    def ReadTargetPosition(self, slave_addr, units=None):
        error_code, position = self.mdbslib.ReadTargetPosition(slave_addr, int())
        if units is not None:
            position = ModbusController._convert_value(units, position, False)
        if error_code:
            return position
        else:
            return error_code
    
    def SendDiagnosis(self, slave_addr, data):
        error_code, response = self.mdbslib.SendDiagnosis(SendReceiveData(), slave_addr, data)
        if error_code:
            return response
        else:
            return error_code
    
    def SendReadHolding(self, slave_addr, register_addr, num_registers):
        error_code, response = self.mdbslib.SendReadHolding(
            SendReceiveData(),
            slave_addr,
            register_addr,
            num_registers
        )
        if error_code:
            bin_response = ''
            for idx, i in enumerate(response.Response.Frame()[3:-2]): # only iter through data bytes
                if i==255:
                    if idx==0:
                        bin_response += '-' # preserves signed values
                    else:
                        continue
                else:
                    bin_response += bin(i)[2:]
            return int(bin_response, base=2)
        else:
            return error_code
    
    def Stop(self, slave_addr):
        return self.mdbslib.Stop(slave_addr)
    
    def __enter__(self):
        if not self.IsPortOpen(): self.PortOpen()
    
    def __exit__(self, p1, p2, p3):
        if self.IsPortOpen(): self.PortClose()

# open port 12 home slave 2 and move.
if __name__=='__main__':
    from serial.tools.list_ports import comports
    mdbslib = ModbusController([c.device for c in comports() if 'serial' in c.description.lower()][0])
    mdbslib.PortOpen()
    mdbslib.Home(2)
    mdbslib.MoveAbsolute(2, 9000, 5000, 2000)
    mdbslib.PortClose()
