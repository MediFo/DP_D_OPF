#!/usr/bin/env julia

"""
Test script to verify Gurobi optimization setup
Run this BEFORE running main.jl to ensure everything is configured correctly
"""

println("="^80)
println("Gurobi Optimization Setup Verification")
println("="^80)

# Test 1: Check Julia version
println("\n[1/6] Checking Julia version...")
println("Julia version: $(VERSION)")
if VERSION >= v"1.6"
    println("✓ Julia version is compatible")
else
    println("✗ Julia version should be >= 1.6")
end

# Test 2: Check required packages
println("\n[2/6] Checking required packages...")
required_packages = ["PowerModels", "JuMP", "Gurobi", "DataFrames", "LinearAlgebra", "CSV", "Distributions"]
missing_packages = String[]

for pkg in required_packages
    try
        eval(Meta.parse("using $pkg"))
        println("✓ $pkg is installed")
    catch e
        println("✗ $pkg is NOT installed")
        push!(missing_packages, pkg)
    end
end

if !isempty(missing_packages)
    println("\n❌ Missing packages detected!")
    println("Install them with:")
    println("using Pkg")
    for pkg in missing_packages
        println("Pkg.add(\"$pkg\")")
    end
    exit(1)
end

# Test 3: Check Gurobi license
println("\n[3/6] Checking Gurobi license...")
try
    using Gurobi
    env = Gurobi.Env()
    println("✓ Gurobi license is valid")
    println("  License file: \$(get(ENV, \"GRB_LICENSE_FILE\", \"default location\"))")
catch e
    println("✗ Gurobi license error:")
    println("  $e")
    println("\nPlease ensure:")
    println("  1. Gurobi is installed: https://www.gurobi.com/downloads/")
    println("  2. License file is set: export GRB_LICENSE_FILE=/path/to/gurobi.lic")
    println("  3. License is valid (not expired)")
    exit(1)
end

# Test 4: Check testbed files
println("\n[4/6] Checking testbed files...")
if isfile("testbeds/pglib_opf_case14_ieee.m")
    println("✓ Test case file exists")
else
    println("✗ testbeds/pglib_opf_case14_ieee.m not found")
    exit(1)
end

# Test 5: Check script files
println("\n[5/6] Checking script files...")
script_files = [
    "scripts/data_manager.jl",
    "scripts/fun_centralized_OPF.jl",
    "scripts/fun_compute_sensitivity.jl",
    "scripts/fun_consensus_update.jl",
    "scripts/fun_dual_update.jl",
    "scripts/fun_residual_update.jl",
    "scripts/fun_reveal_load.jl",
    "scripts/fun_voltage_update.jl"
]

all_exist = true
for script in script_files
    if isfile(script)
        println("✓ $script")
    else
        println("✗ $script NOT FOUND")
        all_exist = false
    end
end

if !all_exist
    println("\n❌ Some script files are missing!")
    exit(1)
end

# Test 6: Simple Gurobi optimization test
println("\n[6/6] Running simple Gurobi optimization test...")
try
    using JuMP, Gurobi
    env = Gurobi.Env()
    model = Model(() -> Gurobi.Optimizer(env))
    set_silent(model)
    @variable(model, x >= 0)
    @variable(model, y >= 0)
    @constraint(model, x + y <= 1)
    @objective(model, Max, x + 2y)
    optimize!(model)

    if termination_status(model) == MOI.OPTIMAL
        obj_val = objective_value(model)
        println("✓ Simple optimization successful")
        println("  Objective value: $obj_val")
        println("  x = $(value(x)), y = $(value(y))")
    else
        println("✗ Optimization failed with status: $(termination_status(model))")
        exit(1)
    end
catch e
    println("✗ Optimization test failed:")
    println("  $e")
    exit(1)
end

println("\n" * "="^80)
println("✅ ALL CHECKS PASSED!")
println("="^80)
println("\nYou can now run: julia main.jl")
println()
