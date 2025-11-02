"""
ISOLATED TEST: Verify ADMM Convergence Without Encryption

Tests the core ADMM algorithm to verify:
1. Consensus averaging is correct
2. Residuals decrease monotonically
3. Converges to centralized OPF solution
"""

using PowerModels
using DataStructures: SortedDict
using JuMP
using Ipopt
using Printf

println("\n" * "="^80)
println(" ISOLATED ADMM CONVERGENCE TEST (No Encryption)")
println("="^80 * "\n")

# Load data manager
include("scripts/data_manager.jl")
include("scripts/fun_centralized_OPF.jl")

# ══════════════════════════════════════════════════════════════════════════════
# SPARSE ADMM FUNCTIONS (FIXED VERSION)
# ══════════════════════════════════════════════════════════════════════════════

function update_θ_sparse(gen, bus, line, B, refbus, μ, θ̅, ρ)
    Ng = length(gen)
    Nb = length(bus)

    model = Model(optimizer_with_attributes(Ipopt.Optimizer,
                                           "print_level" => 0,
                                           "sb" => "yes"))

    @variable(model, p[1:Ng])
    @variable(model, l[1:Nb])

    θ = Dict{Tuple{Int,Int}, VariableRef}()
    for i in 1:Nb
        for j in bus[i].N
            θ[(i,j)] = @variable(model, base_name="θ[$i,$j]")
        end
    end

    @constraint(model, ϕ̲[i=1:Nb, g=bus[i].G], gen[g].p̲ <= p[g])
    @constraint(model, ϕ̅[i=1:Nb, g=bus[i].G], p[g] <= gen[g].p̅)
    @constraint(model, ψ̲[i=1:Nb], -bus[i].d <= l[i])
    @constraint(model, ψ̅[i=1:Nb], l[i] <= bus[i].d)
    @constraint(model, η̲[i=1:Nb, l_idx=bus[i].Λ],
                -line[l_idx].f̅ <= line[l_idx].β * (θ[(i, line[l_idx].b_f)] - θ[(i, line[l_idx].b_t)]))
    @constraint(model, η̅[i=1:Nb, l_idx=bus[i].Λ],
                line[l_idx].β * (θ[(i, line[l_idx].b_f)] - θ[(i, line[l_idx].b_t)]) <= line[l_idx].f̅)
    @constraint(model, λ[i=1:Nb],
                sum(B[i, j] * θ[(i,j)] for j in bus[i].N) ==
                sum(p[g] for g in bus[i].G) - bus[i].d + l[i])
    @constraint(model, κ[i=1:Nb; refbus in bus[i].N], θ[(i, refbus)] == 0)

    for i in 1:Nb
        if bus[i].type == 1
            @constraint(model, l[i] == 0)
        end
    end

    @objective(model, Min,
               sum(gen[g].c2 * p[g]^2 + gen[g].c1 * p[g] + gen[g].c0 for g in 1:Ng) +
               sum(bus[i].c * l[i]^2 for i in 1:Nb) -
               sum(μ[i,j] * θ[(i,j)] for i in 1:Nb for j in bus[i].N) +
               ρ / 2 * sum((θ̅[j] - θ[(i,j)])^2 for i in 1:Nb for j in bus[i].N))

    optimize!(model)

    θ_sol = Dict{Tuple{Int,Int}, Float64}()
    for i in 1:Nb
        for j in bus[i].N
            θ_sol[(i,j)] = JuMP.value(θ[(i,j)])
        end
    end

    p_sol = JuMP.value.(p)
    l_sol = JuMP.value.(l)
    cost = sum(gen[g].c2 * p_sol[g]^2 + gen[g].c1 * p_sol[g] + gen[g].c0 for g in 1:Ng) +
           sum(bus[i].c * l_sol[i]^2 for i in 1:Nb)

    return θ_sol, cost, p_sol, l_sol
end

function update_θ̅_sparse(bus, θ_sparse)
    Nb = length(bus)
    θ̅ = zeros(Nb)

    for i in 1:Nb
        # FIXED: Collect actual values and divide by actual count
        neighbor_values = Float64[]
        for j in bus[i].N
            if haskey(θ_sparse, (j,i))
                push!(neighbor_values, θ_sparse[(j,i)])
            end
        end

        if !isempty(neighbor_values)
            θ̅[i] = sum(neighbor_values) / length(neighbor_values)
        end
    end

    return θ̅
end

function update_μ_sparse(bus, ρ, θ_sparse, θ̅, μ)
    Nb = length(bus)
    μ_new = copy(μ)

    for i in 1:Nb
        for j in bus[i].N
            μ_new[i,j] = μ[i,j] + ρ * (θ_sparse[(i,j)] - θ̅[j])
        end
    end

    return μ_new
end

function residual_sparse(bus, θ_sparse, θ̅)
    Nb = length(bus)
    Γ = sum(abs(θ̅[j] - θ_sparse[(i,j)]) for i in 1:Nb for j in bus[i].N)
    return Γ
