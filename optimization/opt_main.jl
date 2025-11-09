"""
SELF-CONTAINED ADMM OPF with Paillier Homomorphic Encryption
All functions included in this single file - no external script dependencies
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
using Gurobi
using DataFrames
using LinearAlgebra
using JSON
using Dates
using Printf
using Random
using Primes

println("\n" * "="^80)
println(" ADMM OPF WITH PAILLIER ENCRYPTION")
println(" Self-contained implementation")
println("="^80 * "\n")

# ══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

mutable struct Generator
   ind::Int
   bus::Int
   p̅::Float64
   p̲::Float64
   c2::Float64
   c1::Float64
   c0::Float64
   function Generator(ind, bus, p̅, p̲, c2, c1, c0)
      gen = new()
      gen.ind = ind
      gen.bus = bus
      gen.p̅ = p̅
      gen.p̲ = p̲
      gen.c2 = c2
      gen.c1 = c1
      gen.c0 = c0
      return gen
   end
end

mutable struct Bus
   ind::Int
   d::Float64
   c::Float64
   type::Int
   N::Vector{Int}
   G::Vector{Int}
   Λ::Vector{Int}
   function Bus(ind, d, c, type, N, G, Λ)
      i = new()
      i.ind = ind
      i.d = d
      i.c = c
      i.type = type
      i.N = N
      i.G = G
      i.Λ = Λ
      return i
   end
end

mutable struct Line
   ind::Int
   b_f::Int
   b_t::Int
   β::Float64
   f̅::Float64
   function Line(ind, b_f, b_t, β, f̅)
      l = new()
      l.ind = ind
      l.b_f = b_f
      l.b_t = b_t
      l.β = β
      l.f̅ = f̅
      return l
   end
end

# ══════════════════════════════════════════════════════════════════════════════
# PAILLIER CRYPTOSYSTEM
# ══════════════════════════════════════════════════════════════════════════════

mutable struct PaillierPublicKey
    n::BigInt
    n_sq::BigInt
    g::BigInt
    function PaillierPublicKey(n::BigInt)
        new(n, n^2, n + 1)
    end
end

mutable struct PaillierPrivateKey
    λ::BigInt
    μ::BigInt
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

function L(x::BigInt, n::BigInt)::BigInt
    return div(x - 1, n)
end

function generate_keypair(key_length::Int=1024)::PaillierKeypair
    println("  🔐 Generating $(key_length)-bit primes...")
    bit_length = div(key_length, 2)

    p = nextprime(rand(BigInt(2)^(bit_length-1):BigInt(2)^bit_length))
    q = nextprime(rand(BigInt(2)^(bit_length-1):BigInt(2)^bit_length))

    while p == q
        q = nextprime(rand(BigInt(2)^(bit_length-1):BigInt(2)^bit_length))
    end

    n = p * q
    λ = lcm(p - 1, q - 1)
    g = n + 1

    μ = invmod(L(powermod(g, λ, n^2), n), n)

    public_key = PaillierPublicKey(n)
    private_key = PaillierPrivateKey(λ, μ)

    return PaillierKeypair(public_key, private_key)
end

function encrypt(public_key::PaillierPublicKey, plaintext::Float64)::EncryptedNumber
    m = BigInt(round(plaintext * 1e6))
    r = rand(BigInt(1):public_key.n-1)

    n_sq = public_key.n_sq
    g_m = powermod(public_key.g, m, n_sq)
    r_n = powermod(r, public_key.n, n_sq)

    c = mod(g_m * r_n, n_sq)
    return EncryptedNumber(c, public_key)
end

function decrypt(public_key::PaillierPublicKey, private_key::PaillierPrivateKey,
                 encrypted::EncryptedNumber)::Float64
    c_lambda = powermod(encrypted.ciphertext, private_key.λ, public_key.n_sq)
    m = mod(L(c_lambda, public_key.n) * private_key.μ, public_key.n)

    m_signed = m > public_key.n ÷ 2 ? m - public_key.n : m
    return Float64(m_signed) / 1e6
end

function Base.:+(a::EncryptedNumber, b::EncryptedNumber)::EncryptedNumber
    if a.public_key.n != b.public_key.n
        error("Cannot add encrypted numbers with different public keys")
    end
    c_sum = mod(a.ciphertext * b.ciphertext, a.public_key.n_sq)
    return EncryptedNumber(c_sum, a.public_key)
end

function Base.:*(scalar::Float64, encrypted::EncryptedNumber)::EncryptedNumber
    k = BigInt(round(scalar * 1e6))
    c_mult = powermod(encrypted.ciphertext, k, encrypted.public_key.n_sq)
    return EncryptedNumber(c_mult, encrypted.public_key)
end

function encrypted_average(encrypted_values::Vector{EncryptedNumber})::EncryptedNumber
    if isempty(encrypted_values)
        error("Cannot average empty vector")
    end

    sum_enc = encrypted_values[1]
    for i in 2:length(encrypted_values)
        sum_enc = sum_enc + encrypted_values[i]
    end

    n = length(encrypted_values)
    avg_enc = (1.0 / n) * sum_enc

    return avg_enc
end

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

function load_data(caseID::String)
    data = PowerModels.parse_file(caseID)
    PowerModels.standardize_cost_terms!(data, order=2)
    PowerModels.calc_thermal_limits!(data)

    # Build generators
    gen = SortedDict{Int, Generator}()
    for g in 1:length(data["gen"])
        c2 = data["gen"][string(g)]["cost"][1]
        c1 = data["gen"][string(g)]["cost"][2]
        c0 = data["gen"][string(g)]["cost"][3]
        p̅ = data["gen"][string(g)]["pmax"]
        p̲ = data["gen"][string(g)]["pmin"]
        ind = data["gen"][string(g)]["index"]
        bus = data["gen"][string(g)]["gen_bus"]

        add_gen = Generator(ind, bus, p̅, p̲, c2, c1, c0)
        gen[add_gen.ind] = add_gen
    end

    # Build buses
    bus = SortedDict{Int, Bus}()
    for b in 1:length(data["bus"])
        ind = data["bus"][string(b)]["bus_i"]
        type = data["bus"][string(b)]["bus_type"]
        c = 1e3

        d = 0.0
        for l in 1:length(data["load"])
            if data["load"][string(l)]["load_bus"] == b
                d += data["load"][string(l)]["pd"] * data["baseMVA"]
            end
        end

        N = Int[]
        G = Int[]
        Λ = Int[]
        add_bus = Bus(ind, d, c, type, N, G, Λ)
        bus[add_bus.ind] = add_bus
    end

    # Build generators at buses
    for b in 1:length(data["bus"])
        for g in 1:length(data["gen"])
            if data["gen"][string(g)]["gen_bus"] == b
                push!(bus[b].G, g)
            end
        end
    end

    # Build lines
    line = SortedDict{Int, Line}()
    for l in 1:length(data["branch"])
        ind = data["branch"][string(l)]["index"]
        b_f = data["branch"][string(l)]["f_bus"]
        b_t = data["branch"][string(l)]["t_bus"]
        β = 1 / data["branch"][string(l)]["br_x"]
        f̅ = data["branch"][string(l)]["rate_a"]

        add_line = Line(ind, b_f, b_t, β, f̅)
        line[add_line.ind] = add_line
    end

    # Lines at buses
    for b in 1:length(data["bus"])
        for l in 1:length(data["branch"])
            if data["branch"][string(l)]["f_bus"] == b
                push!(bus[b].Λ, l)
            end
            if data["branch"][string(l)]["t_bus"] == b
                push!(bus[b].Λ, l)
            end
        end
    end

    # Build neighbors
    for b in 1:length(data["bus"])
        for l in 1:length(data["branch"])
            if data["branch"][string(l)]["f_bus"] == b
                push!(bus[b].N, data["branch"][string(l)]["t_bus"])
            end
            if data["branch"][string(l)]["t_bus"] == b
                push!(bus[b].N, data["branch"][string(l)]["f_bus"])
            end
            push!(bus[b].N, b)
            bus[b].N = unique(bus[b].N)
        end
    end

    bus = SortedDict(bus)
    gen = SortedDict(gen)
    line = SortedDict(line)

    # Build susceptance matrix
    Nb = length(bus)
    B = zeros(Nb, Nb)
    for i in 1:Nb
        for l in bus[i].Λ
            if line[l].b_f == i
                B[i, line[l].b_t] = -line[l].β
                B[i, i] += line[l].β
            elseif line[l].b_t == i
                B[i, line[l].b_f] = -line[l].β
                B[i, i] += line[l].β
            end
        end
    end

    # Reference bus
    refbus = 0
    for b in 1:Nb
        if bus[b].type == 3
            refbus = b
            break
        end
    end

    return gen, bus, line, B, refbus
end

# ══════════════════════════════════════════════════════════════════════════════
# CENTRALIZED OPF
# ══════════════════════════════════════════════════════════════════════════════

function OPF_centralized(gen, bus, line, B, refbus, gurobi_env)
    Ng = length(gen)
    Nb = length(bus)

    model = Model(() -> Gurobi.Optimizer(gurobi_env))
    set_silent(model)

    @variable(model, p[1:Ng])
    @variable(model, θ[1:Nb])
    @variable(model, l[1:Nb])

    @constraint(model, ϕ̲[i=1:Nb, g=bus[i].G], gen[g].p̲ <= p[g])
    @constraint(model, ϕ̅[i=1:Nb, g=bus[i].G], p[g] <= gen[g].p̅)
    @constraint(model, ψ̲[i=1:Nb], -bus[i].d <= l[i])
    @constraint(model, ψ̅[i=1:Nb], l[i] <= bus[i].d)
    @constraint(model, η̲[i=1:Nb, l_idx=bus[i].Λ],
                -line[l_idx].f̅ <= line[l_idx].β * (θ[line[l_idx].b_f] - θ[line[l_idx].b_t]))
    @constraint(model, η̅[i=1:Nb, l_idx=bus[i].Λ],
                line[l_idx].β * (θ[line[l_idx].b_f] - θ[line[l_idx].b_t]) <= line[l_idx].f̅)
    @constraint(model, λ[i=1:Nb],
                sum(B[i,j] * θ[j] for j in bus[i].N) ==
                sum(p[g] for g in bus[i].G) - bus[i].d + l[i])
    @constraint(model, κ, θ[refbus] == 0)

    for i in 1:Nb
        if bus[i].type == 1
            @constraint(model, l[i] == 0)
        end
    end

    @objective(model, Min,
               sum(gen[g].c2 * p[g]^2 + gen[g].c1 * p[g] + gen[g].c0 for g in 1:Ng) +
               sum(bus[i].c * l[i]^2 for i in 1:Nb))

    optimize!(model)

    cost = objective_value(model)
    dispatch = zeros(Nb, 6)
    power_flow = zeros(length(line), 5)

    return cost, dispatch, power_flow
end

# ══════════════════════════════════════════════════════════════════════════════
# ADMM FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

function update_θ(gen, bus, line, B, refbus, μ, θ̅, ρ, gurobi_env)
    Ng = length(gen)
    Nb = length(bus)

    model = Model(() -> Gurobi.Optimizer(gurobi_env))
    set_silent(model)

    @variable(model, p[1:Ng])
    @variable(model, θ[1:Nb, 1:Nb])
    @variable(model, l[1:Nb])

    @constraint(model, ϕ̲[i=1:Nb, g=bus[i].G], gen[g].p̲ <= p[g])
    @constraint(model, ϕ̅[i=1:Nb, g=bus[i].G], p[g] <= gen[g].p̅)
    @constraint(model, ψ̲[i=1:Nb], -bus[i].d <= l[i])
    @constraint(model, ψ̅[i=1:Nb], l[i] <= bus[i].d)
    @constraint(model, η̲[i=1:Nb, l_idx=bus[i].Λ],
                -line[l_idx].f̅ <= line[l_idx].β * (θ[i,line[l_idx].b_f] - θ[i,line[l_idx].b_t]))
    @constraint(model, η̅[i=1:Nb, l_idx=bus[i].Λ],
                line[l_idx].β * (θ[i,line[l_idx].b_f] - θ[i,line[l_idx].b_t]) <= line[l_idx].f̅)
    @constraint(model, λ[i=1:Nb],
                sum(B[i,j] * θ[i,j] for j in bus[i].N) ==
                sum(p[g] for g in bus[i].G) - bus[i].d + l[i])
    @constraint(model, κ[i=1:Nb], θ[i,refbus] == 0)

    for i in 1:Nb
        if bus[i].type == 1
            @constraint(model, l[i] == 0)
        end
    end

    @objective(model, Min,
               sum(gen[g].c2 * p[g]^2 + gen[g].c1 * p[g] + gen[g].c0 for g in 1:Ng) +
               sum(bus[i].c * l[i]^2 for i in 1:Nb) -
               sum(μ[i,j] * θ[i,j] for i in 1:Nb for j in bus[i].N) +
               ρ/2 * sum((θ̅[j] - θ[i,j])^2 for i in 1:Nb for j in bus[i].N))

    optimize!(model)

    cost = sum(gen[g].c2 * JuMP.value(p[g])^2 + gen[g].c1 * JuMP.value(p[g]) + gen[g].c0 for g in 1:Ng) +
           sum(bus[i].c * JuMP.value(l[i])^2 for i in 1:Nb)

    return JuMP.value.(θ), cost, JuMP.value.(p), JuMP.value.(l)
end

function update_θ̅(bus, θ)
    Nb = length(bus)
    θ̅ = zeros(Nb)

    for i in 1:Nb
        θ̅[i] = sum(θ[j,i] for j in bus[i].N) / length(bus[i].N)
    end

    return θ̅
end

function update_μ(bus, ρ, θ, θ̅, μ)
    Nb = length(bus)
    mu = ones(Nb, Nb)

    for i in 1:Nb
        for j in bus[i].N
            mu[i,j] = μ[i,j] + ρ * (θ̅[j] - θ[i,j])
        end
    end

    return mu
end

function residual(bus, θ, θ̅)
    Nb = length(bus)
    Γ = sum(abs(θ̅[j] - θ[i,j]) for i in 1:Nb for j in bus[i].N)
    return Γ
end

# ══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

function encrypt_θ_dense(public_key::PaillierPublicKey, bus, θ::Matrix{Float64})
    Nb = length(bus)
    θ_enc = Matrix{Union{EncryptedNumber, Nothing}}(nothing, Nb, Nb)

    for i in 1:Nb
        for j in bus[i].N
            θ_enc[i,j] = encrypt(public_key, θ[i,j])
        end
    end

    return θ_enc
end

function update_θ̅_homomorphic(public_key::PaillierPublicKey, private_key::PaillierPrivateKey,
                                bus, θ_enc::Matrix{Union{EncryptedNumber, Nothing}})
    Nb = length(bus)
    θ̅ = zeros(Nb)

    for i in 1:Nb
        enc_neighbors = EncryptedNumber[]
        for j in bus[i].N
            if !isnothing(θ_enc[j,i])
                push!(enc_neighbors, θ_enc[j,i])
            end
        end

        if !isempty(enc_neighbors)
            θ̅_enc_i = encrypted_average(enc_neighbors)
            θ̅[i] = decrypt(public_key, private_key, θ̅_enc_i)
        end
    end

    return θ̅
end

# ══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

println("[1/6] Loading network data...")
caseID = "testbeds/pglib_opf_case30_ieee.m"
network_name = split(split(caseID, "/")[end], ".")[1]
println("  ✓ Using network: $network_name")

(gen, bus, line, B, refbus) = load_data(caseID)
Ng = length(gen)
Nb = length(bus)
println("  ✓ Loaded: $Nb buses, $Ng generators, $(length(line)) lines")

println("\n[2/6] Initializing Gurobi and solving centralized OPF (baseline)...")
gurobi_env = Gurobi.Env()
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus, gurobi_env)
println("  ✓ Centralized cost: \$$(round(cost_c, digits=2))")

println("\n[3/6] Generating Paillier encryption keys...")
key_length = 1024
key_start = time()
keypair = generate_keypair(key_length)
key_time = time() - key_start
println("  ✓ Keys generated in $(round(key_time, digits=2))s")

println("\n[4/6] Testing Paillier homomorphic operations...")
a, b = 15.5, 24.5
enc_sum = encrypt(keypair.public_key, a) + encrypt(keypair.public_key, b)
dec_sum = decrypt(keypair.public_key, keypair.private_key, enc_sum)
println("  ✓ E($a) + E($b) = $(round(dec_sum, digits=1)) (expected: $(a+b))")

println("\n[5/6] Initializing ADMM parameters...")
ν̅ = 1000
ρ = 10.0
γ = 1e-2

μ = zeros(Nb, Nb)
θ = zeros(Nb, Nb)
θ̅ = zeros(Nb)
p_history = zeros(Ng, ν̅)
l_history = zeros(Nb, ν̅)
cost_history = zeros(ν̅)
residuals = zeros(ν̅)

println("  ✓ Parameters: ρ=$ρ, max_iter=$ν̅, tolerance=$γ")
println("  ✓ Using $(key_length)-bit Paillier encryption")

println("\n[6/6] Running ADMM with Paillier encryption...")
println("\n" * "─"^110)
@printf("%-5s %-12s %-12s %-10s | %-8s %-8s %-8s | %-10s\n",
        "Iter", "Cost(\$)", "Residual", "Δ Res", "OPT(s)", "CRYPTO(s)", "OTHER(s)", "Total(s)")
println("─"^110)

converged = false
final_iter = ν̅
total_opt_time = 0.0
total_crypto_time = 0.0
total_other_time = 0.0
admm_start_time = time()
iteration_times = Float64[]
iteration_timestamps = Float64[]

for ν in 2:ν̅
    global μ, θ, θ̅, converged, final_iter
    global total_opt_time, total_crypto_time, total_other_time

    iter_start = time()

    # Primal update
    opt_start = time()
    θ, cost_history[ν], p_history[:, ν], l_history[:, ν] = update_θ(gen, bus, line, B, refbus, μ, θ̅, ρ, gurobi_env)
    opt_time = time() - opt_start

    # Encryption
    enc_start = time()
    θ_enc = encrypt_θ_dense(keypair.public_key, bus, θ)
    enc_time = time() - enc_start

    # Consensus
    cons_start = time()
    θ̅ = update_θ̅_homomorphic(keypair.public_key, keypair.private_key, bus, θ_enc)
    cons_time = time() - cons_start

    crypto_time = enc_time + cons_time

    # Dual update
    dual_start = time()
    μ = update_μ(bus, ρ, θ, θ̅, μ)
    residuals[ν] = residual(bus, θ, θ̅)
    other_time = time() - dual_start

    iter_time = time() - iter_start
    cumulative_time = time() - admm_start_time

    push!(iteration_times, iter_time)
    push!(iteration_timestamps, cumulative_time)

    total_opt_time += opt_time
    total_crypto_time += crypto_time
    total_other_time += other_time

    if ν == 2 || ν % 10 == 0 || residuals[ν] <= γ
        Δres = ν > 2 ? residuals[ν-1] - residuals[ν] : 0.0
        @printf("%-5d \$%-11.2f %-12.6f %-10.6f | %-8.3f %-8.3f %-8.3f | %-10.3f\n",
                ν, cost_history[ν], residuals[ν], Δres, opt_time, crypto_time, other_time, iter_time)
    end

    if residuals[ν] <= γ
        println("─"^110)
        println("✅ CONVERGED at iteration $ν")
        final_iter = ν
        converged = true
        break
    end
end

admm_total_time = time() - admm_start_time

if !converged
    println("─"^110)
    println("⚠️  Maximum iterations reached")
end

println("\n" * "="^80)
println(" RESULTS SUMMARY")
println("="^80)
println("  Converged:           $converged")
println("  Iterations:          $final_iter / $ν̅")
println("  Total time:          $(round(admm_total_time, digits=2))s")
println()
println("  Centralized cost:    \$$(round(cost_c, digits=2))")
println("  Final cost:          \$$(round(cost_history[final_iter], digits=2))")
println("  Optimality loss:     $(round(abs(cost_c - cost_history[final_iter])/cost_c*100, digits=4))%")
println()
pct_opt = total_opt_time / admm_total_time * 100
pct_crypto = total_crypto_time / admm_total_time * 100
pct_other = total_other_time / admm_total_time * 100
println("  Timing breakdown:")
println("    Optimization:      $(round(total_opt_time, digits=2))s ($(round(pct_opt, digits=1))%)")
println("    Cryptography:      $(round(total_crypto_time, digits=2))s ($(round(pct_crypto, digits=1))%)")
println("    Other:             $(round(total_other_time, digits=2))s ($(round(pct_other, digits=1))%)")
println("="^80)

# Save results
output_dir = "results"
if !isdir(output_dir)
    mkpath(output_dir)
end

results = Dict(
    "scheme" => "paillier",
    "converged" => converged,
    "iterations" => final_iter,
    "total_time_s" => admm_total_time,
    "centralized_cost" => cost_c,
    "final_cost" => cost_history[final_iter],
    "optimality_loss_percent" => abs(cost_c - cost_history[final_iter]) / cost_c * 100,
    "final_residual" => residuals[final_iter],
    "pct_opt" => pct_opt,
    "pct_crypto" => pct_crypto,
    "pct_other" => pct_other,
    "iteration_times" => iteration_times,
    "residuals" => residuals[2:final_iter],
    "cost_history" => cost_history[2:final_iter]
)

output_file = joinpath(output_dir, "paillier_results.json")
open(output_file, "w") do f
    JSON.print(f, results, 4)
end

println("\n✓ Results saved to: $output_file\n")
