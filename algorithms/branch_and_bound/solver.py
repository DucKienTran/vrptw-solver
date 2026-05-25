import heapq
import itertools
import math
from typing import Any, Dict

from algorithms.branch_and_bound.branching import branch_node
from algorithms.branch_and_bound.lp_relaxation import solve_lp_relaxation_at_node
from algorithms.branch_and_bound.node import BBNode
from config import EPS, MAX_NODES, NODE_SELECTION, TIME_LIMIT_PER_LP, USE_INITIAL_HEURISTIC
from solvers.gurobi_direct import solve_direct_milp_for_check
from utils.solution import is_integral_x, validate_integral_solution


def manual_branch_and_bound_vrptw(
    data: Dict[str, Any],
    max_nodes: int = MAX_NODES,
    node_selection: str = NODE_SELECTION,
    time_limit_per_lp: float = TIME_LIMIT_PER_LP,
    use_initial_heuristic: bool = USE_INITIAL_HEURISTIC,
):
    """
    Giải VRPTW bằng manual Branch and Bound.

    node_selection:
        - "dfs": duyệt sâu bằng stack.
        - "best_bound": ưu tiên node có lower bound nhỏ nhất.
    """
    root = BBNode(
        depth=0,
        vehicle_lb=0,
        vehicle_ub=data["m"],
        note="root",
    )

    best_obj = math.inf
    best_solution = None

    stats = {
        "nodes_solved": 0,
        "nodes_popped": 0,
        "lp_infeasible": 0,
        "pruned_by_bound": 0,
        "integer_solutions": 0,
        "branch_count": 0,
        "max_depth": 0,
        "log": [],
    }

    counter = itertools.count()
    frontier = []

    def add_frontier(lp_result):
        if node_selection == "dfs":
            frontier.append(lp_result)
        elif node_selection == "best_bound":
            heapq.heappush(frontier, (lp_result["obj"], next(counter), lp_result))
        else:
            raise ValueError("node_selection phải là 'dfs' hoặc 'best_bound'.")

    def pop_frontier():
        if node_selection == "dfs":
            return frontier.pop()
        return heapq.heappop(frontier)[2]

    def frontier_size():
        return len(frontier)

    def evaluate_node(node):
        nonlocal best_obj, best_solution

        stats["nodes_solved"] += 1
        stats["max_depth"] = max(stats["max_depth"], node.depth)

        lp = solve_lp_relaxation_at_node(data, node, time_limit=time_limit_per_lp)

        if stats["nodes_solved"] <= 20 or stats["nodes_solved"] % 500 == 0:
            print(
                f"Solved node #{stats['nodes_solved']} | "
                f"depth={node.depth} | feasible={lp['feasible']} | "
                f"best={best_obj:.4f}",
                flush=True,
            )

        # Cắt nhánh vì LP vô nghiệm.
        if not lp["feasible"]:
            stats["lp_infeasible"] += 1
            return None

        bound = lp["obj"]

        # Cắt nhánh vì cận dưới không tốt hơn incumbent.
        if bound >= best_obj - EPS:
            stats["pruned_by_bound"] += 1
            return None

        # Nếu nghiệm LP đã nguyên, kiểm tra và cập nhật incumbent.
        if is_integral_x(lp["x"]):
            ok, routes, msg = validate_integral_solution(data, lp["x"], lp["t"], lp["y"])

            if ok and bound < best_obj - EPS:
                best_obj = bound
                best_solution = {
                    "obj": bound,
                    "x": lp["x"],
                    "t": lp["t"],
                    "y": lp["y"],
                    "routes": routes,
                    "depth": node.depth,
                    "source": "manual_bnb_integer_lp",
                }

                stats["integer_solutions"] += 1
                log_msg = f"New incumbent: obj={best_obj:.4f}, depth={node.depth}, routes={len(routes)}"
                stats["log"].append(log_msg)
                print(log_msg, flush=True)
            else:
                stats["log"].append(f"Integral LP but validation failed: {msg}")

            return None

        return lp

    if use_initial_heuristic:
        print("Đang chạy heuristic warm-start bằng Gurobi direct MILP trong 30s...")
        h = solve_direct_milp_for_check(data, time_limit=30)

        if h["has_solution"] and h["obj"] < best_obj - EPS:
            best_obj = h["obj"]
            best_solution = {
                "obj": best_obj,
                "x": h["x"],
                "t": h["t"],
                "y": h["y"],
                "routes": h["routes"],
                "depth": 0,
                "source": "heuristic_warmstart",
            }

            stats["integer_solutions"] += 1
            stats["log"].append(f"Heuristic incumbent: obj={best_obj:.4f}")
            print(f"Heuristic incumbent = {best_obj:.4f}")
        else:
            print("Heuristic không tìm được nghiệm, tiếp tục không có incumbent.")

    # Đánh giá root.
    lp_root = evaluate_node(root)

    if lp_root is not None:
        add_frontier(lp_root)

    while frontier_size() > 0 and stats["nodes_solved"] < max_nodes:
        current_lp = pop_frontier()
        stats["nodes_popped"] += 1

        node = current_lp["node"]
        bound = current_lp["obj"]

        if bound >= best_obj - EPS:
            stats["pruned_by_bound"] += 1
            continue

        children, branch_msg = branch_node(data, current_lp)
        stats["branch_count"] += 1

        if stats["branch_count"] <= 20 or stats["branch_count"] % 500 == 0:
            log_msg = (
                f"Branch #{stats['branch_count']}: depth={node.depth}, "
                f"bound={bound:.4f}, best={best_obj:.4f}, {branch_msg}, "
                f"frontier={frontier_size()}, solved={stats['nodes_solved']}"
            )
            stats["log"].append(log_msg)
            print(log_msg, flush=True)

        for child in children:
            if child.vehicle_ub is not None and child.vehicle_lb > child.vehicle_ub:
                continue

            if any(lb > ub + EPS for lb, ub in child.time_bounds.values()):
                continue

            if stats["nodes_solved"] >= max_nodes:
                break

            lp_child = evaluate_node(child)

            if lp_child is not None:
                add_frontier(lp_child)

    stopped_by_limit = stats["nodes_solved"] >= max_nodes and frontier_size() > 0
    optimal_proved = not stopped_by_limit

    return {
        "best_obj": best_obj,
        "best_solution": best_solution,
        "optimal_proved": optimal_proved,
        "stopped_by_node_limit": stopped_by_limit,
        "remaining_nodes": frontier_size(),
        "stats": stats,
    }
