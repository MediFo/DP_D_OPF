"""
Utility Functions for MPC-with-PHE
Julia conversion of util.py from MPC-with-PHE repository
Provides cryptographic primitives for Paillier encryption
"""

using Random
using Primes

# ============================================================================
# CRYPTOGRAPHIC PRIMITIVES
# ============================================================================

"""
    powmod(a, b, c)

Compute (a^b) mod c efficiently using modular exponentiation.
Equivalent to Python's pow(a, b, c) or gmpy2.powmod(a, b, c)
"""
function powmod(a::Integer, b::Integer, c::Integer)
    if a == 1
        return 1
    end
    return powermod(BigInt(a), BigInt(b), BigInt(c))
end

"""
    invert(a, b)

The multiplicative inverse of a in the integers modulo b.
Returns x where a * x ≡ 1 (mod b)
Equivalent to gmpy2.invert(a, b)
"""
function invert(a::Integer, b::Integer)
    try
        return invmod(BigInt(a), BigInt(b))
    catch e
        error("$a has no inverse mod $b")
    end
end

"""
    getprimeover(N)

Return a random N-bit prime number using cryptographically secure random source.
Equivalent to gmpy2.next_prime() or PyCrypto's getPrime()
"""
function getprimeover(N::Integer)
    # Generate random N-bit number with MSB set to 1
    randbits = rand(Random.RandomDevice(), BigInt(2)^(N-1):BigInt(2)^N - 1)
    # Find next prime
    return nextprime(randbits)
end

"""
    isqrt(N)

Returns the integer square root of N.
Equivalent to gmpy2.isqrt(N)
"""
function isqrt(N::Integer)
    if N == 0
        return BigInt(0)
    end
    return Base.isqrt(BigInt(N))
end

"""
    improved_i_sqrt(n)

Pure Julia implementation of integer square root.
Fallback when optimized libraries not available.
From: http://stackoverflow.com/questions/15390807/integer-square-root-in-python
"""
function improved_i_sqrt(n::Integer)
    @assert n >= 0 "n must be non-negative"

    if n == 0
        return 0
    end

    n = BigInt(n)
    i = ndigits(n, base=2) >> 1  # i = floor((1 + floor(log_2(n))) / 2)
    m = BigInt(1) << i           # m = 2^i

    # Iteratively compute square root
    while (m << i) > n
        m >>= 1
        i -= 1
    end

    d = n - (m << i)  # d = n - m^2

    for k in (i-1):-1:0
        j = BigInt(1) << k
        new_diff = d - (((m << 1) | j) << k)
        if new_diff >= 0
            d = new_diff
            m |= j
        end
    end

    return m
end

# ============================================================================
# FIXED-POINT ARITHMETIC (from client.py)
# ============================================================================

const DEFAULT_KEYSIZE = 1024
const DEFAULT_MSGSIZE = 64
const DEFAULT_SECURITYSIZE = 100
const DEFAULT_PRECISION = div(DEFAULT_MSGSIZE, 2)  # 32 bits for fractional part

"""
    fp(scalar, prec=DEFAULT_PRECISION)

Convert floating point to fixed-point integer representation.
Scales by 2^prec to preserve fractional bits.
From MPC-with-PHE client.py: fp(scalar, prec)
"""
function fp(scalar::Real, prec::Integer=DEFAULT_PRECISION)
    return BigInt(round(scalar * (2^prec)))
end

"""
    fp_vector(vec, prec=DEFAULT_PRECISION)

Convert vector of floats to fixed-point integers.
"""
function fp_vector(vec::AbstractVector, prec::Integer=DEFAULT_PRECISION)
    return [fp(x, prec) for x in vec]
end

"""
    retrieve_fp(scalar, prec=DEFAULT_PRECISION)

Convert fixed-point integer back to floating point.
Divides by 2^prec to restore original scale.
From MPC-with-PHE client.py: retrieve_fp(scalar, prec)
"""
function retrieve_fp(scalar::Integer, prec::Integer=DEFAULT_PRECISION)
    return Float64(scalar) / (2^prec)
end

"""
    retrieve_fp_vector(vec, prec=DEFAULT_PRECISION)

Convert vector of fixed-point integers back to floats.
"""
function retrieve_fp_vector(vec::AbstractVector, prec::Integer=DEFAULT_PRECISION)
    return [retrieve_fp(x, prec) for x in vec]
end

"""
    Q_s(scalar, prec=DEFAULT_PRECISION)

Quantize scalar to fixed-point and back (for testing precision).
From MPC-with-PHE client.py: Q_s(scalar, prec)
"""
function Q_s(scalar::Real, prec::Integer=DEFAULT_PRECISION)
    return Int(scalar * (2^prec)) / (2^prec)
end

"""
    Q_vector(vec, prec=DEFAULT_PRECISION)

Quantize vector to fixed-point representation.
"""
function Q_vector(vec::AbstractVector, prec::Integer=DEFAULT_PRECISION)
    if length(vec) > 1
        return [Q_s(x, prec) for x in vec]
    else
        return Q_s(vec[1], prec)
    end
end

"""
    Q_matrix(mat, prec=DEFAULT_PRECISION)

Quantize matrix to fixed-point representation.
"""
function Q_matrix(mat::AbstractMatrix, prec::Integer=DEFAULT_PRECISION)
    return [Q_s(mat[i,j], prec) for i in 1:size(mat,1), j in 1:size(mat,2)]
end

# ============================================================================
# EXPORTS
# ============================================================================

export powmod, invert, getprimeover, isqrt, improved_i_sqrt
export DEFAULT_KEYSIZE, DEFAULT_MSGSIZE, DEFAULT_SECURITYSIZE, DEFAULT_PRECISION
export fp, fp_vector, retrieve_fp, retrieve_fp_vector
export Q_s, Q_vector, Q_matrix

println("✓ MPC-PHE Utility Module Loaded")
