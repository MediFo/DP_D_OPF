# Timestamp Recording Implementation

## Overview
Added comprehensive timestamp recording to all OPF scripts to support dual time-axis visualization (iteration-based and real-time).

## Changes Made

### 1. main.jl (Centralized/Distributed OPF)
**Added:**
- `iteration_timestamps` array - Records cumulative elapsed time from start for each iteration
- `iteration_times` array - Records duration of each individual iteration
- Both arrays included in results dictionary

**Code:**
```julia
# Track timing
start_time = time()
iteration_times = Float64[]  # Duration of each iteration
iteration_timestamps = Float64[]  # Cumulative timestamp (elapsed time from start)

# In ADMM loop:
iter_time = time() - iter_start
cumulative_time = time() - start_time  # Elapsed time from start
push!(iteration_times, iter_time)
push!(iteration_timestamps, cumulative_time)

# In results dictionary:
"iteration_times" => iteration_times,  # Duration of each iteration (seconds)
"iteration_timestamps" => iteration_timestamps,  # Cumulative time (seconds)
```

### 2. opt_main_verified.jl (Paillier Encryption)
**Added:**
- Same timing arrays as main.jl
- Results dictionary with comprehensive metrics
- JSON output to `results/paillier_results.json`

**New Results Dictionary:**
```julia
results = Dict(
    "mode" => "encrypted_paillier",
    "encryption_scheme" => "paillier",
    "iteration_times" => iteration_times[1:final_iter-1],
    "iteration_timestamps" => iteration_timestamps[1:final_iter-1],
    "residuals" => residuals[2:final_iter],
    "cost_history" => cost_history[2:final_iter],
    # ... other metrics
)
```

### 3. opt_main_bgv.jl (BGV Encryption)
**Added:**
- Same timing arrays and results dictionary
- JSON output to `results/bgv_results.json`

### 4. opt_main_ckks.jl (CKKS Encryption)
**Added:**
- Same timing arrays and results dictionary
- JSON output to `results/ckks_results.json`

## Data Structure

### Timing Arrays
All scripts now provide two timing arrays:

1. **iteration_times** (Float64[])
   - Duration of each iteration in seconds
   - Example: [0.125, 0.132, 0.128, ...]
   - Use for: Iteration performance analysis

2. **iteration_timestamps** (Float64[])
   - Cumulative elapsed time from ADMM start in seconds
   - Example: [0.125, 0.257, 0.385, ...]
   - Use for: Real-time progression, dual time-axis plots

### Results Dictionary Fields
Each script now returns:
```julia
{
    "mode": "centralized" | "encrypted_paillier" | "encrypted_bgv" | "encrypted_ckks",
    "total_time_s": Float,
    "iterations": Int,
    "avg_iteration_time_ms": Float,

    # Timing data
    "iteration_times": Float64[],          # Per-iteration duration
    "iteration_timestamps": Float64[],     # Cumulative timestamps

    # Convergence data
    "residuals": Float64[],
    "cost_history": Float64[],

    # For encrypted schemes only:
    "total_opt_time_s": Float,
    "total_crypto_time_s": Float,
    "pct_crypto": Float,

    # ... other fields
}
```

## Integration with Visualization

### How Timestamps Are Used

1. **Edge Simulation Framework** (`julia_wrapper.py`):
   ```python
   results = {
       'resource_monitoring': monitor_stats,  # System timestamps
       'julia_results': julia_results,        # iteration_timestamps
   }
   ```

2. **Visualization** (`visualization.py`):
   - Plot 29: Dual CPU/Memory percentile bands (iteration + real-time)
   - Plot 30: Iteration duration analysis
   - Plot 31: Cumulative computation time
   - Plot 32: Iteration throughput (iterations/minute)
   - Plot 33: Time budget analysis
   - Plot 34: Real-time efficiency metrics
   - Plot 35: Performance degradation analysis

### Dual Time-Axis Plots
Each new plot provides TWO views:

**Iteration-based view:**
- X-axis: Iteration number (1, 2, 3, ...)
- Y-axis: Metric value
- Shows: Per-step progression

**Real-time view:**
- X-axis: Elapsed time in minutes
- Y-axis: Metric value
- Shows: Real-world performance

## File Outputs

### JSON Results Files
- `results/paillier_results.json` - Paillier encryption results
- `results/bgv_results.json` - BGV encryption results
- `results/ckks_results.json` - CKKS encryption results
- `edge/results/node_{id}_results.json` - Distributed node results
- `edge/results/centralized_results.json` - Centralized results

### Visualization Outputs
All plots are generated in `edge/results/`:
- `*_dual_cpu_memory_percentile_iteration.png`
- `*_dual_cpu_memory_percentile_realtime.png`
- `*_iteration_duration_analysis.png`
- `*_cumulative_computation_time.png`
- `*_iteration_throughput.png`
- `*_time_budget_analysis.png`
- `*_realtime_efficiency_metrics.png`
- `*_performance_degradation.png`

## Benefits

### For Performance Analysis
- Track iteration-by-iteration performance
- Identify bottlenecks in real-time
- Measure encryption overhead accurately
- Compare different encryption schemes

### For Dual Time-Axis Visualization
- See ADMM convergence by iteration number
- See real-world elapsed time simultaneously
- Understand throughput (iterations/minute)
- Identify performance degradation over time

### For Debugging
- JSON output allows post-processing
- Detailed timing breakdown per iteration
- Separate crypto vs optimization time
- Easy to load and analyze offline

## Testing

All scripts have been updated and should be tested with:

```bash
# Test centralized mode
cd /home/user/DP_D_OPF/optimization
julia main.jl

# Test encryption schemes
julia opt_main_verified.jl  # Paillier
julia opt_main_bgv.jl        # BGV
julia opt_main_ckks.jl       # CKKS

# Test edge simulation (generates all plots)
cd edge
python3 edge_opf_simulator.py
```

## Notes

- All timestamps are in seconds (convert to minutes by dividing by 60)
- Arrays are truncated to `final_iter` to remove unused entries
- Residuals and cost_history start from iteration 2
- iteration_times and iteration_timestamps start from iteration 1
- System monitoring timestamps (from psutil) are separate from Julia iteration timestamps
