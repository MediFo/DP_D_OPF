using PowerModels
using DataStructures: SortedDict
using JuMP
# Solver: Gurobi (COMMERCIAL) - Using Gurobi for optimization
using Gurobi
using DataFrames
using LinearAlgebra
using CSV
using Distributions
using JSON
using Dates

# load scripts
include("scripts/data_manager.jl")
include("scripts/fun_centralized_OPF.jl")
include("scripts/fun_compute_sensitivity.jl")
include("scripts/fun_consensus_update.jl")
include("scripts/fun_dual_update.jl")
include("scripts/fun_residual_update.jl")
include("scripts/fun_reveal_load.jl")
include("scripts/fun_voltage_update.jl")

"""
Main OPF execution function that can run in centralized or distributed mode
Supports config file input for edge simulation integration
"""
function run_opf(config::Dict)
    # Parse configuration
    caseID = get(config, "caseID", "testbeds/pglib_opf_case14_ieee.m")
    mode = get(config, "mode", "distributed")  # "centralized" or "distributed"

    # ADMM parameters
    ν̅ = get(config, "max_iterations", 15000)
    ρ = get(config, "rho", 1e3)
    γ = get(config, "tolerance", 1e-2)

    # Differential privacy parameters
    ϵ = get(config, "epsilon", 1.0)
    α = get(config, "alpha", 0.1)
    method = get(config, "method", "PVP")

    # Node ID for distributed mode
    node_id = get(config, "node_id", 1)

    println("="^60)
    println("Starting OPF Computation")
    println("Mode: $mode")
    println("Case: $caseID")
    println("Method: $method")
    if mode == "distributed"
        println("Node ID: $node_id")
    end
    println("="^60)

    # load data
    (gen,bus,line,B,refbus)=load_data(caseID)

    # Initialize Gurobi environment
    gurobi_env = Gurobi.Env()

    # Track timing
    start_time = time()
    iteration_times = Float64[]
    residuals = Float64[]

    # solve the centralized OPF problem
    println("Solving centralized OPF...")
    (cost_c,dispatch_c,power_flow_c)=OPF_centralized(gen,bus,line,B,refbus,gurobi_env)

    # create and specify ADMM and model parameters
    μ = zeros(length(bus),length(bus),ν̅)
    μ̃ = zeros(length(bus),length(bus),ν̅)
    θ = zeros(length(bus),length(bus),ν̅)
    θ̃ = zeros(length(bus),length(bus),ν̅)
    θ̅ = zeros(length(bus),ν̅)
    d = zeros(length(bus),length(bus),ν̅)
    p = zeros(length(gen),ν̅)
    l = zeros(length(bus),ν̅)
    cost = zeros(1)
    ν̃ = zeros(1)

    # compute sensitivities
    println("Computing sensitivities...")
    Δ_op=sensitivities(gen,bus,line,B,refbus,ρ,method,α,gurobi_env)

    # Generate noise
    ξ = zeros(length(bus),length(bus))
    for i in 1:length(bus)
        for j in bus[i].N
            ξ[i,j,:] = rand(Laplace(0,Δ_op[i,j]/ϵ),1)
        end
    end

    # solve OPF using ADMM
    println("Starting ADMM iterations...")
    for ν in 2:ν̅
        iter_start = time()

        if method == "DVP"
            μ̃[:,:,ν] = μ[:,:,ν-1] .+ ξ[:,:]
            (θ[:,:,ν],cost[1],p[:,ν],l[:,ν]) = update_θ(gen,bus,line,B,refbus,μ̃[:,:,ν],θ̅[:,ν-1],ρ,gurobi_env)
            d[:,:,ν] = reveal_load(bus,gen,B,ρ,μ[:,:,ν-1],θ̅[:,ν-1],θ[:,:,ν])
            θ̅[:,ν]=update_θ̅(bus,θ[:,:,ν])
            μ[:,:,ν]=update_μ(bus,ρ,θ[:,:,ν],θ̅[:,ν],μ[:,:,ν-1])
            Γ = residual(bus,θ[:,:,ν],θ̅[:,ν])
        end
        if method == "PVP"
            (θ[:,:,ν],cost[1],p[:,ν],l[:,ν]) = update_θ(gen,bus,line,B,refbus,μ[:,:,ν-1],θ̅[:,ν-1],ρ,gurobi_env)
            θ̃[:,:,ν] = θ[:,:,ν] .+ ξ[:,:]
            d[:,:,ν] = reveal_load(bus,gen,B,ρ,μ[:,:,ν-1],θ̅[:,ν-1],θ̃[:,:,ν])
            θ̅[:,ν]=update_θ̅(bus,θ̃[:,:,ν])
            μ[:,:,ν]=update_μ(bus,ρ,θ̃[:,:,ν],θ̅[:,ν],μ[:,:,ν-1])
            Γ = residual(bus,θ̃[:,:,ν],θ̅[:,ν])
        end

        iter_time = time() - iter_start
        push!(iteration_times, iter_time)
        push!(residuals, Γ)

        ν % 100 == 0 ? println("ν --- $(ν) ... res --- $(round(Γ,digits=5)) ... time --- $(round(iter_time*1000, digits=2))ms") : NaN
        if Γ <= γ || ν == ν̅
            ν̃[1] = ν
            println("ADMM terminates at iteration $(ν)")
            break
        end
    end

    total_time = time() - start_time

    # prepare results
    load_inference = DataFrame(node=Any[],actual=Any[],observed=Any[])
    for i in 1:length(bus)
        push!(load_inference,[i,bus[i].d,d[i,i,Int(ν̃[1])]])
    end
    node_dispatch = DataFrame(node=Any[],non_private=Any[],private=Any[])
    for i in 1:length(bus)
        bus[i].type == 1 ? push!(node_dispatch,[i,dispatch_c[bus[i].G[1],3],p[bus[i].G[1],Int(ν̃[1])]]) : NaN
        bus[i].type == 2 ? push!(node_dispatch,[i,dispatch_c[i,4],l[i,Int(ν̃[1])]]) : NaN
    end
    flow_dispatch = DataFrame(line=Any[], b_f = Any[], b_t = Any[], flow_non_private = Any[], flow_private = Any[])
    for l in 1:length(line)
        push!(flow_dispatch,[l,line[l].b_f,line[l].b_t,round(line[l].β * (dispatch_c[line[l].b_f,6]-dispatch_c[line[l].b_t,6]),digits=3),round(line[l].β * (θ̅[line[l].b_f,Int(ν̃[1])]-θ̅[line[l].b_t,Int(ν̃[1])]),digits=3)])
    end

    # print results
    println("="^60)
    println("OPF Computation Complete")
    println("Total time: $(round(total_time, digits=3))s")
    println("Iterations: $(Int(ν̃[1]))")
    println("Optimality loss: $(round(abs(cost_c-cost[1])/cost_c*100, digits=4))%")
    println("="^60)
    println("Comparison of the non-private and differentially private load inference")
    println(load_inference)
    println("Comparison of the optimal and differentially private node dispatch")
    println(node_dispatch)
    println("Comparison of the optimal and differentially private flow dispatch")
    println(flow_dispatch)

    # Return results dictionary (for edge simulation integration)
    results = Dict(
        "mode" => mode,
        "node_id" => node_id,
        "total_time_s" => total_time,
        "iterations" => Int(ν̃[1]),
        "avg_iteration_time_ms" => mean(iteration_times) * 1000,
        "centralized_cost" => cost_c,
        "final_cost" => cost[1],
        "optimality_loss_percent" => abs(cost_c-cost[1])/cost_c*100,
        "final_residual" => residuals[end],
        "iteration_times" => iteration_times,
        "residuals" => residuals,
        "config" => config
    )

    return results
