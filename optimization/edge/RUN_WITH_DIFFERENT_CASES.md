# Running with Different IEEE Test Cases

## 📋 Available Test Cases

Your repository has these test cases in `testbeds/`:

| Case | Buses | Generators | Lines | Complexity |
|------|-------|------------|-------|------------|
| case3_lmbd | 3 | - | - | Very Small |
| case5_pjm | 5 | - | - | Small |
| **case14_ieee** | 14 | - | - | **Default** |
| case24_ieee_rts | 24 | - | - | Medium |
| case30_as | 30 | - | - | Medium |
| case30_fsr | 30 | - | - | Medium |
| case30_ieee | 30 | - | - | Medium |
| case39_epri | 39 | - | - | Medium-Large |
| case57_ieee | 57 | - | - | Large |
| case118_ieee | 118 | - | - | Very Large |
| case200_tamu | 200 | - | - | Huge |
| case500_tamu | 500 | - | - | Massive |

## 🚀 Quick Commands

### Run with IEEE 30 Bus System

```bash
python evaluate_edge_opf.py \
    --mode comparison \
    --servers 5 \
    --case testbeds/pglib_opf_case30_ieee.m
```

### Run with IEEE 57 Bus System

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 7 \
    --case testbeds/pglib_opf_case57_ieee.m \
    --iterations 2000
```

### Run with IEEE 118 Bus System

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 10 \
    --case testbeds/pglib_opf_case118_ieee.m \
    --iterations 3000 \
    --sequential
```

### Run with Small System (Fast Testing)

```bash
python evaluate_edge_opf.py \
    --mode comparison \
    --servers 2 \
    --case testbeds/pglib_opf_case5_pjm.m
```

---

## 📊 Recommended Server Counts

Match the number of simulated edge servers to system size:

| Test Case | Recommended Servers | Reasoning |
|-----------|-------------------|-----------|
| case5 | 2-3 | Small system, minimal benefit from distribution |
| case14 | 3-5 | Default case, good for testing |
| case30 | 5-10 | Medium system, shows scalability |
| case57 | 7-15 | Large system, significant computational load |
| case118 | 10-20 | Very large, benefits from distribution |

**Rule of thumb:** Divide number of buses by 5-10 for server count

---

## 🎯 Complete Examples by Use Case

### Example 1: IEEE 30 Bus - Distributed on 5 Edge Servers

```bash
cd edge

python evaluate_edge_opf.py \
    --mode distributed \
    --servers 5 \
    --case testbeds/pglib_opf_case30_ieee.m \
    --iterations 1500
```

**What this does:**
- Simulates 5 edge devices on your single machine
- Each device handles a portion of the 30-bus system
- Runs ADMM distributed OPF
- Tracks CPU, memory, network, power for each simulated device
- Generates CSV + plots

**Expected runtime:** 10-15 minutes (parallel)

**Output files:**
```
results/distributed_5servers_*_case30_*.csv
plots/distributed_5servers_*_case30_*.png
```

---

### Example 2: IEEE 57 Bus - Comparison Study

```bash
python evaluate_edge_opf.py \
    --mode comparison \
    --servers 7 \
    --case testbeds/pglib_opf_case57_ieee.m \
    --iterations 2000
```

**What this does:**
1. Runs centralized OPF on case57 (single server)
2. Runs distributed OPF on case57 (7 servers)
3. Compares execution time, CPU, memory, energy
4. Generates comparison report

**Expected runtime:** 20-30 minutes

**Key metrics to compare:**
- Speedup: T_centralized / T_distributed
- Resource utilization per server
- Total energy consumption
- Convergence behavior

---

### Example 3: IEEE 118 Bus - Large Scale Sequential

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 10 \
    --case testbeds/pglib_opf_case118_ieee.m \
    --iterations 3000 \
    --sequential
```

**What this does:**
- Simulates 10 edge devices
- Runs them sequentially (safer for large system)
- Each node handles ~12 buses
- Detailed per-node metrics

**Expected runtime:** 40-60 minutes

**Use `--sequential` for:**
- Large test cases (>100 buses)
- Limited RAM (<16GB)
- Debugging
- Per-node analysis

---

### Example 4: Small Case for Quick Testing

```bash
python evaluate_edge_opf.py \
    --mode comparison \
    --servers 2 \
    --case testbeds/pglib_opf_case5_pjm.m \
    --iterations 500
