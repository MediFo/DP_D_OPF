"""
Paillier Homomorphic Encryption Implementation for Julia
Supports homomorphic addition and scalar multiplication
"""

using Random
using Primes

mutable struct PaillierPublicKey
    n::BigInt      # modulus
    n_sq::BigInt   # n^2
    g::BigInt      # generator (typically n+1)

    function PaillierPublicKey(n::BigInt)
        new(n, n^2, n + 1)
    end
end

mutable struct PaillierPrivateKey
    λ::BigInt      # λ = lcm(p-1, q-1)
    μ::BigInt      # μ = (L(g^λ mod n^2))^(-1) mod n

    function PaillierPrivateKey(λ::BigInt, μ::BigInt)
        new(λ, μ)
    end
end

mutable struct PaillierKeypair
    public_key::PaillierPublicKey
    private_key::PaillierPrivateKey
end

mutable struct EncryptedNumber
    ciphertext::BigInt
    public_key::PaillierPublicKey

    function EncryptedNumber(ciphertext::BigInt, public_key::PaillierPublicKey)
        new(mod(ciphertext, public_key.n_sq), public_key)
    end
end

# L function: L(x) = (x-1)/n
function L(x::BigInt, n::BigInt)::BigInt
    return div(x - 1, n)
end

# Extended Euclidean Algorithm for modular inverse
function invmod_custom(a::BigInt, m::BigInt)::BigInt
    return invmod(a, m)
end

"""
Generate Paillier keypair with specified bit length
"""
function generate_paillier_keypair(n_length::Int=2048)::PaillierKeypair
    # Generate two large primes p and q
    bit_length = div(n_length, 2)

    println("  🔐 Generating $(bit_length)-bit primes...")
    p = nextprime(rand(BigInt(2)^(bit_length-1):BigInt(2)^bit_length))
    q = nextprime(rand(BigInt(2)^(bit_length-1):BigInt(2)^bit_length))

    # Ensure p ≠ q
    while p == q
        q = nextprime(rand(BigInt(2)^(bit_length-1):BigInt(2)^bit_length))
    end

    # Compute n = p * q
    n = p * q
    n_sq = n^2

    # g = n + 1 (simplified version)
    g = n + 1

    # Compute λ = lcm(p-1, q-1)
    λ = lcm(p - 1, q - 1)

    # Compute μ = (L(g^λ mod n^2))^(-1) mod n
    g_lambda = powermod(g, λ, n_sq)
    μ = invmod_custom(L(g_lambda, n), n)

    public_key = PaillierPublicKey(n)
    private_key = PaillierPrivateKey(λ, μ)

    return PaillierKeypair(public_key, private_key)
end

"""
Encrypt a number using Paillier public key
"""
function encrypt(public_key::PaillierPublicKey, plaintext::Real)::EncryptedNumber
    # Convert to integer (scale floating point)
    m = BigInt(round(plaintext * 1e6))  # Scale by 10^6 for precision

    # Ensure m < n
    if m >= public_key.n
        error("Plaintext is too large for this key size")
    end

    # Handle negative numbers
    if m < 0
        m = public_key.n + m
    end

    # Generate random r in [1, n)
    r = rand(BigInt(1):public_key.n-1)

    # Compute ciphertext: c = g^m * r^n mod n^2
    # Using g = n+1: g^m mod n^2 = (1 + m*n) mod n^2
    gm = mod(1 + m * public_key.n, public_key.n_sq)
    rn = powermod(r, public_key.n, public_key.n_sq)
    c = mod(gm * rn, public_key.n_sq)

    return EncryptedNumber(c, public_key)
end

"""
Decrypt an encrypted number using Paillier private key
"""
function decrypt(public_key::PaillierPublicKey, private_key::PaillierPrivateKey,
                 encrypted::EncryptedNumber)::Float64
    # Compute m = L(c^λ mod n^2) * μ mod n
    c_lambda = powermod(encrypted.ciphertext, private_key.λ, public_key.n_sq)
    m = mod(L(c_lambda, public_key.n) * private_key.μ, public_key.n)

    # Handle negative numbers (if m > n/2, it's negative)
    if m > div(public_key.n, 2)
        m = m - public_key.n
    end

    # Convert back to float (unscale)
    return Float64(m) / 1e6
end

"""
Homomorphic addition: E(a) + E(b) = E(a + b)
"""
function Base.:+(a::EncryptedNumber, b::EncryptedNumber)::EncryptedNumber
    if a.public_key !== b.public_key
        error("Cannot add encrypted numbers with different public keys")
    end

    # E(a) * E(b) mod n^2 = E(a + b)
    result = mod(a.ciphertext * b.ciphertext, a.public_key.n_sq)
    return EncryptedNumber(result, a.public_key)
end

"""
Homomorphic scalar multiplication: k * E(a) = E(k * a)
"""
function Base.:*(k::Real, enc::EncryptedNumber)::EncryptedNumber
    # Scale and convert to integer
    k_scaled = BigInt(round(k * 1e6))

    # Handle negative scalar
    if k_scaled < 0
        k_scaled = enc.public_key.n + k_scaled
    end

    # E(a)^k mod n^2 = E(k * a)
    result = powermod(enc.ciphertext, k_scaled, enc.public_key.n_sq)
    return EncryptedNumber(result, enc.public_key)
end

"""
Homomorphic subtraction: E(a) - E(b) = E(a - b)
"""
function Base.:-(a::EncryptedNumber, b::EncryptedNumber)::EncryptedNumber
    # E(a) * E(b)^(-1) mod n^2 = E(a - b)
    b_inv = invmod_custom(b.ciphertext, a.public_key.n_sq)
    result = mod(a.ciphertext * b_inv, a.public_key.n_sq)
    return EncryptedNumber(result, a.public_key)
end

"""
Encrypt a vector of numbers
"""
function encrypt_vector(public_key::PaillierPublicKey, vec::Vector{<:Real})::Vector{EncryptedNumber}
    return [encrypt(public_key, v) for v in vec]
end

"""
Decrypt a vector of encrypted numbers
"""
function decrypt_vector(public_key::PaillierPublicKey, private_key::PaillierPrivateKey,
                       enc_vec::Vector{EncryptedNumber})::Vector{Float64}
    return [decrypt(public_key, private_key, e) for e in enc_vec]
end

"""
Homomorphic sum of encrypted numbers
"""
function encrypted_sum(enc_vec::Vector{EncryptedNumber})::EncryptedNumber
    result = enc_vec[1]
    for i in 2:length(enc_vec)
        result = result + enc_vec[i]
    end
    return result
end

"""
Homomorphic average: (1/n) * sum(E(values)) = E(average)
"""
function encrypted_average(enc_vec::Vector{EncryptedNumber})::EncryptedNumber
    sum_enc = encrypted_sum(enc_vec)
    n = length(enc_vec)
    # Scalar division: multiply by 1/n
    return (1.0 / n) * sum_enc
end

println("✓ Paillier cryptography module loaded")
