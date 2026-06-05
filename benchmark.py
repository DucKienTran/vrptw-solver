import time
import math
import tkinter as tk
from tkinter import ttk, messagebox

from config import (
    MAX_NODES,
    NODE_SELECTION,
    TIME_LIMIT_PER_LP,
    USE_INITIAL_HEURISTIC,
)
from algorithms.branch_and_bound.solver import manual_branch_and_bound_vrptw
from algorithms.branch_and_cut.solver import manual_branch_and_cut_vrptw
from algorithms.branch_and_price.solver import manual_branch_and_price_vrptw
from utils.data_builder import build_vrptw_data
from utils.io import read_solomon_instance

DEFAULT_SOLVER_KWARGS = {
    "node_selection": NODE_SELECTION,
    "time_limit_per_lp": TIME_LIMIT_PER_LP,
    "use_initial_heuristic": USE_INITIAL_HEURISTIC,
}


class BenchmarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Đối Sánh Thuật Toán VRPTW (Academic UI)")
        self.root.geometry("1050x600")
        self.root.configure(bg="#f4f6f9")

        title_label = tk.Label(
            root,
            text="VRPTW BENCHMARK PLATFORM",
            font=("Helvetica", 16, "bold"),
            fg="#2c3e50",
            bg="#f4f6f9",
        )
        title_label.pack(pady=15)

        control_frame = tk.Frame(root, bg="#f4f6f9")
        control_frame.pack(pady=10)

        # ── Hàng 0: File path + Customers ────────────────────────────────────────
        tk.Label(control_frame, text="File path:", font=("Helvetica", 10), bg="#f4f6f9").grid(row=0, column=0, padx=5, pady=4, sticky="e")
        self.file_entry = tk.Entry(control_frame, font=("Helvetica", 10), width=14)
        self.file_entry.insert(0, "data/r101.txt")
        self.file_entry.grid(row=0, column=1, padx=5, pady=4)

        tk.Label(control_frame, text="Số khách hàng (instance):", font=("Helvetica", 10), bg="#f4f6f9").grid(row=0, column=2, padx=5, pady=4, sticky="e")
        self.cust_entry = tk.Entry(control_frame, font=("Helvetica", 10), width=8)
        self.cust_entry.insert(0, "10")
        self.cust_entry.grid(row=0, column=3, padx=5, pady=4)

        # ── Hàng 1: Max nodes + Button ────────────────────────────────────────
        tk.Label(control_frame, text="Giới hạn node (max_nodes):", font=("Helvetica", 10), bg="#f4f6f9").grid(row=1, column=0, padx=5, pady=4, sticky="e")
        self.max_nodes_entry = tk.Entry(control_frame, font=("Helvetica", 10), width=14)
        self.max_nodes_entry.insert(0, str(MAX_NODES))
        self.max_nodes_entry.grid(row=1, column=1, padx=5, pady=4)

        tk.Label(
            control_frame,
            text="(số node B&B/B&C được phép duyệt tối đa)",
            font=("Helvetica", 9, "italic"),
            fg="#7f8c8d",
            bg="#f4f6f9",
        ).grid(row=1, column=2, columnspan=2, padx=5, sticky="w")

        self.run_btn = tk.Button(
            control_frame,
            text="KÍCH HOẠT BENCHMARK",
            font=("Helvetica", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            command=self.start_benchmark,
            padx=10,
        )
        self.run_btn.grid(row=0, column=4, rowspan=2, padx=15, pady=4)

        self.status_label = tk.Label(
            root,
            text="Trạng thái: Sẵn sàng thử nghiệm.",
            font=("Helvetica", 10, "italic"),
            fg="#7f8c8d",
            bg="#f4f6f9",
        )
        self.status_label.pack(pady=5)

        table_frame = tk.Frame(root)
        table_frame.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Metric", "BB", "BC", "BP"),
            show="headings",
            height=14,
        )
        self.tree.heading("Metric", text="METRICS")
        self.tree.heading("BB", text="BRANCH & BOUND")
        self.tree.heading("BC", text="BRANCH & CUT")
        self.tree.heading("BP", text="BRANCH & PRICE")

        self.tree.column("Metric", width=280, anchor="w")
        self.tree.column("BB",     width=180, anchor="center")
        self.tree.column("BC",     width=180, anchor="center")
        self.tree.column("BP",     width=180, anchor="center")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), foreground="#2c3e50")
        style.configure("Treeview", font=("Helvetica", 10), rowheight=28)

    def start_benchmark(self):
        file_path = self.file_entry.get().strip()

        try:
            num_cust = int(self.cust_entry.get().strip())
        except ValueError:
            messagebox.showerror("Lỗi dữ liệu", "Vui lòng nhập số lượng khách hàng hợp lệ!")
            return

        try:
            max_nodes = int(self.max_nodes_entry.get().strip())
            if max_nodes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi dữ liệu", "Giới hạn node phải là số nguyên dương!")
            return

        solver_kwargs = {**DEFAULT_SOLVER_KWARGS, "max_nodes": max_nodes}

        # ── Load data dùng đúng pipeline như main.py ──────────────────────────
        self.status_label.config(text="[HỆ THỐNG] Đang nạp dữ liệu từ file...", fg="#e67e22")
        self.root.update()

        try:
            vehicle_number, capacity, df = read_solomon_instance(file_path, num_cust)
            data = build_vrptw_data(df, vehicle_number, capacity)
        except Exception as e:
            messagebox.showerror("Lỗi đọc file", str(e))
            self.status_label.config(text="Trạng thái: Thất bại.", fg="#c0392b")
            return

        import builtins
        builtins.GLOBAL_TIME_LIMIT = 3600.0

        # ── Branch and Bound ───────────────────────────────────────────────────
        self.status_label.config(text="⚡ Đang tính toán: 1. Pure Branch and Bound...", fg="#9b59b6")
        self.root.update()

        builtins.GLOBAL_START_TIME = time.time()
        t0 = time.time()
        res_bb = manual_branch_and_bound_vrptw(data=data, **solver_kwargs)
        time_bb = time.time() - t0

        # ── Branch and Cut ─────────────────────────────────────────────────────
        self.status_label.config(text="⚡ Đang tính toán: 2. Advanced Branch and Cut...", fg="#3498db")
        self.root.update()

        builtins.GLOBAL_START_TIME = time.time()
        t1 = time.time()
        res_bc = manual_branch_and_cut_vrptw(data=data, **solver_kwargs)
        time_bc = time.time() - t1

        # ── Branch and Price ───────────────────────────────────────────────────
        self.status_label.config(text="⚡ Đang tính toán: 3. Branch and Price...", fg="#e67e22")
        self.root.update()

        builtins.GLOBAL_START_TIME = time.time()
        t2 = time.time()
        res_bp = manual_branch_and_price_vrptw(data=data)
        time_bp = time.time() - t2

        self.status_label.config(text="🎉 Đã xử lý xong dữ liệu đối sánh!", fg="#27ae60")
        self._print_benchmark_console(
            file_path, num_cust, max_nodes, vehicle_number, capacity, data,
            res_bb, time_bb, res_bc, time_bc, res_bp, time_bp,
        )
        self.display_results(res_bb, time_bb, res_bc, time_bc, res_bp, time_bp)

    # ── Helper: tính metrics từ result dict ──────────────────────────────────
    @staticmethod
    def _compute_metrics(res, elapsed):
        """
        Chuẩn hoá và tính thêm các metrics từ result dict của bất kỳ solver nào.
        Trả về dict với tất cả metrics cần hiển thị.
        """
        s      = res.get("stats", {})
        obj    = res.get("best_obj", math.inf)
        nodes  = s.get("nodes_solved", 0)
        pruned = s.get("pruned_by_bound", 0)

        # ── Metrics cơ bản ────────────────────────────────────────────────────
        obj_str     = f"{obj:.4f}" if obj != math.inf else "No Sol"
        time_str    = f"{elapsed:.4f}"
        nodes_str   = str(nodes)
        branch_str  = str(s.get("branch_count", "N/A"))
        pruned_str  = str(pruned)
        infeas_str  = str(s.get("lp_infeasible", "N/A"))
        int_sol_str = str(s.get("integer_solutions", "N/A"))
        optimal_str = str(res.get("optimal_proved", "N/A"))

        # ── Pruning rate: pruned / nodes (%) ─────────────────────────────────
        # Ý nghĩa: B&C có pruning rate cao hơn B&B nếu cuts thắt chặt bound tốt
        if isinstance(nodes, int) and nodes > 0 and isinstance(pruned, int):
            pruning_rate_str = f"{pruned / nodes * 100:.1f}%"
        else:
            pruning_rate_str = "N/A"

        # ── Time per node (ms) ────────────────────────────────────────────────
        # Ý nghĩa: B&C chậm hơn/node do overhead cutting plane loop
        # B&P chậm hơn/node do Column Generation (SPPRC) tại mỗi node
        if isinstance(nodes, int) and nodes > 0:
            time_per_node_str = f"{elapsed / nodes * 1000:.2f} ms"
        else:
            time_per_node_str = "N/A"

        # ── Optimality gap: (UB - LB) / UB * 100 (%) ────────────────────────
        lb = res.get("global_lower_bound", None)
        ub = obj
        if lb is not None and ub not in (math.inf, 0) and isinstance(lb, (int, float)):
            gap = abs(ub - lb) / abs(ub) * 100
            opt_gap_str = f"{gap:.2f}%"
        else:
            opt_gap_str = "N/A"

        return {
            "obj"              : obj_str,
            "time"             : time_str,
            "nodes"            : nodes_str,
            "branches"         : branch_str,
            "pruned"           : pruned_str,
            "pruning_rate"     : pruning_rate_str,
            "infeasible"       : infeas_str,
            "time_per_node"    : time_per_node_str,
            "integer_solutions": int_sol_str,
            "opt_gap"          : opt_gap_str,
            "optimal"          : optimal_str,
        }

    # ── In kết quả ra console ─────────────────────────────────────────────────
    def _print_benchmark_console(
            self, file_path, num_cust, max_nodes, vehicle_number, capacity, data,
            r_bb, t_bb, r_bc, t_bc, r_bp, t_bp,
    ):
        m_bb = self._compute_metrics(r_bb, t_bb)
        m_bc = self._compute_metrics(r_bc, t_bc)
        m_bp = self._compute_metrics(r_bp, t_bp)

        print("\n" + "=" * 62)
        print("========== BENCHMARK INSTANCE ==========")
        print(f"Data path      = {file_path}")
        print(f"Max customers  = {num_cust}")
        print(f"Max nodes      = {max_nodes}")
        print(f"Vehicle number = {vehicle_number}")
        print(f"Capacity       = {capacity}")
        print(f"Nodes          = {len(data['nodes'])}")
        print(f"Customers      = {len(data['customers'])}")

        # In chi tiết từng thuật toán
        for label, res, t, m in [
            ("BRANCH AND BOUND",  r_bb, t_bb, m_bb),
            ("BRANCH AND CUT",    r_bc, t_bc, m_bc),
            ("BRANCH AND PRICE",  r_bp, t_bp, m_bp),
        ]:
            print(f"\n========== {label} RESULT ==========")
            print(f"best_obj       = {res['best_obj']}")
            print(f"has_solution   = {res['best_solution'] is not None}")
            print(f"optimal_proved = {res['optimal_proved']}")
            print(f"time           = {t:.4f}s")
            print("Stats:")
            for k, v in res["stats"].items():
                if k != "log":
                    print(f"  {k}: {v}")
            if res["best_solution"] is not None:
                routes = (
                    res["best_solution"]["routes"]
                    if isinstance(res["best_solution"], dict)
                    else [r.get_path() for r in res["best_solution"]]
                )
                print("Routes:")
                for idx, route in enumerate(routes, 1):
                    print(f"  Route {idx}: " + " -> ".join(map(str, route)))

        # Bảng so sánh tổng hợp
        W = 18
        print(f"\n========== COMPARISON SUMMARY ==========")
        print(f"{'Metric':<35} {'B&B':>{W}} {'B&C':>{W}} {'B&P':>{W}}")
        print("-" * (35 + W * 3 + 2))

        rows = [
            ("Min cost",                    m_bb["obj"],               m_bc["obj"],               m_bp["obj"]),
            ("Time (s)",                    m_bb["time"],              m_bc["time"],              m_bp["time"]),
            ("Time / node (ms)",            m_bb["time_per_node"],     m_bc["time_per_node"],     m_bp["time_per_node"]),
            ("Nodes solved",                m_bb["nodes"],             m_bc["nodes"],             m_bp["nodes"]),
            ("Branches",                    m_bb["branches"],          m_bc["branches"],          m_bp["branches"]),
            ("Pruned nodes",                m_bb["pruned"],            m_bc["pruned"],            m_bp["pruned"]),
            ("Pruning rate (%)",            m_bb["pruning_rate"],      m_bc["pruning_rate"],      m_bp["pruning_rate"]),
            ("Infeasible nodes",            m_bb["infeasible"],        m_bc["infeasible"],        m_bp["infeasible"]),
            ("Integer solutions found",     m_bb["integer_solutions"], m_bc["integer_solutions"], m_bp["integer_solutions"]),
            ("Optimality gap (%)",          m_bb["opt_gap"],           m_bc["opt_gap"],           m_bp["opt_gap"]),
            ("Optimal proved",              m_bb["optimal"],           m_bc["optimal"],           m_bp["optimal"]),
        ]
        for row_label, v_bb, v_bc, v_bp in rows:
            print(f"{row_label:<35} {v_bb:>{W}} {v_bc:>{W}} {v_bp:>{W}}")
        print("=" * (35 + W * 3 + 2))

    # ── Cập nhật bảng GUI ─────────────────────────────────────────────────────
    def display_results(self, r_bb, t_bb, r_bc, t_bc, r_bp, t_bp):
        for item in self.tree.get_children():
            self.tree.delete(item)

        m_bb = self._compute_metrics(r_bb, t_bb)
        m_bc = self._compute_metrics(r_bc, t_bc)
        m_bp = self._compute_metrics(r_bp, t_bp)

        # ── Section headers + data rows ───────────────────────────────────────
        # Format: (label, bb_val, bc_val, bp_val, is_header)
        sections = [
            # Header
            ("── KẾT QUẢ ──", "", "", "", True),
            ("Min cost (objective)",        m_bb["obj"],               m_bc["obj"],               m_bp["obj"],               False),
            ("Optimal proved",              m_bb["optimal"],           m_bc["optimal"],           m_bp["optimal"],           False),
            ("Optimality gap (%)",          m_bb["opt_gap"],           m_bc["opt_gap"],           m_bp["opt_gap"],           False),

            ("── THỜI GIAN ──", "", "", "", True),
            ("Total time (s)",              m_bb["time"],              m_bc["time"],              m_bp["time"],              False),
            ("Time / node (ms)",            m_bb["time_per_node"],     m_bc["time_per_node"],     m_bp["time_per_node"],     False),

            ("── CÂY TÌM KIẾM ──", "", "", "", True),
            ("Nodes solved",                m_bb["nodes"],             m_bc["nodes"],             m_bp["nodes"],             False),
            ("Branches",                    m_bb["branches"],          m_bc["branches"],          m_bp["branches"],          False),
            ("Pruned nodes",                m_bb["pruned"],            m_bc["pruned"],            m_bp["pruned"],            False),
            ("Pruning rate (%)",            m_bb["pruning_rate"],      m_bc["pruning_rate"],      m_bp["pruning_rate"],      False),

            ("── CHI TIẾT NODE ──", "", "", "", True),
            ("Infeasible nodes",            m_bb["infeasible"],        m_bc["infeasible"],        m_bp["infeasible"],        False),
            ("Integer solutions found",     m_bb["integer_solutions"], m_bc["integer_solutions"], m_bp["integer_solutions"], False),
        ]

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10), rowheight=26)

        for idx, row in enumerate(sections):
            label, v_bb, v_bc, v_bp, is_header = row
            if is_header:
                tag = "header"
            else:
                tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, values=(label, v_bb, v_bc, v_bp), tags=(tag,))

        self.tree.tag_configure("header", background="#2c3e50", foreground="white",
                                font=("Helvetica", 9, "bold"))
        self.tree.tag_configure("even",   background="#ffffff")
        self.tree.tag_configure("odd",    background="#f0f4f8")


if __name__ == "__main__":
    main_window = tk.Tk()
    app = BenchmarkApp(main_window)
    main_window.mainloop()