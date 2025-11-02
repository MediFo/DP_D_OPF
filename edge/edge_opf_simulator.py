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
        print(f"Loaded {len(self.device_configs)} device configurations from {config_file}")
        return self.device_configs

    def setup_edge_infrastructure(self,
                                  num_servers: int = 3,
                                  server_specs: Optional[ServerSpecs] = None,
                                  config_file: Optional[str] = None):
        """
        Setup edge computing infrastructure

        Args:
            num_servers: Number of edge servers to create
            server_specs: Hardware specifications for servers (same for all if provided)
            config_file: Path to JSON configuration file with device specifications
                        If provided, reads first num_servers devices from the file
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
                print(f"  Server {server_id}: {server_name}")
                print(f"    - CPU: {specs.cpu_cores} cores @ {specs.cpu_freq_ghz} GHz")
                print(f"    - Memory: {specs.memory_gb} GB")
                print(f"    - Power: {specs.power_idle_w}W idle, {specs.power_max_w}W max")
            elif server_specs:
                # Use provided specs (same for all)
                specs = server_specs
                server_name = f"EdgeServer_{server_id}"
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

            server = self.simulator.add_server(
                server_id=server_id,
                name=server_name,
                location=(i * 10.0, i * 10.0),  # Distributed locations
                specs=specs
            )

            self.server_configs[server_id] = specs

        # Create network links between servers (full mesh for ADMM)
        link_id = 1
        for i in range(num_servers):
            for j in range(i + 1, num_servers):
                source_id = i + 1
                target_id = j + 1

                # Bidirectional links
                specs = LinkSpecs(
                    bandwidth_mbps=100.0,
                    latency_ms=10.0,
                    packet_loss_rate=0.001
                )

                # Source -> Target
                self.simulator.add_link(link_id, source_id, target_id, specs)
                link_id += 1

                # Target -> Source
                self.simulator.add_link(link_id, target_id, source_id, specs)
                link_id += 1

        print(f"Created {num_servers} edge servers and {link_id - 1} network links")

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

                        # Update server resources
                        if 'resource_monitoring' in result:
                            stats = result['resource_monitoring']
                            self.simulator.update_server_resources(
                                node_id,
                                stats.get('avg_cpu_percent', 0),
                                stats.get('avg_memory_mb', 0)
                            )

                            # Record service resource usage
                            service.record_resource_usage(
                                stats.get('avg_cpu_percent', 0),
                                stats.get('avg_memory_mb', 0)
                            )

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

                    # Update resources
                    if 'resource_monitoring' in result:
                        stats = result['resource_monitoring']
                        self.simulator.update_server_resources(
                            node_id,
                            stats.get('avg_cpu_percent', 0),
                            stats.get('avg_memory_mb', 0)
                        )
                        service.record_resource_usage(
                            stats.get('avg_cpu_percent', 0),
                            stats.get('avg_memory_mb', 0)
                        )

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
        Simulate network communication overhead for ADMM

        Args:
            services: List of services representing OPF nodes
        """
        # Estimate data transfer for ADMM consensus
        # Each node exchanges dual variables with neighbors
        data_per_exchange_mb = 0.01  # 10KB per exchange (small messages)
        num_exchanges = 100  # Typical number of ADMM iterations

        for i, service_i in enumerate(services):
            for j, service_j in enumerate(services):
                if i != j:
                    # Simulate data transfer
                    service_i.record_network_transfer(
                        sent_mb=data_per_exchange_mb * num_exchanges,
                        recv_mb=data_per_exchange_mb * num_exchanges
                    )

                    # Record in network links
                    self.simulator.record_network_transfer(
                        service_i.node_id,
                        service_j.node_id,
                        data_per_exchange_mb * num_exchanges
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
