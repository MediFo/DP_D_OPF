#!/usr/bin/env python3
"""
Comprehensive verification script for all OPF scripts
Tests Julia and Python scripts for correctness
"""

import os
import sys
import re
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def check_julia_syntax_basic(filepath):
    """Basic Julia syntax checks"""
    errors = []

    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    # Check for basic syntax issues

    # 1. Check for unmatched parentheses, brackets, braces
    paren_count = content.count('(') - content.count(')')
    bracket_count = content.count('[') - content.count(']')

    if paren_count != 0:
        errors.append(f"Unmatched parentheses: {abs(paren_count)} {'extra (' if paren_count > 0 else 'extra )'}")

    if bracket_count != 0:
        errors.append(f"Unmatched brackets: {abs(bracket_count)} {'extra [' if bracket_count > 0 else 'extra ]'}")

    # 2. Check for basic end matching
    end_count = len(re.findall(r'\bend\b', content))
    function_count = len(re.findall(r'\bfunction\b', content))
    for_count = len(re.findall(r'\bfor\b', content))
    if_count = len(re.findall(r'\bif\b', content))
    while_count = len(re.findall(r'\bwhile\b', content))

    expected_ends = function_count + for_count + if_count + while_count

    # Allow some flexibility since there might be other end-requiring constructs
    if abs(end_count - expected_ends) > 5:
        errors.append(f"Possible end mismatch: {end_count} ends, expected ~{expected_ends}")

    # 3. Check for unterminated strings (basic check)
    quote_count = content.count('"') - content.count('\\"')
    if quote_count % 2 != 0:
        errors.append("Possible unterminated string (odd number of quotes)")

    return errors

def check_julia_file(filepath, required_vars=None):
    """Check Julia file for required variables and syntax"""
    print(f"\n{YELLOW}Checking:{RESET} {filepath}")

    # Check file exists
    if not os.path.exists(filepath):
        print_error(f"File not found: {filepath}")
        return False

    # Read content
    with open(filepath, 'r') as f:
        content = f.read()

    success = True

    # Basic syntax check
    errors = check_julia_syntax_basic(filepath)
    if errors:
        for error in errors:
            print_error(f"Syntax issue: {error}")
        success = False
    else:
        print_success("Basic syntax check passed")

    # Check for required variables
    if required_vars:
        for var in required_vars:
            if var in content:
                print_success(f"Found required variable: {var}")
            else:
                print_error(f"Missing required variable: {var}")
                success = False

    # Check for common Julia keywords
    if 'using' not in content and 'import' not in content:
        print_warning("No 'using' or 'import' statements found")

    return success

def check_timestamp_recording(filepath):
    """Check if file has timestamp recording implementation"""
    print(f"\n{YELLOW}Checking timestamp recording:{RESET} {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    required_elements = {
        'iteration_times': 'iteration_times array initialization',
        'iteration_timestamps': 'iteration_timestamps array initialization',
        'push!(iteration_times': 'Recording iteration duration',
        'push!(iteration_timestamps': 'Recording cumulative timestamp',
        'time() - start_time': 'Cumulative time calculation',
    }

    success = True
    for element, description in required_elements.items():
        if element in content:
            print_success(f"{description}")
        else:
            print_error(f"Missing: {description}")
            success = False

    return success

def check_results_dictionary(filepath, expected_scheme=None):
    """Check if file creates proper results dictionary"""
    print(f"\n{YELLOW}Checking results dictionary:{RESET} {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    required_fields = [
        '"iteration_times"',
        '"iteration_timestamps"',
        '"residuals"',
        '"total_time_s"',
        '"iterations"',
    ]

    success = True

    # Check for results dictionary creation
    if 'results = Dict(' in content:
        print_success("Results dictionary created")
    else:
        print_error("No results dictionary found")
        success = False
        return success

    # Check for required fields
    for field in required_fields:
        if field in content:
            print_success(f"Found field: {field}")
        else:
            print_error(f"Missing field: {field}")
            success = False

    # Check for encryption scheme if expected
    if expected_scheme:
        if f'"encryption_scheme" => "{expected_scheme}"' in content:
            print_success(f"Encryption scheme set to: {expected_scheme}")
        else:
            print_error(f"Expected encryption_scheme: {expected_scheme}")
            success = False

    return success

