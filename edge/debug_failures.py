#!/usr/bin/env python3
"""
Debug script to show why Julia nodes failed
Run this after a failed evaluation to see error messages
"""

import json
import sys
from pathlib import Path

# Find the most recent distributed results file
results_dir = Path('results')
if not results_dir.exists():
    print("Error: results/ directory not found")
    print("Make sure you're in the edge/ directory")
    sys.exit(1)

# Get most recent distributed results
distributed_files = sorted(results_dir.glob('distributed_*_full.json'), key=lambda x: x.stat().st_mtime, reverse=True)

if not distributed_files:
    print("No distributed results found. Run an evaluation first:")
    print("  python evaluate_edge_opf.py --mode distributed --servers 3")
    sys.exit(1)

latest_file = distributed_files[0]
print(f"Reading: {latest_file.name}")
print("="*80)

with open(latest_file, 'r') as f:
    results = json.load(f)

print("\nNODE FAILURE ANALYSIS")
print("="*80)

node_results = results.get('node_results', [])
if not node_results:
    print("No node results found")
    sys.exit(1)

for i, node_result in enumerate(node_results, 1):
    print(f"\n{'='*80}")
    print(f"NODE {i}")
    print(f"{'='*80}")

    print(f"Success: {node_result.get('success', False)}")
    print(f"Return Code: {node_result.get('return_code', 'N/A')}")
    print(f"Execution Time: {node_result.get('execution_time_s', 0):.3f}s")

    # Show error output
    stderr = node_result.get('stderr', '').strip()
    if stderr:
        print(f"\n--- STDERR (Error Output) ---")
        print(stderr)

    # Show standard output
    stdout = node_result.get('stdout', '').strip()
    if stdout:
        print(f"\n--- STDOUT (Standard Output) ---")
        print(stdout)

    # Show any error field
    if 'error' in node_result:
        print(f"\n--- ERROR ---")
        print(node_result['error'])

print("\n" + "="*80)
print("COMMON ISSUES AND FIXES")
print("="*80)
print("""
1. Julia not found:
   - Make sure Julia is installed and in PATH
   - Test: julia --version

2. Path issues (Windows):
   - Julia scripts may have wrong path separators
   - Try sequential mode: --sequential

3. File not found:
   - Make sure you're in the DP_D_OPF root directory
   - Check that scripts/ and testbeds/ folders exist

4. Missing Julia packages:
   - Open Julia and run: using PowerModels, JuMP, Gurobi
   - Install if missing: using Pkg; Pkg.add("PowerModels")

5. Gurobi license:
   - Make sure Gurobi is licensed
   - Or modify scripts to use free solver
""")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("""
1. Check the error messages above
2. Fix the identified issue
3. Try running again:

   python evaluate_edge_opf.py --mode centralized  # Test if Julia works
   python evaluate_edge_opf.py --mode distributed --servers 1  # Test single node
   python evaluate_edge_opf.py --mode distributed --servers 3  # Full test
""")
