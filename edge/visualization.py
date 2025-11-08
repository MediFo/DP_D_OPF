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

        # Plot 6: Aggregated statistics (box plots)
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_aggregated_statistics(
                results['simulation_stats']['servers'],
                f"{prefix}_aggregated_stats.png"
            )

        # Plot 7: Device tier comparison (if device configs available)
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_tier_comparison(
                results['simulation_stats']['servers'],
                results.get('device_configs', {}),
                f"{prefix}_tier_comparison.png"
            )

        # Plot 8: Top N devices by resource usage
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_top_n_devices(
                results['simulation_stats']['servers'],
                f"{prefix}_top_devices.png",
                n=10
            )

        # Plot 9: Distribution histograms
        if 'simulation_stats' in results and 'servers' in results['simulation_stats']:
            self._plot_resource_distributions(
                results['simulation_stats']['servers'],
                f"{prefix}_resource_distributions.png"
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

    def _plot_aggregated_statistics(self, servers: Dict, filename: str):
        """Plot aggregated statistics with box plots showing distribution"""
        cpu_avg = [stats.get('avg_cpu_usage', 0) for stats in servers.values()]
        cpu_max = [stats.get('max_cpu_usage', 0) for stats in servers.values()]
        mem_avg = [stats.get('avg_memory_usage_mb', 0) for stats in servers.values()]
        mem_max = [stats.get('max_memory_usage_mb', 0) for stats in servers.values()]
        power = [stats.get('avg_power_w', 0) for stats in servers.values()]
        energy = [stats.get('total_energy_wh', 0) for stats in servers.values()]

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        fig.suptitle('Aggregated Resource Statistics Across All Devices', fontsize=16, fontweight='bold')

        # CPU average box plot
        bp1 = axes[0, 0].boxplot([cpu_avg], vert=True, patch_artist=True, widths=0.5)
        bp1['boxes'][0].set_facecolor('skyblue')
        axes[0, 0].set_ylabel('CPU Usage (%)', fontsize=12)
        axes[0, 0].set_title(f'Avg CPU Distribution\nMean: {np.mean(cpu_avg):.1f}% | Median: {np.median(cpu_avg):.1f}%', fontsize=12)
        axes[0, 0].set_xticklabels(['All Devices'])
        axes[0, 0].grid(True, alpha=0.3, axis='y')

        # CPU max box plot
        bp2 = axes[0, 1].boxplot([cpu_max], vert=True, patch_artist=True, widths=0.5)
        bp2['boxes'][0].set_facecolor('coral')
        axes[0, 1].set_ylabel('CPU Usage (%)', fontsize=12)
        axes[0, 1].set_title(f'Max CPU Distribution\nMean: {np.mean(cpu_max):.1f}% | Median: {np.median(cpu_max):.1f}%', fontsize=12)
        axes[0, 1].set_xticklabels(['All Devices'])
        axes[0, 1].grid(True, alpha=0.3, axis='y')

        # Memory average box plot
        bp3 = axes[0, 2].boxplot([mem_avg], vert=True, patch_artist=True, widths=0.5)
        bp3['boxes'][0].set_facecolor('lightgreen')
        axes[0, 2].set_ylabel('Memory (MB)', fontsize=12)
        axes[0, 2].set_title(f'Avg Memory Distribution\nMean: {np.mean(mem_avg):.1f} MB | Median: {np.median(mem_avg):.1f} MB', fontsize=12)
        axes[0, 2].set_xticklabels(['All Devices'])
        axes[0, 2].grid(True, alpha=0.3, axis='y')

        # Memory max box plot
        bp4 = axes[1, 0].boxplot([mem_max], vert=True, patch_artist=True, widths=0.5)
        bp4['boxes'][0].set_facecolor('plum')
        axes[1, 0].set_ylabel('Memory (MB)', fontsize=12)
        axes[1, 0].set_title(f'Max Memory Distribution\nMean: {np.mean(mem_max):.1f} MB | Median: {np.median(mem_max):.1f} MB', fontsize=12)
        axes[1, 0].set_xticklabels(['All Devices'])
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # Power box plot
        bp5 = axes[1, 1].boxplot([power], vert=True, patch_artist=True, widths=0.5)
        bp5['boxes'][0].set_facecolor('gold')
        axes[1, 1].set_ylabel('Power (W)', fontsize=12)
        axes[1, 1].set_title(f'Avg Power Distribution\nMean: {np.mean(power):.1f} W | Median: {np.median(power):.1f} W', fontsize=12)
        axes[1, 1].set_xticklabels(['All Devices'])
        axes[1, 1].grid(True, alpha=0.3, axis='y')

        # Energy box plot
        bp6 = axes[1, 2].boxplot([energy], vert=True, patch_artist=True, widths=0.5)
        bp6['boxes'][0].set_facecolor('lightcoral')
        axes[1, 2].set_ylabel('Energy (Wh)', fontsize=12)
        axes[1, 2].set_title(f'Total Energy Distribution\nMean: {np.mean(energy):.2f} Wh | Median: {np.median(energy):.2f} Wh', fontsize=12)
        axes[1, 2].set_xticklabels(['All Devices'])
        axes[1, 2].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved aggregated statistics plot to {filename}")

    def _plot_tier_comparison(self, servers: Dict, device_configs: Dict, filename: str):
        """Plot comparison between device tiers (standard vs basic)"""
        # Group servers by tier if device config available
        standard_cpu = []
        standard_mem = []
        standard_power = []
        basic_cpu = []
        basic_mem = []
        basic_power = []

        for sid, stats in servers.items():
            # Try to determine tier from device config
            device_id = stats.get('id', sid)
            tier = 'basic'  # default

            # If we have device configs, look up the tier
            if isinstance(device_configs, dict) and 'devices' in device_configs:
                for dev in device_configs['devices']:
                    if dev.get('id') == device_id:
                        tier = dev.get('tier', 'basic')
                        break

            cpu = stats.get('avg_cpu_usage', 0)
            mem = stats.get('avg_memory_usage_mb', 0)
            pwr = stats.get('avg_power_w', 0)

            if tier == 'standard':
                standard_cpu.append(cpu)
                standard_mem.append(mem)
                standard_power.append(pwr)
            else:  # basic
                basic_cpu.append(cpu)
                basic_mem.append(mem)
                basic_power.append(pwr)

        # If we don't have clear tier separation, skip this plot
        if not standard_cpu or not basic_cpu:
            print("  - Skipping tier comparison (insufficient tier data)")
            return

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('Device Tier Comparison: Standard vs Basic', fontsize=16, fontweight='bold')

        # CPU comparison
        bp1 = axes[0].boxplot([standard_cpu, basic_cpu], labels=['Standard', 'Basic'],
                               patch_artist=True, widths=0.6)
        bp1['boxes'][0].set_facecolor('steelblue')
        bp1['boxes'][1].set_facecolor('lightcoral')
        axes[0].set_ylabel('Avg CPU Usage (%)', fontsize=12)
        axes[0].set_title(f'CPU Usage by Tier\nStd: {np.mean(standard_cpu):.1f}% | Basic: {np.mean(basic_cpu):.1f}%', fontsize=12)
        axes[0].grid(True, alpha=0.3, axis='y')

        # Memory comparison
        bp2 = axes[1].boxplot([standard_mem, basic_mem], labels=['Standard', 'Basic'],
                               patch_artist=True, widths=0.6)
        bp2['boxes'][0].set_facecolor('mediumseagreen')
        bp2['boxes'][1].set_facecolor('plum')
        axes[1].set_ylabel('Avg Memory (MB)', fontsize=12)
        axes[1].set_title(f'Memory Usage by Tier\nStd: {np.mean(standard_mem):.1f} MB | Basic: {np.mean(basic_mem):.1f} MB', fontsize=12)
        axes[1].grid(True, alpha=0.3, axis='y')

        # Power comparison
        bp3 = axes[2].boxplot([standard_power, basic_power], labels=['Standard', 'Basic'],
                               patch_artist=True, widths=0.6)
        bp3['boxes'][0].set_facecolor('gold')
        bp3['boxes'][1].set_facecolor('lightskyblue')
        axes[2].set_ylabel('Avg Power (W)', fontsize=12)
        axes[2].set_title(f'Power Consumption by Tier\nStd: {np.mean(standard_power):.1f} W | Basic: {np.mean(basic_power):.1f} W', fontsize=12)
        axes[2].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved tier comparison plot to {filename}")

    def _plot_top_n_devices(self, servers: Dict, filename: str, n: int = 10):
        """Plot top N devices by resource usage"""
        # Collect all server data
        server_data = []
        for sid, stats in servers.items():
            server_data.append({
                'id': stats.get('id', sid),
                'name': stats.get('name', f'Server_{sid}'),
                'cpu': stats.get('avg_cpu_usage', 0),
                'mem': stats.get('avg_memory_usage_mb', 0),
                'power': stats.get('avg_power_w', 0),
                'energy': stats.get('total_energy_wh', 0)
            })

        # Sort by different metrics and get top N
        top_cpu = sorted(server_data, key=lambda x: x['cpu'], reverse=True)[:n]
        top_mem = sorted(server_data, key=lambda x: x['mem'], reverse=True)[:n]
        top_power = sorted(server_data, key=lambda x: x['power'], reverse=True)[:n]
        top_energy = sorted(server_data, key=lambda x: x['energy'], reverse=True)[:n]

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Top {n} Devices by Resource Usage', fontsize=16, fontweight='bold')

        # Top CPU
        cpu_labels = [f"D{d['id']}" for d in top_cpu]
        cpu_values = [d['cpu'] for d in top_cpu]
        axes[0, 0].barh(cpu_labels, cpu_values, color='orangered', alpha=0.8)
        axes[0, 0].set_xlabel('Avg CPU Usage (%)', fontsize=12)
        axes[0, 0].set_ylabel('Device', fontsize=12)
        axes[0, 0].set_title(f'Top {n} by CPU Usage', fontsize=14)
        axes[0, 0].invert_yaxis()
        axes[0, 0].grid(True, alpha=0.3, axis='x')

        # Top Memory
        mem_labels = [f"D{d['id']}" for d in top_mem]
        mem_values = [d['mem'] for d in top_mem]
        axes[0, 1].barh(mem_labels, mem_values, color='dodgerblue', alpha=0.8)
        axes[0, 1].set_xlabel('Avg Memory (MB)', fontsize=12)
        axes[0, 1].set_ylabel('Device', fontsize=12)
        axes[0, 1].set_title(f'Top {n} by Memory Usage', fontsize=14)
        axes[0, 1].invert_yaxis()
        axes[0, 1].grid(True, alpha=0.3, axis='x')

        # Top Power
        pwr_labels = [f"D{d['id']}" for d in top_power]
        pwr_values = [d['power'] for d in top_power]
        axes[1, 0].barh(pwr_labels, pwr_values, color='gold', alpha=0.8)
        axes[1, 0].set_xlabel('Avg Power (W)', fontsize=12)
        axes[1, 0].set_ylabel('Device', fontsize=12)
        axes[1, 0].set_title(f'Top {n} by Power Consumption', fontsize=14)
        axes[1, 0].invert_yaxis()
        axes[1, 0].grid(True, alpha=0.3, axis='x')

        # Top Energy
        eng_labels = [f"D{d['id']}" for d in top_energy]
        eng_values = [d['energy'] for d in top_energy]
        axes[1, 1].barh(eng_labels, eng_values, color='limegreen', alpha=0.8)
        axes[1, 1].set_xlabel('Total Energy (Wh)', fontsize=12)
        axes[1, 1].set_ylabel('Device', fontsize=12)
        axes[1, 1].set_title(f'Top {n} by Energy Consumption', fontsize=14)
        axes[1, 1].invert_yaxis()
        axes[1, 1].grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved top {n} devices plot to {filename}")

    def _plot_resource_distributions(self, servers: Dict, filename: str):
        """Plot distribution histograms for all resource metrics"""
        cpu_avg = [stats.get('avg_cpu_usage', 0) for stats in servers.values()]
        cpu_max = [stats.get('max_cpu_usage', 0) for stats in servers.values()]
        mem_avg = [stats.get('avg_memory_usage_mb', 0) for stats in servers.values()]
        power = [stats.get('avg_power_w', 0) for stats in servers.values()]

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Resource Usage Distribution Across All Devices', fontsize=16, fontweight='bold')

        # CPU average histogram
        axes[0, 0].hist(cpu_avg, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(np.mean(cpu_avg), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(cpu_avg):.1f}%')
        axes[0, 0].axvline(np.median(cpu_avg), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(cpu_avg):.1f}%')
        axes[0, 0].set_xlabel('Avg CPU Usage (%)', fontsize=12)
        axes[0, 0].set_ylabel('Number of Devices', fontsize=12)
        axes[0, 0].set_title('Average CPU Usage Distribution', fontsize=13)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3, axis='y')

        # CPU max histogram
        axes[0, 1].hist(cpu_max, bins=20, color='coral', edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(np.mean(cpu_max), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(cpu_max):.1f}%')
        axes[0, 1].axvline(np.median(cpu_max), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(cpu_max):.1f}%')
        axes[0, 1].set_xlabel('Max CPU Usage (%)', fontsize=12)
        axes[0, 1].set_ylabel('Number of Devices', fontsize=12)
        axes[0, 1].set_title('Maximum CPU Usage Distribution', fontsize=13)
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3, axis='y')

        # Memory histogram
        axes[1, 0].hist(mem_avg, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(np.mean(mem_avg), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(mem_avg):.1f} MB')
        axes[1, 0].axvline(np.median(mem_avg), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(mem_avg):.1f} MB')
        axes[1, 0].set_xlabel('Avg Memory (MB)', fontsize=12)
        axes[1, 0].set_ylabel('Number of Devices', fontsize=12)
        axes[1, 0].set_title('Average Memory Usage Distribution', fontsize=13)
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # Power histogram
        axes[1, 1].hist(power, bins=20, color='gold', edgecolor='black', alpha=0.7)
        axes[1, 1].axvline(np.mean(power), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(power):.1f} W')
        axes[1, 1].axvline(np.median(power), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(power):.1f} W')
        axes[1, 1].set_xlabel('Avg Power (W)', fontsize=12)
        axes[1, 1].set_ylabel('Number of Devices', fontsize=12)
        axes[1, 1].set_title('Average Power Distribution', fontsize=13)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        filepath = self.plots_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  - Saved resource distribution plots to {filename}")


# Test execution
if __name__ == "__main__":
    # Example usage
    exporter = ResultsExporter()
    print("Results exporter initialized")
    print(f"Output directory: {exporter.output_dir}")
    print(f"Plots directory: {exporter.plots_dir}")
