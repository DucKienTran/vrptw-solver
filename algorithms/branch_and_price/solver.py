import math
import copy
import numpy as np
from typing import Any, Dict

from algorithms.branch_and_price.branchBound import BranchAndBound
from algorithms.branch_and_price.paramsVRP import ParamsVRP
from algorithms.branch_and_price.route import Route


def _build_params_from_data(data: Dict[str, Any]) -> tuple:
    """
    Convert data dict (từ build_vrptw_data) sang ParamsVRP mà B&P dùng.

    ParamsVRP dùng index 0..N-1 trong đó:
      - 0          : depot xuất phát
      - 1..n       : khách hàng (n = len(customers))
      - N-1 = n+1  : depot kết thúc (nhân đôi depot, cùng tọa độ)

    Trả về (p, node2idx, depot_end_idx):
      - p            : ParamsVRP đã khởi tạo đầy đủ
      - node2idx     : dict {node_id_gốc: idx_trong_ParamsVRP}
      - depot_end_idx: index của depot cuối trong ParamsVRP
    """
    customers  = data["customers"]
    depot      = data["depot"]
    n          = len(customers)
    N          = n + 2          # depot_start(0) + n khách hàng + depot_end(N-1)

    # ── Map node id gốc → index ParamsVRP ────────────────────────────────────
    # depot gốc  → 0
    # customer i → 1..n (theo thứ tự trong data["customers"])
    # depot cuối → N-1
    node2idx = {depot: 0}
    for rank, cid in enumerate(customers, start=1):
        node2idx[cid] = rank
    depot_end_idx = N - 1

    # ── Khởi tạo ParamsVRP ────────────────────────────────────────────────────
    p = ParamsVRP(
        nbclients=N,
        capacity=data["Q"],
        mvehic=data["m"],
        speed=1.0,
    )
    p.verybig   = 1e10
    p.gap       = 1e-6

    # Arrays kích thước N
    p.citieslab = list(range(N))
    p.posx      = np.zeros(N)
    p.posy      = np.zeros(N)
    p.d         = np.zeros(N)
    p.a         = np.zeros(N, dtype=int)
    p.b         = np.zeros(N, dtype=int)
    p.s         = np.zeros(N, dtype=int)

    # Depot xuất phát (idx=0)
    p.posx[0] = data["xcoord"][depot]
    p.posy[0] = data["ycoord"][depot]
    p.d[0]    = 0.0
    p.a[0]    = int(data["a"][depot])
    p.b[0]    = int(data["b"][depot])
    p.s[0]    = 0

    # Khách hàng (idx=1..n)
    for cid in customers:
        idx       = node2idx[cid]
        p.posx[idx] = data["xcoord"][cid]
        p.posy[idx] = data["ycoord"][cid]
        p.d[idx]    = data["q"][cid]
        p.a[idx]    = int(data["a"][cid])
        p.b[idx]    = int(data["b"][cid])
        p.s[idx]    = int(data["service"][cid])

    # Depot kết thúc (idx=N-1): cùng thông tin với depot xuất phát
    p.posx[depot_end_idx] = data["xcoord"][depot]
    p.posy[depot_end_idx] = data["ycoord"][depot]
    p.d[depot_end_idx]    = 0.0
    p.a[depot_end_idx]    = int(data["a"][depot])
    p.b[depot_end_idx]    = int(data["b"][depot])
    p.s[depot_end_idx]    = 0

    # ── Ma trận khoảng cách ───────────────────────────────────────────────────
    p.dist_base = np.full((N, N), p.verybig)
    p.ttime     = np.full((N, N), p.verybig)
    p.cost      = np.zeros((N, N))
    p.edges     = np.zeros((N, N))
    p.wval      = np.zeros(N)
    p.maxlength = 0.0

    # Điền khoảng cách giữa mọi cặp node (dùng tọa độ Euclidean)
    for i in range(N):
        max_dist = 0.0
        for j in range(N):
            if i == j:
                continue
            dx   = p.posx[i] - p.posx[j]
            dy   = p.posy[i] - p.posy[j]
            dist = round(10 * math.sqrt(dx*dx + dy*dy)) / 10.0
            p.dist_base[i, j] = dist
            p.ttime[i, j]     = dist / p.speed
            if dist < p.verybig - 1e-6 and dist > max_dist:
                max_dist = dist
        p.maxlength += max_dist

    # Cấm các cung không hợp lệ theo quy ước B&P:
    # - Cấm quay về depot xuất phát (cột 0)
    # - Cấm rời depot kết thúc (hàng N-1)
    # - Cấm tự vòng
    for i in range(N):
        p.dist_base[i, 0]           = p.verybig   # cấm về depot_start
        p.dist_base[depot_end_idx, i] = p.verybig  # cấm rời depot_end
        p.dist_base[i, i]           = p.verybig   # cấm tự vòng

    p.dist = copy.deepcopy(p.dist_base)

    # cost[i][j] = dist[i][j] ban đầu (sẽ được cập nhật bởi dual trong CG)
    for i in range(N):
        for j in range(N):
            p.cost[i, j] = p.dist[i, j]

    return p, node2idx, depot_end_idx


