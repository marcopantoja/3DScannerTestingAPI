"""
UI scripting for automating calibration and then switching
to scan tab to grab ballplate scans.
"""
import time
from py_drive_api import DevConnection, Poses, ui

csv_path = r"C:\calibrations\poses\PosePeturbation.csv"

with DevConnection() as scanplatform:
    for t in range(3):
        unperturbed_calib_paths = [
            f'c:/calibrations/191202/MoritexGoldenT{t}U{i}_calibrationdata.zip' for i in range(5)]
        perturbed_calib_paths = [
            f'c:/calibrations/191202/MoritexGoldenT{t}P{i}_calibrationdata.zip' for i in range(5)]
        posesP = Poses.from_file(csv_path)
        posesU = Poses.GOLDEN
        for id, calib_path in enumerate(unperturbed_calib_paths):
            project_path = f"C:/Testing/MoritexGolden/ScanPlatformMoritexGoldenT{t}U{id}.hp3dscanproj"
            scanplatform.calibrate_position('golden')
            for p in posesU:
                scanplatform.move2pose(p)
                ret = ui.addCalibrationView()
                print(f"this is pose {p}, view added.")
            ret = ui.calibrate(calib_path)
            ret = ui.clearViews()
            ret = ui.saveProject(project_path)
            scanplatform.ballplate_position('unmounted')
            print("Ready to scan ball-plate!")
            ret = ui.scanAfterCalibrating()
            ret = ui.Scan()
            ret = ui.saveProject()
            for _ in range(2):
                scanplatform.zaxis.move_relative(30, scanplatform.zaxis.units)
                time.sleep(5)
                ret = ui.Scan()
                ret = ui.saveProject()
            print("press enter to return to nsd")
            scanplatform.zaxis.move_relative(-60, scanplatform.zaxis.units)
            ret = ui.Scan()
            ret = ui.saveProject()
            ret = ui.clearProject()
            ret = ui.prepareToAddViewsAfterScanning()

        for id, calib_path in enumerate(perturbed_calib_paths):
            project_path = f"C:/Testing/MoritexGolden/ScanPlatformMoritexGoldenT{t}P{id}.hp3dscanproj"
            scanplatform.calibrate_position('golden')
            for p in posesP:
                print(f'key: {p[1]}')
                scanplatform.move(p[1], relative_positions=True)
                ret = ui.addCalibrationView()
                print(f"this is pose {p[0]}, view added.")
            ret = ui.calibrate(calib_path)
            ret = ui.clearViews()
            ret = ui.saveProject(project_path)
            scanplatform.ballplate_position('unmounted')
            print("Ready to scan ball-plate!")
            ret = ui.scanAfterCalibrating()
            ret = ui.Scan()
            ret = ui.saveProject()
            for _ in range(2):
                scanplatform.zaxis.move_relative(30, scanplatform.zaxis.units)
                time.sleep(5)
                ret = ui.Scan()
                ret = ui.saveProject()
            print("press enter to return to nsd")
            scanplatform.zaxis.move_relative(-60, scanplatform.zaxis.units)
            ret = ui.Scan()
            ret = ui.saveProject()
            ret = ui.clearProject()
            ret = ui.prepareToAddViewsAfterScanning()
