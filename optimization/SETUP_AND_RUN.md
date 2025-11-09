# Complete Setup and Run Guide

**Date:** 2025-11-09
**Purpose:** Step-by-step guide to set up and run Edge OPF evaluations

---

## Quick Start (3 Steps)

```bash
# Step 1: Verify setup
python verify_setup.py

# Step 2: Install Julia packages
julia install_julia_packages.jl

# Step 3: Run evaluation
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m
```

---

## Detailed Setup Guide

### Prerequisites

1. **Julia** (version 1.6 or higher)
   - Download: https://julialang.org/downloads/
   - Add to PATH

2. **Python** (version 3.7 or higher)
   - With packages: numpy, pandas, matplotlib

3. **Gurobi Optimizer**
   - Academic license (free): https://www.gurobi.com/academia/
   - Or commercial license

---

## Step-by-Step Setup

### Step 1: Verify Directory Structure

Make sure you're in the correct directory:

```bash
cd /path/to/DP_D_OPF/optimization
pwd  # Should show .../DP_D_OPF/optimization
```

Verify files exist:
```bash
ls -la
# Should see: edge/, testbeds/, evaluate_edge_opf.py, etc.
```

### Step 2: Run Pre-Flight Check

```bash
python verify_setup.py
```

This will check:
- ✓ Python dependencies
- ✓ Directory structure
- ✓ Test cases
- ✓ Julia installation
- ✓ Julia packages
- ✓ Julia scripts
- ✓ CLI script

**If checks fail:** Follow the fix instructions provided by the script.

### Step 3: Install Julia Packages

```bash
julia install_julia_packages.jl
```

This will:
1. Check which packages are already installed
2. Install missing packages
3. Test all imports
4. Verify Gurobi environment

**Expected output:**
```
================================================================================
Verification Results
================================================================================

✓ Success: 12 / 12

================================================================================
✓ ALL PACKAGES INSTALLED AND WORKING!
================================================================================
```

**If packages fail:**

For Primes (common issue):
```bash
julia -e 'using Pkg; Pkg.add("Primes")'
```

For Gurobi license issues:
```bash
# Get license from https://www.gurobi.com/academia/
# Download license file (gurobi.lic)
# Place in home directory or set GRB_LICENSE_FILE
```

### Step 4: Test Basic Execution

Run a quick centralized test:

```bash
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m --max-iter 100
```

**Expected output:**
```
[INIT] Adding edge module to Python path...
[INIT] Importing required modules...
[INIT]   ✓ EdgeOPFSimulator imported
[INIT]   ✓ JuliaOPFExecutor imported
[INIT]   ✓ ServerSpecs imported
[INIT]   ✓ ResultsExporter imported

================================================================================
EDGE OPF EVALUATION
================================================================================
Mode: CENTRALIZED
Case: testbeds/pglib_opf_case14_ieee.m
Max iterations: 100
================================================================================

✓ Configuration saved to: edge/results/config_centralized_YYYYMMDD_HHMMSS.json

[CENT] Step 1: Creating JuliaOPFExecutor...
[CENT]   ✓ JuliaOPFExecutor created
[CENT] Step 2: Running centralized OPF...
...
[CENT] ✓ Centralized OPF completed successfully

================================================================================
✓ EVALUATION COMPLETED SUCCESSFULLY
================================================================================

Results directory: edge/results
Plots directory: edge/plots
```

---

## Running All Modes

### 1. Centralized Mode (Fastest)

**No encryption, single node**

```bash
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m
```

**Typical runtime:** 30-60 seconds

**Output:**
- Results JSON in `edge/results/`
- Config file in `edge/results/`

---

### 2. Distributed Mode (Fast)

**No encryption, multiple edge servers**

```bash
python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m
```

**Typical runtime:** 60-120 seconds (parallel execution)

**Output:**
- Node results in `edge/results/`
- Comprehensive plots in `edge/plots/`
  - 33+ visualization plots
  - Dual time-axis views
  - Performance metrics
  - Resource utilization

