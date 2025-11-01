"""
Resource Monitor for tracking system resources during OPF computation
"""
import psutil
import time
import threading
from typing import Dict, List, Optional
from collections import defaultdict


class ResourceMonitor:
    """
    Monitors system resources (CPU, memory, network) during execution
    """

    def __init__(self, sampling_interval: float = 0.5):
        """
        Initialize resource monitor

        Args:
            sampling_interval: Time between samples in seconds
        """
        self.sampling_interval = sampling_interval
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Resource history
        self.cpu_history: List[Dict] = []
        self.memory_history: List[Dict] = []
        self.network_history: List[Dict] = []
        self.disk_history: List[Dict] = []

        # Process tracking
        self.process = psutil.Process()
        self.start_time = None
        self.end_time = None

        # Network baseline
        self.net_io_start = None

    def start(self):
        """Start monitoring resources"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.start_time = time.time()
        self.net_io_start = psutil.net_io_counters()

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop monitoring resources"""
        self.is_monitoring = False
        self.end_time = time.time()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            timestamp = time.time() - self.start_time

            # CPU monitoring
            cpu_percent = self.process.cpu_percent(interval=None)
            cpu_times = self.process.cpu_times()
            self.cpu_history.append({
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'user_time': cpu_times.user,
                'system_time': cpu_times.system,
                'num_threads': self.process.num_threads()
            })

            # Memory monitoring
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()
            self.memory_history.append({
                'timestamp': timestamp,
                'rss_mb': mem_info.rss / (1024 * 1024),
                'vms_mb': mem_info.vms / (1024 * 1024),
                'percent': mem_percent
            })

            # Network monitoring
            net_io = psutil.net_io_counters()
            self.network_history.append({
                'timestamp': timestamp,
                'bytes_sent': net_io.bytes_sent - self.net_io_start.bytes_sent,
                'bytes_recv': net_io.bytes_recv - self.net_io_start.bytes_recv,
                'packets_sent': net_io.packets_sent - self.net_io_start.packets_sent,
                'packets_recv': net_io.packets_recv - self.net_io_start.packets_recv
            })

            # Disk I/O monitoring
            try:
                disk_io = self.process.io_counters()
                self.disk_history.append({
                    'timestamp': timestamp,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                })
            except (AttributeError, psutil.AccessDenied):
                pass  # Not available on all platforms

            time.sleep(self.sampling_interval)

    def get_summary(self) -> Dict:
        """Get summary statistics of monitored resources"""
        duration = (self.end_time or time.time()) - (self.start_time or 0)

        # CPU stats
        cpu_values = [s['cpu_percent'] for s in self.cpu_history]
        cpu_summary = {
            'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'max': max(cpu_values) if cpu_values else 0,
            'min': min(cpu_values) if cpu_values else 0,
        } if cpu_values else {}

        # Memory stats
        mem_values = [s['rss_mb'] for s in self.memory_history]
        mem_summary = {
            'avg_mb': sum(mem_values) / len(mem_values) if mem_values else 0,
            'max_mb': max(mem_values) if mem_values else 0,
            'min_mb': min(mem_values) if mem_values else 0,
        } if mem_values else {}

        # Network stats
        network_summary = {}
        if self.network_history:
            last_net = self.network_history[-1]
            network_summary = {
                'total_sent_mb': last_net['bytes_sent'] / (1024 * 1024),
                'total_recv_mb': last_net['bytes_recv'] / (1024 * 1024),
                'total_packets_sent': last_net['packets_sent'],
                'total_packets_recv': last_net['packets_recv']
            }

        # Disk stats
        disk_summary = {}
        if self.disk_history:
            total_read = sum(s['read_bytes'] for s in self.disk_history)
            total_write = sum(s['write_bytes'] for s in self.disk_history)
            disk_summary = {
                'total_read_mb': total_read / (1024 * 1024),
                'total_write_mb': total_write / (1024 * 1024)
            }

        return {
            'duration_s': duration,
            'cpu': cpu_summary,
            'memory': mem_summary,
            'network': network_summary,
            'disk': disk_summary,
            'num_samples': len(self.cpu_history)
        }

    def get_time_series(self) -> Dict[str, List]:
        """Get raw time series data for plotting"""
        return {
            'cpu': self.cpu_history,
            'memory': self.memory_history,
            'network': self.network_history,
            'disk': self.disk_history
        }

    def clear(self):
        """Clear all recorded data"""
        self.cpu_history.clear()
        self.memory_history.clear()
        self.network_history.clear()
        self.disk_history.clear()
        self.start_time = None
        self.end_time = None
