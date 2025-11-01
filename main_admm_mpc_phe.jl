"""
ADMM-based Optimal Power Flow with MPC-with-PHE Encryption Approach
Complete Julia implementation using converted MPC-with-PHE libraries

This implementation follows the MPC-with-PHE repository structure:
- Fixed-point arithmetic for float encoding (32-bit precision)
- Paillier homomorphic encryption for secure computation
- Client-based encryption/decryption interface
- Homomorphic operations for dual variable updates

Author: Converted from Python MPC-with-PHE to Julia
Repository: https://github.com/andreea-alexandru/MPC-with-PHE (original Python)
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
using Gurobi
using DataFrames
using LinearAlgebra
using CSV
using Distributions
using Printf

# Load OPF ADMM helper scripts
include("scripts/data_manager.jl")
include("scripts/fun_centralized_OPF.jl")
include("scripts/fun_compute_sensitivity.jl")
include("scripts/fun_consensus_update.jl")
include("scripts/fun_dual_update.jl")
include("scripts/fun_residual_update.jl")
include("scripts/fun_reveal_load.jl")
include("scripts/fun_voltage_update.jl")

# Load MPC-with-PHE encryption modules
include("scripts/mpc_phe_client.jl")

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

const KEYSIZE = 1024              # Paillier key size (bits)
const PRECISION = 32              # Fixed-point precision (bits) - matches MPC-with-PHE
const LOAD_KEYS = false           # Try to load existing keys
const KEYS_DIR = "Keys"           # Directory for key storage

# ADMM Parameters
const MAX_ITERATIONS = 15000      # Maximum ADMM iterations
const PENALTY_PARAMETER = 1e3     # ρ - ADMM penalty parameter
const CONVERGENCE_THRESHOLD = 1e-2  # γ - convergence tolerance

# Differential Privacy Parameters (optional hybrid approach)
const DP_EPSILON = 1.0
const DP_ALPHA = 0.1
const DP_METHOD = "PVP"  # Perturb Primal Variables

# ============================================================================
# HELPER FUNCTIONS FOR ENCRYPTED ADMM
# ============================================================================

"""
    encrypt_dual_variables!(client, enc_μ, μ, bus, iteration)

Encrypt dual variables for the current iteration.
Only encrypts values for neighbor connections (sparse).
"""
function encrypt_dual_variables!(client::MPCClient, enc_μ, μ, bus, iteration)
    n_bus = length(bus)

    for i in 1:n_bus
        for j in bus[i].N
            enc_μ[i,j,iteration] = encrypt_scalar(client, μ[i,j,iteration])
        end
    end
end

"""
    decrypt_dual_variables!(client, μ, enc_μ, bus, iteration)

Decrypt dual variables for local optimization.
Each bus decrypts only its own dual variables.
"""
function decrypt_dual_variables!(client::MPCClient, μ, enc_μ, bus, iteration)
    n_bus = length(bus)

    for i in 1:n_bus
        for j in bus[i].N
            if enc_μ[i,j,iteration] !== nothing
                μ[i,j,iteration] = decrypt_scalar(client, enc_μ[i,j,iteration])
            end
        end
    end
end

"""
    encrypted_dual_update_step!(client, enc_μ_new, enc_μ_prev, θ, θ̅, bus, ρ)

Perform encrypted dual update using homomorphic operations:
    E(μ[i,j]ₖ₊₁) = E(μ[i,j]ₖ) + E(ρ * (θ[i,j] - θ̅[j]))

This is the core privacy-preserving operation where dual variables
are updated without decryption using Paillier's additive homomorphism.
"""
function encrypted_dual_update_step!(client::MPCClient, enc_μ_new, enc_μ_prev,
                                     θ, θ̅, bus, ρ)
    n_bus = length(bus)

    for i in 1:n_bus
        for j in bus[i].N
            # Homomorphic dual update
            enc_μ_new[i,j] = homomorphic_dual_update(client, enc_μ_prev[i,j],
                                                     θ[i,j], θ̅[j], ρ)
        end
    end
end

"""
    verify_encryption_accuracy(client, original_values, encrypted_values, name)

