"""
This test is to tilt the projector in a semi-aggressive 
manner to determine if any camera or lens components are
moving from these disturbances. 

This test will help inform whether we should use ruggedized
lenses, or if the current setup is adequate.
"""
from datetime import datetime as dt
from math import radians
import pyautogui as pg
from os import getenv
from os.path import join
from py_drive_api import DevConnection, Poses, ui, ScanPlatform
from zaber_motion import Units
from random import shuffle


def add_views():
    window = pg.getWindowsWithTitle('HP 3D Scan 6.0.0.')[0]
    if not window.isActive:
        [pg.click(p[0],p[1], duration=0.3) for p in 
            [(654, 1059), (774, 936)]]
    if not window.isMaximized: window.maximize()
    [pg.click(p[0],p[1],duration=1) for p in 
        [(46,86),(210,210),(219,643),(210,210),(215,551),(215,368),(215,708)]
    ]
    return True

def set_speed(speed:str, device:ScanPlatform):
    settings = {
        'fast':{
            'accel':{
                'y_lin':400,
                'x_rot':400
            },
            'maxspeed':{
                'y_lin':350000,
                'x_rot':250000
            }
        },
        'faster':{
            'accel':{
                'y_lin':805,
                'x_rot':400
            },
            'maxspeed':{
                'y_lin':975000,
                'x_rot':250000
            }
        },
        'normal':{
            'accel':{
                'y_lin':205,
                'x_rot':200
            },
            'maxspeed':{
                'y_lin':275000,
                'x_rot':25000
            }
        }
    }
    try:
        for setting in settings[speed]:
            [d.set_setting(setting, settings[speed][setting][d.label]) for d in [device.yaxis,device.xrot]]
        return True
    except:
        return False

def perturb_scanner(device:ScanPlatform, rep, prefix, end_position=-25):
    ball_positions = {
        -25:{
            'target_tilt':radians(10),
            'x_rot':radians(-27.5),
            'y_lin':131.93476855468745,
            'y_rot': 3.141592653589790,
            'z_lin': 213.72053613281238
        },
        0:{
            'target_tilt':radians(-15),
            'x_rot': -0.04345051714379008, 
            'y_lin': 385.33238671874983,
            'y_rot': 3.141592653589790, 
            'z_lin': 169.22489550781242
        },
        25:{
            'target_tilt':radians(-43.01),
            'x_rot':0.4365136636161724,
            'y_lin':658.8134921874996,
            'y_rot':3.141592653589790,
            'z_lin':248.35023632812485
        }
    }
    if speed is not 'off':
        device.ballplate_position(
            'custom', ball_positions[end_position]
        )
        device.wait_idle()
    x = round(device.xrot.get_position(Units.ANGLE_DEGREES))
    ui.Scan(name=f'{prefix}_{rep}R_{x}deg_{dt.now().strftime("%y%m%d_%H%M%S")}')
    device.ballplate_position(
        'custom',
        ball_positions[0]
    )
    device.wait_idle()
    return True
 
Test = 'ScanPlatform-0degScannerCalibrations-ProjectorTiltSpeed-RandomVary-Oct2020'
speeds = ['normal','fast','faster']
repetitions = range(5)
unit_num = 'LP-04'
artifact = 'P-06'
target = 'LP-A'
base = f'E:/ScanPlatform1.5-Testing/{Test}'
posescsv = join(getenv("onedrive"),r"LatestHybrid.csv")
poseList = Poses.from_file(posescsv)
with DevConnection( ) as dago:
    dago.wait_move = False
    for idx, speed in enumerate(speeds):
        ui.clearViews()
        prefix = f'{unit_num}_{target}_{artifact}_{speed}{idx}'
        dago.yrot._home=0
        dago.home_all()
        for p in poseList:
            dago.move(p[-1])
            ui.addCalibrationView(p[0],p[1])
        dago.yrot.move_degrees(-180)
        ui.calibrate(f'{base}/{prefix}_0degScanner_CalibrationData_{dt.now().strftime("%y%m%d_%H%M%S")}.zip')
        ui.saveProject(f'{base}/{prefix}_{Test}_{dt.now().strftime("%y%m%d_%H%M%S")}')
        ui.scanAfterCalibrating(name_scheme='after-calib-scan')
        dago.ballplate_position('custom',{
            'target_tilt':radians(-15),
            'x_rot': -0.04345051714379008, 
            'y_lin': 385.33238671874983, 
            'y_rot': 3.1764992386296798,
            'z_lin': 169.22489550781242})
        set_speed(speed, dago)
        for rep in range(1,2):
            ui.Scan(name=f'{prefix}_{rep}R_+00deg_{dt.now().strftime("%y%m%d_%H%M%S")}')
            perturb_scanner(dago, rep, prefix)
        if speed is not 'normal': set_speed('normal',dago)
        ui.clearProject()
        add_views()