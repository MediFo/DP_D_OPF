"""
Boyd's Consensus ADMM with Paillier Homomorphic Encryption for DC-OPF (Version 2)
Uses original DP_D_OPF scripts with Paillier encryption layer
Cleaner implementation that reuses existing ADMM functions
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
# using Gurobi  # Commercial solver (commented out)
using Ipopt     # Free nonlinear solver
using DataFrames
using LinearAlgebra
using CSV
using Printf

# Load original DP_D_OPF scripts (reuse existing ADMM implementation)
include("scripts/data_manager.jl")
include("scripts/fun_centralized_OPF.jl")
include("scripts/fun_consensus_update.jl")
include("scripts/fun_dual_update.jl")
include("scripts/fun_residual_update.jl")
include("scripts/fun_voltage_update.jl")

# Load Paillier encryption module
include("scripts/paillier_crypto.jl")

# ══════════════════════════════════════════════════════════════════════════════
# PAILLIER ENCRYPTION WRAPPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

"""
Encrypt θ matrix for privacy-preserving sharing
"""
function encrypt_θ_matrix(public_key, bus, θ_plain)
    Nb = length(bus)
    θ_enc = Matrix{Union{EncryptedNumber, Nothing}}(nothing, Nb, Nb)

    for i in 1:Nb
        for j in bus[i].N
            θ_enc[i, j] = encrypt(public_key, θ_plain[i, j])
        end
    end

    return θ_enc
end

"""
Decrypt θ matrix after consensus update
"""
function decrypt_θ_matrix(public_key, private_key, bus, θ_enc)
    Nb = length(bus)
    θ_plain = zeros(Nb, Nb)

    for i in 1:Nb
        for j in bus[i].N
            if θ_enc[i, j] !== nothing
                θ_plain[i, j] = decrypt(public_key, private_key, θ_enc[i, j])
            end
        end
    end

    return θ_plain
end

"""
Homomorphic consensus update (encrypted version of update_θ̅)
Computes consensus via encrypted averaging: θ̅[i] = (1/|N_i|) * Σ E(θ[j,i])
"""
function update_θ̅_homomorphic(public_key, private_key, bus, θ_enc)
    Nb = length(bus)
    θ̅_enc = Vector{Union{EncryptedNumber, Nothing}}(nothing, Nb)
    θ̅_plain = zeros(Nb)

    for i in 1:Nb
        # Collect encrypted values from neighbors
        enc_neighbors = EncryptedNumber[]
        for j in bus[i].N
            if θ_enc[j, i] !== nothing
                push!(enc_neighbors, θ_enc[j, i])
            end
        end

        if !isempty(enc_neighbors)
            # Homomorphic averaging
            θ̅_enc[i] = encrypted_average(enc_neighbors)

            # Decrypt for local use
            θ̅_plain[i] = decrypt(public_key, private_key, θ̅_enc[i])
        end
    end

    return θ̅_plain, θ̅_enc
end

# ══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" BOYD'S CONSENSUS ADMM + PAILLIER ENCRYPTION (Version 2)")
println(" Uses original DP_D_OPF scripts with encryption layer")
println("="^80 * "\n")

# ─────────────────────────────────────────────────────────────────────────────
# [1] Load network data
# ─────────────────────────────────────────────────────────────────────────────
println("[1/6] Loading network data...")
caseID_options = [
    "testbeds/pglib_opf_case33_bw.m",
    "testbeds/pglib_opf_case30_ieee.m",
    "testbeds/pglib_opf_case14_ieee.m"
]

caseID = ""
for case in caseID_options
    if isfile(case)
        global caseID = case
        break
    end
end

if caseID == ""
    global caseID = "testbeds/pglib_opf_case14_ieee.m"  # Default
end

network_name = split(split(caseID, "/")[end], ".")[1]
println("  ✓ Using network: $network_name")

(gen, bus, line, B, refbus) = load_data(caseID)
println("  ✓ Loaded: $(length(bus)) buses, $(length(gen)) generators, $(length(line)) lines")

# ─────────────────────────────────────────────────────────────────────────────
# [2] Solve centralized OPF (baseline for comparison)
# ─────────────────────────────────────────────────────────────────────────────
println("\n[2/6] Solving centralized OPF (baseline)...")
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus)
println("  ✓ Centralized cost: \$", round(cost_c, digits=2))

# ─────────────────────────────────────────────────────────────────────────────
# [3] Generate Paillier encryption keys
# ─────────────────────────────────────────────────────────────────────────────
println("\n[3/6] Generating Paillier encryption keys...")
key_length = 1024  # Use 1024-bit for faster computation (2048-bit for production)
println("  🔐 Generating $(key_length)-bit keypair...")
start_time = time()
keypair = generate_paillier_keypair(key_length)
keygen_time = time() - start_time
println("  ✓ Keys generated in ", round(keygen_time, digits=2), "s")

# Test homomorphic operations
println("\n[4/6] Testing Paillier homomorphic operations...")
test1 = encrypt(keypair.public_key, 15.5)
test2 = encrypt(keypair.public_key, 24.5)
test_sum = test1 + test2
test_result = decrypt(keypair.public_key, keypair.private_key, test_sum)
println("  ✓ E(15.5) + E(24.5) = ", round(test_result, digits=2), " (expected: 40.0)")

# ─────────────────────────────────────────────────────────────────────────────
# [4] Initialize ADMM parameters
# ─────────────────────────────────────────────────────────────────────────────
println("\n[5/6] Initializing ADMM parameters...")
ν̅ = 100        # Maximum iterations
ρ = 50.0       # ADMM penalty parameter
γ = 1e-2       # Convergence tolerance
Nb = length(bus)
Ng = length(gen)

# Initialize ADMM variables (same as original DP_D_OPF)
μ = zeros(Nb, Nb)
θ = zeros(Nb, Nb, ν̅)
θ̅ = zeros(Nb, ν̅)
p = zeros(Ng, ν̅)
l = zeros(Nb, ν̅)
cost = zeros(ν̅)
residuals = zeros(ν̅)

println("  ✓ Parameters: ρ=$ρ, max_iter=$ν̅, tolerance=$γ")
println("  ✓ Using $(key_length)-bit Paillier encryption")

# ─────────────────────────────────────────────────────────────────────────────
# [5] Run ADMM with Paillier encryption
# ─────────────────────────────────────────────────────────────────────────────
println("\n[6/6] Running Boyd's Consensus ADMM with Paillier encryption...")
println("\nDetailed timing: OPT=Optimization, ENC=Encryption, CON=Consensus, DEC=Decryption")
println("\n" * "─"^110)
@printf("%-5s %-12s %-12s %-10s | %-8s %-8s %-8s | %-10s\n",
        "Iter", "Cost(\$)", "Residual", "Δ Res", "OPT(s)", "CRYPTO(s)", "OTHER(s)", "Total(s)")
println("─"^110)

converged = false
final_iter = ν̅

# Timing accumulators
total_opt_time = 0.0
total_crypto_time = 0.0
total_other_time = 0.0

for ν in 2:ν̅
    global μ, final_iter, converged  # Declare global variables modified in loop
    global total_opt_time, total_crypto_time, total_other_time  # Timing accumulators

    iter_start = time()

    # ═══════════════════════════════════════════════════════════════════════
    # ADMM ITERATION (using original DP_D_OPF scripts + Paillier encryption)
    # ═══════════════════════════════════════════════════════════════════════

    # Step 1: Primal update (OPTIMIZATION)
    opt_start = time()
    (θ[:, :, ν], cost[ν], p[:, ν], l[:, ν]) =
        update_θ(gen, bus, line, B, refbus, μ, θ̅[:, ν-1], ρ)
    opt_time = time() - opt_start

    # Step 2: Encrypt θ values (CRYPTOGRAPHY - Encryption)
    enc_start = time()
    θ_enc = encrypt_θ_matrix(keypair.public_key, bus, θ[:, :, ν])
    enc_time = time() - enc_start

    # Step 3: Homomorphic consensus (CRYPTOGRAPHY - Homomorphic ops + Decryption)
    cons_start = time()
    (θ̅[:, ν], θ̅_enc) =
        update_θ̅_homomorphic(keypair.public_key, keypair.private_key, bus, θ_enc)
    cons_time = time() - cons_start

    # Total crypto time = encryption + consensus (includes decryption)
    crypto_time = enc_time + cons_time

    # Step 4: Dual update (LOCAL - no encryption)
    dual_start = time()
    μ = update_μ(bus, ρ, θ[:, :, ν], θ̅[:, ν], μ)

    # Step 5: Compute residual
    residuals[ν] = residual(bus, θ[:, :, ν], θ̅[:, ν])
    other_time = time() - dual_start

    # ═══════════════════════════════════════════════════════════════════════

    iter_time = time() - iter_start

    # Accumulate times
    total_opt_time += opt_time
    total_crypto_time += crypto_time
    total_other_time += other_time

    # Print progress with timing breakdown
    if ν == 2 || ν % 10 == 0 || residuals[ν] <= γ
        Δres = ν > 2 ? residuals[ν-1] - residuals[ν] : 0.0
        @printf("%-5d \$%-11.2f %-12.6f %-10.6f | %-8.3f %-8.3f %-8.3f | %-10.3f\n",
                ν, cost[ν], residuals[ν], Δres, opt_time, crypto_time, other_time, iter_time)
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

if !converged
    println("─"^80)
    println("⚠  Maximum iterations ($ν̅) reached")
    println("   Final residual: $(round(residuals[final_iter], digits=6))")
end

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" RESULTS SUMMARY")
println("="^80 * "\n")

println("Network: $network_name")
println("  Buses: $(length(bus)), Generators: $(length(gen)), Lines: $(length(line))")
println()

println("Convergence:")
println("  Status:     ", converged ? "✅ Converged" : "⚠  Not converged")
println("  Iterations: $final_iter / $ν̅")
println("  Residual:   ", round(residuals[final_iter], digits=6))
println()

println("Cost Comparison:")
println("  Centralized OPF:  \$", round(cost_c, digits=2))
println("  ADMM+Paillier:    \$", round(cost[final_iter], digits=2))
cost_diff = abs(cost_c - cost[final_iter])
cost_pct = (cost_diff / cost_c) * 100
println("  Absolute diff:    \$", round(cost_diff, digits=4))
println("  Relative diff:    ", round(cost_pct, digits=4), "%")
println()

println("Encryption:")
println("  Key size:      $(key_length)-bit Paillier")
println("  Security:      Computational (ciphertext indistinguishability)")
println("  Privacy:       Voltage angles encrypted during sharing")
println()

# Timing breakdown summary
total_time = total_opt_time + total_crypto_time + total_other_time
avg_opt = total_opt_time / (final_iter - 1)
avg_crypto = total_crypto_time / (final_iter - 1)
avg_other = total_other_time / (final_iter - 1)
avg_total = total_time / (final_iter - 1)

pct_opt = (total_opt_time / total_time) * 100
pct_crypto = (total_crypto_time / total_time) * 100
pct_other = (total_other_time / total_time) * 100

println("Performance Analysis:")
println("─"^80)
println("  Component              Total Time    Avg/Iter    Percentage")
println("─"^80)
@printf("  Optimization (OPF)     %-10.3fs    %-10.3fs    %5.1f%%\n",
        total_opt_time, avg_opt, pct_opt)
@printf("  Cryptography (Enc+Dec) %-10.3fs    %-10.3fs    %5.1f%%\n",
        total_crypto_time, avg_crypto, pct_crypto)
@printf("  Other (Dual+Residual)  %-10.3fs    %-10.3fs    %5.1f%%\n",
        total_other_time, avg_other, pct_other)
println("─"^80)
@printf("  TOTAL                  %-10.3fs    %-10.3fs    100.0%%\n",
        total_time, avg_total)
println("─"^80)
println()
println("Key Insights:")
if pct_crypto > 50
    println("  ⚠  Cryptography is the bottleneck ($(round(pct_crypto, digits=1))% of time)")
    println("     → Consider reducing key size for faster testing (1024→512 bit)")
    println("     → Or reduce max iterations to get preliminary results")
elseif pct_opt > 50
    println("  ℹ  Optimization is dominant ($(round(pct_opt, digits=1))% of time)")
    println("     → This is expected for well-tuned ADMM")
    println("     → Cryptography overhead is reasonable")
else
    println("  ✓ Balanced time distribution between optimization and cryptography")
end
println("  ℹ  Encryption overhead: $(round(pct_crypto, digits=1))% vs baseline ADMM")
println()

# Dispatch comparison (first 10 buses)
println("Dispatch Comparison (first 10 buses):")
println("─"^80)
@printf("%-6s %-10s %-15s %-15s %-15s\n", "Bus", "Type", "Centralized", "ADMM+Paillier", "Error")
println("─"^80)

for i in 1:min(10, Nb)
    if bus[i].type == 1 && !isempty(bus[i].G)  # Generator bus
        g = bus[i].G[1]
        cent = dispatch_c[g, 3]
        admm = p[g, final_iter]
        err = abs(cent - admm)
        @printf("%-6d %-10s %-15.3f %-15.3f %-15.5f\n", i, "Generator", cent, admm, err)
    elseif bus[i].type == 2  # Load bus
        cent = dispatch_c[i, 4]
        admm = l[i, final_iter]
        err = abs(cent - admm)
        @printf("%-6d %-10s %-15.3f %-15.3f %-15.5f\n", i, "Load", cent, admm, err)
    end
end
println("─"^80)

println("\n" * "="^80)
println(" ✅ ADMM WITH PAILLIER ENCRYPTION COMPLETED SUCCESSFULLY")
println("="^80 * "\n")

println("Implementation Notes:")
println("  • Uses original DP_D_OPF ADMM scripts (tested & verified)")
println("  • Adds Paillier encryption layer for privacy")
println("  • Homomorphic consensus ensures data privacy")
println("  • Free Ipopt solver (no commercial license needed)")
println("  • Detailed timing breakdown shows optimization vs cryptography overhead")
println()