```

**What this does:**
- Very fast test (~2-3 minutes)
- Verify framework works
- Check output format
- Debug issues

**Use for:**
- First-time setup verification
- Testing code changes
- Quick sanity checks

---

## 🔧 Adding IEEE 33 Bus Case (If You Have It)

If you have an IEEE 33 bus case file (e.g., `case33_bw.m`):

### Step 1: Add File to testbeds

```bash
cp /path/to/case33_bw.m testbeds/pglib_opf_case33_bw.m
```

### Step 2: Verify Format

The file should be in MATPOWER format (.m file). Check it can be loaded:

```bash
julia -e 'using PowerModels; parse_file("testbeds/pglib_opf_case33_bw.m")'
```

### Step 3: Run Evaluation

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 5 \
    --case testbeds/pglib_opf_case33_bw.m \
    --iterations 1500
```

---

## 🎛️ Tuning for Different Case Sizes

### Small Cases (5-14 buses)

```bash
python evaluate_edge_opf.py \
    --mode comparison \
    --servers 2 \
    --case testbeds/pglib_opf_case5_pjm.m \
    --iterations 500
```

**Settings:**
- Servers: 2-3
- Iterations: 500-1000
- Mode: comparison (to see if distribution helps)

---

### Medium Cases (30-57 buses)

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 7 \
    --case testbeds/pglib_opf_case57_ieee.m \
    --iterations 2000
```

**Settings:**
- Servers: 5-10
- Iterations: 1500-2000
- Mode: distributed or comparison

**Recommended adjustments in `evaluate_edge_opf.py`:**

```python
julia_config = JuliaConfig(
    max_iterations=2000,
    rho=5e3,           # Higher for faster convergence
    tolerance=1e-2,    # Can stay relaxed
    epsilon=1.0,
    method="PVP"
)
```

---

### Large Cases (118+ buses)

```bash
python evaluate_edge_opf.py \
    --mode distributed \
    --servers 15 \
    --case testbeds/pglib_opf_case118_ieee.m \
    --iterations 3000 \
    --sequential
```

**Settings:**
- Servers: 10-20
- Iterations: 3000-5000
- Mode: distributed only
- Use `--sequential` flag

**Recommended adjustments:**

```python
julia_config = JuliaConfig(
    max_iterations=5000,
    rho=1e4,           # Much higher for large cases
    tolerance=1e-1,    # Relax for initial tests
    epsilon=2.0,       # Less strict privacy for testing
    method="PVP"
)
```

---

## 📈 Performance Expectations

### Execution Time vs Case Size

| Case | Buses | Centralized | Distributed (5 servers) | Distributed (10 servers) |
|------|-------|-------------|------------------------|--------------------------|
| case5 | 5 | ~1 min | ~1 min | ~1 min |
| case14 | 14 | ~3 min | ~2 min | ~2 min |
| case30 | 30 | ~8 min | ~5 min | ~4 min |
| case57 | 57 | ~15 min | ~10 min | ~7 min |
| case118 | 118 | ~45 min | ~25 min | ~18 min |

*Times are approximate and depend on your hardware*

### Memory Requirements

| Case | Centralized | Distributed (per server) | Total (parallel) |
|------|-------------|-------------------------|------------------|
| case14 | ~2 GB | ~1 GB | ~3-5 GB |
| case30 | ~4 GB | ~1.5 GB | ~7-10 GB |
| case57 | ~8 GB | ~2 GB | ~12-16 GB |
| case118 | ~16 GB | ~3 GB | ~20-30 GB |

---

## 💡 Tips and Tricks

### Tip 1: Start Small, Scale Up

```bash
# First test
python evaluate_edge_opf.py --case testbeds/pglib_opf_case5_pjm.m --servers 2

# Then medium
python evaluate_edge_opf.py --case testbeds/pglib_opf_case30_ieee.m --servers 5

# Then large
python evaluate_edge_opf.py --case testbeds/pglib_opf_case57_ieee.m --servers 7
```

---

### Tip 2: Use Sequential for First Run

```bash
python evaluate_edge_opf.py \
    --case testbeds/pglib_opf_case30_ieee.m \
    --servers 5 \
    --sequential  # ← Easier to debug
```

---

### Tip 3: Adjust Iterations Based on Convergence

Monitor the Julia output. If residual drops quickly:

```bash
# Converges fast? Use fewer iterations
python evaluate_edge_opf.py --iterations 800

# Converges slow? Increase
python evaluate_edge_opf.py --iterations 3000
```

---

### Tip 4: Compare Multiple Configurations

Run multiple tests to see what works best:

```bash
# Test different server counts
for servers in 3 5 7 10; do
    python evaluate_edge_opf.py \
        --case testbeds/pglib_opf_case30_ieee.m \
        --servers $servers \
        --mode distributed
