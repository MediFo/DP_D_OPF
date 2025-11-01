"""
Paillier Homomorphic Encryption for MPC
Julia conversion of paillier.py from MPC-with-PHE repository
Adapted to be a fixed-point library without encoding layer
"""

using Random
include("mpc_phe_util.jl")

# ============================================================================
# PAILLIER PUBLIC KEY
# ============================================================================

"""
    PaillierPublicKey

Contains a public key and associated encryption methods.
Matches paillier.py::PaillierPublicKey structure.

Fields:
- n::BigInt - the modulus of the public key
- g::BigInt - part of the public key (set to n + 1)
- nsquare::BigInt - n^2, stored for frequent use
- max_int::BigInt - maximum int that may safely be stored
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

function Base.:(==)(a::PaillierPublicKey, b::PaillierPublicKey)
    return a.n == b.n
end

function Base.hash(pk::PaillierPublicKey, h::UInt)
    return hash(pk.n, h)
end

"""
    get_random_lt_n(public_key::PaillierPublicKey)

Return a cryptographically random number less than n.
"""
function get_random_lt_n(public_key::PaillierPublicKey)
    return rand(Random.RandomDevice(), BigInt(1):public_key.n-1)
end

"""
    raw_encrypt(public_key::PaillierPublicKey, plaintext::Integer, r_value=nothing)

Paillier encryption of a positive integer plaintext < n.
Uses the optimization g = n + 1, so (n+1)^plaintext = n*plaintext + 1 mod n^2

Args:
- plaintext: positive integer < n to be encrypted
- r_value: obfuscator for ciphertext (precomputed r^n mod n^2), or nothing for random

Returns:
- Ciphertext as BigInt
"""
function raw_encrypt(public_key::PaillierPublicKey, plaintext::Integer, r_value=nothing)
    plaintext = BigInt(plaintext)

    if !(plaintext isa BigInt || plaintext isa Int)
        error("Expected int type plaintext but got: $(typeof(plaintext))")
    end

    n = public_key.n
    nsquare = public_key.nsquare
    max_int = public_key.max_int

    # Handle very large plaintexts using inverse shortcut
    if n - max_int <= plaintext < n
        neg_plaintext = n - plaintext
        neg_ciphertext = (n * neg_plaintext + 1) % nsquare
        nude_ciphertext = invert(neg_ciphertext, nsquare)
    else
        # Exploit g = n + 1: (n+1)^plaintext = n*plaintext + 1 mod n^2
        nude_ciphertext = (n * plaintext + 1) % nsquare
    end

    # Apply obfuscation with r^n mod n^2
    if r_value === nothing
        r = get_random_lt_n(public_key)
        obfuscator = powmod(r, n, nsquare)
    else
        obfuscator = r_value
    end

    return (nude_ciphertext * obfuscator) % nsquare
end

"""
    encrypt(public_key::PaillierPublicKey, value::Integer, r_value=nothing)

Encode and Paillier encrypt an integer value.
Returns EncryptedNumber object.

Args:
- value: integer to encrypt (must satisfy abs(value) < n/3)
- r_value: obfuscator for ciphertext (optional, random if nothing)
"""
function encrypt(public_key::PaillierPublicKey, value::Integer, r_value=nothing)
    obfuscator = r_value === nothing ? 1 : r_value

    value = BigInt(value)
    if value < 0
        value = value + public_key.n
    end

    ciphertext = raw_encrypt(public_key, value, r_value=obfuscator)
    encrypted_number = EncryptedNumber(public_key, ciphertext)

    if r_value === nothing
        obfuscate!(encrypted_number)
    end

    return encrypted_number
end

# ============================================================================
# PAILLIER PRIVATE KEY
# ============================================================================

"""
    PaillierPrivateKey

Contains a private key and associated decryption method.
Uses Chinese Remainder Theorem for fast decryption.

Fields:
- public_key::PaillierPublicKey - corresponding public key
- p::BigInt - private secret prime
- q::BigInt - private secret prime
- psquare::BigInt - p^2
- qsquare::BigInt - q^2
- p_inverse::BigInt - p^(-1) mod q
- hp::BigInt - h(p) for decryption
- hq::BigInt - h(q) for decryption
- n::BigInt - modulus (p*q)
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
            error("p and q have to be different")
        end

        # Ensure p < q
        if q < p
            p, q = q, p
        end

        psquare = p * p
        qsquare = q * q
        p_inverse = invert(p, q)

        # Compute h functions for CRT decryption
        hp = h_function(public_key, p, psquare)
        hq = h_function(public_key, q, qsquare)

        new(public_key, p, q, psquare, qsquare, p_inverse, hp, hq, public_key.n)
    end
end

"""
    l_function(x::Integer, p::Integer)

Computes the L function as defined in Paillier's paper.
L(x, p) = (x - 1) / p
"""
function l_function(x::Integer, p::Integer)
    return div(BigInt(x) - 1, BigInt(p))
end

