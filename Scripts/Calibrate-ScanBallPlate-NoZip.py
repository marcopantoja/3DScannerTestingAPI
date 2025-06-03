"""
This scripts is to analyze differences in calibrations
as a scanner unit reaches a steady state temperature.

Calibrations performed repeatedly until script is stopped
or fatal david error occurs. Hardware setup file from each 
calibration is copied from APPDATA to project folder.
"""
import time
from os import getenv, listdir, makedirs
from os.path import join
from shutil import copy
from datetime import datetime as dt

from py_drive_api import DevConnection, Poses, ui
from zaber_motion.ascii import Connection

appdata = join(getenv('LOCALAPPDATA'), 'HP3DScan6')
test_name = 'CalibrationBallplateScans'
scanner = '3DScanner'
artefact = '3DScanArtifact'
target_id = '3DScanCalibrationTarget'
project_folder = f'C:/calibrations/{scanner}_{target_id}_CalibrationData_{dt.now().strftime("%y%m%d_%H%M%S")}'
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

poseList = Poses.from_file("C:/Users/Opus/Desktop/MarcoGithub/dagobah/Scripts/Tests/Optimus-LP_Markus15Pose.csv")
with DevConnection() as dago:
    dago.wait_move = False
    dago.calibrate_position('3DScanner')
    dago.new_home()
    count = 0
    file_name = f'{project_folder}/{count}_{test_name}.hp3dscanproj'
    start_time = time.time()
    test_duration = 3600*5
    while time.time()-start_time<=test_duration: # loop for a total of 5 hours
        ui.clearViews()
        for pose in poseList:
            dago.move(pose[1])
            ret = ui.addCalibrationView()
            while not ret:
                ret = ui.addCalibrationView()
        if ui.calibrate():#f'{project_folder}/calibZip.zip' no export calibration
            count +=1
            idx += 1
            store_setup(str(count))
            dago.ballplate_position('3DScanner')
            print('scanning ballplate...')
            ui.scanAfterCalibrating(
                1,
                f'{scanner}_{artefact}_{target_id}_{round(dago.zaxis.position,4)}_{dt.now().strftime("%y%m%d_%H%M%S")}'
            )
            ui.saveProject(file_name)
        if idx>=25:
            ui.clearProject()
            idx = 0
            file_name = f'{project_folder}/{count}_{test_name}.hp3dscanproj'
        print('next calibration...')
        ui.prepareToAddViewsAfterScanning()