"""
MPC Client for Encrypted Computation
Julia conversion of client.py from MPC-with-PHE repository
Provides high-level interface for encrypted operations on OPF data
"""

include("mpc_phe_util.jl")
include("mpc_phe_paillier.jl")

# ============================================================================
# CLIENT CLASS FOR ENCRYPTED OPERATIONS
# ============================================================================

"""
    MPCClient

Client for performing encrypted MPC operations.
Manages keys and provides encryption/decryption of OPF variables.

Fields:
- pubkey::PaillierPublicKey - public key for encryption
- privkey::PaillierPrivateKey - private key for decryption
- precision::Int - fixed-point precision (bits for fractional part)
- keysize::Int - key size in bits
"""
mutable struct MPCClient
    pubkey::PaillierPublicKey
    privkey::PaillierPrivateKey
    precision::Int
    keysize::Int

    """
        MPCClient(; keysize=DEFAULT_KEYSIZE, precision=DEFAULT_PRECISION, load_keys=false, keys_dir="Keys")

    Initialize MPC client with Paillier keys.

    Args:
    - keysize: RSA modulus size in bits (default: 1024)
    - precision: Fixed-point precision in bits (default: 32)
    - load_keys: Try to load keys from files (default: false)
    - keys_dir: Directory for key files (default: "Keys")
    """
    function MPCClient(; keysize::Int=DEFAULT_KEYSIZE,
                        precision::Int=DEFAULT_PRECISION,
                        load_keys::Bool=false,
                        keys_dir::String="Keys")

        pubkey, privkey = nothing, nothing

        if load_keys
            try
                # Try to load keys from files
                mkpath(keys_dir)
                pubkey_file = joinpath(keys_dir, "pubkey$(keysize).txt")
                privkey_file = joinpath(keys_dir, "privkey$(keysize).txt")

                if isfile(pubkey_file) && isfile(privkey_file)
                    # Load public key
                    n = parse(BigInt, strip(read(pubkey_file, String)))
                    pubkey = PaillierPublicKey(n)

                    # Load private key
                    priv_data = split(strip(read(privkey_file, String)), '\n')
                    p = parse(BigInt, strip(priv_data[1]))
                    q = parse(BigInt, strip(priv_data[2]))
                    privkey = PaillierPrivateKey(pubkey, p, q)

                    println("✓ Loaded $(keysize)-bit keys from $keys_dir")
                else
                    throw(ErrorException("Key files not found"))
                end
            catch e
                println("⚠ Could not load keys: $e")
                println("  Generating new keys...")
                load_keys = false
            end
        end

        if !load_keys
            # Generate new keys
            println("  Generating $(keysize)-bit Paillier keypair...")
            pubkey, privkey = generate_paillier_keypair(n_length=keysize)

            # Save keys to files
            try
                mkpath(keys_dir)
                pubkey_file = joinpath(keys_dir, "pubkey$(keysize).txt")
                privkey_file = joinpath(keys_dir, "privkey$(keysize).txt")

                write(pubkey_file, string(pubkey.n))
                write(privkey_file, "$(privkey.p)\n$(privkey.q)")

                println("✓ Keys saved to $keys_dir")
            catch e
                println("⚠ Could not save keys: $e")
            end
        end

        new(pubkey, privkey, precision, keysize)
    end
end

# ============================================================================
# ENCRYPTION/DECRYPTION OF OPF VARIABLES
# ============================================================================

"""
    encrypt_scalar(client::MPCClient, value::Real)

Encrypt a scalar value using fixed-point encoding.
"""
function encrypt_scalar(client::MPCClient, value::Real)
    encoded = fp(value, client.precision)
    return encrypt(client.pubkey, encoded)
end

"""
    decrypt_scalar(client::MPCClient, enc_value::EncryptedNumber)

Decrypt a scalar value and decode from fixed-point.
"""
function decrypt_scalar(client::MPCClient, enc_value::EncryptedNumber)
    decrypted = decrypt(client.privkey, enc_value)
    return retrieve_fp(decrypted, client.precision)
end

"""
    encrypt_opf_vector(client::MPCClient, vec::AbstractVector)

Encrypt a vector of OPF variables (e.g., loads, voltage angles).
"""
function encrypt_opf_vector(client::MPCClient, vec::AbstractVector)
    encoded = fp_vector(vec, client.precision)
    return encrypt_vector(client.pubkey, encoded)
end

"""
    decrypt_opf_vector(client::MPCClient, enc_vec::AbstractVector{EncryptedNumber})

Decrypt a vector of encrypted OPF variables.
"""
function decrypt_opf_vector(client::MPCClient, enc_vec::AbstractVector{EncryptedNumber})
    decrypted = decrypt_vector(client.privkey, enc_vec)
    return retrieve_fp_vector(decrypted, client.precision)
end

"""
    encrypt_opf_matrix(client::MPCClient, mat::AbstractMatrix)

Encrypt a matrix of OPF variables.
"""
function encrypt_opf_matrix(client::MPCClient, mat::AbstractMatrix)
    m, n = size(mat)
    enc_mat = Matrix{EncryptedNumber}(undef, m, n)

    for i in 1:m
        for j in 1:n
            enc_mat[i,j] = encrypt_scalar(client, mat[i,j])
        end
    end

    return enc_mat
end

"""
    decrypt_opf_matrix(client::MPCClient, enc_mat::AbstractMatrix{EncryptedNumber})

Decrypt a matrix of encrypted OPF variables.
"""
function decrypt_opf_matrix(client::MPCClient, enc_mat::AbstractMatrix{EncryptedNumber})
    m, n = size(enc_mat)
    dec_mat = zeros(Float64, m, n)

    for i in 1:m
        for j in 1:n
            dec_mat[i,j] = decrypt_scalar(client, enc_mat[i,j])
        end
    end

    return dec_mat