"""
    h_function(public_key::PaillierPublicKey, x::BigInt, xsquare::BigInt)

Computes the h-function as defined in Paillier's paper page 12.
Used in 'Decryption using Chinese-remaindering'.
"""
function h_function(public_key::PaillierPublicKey, x::BigInt, xsquare::BigInt)
    g_pow = powmod(public_key.g, x - 1, xsquare)
    l_val = l_function(g_pow, x)
    return invert(l_val, x)
end

"""
    crt(private_key::PaillierPrivateKey, mp::Integer, mq::Integer)

The Chinese Remainder Theorem as needed for decryption.
Returns the solution modulo n = p*q.

Args:
- mp: the solution modulo p
- mq: the solution modulo q
"""
function crt(private_key::PaillierPrivateKey, mp::Integer, mq::Integer)
    mp = BigInt(mp)
    mq = BigInt(mq)
    u = ((mq - mp) * private_key.p_inverse) % private_key.q
    return mp + (u * private_key.p)
end

"""
    raw_decrypt(private_key::PaillierPrivateKey, ciphertext::Integer)

Decrypt raw ciphertext and return raw plaintext.
Uses Chinese Remainder Theorem for efficiency.

Args:
- ciphertext: integer ciphertext to decrypt

Returns:
- Plaintext as BigInt
"""
function raw_decrypt(private_key::PaillierPrivateKey, ciphertext::Integer)
    ciphertext = BigInt(ciphertext)

    if !(ciphertext isa BigInt || ciphertext isa Int)
        error("Expected ciphertext to be an int, not: $(typeof(ciphertext))")
    end

    p = private_key.p
    q = private_key.q
    psquare = private_key.psquare
    qsquare = private_key.qsquare
    n = private_key.n

    # Decrypt using CRT
    decrypt_to_p = (l_function(powmod(ciphertext, p-1, psquare), p) * private_key.hp) % p
    decrypt_to_q = (l_function(powmod(ciphertext, q-1, qsquare), q) * private_key.hq) % q

    value = crt(private_key, decrypt_to_p, decrypt_to_q)

    # Handle negative numbers: convention is x < n/3 is positive, x > 2n/3 is negative
    if value < div(n, 3)
        return value
    else
        return value - n
    end
end

"""
    decrypt(private_key::PaillierPrivateKey, encrypted_number::EncryptedNumber)

Return the decrypted plaintext of encrypted_number.

Args:
- encrypted_number: EncryptedNumber to decrypt

Returns:
- Decrypted integer value
"""
function decrypt(private_key::PaillierPrivateKey, encrypted_number::EncryptedNumber)
    if !isa(encrypted_number, EncryptedNumber)
        error("Expected encrypted_number to be an EncryptedNumber, not: $(typeof(encrypted_number))")
    end

    if private_key.public_key != encrypted_number.public_key
        error("Encrypted number was encrypted against a different key!")
    end

    return raw_decrypt(private_key, ciphertext(encrypted_number, be_secure=false))
end

# ============================================================================
# ENCRYPTED NUMBER
# ============================================================================

"""
    EncryptedNumber

Represents the Paillier encryption of an integer.
Supports homomorphic operations:
1. D(E(a) * E(b)) = a + b  (addition)
2. D(E(a)^b) = a * b       (scalar multiplication)

Fields:
- public_key::PaillierPublicKey
- __ciphertext::BigInt
- __is_obfuscated::Bool
"""
mutable struct EncryptedNumber
    public_key::PaillierPublicKey
    __ciphertext::BigInt
    __is_obfuscated::Bool

    function EncryptedNumber(public_key::PaillierPublicKey, ciphertext::Integer)
        if isa(ciphertext, EncryptedNumber)
            error("Ciphertext should be an integer")
        end
        if !isa(public_key, PaillierPublicKey)
            error("public_key should be a PaillierPublicKey")
        end
        new(public_key, BigInt(ciphertext), false)
    end
end

"""
    ciphertext(enc::EncryptedNumber; be_secure=true)

Return the ciphertext of the EncryptedNumber.
If be_secure=true, obfuscates before returning.
"""
function ciphertext(enc::EncryptedNumber; be_secure=true)
    if be_secure && !enc.__is_obfuscated
        obfuscate!(enc)
    end
    return enc.__ciphertext
end

"""
    obfuscate!(enc::EncryptedNumber)

Disguise ciphertext by multiplying by r^n with random r.
Must be performed before sending to untrusted parties.
"""
function obfuscate!(enc::EncryptedNumber)
    r = get_random_lt_n(enc.public_key)
    r_pow_n = powmod(r, enc.public_key.n, enc.public_key.nsquare)
    enc.__ciphertext = (enc.__ciphertext * r_pow_n) % enc.public_key.nsquare
    enc.__is_obfuscated = true
    return enc
end

# ============================================================================
# HOMOMORPHIC OPERATIONS
# ============================================================================

"""
    _raw_add(enc::EncryptedNumber, e_a::Integer, e_b::Integer)

Returns E(a + b) given E(a) and E(b).
Low-level operation without obfuscation.
"""
function _raw_add(enc::EncryptedNumber, e_a::Integer, e_b::Integer)
    return (BigInt(e_a) * BigInt(e_b)) % enc.public_key.nsquare
