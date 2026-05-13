@echo off
REM Builds a standalone ScentDispenserFlash.exe for Windows.
REM Run once from the utility\ directory by double-clicking this file.
REM
REM Output: dist\ScentDispenserFlash.exe
REM Distribute by zipping that .exe alongside the .hex files.

pip install pyinstaller pymcuprog pyserial

pyinstaller ^
  --onedir ^
  --windowed ^
  --name "ScentDispenserFlash" ^
  flash_gui.py

echo.
echo Build complete: dist\ScentDispenserFlash.exe
echo.
echo To distribute:
echo   1. Copy your .hex files next to ScentDispenserFlash.exe
echo   2. Zip the folder and share it
PAUSE
