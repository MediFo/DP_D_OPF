# Running on a Single Device - Complete Guide

## 🎯 Overview

**You only need ONE physical device!** The framework **simulates** multiple edge servers on your single machine.

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR SINGLE PHYSICAL MACHINE                                │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  EdgeSimPy Simulator (Python)                       │    │
│  │                                                       │    │
│  │  Simulated Edge Server 1  ←─┐                       │    │
│  │    └─ Julia Process (OPF)    │ All running on       │    │
│  │                               │ your single          │    │
│  │  Simulated Edge Server 2  ←─┤ physical device      │    │
│  │    └─ Julia Process (OPF)    │                       │    │
│  │                               │                       │    │
│  │  Simulated Edge Server 3  ←─┘                       │    │
│  │    └─ Julia Process (OPF)                           │    │
│  │                                                       │    │
│  │  Resource Monitor: Tracks CPU, Memory, Network      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Results: CSV files + Plots                                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start (5 Minutes)

### 1. Check Dependencies

```bash
cd edge
python quick_test.py
```

This will check if everything is ready.

### 2. Install Python Dependencies (if needed)

```bash
pip install psutil numpy matplotlib
```

### 3. Run Your First Simulation

**Option A: Sequential (Recommended for First Test)**

Runs OPF computations one after another on your device:

```bash
python evaluate_edge_opf.py --mode distributed --servers 3 --sequential
```

**What happens:**
- Simulates 3 edge servers
- Runs OPF computation on Server 1 → monitors resources
- Runs OPF computation on Server 2 → monitors resources
- Runs OPF computation on Server 3 → monitors resources
- Generates CSV files and plots

**Time:** ~5-10 minutes (depends on convergence)

---

**Option B: Parallel (Simulates Concurrent Execution)**

Runs multiple Julia processes at once:

```bash
python evaluate_edge_opf.py --mode distributed --servers 3
```

**What happens:**
- Simulates 3 edge servers
- Spawns 3 Julia processes running in parallel
- Each process runs OPF for one node
- Monitors aggregate resource usage
- Simulates network communication

**Time:** Faster than sequential (~3-5 minutes)

---

**Option C: Comparison Mode (Best for Research)**

Runs both centralized and distributed:

```bash
python evaluate_edge_opf.py --mode comparison --servers 3
```

**What happens:**
1. Runs centralized OPF on single simulated server
2. Runs distributed OPF on 3 simulated servers
3. Compares performance
4. Generates comparison reports

**Time:** ~10-15 minutes

---

## 📊 What Gets Simulated

### Physical Reality (What You Have)
- 1 laptop/desktop/server
- 1 CPU
- 1 memory system
- 1 network interface

### Simulation (What The Framework Creates)
- Multiple **logical** edge servers
- Each with **simulated** CPU allocation
- Each with **simulated** memory allocation
- **Simulated** network links between servers
- **Simulated** power consumption

### What Gets Actually Measured
- **Real CPU usage** from your physical machine
- **Real memory usage** from your physical machine
- **Real execution time** for OPF computations
- **Estimated power** based on CPU usage
- **Simulated network** traffic (not real packets)

---

## 🎮 Execution Modes Explained

### Sequential Mode (`--sequential`)

```
Time →

Server 1: [========OPF========]
Server 2:                      [========OPF========]
Server 3:                                           [========OPF========]

Your CPU: [████████████████████████████████████████████████████████████]
          ↑                    ↑                    ↑
          Server 1 active      Server 2 active      Server 3 active
```

**Pros:**
- Easier to debug
- Lower memory usage
- Clearer per-server metrics
- More realistic for resource-constrained devices

**Cons:**
- Takes longer
- Doesn't test parallel performance

**Use when:**
- First time testing
- Debugging issues
- Limited RAM (<8GB)

---

### Parallel Mode (default)

```
Time →

Server 1: [========OPF========]
Server 2: [========OPF========]
Server 3: [========OPF========]

Your CPU: [████████████████████]
          ↑
          All servers active simultaneously
```

**Pros:**
- Faster execution
- Tests parallel performance
- Simulates real distributed scenario
- Shows aggregate resource usage

**Cons:**
- Higher memory usage
- May overwhelm single machine
- Harder to debug

**Use when:**
- You have sufficient RAM (>8GB)
- Testing scalability
- Simulating real deployment

---

## 📈 Understanding Your Results

### Example Output

After running, you'll see files like:

```
results/
├── distributed_3servers_20251101_143022_servers.csv
├── distributed_3servers_20251101_143022_services.csv
├── distributed_3servers_20251101_143022_node_execution.csv
└── distributed_3servers_20251101_143022_summary.csv

plots/
├── distributed_3servers_20251101_143022_server_resources.png
├── distributed_3servers_20251101_143022_node_performance.png
└── distributed_3servers_20251101_143022_resource_timeline.png
```

### What The Numbers Mean

**Example from `servers.csv`:**

| Server_ID | Avg_CPU_% | Max_CPU_% | Avg_Memory_MB | Max_Memory_MB |
|-----------|-----------|-----------|---------------|---------------|
| 1         | 85.3      | 98.7      | 1024.5        | 1356.2        |
| 2         | 82.1      | 95.4      | 1018.3        | 1342.8        |
| 3         | 84.7      | 97.2      | 1021.9        | 1349.5        |

**Interpretation:**
- Each "server" represents a simulated edge device
- CPU% shows how much of YOUR machine's CPU was used
- Memory_MB shows actual RAM consumed on YOUR machine
- These are measured values from real execution

**Example from `node_execution.csv`:**

