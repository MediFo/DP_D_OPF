"""
Centralized OPF for Edge Computing Evaluation
Simplified version for benchmarking on edge devices
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
using Gurobi
using DataFrames
using LinearAlgebra
using CSV
using JSON
using Dates

# Load scripts from parent directory
include("../../scripts/data_manager.jl")
include("../../scripts/fun_centralized_OPF.jl")

"""
Run centralized OPF computation
"""
function run_centralized_opf(config::Dict)
    println("="^60)
    println("Starting Centralized OPF Computation")
    println("Configuration: ", config)
    println("="^60)

    # Load data
    caseID = get(config, "caseID", "../../testbeds/pglib_opf_case14_ieee.m")
    (gen, bus, line, B, refbus) = load_data(caseID)

    # Initialize Gurobi environment
    gurobi_env = Gurobi.Env()

    println("Solving centralized OPF...")
    start_time = time()

    # Solve the centralized OPF problem
    (cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus)

    total_time = time() - start_time

    println("="^60)
    println("Centralized OPF Computation completed")
    println("Total time: $(round(total_time, digits=3))s")
    println("Optimal cost: $cost_c")
    println("="^60)

    # Prepare results
    results = Dict(
        "type" => "centralized",
        "total_time_s" => total_time,
        "optimal_cost" => cost_c,
        "num_generators" => length(gen),
        "num_buses" => length(bus),
        "num_lines" => length(line),
        "config" => config,
        "timestamp" => string(now())
    )

    return results
end

"""
Main entry point
"""
function main()
    # Parse command line arguments
    if length(ARGS) > 0
        config_file = ARGS[1]
        config = JSON.parsefile(config_file)
    else
        # Default configuration
        config = Dict(
            "caseID" => "../../testbeds/pglib_opf_case14_ieee.m"
        )
    end

    # Run centralized OPF
    results = run_centralized_opf(config)

    # Save results
    output_dir = "../../edge/results"
    if !isdir(output_dir)
        mkpath(output_dir)
    end

    output_file = joinpath(output_dir, "centralized_results.json")
    open(output_file, "w") do f
        JSON.print(f, results, 4)
    end

    println("Results saved to: $output_file")

    return results
end

# Run if executed directly
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
