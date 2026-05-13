#!/bin/bash
# Builds a standalone ScentDispenserFlash.app for macOS.
# Run once from the utility/ directory: bash build_mac.sh
#
# Output: dist/ScentDispenserFlash.app
# Distribute by zipping that .app alongside the .hex files.

pip3 install pyinstaller pymcuprog pyserial

pyinstaller \
  --onedir \
  --windowed \
  --name "ScentDispenserFlash" \
  flash_gui.py

echo ""
echo "Build complete: dist/ScentDispenserFlash.app"
echo ""
echo "To distribute:"
echo "  1. Copy your .hex files next to ScentDispenserFlash.app"
echo "  2. Zip the folder and share it"
read -p "Press Enter to exit..."
