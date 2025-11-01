"""
Paillier Homomorphic Encryption Library for Julia
Adapted from MPC-with-PHE repository (https://github.com/andreea-alexandru/MPC-with-PHE)
Original Python implementation converted to Julia

This module implements the Paillier cryptosystem for partially homomorphic encryption,
supporting encrypted addition and scalar multiplication operations.
"""

using Random
using Primes

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

"""
    powmod(a, b, c)

Compute (a^b) mod c efficiently using modular exponentiation.
"""
function powmod(a::Integer, b::Integer, c::Integer)
    if a == 1
        return 1
    end
    return powermod(a, b, c)  # Julia built-in
end

"""
    modinv(a, b)

Compute the multiplicative inverse of a modulo b.
Returns x such that (a * x) ≡ 1 (mod b)
"""
function modinv(a::Integer, b::Integer)
    return invmod(a, b)  # Julia built-in
end

"""
    getprimeover(N)

Generate a random prime number with N bits.
"""
function getprimeover(N::Integer)
    # Generate random N-bit number
    randbits = rand(Random.RandomDevice(), big(2)^(N-1):big(2)^N-1)
    # Find next prime
    return nextprime(randbits)
end

"""
    isqrt_custom(n)

Compute integer square root of n.
"""
function isqrt_custom(n::Integer)
    if n == 0
        return 0
    end
    return isqrt(n)  # Julia built-in
end

# ============================================================================
# PAILLIER PUBLIC KEY
# ============================================================================

"""
    PaillierPublicKey

Represents a Paillier public key.

Fields:
- `n::BigInt`: The modulus (product of two primes p and q)
- `g::BigInt`: Generator (typically n + 1)
- `nsquare::BigInt`: n^2, precomputed for efficiency
- `max_int::BigInt`: Maximum safe integer value
"""
mutable struct PaillierPublicKey
    n::BigInt
    g::BigInt
    nsquare::BigInt
    max_int::BigInt

    function PaillierPublicKey(n::BigInt)
        g = n + 1
        nsquare = n * n
        max_int = div(n, 3) - 1
        new(n, g, nsquare, max_int)
    end
end

"""
    get_random_lt_n(public_key::PaillierPublicKey)

Generate a cryptographically random number less than n.
"""
function get_random_lt_n(public_key::PaillierPublicKey)
    return rand(Random.RandomDevice(), big(1):public_key.n-1)
end

"""
    raw_encrypt(public_key::PaillierPublicKey, plaintext::Integer, r_value=nothing)

Perform raw Paillier encryption of a positive integer plaintext < n.

Args:
- `public_key`: The public key to use for encryption
- `plaintext`: Integer to encrypt (must be < n)
- `r_value`: Optional pre-computed randomness (r^n mod n^2)

Returns:
- Ciphertext as BigInt
"""
function raw_encrypt(public_key::PaillierPublicKey, plaintext::Integer, r_value=nothing)
    n = public_key.n
    nsquare = public_key.nsquare
    max_int = public_key.max_int

    # Handle negative numbers by converting to positive representation
    if plaintext < 0
        plaintext = plaintext + n
    end

    # Compute nude ciphertext
    if n - max_int <= plaintext < n
        # Very large plaintext, use inverse shortcut
        neg_plaintext = n - plaintext
        neg_ciphertext = (n * neg_plaintext + 1) % nsquare
        nude_ciphertext = modinv(neg_ciphertext, nsquare)
    else
        # Standard case: g^plaintext = (n+1)^plaintext = n*plaintext + 1 mod n^2
        nude_ciphertext = (n * plaintext + 1) % nsquare
    end

    # Apply obfuscation
    if r_value === nothing
        r = get_random_lt_n(public_key)
        obfuscator = powmod(r, n, nsquare)
    else
        obfuscator = r_value
    end

    return (nude_ciphertext * obfuscator) % nsquare
end

# ============================================================================
# PAILLIER PRIVATE KEY
# ============================================================================

