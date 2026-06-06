from typing import Any, Dict
from gurobipy import GRB
from algorithms.branch_and_bound.node import BBNode
from models.vrptw_model import build_gurobi_vrptw_model
from utils.solution import get_solution_values
from algorithms.branch_and_cut.cutting_planes import graph_shrinking, replay_global_cuts, add_static_2_cycle_cuts

# Giới hạn vòng lặp cutting plane tại mỗi node
# để tránh lãng phí thời gian khi cuts yếu không cải thiện bound
def solve_lp_relaxation_with_cuts(
        data: Dict[str, Any],
        node: BBNode,
        time_limit: float,
):
    """
    Giải LP relaxation tại một node B&B, tích hợp cutting plane loop.

    Luồng:
    1. Build model LP,
    2. Replay toàn bộ global cut pool từ các node trước
    3. Cutting plane loop: Graph Shrinking → addConstr → optimize lại
       dừng khi không còn cut mới hoặc đạt _MAX_CUT_ROUNDS
    4. Trả về nghiệm cuối theo format B&B yêu cầu
    """

    # ── 1. Build model LP ───────────────────────────────────────────────────
    model, x, t, y = build_gurobi_vrptw_model(
        data=data,
        node=node,
        relax=True,
        name=f"BC_node_depth_{node.depth}",
        time_limit=time_limit,
        output_flag=0,
    )

    # ── 2. Replay global cut pool lên model mới ─────────────────────────────
    # Thêm n^2 cuts để loại bỏ chu trình con giữa 2 đỉnh nếu trong model đang chưa có
    add_static_2_cycle_cuts(model, x, data)
    # Giới hạn Pool chỉ giữ lại 500 mặt cắt mới nhất
    if "global_cut_pool" in data and isinstance(data["global_cut_pool"], list):
        data["global_cut_pool"] = data["global_cut_pool"][-500:]
    # gọi lại các cuts đã thêm từ model trước
    replay_global_cuts(model, x, data)

    model.optimize()

    # Kiểm tra tính khả thi ngay từ đầu
    if (
            model.Status in [GRB.INFEASIBLE, GRB.INF_OR_UNBD, GRB.UNBOUNDED]
            or model.SolCount == 0
    ):
        return {
            "status": model.Status,
            "feasible": False,
            "reason": "Infeasible at root eval",
            "node": node,
        }

    # ── 3. Cutting plane loop ────────────────────────────────────────────────
    prev_obj = float(model.ObjVal)

    _MAX_CUT_ROUNDS = 20 if node.depth == 0 else 1
    for cut_round in range(_MAX_CUT_ROUNDS):
        model.optimize()

        # Kiểm tra tính khả thi
        if (
                model.Status in [GRB.INFEASIBLE, GRB.INF_OR_UNBD, GRB.UNBOUNDED]
                or model.SolCount == 0
        ):
            return {
                "status": model.Status,
                "feasible": False,
                "reason": "Infeasible",
                "node": node,
            }

        x_sol, t_sol, y_sol = get_solution_values(x, t, y)
        current_obj = float(model.ObjVal)

        # Tìm và nạp cuts vi phạm
        new_cuts = graph_shrinking(model, x, x_sol, data)

        # Điều kiện thoát:
        # (a) Không còn cut mới → LP đã được thắt chặt tối đa
        # (b) Bound không tăng sau vòng này → cuts yếu, dừng sớm tránh lãng phí
        if new_cuts == 0:
            break

        if prev_obj is not None and current_obj - prev_obj < 1e-4:
            # Bound hầu như không tăng dù đã thêm cuts → dừng
            break

        prev_obj = current_obj
        model.update()

    # ── 4. Nghiệm cuối cùng ─────────────────────────────────────────────────
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