import math
import random
from gurobipy import quicksum


def add_capacity_constraint(model, x_vars, x_hat, S, data):
    """
    Kiểm tra và thêm ràng buộc sức chứa nếu phát hiện vi phạm.

    Cut pool lưu dạng: (frozenset(S), k_S) để dedup,
    nhưng cũng lưu thêm (S_list, k_S) để tái áp dụng lên model mới.
    """
    depot = data["depot"]
    customers = data["customers"]
    V = customers + [depot]

    demand = data.get("demand", data.get("q"))
    capacity = data.get("capacity", data.get("Q"))

    sum_q = sum(demand[i] for i in S)
    k_S = math.ceil(sum_q / capacity)

    # if k_S <= 1:
    #     # Không đáng thêm cut nếu chỉ cần 1 xe
    #     return False

    V_minus_S = [j for j in V if j not in S]
    f_S = sum(x_hat.get((i, j), 0.0) for i in S for j in V_minus_S)

    if f_S < k_S - 1e-4:
        # ── Khởi tạo cut pool nếu chưa có ──────────────────────────────────
        if "global_cuts" not in data:
            data["global_cuts"] = []          # list of (frozenset, k_S)
            data["global_cuts_raw"] = []      # list of (S_list, k_S) để replay

        key = (frozenset(S), k_S)
        seen_keys = {(fs, k) for fs, k in data["global_cuts"]}
        if key in seen_keys:
            return False

        # ── Thêm vào model hiện tại ─────────────────────────────────────────
        S_list = list(S)
        cut_expr = quicksum(
            x_vars[i, j]
            for i in S_list
            for j in V_minus_S
            if (i, j) in x_vars
        )
        model.addConstr(
            cut_expr >= k_S,
            name=f"cap_cut_{len(S)}_{random.randint(0, 99999)}"
        )

        # ── Lưu vào cut pool ────────────────────────────────────────────────
        data["global_cuts"].append((frozenset(S), k_S))
        data["global_cuts_raw"].append((S_list, k_S))
        return True

    return False


def replay_global_cuts(model, x_vars, data):
    """
    Tái áp dụng toàn bộ cuts trong global pool lên một model mới.
    Gọi ngay sau khi build model, trước vòng lặp cutting plane.
    """
    if "global_cuts_raw" not in data:
        return 0

    depot = data["depot"]
    customers = data["customers"]
    V = customers + [depot]
    replayed = 0

    for S_list, k_S in data["global_cuts_raw"]:
        S_set = set(S_list)
        V_minus_S = [j for j in V if j not in S_set]
        cut_expr = quicksum(
            x_vars[i, j]
            for i in S_list
            for j in V_minus_S
            if (i, j) in x_vars
        )
        model.addConstr(
            cut_expr >= k_S,
            name=f"replay_cap_{len(S_list)}_{random.randint(0, 99999)}"
        )
        replayed += 1

    if replayed:
        model.update()

    return replayed


def graph_shrinking(model, x_vars, x_hat, data, max_iter=10, mu=5):
    """
    Heuristic Graph Shrinking tìm các tập vi phạm sức chứa.

    Mỗi iteration khởi tạo lại supernodes + danh sách cung L độc lập
    (đúng theo pseudocode báo cáo), đảm bảo tính ngẫu nhiên thực sự
    thay vì dùng lại L đã bị pop.
    """
    depot = data["depot"]
    customers = data["customers"]

    # Chỉ xét cung giữa khách hàng (bỏ depot)
    A0 = [
        (i, j)
        for (i, j) in x_vars.keys()
        if i != depot and j != depot and x_hat.get((i, j), 0.0) > 1e-4
    ]

    if not A0:
        return 0

    demand  = data.get("demand", data.get("q"))
    capacity = data.get("capacity", data.get("Q"))
    depot   = data["depot"]
    V       = customers + [depot]

    # Cache demand tổng theo supernode để tránh tính lại mỗi lần
    # supernode_demand[id(S)] = sum of demand trong S
    cuts_added = 0

    for _ in range(max_iter):
        # ── Khởi tạo lại supernodes cho mỗi iteration ──────────────────────
        supernodes       = {v: {v} for v in customers}
        supernode_demand = {v: demand[v] for v in customers}   # demand theo node đại diện

        # Tạo bản sao L mới mỗi iteration, sort giảm dần theo x_hat
        L = sorted(A0, key=lambda arc: x_hat.get(arc, 0.0), reverse=True)

        while L:
            limit = min(mu, len(L))
            chosen_idx = random.randint(0, limit - 1)
            u, v = L.pop(chosen_idx)

            Su = supernodes[u]
            Sv = supernodes[v]

            if Su is not Sv:
                sum_q_new = supernode_demand[u] + supernode_demand[v]

                if sum_q_new <= capacity:
                    S_new = Su | Sv
                    for node in S_new:
                        supernodes[node]       = S_new
                        supernode_demand[node] = sum_q_new
                    if add_capacity_constraint(model, x_vars, x_hat, S_new, data):
                        cuts_added += 1

                else:
                    continue
    return cuts_added