"""
    PaillierPrivateKey

Represents a Paillier private key.

Fields:
- `public_key::PaillierPublicKey`: The corresponding public key
- `p::BigInt`: First prime factor
- `q::BigInt`: Second prime factor
- `psquare::BigInt`: p^2
- `qsquare::BigInt`: q^2
- `p_inverse::BigInt`: p^(-1) mod q
- `hp::BigInt`: h(p) for decryption
- `hq::BigInt`: h(q) for decryption
"""
mutable struct PaillierPrivateKey
    public_key::PaillierPublicKey
    p::BigInt
    q::BigInt
    psquare::BigInt
    qsquare::BigInt
    p_inverse::BigInt
    hp::BigInt
    hq::BigInt
    n::BigInt

    function PaillierPrivateKey(public_key::PaillierPublicKey, p::BigInt, q::BigInt)
        if p * q != public_key.n
            error("Given public key does not match the given p and q")
        end
        if p == q
            error("p and q must be different")
        end

        # Ensure p < q
        if q < p
            p, q = q, p
        end

        psquare = p * p
        qsquare = q * q
        p_inverse = modinv(p, q)

        # Compute h functions
        hp = h_function(public_key, p, psquare)
        hq = h_function(public_key, q, qsquare)

        new(public_key, p, q, psquare, qsquare, p_inverse, hp, hq, public_key.n)
    end
end

"""
    l_function(x::Integer, p::Integer)

Compute the L function: L(x,p) = (x-1)/p
"""
function l_function(x::Integer, p::Integer)
    return div(x - 1, p)
end

"""
    h_function(public_key::PaillierPublicKey, x::BigInt, xsquare::BigInt)

Compute the h-function for decryption using Chinese Remainder Theorem.
"""
function h_function(public_key::PaillierPublicKey, x::BigInt, xsquare::BigInt)
    g_pow = powmod(public_key.g, x - 1, xsquare)
    l_val = l_function(g_pow, x)
    return modinv(l_val, x)
end

"""
    crt(private_key::PaillierPrivateKey, mp::Integer, mq::Integer)

Chinese Remainder Theorem: compute solution modulo n = p*q.

Args:
- `mp`: Solution modulo p
- `mq`: Solution modulo q

Returns:
- Solution modulo n
"""
function crt(private_key::PaillierPrivateKey, mp::Integer, mq::Integer)
    u = ((mq - mp) * private_key.p_inverse) % private_key.q
    return mp + (u * private_key.p)
end

"""
    raw_decrypt(private_key::PaillierPrivateKey, ciphertext::Integer)

Decrypt raw ciphertext and return raw plaintext.

Args:
- `private_key`: The private key to use for decryption
- `ciphertext`: Encrypted value

Returns:
- Decrypted plaintext as Integer
"""
function raw_decrypt(private_key::PaillierPrivateKey, ciphertext::Integer)
    p = private_key.p
    q = private_key.q
    psquare = private_key.psquare
    qsquare = private_key.qsquare
    n = private_key.n

    # Decrypt using CRT
    decrypt_to_p = (l_function(powmod(ciphertext, p-1, psquare), p) * private_key.hp) % p
    decrypt_to_q = (l_function(powmod(ciphertext, q-1, qsquare), q) * private_key.hq) % q

    value = crt(private_key, decrypt_to_p, decrypt_to_q)

    # Handle negative numbers
    if value < div(n, 3)
        return value
    else
        return value - n
    end
end

# ============================================================================
# ENCRYPTED NUMBER
# ============================================================================

"""
    EncryptedNumber

Represents an encrypted number with homomorphic properties.

Fields:
- `public_key::PaillierPublicKey`: The public key used for encryption
- `ciphertext::BigInt`: The encrypted value
- `is_obfuscated::Bool`: Whether the ciphertext has been obfuscated
"""
mutable struct EncryptedNumber
    public_key::PaillierPublicKey
    ciphertext::BigInt
    is_obfuscated::Bool

    function EncryptedNumber(public_key::PaillierPublicKey, ciphertext::BigInt)
        new(public_key, ciphertext, false)
    end
end

"""
    obfuscate!(enc::EncryptedNumber)

Obfuscate ciphertext by multiplying with r^n for random r.
This must be done before sharing with untrusted parties.
"""
function obfuscate!(enc::EncryptedNumber)
    r = get_random_lt_n(enc.public_key)
    r_pow_n = powmod(r, enc.public_key.n, enc.public_key.nsquare)
    enc.ciphertext = (enc.ciphertext * r_pow_n) % enc.public_key.nsquare
    enc.is_obfuscated = true
    return enc
end

"""
    get_ciphertext(enc::EncryptedNumber; be_secure=true)

Get the ciphertext, obfuscating if necessary for security.
"""
function get_ciphertext(enc::EncryptedNumber; be_secure=true)
    if be_secure && !enc.is_obfuscated
        obfuscate!(enc)
    end
    return enc.ciphertext
