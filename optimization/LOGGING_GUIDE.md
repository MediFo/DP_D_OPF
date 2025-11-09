# Logging Guide - Understanding CLI Output

**Date:** 2025-11-09
**File:** `evaluate_edge_opf.py`

---

## Overview

The CLI interface includes comprehensive step-by-step logging to help you understand exactly what's happening during execution and quickly identify any problems.

---

## Log Prefixes

All log messages use prefixes to indicate which part of the code is executing:

| Prefix | Component | Description |
|--------|-----------|-------------|
| **[INIT]** | Initialization | Module imports and setup |
| **[CENT]** | Centralized Mode | Single-node OPF execution |
| **[DIST]** | Distributed Mode | Multi-node edge simulation |
| **[ENC]** | Encrypted Mode | Paillier/BGV/CKKS execution |
| **[VIZ]** | Visualization | Plot generation |

---

## Log Symbols

| Symbol | Meaning |
|--------|---------|
| **✓** | Success - step completed without errors |
| **✗** | Error - step failed |
| **⚠️** | Warning - informational, not an error |

---

## Initialization Phase [INIT]

**What happens:**
- Python modules are imported
- Edge simulation infrastructure is loaded
- Julia wrapper is initialized

**Example output:**
```
[INIT] Adding edge module to Python path...
[INIT] Importing required modules...
[INIT]   ✓ EdgeOPFSimulator imported
[INIT]   ✓ JuliaOPFExecutor imported
[INIT]   ✓ ResultsExporter imported
```

**Common errors:**

### Error: Module not found
```
[INIT]   ✗ Failed to import EdgeOPFSimulator: No module named 'edge_opf_simulator'
[INIT]   Check that edge/edge_opf_simulator.py exists
```

**Solution:** Make sure you're running from the `optimization/` directory:
```bash
cd /home/user/DP_D_OPF/optimization
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m
```

---

## Centralized Mode [CENT]

**What happens:**
1. JuliaOPFExecutor is created
2. Julia script runs centralized OPF
3. Results are collected and displayed

**Example output:**
```
[CENT] Step 1: Creating JuliaOPFExecutor...
[CENT]   ✓ JuliaOPFExecutor created
[CENT] Step 2: Running centralized OPF...
[CENT]   Case: testbeds/pglib_opf_case14_ieee.m
[CENT]   Max iterations: 1000
[CENT]   Privacy method: PVP
[CENT]   Epsilon: 1.0

[CENT] ✓ Centralized OPF completed successfully
[CENT]   Execution time: 32.45s
[CENT]   Iterations: 897
[CENT]   Final cost: $8081.53
[CENT]   Optimality loss: 32.9673%
```

**Understanding high optimality loss:**

If you see:
```
[CENT]   ⚠️  High optimality loss detected (> 20%)
[CENT]   This is expected with differential privacy
[CENT]   To reduce: increase --epsilon (less privacy) or decrease --alpha
```

**This is NORMAL!** Differential privacy adds noise to protect privacy, which reduces optimality. Adjust parameters:

```bash
# More accuracy, less privacy
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m --epsilon 10.0

# More privacy, less accuracy
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m --epsilon 0.1
```

---

## Distributed Mode [DIST]

**What happens:**
1. EdgeOPFSimulator is created
2. Edge infrastructure (servers, network) is configured
3. Julia configuration is prepared
4. Distributed OPF runs across multiple nodes
5. Results are aggregated

**Example output:**
```
[DIST] Step 1: Creating EdgeOPFSimulator...
[DIST]   Simulation name: Distributed_OPF_Edge_Simulation
[DIST]   ✓ EdgeOPFSimulator created successfully

[DIST] Step 2: Setting up edge infrastructure...
[DIST]   Number of servers: 14
[DIST]   Server specs: 4 cores, 8.0 GB RAM
[DIST]   Network: 100.0 Mbps, 10.0 ms latency
[DIST]   ✓ Edge infrastructure configured

[DIST] Step 3: Setting up Julia OPF configuration...
[DIST]   Case: testbeds/pglib_opf_case14_ieee.m
[DIST]   Max iterations: 1000
[DIST]   Privacy method: PVP
[DIST]   ✓ Julia configuration created

[DIST] Step 4: Running distributed OPF computation...
[DIST]   Parallel execution: True
[DIST]   ✓ Distributed OPF computation completed
[DIST]   Total nodes processed: 14

✓ Distributed simulation completed successfully
```

**Common errors:**

