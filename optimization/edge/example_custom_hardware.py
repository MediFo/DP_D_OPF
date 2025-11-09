"""
Example: Custom Edge Server Configurations
Shows how to configure different hardware specs for each edge server
"""

from edge_opf_simulator import EdgeOPFSimulator
from edgesimpy.edge_server import ServerSpecs
from edgesimpy.network_link import LinkSpecs
from julia_wrapper import JuliaConfig
from visualization import ResultsExporter

# Create simulator
sim = EdgeOPFSimulator("Custom_Hardware_OPF_Evaluation")

print("="*80)
print("Setting up edge infrastructure with CUSTOM hardware for each server")
print("="*80)
print()

# Define custom specs for each server
# Each dict represents a different type of edge device

server_configs = {
    # Server 1: High-end edge server (data center edge)
    1: ServerSpecs(
        cpu_cores=8,
        cpu_freq_ghz=3.5,
        memory_gb=16.0,
        storage_gb=500.0,
        power_idle_w=80.0,
        power_max_w=250.0
    ),

    # Server 2: Mid-range edge server (enterprise edge)
    2: ServerSpecs(
        cpu_cores=4,
        cpu_freq_ghz=2.8,
        memory_gb=8.0,
        storage_gb=256.0,
        power_idle_w=50.0,
        power_max_w=150.0
    ),

    # Server 3: Low-power edge device (IoT gateway)
    3: ServerSpecs(
        cpu_cores=2,
        cpu_freq_ghz=1.8,
        memory_gb=4.0,
        storage_gb=64.0,
        power_idle_w=15.0,
        power_max_w=45.0
    ),

    # Server 4: Raspberry Pi-like device
    4: ServerSpecs(
        cpu_cores=4,
        cpu_freq_ghz=1.5,
        memory_gb=2.0,
        storage_gb=32.0,
        power_idle_w=3.0,
        power_max_w=15.0
    ),

    # Server 5: Industrial edge controller
    5: ServerSpecs(
        cpu_cores=6,
        cpu_freq_ghz=2.2,
        memory_gb=12.0,
        storage_gb=128.0,
        power_idle_w=40.0,
        power_max_w=120.0
    )
}

# Manually create servers with custom specs
num_servers = len(server_configs)
print(f"Creating {num_servers} edge servers with custom specifications:")
print()

for server_id, specs in server_configs.items():
    server = sim.simulator.add_server(
        server_id=server_id,
        name=f"EdgeServer_{server_id}",
        location=(server_id * 10.0, server_id * 10.0),
        specs=specs
    )

    print(f"Server {server_id}:")
    print(f"  - CPU: {specs.cpu_cores} cores @ {specs.cpu_freq_ghz} GHz")
    print(f"  - Memory: {specs.memory_gb} GB")
    print(f"  - Storage: {specs.storage_gb} GB")
    print(f"  - Power: {specs.power_idle_w}W (idle) to {specs.power_max_w}W (max)")
    print()

sim.num_edge_servers = num_servers

# Create network links with varying characteristics
print("Creating network links with different characteristics:")
print()

network_configs = {
    # Links between high-performance servers (fiber)
    (1, 2): LinkSpecs(bandwidth_mbps=1000.0, latency_ms=2.0, packet_loss_rate=0.0001),
    (2, 1): LinkSpecs(bandwidth_mbps=1000.0, latency_ms=2.0, packet_loss_rate=0.0001),

    # Links to mid-range servers (ethernet)
    (2, 3): LinkSpecs(bandwidth_mbps=100.0, latency_ms=10.0, packet_loss_rate=0.001),
    (3, 2): LinkSpecs(bandwidth_mbps=100.0, latency_ms=10.0, packet_loss_rate=0.001),

    # Links to low-power devices (WiFi)
    (3, 4): LinkSpecs(bandwidth_mbps=50.0, latency_ms=20.0, packet_loss_rate=0.01),
    (4, 3): LinkSpecs(bandwidth_mbps=50.0, latency_ms=20.0, packet_loss_rate=0.01),

    # Links to industrial controllers (ethernet)
    (1, 5): LinkSpecs(bandwidth_mbps=100.0, latency_ms=5.0, packet_loss_rate=0.0005),
    (5, 1): LinkSpecs(bandwidth_mbps=100.0, latency_ms=5.0, packet_loss_rate=0.0005),

    # Create full mesh with default specs for remaining links
}

link_id = 1
for i in range(1, num_servers + 1):
    for j in range(i + 1, num_servers + 1):
        # Check if custom link config exists
        if (i, j) in network_configs:
            forward_specs = network_configs[(i, j)]
            backward_specs = network_configs[(j, i)]
        else:
            # Use default specs
            forward_specs = backward_specs = LinkSpecs(
                bandwidth_mbps=100.0,
                latency_ms=10.0,
                packet_loss_rate=0.001
            )

        # Add bidirectional links
        sim.simulator.add_link(link_id, i, j, forward_specs)
        print(f"  Link {i} → {j}: {forward_specs.bandwidth_mbps} Mbps, {forward_specs.latency_ms} ms")
        link_id += 1

        sim.simulator.add_link(link_id, j, i, backward_specs)
        link_id += 1

print()
print(f"Created {link_id - 1} network links")
print()

# Run distributed OPF
print("="*80)
print("Running Distributed OPF on Custom Edge Infrastructure")
print("="*80)
print()

julia_config = JuliaConfig(
    max_iterations=1000,
    tolerance=1e-2,
    method="PVP"
)

results = sim.run_distributed_opf(julia_config=julia_config, parallel=True)

# Export results
print()
print("="*80)
print("Exporting Results")
print("="*80)

exporter = ResultsExporter()
import time
timestamp = time.strftime("%Y%m%d_%H%M%S")
prefix = f"custom_hardware_{timestamp}"

# Save results
import json
from pathlib import Path
results_file = Path("results") / f"{prefix}_full.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2, default=str)

exporter.export_to_csv(results, prefix)
exporter.generate_plots(results, prefix)

# Print summary
print()
print("="*80)
print("Hardware-Specific Results")
print("="*80)
print()

for server_id, stats in results['simulation_stats']['servers'].items():
    specs = server_configs[int(server_id)]
    print(f"Server {server_id} ({specs.cpu_cores} cores, {specs.memory_gb}GB RAM):")
    print(f"  - Avg CPU: {stats['avg_cpu_usage']:.1f}%")
    print(f"  - Max CPU: {stats['max_cpu_usage']:.1f}%")
    print(f"  - Avg Memory: {stats['avg_memory_usage_mb']:.1f} MB")
    print(f"  - Avg Power: {stats['avg_power_w']:.1f} W")
    print(f"  - Total Energy: {stats['total_energy_wh']:.4f} Wh")
    print()

print("="*80)
print(f"Results saved to results/{prefix}_*.csv")
print(f"Plots saved to plots/{prefix}_*.png")
print("="*80)
