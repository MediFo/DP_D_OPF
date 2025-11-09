#!/usr/bin/env julia
"""
Install all required Julia packages for DP_D_OPF

Usage:
    julia install_julia_packages.jl
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

success_count = 0
failed_packages = []

for pkg in packages
    println("\nInstalling $pkg...")
    try
        Pkg.add(pkg)
        println("✓ $pkg installed successfully")
        success_count += 1
    catch e
        println("✗ Error installing $pkg: $e")
        push!(failed_packages, pkg)
    end
end

println("\n" * "="^80)
println("Installation Summary")
println("="^80)
println("Successful: $success_count / $(length(packages))")

if !isempty(failed_packages)
    println("\nFailed packages:")
    for pkg in failed_packages
        println("  - $pkg")
    end
end

# Test installations
println("\n" * "="^80)
println("Testing Installations")
println("="^80)

test_results = Dict()

# Test core packages
println("\n[1] Testing core packages...")
try
    using PowerModels
    println("  ✓ PowerModels")
    test_results["PowerModels"] = true
catch e
    println("  ✗ PowerModels: $e")
    test_results["PowerModels"] = false
end

try
    using JuMP
    println("  ✓ JuMP")
    test_results["JuMP"] = true
catch e
    println("  ✗ JuMP: $e")
    test_results["JuMP"] = false
end

try
    using Gurobi
    println("  ✓ Gurobi")
    test_results["Gurobi"] = true
catch e
    println("  ✗ Gurobi: $e")
    test_results["Gurobi"] = false
end

try
    using JSON
    println("  ✓ JSON")
    test_results["JSON"] = true
catch e
    println("  ✗ JSON: $e")
    test_results["JSON"] = false
end

# Test encryption packages
println("\n[2] Testing encryption packages...")
try
    using Primes
    p = nextprime(2^10)
    println("  ✓ Primes (found prime: $p)")
    test_results["Primes"] = true
catch e
    println("  ✗ Primes: $e")
    test_results["Primes"] = false
end

try
    using Random
    println("  ✓ Random")
    test_results["Random"] = true
catch e
    println("  ✗ Random: $e")
    test_results["Random"] = false
end

# Test Gurobi environment
println("\n[3] Testing Gurobi environment...")
try
    env = Gurobi.Env()
    println("  ✓ Gurobi environment created successfully")
    test_results["Gurobi_env"] = true
catch e
    println("  ✗ Gurobi environment failed: $e")
    println("  Note: Make sure Gurobi is licensed (free academic license available)")
    test_results["Gurobi_env"] = false
end

# Summary
println("\n" * "="^80)
println("Final Summary")
println("="^80)

all_passed = all(values(test_results))

if all_passed
    println("\n✓ ALL TESTS PASSED")
    println("\nYou can now run:")
    println("  - Centralized: python evaluate_edge_opf.py --mode centralized --case testbeds/pglib_opf_case14_ieee.m")
    println("  - Distributed: python evaluate_edge_opf.py --mode distributed --servers 14 --case testbeds/pglib_opf_case14_ieee.m")
    println("  - Paillier:    python evaluate_edge_opf.py --mode paillier --case testbeds/pglib_opf_case14_ieee.m")
else
    println("\n⚠ SOME TESTS FAILED")
    println("\nFailed tests:")
    for (name, result) in test_results
        if !result
            println("  - $name")
        end
    end
    println("\nPlease check:")
    println("  1. Gurobi is installed and licensed (https://www.gurobi.com/)")
    println("  2. Environment variables are set correctly")
    println("  3. Run: julia> using Pkg; Pkg.build(\"Gurobi\")")
end

println("\n" * "="^80)
