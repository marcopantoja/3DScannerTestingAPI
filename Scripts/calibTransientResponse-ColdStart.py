"""
This scripts is to analyze differences in calibrations
as a scanner unit reaches a steady state temperature.

Calibrations performed repeatedly until script is stopped
or fatal david error occurs. Hardware setup file from each 
calibration is copied from APPDATA to project folder.
"""
import time
from os import listdir, makedirs
from os.path import join
from shutil import copy
from datetime import datetime as dt

from py_drive_api import DevConnection, Poses, ui
from py_drive_api import logs_dir

appdata = join(logs_dir,'data')
add_view_time = 20
test_name = 'TransientResponseColdStart'
scanner = 'SI-26'
artefact = 'P102'
target_id = 'LP-A'
base_dir = 'D:/Testing'
artefact_path = r"C:\Avg_200108_0rot.artefact"
project_folder = f'{base_dir}/{test_name}_{scanner}_{target_id}_CalibrationData_{dt.now().strftime("%y%m%d")}'
idx = 1
try:
    makedirs(project_folder)
except OSError:
    pass
# no storesetup if exporting entire zip files!
def store_setup(id_tag):
    hwSetup = [o for o in listdir(appdata) if o.endswith('.3dscansetup')]
    for h in hwSetup:
        new_name = join(project_folder, id_tag.zfill(3) + "_" + h)
        copy(
            join(appdata, h),
            new_name)

poseList = Poses.from_file(r"C:\3DScanner\Scripts\Tests\poses15Tilt.csv")
with DevConnection() as dago:
    dago.wait_move = False
    dago.calibrate_position('3DScanner')
    dago.new_home()
    count = 1
    file_name = f'{project_folder}/{count}_{test_name}.3dscanproj'
    start_time = time.time()
    test_duration = 3600*12
    while time.time()-start_time<=test_duration:
        ui.clearViews()
        for pose in poseList:
            dago.move(pose[1])
            ret = ui.addCalibrationView()
        if ui.calibrate(f'{project_folder}/{test_name}_{scanner}_{target_id}_CalibrationData_{dt.now().strftime("%y%m%d_%H%M%S")}.zip'):# no export calibration
            # store_setup(str(count))
            count +=1
            idx += 1
            dago.ballplate_position('Scanner-Zero')
            print('scanning ballplate...')
            ui.scanAfterCalibrating(
                1,
                f'{scanner}_{artefact}_{target_id}_{dt.now().strftime("%y%m%d_%H%M%S")}'
            )
            ui.saveProject(file_name)
        if idx>30:
            ui.clearProject()
            idx = 0
            count += 1
            file_name = f'{project_folder}/{count}_{test_name}.3dscanproj'
        print('next calibration...')
        ui.prepareToAddViewsAfterScanning()