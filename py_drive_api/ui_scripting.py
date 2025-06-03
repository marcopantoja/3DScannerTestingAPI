import json
import logging
import sys
import pyautogui as pg
from time import sleep
from os import listdir, getenv, makedirs
from os.path import getmtime, join, isdir, dirname
from xml.etree import ElementTree as ET

from ..py_drive_api import logs_dir

logger = logging.getLogger(__name__)


class UI_Scripting:
    """
    This class allows the user to interface with the 
    David6 gui, to drive calibrations and scans without
    any clicks.
    """
    id = 0
    file_saved = False
    cFpath = ''
    cUITab = 'Calibration'
    sequence = 1
    CUSTOM_METADATA = False
    _template = join(logs_dir,'custom-scan-metadata.xml')


    #################################################
    # Helper functions - these don't need to be called from main
    #################################################
    @staticmethod
    def log(message):
        logger.debug(message)
        print(message, flush=True)

    @staticmethod
    def jsonrpcCall(method, params=None):
        UI_Scripting.id = UI_Scripting.id + 1
        logger.info(
            f"{UI_Scripting.id} --> Requesting: {method}, params: {params}")
        if(params is not None):
            params = params.replace('\\','/')
            print('{"jsonrpc":"2.0", "method":"' +
                  method +
                  '", "id":' +
                  str(UI_Scripting.id) +
                  ', "params":["' +
                  str(params) +
                  '"]' +
                  '}', flush=True)
        else:
            print('{"jsonrpc":"2.0", "method":"' + method +
                  '", "id":' + str(UI_Scripting.id) + '}', flush=True)
        try:
            j = json.loads(sys.stdin.readline())
        except:
            print('Invalid input. Expected json formatted response with "result" field!')
            return False
        if "result" in j:
            m = '<-- ' + str(UI_Scripting.id) + ' succeeded'
            UI_Scripting.log(m)
            logger.info(m)
            return True
        else:
            m = '<-- ' + str(UI_Scripting.id) + ' ***FAILED***'
            UI_Scripting.log(m)
            logger.warning(f'Failure: {j}' + m)
            return False

    @staticmethod
    def __addScanToFusion():
        if UI_Scripting.jsonrpcCall("ScanAddToFusion"):
            UI_Scripting.sequence += 1
            UI_Scripting.cUITab = 'Alignment'
            return True
        return False

    # saves current project to path specified
    @staticmethod
    def __saveProjectAs(filepath):
        """
        save project to "filepath"
        """
        if not filepath.endswith('.3dscanproj') or filepath.endswith('.3dscanprojzip'):
            filepath+='.3dscanprojzip'
        if not isdir(dirname(filepath)): makedirs(dirname(filepath))
        UI_Scripting.file_saved = True
        UI_Scripting.cFpath = filepath
        logger.info(f'Saving project to {filepath}')
        return UI_Scripting.jsonrpcCall("SaveProjectAs", filepath)
    
    @staticmethod
    def _scanReferenceDataPath(path:str):
        """
        include all data from an xml formatted file
        in subsequent scan metadata.

        the file must exist at the location specified by
        path! Use an absolute path. 
        """
        if UI_Scripting.jsonrpcCall("SetScanReferenceDataPath", path):
            logger.info(f'Successfully set metadata Reference Data Path: {path}\n')
            if path is "":
                UI_Scripting.CUSTOM_METADATA = False
            else:
                UI_Scripting.CUSTOM_METADATA = True
            return True
        else:
            logger.warning('#####METADATA#####\nFailed to set metadata Reference Data Path!')
            return False

    # Specity either "FlatPlate" or "Artefact" for this method
    @staticmethod
    def __setTargetType(target):
        """
        changes the current target type during calibration pose
        capture.
        """
        return UI_Scripting.jsonrpcCall("SetCalibrationTargetType", target)

    @staticmethod
    def __startCalibrationProcess():
        return UI_Scripting.jsonrpcCall("StartCalibration")

    @staticmethod
    def __startScan():
        if UI_Scripting.jsonrpcCall("ScanStart"):
            return True
        if not UI_Scripting.__switchToTab("Scanning"):
            logger.warning("Failed starting scan. Switched to scanning tab to retry!")
            return UI_Scripting.jsonrpcCall("ScanStart")

    @staticmethod
    def __stepCalibrationForward():
        return UI_Scripting.jsonrpcCall("FlatPlateCalibrationStepForwards")

    @staticmethod
    def __switchToTab(tabName):
        UI_Scripting.cUITab = tabName
        return UI_Scripting.jsonrpcCall("ChangeNavigationTab", tabName)

    @staticmethod
    def switchTab(self, value):
        """
        updates internally stored ui page, and requests UI
        to change navigation page.
        """
        UI_Scripting.__switchToTab(value)
        return None

    @staticmethod
    def __updateMetadataFile(positions:dict=None, alignment:dict=None, metaentry_tuple_list:list=None):
        """
        this function will update the xml formatted file in %LOCALAPPDATA%/3DScan to include
        custom information in scan metadata. Normally used to include the current absolute values
        for all axes positions when a scan is captured. 
        Params:
            positions: 
              the curent value in default actuator units. mm for linear and rad for rotary
            alignment:
              the desired alignmentGuide parameters to be used for measuring. be sure to enable 
              the option 'Metadata' when measuring scans!
            metaentry_tuple_list:
              any number of additional metaentries can be specified through this list. members must
              be tuples of length 2. The first element is assigned to name, and the other element is 
              the value field.
        """
        units = {
            'target_tilt':'rad','x_rot':'rad','y_rot':'rad','z_lin':'mm','y_lin':'mm'
        }
        metatree = ET.Element('metatree',name='python')
        metatree.text = '\n\t'
        if alignment:
            guide = {str(a):str(alignment[a]) for a in alignment if a in ['rotX','rotY','rotZ','angleTolerance','icr']}
            if guide: 
                if 'angleTolerance' not in guide: guide['angleTolerance'] = '5'
                if 'icr' not in guide: guide['icr'] = 'None'
                metatree.append(ET.Element('alignmentGuide',guide))
        if positions:
            for p in positions:
                if p in units:
                    metatree.append(ET.Element('metaentry',{
                        'name':f'{p}-absolute_{units[p]}',
                        'value':str(positions[p])
                    }))
        if metaentry_tuple_list:
            for l in metaentry_tuple_list:
                if type(l) is tuple and len(l)==2:
                    metatree.append(
                        ET.Element(
                            'metaentry',
                            {
                                'name':str(l[0]),
                                'value':str(l[1])
                            })
                    )
        for idx, e in enumerate(metatree):
            if idx<len(metatree)-1:
                e.tail = '\n\t'
            else: 
                e.tail = '\n'
        with open(UI_Scripting._template,'w') as template:
            template.write(ET.tostring(metatree).decode())
        return True

    #################################################
    # User functions - call these from main
    #################################################
    # adds a view to the calibration
    @staticmethod
    def addCalibrationView(name=None, target_type='FlatPlate'):
        """
        adds the current view with the filename "name" if 
        it is specified. If capture fails, this will retry up
        to ten times, before logging a failed capture.
        """
        if UI_Scripting.__setTargetType(target_type):
            ret = UI_Scripting.jsonrpcCall("AddCalibrationView", name)
            if ret:
                return True
            else:
                i = 0
                while not ret and i < 10:
                    UI_Scripting.log("add view failed...Reattempting")
                    logger.warning(f'Failed to add calibration view. re-attempt {i+1}...')
                    if name is not None:
                        ret = UI_Scripting.jsonrpcCall("AddCalibrationView", name+f'-attempt{i+2}')
                    else:
                        ret = UI_Scripting.jsonrpcCall("AddCalibrationView", name)
                    i+=1
                    sleep(5)
                logger.warning('View capture failed!')
                return False
        else:
            logger.warning(f'Failed to set target type to {target_type}')
            return False

    # change the path for saving ExportBasePathEvaluationResult, or
    # use an empty string for no export.
    @staticmethod
    def basePath(path):
        """
        change path for BasePathEvaluationResult to be stored.
        paths must be absolute paths.
        """
        return UI_Scripting.jsonrpcCall(
            "SetExportBasePathEvaluationResult", path)

    # makes a calibration file using the currently added views
    @staticmethod
    def calibrate(zipFilePath='',auto_clear_views=True):
        """
        calibrate the scanner, and export the zip file to 
        "zipFilePath" 
        path must be a full path, do not use relative paths.
        """
        if not zipFilePath.endswith('.zip'): zipFilePath+='.zip'
        if not isdir(dirname(zipFilePath)): makedirs(dirname(zipFilePath))
        if UI_Scripting.jsonrpcCall("CalibrateUsingFlatPlateTarget", zipFilePath):
            if auto_clear_views:
                return UI_Scripting.clearViews()
            else: return True
        return False

    # use this for a new file
    @staticmethod
    def clearProject():
        """
        start a new project file.
        """
        UI_Scripting.file_saved = False
        UI_Scripting.sequence = 1
        UI_Scripting.cFpath = ''
        logger.info("Project Cleared! Starting New Project.")
        return UI_Scripting.jsonrpcCall("ClearProject")

    # deletes the current set of calibration views
    @staticmethod
    def clearViews():
        """
        deletes all current views from calibration.
        """
        return UI_Scripting.jsonrpcCall("DeleteCalibrationViews")

    @staticmethod
    def exportCalibrationViews(zip_path:str):
        """
        export a zip with all captured views, without
        performing a calibration.
        this method is useful for 'offline' calibrations.
        """
        if not isdir(dirname(zip_path)): makedirs(dirname(zip_path))
        return UI_Scripting.jsonrpcCall("ExportCalibrationViews", zip_path)

    # use this to load a hardware setup file
    @staticmethod
    def loadSetupFile(path:str):
        """
        load a hardware setup file into current calibration.
        """
        logger.info(f'Loaded hardware setup file from: {path}')
        return UI_Scripting.jsonrpcCall("ImportHardwareSetup", path)

    # requires that the user has swiched to the scanning page
    # this function will switch back to the calibration tab and step through
    # the calibration steps until it reaches step 5 (addCalibrationViews).
    # after calling this function the user can then call addCalibrationView and
    # calibrate again.
    @staticmethod
    def prepareToAddViewsAfterScanning():
        """
        switches gui back to calibration tab and leaves you ready to 
        capture views.
        """
        window = pg.getWindowsWithTitle(' 3D Scan 6.0.0.')[0]
        window.activate()
        [pg.click(p[0],p[1],duration=1) for p in 
            [(46,86),(210,210),(219,643),(210,210),(215,551),(215,368),(215,708)]
        ]
        return True
   
    # if no path is passed to load setup dialog box will popup.
    # not currently working correctly! does not restart scanner as intended. 
    @staticmethod
    def reconnect_scanner(time_delay=0):
        """
        reconnect the scanner and then wait for 'time_delay' seconds.
        """
        hw_setup_files = [join(getenv('localappdata'), f) for f in listdir(getenv('localappdata')) 
                            if f.endswith('.3dscansetup')]
        if len(hw_setup_files)==0:
            most_recent = None
        elif len(hw_setup_files)==1:
            most_recent = hw_setup_files[0]
        else:
            for hw in hw_setup_files:
                if getmtime(hw) > getmtime(most_recent):
                    most_recent = hw
        if not UI_Scripting.loadSetupFile(most_recent):
            logger.warning('Failed to load most recent setup file. Reconnect scanner failed!')
            print('Reconnect failed!')
            return False
        else:
            logger.debug('Scanner reconnected successfully!')
            sleep(time_delay)
            return True


    # requires user pass unique paths to avoid file overwrites!
    @staticmethod
    def saveProject(filepath=None):
        """
        saves current project to "filepath"
        use this instead of saveProjectAs!
        """
        logger.debug("Save project.")
        if not UI_Scripting.file_saved:
            if filepath is None:
                logger.exception(
                    "provide a path to save project file, or call saveAs first!")
                return False
            if not UI_Scripting.__saveProjectAs(filepath):
                logger.warning(f'Error saving to {filepath}')
        elif not UI_Scripting.cFpath == filepath:
            UI_Scripting.clearProject()
            UI_Scripting.__saveProjectAs(filepath)
        return UI_Scripting.jsonrpcCall("SaveProject")

    # Scans and adds the scan to the list
    @staticmethod
    def Scan(repeats=1,
    name=None, 
    basepath=None, 
    axes_position_metadata=None, 
    alignment_guide_metadata=None, 
    metaentry_tuple_list:list=None):
        """
        captures a scan.
        Arguments:
          repeats-- to capture a loop of scans. 
          name----- to set base scan names
          basepath- to export basepath evaluation results for correspondence debugging
          position_metadata-
                    use the position attribute from the Dagobah class, or
                    give a dict with axes labels and their current position, in default units
          alignment_guide_metadata-
                    give a dict with keys 'rotX','rotY','rotZ','icr','angleTolerance'
                    to specify an alignment guide in scan metadata that will be used 
                    when aligning .artifact in David6
        """
        if axes_position_metadata or alignment_guide_metadata or metaentry_tuple_list:
                logger.info('Writing Custom Metadata...')
                UI_Scripting.__updateMetadataFile(axes_position_metadata, alignment_guide_metadata, metaentry_tuple_list)
                UI_Scripting._scanReferenceDataPath(UI_Scripting._template)
                logger.debug('Done writing!!')
        for r in range(round(repeats)):
            if name is not None:
                UI_Scripting.scanNames(f"{name}_R{r}_S{UI_Scripting.sequence}")
            if basepath is not None:
                if not UI_Scripting.basePath(basepath):
                    logger.warning(f"Error setting basePathEval for scan: {name}")
            scanned = False
            failed = 0
            while failed<6 and not scanned:
                if UI_Scripting.cUITab != "Scanning":
                    if not UI_Scripting.__switchToTab("Scanning"):
                        UI_Scripting.log("Error switching to scan tab")
                        logger.warning(f"{name}: Failed switching to scan tab. . .")
                if UI_Scripting.__startScan():
                    if UI_Scripting.__addScanToFusion():
                        scanned = True
                    else:
                        UI_Scripting.log("Error adding scan to fusion list")
                        logger.warning(f"{name} add to fusion failed!")
                else:    
                    UI_Scripting.log("Error starting scan")
                    logger.warning(f"{name} scan failed to start capture!")
                if not scanned:
                    timeout=5
                    if UI_Scripting.__switchToTab("Calibration"):
                        logger.warning(f"Scan {name} failed! Switched to calibration tab to reset projector. waiting {timeout}s...")
                    else:
                        logger.warning(f"Scan {name} failed! Attempted switch to calibration tab and failed! waiting {timeout}s...")
                    failed += 1
                    print(f'Scan failed {failed} times...retrying scan!')
                    sleep(timeout)
                    UI_Scripting.__switchToTab("Scanning")
            if UI_Scripting.file_saved:  # Autosave additional scans
                if not UI_Scripting.saveProject(filepath=UI_Scripting.cFpath):
                    logger.warning(f"Error autosaving scan {name}!")
                    return False
        if axes_position_metadata or alignment_guide_metadata or metaentry_tuple_list:
            UI_Scripting._scanReferenceDataPath('')
        return True

    # requres the system to be on the calibration tab and to have calibration already done
    # this will switch from the calibration page to the scanning page and scan and add the
    # scan to the list
    @staticmethod
    def scanAfterCalibrating(scan_repeats=1, name_scheme=None):
        """
        takes "scan_repeats" scans named according to "name_scheme"
        after stepping calibration forward, and switching to scan tab.
        """
        if not UI_Scripting.__stepCalibrationForward():
            UI_Scripting.log("Error switching to scan tab")
        if not UI_Scripting.__switchToTab("Scanning"):
            UI_Scripting.log("Error switching to scan tab")
        if not UI_Scripting.Scan(scan_repeats, name_scheme):
            UI_Scripting.log("Error scanning after calibration!")
            return False

    # change the base scan name to "base_name"
    @staticmethod
    def scanNames(base_name):
        """
        changes default base scan name to "base_name"
        """
        logger.debug(f'New Scan Name: {base_name}')
        return UI_Scripting.jsonrpcCall("SetBaseScanName", base_name)


# tested py auto gui function added here
if __name__ == '__main__':
    UI_Scripting.prepareToAddViewsAfterScanning()