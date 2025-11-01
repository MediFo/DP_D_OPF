# Quick Start Installation Guide for ADMM+Paillier

## Prerequisites
- Julia 1.0 or higher
- No commercial solver license required (uses free Ipopt solver)

## Step 1: Install Julia Packages

Open Julia REPL and run:

```julia
using Pkg

# Core packages
Pkg.add("PowerModels")
Pkg.add("JuMP")
Pkg.add("Ipopt")          # Free nonlinear solver
Pkg.add("DataFrames")
Pkg.add("LinearAlgebra")
Pkg.add("Primes")         # For Paillier cryptography
Pkg.add("DataStructures")
Pkg.add("CSV")
Pkg.add("Printf")
```

## Step 2: Run the Code

```bash
# Clone the repository (if not already done)
git clone https://github.com/MediFo/DP_D_OPF.git
cd DP_D_OPF

# Run ADMM with Paillier encryption
julia main_admm_paillier.jl
```

## Step 3: Verify Installation

You should see output like:

```
================================================================================
 BOYD'S CONSENSUS ADMM + PAILLIER ENCRYPTION FOR DC-OPF
================================================================================

[1/6] Loading network data...
  ✓ Network loaded: 14 buses, 5 generators, 20 lines

[2/6] Solving centralized OPF (baseline)...
  ✓ Centralized cost: $8081.52

[3/6] Generating Paillier encryption keys...
  🔐 Generating 512-bit primes...
  ✓ Keys generated in 2.34s (1024-bit)

...
```

## Troubleshooting

### "Ipopt not found"
```julia
using Pkg
Pkg.add("Ipopt")
```

### "Primes not found"
```julia
using Pkg
Pkg.add("Primes")
```

### "PowerModels not found"
```julia
using Pkg
Pkg.add("PowerModels")
```

### Slow performance
- Reduce `key_length` from 2048 to 1024 in `main_admm_paillier.jl`
- Reduce `ν̅` (max iterations) from 100 to 50

### Not converging
- Increase `ρ` parameter (try 100 instead of 50)
- Check that dual update is using correct sign (should be fixed in this version)

## Optional: Install Gurobi (Commercial Solver)

If you have a Gurobi license:

```julia
using Pkg
Pkg.add("Gurobi")
```

Then uncomment Gurobi sections and comment out Ipopt sections in:
- `main_admm_paillier.jl`
- `scripts/fun_centralized_OPF.jl`
- `scripts/fun_voltage_update.jl`
- `scripts/fun_compute_sensitivity.jl`

## Files Overview

- `main_admm_paillier.jl` - Main ADMM+Paillier implementation
- `scripts/paillier_crypto.jl` - Paillier encryption library
- `scripts/fun_dual_update.jl` - ADMM dual update (fixed sign)
- `README_ADMM_PAILLIER.md` - Full documentation

## Expected Runtime

| Network | Iterations | Key Size | Time |
|---------|-----------|----------|------|
| IEEE 14-bus | ~30 | 1024-bit | ~30s |
| IEEE 14-bus | ~30 | 2048-bit | ~3min |
| IEEE 30-bus | ~40 | 1024-bit | ~1min |
| IEEE 30-bus | ~40 | 2048-bit | ~6min |

## Success Criteria

✅ Code runs without errors
✅ Residual decreases over iterations
✅ Converges in <100 iterations
✅ Final cost matches centralized OPF (within 0.1%)

## Need Help?

See `README_ADMM_PAILLIER.md` for detailed documentation.
