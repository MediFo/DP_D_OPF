"""
Boyd's Consensus ADMM with Paillier Homomorphic Encryption for DC-OPF
Combines the ADMM formulation from DP_D_OPF with Paillier encryption
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
# using Gurobi  # Commercial solver (commented out)
using Ipopt     # Free nonlinear solver (recommended for DC-OPF with quadratic costs)
# using GLPK    # Free linear solver (alternative, but doesn't support quadratic objectives)
using DataFrames
using LinearAlgebra
using CSV
using Printf

# Load existing scripts
include("scripts/data_manager.jl")
include("scripts/fun_centralized_OPF.jl")
include("scripts/paillier_crypto.jl")

# ══════════════════════════════════════════════════════════════════════════════
# ADMM UPDATE FUNCTIONS WITH PAILLIER ENCRYPTION
# ══════════════════════════════════════════════════════════════════════════════

"""
Primal update: Each node solves local OPF (same as original, but returns both encrypted and plain)
"""
function update_θ_encrypted(gen, bus, line, B, refbus, μ_plain, θ̅_plain, ρ, public_key)
    Ng = length(gen)
    Nb = length(bus)
    Nl = length(line)

    # Free solver (Ipopt)
    model = Model(optimizer_with_attributes(Ipopt.Optimizer,
                                           "print_level" => 0,
                                           "sb" => "yes"))  # Suppress banner

    # Commercial solver (Gurobi) - Uncomment if you have a license
    # model = Model(optimizer_with_attributes(() -> Gurobi.Optimizer(gurobi_env),
    #                                        "Method" => 2,
    #                                        "Presolve" => 1,
    #                                        "OutputFlag" => 0))

    @variable(model, p[1:Ng])
    @variable(model, θ[1:Nb, 1:Nb])
    @variable(model, l[1:Nb])

    # Generator limits
    @constraint(model, ϕ̲[i=1:Nb, g=bus[i].G], gen[g].p̲ <= p[g])
    @constraint(model, ϕ̅[i=1:Nb, g=bus[i].G], p[g] <= gen[g].p̅)

    # Load flexibility limits
    @constraint(model, ψ̲[i=1:Nb], -bus[i].d <= l[i])
    @constraint(model, ψ̅[i=1:Nb], l[i] <= bus[i].d)

    # Power flow limits
    @constraint(model, η̲[i=1:Nb, l=bus[i].Λ],
                -line[l].f̅ <= line[l].β * (θ[i, line[l].b_f] - θ[i, line[l].b_t]))
    @constraint(model, η̅[i=1:Nb, l=bus[i].Λ],
                line[l].β * (θ[i, line[l].b_f] - θ[i, line[l].b_t]) <= line[l].f̅)

    # Power balance
    @constraint(model, λ[i=1:Nb],
                sum(B[i, j] * θ[i, j] for j in bus[i].N) ==
                sum(p[g] for g in bus[i].G) - bus[i].d + l[i])

    # Reference bus
    @constraint(model, κ[i=1:Nb], θ[i, refbus] == 0)

    # Generator buses have no load flexibility
    for i in 1:Nb
        if bus[i].type == 1
            @constraint(model, l[i] == 0)
        end
    end

    # Objective: generation cost + load cost + ADMM augmented Lagrangian
    @objective(model, Min,
               sum(gen[g].c2 * p[g]^2 + gen[g].c1 * p[g] + gen[g].c0 for g in 1:Ng) +
               sum(bus[i].c * l[i]^2 for i in 1:Nb) -
               sum(μ_plain[i, j] * θ[i, j] for i in 1:Nb for j in bus[i].N) +
               ρ / 2 * sum((θ̅_plain[j] - θ[i, j])^2 for i in 1:Nb for j in bus[i].N))

    optimize!(model)

    # Extract solution
    θ_sol = JuMP.value.(θ)
    p_sol = JuMP.value.(p)
    l_sol = JuMP.value.(l)
    cost = sum(gen[g].c2 * p_sol[g]^2 + gen[g].c1 * p_sol[g] + gen[g].c0 for g in 1:Ng) +
           sum(bus[i].c * l_sol[i]^2 for i in 1:Nb)

    # Encrypt θ values for sharing
    θ_enc = Matrix{Union{EncryptedNumber, Nothing}}(nothing, Nb, Nb)
    for i in 1:Nb
        for j in bus[i].N
            θ_enc[i, j] = encrypt(public_key, θ_sol[i, j])
        end
    end

    return θ_sol, θ_enc, cost, p_sol, l_sol
end

"""
Consensus update: Average encrypted values homomorphically
θ̅[i] = (1/|N_i|) * Σ_{j ∈ N_i} θ[j,i]
"""
function update_θ̅_encrypted(bus, θ_enc, public_key, private_key)
    Nb = length(bus)
    θ̅_enc = Vector{Union{EncryptedNumber, Nothing}}(nothing, Nb)
    θ̅_plain = zeros(Nb)

    for i in 1:Nb
        # Collect encrypted values from neighbors
        enc_values = EncryptedNumber[]
        for j in bus[i].N
            if θ_enc[j, i] !== nothing
                push!(enc_values, θ_enc[j, i])
            end
        end

        if !isempty(enc_values)
            # Homomorphic average
            θ̅_enc[i] = encrypted_average(enc_values)
            # Decrypt for use in next iteration
            θ̅_plain[i] = decrypt(public_key, private_key, θ̅_enc[i])
        end
    end

    return θ̅_plain, θ̅_enc
end

"""
Dual update: μ[i,j] = μ[i,j] + ρ * (θ[i,j] - θ̅[j])
Uses plaintext values (dual variables are kept private locally)
"""
function update_μ_encrypted(bus, ρ, θ_plain, θ̅_plain, μ)
    Nb = length(bus)
    μ_new = zeros(Nb, Nb)

    for i in 1:Nb
        for j in bus[i].N
            μ_new[i, j] = μ[i, j] + ρ * (θ_plain[i, j] - θ̅_plain[j])
        end
    end

    return μ_new
end

"""
Compute residual for convergence check
"""
function compute_residual(bus, θ_plain, θ̅_plain)
    Nb = length(bus)
    Γ = sum(abs(θ̅_plain[j] - θ_plain[i, j]) for i in 1:Nb for j in bus[i].N)
    return Γ
end

# ══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" BOYD'S CONSENSUS ADMM + PAILLIER ENCRYPTION FOR DC-OPF")
println("="^80 * "\n")

# Load network data
println("[1/6] Loading network data...")
# Try IEEE 33-bus first, fall back to IEEE 14-bus
caseID_33 = "testbeds/pglib_opf_case33_bw.m"
caseID_14 = "testbeds/pglib_opf_case14_ieee.m"

if isfile(caseID_33)
    caseID = caseID_33
    println("  ✓ Using IEEE 33-Bus network")
else
    caseID = caseID_14
    println("  ⚠  IEEE 33-Bus not found, using IEEE 14-Bus network")
    println("  ℹ  To use IEEE 33-Bus, add pglib_opf_case33_bw.m to testbeds/")
end

(gen, bus, line, B, refbus) = load_data(caseID)
println("  ✓ Network loaded: $(length(bus)) buses, $(length(gen)) generators, $(length(line)) lines")

# Initialize Gurobi environment (commented out - using free solver instead)
# global gurobi_env = Gurobi.Env()

# Solve centralized OPF for comparison
println("\n[2/6] Solving centralized OPF (baseline)...")
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus)
println("  ✓ Centralized cost: \$", round(cost_c, digits=2))

# Generate Paillier keys
println("\n[3/6] Generating Paillier encryption keys...")
key_length = 1024  # Use 1024-bit for faster computation (2048-bit for production)
start_time = time()
keypair = generate_paillier_keypair(key_length)
keygen_time = time() - start_time
println("  ✓ Keys generated in ", round(keygen_time, digits=2), "s ($(key_length)-bit)")

# Test encryption
println("\n[4/6] Testing Paillier homomorphic operations...")
test_enc1 = encrypt(keypair.public_key, 10.5)
test_enc2 = encrypt(keypair.public_key, 20.3)
test_sum = test_enc1 + test_enc2
test_result = decrypt(keypair.public_key, keypair.private_key, test_sum)
println("  ✓ E(10.5) + E(20.3) = ", round(test_result, digits=2), " (expected: 30.8)")

# Initialize ADMM parameters
println("\n[5/6] Initializing ADMM parameters...")
ν̅ = 100  # Maximum iterations (reduce for testing with encryption)
ρ = 50.0   # ADMM penalty parameter
γ = 1e-2   # Convergence tolerance

Nb = length(bus)
Ng = length(gen)

μ = zeros(Nb, Nb)
θ_plain = zeros(Nb, Nb)
θ̅_plain = zeros(Nb)
p = zeros(Ng, ν̅)
l = zeros(Nb, ν̅)
cost_history = zeros(ν̅)
residual_history = zeros(ν̅)

println("  ✓ ADMM parameters set: ρ = $ρ, max_iter = $ν̅, tol = $γ")

# Run ADMM with Paillier encryption
println("\n[6/6] Running Boyd's Consensus ADMM with Paillier encryption...")
println("\n" * "─"^80)
@printf("%-6s %-15s %-15s %-15s %-10s\n", "Iter", "Cost (\$)", "Residual", "Improvement", "Time(s)")
println("─"^80)

converged = false
final_iter = ν̅

for ν in 1:ν̅
    global μ, θ_plain, θ̅_plain, final_iter, converged  # Declare global variables modified in loop

    iter_start = time()

    # Step 1: Primal update (each agent solves local OPF and encrypts solution)
    θ_plain, θ_enc, cost_history[ν], p[:, ν], l[:, ν] =
        update_θ_encrypted(gen, bus, line, B, refbus, μ, θ̅_plain, ρ, keypair.public_key)

    # Step 2: Consensus update (homomorphic averaging of encrypted values)
    θ̅_plain, θ̅_enc =
        update_θ̅_encrypted(bus, θ_enc, keypair.public_key, keypair.private_key)

    # Step 3: Dual update (local, no encryption needed)
    μ = update_μ_encrypted(bus, ρ, θ_plain, θ̅_plain, μ)

    # Step 4: Compute residual
    residual_history[ν] = compute_residual(bus, θ_plain, θ̅_plain)

    iter_time = time() - iter_start

    # Print progress
    if ν == 1 || ν % 10 == 0 || residual_history[ν] <= γ
        improvement = ν > 1 ? residual_history[ν-1] - residual_history[ν] : 0.0
        @printf("%-6d \$%-14.2f %-15.6f %-15.6f %-10.3f\n",
                ν, cost_history[ν], residual_history[ν], improvement, iter_time)
    end

    # Check convergence
    if residual_history[ν] <= γ
        println("─"^80)
        println("✅ CONVERGED at iteration $ν")
        final_iter = ν
        converged = true
        break
    end
end

if !converged
    println("─"^80)
    println("⚠  Maximum iterations reached without convergence")
end

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" RESULTS SUMMARY")
println("="^80 * "\n")

println("Convergence:")
println("  Status: ", converged ? "✅ Converged" : "⚠  Not converged")
println("  Iterations: $final_iter / $ν̅")
println("  Final residual: ", round(residual_history[final_iter], digits=6))
println()

println("Cost Comparison:")
println("  Centralized OPF: \$", round(cost_c, digits=2))
println("  ADMM+Paillier:   \$", round(cost_history[final_iter], digits=2))
cost_diff = abs(cost_c - cost_history[final_iter])
cost_pct = cost_diff / cost_c * 100
println("  Difference:      \$", round(cost_diff, digits=2), " (", round(cost_pct, digits=3), "%)")
println()

# Node dispatch comparison
println("Node Dispatch Comparison (first 10 buses):")
println("─"^80)
@printf("%-6s %-12s %-15s %-15s %-15s\n", "Bus", "Type", "Centralized", "ADMM+Paillier", "Difference")
println("─"^80)
for i in 1:min(10, Nb)
    if bus[i].type == 1 && !isempty(bus[i].G)  # Generator bus
        cent_val = dispatch_c[bus[i].G[1], 3]
        admm_val = p[bus[i].G[1], final_iter]
        diff_val = abs(cent_val - admm_val)
        @printf("%-6d %-12s %-15.3f %-15.3f %-15.3f\n",
                i, "Generator", cent_val, admm_val, diff_val)
    elseif bus[i].type == 2  # Load bus
        cent_val = dispatch_c[i, 4]
        admm_val = l[i, final_iter]
        diff_val = abs(cent_val - admm_val)
        @printf("%-6d %-12s %-15.3f %-15.3f %-15.3f\n",
                i, "Load", cent_val, admm_val, diff_val)
    end
end
println("─"^80)

println("\n" * "="^80)
println(" ✅ ADMM WITH PAILLIER ENCRYPTION COMPLETED")
println("="^80 * "\n")
