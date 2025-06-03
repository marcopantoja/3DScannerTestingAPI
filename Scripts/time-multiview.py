from py_drive_api import DevConnection, ui, Poses
from zaber_motion import Units
from time import time


base = f'E:/Timed-multiview'
posescsv = r"C:\15Pose-LatestHybrid.csv"
poseList = Poses.from_file(posescsv)
times={}
log_time = []
with DevConnection() as scanplatform:
    scanplatform.home_all()
    times['calibration_pose-capture'] = time()
    for pose in poseList:
        scanplatform.move(pose[-1])
        ui.addCalibrationView(
            name=pose[0],
            target_type=pose[1]
        )
    times['calibration_pose-capture'] -= time()
    times['calibration_evaluation-export'] = time()
    ui.calibrate(f'{base}/test-calib.zip')
    times['calibration_evaluation-export'] -= time()
    for trial in range(1,4):
        log_time.append(times)
        times = {'scanning':0,'moving':0}
        times['Trial'] = trial
        ui.clearProject()
        move_start = time()
        scanplatform.home_all()
        times[f'Trial{trial}-homing'] = time() - move_start
        for scan in range(4): # 4 turntable rotation
            scan_start = time()
            ui.Scan()
            times['scanning'] += time()-scan_start
            move_start = time()
            scanplatform.yrot.move_relative(90, Units.ANGLE_DEGREES, True)
            times['moving'] += time()-move_start
        scanplatform.yrot.move_degrees()