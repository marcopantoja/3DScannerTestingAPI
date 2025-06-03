"""
basic script to capture artefact pfm/png
views for offline calibrations.
"""
from datetime import datetime as dt
from py_drive_api import DevConnection, Poses, ui
from os import makedirs

test = 'ArtefactViews-15PoseViews'
num_views = 4
num_calib_exports = 10
proj_time = dt.now().strftime("%y%m%d")
scanner = '3DScanner'
artefact = 'CALIBRATIONARTIFACT'
target = 'CALIBRATIONTARGET'
base = 'E:/Testing/3DSCANNER_Target-Verification_200309'
proj_folder = f'{base}/{scanner}_{artefact}_{target}_{test}_{proj_time}'
try:
    makedirs(proj_folder)
except OSError:
    pass
poseList = Poses.from_file("D:/3DScanner/Github/dagobah(master)/Scripts/Tests/3DScanner_Markus15Pose.csv")
with DevConnection() as dago:
    # ui.clearViews()
    dago.wait_move = False
    dago.calibrate_position('3DScanner')
    for _ in range(2):
        ui.addCalibrationView()
    dago.ballplate_position('3DScanner')
    for v in range(num_views):
        z, y, t = ('+00','+00','+45')
        ui.addCalibrationView(
            f'{scanner}--{artefact}--{dt.now().strftime("%H%M%S")}--({z}Pz{y}Ry{t}T)',
            'Artifact'
        )
    ui.exportCalibrationViews(f'{proj_folder}/{scanner}_{artefact}_ArtefactViews_{dt.now().strftime("%y%m%d")}_{dt.now().strftime("%H%M%S")}.zip')
    ui.clearViews()
    dago.calibrate_position('3DScanner')
    dago.new_home()
    for _ in range(num_calib_exports):
        for p in poseList:
            dago.move(p[1])
            ui.addCalibrationView()
        ui.exportCalibrationViews(
            f'{proj_folder}/{scanner}_{target}_CalibrationData_{dt.now().strftime("%y%m%d")}_{dt.now().strftime("%H%M%S")}.zip'
        )
        ui.clearViews()
    dago.calibrate_position('3DScanner')