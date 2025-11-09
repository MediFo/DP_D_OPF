#!/usr/bin/env python3
"""
Test visualization with mock data to verify dual time-axis plots work
"""

import sys
import os
sys.path.insert(0, 'edge')

import numpy as np
from visualization import ResultsExporter
import json

def create_mock_results():
    """Create mock simulation results with timestamp data"""

    # Create mock node results (simulating 10 edge devices)
    node_results = []

    for node_id in range(1, 11):
        # Simulate 100 iterations
        num_iterations = 100

        # Create realistic timestamps (cumulative time)
        base_iteration_time = 0.1 + np.random.rand() * 0.05  # 100-150ms per iteration
        timestamps = np.cumsum([base_iteration_time + np.random.rand() * 0.02
                                for _ in range(num_iterations)])

        # Create CPU and memory history
        cpu_base = 30 + np.random.rand() * 20
        mem_base = 40 + np.random.rand() * 20

        cpu_history = [cpu_base + np.random.rand() * 10 + i * 0.1  # Slight upward trend
                      for i in range(num_iterations)]
        mem_history = [mem_base + np.random.rand() * 10 + i * 0.05
                      for i in range(num_iterations)]

        node_result = {
            'node_id': node_id,
            'success': True,
            'execution_time_s': timestamps[-1],
            'resource_monitoring': {
                'timestamps': timestamps.tolist(),
                'cpu_history': cpu_history,
                'memory_history': mem_history,
                'execution_time_s': timestamps[-1],
            },
            'julia_results': {
                'iterations': num_iterations,
                'total_time_s': timestamps[-1],
                'iteration_times': np.diff([0] + timestamps.tolist()).tolist(),
                'iteration_timestamps': timestamps.tolist(),
                'residuals': [1.0 / (i + 1) for i in range(num_iterations)],
                'final_cost': 1000 + np.random.rand() * 100,
            }
        }

        node_results.append(node_result)

    # Create mock simulation stats
    simulation_stats = {
        'servers': {},
        'links': {}
    }

    # Mock server stats
    for node_id in range(1, 11):
        simulation_stats['servers'][node_id] = {
            'id': node_id,
            'cpu_usage': 30 + np.random.rand() * 40,
            'memory_usage': 40 + np.random.rand() * 30,
            'power_consumption': 50 + np.random.rand() * 50,
        }

    # Create mock link data
    for i in range(1, 10):
        simulation_stats['links'][(i, i+1)] = {
            'utilization': np.random.rand() * 100,
            'bandwidth_mbps': 100,
            'transmission_history': [
                {'timestamp': t, 'bytes': np.random.randint(1000, 10000)}
                for t in np.linspace(0, 10, 50)
            ]
        }

    results = {
        'node_results': node_results,
        'simulation_stats': simulation_stats,
        'device_configs': {},
    }

    return results

def test_visualization():
    """Test visualization with mock data"""
    print("="*80)
    print("TESTING VISUALIZATION WITH MOCK DATA")
    print("="*80)

    # Create output directory
    os.makedirs('edge/results', exist_ok=True)

    # Create mock results
    print("\n[1/4] Creating mock simulation results...")
    results = create_mock_results()
    print(f"  ✓ Created results for {len(results['node_results'])} nodes")
    print(f"  ✓ Each node has {len(results['node_results'][0]['resource_monitoring']['timestamps'])} iterations")

    # Initialize exporter
    print("\n[2/4] Initializing ResultsExporter...")
    exporter = ResultsExporter(output_dir='edge/results')
    print("  ✓ ResultsExporter initialized")

    # Generate plots
    print("\n[3/4] Generating plots...")
    try:
        exporter.generate_plots(results, prefix='test')
        print("  ✓ Plots generated successfully")
    except Exception as e:
        print(f"  ✗ Error generating plots: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check output files
    print("\n[4/4] Checking output files...")
    import glob

    plot_files = glob.glob('edge/results/test_*.png')
    print(f"  ✓ Generated {len(plot_files)} plot files")

    # Check for new dual time-axis plots
    expected_new_plots = [
        'test_dual_cpu_memory_percentile_iteration.png',
        'test_dual_cpu_memory_percentile_realtime.png',
        'test_iteration_duration_analysis.png',
        'test_cumulative_computation_time.png',
        'test_iteration_throughput.png',
        'test_time_budget_analysis.png',
        'test_realtime_efficiency_metrics.png',
        'test_performance_degradation.png',
    ]

    print("\n  Checking for new dual time-axis plots:")
    for plot_name in expected_new_plots:
        plot_path = f'edge/results/{plot_name}'
        if os.path.exists(plot_path):
            size_kb = os.path.getsize(plot_path) / 1024
            print(f"    ✓ {plot_name} ({size_kb:.1f} KB)")
        else:
            print(f"    ✗ Missing: {plot_name}")

    # Save mock results to JSON
    print("\n[5/5] Saving mock results to JSON...")
    with open('edge/results/test_mock_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("  ✓ Saved to: edge/results/test_mock_results.json")

    print("\n" + "="*80)
    print("✓ VISUALIZATION TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"\nGenerated plots are in: edge/results/")
    print(f"Total plot files: {len(plot_files)}")

    return True

if __name__ == '__main__':
    success = test_visualization()
    sys.exit(0 if success else 1)
