#!/usr/bin/env julia
"""
Julia Package Installer for OPF Edge Evaluation
Installs all required Julia packages for the framework

Usage:
    julia install_julia_packages.jl
"""

using Pkg

println("="^80)
println("Installing Julia Packages for OPF Edge Evaluation")
println("="^80)
println()

# List of required packages
required_packages = [
    "PowerModels",
    "DataStructures",
    "JuMP",
    "HiGHS",         # FREE solver (default)
    "DataFrames",
    "LinearAlgebra", # Standard library, but good to ensure
    "CSV",
    "Distributions",
    "JSON"
]

# Optional packages (for those who have licenses)
optional_packages = [
    "Gurobi",  # Commercial solver (requires license)
    "GLPK"     # Another free solver option
]

println("Installing REQUIRED packages...")
println("-" * 80)

for pkg in required_packages
    try
        println("Installing $pkg...")
        Pkg.add(pkg)
        println("✓ $pkg installed successfully")
    catch e
        println("✗ Failed to install $pkg: $e")
        println("  You may need to install this package manually")
    end
    println()
end

println()
println("="^80)
println("OPTIONAL Packages (skipping by default)")
println("="^80)
println()
println("The following packages are optional:")
for pkg in optional_packages
    println("  - $pkg")
end
println()
println("To install Gurobi (if you have a license):")
println("  julia -e 'using Pkg; Pkg.add(\"Gurobi\")'")
println()
println("To install GLPK (free alternative solver):")
println("  julia -e 'using Pkg; Pkg.add(\"GLPK\")'")
println()

println("="^80)
println("Testing installations...")
println("="^80)
println()

# Test imports
success_count = 0
fail_count = 0

for pkg in required_packages
    try
        if pkg != "LinearAlgebra"  # Skip standard library
            eval(Meta.parse("using $pkg"))
            println("✓ $pkg imports successfully")
            success_count += 1
        end
    catch e
        println("✗ $pkg failed to import: $e")
        fail_count += 1
    end
end

println()
println("="^80)
println("Installation Summary")
println("="^80)
println("✓ Successfully installed/verified: $success_count packages")
if fail_count > 0
    println("✗ Failed: $fail_count packages")
    println()
    println("Please manually install failed packages:")
    println("  julia -e 'using Pkg; Pkg.add(\"PackageName\")'")
else
    println("✓ All required packages are ready!")
end
println()

# Test HiGHS solver specifically
println("="^80)
println("Testing HiGHS Solver")
println("="^80)
try
    using HiGHS
    using JuMP

    # Create a simple test model
    model = Model(HiGHS.Optimizer)
    set_silent(model)
    @variable(model, x >= 0)
    @objective(model, Min, x)
    @constraint(model, x >= 1)
    optimize!(model)

    if termination_status(model) == MOI.OPTIMAL
        println("✓ HiGHS solver is working correctly!")
        println("  Test result: x = $(value(x))")
    else
        println("⚠ HiGHS solver ran but didn't find optimal solution")
    end
catch e
    println("✗ HiGHS solver test failed: $e")
    println("  You may need to reinstall HiGHS:")
    println("  julia -e 'using Pkg; Pkg.rm(\"HiGHS\"); Pkg.add(\"HiGHS\")'")
end

println()
println("="^80)
println("Installation Complete!")
println("="^80)
println()
println("You can now run:")
println("  julia main.jl")
println("  julia edge/scripts/opf_centralized_edge.jl")
println()
println("Or use the Python evaluation framework:")
println("  cd edge")
println("  python evaluate_edge_opf.py --mode centralized")
println()
