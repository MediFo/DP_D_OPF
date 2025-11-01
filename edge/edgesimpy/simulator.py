"""
Edge Computing Simulator for OPF Evaluation
"""
import time
from typing import List, Dict, Optional
from .edge_server import EdgeServer, ServerSpecs
from .edge_service import EdgeService, ServiceRequirements
from .network_link import NetworkLink, LinkSpecs
from .resource_monitor import ResourceMonitor


class EdgeSimulator:
    """
    Main simulator class for edge computing environment
    """

    def __init__(self, name: str = "OPF_Edge_Simulation"):
        """
        Initialize edge simulator

        Args:
            name: Simulation name
        """
        self.name = name
        self.current_time = 0.0
        self.start_time = None
        self.end_time = None

        # Components
        self.servers: Dict[int, EdgeServer] = {}
        self.services: Dict[int, EdgeService] = {}
        self.links: Dict[int, NetworkLink] = {}

        # Monitoring
        self.global_monitor = ResourceMonitor()

        # Event log
        self.events: List[Dict] = []

    def add_server(self,
                   server_id: int,
                   name: str,
                   location: tuple = (0.0, 0.0),
                   specs: Optional[ServerSpecs] = None) -> EdgeServer:
        """
        Add an edge server to the simulation

        Args:
            server_id: Unique server ID
            name: Server name
            location: Geographic location
            specs: Hardware specifications

        Returns:
            Created EdgeServer instance
        """
        server = EdgeServer(server_id, name, location, specs)
        self.servers[server_id] = server
        self.log_event(f"Added server: {name} (ID: {server_id})")
        return server

    def add_service(self,
                    service_id: int,
                    name: str,
                    service_type: str = "opf_computation",
                    requirements: Optional[ServiceRequirements] = None,
                    node_id: Optional[int] = None) -> EdgeService:
        """
        Add a service to the simulation

        Args:
            service_id: Unique service ID
            name: Service name
            service_type: Type of service
            requirements: Resource requirements
            node_id: Associated power grid node ID

        Returns:
            Created EdgeService instance
        """
        service = EdgeService(service_id, name, service_type, requirements, node_id)
        self.services[service_id] = service
        self.log_event(f"Added service: {name} (ID: {service_id})")
        return service

    def add_link(self,
                 link_id: int,
                 source_server_id: int,
                 target_server_id: int,
                 specs: Optional[LinkSpecs] = None) -> NetworkLink:
        """
        Add a network link between servers

        Args:
            link_id: Unique link ID
            source_server_id: Source server ID
            target_server_id: Target server ID
            specs: Link specifications

        Returns:
            Created NetworkLink instance
        """
        link = NetworkLink(link_id, source_server_id, target_server_id, specs)
        self.links[link_id] = link
        self.log_event(f"Added link: {source_server_id} -> {target_server_id}")
        return link

    def assign_service_to_server(self, service_id: int, server_id: int):
        """
        Assign a service to an edge server

        Args:
            service_id: Service ID to assign
            server_id: Target server ID
        """
        if service_id not in self.services:
            raise ValueError(f"Service {service_id} not found")
        if server_id not in self.servers:
            raise ValueError(f"Server {server_id} not found")

        service = self.services[service_id]
        server = self.servers[server_id]

        server.assign_service(service)
        self.log_event(f"Assigned service {service.name} to server {server.name}")

    def start_simulation(self):
        """Start the simulation"""
        self.start_time = time.time()
        self.current_time = 0.0
        self.global_monitor.start()
        self.log_event("Simulation started")

    def stop_simulation(self):
        """Stop the simulation"""
        self.end_time = time.time()
        self.global_monitor.stop()
        self.log_event("Simulation stopped")

    def update_server_resources(self, server_id: int, cpu_percent: float, memory_mb: float):
        """
        Update resource usage for a specific server

        Args:
            server_id: Server ID
            cpu_percent: CPU usage percentage
            memory_mb: Memory usage in MB
        """
        if server_id in self.servers:
            self.servers[server_id].update_resource_usage(cpu_percent, memory_mb)

    def record_network_transfer(self, source_id: int, target_id: int, data_mb: float):
        """
        Record network data transfer between servers

        Args:
            source_id: Source server ID
            target_id: Target server ID
            data_mb: Amount of data in MB
        """
        # Find link
        for link in self.links.values():
            if link.source_id == source_id and link.target_id == target_id:
                link.transmit_data(data_mb, self.current_time)
                break

    def log_event(self, message: str):
        """
        Log a simulation event

        Args:
            message: Event message
        """
        self.events.append({
            'timestamp': time.time() - (self.start_time or time.time()),
            'message': message
        })

    def get_simulation_stats(self) -> Dict:
        """Get comprehensive simulation statistics"""
        duration = (self.end_time or time.time()) - (self.start_time or time.time())

        # Server statistics
        server_stats = {sid: server.get_summary_stats() for sid, server in self.servers.items()}

        # Service statistics
        service_stats = {sid: service.get_stats() for sid, service in self.services.items()}

        # Link statistics
        link_stats = {lid: link.get_stats() for lid, link in self.links.items()}

        # Global resource monitoring
        global_resources = self.global_monitor.get_summary()

        return {
            'simulation_name': self.name,
            'duration_s': duration,
            'num_servers': len(self.servers),
            'num_services': len(self.services),
            'num_links': len(self.links),
            'servers': server_stats,
            'services': service_stats,
            'links': link_stats,
            'global_resources': global_resources,
            'events': self.events
        }

    def get_time_series_data(self) -> Dict:
        """Get time series data for visualization"""
        return {
            'global': self.global_monitor.get_time_series(),
            'servers': {sid: {
                'cpu': server.cpu_usage_history,
                'memory': server.memory_usage_history,
                'power': server.power_usage_history
            } for sid, server in self.servers.items()}
        }

    def __repr__(self):
        return f"EdgeSimulator(name={self.name}, servers={len(self.servers)}, services={len(self.services)})"
