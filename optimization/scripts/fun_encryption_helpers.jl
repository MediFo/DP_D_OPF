"""
Encryption helper functions for SPARSE ADMM
Handles encryption/decryption of sparse θ dictionaries
"""

function encrypt_θ_sparse(public_key, bus, θ_sparse::Dict{Tuple{Int,Int}, Float64})
    """
    Encrypt all θ[( i,j)] values in sparse dictionary

    Args:
        public_key: Paillier public key
        bus: Network bus data
        θ_sparse: Sparse primal variables

    Returns:
        θ_enc: Encrypted sparse dictionary
    """
    θ_enc = Dict{Tuple{Int,Int}, EncryptedNumber}()

    for i in 1:length(bus)
        for j in bus[i].N
            if haskey(θ_sparse, (i,j))
                θ_enc[(i,j)] = encrypt(public_key, θ_sparse[(i,j)])
            end
        end
    end

    return θ_enc
end
