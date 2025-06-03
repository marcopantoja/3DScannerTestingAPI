from .scan_platform import ScanPlatform
from .poses import Poses
from .ui_scripting import UI_Scripting as ui
from .dev_connection import DevConnection
from sys import base_prefix
from os.path import join
logs_dir = join(base_prefix, 'Lib', 'site-packages', 'py_drive_api')