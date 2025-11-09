#!/usr/bin/env python3
"""
Solver Switcher Utility
Helps switch between HiGHS (free) and Gurobi (commercial) solvers
"""

import sys
import re
from pathlib import Path


def switch_solver(solver_name):
    """
    Switch the solver in Julia scripts

    Args:
        solver_name: 'highs' or 'gurobi'
    """
    solver_name = solver_name.lower()

    if solver_name not in ['highs', 'gurobi']:
        print(f"Error: Unknown solver '{solver_name}'")
        print("Valid options: 'highs' or 'gurobi'")
        return False

    # Files to modify
    project_root = Path(__file__).parent.parent
    files_to_modify = [
        project_root / "scripts" / "fun_centralized_OPF.jl",
        project_root / "scripts" / "fun_voltage_update.jl",
        project_root / "main.jl"
    ]

    print("="*80)
    print(f"Switching to {solver_name.upper()} solver")
    print("="*80)
    print()

    for filepath in files_to_modify:
        if not filepath.exists():
            print(f"⚠ Warning: {filepath} not found, skipping")
            continue

        print(f"Modifying {filepath.name}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if solver_name == 'highs':
                # Switch to HiGHS
                # Uncomment HiGHS lines
                content = re.sub(r'^# (using HiGHS)', r'\1', content, flags=re.MULTILINE)
                content = re.sub(r'^# (const SOLVER.*HiGHS)', r'\1', content, flags=re.MULTILINE)

                # Comment Gurobi lines
                content = re.sub(r'^(using Gurobi)(?!.*#)', r'# \1', content, flags=re.MULTILINE)
                content = re.sub(r'^(const SOLVER.*Gurobi)(?!.*#)', r'# \1', content, flags=re.MULTILINE)
                content = re.sub(r'^(gurobi_env.*)', r'# \1', content, flags=re.MULTILINE)

            else:  # gurobi
                # Switch to Gurobi
                # Comment HiGHS lines
                content = re.sub(r'^(using HiGHS)(?!.*#)', r'# \1', content, flags=re.MULTILINE)
                content = re.sub(r'^(const SOLVER.*HiGHS)(?!.*#)', r'# \1', content, flags=re.MULTILINE)

                # Uncomment Gurobi lines
                content = re.sub(r'^# (using Gurobi)', r'\1', content, flags=re.MULTILINE)
                content = re.sub(r'^# (const SOLVER.*Gurobi)', r'\1', content, flags=re.MULTILINE)
                content = re.sub(r'^# (gurobi_env.*)', r'\1', content, flags=re.MULTILINE)

            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  ✓ Updated {filepath.name}")

        except Exception as e:
            print(f"  ✗ Error modifying {filepath.name}: {e}")
            return False

    print()
    print("="*80)
    print(f"✓ Successfully switched to {solver_name.upper()}")
    print("="*80)
    print()

    if solver_name == 'highs':
        print("Using HiGHS (FREE, open-source) solver")
        print()
        print("Make sure HiGHS is installed:")
        print("  julia -e 'using Pkg; Pkg.add(\"HiGHS\")'")
    else:
        print("Using Gurobi (commercial) solver")
        print()
        print("Make sure:")
        print("  1. Gurobi is installed")
        print("  2. Gurobi is in your PATH")
        print("  3. You have a valid Gurobi license")
        print()
        print("Install Gurobi.jl:")
        print("  julia -e 'using Pkg; Pkg.add(\"Gurobi\")'")

    print()
    print("Test the solver:")
    print("  julia main.jl")
    print()

    return True


def check_current_solver():
    """Check which solver is currently configured"""
    project_root = Path(__file__).parent.parent
    filepath = project_root / "scripts" / "fun_centralized_OPF.jl"

    if not filepath.exists():
        print("Error: Could not find fun_centralized_OPF.jl")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check which solver is active (not commented)
    highs_active = bool(re.search(r'^using HiGHS(?!.*#)', content, re.MULTILINE))
    gurobi_active = bool(re.search(r'^using Gurobi(?!.*#)', content, re.MULTILINE))

    print("="*80)
    print("Current Solver Configuration")
    print("="*80)
    print()

    if highs_active:
        print("✓ Currently using: HiGHS (FREE)")
    elif gurobi_active:
        print("✓ Currently using: Gurobi (commercial)")
    else:
        print("⚠ Warning: No solver appears to be active")

    print()
    print("To switch solvers:")
    print("  python switch_solver.py highs")
    print("  python switch_solver.py gurobi")
    print()


def main():
    if len(sys.argv) < 2:
        print("="*80)
        print("Solver Switcher Utility")
        print("="*80)
        print()
        print("Usage:")
        print("  python switch_solver.py [highs|gurobi|check]")
        print()
        print("Examples:")
        print("  python switch_solver.py highs    # Switch to HiGHS (free)")
        print("  python switch_solver.py gurobi   # Switch to Gurobi (commercial)")
        print("  python switch_solver.py check    # Check current solver")
        print()
        check_current_solver()
        return

    command = sys.argv[1].lower()

    if command == 'check':
        check_current_solver()
    elif command in ['highs', 'gurobi']:
        if switch_solver(command):
            print("✓ Solver switch completed successfully!")
        else:
            print("✗ Solver switch failed")
            sys.exit(1)
    else:
        print(f"Error: Unknown command '{command}'")
        print("Valid commands: highs, gurobi, check")
        sys.exit(1)


if __name__ == "__main__":
    main()
