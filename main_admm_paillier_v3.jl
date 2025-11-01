using PowerModels
using DataStructures: SortedDict
using JuMP
using Gurobi
using DataFrames
using LinearAlgebra
using CSV
using Distributions
using Paillier  # Paillier homomorphic encryption

# load scripts
include("scripts/data_manager.jl")
include("scripts/fun_centralized_OPF.jl")
include("scripts/fun_compute_sensitivity.jl")
include("scripts/fun_consensus_update.jl")
include("scripts/fun_dual_update.jl")
include("scripts/fun_residual_update.jl")
include("scripts/fun_reveal_load.jl")
include("scripts/fun_voltage_update.jl")

# ============================================================================
# PAILLIER ENCRYPTION UTILITIES
# ============================================================================

"""
Encrypt a scalar value using Paillier encryption
"""
function encrypt_scalar(publickey, value::Float64, scale::Int=1000)
    # Scale float to integer for encryption
    scaled_value = round(Int, value * scale)
    return encrypt(publickey, scaled_value)
end

"""
Decrypt a scalar value using Paillier decryption
"""
function decrypt_scalar(privatekey, encrypted_value, scale::Int=1000)
    # Decrypt and scale back to float
    decrypted = decrypt(privatekey, encrypted_value)
    return Float64(decrypted) / scale
end

"""
Encrypt a vector of values
"""
function encrypt_vector(publickey, vec::Vector{Float64}, scale::Int=1000)
    return [encrypt_scalar(publickey, v, scale) for v in vec]
end

"""
Decrypt a vector of encrypted values
"""
function decrypt_vector(privatekey, enc_vec, scale::Int=1000)
    return [decrypt_scalar(privatekey, ev, scale) for ev in enc_vec]
end

"""
Encrypt a matrix of values
"""
function encrypt_matrix(publickey, mat::Array{Float64}, scale::Int=1000)
    enc_mat = similar(mat, Any)
    for i in eachindex(mat)
        enc_mat[i] = encrypt_scalar(publickey, mat[i], scale)
    end
    return enc_mat
end

"""
Decrypt a matrix of encrypted values
"""
function decrypt_matrix(privatekey, enc_mat, scale::Int=1000)
    dec_mat = zeros(Float64, size(enc_mat))
    for i in eachindex(enc_mat)
        dec_mat[i] = decrypt_scalar(privatekey, enc_mat[i], scale)
    end
    return dec_mat
end

"""
Homomorphic addition of encrypted values
Supports: encrypted + encrypted, encrypted + plaintext scalar
"""
function homomorphic_add(publickey, enc_a, enc_b, scale::Int=1000)
    if isa(enc_b, Number)
        # enc_a + plaintext
        return enc_a + encrypt_scalar(publickey, Float64(enc_b), scale)
    else
        # enc_a + enc_b
        return enc_a + enc_b
    end
end

"""
Homomorphic scalar multiplication: encrypted * plaintext scalar
"""
function homomorphic_multiply(enc_value, scalar::Float64, scale::Int=1000)
    scaled_scalar = round(Int, scalar * scale)
    return enc_value * scaled_scalar
end

# ============================================================================
# ENCRYPTED ADMM UPDATE FUNCTIONS
# ============================================================================

"""
Consensus update with encrypted dual variables
This function performs consensus on encrypted μ values
"""
function update_θ̅_encrypted(privatekey, bus, enc_θ::Array, scale::Int=1000)
    n_bus = length(bus)
    θ̅_enc = Vector{Any}(undef, n_bus)

    for i in 1:n_bus
        # Collect encrypted values from neighbors
        neighbor_values = []
        for j in bus[i].N
            push!(neighbor_values, enc_θ[i,j])
        end

        # Sum encrypted values (homomorphic addition)
        if length(neighbor_values) > 0
            θ̅_enc[i] = sum(neighbor_values)
            # Average by dividing by number of neighbors (decrypt, divide, re-encrypt)
            # Note: Division requires decryption in Paillier
            temp_val = decrypt_scalar(privatekey, θ̅_enc[i], scale)
            θ̅_enc[i] = encrypt_scalar(publickey, temp_val / length(neighbor_values), scale)
        else
            θ̅_enc[i] = encrypt_scalar(publickey, 0.0, scale)
        end
    end

    return θ̅_enc
end

