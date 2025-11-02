# Encryption Schemes for Privacy-Preserving ADMM

This repository now implements **multiple homomorphic encryption schemes** for privacy-preserving distributed optimization using ADMM (Alternating Direction Method of Multipliers).

## 📚 Available Encryption Schemes

### 1. **Paillier** (Partial Homomorphic Encryption)
- **File**: `opt_main.jl`
- **Library**: `scripts/paillier_crypto.jl`
- **Type**: Partial HE (addition only)
- **Performance**: **1x baseline (FASTEST)**
- **Security**: RSA-based, NOT post-quantum secure
- **Recommended for**: Production ADMM deployments

**Characteristics:**
- ✅ Fast encryption/decryption
- ✅ Efficient homomorphic addition
- ✅ Proven security (RSA hardness)
- ✅ Sufficient for ADMM consensus
- ⚠️ NOT resistant to quantum computers
- ⚠️ NO multiplication support

**Run:**
```bash
julia opt_main.jl
```

---

### 2. **BGV/BFV** (Fully Homomorphic Encryption - Integers)
- **File**: `opt_main_bgv.jl`
- **Library**: `scripts/bgv_crypto.jl`
- **Type**: Fully HE (addition + multiplication)
- **Performance**: **~30x slower than Paillier**
- **Security**: Lattice-based (Ring-LWE), **POST-QUANTUM SECURE** 🔐
- **Recommended for**: Post-quantum security requirements, integer computations

