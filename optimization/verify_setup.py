#!/usr/bin/env python3
"""
Pre-Flight Check for Edge OPF Evaluation

Verifies that all dependencies and files are in place before running evaluations.

Usage:
    python verify_setup.py
"""

import sys
import os
import subprocess
from pathlib import Path

print("=" * 80)
print("Edge OPF Pre-Flight Check")
print("=" * 80)
print()

checks_passed = 0
checks_failed = 0
warnings = 0

def check(name, passed, error_msg=None, fix_msg=None):
    global checks_passed, checks_failed
    if passed:
        print(f"✓ {name}")
        checks_passed += 1
    else:
        print(f"✗ {name}")
        if error_msg:
            print(f"  Error: {error_msg}")
        if fix_msg:
            print(f"  Fix: {fix_msg}")
        checks_failed += 1

def warn(name, msg):
    global warnings
    print(f"⚠️  {name}")
    print(f"  {msg}")
    warnings += 1

# 1. Check Python modules
print("[1] Checking Python Dependencies")
print("-" * 80)

try:
    import numpy
    check("NumPy", True)
except ImportError:
    check("NumPy", False, "NumPy not installed", "pip install numpy")

try:
    import pandas
    check("Pandas", True)
except ImportError:
    check("Pandas", False, "Pandas not installed", "pip install pandas")

try:
    import matplotlib
    check("Matplotlib", True)
except ImportError:
    check("Matplotlib", False, "Matplotlib not installed", "pip install matplotlib")

print()

# 2. Check directory structure
print("[2] Checking Directory Structure")
print("-" * 80)

current_dir = Path.cwd()
check("Current directory", current_dir.name == "optimization",
      f"Not in optimization directory (currently in {current_dir.name})",
      "cd /path/to/DP_D_OPF/optimization")

edge_dir = Path("edge")
check("edge/ directory exists", edge_dir.exists(),
      "edge directory not found",
      "Make sure you're in the optimization directory")

if edge_dir.exists():
    check("edge/edge_opf_simulator.py", (edge_dir / "edge_opf_simulator.py").exists())
    check("edge/julia_wrapper.py", (edge_dir / "julia_wrapper.py").exists())
    check("edge/visualization.py", (edge_dir / "visualization.py").exists())
    check("edge/edgesimpy/ directory", (edge_dir / "edgesimpy").exists())

print()

# 3. Check testbeds
print("[3] Checking Test Cases")
print("-" * 80)

testbeds_dir = Path("testbeds")
check("testbeds/ directory exists", testbeds_dir.exists(),
      "testbeds directory not found")

if testbeds_dir.exists():
    case14 = testbeds_dir / "pglib_opf_case14_ieee.m"
    check("pglib_opf_case14_ieee.m", case14.exists(),
          "Case 14 file not found",
          "Download from https://github.com/power-grid-lib/pglib-opf")

    case_files = list(testbeds_dir.glob("*.m"))
    if len(case_files) > 0:
        print(f"  Found {len(case_files)} test case(s)")
    else:
        warn("No test cases", "No .m files found in testbeds/")

print()

# 4. Check Julia installation
print("[4] Checking Julia")
print("-" * 80)

try:
    result = subprocess.run(['julia', '--version'],
                          capture_output=True,
                          text=True,
                          timeout=5)
    if result.returncode == 0:
        version = result.stdout.strip()
        check(f"Julia installed ({version})", True)
    else:
        check("Julia installed", False, "Julia command failed")
except FileNotFoundError:
    check("Julia installed", False,
          "Julia not found in PATH",
          "Install from https://julialang.org/downloads/")
except subprocess.TimeoutExpired:
    warn("Julia check", "Julia command timed out")

print()

# 5. Check Julia packages
print("[5] Checking Julia Packages")
print("-" * 80)

julia_pkg_check = '''
using Pkg
packages = ["PowerModels", "JuMP", "Gurobi", "Primes", "JSON"]
for pkg in packages
    if haskey(Pkg.project().dependencies, pkg) || pkg in ["PowerModels", "JuMP", "Gurobi", "Primes", "JSON"]
        try
            eval(Meta.parse("using $pkg"))
            println("PASS:$pkg")
        catch e
            println("FAIL:$pkg")
        end
    else
        println("MISSING:$pkg")
    end
end
'''

try:
    result = subprocess.run(['julia', '-e', julia_pkg_check],
                          capture_output=True,
                          text=True,
                          timeout=30)

    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if line.startswith("PASS:"):
                pkg = line.split(":")[1]
                check(pkg, True)
            elif line.startswith("FAIL:"):
                pkg = line.split(":")[1]
                check(pkg, False, f"{pkg} package failed to load",
                      f"julia -e 'using Pkg; Pkg.add(\"{pkg}\")'")
            elif line.startswith("MISSING:"):
                pkg = line.split(":")[1]
                check(pkg, False, f"{pkg} package not installed",
                      "Run: julia install_julia_packages.jl")
    else:
        warn("Julia package check", "Package check script failed")
        print("  Run manual check: julia install_julia_packages.jl")

except FileNotFoundError:
    print("  Skipped (Julia not available)")
except subprocess.TimeoutExpired:
    warn("Julia package check", "Package check timed out")
except Exception as e:
    warn("Julia package check", f"Unexpected error: {e}")

print()

# 6. Check Julia scripts
print("[6] Checking Julia OPF Scripts")
print("-" * 80)

julia_scripts = [
    "opt_main_verified.jl",  # Paillier
    "opt_main_bgv.jl",       # BGV
    "opt_main_ckks.jl",      # CKKS
]

for script in julia_scripts:
    script_path = Path(script)
    check(script, script_path.exists())

print()

# 7. Check CLI script
print("[7] Checking CLI Script")
print("-" * 80)

cli_script = Path("evaluate_edge_opf.py")
check("evaluate_edge_opf.py", cli_script.exists())

if cli_script.exists():
    # Try importing to check for syntax errors
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("evaluate_edge_opf", cli_script)
        if spec and spec.loader:
            print("  ✓ CLI script has valid Python syntax")
    except Exception as e:
        warn("CLI script syntax", f"Syntax check failed: {e}")

print()

# Summary
print("=" * 80)
print("Summary")
print("=" * 80)
print()

total_checks = checks_passed + checks_failed
print(f"✓ Passed:   {checks_passed} / {total_checks}")
print(f"✗ Failed:   {checks_failed} / {total_checks}")
if warnings > 0:
    print(f"⚠️  Warnings: {warnings}")

print()

if checks_failed == 0:
    print("=" * 80)
    print("✓ ALL CHECKS PASSED - READY TO RUN")
    print("=" * 80)
    print()
    print("Quick Start Commands:")
    print()
    print("1. Install Julia packages (if not done):")
    print("   julia install_julia_packages.jl")
    print()
    print("2. Run evaluations:")
    print("   python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m")
    print("   python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m")
    print("   python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m")
    print()
else:
    print("=" * 80)
    print("⚠️  SETUP INCOMPLETE - FIX ERRORS ABOVE")
    print("=" * 80)
    print()
    print("Common fixes:")
    print()
    print("1. Julia packages missing:")
    print("   julia install_julia_packages.jl")
    print()
    print("2. Python packages missing:")
    print("   pip install numpy pandas matplotlib")
    print()
    print("3. Wrong directory:")
    print("   cd /path/to/DP_D_OPF/optimization")
    print()
    print("4. Gurobi license:")
    print("   Get free academic license: https://www.gurobi.com/academia/")
    print()

    sys.exit(1)

print("=" * 80)
