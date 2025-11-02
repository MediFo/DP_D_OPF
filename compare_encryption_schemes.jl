"""
ENCRYPTION SCHEMES COMPARISON TOOL

Quick comparison of Paillier vs CKKS on small test case
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
# CKKS TEST
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "─"^80)
println("CKKS (Fully HE - Addition AND Multiplication)")
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
println("─"^80)
@printf("%-20s %-12s %-12s %-10s\n", "Operation", "Paillier", "CKKS", "Overhead")
println("─"^80)

overhead_keygen = t_keygen_ckks / t_keygen_paillier
@printf("%-20s %-12s %-12s %-10s\n",
        "Key generation",
        "$(round(t_keygen_paillier, digits=3))s",
        "$(round(t_keygen_ckks, digits=3))s",
        "$(round(overhead_keygen, digits=1))x")

overhead_enc = t_enc_ckks / t_enc_paillier
@printf("%-20s %-12s %-12s %-10s\n",
        "Encryption ($n_values)",
        "$(round(t_enc_paillier, digits=3))s",
        "$(round(t_enc_ckks, digits=3))s",
        "$(round(overhead_enc, digits=1))x")

overhead_add = t_add_ckks / t_add_paillier
@printf("%-20s %-12s %-12s %-10s\n",
        "Addition",
        "$(round(t_add_paillier, digits=3))s",
        "$(round(t_add_ckks, digits=3))s",
        "$(round(overhead_add, digits=1))x")

overhead_dec = t_dec_ckks / t_dec_paillier
@printf("%-20s %-12s %-12s %-10s\n",
        "Decryption",
        "$(round(t_dec_paillier, digits=3))s",
        "$(round(t_dec_ckks, digits=3))s",
        "$(round(overhead_dec, digits=1))x")

println("─"^80)
overhead_total = t_total_ckks / t_total_paillier
@printf("%-20s %-12s %-12s %-10s\n",
        "TOTAL",
        "$(round(t_total_paillier, digits=3))s",
        "$(round(t_total_ckks, digits=3))s",
        "$(round(overhead_total, digits=1))x")
println("─"^80)

println("\nAccuracy check:")
paillier_error = abs(paillier_result - test_value)
ckks_error = abs(ckks_result - test_value)
println("  Paillier error: $(round(paillier_error, digits=6))")
println("  CKKS error:     $(round(ckks_error, digits=6))")

println("\n" * "="^80)
println(" SUMMARY")
println("="^80 * "\n")

println("Paillier (Partial HE):")
println("  ✅ Fast: $(round(t_total_paillier, digits=3))s total")
println("  ✅ Supports addition (sufficient for ADMM)")
println("  ✅ Recommended for production")
println()

println("CKKS (Fully HE):")
println("  ⚠️  Slow: $(round(t_total_ckks, digits=3))s total ($(round(overhead_total, digits=1))x overhead)")
println("  ✅ Supports addition AND multiplication")
println("  ✅ Stronger security (lattice-based)")
println("  ⚠️  Overkill for ADMM (doesn't need multiplication)")
println("  ✓ Best for: Research, ML on encrypted data, complex computations")
println()

println("Recommendation:")
println("  For ADMM: Use Paillier ✅")
println("  For FHE research: Use CKKS 🔬")
println()

println("="^80)
println(" ✅ COMPARISON COMPLETE")
println("="^80 * "\n")
