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
import logging
from pathlib import Path
from datetime import datetime

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add edge module to path
logger.info("[INIT] Adding edge module to Python path...")
sys.path.insert(0, str(Path(__file__).parent / 'edge'))

# Import modules with error handling
logger.info("[INIT] Importing required modules...")
try:
    from edge_opf_simulator import EdgeOPFSimulator
    logger.info("[INIT]   ✓ EdgeOPFSimulator imported")
except ImportError as e:
    logger.error(f"[INIT]   ✗ Failed to import EdgeOPFSimulator: {e}")
    logger.error("[INIT]   Check that edge/edge_opf_simulator.py exists")
    sys.exit(1)

try:
    from julia_wrapper import JuliaOPFExecutor, JuliaConfig
    logger.info("[INIT]   ✓ JuliaOPFExecutor imported")
except ImportError as e:
    logger.error(f"[INIT]   ✗ Failed to import JuliaOPFExecutor: {e}")
    logger.error("[INIT]   Check that edge/julia_wrapper.py exists")
    sys.exit(1)

try:
    from edgesimpy.edge_server import ServerSpecs
    logger.info("[INIT]   ✓ ServerSpecs imported")
except ImportError as e:
    logger.error(f"[INIT]   ✗ Failed to import ServerSpecs: {e}")
    logger.error("[INIT]   Check that edge/edgesimpy/edge_server.py exists")
    sys.exit(1)

try:
    from visualization import ResultsExporter
    logger.info("[INIT]   ✓ ResultsExporter imported")
except ImportError as e:
    logger.error(f"[INIT]   ✗ Failed to import ResultsExporter: {e}")
    logger.error("[INIT]   Check that edge/visualization.py exists")
    sys.exit(1)


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
    logger.info("\n" + "="*80)
    logger.info("RUNNING CENTRALIZED OPF")
    logger.info("="*80 + "\n")

    try:
        logger.info("[CENT] Step 1: Creating JuliaOPFExecutor...")
        executor = JuliaOPFExecutor()
        logger.info("[CENT]   ✓ JuliaOPFExecutor created")

        logger.info("[CENT] Step 2: Running centralized OPF...")
        logger.info(f"[CENT]   Case: {config.get('caseID', 'N/A')}")
        logger.info(f"[CENT]   Max iterations: {config.get('max_iterations', 'N/A')}")
        logger.info(f"[CENT]   Privacy method: {config.get('method', 'N/A')}")
        logger.info(f"[CENT]   Epsilon: {config.get('epsilon', 'N/A')}")

        result = executor.run_centralized(config)

        if result['success']:
            logger.info("\n[CENT] ✓ Centralized OPF completed successfully")
            logger.info(f"[CENT]   Execution time: {result['execution_time_s']:.2f}s")

            if 'julia_results' in result and result['julia_results']:
                jr = result['julia_results']
                logger.info(f"[CENT]   Iterations: {jr.get('iterations', 'N/A')}")
                logger.info(f"[CENT]   Final cost: ${jr.get('final_cost', 'N/A'):.2f}")
                logger.info(f"[CENT]   Optimality loss: {jr.get('optimality_loss_percent', 'N/A'):.4f}%")

                if jr.get('optimality_loss_percent', 0) > 20.0:
                    logger.warning(f"[CENT]   ⚠️  High optimality loss detected (> 20%)")
                    logger.warning(f"[CENT]   This is expected with differential privacy")
                    logger.warning(f"[CENT]   To reduce: increase --epsilon (less privacy) or decrease --alpha")
        else:
            logger.error("\n[CENT] ✗ Centralized OPF failed")
            logger.error(f"[CENT]   Error: {result.get('error', 'Unknown error')}")
            return False

        return result

    except Exception as e:
        logger.error(f"[CENT] ✗ Unexpected error: {e}")
        logger.error(f"[CENT]   Error type: {type(e).__name__}")
        raise


