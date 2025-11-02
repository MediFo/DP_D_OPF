"""
ENCRYPTION SCHEMES COMPARISON TOOL

Quick comparison of Paillier vs BGV vs CKKS on small test case
Demonstrates the performance overhead differences

Usage:
    julia compare_encryption_schemes.jl
"""

using Printf

println("\n" * "="^80)
println(" ENCRYPTION SCHEMES PERFORMANCE COMPARISON")
println("="^80 * "\n")

# Load crypto libraries
println("Loading encryption libraries...")
include("scripts/paillier_crypto.jl")
include("scripts/bgv_crypto.jl")
include("scripts/ckks_crypto.jl")

# Test parameters
n_values = 10  # Number of values to encrypt/decrypt
test_value = 42.5

println("\nTest configuration:")
println("  Number of values: $n_values")
println("  Test value: $test_value")
println("  Operations: Encrypt → Add → Decrypt")
println()

# ══════════════════════════════════════════════════════════════════════════════
# PAILLIER TEST
# ══════════════════════════════════════════════════════════════════════════════

println("─"^80)
println("PAILLIER (Partial HE - Addition only)")
println("─"^80)

# Key generation
print("  Key generation... ")
flush(stdout)
t_start = time()
paillier_keypair = generate_paillier_keypair(1024)  # 1024-bit for speed
t_keygen_paillier = time() - t_start
println("✓ $(round(t_keygen_paillier, digits=3))s")

# Encryption
print("  Encrypting $n_values values... ")
flush(stdout)
t_start = time()
paillier_enc = [encrypt(paillier_keypair.public_key, test_value) for _ in 1:n_values]
t_enc_paillier = time() - t_start
println("✓ $(round(t_enc_paillier, digits=3))s")

# Homomorphic addition
print("  Homomorphic addition... ")
flush(stdout)
t_start = time()
paillier_sum = encrypted_average(paillier_enc)
t_add_paillier = time() - t_start
println("✓ $(round(t_add_paillier, digits=3))s")

# Decryption
print("  Decrypting result... ")
flush(stdout)
t_start = time()
paillier_result = decrypt(paillier_keypair.public_key, paillier_keypair.private_key, paillier_sum)
t_dec_paillier = time() - t_start
println("✓ $(round(t_dec_paillier, digits=3))s")

t_total_paillier = t_keygen_paillier + t_enc_paillier + t_add_paillier + t_dec_paillier
println("  Result: $(round(paillier_result, digits=2)) (expected: $test_value)")
println("  Total time: $(round(t_total_paillier, digits=3))s")

# ══════════════════════════════════════════════════════════════════════════════
# BGV TEST
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "─"^80)
println("BGV/BFV (Fully HE - Addition AND Multiplication, Integer-based)")
println("─"^80)

# Key generation
print("  Key generation... ")
flush(stdout)
t_start = time()
bgv_keypair = generate_bgv_keypair(n=2048, log_q=100, max_depth=3)  # Reduced params
t_keygen_bgv = time() - t_start
println("✓ $(round(t_keygen_bgv, digits=3))s")

# Encryption
print("  Encrypting $n_values values... ")
flush(stdout)
t_start = time()
bgv_enc = [encrypt_bgv(bgv_keypair.public_key, test_value) for _ in 1:n_values]
t_enc_bgv = time() - t_start
println("✓ $(round(t_enc_bgv, digits=3))s")

# Homomorphic addition
print("  Homomorphic addition... ")
flush(stdout)
t_start = time()
bgv_sum = encrypted_average_bgv(bgv_enc)
t_add_bgv = time() - t_start
println("✓ $(round(t_add_bgv, digits=3))s")

# Decryption
print("  Decrypting result... ")
flush(stdout)
t_start = time()
bgv_result = decrypt_bgv(bgv_keypair.public_key, bgv_keypair.private_key, bgv_sum)
t_dec_bgv = time() - t_start
println("✓ $(round(t_dec_bgv, digits=3))s")

t_total_bgv = t_keygen_bgv + t_enc_bgv + t_add_bgv + t_dec_bgv
println("  Result: $(round(bgv_result, digits=2)) (expected: $test_value)")
println("  Total time: $(round(t_total_bgv, digits=3))s")
println("  Security: Post-quantum secure (lattice-based)")

# ══════════════════════════════════════════════════════════════════════════════
# CKKS TEST
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "─"^80)
println("CKKS (Fully HE - Addition AND Multiplication, Real numbers)")
println("─"^80)

# Key generation
print("  Key generation... ")
flush(stdout)
t_start = time()
ckks_keypair = generate_ckks_keypair(n=2048, log_q=100, max_depth=3)  # Reduced params
t_keygen_ckks = time() - t_start
println("✓ $(round(t_keygen_ckks, digits=3))s")

# Encryption
print("  Encrypting $n_values values... ")
flush(stdout)
t_start = time()
ckks_enc = [encrypt_ckks(ckks_keypair.public_key, test_value) for _ in 1:n_values]
t_enc_ckks = time() - t_start
println("✓ $(round(t_enc_ckks, digits=3))s")

# Homomorphic addition
print("  Homomorphic addition... ")
flush(stdout)
t_start = time()
ckks_sum = encrypted_average_ckks(ckks_enc)
t_add_ckks = time() - t_start
println("✓ $(round(t_add_ckks, digits=3))s")

# Decryption
print("  Decrypting result... ")
flush(stdout)
t_start = time()
ckks_result = decrypt_ckks(ckks_keypair.public_key, ckks_keypair.private_key, ckks_sum)
t_dec_ckks = time() - t_start
println("✓ $(round(t_dec_ckks, digits=3))s")