### Error: AttributeError - 'run' method
```
[DIST] ✗ Attribute error: 'EdgeOPFSimulator' object has no attribute 'run'
[DIST]   This might indicate an API mismatch
[DIST]   Check that EdgeOPFSimulator has the expected methods
```

**Solution:** This error was fixed in the latest version. Update your code:
```bash
git pull origin claude/edge-device-evaluation-011CUi3Sxn7ZKMHFNPBXsfNE
```

### Error: Configuration missing
```
[DIST] ✗ Configuration error: Missing key 'edge_infrastructure'
[DIST]   Check your configuration has all required fields
```

**Solution:** This is an internal error. Report it if you encounter it.

---

## Encrypted Mode [ENC]

**What happens:**
1. Julia environment is prepared
2. Script existence is verified (opt_main_verified.jl, opt_main_bgv.jl, or opt_main_ckks.jl)
3. Julia installation is checked
4. Julia script executes with homomorphic encryption
5. Results JSON is loaded

**Example output:**
```
⚠️  Note: PAILLIER encryption adds significant overhead
⚠️  Expected overhead: ~10x slower than non-encrypted

[ENC] Step 1: Preparing Julia environment...
[ENC]   Current directory: /home/user/some/path
[ENC]   Changing to: /home/user/DP_D_OPF/optimization
[ENC]   ✓ Working directory changed

[ENC] Step 2: Checking Julia script...
[ENC]   Script: opt_main_verified.jl
[ENC]   ✓ Script found: /home/user/DP_D_OPF/optimization/opt_main_verified.jl

[ENC] Step 3: Checking Julia installation...
[ENC]   ✓ Julia found: julia version 1.9.3

[ENC] Step 4: Running Julia script...
[ENC]   Command: julia opt_main_verified.jl
[ENC]   Timeout: 3600 seconds (1 hour)
--------------------------------------------------------------------------------

[Julia output appears here...]

--------------------------------------------------------------------------------
[ENC] Step 5: Checking for results...
[ENC]   Looking for: /home/user/DP_D_OPF/optimization/results/paillier_results.json
[ENC]   ✓ Results file found

================================================================================
✓ PAILLIER ENCRYPTION COMPLETED
================================================================================
  Total time: 146.32s
  Iterations: 203
  Final cost: $8081.53
  Optimality loss: 32.9673%
  Converged: true

  Timing breakdown:
    Optimization: 45.2%
    Cryptography: 48.3%
    Other: 6.5%
```

**Common errors:**

### Error: Missing Primes package
```
ERROR: LoadError: ArgumentError: Package Primes not found in current path.

[ENC] ✗ Missing Julia package: Primes
[ENC]   Install with: julia -e 'using Pkg; Pkg.add("Primes")'
[ENC]   Or run: julia install_julia_packages.jl
```

**Solution:** Install the missing package:
```bash
# Option 1: Quick fix
julia -e 'using Pkg; Pkg.add("Primes")'

# Option 2: Install all packages (recommended)
cd /home/user/DP_D_OPF/optimization
julia install_julia_packages.jl
```

### Error: Julia not found
```
[ENC]   ✗ Julia not found in PATH
[ENC]   Install Julia from: https://julialang.org/downloads/
```

**Solution:** Install Julia:
```bash
# See JULIA_SETUP.md for detailed instructions
cat JULIA_SETUP.md
```

### Error: Script timeout
```
[ENC] ✗ Julia script timeout (exceeded 1 hour)
[ENC]   Consider reducing --max-iter for encrypted modes
```

**Solution:** Encrypted modes are VERY slow. Reduce iterations:
```bash
# For Paillier (10x overhead)
python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m --max-iter 200

# For BGV/CKKS (3000x overhead!)
python evaluate_edge_opf.py --mode bgv --case testbeds/pglib_opf_case14_ieee.m --max-iter 50
```

### Error: Results file not found
```
[ENC]   ✗ Results file not found: results/paillier_results.json
[ENC]   Expected at: /home/user/DP_D_OPF/optimization/results/paillier_results.json
[ENC]   Julia script failed with return code: 1
[ENC]   Check the error messages above
```

**Solution:** The Julia script crashed. Look at the Julia output above this message for the actual error.

---

## Visualization Phase [VIZ]

**What happens:**
1. Output directories are created
2. ResultsExporter is initialized
3. Plots are generated based on mode