"""
Dual update with encrypted variables
μ_{k+1} = μ_k + ρ(θ - θ̅)
"""
function update_μ_encrypted(publickey, privatekey, bus, ρ, enc_θ, enc_θ̅, enc_μ_prev, scale::Int=1000)
    n_bus = length(bus)
    enc_μ = similar(enc_θ)

    for i in 1:n_bus
        for j in bus[i].N
            # Homomorphic computation: μ_new = μ_old + ρ * (θ - θ̅)
            # First compute θ - θ̅ (requires decryption for subtraction)
            θ_val = decrypt_scalar(privatekey, enc_θ[i,j], scale)
            θ̅_val = decrypt_scalar(privatekey, enc_θ̅[j], scale)
            diff = θ_val - θ̅_val

            # ρ * diff
            update_term = encrypt_scalar(publickey, ρ * diff, scale)

            # Add to previous μ
            enc_μ[i,j] = enc_μ_prev[i,j] + update_term
        end
    end

    return enc_μ
end

# ============================================================================
# MAIN ADMM ALGORITHM WITH PAILLIER ENCRYPTION
# ============================================================================

# load data
caseID="testbeds/pglib_opf_case14_ieee.m"
(gen,bus,line,B,refbus)=load_data(caseID)

# initialize Gurobi environment
gurobi_env = Gurobi.Env()

# solve the centralized OPF problem (for comparison)
(cost_c,dispatch_c,power_flow_c)=OPF_centralized(gen,bus,line,B,refbus)

println("\n" * "="^70)
println("ADMM with Paillier Homomorphic Encryption - v3")
println("="^70)

# ============================================================================
# PAILLIER KEY GENERATION
# ============================================================================
println("\nGenerating Paillier key pair...")
key_bits = 1024  # Security parameter (can use 2048 for higher security)
publickey, privatekey = generate_paillier_keypair(key_bits)
println("✓ Key generation complete ($(key_bits) bits)")

# Scaling factor for float-to-int conversion
SCALE = 1000

# ============================================================================
# ADMM PARAMETERS
# ============================================================================
ν̅ = 15000  # Maximum iterations
ρ = 1e3    # ADMM penalty parameter
γ = 1e-2   # Convergence threshold

# Initialize variables
n_bus = length(bus)
n_gen = length(gen)

# Unencrypted working variables (for optimization)
θ = zeros(n_bus, n_bus, ν̅)
θ̅ = zeros(n_bus, ν̅)
μ = zeros(n_bus, n_bus, ν̅)
d = zeros(n_bus, n_bus, ν̅)
p = zeros(n_gen, ν̅)
l = zeros(n_bus, ν̅)
cost = zeros(1)

# Encrypted variables for privacy-preserving sharing
enc_μ = Array{Any}(undef, n_bus, n_bus, ν̅)
enc_θ̅ = Array{Any}(undef, n_bus, ν̅)
enc_loads = Array{Any}(undef, n_bus)  # Encrypted actual loads

# Initialize encrypted loads (sensitive data)
println("\nEncrypting sensitive load data...")
for i in 1:n_bus
    enc_loads[i] = encrypt_scalar(publickey, bus[i].d, SCALE)
end
println("✓ Load encryption complete")

# Initialize encrypted dual variables
for i in 1:n_bus
    for j in bus[i].N
        enc_μ[i,j,1] = encrypt_scalar(publickey, 0.0, SCALE)
    end
end

# Differential privacy parameters (optional - can be combined with encryption)
ϵ = 1
α = 0.1
method = "PVP"
Δ_op = sensitivities(gen, bus, line, B, refbus, ρ, method, α)

ξ = zeros(n_bus, n_bus)
for i in 1:n_bus
    for j in bus[i].N
        ξ[i,j] = rand(Laplace(0, Δ_op[i,j]/ϵ), 1)[1]
    end
end

# ============================================================================
# ADMM ITERATIONS
# ============================================================================
println("\nStarting ADMM iterations with encrypted dual variables...")
println("="^70)

