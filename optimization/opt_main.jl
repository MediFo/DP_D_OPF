"""
ADMM OPF with Paillier Homomorphic Encryption
Based on original DP_D_OPF formulation (DENSE matrices, not sparse)

Uses:
- scripts/data_manager.jl
- scripts/fun_centralized_OPF.jl
- scripts/paillier_crypto.jl
- Original ADMM functions (fun_voltage_update.jl, fun_consensus_update.jl, etc.)
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
using Printf

# ═══════════════════════════════════════════════════════════════════════════
# Load required scripts
# ═══════════════════════════════════════════════════════════════════════════
println("\n[INIT] Loading optimization scripts...")

include("scripts/data_manager.jl")
println("  ✓ data_manager.jl")

include("scripts/fun_centralized_OPF.jl")
println("  ✓ fun_centralized_OPF.jl")

include("scripts/paillier_crypto.jl")
println("  ✓ paillier_crypto.jl")

include("scripts/fun_voltage_update.jl")
println("  ✓ fun_voltage_update.jl")

include("scripts/fun_consensus_update.jl")
println("  ✓ fun_consensus_update.jl")

include("scripts/fun_dual_update.jl")
println("  ✓ fun_dual_update.jl")

include("scripts/fun_residual_update.jl")
println("  ✓ fun_residual_update.jl")

println("[INIT] ✓ All scripts loaded successfully\n")

# ═══════════════════════════════════════════════════════════════════════════
# Encryption helper functions for DENSE formulation
# ═══════════════════════════════════════════════════════════════════════════

"""
Encrypt dense θ matrix (Nb×Nb)
Returns: encrypted matrix of same shape
"""
function encrypt_θ_dense(public_key::PaillierPublicKey, bus, θ::Matrix{Float64})
    Nb = length(bus)
    θ_enc = Matrix{EncryptedNumber}(undef, Nb, Nb)

    for i in 1:Nb
        for j in bus[i].N  # Only encrypt neighbor values
            θ_enc[i,j] = encrypt(public_key, θ[i,j])
        end
    end

    return θ_enc
end

"""
Homomorphic consensus update for DENSE formulation
θ̅[i] = (1/|N(i)|) * Σ_{j∈N(i)} θ[j,i]
"""
function update_θ̅_homomorphic_dense(public_key::PaillierPublicKey,
                                      private_key::PaillierPrivateKey,
                                      bus, θ_enc::Matrix{EncryptedNumber})
    Nb = length(bus)
    θ̅ = zeros(Nb)

    for i in 1:Nb
        # Collect encrypted neighbors: E(θ[j,i]) for j ∈ N(i)
        enc_neighbors = EncryptedNumber[]
        for j in bus[i].N
            push!(enc_neighbors, θ_enc[j,i])
        end

        if !isempty(enc_neighbors)
            # Homomorphic average
            θ̅_enc_i = encrypted_average(enc_neighbors)
            # Decrypt for local use
            θ̅[i] = decrypt(public_key, private_key, θ̅_enc_i)
        end
    end

    return θ̅
end

# ═══════════════════════════════════════════════════════════════════════════
# Main execution
# ═══════════════════════════════════════════════════════════════════════════

println("="^80)
println(" ADMM + Paillier (ORIGINAL DP_D_OPF DENSE Formulation)")
println("="^80)
println()

# ─────────────────────────────────────────────────────────────────────────────
# [1] Load configuration
# ─────────────────────────────────────────────────────────────────────────────
# Use case30 by default (case14 is too small for meaningful benchmarking)
caseID = "testbeds/pglib_opf_case30_ieee.m"
ν̅ = 1000      # Max iterations
ρ = 10.0       # Penalty parameter
γ = 1e-2       # Convergence tolerance
key_length = 1024  # Paillier key size (bits)

println("[1/6] Loading network data...")
println("  ✓ Using network: pglib_opf_case30_ieee")

# ─────────────────────────────────────────────────────────────────────────────
# [2] Load network data
# ─────────────────────────────────────────────────────────────────────────────
(gen, bus, line, B, refbus) = load_data(caseID)
Ng = length(gen)
Nb = length(bus)

println("  ✓ Loaded: $Nb buses, $Ng generators, $(length(line)) lines")

# ─────────────────────────────────────────────────────────────────────────────
# [3] Solve centralized OPF (baseline)
# ─────────────────────────────────────────────────────────────────────────────
println("\n[2/6] Initializing Gurobi and solving centralized OPF (baseline)...")
gurobi_env = Gurobi.Env()
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus, gurobi_env)
println("  ✓ Centralized cost: \$$(round(cost_c, digits=2))")

# ─────────────────────────────────────────────────────────────────────────────
# [4] Generate Paillier keys
# ─────────────────────────────────────────────────────────────────────────────
println("\n[3/6] Generating Paillier encryption keys...")
println("  🔐 Generating $(key_length)-bit keypair...")
key_start = time()
keypair = generate_keypair(key_length)
key_time = time() - key_start
println("  ✓ Keys generated in $(round(key_time, digits=2))s")

# Test encryption
println("\n[4/6] Testing Paillier homomorphic operations...")
a = 15.5
b = 24.5
enc_a = encrypt(keypair.public_key, a)
enc_b = encrypt(keypair.public_key, b)
enc_sum = enc_a + enc_b
dec_sum = decrypt(keypair.public_key, keypair.private_key, enc_sum)
println("  ✓ E($a) + E($b) = $(round(dec_sum, digits=1)) (expected: $(a+b))")

# ─────────────────────────────────────────────────────────────────────────────
# [5] Initialize ADMM variables (DENSE formulation)
# ─────────────────────────────────────────────────────────────────────────────
println("\n[5/6] Initializing ADMM parameters...")

# DENSE matrices (original DP_D_OPF formulation)
μ = zeros(Nb, Nb)
θ = zeros(Nb, Nb)
θ̅ = zeros(Nb)

p_history = zeros(Ng, ν̅)
l_history = zeros(Nb, ν̅)
cost_history = zeros(ν̅)
residuals = zeros(ν̅)

println("  ✓ Parameters: ρ=$ρ, max_iter=$ν̅, tolerance=$γ")
println("  ✓ Using $(key_length)-bit Paillier encryption")
println("  ℹ  Using ORIGINAL DP_D_OPF ADMM formulation (DENSE matrices)")

# ─────────────────────────────────────────────────────────────────────────────
# [6] Run ADMM with encryption
# ─────────────────────────────────────────────────────────────────────────────
println("\n[6/6] Running ADMM with Paillier encryption...")
println("\nDetailed timing: OPT=Optimization, CRYPTO=Encryption, OTHER=Dual+Residual")
println("\n" * "─"^110)
@printf("%-5s %-12s %-12s %-10s | %-8s %-8s %-8s | %-10s\n",
        "Iter", "Cost(\$)", "Residual", "Δ Res", "OPT(s)", "CRYPTO(s)", "OTHER(s)", "Total(s)")
println("─"^110)

converged = false
final_iter = ν̅
total_opt_time = 0.0
total_crypto_time = 0.0
total_other_time = 0.0

# Track iteration timestamps
admm_start_time = time()
iteration_times = Float64[]
iteration_timestamps = Float64[]

for ν in 2:ν̅
    global μ, θ, θ̅, converged, final_iter
    global total_opt_time, total_crypto_time, total_other_time

    iter_start = time()

    # ═══════════════════════════════════════════════════════════════════════
    # Step 1: Primal update (uses fun_voltage_update.jl - ORIGINAL)
    # ═══════════════════════════════════════════════════════════════════════
    opt_start = time()
    θ, cost_history[ν], p_history[:, ν], l_history[:, ν] =
        update_θ(gen, bus, line, B, refbus, μ, θ̅, ρ, gurobi_env)
    opt_time = time() - opt_start

    # ═══════════════════════════════════════════════════════════════════════
    # Step 2: Encryption
    # ═══════════════════════════════════════════════════════════════════════
    enc_start = time()
    θ_enc = encrypt_θ_dense(keypair.public_key, bus, θ)
    enc_time = time() - enc_start

    # ═══════════════════════════════════════════════════════════════════════
    # Step 3: Consensus update (homomorphic)
    # ═══════════════════════════════════════════════════════════════════════
    cons_start = time()
    θ̅ = update_θ̅_homomorphic_dense(keypair.public_key, keypair.private_key, bus, θ_enc)
    cons_time = time() - cons_start

    crypto_time = enc_time + cons_time

    # ═══════════════════════════════════════════════════════════════════════
    # Step 4: Dual update (uses fun_dual_update.jl - ORIGINAL)
    # ═══════════════════════════════════════════════════════════════════════
    dual_start = time()
    μ = update_μ(bus, ρ, θ, θ̅, μ)

    # ═══════════════════════════════════════════════════════════════════════
    # Step 5: Residual (uses fun_residual_update.jl - ORIGINAL)
    # ═══════════════════════════════════════════════════════════════════════
    residuals[ν] = residual(bus, θ, θ̅)
    other_time = time() - dual_start

    # ═══════════════════════════════════════════════════════════════════════

    iter_time = time() - iter_start
    cumulative_time = time() - admm_start_time

    # Record timing data
    push!(iteration_times, iter_time)
    push!(iteration_timestamps, cumulative_time)

    total_opt_time += opt_time
    total_crypto_time += crypto_time
    total_other_time += other_time

    # Print progress
    if ν == 2 || ν % 10 == 0 || residuals[ν] <= γ
        Δres = ν > 2 ? residuals[ν-1] - residuals[ν] : 0.0
        @printf("%-5d \$%-11.2f %-12.6f %-10.6f | %-8.3f %-8.3f %-8.3f | %-10.3f\n",
                ν, cost_history[ν], residuals[ν], Δres, opt_time, crypto_time, other_time, iter_time)
    end

    # Check convergence
    if residuals[ν] <= γ
        println("─"^110)
        println("✅ CONVERGED at iteration $ν")
        println("   Residual $(round(residuals[ν], digits=6)) ≤ tolerance $γ")
        final_iter = ν
        converged = true
        break
    end
end

admm_total_time = time() - admm_start_time

if !converged
    println("─"^110)
    println("⚠️  Maximum iterations ($ν̅) reached without convergence")
    println("   Final residual: $(round(residuals[final_iter], digits=6)) > tolerance $γ")
end

# ═══════════════════════════════════════════════════════════════════════════
# Print summary
# ═══════════════════════════════════════════════════════════════════════════
println("\n" * "="^80)
println(" RESULTS SUMMARY")
println("="^80)
println("  Converged:           $converged")
println("  Iterations:          $final_iter / $ν̅")
println("  Total time:          $(round(admm_total_time, digits=2))s")
println("  Avg iter time:       $(round(admm_total_time/final_iter*1000, digits=2))ms")
println()
println("  Centralized cost:    \$$(round(cost_c, digits=2))")
println("  Final cost:          \$$(round(cost_history[final_iter], digits=2))")
println("  Optimality loss:     $(round(abs(cost_c - cost_history[final_iter])/cost_c*100, digits=4))%")
println()
println("  Timing breakdown:")
pct_opt = total_opt_time / admm_total_time * 100
pct_crypto = total_crypto_time / admm_total_time * 100
pct_other = total_other_time / admm_total_time * 100
println("    Optimization:      $(round(total_opt_time, digits=2))s ($(round(pct_opt, digits=1))%)")
println("    Cryptography:      $(round(total_crypto_time, digits=2))s ($(round(pct_crypto, digits=1))%)")
println("    Other:             $(round(total_other_time, digits=2))s ($(round(pct_other, digits=1))%)")
println("="^80)

# ═══════════════════════════════════════════════════════════════════════════
# Save results to JSON
# ═══════════════════════════════════════════════════════════════════════════
output_dir = "results"
if !isdir(output_dir)
    mkpath(output_dir)
end

results = Dict(
    "scheme" => "paillier",
    "converged" => converged,
    "iterations" => final_iter,
    "max_iterations" => ν̅,
    "total_time_s" => admm_total_time,
    "avg_iteration_time_ms" => admm_total_time / final_iter * 1000,
    "centralized_cost" => cost_c,
    "final_cost" => cost_history[final_iter],
    "optimality_loss_percent" => abs(cost_c - cost_history[final_iter]) / cost_c * 100,
    "final_residual" => residuals[final_iter],
    "tolerance" => γ,
    "rho" => ρ,
    "key_length_bits" => key_length,
    "network" => caseID,
    "num_buses" => Nb,
    "num_generators" => Ng,
    # Timing breakdown
    "opt_time_s" => total_opt_time,
    "crypto_time_s" => total_crypto_time,
    "other_time_s" => total_other_time,
    "pct_opt" => pct_opt,
    "pct_crypto" => pct_crypto,
    "pct_other" => pct_other,
    # Iteration data
    "iteration_times" => iteration_times[1:final_iter],
    "iteration_timestamps" => iteration_timestamps[1:final_iter],
    "residuals" => residuals[2:final_iter],
    "cost_history" => cost_history[2:final_iter]
)

output_file = joinpath(output_dir, "paillier_results.json")
open(output_file, "w") do f
    JSON.print(f, results, 4)
end

println("\n✓ Results saved to: $output_file")
println()