end

# ══════════════════════════════════════════════════════════════════════════════
# RUN TEST
# ══════════════════════════════════════════════════════════════════════════════

# Load 14-bus network
println("[1/4] Loading network data...")
caseID = "testbeds/pglib_opf_case14_ieee.m"
(gen, bus, line, B, refbus) = load_data(caseID)
Nb = length(bus)
Ng = length(gen)
println("  ✓ Loaded: $Nb buses, $Ng generators")

# Centralized solution
println("\n[2/4] Solving centralized OPF (target)...")
(cost_c, dispatch_c, power_flow_c) = OPF_centralized(gen, bus, line, B, refbus)
println("  ✓ Centralized cost: \$", round(cost_c, digits=2))

# Initialize ADMM
println("\n[3/4] Initializing ADMM...")
ν̅ = 100  # Test with 100 iterations first
ρ = 10.0  # Fixed penalty parameter
γ = 1e-2  # Convergence tolerance

μ = zeros(Nb, Nb)
θ̅ = zeros(Nb)
residuals = zeros(ν̅)
cost_history = zeros(ν̅)

println("  ✓ Parameters: ρ=$ρ, max_iter=$ν̅, tolerance=$γ")

# Run ADMM
println("\n[4/4] Running ADMM convergence test...")
println("\n" * "─"^80)
@printf("%-5s %-15s %-15s %-15s\n", "Iter", "Cost(\$)", "Residual", "Δ Residual")
println("─"^80)

converged = false
final_iter = ν̅
θ_sparse = Dict{Tuple{Int,Int}, Float64}()

for ν in 2:ν̅
    global μ, θ̅, θ_sparse, converged, final_iter

    # Primal update
    θ_sparse, cost_history[ν], p_sol, l_sol = update_θ_sparse(gen, bus, line, B, refbus, μ, θ̅, ρ)

    # Consensus update (FIXED VERSION)
    θ̅ = update_θ̅_sparse(bus, θ_sparse)

    # Dual update
    μ = update_μ_sparse(bus, ρ, θ_sparse, θ̅, μ)

    # Residual
    residuals[ν] = residual_sparse(bus, θ_sparse, θ̅)

    # Print progress
    if ν == 2 || ν % 10 == 0 || residuals[ν] <= γ
        Δres = ν > 2 ? residuals[ν-1] - residuals[ν] : 0.0
        @printf("%-5d \$%-14.2f %-15.6f %-15.6f\n",
                ν, cost_history[ν], residuals[ν], Δres)
    end

    # Check convergence
    if residuals[ν] <= γ
        println("─"^80)
        println("✅ CONVERGED at iteration $ν")
        final_iter = ν
        converged = true
        break
    end
end

if !converged
    println("─"^80)
    println("⚠  Maximum iterations reached")
end

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════

println("\n" * "="^80)
println(" TEST RESULTS")
println("="^80 * "\n")

println("Convergence:")
println("  Status:     ", converged ? "✅ CONVERGED" : "❌ NOT CONVERGED")
println("  Iterations: $final_iter / $ν̅")
println("  Residual:   ", round(residuals[final_iter], digits=6))
println()

cost_diff = abs(cost_c - cost_history[final_iter])
cost_pct = (cost_diff / cost_c) * 100

println("Cost Comparison:")
println("  Centralized:  \$", round(cost_c, digits=2))
println("  ADMM:         \$", round(cost_history[final_iter], digits=2))
println("  Difference:   \$", round(cost_diff, digits=4), " (", round(cost_pct, digits=4), "%)")
println()

# Check if residuals are decreasing
println("Residual Trend Analysis:")
decreasing_count = 0
total_count = 0
for i in 3:final_iter
    if residuals[i] < residuals[i-1]
        decreasing_count += 1
    end
    total_count += 1
end

decrease_pct = (decreasing_count / total_count) * 100
println("  Decreasing iterations: $decreasing_count / $total_count (", round(decrease_pct, digits=1), "%)")

if decrease_pct > 80
    println("  ✅ Residuals mostly decreasing - good convergence behavior")
elseif decrease_pct > 50
    println("  ⚠️  Residuals sometimes increase - may need tuning")
else
    println("  ❌ Residuals frequently increase - poor convergence")
end

println("\n" * "="^80)
if converged && cost_pct < 0.1 && decrease_pct > 80
    println(" ✅ TEST PASSED: ADMM converges correctly!")
else
    println(" ❌ TEST FAILED: Issues detected")
    if !converged
        println("    - Did not converge within $ν̅ iterations")
    end
    if cost_pct >= 0.1
        println("    - Cost differs from centralized by ", round(cost_pct, digits=2), "%")
    end
    if decrease_pct <= 80
        println("    - Residuals not decreasing consistently")
    end
end
println("="^80 * "\n")
