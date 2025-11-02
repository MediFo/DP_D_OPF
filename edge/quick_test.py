#!/usr/bin/env python3
"""
Quick Test Script - Simulates Multiple Edge Devices on Single Machine
Run this to test the framework without needing actual edge devices
"""

import sys
import time
print("="*80)
print("EDGE OPF EVALUATION - QUICK TEST")
print("Simulating multiple edge devices on YOUR single machine")
print("="*80)
print()

# Check Python dependencies
print("Step 1: Checking Python dependencies...")
try:
    import psutil
    import numpy
    import matplotlib
    print("✓ All Python dependencies found")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("\nPlease install dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

print()

# Check Julia
print("Step 2: Checking Julia installation...")
import subprocess
try:
    result = subprocess.run(["julia", "--version"],
                          capture_output=True,
                          text=True,
                          timeout=5)
    if result.returncode == 0:
        print(f"✓ Julia found: {result.stdout.strip()}")
        julia_available = True
    else:
        print("✗ Julia not working properly")
        julia_available = False
except (FileNotFoundError, subprocess.TimeoutExpired):
    print("✗ Julia not found in PATH")
    print("\n  To install Julia:")
    print("  1. Download from: https://julialang.org/downloads/")
    print("  2. Add to PATH: export PATH='path/to/julia/bin:$PATH'")
    julia_available = False

print()

if not julia_available:
    print("="*80)
    print("NOTICE: Julia not available")
    print("="*80)
    print("The framework is installed correctly, but you need Julia to run")
    print("OPF computations. Once Julia is installed, run:")
    print()
    print("  python evaluate_edge_opf.py --mode comparison --servers 3")
    print()
    print("This will simulate 3 edge devices on your single machine.")
    print("="*80)
    sys.exit(0)

# Test the framework
print("Step 3: Testing framework components...")
try:
    from edgesimpy import EdgeServer, EdgeSimulator
    from julia_wrapper import JuliaConfig
    from edge_opf_simulator import EdgeOPFSimulator
    from visualization import ResultsExporter
    print("✓ All framework modules loaded successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print()

# Run a minimal test
print("Step 4: Creating test simulation...")
print()
print("This simulates 3 edge servers on YOUR single machine:")
print("  - Edge Server 1: Will run OPF Node 1")
print("  - Edge Server 2: Will run OPF Node 2")
print("  - Edge Server 3: Will run OPF Node 3")
print()
print("All computations happen on your one physical device.")
print("The simulator tracks CPU, memory, network, and power for each.")
print()

sim = EdgeSimulator("Test_Simulation")

# Create 3 simulated edge servers
print("Creating 3 simulated edge servers...")
for i in range(3):
    server = sim.add_server(
        server_id=i+1,
        name=f"EdgeServer_{i+1}",
        location=(i*10.0, i*10.0)
    )
    print(f"  ✓ {server.name} created (simulated)")

print()
print(f"✓ Simulation ready with {len(sim.servers)} edge servers")
print()

print("="*80)
print("READY TO RUN!")
print("="*80)
print()
print("Now run the full evaluation:")
print()
print("Option 1 - Quick test (3 simulated servers, sequential):")
print("  python evaluate_edge_opf.py --mode distributed --servers 3 --sequential")
print()
print("Option 2 - Comparison test (centralized vs distributed):")
print("  python evaluate_edge_opf.py --mode comparison --servers 3")
print()
print("Option 3 - Parallel test (faster, simulates concurrent execution):")
print("  python evaluate_edge_opf.py --mode distributed --servers 3")
print()
print("Results will be saved to:")
print("  - edge/results/*.csv")
print("  - edge/plots/*.png")
print()
print("="*80)
