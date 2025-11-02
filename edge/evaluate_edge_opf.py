#!/usr/bin/env python3
"""
Main Evaluation Script for OPF on Edge Devices
Runs distributed and centralized OPF, exports results, and generates visualizations
"""

import argparse
import json
import time
from pathlib import Path

from edge_opf_simulator import EdgeOPFSimulator
from julia_wrapper import JuliaConfig
from edgesimpy.edge_server import ServerSpecs
from visualization import ResultsExporter


def run_distributed_evaluation(num_servers: int = 3,
                               max_iterations: int = 1000,
                               parallel: bool = True,
                               case_id: str = "testbeds/pglib_opf_case14_ieee.m",
                               config_file: str = None):
    """
    Run distributed OPF evaluation on edge devices

    Args:
        num_servers: Number of edge servers
        max_iterations: Maximum ADMM iterations
        parallel: Execute nodes in parallel
        case_id: Power system test case
        config_file: JSON configuration file for hardware specifications
    """
    print("\n" + "="*80)
    print("DISTRIBUTED OPF EVALUATION ON EDGE DEVICES")
    print("="*80)

    # Create simulator
    sim = EdgeOPFSimulator(f"Distributed_OPF_{num_servers}_Servers")

    # Setup edge infrastructure with power grid topology
    if config_file:
        # Use custom hardware configs from JSON
        sim.setup_edge_infrastructure(num_servers=num_servers, config_file=config_file, case_file=case_id)
    else:
        # Use default specs for all servers
        server_specs = ServerSpecs(
            cpu_cores=4,
            cpu_freq_ghz=2.4,
            memory_gb=8.0,
            storage_gb=100.0,
            power_idle_w=50.0,
            power_max_w=150.0
        )
        sim.setup_edge_infrastructure(num_servers=num_servers, server_specs=server_specs, case_file=case_id)

    # Configure Julia OPF
    julia_config = JuliaConfig(
        caseID=case_id,
        max_iterations=max_iterations,
        rho=1e3,
        tolerance=1e-2,
        epsilon=1.0,
        alpha=0.1,
        method="PVP"
    )

    # Run distributed OPF
    print(f"\nRunning distributed OPF with {num_servers} edge servers...")
    results = sim.run_distributed_opf(julia_config=julia_config, parallel=parallel)

    # Export results
    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)

    exporter = ResultsExporter()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = f"distributed_{num_servers}servers_{timestamp}"

    # Save full results to JSON
    results_file = exporter.output_dir / f"{prefix}_full.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"✓ Saved full results to {results_file.name}")

    # Export to CSV
    exporter.export_to_csv(results, prefix)

    # Generate plots
    exporter.generate_plots(results, prefix)

    # Print summary
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"Simulation: {results['simulation_name']}")
    print(f"Execution mode: {results['execution_mode']}")
    print(f"Number of edge servers: {results['num_edge_servers']}")

    if 'node_results' in results:
        successful = sum(1 for r in results['node_results'] if r.get('success', False))
        print(f"Successful nodes: {successful}/{len(results['node_results'])}")

    if 'simulation_stats' in results and 'global_resources' in results['simulation_stats']:
        global_res = results['simulation_stats']['global_resources']
        print(f"\nGlobal Resource Usage:")
        if 'cpu' in global_res:
            print(f"  - Avg CPU: {global_res['cpu'].get('avg', 0):.1f}%")
            print(f"  - Max CPU: {global_res['cpu'].get('max', 0):.1f}%")
        if 'memory' in global_res:
            print(f"  - Avg Memory: {global_res['memory'].get('avg_mb', 0):.1f} MB")
            print(f"  - Max Memory: {global_res['memory'].get('max_mb', 0):.1f} MB")

    print("\n" + "="*80)
    return results


def run_centralized_evaluation(case_id: str = "testbeds/pglib_opf_case14_ieee.m",
                               config_file: str = None):
    """
    Run centralized OPF evaluation on a single edge device

    Args:
        case_id: Power system test case
        config_file: JSON configuration file for hardware specifications (uses first device)
    """
    print("\n" + "="*80)
    print("CENTRALIZED OPF EVALUATION ON EDGE DEVICE")
    print("="*80)

    # Create simulator
    sim = EdgeOPFSimulator("Centralized_OPF")

    # Setup single edge server (no topology needed for centralized)
    if config_file:
        # Use first device from config file
        sim.setup_edge_infrastructure(num_servers=1, config_file=config_file, case_file=None)
    else:
        # Use default specs
        server_specs = ServerSpecs(
            cpu_cores=4,
            cpu_freq_ghz=2.4,
            memory_gb=8.0,
            storage_gb=100.0,
            power_idle_w=50.0,
            power_max_w=150.0
        )
        sim.setup_edge_infrastructure(num_servers=1, server_specs=server_specs, case_file=None)

    # Run centralized OPF
    config = {"caseID": case_id}
    print("\nRunning centralized OPF on single edge server...")
    results = sim.run_centralized_opf(julia_config=config)

    # Export results
    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)

    exporter = ResultsExporter()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = f"centralized_{timestamp}"

    # Save full results to JSON
    results_file = exporter.output_dir / f"{prefix}_full.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"✓ Saved full results to {results_file.name}")

    # Export to CSV
    exporter.export_to_csv(results, prefix)

    # Generate plots (limited for centralized)
    exporter.generate_plots(results, prefix)

    # Print summary
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"Simulation: {results['simulation_name']}")

    if 'result' in results:
        res = results['result']
        print(f"Success: {res.get('success', False)}")
        print(f"Execution time: {res.get('execution_time_s', 0):.3f}s")

        if 'resource_monitoring' in res:
            mon = res['resource_monitoring']
            print(f"\nResource Usage:")
            print(f"  - Avg CPU: {mon.get('avg_cpu_percent', 0):.1f}%")
            print(f"  - Max CPU: {mon.get('max_cpu_percent', 0):.1f}%")
            print(f"  - Avg Memory: {mon.get('avg_memory_mb', 0):.1f} MB")
            print(f"  - Max Memory: {mon.get('max_memory_mb', 0):.1f} MB")

    print("\n" + "="*80)
    return results


