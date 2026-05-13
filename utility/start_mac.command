#!/bin/bash
# Double-click this file in Finder to install dependencies and launch the app.
# First time only: right-click → Open → Open (to allow macOS to run it).

cd "$(dirname "$0")"

echo "============================================"
echo "  Scent Dispenser – Firmware Utility"
echo "============================================"
echo ""
echo "Checking / installing required packages..."
pip3 install --quiet --user pymcuprog pyserial argparse matplotlib
echo "Packages ready."
echo ""
echo "Launching app..."
python3 flash_gui.py
