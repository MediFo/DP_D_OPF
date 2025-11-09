"""
SPARSE version of residual computation
Based on: scripts/fun_residual_update.jl (original DP_D_OPF)

Differences:
1. Works with sparse Dict{Tuple{Int,Int}, Float64}
2. Same mathematical formula as original: Γ = Σ |θ̅[j] - θ[i,j]|
"""

function residual_sparse(bus, θ_sparse::Dict{Tuple{Int,Int}, Float64}, θ̅)
    """
    SPARSE residual computation

    Computes consensus constraint violation:
    Γ = Σ_{i∈buses} Σ_{j∈N(i)} |θ̅[j] - θ[i,j]|

    Args:
        bus: Network bus data
        θ_sparse: Sparse primal variables θ[(i,j)]
        θ̅: Consensus variables

    Returns:
        Γ: Total residual (convergence metric)
    """
    Nb = length(bus)

    # Original DP_D_OPF formula (line 7 in fun_residual_update.jl):
    # Γ = sum(norm(θ̅[j]-θ[i,j]) for i in 1:Nb for j in bus[i].N)
    #
    # Note: norm() for scalars is just abs()
    Γ = sum(abs(θ̅[j] - θ_sparse[(i,j)]) for i in 1:Nb for j in bus[i].N)

    return Γ
end
