# Quick Start - 3 Commands to Get Results

## 🎯 You Have ONE Device? Perfect!

The framework **simulates multiple edge servers** on your single machine. No need for actual edge devices!

---

## 🚀 Getting Started (5 Minutes)

### Step 1: Install Dependencies

```bash
cd edge
pip install psutil numpy matplotlib
```

### Step 2: Check Everything is Ready

```bash
python quick_test.py
```

You should see:
```
✓ All Python dependencies found
✓ Julia found
✓ All framework modules loaded successfully
✓ Simulation ready with 3 edge servers
```

### Step 3: Run Your First Evaluation

```bash
python evaluate_edge_opf.py --mode comparison --servers 3
```

**Done!** Results are in `results/` and `plots/`

---

## 📊 View Your Results

```bash
# See what was generated
ls results/
ls plots/

# Open plots (if you have image viewer)
# Or copy to your local machine
```

---

## 🎮 Different Test Cases

### Quick Test (IEEE 14 bus - Default)
```bash
python evaluate_edge_opf.py --mode comparison --servers 3
# Time: ~5-10 minutes
```

### Medium Test (IEEE 30 bus)
```bash
python evaluate_edge_opf.py --mode comparison --servers 5 --case testbeds/pglib_opf_case30_ieee.m
# Time: ~10-15 minutes
```

### Large Test (IEEE 57 bus)
```bash
python evaluate_edge_opf.py --mode distributed --servers 7 --case testbeds/pglib_opf_case57_ieee.m
# Time: ~15-25 minutes
```

### Even Easier - Use the Helper Script

```bash
./run_case.sh 30 5        # IEEE 30 bus, 5 servers
./run_case.sh 57 7        # IEEE 57 bus, 7 servers
./run_case.sh 118 10      # IEEE 118 bus, 10 servers
```

---

## 💡 What Do The Numbers Mean?

### Servers
- Number of **simulated** edge devices on your one machine
- More servers = more distributed computation
- Recommended: 1 server per 5-10 buses

### Mode
- **comparison**: Runs both centralized and distributed (best for research)
- **distributed**: Only distributed OPF
- **centralized**: Only centralized OPF

---

## 📈 Understanding Your Results

After running, check:

### 1. Summary CSV
```bash
cat results/*summary.csv
```

Shows:
- Total execution time
- Number of servers used
- Success/failure rates

### 2. Server Resources CSV
```bash
cat results/*servers.csv
```

Shows per-server:
- CPU usage (average and peak)
- Memory usage
- Power consumption
- Energy used

### 3. Plots
```bash
ls plots/*.png
```

Visual results:
- `*_server_resources.png` - CPU, memory, power bars
- `*_node_performance.png` - Execution time comparison
- `*_resource_timeline.png` - CPU/memory over time
- `*_network_traffic.png` - Data transferred

---

## 🎯 Common Scenarios

### Scenario 1: "I want to test quickly"

```bash
python evaluate_edge_opf.py --mode centralized
# Fastest - just runs centralized OPF
# Time: ~2-3 minutes
```

### Scenario 2: "I want to compare approaches"

```bash
python evaluate_edge_opf.py --mode comparison --servers 3
# Runs both centralized and distributed
# Best for understanding trade-offs
# Time: ~8-12 minutes
```

### Scenario 3: "I want to test scalability"

```bash
# Run with different server counts
./run_case.sh 30 3
./run_case.sh 30 5
./run_case.sh 30 7
./run_case.sh 30 10

# Compare execution times
grep "Total_Duration" results/*case30*summary.csv
```

### Scenario 4: "I have limited RAM"

```bash
python evaluate_edge_opf.py --mode distributed --servers 3 --sequential
# Runs servers one at a time
# Uses less memory
# Takes longer
```

### Scenario 5: "I have a powerful machine"

```bash
python evaluate_edge_opf.py --mode distributed --servers 10 --case testbeds/pglib_opf_case118_ieee.m
# Larger case, more servers
# Parallel execution (default)
# Shows framework at scale
```

---

## 🐛 Troubleshooting

### Problem: "Julia not found"

**Quick Fix:**
```bash
# Check if Julia is installed
julia --version

# If not, install it:
# 1. Download from https://julialang.org/downloads/
# 2. Extract and add to PATH
export PATH="/path/to/julia/bin:$PATH"
```

### Problem: "Out of memory"

**Quick Fix:**
```bash
# Use sequential mode
python evaluate_edge_opf.py --mode distributed --servers 3 --sequential

# Or reduce servers
python evaluate_edge_opf.py --mode distributed --servers 2
```

### Problem: "Taking too long"

**Quick Fix:**
```bash
# Use smaller test case
python evaluate_edge_opf.py --case testbeds/pglib_opf_case5_pjm.m --servers 2

# Or reduce iterations
python evaluate_edge_opf.py --iterations 500
```

### Problem: "Module not found"

**Quick Fix:**
```bash
cd edge
pip install psutil numpy matplotlib
```

---

## 📚 Next Steps

Once you have results:

1. **Read the guides:**
   - `SINGLE_DEVICE_GUIDE.md` - Understand how simulation works
   - `RUN_WITH_DIFFERENT_CASES.md` - Try different IEEE cases
   - `USAGE_GUIDE.md` - Advanced features

2. **Analyze your CSV files:**
   - Import into Excel/Python/R
   - Compare server resources
   - Plot trends

3. **Customize:**
   - Edit `evaluate_edge_opf.py` to change server specs
   - Adjust OPF parameters
   - Modify network configuration

---

## 🎓 For IEEE 33 Bus (If You Have It)

If you have an IEEE 33 bus case file:

```bash
# 1. Copy to testbeds
cp /path/to/case33.m testbeds/pglib_opf_case33_ieee.m

# 2. Run evaluation
python evaluate_edge_opf.py --case testbeds/pglib_opf_case33_ieee.m --servers 5

# Or use the helper script
# Edit run_case.sh to add case 33, then:
./run_case.sh 33 5
```

---

## ✅ Checklist

Before running:
- [ ] Python 3.7+ installed
- [ ] `pip install psutil numpy matplotlib` done
- [ ] Julia installed and in PATH
- [ ] Julia packages installed (PowerModels, JuMP, Gurobi, etc.)
- [ ] In the `edge/` directory

First run:
- [ ] `python quick_test.py` succeeds
- [ ] `python evaluate_edge_opf.py --mode centralized` works
- [ ] Results appear in `results/` and `plots/`

---

## 🎯 TL;DR - Copy and Paste This

```bash
# Setup (once)
cd edge
pip install psutil numpy matplotlib
python quick_test.py

# Run evaluation
python evaluate_edge_opf.py --mode comparison --servers 3

# View results
ls results/*.csv
ls plots/*.png

# Try different cases
./run_case.sh 30 5    # IEEE 30 bus
./run_case.sh 57 7    # IEEE 57 bus
```

That's it! 🚀
