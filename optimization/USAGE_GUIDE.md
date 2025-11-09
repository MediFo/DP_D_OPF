# Complete Usage Guide - Running OPF in Different Modes

This guide shows you **exactly** how to run OPF simulations in all different modes: centralized, distributed, and encrypted (Paillier, BGV, CKKS).

---

## Quick Start

### Prerequisites

```bash
cd /home/user/DP_D_OPF/optimization
```

Make sure you have:
- ✅ Python 3.x installed
- ✅ Julia installed (for running OPF computations)
- ✅ Required Python packages: numpy, matplotlib, psutil

---

## 📋 Available Modes

| Mode | Description | Overhead | Use Case |
|------|-------------|----------|----------|
| **centralized** | Single node, no encryption | Baseline | Fast, non-private |
| **distributed** | Multiple edge servers, no encryption | ~1x | Edge computing simulation |
| **paillier** | Paillier homomorphic encryption | ~10x | Privacy-preserving (practical) |
| **bgv** | BGV/BFV full homomorphic encryption | ~3000x | Maximum privacy (slow) |
| **ckks** | CKKS full homomorphic encryption | ~3000x | Maximum privacy (slow) |

---

## 1️⃣ Centralized Mode (Non-Encrypted)

Run OPF on a single node without encryption - **fastest mode**.

### Basic Usage

```bash
python evaluate_edge_opf.py \
  --mode centralized \
  --case testbeds/pglib_opf_case14_ieee.m
```

### With Custom Parameters

```bash
python evaluate_edge_opf.py \
  --mode centralized \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 2000 \
  --rho 1000.0 \
  --tolerance 0.01 \
  --privacy-method PVP
```

### Expected Output

```
================================================================================
EDGE OPF EVALUATION
================================================================================
Mode: CENTRALIZED
Case: testbeds/pglib_opf_case14_ieee.m
Max iterations: 1000
================================================================================

✓ Centralized OPF completed successfully
  Execution time: 5.23s
  Iterations: 145
  Final cost: $8081.53
  Optimality loss: 0.0234%
```

---

## 2️⃣ Distributed Mode (Edge Computing)

Run OPF distributed across multiple edge servers - **realistic edge scenario**.

### Basic Usage (14 Servers)

```bash
python evaluate_edge_opf.py \
  --mode distributed \
  --servers 14 \
  --case testbeds/pglib_opf_case14_ieee.m
```

### With Custom Infrastructure

```bash
python evaluate_edge_opf.py \
  --mode distributed \
  --servers 14 \
  --case testbeds/pglib_opf_case14_ieee.m \
  --cpu-cores 4 \
  --cpu-freq 2.4 \
  --memory 8.0 \
  --bandwidth 100.0 \
  --latency 10.0
```

### Large-Scale Deployment (30 Servers)

```bash
python evaluate_edge_opf.py \
  --mode distributed \
  --servers 30 \
  --case testbeds/pglib_opf_case30_ieee.m \
  --cpu-cores 8 \
  --memory 16.0 \
  --bandwidth 1000.0
```

### Expected Output

```
================================================================================
RUNNING DISTRIBUTED OPF ON EDGE INFRASTRUCTURE
================================================================================

✓ Distributed simulation completed
  Total nodes: 14

✓ Plots saved to: edge/plots
  Generated 35 plots including dual time-axis visualizations
```

---

## 3️⃣ Paillier Encryption Mode

Run OPF with **Paillier homomorphic encryption** - practical privacy (~10x overhead).

### Basic Usage

```bash
python evaluate_edge_opf.py \
  --mode paillier \
  --case testbeds/pglib_opf_case14_ieee.m
```

### With Custom Iterations

```bash
python evaluate_edge_opf.py \
  --mode paillier \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 1000 \
  --rho 10.0 \
  --tolerance 0.01
```

### Expected Output

