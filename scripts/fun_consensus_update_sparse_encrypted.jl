"""
SPARSE + ENCRYPTED version of consensus update
Based on: scripts/fun_consensus_update.jl (original DP_D_OPF)

Differences:
1. Works with sparse Dict{Tuple{Int,Int}, Float64} instead of dense matrix
2. Adds homomorphic encryption support
3. Same mathematical formula as original: θ̅[i] = sum(θ[j,i])/|N(i)|
"""

function update_θ̅_sparse(bus, θ_sparse::Dict{Tuple{Int,Int}, Float64})
    """
    SPARSE consensus update (no encryption)

    Boyd's consensus ADMM: average θ[j,i] over all neighbors j ∈ N(i)
    Formula: θ̅[i] = (1/|N(i)|) * Σ_{j∈N(i)} θ[j,i]

    Args:
        bus: Network bus data
        θ_sparse: Sparse dictionary θ[(i,j)] for i's estimate of θ_j

    Returns:
        θ̅: Consensus variables (dense vector)
    """
    Nb = length(bus)
    θ̅ = zeros(Nb)

    for i in 1:Nb
        # Original DP_D_OPF formula (line 14 in fun_consensus_update.jl):
        # θ̅[i] = sum(θ[j,i] for j in bus[i].N)/length(bus[i].N)
        θ̅[i] = sum(θ_sparse[(j,i)] for j in bus[i].N) / length(bus[i].N)
    end

    return θ̅
end

function update_θ̅_homomorphic_sparse(public_key, private_key, bus, θ_enc::Dict{Tuple{Int,Int}, EncryptedNumber})
    """
    SPARSE consensus update with homomorphic encryption

    Same as update_θ̅_sparse but operates on encrypted values
    Uses Paillier homomorphic addition for privacy-preserving averaging

    Args:
        public_key, private_key: Paillier keys
        bus: Network bus data
        θ_enc: Encrypted sparse dictionary

    Returns:
        θ̅_plain: Decrypted consensus (for local use)
        θ̅_enc: Encrypted consensus (for sharing)
    """
    Nb = length(bus)
    θ̅_enc = Vector{Union{EncryptedNumber, Nothing}}(nothing, Nb)
    θ̅_plain = zeros(Nb)

    for i in 1:Nb
        # Collect encrypted neighbors: E(θ[j,i]) for j ∈ N(i)
        enc_neighbors = EncryptedNumber[]
        for j in bus[i].N
            if haskey(θ_enc, (j,i))
                push!(enc_neighbors, θ_enc[(j,i)])
            end
        end

        if !isempty(enc_neighbors)
            # Homomorphic averaging: E(θ̅[i]) = (1/|N|) * Σ E(θ[j,i])
            θ̅_enc[i] = encrypted_average(enc_neighbors)
            # Decrypt for local use
            θ̅_plain[i] = decrypt(public_key, private_key, θ̅_enc[i])
        end
    end

    return θ̅_plain, θ̅_enc
end
