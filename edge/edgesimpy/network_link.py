"""
Network Link component for modeling communication between edge servers
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class LinkSpecs:
    """Network link specifications"""
    bandwidth_mbps: float = 100.0
    latency_ms: float = 10.0
    packet_loss_rate: float = 0.001


class NetworkLink:
    """
    Represents a network connection between edge servers
    """

    def __init__(self,
                 link_id: int,
                 source_server_id: int,
                 target_server_id: int,
                 specs: LinkSpecs = None):
        """
        Initialize network link

        Args:
            link_id: Unique identifier
            source_server_id: Source server ID
            target_server_id: Target server ID
            specs: Link specifications
        """
        self.id = link_id
        self.source_id = source_server_id
        self.target_id = target_server_id
        self.specs = specs or LinkSpecs()

        # Traffic tracking
        self.data_transmitted_mb = 0.0
        self.data_received_mb = 0.0
        self.transmission_history: List[Dict] = []
        self.current_utilization = 0.0

    def transmit_data(self, data_size_mb: float, timestamp: float = 0.0):
        """
        Record data transmission over this link

        Args:
            data_size_mb: Amount of data in MB
            timestamp: Timestamp of transmission
        """
        self.data_transmitted_mb += data_size_mb
        transmission_time_s = (data_size_mb * 8) / self.specs.bandwidth_mbps  # Convert to seconds

        self.transmission_history.append({
            'timestamp': timestamp,
            'data_mb': data_size_mb,
            'transmission_time_s': transmission_time_s,
            'latency_ms': self.specs.latency_ms
        })

        return transmission_time_s

    def get_total_latency(self, data_size_mb: float) -> float:
        """
        Calculate total latency for data transmission

        Args:
            data_size_mb: Size of data to transmit

        Returns:
            Total latency in seconds
        """
        transmission_time = (data_size_mb * 8) / self.specs.bandwidth_mbps
        propagation_delay = self.specs.latency_ms / 1000.0
        return transmission_time + propagation_delay

    def get_stats(self) -> Dict:
        """Get link statistics"""
        total_transmissions = len(self.transmission_history)
        total_time = sum(t['transmission_time_s'] for t in self.transmission_history)

        return {
            'id': self.id,
            'source_server_id': self.source_id,
            'target_server_id': self.target_id,
            'bandwidth_mbps': self.specs.bandwidth_mbps,
            'latency_ms': self.specs.latency_ms,
            'total_data_transmitted_mb': self.data_transmitted_mb,
            'num_transmissions': total_transmissions,
            'total_transmission_time_s': total_time,
            'avg_transmission_time_s': total_time / total_transmissions if total_transmissions > 0 else 0
        }

    def __repr__(self):
        return f"NetworkLink(id={self.id}, {self.source_id}->{self.target_id}, bw={self.specs.bandwidth_mbps}Mbps)"
