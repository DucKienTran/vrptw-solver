"""
benchmark_v2.py
---------------
Chạy benchmark 3 thuật toán VRPTW trên cùng 1 instance:
  1. Branch and Bound  (B&B)
  2. Branch and Cut    (B&C)
  3. Branch and Price  (B&P)

Yêu cầu: đặt file này cùng cấp với thư mục algorithms/, utils/, models/, data/
"""

import copy
import math
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict

import numpy as np

# ── B&B và B&C ────────────────────────────────────────────────────────────────
from algorithms.branch_and_bound.solver import manual_branch_and_bound_vrptw
from algorithms.branch_and_cut.solver import manual_branch_and_cut_vrptw
from utils.io import read_solomon_instance
from utils.data_builder import build_vrptw_data

# ── B&P (code của bạn, đặt trong algorithms/branch_and_price/) ───────────────
from algorithms.branch_and_price.paramsVRP import ParamsVRP
from algorithms.branch_and_price.route import Route
from algorithms.branch_and_price.branchBound import BranchAndBound

def build_params_vrp_from_data(data: Dict[str, Any]):

    customers = data["customers"]
    depot = data["depot"]

    n = len(customers)

    # depot_start + customers + depot_end
    nb = n + 2

    node2idx = {depot: 0}

    for k, cust in enumerate(customers, start=1):
        node2idx[cust] = k

    depot_end_idx = nb - 1

    p = ParamsVRP(
        nbclients=nb,
        capacity=data["Q"],
        mvehic=data["m"]
    )

    p.datasetName = "from_data_dict"

    p.verybig = 1e10
    p.gap = 1e-6

    # Allocate arrays
    p.citieslab = list(range(nb))

    p.posx = np.zeros(nb)
    p.posy = np.zeros(nb)

    p.d = np.zeros(nb)

    p.a = np.zeros(nb, dtype=int)
    p.b = np.zeros(nb, dtype=int)

    p.s = np.zeros(nb, dtype=int)

    p.dist_base = np.zeros((nb, nb))
    p.dist = np.zeros((nb, nb))

    p.ttime = np.zeros((nb, nb))
    p.cost = np.zeros((nb, nb))

    p.edges = np.zeros((nb, nb))
    p.wval = np.zeros(nb)

    # Read coordinates
    df = data["df"]

    coord_map = {
        int(r["cust_no"]): (
            float(r["x"]),
            float(r["y"])
        )
        for _, r in df.iterrows()
    }

    all_nodes = [depot] + customers

    for orig in all_nodes:

        idx = node2idx[orig]

        p.posx[idx] = coord_map[orig][0]
        p.posy[idx] = coord_map[orig][1]

        p.d[idx] = data["q"].get(orig, 0.0)

        p.a[idx] = int(data["a"].get(orig, 0))
        p.b[idx] = int(data["b"].get(orig, 0))

        p.s[idx] = int(
            data.get("service", {}).get(orig, 0)
        )

    # Copy depot -> depot_end
    p.posx[depot_end_idx] = p.posx[0]
    p.posy[depot_end_idx] = p.posy[0]

    p.d[depot_end_idx] = 0.0

    p.a[depot_end_idx] = p.a[0]
    p.b[depot_end_idx] = p.b[0]

    p.s[depot_end_idx] = 0

    # Build dist matrix
    # EXACTLY like original code
    p.maxlength = 0.0

    for i in range(nb):
        max_dist = 0.0
        for j in range(nb):
            dx = p.posx[i] - p.posx[j]
            dy = p.posy[i] - p.posy[j]

            dist_val = round(
                10 * math.sqrt(dx * dx + dy * dy)
            ) / 10.0

            p.dist_base[i, j] = dist_val

            if dist_val > max_dist:
                max_dist = dist_val

        p.maxlength += max_dist

    # Same forbidden arcs
    for i in range(nb):

        # cannot go INTO start depot
        p.dist_base[i, 0] = p.verybig

        # cannot leave end depot
        p.dist_base[depot_end_idx, i] = p.verybig

        # no self-loop
        p.dist_base[i, i] = p.verybig

    # dist
    p.dist = p.dist_base.copy()

    # ttime
    for i in range(nb):
        for j in range(nb):

            p.ttime[i, j] = (
                p.dist_base[i, j] / p.speed
            )

    # IMPORTANT:
    # cost matrix EXACTLY
    # like original code
    p.cost = np.zeros((nb, nb))

    for j in range(nb):

        p.cost[0][j] = p.dist[0][j]

        p.cost[j][depot_end_idx] = (
            p.dist[j][depot_end_idx]
        )

    # wval
    for i in range(1, nb):
        p.wval[i] = 0.0

    return p, node2idx, depot_end_idx

