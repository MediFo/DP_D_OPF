"""
Edge Server component for simulating edge computing nodes
"""
import time
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ServerSpecs:
    """Hardware specifications for edge server"""
    cpu_cores: int = 4
    cpu_freq_ghz: float = 2.4
    memory_gb: float = 8.0
    storage_gb: float = 100.0
    power_idle_w: float = 50.0
    power_max_w: float = 150.0


class EdgeServer:
    """
    Represents an edge computing server node
    """

    def __init__(self,
                 server_id: int,
                 name: str,
                 location: tuple = (0.0, 0.0),
                 specs: Optional[ServerSpecs] = None):
        """
        Initialize edge server

        Args:
            server_id: Unique identifier
            name: Server name
            location: Geographic coordinates (lat, lon)
            specs: Hardware specifications
        """
        self.id = server_id
        self.name = name
        self.location = location
        self.specs = specs or ServerSpecs()

        # Resource tracking
        self.services: List = []
        self.cpu_usage_history: List[float] = []
        self.memory_usage_history: List[float] = []
        self.power_usage_history: List[float] = []
        self.network_usage_history: List[Dict] = []

        # Current state
        self.current_cpu_usage = 0.0
        self.current_memory_usage = 0.0
        self.current_power = self.specs.power_idle_w

        # Status
        self.is_active = True
        self.start_time = None

    def assign_service(self, service):
        """Assign a service to this edge server"""
        if service not in self.services:
            self.services.append(service)
            service.assigned_server = self

    def remove_service(self, service):
        """Remove a service from this edge server"""
        if service in self.services:
            self.services.remove(service)
            service.assigned_server = None

    def update_resource_usage(self, cpu_percent: float, memory_mb: float):
        """
        Update current resource usage

        Args:
            cpu_percent: CPU utilization percentage (0-100)
            memory_mb: Memory usage in MB
        """
        self.current_cpu_usage = min(cpu_percent, 100.0)
        self.current_memory_usage = min(memory_mb, self.specs.memory_gb * 1024)

        # Calculate power based on CPU usage (linear model)
        cpu_ratio = self.current_cpu_usage / 100.0
        self.current_power = (self.specs.power_idle_w +
                             (self.specs.power_max_w - self.specs.power_idle_w) * cpu_ratio)

        # Store history
        self.cpu_usage_history.append(self.current_cpu_usage)
        self.memory_usage_history.append(self.current_memory_usage)
        self.power_usage_history.append(self.current_power)

    def get_available_cpu(self) -> float:
        """Get available CPU percentage"""
        return 100.0 - self.current_cpu_usage

    def get_available_memory(self) -> float:
        """Get available memory in MB"""
        return (self.specs.memory_gb * 1024) - self.current_memory_usage

    def get_stats(self) -> Dict:
        """Get current server statistics"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'cpu_usage_percent': self.current_cpu_usage,
            'memory_usage_mb': self.current_memory_usage,
            'available_cpu_percent': self.get_available_cpu(),
            'available_memory_mb': self.get_available_memory(),
            'power_consumption_w': self.current_power,
            'num_services': len(self.services),
            'is_active': self.is_active
        }

    def get_summary_stats(self) -> Dict:
        """Get summary statistics over entire execution"""
        if not self.cpu_usage_history:
            return self.get_stats()

        return {
            'id': self.id,
            'name': self.name,
            'avg_cpu_usage': sum(self.cpu_usage_history) / len(self.cpu_usage_history),
            'max_cpu_usage': max(self.cpu_usage_history) if self.cpu_usage_history else 0,
            'avg_memory_usage_mb': sum(self.memory_usage_history) / len(self.memory_usage_history),
            'max_memory_usage_mb': max(self.memory_usage_history) if self.memory_usage_history else 0,
            'avg_power_w': sum(self.power_usage_history) / len(self.power_usage_history),
            'total_energy_wh': sum(self.power_usage_history) / 3600.0,  # Assuming 1s sampling
            'num_samples': len(self.cpu_usage_history)
        }

    def __repr__(self):
        return f"EdgeServer(id={self.id}, name={self.name}, cpu={self.current_cpu_usage:.1f}%, mem={self.current_memory_usage:.1f}MB)"