end

"""
    _raw_mul(enc::EncryptedNumber, plaintext::Integer)

Returns E(a * plaintext) where E(a) = ciphertext.
Low-level scalar multiplication without obfuscation.
"""
function _raw_mul(enc::EncryptedNumber, plaintext::Integer)
    plaintext = BigInt(plaintext)

    if !(plaintext isa BigInt || plaintext isa Int)
        error("Expected ciphertext to be int, not $(typeof(plaintext))")
    end

    if plaintext < 0 || plaintext >= enc.public_key.n
        error("Scalar out of bounds: $plaintext")
    end

    if enc.public_key.n - enc.public_key.max_int <= plaintext
        # Very large plaintext, use inverse trick
        neg_c = invert(ciphertext(enc, be_secure=false), enc.public_key.nsquare)
        neg_scalar = enc.public_key.n - plaintext
        return powmod(neg_c, neg_scalar, enc.public_key.nsquare)
    else
        return powmod(ciphertext(enc, be_secure=false), plaintext, enc.public_key.nsquare)
    end
end

"""
    _add_encrypted(a::EncryptedNumber, b::EncryptedNumber)

Returns E(a + b) given E(a) and E(b).
"""
function _add_encrypted(a::EncryptedNumber, b::EncryptedNumber)
    if a.public_key != b.public_key
        error("Attempted to add numbers encrypted against different public keys!")
    end

    sum_ciphertext = _raw_add(a, ciphertext(a, be_secure=false), ciphertext(b, be_secure=false))
    return EncryptedNumber(a.public_key, sum_ciphertext)
end

"""
    _add_scalar(enc::EncryptedNumber, scalar::Integer)

Returns E(a + b), given E(a) and plaintext b.
"""
function _add_scalar(enc::EncryptedNumber, scalar::Integer)
    scalar = BigInt(scalar)
    # Don't obfuscate in basic operation
    encrypted_scalar = raw_encrypt(enc.public_key, scalar, 1)
    sum_ciphertext = _raw_add(enc, ciphertext(enc, be_secure=false), encrypted_scalar)
    return EncryptedNumber(enc.public_key, sum_ciphertext)
end

# Operator overloading
function Base.:+(a::EncryptedNumber, b::EncryptedNumber)
    return _add_encrypted(a, b)
end

function Base.:+(enc::EncryptedNumber, scalar::Integer)
    return _add_scalar(enc, scalar)
end

function Base.:+(scalar::Integer, enc::EncryptedNumber)
    return enc + scalar
end

function Base.:*(enc::EncryptedNumber, scalar::Integer)
    scalar = BigInt(scalar)
    if scalar < 0
        scalar = scalar + enc.public_key.n
    end
    product = _raw_mul(enc, scalar)
    return EncryptedNumber(enc.public_key, product)
end

function Base.:*(scalar::Integer, enc::EncryptedNumber)
    return enc * scalar
end

function Base.:-(a::EncryptedNumber, b::Union{EncryptedNumber,Integer})
    if isa(b, EncryptedNumber)
        return a + (b * -1)
    else
        return a + (-b)
    end
end

function Base.:-(scalar::Integer, enc::EncryptedNumber)
    return scalar + (enc * -1)
end

# ============================================================================
# KEY GENERATION
# ============================================================================

"""
    generate_paillier_keypair(; n_length=DEFAULT_KEYSIZE)

Return a new PaillierPublicKey and PaillierPrivateKey.

Args:
- n_length: key size in bits (default: 1024)

Returns:
- Tuple of (PaillierPublicKey, PaillierPrivateKey)
"""
function generate_paillier_keypair(; n_length::Integer=DEFAULT_KEYSIZE)
    p = q = n = nothing
    n_len = 0

    # Generate primes until modulus has correct bit length
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
# VECTOR OPERATIONS (from client.py)
# ============================================================================

"""
    encrypt_vector(pubkey::PaillierPublicKey, x::AbstractVector, coins=nothing)

Encrypt a vector of integers.
If coins provided, use them as obfuscators (for deterministic encryption).
"""
function encrypt_vector(pubkey::PaillierPublicKey, x::AbstractVector, coins=nothing)
    if coins === nothing
        return [encrypt(pubkey, BigInt(y)) for y in x]
    else
        return [encrypt(pubkey, BigInt(y), coins[i]) for (i, y) in enumerate(x)]
    end
end

"""
    decrypt_vector(privkey::PaillierPrivateKey, x::AbstractVector{EncryptedNumber})

Decrypt a vector of encrypted numbers.
"""
function decrypt_vector(privkey::PaillierPrivateKey, x::AbstractVector{EncryptedNumber})
    return [decrypt(privkey, enc) for enc in x]
end

# ============================================================================
# EXPORTS
# ============================================================================

export PaillierPublicKey, PaillierPrivateKey, EncryptedNumber
export generate_paillier_keypair
export encrypt, decrypt, raw_encrypt, raw_decrypt
export encrypt_vector, decrypt_vector
export obfuscate!, ciphertext

println("✓ MPC-PHE Paillier Module Loaded")
