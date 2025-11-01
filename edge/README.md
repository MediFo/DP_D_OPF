# Edge Device Evaluation for Distributed OPF

This module evaluates the runtime and resource utilization of Optimal Power Flow (OPF) computation on edge computing devices using a custom EdgeSimPy-based simulator.

## Overview

The system integrates:
- **Julia OPF Implementation**: Distributed ADMM-based OPF with differential privacy
- **EdgeSimPy Modules**: Edge computing simulation framework
- **Resource Monitoring**: CPU, memory, network, and power consumption tracking
- **Visualization**: Comprehensive CSV export and plotting capabilities

## Directory Structure

```
edge/
├── edgesimpy/              # EdgeSimPy simulation modules
│   ├── __init__.py
│   ├── edge_server.py      # Edge server component
│   ├── edge_service.py     # Service/task component
│   ├── network_link.py     # Network connectivity
│   ├── resource_monitor.py # Resource monitoring
│   └── simulator.py        # Main simulator
├── scripts/                # Modified Julia scripts
│   ├── opf_edge_node.jl    # Distributed ADMM node
│   └── opf_centralized_edge.jl  # Centralized OPF
├── results/                # Output directory for CSV and JSON
├── plots/                  # Output directory for visualizations
├── julia_wrapper.py        # Python-Julia interface
├── edge_opf_simulator.py   # Edge OPF simulator
├── visualization.py        # CSV export and plotting
├── evaluate_edge_opf.py    # Main evaluation script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

### 1. Install Python Dependencies

```bash
cd edge
pip install -r requirements.txt
```

### 2. Julia Setup

Ensure Julia is installed and the following packages are available:
- PowerModels
- JuMP
- Gurobi
- DataFrames
- CSV
- Distributions
- JSON

### 3. Verify Installation

```bash
python -c "import psutil, numpy, matplotlib; print('Python dependencies OK')"
julia --version
```

## Usage

### Quick Start

Run a comparison evaluation (both centralized and distributed):

```bash
python evaluate_edge_opf.py --mode comparison --servers 3
```

### Evaluation Modes

#### 1. Distributed OPF on Multiple Edge Servers

```bash
python evaluate_edge_opf.py --mode distributed --servers 5 --iterations 1000
```

Options:
- `--servers N`: Number of edge servers (default: 3)
- `--iterations N`: Maximum ADMM iterations (default: 1000)
- `--sequential`: Run nodes sequentially instead of parallel
- `--case PATH`: Power system test case file

#### 2. Centralized OPF on Single Edge Server

```bash
python evaluate_edge_opf.py --mode centralized
```

#### 3. Comparison Mode (Recommended)

```bash
python evaluate_edge_opf.py --mode comparison --servers 3
```

Runs both centralized and distributed evaluations for direct comparison.

## Outputs

### CSV Files (in `results/`)

- `*_servers.csv`: Server resource statistics
- `*_services.csv`: Service execution metrics
- `*_links.csv`: Network link statistics
- `*_node_execution.csv`: Per-node OPF execution details
- `*_global_resources.csv`: Global resource monitoring
- `*_summary.csv`: High-level summary

### Plots (in `plots/`)

- `*_server_resources.png`: CPU, memory, power comparison across servers
- `*_node_performance.png`: Execution time, iterations, performance
- `*_resource_timeline.png`: CPU and memory usage over time
- `*_network_traffic.png`: Data transfer between edge servers

### JSON Files (in `results/`)

- `*_full.json`: Complete simulation results with all metrics
- `comparison_*.json`: Combined centralized and distributed results

## Architecture

### Components

1. **EdgeSimPy Modules** (`edgesimpy/`)
   - Lightweight edge computing simulator
   - Models servers, services, and network infrastructure
   - Tracks resource usage and power consumption

2. **Julia Wrapper** (`julia_wrapper.py`)
   - Executes Julia OPF scripts as subprocesses
   - Monitors process resources (CPU, memory)
   - Captures execution time and results

3. **Edge OPF Simulator** (`edge_opf_simulator.py`)
   - Integrates Julia execution with EdgeSimPy
   - Manages distributed node coordination
   - Simulates network communication overhead

4. **Visualization** (`visualization.py`)
   - Exports results to CSV format
   - Generates publication-quality plots
   - Provides summary statistics

### Workflow

```
[Edge Infrastructure Setup]
         ↓