end

"""
Entry point for command-line execution
"""
function main()
    println("Julia working directory: $(pwd())")

    # Parse command line arguments
    if length(ARGS) > 0
        config_file = ARGS[1]
        println("Loading config from: $config_file")

        if !isfile(config_file)
            error("Config file not found: $config_file")
        end

        config = JSON.parsefile(config_file)
    else
        # Default configuration for standalone execution
        println("No config file provided, using defaults")
        config = Dict(
            "caseID" => "testbeds/pglib_opf_case14_ieee.m",
            "mode" => "distributed",
            "node_id" => 1,
            "max_iterations" => 15000,
            "rho" => 1e3,
            "tolerance" => 1e-2,
            "epsilon" => 1.0,
            "alpha" => 0.1,
            "method" => "PVP"
        )
    end

    # Run OPF computation
    results = run_opf(config)

    # Save results to JSON if called from edge simulation
    if length(ARGS) > 0
        mode = get(config, "mode", "distributed")
        node_id = get(config, "node_id", 1)

        # Determine output directory and file
        if mode == "centralized"
            output_dir = joinpath(pwd(), "edge", "results")
            output_file = joinpath(output_dir, "centralized_results.json")
        else
            output_dir = joinpath(pwd(), "edge", "results")
            output_file = joinpath(output_dir, "node_$(node_id)_results.json")
        end

        if !isdir(output_dir)
            mkpath(output_dir)
        end

        open(output_file, "w") do f
            JSON.print(f, results, 4)
        end

        println("Results saved to: $output_file")
    end

    return results
end

# Run if executed directly
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
