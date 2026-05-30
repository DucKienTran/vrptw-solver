import time
import math
import tkinter as tk
from tkinter import ttk, messagebox
import copy

from config import (
    MAX_NODES,
    NODE_SELECTION,
    TIME_LIMIT_PER_LP,
    USE_INITIAL_HEURISTIC,
)
from algorithms.branch_and_bound.solver import manual_branch_and_bound_vrptw
from algorithms.branch_and_cut.solver import manual_branch_and_cut_vrptw
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
        self.root.geometry("800x550")
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

        tk.Label(control_frame, text="File path:", font=("Helvetica", 10), bg="#f4f6f9").grid(row=0, column=0, padx=5, pady=4, sticky="e")
        self.file_entry = tk.Entry(control_frame, font=("Helvetica", 10), width=14)
        self.file_entry.insert(0, "data/r101.txt")
        self.file_entry.grid(row=0, column=1, padx=5, pady=4)

        tk.Label(control_frame, text="Số khách hàng (instance):", font=("Helvetica", 10), bg="#f4f6f9").grid(row=0, column=2, padx=5, pady=4, sticky="e")
        self.cust_entry = tk.Entry(control_frame, font=("Helvetica", 10), width=8)
        self.cust_entry.insert(0, "10")
        self.cust_entry.grid(row=0, column=3, padx=5, pady=4)

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
            columns=("Metric", "BB", "BC"),
            show="headings",
            height=8,
        )
        self.tree.heading("Metric", text="METRICS")
        self.tree.heading("BB", text="BRANCH AND BOUND (B&B)")
        self.tree.heading("BC", text="BRANCH AND CUT (B&C)")

        self.tree.column("Metric", width=320, anchor="w")
        self.tree.column("BB", width=200, anchor="center")
        self.tree.column("BC", width=200, anchor="center")
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

        self.status_label.config(text="[HỆ THỐNG] Đang nạp dữ liệu từ file...", fg="#e67e22")
        self.root.update()

        try:
            vehicle_number, capacity, df = read_solomon_instance(file_path, num_cust)
            data = build_vrptw_data(df, vehicle_number, capacity)
        except Exception as e:
            messagebox.showerror("Lỗi đọc file", str(e))
            self.status_label.config(text="Trạng thái: Thất bại.", fg="#c0392b")
            return

        # Khởi tạo bản sao dữ liệu cô lập cho từng thuật toán
        data_for_bb = copy.deepcopy(data)
        data_for_bc = copy.deepcopy(data)

        # ── Branch and Bound ───────────────────────────────────────────────────
        self.status_label.config(text="⚡ Đang tính toán: 1. Pure Branch and Bound...", fg="#9b59b6")
        self.root.update()

        t0 = time.time()
        res_bb = manual_branch_and_bound_vrptw(data=data_for_bb, **solver_kwargs)
        time_bb = time.time() - t0

        # ── Branch and Cut ─────────────────────────────────────────────────────
        self.status_label.config(text="⚡ Đang tính toán: 2. Advanced Branch and Cut...", fg="#3498db")
        self.root.update()

        t1 = time.time()
        res_bc = manual_branch_and_cut_vrptw(data=data_for_bc, **solver_kwargs)
        time_bc = time.time() - t1

        self.status_label.config(text="🎉 Đã xử lý xong dữ liệu đối sánh!", fg="#27ae60")
        self._print_benchmark_console(file_path, num_cust, max_nodes, vehicle_number, capacity, data, res_bb, time_bb, res_bc, time_bc)
        self.display_results(res_bb, time_bb, res_bc, time_bc)

    def _print_benchmark_console(self, file_path, num_cust, max_nodes, vehicle_number, capacity, data, r_bb, t_bb, r_bc, t_bc):
        print("\n" + "=" * 50)
        print("========== BENCHMARK INSTANCE ==========")
        print(f"Data path      = {file_path}")
        print(f"Max customers  = {num_cust}")
        print(f"Max nodes      = {max_nodes}")
        print(f"Vehicle number = {vehicle_number}")
        print(f"Capacity       = {capacity}")
        print(f"Nodes          = {len(data['nodes'])}")
        print(f"Customers      = {len(data['customers'])}")

        print("\n========== BRANCH AND BOUND RESULT ==========")
        print(f"best_obj           = {r_bb['best_obj']}")
        print(f"has_solution       = {r_bb['best_solution'] is not None}")
        print(f"optimal_proved     = {r_bb['optimal_proved']}")
        print(f"stopped_node_limit = {r_bb['stopped_by_node_limit']}")
        print(f"remaining_nodes    = {r_bb['remaining_nodes']}")
        print(f"time               = {t_bb:.4f}s")
        print("Stats:")
        for k, v in r_bb["stats"].items():
            if k != "log":
                print(f"  {k}: {v}")
        if r_bb["best_solution"] is not None:
            print("Routes:")
            for idx, route in enumerate(r_bb["best_solution"]["routes"], 1):
                print(f"  Route {idx}: " + " -> ".join(map(str, route)))

        print("\n========== BRANCH AND CUT RESULT ==========")
        print(f"best_obj           = {r_bc['best_obj']}")
        print(f"has_solution       = {r_bc['best_solution'] is not None}")
        print(f"optimal_proved     = {r_bc['optimal_proved']}")
        print(f"stopped_node_limit = {r_bc['stopped_by_node_limit']}")
        print(f"remaining_nodes    = {r_bc['remaining_nodes']}")
        print(f"time               = {t_bc:.4f}s")
        print("Stats:")
        for k, v in r_bc["stats"].items():
            if k != "log":
                print(f"  {k}: {v}")
        if r_bc["best_solution"] is not None:
            print("Routes:")
            for idx, route in enumerate(r_bc["best_solution"]["routes"], 1):
                print(f"  Route {idx}: " + " -> ".join(map(str, route)))

        print("\n========== COMPARISON SUMMARY ==========")
        print(f"{'Metric':<30} {'B&B':>15} {'B&C':>15}")
        print("-" * 62)
        bb_obj = f"{r_bb['best_obj']:.4f}" if r_bb['best_obj'] != math.inf else "No Sol"
        bc_obj = f"{r_bc['best_obj']:.4f}" if r_bc['best_obj'] != math.inf else "No Sol"
        rows = [
            ("Min cost",         bb_obj,                                     bc_obj),
            ("Time (s)",         f"{t_bb:.4f}",                              f"{t_bc:.4f}"),
            ("Nodes solved",     str(r_bb["stats"]["nodes_solved"]),         str(r_bc["stats"]["nodes_solved"])),
            ("Branches",         str(r_bb["stats"]["branch_count"]),         str(r_bc["stats"]["branch_count"])),
            ("Pruned nodes",     str(r_bb["stats"]["pruned_by_bound"]),      str(r_bc["stats"]["pruned_by_bound"])),
            ("Infeasible nodes", str(r_bb["stats"]["lp_infeasible"]),        str(r_bc["stats"]["lp_infeasible"])),
            ("Optimal proved",   str(r_bb["optimal_proved"]),                str(r_bc["optimal_proved"])),
        ]
        for label, v_bb, v_bc in rows:
            print(f"{label:<30} {v_bb:>15} {v_bc:>15}")
        print("=" * 62)

    def display_results(self, r_bb, t_bb, r_bc, t_bc):
        for item in self.tree.get_children():
            self.tree.delete(item)

        bb_obj = f"{r_bb['best_obj']:.4f}" if r_bb['best_obj'] != math.inf else "No Sol"
        bc_obj = f"{r_bc['best_obj']:.4f}" if r_bc['best_obj'] != math.inf else "No Sol"

        metrics_list = [
            ("Min cost",         bb_obj,                                     bc_obj),
            ("Time (s)",         f"{t_bb:.4f}",                              f"{t_bc:.4f}"),
            ("Nodes solved",     str(r_bb["stats"]["nodes_solved"]),         str(r_bc["stats"]["nodes_solved"])),
            ("Branches",         str(r_bb["stats"]["branch_count"]),         str(r_bc["stats"]["branch_count"])),
            ("Pruned nodes",     str(r_bb["stats"]["pruned_by_bound"]),      str(r_bc["stats"]["pruned_by_bound"])),
            ("Infeasible nodes", str(r_bb["stats"]["lp_infeasible"]),        str(r_bc["stats"]["lp_infeasible"])),
            ("Optimal proved",   str(r_bb["optimal_proved"]),                str(r_bc["optimal_proved"])),
        ]

        for idx, row in enumerate(metrics_list):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, values=row, tags=(tag,))

        self.tree.tag_configure("even", background="#ffffff")
        self.tree.tag_configure("odd", background="#f9f9f9")


if __name__ == "__main__":
    main_window = tk.Tk()
    app = BenchmarkApp(main_window)
    main_window.mainloop()