def run_distributed(config):
    """Run distributed OPF on edge infrastructure"""
    logger.info("\n" + "="*80)
    logger.info("RUNNING DISTRIBUTED OPF ON EDGE INFRASTRUCTURE")
    logger.info("="*80 + "\n")

    try:
        # Create simulator
        logger.info("[DIST] Step 1: Creating EdgeOPFSimulator...")
        simulation_name = config.get('simulation_name', 'Distributed_OPF_Edge_Simulation')
        logger.info(f"[DIST]   Simulation name: {simulation_name}")

        simulator = EdgeOPFSimulator(name=simulation_name)
        logger.info("[DIST]   ✓ EdgeOPFSimulator created successfully")

        # Setup edge infrastructure
        logger.info("[DIST] Step 2: Setting up edge infrastructure...")
        edge_infra = config['edge_infrastructure']
        server_cfg = edge_infra['server_specs']

        logger.info(f"[DIST]   Number of servers: {edge_infra['num_servers']}")
        logger.info(f"[DIST]   Server specs: {server_cfg['cpu_cores']} cores, {server_cfg['memory_gb']} GB RAM")

        # Create ServerSpecs object
        server_specs = ServerSpecs(
            cpu_cores=server_cfg['cpu_cores'],
            cpu_freq_ghz=server_cfg['cpu_freq_ghz'],
            memory_gb=server_cfg['memory_gb'],
            storage_gb=server_cfg['storage_gb'],
            power_idle_w=server_cfg['power_idle_w'],
            power_max_w=server_cfg['power_max_w']
        )

        # Get case file from OPF config
        opf_cfg = config['opf_config']
        case_file = opf_cfg['caseID']

        logger.info(f"[DIST]   Case file: {case_file}")

        # Setup edge infrastructure with case file for topology
        simulator.setup_edge_infrastructure(
            num_servers=edge_infra['num_servers'],
            server_specs=server_specs,
            case_file=case_file
        )
        logger.info("[DIST]   ✓ Edge infrastructure configured")

        # Setup Julia configuration
        logger.info("[DIST] Step 3: Setting up Julia OPF configuration...")

        logger.info(f"[DIST]   Max iterations: {opf_cfg['max_iterations']}")
        logger.info(f"[DIST]   Privacy method: {opf_cfg['method']}")

        julia_config = JuliaConfig(
            node_id=1,  # Will be overridden for each node
            caseID=case_file,
            max_iterations=opf_cfg['max_iterations'],
            rho=opf_cfg['rho'],
            tolerance=opf_cfg['tolerance'],
            epsilon=opf_cfg['epsilon'],
            alpha=opf_cfg['alpha'],
            method=opf_cfg['method']
        )
        logger.info("[DIST]   ✓ Julia configuration created")

        # Run distributed OPF
        logger.info("[DIST] Step 4: Running distributed OPF computation...")
        parallel = config['execution'].get('parallel', True)
        logger.info(f"[DIST]   Parallel execution: {parallel}")

        results = simulator.run_distributed_opf(julia_config=julia_config, parallel=parallel)

        logger.info("[DIST]   ✓ Distributed OPF computation completed")

        if 'node_results' in results:
            logger.info(f"[DIST]   Total nodes processed: {len(results['node_results'])}")

        logger.info("\n✓ Distributed simulation completed successfully")
        return results

    except KeyError as e:
        logger.error(f"[DIST] ✗ Configuration error: Missing key {e}")
        logger.error(f"[DIST]   Check your configuration has all required fields")
        raise
    except AttributeError as e:
        logger.error(f"[DIST] ✗ Attribute error: {e}")
        logger.error(f"[DIST]   This might indicate an API mismatch")
        logger.error(f"[DIST]   Check that EdgeOPFSimulator has the expected methods")
        raise
    except Exception as e:
        logger.error(f"[DIST] ✗ Unexpected error: {e}")
        logger.error(f"[DIST]   Error type: {type(e).__name__}")
        raise


