# Quick Start Guide - Gurobi Optimization

## Prerequisites

### 1. Install Gurobi
```bash
# Download Gurobi from: https://www.gurobi.com/downloads/
# Follow installation instructions for your OS
```

### 2. Get Gurobi License
```bash
# Academic (FREE): https://www.gurobi.com/academia/
# Commercial Trial (30 days FREE): https://www.gurobi.com/downloads/request-an-evaluation-license/

# Set license file location
export GRB_LICENSE_FILE=/path/to/gurobi.lic
```

### 3. Install Julia Packages
```julia
# Open Julia REPL
using Pkg
Pkg.add("PowerModels")
Pkg.add("DataStructures")
Pkg.add("JuMP")
Pkg.add("Gurobi")
Pkg.add("DataFrames")
Pkg.add("LinearAlgebra")
Pkg.add("CSV")
Pkg.add("Distributions")
```

## Verify Setup

```bash
cd optimization
julia test_setup.jl
```

You should see:
```
✅ ALL CHECKS PASSED!
```

## Run Optimization

### Basic Usage
```bash
cd optimization
julia main.jl
```

### Expected Output
```
[ Info: Centralized OPF terminates with status OPTIMAL
ν --- 100 ... res --- 0.12345
ν --- 200 ... res --- 0.00234
[ Info: ADMM terminates at iteration 234

Optimality loss ---> 0.15%
Comparison of the non-private and differentially private load inference
14×3 DataFrame
 Row │ node   actual   observed
     │ Any    Any      Any
─────┼─────────────────────────
   1 │ 1      0.0      0.0
   2 │ 2      21.7     21.652
  ...
```

## Run Edge Simulations

```bash
cd optimization/edge

# Distributed simulation with 36 edge devices
python example_distributed_opf.py

# Centralized simulation (single device)
python example_centralized_opf.py

# Custom hardware configuration
python example_custom_hardware.py
```

### Expected Output
```
Initializing EdgeSimPy simulator...
Creating 36 edge devices...
Running distributed OPF...
Generating plots (31 total)...
✓ All plots saved to plots/
```

## Customize Parameters

### Change Test Case
Edit `main.jl` line 24:
```julia
# Use different power system case
caseID="testbeds/pglib_opf_case30_ieee.m"  # 30-bus system
# caseID="testbeds/pglib_opf_case118_ieee.m"  # 118-bus system
```

### Adjust ADMM Parameters
Edit `main.jl` lines 32-46:
```julia
ν̅ = 15000      # Maximum iterations
ρ = 1e3        # Penalty parameter
γ = 1e-2       # Convergence tolerance
ϵ = 1.0        # Privacy budget
α = 0.1        # Adjacency coefficient
method = "PVP" # Or "DVP"
```

### Gurobi Solver Settings
Edit `scripts/fun_centralized_OPF.jl`:
```julia
# After creating model, add:
set_optimizer_attribute(m, "Threads", 4)     # Use 4 CPU cores
set_optimizer_attribute(m, "Method", 2)      # Barrier method
set_optimizer_attribute(m, "TimeLimit", 300) # 5 minute limit
```

## Troubleshooting

If you encounter errors:
```bash
# See detailed troubleshooting
cat TROUBLESHOOTING.md

# Common fixes:
export GRB_LICENSE_FILE=/path/to/gurobi.lic  # License not found
julia test_setup.jl                           # Verify setup
```

## Compare with HiGHS

```bash
# Run main project (HiGHS solver)
cd ..
julia main.jl > highs_results.txt

# Run optimization (Gurobi solver)
cd optimization
julia main.jl > gurobi_results.txt

# Compare
diff highs_results.txt gurobi_results.txt
```

## Next Steps

- ✅ Read `README.md` for detailed documentation
- ✅ See `TROUBLESHOOTING.md` for common issues
- ✅ Explore `edge/` folder for simulation options
- ✅ Check `edge/visualization.py` for plot customization

## Performance Tips

**For Large Problems (100+ buses):**
- Use Method=2 (barrier algorithm)
- Increase Threads to match your CPU cores
- Enable aggressive presolve

**For Quick Testing:**
- Reduce ν̅ (max iterations) to 1000
- Increase γ (tolerance) to 1e-1
- Use smaller test cases (case14, case30)

**For High Accuracy:**
- Set tighter tolerances in Gurobi
- Increase maximum iterations
- Use Method=2 with crossover

---

**Need Help?** See `TROUBLESHOOTING.md` or contact Gurobi support