def run_comparison_evaluation(num_servers: int = 3,
                              max_iterations: int = 1000,
                              case_id: str = "testbeds/pglib_opf_case14_ieee.m",
                              config_file: str = None):
    """
    Run both distributed and centralized evaluations for comparison

    Args:
        num_servers: Number of edge servers for distributed
        max_iterations: Maximum ADMM iterations
        case_id: Power system test case
        config_file: JSON configuration file for hardware specifications
    """
    print("\n" + "="*80)
    print("COMPARATIVE EVALUATION: DISTRIBUTED vs CENTRALIZED OPF")
    print("="*80)

    # Run centralized
    print("\n>>> Phase 1: Centralized OPF")
    centralized_results = run_centralized_evaluation(case_id, config_file)

    # Run distributed
    print("\n>>> Phase 2: Distributed OPF")
    distributed_results = run_distributed_evaluation(
        num_servers=num_servers,
        max_iterations=max_iterations,
        parallel=True,
        case_id=case_id,
        config_file=config_file
    )

    # Create comparison summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    # Extract metrics
    cent_res = centralized_results.get('result', {})
    cent_time = cent_res.get('execution_time_s', 0)
    cent_monitoring = cent_res.get('resource_monitoring', {})

    dist_stats = distributed_results.get('simulation_stats', {})
    dist_global = dist_stats.get('global_resources', {})

    print("\nExecution Time:")
    print(f"  - Centralized: {cent_time:.3f}s")
    print(f"  - Distributed: {dist_global.get('duration_s', 0):.3f}s")

    print("\nCPU Usage:")
    print(f"  - Centralized Avg: {cent_monitoring.get('avg_cpu_percent', 0):.1f}%")
    print(f"  - Distributed Avg: {dist_global.get('cpu', {}).get('avg', 0):.1f}%")

    print("\nMemory Usage:")
    print(f"  - Centralized Max: {cent_monitoring.get('max_memory_mb', 0):.1f} MB")
    print(f"  - Distributed Max: {dist_global.get('memory', {}).get('max_mb', 0):.1f} MB")

    # Save comparison
    exporter = ResultsExporter()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    comparison_file = exporter.output_dir / f"comparison_{timestamp}.json"

    comparison_data = {
        'centralized': centralized_results,
        'distributed': distributed_results,
        'timestamp': timestamp
    }

    with open(comparison_file, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=str)

    print(f"\n✓ Saved comparison to {comparison_file.name}")
    print("="*80)

    return comparison_data


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Evaluate OPF computation on edge devices using EdgeSimPy"
    )
    parser.add_argument(
        '--mode',
        choices=['distributed', 'centralized', 'comparison'],
        default='comparison',
        help='Evaluation mode (default: comparison)'
    )
    parser.add_argument(
        '--servers',
        type=int,
        default=3,
        help='Number of edge servers for distributed mode (default: 3)'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=1000,
        help='Maximum ADMM iterations (default: 1000)'
    )
    parser.add_argument(
        '--case',
        default='testbeds/pglib_opf_case14_ieee.m',
        help='Power system test case file'
    )
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Run distributed nodes sequentially instead of parallel'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='JSON configuration file with hardware specifications for edge devices (default: edge/edge_devices_config.json if not specified)'
    )

    args = parser.parse_args()

    # Use default config file if none specified
    config_file = args.config
    if config_file is None:
        default_config = Path(__file__).parent / "edge_devices_config.json"
        if default_config.exists():
            config_file = str(default_config)
            print(f"Using default configuration file: {config_file}")

    print("\n" + "="*80)
    print("EDGE OPF EVALUATION TOOL")
    print("Evaluating OPF Runtime and Resource Utilization on Edge Devices")
    print("="*80)
    print(f"Mode: {args.mode}")
    print(f"Test case: {args.case}")
    if config_file:
        print(f"Hardware config: {config_file}")
    if args.mode in ['distributed', 'comparison']:
        print(f"Edge servers: {args.servers}")
        print(f"Max iterations: {args.iterations}")
        print(f"Execution: {'Sequential' if args.sequential else 'Parallel'}")
    print("="*80)

    try:
        if args.mode == 'distributed':
            run_distributed_evaluation(
                num_servers=args.servers,
                max_iterations=args.iterations,
                parallel=not args.sequential,
                case_id=args.case,
                config_file=config_file
            )
        elif args.mode == 'centralized':
            run_centralized_evaluation(case_id=args.case, config_file=config_file)
        elif args.mode == 'comparison':
            run_comparison_evaluation(
                num_servers=args.servers,
                max_iterations=args.iterations,
                case_id=args.case,
                config_file=config_file
            )

        print("\n✓ Evaluation completed successfully!")

    except Exception as e:
        print(f"\n✗ Evaluation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
