@echo off
cd /d "%~dp0"

echo ============================================
echo   Scent Dispenser - Firmware Utility
echo ============================================
echo.

REM ── Quick driver check ──────────────────────────────────────────────────────
set CH340_OK=0
set FTDI_OK=0
reg query "HKLM\SYSTEM\CurrentControlSet\Enum\USB\VID_1A86&PID_7523" >nul 2>&1
if %errorlevel% equ 0 set CH340_OK=1
reg query "HKLM\SYSTEM\CurrentControlSet\Enum\USB\VID_0403&PID_6015" >nul 2>&1
if %errorlevel% equ 0 set FTDI_OK=1

if %CH340_OK%==0 (
    echo WARNING: CH340 driver not detected (needed for firmware flashing).
    echo          Run check_drivers_win.bat for installation instructions.
    echo.
)
if %FTDI_OK%==0 (
    echo WARNING: FTDI driver not detected (needed for USB-C log download).
    echo          Run check_drivers_win.bat for installation instructions.
    echo.
)

REM ── Install Python packages and launch ─────────────────────────────────────
echo Checking / installing required packages...
pip install --quiet pymcuprog pyserial argparse matplotlib
echo Packages ready.
echo.
echo Launching app...
python flash_gui.py
PAUSE
