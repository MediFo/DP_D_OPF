"""
Edge Service component representing computational tasks (OPF computation)
"""
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ServiceRequirements:
    """Resource requirements for a service"""
    cpu_cores: float = 1.0
    memory_mb: float = 512.0
    estimated_runtime_s: float = 10.0


class EdgeService:
    """
    Represents a computational service running on edge infrastructure
    For OPF evaluation, this represents an OPF computation task
    """

    def __init__(self,
                 service_id: int,
                 name: str,
                 service_type: str = "opf_computation",
                 requirements: Optional[ServiceRequirements] = None,
                 node_id: Optional[int] = None):
        """
        Initialize edge service

        Args:
            service_id: Unique identifier
            name: Service name
            service_type: Type of service (e.g., 'opf_computation', 'admm_node')
            requirements: Resource requirements
            node_id: Associated power grid node ID (if applicable)
        """
        self.id = service_id
        self.name = name
        self.type = service_type
        self.requirements = requirements or ServiceRequirements()
        self.node_id = node_id

        # Assignment
        self.assigned_server = None

        # Execution tracking
        self.status = "initialized"  # initialized, running, completed, failed
        self.start_time = None
        self.end_time = None
        self.actual_runtime = 0.0

        # Resource usage tracking
        self.cpu_usage_samples = []
        self.memory_usage_samples = []
        self.network_data_sent_mb = 0.0
        self.network_data_recv_mb = 0.0

        # Results
        self.result_data: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None

    def start(self):
        """Mark service as started"""
        self.status = "running"
        self.start_time = time.time()

    def complete(self, result_data: Optional[Dict] = None):
        """Mark service as completed"""
        self.status = "completed"
        self.end_time = time.time()
        if self.start_time:
            self.actual_runtime = self.end_time - self.start_time
        self.result_data = result_data

    def fail(self, error_message: str):
        """Mark service as failed"""
        self.status = "failed"
        self.end_time = time.time()
        if self.start_time:
            self.actual_runtime = self.end_time - self.start_time
        self.error_message = error_message

    def record_resource_usage(self, cpu_percent: float, memory_mb: float):
        """Record resource usage sample"""
        self.cpu_usage_samples.append(cpu_percent)
        self.memory_usage_samples.append(memory_mb)

    def record_network_transfer(self, sent_mb: float, recv_mb: float):
        """Record network data transfer"""
        self.network_data_sent_mb += sent_mb
        self.network_data_recv_mb += recv_mb

    def get_stats(self) -> Dict:
        """Get service statistics"""
        avg_cpu = sum(self.cpu_usage_samples) / len(self.cpu_usage_samples) if self.cpu_usage_samples else 0
        avg_mem = sum(self.memory_usage_samples) / len(self.memory_usage_samples) if self.memory_usage_samples else 0

        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'node_id': self.node_id,
            'status': self.status,
            'assigned_server': self.assigned_server.id if self.assigned_server else None,
            'actual_runtime_s': self.actual_runtime,
            'avg_cpu_usage': avg_cpu,
            'max_cpu_usage': max(self.cpu_usage_samples) if self.cpu_usage_samples else 0,
            'avg_memory_usage_mb': avg_mem,
            'max_memory_usage_mb': max(self.memory_usage_samples) if self.memory_usage_samples else 0,
            'network_sent_mb': self.network_data_sent_mb,
            'network_recv_mb': self.network_data_recv_mb,
            'total_network_mb': self.network_data_sent_mb + self.network_data_recv_mb
        }

    def __repr__(self):
        return f"EdgeService(id={self.id}, name={self.name}, status={self.status}, server={self.assigned_server.id if self.assigned_server else None})"