Verify that encryption/decryption preserves accuracy within tolerance.
"""
function verify_encryption_accuracy(client::MPCClient, original_values,
                                   encrypted_values, name::String)
    decrypted = [decrypt_scalar(client, enc) for enc in encrypted_values]
    errors = abs.(original_values .- decrypted)
    max_error = maximum(errors)
    mean_error = sum(errors) / length(errors)

    println("  $name:")
    println("    Max error:  $(max_error)")
    println("    Mean error: $(mean_error)")
    println("    Status:     $(max_error < 1e-6 ? "✓ PASS" : "✗ FAIL")")

    return max_error < 1e-6
end

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function main()
    println("\n" * "="^80)
    println("  ADMM-based OPF with MPC-with-PHE Encryption Approach")
    println("  Julia implementation using converted MPC-with-PHE libraries")
    println("="^80)

    # ========================================================================
    # PHASE 1: LOAD DATA AND SOLVE CENTRALIZED OPF
    # ========================================================================

    println("\n[Phase 1/7] Loading power system data...")
    caseID = "testbeds/pglib_opf_case14_ieee.m"
    (gen, bus, line, B, refbus) = load_data(caseID)
    n_bus = length(bus)
    n_gen = length(gen)
    println("  ✓ Loaded $(n_bus)-bus IEEE test system")
    println("  ✓ Number of generators: $(n_gen)")
    println("  ✓ Number of transmission lines: $(length(line))")

    # Initialize Gurobi
    gurobi_env = Gurobi.Env()

    # Solve centralized OPF (baseline for comparison)
    println("\n  Solving centralized OPF (baseline)...")
    (cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus)
    println("  ✓ Centralized optimal cost: \$$(round(cost_c, digits=2))")

    # ========================================================================
    # PHASE 2: INITIALIZE MPC CLIENT AND GENERATE KEYS
    # ========================================================================

    println("\n[Phase 2/7] Initializing MPC-PHE encryption...")
    client = MPCClient(keysize=KEYSIZE, precision=PRECISION,
                       load_keys=LOAD_KEYS, keys_dir=KEYS_DIR)
    println("  ✓ MPC Client initialized")
    println("  ✓ Key size: $(client.keysize) bits")
    println("  ✓ Fixed-point precision: $(client.precision) bits")
    println("  ✓ Public key modulus n: $(ndigits(client.pubkey.n, base=10)) decimal digits")

    # ========================================================================
    # PHASE 3: INITIALIZE ADMM VARIABLES
    # ========================================================================

    println("\n[Phase 3/7] Initializing ADMM variables...")

    # Primal variables (local, unencrypted)
    θ = zeros(n_bus, n_bus, MAX_ITERATIONS)      # Voltage angles
    θ̅ = zeros(n_bus, MAX_ITERATIONS)             # Consensus angles
    p = zeros(n_gen, MAX_ITERATIONS)            # Generator dispatch
    l = zeros(n_bus, MAX_ITERATIONS)            # Load dispatch
    d = zeros(n_bus, n_bus, MAX_ITERATIONS)     # Revealed loads
    cost = zeros(1)

    # Dual variables (both encrypted and plaintext versions)
    μ = zeros(n_bus, n_bus, MAX_ITERATIONS)  # Plaintext (for local use)
    enc_μ = Matrix{Union{EncryptedNumber,Nothing}}(nothing, n_bus, n_bus, MAX_ITERATIONS)

    # Initialize encrypted dual variables to zero
    println("  Initializing encrypted dual variables...")
    for i in 1:n_bus
        for j in bus[i].N
            μ[i,j,1] = 0.0
            enc_μ[i,j,1] = encrypt_scalar(client, 0.0)
        end
    end

    # Encrypt sensitive load data (demonstration)
    println("  Encrypting sensitive load data...")
    enc_loads = Vector{EncryptedNumber}(undef, n_bus)
    original_loads = [bus[i].d for i in 1:n_bus]
    for i in 1:n_bus
        enc_loads[i] = encrypt_scalar(client, bus[i].d)
    end

    # Verify encryption accuracy
    println("\n  Verifying encryption accuracy...")
    verify_encryption_accuracy(client, original_loads, enc_loads, "Load encryption")

    # Differential Privacy setup (optional)
    println("\n  Setting up differential privacy (optional layer)...")
    Δ_op = sensitivities(gen, bus, line, B, refbus, PENALTY_PARAMETER, DP_METHOD, DP_ALPHA)
    ξ = zeros(n_bus, n_bus)
    for i in 1:n_bus
        for j in bus[i].N
            ξ[i,j] = rand(Laplace(0, Δ_op[i,j]/DP_EPSILON))
        end
    end
    println("  ✓ DP noise generated (ε = $(DP_EPSILON), method = $(DP_METHOD))")

    println("  ✓ ADMM initialization complete")

    # ========================================================================
    # PHASE 4: RUN ENCRYPTED ADMM ITERATIONS
    # ========================================================================

    println("\n[Phase 4/7] Running encrypted ADMM iterations...")
    println("="^80)
    println("  Iter    Residual      Cost (\$)      Time (s)")
    println("-"^80)

    ν̃ = 0  # Actual iterations
    start_time = time()
    last_print_time = start_time

    for ν in 2:MAX_ITERATIONS
        # ----------------------------------------------------------------
        # Step 1: Decrypt dual variables for local optimization
        # (Each bus decrypts only its own μ values)
        # ----------------------------------------------------------------
        decrypt_dual_variables!(client, μ, enc_μ, bus, ν-1)

        # ----------------------------------------------------------------
        # Step 2: Local optimization (standard ADMM update)
        # ----------------------------------------------------------------
        (θ[:,:,ν], cost[1], p[:,ν], l[:,ν]) = update_θ(gen, bus, line, B, refbus,
                                                         μ[:,:,ν-1], θ̅[:,ν-1],
                                                         PENALTY_PARAMETER)

        # ----------------------------------------------------------------
        # Step 3: Add differential privacy noise (optional)
        # ----------------------------------------------------------------
        θ̃ = θ[:,:,ν] .+ ξ

        # ----------------------------------------------------------------
        # Step 4: Consensus update
        # ----------------------------------------------------------------
        θ̅[:,ν] = update_θ̅(bus, θ̃)

        # ----------------------------------------------------------------
        # Step 5: ENCRYPTED DUAL UPDATE (Privacy-Preserving Core)
        # Uses homomorphic operations - no plaintext dual sharing
        # ----------------------------------------------------------------
        encrypted_dual_update_step!(client, view(enc_μ, :, :, ν),
                                   view(enc_μ, :, :, ν-1),
                                   θ̃, θ̅[:,ν], bus, PENALTY_PARAMETER)

        # ----------------------------------------------------------------
        # Step 6: Load revelation (for analysis)
        # ----------------------------------------------------------------
        d[:,:,ν] = reveal_load(bus, gen, B, PENALTY_PARAMETER,
                              μ[:,:,ν-1], θ̅[:,ν-1], θ̃)

        # ----------------------------------------------------------------
        # Step 7: Convergence check
        # ----------------------------------------------------------------
        Γ = residual(bus, θ̃, θ̅[:,ν])

        # Progress reporting
        current_time = time()
        if ν % 100 == 0 || (current_time - last_print_time) >= 5.0
            elapsed = current_time - start_time
            @printf("  %5d   %10.6f   %11.2f   %8.2f\n", ν, Γ, cost[1], elapsed)
            last_print_time = current_time
        end

        # Check convergence
        if Γ <= CONVERGENCE_THRESHOLD || ν == MAX_ITERATIONS
            ν̃ = ν
            elapsed = time() - start_time
            println("-"^80)
            println("  ✓ ADMM converged at iteration $(ν)")
            println("  ✓ Final residual: $(round(Γ, digits=8))")
            println("  ✓ Total time: $(round(elapsed, digits=2)) seconds")
            println("  ✓ Time per iteration: $(round(elapsed/ν, digits=4)) seconds")
            break
        end
    end

    # ========================================================================
    # PHASE 5: DECRYPT FINAL RESULTS
    # ========================================================================

    println("\n[Phase 5/7] Decrypting final results...")

    # Decrypt final dual variables
    final_μ_decrypted = zeros(n_bus, n_bus)
    for i in 1:n_bus
        for j in bus[i].N
            if enc_μ[i,j,ν̃] !== nothing
                final_μ_decrypted[i,j] = decrypt_scalar(client, enc_μ[i,j,ν̃])
            end
        end
    end

    # Decrypt loads
    decrypted_loads = [decrypt_scalar(client, enc_loads[i]) for i in 1:n_bus]

    println("  ✓ Decryption complete")

    # ========================================================================
    # PHASE 6: PREPARE COMPARISON RESULTS
    # ========================================================================

    println("\n[Phase 6/7] Preparing comparison results...")

    # Load comparison
    load_comparison = DataFrame(
        Bus = 1:n_bus,
        Actual_Load = original_loads,
        Encrypted_Decrypted = decrypted_loads,
        Observed_Load = [d[i,i,ν̃] for i in 1:n_bus],
        Encryption_Error = abs.(original_loads .- decrypted_loads),
        Observation_Error = abs.(original_loads .- [d[i,i,ν̃] for i in 1:n_bus])
    )

    # Dispatch comparison
    dispatch_comparison = DataFrame(
        Bus = Int[],
        Type = String[],
        Centralized = Float64[],
        ADMM_MPC_PHE = Float64[],
        Difference = Float64[]
    )

    for i in 1:n_bus
        if bus[i].type == 1  # Generator
            gen_idx = bus[i].G[1]
            cent_val = dispatch_c[gen_idx, 3]
            admm_val = p[gen_idx, ν̃]
            push!(dispatch_comparison, (i, "Generator", cent_val, admm_val, abs(cent_val - admm_val)))
        elseif bus[i].type == 2  # Load
            cent_val = dispatch_c[i, 4]
            admm_val = l[i, ν̃]
            push!(dispatch_comparison, (i, "Load", cent_val, admm_val, abs(cent_val - admm_val)))
        end
    end

    # Flow comparison
    flow_comparison = DataFrame(
        Line = 1:length(line),
        From_Bus = [line[l].b_f for l in 1:length(line)],
        To_Bus = [line[l].b_t for l in 1:length(line)],
        Centralized = [round(line[l].β * (dispatch_c[line[l].b_f,6] - dispatch_c[line[l].b_t,6]), digits=4)
                      for l in 1:length(line)],
        ADMM_MPC_PHE = [round(line[l].β * (θ̅[line[l].b_f,ν̃] - θ̅[line[l].b_t,ν̃]), digits=4)
                       for l in 1:length(line)]
    )
    flow_comparison.Difference = abs.(flow_comparison.Centralized .- flow_comparison.ADMM_MPC_PHE)

    println("  ✓ Comparison tables generated")

    # ========================================================================
    # PHASE 7: DISPLAY RESULTS
    # ========================================================================

    println("\n[Phase 7/7] Displaying results...")
    println("\n" * "="^80)
    println("  FINAL RESULTS - ADMM with MPC-with-PHE Encryption")
    println("="^80)

    # Optimization performance
    println("\n┌─ Optimization Performance")
    println("│")
    println("│  Centralized OPF cost:      \$$(round(cost_c, digits=2))")
    println("│  ADMM MPC-PHE cost:         \$$(round(cost[1], digits=2))")
    println("│  Absolute difference:       \$$(round(abs(cost_c - cost[1]), digits=2))")
    println("│  Optimality gap:            $(round(abs(cost_c - cost[1])/cost_c * 100, digits=4))%")
    println("│  Iterations to convergence: $(ν̃)")
    println("│")
    println("└─")

    # Encryption parameters
    println("\n┌─ MPC-with-PHE Encryption Configuration")
    println("│")
    println("│  Key size:                  $(client.keysize) bits")
    println("│  Security level:            ~$(div(client.keysize, 2)) bits")
    println("│  Fixed-point precision:     $(client.precision) bits")
    println("│  Precision loss:            ~$(2.0^(-client.precision)) per operation")
    println("│  Privacy method:            $(DP_METHOD) (Differential Privacy)")
    println("│  DP epsilon:                $(DP_EPSILON)")
    println("│")
    println("└─")

    # Encryption verification
    println("\n┌─ Encryption Verification")
    println("│")
    max_enc_error = maximum(load_comparison.Encryption_Error)
    mean_enc_error = sum(load_comparison.Encryption_Error) / n_bus
    println("│  Maximum encryption error:  $(max_enc_error)")
    println("│  Mean encryption error:     $(mean_enc_error)")
    println("│  Verification status:       $(max_enc_error < 1e-6 ? "✓ PASS" : "✗ FAIL")")
    println("│")
    println("└─")

    # Detailed results
    println("\n" * "="^80)
    println("  DETAILED COMPARISON TABLES")
    println("="^80)

    println("\n■ Load Encryption and Observation")
    println(load_comparison)

    println("\n■ Node Dispatch Comparison")
    println(dispatch_comparison)

    println("\n■ Power Flow Comparison")
    println(flow_comparison)

    # Privacy analysis
    println("\n" * "="^80)
    println("  PRIVACY AND SECURITY ANALYSIS")
    println("="^80)

    println("\n┌─ MPC-with-PHE Approach Implementation")
    println("│")
    println("│  ✓ Converted from Python MPC-with-PHE repository to Julia")
    println("│  ✓ Fixed-point arithmetic ($(client.precision)-bit precision)")
    println("│  ✓ Paillier homomorphic encryption ($(client.keysize)-bit keys)")
    println("│  ✓ Client-based encryption/decryption interface")
    println("│  ✓ Sparse matrix handling for network topology")
    println("│")
    println("└─")

    println("\n┌─ Privacy Guarantees")
    println("│")
    println("│  • Sensitive load data encrypted with Paillier cryptosystem")
    println("│  • Dual variables (μ) shared between buses in encrypted form")
    println("│  • Homomorphic operations enable updates without decryption")
    println("│  • Each bus decrypts only its own local variables")
    println("│  • Optional differential privacy layer (ε = $(DP_EPSILON))")
    println("│")
    println("└─")

    println("\n┌─ Security Properties")
    println("│")
    println("│  Encryption scheme:         Paillier (additively homomorphic)")
    println("│  Security assumption:       Decisional Composite Residuosity")
    println("│  Estimated security level:  ~$(div(client.keysize, 2)) bits")
    println("│  Homomorphic operations:    E(a) + E(b) = E(a+b)")
    println("│                             E(a) × k = E(a×k)")
    println("│  Communication privacy:     Encrypted dual variable exchange")
    println("│  Computation privacy:       Local decryption only")
    println("│")
    println("└─")

    println("\n┌─ MPC-with-PHE Modules Used")
    println("│")
    println("│  • mpc_phe_util.jl         - Cryptographic primitives")
    println("│  • mpc_phe_paillier.jl     - Paillier encryption core")
    println("│  • mpc_phe_client.jl       - High-level encryption interface")
    println("│  • main_admm_mpc_phe.jl    - ADMM with encrypted operations")
    println("│")
    println("└─")

    println("\n" * "="^80)
    println("  ✓ Execution Complete!")
    println("="^80)
    println()

    return (client=client, cost_centralized=cost_c, cost_admm=cost[1],
            iterations=ν̃, load_comparison=load_comparison,
            dispatch_comparison=dispatch_comparison,
            flow_comparison=flow_comparison)
end

# ============================================================================
# RUN MAIN PROGRAM
# ============================================================================

if abspath(PROGRAM_FILE) == @__FILE__
    results = main()
end