**Example output:**
```
[VIZ] Step 1: Creating output directories...
[VIZ]   ✓ Output dir: edge/results
[VIZ]   ✓ Plots dir: edge/plots

[VIZ] Step 2: Initializing ResultsExporter...
[VIZ]   ✓ ResultsExporter initialized

[VIZ] Step 3: Generating plots...
[VIZ]   Mode: distributed - generating full plot suite
[VIZ]   ✓ Plots generated successfully

[VIZ] ✓ Plots saved to: edge/plots
```

**Note:** Distributed mode generates the most comprehensive plots (33+ plots including dual time-axis views).

---

## Performance Overhead Warnings

When using encrypted modes, you'll see these warnings:

```
⚠️  Note: PAILLIER encryption adds significant overhead
⚠️  Expected overhead: ~10x slower than non-encrypted
```

```
⚠️  Note: BGV encryption adds significant overhead
⚠️  Expected overhead: ~300x slower than Paillier (~3000x vs non-encrypted)
```

```
⚠️  Note: CKKS encryption adds significant overhead
⚠️  Expected overhead: ~300x slower than Paillier (~3000x vs non-encrypted)
```

**These are informational warnings**, not errors. Homomorphic encryption is computationally expensive.

---

## Complete Example Output

Here's what a successful centralized run looks like:

```
[INIT] Adding edge module to Python path...
[INIT] Importing required modules...
[INIT]   ✓ EdgeOPFSimulator imported
[INIT]   ✓ JuliaOPFExecutor imported
[INIT]   ✓ ResultsExporter imported

================================================================================
EDGE OPF EVALUATION
================================================================================
Mode: CENTRALIZED
Case: testbeds/pglib_opf_case14_ieee.m
Max iterations: 1000
================================================================================

✓ Configuration saved to: edge/results/config_centralized_20251109_143052.json

================================================================================
RUNNING CENTRALIZED OPF
================================================================================

[CENT] Step 1: Creating JuliaOPFExecutor...
[CENT]   ✓ JuliaOPFExecutor created
[CENT] Step 2: Running centralized OPF...
[CENT]   Case: testbeds/pglib_opf_case14_ieee.m
[CENT]   Max iterations: 1000
[CENT]   Privacy method: PVP
[CENT]   Epsilon: 1.0

[CENT] ✓ Centralized OPF completed successfully
[CENT]   Execution time: 32.45s
[CENT]   Iterations: 897
[CENT]   Final cost: $8081.53
[CENT]   Optimality loss: 32.9673%
[CENT]   ⚠️  High optimality loss detected (> 20%)
[CENT]   This is expected with differential privacy
[CENT]   To reduce: increase --epsilon (less privacy) or decrease --alpha

================================================================================
✓ EVALUATION COMPLETED SUCCESSFULLY
================================================================================

Results directory: edge/results
Plots directory: edge/plots
```

---

## Troubleshooting Tips

### 1. Empty output or no logs?

**Check:** Are you running from the correct directory?
```bash
cd /home/user/DP_D_OPF/optimization
pwd  # Should show: /home/user/DP_D_OPF/optimization
```

### 2. Module import errors?

**Check:** Do the files exist?
```bash
ls edge/edge_opf_simulator.py
ls edge/julia_wrapper.py
ls edge/visualization.py
```

### 3. Distributed mode fails?

**Check:** Is your version up to date?
```bash
git pull origin claude/edge-device-evaluation-011CUi3Sxn7ZKMHFNPBXsfNE
```

### 4. Encrypted mode missing packages?

**Check:** Run the Julia package installer:
```bash
julia install_julia_packages.jl
```

### 5. Still stuck?

**Check:** Review the comprehensive guides:
```bash
cat USAGE_GUIDE.md        # Complete CLI usage
cat FIXES_APPLIED.md      # Known issues and solutions
cat JULIA_SETUP.md        # Julia installation
```

---

## Log Files

The CLI currently outputs to stdout. To save logs to a file:

```bash
# Save logs to file
python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m 2>&1 | tee run.log

# Save only errors
python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m 2> errors.log
```

---

## Summary

The logging system provides:
- ✅ **Step-by-step execution tracking** - Know exactly what's happening
- ✅ **Clear error messages** - Understand what went wrong
- ✅ **Helpful solutions** - Get commands to fix common errors
- ✅ **Performance warnings** - Know what to expect from encrypted modes
- ✅ **Success indicators** - Confirm each step completed correctly

**With comprehensive logging, you can quickly identify and fix issues!**

---

**Last Updated:** 2025-11-09
**Related Files:** USAGE_GUIDE.md, FIXES_APPLIED.md, JULIA_SETUP.md