def _convert_routes_to_original(best_routes, node2idx, depot_end_idx, data):
    """
    Convert routes từ index ParamsVRP về node id gốc.
    Thay depot_end_idx → depot gốc (0 trong data).
    Trả về list of list, ví dụ: [[0, 3, 7, 0], [0, 1, 0]]
    """
    idx2node = {v: k for k, v in node2idx.items()}
    idx2node[depot_end_idx] = data["depot"]

    result = []
    for route in best_routes:
        path = route.get_path()
        converted = [idx2node.get(p, p) for p in path]
        result.append(converted)
    return result


def manual_branch_and_price_vrptw(data: Dict[str, Any], **kwargs) -> Dict[str, Any]:

    print("=== Khởi động hệ thống BRANCH AND PRICE ===")

    # ── 1. Convert data → ParamsVRP ───────────────────────────────────────────
    p, node2idx, depot_end_idx = _build_params_from_data(data)

    # ── 2. Khởi tạo routes ban đầu: mỗi khách hàng 1 tuyến riêng ─────────────
    init_routes = []
    for k in range(1, p.nbclients - 1):
        cost = p.dist_base[0][k] + p.dist_base[k][depot_end_idx]
        if cost < p.verybig - 1e-6:
            r = Route(path=[0, k, depot_end_idx], cost=cost, Q=1.0)
            init_routes.append(r)

    # ── 3. Chạy B&P ───────────────────────────────────────────────────────────
    bp          = BranchAndBound()
    best_routes = []

    bp.bb_node(p, init_routes, None, best_routes, depth=0)

    # ── 4. Tính chi phí nghiệm (dùng dist_base để tránh ảnh hưởng branching) ──
    opt_cost = math.inf
    if best_routes:
        opt_cost = sum(
            sum(
                p.dist_base[path[i]][path[i + 1]]
                for i in range(len(path) - 1)
                if p.dist_base[path[i]][path[i + 1]] < p.verybig - 1e-6
            )
            for route in best_routes
            for path in [route.get_path()]
        )

    # ── 5. Convert routes về node id gốc ─────────────────────────────────────
    if best_routes:
        converted_routes = _convert_routes_to_original(
            best_routes, node2idx, depot_end_idx, data
        )
        best_solution = {"routes": converted_routes}
    else:
        best_solution = None

    # ── 6. Đóng gói stats ─────────────────────────────────────────────────────
    stats = {
        "nodes_solved"    : bp.nodes_solved,
        "nodes_popped"    : bp.nodes_solved,
        "branch_count"    : bp.branch_count,
        "pruned_by_bound" : bp.pruned_by_bound,
        "lp_infeasible"   : "N/A",
        "integer_solutions": "N/A",
        "max_depth"       : "N/A",
        "log"             : [],
    }

    # ── 7. KIỂM TRA GIỚI HẠN THỜI GIAN VÀ CẬP NHẬT TRẠNG THÁI TỐI ƯU ──────────
    import builtins
    import time

    # Kiểm tra xem có bị dừng do hết thời gian (timeout) không
    stopped_by_limit = False
    if time.time() - getattr(builtins, "GLOBAL_START_TIME", time.time()) >= getattr(builtins, "GLOBAL_TIME_LIMIT", 3600):
        stopped_by_limit = True

    # Chỉ được công nhận là TỐI ƯU nếu: Có nghiệm (< math.inf) VÀ Không bị ngắt do hết giờ
    optimal_proved = (opt_cost < math.inf) and (not stopped_by_limit)

    # Đảm bảo trả về global_lower_bound để file main.py tính được Optimality Gap
    global_lb = bp.lowerbound if bp.lowerbound > -1e9 else None

    return {
        "best_obj"             : opt_cost,
        "best_solution"        : best_solution,
        "optimal_proved"       : optimal_proved,
        "stopped_by_node_limit": stopped_by_limit,
        "global_lower_bound"   : global_lb,
        "remaining_nodes"      : 0,
        "stats"                : stats,
    }