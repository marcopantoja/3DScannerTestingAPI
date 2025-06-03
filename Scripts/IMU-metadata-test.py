from datetime import datetime as dt
from math import degrees, radians
import pyautogui as pg
from os import listdir, makedirs
from py_drive_api import DevConnection, Poses, ui, Dagobah
from zaber_motion import Units
from random import shuffle


def set_speed(speed:str, device:Dagobah):
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
                'y_lin':754437,
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

def perturb_scanner(device:Dagobah, rep, prefix, end_position=-25):
    ball_positions = {
        -25:{
            'target_tilt': 0.17435839227423353, 
            'x_rot': -0.4712388980384689, 
            'y_lin': 136.31478027343744, 
            'y_rot': 3.141592653589793, 
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
            'target_tilt': -0.6983062337229313, 
            'x_rot': 0.4031710572106901, 
            'y_lin': 639.6770478515622, 
            'y_rot': 3.141592653589793, 
            'z_lin': 238.54209082031238
        }
    }
    moved = False
    while not moved:
        try:
            maxspeed = device.yaxis.settings['maxspeed']
            device.ballplate_position(
                'custom', ball_positions[end_position]
            )
            moved = True
        except:
            maxspeed *= .95
            device.yaxis.set_setting('maxspeed',maxspeed)
        device.wait_idle()
    x = round(device.xrot.get_position(Units.ANGLE_DEGREES))+2
    ui.Scan(name=f'{prefix}_{rep}R_{x}deg_maxspeed-{maxspeed}_{dt.now().strftime("%y%m%d_%H%M%S")}')
    return True

base = 'E:/Testing'
test = f'IMU-metadata-test_{dt.now().strftime("%y%m%d")}'
proj_dir = f'{base}/{test}'
speeds = ['normal','fast','faster']
trials = range(5)
pose_csv = r"C:\Scripts\Poses\LatestHybrid.csv"
poselist = Poses.from_file(pose_csv)
with DevConnection() as dago:
    dago.wait_move = False
    dago.home_all()
    for pose in poselist:
        dago.move(pose[-1])
        ui.addCalibrationView(pose[0],pose[1])
    ui.calibrate(f'{proj_dir}/CalibrationData_{dt.now().strftime("%y%m%d_%H%M%S")}.zip')
    ui.saveProject(f'{proj_dir}/IMU-meta-test.3dscanprojzip')
    for t in trials:
        shuffle(speeds)
        for speed in speeds:
            if set_speed(speed, dago):
                for position in [-25, 25]:
                    perturb_scanner(dago, t, f'3dScanner-{speed}', position)
            else:
                raise Exception(f'Falied setting device speeds to {speed}!')