**Advanced options:**
```bash
# Custom server specs
python evaluate_edge_opf.py --mode distributed \
  --servers 14 \
  --cpu-cores 8 \
  --memory 16.0 \
  --case testbeds/pglib_opf_case14_ieee.m

# Disable parallel execution
python evaluate_edge_opf.py --mode distributed \
  --servers 14 \
  --no-parallel \
  --case testbeds/pglib_opf_case14_ieee.m
```

---

### 3. Paillier Encryption (Slow)

**Homomorphic encryption, ~10x overhead**

```bash
python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m --max-iter 200
```

**Typical runtime:** 5-10 minutes (with 200 iterations)

**Important:**
- First run must install Primes package
- Reduce `--max-iter` for faster testing
- Monitor Julia output for progress

**Common error:**
```
ERROR: Package Primes not found
```

**Fix:**
```bash
julia -e 'using Pkg; Pkg.add("Primes")'
# Then re-run
```

---

### 4. BGV Encryption (Very Slow)

**Full homomorphic encryption, ~3000x overhead**

```bash
python evaluate_edge_opf.py --mode bgv --case testbeds/pglib_opf_case14_ieee.m --max-iter 50
```

**Typical runtime:** 30-60 minutes (with 50 iterations!)

**Recommended:**
- Start with very low `--max-iter` (10-20)
- Run on a powerful machine
- Be patient - this is VERY computationally intensive

---

### 5. CKKS Encryption (Very Slow)

**Full homomorphic encryption with floating point, ~3000x overhead**

```bash
python evaluate_edge_opf.py --mode ckks --case testbeds/pglib_opf_case14_ieee.m --max-iter 50
```

**Typical runtime:** 30-60 minutes (with 50 iterations!)

**Same recommendations as BGV**

---

## Understanding the Output

### Log Prefixes

| Prefix | Meaning |
|--------|---------|
| `[INIT]` | Initialization and module imports |
| `[CENT]` | Centralized mode execution |
| `[DIST]` | Distributed mode execution |
| `[ENC]` | Encrypted mode execution |
| `[VIZ]` | Visualization generation |

### Success Indicators

- `✓` = Step completed successfully
- `✗` = Error occurred
- `⚠️` = Warning (informational)

### Results Location

**All modes:**
- Configuration: `edge/results/config_MODE_TIMESTAMP.json`

**Distributed mode:**
- Node results: `edge/results/node_N_results.json`
- Plots: `edge/plots/*.png` (33+ plots)

**Encrypted modes:**
- Results: `results/SCHEME_results.json` (in optimization/)
- Timing data
- Convergence metrics

---

## Troubleshooting

### Problem 1: "Module not found" errors

**Symptoms:**
```
[INIT]   ✗ Failed to import EdgeOPFSimulator
```

**Fix:**
```bash
# Check you're in the right directory
cd /path/to/DP_D_OPF/optimization
pwd

# Verify edge directory exists
ls edge/edge_opf_simulator.py
```

---

### Problem 2: "Package Primes not found"

**Symptoms:**
```
ERROR: LoadError: ArgumentError: Package Primes not found
```

**Fix:**
```bash
# Install Primes package
julia -e 'using Pkg; Pkg.add("Primes")'

# Or install all packages
julia install_julia_packages.jl
```

---

### Problem 3: Distributed mode fails

**Symptoms:**
```
TypeError: setup_edge_infrastructure() got an unexpected keyword argument
```

**Fix:**
```bash
# Make sure you have the latest version
git pull origin claude/edge-device-evaluation-011CUi3Sxn7ZKMHFNPBXsfNE

# Verify the fix is applied
grep "ServerSpecs" evaluate_edge_opf.py
# Should see: from edgesimpy.edge_server import ServerSpecs
```

---

### Problem 4: Empty plots/results folders

**Symptoms:**
- Evaluation completes but no files in `edge/results/` or `edge/plots/`

**Possible causes:**
1. **Julia script crashed** - Check log output for Julia errors
2. **Missing packages** - Run `julia install_julia_packages.jl`
3. **Wrong directory** - Make sure you're in `optimization/`

**Fix:**
```bash
# Check for errors in logs
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m 2>&1 | tee debug.log

# Look for error messages
grep -E "ERROR|✗|Failed" debug.log

# Check if results were created
ls -la edge/results/
ls -la edge/plots/
```

---

### Problem 5: High optimality loss (>20%)