end

# ============================================================================
# HOMOMORPHIC OPERATIONS
# ============================================================================

"""
    Base.:+(a::EncryptedNumber, b::EncryptedNumber)

Homomorphic addition: E(a) + E(b) = E(a + b)
"""
function Base.:+(a::EncryptedNumber, b::EncryptedNumber)
    if a.public_key != b.public_key
        error("Cannot add numbers encrypted with different keys")
    end

    sum_ciphertext = (get_ciphertext(a, be_secure=false) *
                      get_ciphertext(b, be_secure=false)) % a.public_key.nsquare
    return EncryptedNumber(a.public_key, sum_ciphertext)
end

"""
    Base.:+(enc::EncryptedNumber, scalar::Number)

Add plaintext scalar to encrypted number: E(a) + b = E(a + b)
"""
function Base.:+(enc::EncryptedNumber, scalar::Number)
    scalar_int = BigInt(round(scalar))
    if scalar_int < 0
        scalar_int = scalar_int + enc.public_key.n
    end

    encrypted_scalar = raw_encrypt(enc.public_key, scalar_int, 1)
    sum_ciphertext = (get_ciphertext(enc, be_secure=false) * encrypted_scalar) % enc.public_key.nsquare
    return EncryptedNumber(enc.public_key, sum_ciphertext)
end

Base.:+(scalar::Number, enc::EncryptedNumber) = enc + scalar

"""
    Base.:*(enc::EncryptedNumber, scalar::Integer)

Homomorphic scalar multiplication: E(a) * b = E(a * b)
"""
function Base.:*(enc::EncryptedNumber, scalar::Integer)
    scalar_int = BigInt(scalar)
    if scalar_int < 0
        scalar_int = scalar_int + enc.public_key.n
    end

    if scalar_int < 0 || scalar_int >= enc.public_key.n
        error("Scalar out of bounds")
    end

    # Handle very large scalars
    if enc.public_key.n - enc.public_key.max_int <= scalar_int
        neg_c = modinv(get_ciphertext(enc, be_secure=false), enc.public_key.nsquare)
        neg_scalar = enc.public_key.n - scalar_int
        product = powmod(neg_c, neg_scalar, enc.public_key.nsquare)
    else
        product = powmod(get_ciphertext(enc, be_secure=false), scalar_int, enc.public_key.nsquare)
    end

    return EncryptedNumber(enc.public_key, product)
end

Base.:*(scalar::Integer, enc::EncryptedNumber) = enc * scalar

"""
    Base.:-(a::EncryptedNumber, b::Union{EncryptedNumber,Number})

Homomorphic subtraction
"""
function Base.:-(a::EncryptedNumber, b::Union{EncryptedNumber,Number})
    if isa(b, EncryptedNumber)
        return a + (b * -1)
    else
        return a + (-b)
    end
end

# ============================================================================
# KEY GENERATION
# ============================================================================

"""
    generate_paillier_keypair(; n_length=1024)

Generate a new Paillier public/private key pair.

Args:
- `n_length`: Key size in bits (default: 1024)

Returns:
- Tuple of (PaillierPublicKey, PaillierPrivateKey)
"""
function generate_paillier_keypair(; n_length::Integer=1024)
    p = q = n = nothing
    n_len = 0

    # Generate primes until we get the desired bit length
    while n_len != n_length
        p = getprimeover(div(n_length, 2))
        q = p
        while q == p
            q = getprimeover(div(n_length, 2))
        end
        n = p * q
        n_len = ndigits(n, base=2)
    end

    public_key = PaillierPublicKey(n)
    private_key = PaillierPrivateKey(public_key, p, q)

    return public_key, private_key
end

# ============================================================================
# ENCRYPTION/DECRYPTION INTERFACE
# ============================================================================

"""
    encrypt(public_key::PaillierPublicKey, value::Integer; r_value=nothing)

Encrypt an integer value.

Args:
- `public_key`: Public key for encryption
- `value`: Integer to encrypt
- `r_value`: Optional pre-computed randomness

Returns:
- EncryptedNumber
"""
function encrypt(public_key::PaillierPublicKey, value::Integer; r_value=nothing)
    obfuscator = r_value === nothing ? nothing : r_value

    value_int = BigInt(value)
    if value_int < 0
        value_int = value_int + public_key.n
    end

    ciphertext = raw_encrypt(public_key, value_int, obfuscator)
    encrypted_number = EncryptedNumber(public_key, ciphertext)

    if r_value === nothing
        obfuscate!(encrypted_number)
    end

    return encrypted_number