t_total_ckks = t_keygen_ckks + t_enc_ckks + t_add_ckks + t_dec_ckks
println("  Result: $(round(ckks_result, digits=2)) (expected: $test_value)")
println("  Total time: $(round(t_total_ckks, digits=3))s")

# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON TABLE
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" PERFORMANCE COMPARISON")
println("="^80 * "\n")

println("Time breakdown (seconds):")
println("─"^100)
@printf("%-20s %-12s %-12s %-12s %-12s %-12s\n", "Operation", "Paillier", "BGV", "CKKS", "BGV/Pail", "CKKS/Pail")
println("─"^100)

overhead_keygen_bgv = t_keygen_bgv / t_keygen_paillier
overhead_keygen_ckks = t_keygen_ckks / t_keygen_paillier
@printf("%-20s %-12s %-12s %-12s %-12s %-12s\n",
        "Key generation",
        "$(round(t_keygen_paillier, digits=3))s",
        "$(round(t_keygen_bgv, digits=3))s",
        "$(round(t_keygen_ckks, digits=3))s",
        "$(round(overhead_keygen_bgv, digits=1))x",
        "$(round(overhead_keygen_ckks, digits=1))x")

overhead_enc_bgv = t_enc_bgv / t_enc_paillier
overhead_enc_ckks = t_enc_ckks / t_enc_paillier
@printf("%-20s %-12s %-12s %-12s %-12s %-12s\n",
        "Encryption ($n_values)",
        "$(round(t_enc_paillier, digits=3))s",
        "$(round(t_enc_bgv, digits=3))s",
        "$(round(t_enc_ckks, digits=3))s",
        "$(round(overhead_enc_bgv, digits=1))x",
        "$(round(overhead_enc_ckks, digits=1))x")

overhead_add_bgv = t_add_bgv / t_add_paillier
overhead_add_ckks = t_add_ckks / t_add_paillier
@printf("%-20s %-12s %-12s %-12s %-12s %-12s\n",
        "Addition",
        "$(round(t_add_paillier, digits=3))s",
        "$(round(t_add_bgv, digits=3))s",
        "$(round(t_add_ckks, digits=3))s",
        "$(round(overhead_add_bgv, digits=1))x",
        "$(round(overhead_add_ckks, digits=1))x")

overhead_dec_bgv = t_dec_bgv / t_dec_paillier
overhead_dec_ckks = t_dec_ckks / t_dec_paillier
@printf("%-20s %-12s %-12s %-12s %-12s %-12s\n",
        "Decryption",
        "$(round(t_dec_paillier, digits=3))s",
        "$(round(t_dec_bgv, digits=3))s",
        "$(round(t_dec_ckks, digits=3))s",
        "$(round(overhead_dec_bgv, digits=1))x",
        "$(round(overhead_dec_ckks, digits=1))x")

println("─"^100)
overhead_total_bgv = t_total_bgv / t_total_paillier
overhead_total_ckks = t_total_ckks / t_total_paillier
@printf("%-20s %-12s %-12s %-12s %-12s %-12s\n",
        "TOTAL",
        "$(round(t_total_paillier, digits=3))s",
        "$(round(t_total_bgv, digits=3))s",
        "$(round(t_total_ckks, digits=3))s",
        "$(round(overhead_total_bgv, digits=1))x",
        "$(round(overhead_total_ckks, digits=1))x")
println("─"^100)

println("\nAccuracy check:")
paillier_error = abs(paillier_result - test_value)
bgv_error = abs(bgv_result - test_value)
ckks_error = abs(ckks_result - test_value)
println("  Paillier error: $(round(paillier_error, digits=6))")
println("  BGV error:      $(round(bgv_error, digits=6))")
println("  CKKS error:     $(round(ckks_error, digits=6))")

println("\n" * "="^80)
println(" SUMMARY")
println("="^80 * "\n")

println("Paillier (Partial HE):")
println("  ✅ Fast: $(round(t_total_paillier, digits=3))s total")
println("  ✅ Supports addition (sufficient for ADMM)")
println("  ✅ Recommended for production ADMM")
println("  ⚠️  NOT post-quantum secure")
println()

println("BGV/BFV (Fully HE):")
println("  ⚠️  Medium-slow: $(round(t_total_bgv, digits=3))s total ($(round(overhead_total_bgv, digits=1))x overhead)")
println("  ✅ Supports addition AND multiplication")
println("  ✅ POST-QUANTUM SECURE (lattice-based) 🔐")
println("  ✅ Integer-based (fast for discrete operations)")
println("  ⚠️  Overkill for ADMM (doesn't need multiplication)")
println("  ✓ Best for: Post-quantum security, integer computations")
println()

println("CKKS (Fully HE):")
println("  ⚠️  Slow: $(round(t_total_ckks, digits=3))s total ($(round(overhead_total_ckks, digits=1))x overhead)")
println("  ✅ Supports addition AND multiplication")
println("  ✅ POST-QUANTUM SECURE (lattice-based) 🔐")
println("  ✅ Works on real numbers natively")
println("  ⚠️  Overkill for ADMM (doesn't need multiplication)")
println("  ✓ Best for: ML on encrypted data, signal processing, complex computations")
println()

println("Recommendation:")
println("  For ADMM (speed):              Use Paillier ✅")
println("  For ADMM (post-quantum):       Use BGV 🔐")
println("  For FHE research (integers):   Use BGV 🔬")
println("  For FHE research (reals):      Use CKKS 🔬")
println("  For ML on encrypted data:      Use CKKS 🤖")
println()

println("="^80)
println(" ✅ COMPARISON COMPLETE")
println("="^80 * "\n")