end

"""
    encrypt_sparse_matrix(client::MPCClient, bus, mat::AbstractMatrix)

Encrypt only the non-zero entries corresponding to network neighbors.
Efficient for sparse power network topology.
"""
function encrypt_sparse_matrix(client::MPCClient, bus, mat::AbstractMatrix)
    n_bus = length(bus)
    enc_mat = Matrix{Union{EncryptedNumber,Nothing}}(nothing, n_bus, n_bus)

    for i in 1:n_bus
        for j in bus[i].N  # Only neighbors
            enc_mat[i,j] = encrypt_scalar(client, mat[i,j])
        end
    end

    return enc_mat
end

"""
    decrypt_sparse_matrix(client::MPCClient, bus, enc_mat)

Decrypt sparse encrypted matrix.
"""
function decrypt_sparse_matrix(client::MPCClient, bus, enc_mat)
    n_bus = length(bus)
    dec_mat = zeros(Float64, n_bus, n_bus)

    for i in 1:n_bus
        for j in bus[i].N
            if enc_mat[i,j] !== nothing
                dec_mat[i,j] = decrypt_scalar(client, enc_mat[i,j])
            end
        end
    end

    return dec_mat
end

# ============================================================================
# HOMOMORPHIC OPERATIONS FOR ADMM
# ============================================================================

"""
    homomorphic_dual_update(client::MPCClient, enc_μ_prev::EncryptedNumber,
                           θ::Real, θ̅::Real, ρ::Real)

Compute encrypted dual update: E(μ_new) = E(μ_prev) + E(ρ * (θ - θ̅))
Uses homomorphic addition.
"""
function homomorphic_dual_update(client::MPCClient, enc_μ_prev::EncryptedNumber,
                                 θ::Real, θ̅::Real, ρ::Real)
    # Compute update value
    update_val = ρ * (θ - θ̅)

    # Encrypt update
    enc_update = encrypt_scalar(client, update_val)

    # Homomorphic addition
    return enc_μ_prev + enc_update
end

"""
    homomorphic_sum(enc_values::AbstractVector{EncryptedNumber})

Compute homomorphic sum of encrypted values.
"""
function homomorphic_sum(enc_values::AbstractVector{EncryptedNumber})
    if isempty(enc_values)
        error("Cannot sum empty vector")
    end

    result = enc_values[1]
    for i in 2:length(enc_values)
        result = result + enc_values[i]
    end

    return result
end

"""
    homomorphic_average(client::MPCClient, enc_values::AbstractVector{EncryptedNumber})

Compute encrypted average by summing then dividing by count.
Note: Division requires decryption, then re-encryption.
"""
function homomorphic_average(client::MPCClient, enc_values::AbstractVector{EncryptedNumber})
    if isempty(enc_values)
        error("Cannot average empty vector")
    end

    # Sum encrypted values (homomorphic)
    enc_sum = homomorphic_sum(enc_values)

    # Decrypt sum
    sum_val = decrypt_scalar(client, enc_sum)

    # Compute average
    avg_val = sum_val / length(enc_values)

    # Re-encrypt average
    return encrypt_scalar(client, avg_val)
end

"""
    homomorphic_weighted_sum(enc_values::AbstractVector{EncryptedNumber},
                            weights::AbstractVector{<:Real})

Compute weighted sum: Σ(wᵢ * E(xᵢ)) = E(Σ(wᵢ * xᵢ))
Uses homomorphic scalar multiplication.
"""
function homomorphic_weighted_sum(client::MPCClient,
                                 enc_values::AbstractVector{EncryptedNumber},
                                 weights::AbstractVector{<:Real})
    if length(enc_values) != length(weights)
        error("Lengths must match")
    end

    # Convert weights to fixed-point integers
    weight_ints = [BigInt(round(w * (2^client.precision))) for w in weights]

    # Compute weighted terms
    result = enc_values[1] * weight_ints[1]
    for i in 2:length(enc_values)
        result = result + (enc_values[i] * weight_ints[i])
    end

    return result
end

# ============================================================================
# QUANTIZATION HELPERS
# ============================================================================

"""
    quantize_scalar(value::Real, prec::Int=DEFAULT_PRECISION)

Quantize a scalar to fixed-point precision (for testing).
"""
function quantize_scalar(value::Real, prec::Int=DEFAULT_PRECISION)
    return Q_s(value, prec)
end

"""
    quantize_vector(vec::AbstractVector, prec::Int=DEFAULT_PRECISION)

Quantize a vector to fixed-point precision.
"""
function quantize_vector(vec::AbstractVector, prec::Int=DEFAULT_PRECISION)
    return Q_vector(vec, prec)
end

"""
    quantize_matrix(mat::AbstractMatrix, prec::Int=DEFAULT_PRECISION)

Quantize a matrix to fixed-point precision.
"""
function quantize_matrix(mat::AbstractMatrix, prec::Int=DEFAULT_PRECISION)
    return Q_matrix(mat, prec)
end

# ============================================================================
# EXPORTS
# ============================================================================

export MPCClient
export encrypt_scalar, decrypt_scalar
export encrypt_opf_vector, decrypt_opf_vector
export encrypt_opf_matrix, decrypt_opf_matrix
export encrypt_sparse_matrix, decrypt_sparse_matrix
export homomorphic_dual_update, homomorphic_sum, homomorphic_average, homomorphic_weighted_sum
export quantize_scalar, quantize_vector, quantize_matrix

println("✓ MPC-PHE Client Module Loaded")