def run_encrypted(config, scheme):
    """Run encrypted OPF (Paillier, BGV, or CKKS)"""
    logger.info("\n" + "="*80)
    logger.info(f"RUNNING {scheme.upper()} ENCRYPTED OPF")
    logger.info("="*80 + "\n")

    logger.warning(f"⚠️  Note: {scheme.upper()} encryption adds significant overhead")
    if scheme == 'paillier':
        logger.warning("⚠️  Expected overhead: ~10x slower than non-encrypted")
    elif scheme == 'bgv':
        logger.warning("⚠️  Expected overhead: ~300x slower than Paillier (~3000x vs non-encrypted)")
    elif scheme == 'ckks':
        logger.warning("⚠️  Expected overhead: ~300x slower than Paillier (~3000x vs non-encrypted)")

    logger.info("")

    # Change to optimization directory to run Julia scripts
    logger.info(f"[ENC] Step 1: Preparing Julia environment...")
    original_dir = os.getcwd()
    opt_dir = Path(__file__).parent
    logger.info(f"[ENC]   Current directory: {original_dir}")
    logger.info(f"[ENC]   Changing to: {opt_dir}")
    os.chdir(opt_dir)
    logger.info(f"[ENC]   ✓ Working directory changed")

    try:
        import subprocess

        # Map scheme to Julia script
        script_map = {
            'paillier': 'opt_main_verified.jl',
            'bgv': 'opt_main_bgv.jl',
            'ckks': 'opt_main_ckks.jl',
        }

        script = script_map[scheme]
        script_path = Path(script)

        logger.info(f"[ENC] Step 2: Checking Julia script...")
        logger.info(f"[ENC]   Script: {script}")

        if not script_path.exists():
            logger.error(f"[ENC]   ✗ Julia script not found: {script}")
            logger.error(f"[ENC]   Expected location: {script_path.absolute()}")
            return {'success': False, 'error': f'Script not found: {script}'}

        logger.info(f"[ENC]   ✓ Script found: {script_path.absolute()}")

        # Check if Julia is available
        logger.info(f"[ENC] Step 3: Checking Julia installation...")
        try:
            julia_version = subprocess.run(['julia', '--version'], capture_output=True, text=True, timeout=5)
            logger.info(f"[ENC]   ✓ Julia found: {julia_version.stdout.strip()}")
        except FileNotFoundError:
            logger.error(f"[ENC]   ✗ Julia not found in PATH")
            logger.error(f"[ENC]   Install Julia from: https://julialang.org/downloads/")
            return {'success': False, 'error': 'Julia not found'}
        except Exception as e:
            logger.warning(f"[ENC]   ⚠ Could not check Julia version: {e}")

        logger.info(f"[ENC] Step 4: Running Julia script...")
        logger.info(f"[ENC]   Command: julia {script}")
        logger.info(f"[ENC]   Timeout: 3600 seconds (1 hour)")
        logger.info("-" * 80 + "\n")

        # Run Julia script
        result = subprocess.run(
            ['julia', script],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        # Print output
        logger.info(result.stdout)
        if result.stderr:
            if "ERROR" in result.stderr or "LoadError" in result.stderr:
                logger.error(f"\n[ENC] Julia errors detected:")
                logger.error(result.stderr)

                # Check for common errors
                if "Package Primes not found" in result.stderr:
                    logger.error(f"\n[ENC] ✗ Missing Julia package: Primes")
                    logger.error(f"[ENC]   Install with: julia -e 'using Pkg; Pkg.add(\"Primes\")'")
                    logger.error(f"[ENC]   Or run: julia install_julia_packages.jl")
            else:
                logger.info("\nSTDERR:", result.stderr)

        logger.info("-" * 80)

        # Check for results JSON
        logger.info(f"\n[ENC] Step 5: Checking for results...")
        results_file = f"results/{scheme}_results.json"
        results_path = Path(results_file)

        logger.info(f"[ENC]   Looking for: {results_path.absolute()}")

        if results_path.exists():
            logger.info(f"[ENC]   ✓ Results file found")
            with open(results_file, 'r') as f:
                julia_results = json.load(f)

            logger.info("\n" + "="*80)
            logger.info(f"✓ {scheme.upper()} ENCRYPTION COMPLETED")
            logger.info("="*80)
            logger.info(f"  Total time: {julia_results.get('total_time_s', 'N/A'):.2f}s")
            logger.info(f"  Iterations: {julia_results.get('iterations', 'N/A')}")
            logger.info(f"  Final cost: ${julia_results.get('final_cost', 'N/A'):.2f}")
            logger.info(f"  Optimality loss: {julia_results.get('optimality_loss_percent', 'N/A'):.4f}%")
            logger.info(f"  Converged: {julia_results.get('converged', 'N/A')}")

            if 'pct_crypto' in julia_results:
                logger.info(f"\n  Timing breakdown:")
                logger.info(f"    Optimization: {julia_results.get('pct_opt', 'N/A'):.1f}%")
                logger.info(f"    Cryptography: {julia_results.get('pct_crypto', 'N/A'):.1f}%")
                logger.info(f"    Other: {julia_results.get('pct_other', 'N/A'):.1f}%")

            return julia_results
        else:
            logger.warning(f"[ENC]   ✗ Results file not found: {results_file}")
            logger.warning(f"[ENC]   Expected at: {results_path.absolute()}")

            if result.returncode != 0:
                logger.error(f"[ENC]   Julia script failed with return code: {result.returncode}")
                logger.error(f"[ENC]   Check the error messages above")

            return {'success': result.returncode == 0}

    except subprocess.TimeoutExpired:
        logger.error(f"[ENC] ✗ Julia script timeout (exceeded 1 hour)")
        logger.error(f"[ENC]   Consider reducing --max-iter for encrypted modes")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.error(f"[ENC] ✗ Unexpected error: {e}")
        logger.error(f"[ENC]   Error type: {type(e).__name__}")
        raise
    finally:
        logger.info(f"\n[ENC] Restoring original directory: {original_dir}")
        os.chdir(original_dir)


def generate_visualizations(results, mode, output_dir, plots_dir):
    """Generate visualization plots"""
    logger.info("\n" + "="*80)
    logger.info("GENERATING VISUALIZATIONS")
    logger.info("="*80 + "\n")

    try:
        logger.info("[VIZ] Step 1: Creating output directories...")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(plots_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"[VIZ]   ✓ Output dir: {output_dir}")
        logger.info(f"[VIZ]   ✓ Plots dir: {plots_dir}")

        logger.info("[VIZ] Step 2: Initializing ResultsExporter...")
        exporter = ResultsExporter(output_dir=output_dir)
        logger.info("[VIZ]   ✓ ResultsExporter initialized")

        logger.info("[VIZ] Step 3: Generating plots...")
        if mode == 'distributed':
            logger.info(f"[VIZ]   Mode: distributed - generating full plot suite")
            exporter.generate_plots(results, prefix=f"{mode}")
            logger.info(f"[VIZ]   ✓ Plots generated successfully")
        else:
            logger.info(f"[VIZ]   Mode: {mode}")
            logger.info(f"[VIZ]   Note: Visualization for centralized/encrypted modes")
            logger.info(f"[VIZ]   uses results JSON files directly")

        logger.info(f"\n[VIZ] ✓ Plots saved to: {plots_dir}")

    except Exception as e:
        logger.error(f"[VIZ] ✗ Error generating visualizations: {e}")
        logger.error(f"[VIZ]   Error type: {type(e).__name__}")
        raise


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
