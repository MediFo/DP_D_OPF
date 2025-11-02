"""
Edge OPF Simulator - Integrates Julia OPF with EdgeSimPy
Simulates distributed OPF computation on edge devices
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from edgesimpy.simulator import EdgeSimulator
from edgesimpy.edge_server import EdgeServer, ServerSpecs
from edgesimpy.edge_service import EdgeService, ServiceRequirements
from edgesimpy.network_link import NetworkLink, LinkSpecs
from julia_wrapper import JuliaOPFExecutor, JuliaConfig
from power_grid_topology import get_bus_neighbors, get_grid_statistics


class EdgeOPFSimulator:
    """
    Simulates OPF computation on edge computing infrastructure
    """

    def __init__(self, name: str = "Distributed_OPF_Edge_Simulation"):
        """
        Initialize the edge OPF simulator

        Args:
            name: Simulation name
        """
        self.name = name
        self.simulator = EdgeSimulator(name)
        self.julia_executor = JuliaOPFExecutor()

        # Configuration
        self.num_edge_servers = 0
        self.server_configs: Dict[int, ServerSpecs] = {}
        self.link_configs: Dict[int, LinkSpecs] = {}
        self.device_configs: List[Dict] = []  # Loaded from JSON config
        self.network_profiles: Dict[str, Dict] = {}  # Network link profiles
        self.device_performance: Dict[int, Dict] = {}  # Performance characteristics per device

        # Results storage
        self.execution_results: List[Dict] = []

    def load_device_configs_from_json(self, config_file: str) -> List[Dict]:
        """
        Load device configurations from JSON file

        Args:
            config_file: Path to JSON configuration file

        Returns:
            List of device configurations
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, 'r') as f:
            config_data = json.load(f)

        if 'devices' not in config_data:
            raise ValueError("Invalid configuration file: 'devices' key not found")

        self.device_configs = config_data['devices']
        self.network_profiles = config_data.get('network_profiles', {})

        print(f"Loaded {len(self.device_configs)} device configurations from {config_file}")
        if self.network_profiles:
            print(f"Loaded {len(self.network_profiles)} network profiles")

        return self.device_configs

    def _get_network_link_specs(self, device1: Dict, device2: Dict) -> LinkSpecs:
        """
        Determine network link specifications based on device network types
        Uses the worse network type between two devices

        Args:
            device1: First device configuration
            device2: Second device configuration

        Returns:
            LinkSpecs for the connection
        """
        import random

        net_type1 = device1.get('network_type', 'ethernet_fast')
        net_type2 = device2.get('network_type', 'ethernet_fast')

        # Network type priority (lower is better)
        priority = {
            'fiber': 1,
            'ethernet_gigabit': 2,
            'ethernet_fast': 3,
            'wifi_ac': 4,
            'wifi_n': 5,
            'lte': 6,
            'low_bandwidth': 7
        }

        # Use the worse network type (bottleneck)
        if priority.get(net_type1, 3) > priority.get(net_type2, 3):
            net_type = net_type1
        else:
            net_type = net_type2

        # Get base specs from network profile
        if net_type in self.network_profiles:
            profile = self.network_profiles[net_type]
            # Add random variation (+/- 10%)
            variation = random.uniform(0.9, 1.1)
            bandwidth = profile['bandwidth_mbps'] * variation
            latency = profile['latency_ms'] * variation
            packet_loss = profile['packet_loss_rate'] * variation
        else:
            # Default specs
            bandwidth = 100.0
            latency = 10.0
            packet_loss = 0.001

        return LinkSpecs(
            bandwidth_mbps=bandwidth,
            latency_ms=latency,
            packet_loss_rate=packet_loss
        )

    def _scale_resource_utilization(self, node_id: int, stats: Dict) -> Dict:
        """
        Scale resource utilization based on device performance characteristics
        Lower compute efficiency = higher CPU usage for same workload
        Lower memory efficiency = higher memory usage

        Args:
            node_id: Node identifier
            stats: Raw resource monitoring statistics

        Returns:
            Scaled resource statistics
        """
        import random

        if node_id not in self.device_performance:
            return stats

        perf = self.device_performance[node_id]

        # Scale CPU usage inversely with compute efficiency
        # Lower efficiency means higher utilization for same workload
        compute_eff = perf.get('compute_efficiency', 1.0)
        cpu_scale = 1.0 / compute_eff if compute_eff > 0 else 1.0

        # Scale memory usage inversely with memory efficiency
        memory_eff = perf.get('memory_efficiency', 1.0)
        mem_scale = 1.0 / memory_eff if memory_eff > 0 else 1.0

        # Add random variation (±5%) for realism
        cpu_variation = random.uniform(0.95, 1.05)
        mem_variation = random.uniform(0.95, 1.05)

        # Scale workload-dependent resources
        workload_factor = perf.get('workload_capacity', 1.0)

        scaled_stats = stats.copy()

        # Scale CPU metrics
        if 'avg_cpu_percent' in stats:
            scaled_stats['avg_cpu_percent'] = min(100.0, stats['avg_cpu_percent'] * cpu_scale * cpu_variation)
        if 'max_cpu_percent' in stats:
            scaled_stats['max_cpu_percent'] = min(100.0, stats['max_cpu_percent'] * cpu_scale * cpu_variation)

        # Scale memory metrics
        if 'avg_memory_mb' in stats:
            scaled_stats['avg_memory_mb'] = stats['avg_memory_mb'] * mem_scale * mem_variation
        if 'max_memory_mb' in stats:
            scaled_stats['max_memory_mb'] = stats['max_memory_mb'] * mem_scale * mem_variation

        # Scale network transfer based on workload (more capable devices handle more data)
        if 'network_sent_mb' in stats:
            scaled_stats['network_sent_mb'] = stats['network_sent_mb'] * workload_factor
        if 'network_recv_mb' in stats:
            scaled_stats['network_recv_mb'] = stats['network_recv_mb'] * workload_factor

        return scaled_stats

    def setup_edge_infrastructure(self,
                                  num_servers: int = 3,
                                  server_specs: Optional[ServerSpecs] = None,
                                  config_file: Optional[str] = None,
                                  case_file: Optional[str] = None):
        """
        Setup edge computing infrastructure with topology matching power grid

        Args:
            num_servers: Number of edge servers to create
            server_specs: Hardware specifications for servers (same for all if provided)
            config_file: Path to JSON configuration file with device specifications
                        If provided, reads first num_servers devices from the file
            case_file: Path to MATPOWER case file for network topology
                      If provided, network links follow power grid topology
        """
        self.num_edge_servers = num_servers

        print(f"Setting up edge infrastructure with {num_servers} servers...")

        # Load device configurations from JSON if provided
        if config_file:
            self.load_device_configs_from_json(config_file)
            if len(self.device_configs) < num_servers:
                print(f"Warning: Config file has {len(self.device_configs)} devices, but {num_servers} servers requested.")
                print(f"Using first {min(len(self.device_configs), num_servers)} configurations.")

        # Create edge servers
        for i in range(num_servers):
            server_id = i + 1
            device_config = None

            # Determine specs for this server
            if config_file and i < len(self.device_configs):
                # Use configuration from JSON file
                device_config = self.device_configs[i]
                specs_dict = device_config['specs']
                specs = ServerSpecs(
                    cpu_cores=specs_dict['cpu_cores'],
                    cpu_freq_ghz=specs_dict['cpu_freq_ghz'],
                    memory_gb=specs_dict['memory_gb'],
                    storage_gb=specs_dict['storage_gb'],
                    power_idle_w=specs_dict['power_idle_w'],
                    power_max_w=specs_dict['power_max_w']
                )
                server_name = device_config.get('name', f"EdgeServer_{server_id}")

                # Store performance characteristics
                self.device_performance[server_id] = device_config.get('performance', {
                    'compute_efficiency': 1.0,
                    'memory_efficiency': 1.0,
                    'workload_capacity': 1.0,
                    'reliability': 0.95
                })

                print(f"  Server {server_id}: {server_name}")
                print(f"    - Tier: {device_config.get('tier', 'standard')}")
                print(f"    - Network: {device_config.get('network_type', 'ethernet_fast')}")
                print(f"    - CPU: {specs.cpu_cores} cores @ {specs.cpu_freq_ghz} GHz")
                print(f"    - Memory: {specs.memory_gb} GB")
                print(f"    - Power: {specs.power_idle_w}W idle, {specs.power_max_w}W max")
                print(f"    - Compute Efficiency: {self.device_performance[server_id]['compute_efficiency']:.2f}x")
            elif server_specs:
                # Use provided specs (same for all)
                specs = server_specs
                server_name = f"EdgeServer_{server_id}"
                self.device_performance[server_id] = {
                    'compute_efficiency': 1.0,
                    'memory_efficiency': 1.0,
                    'workload_capacity': 1.0,
                    'reliability': 0.95
                }
            else:
                # Use default specs
                specs = ServerSpecs(
                    cpu_cores=4,
                    cpu_freq_ghz=2.4,
                    memory_gb=8.0,
                    storage_gb=100.0,
                    power_idle_w=50.0,
                    power_max_w=150.0
                )
                server_name = f"EdgeServer_{server_id}"
                self.device_performance[server_id] = {
                    'compute_efficiency': 1.0,
                    'memory_efficiency': 1.0,
                    'workload_capacity': 1.0,
                    'reliability': 0.95
                }

            server = self.simulator.add_server(
                server_id=server_id,
                name=server_name,
                location=(i * 10.0, i * 10.0),  # Distributed locations
                specs=specs
            )

            self.server_configs[server_id] = specs

        # Create network links based on power grid topology
        link_id = 1
        print("\n  Creating network links:")

        if case_file:
            # Use power grid topology for network connections
            print(f"    Using topology from: {Path(case_file).name}")
            grid_stats = get_grid_statistics(case_file)
            bus_neighbors = grid_stats['neighbors']

            print(f"    Grid: {grid_stats['num_buses']} buses, {grid_stats['num_lines']} lines")
            print(f"    Average connections per node: {grid_stats['avg_connections_per_bus']:.2f}")

            # Create links only between neighboring buses
            created_links = set()

            for bus_id in range(1, num_servers + 1):
                if bus_id not in bus_neighbors:
                    continue

                neighbors = bus_neighbors[bus_id]

                for neighbor_id in neighbors:
                    # Only create link if neighbor is within our server range
                    if neighbor_id > num_servers:
                        continue

                    # Avoid creating duplicate bidirectional links
                    link_pair = tuple(sorted([bus_id, neighbor_id]))
                    if link_pair in created_links:
                        continue

                    created_links.add(link_pair)

                    # Determine link specs based on device network types
                    if config_file and (bus_id - 1) < len(self.device_configs) and (neighbor_id - 1) < len(self.device_configs):
                        device1 = self.device_configs[bus_id - 1]
                        device2 = self.device_configs[neighbor_id - 1]
                        link_specs = self._get_network_link_specs(device1, device2)
                        print(f"    Link {bus_id}↔{neighbor_id}: {link_specs.bandwidth_mbps:.0f} Mbps, {link_specs.latency_ms:.1f}ms latency")
                    else:
                        # Default specs
                        link_specs = LinkSpecs(
                            bandwidth_mbps=100.0,
                            latency_ms=10.0,
                            packet_loss_rate=0.001
                        )
                        print(f"    Link {bus_id}↔{neighbor_id}: {link_specs.bandwidth_mbps:.0f} Mbps, {link_specs.latency_ms:.1f}ms latency")

                    # Create bidirectional links
                    self.simulator.add_link(link_id, bus_id, neighbor_id, link_specs)
                    link_id += 1

                    self.simulator.add_link(link_id, neighbor_id, bus_id, link_specs)
                    link_id += 1

            print(f"\n✓ Created {num_servers} edge servers and {link_id - 1} network links (topology-based)")

        else:
            # Fallback to full mesh if no case file provided
            print("    Using full mesh topology (no case file provided)")
            for i in range(num_servers):
                for j in range(i + 1, num_servers):
                    source_id = i + 1
                    target_id = j + 1

                    # Determine link specs based on device network types
                    if config_file and i < len(self.device_configs) and j < len(self.device_configs):
                        device1 = self.device_configs[i]
                        device2 = self.device_configs[j]
                        link_specs = self._get_network_link_specs(device1, device2)
                        print(f"    Link {source_id}↔{target_id}: {link_specs.bandwidth_mbps:.0f} Mbps, {link_specs.latency_ms:.1f}ms latency")
                    else:
                        # Default specs
                        link_specs = LinkSpecs(
                            bandwidth_mbps=100.0,
                            latency_ms=10.0,
                            packet_loss_rate=0.001
                        )

                    # Source -> Target
                    self.simulator.add_link(link_id, source_id, target_id, link_specs)
                    link_id += 1

                    # Target -> Source (symmetric link with same specs)
                    self.simulator.add_link(link_id, target_id, source_id, link_specs)
                    link_id += 1

            print(f"\n✓ Created {num_servers} edge servers and {link_id - 1} network links (full mesh)")

    def run_distributed_opf(self,
                           julia_config: Optional[JuliaConfig] = None,
                           parallel: bool = True) -> Dict:
        """
        Run distributed OPF computation across edge servers

        Args:
            julia_config: Configuration for Julia OPF execution
            parallel: Whether to run nodes in parallel

        Returns:
            Comprehensive simulation results
        """
        print("="*80)
        print(f"Running Distributed OPF on {self.num_edge_servers} Edge Devices")
        print("="*80)

        # Start simulation
        self.simulator.start_simulation()

        # Create services for each edge server (representing OPF nodes)
        services = []
        for i in range(self.num_edge_servers):
            node_id = i + 1
            service = self.simulator.add_service(
                service_id=node_id,
                name=f"OPF_Node_{node_id}",
                service_type="admm_opf_node",
                requirements=ServiceRequirements(
                    cpu_cores=2.0,
                    memory_mb=2048.0,
                    estimated_runtime_s=30.0
                ),
                node_id=node_id
            )

            # Assign service to corresponding server
            self.simulator.assign_service_to_server(node_id, node_id)
            services.append(service)

        # Execute OPF computation on each node
        node_results = []

        if parallel:
            # Parallel execution
            print("\nExecuting nodes in parallel...")
            with ThreadPoolExecutor(max_workers=self.num_edge_servers) as executor:
                futures = {}
                for i in range(self.num_edge_servers):
                    node_id = i + 1
                    service = services[i]
                    service.start()

                    future = executor.submit(
                        self.julia_executor.run_distributed_node,
                        node_id,
                        julia_config
                    )
                    futures[future] = (node_id, service)

                # Collect results
                for future in as_completed(futures):
                    node_id, service = futures[future]
                    try:
                        result = future.result()
                        node_results.append(result)

                        # Update service status
                        if result.get('success', False):
                            service.complete(result)
                            print(f"✓ Node {node_id} completed successfully")
                        else:
                            service.fail(result.get('error', 'Unknown error'))
                            print(f"✗ Node {node_id} failed")

                        # Update server resources with scaling
                        if 'resource_monitoring' in result:
                            raw_stats = result['resource_monitoring']
                            scaled_stats = self._scale_resource_utilization(node_id, raw_stats)

                            self.simulator.update_server_resources(
                                node_id,
                                scaled_stats.get('avg_cpu_percent', 0),
                                scaled_stats.get('avg_memory_mb', 0)
                            )

                            # Record service resource usage with scaled values
                            service.record_resource_usage(
                                scaled_stats.get('avg_cpu_percent', 0),
                                scaled_stats.get('avg_memory_mb', 0)
                            )

                            # Store scaled stats back in result for reporting
                            result['resource_monitoring_scaled'] = scaled_stats

                    except Exception as e:
                        print(f"✗ Node {node_id} failed with exception: {e}")
                        service.fail(str(e))
        else:
            # Sequential execution
            print("\nExecuting nodes sequentially...")
            for i in range(self.num_edge_servers):
                node_id = i + 1
                service = services[i]
                service.start()

                try:
                    result = self.julia_executor.run_distributed_node(node_id, julia_config)
                    node_results.append(result)

                    if result.get('success', False):
                        service.complete(result)
                        print(f"✓ Node {node_id} completed successfully")
                    else:
                        service.fail(result.get('error', 'Unknown error'))
                        print(f"✗ Node {node_id} failed")

                    # Update resources with scaling
                    if 'resource_monitoring' in result:
                        raw_stats = result['resource_monitoring']
                        scaled_stats = self._scale_resource_utilization(node_id, raw_stats)

                        self.simulator.update_server_resources(
                            node_id,
                            scaled_stats.get('avg_cpu_percent', 0),
                            scaled_stats.get('avg_memory_mb', 0)
                        )
                        service.record_resource_usage(
                            scaled_stats.get('avg_cpu_percent', 0),
                            scaled_stats.get('avg_memory_mb', 0)
                        )

                        # Store scaled stats back in result for reporting
                        result['resource_monitoring_scaled'] = scaled_stats

                except Exception as e:
                    print(f"✗ Node {node_id} failed with exception: {e}")
                    service.fail(str(e))

        # Simulate network communication overhead (ADMM requires inter-node communication)
        self._simulate_network_communication(services)

        # Stop simulation
        self.simulator.stop_simulation()

        # Gather comprehensive statistics
        sim_stats = self.simulator.get_simulation_stats()

        print("\n" + "="*80)
        print("Distributed OPF Simulation Completed")
        print("="*80)

        return {
            'simulation_name': self.name,
            'num_edge_servers': self.num_edge_servers,
            'execution_mode': 'parallel' if parallel else 'sequential',
            'node_results': node_results,
            'simulation_stats': sim_stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def run_centralized_opf(self, julia_config: Optional[Dict] = None) -> Dict:
        """
        Run centralized OPF on a single edge server for comparison

        Args:
            julia_config: Configuration for Julia execution

        Returns:
            Simulation results
        """
        print("="*80)
        print("Running Centralized OPF on Single Edge Device")
        print("="*80)

        # Start simulation
        self.simulator.start_simulation()

        # Use first server
        server_id = 1
        service = self.simulator.add_service(
            service_id=100,
            name="Centralized_OPF",
            service_type="centralized_opf",
            requirements=ServiceRequirements(
                cpu_cores=4.0,
                memory_mb=4096.0,
                estimated_runtime_s=60.0
            )
        )

        self.simulator.assign_service_to_server(100, server_id)
        service.start()

        # Execute centralized OPF
        result = self.julia_executor.run_centralized(julia_config)

        if result.get('success', False):
            service.complete(result)
            print("✓ Centralized OPF completed successfully")
        else:
            service.fail(result.get('error', 'Unknown error'))
            print("✗ Centralized OPF failed")

        # Update resources
        if 'resource_monitoring' in result:
            stats = result['resource_monitoring']
            self.simulator.update_server_resources(
                server_id,
                stats.get('avg_cpu_percent', 0),
                stats.get('avg_memory_mb', 0)
            )
            service.record_resource_usage(
                stats.get('avg_cpu_percent', 0),
                stats.get('avg_memory_mb', 0)
            )

        # Stop simulation
        self.simulator.stop_simulation()

        # Gather statistics
        sim_stats = self.simulator.get_simulation_stats()

        print("\n" + "="*80)
        print("Centralized OPF Simulation Completed")
        print("="*80)

        return {
            'simulation_name': self.name + "_Centralized",
            'execution_mode': 'centralized',
            'result': result,
            'simulation_stats': sim_stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _simulate_network_communication(self, services: List[EdgeService]):
        """
        Simulate network communication overhead for ADMM with variability

        Args:
            services: List of services representing OPF nodes
        """
        import random

        # Base data transfer for ADMM consensus
        base_data_per_exchange_mb = 0.01  # 10KB per exchange (small messages)
        num_exchanges = 100  # Typical number of ADMM iterations

        for i, service_i in enumerate(services):
            node_i = service_i.node_id

            # Get workload capacity for this node (affects data volume)
            perf_i = self.device_performance.get(node_i, {})
            workload_i = perf_i.get('workload_capacity', 1.0)

            for j, service_j in enumerate(services):
                if i != j:
                    node_j = service_j.node_id

                    # Get workload capacity for target node
                    perf_j = self.device_performance.get(node_j, {})
                    workload_j = perf_j.get('workload_capacity', 1.0)

                    # Data volume varies based on workload capacity
                    # Higher capacity devices process and send more data
                    workload_factor = (workload_i + workload_j) / 2.0

                    # Add random variation (±15%) for realistic network traffic
                    variation = random.uniform(0.85, 1.15)

                    # Calculate actual data transfer
                    data_sent = base_data_per_exchange_mb * num_exchanges * workload_factor * variation
                    data_recv = base_data_per_exchange_mb * num_exchanges * workload_factor * variation

                    # Simulate data transfer
                    service_i.record_network_transfer(
                        sent_mb=data_sent,
                        recv_mb=data_recv
                    )

                    # Record in network links
                    self.simulator.record_network_transfer(
                        node_i,
                        node_j,
                        data_sent
                    )


# Test execution
if __name__ == "__main__":
    # Create simulator
    sim = EdgeOPFSimulator("Test_Distributed_OPF")

    # Setup infrastructure
    sim.setup_edge_infrastructure(num_servers=3)

    # Run distributed OPF
    config = JuliaConfig(
        max_iterations=500,
        tolerance=1e-2,
        method="PVP"
    )

    results = sim.run_distributed_opf(julia_config=config, parallel=True)

    print("\nSimulation Summary:")
    print(f"Total servers: {results['num_edge_servers']}")
    print(f"Execution mode: {results['execution_mode']}")
    print(f"Successful nodes: {sum(1 for r in results['node_results'] if r.get('success', False))}")