```
================================================================================
RUNNING PAILLIER ENCRYPTED OPF
================================================================================

⚠️  Note: PAILLIER encryption adds significant overhead
⚠️  Expected overhead: ~10x slower than non-encrypted

Running Julia script: opt_main_verified.jl
--------------------------------------------------------------------------------

[1/6] Loading PowerModels and setting up Gurobi...
[2/6] Loading power grid: testbeds/pglib_opf_case14_ieee.m
[3/6] Generating Paillier keypair...
  ✓ Keys generated in 2.34s
[5/6] Initializing ADMM parameters...
[6/6] Running ADMM with Paillier encryption...

================================================================================
✓ PAILLIER ENCRYPTION COMPLETED
================================================================================
  Total time: 145.67s
  Iterations: 234
  Final cost: $8081.53
  Optimality loss: 0.0001%
  Converged: true

  Timing breakdown:
    Optimization: 45.2%
    Cryptography: 48.3%
    Other: 6.5%

📊 Results saved to: results/paillier_results.json
```

---

## 4️⃣ BGV Encryption Mode

Run OPF with **BGV/BFV full homomorphic encryption** - maximum privacy (~3000x overhead).

### ⚠️ WARNING: VERY SLOW!

BGV is **approximately 3000x slower** than non-encrypted mode. Use **reduced iterations** for testing.

### Basic Usage (Reduced Iterations)

```bash
python evaluate_edge_opf.py \
  --mode bgv \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 100
```

### Expected Output

```
================================================================================
RUNNING BGV ENCRYPTED OPF
================================================================================

⚠️  Note: BGV encryption adds significant overhead
⚠️  Expected overhead: ~300x slower than Paillier (~3000x vs non-encrypted)

Running Julia script: opt_main_bgv.jl
--------------------------------------------------------------------------------

[1/6] Loading PowerModels and setting up Gurobi...
[2/6] Loading power grid: testbeds/pglib_opf_case14_ieee.m
[3/6] Setting up BGV/BFV encryption...
  ⏱  Using 100 iterations (may take ~30x longer than Paillier)
  ⚠️  WARNING: Each iteration will be ~30x slower than Paillier!
[6/6] Running ADMM with BGV encryption...

================================================================================
✓ BGV ENCRYPTION COMPLETED
================================================================================
  Total time: 3245.12s  (~ 54 minutes)
  Iterations: 100
  Final cost: $8082.45
  Converged: false

📊 Results saved to: results/bgv_results.json
```

---

## 5️⃣ CKKS Encryption Mode

Run OPF with **CKKS full homomorphic encryption** - maximum privacy for real numbers (~3000x overhead).

### ⚠️ WARNING: VERY SLOW!

CKKS is **approximately 3000x slower** than non-encrypted mode. Use **reduced iterations** for testing.

### Basic Usage (Reduced Iterations)

```bash
python evaluate_edge_opf.py \
  --mode ckks \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 100
```

### Expected Output

```
================================================================================
RUNNING CKKS ENCRYPTED OPF
================================================================================

⚠️  Note: CKKS encryption adds significant overhead
⚠️  Expected overhead: ~300x slower than Paillier (~3000x vs non-encrypted)

Running Julia script: opt_main_ckks.jl
--------------------------------------------------------------------------------

[Similar output to BGV...]

📊 Results saved to: results/ckks_results.json
```

---

## 📊 Comparison Mode

Run **all modes** for comparison (be prepared - this will take a long time!):

```bash
# Centralized (baseline)
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m

# Distributed (14 servers)
python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m

# Paillier (~10x overhead)
python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m

# BGV (very slow! ~3000x overhead)
python evaluate_edge_opf.py --mode bgv --case testbeds/pglib_opf_case14_ieee.m --max-iter 50

# CKKS (very slow! ~3000x overhead)
python evaluate_edge_opf.py --mode ckks --case testbeds/pglib_opf_case14_ieee.m --max-iter 50
```

---

