from datetime import datetime as dt
import math
import os
import time


from py_drive_api import DevConnection, Poses, ui

import winsound
frequency = 2500  # Set Frequency To 2500 Hertz
duration = 1000  # Set Duration To 1000 ms == 1 second


Test = 'MoritexDagoba'
trials = 3
directory = "Desktop/MarcoGithub/calibrations"
posefile = "Desktop/MarcoGithub/calibrations/Poses/Pose.csv"
poselist = Poses.from_file(posefile)[:15]
if __name__ == "__main__":
    print("Script started")
    with DevConnection() as dago:
        dago.wait_move = False
        dago.xrot._home -= math.radians(1)
        dago.home_all()
        dago.wait_move = True
        dago.alignSequence(2,2)
        winsound.Beep(frequency, duration)
        dago.zaxis.set_setting('maxspeed', 2*dago.zaxis.settings['maxspeed'])
        for t in range(trials):
            a = '18'
            ui.clearProject()
            ui.clearViews()
            path = f'{directory}/{Test}_Attack{a}_calibrationdata_{dt.now().strftime("%y%m%d_%H%M%S")}_{t+1}.zip'
            print(f"Rotate target to {a}")
            winsound.Beep(frequency, duration)
            time.sleep(15)
            for p in poselist:
                dago.move(p[1])
                ret = ui.addCalibrationView()
            print(f"Rotate target to -{a}")
            winsound.Beep(frequency, duration)
            time.sleep(15)
            for p in poselist:
                dago.move(p[1])
                ret = ui.addCalibrationView()
            winsound.Beep(frequency, duration)
            ret = ui.calibrate(path)
            ret = ui.clearViews()
            dago.wait_move = False
            dago.home_all()
            dago.wait_move = True
            projpath = f'{directory}{Test}_{dt.now().strftime("%y%m%d")}_{t}.hp3dscanproj'
            ui.saveProject(projpath)
            ui.scanAfterCalibrating()
            ui.Scan(name='TargetScan')
            dago.ballplate_position(
            position='custom',
            custom={
                'y_lin':363.1261894531248,
                'z_lin':100.24871433593742,
                'y_rot':math.pi}
            )
            print("Ready to scan ball-plate!")
            ret = ui.Scan(2,f'SI-25_P102_{round(dago.zaxis.position,4)}_{dt.now().strftime("%y%m%d_%H%M%S")}')
            ui.saveProject()
            winsound.Beep(frequency, duration)
            time.sleep(15)
            ui.Scan(name=f'SI-25_P102_{round(dago.zaxis.position,4)}_{dt.now().strftime("%y%m%d_%H%M%S")}')
            ui.saveProject()
            ui.prepareToAddViewsAfterScanning()
            winsound.Beep(frequency, duration)
                # proj_path = f"{directory}/dago_{Test}_Attack-{a}_{dt.now().strftime('%y%m%d')}_{t+1}.hp3dscanproj"
                # ui.saveProjectAs(proj_path)
    # Uncomment the following portion to scan ballplate after calibration steps
                # dago.ballplate_positon('mounted')
                # print("Ready to scan ball-plate!")
                # ret = ui.scanAfterCalibrating()
                # ret = ui.Scan(2)
                # ui.saveProject()
                # time = dt.now().strftime("%y%m%d_%H%M%S")
                # ui.scanNames(f'MAP_P102_SI-25_MoritexGolden_+45abtX_{time}')
                # ui.saveProject()
                # ui.prepareToAddViewsAfterScanning()
