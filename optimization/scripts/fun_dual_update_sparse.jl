"""
SPARSE version of dual update
Based on: scripts/fun_dual_update.jl (original DP_D_OPF)

Differences:
1. Works with sparse Dict{Tuple{Int,Int}, Float64}
2. Dense μ matrix for simplicity (only neighbors are non-zero anyway)
3. Same mathematical formula as original: μ[i,j] = μ[i,j] + ρ*(θ[i,j] - θ̅[j])
"""

function update_μ_sparse(bus, ρ, θ_sparse::Dict{Tuple{Int,Int}, Float64}, θ̅, μ)
    """
    SPARSE dual variable update

    Boyd's ADMM dual update:
    μ[i,j] = μ[i,j] + ρ * (θ[i,j] - θ̅[j])

    Args:
        bus: Network bus data
        ρ: Penalty parameter
        θ_sparse: Sparse primal variables θ[(i,j)]
        θ̅: Consensus variables
        μ: Previous dual variables (dense Nb×Nb matrix)

    Returns:
        μ_new: Updated dual variables (dense Nb×Nb matrix)
    """
    Nb = length(bus)
    μ_new = copy(μ)

    for i in 1:Nb
        for j in bus[i].N
            # Original DP_D_OPF formula (line 10 in fun_dual_update.jl):
            # mu[i,j] = μ[i,j] + ρ * (θ[i,j] - θ̅[j])
            μ_new[i,j] = μ[i,j] + ρ * (θ_sparse[(i,j)] - θ̅[j])
        end
    end

    return μ_new
end
