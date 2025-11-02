"""
OPF Edge Node - Distributed ADMM for Edge Computing Evaluation
This script runs a single node's OPF computation in a distributed setting
Modified from main.jl for edge device evaluation
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
using Gurobi
using DataFrames
using LinearAlgebra
using CSV
using Distributions
using JSON
using Dates

# Get the directory where this script is located
script_dir = @__DIR__
# Navigate to project root (2 levels up from edge/scripts/)
project_root = abspath(joinpath(script_dir, "..", ".."))
scripts_dir = joinpath(project_root, "scripts")

# Load scripts from project root - using absolute paths for cross-platform compatibility
include(joinpath(scripts_dir, "data_manager.jl"))
include(joinpath(scripts_dir, "fun_centralized_OPF.jl"))
include(joinpath(scripts_dir, "fun_compute_sensitivity.jl"))
include(joinpath(scripts_dir, "fun_consensus_update.jl"))
include(joinpath(scripts_dir, "fun_dual_update.jl"))
include(joinpath(scripts_dir, "fun_residual_update.jl"))
include(joinpath(scripts_dir, "fun_reveal_load.jl"))
include(joinpath(scripts_dir, "fun_voltage_update.jl"))

"""
Run OPF computation for a specific node in distributed ADMM setting
"""
function run_node_opf(node_id::Int, config::Dict)
    println("="^60)
    println("Starting OPF computation for Node $node_id")
    println("Configuration: ", config)
    println("="^60)

    # Load data - convert path to absolute if relative
    caseID = get(config, "caseID", joinpath(project_root, "testbeds", "pglib_opf_case14_ieee.m"))
    if !isabs(caseID)
        caseID = joinpath(project_root, caseID)
    end

    println("Loading case: $caseID")
    if !isfile(caseID)
        error("Case file not found: $caseID")
    end

    (gen, bus, line, B, refbus) = load_data(caseID)

    # Initialize Gurobi environment
    gurobi_env = Gurobi.Env()

    # ADMM parameters
    ν̅ = get(config, "max_iterations", 1000)
    ρ = get(config, "rho", 1e3)
    γ = get(config, "tolerance", 1e-2)

    # Differential privacy parameters
    ϵ = get(config, "epsilon", 1.0)
    α = get(config, "alpha", 0.1)
    method = get(config, "method", "PVP")

    # Initialize variables
    μ = zeros(length(bus), length(bus), ν̅)
    μ̃ = zeros(length(bus), length(bus), ν̅)
    θ = zeros(length(bus), length(bus), ν̅)
    θ̃ = zeros(length(bus), length(bus), ν̅)
    θ̅ = zeros(length(bus), ν̅)
    d = zeros(length(bus), length(bus), ν̅)
    p = zeros(length(gen), ν̅)
    l = zeros(length(bus), ν̅)
    cost = zeros(1)
    ν̃ = zeros(1)

    # Compute sensitivities
    println("Computing sensitivities...")
    Δ_op = sensitivities(gen, bus, line, B, refbus, ρ, method, α)

    # Generate noise
    ξ = zeros(length(bus), length(bus))
    for i in 1:length(bus)
        for j in bus[i].N
            ξ[i,j] = rand(Laplace(0, Δ_op[i,j]/ϵ), 1)[1]
        end
    end

    # Track metrics
    iteration_times = Float64[]
    residuals = Float64[]

    println("Starting ADMM iterations...")
    start_time = time()

    # ADMM iterations
    for ν in 2:ν̅
        iter_start = time()

        if method == "DVP"
            μ̃[:,:,ν] = μ[:,:,ν-1] .+ ξ[:,:]
            (θ[:,:,ν], cost[1], p[:,ν], l[:,ν]) = update_θ(gen, bus, line, B, refbus, μ̃[:,:,ν], θ̅[:,ν-1], ρ)
            d[:,:,ν] = reveal_load(bus, gen, B, ρ, μ[:,:,ν-1], θ̅[:,ν-1], θ[:,:,ν])
            θ̅[:,ν] = update_θ̅(bus, θ[:,:,ν])
            μ[:,:,ν] = update_μ(bus, ρ, θ[:,:,ν], θ̅[:,ν], μ[:,:,ν-1])
            Γ = residual(bus, θ[:,:,ν], θ̅[:,ν])
        end

        if method == "PVP"
            (θ[:,:,ν], cost[1], p[:,ν], l[:,ν]) = update_θ(gen, bus, line, B, refbus, μ[:,:,ν-1], θ̅[:,ν-1], ρ)
            θ̃[:,:,ν] = θ[:,:,ν] .+ ξ[:,:]
            d[:,:,ν] = reveal_load(bus, gen, B, ρ, μ[:,:,ν-1], θ̅[:,ν-1], θ̃[:,:,ν])
            θ̅[:,ν] = update_θ̅(bus, θ̃[:,:,ν])
            μ[:,:,ν] = update_μ(bus, ρ, θ̃[:,:,ν], θ̅[:,ν], μ[:,:,ν-1])
            Γ = residual(bus, θ̃[:,:,ν], θ̅[:,ν])
        end

        iter_time = time() - iter_start
        push!(iteration_times, iter_time)
        push!(residuals, Γ)

        if ν % 100 == 0
            println("ν --- $(ν) ... res --- $(round(Γ, digits=5)) ... time --- $(round(iter_time*1000, digits=2))ms")
        end

        if Γ <= γ || ν == ν̅
            ν̃[1] = ν
            println("ADMM converged at iteration $(ν)")
            break
        end
    end

    total_time = time() - start_time

    println("="^60)
    println("OPF Computation completed for Node $node_id")
    println("Total time: $(round(total_time, digits=3))s")
    println("Iterations: $(Int(ν̃[1]))")
    println("="^60)

    # Prepare results
    results = Dict(
        "node_id" => node_id,
        "total_time_s" => total_time,
        "iterations" => Int(ν̃[1]),
        "avg_iteration_time_ms" => mean(iteration_times) * 1000,
        "final_cost" => cost[1],
        "final_residual" => residuals[end],
        "iteration_times" => iteration_times,
        "residuals" => residuals,
        "config" => config
    )

    return results
end

"""
Main entry point for standalone execution
"""
function main()
    println("Julia working directory: $(pwd())")
    println("Script directory: $script_dir")
    println("Project root: $project_root")

    # Parse command line arguments
    if length(ARGS) > 0
        config_file = ARGS[1]
        if !isabs(config_file)
            config_file = abspath(config_file)
        end
        println("Loading config from: $config_file")

        if !isfile(config_file)
            error("Config file not found: $config_file")
        end

        config = JSON.parsefile(config_file)
        node_id = get(config, "node_id", 1)
    else
        # Default configuration
        node_id = 1
        config = Dict(
            "node_id" => node_id,
            "caseID" => joinpath(project_root, "testbeds", "pglib_opf_case14_ieee.m"),
            "max_iterations" => 1000,
            "rho" => 1e3,
            "tolerance" => 1e-2,
            "epsilon" => 1.0,
            "alpha" => 0.1,
            "method" => "PVP"
        )
    end

    # Run OPF computation
    results = run_node_opf(node_id, config)

    # Save results
    output_dir = joinpath(project_root, "edge", "results")
    if !isdir(output_dir)
        mkpath(output_dir)
    end

    output_file = joinpath(output_dir, "node_$(node_id)_results.json")
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