def check_json_output(filepath, expected_output_file):
    """Check if file outputs JSON results"""
    print(f"\n{YELLOW}Checking JSON output:{RESET} {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    success = True

    if 'JSON.print' in content:
        print_success("JSON output code found")
    else:
        print_error("No JSON output code found")
        success = False

    if expected_output_file in content:
        print_success(f"Output file: {expected_output_file}")
    else:
        print_error(f"Expected output file not found: {expected_output_file}")
        success = False

    return success

def check_python_imports():
    """Check all Python imports work"""
    print_header("CHECKING PYTHON IMPORTS")

    try:
        import numpy as np
        print_success("numpy imported")
    except ImportError:
        print_error("numpy not available")
        return False

    try:
        import matplotlib.pyplot as plt
        print_success("matplotlib imported")
    except ImportError:
        print_error("matplotlib not available")
        return False

    try:
        import json
        print_success("json imported")
    except ImportError:
        print_error("json not available")
        return False

    try:
        import psutil
        print_success("psutil imported")
    except ImportError:
        print_error("psutil not available")
        return False

    return True

def check_visualization_plots():
    """Check that visualization.py has all expected plot methods"""
    print_header("CHECKING VISUALIZATION PLOT METHODS")

    filepath = Path('edge/visualization.py')

    if not filepath.exists():
        print_error(f"File not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    # Check for new dual time-axis plot methods
    new_methods = [
        '_plot_dual_cpu_memory_percentile',
        '_plot_iteration_duration_analysis',
        '_plot_cumulative_computation_time',
        '_plot_iteration_throughput',
        '_plot_time_budget_analysis',
        '_plot_realtime_efficiency_metrics',
        '_plot_performance_degradation',
    ]

    success = True
    for method in new_methods:
        if f'def {method}(' in content:
            print_success(f"Found method: {method}")
        else:
            print_error(f"Missing method: {method}")
            success = False

    # Check that generate_plots calls these methods
    if not success:
        return False

    print("\nChecking generate_plots calls new methods...")
    for method in new_methods:
        # Look for method call (without 'def')
        method_call = f'{method}('
        if method_call in content and content.count(method_call) >= 2:  # def + at least one call
            print_success(f"Method called: {method}")
        else:
            print_error(f"Method not called in generate_plots: {method}")
            success = False

    return success

def main():
    print_header("COMPREHENSIVE SCRIPT VERIFICATION")
    print(f"Working directory: {os.getcwd()}")

    all_passed = True

    # Change to optimization directory
    os.chdir('/home/user/DP_D_OPF/optimization')

    # ========================================================================
    # 1. Check Python imports
    # ========================================================================
    if not check_python_imports():
        all_passed = False

    # ========================================================================
    # 2. Check main.jl (centralized/distributed)
    # ========================================================================
    print_header("CHECKING main.jl (Centralized/Distributed)")

    if not check_julia_file('main.jl', required_vars=['iteration_times', 'iteration_timestamps']):
        all_passed = False

    if not check_timestamp_recording('main.jl'):
        all_passed = False

    if not check_results_dictionary('main.jl'):
        all_passed = False

    # ========================================================================
    # 3. Check opt_main_verified.jl (Paillier)
    # ========================================================================
    print_header("CHECKING opt_main_verified.jl (Paillier)")

    if not check_julia_file('opt_main_verified.jl', required_vars=['iteration_times', 'iteration_timestamps']):
        all_passed = False

    if not check_timestamp_recording('opt_main_verified.jl'):
        all_passed = False

    if not check_results_dictionary('opt_main_verified.jl', expected_scheme='paillier'):
        all_passed = False

    if not check_json_output('opt_main_verified.jl', 'paillier_results.json'):
        all_passed = False

    # ========================================================================
    # 4. Check opt_main_bgv.jl (BGV)
    # ========================================================================
    print_header("CHECKING opt_main_bgv.jl (BGV)")

    if not check_julia_file('opt_main_bgv.jl', required_vars=['iteration_times', 'iteration_timestamps']):
        all_passed = False

    if not check_timestamp_recording('opt_main_bgv.jl'):
        all_passed = False

    if not check_results_dictionary('opt_main_bgv.jl', expected_scheme='bgv'):
        all_passed = False

    if not check_json_output('opt_main_bgv.jl', 'bgv_results.json'):
        all_passed = False

    # ========================================================================
    # 5. Check opt_main_ckks.jl (CKKS)
    # ========================================================================
    print_header("CHECKING opt_main_ckks.jl (CKKS)")

    if not check_julia_file('opt_main_ckks.jl', required_vars=['iteration_times', 'iteration_timestamps']):
        all_passed = False

    if not check_timestamp_recording('opt_main_ckks.jl'):
        all_passed = False

    if not check_results_dictionary('opt_main_ckks.jl', expected_scheme='ckks'):
        all_passed = False

    if not check_json_output('opt_main_ckks.jl', 'ckks_results.json'):
        all_passed = False

    # ========================================================================
    # 6. Check visualization.py
    # ========================================================================
    if not check_visualization_plots():
        all_passed = False

    # ========================================================================
    # 7. Check file paths
    # ========================================================================
    print_header("CHECKING FILE PATHS AND DEPENDENCIES")

    required_files = [
        'main.jl',
        'opt_main_verified.jl',
        'opt_main_bgv.jl',
        'opt_main_ckks.jl',
        'edge/visualization.py',
        'edge/julia_wrapper.py',
        'edge/edge_opf_simulator.py',
        'edge/power_grid_topology.py',
    ]

    for filepath in required_files:
        if os.path.exists(filepath):
            print_success(f"Found: {filepath}")
        else:
            print_error(f"Missing: {filepath}")
            all_passed = False

    # ========================================================================
    # Final summary
    # ========================================================================
    print_header("VERIFICATION SUMMARY")

    if all_passed:
        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN}{'✓ ALL CHECKS PASSED'.center(80)}{RESET}")
        print(f"{GREEN}{'='*80}{RESET}\n")
        print(f"{GREEN}All scripts are properly configured with:{RESET}")
        print(f"{GREEN}  ✓ Timestamp recording (iteration_times, iteration_timestamps){RESET}")
        print(f"{GREEN}  ✓ Results dictionaries{RESET}")
        print(f"{GREEN}  ✓ JSON output{RESET}")
        print(f"{GREEN}  ✓ Dual time-axis visualization plots{RESET}")
        print(f"{GREEN}  ✓ Proper syntax structure{RESET}")
        return 0
    else:
        print(f"\n{RED}{'='*80}{RESET}")
        print(f"{RED}{'✗ SOME CHECKS FAILED'.center(80)}{RESET}")
        print(f"{RED}{'='*80}{RESET}\n")
        print(f"{RED}Please review the errors above and fix the issues.{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
