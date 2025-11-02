#!/bin/bash
# Quick installer for OPF Edge Evaluation dependencies
# For Linux/Mac

echo "================================================================================"
echo "OPF Edge Evaluation - Dependency Installer (Linux/Mac)"
echo "================================================================================"
echo

echo "Step 1: Installing Julia packages..."
echo "--------------------------------------------------------------------------------"
julia install_julia_packages.jl
if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Julia package installation failed!"
    echo "Make sure Julia is installed and in your PATH."
    echo
    exit 1
fi

echo
echo "Step 2: Installing Python packages..."
echo "--------------------------------------------------------------------------------"
cd edge
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Python package installation failed!"
    echo "Make sure Python and pip are installed."
    echo
    exit 1
fi
cd ..

echo
echo "================================================================================"
echo "Installation Complete!"
echo "================================================================================"
echo
echo "You can now run:"
echo "  - julia main.jl"
echo "  - cd edge && python evaluate_edge_opf.py --mode centralized"
echo
echo "For more info, see:"
echo "  - edge/README.md"
echo "  - edge/QUICKSTART.md"
echo