def run_branch_and_price(data: Dict[str, Any]):
    """
    Chạy B&P và trả về dict kết quả chuẩn hoá giống B&B / B&C.
    """
    p, node2idx, depot_end_idx = build_params_vrp_from_data(data)

    # Khởi tạo routes ban đầu: mỗi khách hàng đi 1 tuyến riêng
    init_routes = []
    for k in range(1, p.nbclients - 1):
        cost = p.dist_base[0][k] + p.dist_base[k][depot_end_idx]
        if cost < p.verybig - 1e-6:
            r = Route(path=[0, k, depot_end_idx], cost=cost, Q=1.0)
            init_routes.append(r)

    bp        = BranchAndBound()
    best_routes = []

    bp.bb_node(p, init_routes, None, best_routes, 0)

    # Tính chi phí nghiệm
    opt_cost = sum(
        sum(p.dist_base[path[i]][path[i+1]]
            for i in range(len(path)-1)
            if p.dist_base[path[i]][path[i+1]] < p.verybig - 1e-6)
        for r in best_routes
        for path in [r.get_path()]
    ) if best_routes else math.inf

    # Tạo stats tương đương để hiển thị chung
    
    stats = {
        "nodes_solved"   : bp.nodes_solved,
        "branch_count"   : bp.branch_count,
        "pruned_by_bound": bp.pruned_by_bound,
        "lp_infeasible"  : "N/A",   # B&P không track riêng chỉ số này
    }

    return {
        "best_obj"            : opt_cost,
        "best_solution"       : best_routes if best_routes else None,
        "optimal_proved"      : opt_cost < math.inf,
        "stopped_by_node_limit": False,
        "stats"               : stats,
    }


#  LOAD DATA dùng chung cho B&B và B&C  (dùng utils chuẩn của codebase 1)

def load_data(file_name: str, num_customers: int) -> Dict[str, Any]:
    """
    Đọc file Solomon và build data dict chuẩn cho B&B / B&C.
    file_name: tên file không cần .txt, ví dụ 'r101'
    """
    base_dir  = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "data", file_name)
    if not file_path.endswith(".txt"):
        file_path += ".txt"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    vehicle_number, capacity, df = read_solomon_instance(file_path, max_customers=num_customers)
    data = build_vrptw_data(df, vehicle_number, capacity)
    return data


#  TKINTER UI

SHARED_PARAMS = dict(
    max_nodes           = 2000,
    node_selection      = "best_bound",
    time_limit_per_lp   = 15.0,
    use_initial_heuristic = False,
)


class BenchmarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VRPTW Benchmark — B&B vs B&C vs B&P")
        self.root.geometry("960x560")
        self.root.configure(bg="#f4f6f9")

        # Tiêu đề
        tk.Label(
            root, text="VRPTW BENCHMARK PLATFORM",
            font=("Helvetica", 16, "bold"), fg="#2c3e50", bg="#f4f6f9"
        ).pack(pady=14)

        # Thanh điều khiển
        ctrl = tk.Frame(root, bg="#f4f6f9")
        ctrl.pack(pady=8)

        tk.Label(ctrl, text="File Solomon:", font=("Helvetica", 10), bg="#f4f6f9").grid(row=0, column=0, padx=5)
        self.file_entry = tk.Entry(ctrl, font=("Helvetica", 10), width=10)
        self.file_entry.insert(0, "r101")
        self.file_entry.grid(row=0, column=1, padx=5)

        tk.Label(ctrl, text="Số khách hàng:", font=("Helvetica", 10), bg="#f4f6f9").grid(row=0, column=2, padx=5)
        self.cust_entry = tk.Entry(ctrl, font=("Helvetica", 10), width=6)
        self.cust_entry.insert(0, "10")
        self.cust_entry.grid(row=0, column=3, padx=5)

        tk.Button(
            ctrl, text="▶  CHẠY BENCHMARK",
            font=("Helvetica", 10, "bold"), bg="#2ecc71", fg="white",
            command=self.start_benchmark, padx=12
        ).grid(row=0, column=4, padx=18)

        # Trạng thái
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        tk.Label(root, textvariable=self.status_var,
                 font=("Helvetica", 10, "italic"), fg="#7f8c8d", bg="#f4f6f9").pack(pady=4)

        # Bảng kết quả
        frm = tk.Frame(root)
        frm.pack(pady=12, padx=20, fill=tk.BOTH, expand=True)

        cols = ("Metric", "BB", "BC", "BP")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=9)
        headers = {
            "Metric": ("Chỉ số",               220, "w"),
            "BB":     ("Branch & Bound",        190, "center"),
            "BC":     ("Branch & Cut",          190, "center"),
            "BP":     ("Branch & Price",        190, "center"),
        }
        for col, (hdr, w, anchor) in headers.items():
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w, anchor=anchor)

        sb = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), foreground="#2c3e50")
        style.configure("Treeview",         font=("Helvetica", 10), rowheight=28)

    # Chạy benchmark

    def set_status(self, msg, color="#e67e22"):
        self.status_var.set(msg)
        self.root.update()

    def start_benchmark(self):
        file_name = self.file_entry.get().strip()
        try:
            num_cust = int(self.cust_entry.get().strip())
        except ValueError:
            messagebox.showerror("Lỗi", "Số khách hàng phải là số nguyên.")
            return

        # Load data
        self.set_status("Đang đọc dữ liệu Solomon...")
        try:
            data = load_data(file_name, num_cust)
        except Exception as e:
            messagebox.showerror("Lỗi đọc file", str(e))
            self.set_status("Thất bại.", "#c0392b")
            return

        # B&B 
        self.set_status("⚡ Đang chạy Branch & Bound...", "#9b59b6")
        t0 = time.time()
        res_bb = manual_branch_and_bound_vrptw(data, **SHARED_PARAMS)
        time_bb = time.time() - t0

        # B&C
        self.set_status("⚡ Đang chạy Branch & Cut...", "#2980b9")
        # B&C modify data["global_cuts"], dùng bản sao để không ảnh hưởng B&P
        data_bc = copy.deepcopy(data)
        t1 = time.time()
        res_bc = manual_branch_and_cut_vrptw(data_bc, **SHARED_PARAMS)
        time_bc = time.time() - t1

        # B&P
        self.set_status("⚡ Đang chạy Branch & Price...", "#e67e22")
        t2 = time.time()
        try:
            res_bp = run_branch_and_price(data)
        except Exception as e:
            res_bp = {
                "best_obj": math.inf,
                "optimal_proved": False,
                "stats": {"nodes_solved": "ERR", "branch_count": "ERR",
                          "pruned_by_bound": "ERR", "lp_infeasible": "ERR"},
            }
            messagebox.showwarning("B&P lỗi", str(e))
        time_bp = time.time() - t2

        self.set_status("✅ Hoàn thành benchmark!", "#27ae60")
        self.display_results(res_bb, time_bb, res_bc, time_bc, res_bp, time_bp)

    # Hiển thị kết quả

    def _fmt_obj(self, res):
        v = res.get("best_obj", math.inf)
        return f"{v:.4f}" if v != math.inf else "No Sol"

    def _fmt_stat(self, res, key):
        v = res.get("stats", {}).get(key, "N/A")
        return str(v)

    def display_results(self, r_bb, t_bb, r_bc, t_bc, r_bp, t_bp):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = [
            ("Chi phí tốt nhất (obj)",
             self._fmt_obj(r_bb), self._fmt_obj(r_bc), self._fmt_obj(r_bp)),

            ("Thời gian chạy (s)",
             f"{t_bb:.4f}", f"{t_bc:.4f}", f"{t_bp:.4f}"),

            ("Nodes đã giải",
             self._fmt_stat(r_bb, "nodes_solved"),
             self._fmt_stat(r_bc, "nodes_solved"),
             self._fmt_stat(r_bp, "nodes_solved")),

            ("Số lần rẽ nhánh",
             self._fmt_stat(r_bb, "branch_count"),
             self._fmt_stat(r_bc, "branch_count"),
             self._fmt_stat(r_bp, "branch_count")),

            ("Nodes bị cắt (bound)",
             self._fmt_stat(r_bb, "pruned_by_bound"),
             self._fmt_stat(r_bc, "pruned_by_bound"),
             self._fmt_stat(r_bp, "pruned_by_bound")),

            ("LP vô nghiệm",
             self._fmt_stat(r_bb, "lp_infeasible"),
             self._fmt_stat(r_bc, "lp_infeasible"),
             self._fmt_stat(r_bp, "lp_infeasible")),

            ("Tối ưu chứng minh được",
             str(r_bb.get("optimal_proved")),
             str(r_bc.get("optimal_proved")),
             str(r_bp.get("optimal_proved"))),
        ]

        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, values=row, tags=(tag,))

        self.tree.tag_configure("even", background="#ffffff")
        self.tree.tag_configure("odd",  background="#f2f5f9")


if __name__ == "__main__":
    root = tk.Tk()
    BenchmarkApp(root)
    root.mainloop()
