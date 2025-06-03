from setuptools import setup, find_packages
from datetime import datetime as dt
from os import listdir, remove

try:
    if len(listdir('dist'))>0:
        [remove(f'dist/{f}') for f in listdir('dist')]
except:
    pass
setup(
    name='py_drive_api',
    version=dt.now().strftime("%m.%d.%Y.%H"),
    description='for controlling zaber-motion devices',
    author='marco pantoja',
    python_requires='>3.8',
    install_requires=['zaber-motion','pythonnet','pyserial','pyautogui'],
    packages=find_packages('.')
    )