## 🎛️ Complete Parameter Reference

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--mode` | Execution mode | `centralized`, `distributed`, `paillier`, `bgv`, `ckks` |
| `--case` | Power grid test case | `testbeds/pglib_opf_case14_ieee.m` |

### Edge Infrastructure (Distributed Mode)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--servers` | 3 | Number of edge servers |
| `--cpu-cores` | 4 | CPU cores per server |
| `--cpu-freq` | 2.4 | CPU frequency (GHz) |
| `--memory` | 8.0 | Memory per server (GB) |
| `--storage` | 100.0 | Storage per server (GB) |
| `--power-idle` | 50.0 | Idle power consumption (W) |
| `--power-max` | 150.0 | Max power consumption (W) |

### Network Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--bandwidth` | 100.0 | Network bandwidth (Mbps) |
| `--latency` | 10.0 | Network latency (ms) |
| `--packet-loss` | 0.001 | Packet loss rate |

### OPF Algorithm Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max-iter` | 1000 | Maximum ADMM iterations |
| `--rho` | 1000.0 | ADMM penalty parameter |
| `--tolerance` | 0.01 | Convergence tolerance |
| `--epsilon` | 1.0 | Differential privacy ε |
| `--alpha` | 0.1 | Differential privacy α |
| `--privacy-method` | PVP | Privacy method (PVP or DVP) |

### Execution Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--parallel` | True | Run in parallel (distributed) |
| `--no-parallel` | - | Disable parallel execution |
| `--generate-plots` | True | Generate visualization plots |
| `--no-plots` | - | Skip plot generation |
| `--export-csv` | True | Export results to CSV |
| `--no-csv` | - | Skip CSV export |

### Output Directories

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--output-dir` | edge/results | Results output directory |
| `--plots-dir` | edge/plots | Plots output directory |

---

## 📁 Output Files

After running, you'll find results in:

### For Distributed Mode

```
edge/
├── results/
│   ├── config_distributed_YYYYMMDD_HHMMSS.json  # Configuration used
│   ├── simulation_results_YYYYMMDD_HHMMSS.json  # Full results
│   └── node_*.json                               # Per-node results
└── plots/
    ├── distributed_*.png                         # 35 visualization plots
    ├── distributed_dual_cpu_memory_percentile_*.png  # Dual time-axis plots
    └── ...
```

### For Encrypted Modes (Paillier, BGV, CKKS)

```
results/
├── paillier_results.json                         # Paillier results
├── bgv_results.json                              # BGV results
└── ckks_results.json                             # CKKS results
```

Each JSON file contains:
- `iteration_times` - Duration of each iteration (seconds)
- `iteration_timestamps` - Cumulative time from start (seconds)
- `residuals` - Convergence residuals per iteration
- `cost_history` - Cost value per iteration
- Timing breakdown (for encrypted modes)

---

## 🔍 Available Test Cases

The system includes various IEEE test cases:

```bash
# Small (14 buses)
testbeds/pglib_opf_case14_ieee.m

# Medium (30 buses)
testbeds/pglib_opf_case30_ieee.m

# Large (57 buses)
testbeds/pglib_opf_case57_ieee.m

