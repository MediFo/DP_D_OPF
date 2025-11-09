# Gurobi Optimization Troubleshooting Guide

This guide helps you resolve common issues when running the Gurobi-based optimization code.

## Quick Diagnostic

Run this first to identify issues:
```bash
cd optimization
julia test_setup.jl
```

This will check:
- ✅ Julia version
- ✅ Required packages
- ✅ Gurobi license
- ✅ Testbed files
- ✅ Script files
- ✅ Basic optimization test

---

## Common Errors and Solutions

### 1. "Gurobi license not found" or "No Gurobi license"

**Error:**
```
ERROR: GurobiError(10009): No Gurobi license found (user [username], host [hostname], hostid [id])
```

**Causes & Solutions:**

#### Solution A: Set License File Path
```bash
# Find your license file
find ~ -name "gurobi.lic" 2>/dev/null

# Set environment variable
export GRB_LICENSE_FILE=/path/to/gurobi.lic

# Make it permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export GRB_LICENSE_FILE=/path/to/gurobi.lic' >> ~/.bashrc
source ~/.bashrc
```

#### Solution B: Get a License
If you don't have a license:

**Academic License (FREE for universities):**
```bash
# 1. Create account at https://www.gurobi.com/
# 2. Get academic license: https://www.gurobi.com/academia/academic-program-and-licenses/
# 3. Download license file
# 4. Place in ~/.gurobi/ directory
```

**Commercial Trial (30 days FREE):**
```bash
# Get trial license: https://www.gurobi.com/downloads/request-an-evaluation-license/
```

#### Solution C: Use Named-User License
```bash
# If you have a named-user license server
export GRB_LICENSE_FILE=port@server
# Example: export GRB_LICENSE_FILE=port@licenseserver.university.edu
```

---

### 2. "Package Gurobi not found"

**Error:**
```
ERROR: ArgumentError: Package Gurobi not found in current path
```

**Solution:**
```julia
# In Julia REPL
using Pkg
Pkg.add("Gurobi")
Pkg.build("Gurobi")

# If build fails, install Gurobi software first:
# Download from: https://www.gurobi.com/downloads/
```

---

### 3. "LoadError: MethodError" or Function Signature Errors

**Error:**
```
ERROR: MethodError: no method matching OPF_centralized(::Vector{...}, ...)
```

**Cause:** Missing `gurobi_env` parameter in function calls

**Solution:** Ensure all optimizer functions receive `gurobi_env`:
```julia
# ✓ CORRECT:
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus, gurobi_env)
(θ, cost, p, l) = update_θ(gen, bus, line, B, refbus, μ, θ̅, ρ, gurobi_env)
Δ_op = sensitivities(gen, bus, line, B, refbus, ρ, method, α, gurobi_env)

# ✗ WRONG:
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus)  # Missing gurobi_env!
```

---

### 4. "Gurobi Optimizer returned with error code X"

**Common Error Codes:**

| Code | Meaning | Solution |
|------|---------|----------|
| 10001 | Out of memory | Reduce problem size or increase system RAM |
| 10003 | Numerical issues | Try different Gurobi parameters (see below) |
| 10009 | No license | See Error #1 above |
| 10020 | Model is infeasible | Check problem formulation |
| 10021 | Model is unbounded | Add missing constraints |

**Debugging with Verbose Output:**
```julia
# In fun_centralized_OPF.jl or fun_voltage_update.jl
# Change from:
set_silent(m)

# To:
# set_silent(m)  # Comment out this line to see solver output
```

---

### 5. "DataStructures: SortedDict not found"

**Error:**
```
ERROR: UndefVarError: SortedDict not defined
```

**Solution:**
```julia
using Pkg
Pkg.add("DataStructures")
```

---

### 6. Gurobi Optimizer Parameters Not Working

**Error:**
```
ERROR: Gurobi Error 10003: Unknown parameter 'XXX'
```

**Solution:** Use `set_optimizer_attribute` syntax:
```julia
# ✓ CORRECT (modern JuMP syntax):
set_optimizer_attribute(m, "Method", 2)
set_optimizer_attribute(m, "Presolve", 1)
set_optimizer_attribute(m, "OutputFlag", 0)

# ✗ WRONG (old syntax):
m = Model(with_optimizer(Gurobi.Optimizer, Method=2))  # Deprecated!
```

---

### 7. Slow Performance / Optimization Taking Too Long

**Solutions:**

