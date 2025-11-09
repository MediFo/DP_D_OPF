#!/usr/bin/env python3
"""
Test script to verify edge simulation integration with root main.jl
"""

import sys
from pathlib import Path
from julia_wrapper import JuliaOPFExecutor, JuliaConfig

def test_centralized():
    """Test centralized OPF execution using root main.jl"""
    print("="*60)
    print("Testing Centralized OPF (calls root main.jl)")
    print("="*60)

    executor = JuliaOPFExecutor()

    # Verify main script path
    print(f"Base directory: {executor.base_dir}")
    print(f"Main script: {executor.main_script}")
    print(f"Main script exists: {executor.main_script.exists()}")

    if not executor.main_script.exists():
        print(f"❌ ERROR: main.jl not found at {executor.main_script}")
        return False

    config = {
        "caseID": "testbeds/pglib_opf_case14_ieee.m",
        "max_iterations": 100,  # Short test
        "rho": 1e3,
        "tolerance": 1e-2,
        "epsilon": 1.0,
        "alpha": 0.1,
        "method": "PVP"
    }

    try:
        result = executor.run_centralized(config)

        print(f"\nSuccess: {result['success']}")
        print(f"Return code: {result['return_code']}")
        print(f"Execution time: {result['execution_time_s']:.2f}s")

        if result['success']:
            print("✓ Centralized OPF completed successfully")

            # Check results
            if 'resource_monitoring' in result and result['resource_monitoring']:
                stats = result['resource_monitoring']
                print(f"  Avg CPU: {stats.get('avg_cpu_percent', 0):.1f}%")
                print(f"  Max Memory: {stats.get('max_memory_mb', 0):.1f}MB")

            if 'julia_results' in result and result['julia_results']:
                jresults = result['julia_results']
                print(f"  Iterations: {jresults.get('iterations', 'N/A')}")
                print(f"  Final cost: {jresults.get('final_cost', 'N/A')}")
        else:
            print("✗ Centralized OPF failed")
            print(f"  Error: {result.get('error', 'Unknown')}")
            if 'stderr' in result and result['stderr']:
                print(f"  STDERR:\n{result['stderr'][:500]}")

        return result['success']

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_distributed():
    """Test distributed OPF execution using root main.jl"""
    print("\n" + "="*60)
    print("Testing Distributed OPF (calls root main.jl)")
    print("="*60)

    executor = JuliaOPFExecutor()

    config = JuliaConfig(
        node_id=1,
        caseID="testbeds/pglib_opf_case14_ieee.m",
        max_iterations=100,  # Short test
        rho=1e3,
        tolerance=1e-2,
        epsilon=1.0,
        alpha=0.1,
        method="PVP"
    )

    try:
        result = executor.run_distributed_node(node_id=1, config=config)

        print(f"\nSuccess: {result['success']}")
        print(f"Return code: {result['return_code']}")
        print(f"Execution time: {result['execution_time_s']:.2f}s")

        if result['success']:
            print("✓ Distributed OPF (Node 1) completed successfully")

            # Check results
            if 'resource_monitoring' in result and result['resource_monitoring']:
                stats = result['resource_monitoring']
                print(f"  Avg CPU: {stats.get('avg_cpu_percent', 0):.1f}%")
                print(f"  Max Memory: {stats.get('max_memory_mb', 0):.1f}MB")

            if 'julia_results' in result and result['julia_results']:
                jresults = result['julia_results']
                print(f"  Node ID: {jresults.get('node_id', 'N/A')}")
                print(f"  Iterations: {jresults.get('iterations', 'N/A')}")
                print(f"  Final cost: {jresults.get('final_cost', 'N/A')}")
        else:
            print("✗ Distributed OPF failed")
            print(f"  Error: {result.get('error', 'Unknown')}")
            if 'stderr' in result and result['stderr']:
                print(f"  STDERR:\n{result['stderr'][:500]}")

        return result['success']

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_structure():
    """Verify the file structure is correct"""
    print("="*60)
    print("Verifying File Structure")
    print("="*60)

    base_dir = Path(__file__).parent.parent

    files_to_check = [
        base_dir / "main.jl",
        base_dir / "scripts" / "data_manager.jl",
        base_dir / "scripts" / "fun_centralized_OPF.jl",
        base_dir / "scripts" / "fun_voltage_update.jl",
        base_dir / "testbeds" / "pglib_opf_case14_ieee.m",
        base_dir / "edge" / "julia_wrapper.py",
    ]

    all_exist = True
    for f in files_to_check:
        exists = f.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {f.relative_to(base_dir)}")
        if not exists:
            all_exist = False

    return all_exist


if __name__ == "__main__":
    print("\nEdge Simulation Integration Test")
    print("This test verifies that edge_opf_simulator.py correctly calls root main.jl\n")

    # Verify structure
    structure_ok = verify_structure()

    if not structure_ok:
        print("\n❌ File structure verification failed!")
        sys.exit(1)

    print("\n✓ File structure verified")

    # Check if Julia is available
    import shutil
    if shutil.which("julia") is None:
        print("\n⚠️  Julia not found in PATH")
        print("Skipping execution tests (structure verification passed)")
        print("\nTo run full tests, ensure:")
        print("  1. Julia is installed")
        print("  2. Gurobi is installed with valid license")
        print("  3. Required Julia packages are installed")
        sys.exit(0)

    # Run tests
    print("\n" + "="*60)
    print("Running Execution Tests")
    print("="*60)

    success_centralized = test_centralized()
    success_distributed = test_distributed()

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Centralized: {'✓ PASS' if success_centralized else '✗ FAIL'}")
    print(f"Distributed: {'✓ PASS' if success_distributed else '✗ FAIL'}")

    if success_centralized and success_distributed:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
