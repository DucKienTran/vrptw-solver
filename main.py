import argparse
import time
import math
from pathlib import Path
import pandas as pd

from algorithms.branch_and_bound.solver import manual_branch_and_bound_vrptw
from algorithms.branch_and_cut.solver import manual_branch_and_cut_vrptw
from algorithms.branch_and_price.solver import manual_branch_and_price_vrptw
from config import (
    DEFAULT_DATA_PATH,
    DEFAULT_MAX_CUSTOMERS,
    MAX_NODES,
    NODE_SELECTION,
    TIME_LIMIT_PER_LP,
    USE_INITIAL_HEURISTIC,
)
from utils.data_builder import build_vrptw_data
from utils.io import read_solomon_instance
from utils.solution import summarize_routes
from utils.visualization import plot_routes


def print_routes(routes):
    for idx, route in enumerate(routes, start=1):
        print(f"Route {idx}: " + " -> ".join(map(str, route)))


def save_result_summary(output_dir: Path, instance_name: str, method: str, result: dict, routes_df: pd.DataFrame):
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{instance_name}_{method}_summary.txt"
    routes_path = output_dir / f"{instance_name}_{method}_routes.csv"

    with summary_path.open("w", encoding="utf-8") as f:
        f.write(f"Instance: {instance_name}\nMethod: {method}\n")
        f.write(f"Has solution: {result.get('best_solution') is not None}\n")
        f.write(f"Best objective: {result.get('best_obj')}\n")
        f.write(f"Optimal proved: {result.get('optimal_proved')}\n")

        if "stats" in result:
            f.write("Stats:\n")
            for k, v in result["stats"].items():
                if k != "log":
                    f.write(f"  {k}: {v}\n")

    if not routes_df.empty:
        routes_df.to_csv(routes_path, index=False, encoding="utf-8-sig")

    print(f"\nĐã lưu summary: {summary_path}")
    if not routes_df.empty:
        print(f"Đã lưu routes: {routes_path}")


def print_full_metrics(result, elapsed_time, method_name):
    s = result.get("stats", {})
    obj = result.get("best_obj", math.inf)
    nodes = s.get("nodes_solved", 0)
    pruned = s.get("pruned_by_bound", 0)
    lb = result.get("global_lower_bound", None)

    pruning_rate = f"{pruned / nodes * 100:.1f}%" if nodes > 0 else "N/A"
    time_per_node = f"{elapsed_time / nodes * 1000:.2f} ms" if nodes > 0 else "N/A"

    opt_gap = "N/A"
    if lb is not None and obj not in (math.inf, 0) and isinstance(lb, (int, float)):
        opt_gap = f"{abs(obj - lb) / abs(obj) * 100:.2f}%"

    print(f"\n========== {method_name.upper()} METRICS ==========")
    print(f"{'Min cost':<25}: {obj if obj != math.inf else 'No Sol'}")
    print(f"{'Total time (s)':<25}: {elapsed_time:.4f}")
    print(f"{'Time / node (ms)':<25}: {time_per_node}")
    print(f"{'Nodes solved':<25}: {nodes}")
    print(f"{'Branches':<25}: {s.get('branch_count', 'N/A')}")
    print(f"{'Pruned nodes':<25}: {pruned}")
    print(f"{'Pruning rate (%)':<25}: {pruning_rate}")
    print(f"{'Infeasible nodes':<25}: {s.get('lp_infeasible', 'N/A')}")
    print(f"{'Integer solutions':<25}: {s.get('integer_solutions', 'N/A')}")
    print(f"{'Optimality gap (%)':<25}: {opt_gap}")
    print(f"{'Optimal proved':<25}: {result.get('optimal_proved', 'N/A')}")