#### A. Enable Parallel Processing
```julia
# In fun_centralized_OPF.jl, add after creating model:
set_optimizer_attribute(m, "Threads", 4)  # Use 4 CPU threads
```

#### B. Adjust Gurobi Method
```julia
# Try different optimization methods
set_optimizer_attribute(m, "Method", 2)  # 0=primal, 1=dual, 2=barrier, 3=concurrent
```

#### C. Relax Tolerance
```julia
# For faster (less accurate) solutions
set_optimizer_attribute(m, "OptimalityTol", 1e-4)  # Default: 1e-6
set_optimizer_attribute(m, "FeasibilityTol", 1e-4)  # Default: 1e-6
```

---

### 8. "Unsupported constraint" or "Quadratic constraints"

**Error:**
```
ERROR: Gurobi does not support this constraint type
```

**Solution:** Ensure you have a valid Gurobi license that supports quadratic programming (QP):
- **Academic licenses**: Support QP
- **Trial licenses**: Support QP
- **Some commercial licenses**: May not support QP

Check your license capabilities at: https://www.gurobi.com/

---

### 9. Results Don't Match Expected Values

**Diagnostic Steps:**

#### Step 1: Check Gurobi vs HiGHS Results
```bash
# Run main project (HiGHS)
cd ..
julia main.jl > results_highs.txt

# Run optimization (Gurobi)
cd optimization
julia main.jl > results_gurobi.txt

# Compare
diff results_highs.txt results_gurobi.txt
```

#### Step 2: Enable Verbose Output
```julia
# In main.jl, add after creating gurobi_env:
set_optimizer_attribute(m, "OutputFlag", 1)  # Show detailed solver output
```

#### Step 3: Check Termination Status
```julia
# In fun_centralized_OPF.jl, change:
@info("Centralized OPF terminates with status $(status)")

# To:
println("Status: $(status)")
println("Primal status: $(primal_status(m))")
println("Dual status: $(dual_status(m))")
println("Objective value: $(objective_value(m))")
```

---

### 10. Edge Simulation Errors (Python)

**Error:**
```
ModuleNotFoundError: No module named 'edgesimpy'
```

**Solution:**
```bash
cd optimization/edge
pip install -r requirements.txt
```

**Error:**
```
julia: command not found (from Python)
```

**Solution:**
```bash
# Ensure Julia is in PATH
which julia

# If not found, add to PATH
export PATH="/path/to/julia/bin:$PATH"
```

---

## Advanced Debugging

### Enable Full Gurobi Logging
```julia
# Create a log file to capture all Gurobi output
set_optimizer_attribute(m, "LogFile", "gurobi.log")
set_optimizer_attribute(m, "LogToConsole", 1)
```

### Check Gurobi Installation
```julia
# In Julia REPL
using Gurobi
Gurobi.version()  # Should show version like (10, 0, 0)
```

### Verify License Details
```julia
using Gurobi
env = Gurobi.Env()
# Check console output for license type and expiration
```

---

## Performance Tuning

### For Large-Scale Problems (case118+)

```julia
# In fun_centralized_OPF.jl or fun_voltage_update.jl
set_optimizer_attribute(m, "Method", 2)          # Barrier method (fastest for large LP/QP)
set_optimizer_attribute(m, "Threads", 8)         # Use 8 CPU cores
set_optimizer_attribute(m, "BarConvTol", 1e-5)   # Barrier convergence tolerance
set_optimizer_attribute(m, "Presolve", 2)        # Aggressive presolve
```

### For Quick Prototyping

```julia
# Sacrifice accuracy for speed
set_optimizer_attribute(m, "OptimalityTol", 1e-3)
set_optimizer_attribute(m, "TimeLimit", 60)      # Stop after 60 seconds
```

---

## Getting Help

1. **Gurobi Support:** https://support.gurobi.com/
2. **JuMP.jl Documentation:** https://jump.dev/
3. **PowerModels.jl:** https://github.com/lanl-ansi/PowerModels.jl
4. **This Project Issues:** See main project README

---

## Checklist Before Running

- [ ] Gurobi is installed
- [ ] Valid Gurobi license (not expired)
- [ ] GRB_LICENSE_FILE environment variable is set
- [ ] All Julia packages installed (run `test_setup.jl`)
- [ ] Scripts are in `optimization/scripts/` folder
- [ ] Test case files are in `optimization/testbeds/` folder
- [ ] Julia version >= 1.6
- [ ] `gurobi_env` is passed to all optimizer functions

---

**Last Updated:** November 2025
