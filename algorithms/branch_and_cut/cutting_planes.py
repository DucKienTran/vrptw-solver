import math
import random
from gurobipy import quicksum


def add_capacity_constraint(model, x_vars, x_hat, S, data):
    """
    Kiểm tra và thêm ràng buộc sức chứa nếu phát hiện vi phạm.
    """
    depot = data["depot"]
    customers = data["customers"]
    V = customers + [depot]

    demand = data.get("demand", data.get("q"))
    capacity = data.get("capacity", data.get("Q"))

    sum_q = sum(demand[i] for i in S)
    k_S = math.ceil(sum_q / capacity)


    V_minus_S = [j for j in V if j not in S]
    f_S = sum(x_hat.get((i, j), 0.0) for i in S for j in V_minus_S)

    if f_S < k_S - 1e-4:
        if "global_cuts" not in data:
            data["global_cuts"] = []
            data["global_cuts_raw"] = []

        key = (frozenset(S), k_S)
        seen_keys = {(fs, k) for fs, k in data["global_cuts"]}
        if key in seen_keys:
            return False

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

def add_static_2_cycle_cuts(model, x_vars, data):
    """
    Thêm các ràng buộc loại bỏ chu trình 2 đỉnh (2-cycle elimination): x_ij + x_ji <= 1
    Chạy O(n^2) một lần duy nhất vào lúc khởi tạo bài toán
    """
    if "static_2_cycle_pairs" not in data:
        customers = data["customers"]
        n = len(customers)
        valid_pairs = []

        for i in range(n):
            for j in range(i + 1, n):
                u = customers[i]
                v = customers[j]
                if (u, v) in x_vars and (v, u) in x_vars:
                    valid_pairs.append((u, v))

        data["static_2_cycle_pairs"] = valid_pairs

        for u, v in data["static_2_cycle_pairs"]:
            model.addConstr(
                x_vars[u, v] + x_vars[v, u] <= 1,
                name=f"static_2_cycle_{u}_{v}"
            )

        if data["static_2_cycle_pairs"]:
            model.update()

def replay_global_cuts(model, x_vars, data):
    """
    Tái áp dụng toàn bộ cuts trong global pool lên một model mới.
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

    """
    depot = data["depot"]
    customers = data["customers"]

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


    cuts_added = 0

    for _ in range(max_iter):
        # Khởi tạo lại supernodes cho mỗi iteration
        supernodes       = {v: {v} for v in customers}
        supernode_demand = {v: demand[v] for v in customers}

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
                S_new = Su | Sv
                for node in S_new:
                    supernodes[node]       = S_new
                    supernode_demand[node] = sum_q_new

                if add_capacity_constraint(model, x_vars, x_hat, S_new, data):
                    cuts_added += 1

    return cuts_added