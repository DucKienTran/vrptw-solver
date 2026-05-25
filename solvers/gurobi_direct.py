import math
from typing import Any, Dict

from algorithms.branch_and_bound.node import BBNode
from models.vrptw_model import build_gurobi_vrptw_model
from utils.solution import get_solution_values, validate_integral_solution


def solve_direct_milp_for_check(data: Dict[str, Any], time_limit: float = 5000):
    """
    Giải trực tiếp mô hình MILP VRPTW bằng Gurobi.

    Hàm này dùng để:
    - Kiểm tra nghiệm so với manual Branch and Bound.
    - Tạo nghiệm tham khảo.
    - Có thể dùng làm baseline.
    """
    model, x, t, y = build_gurobi_vrptw_model(
        data=data,
        node=BBNode(depth=0, vehicle_lb=0, vehicle_ub=data["m"], note="direct_milp"),
        relax=False,
        name="VRPTW_Direct_MILP_Check",
        time_limit=time_limit,
        output_flag=1,
    )

    model.optimize()

    if model.SolCount == 0:
        return {
            "status": model.Status,
            "has_solution": False,
            "obj": math.inf,
            "routes": [],
            "model": model,
        }

    x_sol, t_sol, y_sol = get_solution_values(x, t, y)
    ok, routes, msg = validate_integral_solution(data, x_sol, t_sol, y_sol)

    return {
        "status": model.Status,
        "has_solution": True,
        "obj": float(model.ObjVal),
        "mip_gap": getattr(model, "MIPGap", None),
        "x": x_sol,
        "t": t_sol,
        "y": y_sol,
        "routes": routes,
        "valid": ok,
        "message": msg,
        "model": model,
    }
