# Edge OPF Evaluation - Complete Usage Guide

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd edge
pip install -r requirements.txt
```

### 2. Run a Quick Test

```bash
# Run comparison evaluation (centralized vs distributed)
python evaluate_edge_opf.py --mode comparison --servers 3
```

### 3. Check Results

```bash
# View CSV results
ls -lh results/*.csv

# View plots
ls -lh plots/*.png
```

---

## Detailed Usage Examples

### Example 1: Evaluate Distributed OPF on 5 Edge Servers

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 5 \
    --iterations 1500 \
    --case testbeds/pglib_opf_case14_ieee.m
```

**What this does:**
- Creates 5 virtual edge servers
- Runs distributed ADMM OPF computation
- Executes nodes in parallel (default)
- Monitors CPU, memory, network, power
- Exports CSV files and generates plots

**Expected output:**
```
results/distributed_5servers_YYYYMMDD_HHMMSS_*.csv
plots/distributed_5servers_YYYYMMDD_HHMMSS_*.png
```

---

### Example 2: Sequential Execution for Debugging

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 3 \
    --sequential
```

**Why use this:**
- Easier to debug errors
- See output from each node sequentially
- Lower memory footprint
- More realistic for resource-constrained devices

---

### Example 3: Centralized OPF Baseline

```bash
python evaluate_edge_opf.py --mode centralized
```

**Purpose:**
- Establish baseline performance
- Compare against distributed approach
- Measure single-device resource limits

---

### Example 4: Full Comparison Study

```bash
python evaluate_edge_opf.py \
    --mode comparison \
    --servers 4 \
    --iterations 2000 \
    --case testbeds/pglib_opf_case14_ieee.m
```

**Generates:**
- Centralized OPF results
- Distributed OPF results (4 servers)
- Side-by-side comparison
- Combined JSON with both datasets

---

## Understanding the Results

### CSV Files Explained

#### 1. `*_servers.csv`
Server-level resource metrics:

| Column | Description |
|--------|-------------|
| Server_ID | Unique server identifier |
| Avg_CPU_% | Average CPU utilization |
| Max_CPU_% | Peak CPU usage |
| Avg_Memory_MB | Average memory consumption |
| Max_Memory_MB | Peak memory usage |
| Avg_Power_W | Average power draw |
| Total_Energy_Wh | Total energy consumed |

**Use case:** Identify resource-constrained servers, balance load

---

#### 2. `*_services.csv`
Service/task execution metrics:

| Column | Description |
|--------|-------------|
| Service_ID | Service identifier |
| Node_ID | Associated OPF node |
| Status | completed/failed |
| Runtime_s | Execution time |
| Avg_CPU_% | CPU usage during execution |
| Network_Sent_MB | Data transmitted |
| Network_Recv_MB | Data received |

**Use case:** Analyze per-node performance, identify bottlenecks

---

#### 3. `*_node_execution.csv`
OPF-specific execution details:

| Column | Description |
|--------|-------------|
| Node_ID | OPF node identifier |
| Iterations | ADMM iterations to convergence |
| Avg_Iteration_Time_ms | Time per iteration |
| Final_Cost | OPF objective value |
| Final_Residual | Convergence residual |

**Use case:** Understand OPF convergence behavior, algorithm performance

---

#### 4. `*_links.csv`
Network communication statistics:

| Column | Description |
|--------|-------------|
| Source_Server | Origin server |
| Target_Server | Destination server |
| Total_Data_MB | Data transferred |
| Num_Transmissions | Number of messages |
| Avg_Transmission_Time_s | Average transfer time |

**Use case:** Network capacity planning, communication overhead analysis

---

### Plots Explained

#### 1. Server Resources Plot
**File:** `*_server_resources.png`

**4 subplots:**
- CPU Utilization: Compare average and peak CPU across servers
- Memory Utilization: Average and peak memory usage
- Power Consumption: Average power draw per server
- Energy Consumption: Total energy used (important for edge devices!)

**Insights:**
- Are resources balanced across servers?
- Which server is the bottleneck?
- What's the power/energy cost of distributed OPF?

---

#### 2. Node Performance Plot
**File:** `*_node_performance.png`

**3 subplots:**
- Total Execution Time: How long each node took
- ADMM Iterations: Convergence speed per node
- Average Iteration Time: Computational efficiency

**Insights:**
- Do all nodes converge at similar rates?
- Which node is slower? (potential bottleneck)
- Is the algorithm converging efficiently?

---

#### 3. Resource Timeline Plot
**File:** `*_resource_timeline.png`

**2 time-series plots:**
- CPU Usage Over Time: Track CPU% throughout execution
- Memory Usage Over Time: Track memory consumption

**Insights:**
- When do resource peaks occur?
- Are there memory leaks?
- How does resource usage evolve during ADMM iterations?

---

#### 4. Network Traffic Plot
**File:** `*_network_traffic.png`

**Horizontal bar chart:**
- Data transferred per network link

**Insights:**
- Which links carry the most traffic?
- Is communication overhead significant?
- Network capacity requirements

---

## Advanced Configuration

### Custom Server Specifications

Edit `evaluate_edge_opf.py`, modify `server_specs`:

```python
server_specs = ServerSpecs(
    cpu_cores=8,           # 8-core CPU
    cpu_freq_ghz=3.5,      # 3.5 GHz
    memory_gb=32.0,        # 32 GB RAM
    storage_gb=500.0,      # 500 GB storage
    power_idle_w=25.0,     # 25W idle
    power_max_w=250.0      # 250W under load
)
```

**Use case:** Model different edge device types (Raspberry Pi, industrial PC, etc.)

---

### Custom OPF Parameters

Edit `evaluate_edge_opf.py`, modify `julia_config`:

```python
julia_config = JuliaConfig(
    max_iterations=5000,   # More iterations for harder problems
    rho=5e3,              # Adjust ADMM penalty
    tolerance=1e-4,       # Tighter convergence
    epsilon=0.5,          # Stronger privacy
    method="DVP"          # Use DVP instead of PVP
)
```

**Parameters explained:**
- `rho`: ADMM penalty parameter (higher = faster convergence but less accurate)
- `tolerance`: Convergence threshold (lower = more accurate but slower)
- `epsilon`: Privacy parameter (lower = more private but more noise)
- `method`: "PVP" (Primal Variable Perturbation) or "DVP" (Dual Variable Perturbation)

---

### Custom Network Configuration

Edit `edge_opf_simulator.py`, modify link specs:

```python
specs = LinkSpecs(
    bandwidth_mbps=1000.0,  # 1 Gbps link
    latency_ms=1.0,         # 1ms latency (LAN)
    packet_loss_rate=0.0    # No packet loss
)
```

**Scenarios to model:**
- LAN: High bandwidth (1000 Mbps), low latency (1ms)
- WAN: Medium bandwidth (100 Mbps), medium latency (50ms)
- Cellular: Low bandwidth (10 Mbps), high latency (100ms)

---

## Interpreting Results for Research

### Performance Metrics

**Speedup:**
```
Speedup = T_centralized / T_distributed
```

**Efficiency:**
```
Efficiency = Speedup / N_servers
```

**Energy Efficiency:**
```
Energy per Iteration = Total_Energy_Wh / Iterations
```

---

### Resource Utilization

**Average Resource Utilization:**
```
Utilization = (Used_Resources / Total_Resources) * 100
```

**Load Imbalance:**
```
Imbalance = (Max_Load - Min_Load) / Avg_Load
```

---

### Communication Overhead

**Communication-to-Computation Ratio:**
```
CCR = Network_Time / Computation_Time
```

**Network Efficiency:**
```
Net_Eff = Useful_Data / Total_Data_Transferred
```

---

## Common Issues and Solutions

### Issue 1: Julia Command Not Found

**Error:**
```
/bin/bash: julia: command not found
```

**Solution:**
```bash
# Install Julia
wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz
tar xvf julia-1.9.3-linux-x86_64.tar.gz
export PATH="$PWD/julia-1.9.3/bin:$PATH"
```

---

### Issue 2: Gurobi License Error

**Error:**
```
No Gurobi license found
```

**Solution:**
- Obtain academic/commercial Gurobi license
- Set `GRB_LICENSE_FILE` environment variable
- Or use free alternative solver (modify Julia scripts)

---

### Issue 3: Out of Memory

**Error:**
```
MemoryError: Unable to allocate array
```

**Solution:**
- Reduce `--servers` count
- Use `--sequential` flag
- Reduce `max_iterations`
- Use smaller test case

---

### Issue 4: Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'results/'
```

**Solution:**
```bash
chmod -R 755 edge/results edge/plots
```

---

## Performance Tuning Tips

### 1. Optimize for Speed
- Use `--parallel` (default)
- Increase `rho` parameter
- Relax `tolerance` (e.g., 1e-2 instead of 1e-4)
- Use fewer servers for smaller problems

### 2. Optimize for Accuracy
- Use `--sequential` to avoid race conditions
- Decrease `tolerance` (e.g., 1e-4)
- Increase `max_iterations`
- Use more servers for better load distribution

### 3. Optimize for Energy
- Use lower power servers (adjust `ServerSpecs`)
- Minimize iterations (tune `rho`)
- Reduce communication (increase `tolerance`)

---

## Reproducibility Checklist

For reproducible experiments:

✅ Record exact command used
✅ Save generated JSON files (contain full config)
✅ Note Julia version (`julia --version`)
✅ Note Python version (`python --version`)
✅ Record system specs (CPU, RAM)
✅ Use same test case file
✅ Set random seed (if needed)

---

## Integration with Existing Workflows

### Export to Pandas for Analysis

```python
import pandas as pd

# Load server stats
df_servers = pd.read_csv('results/distributed_3servers_*_servers.csv')

# Analyze
print(df_servers.describe())
print(df_servers.groupby('Server_ID')['Avg_CPU_%'].mean())
```

---

### Generate Custom Plots

```python
from visualization import ResultsExporter
import json

# Load results
with open('results/distributed_*_full.json') as f:
    results = json.load(f)

# Create custom exporter
exporter = ResultsExporter()

# Generate specific plots
exporter._plot_server_resources(
    results['simulation_stats']['servers'],
    'my_custom_plot.png'
)
```

---

## Citation

If you use this edge evaluation framework in your research, please cite:

```
[Original OPF Repository]
Distributed Optimal Power Flow with Differential Privacy
GitHub: [repository URL]
```

---

## Support

For questions or issues:
1. Check this guide first
2. Review `README.md`
3. Examine example output in `results/`
4. Open an issue on GitHub

---

**Last Updated:** 2025-11-01
