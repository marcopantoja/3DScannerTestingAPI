"""
This script is designed to capture calibration pose views
from various positions, to be used in 'offline' calibrations.
The intent is for this to reveal an ideal set of poses for
calibration purposes.
"""
from csv import DictWriter
from time import sleep
from datetime import datetime as dt
from math import degrees, pi
from os import listdir, makedirs
from os.path import exists, join
from winsound import Beep

from py_drive_api import DevConnection, Poses, ui, ScanPlatform
from zaber_motion.ascii.connection import Connection

#  
# Pose capture coordinates:
base_zip_path = 'C:/Users/Opus/Desktop/MarcoGithub/calibrations/calibDOE_200323/Trial4'
tilts = ['+20Tilt', '-15Tilt', '-20Tilt', '-17.5Tilt', '+17.5Tilt', '+15Tilt']
poseList = Poses().from_file(r"C:\Users\Opus\OneDrive - HP Inc\Optimus-LP\calibrations\AllPoses.csv")
rel_moves = {
    '-20Tilt':-7.5,
    '-17.5Tilt':-8,
    '-15Tilt':-8,
    '+15Tilt':7.5,
    '+17.5Tilt':7.5,
    '+20Tilt':8
}
ball_tilts = {
    '-20Tilt':'+80T',
    '-17.5Tilt':'+77.5T',
    '-15Tilt':'+75T',
    '+15Tilt':'+45T',
    '+17.5Tilt':'+42.5T',
    '+20Tilt':'+40T',
    '+120Tilt':'-60T',
    '+45Tilt':'+15T'
}
abs_positions = {
    '+120Tilt':300,
    '+45Tilt':218.25
}
try:
    listdir(base_zip_path)
except:
    makedirs(base_zip_path)