**Symptoms:**
```
[CENT]   Optimality loss: 32.9673%
[CENT]   ⚠️  High optimality loss detected (> 20%)
```

**This is NORMAL!**

Differential privacy adds noise for privacy, which reduces optimality.

**To reduce loss (less privacy):**
```bash
python evaluate_edge_opf.py --mode centralized \
  --case testbeds/pglib_opf_case14_ieee.m \
  --epsilon 10.0  # Default is 1.0, higher = less privacy, better accuracy
```

**To increase privacy (more loss):**
```bash
python evaluate_edge_opf.py --mode centralized \
  --case testbeds/pglib_opf_case14_ieee.m \
  --epsilon 0.1  # Lower = more privacy, worse accuracy
```

---

## Testing Checklist

Run this checklist to verify everything works:

```bash
# 1. Pre-flight check
python verify_setup.py
# Expected: ✓ ALL CHECKS PASSED

# 2. Install Julia packages
julia install_julia_packages.jl
# Expected: ✓ ALL PACKAGES INSTALLED AND WORKING!

# 3. Test centralized (quick, ~1 minute)
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m --max-iter 100
# Expected: ✓ EVALUATION COMPLETED SUCCESSFULLY

# 4. Check results were created
ls -la edge/results/
# Expected: Should see config_centralized_*.json

# 5. Test distributed (medium, ~2 minutes)
python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m --max-iter 100
# Expected: ✓ EVALUATION COMPLETED SUCCESSFULLY

# 6. Check plots were created
ls -la edge/plots/
# Expected: Should see 33+ .png files

# 7. Test Paillier (slow, ~5 minutes)
python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m --max-iter 50
# Expected: ✓ PAILLIER ENCRYPTION COMPLETED

# 8. Check Paillier results
ls -la results/paillier_results.json
# Expected: File exists with timing data
```

**If all 8 tests pass: ✓ SETUP COMPLETE!**

---

## Advanced Usage

### Save logs to file

```bash
python evaluate_edge_opf.py --mode centralized \
  --case testbeds/pglib_opf_case14_ieee.m \
  2>&1 | tee evaluation.log
```

### Run multiple test cases

```bash
for case in testbeds/*.m; do
    echo "Running $case..."
    python evaluate_edge_opf.py --mode centralized --case "$case" --max-iter 100
done
```

### Custom output directories

```bash
python evaluate_edge_opf.py --mode distributed \
  --servers 14 \
  --case testbeds/pglib_opf_case14_ieee.m \
  --output-dir my_results \
  --plots-dir my_plots
```

---

## Performance Expectations

| Mode | Overhead vs Baseline | Typical Runtime (case14, 1000 iter) |
|------|---------------------|--------------------------------------|
| Centralized | 1x (baseline) | 30-60 seconds |
| Distributed (14 servers) | 1-2x | 60-120 seconds (parallel) |
| Paillier | ~10x | 5-10 minutes |
| BGV | ~3000x | 30-60 minutes |
| CKKS | ~3000x | 30-60 minutes |

**Note:** Times are approximate and depend on:
- Hardware (CPU, cores, RAM)
- Test case size (case14 vs case300)
- Iteration count
- Privacy parameters

---

## Documentation Files

- `SETUP_AND_RUN.md` (this file) - Complete setup guide
- `USAGE_GUIDE.md` - Detailed CLI usage documentation
- `LOGGING_GUIDE.md` - Understanding log output
- `FIXES_APPLIED.md` - Bug fixes and solutions
- `JULIA_SETUP.md` - Julia package details
- `CLI_VERIFICATION_REPORT.md` - CLI testing report

---

## Getting Help

**If stuck:**

1. Check logging output for specific error messages
2. Review `LOGGING_GUIDE.md` for error explanations
3. Run `python verify_setup.py` to identify missing dependencies
4. Check `FIXES_APPLIED.md` for known issues
5. Review `USAGE_GUIDE.md` for CLI parameter details

**Common commands:**
```bash
# View comprehensive CLI help
python evaluate_edge_opf.py --help

# Check Julia packages
julia install_julia_packages.jl

# Verify setup
python verify_setup.py
```

---

**Last Updated:** 2025-11-09
**Version:** 1.0
**Status:** Ready for use ✓
