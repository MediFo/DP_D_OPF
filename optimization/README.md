# Optimization Folder - Gurobi Solver Version

This folder contains the **Gurobi-optimized version** of the DP_D_OPF project for high-performance optimization.

## Overview

This is a complete copy of the main project optimized to use **Gurobi** commercial solver instead of the free HiGHS solver. Everything else remains identical to the main project.

## Folder Structure

```
optimization/
├── main.jl                      # Main execution script (Gurobi version)
├── scripts/                     # Julia optimization scripts
│   ├── data_manager.jl         # Data loading and management
│   ├── fun_centralized_OPF.jl  # Centralized OPF with Gurobi
│   ├── fun_compute_sensitivity.jl  # Sensitivity computation with Gurobi
│   ├── fun_voltage_update.jl   # Voltage angle update with Gurobi
│   ├── fun_consensus_update.jl # ADMM consensus update
│   ├── fun_dual_update.jl      # ADMM dual variable update
│   ├── fun_residual_update.jl  # Residual computation
│   └── fun_reveal_load.jl      # Load revelation mechanism
├── testbeds/                    # Power system test cases
│   └── pglib_opf_case*.m       # MATPOWER format test cases
└── edge/                        # Edge device simulation framework
    ├── edge_opf_simulator.py   # Main simulator
    ├── visualization.py         # Comprehensive visualization (31 plots!)
    ├── julia_wrapper.py         # Julia-Python integration
    ├── example_*.py             # Example scripts
    └── edgesimpy/               # EdgeSimPy framework
```

## Key Differences from Main Project

| Feature | Main Project | This Folder (Optimization) |
|---------|-------------|---------------------------|
| **Solver** | HiGHS (Free) | **Gurobi (Commercial)** |
| **Performance** | Good | **Excellent** |
| **License** | Open-source | Requires Gurobi License |
| **Julia Scripts** | HiGHS-based | Gurobi-based |
| **Edge Simulation** | ✅ Identical | ✅ Identical |
| **Visualization** | ✅ 31 plots | ✅ 31 plots |

## Why Use This Version?

✅ **Faster Optimization**: Gurobi is generally faster than open-source solvers
✅ **Better Scalability**: Handles larger power systems more efficiently
✅ **Commercial Support**: Professional support from Gurobi
✅ **Advanced Features**: Access to Gurobi's advanced optimization algorithms

## Prerequisites

### 1. Gurobi License
You need a valid Gurobi license. Options:
- **Academic**: Free licenses available for academic research
- **Commercial**: Paid licenses for commercial use
- **Trial**: Free 30-day trial available

Get your license at: https://www.gurobi.com/downloads/

### 2. Julia Packages
```julia
using Pkg
Pkg.add("Gurobi")
Pkg.add("PowerModels")
Pkg.add("JuMP")
Pkg.add("DataFrames")
Pkg.add("LinearAlgebra")
Pkg.add("CSV")
Pkg.add("Distributions")
```

### 3. Python Dependencies (for edge simulations)
```bash
pip install numpy pandas matplotlib seaborn psutil
```

## Usage

### Running Julia Optimization (Gurobi)
```bash
cd optimization
julia main.jl
```

### Running Edge Simulations
```bash
cd optimization/edge
python example_distributed_opf.py
```

### Running with Custom Test Case
```julia
# Edit main.jl, change line 24:
caseID="testbeds/pglib_opf_case30_ieee.m"  # Change to your case
```

## Edge Simulation Features

The `edge/` folder contains a complete edge computing simulation framework with **31 comprehensive visualization plots**:

### Time-Series Plots (Percentile Bands Over Time)
- CPU Usage Over Time
- Memory Usage Over Time
- Power Consumption Over Time
- Energy Consumption Over Time (Cumulative)
- Network Efficiency Over Time

### Resource Plots (15 types)
- Resource heatmaps
- Stacked area charts
- Parallel coordinates
- Device type comparisons
- Correlation matrices
- CDF curves
- Small multiples (6x6 grid)
- Network topology graphs

### Network Plots (11 types)
- Traffic heatmaps
- Link utilization distributions
- Bottleneck identification
- Temporal traffic patterns
- Network efficiency metrics
- Box plots
- Violin plots
- Sorted bar charts
- CDF curves
- Swarm plots

## Modifications Made for Gurobi

All Julia scripts have been modified to use Gurobi:

1. **main.jl** - Uses `Gurobi.Env()` and passes `gurobi_env` to all functions
2. **fun_centralized_OPF.jl** - Solver changed to `Gurobi.Optimizer(gurobi_env)`
3. **fun_voltage_update.jl** - Solver changed to `Gurobi.Optimizer(gurobi_env)`
4. **fun_compute_sensitivity.jl** - Solver changed to `Gurobi.Optimizer(gurobi_env)` with advanced settings

## Performance Tips

### Gurobi Solver Settings
The solver is configured with optimal settings in `fun_compute_sensitivity.jl`:
```julia
set_optimizer_attribute(m, "Method", 2)      # Barrier method
set_optimizer_attribute(m, "Presolve", 1)    # Enable presolve
set_optimizer_attribute(m, "OutputFlag", 0)  # Silent mode
```

### For Large-Scale Problems
Consider adjusting in your functions:
- `Threads`: Number of parallel threads
- `MIPGap`: Relative MIP optimality gap
- `TimeLimit`: Maximum solve time

## Troubleshooting

### "Gurobi license not found"
```bash
# Set up Gurobi license
export GRB_LICENSE_FILE=/path/to/gurobi.lic
```

### "Package Gurobi not found"
```julia
using Pkg
Pkg.add("Gurobi")
Pkg.build("Gurobi")
```

### Python edge simulation errors
```bash
# Ensure Julia is accessible from Python
which julia
# Should show Julia installation path
```

## Comparison with Main Project

To compare results between HiGHS (main project) and Gurobi (this folder):

1. Run main project: `julia ../main.jl > results_highs.txt`
2. Run optimization: `julia main.jl > results_gurobi.txt`
3. Compare optimization times, objective values, and convergence rates

## License

This folder inherits the license from the main DP_D_OPF project.

**Note**: Gurobi itself requires a separate commercial or academic license.

## Support

- **DP_D_OPF Issues**: See main project README
- **Gurobi Issues**: https://support.gurobi.com/
- **EdgeSimPy Issues**: https://github.com/EdgeSimPy/EdgeSimPy

---

**Created**: November 2025
**Purpose**: High-performance optimization with Gurobi solver
**Maintained**: Same as main project
