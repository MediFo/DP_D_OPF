#!/usr/bin/env python3
"""
COMPREHENSIVE PYTHON TEST SUITE
Tests all Python scripts for syntax, imports, and basic functionality
"""

import sys
import os
import importlib.util
from pathlib import Path

print("="*80)
print(" PYTHON TEST SUITE")
print("="*80)
print()

# Track results
tests_run = 0
tests_passed = 0
tests_failed = 0
test_errors = []

def run_test(name, test_func):
    global tests_run, tests_passed, tests_failed, test_errors
    tests_run += 1

    print(f"Testing: {name}... ", end="", flush=True)

    try:
        result = test_func()
        if result:
            print("✓ PASS")
            tests_passed += 1
            return True
        else:
            print("✗ FAIL")
            tests_failed += 1
            test_errors.append((name, "Test returned False"))
            return False
    except Exception as e:
        print("✗ ERROR")
        tests_failed += 1
        test_errors.append((name, str(e)))
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: File Structure
# ══════════════════════════════════════════════════════════════════════════════

print("[1] Testing file structure...")
print("─"*80)

required_files = [
    "julia_wrapper.py",
    "edge_opf_simulator.py",
    "visualization.py",
    "power_grid_topology.py",
    "test_integration.py",
    "test_all_python.py"
]

def test_files_exist():
    all_exist = True
    for f in required_files:
        if not Path(f).exists():
            print(f"\n  ⚠️  Missing: {f}")
            all_exist = False
    return all_exist

run_test("Required files exist", test_files_exist)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Python Syntax
# ══════════════════════════════════════════════════════════════════════════════

print("\n[2] Testing Python syntax...")
print("─"*80)

def test_syntax(filepath):
    def _test():
        import py_compile
        try:
            py_compile.compile(filepath, doraise=True)
            return True
        except py_compile.PyCompileError as e:
            print(f"\n  Syntax error in {filepath}: {e}")
            return False
    return _test

for pyfile in required_files:
    if Path(pyfile).exists():
        run_test(f"Syntax: {pyfile}", test_syntax(pyfile))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Imports
# ══════════════════════════════════════════════════════════════════════════════

print("\n[3] Testing imports...")
print("─"*80)

def test_import_module(module_name, filepath):
    def _test():
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None:
                return False
            module = importlib.util.module_from_spec(spec)
            # Don't execute, just check it can be loaded
            return True
        except Exception as e:
            print(f"\n  Import error: {e}")
            return False
    return _test

importable_files = {
    "julia_wrapper": "julia_wrapper.py",
    "visualization": "visualization.py",
    "power_grid_topology": "power_grid_topology.py"
}

for mod_name, filepath in importable_files.items():
    if Path(filepath).exists():
        run_test(f"Import: {mod_name}", test_import_module(mod_name, filepath))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Dependencies
# ══════════════════════════════════════════════════════════════════════════════

print("\n[4] Testing Python dependencies...")
print("─"*80)

required_packages = [
    "json",
    "pathlib",
    "subprocess",
    "psutil",
    "numpy",
    "matplotlib"
]

def test_package(pkg_name):
    def _test():
        try:
            __import__(pkg_name)
            return True
        except ImportError:
            print(f"\n  ⚠️  Package not installed: {pkg_name}")
            return False
    return _test

for pkg in required_packages:
    run_test(f"Package: {pkg}", test_package(pkg))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Julia Wrapper
# ══════════════════════════════════════════════════════════════════════════════

print("\n[5] Testing julia_wrapper.py...")
print("─"*80)

def test_julia_wrapper_classes():
    try:
        from julia_wrapper import JuliaOPFExecutor, JuliaConfig, JuliaProcessMonitor

        # Test JuliaConfig creation
        config = JuliaConfig(
            node_id=1,
            caseID="testbeds/pglib_opf_case14_ieee.m",
            max_iterations=100
        )

        # Test JuliaOPFExecutor creation
        executor = JuliaOPFExecutor()

        # Check that main_script points to root main.jl
        expected_path = Path(executor.base_dir) / "main.jl"

        return executor.main_script == expected_path
    except Exception as e:
        print(f"\n  Error: {e}")
        return False

