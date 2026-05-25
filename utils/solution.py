from typing import Any, Dict, List, Tuple

import pandas as pd

from config import EPS


def get_solution_values(x, t, y):
    """Lấy nghiệm từ biến Gurobi."""
    x_sol = {key: var.X for key, var in x.items()}
    t_sol = {key: var.X for key, var in t.items()}
    y_sol = {key: var.X for key, var in y.items()}
    return x_sol, t_sol, y_sol


def is_binary_value(v: float, eps: float = EPS) -> bool:
    return abs(v) <= eps or abs(v - 1.0) <= eps


def is_integral_x(x_sol: Dict[Tuple[int, int], float], eps: float = EPS) -> bool:
    return all(is_binary_value(v, eps) for v in x_sol.values())


def selected_arcs_from_x(x_sol: Dict[Tuple[int, int], float], eps: float = EPS):
    return [(i, j) for (i, j), val in x_sol.items() if val >= 1.0 - eps]


def extract_routes_from_x(data: Dict[str, Any], x_sol: Dict[Tuple[int, int], float], eps: float = EPS):
    """
    Truy vết tuyến từ nghiệm nguyên x_ij.
    """
    depot = data["depot"]
    customers = set(data["customers"])
    arcs = selected_arcs_from_x(x_sol, eps)

    next_map = {}
    for i, j in arcs:
        next_map[i] = j

    starts = [j for (i, j) in arcs if i == depot and j != depot]
    routes = []
    visited_customers = set()

    for start in starts:
        route = [depot]
        current = start
        safety = 0

        while True:
            route.append(current)

            if current == depot:
                break

            if current in visited_customers:
                route.append("LOOP")
                break

            visited_customers.add(current)

            if current not in next_map:
                route.append("DEAD_END")
                break

            current = next_map[current]
            safety += 1

            if safety > len(customers) + 2:
                route.append("LOOP")
                break

        routes.append(route)

    missing = sorted(customers - visited_customers)
    return routes, missing


def route_load(data: Dict[str, Any], route: List[int]) -> float:
    """Tính tổng demand trên một route."""
    q = data["q"]
    total = 0.0

    for node in route:
        if isinstance(node, int) and node != data["depot"]:
            total += q[node]

    return total


def route_distance(data: Dict[str, Any], route: List[int]) -> float:
    """Tính tổng quãng đường trên một route."""
    c = data["c"]
    total = 0.0
    clean_route = [node for node in route if isinstance(node, int)]

    for i, j in zip(clean_route[:-1], clean_route[1:]):
        total += c[i, j]

    return total


def validate_integral_solution(data: Dict[str, Any], x_sol, t_sol=None, y_sol=None, eps: float = EPS):
    """
    Kiểm tra nghiệm nguyên có tạo được các tuyến đầy đủ và khả thi cơ bản không.
    """
    customers = data["customers"]
    nodes = data["nodes"]
    depot = data["depot"]
    Q = data["Q"]

    for i in customers:
        out_sum = sum(1 for j in nodes if j != i and x_sol.get((i, j), 0.0) >= 1 - eps)
        in_sum = sum(1 for j in nodes if j != i and x_sol.get((j, i), 0.0) >= 1 - eps)

        if out_sum != 1 or in_sum != 1:
            return False, [], f"Customer {i} has out={out_sum}, in={in_sum}"

    routes, missing = extract_routes_from_x(data, x_sol, eps)

    if missing:
        return False, routes, f"Missing customers not connected from depot: {missing}"

    for route in routes:
        if not route or route[0] != depot or route[-1] != depot:
            return False, routes, f"Route does not start/end at depot: {route}"

        if route_load(data, route) > Q + eps:
            return False, routes, f"Capacity violation route {route}"

    return True, routes, "OK"


def summarize_routes(data: Dict[str, Any], routes: List[List[int]]) -> pd.DataFrame:
    """Tạo bảng tóm tắt các route."""
    rows = []

    for idx, route in enumerate(routes, start=1):
        clean_route = [node for node in route if isinstance(node, int)]
        customers_in_route = [node for node in clean_route if node != data["depot"]]

        rows.append({
            "route_id": idx,
            "route": " -> ".join(map(str, clean_route)),
            "num_customers": len(customers_in_route),
            "load": route_load(data, clean_route),
            "distance": route_distance(data, clean_route),
        })

    return pd.DataFrame(rows)