def run(args):
    if args.data_path == DEFAULT_DATA_PATH:
        user_path = input(f"Nhập đường dẫn file dữ liệu (Mặc định: {DEFAULT_DATA_PATH}): ").strip()
        if user_path:
            args.data_path = user_path

    if args.max_customers == DEFAULT_MAX_CUSTOMERS or args.max_customers is None:
        user_cust = input(f"Nhập số lượng khách hàng muốn giải (Mặc định: {DEFAULT_MAX_CUSTOMERS}): ").strip()
        if user_cust:
            args.max_customers = int(user_cust)
            if args.max_customers == -1:
                args.max_customers = None
    # --------------------------------------------------

    # Hiển thị bảng lựa chọn nếu chưa truyền qua CLI
    if args.method is None:
        print("\n+" + "="*45 + "+")
        print(f"| {'CHỌN PHƯƠNG PHÁP GIẢI VRPTW':^43} |")
        print("+" + "="*45 + "+")
        print(f"| {'(1) Branch and Bound (bnb)':<43} |")
        print(f"| {'(2) Branch and Cut (branch_and_cut)':<43} |")
        print(f"| {'(3) Branch and Price (branch_and_price)':<43} |")
        print("+" + "-"*45 + "+")

        while True:
            choice = input("Chọn phương pháp thực hiện (1-3): ").strip()
            mapping = {"1": "bnb", "2": "branch_and_cut", "3": "branch_and_price"}
            if choice in mapping:
                args.method = mapping[choice]
                break
            print("[!] Lựa chọn không hợp lệ. Vui lòng nhập lại.")

    vehicle_number, capacity, df = read_solomon_instance(args.data_path, args.max_customers)
    data = build_vrptw_data(df, vehicle_number, capacity)
    instance_name = Path(args.data_path).stem

    print("\n========== INSTANCE ==========")
    print(f"Data path       = {args.data_path}")
    print(f"Instance        = {instance_name}")
    print(f"Customers       = {len(df) - 1}")
    print(f"Method          = {args.method}")

    solver_kwargs = {
        "max_nodes": args.max_nodes,
        "node_selection": args.node_selection,
        "time_limit_per_lp": args.time_limit_per_lp,
        "use_initial_heuristic": args.use_initial_heuristic,
    }
    import builtins
    builtins.GLOBAL_START_TIME = time.time() # Lấy chuẩn thời gian bắt đầu tại đây
    builtins.GLOBAL_TIME_LIMIT = args.time_limit
    t0 = time.time()
    if args.method == "bnb":
        result = manual_branch_and_bound_vrptw(data=data, **solver_kwargs)
    elif args.method == "branch_and_cut":
        result = manual_branch_and_cut_vrptw(data=data, **solver_kwargs)
    elif args.method == "branch_and_price":
        result = manual_branch_and_price_vrptw(data=data)
    else:
        raise ValueError(f"Method không hợp lệ: {args.method}")
    elapsed_time = time.time() - t0

    print_full_metrics(result, elapsed_time, args.method)

    routes = []
    routes_df = pd.DataFrame()

    if result.get("best_solution") is not None:
        raw_routes = result["best_solution"].get("routes") if isinstance(result["best_solution"], dict) else [r.get_path() for r in result["best_solution"]]
        routes = raw_routes
        print("\n========== ROUTES ==========")
        print_routes(routes)
        routes_df = summarize_routes(data, routes)
    else:
        print("\n[!] Chưa tìm được nghiệm nguyên trong giới hạn hiện tại.")

    if args.save:
        save_result_summary(Path(args.output_dir), instance_name, args.method, result, routes_df)

    if args.plot and routes:
        plot_routes(data, routes, title=f"{instance_name} - {args.method}")

    return result


def parse_args():
    parser = argparse.ArgumentParser(description="VRPTW Solver")
    parser.add_argument("--data-path", default=DEFAULT_DATA_PATH)
    parser.add_argument("--max-customers", type=int, default=DEFAULT_MAX_CUSTOMERS)
    parser.add_argument("--method", choices=["bnb", "branch_and_cut", "branch_and_price"], default=None)
    parser.add_argument("--max-nodes", type=int, default=MAX_NODES)
    parser.add_argument("--node-selection", choices=["dfs", "best_bound"], default=NODE_SELECTION)
    parser.add_argument("--time-limit-per-lp", type=float, default=TIME_LIMIT_PER_LP)
    parser.add_argument("--use-initial-heuristic", action="store_true", default=USE_INITIAL_HEURISTIC)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--plot", action="store_true")

    parser.add_argument("--time-limit", type=float, default=3600.0, help="Time limit (s)")

    args = parser.parse_args()
    if args.max_customers == -1:
        args.max_customers = None
    return args


if __name__ == "__main__":
    run(parse_args())