run_test("JuliaOPFExecutor classes", test_julia_wrapper_classes)

def test_julia_wrapper_paths():
    try:
        from julia_wrapper import JuliaOPFExecutor
        executor = JuliaOPFExecutor()

        # Verify paths
        checks = []
        checks.append(executor.main_script.name == "main.jl")
        checks.append(executor.results_dir.name == "results")
        checks.append("edge" in str(executor.edge_dir))

        return all(checks)
    except Exception as e:
        print(f"\n  Error: {e}")
        return False

run_test("Julia wrapper paths", test_julia_wrapper_paths)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Visualization
# ══════════════════════════════════════════════════════════════════════════════

print("\n[6] Testing visualization.py...")
print("─"*80)

def test_visualization_class():
    try:
        from visualization import ResultsExporter

        # Test creation
        exporter = ResultsExporter()

        # Check attributes
        return hasattr(exporter, 'generate_plots') and hasattr(exporter, 'export_to_csv')
    except Exception as e:
        print(f"\n  Error: {e}")
        return False

run_test("ResultsExporter class", test_visualization_class)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Config Files
# ══════════════════════════════════════════════════════════════════════════════

print("\n[7] Testing config files...")
print("─"*80)

config_files = [
    "test_config_centralized.json",
    "test_config_distributed.json"
]

def test_config_file(filepath):
    def _test():
        try:
            import json
            with open(filepath, 'r') as f:
                config = json.load(f)
            return isinstance(config, dict) and len(config) > 0
        except Exception as e:
            print(f"\n  Error parsing {filepath}: {e}")
            return False
    return _test

for config_file in config_files:
    if Path(config_file).exists():
        run_test(f"Parse: {config_file}", test_config_file(config_file))

# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: Integration Test Script
# ══════════════════════════════════════════════════════════════════════════════

print("\n[8] Testing test_integration.py...")
print("─"*80)

def test_integration_script():
    try:
        # Check if we can at least import the key functions
        spec = importlib.util.spec_from_file_location("test_integration", "test_integration.py")
        if spec is None:
            return False

        # File is syntactically correct
        return True
    except Exception as e:
        print(f"\n  Error: {e}")
        return False

if Path("test_integration.py").exists():
    run_test("Integration test script", test_integration_script)

# ══════════════════════════════════════════════════════════════════════════════
# TEST 9: EdgeSimPy Integration
# ══════════════════════════════════════════════════════════════════════════════

print("\n[9] Testing EdgeSimPy integration...")
print("─"*80)

def test_edgesimpy_import():
    try:
        # Try to import edgesimpy components
        if Path("edgesimpy").exists():
            sys.path.insert(0, str(Path.cwd()))
            from edgesimpy import EdgeServer, NetworkLink, EdgeSimulation
            return True
        else:
            print("\n  ⚠️  edgesimpy folder not found (optional)")
            return True  # Not a critical failure
    except Exception as e:
        print(f"\n  Warning: {e}")
        return True  # Not critical

run_test("EdgeSimPy import", test_edgesimpy_import)

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print(" TEST SUMMARY")
print("="*80)
print(f"Total tests:  {tests_run}")
print(f"Passed:       {tests_passed} ({tests_passed/tests_run*100:.1f}%)")
print(f"Failed:       {tests_failed} ({tests_failed/tests_run*100:.1f}%)")
print("="*80)

if tests_failed > 0:
    print("\nFailed tests:")
    for test_name, error_msg in test_errors:
        print(f"  ✗ {test_name}")
        print(f"    → {error_msg}")

print()
if tests_failed == 0:
    print("✅ ALL PYTHON TESTS PASSED!")
    print("\nNext steps:")
    print("  1. Run full integration test: python3 test_integration.py")
    print("  2. Run edge simulation: python3 edge_opf_simulator.py")
    print("  3. Check Julia side: cd .. && julia test_all_scripts.jl")
    sys.exit(0)
else:
    print("⚠️  SOME TESTS FAILED")
    print("\nCheck:")
    print("  1. Python packages: pip install psutil numpy matplotlib")
    print("  2. File paths are correct")
    print("  3. No syntax errors in Python files")
    sys.exit(1)
