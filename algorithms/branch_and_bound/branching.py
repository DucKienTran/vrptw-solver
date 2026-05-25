import math
from typing import Any, Dict, Tuple

from algorithms.branch_and_bound.node import clone_node
from config import EPS


def fractional_part(v: float) -> float:
    return abs(v - round(v))


def is_integer_like(v: float, eps: float = EPS) -> bool:
    return abs(v - round(v)) <= eps


def choose_fractional_arc(x_sol: Dict[Tuple[int, int], float], eps: float = EPS):
    """
    Chọn biến x_uv phân số gần 0.5 nhất để rẽ nhánh.
    """
    candidates = []

    for (i, j), val in x_sol.items():
        if eps < val < 1.0 - eps:
            candidates.append((abs(val - 0.5), i, j, val))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    _, i, j, val = candidates[0]

    return i, j, val


def branch_node(data: Dict[str, Any], lp_result: Dict[str, Any]):
    """
    Rẽ nhánh tại node hiện tại.

    Ưu tiên:
    1. Rẽ nhánh theo số xe nếu tổng số xe đang là phân số.
    2. Rẽ nhánh theo biến cung x_ij phân số.
    """
    node = lp_result["node"]
    x_sol = lp_result["x"]
    depot = data["depot"]
    customers = data["customers"]
    m = data["m"]

    # Chiến lược 1: branch theo số lượng xe.
    vehicle_value = sum(x_sol[depot, j] for j in customers)

    if not is_integer_like(vehicle_value):
        low = math.floor(vehicle_value)
        high = math.ceil(vehicle_value)

        child_le = clone_node(node, note=f"vehicle <= {low}")
        child_le.vehicle_ub = low if child_le.vehicle_ub is None else min(child_le.vehicle_ub, low)

        child_ge = clone_node(node, note=f"vehicle >= {high}")
        child_ge.vehicle_lb = max(child_ge.vehicle_lb, high)

        if child_ge.vehicle_ub is None:
            child_ge.vehicle_ub = m

        return [child_le, child_ge], f"Branch vehicle count l={vehicle_value:.6f}"

    # Chiến lược 2: branch theo biến luồng x_uv.
    arc_choice = choose_fractional_arc(x_sol)

    if arc_choice is None:
        return [], "No fractional arc found"

    u, v, val = arc_choice

    child_zero = clone_node(node, note=f"x_{u}_{v}=0")
    child_zero.fixed_arcs[u, v] = 0

    child_one = clone_node(node, note=f"x_{u}_{v}=1")
    child_one.fixed_arcs[u, v] = 1

    return [child_zero, child_one], f"Branch arc x[{u},{v}]={val:.6f}"
