#!/bin/bash
# Launcher script for Ouroboros Conductor GUI

echo "🚀 Starting Ouroboros Conductor GUI..."
echo "======================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if GUI requirements are installed
echo ""
echo "Checking dependencies..."

# Try to import tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: tkinter is not available"
    echo "   On Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "   On Fedora: sudo dnf install python3-tkinter"
    echo "   On macOS: tkinter should be included with Python"
    exit 1
fi
echo "✓ tkinter is available"

# Check optional dependencies
python3 -c "import numpy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ numpy is available (vector operations enabled)"
else
    echo "⚠ numpy is not available (using fallback mode)"
fi

python3 -c "import jax" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ JAX is available (GPU acceleration enabled)"
else
    echo "⚠ JAX is not available (CPU-only mode)"
fi

echo ""
echo "======================================"
echo "Launching GUI..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Launch the GUI
python3 -m gui.conductor_gui

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ GUI exited with an error"
    exit 1
fi

echo ""
echo "✓ GUI closed successfully"
