"""
This scripts is to calibrate scanner and then scan
the ballplate/artefact.

Calibrations performed repeatedly until script is stopped,
'test_duration' is reached, or fatal david error occurs.
"""
import time
from os import getenv, listdir, makedirs
from os.path import join
from shutil import copy
from datetime import datetime as dt

from py_drive_api import DevConnection, Poses, ui
from zaber_motion.ascii import Connection

appdata = join(getenv('LOCALAPPDATA'), 'HP3DScan6')
test_name = 'LP-Target-Verification'
scanner = 'SI-26'
artefact = 'P102'
target_id = 'LP-I'
project_folder = f'D:/3DScanner/Testing/{scanner}_{test_name}_{artefact}_200225/{scanner}_{target_id}_CalibrationData'
idx = 1
try:
    listdir(project_folder)
except:
    makedirs(project_folder)
def store_setup(id_tag):
    hwSetup = [o for o in listdir(appdata) if o.endswith('.hp3dscansetup')]
    for h in hwSetup:
        new_name = join(project_folder, id_tag.zfill(3) + "_" + h)
        copy(
            join(appdata, h),
            new_name)

poseList = Poses.from_file("D:/3DScanner/Github/dagobah(master)/Scripts/Tests/3DScanner_Markus15Pose.csv")
with DevConnection() as scanplatform:
    scanplatform.wait_move = False
    scanplatform.calibrate_position('3DScanner')
    scanplatform.new_home()
    count = 1
    # ui.sequence=13
    file_name = f'{project_folder}/{scanner}_{target_id}_1_{test_name}.hp3dscanproj'
    start_time = time.time()
    test_duration = 10
    while count<=test_duration:
        ui.clearViews()
        for pose in poseList:
            scanplatform.move(pose[1])
            ret = ui.addCalibrationView()
            while not ret:
                ret = ui.addCalibrationView()
        # ---Calibration Zip Export--- #
        if ui.calibrate(f'{project_folder}/{scanner}_{target_id}_CalibrationData_{dt.now().strftime("%y%m%d_%H%M%S")}.zip'):# no export calibration
            scanplatform.ballplate_position('3DScanner')
            print('scanning ballplate...')
            num_scans = 3
            ui.scanAfterCalibrating(
                num_scans,
                f'{scanner}_{artefact}_{target_id}_{dt.now().strftime("%y%m%d_%H%M%S")}'
            )
            count +=1
            idx += num_scans
            ui.saveProject(file_name)
        if idx>=60:
            ui.clearProject()
            idx = 0
            file_name = f'{project_folder}/{scanner}_{target_id}_{count}_{test_name}.hp3dscanproj'
        print('next calibration...')
        ui.prepareToAddViewsAfterScanning()
    ui.clearProject()