end

"""
    decrypt(private_key::PaillierPrivateKey, encrypted_number::EncryptedNumber)

Decrypt an encrypted number.

Args:
- `private_key`: Private key for decryption
- `encrypted_number`: EncryptedNumber to decrypt

Returns:
- Decrypted integer value
"""
function decrypt(private_key::PaillierPrivateKey, encrypted_number::EncryptedNumber)
    if private_key.public_key != encrypted_number.public_key
        error("Encrypted number was encrypted with a different key")
    end

    return raw_decrypt(private_key, get_ciphertext(encrypted_number, be_secure=false))
end

# ============================================================================
# VECTOR AND MATRIX OPERATIONS (MPC-with-PHE style)
# ============================================================================

"""
    encrypt_vector(public_key::PaillierPublicKey, vec::Vector)

Encrypt a vector of values.
"""
function encrypt_vector(public_key::PaillierPublicKey, vec::Vector)
    return [encrypt(public_key, BigInt(round(v))) for v in vec]
end

"""
    decrypt_vector(private_key::PaillierPrivateKey, enc_vec::Vector{EncryptedNumber})

Decrypt a vector of encrypted numbers.
"""
function decrypt_vector(private_key::PaillierPrivateKey, enc_vec::Vector{EncryptedNumber})
    return [decrypt(private_key, enc) for enc in enc_vec]
end

"""
    encrypt_matrix(public_key::PaillierPublicKey, mat::Matrix)

Encrypt a matrix of values.
"""
function encrypt_matrix(public_key::PaillierPublicKey, mat::Matrix)
    return [encrypt(public_key, BigInt(round(mat[i,j])))
            for i in 1:size(mat,1), j in 1:size(mat,2)]
end

"""
    decrypt_matrix(private_key::PaillierPrivateKey, enc_mat::Matrix{EncryptedNumber})

Decrypt a matrix of encrypted numbers.
"""
function decrypt_matrix(private_key::PaillierPrivateKey, enc_mat::Matrix{EncryptedNumber})
    return [decrypt(private_key, enc_mat[i,j])
            for i in 1:size(enc_mat,1), j in 1:size(enc_mat,2)]
end

# ============================================================================
# FIXED-POINT ARITHMETIC (for float support)
# ============================================================================

"""
Fixed-point encoding/decoding for floating point numbers.
Scales floats by 2^precision to convert to integers for encryption.
"""

const DEFAULT_PRECISION = 32

"""
    encode_float(value::Float64, precision::Int=DEFAULT_PRECISION)

Convert float to fixed-point integer representation.
"""
function encode_float(value::Float64, precision::Int=DEFAULT_PRECISION)
    return BigInt(round(value * (2^precision)))
end

"""
    decode_float(value::Integer, precision::Int=DEFAULT_PRECISION)

Convert fixed-point integer back to float.
"""
function decode_float(value::Integer, precision::Int=DEFAULT_PRECISION)
    return Float64(value) / (2^precision)
end

"""
    encrypt_float(public_key::PaillierPublicKey, value::Float64, precision::Int=DEFAULT_PRECISION)

Encrypt a floating point number using fixed-point encoding.
"""
function encrypt_float(public_key::PaillierPublicKey, value::Float64, precision::Int=DEFAULT_PRECISION)
    encoded = encode_float(value, precision)
    return encrypt(public_key, encoded)
end

"""
    decrypt_float(private_key::PaillierPrivateKey, encrypted_number::EncryptedNumber, precision::Int=DEFAULT_PRECISION)

Decrypt to floating point number using fixed-point decoding.
"""
function decrypt_float(private_key::PaillierPrivateKey, encrypted_number::EncryptedNumber, precision::Int=DEFAULT_PRECISION)
    decrypted = decrypt(private_key, encrypted_number)
    return decode_float(decrypted, precision)
end

# ============================================================================
# EXPORTS
# ============================================================================

export PaillierPublicKey, PaillierPrivateKey, EncryptedNumber
export generate_paillier_keypair
export encrypt, decrypt
export encrypt_vector, decrypt_vector
export encrypt_matrix, decrypt_matrix
export encrypt_float, decrypt_float
export encode_float, decode_float
export obfuscate!

println("Paillier Encryption Module Loaded (adapted from MPC-with-PHE)")