# Very Large (118 buses)
testbeds/pglib_opf_case118_ieee.m
```

List all available cases:
```bash
ls -1 testbeds/*.m
```

---

## ⚡ Performance Expectations

### Time Estimates (14-bus system, 1000 iterations)

| Mode | Approximate Time | Notes |
|------|------------------|-------|
| **Centralized** | 5-10 seconds | Baseline performance |
| **Distributed (14 servers)** | 10-20 seconds | Slight overhead from distribution |
| **Paillier** | 50-100 seconds | ~10x slower, practical |
| **BGV** (100 iter) | 30-60 minutes | ~3000x slower, use sparingly |
| **CKKS** (100 iter) | 30-60 minutes | ~3000x slower, use sparingly |

### Memory Usage

| Mode | RAM Usage | Notes |
|------|-----------|-------|
| **Centralized** | ~500 MB | Minimal |
| **Distributed** | ~2-4 GB | Depends on servers |
| **Paillier** | ~1-2 GB | Encryption keys |
| **BGV** | ~4-8 GB | Large keys |
| **CKKS** | ~4-8 GB | Large keys |

---

## 🐛 Troubleshooting

### Error: "Julia not found"

```bash
# Install Julia from https://julialang.org/downloads/
# Or check if it's in PATH:
which julia
```

### Error: "Case file not found"

```bash
# Make sure you're in the optimization directory:
cd /home/user/DP_D_OPF/optimization

# List available cases:
ls testbeds/*.m
```

### Error: "Gurobi not available"

The scripts use Gurobi solver. Make sure:
1. Gurobi is installed
2. Julia packages are installed: `PowerModels`, `Gurobi`, `JuMP`

```bash
julia -e 'using Pkg; Pkg.add(["PowerModels", "Gurobi", "JuMP"])'
```

### Slow Performance in Encrypted Modes

This is **expected**! Encryption adds significant overhead:
- **Paillier**: ~10x slower (practical)
- **BGV/CKKS**: ~3000x slower (use reduced iterations)

Use `--max-iter 50` or `--max-iter 100` for testing encrypted modes.

---

## 📖 Examples Library

### Example 1: Quick Test (Centralized)

```bash
python evaluate_edge_opf.py \
  --mode centralized \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 500
```

### Example 2: Edge Deployment (Small)

```bash
python evaluate_edge_opf.py \
  --mode distributed \
  --servers 14 \
  --case testbeds/pglib_opf_case14_ieee.m \
  --cpu-cores 4 \
  --memory 8.0
```

### Example 3: Edge Deployment (Large)

```bash
python evaluate_edge_opf.py \
  --mode distributed \
  --servers 30 \
  --case testbeds/pglib_opf_case30_ieee.m \
  --cpu-cores 8 \
  --memory 16.0 \
  --bandwidth 1000.0
```

### Example 4: Privacy-Preserving (Paillier)

```bash
python evaluate_edge_opf.py \
  --mode paillier \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 1000
```

### Example 5: Maximum Privacy (BGV - Testing)

```bash
python evaluate_edge_opf.py \
  --mode bgv \
  --case testbeds/pglib_opf_case14_ieee.m \
  --max-iter 50 \
  --no-plots
```

### Example 6: No Plots, CSV Only

```bash
python evaluate_edge_opf.py \
  --mode distributed \
  --servers 14 \
  --case testbeds/pglib_opf_case14_ieee.m \
  --no-plots \
  --export-csv
```

---

## 🎯 Recommended Workflow

### 1. Start with Centralized (Baseline)

```bash
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m
```

### 2. Test Distributed

```bash
python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m
```

### 3. Add Privacy (Paillier)

```bash
python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m
```

### 4. (Optional) Test FHE with Reduced Iterations

```bash
# Only if you have time! Very slow.
python evaluate_edge_opf.py --mode bgv --case testbeds/pglib_opf_case14_ieee.m --max-iter 20
```

---

## 💡 Tips

1. **Start small**: Test with 14-bus case before moving to larger cases
2. **Reduce iterations for encrypted modes**: Use `--max-iter 50-100` for BGV/CKKS
3. **Skip plots for quick tests**: Use `--no-plots` to speed up execution
4. **Monitor progress**: Scripts print progress during execution
5. **Check results**: JSON files contain detailed timing and convergence data

---

## 📚 Additional Resources

- **VERIFICATION_REPORT.md** - Complete verification of all functionality
- **TIMESTAMP_RECORDING.md** - Technical details on timing implementation
- **QUICK_REFERENCE.md** - Quick reference guide
- **test_visualization_mock.py** - Test plots with mock data
- **verify_all_scripts.py** - Verify all scripts are working

---

**Created:** 2025-11-09
**Version:** 1.0
**Status:** Production Ready ✅
