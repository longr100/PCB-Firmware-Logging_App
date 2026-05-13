@echo off
echo ============================================
echo   Scent Dispenser - Windows Driver Check
echo ============================================
echo.
echo Checking for the two USB drivers required:
echo   CH340   -- UPDI programmer (firmware flash)
echo   FTDI    -- USB-C port (log download)
echo.
echo Note: checking does NOT require administrator access.
echo       Installing drivers DOES (a UAC prompt will appear).
echo       If you lack admin rights, ask your IT department.
echo.

set CH340_OK=0
set FTDI_OK=0

reg query "HKLM\SYSTEM\CurrentControlSet\Enum\USB\VID_1A86&PID_7523" >nul 2>&1
if %errorlevel% equ 0 set CH340_OK=1

reg query "HKLM\SYSTEM\CurrentControlSet\Enum\USB\VID_0403&PID_6015" >nul 2>&1
if %errorlevel% equ 0 set FTDI_OK=1

echo --- Results ---
echo.

if %CH340_OK%==1 (
    echo [OK] CH340 driver detected  (UPDI programmer / firmware flash)
) else (
    echo [!!] CH340 driver NOT found  (UPDI programmer / firmware flash)
    echo      This driver is needed to flash firmware.
    echo      Download the installer from:
    echo        https://www.wch-ic.com/downloads/CH341SER_ZIP.html
    echo      Run it and click Install (administrator access required).
)
echo.

if %FTDI_OK%==1 (
    echo [OK] FTDI driver detected  (USB-C log port)
) else (
    echo [!!] FTDI driver NOT found  (USB-C log port)
    echo      This driver is needed to download log data via USB-C.
    echo      Download the VCP installer from:
    echo        https://ftdichip.com/drivers/vcp-drivers/
    echo      Click "setup executable", run it, and click Extract then Install.
    echo      (Administrator access required.)
)
echo.

if %CH340_OK%==1 if %FTDI_OK%==1 (
    echo Both drivers are installed.
    echo If a device is still not appearing, try:
    echo   1. Unplug and re-plug the USB cable
    echo   2. Open Device Manager and look for any yellow warning icons
    echo   3. Try a different USB port or cable
)

if %CH340_OK%==0 (
    echo After installing missing drivers, plug in the device and run
    echo this script again to confirm detection.
)
if %FTDI_OK%==0 (
    echo After installing missing drivers, plug in the device and run
    echo this script again to confirm detection.
)

echo.
PAUSE