def log_position(platform_:ScanPlatform, pose_coordinates, attempt, type_capture):
    fpath = join(base_zip_path, 'position_log.csv')
    row = platform_.position
    row['Pose Coordinates'] = pose_coordinates
    row['First Attempt'] = attempt
    row['Target Type'] = type_capture
    row['Date'] = dt.now().strftime('%y%m%d')
    row['Time'] = dt.now().strftime('%H%M%S')
    if exists(fpath):
        file_exists = True
    else:
        file_exists = False
    with open(fpath, mode='a', newline='') as csv:
        writer = DictWriter(
            csv, row.keys()
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# start connection
with DevConnection() as platform_:
    platform_.wait_move = False
    platform_.move({
            'x_rot': -0.5515254071686861-platform_.xrot._home, 
            'y_lin': -328, 
            'y_rot': 0.0, 
            'z_lin': 152.91172080569144})
    platform_.new_home()
    count = 0
    total = 0
    zips = 1
    zip_size = 21
    ui.clearProject()
    ui.clearViews()
    for tilt in tilts:
        platform_.home_all()
        print(f'Now capturing {tilt}...')
        zmin = poseList[0][1]['z_lin']
        for pose in poseList:
            zlin = pose[1]['z_lin']
            yrot = float(pose[1]['y_rot'])
            if count == 1:
                zmin = pose[1]['z_lin']
            elif (count == zip_size or
                 (zlin == '0' and yrot == 0) or 
                 (zlin == '60' and yrot == 0) ) :
                zip_path = base_zip_path +'/'+ tilt +'/'
                try:
                    makedirs(zip_path)
                except OSError:
                    pass
                zip_name = zip_path + f'{zmin}_{zmax}_CalibrationSource_{zips}.zip'
                ui.exportCalibrationViews(zip_name)
                zips += 1
                count = 0
                ui.clearViews()
            z = pose[1]['z_lin'].zfill(2)
            yrot = str(round(degrees(-yrot))).zfill(2)
            if z[0] != '-': z = "+" + z
            if yrot[0] != '-': yrot = "+" + yrot
            pose_coordinates = f'({z}Pz{yrot}Ry{tilt.replace("Tilt","T")})'
            platform_.move(pose[1])
            print('moved')
            attempt = ui.addCalibrationView(pose_coordinates)
            log_position(platform_, pose_coordinates, attempt, 'FlatPlate')
            count += 1
            total += 1
            zmax = pose[1]['z_lin']
        if total%zip_size>0:
            zip_path = base_zip_path +'/'+ tilt +'/'
            zip_name = zip_path + f'{zmin}_{zmax}_CalibrationSource_{zips}.zip'
            zips+=1
            ui.exportCalibrationViews(zip_name)
            ui.clearViews()
        # Ballplate "zero" Position
        platform_.home_all()
        [ui.addCalibrationView() for _ in range(2)] # 2 views to allow multiple artifact views in zip export
        platform_.ballplate_positon(
            'custom',{
                'x_rot': platform_.xrot.position, 
                'y_lin': platform_.yaxis.position, 
                'y_rot': pi, 
                'z_lin': 225.24889648437488
                }
        )
        platform_.zaxis.move_relative(rel_moves[tilt], platform_.zaxis.units, True) # CGz : 0
        pose_coordinates = f'(+00Pz+00Ry{ball_tilts[tilt]})'
        attempt = ui.addCalibrationView(
            name= pose_coordinates,
            target_type='Artifact'
        )
        log_position(platform_, pose_coordinates, attempt, 'Artifact')
        platform_.zaxis.move_relative(33, platform_.zaxis.units, True) # CGz : 33
        pose_coordinates = f'(+33Pz+00Ry{ball_tilts[tilt]})'
        attempt = ui.addCalibrationView(
            name= pose_coordinates,
            target_type='Artifact'
        )
        log_position(platform_, pose_coordinates, attempt, 'Artifact')
        platform_.zaxis.move_relative(-23, platform_.zaxis.units, True) # CGz : 10
        pose_coordinates = f'(+10Pz+00Ry{ball_tilts[tilt]})'
        attempt = ui.addCalibrationView(
            name= pose_coordinates,
            target_type='Artifact'
        )
        log_position(platform_, pose_coordinates, attempt, 'Artifact')
        platform_.zaxis.move_relative(-50, platform_.zaxis.units, True) # CGz : -40
        pose_coordinates = f'(-40Pz+00Ry{ball_tilts[tilt]})'
        attempt = ui.addCalibrationView(
            name= pose_coordinates,
            target_type='Artifact'
        )
        log_position(platform_, pose_coordinates, attempt, 'Artifact')
        zip_path = base_zip_path +'/'+ tilt +'/'
        zip_name = zip_path + f'P102_CalibrationSource_{zips}.zip'
        zips += 1
        ui.exportCalibrationViews(zip_name)
        ui.clearViews()
        platform_.yrot.move(0)
        Beep(3000,1500)
        Beep(700, 2500)
        sleep(45)
    # Flat & +15 Ballplate views
    platform_.home_all()
    [ui.addCalibrationView() for _ in range(2)] # 2 views to allow multiple artifact views in zip export
    for tilt in abs_positions:
        platform_.yrot.move(pi)
        Beep(750,1000)
        Beep(850,1000)
        sleep(30)
        platform_.zaxis.move_absolute(abs_positions[tilt], platform_.zaxis.units, True) # CGz : 0
        pose_coordinates = f'(+00Pz+00Ry{ball_tilts[tilt]})'
        attempt = ui.addCalibrationView(
            name=pose_coordinates,
            target_type='Artifact'
        )
        log_position(platform_, pose_coordinates, attempt, 'Artifact')
        if tilt != '+120Tilt':
            platform_.zaxis.move_relative(33, platform_.zaxis.units, True) # CGz : 33
            pose_coordinates = f'(+33Pz+00Ry{ball_tilts[tilt]})'
            attempt = ui.addCalibrationView(
                name=pose_coordinates,
                target_type='Artifact'
            )
            log_position(platform_, pose_coordinates, attempt, 'Artifact')
            platform_.zaxis.move_relative(-23, platform_.zaxis.units, True) # CGz : 10
            pose_coordinates = f'(+10Pz+00Ry{ball_tilts[tilt]})'
            attempt = ui.addCalibrationView(
                name=pose_coordinates,
                target_type='Artifact'
            )
            log_position(platform_, pose_coordinates, attempt, 'Artifact')
            platform_.zaxis.move_relative(-50, platform_.zaxis.units, True) # CGz : -40
            pose_coordinates = f'(-40Pz+00Ry{ball_tilts[tilt]})'
            attempt = ui.addCalibrationView(
                name=pose_coordinates,
                target_type='Artifact'
            )
            log_position(platform_, pose_coordinates, attempt, 'Artifact')
    zip_path = base_zip_path +'/'+ 'ArtefactViews' +'/'
    try:
        makedirs(zip_path)
    except OSError:
        pass
    zip_name = zip_path + f'P102_CalibrationSource_{zips}.zip'
    zips += 1
    ui.exportCalibrationViews(zip_name)
    ui.clearViews()