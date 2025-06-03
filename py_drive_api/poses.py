import csv
import logging
import math
import os
import xml.etree.ElementTree as ET
import zipfile

logger = logging.getLogger(__name__)


class Poses():
    """
    This class is for importing data from external sources. Currently supports import
    from a csv or xml file.

    use the from_file() method for scripting imports. csv, xml, and zip are valid.

    """

    GOLDEN = [(0, 0), (-6, -6), (-2, -4), (-4, -2),
              (6, 3), (3, 6), (9, 9), (3, -3), (-3, 3)]

    # this formats the output of the import csv or xml functions, so that the output
    # to the user is the same in either case.
    @staticmethod
    def __format_file(file):
        heading = file[0]
        file = file[1:]
        formatted_file = []
        for f in file:
            f_row = []
            pose_num = f[0]
            data = f[1:]
            f_row.append(pose_num)
            dic = {heading[d + 1]: data[d] for d in range(len(data))}
            f_row.append(dic)
            formatted_file.append(f_row)
        return formatted_file

    # method for importing a csv file given a path to the file. path must be a string
    # path can be full, but if files are in the working directory filenames
    # are sufficient.
    @staticmethod
    def __csv(csvpath: str, delim_char: str = ','):
        def format(s: str):
            no = ['_', ' ', 'mm', 'rad', 'deg', 'um']
            for n in no:
                s = s.lower().replace(n, '')
            return s
        axes = 'ylinzlinyrotxrotattack'
        file = []
        items = []
        values = []
        row_data = {}
        r = []
        with open(csvpath, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                for item in row:
                    if axes.rfind(format(item)) == -1:
                        r.append(row[item])
                    else:
                        items.append(item)
                        values.append(row[item])
                row_data = dict(zip(items, values))
                r.append(row_data)
                file.append(r)
                row_data = {}
                r = []
        return file

    # method for importing a csv file created/saved by excel if the method above fails.
    # 'dialect' is excel specific for certain situations in which an Error
    # gets raised from the method above.
    @staticmethod
    def __csv_excel(csvpath, delim_char=','):
        try:
            with open(csvpath, newline='') as csvfile:
                csv_reader = csv.reader(
                    csvfile, delimiter=delim_char, dialect='excel')
                c = 0
                row_data = []
                file = []
                heading = []
                for row in csv_reader:
                    columns = len(row)
                    for item in row:
                        if c <= columns - 1:
                            try:
                                r = float(item)
                                row_data.append(r)
                            except BaseException:
                                heading.append(item)
                            c += 1
                        if c == columns:
                            file.append(row_data)
                            row_data = []
                            c = 0
        except UnicodeDecodeError as e:
            logger.exception(e)
            pass
        file[0] = heading
        file = Poses.__format_file(file)
        return file

    # method for importing data from an xml file. see xml example 'test3.xlm' for
    # heirarchy.
    @staticmethod
    def __xml(xmlpath):
        tree = ET.parse(xmlpath).getroot()
        poseList = tree.findall('poses/pose')
        data = []
        d = {}
        keys = []
        values = []
        file = []
        for pose in poseList:
            pose_num = pose.get('number')
            children = [p for p in pose]
            data.append(pose_num)
            for child in children:
                tag = child.tag
                text = child.text
                numeric = float(text.replace('="', '').replace('"', ''))
                keys.append(tag)
                values.append(numeric)
            d = {keys[i]: values[i] for i in range(len(keys))}
            keys = []
            values = []
            data.append(d)
            d = {}
            file.append(data)
            data = []
        return file

    # call this method from the from_file() method. This is to be used
    # when you want to recreate a set of poses from a previous calibration.
    # this method reads in data from the Calibration.log file in the
    # CalibrationData.zip archives, saved during calibrating.
    @ staticmethod
    def __calib_log(zip_path):
        pose_list = []
        pos = {}
        i = 1
        with zipfile.ZipFile(zip_path) as cz:
            with cz.open('calibration.log') as log:
                stream = log.read()
        xml = ET.fromstring(stream)
        poses = xml.findall('multiView/world_T_plate')
        for p in poses:
            for c in p:
                try:
                    pos['x_rot'] = c.attrib['rx']
                    pos['y_rot'] = c.attrib['ry']
                    pos['z_rot'] = c.attrib['rz']
                except KeyError:
                    pos['x_lin'] = c.attrib['x']
                    pos['y_lin'] = c.attrib['y']
                    pos['z_lin'] = c.attrib['z']
                pose = (i, pos)
            pose_list.append(pose)
            i += 1
            pos = {}
        return pose_list

    # use this method for importing files with poses. file paths can be given
    # individually, or for many files, a list comprehension can be used.
    @staticmethod
    def from_file(file_path: str):
        """
        The CSV headers are the 'keys' or commands that go with the values in each row.
        The XML file takes text from pose//c as the 'keys.'
        """
        file_name = os.path.basename(file_path)
        ext = ''
        valid_ext = ['csv', 'xml', 'zip']
        not_imported = True
        for r in range(len(file_name) - 1, -1, -1):
            if file_name[r] is not '.':
                ext = file_name[r] + ext
            else:
                break
        if ext not in valid_ext:
            logger.debug(f'Extension "{ext}" is invalid!')
        if ext == 'csv':
            try:
                from_file = Poses.__csv(file_path)
                not_imported = False
            except UnicodeDecodeError as e:
                logger.debug(e + '\nAttempting Excel csv import...')
                try:
                    from_file = Poses.__csv_excel(file_path)
                    not_imported = False
                except BaseException:
                    logger.debug('Excel csv import failed.')
        if ext == 'xml':
            from_file = Poses.__xml(file_path)
            not_imported = False
        if ext == 'zip':
            from_file = Poses.__calib_log(file_path)
            not_imported = False
        elif not_imported:
            logger.debug('Check file! Error importing from:\n')
            logger.debug(f'Path: {file_path}')
            from_file = ''
        return from_file