**Characteristics:**
- ✅ Post-quantum secure (resistant to quantum attacks)
- ✅ Supports addition AND multiplication
- ✅ Integer-based (efficient for discrete operations)
- ✅ Moderate overhead (faster than CKKS)
- ⚠️ Slower than Paillier (~30x)
- ⚠️ Overkill for ADMM (doesn't need multiplication)

**Run:**
```bash
julia opt_main_bgv.jl
```

**Expected Runtime (14-bus):**
- Paillier: ~30 seconds
- BGV: ~15 minutes (30x slower)

---

### 3. **CKKS** (Fully Homomorphic Encryption - Real Numbers)
- **File**: `opt_main_ckks.jl`
- **Library**: `scripts/ckks_crypto.jl`
- **Type**: Fully HE (addition + multiplication)
- **Performance**: **~50x slower than Paillier (SLOWEST)**
- **Security**: Lattice-based (RLWE), **POST-QUANTUM SECURE** 🔐
- **Recommended for**: ML on encrypted data, signal processing, FHE research

**Characteristics:**
- ✅ Post-quantum secure (resistant to quantum attacks)
- ✅ Supports addition AND multiplication
- ✅ Works natively on real/complex numbers
- ✅ Best for encrypted machine learning
- ⚠️ Very slow (~50x Paillier)
- ⚠️ Overkill for ADMM

**Run:**
```bash
julia opt_main_ckks.jl
```

**Expected Runtime (14-bus):**
- Paillier: ~30 seconds
- CKKS: ~25 minutes (50x slower)

---

## 🔬 Comparison Tool

Compare all three encryption schemes side-by-side:

```bash
julia compare_encryption_schemes.jl
```

**Output:**
- Performance timing for each scheme
- Overhead multipliers (vs Paillier baseline)
- Accuracy validation
- Use-case recommendations

**Sample Output:**
```
Operation            Paillier     BGV          CKKS         BGV/Pail     CKKS/Pail
─────────────────────────────────────────────────────────────────────────────────────
Key generation       0.285s       8.524s       14.235s      29.9x        50.0x
Encryption (10)      0.042s       1.263s       2.105s       30.1x        50.1x
Addition             0.001s       0.028s       0.047s       28.0x        47.0x
Decryption           0.041s       1.228s       2.049s       29.9x        50.0x
─────────────────────────────────────────────────────────────────────────────────────
TOTAL                0.369s       11.043s      18.436s      29.9x        50.0x
```

---

## 📊 Performance Summary

| Scheme     | Overhead | Post-Quantum | Operations | Best For                    |
|------------|----------|--------------|------------|-----------------------------|
| **Paillier** | 1x (baseline) | ❌ No  | Addition only | Production ADMM (speed)    |
| **BGV/BFV**  | ~30x     | ✅ Yes (lattice) | Add + Mul  | Post-quantum ADMM          |
| **CKKS**     | ~50x     | ✅ Yes (lattice) | Add + Mul  | Encrypted ML, research     |

---

## 🎯 Which Encryption Scheme Should I Use?

### Decision Tree:

```
Do you need post-quantum security?
│
├─ NO → Use Paillier ✅
│       - Fastest (1x)
│       - Production-ready
│       - Sufficient for ADMM
│
└─ YES → Need multiplication on encrypted data?
         │
         ├─ NO → Use BGV 🔐
         │       - Post-quantum secure
         │       - ~30x overhead (acceptable)
         │       - Integer-based (efficient)
         │
         └─ YES → Working with real numbers?
                  │
                  ├─ NO (integers) → Use BGV 🔐
                  │
                  └─ YES (reals) → Use CKKS 🔬
                                   - Native real number support
                                   - Best for ML on encrypted data
                                   - ~50x overhead
```

### Use Case Recommendations:

| Use Case | Recommended Scheme | Why? |
|----------|-------------------|------|
| **Production ADMM** | Paillier | Fastest, sufficient functionality |
| **Post-quantum ADMM** | BGV | Post-quantum secure, reasonable overhead |
| **Encrypted ML** | CKKS | Supports real numbers, multiplication |
| **Integer computations** | BGV | Faster than CKKS for integers |
| **FHE research (reals)** | CKKS | Native real number support |
| **FHE research (integers)** | BGV | Efficient integer operations |

---

## 🔧 Implementation Details

### Common Optimizations (All Schemes):

1. **Sparse Variables**: Only create θ[i,j] for actual network neighbors
   - Reduces variables by 70-90%
   - Example: 14-bus network uses 42 variables instead of 196

2. **Detailed Timing**: Separates optimization time vs cryptography overhead
   - OPT(s): Optimization solver time (NOT affected by encryption)
   - CRYPTO(s): Encryption + decryption + homomorphic operations
   - OTHER(s): Dual updates, residual computation

3. **Progress Indicators**: Real-time feedback showing encryption/consensus progress
   - Prevents "stuck" concerns during slow encryption

### Encryption-Specific Features:

**Paillier (`opt_main.jl`):**
- Optimized for speed with 2048-bit keys
- Efficient modular arithmetic
- Production-grade implementation

**BGV (`opt_main_bgv.jl`):**
- Integer scaling for real numbers (t=256)
- Polynomial degree n=2048 (demo), n=4096 (production)
- Multiplicative depth tracking
- Reduced iterations (20) for demonstration

**CKKS (`opt_main_ckks.jl`):**
- Native real number encoding with scaling
- Polynomial degree n=2048 (demo), n=4096 (production)
- Level/depth management for multiplications
- Reduced iterations (20) for demonstration

---

## 📖 Documentation Files

- **ENCRYPTION_SCHEMES_COMPARISON.md**: Detailed comparison of all schemes
- **ENCRYPTION_PERFORMANCE_IMPACT.md**: Explains why encryption doesn't slow optimization
- **OPTIMIZATION_GUIDE.md**: Explains sparse variable optimization
- **README_ADMM_PAILLIER.md**: Original Paillier implementation guide

---

## 🚀 Quick Start

1. **Fastest (Paillier)**:
   ```bash
   julia opt_main.jl
   # ~30 seconds for 14-bus network
   ```

2. **Post-Quantum Secure (BGV)**:
   ```bash
   julia opt_main_bgv.jl
   # ~15 minutes for 14-bus network (30x slower)
   ```

3. **Full FHE Research (CKKS)**:
   ```bash
   julia opt_main_ckks.jl
   # ~25 minutes for 14-bus network (50x slower)
   ```

4. **Compare All Schemes**:
   ```bash
   julia compare_encryption_schemes.jl
   # Quick benchmark on 10 encrypted values
   ```

---

## 🔐 Security Considerations

### Paillier:
- **Security Level**: ~1024-2048 bits (RSA equivalent)
- **Hardness Assumption**: RSA problem (factorization)
- **Post-Quantum**: ❌ NO - vulnerable to Shor's algorithm
- **Recommended Key Size**: 2048 bits (current), 3072 bits (future)

### BGV/BFV:
- **Security Level**: 80-256 bits (configurable with n)
  - n=2048: ~80 bits (demo only)
  - n=4096: ~128 bits (standard)
  - n=8192: ~256 bits (very high)
- **Hardness Assumption**: Ring-LWE (lattice-based)
- **Post-Quantum**: ✅ YES - no known quantum attacks
- **Recommended Parameters**: n≥4096 for production

### CKKS:
- **Security Level**: 80-256 bits (configurable with n)
  - n=2048: ~80 bits (demo only)
  - n=4096: ~128 bits (standard)
  - n=8192: ~256 bits (very high)
- **Hardness Assumption**: RLWE (Ring Learning With Errors)
- **Post-Quantum**: ✅ YES - no known quantum attacks
- **Recommended Parameters**: n≥4096 for production

---

## ⚠️ Important Notes

1. **Demo vs Production Parameters**:
   - Demo files use reduced parameters (n=2048, 20 iterations) for faster testing
   - Production should use n≥4096 and convergence-based termination

2. **Simulation vs Real Crypto**:
   - BGV and CKKS implementations are **simulators** for demonstration
   - Production use should employ libraries like:
     - Microsoft SEAL (C++)
     - HElib (C++)
     - Lattigo (Go)
     - TenSEAL (Python)

3. **Performance Scaling**:
   - Overhead multipliers (30x, 50x) are approximate
   - Actual performance depends on network size, parameters, hardware
   - Larger networks see better relative performance for FHE schemes

4. **Convergence**:
   - All schemes converge to same optimal cost as centralized OPF
   - Encryption overhead is purely in runtime, not solution quality

---

## 📚 References

### Paillier:
- Paillier, P. (1999). "Public-Key Cryptosystems Based on Composite Degree Residuosity Classes"

### BGV:
- Brakerski, Z., Gentry, C., & Vaikuntanathan, V. (2012). "Fully Homomorphic Encryption without Bootstrapping"

### BFV:
- Fan, J., & Vercauteren, F. (2012). "Somewhat Practical Fully Homomorphic Encryption"

### CKKS:
- Cheon, J. H., Kim, A., Kim, M., & Song, Y. (2017). "Homomorphic Encryption for Arithmetic of Approximate Numbers"

### ADMM:
- Boyd, S., et al. (2011). "Distributed Optimization and Statistical Learning via ADMM"

---

## 👥 Contributors

Developed for privacy-preserving distributed optimal power flow using Boyd's Consensus ADMM with homomorphic encryption.

---

## 📝 License

See main repository LICENSE file.