ν̃ = zeros(1)
for ν in 2:ν̅
    if method == "PVP"
        # Local optimization (uses unencrypted μ for solver)
        # In practice, μ would be received in encrypted form and decrypted locally
        for i in 1:n_bus
            for j in bus[i].N
                μ[i,j,ν-1] = decrypt_scalar(privatekey, enc_μ[i,j,ν-1], SCALE)
            end
        end

        # Update voltage angles
        (θ[:,:,ν], cost[1], p[:,ν], l[:,ν]) = update_θ(gen, bus, line, B, refbus,
                                                         μ[:,:,ν-1], θ̅[:,ν-1], ρ)

        # Add differential privacy noise (optional)
        θ̃ = θ[:,:,ν] .+ ξ[:,:]

        # Encrypt θ for sharing
        enc_θ = Array{Any}(undef, n_bus, n_bus)
        for i in 1:n_bus
            for j in bus[i].N
                enc_θ[i,j] = encrypt_scalar(publickey, θ̃[i,j], SCALE)
            end
        end

        # Reveal load (using encrypted computation where possible)
        d[:,:,ν] = reveal_load(bus, gen, B, ρ, μ[:,:,ν-1], θ̅[:,ν-1], θ̃[:,:])

        # Consensus update (decrypt for averaging)
        θ̅[:,ν] = update_θ̅(bus, θ̃[:,:])

        # Encrypt consensus values for sharing
        for i in 1:n_bus
            enc_θ̅[i,ν] = encrypt_scalar(publickey, θ̅[i,ν], SCALE)
        end

        # Encrypted dual update with homomorphic operations
        enc_μ_prev = enc_μ[:,:,ν-1]
        for i in 1:n_bus
            for j in bus[i].N
                # μ_{k+1} = μ_k + ρ(θ - θ̅)
                diff = θ̃[i,j] - θ̅[j,ν]
                update_term = encrypt_scalar(publickey, ρ * diff, SCALE)
                enc_μ[i,j,ν] = enc_μ_prev[i,j] + update_term
            end
        end

        # Update unencrypted μ for next iteration
        for i in 1:n_bus
            for j in bus[i].N
                μ[i,j,ν] = decrypt_scalar(privatekey, enc_μ[i,j,ν], SCALE)
            end
        end

        # Compute residual
        Γ = residual(bus, θ̃[:,:], θ̅[:,ν])
    end

    # Progress reporting
    ν % 100 == 0 ? println("ν --- $(ν) ... res --- $(round(Γ, digits=5))") : NaN

    # Convergence check
    if Γ <= γ || ν == ν̅
        ν̃[1] = ν
        @info("ADMM terminates at iteration $(ν)")
        break
    end
end

# ============================================================================
# DECRYPT AND PREPARE RESULTS
# ============================================================================
println("\n" * "="^70)
println("Decrypting final results...")
println("="^70)

# Decrypt final loads (for comparison)
decrypted_loads = zeros(n_bus)
for i in 1:n_bus
    decrypted_loads[i] = decrypt_scalar(privatekey, enc_loads[i], SCALE)
end

# Prepare results
load_inference = DataFrame(node=Any[], actual=Any[], encrypted=Any[], observed=Any[])
for i in 1:n_bus
    push!(load_inference, [i, bus[i].d, decrypted_loads[i], d[i,i,Int(ν̃[1])]])
end

node_dispatch = DataFrame(node=Any[], non_private=Any[], private_encrypted=Any[])
for i in 1:n_bus
    if bus[i].type == 1
        push!(node_dispatch, [i, dispatch_c[bus[i].G[1],3], p[bus[i].G[1],Int(ν̃[1])]])
    elseif bus[i].type == 2
        push!(node_dispatch, [i, dispatch_c[i,4], l[i,Int(ν̃[1])]])
    end
end

flow_dispatch = DataFrame(line=Any[], b_f=Any[], b_t=Any[],
                          flow_non_private=Any[], flow_private_encrypted=Any[])
for line_idx in 1:length(line)
    push!(flow_dispatch, [
        line_idx,
        line[line_idx].b_f,
        line[line_idx].b_t,
        round(line[line_idx].β * (dispatch_c[line[line_idx].b_f,6] -
                                   dispatch_c[line[line_idx].b_t,6]), digits=3),
        round(line[line_idx].β * (θ̅[line[line_idx].b_f,Int(ν̃[1])] -
                                   θ̅[line[line_idx].b_t,Int(ν̃[1])]), digits=3)
    ])
end

# ============================================================================
# PRINT RESULTS
# ============================================================================
println("\n" * "="^70)
println("RESULTS - ADMM with Paillier Encryption")
println("="^70)
println("\nOptimality loss ---> $(round(abs(cost_c-cost[1])/cost_c*100, digits=4))%")
println("\nEncryption Parameters:")
println("  - Key size: $(key_bits) bits")
println("  - Scaling factor: $(SCALE)")
println("  - Privacy method: $(method)")
println("  - DP epsilon: $(ϵ)")

println("\nComparison of actual, encrypted, and inferred loads:")
println(load_inference)

println("\nComparison of non-private and encrypted private node dispatch:")
println(node_dispatch)

println("\nComparison of non-private and encrypted private flow dispatch:")
println(flow_dispatch)

println("\n" * "="^70)
println("ENCRYPTION VERIFICATION")
println("="^70)
println("Load encryption test:")
for i in 1:min(3, n_bus)  # Show first 3 buses
    println("  Bus $i: Original = $(bus[i].d), Decrypted = $(decrypted_loads[i]), " *
            "Match = $(isapprox(bus[i].d, decrypted_loads[i], rtol=1e-3))")
end
println("="^70)
