#!/bin/bash

# Validation script for Gurobi optimization folder structure
# Run this to verify all files are in the correct location

echo "======================================================================"
echo "Validating Optimization Folder Structure"
echo "======================================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ERRORS=0

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ MISSING: $1"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
    else
        echo "✗ MISSING DIR: $1/"
        ERRORS=$((ERRORS + 1))
    fi
}

echo ""
echo "Checking Main Files..."
check_file "main.jl"
check_file "README.md"
check_file "QUICK_START.md"
check_file "TROUBLESHOOTING.md"
check_file "test_setup.jl"

echo ""
echo "Checking Script Files (Julia optimization)..."
check_dir "scripts"
check_file "scripts/data_manager.jl"
check_file "scripts/fun_centralized_OPF.jl"
check_file "scripts/fun_compute_sensitivity.jl"
check_file "scripts/fun_consensus_update.jl"
check_file "scripts/fun_dual_update.jl"
check_file "scripts/fun_residual_update.jl"
check_file "scripts/fun_reveal_load.jl"
check_file "scripts/fun_voltage_update.jl"

echo ""
echo "Checking Testbed Files..."
check_dir "testbeds"
check_file "testbeds/pglib_opf_case14_ieee.m"
check_file "testbeds/pglib_opf_case30_ieee.m"
check_file "testbeds/pglib_opf_case118_ieee.m"

echo ""
echo "Checking Edge Simulation Framework..."
check_dir "edge"
check_file "edge/edge_opf_simulator.py"
check_file "edge/visualization.py"
check_file "edge/julia_wrapper.py"
check_file "edge/evaluate_edge_opf.py"
check_file "edge/example_custom_hardware.py"
check_file "edge/quick_test.py"

echo ""
echo "Checking Edge Scripts (Julia for edge devices)..."
check_dir "edge/scripts"
check_file "edge/scripts/opf_centralized_edge.jl"
check_file "edge/scripts/opf_edge_node.jl"

echo ""
echo "Checking Edge Simulator Components..."
check_dir "edge/edgesimpy"
check_file "edge/edgesimpy/__init__.py"
check_file "edge/edgesimpy/simulator.py"
check_file "edge/edgesimpy/edge_server.py"
check_file "edge/edgesimpy/edge_service.py"
check_file "edge/edgesimpy/network_link.py"
check_file "edge/edgesimpy/resource_monitor.py"

echo ""
echo "Checking for Gurobi references in Julia files..."
echo "----------------------------------------------------------------------"

GUROBI_COUNT=$(grep -r "using Gurobi" scripts/*.jl edge/scripts/*.jl 2>/dev/null | wc -l)
echo "Found 'using Gurobi' in $GUROBI_COUNT files"

if [ $GUROBI_COUNT -lt 3 ]; then
    echo "✗ WARNING: Expected at least 3 files to use Gurobi"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ Gurobi properly imported in Julia scripts"
fi

echo ""
echo "Checking for gurobi_env parameter passing..."
GUROBI_ENV_COUNT=$(grep -r "gurobi_env" scripts/*.jl edge/scripts/*.jl 2>/dev/null | grep "function\|Gurobi.Optimizer" | wc -l)
echo "Found gurobi_env parameter in $GUROBI_ENV_COUNT function signatures"

if [ $GUROBI_ENV_COUNT -lt 5 ]; then
    echo "✗ WARNING: Expected at least 5 functions to use gurobi_env"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ gurobi_env properly passed to functions"
fi

echo ""
echo "======================================================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED!"
    echo "======================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Run: julia test_setup.jl (verify Julia packages and Gurobi license)"
    echo "  2. Run: julia main.jl (run optimization)"
    echo "  3. Run: cd edge && python example_distributed_opf.py (run edge simulations)"
    exit 0
else
    echo "❌ FOUND $ERRORS ERROR(S)"
    echo "======================================================================"
    echo ""
    echo "Please fix the errors above before proceeding."
    exit 1
fi
