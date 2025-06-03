@echo off

:::::::::::::::::::::::::::::::::::::::::::
:: build dagobah_device wheel
:::::::::::::::::::::::::::::::::::::::::::
py -m pip install setuptools
py -m pip install wheel
echo "Building wheel..."

py setup.py bdist_wheel
echo "Done building wheel"

:::::::::::::::::::::::::::::::::::::::::::
:: uninstall dagobah_device
:::::::::::::::::::::::::::::::::::::::::::
echo y | pip uninstall py_drive_api

:::::::::::::::::::::::::::::::::::::::::::
:: Install dagobah_device Wheel
:::::::::::::::::::::::::::::::::::::::::::
set fileName=""
for /r %%i in (.\dist\py_drive_api-*.whl) do (
  set fileName=%%i
)
echo Installing %fileName%

py -m pip install "%fileName%"

echo "Done"