done

# Compare results
ls results/*case30*summary.csv
```

---

## 🔍 Analyzing Results for Different Cases

### Example: Compare case14 vs case30 vs case57

```bash
# Run all three
python evaluate_edge_opf.py --case testbeds/pglib_opf_case14_ieee.m --servers 3
python evaluate_edge_opf.py --case testbeds/pglib_opf_case30_ieee.m --servers 5
python evaluate_edge_opf.py --case testbeds/pglib_opf_case57_ieee.m --servers 7

# Check execution times
grep "Total_Duration" results/*summary.csv

# Check CPU usage
grep "Avg_CPU" results/*global_resources.csv

# Check memory
grep "Max_Memory" results/*global_resources.csv
```

---

## 📝 Complete Example Session with case30

```bash
$ cd edge

$ # Run distributed OPF on IEEE 30 bus system with 5 simulated edge servers
$ python evaluate_edge_opf.py \
    --mode distributed \
    --servers 5 \
    --case testbeds/pglib_opf_case30_ieee.m \
    --iterations 1500

================================================================================
DISTRIBUTED OPF EVALUATION ON EDGE DEVICES
================================================================================

Running distributed OPF with 5 edge servers...
Setting up edge infrastructure with 5 servers...
Created 5 edge servers and 20 network links

Executing nodes in parallel...
Executing Julia OPF for Node 1...
Executing Julia OPF for Node 2...
Executing Julia OPF for Node 3...
Executing Julia OPF for Node 4...
Executing Julia OPF for Node 5...

✓ Node 1 completed successfully
✓ Node 2 completed successfully
✓ Node 3 completed successfully
✓ Node 4 completed successfully
✓ Node 5 completed successfully

================================================================================
EXPORTING RESULTS
================================================================================

Exporting results to CSV (prefix: distributed_5servers_20251101_150234)...
  - Saved server stats to distributed_5servers_20251101_150234_servers.csv
  - Saved service stats to distributed_5servers_20251101_150234_services.csv
  - Saved link stats to distributed_5servers_20251101_150234_links.csv
  - Saved node execution results to distributed_5servers_20251101_150234_node_execution.csv
  - Saved global resources to distributed_5servers_20251101_150234_global_resources.csv
  - Saved summary to distributed_5servers_20251101_150234_summary.csv
✓ CSV export completed

Generating plots (prefix: distributed_5servers_20251101_150234)...
  - Saved server resources plot to distributed_5servers_20251101_150234_server_resources.png
  - Saved node performance plot to distributed_5servers_20251101_150234_node_performance.png
  - Saved resource timeline plot to distributed_5servers_20251101_150234_resource_timeline.png
  - Saved network traffic plot to distributed_5servers_20251101_150234_network_traffic.png
✓ Plot generation completed

================================================================================
EVALUATION SUMMARY
================================================================================
Simulation: Distributed_OPF_5_Servers
Execution mode: parallel
Number of edge servers: 5
Successful nodes: 5/5

Global Resource Usage:
  - Avg CPU: 62.3%
  - Max CPU: 94.7%
  - Avg Memory: 4523.8 MB
  - Max Memory: 6234.1 MB

✓ Evaluation completed successfully!

$ # View results
$ ls results/*case30*
results/distributed_5servers_20251101_150234_servers.csv
results/distributed_5servers_20251101_150234_services.csv
...

$ # View plots
$ ls plots/*case30*
plots/distributed_5servers_20251101_150234_server_resources.png
plots/distributed_5servers_20251101_150234_node_performance.png
...
```

---

## 🎯 Summary

**To run with ANY test case:**

```bash
python evaluate_edge_opf.py \
    --mode [distributed|centralized|comparison] \
    --servers [number] \
    --case testbeds/pglib_opf_case[SIZE]_[NAME].m \
    --iterations [number]
```

**Examples:**

```bash
# IEEE 30
python evaluate_edge_opf.py --case testbeds/pglib_opf_case30_ieee.m --servers 5

# IEEE 57
python evaluate_edge_opf.py --case testbeds/pglib_opf_case57_ieee.m --servers 7

# IEEE 118
python evaluate_edge_opf.py --case testbeds/pglib_opf_case118_ieee.m --servers 10 --sequential
```

**For IEEE 33 (if you have it):**
1. Add case file to `testbeds/`
2. Run with `--case testbeds/[your_file].m`

All outputs go to `results/` and `plots/` with timestamps!
