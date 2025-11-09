#!/usr/bin/env python3
"""
Edge OPF Evaluation - Command Line Interface

Easy-to-use CLI for running OPF simulations in different modes:
- Centralized (single node)
- Distributed (multiple nodes)
- Encrypted: Paillier, BGV, CKKS

Usage Examples:
  # Distributed mode with 14 servers
  python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m

  # Centralized mode
  python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m

  # Paillier encryption
  python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m

  # BGV encryption
  python evaluate_edge_opf.py --mode bgv --case testbeds/pglib_opf_case14_ieee.m

  # CKKS encryption
  python evaluate_edge_opf.py --mode ckks --case testbeds/pglib_opf_case14_ieee.m
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add edge module to path
sys.path.insert(0, str(Path(__file__).parent / 'edge'))

from edge_opf_simulator import EdgeOPFSimulator
from julia_wrapper import JuliaOPFExecutor
from visualization import ResultsExporter


def create_config(args):
    """Create configuration dictionary from command-line arguments"""

    # Base OPF configuration
    opf_config = {
        "caseID": args.case,
        "max_iterations": args.max_iter,
        "rho": args.rho,
        "tolerance": args.tolerance,
        "epsilon": args.epsilon,
        "alpha": args.alpha,
        "method": args.privacy_method,
    }

    # Determine mode and encryption scheme
    mode = args.mode.lower()

    # Map mode names to config values
    mode_mapping = {
        'centralized': ('centralized', 'none'),
        'distributed': ('distributed', 'none'),
        'paillier': ('encrypted', 'paillier'),
        'bgv': ('encrypted', 'bgv'),
        'ckks': ('encrypted', 'ckks'),
    }

    if mode not in mode_mapping:
        raise ValueError(f"Unknown mode: {mode}. Choose from: {list(mode_mapping.keys())}")

    opf_mode, encryption_scheme = mode_mapping[mode]
    opf_config['mode'] = opf_mode
    opf_config['encryption_scheme'] = encryption_scheme

    # For distributed mode, create edge simulation config
    if opf_mode == 'distributed':
        config = {
            "simulation_name": f"Edge_OPF_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": f"{mode} mode evaluation",

            "edge_infrastructure": {
                "num_servers": args.servers,
                "server_specs": {
                    "cpu_cores": args.cpu_cores,
                    "cpu_freq_ghz": args.cpu_freq,
                    "memory_gb": args.memory,
                    "storage_gb": args.storage,
                    "power_idle_w": args.power_idle,
                    "power_max_w": args.power_max,
                },
                "network": {
                    "bandwidth_mbps": args.bandwidth,
                    "latency_ms": args.latency,
                    "packet_loss_rate": args.packet_loss,
                }
            },

            "opf_config": opf_config,

            "execution": {
                "mode": "distributed",
                "parallel": args.parallel,
                "export_csv": args.export_csv,
                "generate_plots": args.generate_plots,
            },

            "output": {
                "results_dir": args.output_dir,
                "plots_dir": args.plots_dir,
                "timestamp_format": "%Y%m%d_%H%M%S",
            }
        }
    else:
        # For centralized or encrypted modes, simpler config
        config = opf_config
        config['output_dir'] = args.output_dir
        config['plots_dir'] = args.plots_dir
        config['generate_plots'] = args.generate_plots
        config['export_csv'] = args.export_csv

    return config, opf_mode, encryption_scheme


def run_centralized(config):
    """Run centralized OPF"""
    print("\n" + "="*80)
    print("RUNNING CENTRALIZED OPF")
    print("="*80 + "\n")

    executor = JuliaOPFExecutor()
    result = executor.run_centralized(config)

    if result['success']:
        print("\n✓ Centralized OPF completed successfully")
        print(f"  Execution time: {result['execution_time_s']:.2f}s")

        if 'julia_results' in result and result['julia_results']:
            jr = result['julia_results']
            print(f"  Iterations: {jr.get('iterations', 'N/A')}")
            print(f"  Final cost: ${jr.get('final_cost', 'N/A'):.2f}")
            print(f"  Optimality loss: {jr.get('optimality_loss_percent', 'N/A'):.4f}%")
    else:
        print("\n✗ Centralized OPF failed")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        return False

    return result


def run_distributed(config):
    """Run distributed OPF on edge infrastructure"""
    print("\n" + "="*80)
    print("RUNNING DISTRIBUTED OPF ON EDGE INFRASTRUCTURE")
    print("="*80 + "\n")

    simulator = EdgeOPFSimulator(config)
    results = simulator.run()

    print(f"\n✓ Distributed simulation completed")
    print(f"  Total nodes: {len(results.get('node_results', []))}")

    return results


def run_encrypted(config, scheme):
    """Run encrypted OPF (Paillier, BGV, or CKKS)"""
    print("\n" + "="*80)
    print(f"RUNNING {scheme.upper()} ENCRYPTED OPF")
    print("="*80 + "\n")

    print(f"⚠️  Note: {scheme.upper()} encryption adds significant overhead")
    print(f"⚠️  Expected overhead: ", end="")

    if scheme == 'paillier':
        print("~10x slower than non-encrypted")
    elif scheme == 'bgv':
        print("~300x slower than Paillier (~3000x vs non-encrypted)")
    elif scheme == 'ckks':
        print("~300x slower than Paillier (~3000x vs non-encrypted)")

    print()

    # Change to optimization directory to run Julia scripts
    original_dir = os.getcwd()
    opt_dir = Path(__file__).parent
    os.chdir(opt_dir)

    try:
        import subprocess

        # Map scheme to Julia script
        script_map = {
            'paillier': 'opt_main_verified.jl',
            'bgv': 'opt_main_bgv.jl',
            'ckks': 'opt_main_ckks.jl',
        }

        script = script_map[scheme]

        print(f"Running Julia script: {script}")
        print("-" * 80 + "\n")

        # Run Julia script
        result = subprocess.run(
            ['julia', script],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Check for results JSON
        results_file = f"results/{scheme}_results.json"
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                julia_results = json.load(f)

            print("\n" + "="*80)
            print(f"✓ {scheme.upper()} ENCRYPTION COMPLETED")
            print("="*80)
            print(f"  Total time: {julia_results.get('total_time_s', 'N/A'):.2f}s")
            print(f"  Iterations: {julia_results.get('iterations', 'N/A')}")
            print(f"  Final cost: ${julia_results.get('final_cost', 'N/A'):.2f}")
            print(f"  Optimality loss: {julia_results.get('optimality_loss_percent', 'N/A'):.4f}%")
            print(f"  Converged: {julia_results.get('converged', 'N/A')}")

            if 'pct_crypto' in julia_results:
                print(f"\n  Timing breakdown:")
                print(f"    Optimization: {julia_results.get('pct_opt', 'N/A'):.1f}%")
                print(f"    Cryptography: {julia_results.get('pct_crypto', 'N/A'):.1f}%")
                print(f"    Other: {julia_results.get('pct_other', 'N/A'):.1f}%")

            return julia_results
        else:
            print(f"\n⚠️  Results file not found: {results_file}")
            return {'success': result.returncode == 0}

    finally:
        os.chdir(original_dir)


def generate_visualizations(results, mode, output_dir, plots_dir):
    """Generate visualization plots"""
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80 + "\n")

    # Create output directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(plots_dir).mkdir(parents=True, exist_ok=True)

    # Initialize exporter
    exporter = ResultsExporter(output_dir=output_dir)

    # Generate plots based on mode
    if mode == 'distributed':
        exporter.generate_plots(results, prefix=f"{mode}")
    else:
        # For centralized/encrypted, we need to format results properly
        # This would need to be wrapped in the expected format
        print("  Note: Visualization for centralized/encrypted modes")
        print("  uses results JSON files directly")

    print(f"\n✓ Plots saved to: {plots_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Edge OPF Evaluation - Run OPF in different modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Distributed mode with 14 servers
  %(prog)s --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m

  # Centralized mode
  %(prog)s --mode centralized --case testbeds/pglib_opf_case14_ieee.m

  # Paillier encryption
  %(prog)s --mode paillier --case testbeds/pglib_opf_case14_ieee.m

  # BGV encryption (very slow!)
  %(prog)s --mode bgv --case testbeds/pglib_opf_case14_ieee.m --max-iter 100

  # CKKS encryption (very slow!)
  %(prog)s --mode ckks --case testbeds/pglib_opf_case14_ieee.m --max-iter 100

Available modes:
  centralized - Single node, no encryption
  distributed - Multiple edge servers, no encryption
  paillier    - Paillier homomorphic encryption (~10x overhead)
  bgv         - BGV/BFV full homomorphic encryption (~3000x overhead)
  ckks        - CKKS full homomorphic encryption (~3000x overhead)
        """
    )

    # Required arguments
    parser.add_argument('--mode', required=True,
                        choices=['centralized', 'distributed', 'paillier', 'bgv', 'ckks'],
                        help='Execution mode')

    parser.add_argument('--case', required=True,
                        help='Power grid test case file (e.g., testbeds/pglib_opf_case14_ieee.m)')

    # Edge infrastructure (for distributed mode)
    parser.add_argument('--servers', type=int, default=3,
                        help='Number of edge servers (distributed mode only, default: 3)')

    parser.add_argument('--cpu-cores', type=int, default=4,
                        help='CPU cores per server (default: 4)')

    parser.add_argument('--cpu-freq', type=float, default=2.4,
                        help='CPU frequency in GHz (default: 2.4)')

    parser.add_argument('--memory', type=float, default=8.0,
                        help='Memory in GB per server (default: 8.0)')

    parser.add_argument('--storage', type=float, default=100.0,
                        help='Storage in GB per server (default: 100.0)')

    parser.add_argument('--power-idle', type=float, default=50.0,
                        help='Idle power consumption in Watts (default: 50.0)')

    parser.add_argument('--power-max', type=float, default=150.0,
                        help='Max power consumption in Watts (default: 150.0)')

    # Network configuration
    parser.add_argument('--bandwidth', type=float, default=100.0,
                        help='Network bandwidth in Mbps (default: 100.0)')

    parser.add_argument('--latency', type=float, default=10.0,
                        help='Network latency in ms (default: 10.0)')

    parser.add_argument('--packet-loss', type=float, default=0.001,
                        help='Packet loss rate (default: 0.001)')

    # OPF parameters
    parser.add_argument('--max-iter', type=int, default=1000,
                        help='Maximum ADMM iterations (default: 1000)')

    parser.add_argument('--rho', type=float, default=1000.0,
                        help='ADMM penalty parameter (default: 1000.0)')

    parser.add_argument('--tolerance', type=float, default=0.01,
                        help='Convergence tolerance (default: 0.01)')

    parser.add_argument('--epsilon', type=float, default=1.0,
                        help='Differential privacy epsilon (default: 1.0)')

    parser.add_argument('--alpha', type=float, default=0.1,
                        help='Differential privacy alpha (default: 0.1)')

    parser.add_argument('--privacy-method', default='PVP',
                        choices=['PVP', 'DVP'],
                        help='Privacy method: PVP or DVP (default: PVP)')

    # Execution options
    parser.add_argument('--parallel', action='store_true', default=True,
                        help='Run in parallel (distributed mode, default: True)')

    parser.add_argument('--no-parallel', action='store_false', dest='parallel',
                        help='Disable parallel execution')

    parser.add_argument('--generate-plots', action='store_true', default=True,
                        help='Generate visualization plots (default: True)')

    parser.add_argument('--no-plots', action='store_false', dest='generate_plots',
                        help='Skip plot generation')

    parser.add_argument('--export-csv', action='store_true', default=True,
                        help='Export results to CSV (default: True)')

    parser.add_argument('--no-csv', action='store_false', dest='export_csv',
                        help='Skip CSV export')

    # Output directories
    parser.add_argument('--output-dir', default='edge/results',
                        help='Output directory for results (default: edge/results)')

    parser.add_argument('--plots-dir', default='edge/plots',
                        help='Output directory for plots (default: edge/plots)')

    args = parser.parse_args()

    # Print header
    print("\n" + "="*80)
    print("EDGE OPF EVALUATION")
    print("="*80)
    print(f"Mode: {args.mode.upper()}")
    print(f"Case: {args.case}")
    if args.mode == 'distributed':
        print(f"Servers: {args.servers}")
    print(f"Max iterations: {args.max_iter}")
    print("="*80 + "\n")

    # Verify case file exists
    if not os.path.exists(args.case):
        print(f"✗ Error: Case file not found: {args.case}")
        print(f"\nAvailable test cases:")
        testbed_dir = Path('testbeds')
        if testbed_dir.exists():
            for case_file in sorted(testbed_dir.glob('*.m')):
                print(f"  - {case_file}")
        return 1

    # Create configuration
    try:
        config, opf_mode, encryption_scheme = create_config(args)
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return 1

    # Save configuration
    config_file = Path(args.output_dir) / f"config_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Configuration saved to: {config_file}\n")

    # Run simulation based on mode
    try:
        if opf_mode == 'centralized':
            results = run_centralized(config)
        elif opf_mode == 'distributed':
            results = run_distributed(config)
        elif opf_mode == 'encrypted':
            results = run_encrypted(config, encryption_scheme)
        else:
            print(f"✗ Unknown mode: {opf_mode}")
            return 1

        # Generate plots if requested
        if args.generate_plots and results:
            generate_visualizations(results, args.mode, args.output_dir, args.plots_dir)

        print("\n" + "="*80)
        print("✓ EVALUATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nResults directory: {args.output_dir}")
        if args.generate_plots:
            print(f"Plots directory: {args.plots_dir}")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
