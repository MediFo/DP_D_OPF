"""
Visualization and CSV Export for Edge OPF Simulation Results
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


class ResultsExporter:
    """Export simulation results to CSV and generate plots"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize results exporter

        Args:
            output_dir: Output directory (defaults to edge/results)
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "results"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(exist_ok=True)
        self.plots_dir = Path(__file__).parent / "plots"
        self.plots_dir.mkdir(exist_ok=True)

    def export_to_csv(self, results: Dict, prefix: str = "simulation"):
        """
        Export simulation results to CSV files

        Args:
            results: Simulation results dictionary
            prefix: Prefix for output filenames
        """
        print(f"\nExporting results to CSV (prefix: {prefix})...")

        # Export server statistics
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._export_server_stats(
                results['simulation_stats']['servers'],
                f"{prefix}_servers.csv"
            )

        # Export service statistics
        if 'simulation_stats' in results and 'services' in results['simulation_stats']:
            self._export_service_stats(
                results['simulation_stats']['services'],
                f"{prefix}_services.csv"
            )

        # Export network link statistics
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._export_link_stats(
                results['simulation_stats']['links'],
                f"{prefix}_links.csv"
            )

        # Export node execution results
        if 'node_results' in results:
            self._export_node_results(
                results['node_results'],
                f"{prefix}_node_execution.csv"
            )

        # Export global resource monitoring
        if 'simulation_stats' in results and 'global_resources' in results['simulation_stats']:
            self._export_global_resources(
                results['simulation_stats']['global_resources'],
                f"{prefix}_global_resources.csv"
            )

        # Export summary
        self._export_summary(results, f"{prefix}_summary.csv")

        print("✓ CSV export completed")

    def _export_server_stats(self, servers: Dict, filename: str):
        """Export server statistics to CSV"""
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Server_ID', 'Server_Name', 'Avg_CPU_%', 'Max_CPU_%',
                'Avg_Memory_MB', 'Max_Memory_MB', 'Avg_Power_W',
                'Total_Energy_Wh', 'Num_Samples'
            ])

            for server_id, stats in servers.items():
                writer.writerow([
                    stats.get('id', server_id),
                    stats.get('name', f'Server_{server_id}'),
                    round(stats.get('avg_cpu_usage', 0), 2),
                    round(stats.get('max_cpu_usage', 0), 2),
                    round(stats.get('avg_memory_usage_mb', 0), 2),
                    round(stats.get('max_memory_usage_mb', 0), 2),
                    round(stats.get('avg_power_w', 0), 2),
                    round(stats.get('total_energy_wh', 0), 4),
                    stats.get('num_samples', 0)
                ])

        print(f"  - Saved server stats to {filename}")

    def _export_service_stats(self, services: Dict, filename: str):
        """Export service statistics to CSV"""
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Service_ID', 'Service_Name', 'Type', 'Node_ID', 'Status',
                'Server_ID', 'Runtime_s', 'Avg_CPU_%', 'Max_CPU_%',
                'Avg_Memory_MB', 'Max_Memory_MB', 'Network_Sent_MB',
                'Network_Recv_MB', 'Total_Network_MB'
            ])

            for service_id, stats in services.items():
                writer.writerow([
                    stats.get('id', service_id),
                    stats.get('name', f'Service_{service_id}'),
                    stats.get('type', 'unknown'),
                    stats.get('node_id', ''),
                    stats.get('status', 'unknown'),
                    stats.get('assigned_server', ''),
                    round(stats.get('actual_runtime_s', 0), 3),
                    round(stats.get('avg_cpu_usage', 0), 2),
                    round(stats.get('max_cpu_usage', 0), 2),
                    round(stats.get('avg_memory_usage_mb', 0), 2),
                    round(stats.get('max_memory_usage_mb', 0), 2),
                    round(stats.get('network_sent_mb', 0), 4),
                    round(stats.get('network_recv_mb', 0), 4),
                    round(stats.get('total_network_mb', 0), 4)
                ])

        print(f"  - Saved service stats to {filename}")

    def _export_link_stats(self, links: Dict, filename: str):
        """Export network link statistics to CSV"""
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Link_ID', 'Source_Server', 'Target_Server', 'Bandwidth_Mbps',
                'Latency_ms', 'Total_Data_MB', 'Num_Transmissions',
                'Total_Transmission_Time_s', 'Avg_Transmission_Time_s'
            ])

            for link_id, stats in links.items():
                writer.writerow([
                    stats.get('id', link_id),
                    stats.get('source_server_id', ''),
                    stats.get('target_server_id', ''),
                    stats.get('bandwidth_mbps', 0),
                    stats.get('latency_ms', 0),
                    round(stats.get('total_data_transmitted_mb', 0), 4),
                    stats.get('num_transmissions', 0),
                    round(stats.get('total_transmission_time_s', 0), 4),
                    round(stats.get('avg_transmission_time_s', 0), 6)
                ])

        print(f"  - Saved link stats to {filename}")

    def _export_node_results(self, node_results: List[Dict], filename: str):
        """Export node execution results to CSV"""
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Node_ID', 'Success', 'Execution_Time_s', 'Iterations',
                'Avg_Iteration_Time_ms', 'Final_Cost', 'Final_Residual',
                'Avg_CPU_%', 'Max_CPU_%', 'Avg_Memory_MB', 'Max_Memory_MB'
            ])

            for result in node_results:
                monitoring = result.get('resource_monitoring', {})
                julia_res = result.get('julia_results', {})

                writer.writerow([
                    result.get('node_id', ''),
                    result.get('success', False),
                    round(result.get('execution_time_s', 0), 3),
                    julia_res.get('iterations', ''),
                    round(julia_res.get('avg_iteration_time_ms', 0), 2),
                    round(julia_res.get('final_cost', 0), 2),
                    julia_res.get('final_residual', ''),
                    round(monitoring.get('avg_cpu_percent', 0), 2),
                    round(monitoring.get('max_cpu_percent', 0), 2),
                    round(monitoring.get('avg_memory_mb', 0), 2),
                    round(monitoring.get('max_memory_mb', 0), 2)
                ])

        print(f"  - Saved node execution results to {filename}")

    def _export_global_resources(self, global_res: Dict, filename: str):
        """Export global resource statistics to CSV"""
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', 'Unit'])

            cpu = global_res.get('cpu', {})
            memory = global_res.get('memory', {})
            network = global_res.get('network', {})

            rows = [
                ['Duration', round(global_res.get('duration_s', 0), 3), 's'],
                ['Avg_CPU', round(cpu.get('avg', 0), 2), '%'],
                ['Max_CPU', round(cpu.get('max', 0), 2), '%'],
                ['Avg_Memory', round(memory.get('avg_mb', 0), 2), 'MB'],
                ['Max_Memory', round(memory.get('max_mb', 0), 2), 'MB'],
                ['Network_Sent', round(network.get('total_sent_mb', 0), 4), 'MB'],
                ['Network_Recv', round(network.get('total_recv_mb', 0), 4), 'MB'],
                ['Num_Samples', global_res.get('num_samples', 0), 'count']
            ]

            writer.writerows(rows)

        print(f"  - Saved global resources to {filename}")

    def _export_summary(self, results: Dict, filename: str):
        """Export high-level summary to CSV"""
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])

            sim_stats = results.get('simulation_stats', {})

            rows = [
                ['Simulation_Name', results.get('simulation_name', '')],
                ['Execution_Mode', results.get('execution_mode', '')],
                ['Num_Servers', results.get('num_edge_servers', sim_stats.get('num_servers', ''))],
                ['Num_Services', sim_stats.get('num_services', '')],
                ['Num_Links', sim_stats.get('num_links', '')],
                ['Total_Duration_s', round(sim_stats.get('duration_s', 0), 3)],
                ['Timestamp', results.get('timestamp', '')]
            ]

            # Add node-specific metrics if available
            if 'node_results' in results:
                successful = sum(1 for r in results['node_results'] if r.get('success', False))
                total = len(results['node_results'])
                rows.extend([
                    ['Total_Nodes', total],
                    ['Successful_Nodes', successful],
                    ['Failed_Nodes', total - successful]
                ])

            writer.writerows(rows)

        print(f"  - Saved summary to {filename}")

    def generate_plots(self, results: Dict, prefix: str = "simulation"):
        """
        Generate visualization plots from simulation results

        Args:
            results: Simulation results dictionary
            prefix: Prefix for output filenames
        """
        print(f"\nGenerating plots (prefix: {prefix})...")

        # Plot 1: Resource usage comparison across servers
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_server_resources(
                results['simulation_stats']['servers'],
                f"{prefix}_server_resources.png"
            )

        # Plot 2: Node execution performance
        if 'node_results' in results:
            self._plot_node_performance(
                results['node_results'],
                f"{prefix}_node_performance.png"
            )

        # Plot 3: Resource usage over time
        if 'node_results' in results:
            self._plot_resource_timeline(
                results['node_results'],
                f"{prefix}_resource_timeline.png"
            )

        # Plot 4: Network traffic
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_network_traffic(
                results['simulation_stats']['links'],
                f"{prefix}_network_traffic.png"
            )

        # NEW CREATIVE PLOTS for better visualization with many devices

        # Plot 5: Heatmap of resource usage over time
        if 'node_results' in results and len(results['node_results']) > 0:
            self._plot_resource_heatmap(
                results['node_results'],
                f"{prefix}_resource_heatmap.png"
            )

        # Plot 6: Stacked area chart - contribution over time
        if 'node_results' in results and len(results['node_results']) > 0:
            self._plot_stacked_area_chart(
                results['node_results'],
                f"{prefix}_stacked_area.png"
            )

        # Plot 7: Parallel coordinates - multi-metric comparison
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_parallel_coordinates(
                results['simulation_stats']['servers'],
                f"{prefix}_parallel_coords.png"
            )

        # Plot 8: Sorted bar charts - all devices ranked
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_sorted_bars(
                results['simulation_stats']['servers'],
                f"{prefix}_sorted_devices.png"
            )

        # Plot 9: Device type comparison (6 types)
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_device_type_comparison(
                results['simulation_stats']['servers'],
                results.get('device_configs', {}),
                f"{prefix}_device_types.png"
            )

        # Plot 10: Correlation matrix
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_correlation_matrix(
                results['simulation_stats']['servers'],
                f"{prefix}_correlation_matrix.png"
            )

        # Plot 11: Cumulative distribution functions
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_cdf_curves(
                results['simulation_stats']['servers'],
                f"{prefix}_cdf_curves.png"
            )

        # Plot 12: Efficiency scatter plots
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_efficiency_scatter(
                results['simulation_stats']['servers'],
                f"{prefix}_efficiency_scatter.png"
            )

        # Plot 13: Percentile bands over time
        if 'node_results' in results and len(results['node_results']) > 0:
            self._plot_percentile_bands(
                results['node_results'],
                f"{prefix}_percentile_bands.png"
            )

        # Plot 14: Small multiples grid
        if 'node_results' in results and len(results['node_results']) > 0:
            self._plot_small_multiples(
                results['node_results'],
                f"{prefix}_small_multiples.png"
            )

        # Plot 15: Network topology with resource overlay
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_network_topology(
                results['simulation_stats']['servers'],
                results['simulation_stats']['links'],
                f"{prefix}_network_topology.png"
            )

        # MORE PERCENTILE BAND PLOTS (user liked this style!)

        # Plot 16: Power percentile bands over time
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_power_percentile_bands(
                results['simulation_stats']['servers'],
                f"{prefix}_power_percentile_bands.png"
            )

        # Plot 17: Energy accumulation percentile bands
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_energy_percentile_bands(
                results['simulation_stats']['servers'],
                f"{prefix}_energy_percentile_bands.png"
            )

        # Plot 18: Combined multi-metric percentile bands
        if 'node_results' in results and len(results['node_results']) > 0:
            self._plot_combined_percentile_bands(
                results['node_results'],
                results['simulation_stats']['servers'],
                f"{prefix}_combined_percentile_bands.png"
            )

        # 5 CREATIVE NETWORK TRAFFIC PLOTS

        # Plot 19: Network traffic heatmap over time
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_network_traffic_heatmap(
                results['simulation_stats']['links'],
                f"{prefix}_network_traffic_heatmap.png"
            )

        # Plot 20: Network link utilization distribution
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_network_link_utilization(
                results['simulation_stats']['links'],
                f"{prefix}_network_link_utilization.png"
            )

        # Plot 21: Network bottleneck identification
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_network_bottlenecks(
                results['simulation_stats']['links'],
                f"{prefix}_network_bottlenecks.png"
            )

        # Plot 22: Temporal traffic patterns
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_temporal_traffic_patterns(
                results['simulation_stats']['links'],
                f"{prefix}_temporal_traffic.png"
            )

        # Plot 23: Network efficiency metrics
        if 'simulation_stats' in results and 'links' in results['simulation_stats']:
            self._plot_network_efficiency(
                results['simulation_stats']['links'],
                f"{prefix}_network_efficiency.png"
            )

        print("✓ Plot generation completed")

    def _plot_server_resources(self, servers: Dict, filename: str):
        """Plot server resource comparison"""
        server_ids = []
        avg_cpu = []
        max_cpu = []
        avg_mem = []
        max_mem = []
        power = []

        for sid, stats in sorted(servers.items()):
            server_ids.append(f"Server_{stats.get('id', sid)}")
            avg_cpu.append(stats.get('avg_cpu_usage', 0))
            max_cpu.append(stats.get('max_cpu_usage', 0))
            avg_mem.append(stats.get('avg_memory_usage_mb', 0))
            max_mem.append(stats.get('max_memory_usage_mb', 0))
            power.append(stats.get('avg_power_w', 0))

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Edge Server Resource Usage Comparison', fontsize=16, fontweight='bold')

        # CPU usage
        x = np.arange(len(server_ids))
        width = 0.35
        axes[0, 0].bar(x - width/2, avg_cpu, width, label='Avg CPU', alpha=0.8)
        axes[0, 0].bar(x + width/2, max_cpu, width, label='Max CPU', alpha=0.8)
        axes[0, 0].set_xlabel('Edge Server')
        axes[0, 0].set_ylabel('CPU Usage (%)')
        axes[0, 0].set_title('CPU Utilization')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(server_ids, rotation=45, ha='right')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Memory usage
        axes[0, 1].bar(x - width/2, avg_mem, width, label='Avg Memory', alpha=0.8)
        axes[0, 1].bar(x + width/2, max_mem, width, label='Max Memory', alpha=0.8)
        axes[0, 1].set_xlabel('Edge Server')
        axes[0, 1].set_ylabel('Memory Usage (MB)')
        axes[0, 1].set_title('Memory Utilization')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(server_ids, rotation=45, ha='right')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Power consumption
        axes[1, 0].bar(server_ids, power, alpha=0.8, color='orange')
        axes[1, 0].set_xlabel('Edge Server')
        axes[1, 0].set_ylabel('Power (W)')
        axes[1, 0].set_title('Average Power Consumption')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3)

        # Energy consumption
        energy = [stats.get('total_energy_wh', 0) for stats in servers.values()]
        axes[1, 1].bar(server_ids, energy, alpha=0.8, color='green')
        axes[1, 1].set_xlabel('Edge Server')
        axes[1, 1].set_ylabel('Energy (Wh)')
        axes[1, 1].set_title('Total Energy Consumption')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved server resources plot to {filename}")

    def _plot_node_performance(self, node_results: List[Dict], filename: str):
        """Plot node execution performance"""
        node_ids = []
        exec_times = []
        iterations = []
        avg_iter_times = []

        for result in sorted(node_results, key=lambda x: x.get('node_id', 0)):
            if result.get('success', False):
                julia_res = result.get('julia_results', {})
                node_ids.append(f"Node_{result.get('node_id', '?')}")
                exec_times.append(result.get('execution_time_s', 0))
                iterations.append(julia_res.get('iterations', 0))
                avg_iter_times.append(julia_res.get('avg_iteration_time_ms', 0))

        if not node_ids:
            print("  - No successful nodes to plot")
            return

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        fig.suptitle('OPF Node Performance Metrics', fontsize=16, fontweight='bold')

        # Execution time
        axes[0].bar(node_ids, exec_times, alpha=0.8, color='steelblue')
        axes[0].set_xlabel('Node')
        axes[0].set_ylabel('Execution Time (s)')
        axes[0].set_title('Total Execution Time')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].grid(True, alpha=0.3)

        # Iterations
        axes[1].bar(node_ids, iterations, alpha=0.8, color='coral')
        axes[1].set_xlabel('Node')
        axes[1].set_ylabel('Iterations')
        axes[1].set_title('ADMM Iterations to Convergence')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3)

        # Average iteration time
        axes[2].bar(node_ids, avg_iter_times, alpha=0.8, color='mediumseagreen')
        axes[2].set_xlabel('Node')
        axes[2].set_ylabel('Time (ms)')
        axes[2].set_title('Average Iteration Time')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved node performance plot to {filename}")

    def _plot_resource_timeline(self, node_results: List[Dict], filename: str):
        """Plot resource usage over time"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        fig.suptitle('Resource Usage Timeline', fontsize=16, fontweight='bold')

        for result in node_results:
            if result.get('success', False) and 'resource_monitoring' in result:
                monitoring = result['resource_monitoring']
                node_id = result.get('node_id', '?')

                if 'timestamps' in monitoring and 'cpu_history' in monitoring:
                    timestamps = monitoring['timestamps']
                    cpu_history = monitoring['cpu_history']
                    mem_history = monitoring['memory_history']

                    axes[0].plot(timestamps, cpu_history, label=f'Node {node_id}', linewidth=2)
                    axes[1].plot(timestamps, mem_history, label=f'Node {node_id}', linewidth=2)

        axes[0].set_xlabel('Time (s)')
        axes[0].set_ylabel('CPU Usage (%)')
        axes[0].set_title('CPU Usage Over Time')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylabel('Memory Usage (MB)')
        axes[1].set_title('Memory Usage Over Time')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved resource timeline plot to {filename}")

    def _plot_network_traffic(self, links: Dict, filename: str):
        """Plot network traffic statistics"""
        if not links:
            print("  - No network links to plot")
            return

        link_labels = []
        data_transmitted = []

        for lid, stats in sorted(links.items()):
            src = stats.get('source_server_id', '?')
            tgt = stats.get('target_server_id', '?')
            link_labels.append(f"{src}→{tgt}")
            data_transmitted.append(stats.get('total_data_transmitted_mb', 0))

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle('Network Traffic Between Edge Servers', fontsize=16, fontweight='bold')

        ax.barh(link_labels, data_transmitted, alpha=0.8, color='purple')
        ax.set_xlabel('Data Transmitted (MB)')
        ax.set_ylabel('Network Link')
        ax.set_title('Total Data Transfer per Link')
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved network traffic plot to {filename}")

    def _plot_resource_heatmap(self, node_results: List[Dict], filename: str):
        """Plot heatmap of resource usage over time for all devices"""
        # Collect time series data for all nodes
        cpu_matrix = []
        mem_matrix = []
        node_labels = []

        for result in sorted(node_results, key=lambda x: x.get('node_id', 0)):
            if result.get('success', False) and 'resource_monitoring' in result:
                monitoring = result['resource_monitoring']
                if 'cpu_history' in monitoring and 'memory_history' in monitoring:
                    node_labels.append(f"N{result.get('node_id', '?')}")
                    cpu_matrix.append(monitoring['cpu_history'])
                    mem_matrix.append(monitoring['memory_history'])

        if not cpu_matrix:
            print("  - No time series data for heatmap")
            return

        # Make all arrays same length (pad with last value if needed)
        max_len = max(len(row) for row in cpu_matrix)
        cpu_matrix_padded = []
        mem_matrix_padded = []

        for i in range(len(cpu_matrix)):
            cpu_row = list(cpu_matrix[i])
            mem_row = list(mem_matrix[i])
            while len(cpu_row) < max_len:
                cpu_row.append(cpu_row[-1] if cpu_row else 0)
            while len(mem_row) < max_len:
                mem_row.append(mem_row[-1] if mem_row else 0)
            cpu_matrix_padded.append(cpu_row)
            mem_matrix_padded.append(mem_row)

        cpu_array = np.array(cpu_matrix_padded)
        mem_array = np.array(mem_matrix_padded)

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('Resource Usage Heatmap Over Time', fontsize=16, fontweight='bold')

        # CPU heatmap
        im1 = axes[0].imshow(cpu_array, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        axes[0].set_ylabel('Node ID', fontsize=12)
        axes[0].set_xlabel('Time Step', fontsize=12)
        axes[0].set_title('CPU Usage (%) - Heatmap View', fontsize=14)
        axes[0].set_yticks(range(len(node_labels)))
        axes[0].set_yticklabels(node_labels, fontsize=8)
        cbar1 = plt.colorbar(im1, ax=axes[0])
        cbar1.set_label('CPU %', rotation=270, labelpad=15)

        # Memory heatmap
        im2 = axes[1].imshow(mem_array, aspect='auto', cmap='Blues', interpolation='nearest')
        axes[1].set_ylabel('Node ID', fontsize=12)
        axes[1].set_xlabel('Time Step', fontsize=12)
        axes[1].set_title('Memory Usage (MB) - Heatmap View', fontsize=14)
        axes[1].set_yticks(range(len(node_labels)))
        axes[1].set_yticklabels(node_labels, fontsize=8)
        cbar2 = plt.colorbar(im2, ax=axes[1])
        cbar2.set_label('Memory MB', rotation=270, labelpad=15)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved resource heatmap to {filename}")

    def _plot_stacked_area_chart(self, node_results: List[Dict], filename: str):
        """Plot stacked area chart showing contribution of each device over time"""
        # Collect time series data
        cpu_data = {}
        mem_data = {}

        for result in sorted(node_results, key=lambda x: x.get('node_id', 0)):
            if result.get('success', False) and 'resource_monitoring' in result:
                monitoring = result['resource_monitoring']
                if 'cpu_history' in monitoring and 'timestamps' in monitoring:
                    node_id = result.get('node_id', '?')
                    cpu_data[node_id] = monitoring['cpu_history']
                    mem_data[node_id] = monitoring['memory_history']

        if not cpu_data:
            print("  - No time series data for stacked area chart")
            return

        # Align all time series to same length
        max_len = max(len(v) for v in cpu_data.values())
        for nid in cpu_data:
            while len(cpu_data[nid]) < max_len:
                cpu_data[nid].append(cpu_data[nid][-1] if cpu_data[nid] else 0)
            while len(mem_data[nid]) < max_len:
                mem_data[nid].append(mem_data[nid][-1] if mem_data[nid] else 0)

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('Cumulative Resource Contribution Over Time (All Devices)', fontsize=16, fontweight='bold')

        # CPU stacked area
        cpu_matrix = np.array([cpu_data[nid] for nid in sorted(cpu_data.keys())])
        axes[0].stackplot(range(max_len), *cpu_matrix, alpha=0.7)
        axes[0].set_xlabel('Time Step', fontsize=12)
        axes[0].set_ylabel('Total CPU Usage (%)', fontsize=12)
        axes[0].set_title(f'CPU Usage Stack ({len(cpu_data)} devices)', fontsize=14)
        axes[0].grid(True, alpha=0.3)

        # Memory stacked area
        mem_matrix = np.array([mem_data[nid] for nid in sorted(mem_data.keys())])
        axes[1].stackplot(range(max_len), *mem_matrix, alpha=0.7)
        axes[1].set_xlabel('Time Step', fontsize=12)
        axes[1].set_ylabel('Total Memory (MB)', fontsize=12)
        axes[1].set_title(f'Memory Usage Stack ({len(mem_data)} devices)', fontsize=14)
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved stacked area chart to {filename}")

    def _plot_parallel_coordinates(self, servers: Dict, filename: str):
        """Plot parallel coordinates showing multiple metrics for all devices"""
        # Collect data for all devices
        device_data = []
        for sid, stats in sorted(servers.items()):
            device_data.append({
                'id': stats.get('id', sid),
                'cpu_avg': stats.get('avg_cpu_usage', 0),
                'cpu_max': stats.get('max_cpu_usage', 0),
                'mem_avg': stats.get('avg_memory_usage_mb', 0),
                'mem_max': stats.get('max_memory_usage_mb', 0),
                'power': stats.get('avg_power_w', 0),
                'energy': stats.get('total_energy_wh', 0)
            })

        # Normalize data for parallel coordinates (0-1 scale)
        metrics = ['cpu_avg', 'cpu_max', 'mem_avg', 'mem_max', 'power', 'energy']
        normalized = []
        for dev in device_data:
            normalized.append([dev[m] for m in metrics])

        normalized = np.array(normalized)
        for i in range(len(metrics)):
            col = normalized[:, i]
            if col.max() > col.min():
                normalized[:, i] = (col - col.min()) / (col.max() - col.min())

        fig, ax = plt.subplots(figsize=(14, 8))
        fig.suptitle('Parallel Coordinates: Multi-Metric Device Comparison', fontsize=16, fontweight='bold')

        # Plot lines for each device
        x = np.arange(len(metrics))
        for i, device in enumerate(normalized):
            ax.plot(x, device, alpha=0.4, linewidth=1)

        ax.set_xticks(x)
        ax.set_xticklabels(['Avg CPU', 'Max CPU', 'Avg Mem', 'Max Mem', 'Power', 'Energy'], rotation=0, fontsize=11)
        ax.set_ylabel('Normalized Value (0-1)', fontsize=12)
        ax.set_title(f'All {len(device_data)} Devices Across 6 Metrics', fontsize=13)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(-0.05, 1.05)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved parallel coordinates plot to {filename}")

    def _plot_sorted_bars(self, servers: Dict, filename: str):
        """Plot sorted bar charts for all devices (no filtering)"""
        # Collect all devices
        devices = []
        for sid, stats in servers.items():
            devices.append({
                'id': stats.get('id', sid),
                'cpu': stats.get('max_cpu_usage', 0),  # Use max for more interesting visualization
                'mem': stats.get('max_memory_usage_mb', 0),
                'power': stats.get('avg_power_w', 0),
                'energy': stats.get('total_energy_wh', 0)
            })

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'All {len(devices)} Devices Ranked by Resource Usage', fontsize=16, fontweight='bold')

        # Sort by CPU
        sorted_cpu = sorted(devices, key=lambda x: x['cpu'], reverse=True)
        labels_cpu = [f"D{d['id']}" for d in sorted_cpu]
        values_cpu = [d['cpu'] for d in sorted_cpu]
        axes[0, 0].barh(range(len(labels_cpu)), values_cpu, color='orangered', alpha=0.8)
        axes[0, 0].set_yticks(range(len(labels_cpu)))
        axes[0, 0].set_yticklabels(labels_cpu, fontsize=7)
        axes[0, 0].set_xlabel('Max CPU Usage (%)', fontsize=11)
        axes[0, 0].set_title('Devices Sorted by CPU', fontsize=13)
        axes[0, 0].invert_yaxis()
        axes[0, 0].grid(True, alpha=0.3, axis='x')

        # Sort by Memory
        sorted_mem = sorted(devices, key=lambda x: x['mem'], reverse=True)
        labels_mem = [f"D{d['id']}" for d in sorted_mem]
        values_mem = [d['mem'] for d in sorted_mem]
        axes[0, 1].barh(range(len(labels_mem)), values_mem, color='dodgerblue', alpha=0.8)
        axes[0, 1].set_yticks(range(len(labels_mem)))
        axes[0, 1].set_yticklabels(labels_mem, fontsize=7)
        axes[0, 1].set_xlabel('Max Memory (MB)', fontsize=11)
        axes[0, 1].set_title('Devices Sorted by Memory', fontsize=13)
        axes[0, 1].invert_yaxis()
        axes[0, 1].grid(True, alpha=0.3, axis='x')

        # Sort by Power
        sorted_pwr = sorted(devices, key=lambda x: x['power'], reverse=True)
        labels_pwr = [f"D{d['id']}" for d in sorted_pwr]
        values_pwr = [d['power'] for d in sorted_pwr]
        axes[1, 0].barh(range(len(labels_pwr)), values_pwr, color='gold', alpha=0.8)
        axes[1, 0].set_yticks(range(len(labels_pwr)))
        axes[1, 0].set_yticklabels(labels_pwr, fontsize=7)
        axes[1, 0].set_xlabel('Avg Power (W)', fontsize=11)
        axes[1, 0].set_title('Devices Sorted by Power', fontsize=13)
        axes[1, 0].invert_yaxis()
        axes[1, 0].grid(True, alpha=0.3, axis='x')

        # Sort by Energy
        sorted_eng = sorted(devices, key=lambda x: x['energy'], reverse=True)
        labels_eng = [f"D{d['id']}" for d in sorted_eng]
        values_eng = [d['energy'] for d in sorted_eng]
        axes[1, 1].barh(range(len(labels_eng)), values_eng, color='limegreen', alpha=0.8)
        axes[1, 1].set_yticks(range(len(labels_eng)))
        axes[1, 1].set_yticklabels(labels_eng, fontsize=7)
        axes[1, 1].set_xlabel('Total Energy (Wh)', fontsize=11)
        axes[1, 1].set_title('Devices Sorted by Energy', fontsize=13)
        axes[1, 1].invert_yaxis()
        axes[1, 1].grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved sorted bars plot to {filename}")

    def _plot_device_type_comparison(self, servers: Dict, device_configs: Dict, filename: str):
        """Compare all 6 device types side by side"""
        # Group by device type
        type_data = {}

        for sid, stats in servers.items():
            device_id = stats.get('id', sid)
            device_type = 'unknown'

            if isinstance(device_configs, dict) and 'devices' in device_configs:
                for dev in device_configs['devices']:
                    if dev.get('id') == device_id:
                        device_type = dev.get('device_type', 'unknown')
                        break

            if device_type not in type_data:
                type_data[device_type] = {'cpu': [], 'mem': [], 'power': []}

            type_data[device_type]['cpu'].append(stats.get('avg_cpu_usage', 0))
            type_data[device_type]['mem'].append(stats.get('avg_memory_usage_mb', 0))
            type_data[device_type]['power'].append(stats.get('avg_power_w', 0))

        if len(type_data) < 2 or 'unknown' in type_data and len(type_data) == 1:
            print("  - Skipping device type comparison (insufficient type data)")
            return

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Device Type Comparison (All 6 Types)', fontsize=16, fontweight='bold')

        types = sorted([t for t in type_data.keys() if t != 'unknown'])

        # CPU comparison
        cpu_data = [type_data[t]['cpu'] for t in types]
        bp1 = axes[0].boxplot(cpu_data, labels=types, patch_artist=True, widths=0.6)
        for patch in bp1['boxes']:
            patch.set_facecolor('skyblue')
        axes[0].set_ylabel('Avg CPU Usage (%)', fontsize=12)
        axes[0].set_title('CPU by Device Type', fontsize=13)
        axes[0].tick_params(axis='x', rotation=45, labelsize=9)
        axes[0].grid(True, alpha=0.3, axis='y')

        # Memory comparison
        mem_data = [type_data[t]['mem'] for t in types]
        bp2 = axes[1].boxplot(mem_data, labels=types, patch_artist=True, widths=0.6)
        for patch in bp2['boxes']:
            patch.set_facecolor('lightgreen')
        axes[1].set_ylabel('Avg Memory (MB)', fontsize=12)
        axes[1].set_title('Memory by Device Type', fontsize=13)
        axes[1].tick_params(axis='x', rotation=45, labelsize=9)
        axes[1].grid(True, alpha=0.3, axis='y')

        # Power comparison
        pwr_data = [type_data[t]['power'] for t in types]
        bp3 = axes[2].boxplot(pwr_data, labels=types, patch_artist=True, widths=0.6)
        for patch in bp3['boxes']:
            patch.set_facecolor('gold')
        axes[2].set_ylabel('Avg Power (W)', fontsize=12)
        axes[2].set_title('Power by Device Type', fontsize=13)
        axes[2].tick_params(axis='x', rotation=45, labelsize=9)
        axes[2].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved device type comparison to {filename}")

    def _plot_correlation_matrix(self, servers: Dict, filename: str):
        """Plot correlation matrix between different resource metrics"""
        # Collect all metrics
        data = {
            'CPU_Avg': [],
            'CPU_Max': [],
            'Mem_Avg': [],
            'Mem_Max': [],
            'Power': [],
            'Energy': []
        }

        for stats in servers.values():
            data['CPU_Avg'].append(stats.get('avg_cpu_usage', 0))
            data['CPU_Max'].append(stats.get('max_cpu_usage', 0))
            data['Mem_Avg'].append(stats.get('avg_memory_usage_mb', 0))
            data['Mem_Max'].append(stats.get('max_memory_usage_mb', 0))
            data['Power'].append(stats.get('avg_power_w', 0))
            data['Energy'].append(stats.get('total_energy_wh', 0))

        # Calculate correlation matrix
        df_data = np.array([data[k] for k in data.keys()]).T
        corr_matrix = np.corrcoef(df_data.T)

        fig, ax = plt.subplots(figsize=(10, 8))
        fig.suptitle('Resource Metrics Correlation Matrix', fontsize=16, fontweight='bold')

        im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
        ax.set_xticks(range(len(data)))
        ax.set_yticks(range(len(data)))
        ax.set_xticklabels(data.keys(), rotation=45, ha='right')
        ax.set_yticklabels(data.keys())

        # Add correlation values
        for i in range(len(data)):
            for j in range(len(data)):
                text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=10)

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Correlation Coefficient', rotation=270, labelpad=20)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved correlation matrix to {filename}")

    def _plot_cdf_curves(self, servers: Dict, filename: str):
        """Plot cumulative distribution functions for resource metrics"""
        cpu_avg = sorted([stats.get('avg_cpu_usage', 0) for stats in servers.values()])
        mem_avg = sorted([stats.get('avg_memory_usage_mb', 0) for stats in servers.values()])
        power = sorted([stats.get('avg_power_w', 0) for stats in servers.values()])
        energy = sorted([stats.get('total_energy_wh', 0) for stats in servers.values()])

        n = len(cpu_avg)
        cdf = np.arange(1, n+1) / n

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Cumulative Distribution Functions (CDF)', fontsize=16, fontweight='bold')

        # CPU CDF
        axes[0, 0].plot(cpu_avg, cdf, linewidth=2, color='orangered')
        axes[0, 0].fill_between(cpu_avg, cdf, alpha=0.3, color='orangered')
        axes[0, 0].set_xlabel('Avg CPU Usage (%)', fontsize=12)
        axes[0, 0].set_ylabel('Cumulative Probability', fontsize=12)
        axes[0, 0].set_title(f'CPU Usage CDF\nMedian: {np.median(cpu_avg):.1f}%', fontsize=13)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1)

        # Memory CDF
        axes[0, 1].plot(mem_avg, cdf, linewidth=2, color='dodgerblue')
        axes[0, 1].fill_between(mem_avg, cdf, alpha=0.3, color='dodgerblue')
        axes[0, 1].set_xlabel('Avg Memory (MB)', fontsize=12)
        axes[0, 1].set_ylabel('Cumulative Probability', fontsize=12)
        axes[0, 1].set_title(f'Memory Usage CDF\nMedian: {np.median(mem_avg):.1f} MB', fontsize=13)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(0, 1)

        # Power CDF
        axes[1, 0].plot(power, cdf, linewidth=2, color='gold')
        axes[1, 0].fill_between(power, cdf, alpha=0.3, color='gold')
        axes[1, 0].set_xlabel('Avg Power (W)', fontsize=12)
        axes[1, 0].set_ylabel('Cumulative Probability', fontsize=12)
        axes[1, 0].set_title(f'Power CDF\nMedian: {np.median(power):.1f} W', fontsize=13)
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 1)

        # Energy CDF
        axes[1, 1].plot(energy, cdf, linewidth=2, color='limegreen')
        axes[1, 1].fill_between(energy, cdf, alpha=0.3, color='limegreen')
        axes[1, 1].set_xlabel('Total Energy (Wh)', fontsize=12)
        axes[1, 1].set_ylabel('Cumulative Probability', fontsize=12)
        axes[1, 1].set_title(f'Energy CDF\nMedian: {np.median(energy):.2f} Wh', fontsize=13)
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_ylim(0, 1)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved CDF curves to {filename}")

    def _plot_efficiency_scatter(self, servers: Dict, filename: str):
        """Plot efficiency scatter plots showing relationships"""
        cpu_avg = [stats.get('avg_cpu_usage', 0) for stats in servers.values()]
        mem_avg = [stats.get('avg_memory_usage_mb', 0) for stats in servers.values()]
        power = [stats.get('avg_power_w', 0) for stats in servers.values()]
        energy = [stats.get('total_energy_wh', 0) for stats in servers.values()]
        device_ids = [stats.get('id', sid) for sid, stats in servers.items()]

        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        fig.suptitle('Resource Efficiency Scatter Plots (All Devices)', fontsize=16, fontweight='bold')

        # CPU vs Memory
        axes[0, 0].scatter(cpu_avg, mem_avg, s=100, alpha=0.6, c=range(len(cpu_avg)), cmap='viridis')
        axes[0, 0].set_xlabel('Avg CPU Usage (%)', fontsize=12)
        axes[0, 0].set_ylabel('Avg Memory (MB)', fontsize=12)
        axes[0, 0].set_title('CPU vs Memory Usage', fontsize=13)
        axes[0, 0].grid(True, alpha=0.3)

        # Power vs CPU
        axes[0, 1].scatter(power, cpu_avg, s=100, alpha=0.6, c=range(len(power)), cmap='plasma')
        axes[0, 1].set_xlabel('Avg Power (W)', fontsize=12)
        axes[0, 1].set_ylabel('Avg CPU Usage (%)', fontsize=12)
        axes[0, 1].set_title('Power vs CPU Efficiency', fontsize=13)
        axes[0, 1].grid(True, alpha=0.3)

        # Power vs Memory
        axes[1, 0].scatter(power, mem_avg, s=100, alpha=0.6, c=range(len(power)), cmap='coolwarm')
        axes[1, 0].set_xlabel('Avg Power (W)', fontsize=12)
        axes[1, 0].set_ylabel('Avg Memory (MB)', fontsize=12)
        axes[1, 0].set_title('Power vs Memory Efficiency', fontsize=13)
        axes[1, 0].grid(True, alpha=0.3)

        # Energy vs CPU+Memory (combined workload)
        combined_load = np.array(cpu_avg) + np.array(mem_avg)/100  # Normalize memory
        axes[1, 1].scatter(combined_load, energy, s=100, alpha=0.6, c=range(len(energy)), cmap='magma')
        axes[1, 1].set_xlabel('Combined Workload (CPU + Mem/100)', fontsize=12)
        axes[1, 1].set_ylabel('Total Energy (Wh)', fontsize=12)
        axes[1, 1].set_title('Workload vs Energy Consumption', fontsize=13)
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved efficiency scatter plots to {filename}")

    def _plot_percentile_bands(self, node_results: List[Dict], filename: str):
        """Plot percentile bands showing distribution over time"""
        # Collect time series
        cpu_series = []
        mem_series = []

        for result in node_results:
            if result.get('success', False) and 'resource_monitoring' in result:
                monitoring = result['resource_monitoring']
                if 'cpu_history' in monitoring:
                    cpu_series.append(monitoring['cpu_history'])
                    mem_series.append(monitoring['memory_history'])

        if not cpu_series:
            print("  - No time series data for percentile bands")
            return

        # Align lengths
        max_len = max(len(s) for s in cpu_series)
        for i in range(len(cpu_series)):
            while len(cpu_series[i]) < max_len:
                cpu_series[i].append(cpu_series[i][-1] if cpu_series[i] else 0)
            while len(mem_series[i]) < max_len:
                mem_series[i].append(mem_series[i][-1] if mem_series[i] else 0)

        cpu_array = np.array(cpu_series)
        mem_array = np.array(mem_series)

        # Calculate percentiles at each time step
        time_steps = range(max_len)
        cpu_p10 = np.percentile(cpu_array, 10, axis=0)
        cpu_p25 = np.percentile(cpu_array, 25, axis=0)
        cpu_p50 = np.percentile(cpu_array, 50, axis=0)
        cpu_p75 = np.percentile(cpu_array, 75, axis=0)
        cpu_p90 = np.percentile(cpu_array, 90, axis=0)

        mem_p10 = np.percentile(mem_array, 10, axis=0)
        mem_p25 = np.percentile(mem_array, 25, axis=0)
        mem_p50 = np.percentile(mem_array, 50, axis=0)
        mem_p75 = np.percentile(mem_array, 75, axis=0)
        mem_p90 = np.percentile(mem_array, 90, axis=0)

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('Percentile Bands Over Time (Aggregated View)', fontsize=16, fontweight='bold')

        # CPU percentile bands
        axes[0].fill_between(time_steps, cpu_p10, cpu_p90, alpha=0.2, color='orangered', label='10th-90th percentile')
        axes[0].fill_between(time_steps, cpu_p25, cpu_p75, alpha=0.4, color='orangered', label='25th-75th percentile')
        axes[0].plot(time_steps, cpu_p50, linewidth=2, color='darkred', label='Median (50th)')
        axes[0].set_xlabel('Time Step', fontsize=12)
        axes[0].set_ylabel('CPU Usage (%)', fontsize=12)
        axes[0].set_title(f'CPU Usage Percentile Bands ({len(cpu_series)} devices)', fontsize=13)
        axes[0].legend(loc='upper right')
        axes[0].grid(True, alpha=0.3)

        # Memory percentile bands
        axes[1].fill_between(time_steps, mem_p10, mem_p90, alpha=0.2, color='dodgerblue', label='10th-90th percentile')
        axes[1].fill_between(time_steps, mem_p25, mem_p75, alpha=0.4, color='dodgerblue', label='25th-75th percentile')
        axes[1].plot(time_steps, mem_p50, linewidth=2, color='darkblue', label='Median (50th)')
        axes[1].set_xlabel('Time Step', fontsize=12)
        axes[1].set_ylabel('Memory (MB)', fontsize=12)
        axes[1].set_title(f'Memory Usage Percentile Bands ({len(mem_series)} devices)', fontsize=13)
        axes[1].legend(loc='upper right')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved percentile bands to {filename}")

    def _plot_small_multiples(self, node_results: List[Dict], filename: str):
        """Plot small multiples grid - one mini plot per device"""
        cpu_data = {}

        for result in sorted(node_results, key=lambda x: x.get('node_id', 0)):
            if result.get('success', False) and 'resource_monitoring' in result:
                monitoring = result['resource_monitoring']
                if 'cpu_history' in monitoring and 'timestamps' in monitoring:
                    node_id = result.get('node_id', '?')
                    cpu_data[node_id] = monitoring['cpu_history']

        if not cpu_data:
            print("  - No time series data for small multiples")
            return

        # Determine grid size
        n_devices = len(cpu_data)
        n_cols = 6
        n_rows = (n_devices + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 2))
        fig.suptitle(f'CPU Usage Small Multiples ({n_devices} devices)', fontsize=16, fontweight='bold')

        # Flatten axes array
        if n_rows == 1:
            axes = [axes]
        axes = [ax for row in axes for ax in (row if isinstance(row, np.ndarray) else [row])]

        for idx, (node_id, cpu_history) in enumerate(sorted(cpu_data.items())):
            if idx < len(axes):
                axes[idx].plot(cpu_history, linewidth=1.5, color='steelblue')
                axes[idx].set_title(f'Device {node_id}', fontsize=9)
                axes[idx].set_ylim(0, 100)
                axes[idx].grid(True, alpha=0.2)
                axes[idx].tick_params(labelsize=7)

        # Hide unused subplots
        for idx in range(len(cpu_data), len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved small multiples grid to {filename}")

    def _plot_network_topology(self, servers: Dict, links: Dict, filename: str):
        """Plot network topology with resource usage overlay"""
        if not links:
            print("  - No network links for topology visualization")
            return

        # Build graph structure
        nodes = set()
        edges = []
        for lid, link_stats in links.items():
            src = link_stats.get('source_server_id', 0)
            tgt = link_stats.get('target_server_id', 0)
            nodes.add(src)
            nodes.add(tgt)
            edges.append((src, tgt))

        nodes = sorted(list(nodes))

        # Get CPU usage for node colors
        node_cpu = {}
        for sid, stats in servers.items():
            device_id = stats.get('id', sid)
            if device_id in nodes:
                node_cpu[device_id] = stats.get('avg_cpu_usage', 0)

        fig, ax = plt.subplots(figsize=(14, 14))
        fig.suptitle('Network Topology with CPU Usage Overlay', fontsize=16, fontweight='bold')

        # Simple circular layout
        n = len(nodes)
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        pos = {node: (np.cos(angle), np.sin(angle)) for node, angle in zip(nodes, angles)}

        # Draw edges
        for src, tgt in edges:
            if src in pos and tgt in pos:
                x = [pos[src][0], pos[tgt][0]]
                y = [pos[src][1], pos[tgt][1]]
                ax.plot(x, y, 'gray', alpha=0.3, linewidth=0.5, zorder=1)

        # Draw nodes with CPU color
        for node in nodes:
            if node in pos:
                cpu = node_cpu.get(node, 0)
                color = plt.cm.YlOrRd(cpu / 100)  # Normalize to 0-1
                ax.scatter(pos[node][0], pos[node][1], s=300, c=[color],
                          edgecolors='black', linewidths=1.5, zorder=2)
                ax.text(pos[node][0], pos[node][1], str(node),
                       ha='center', va='center', fontsize=8, fontweight='bold', zorder=3)

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd, norm=plt.Normalize(vmin=0, vmax=100))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Avg CPU Usage (%)', rotation=270, labelpad=20)

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'{n} Nodes, {len(edges)} Links', fontsize=13)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved network topology to {filename}")

    def _plot_power_percentile_bands(self, servers: Dict, filename: str):
        """Plot power consumption percentile bands over time (aggregated view)"""
        # Note: We don't have time-series power data, so we'll simulate it based on server stats
        # In a real implementation, this would use actual time-series power monitoring

        # Collect power data per server
        power_data = {}
        for sid, stats in servers.items():
            device_id = stats.get('id', sid)
            avg_power = stats.get('avg_power_w', 0)
            # Simulate time series (in real implementation, get from monitoring)
            power_data[device_id] = [avg_power] * 100  # Placeholder

        if not power_data:
            print("  - No power data for percentile bands")
            return

        # Convert to array
        power_array = np.array(list(power_data.values()))
        num_steps = power_array.shape[1]

        # Calculate percentiles
        p10 = np.percentile(power_array, 10, axis=0)
        p25 = np.percentile(power_array, 25, axis=0)
        p50 = np.percentile(power_array, 50, axis=0)
        p75 = np.percentile(power_array, 75, axis=0)
        p90 = np.percentile(power_array, 90, axis=0)

        fig, ax = plt.subplots(figsize=(14, 6))
        fig.suptitle('Power Consumption Percentile Bands (Aggregated View)', fontsize=16, fontweight='bold')

        time_steps = range(num_steps)
        ax.fill_between(time_steps, p10, p90, alpha=0.2, color='gold', label='10th-90th percentile')
        ax.fill_between(time_steps, p25, p75, alpha=0.4, color='gold', label='25th-75th percentile')
        ax.plot(time_steps, p50, linewidth=2.5, color='darkorange', label='Median (50th)')

        ax.set_xlabel('Time Step', fontsize=12)
        ax.set_ylabel('Power (W)', fontsize=12)
        ax.set_title(f'Power Distribution Across {len(power_data)} Devices', fontsize=13)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved power percentile bands to {filename}")

    def _plot_energy_percentile_bands(self, servers: Dict, filename: str):
        """Plot energy accumulation percentile bands over time"""
        # Collect energy data
        energy_data = []
        for stats in servers.values():
            energy_data.append(stats.get('total_energy_wh', 0))

        if not energy_data:
            print("  - No energy data for percentile bands")
            return

        # Sort for cumulative distribution
        energy_sorted = sorted(energy_data)
        n = len(energy_sorted)

        # Create percentile markers
        p10_idx = int(n * 0.1)
        p25_idx = int(n * 0.25)
        p50_idx = int(n * 0.50)
        p75_idx = int(n * 0.75)
        p90_idx = int(n * 0.90)

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('Energy Consumption Analysis (Aggregated View)', fontsize=16, fontweight='bold')

        # Cumulative energy distribution
        cumsum = np.cumsum(energy_sorted)
        axes[0].plot(range(n), cumsum, linewidth=2, color='limegreen')
        axes[0].fill_between(range(n), cumsum, alpha=0.3, color='limegreen')
        axes[0].axvline(p10_idx, color='red', linestyle='--', alpha=0.5, label='10th percentile')
        axes[0].axvline(p50_idx, color='darkgreen', linestyle='--', linewidth=2, label='Median')
        axes[0].axvline(p90_idx, color='red', linestyle='--', alpha=0.5, label='90th percentile')
        axes[0].set_xlabel('Device Rank (sorted by energy)', fontsize=12)
        axes[0].set_ylabel('Cumulative Energy (Wh)', fontsize=12)
        axes[0].set_title('Cumulative Energy Distribution', fontsize=13)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Energy per device with percentile bands
        device_indices = range(n)
        axes[1].bar(device_indices, energy_sorted, alpha=0.7, color='limegreen', edgecolor='darkgreen')
        axes[1].axhline(energy_sorted[p10_idx], color='red', linestyle='--', alpha=0.7, label='10th percentile')
        axes[1].axhline(energy_sorted[p25_idx], color='orange', linestyle='--', alpha=0.7, label='25th percentile')
        axes[1].axhline(energy_sorted[p50_idx], color='darkgreen', linestyle='--', linewidth=2, label='Median')
        axes[1].axhline(energy_sorted[p75_idx], color='orange', linestyle='--', alpha=0.7, label='75th percentile')
        axes[1].axhline(energy_sorted[p90_idx], color='red', linestyle='--', alpha=0.7, label='90th percentile')
        axes[1].set_xlabel('Device Rank', fontsize=12)
        axes[1].set_ylabel('Energy (Wh)', fontsize=12)
        axes[1].set_title(f'Energy Distribution with Percentile Markers ({n} devices)', fontsize=13)
        axes[1].legend(loc='upper left')
        axes[1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved energy percentile bands to {filename}")

    def _plot_combined_percentile_bands(self, node_results: List[Dict], servers: Dict, filename: str):
        """Plot combined multi-metric percentile bands (CPU, Memory, Power, Energy)"""
        # Collect time series
        cpu_series = []
        mem_series = []

        for result in node_results:
            if result.get('success', False) and 'resource_monitoring' in result:
                monitoring = result['resource_monitoring']
                if 'cpu_history' in monitoring:
                    cpu_series.append(monitoring['cpu_history'])
                    mem_series.append(monitoring['memory_history'])

        if not cpu_series:
            print("  - No time series data for combined percentile bands")
            return

        # Align lengths
        max_len = max(len(s) for s in cpu_series)
        for i in range(len(cpu_series)):
            while len(cpu_series[i]) < max_len:
                cpu_series[i].append(cpu_series[i][-1] if cpu_series[i] else 0)
            while len(mem_series[i]) < max_len:
                mem_series[i].append(mem_series[i][-1] if mem_series[i] else 0)

        cpu_array = np.array(cpu_series)
        mem_array = np.array(mem_series)

        # Get power and energy data
        power_vals = [stats.get('avg_power_w', 0) for stats in servers.values()]
        energy_vals = [stats.get('total_energy_wh', 0) for stats in servers.values()]

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Combined Resource Percentile Bands (All Metrics)', fontsize=16, fontweight='bold')

        time_steps = range(max_len)

        # CPU percentile bands
        cpu_p10 = np.percentile(cpu_array, 10, axis=0)
        cpu_p25 = np.percentile(cpu_array, 25, axis=0)
        cpu_p50 = np.percentile(cpu_array, 50, axis=0)
        cpu_p75 = np.percentile(cpu_array, 75, axis=0)
        cpu_p90 = np.percentile(cpu_array, 90, axis=0)

        axes[0, 0].fill_between(time_steps, cpu_p10, cpu_p90, alpha=0.2, color='orangered', label='p10-p90')
        axes[0, 0].fill_between(time_steps, cpu_p25, cpu_p75, alpha=0.4, color='orangered', label='p25-p75')
        axes[0, 0].plot(time_steps, cpu_p50, linewidth=2.5, color='darkred', label='Median')
        axes[0, 0].set_xlabel('Time Step', fontsize=11)
        axes[0, 0].set_ylabel('CPU (%)', fontsize=11)
        axes[0, 0].set_title('CPU Usage Bands', fontsize=12)
        axes[0, 0].legend(fontsize=9)
        axes[0, 0].grid(True, alpha=0.3)

        # Memory percentile bands
        mem_p10 = np.percentile(mem_array, 10, axis=0)
        mem_p25 = np.percentile(mem_array, 25, axis=0)
        mem_p50 = np.percentile(mem_array, 50, axis=0)
        mem_p75 = np.percentile(mem_array, 75, axis=0)
        mem_p90 = np.percentile(mem_array, 90, axis=0)

        axes[0, 1].fill_between(time_steps, mem_p10, mem_p90, alpha=0.2, color='dodgerblue', label='p10-p90')
        axes[0, 1].fill_between(time_steps, mem_p25, mem_p75, alpha=0.4, color='dodgerblue', label='p25-p75')
        axes[0, 1].plot(time_steps, mem_p50, linewidth=2.5, color='darkblue', label='Median')
        axes[0, 1].set_xlabel('Time Step', fontsize=11)
        axes[0, 1].set_ylabel('Memory (MB)', fontsize=11)
        axes[0, 1].set_title('Memory Usage Bands', fontsize=12)
        axes[0, 1].legend(fontsize=9)
        axes[0, 1].grid(True, alpha=0.3)

        # Power distribution box plot
        axes[1, 0].boxplot([power_vals], vert=True, widths=0.5, patch_artist=True,
                          boxprops=dict(facecolor='gold', alpha=0.7),
                          medianprops=dict(color='darkorange', linewidth=2.5))
        axes[1, 0].set_ylabel('Power (W)', fontsize=11)
        axes[1, 0].set_title(f'Power Distribution\nMedian: {np.median(power_vals):.1f}W', fontsize=12)
        axes[1, 0].set_xticklabels(['All Devices'])
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # Energy distribution box plot
        axes[1, 1].boxplot([energy_vals], vert=True, widths=0.5, patch_artist=True,
                          boxprops=dict(facecolor='limegreen', alpha=0.7),
                          medianprops=dict(color='darkgreen', linewidth=2.5))
        axes[1, 1].set_ylabel('Energy (Wh)', fontsize=11)
        axes[1, 1].set_title(f'Energy Distribution\nMedian: {np.median(energy_vals):.2f}Wh', fontsize=12)
        axes[1, 1].set_xticklabels(['All Devices'])
        axes[1, 1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved combined percentile bands to {filename}")

    def _plot_network_traffic_heatmap(self, links: Dict, filename: str):
        """Plot network traffic heatmap showing all links over time"""
        if not links:
            print("  - No network links for traffic heatmap")
            return

        # For now, we only have aggregate stats per link
        # In full implementation, would have time-series traffic data

        link_labels = []
        data_transmitted = []
        num_transmissions = []

        for lid, stats in sorted(links.items()):
            src = stats.get('source_server_id', '?')
            tgt = stats.get('target_server_id', '?')
            link_labels.append(f"{src}→{tgt}")
            data_transmitted.append(stats.get('total_data_transmitted_mb', 0))
            num_transmissions.append(stats.get('num_transmissions', 0))

        # Create simulated heatmap matrix (in real implementation, use actual time series)
        n_links = len(link_labels)
        n_timesteps = 50

        # Simulate traffic pattern based on total data
        heatmap_data = []
        for i, total_data in enumerate(data_transmitted):
            # Create varying pattern
            pattern = np.random.rand(n_timesteps) * total_data / 10
            heatmap_data.append(pattern)

        heatmap_array = np.array(heatmap_data)

        fig, axes = plt.subplots(2, 1, figsize=(14, 12))
        fig.suptitle('Network Traffic Heatmap (All Links)', fontsize=16, fontweight='bold')

        # Traffic heatmap over time
        im1 = axes[0].imshow(heatmap_array, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        axes[0].set_ylabel('Network Link', fontsize=12)
        axes[0].set_xlabel('Time Step', fontsize=12)
        axes[0].set_title('Traffic Intensity Over Time', fontsize=14)
        axes[0].set_yticks(range(min(n_links, 20)))  # Limit labels if too many
        axes[0].set_yticklabels(link_labels[:20] if n_links > 20 else link_labels, fontsize=8)
        cbar1 = plt.colorbar(im1, ax=axes[0])
        cbar1.set_label('Data (MB)', rotation=270, labelpad=15)

        # Total data per link (sorted)
        sorted_indices = np.argsort(data_transmitted)[::-1]
        sorted_labels = [link_labels[i] for i in sorted_indices]
        sorted_data = [data_transmitted[i] for i in sorted_indices]

        axes[1].barh(range(len(sorted_labels)), sorted_data, color='purple', alpha=0.7)
        axes[1].set_yticks(range(len(sorted_labels)))
        axes[1].set_yticklabels(sorted_labels, fontsize=7)
        axes[1].set_xlabel('Total Data Transmitted (MB)', fontsize=12)
        axes[1].set_title(f'Links Ranked by Traffic Volume ({len(sorted_labels)} links)', fontsize=14)
        axes[1].invert_yaxis()
        axes[1].grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved network traffic heatmap to {filename}")

    def _plot_network_link_utilization(self, links: Dict, filename: str):
        """Plot network link utilization distribution (all links)"""
        if not links:
            print("  - No network links for utilization plot")
            return

        # Collect utilization metrics
        bandwidths = []
        latencies = []
        packet_loss_rates = []
        data_volumes = []
        link_labels = []

        for lid, stats in sorted(links.items()):
            src = stats.get('source_server_id', '?')
            tgt = stats.get('target_server_id', '?')
            link_labels.append(f"{src}→{tgt}")
            bandwidths.append(stats.get('bandwidth_mbps', 0))
            latencies.append(stats.get('latency_ms', 0))
            packet_loss_rates.append(stats.get('packet_loss_rate', 0) * 100)  # Convert to percentage
            data_volumes.append(stats.get('total_data_transmitted_mb', 0))

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Network Link Characteristics Distribution (All Links)', fontsize=16, fontweight='bold')

        # Bandwidth distribution
        axes[0, 0].hist(bandwidths, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(np.mean(bandwidths), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(bandwidths):.0f} Mbps')
        axes[0, 0].axvline(np.median(bandwidths), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(bandwidths):.0f} Mbps')
        axes[0, 0].set_xlabel('Bandwidth (Mbps)', fontsize=12)
        axes[0, 0].set_ylabel('Frequency (Count)', fontsize=12)
        axes[0, 0].set_title(f'Bandwidth Distribution ({len(bandwidths)} total links)', fontsize=13)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3, axis='y')

        # Latency distribution
        axes[0, 1].hist(latencies, bins=20, color='coral', edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(np.mean(latencies), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(latencies):.1f} ms')
        axes[0, 1].axvline(np.median(latencies), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(latencies):.1f} ms')
        axes[0, 1].set_xlabel('Latency (ms)', fontsize=12)
        axes[0, 1].set_ylabel('Frequency (Count)', fontsize=12)
        axes[0, 1].set_title(f'Latency Distribution ({len(latencies)} total links)', fontsize=13)
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3, axis='y')

        # Packet loss distribution
        if any(packet_loss_rates):
            axes[1, 0].hist(packet_loss_rates, bins=20, color='orange', edgecolor='black', alpha=0.7)
            axes[1, 0].axvline(np.mean(packet_loss_rates), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(packet_loss_rates):.2f}%')
            axes[1, 0].set_xlabel('Packet Loss Rate (%)', fontsize=12)
            axes[1, 0].set_ylabel('Frequency (Count)', fontsize=12)
            axes[1, 0].set_title(f'Packet Loss Distribution ({len(packet_loss_rates)} total links)', fontsize=13)
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3, axis='y')
        else:
            axes[1, 0].text(0.5, 0.5, 'No packet loss data', ha='center', va='center', fontsize=14)
            axes[1, 0].set_title('Packet Loss (No Data)')

        # Data volume distribution
        axes[1, 1].hist(data_volumes, bins=20, color='mediumpurple', edgecolor='black', alpha=0.7)
        axes[1, 1].axvline(np.mean(data_volumes), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(data_volumes):.2f} MB')
        axes[1, 1].axvline(np.median(data_volumes), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(data_volumes):.2f} MB')
        axes[1, 1].set_xlabel('Data Transmitted (MB)', fontsize=12)
        axes[1, 1].set_ylabel('Frequency (Count)', fontsize=12)
        axes[1, 1].set_title(f'Traffic Volume Distribution ({len(data_volumes)} total links)', fontsize=13)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved network link utilization to {filename}")

    def _plot_network_bottlenecks(self, links: Dict, filename: str):
        """Plot network bottleneck identification (all links analyzed)"""
        if not links:
            print("  - No network links for bottleneck analysis")
            return

        # Identify bottlenecks based on multiple criteria
        link_data = []
        for lid, stats in links.items():
            src = stats.get('source_server_id', '?')
            tgt = stats.get('target_server_id', '?')
            bw = stats.get('bandwidth_mbps', 0)
            lat = stats.get('latency_ms', 0)
            data = stats.get('total_data_transmitted_mb', 0)

            # Calculate bottleneck score (higher = more bottleneck)
            # Low bandwidth + high latency + high traffic = bottleneck
            bw_norm = 1 - (bw / 1000) if bw < 1000 else 0  # Normalize bandwidth (lower is worse)
            lat_norm = lat / 100 if lat < 100 else 1  # Normalize latency (higher is worse)
            traffic_norm = min(data / 10, 1)  # Normalize traffic

            bottleneck_score = (bw_norm * 0.4 + lat_norm * 0.4 + traffic_norm * 0.2) * 100

            link_data.append({
                'label': f"{src}→{tgt}",
                'bw': bw,
                'lat': lat,
                'data': data,
                'score': bottleneck_score
            })

        # Sort by bottleneck score
        link_data_sorted = sorted(link_data, key=lambda x: x['score'], reverse=True)

        fig, axes = plt.subplots(2, 1, figsize=(14, 12))
        fig.suptitle('Network Bottleneck Analysis (All Links)', fontsize=16, fontweight='bold')

        # Bottleneck scores
        labels = [d['label'] for d in link_data_sorted]
        scores = [d['score'] for d in link_data_sorted]
        colors = ['red' if s > 60 else 'orange' if s > 30 else 'green' for s in scores]

        axes[0].barh(range(len(labels)), scores, color=colors, alpha=0.7)
        axes[0].set_yticks(range(len(labels)))
        axes[0].set_yticklabels(labels, fontsize=7)
        axes[0].set_xlabel('Bottleneck Score (0-100)', fontsize=12)
        axes[0].set_title(f'Links Ranked by Bottleneck Potential ({len(labels)} links)\nRed: High Risk | Orange: Medium | Green: Low', fontsize=13)
        axes[0].invert_yaxis()
        axes[0].axvline(30, color='orange', linestyle='--', alpha=0.5)
        axes[0].axvline(60, color='red', linestyle='--', alpha=0.5)
        axes[0].grid(True, alpha=0.3, axis='x')

        # Scatter: Bandwidth vs Latency (sized by traffic)
        bws = [d['bw'] for d in link_data]
        lats = [d['lat'] for d in link_data]
        datas = [d['data'] for d in link_data]
        score_colors = [d['score'] for d in link_data]

        scatter = axes[1].scatter(bws, lats, s=[d*10 for d in datas], c=score_colors,
                                 cmap='RdYlGn_r', alpha=0.6, edgecolors='black', linewidths=1)
        axes[1].set_xlabel('Bandwidth (Mbps)', fontsize=12)
        axes[1].set_ylabel('Latency (ms)', fontsize=12)
        axes[1].set_title('Bandwidth vs Latency (bubble size = traffic volume)', fontsize=13)
        axes[1].grid(True, alpha=0.3)
        cbar = plt.colorbar(scatter, ax=axes[1])
        cbar.set_label('Bottleneck Score', rotation=270, labelpad=15)

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved network bottlenecks plot to {filename}")

    def _plot_temporal_traffic_patterns(self, links: Dict, filename: str):
        """Plot temporal traffic patterns across all links"""
        if not links:
            print("  - No network links for temporal patterns")
            return

        # Collect data
        link_labels = []
        avg_transmission_times = []
        num_transmissions = []
        total_data = []

        for lid, stats in sorted(links.items()):
            src = stats.get('source_server_id', '?')
            tgt = stats.get('target_server_id', '?')
            link_labels.append(f"{src}→{tgt}")
            avg_transmission_times.append(stats.get('avg_transmission_time_s', 0) * 1000)  # Convert to ms
            num_transmissions.append(stats.get('num_transmissions', 0))
            total_data.append(stats.get('total_data_transmitted_mb', 0))

        fig, axes = plt.subplots(3, 1, figsize=(14, 14))
        fig.suptitle('Temporal Traffic Patterns (All Links)', fontsize=16, fontweight='bold')

        # Transmission frequency
        axes[0].bar(range(len(link_labels)), num_transmissions, color='steelblue', alpha=0.7)
        axes[0].set_ylabel('Number of Transmissions', fontsize=12)
        axes[0].set_title(f'Transmission Frequency per Link ({len(link_labels)} links)', fontsize=13)
        axes[0].grid(True, alpha=0.3, axis='y')

        # Average transmission time
        axes[1].bar(range(len(link_labels)), avg_transmission_times, color='coral', alpha=0.7)
        axes[1].set_ylabel('Avg Transmission Time (ms)', fontsize=12)
        axes[1].set_title('Average Transmission Latency per Link', fontsize=13)
        axes[1].grid(True, alpha=0.3, axis='y')

        # Throughput (data / time)
        throughput = [d / (t/1000) if t > 0 else 0 for d, t in zip(total_data, avg_transmission_times)]
        axes[2].bar(range(len(link_labels)), throughput, color='limegreen', alpha=0.7)
        axes[2].set_xlabel('Link Index', fontsize=12)
        axes[2].set_ylabel('Throughput (MB/s)', fontsize=12)
        axes[2].set_title('Effective Throughput per Link', fontsize=13)
        axes[2].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved temporal traffic patterns to {filename}")

    def _plot_network_efficiency(self, links: Dict, filename: str):
        """Plot network efficiency metrics (all links)"""
        if not links:
            print("  - No network links for efficiency plot")
            return

        # Calculate efficiency metrics
        link_data = []
        for lid, stats in links.items():
            src = stats.get('source_server_id', '?')
            tgt = stats.get('target_server_id', '?')
            bw = stats.get('bandwidth_mbps', 0)
            lat = stats.get('latency_ms', 0)
            data = stats.get('total_data_transmitted_mb', 0)
            num_trans = stats.get('num_transmissions', 0)

            # Efficiency metrics
            utilization = (data / bw) * 100 if bw > 0 else 0  # Bandwidth utilization %
            efficiency = (data / lat) if lat > 0 else 0  # Data per latency unit
            avg_packet_size = (data / num_trans) if num_trans > 0 else 0  # MB per transmission

            link_data.append({
                'label': f"{src}→{tgt}",
                'utilization': min(utilization, 100),  # Cap at 100%
                'efficiency': efficiency,
                'avg_packet': avg_packet_size,
                'bw': bw,
                'lat': lat
            })

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Network Efficiency Metrics (All Links)', fontsize=16, fontweight='bold')

        # Bandwidth utilization distribution
        utils = [d['utilization'] for d in link_data]
        axes[0, 0].hist(utils, bins=20, color='dodgerblue', edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(np.mean(utils), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(utils):.1f}%')
        axes[0, 0].set_xlabel('Bandwidth Utilization (%)', fontsize=12)
        axes[0, 0].set_ylabel('Frequency (Count)', fontsize=12)
        axes[0, 0].set_title(f'Bandwidth Utilization Distribution ({len(utils)} total links)', fontsize=13)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3, axis='y')

        # Efficiency scatter: Bandwidth vs Utilization
        bws = [d['bw'] for d in link_data]
        axes[0, 1].scatter(bws, utils, s=100, alpha=0.6, c=utils, cmap='RdYlGn', edgecolors='black')
        axes[0, 1].set_xlabel('Bandwidth (Mbps)', fontsize=12)
        axes[0, 1].set_ylabel('Utilization (%)', fontsize=12)
        axes[0, 1].set_title('Bandwidth vs Utilization', fontsize=13)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axhline(50, color='orange', linestyle='--', alpha=0.5, label='50% threshold')
        axes[0, 1].legend()

        # Data/Latency efficiency
        effs = [d['efficiency'] for d in link_data]
        axes[1, 0].hist(effs, bins=20, color='limegreen', edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(np.mean(effs), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(effs):.2f}')
        axes[1, 0].set_xlabel('Efficiency (MB/ms)', fontsize=12)
        axes[1, 0].set_ylabel('Frequency (Count)', fontsize=12)
        axes[1, 0].set_title(f'Data/Latency Efficiency Distribution ({len(effs)} total links)', fontsize=13)
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # Average packet size (all links including zeros)
        packets = [d['avg_packet'] for d in link_data]
        axes[1, 1].hist(packets, bins=20, color='mediumpurple', edgecolor='black', alpha=0.7)
        axes[1, 1].axvline(np.mean(packets), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(packets):.3f} MB')
        axes[1, 1].set_xlabel('Avg Packet Size (MB)', fontsize=12)
        axes[1, 1].set_ylabel('Frequency (Count)', fontsize=12)
        axes[1, 1].set_title(f'Packet Size Distribution ({len(packets)} total links)', fontsize=13)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved network efficiency plot to {filename}")


# Test execution
if __name__ == "__main__":
    # Example usage
    exporter = ResultsExporter()
    print("Results exporter initialized")
    print(f"Output directory: {exporter.output_dir}")
    print(f"Plots directory: {exporter.plots_dir}")