[Create OPF Services for Each Node]
         ↓
[Execute Julia OPF (Parallel/Sequential)]
         ↓
[Monitor Resources: CPU, Memory, Network]
         ↓
[Simulate Network Communication]
         ↓
[Export Results: CSV + Plots + JSON]
```

## Customization

### Modify Edge Server Specifications

Edit in `evaluate_edge_opf.py`:

```python
server_specs = ServerSpecs(
    cpu_cores=8,           # CPU cores
    cpu_freq_ghz=3.0,      # CPU frequency
    memory_gb=16.0,        # RAM
    storage_gb=200.0,      # Storage
    power_idle_w=30.0,     # Idle power
    power_max_w=200.0      # Max power
)
```

### Modify OPF Parameters

Edit in `evaluate_edge_opf.py`:

```python
julia_config = JuliaConfig(
    max_iterations=2000,   # ADMM iterations
    rho=1e3,              # ADMM penalty parameter
    tolerance=1e-3,       # Convergence tolerance
    epsilon=1.0,          # Privacy parameter
    method="PVP"          # Privacy method (PVP/DVP)
)
```

### Network Configuration

Edit in `edge_opf_simulator.py`:

```python
specs = LinkSpecs(
    bandwidth_mbps=1000.0,  # Link bandwidth
    latency_ms=5.0,         # Network latency
    packet_loss_rate=0.0    # Packet loss
)
```

## Example Output

```
================================================================================
COMPARATIVE EVALUATION: DISTRIBUTED vs CENTRALIZED OPF
================================================================================

>>> Phase 1: Centralized OPF
Running centralized OPF on single edge server...
✓ Centralized OPF completed successfully

>>> Phase 2: Distributed OPF
Running distributed OPF with 3 edge servers...
✓ Node 1 completed successfully
✓ Node 2 completed successfully
✓ Node 3 completed successfully

COMPARISON SUMMARY
================================================================================

Execution Time:
  - Centralized: 12.456s
  - Distributed: 8.234s

CPU Usage:
  - Centralized Avg: 87.3%
  - Distributed Avg: 56.2%

Memory Usage:
  - Centralized Max: 2048.5 MB
  - Distributed Max: 1456.3 MB

✓ Evaluation completed successfully!
```

## Metrics Tracked

### Server-Level Metrics
- CPU utilization (avg, max, min)
- Memory usage (avg, max, min)
- Power consumption (instantaneous, average)
- Energy consumption (total)

### Service-Level Metrics
- Execution time
- ADMM iterations to convergence
- Average iteration time
- Network data transfer (sent/received)

### Network Metrics
- Total data transmitted per link
- Number of transmissions
- Average transmission time
- Latency measurements

### Global Metrics
- Total simulation duration
- Aggregate resource usage
- Success/failure rates
- Convergence behavior

## Troubleshooting

### Julia Not Found
```bash
export PATH="/path/to/julia/bin:$PATH"
```

### Permission Errors
Ensure the `results/` and `plots/` directories are writable.

### Gurobi License
Make sure Gurobi is properly licensed and accessible from Julia.

### Import Errors
```bash
cd edge
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Notes

- The original `main.jl` remains unchanged
- All edge evaluation code is isolated in the `edge/` folder
- Results are timestamped to avoid overwriting
- Failed nodes are reported but don't stop the simulation
- Network communication is simulated (not actual data transfer)

## References

- Original OPF Implementation: `../main.jl`
- EdgeSimPy Inspiration: https://github.com/MediFo/EdgeSimPy
- Power system test cases: `../testbeds/`

## Contact

For questions or issues, please refer to the main repository documentation.
