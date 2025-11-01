"""
Julia Wrapper for OPF Computation on Edge Devices
Executes Julia scripts and monitors resource usage
"""

import subprocess
import json
import time
import os
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class JuliaConfig:
    """Configuration for Julia OPF execution"""
    node_id: int = 1
    caseID: str = "testbeds/pglib_opf_case14_ieee.m"
    max_iterations: int = 1000
    rho: float = 1e3
    tolerance: float = 1e-2
    epsilon: float = 1.0
    alpha: float = 0.1
    method: str = "PVP"


class JuliaProcessMonitor:
    """Monitors a Julia process for resource usage"""

    def __init__(self, process: psutil.Process, sampling_interval: float = 0.1):
        self.process = process
        self.sampling_interval = sampling_interval
        self.is_monitoring = False
        self.monitor_thread = None

        # Metrics
        self.cpu_samples = []
        self.memory_samples = []
        self.timestamps = []
        self.start_time = None

    def start(self):
        """Start monitoring the process"""
        self.is_monitoring = True
        self.start_time = time.time()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                if self.process.is_running():
                    timestamp = time.time() - self.start_time
                    cpu_percent = self.process.cpu_percent(interval=None)
                    mem_info = self.process.memory_info()
                    mem_mb = mem_info.rss / (1024 * 1024)

                    self.timestamps.append(timestamp)
                    self.cpu_samples.append(cpu_percent)
                    self.memory_samples.append(mem_mb)

                    # Also monitor child processes
                    try:
                        children = self.process.children(recursive=True)
                        for child in children:
                            cpu_percent += child.cpu_percent(interval=None)
                            mem_mb += child.memory_info().rss / (1024 * 1024)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    time.sleep(self.sampling_interval)
                else:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def get_stats(self) -> Dict:
        """Get statistics from monitoring"""
        if not self.cpu_samples:
            return {}

        return {
            'avg_cpu_percent': sum(self.cpu_samples) / len(self.cpu_samples),
            'max_cpu_percent': max(self.cpu_samples),
            'min_cpu_percent': min(self.cpu_samples),
            'avg_memory_mb': sum(self.memory_samples) / len(self.memory_samples),
            'max_memory_mb': max(self.memory_samples),
            'min_memory_mb': min(self.memory_samples),
            'num_samples': len(self.cpu_samples),
            'cpu_history': self.cpu_samples,
            'memory_history': self.memory_samples,
            'timestamps': self.timestamps
        }


class JuliaOPFExecutor:
    """Executes Julia OPF scripts with resource monitoring"""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize Julia executor

        Args:
            base_dir: Base directory of the project (defaults to parent of edge/)
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)

        self.edge_dir = self.base_dir / "edge"
        self.scripts_dir = self.edge_dir / "scripts"
        self.results_dir = self.edge_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

    def run_distributed_node(self,
                            node_id: int,
                            config: Optional[JuliaConfig] = None) -> Dict:
        """
        Run OPF computation for a single distributed node

        Args:
            node_id: Node identifier
            config: Julia configuration (uses defaults if None)

        Returns:
            Dictionary with execution results and metrics
        """
        if config is None:
            config = JuliaConfig(node_id=node_id)
        else:
            config.node_id = node_id

        # Save config to JSON
        config_dict = asdict(config)
        config_file = self.results_dir / f"config_node_{node_id}.json"
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)

        # Julia script path
        script_path = self.scripts_dir / "opf_edge_node.jl"

        # Execute Julia script
        print(f"Executing Julia OPF for Node {node_id}...")
        start_time = time.time()

        cmd = ["julia", str(script_path), str(config_file)]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.base_dir)
            )

            # Monitor the process
            ps_process = psutil.Process(process.pid)
            monitor = JuliaProcessMonitor(ps_process)
            monitor.start()

            # Wait for completion
            stdout, stderr = process.communicate()
            monitor.stop()

            end_time = time.time()
            execution_time = end_time - start_time

            # Get monitoring stats
            monitor_stats = monitor.get_stats()

            # Read results from JSON
            result_file = self.results_dir / f"node_{node_id}_results.json"
            if result_file.exists():
                with open(result_file, 'r') as f:
                    julia_results = json.load(f)
            else:
                julia_results = {}

            # Combine results
            results = {
                'node_id': node_id,
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'execution_time_s': execution_time,
                'stdout': stdout,
                'stderr': stderr,
                'resource_monitoring': monitor_stats,
                'julia_results': julia_results
            }

            return results

        except Exception as e:
            return {
                'node_id': node_id,
                'success': False,
                'error': str(e),
                'execution_time_s': time.time() - start_time
            }

    def run_centralized(self, config: Optional[Dict] = None) -> Dict:
        """
        Run centralized OPF computation

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary with execution results and metrics
        """
        if config is None:
            config = {"caseID": "testbeds/pglib_opf_case14_ieee.m"}

        # Save config to JSON
        config_file = self.results_dir / "config_centralized.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Julia script path
        script_path = self.scripts_dir / "opf_centralized_edge.jl"

        # Execute Julia script
        print("Executing Centralized Julia OPF...")
        start_time = time.time()

        cmd = ["julia", str(script_path), str(config_file)]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.base_dir)
            )

            # Monitor the process
            ps_process = psutil.Process(process.pid)
            monitor = JuliaProcessMonitor(ps_process)
            monitor.start()

            # Wait for completion
            stdout, stderr = process.communicate()
            monitor.stop()

            end_time = time.time()
            execution_time = end_time - start_time

            # Get monitoring stats
            monitor_stats = monitor.get_stats()

            # Read results from JSON
            result_file = self.results_dir / "centralized_results.json"
            if result_file.exists():
                with open(result_file, 'r') as f:
                    julia_results = json.load(f)
            else:
                julia_results = {}

            # Combine results
            results = {
                'type': 'centralized',
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'execution_time_s': execution_time,
                'stdout': stdout,
                'stderr': stderr,
                'resource_monitoring': monitor_stats,
                'julia_results': julia_results
            }

            return results

        except Exception as e:
            return {
                'type': 'centralized',
                'success': False,
                'error': str(e),
                'execution_time_s': time.time() - start_time
            }


# Test execution
if __name__ == "__main__":
    executor = JuliaOPFExecutor()

    # Test centralized execution
    print("Testing centralized OPF execution...")
    result = executor.run_centralized()
    print(f"Success: {result['success']}")
    print(f"Execution time: {result['execution_time_s']:.2f}s")
    if result.get('resource_monitoring'):
        stats = result['resource_monitoring']
        print(f"Avg CPU: {stats.get('avg_cpu_percent', 0):.1f}%")
        print(f"Max Memory: {stats.get('max_memory_mb', 0):.1f}MB")
