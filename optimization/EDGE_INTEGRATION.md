# Edge Simulation Integration with Root main.jl

## Overview

The edge simulation framework (`optimization/edge/`) now calls the **root `main.jl`** from `/optimization/` instead of using separate edge-specific Julia scripts.

This ensures consistency between standalone execution and edge simulation, using the exact same optimization code.

---

## What Changed

### 1. Modified `optimization/main.jl`

The root `main.jl` has been enhanced to:

- **Accept config files** as command-line arguments
- **Support both modes**: centralized and distributed
- **Save results to JSON** for edge simulation integration
- **Maintain backward compatibility** for standalone execution

**Key features:**
```julia
# Accepts config file as argument
julia main.jl path/to/config.json

# Or run standalone with defaults
julia main.jl
```

**Config parameters:**
- `mode`: "centralized" or "distributed"
- `node_id`: Node identifier (for distributed mode)
- `caseID`: Path to MATPOWER case file
- `max_iterations`: Maximum ADMM iterations
- `rho`: ADMM penalty parameter
- `tolerance`: Convergence tolerance
- `epsilon`: Privacy parameter
- `alpha`: Sensitivity scaling factor
- `method`: Privacy method ("PVP" or "DVP")

### 2. Updated `optimization/edge/julia_wrapper.py`

**Changes:**
- `self.main_script` now points to `base_dir / "main.jl"` (root main.jl)
- `run_distributed_node()` sets `config['mode'] = 'distributed'`
- `run_centralized()` sets `config['mode'] = 'centralized'`
- Both methods call root `main.jl` instead of edge-specific scripts

**Before:**
```python
script_path = self.scripts_dir / "opf_edge_node.jl"  # Edge-specific
```

**After:**
```python
script_path = self.main_script  # Root main.jl
```

---

## File Structure

```
optimization/
├── main.jl                     # ROOT SCRIPT (called by edge simulation)
├── scripts/
│   ├── data_manager.jl
│   ├── fun_centralized_OPF.jl  # Uses Gurobi
│   ├── fun_voltage_update.jl   # Uses Gurobi
│   └── ... (other functions)
├── testbeds/
│   └── pglib_opf_case14_ieee.m
└── edge/
    ├── julia_wrapper.py        # Modified to call root main.jl
    ├── edge_opf_simulator.py   # Uses julia_wrapper.py
    ├── test_integration.py     # Test script
    └── results/                # Output directory
```

---

## Usage

### 1. Standalone Execution

Run root `main.jl` directly:

```bash
cd optimization
julia main.jl
```

This uses default parameters and runs distributed mode.

### 2. With Config File

```bash
cd optimization
julia main.jl edge/test_config_centralized.json
```

### 3. Edge Simulation (Python)

```python
from edge.julia_wrapper import JuliaOPFExecutor, JuliaConfig

executor = JuliaOPFExecutor()

# Centralized mode
result = executor.run_centralized({
    "caseID": "testbeds/pglib_opf_case14_ieee.m",
    "max_iterations": 1000
})

# Distributed mode
result = executor.run_distributed_node(
    node_id=1,
    config=JuliaConfig(
        caseID="testbeds/pglib_opf_case14_ieee.m",
        max_iterations=1000,
        method="PVP"
    )
)
```

### 4. Full Edge Simulation

```bash
cd optimization/edge
python3 edge_opf_simulator.py
```

This will:
- Create edge computing topology with multiple servers
- Distribute OPF computations across edge nodes
- Call root `main.jl` for each node
- Monitor CPU, memory, power, energy
- Generate 31 visualization plots

---

## Testing

### Quick Structure Verification

```bash
cd optimization/edge
python3 test_integration.py
```

This verifies:
- ✓ All required files exist
- ✓ Python syntax is valid
- ✓ File paths are correct

### Full Integration Test (requires Julia + Gurobi)

When Julia and Gurobi are available:

```bash
cd optimization/edge
python3 test_integration.py
```

This runs:
1. Structure verification
2. Centralized OPF test
3. Distributed OPF test (single node)

---

## Example Config Files

### Centralized Mode

`config_centralized.json`:
```json
{
  "caseID": "testbeds/pglib_opf_case14_ieee.m",
  "mode": "centralized",
  "max_iterations": 1000,
  "rho": 1000.0,
  "tolerance": 0.01,
  "epsilon": 1.0,
  "alpha": 0.1,
  "method": "PVP"
}
```

### Distributed Mode

`config_node_1.json`:
```json
{
  "node_id": 1,
  "caseID": "testbeds/pglib_opf_case14_ieee.m",
  "mode": "distributed",
  "max_iterations": 1000,
  "rho": 1000.0,
  "tolerance": 0.01,
  "epsilon": 1.0,
  "alpha": 0.1,
  "method": "PVP"
}
```

---

## Output Format

### Results JSON Structure

When called from edge simulation, `main.jl` saves results to:
- **Centralized**: `edge/results/centralized_results.json`
- **Distributed**: `edge/results/node_{id}_results.json`

**JSON format:**
```json
{
  "mode": "distributed",
  "node_id": 1,
  "total_time_s": 12.345,
  "iterations": 450,
  "avg_iteration_time_ms": 27.43,
  "centralized_cost": 8123.45,
  "final_cost": 8125.67,
  "optimality_loss_percent": 0.027,
  "final_residual": 0.0095,
  "iteration_times": [...],
  "residuals": [...],
  "config": {...}
}
```

---

## Benefits of This Approach

1. **Code Consistency**: Same optimization logic for standalone and edge simulation
2. **Single Source of Truth**: Root `main.jl` is the only execution entry point
3. **Easier Maintenance**: Changes to optimization logic only need to be made once
4. **Gurobi Integration**: All executions use Gurobi solver consistently
5. **Backward Compatible**: `main.jl` still works standalone without edge simulation

---

## Troubleshooting

### Error: "Config file not found"

Make sure you're running from the correct directory:
```bash
cd /path/to/optimization
julia main.jl edge/results/config_node_1.json
```

### Error: "Gurobi license not found"

See `TROUBLESHOOTING.md` for Gurobi license setup instructions.

### Results not saved

Check that:
1. `edge/results/` directory exists (created automatically)
2. Config file was provided as argument (required for JSON output)
3. Julia script completed successfully

### Python can't find Julia

Ensure Julia is in PATH:
```bash
export PATH="/path/to/julia/bin:$PATH"
julia --version
```

---

## Migration from Edge Scripts

**Previous approach** (deprecated):
- `edge/scripts/opf_centralized_edge.jl` - Separate centralized script
- `edge/scripts/opf_edge_node.jl` - Separate distributed script
- Duplication of optimization logic

**Current approach**:
- `main.jl` - Single unified script
- Supports both centralized and distributed modes via config
- Called by `julia_wrapper.py` for edge simulation

**No code changes needed** in edge simulation Python scripts - they automatically use the new integration.

---

## Next Steps

1. **Run edge simulation**: `python3 edge/edge_opf_simulator.py`
2. **View results**: Check `edge/results/` for JSON files and plots
3. **Customize config**: Modify simulation parameters in edge scripts
4. **Scale up**: Increase number of edge nodes in `edge_opf_simulator.py`

---

**Last Updated**: November 2025