| Node_ID | Execution_Time_s | Iterations | Avg_Iteration_Time_ms |
|---------|------------------|------------|-----------------------|
| 1       | 28.34           | 342        | 82.8                  |
| 2       | 29.12           | 356        | 81.8                  |
| 3       | 27.89           | 338        | 82.5                  |

**Interpretation:**
- Shows how long each OPF computation took
- Number of ADMM iterations to converge
- Average time per iteration

---

## 🔧 Adjusting For Your Device

### If You Have Limited Resources

**Reduce number of servers:**
```bash
python evaluate_edge_opf.py --mode distributed --servers 2 --sequential
```

**Reduce iterations:**
```bash
python evaluate_edge_opf.py --mode distributed --servers 3 --iterations 500
```

**Use smaller test case:**
Edit `evaluate_edge_opf.py` and change:
```python
case_id = "testbeds/pglib_opf_case5_pjm.m"  # Smaller system
```

---

### If You Have Powerful Hardware

**Increase servers:**
```bash
python evaluate_edge_opf.py --mode distributed --servers 10
```

**Tighter tolerance:**
```bash
# Edit evaluate_edge_opf.py
julia_config = JuliaConfig(
    tolerance=1e-4  # Stricter convergence
)
```

**Larger test case:**
```bash
python evaluate_edge_opf.py --case testbeds/pglib_opf_case30_ieee.m --servers 5
```

---

## 💡 Common Scenarios

### Scenario 1: Testing Algorithm Convergence

**Goal:** See how many iterations ADMM needs

```bash
python evaluate_edge_opf.py --mode distributed --servers 3 --iterations 5000
```

**Look at:** `node_execution.csv` → `Iterations` column

---

### Scenario 2: Resource Requirements

**Goal:** Understand CPU/memory needs for deployment

```bash
python evaluate_edge_opf.py --mode distributed --servers 5 --sequential
```

**Look at:** `servers.csv` → `Avg_CPU_%`, `Max_Memory_MB`

---

### Scenario 3: Centralized vs Distributed Comparison

**Goal:** Compare performance approaches

```bash
python evaluate_edge_opf.py --mode comparison --servers 4
```

**Look at:** `comparison_*.json` → Check execution times

---

### Scenario 4: Scalability Testing

**Goal:** How does it scale with more nodes?

```bash
for n in 2 3 4 5 6; do
    python evaluate_edge_opf.py --mode distributed --servers $n --sequential
done
```

**Look at:** Compare execution times across different server counts

---

## 🐛 Troubleshooting

### Problem: "Julia not found"

**Solution:**
```bash
# Install Julia
wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz
tar xvf julia-1.9.3-linux-x86_64.tar.gz
export PATH="$PWD/julia-1.9.3/bin:$PATH"

# Verify
julia --version
```

---

### Problem: "Out of Memory"

**Solutions:**
1. Use sequential mode: `--sequential`
2. Reduce servers: `--servers 2`
3. Close other applications
4. Use swap space

---

### Problem: "Gurobi license error"

**Solutions:**
1. Get free academic license: https://www.gurobi.com/academia/
2. Or modify Julia scripts to use free solver (e.g., GLPK)

---

### Problem: "No module named 'psutil'"

**Solution:**
```bash
pip install psutil numpy matplotlib
```

---

### Problem: "Takes too long"

**Solutions:**
1. Relax tolerance (faster convergence):
   ```python
   # In evaluate_edge_opf.py
   tolerance=1e-2  # Instead of 1e-4
   ```

2. Reduce max iterations:
   ```bash
   python evaluate_edge_opf.py --iterations 500
   ```

3. Use parallel mode (default)

---

## 📝 Example Session

Here's what a typical session looks like:

```bash
$ cd edge

$ python quick_test.py
================================================================================
EDGE OPF EVALUATION - QUICK TEST
Simulating multiple edge devices on YOUR single machine
================================================================================

Step 1: Checking Python dependencies...
✓ All Python dependencies found

Step 2: Checking Julia installation...
✓ Julia found: julia version 1.9.3

Step 3: Testing framework components...
✓ All framework modules loaded successfully

Step 4: Creating test simulation...
Creating 3 simulated edge servers...
  ✓ EdgeServer_1 created (simulated)
  ✓ EdgeServer_2 created (simulated)
  ✓ EdgeServer_3 created (simulated)

✓ Simulation ready with 3 edge servers

================================================================================
READY TO RUN!
================================================================================

$ python evaluate_edge_opf.py --mode comparison --servers 3

================================================================================
COMPARATIVE EVALUATION: DISTRIBUTED vs CENTRALIZED OPF
================================================================================

>>> Phase 1: Centralized OPF
Running centralized OPF on single edge server...
✓ Centralized OPF completed successfully

>>> Phase 2: Distributed OPF
Running distributed OPF with 3 edge servers...
Executing nodes in parallel...
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

✓ Evaluation completed successfully!

$ ls results/
comparison_20251101_143022.json
centralized_20251101_142955_full.json
distributed_3servers_20251101_143022_full.json
...

$ ls plots/
distributed_3servers_20251101_143022_server_resources.png
distributed_3servers_20251101_143022_node_performance.png
...
```

---

## 🎯 Summary

**Key Points:**
- ✅ You only need ONE physical device
- ✅ The framework SIMULATES multiple edge servers
- ✅ All computations run on YOUR machine
- ✅ Metrics are REAL (CPU, memory) from actual execution
- ✅ Network is SIMULATED (no actual packets sent)
- ✅ Results show what WOULD happen on multiple devices

**Start with:**
```bash
python evaluate_edge_opf.py --mode comparison --servers 3
```

**Then explore the CSV and PNG files to understand performance!**

---

## 🔗 Need More Help?

- Check `README.md` for technical details
- Check `USAGE_GUIDE.md` for advanced examples
- Run `python quick_test.py` to verify setup
