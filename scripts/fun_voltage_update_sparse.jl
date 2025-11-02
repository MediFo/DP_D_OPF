"""
SPARSE version of voltage/theta update (primal ADMM step)
Based on: scripts/fun_voltage_update.jl (original DP_D_OPF)

Differences:
1. Creates SPARSE variables θ[(i,j)] only for j ∈ N(i) (neighbor-only)
2. Dense version creates θ[1:Nb, 1:Nb] = Nb² variables
3. Sparse version creates only Σ|N(i)| ≈ 2*Nl variables (70-90% reduction!)
4. Returns Dict instead of dense matrix
5. Same optimization problem, same constraints, same objective
"""

using JuMP
using Ipopt

function update_θ_sparse(gen, bus, line, B, refbus, μ, θ̅, ρ)
    """
    SPARSE voltage angle update (primal ADMM step)

    Solves local OPF with ADMM augmented Lagrangian:
    min  Cost(p,l) - μ'θ + (ρ/2)||θ - θ̅||²
    s.t. Power flow constraints
         Generator limits
         Load flexibility limits

    Args:
        gen, bus, line, B: Network data
        refbus: Reference bus index
        μ: Dual variables (Nb×Nb matrix)
        θ̅: Consensus variables (Nb vector)
        ρ: Penalty parameter

    Returns:
        θ_sol: Sparse Dict{Tuple{Int,Int}, Float64}
        cost: Objective value
        p_sol: Generator dispatch
        l_sol: Load flexibility
    """
    Ng = length(gen)
    Nb = length(bus)

    # Create model with Ipopt solver
    model = Model(optimizer_with_attributes(Ipopt.Optimizer,
                                           "print_level" => 0,
                                           "sb" => "yes"))

    # Standard variables (same as original)
    @variable(model, p[1:Ng])
    @variable(model, l[1:Nb])

    # SPARSE θ variables: Only create θ[(i,j)] for j ∈ N(i)
    # Original creates: @variable(model, θ[1:Nb, 1:Nb])
    # Sparse creates: θ_dict[(i,j)] for j ∈ neighbors(i)
    θ = Dict{Tuple{Int,Int}, VariableRef}()
    for i in 1:Nb
        for j in bus[i].N
            θ[(i,j)] = @variable(model, base_name="θ[$i,$j]")
        end
    end

    # Generator limits (same as original line 20-21)
    @constraint(model, ϕ̲[i=1:Nb, g=bus[i].G], gen[g].p̲ <= p[g])
    @constraint(model, ϕ̅[i=1:Nb, g=bus[i].G], p[g] <= gen[g].p̅)

    # Load flexibility limits (same as original line 22-23)
    @constraint(model, ψ̲[i=1:Nb], -bus[i].d <= l[i])
    @constraint(model, ψ̅[i=1:Nb], l[i] <= bus[i].d)

    # Power flow limits (adapted for sparse θ, original line 24-25)
    @constraint(model, η̲[i=1:Nb, l_idx=bus[i].Λ],
                -line[l_idx].f̅ <= line[l_idx].β * (θ[(i, line[l_idx].b_f)] - θ[(i, line[l_idx].b_t)]))
    @constraint(model, η̅[i=1:Nb, l_idx=bus[i].Λ],
                line[l_idx].β * (θ[(i, line[l_idx].b_f)] - θ[(i, line[l_idx].b_t)]) <= line[l_idx].f̅)

    # Power balance (adapted for sparse θ, original line 26)
    # Only sum over actual neighbors j ∈ N(i)
    @constraint(model, λ[i=1:Nb],
                sum(B[i, j] * θ[(i,j)] for j in bus[i].N) ==
                sum(p[g] for g in bus[i].G) - bus[i].d + l[i])

    # Reference bus (adapted for sparse θ, original line 27)
    # Original: @constraint(model, κ[i=1:Nb], θ[i,refbus] == 0)
    # Sparse: Only constrain buses that have refbus as neighbor
    @constraint(model, κ[i=1:Nb; refbus in bus[i].N], θ[(i, refbus)] == 0)

    # Generator buses have no load flexibility (same as original line 28-30)
    for i in 1:Nb
        if bus[i].type == 1
            @constraint(model, l[i] == 0)
        end
    end

    # Objective: ADMM augmented Lagrangian (adapted for sparse θ, original line 31)
    # Cost(p,l) - μ'θ + (ρ/2)||θ - θ̅||²
    @objective(model, Min,
               # Generation cost + load flexibility cost
               sum(gen[g].c2 * p[g]^2 + gen[g].c1 * p[g] + gen[g].c0 for g in 1:Ng) +
               sum(bus[i].c * l[i]^2 for i in 1:Nb) -
               # Dual term: -Σ μ[i,j]*θ[i,j] (only over neighbors)
               sum(μ[i,j] * θ[(i,j)] for i in 1:Nb for j in bus[i].N) +
               # Penalty term: (ρ/2)*Σ(θ̅[j] - θ[i,j])² (only over neighbors)
               ρ / 2 * sum((θ̅[j] - θ[(i,j)])^2 for i in 1:Nb for j in bus[i].N))

    # Solve optimization problem (same as original line 32)
    optimize!(model)

    # Extract sparse solution (adapted from original line 34)
    θ_sol = Dict{Tuple{Int,Int}, Float64}()
    for i in 1:Nb
        for j in bus[i].N
            θ_sol[(i,j)] = JuMP.value(θ[(i,j)])
        end
    end

    p_sol = JuMP.value.(p)
    l_sol = JuMP.value.(l)

    # Compute objective value (same as original line 33)
    cost = sum(gen[g].c2 * p_sol[g]^2 + gen[g].c1 * p_sol[g] + gen[g].c0 for g in 1:Ng) +
           sum(bus[i].c * l_sol[i]^2 for i in 1:Nb)

    return θ_sol, cost, p_sol, l_sol
end
