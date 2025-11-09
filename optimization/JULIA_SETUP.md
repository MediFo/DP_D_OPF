# Julia Dependencies Installation Guide

## Required Julia Packages

The OPF scripts require several Julia packages. Here's how to install them:

### Quick Installation (All Packages)

```julia
# Launch Julia REPL
julia

# Install all required packages
using Pkg

# Core packages
Pkg.add("PowerModels")
Pkg.add("JuMP")
Pkg.add("Gurobi")
Pkg.add("DataStructures")
Pkg.add("DataFrames")
Pkg.add("LinearAlgebra")
Pkg.add("CSV")
Pkg.add("Distributions")
Pkg.add("JSON")
Pkg.add("Dates")

# Encryption packages (for encrypted modes)
Pkg.add("Primes")         # Required for Paillier
Pkg.add("Random")
```

### Command-Line Installation

You can also install from command line:

```bash
julia -e 'using Pkg; Pkg.add(["PowerModels", "JuMP", "Gurobi", "DataStructures", "DataFrames", "LinearAlgebra", "CSV", "Distributions", "JSON", "Dates", "Primes", "Random"])'
```

---

## Package List by Mode

### For All Modes (Centralized & Distributed)

```julia
Pkg.add("PowerModels")      # Power system modeling
Pkg.add("JuMP")             # Optimization modeling
Pkg.add("Gurobi")           # Solver
Pkg.add("DataStructures")   # SortedDict
Pkg.add("DataFrames")       # Data manipulation
Pkg.add("LinearAlgebra")    # Matrix operations
Pkg.add("CSV")              # File I/O
Pkg.add("Distributions")    # Laplace distribution for DP
Pkg.add("JSON")             # JSON output
Pkg.add("Dates")            # Timestamps
```

### Additional for Encrypted Modes (Paillier, BGV, CKKS)

```julia
Pkg.add("Primes")          # Prime number generation
Pkg.add("Random")          # Random number generation
```

---

## Gurobi Setup

### Windows

1. Download Gurobi from: https://www.gurobi.com/downloads/
2. Install Gurobi
3. Get a license (free academic license available)
4. Set environment variable:
   ```
   setx GUROBI_HOME "C:\gurobi1100\win64"
   setx PATH "%PATH%;%GUROBI_HOME%\bin"
   ```
5. In Julia:
   ```julia
   using Pkg
   Pkg.add("Gurobi")
   Pkg.build("Gurobi")
   ```

### Linux/Mac

1. Download and install Gurobi
2. Set environment variables:
   ```bash
   export GUROBI_HOME="/opt/gurobi1100/linux64"
   export PATH="${PATH}:${GUROBI_HOME}/bin"
   export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"
   ```
3. Get license and install
4. In Julia:
   ```julia
   using Pkg
   Pkg.add("Gurobi")
   Pkg.build("Gurobi")
   ```

---

## Verification

### Test Basic Installation

```julia
using PowerModels
using JuMP
using Gurobi
using JSON

println("✓ All basic packages loaded successfully")
```

### Test Gurobi

```julia
using JuMP
using Gurobi

env = Gurobi.Env()
model = Model(() -> Gurobi.Optimizer(env))

println("✓ Gurobi working correctly")
```

### Test Encryption Packages

```julia
using Primes
using Random

p = nextprime(2^10)
println("✓ Primes package working: Found prime $p")
```

---

## Troubleshooting

### Error: "Package X not found"

**Solution:** Install the missing package:
```julia
using Pkg
Pkg.add("PackageName")
```

### Error: "Gurobi not properly installed"

**Solutions:**
1. Make sure Gurobi is installed and licensed
2. Check environment variables
3. Rebuild the Julia package:
   ```julia
   using Pkg
   Pkg.build("Gurobi")
   ```

### Error: "LoadError: ArgumentError: Package Primes not found"

**Solution:** This is needed for Paillier encryption:
```julia
using Pkg
Pkg.add("Primes")
```

---

## Complete Installation Script

Save this as `install_julia_packages.jl`:

```julia
#!/usr/bin/env julia
"""
Install all required Julia packages for DP_D_OPF
"""

using Pkg

println("="^80)
println("Installing Julia Packages for DP_D_OPF")
println("="^80)

packages = [
    "PowerModels",
    "JuMP",
    "Gurobi",
    "DataStructures",
    "DataFrames",
    "LinearAlgebra",
    "CSV",
    "Distributions",
    "JSON",
    "Dates",
    "Primes",
    "Random"
]

for pkg in packages
    println("\nInstalling $pkg...")
    try
        Pkg.add(pkg)
        println("✓ $pkg installed successfully")
    catch e
        println("✗ Error installing $pkg: $e")
    end
end

println("\n" * "="^80)
println("Installation Complete")
println("="^80)

# Test installations
println("\nTesting installations...")

try
    using PowerModels
    using JuMP
    using Gurobi
    using JSON
    using Primes
    println("✓ All packages loaded successfully")
catch e
    println("✗ Error loading packages: $e")
    println("  Some packages may need additional setup (e.g., Gurobi license)")
end
```

Run it:
```bash
julia install_julia_packages.jl
```

---

## Quick Fix for Current Error

The error you're seeing:
```
ERROR: LoadError: ArgumentError: Package Primes not found
```

**Fix:**
```bash
julia -e 'using Pkg; Pkg.add("Primes")'
```

Then re-run your command:
```bash
python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m
```

---

## Minimum Requirements

### For Centralized/Distributed (No Encryption):
- PowerModels
- JuMP
- Gurobi (with valid license)
- DataStructures
- DataFrames
- LinearAlgebra
- CSV
- Distributions
- JSON
- Dates

### Additional for Encryption:
- Primes
- Random

---

## Version Information

Recommended Julia version: **1.8 or higher**

Check your Julia version:
```bash
julia --version
```

Update Julia if needed from: https://julialang.org/downloads/

---

**Last Updated:** 2025-11-09
