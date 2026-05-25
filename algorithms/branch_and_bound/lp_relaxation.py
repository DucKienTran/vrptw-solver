from typing import Any, Dict

try:
    from gurobipy import GRB
except Exception as exc:
    raise ImportError("Chưa import được gurobipy. Hãy kiểm tra cài đặt Gurobi.") from exc

from algorithms.branch_and_bound.node import BBNode
from config import TIME_LIMIT_PER_LP
from models.vrptw_model import build_gurobi_vrptw_model
from utils.solution import get_solution_values


def solve_lp_relaxation_at_node(
    data: Dict[str, Any],
    node: BBNode,
    time_limit: float = TIME_LIMIT_PER_LP,
):
    """Giải LP relaxation tại một node của cây Branch and Bound."""
    model, x, t, y = build_gurobi_vrptw_model(
        data=data,
        node=node,
        relax=True,
        name=f"LP_node_depth_{node.depth}",
        time_limit=time_limit,
        output_flag=0,
    )

    model.optimize()

    if model.Status in [GRB.INFEASIBLE, GRB.INF_OR_UNBD, GRB.UNBOUNDED]:
        return {
            "status": model.Status,
            "feasible": False,
            "reason": "LP infeasible/unbounded",
            "node": node,
        }

    if model.SolCount == 0:
        return {
            "status": model.Status,
            "feasible": False,
            "reason": "No LP solution found",
            "node": node,
        }

    x_sol, t_sol, y_sol = get_solution_values(x, t, y)

    return {
        "status": model.Status,
        "feasible": True,
        "obj": float(model.ObjVal),
        "x": x_sol,
        "t": t_sol,
        "y": y_sol,
        "node": node,
    }
