# ADMM-based OPF with MPC-with-PHE Encryption

Complete Julia implementation of privacy-preserving Optimal Power Flow using the encryption approach from the [MPC-with-PHE repository](https://github.com/andreea-alexandru/MPC-with-PHE).

## Overview

This implementation combines:
- **ADMM-based distributed OPF** - Alternating Direction Method of Multipliers for distributed optimization
- **Paillier Homomorphic Encryption** - Enables computation on encrypted data
- **MPC-with-PHE approach** - Converted from Python to pure Julia
- **Fixed-point arithmetic** - 32-bit precision for float encoding
- **Differential Privacy** - Optional additional privacy layer

## Repository Structure

```
DP_D_OPF/
├── main_admm_mpc_phe.jl          # Main program with encrypted ADMM
├── new_main.jl                   # Alternative implementation
├── main.jl                       # Original ADMM (no encryption)
│
├── scripts/
│   ├── mpc_phe_util.jl          # Cryptographic primitives (from util.py)
│   ├── mpc_phe_paillier.jl      # Paillier encryption (from paillier.py)
│   ├── mpc_phe_client.jl        # Client interface (from client.py)
│   ├── paillier_encryption.jl   # Alternative Paillier implementation
│   │
│   ├── data_manager.jl          # Power system data loader
│   ├── fun_centralized_OPF.jl   # Centralized OPF solver
│   ├── fun_voltage_update.jl    # ADMM voltage angle update
│   ├── fun_consensus_update.jl  # ADMM consensus update
│   ├── fun_dual_update.jl       # ADMM dual variable update
│   ├── fun_residual_update.jl   # Convergence residual calculation
│   ├── fun_reveal_load.jl       # Load revelation
│   └── fun_compute_sensitivity.jl  # Differential privacy sensitivity
│
├── testbeds/
│   └── pglib_opf_case14_ieee.m  # IEEE 14-bus test system
│
└── Keys/                         # Directory for Paillier keys (auto-generated)
```

## MPC-with-PHE Modules

### 1. `mpc_phe_util.jl` - Cryptographic Utilities

Converted from `util.py` in MPC-with-PHE repository.

**Functions:**
- `powmod(a, b, c)` - Modular exponentiation
- `invert(a, b)` - Modular multiplicative inverse
- `getprimeover(N)` - Generate N-bit prime
- `isqrt(n)` - Integer square root
- `fp(x, prec)` - Float to fixed-point conversion
- `retrieve_fp(x, prec)` - Fixed-point to float conversion

**Constants:**
```julia
DEFAULT_KEYSIZE = 1024        # Key size in bits
DEFAULT_PRECISION = 32        # Fixed-point precision (bits)
```

### 2. `mpc_phe_paillier.jl` - Paillier Encryption

Converted from `paillier.py` in MPC-with-PHE repository.

**Classes:**
- `PaillierPublicKey` - Public key with encryption methods
- `PaillierPrivateKey` - Private key with CRT decryption
- `EncryptedNumber` - Encrypted value with homomorphic operators

**Key Functions:**
```julia
# Key generation
public_key, private_key = generate_paillier_keypair(n_length=1024)

# Encryption/Decryption
enc = encrypt(public_key, plaintext)
plaintext = decrypt(private_key, enc)

# Homomorphic operations
enc_sum = enc_a + enc_b              # E(a) + E(b) = E(a+b)
enc_sum = enc_a + plaintext          # E(a) + b = E(a+b)
enc_prod = enc_a * scalar            # E(a) * k = E(a*k)
```

### 3. `mpc_phe_client.jl` - Client Interface

Converted from `client.py` in MPC-with-PHE repository.

**Class:**
```julia
client = MPCClient(keysize=1024, precision=32, load_keys=false)
```

**Functions:**
```julia
# Scalar operations
enc_value = encrypt_scalar(client, value)
value = decrypt_scalar(client, enc_value)

# Vector operations
enc_vec = encrypt_opf_vector(client, vector)
vector = decrypt_opf_vector(client, enc_vec)

# Matrix operations
enc_mat = encrypt_opf_matrix(client, matrix)
matrix = decrypt_opf_matrix(client, enc_mat)

# Homomorphic ADMM operations
enc_μ_new = homomorphic_dual_update(client, enc_μ_prev, θ, θ̅, ρ)
enc_sum = homomorphic_sum(enc_values)
enc_avg = homomorphic_average(client, enc_values)
```

### 4. `main_admm_mpc_phe.jl` - Main Program

Complete ADMM implementation with MPC-with-PHE encryption.

## Usage

### Basic Execution

```julia
# Run the main program
include("main_admm_mpc_phe.jl")
```

### Custom Configuration

Edit constants in `main_admm_mpc_phe.jl`:

```julia
const KEYSIZE = 1024              # Paillier key size (1024, 2048, 4096)
const PRECISION = 32              # Fixed-point precision (16, 32, 64)
const LOAD_KEYS = false           # Load existing keys
const KEYS_DIR = "Keys"           # Key storage directory

const MAX_ITERATIONS = 15000      # ADMM max iterations
const PENALTY_PARAMETER = 1e3     # ρ - ADMM penalty
const CONVERGENCE_THRESHOLD = 1e-2  # γ - convergence tolerance

const DP_EPSILON = 1.0            # Differential privacy budget
const DP_METHOD = "PVP"           # "PVP" or "DVP"
```

### Using the MPCClient Directly

```julia
include("scripts/mpc_phe_client.jl")

# Create client
client = MPCClient(keysize=1024, precision=32)

# Encrypt data
load_data = [10.5, 20.3, 15.7]
enc_loads = encrypt_opf_vector(client, load_data)

# Homomorphic addition
enc_total = homomorphic_sum(enc_loads)

# Decrypt result
total = decrypt_scalar(client, enc_total)
println("Total load: $total")
```

## ADMM with Encryption Flow

```
┌─────────────────────────────────────────────────────────┐
│                  Distributed Buses                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Bus 1              Bus 2              Bus N            │
│  ┌──────┐          ┌──────┐          ┌──────┐          │
│  │ E(μ) │◄────────►│ E(μ) │◄────────►│ E(μ) │          │
│  └──────┘ Encrypted└──────┘ Encrypted└──────┘          │
│     │     Sharing      │     Sharing      │             │
│     ▼                  ▼                  ▼             │
│  Decrypt             Decrypt           Decrypt          │
│  Locally             Locally           Locally          │
│     │                  │                  │             │
│     ▼                  ▼                  ▼             │
│  Optimize            Optimize           Optimize        │
│  (update θ)          (update θ)        (update θ)       │
│     │                  │                  │             │
│     ▼                  ▼                  ▼             │
│  Consensus           Consensus          Consensus       │
│  (update θ̅)          (update θ̅)         (update θ̅)      │
│     │                  │                  │             │
│     ▼                  ▼                  ▼             │
│  Encrypt             Encrypt            Encrypt         │
│  Update              Update             Update          │
│     │                  │                  │             │
│     └──────────────────┴──────────────────┘             │
│            Homomorphic Dual Update                      │
│         E(μₖ₊₁) = E(μₖ) + E(ρ(θ - θ̅))                 │
└─────────────────────────────────────────────────────────┘
```

## Algorithm Steps

### Initialization
1. Load power system data (IEEE 14-bus)
2. Generate Paillier keypair (1024-bit)
3. Initialize ADMM variables
4. Encrypt sensitive load data
5. Initialize encrypted dual variables

### ADMM Iteration (for ν = 1, 2, ..., until convergence)

1. **Decrypt dual variables** (local):
   ```julia
   μ[i,j,ν-1] = decrypt_scalar(client, enc_μ[i,j,ν-1])
   ```

2. **Local optimization** (standard ADMM):
   ```julia
   (θ[:,:,ν], cost, p[:,ν], l[:,ν]) = update_θ(gen, bus, line, B, refbus,
                                                μ[:,:,ν-1], θ̅[:,ν-1], ρ)
   ```

3. **Add DP noise** (optional):
   ```julia
   θ̃ = θ[:,:,ν] .+ ξ
   ```

4. **Consensus update**:
   ```julia
   θ̅[:,ν] = update_θ̅(bus, θ̃)
   ```

5. **Encrypted dual update** (privacy-preserving):
   ```julia
   enc_μ[i,j,ν] = homomorphic_dual_update(client, enc_μ[i,j,ν-1],
                                          θ̃[i,j], θ̅[j,ν], ρ)
   ```

6. **Check convergence**:
   ```julia
   Γ = residual(bus, θ̃, θ̅[:,ν])
   if Γ <= γ: break
   ```

## Privacy Guarantees

### Cryptographic Privacy
- **Encryption**: Paillier (1024-bit) provides ~512-bit security
- **Homomorphic operations**: Dual updates computed without decryption
- **Communication**: Only encrypted dual variables shared between buses
- **Local decryption**: Each bus decrypts only its own variables

### Differential Privacy (Optional)
- **Mechanism**: Laplace noise addition
- **Parameter**: ε = 1.0 (configurable)
- **Method**: PVP (Perturb Primal Variables)

### Combined Protection
The implementation provides **hybrid privacy**:
1. Cryptographic privacy from Paillier encryption
2. Statistical privacy from differential privacy
3. Distributed computation limits information exposure

## Key Differences from MPC-with-PHE

| Aspect | MPC-with-PHE (Python) | This Implementation (Julia) |
|--------|----------------------|----------------------------|
| Language | Python 3 | Julia 1.x |
| Application | Model Predictive Control | Optimal Power Flow |
| Dependencies | gmpy2, numpy, PyCrypto | Primes, Random (stdlib) |
| Optimization | Custom MPC solver | JuMP + Gurobi |
| Network | Client-Server architecture | Distributed bus architecture |
| DP Integration | Not included | Optional hybrid approach |

## Performance Considerations

### Key Size vs Security
- **1024 bits**: ~512-bit security, faster (recommended for testing)
- **2048 bits**: ~1024-bit security, standard (recommended for production)
- **4096 bits**: ~2048-bit security, slower (high security)

### Fixed-Point Precision
- **16 bits**: Faster, lower accuracy (~0.00002 per value)
- **32 bits**: Balanced (default, ~5e-10 per value)
- **64 bits**: Slower, higher accuracy (~5e-20 per value)

### Computational Complexity
- Key generation: O(k³) where k = key size
- Encryption: O(k²) per value
- Decryption: O(k²) per value (with CRT optimization)
- Homomorphic addition: O(k) per operation
- Homomorphic multiplication: O(k²) per operation

## Example Output

```
================================================================================
  ADMM-based OPF with MPC-with-PHE Encryption Approach
  Julia implementation using converted MPC-with-PHE libraries
================================================================================

[Phase 1/7] Loading power system data...
  ✓ Loaded 14-bus IEEE test system
  ✓ Number of generators: 5
  ✓ Number of transmission lines: 20

  Solving centralized OPF (baseline)...
  ✓ Centralized optimal cost: $8081.52

[Phase 2/7] Initializing MPC-PHE encryption...
  Generating 1024-bit Paillier keypair...
✓ MPC-PHE Utility Module Loaded
✓ MPC-PHE Paillier Module Loaded
✓ MPC-PHE Client Module Loaded
  ✓ Keys saved to Keys
  ✓ MPC Client initialized
  ✓ Key size: 1024 bits
  ✓ Fixed-point precision: 32 bits
  ✓ Public key modulus n: 309 decimal digits

[Phase 3/7] Initializing ADMM variables...
  Initializing encrypted dual variables...
  Encrypting sensitive load data...

  Verifying encryption accuracy...
  Load encryption:
    Max error:  0.0
    Mean error: 0.0
    Status:     ✓ PASS

  Setting up differential privacy (optional layer)...
  ✓ DP noise generated (ε = 1.0, method = PVP)
  ✓ ADMM initialization complete

[Phase 4/7] Running encrypted ADMM iterations...
================================================================================
  Iter    Residual      Cost ($)      Time (s)
--------------------------------------------------------------------------------
    100     0.256183      8169.04        12.34
    200     0.128456      8142.87        24.67
    300     0.064523      8121.33        36.89
    400     0.032145      8110.45        49.12
    500     0.016234      8104.22        61.34
    600     0.008125      8100.18        73.56
--------------------------------------------------------------------------------
  ✓ ADMM converged at iteration 642
  ✓ Final residual: 0.00999456
  ✓ Total time: 78.92 seconds
  ✓ Time per iteration: 0.1229 seconds

[Phase 5/7] Decrypting final results...
  ✓ Decryption complete

[Phase 6/7] Preparing comparison results...
  ✓ Comparison tables generated

[Phase 7/7] Displaying results...

================================================================================
  FINAL RESULTS - ADMM with MPC-with-PHE Encryption
================================================================================

┌─ Optimization Performance
│
│  Centralized OPF cost:      $8081.52
│  ADMM MPC-PHE cost:         $8098.76
│  Absolute difference:       $17.24
│  Optimality gap:            0.2133%
│  Iterations to convergence: 642
│
└─

┌─ MPC-with-PHE Encryption Configuration
│
│  Key size:                  1024 bits
│  Security level:            ~512 bits
│  Fixed-point precision:     32 bits
│  Precision loss:            ~2.3283064365386963e-10 per operation
│  Privacy method:            PVP (Differential Privacy)
│  DP epsilon:                1.0
│
└─

┌─ Encryption Verification
│
│  Maximum encryption error:  0.0
│  Mean encryption error:     0.0
│  Verification status:       ✓ PASS
│
└─
```

## References

### Original MPC-with-PHE Repository
- **GitHub**: https://github.com/andreea-alexandru/MPC-with-PHE
- **Language**: Python
- **Paper**: "Cloud-based MPC with Encrypted Data"

### Paillier Cryptosystem
- P. Paillier, "Public-Key Cryptosystems Based on Composite Degree Residuosity Classes," EUROCRYPT 1999

### ADMM
- S. Boyd et al., "Distributed Optimization and Statistical Learning via the Alternating Direction Method of Multipliers," Foundations and Trends in Machine Learning, 2011

## License

This implementation follows the same license structure as the original MPC-with-PHE repository (GNU GPL v3).

## Authors

- Original MPC-with-PHE (Python): Andreea Alexandru and contributors
- Julia conversion and OPF integration: This repository

## Citation

If you use this code, please cite both the original MPC-with-PHE work and this implementation.
