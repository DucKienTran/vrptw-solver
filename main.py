import argparse
import math
from pathlib import Path

import pandas as pd

from algorithms.branch_and_bound.solver import manual_branch_and_bound_vrptw
# from algorithms.branch_and_cut.solver import solve_branch_and_cut
# from algorithms.branch_and_price.solver import solve_branch_and_price
from config import (
    DEFAULT_DATA_PATH,
    DEFAULT_MAX_CUSTOMERS,
    DIRECT_MILP_TIME_LIMIT,
    MAX_NODES,
    NODE_SELECTION,
    TIME_LIMIT_PER_LP,
    USE_INITIAL_HEURISTIC,
)
from solvers.gurobi_direct import solve_direct_milp_for_check
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
        f.write(f"Instance: {instance_name}\n")
        f.write(f"Method: {method}\n")

        if method == "bnb":
            f.write(f"Has solution: {result['best_solution'] is not None}\n")
            f.write(f"Best objective: {result['best_obj']}\n")
            f.write(f"Optimal proved: {result['optimal_proved']}\n")
            f.write(f"Stopped by node limit: {result['stopped_by_node_limit']}\n")
            f.write(f"Remaining nodes: {result['remaining_nodes']}\n")
            f.write("Stats:\n")
            for k, v in result["stats"].items():
                if k != "log":
                    f.write(f"  {k}: {v}\n")
        else:
            f.write(f"Has solution: {result['has_solution']}\n")
            f.write(f"Objective: {result['obj']}\n")
            f.write(f"Status: {result['status']}\n")
            f.write(f"Valid: {result.get('valid')}\n")
            f.write(f"Message: {result.get('message')}\n")
            f.write(f"MIP gap: {result.get('mip_gap')}\n")

    if not routes_df.empty:
        routes_df.to_csv(routes_path, index=False, encoding="utf-8-sig")

    print(f"Đã lưu summary: {summary_path}")
    if not routes_df.empty:
        print(f"Đã lưu routes: {routes_path}")


def run(args):
    vehicle_number, capacity, df = read_solomon_instance(args.data_path, args.max_customers)
    data = build_vrptw_data(df, vehicle_number, capacity)

    instance_name = Path(args.data_path).stem

    print("========== INSTANCE ==========")
    print("Data path       =", args.data_path)
    print("Instance        =", instance_name)
    print("Vehicle number  =", vehicle_number)
    print("Capacity        =", capacity)
    print("Nodes           =", len(df))
    print("Customers       =", len(df) - 1)
    print("Method          =", args.method)

    if args.method == "bnb":
        result = manual_branch_and_bound_vrptw(
            data=data,
            max_nodes=args.max_nodes,
            node_selection=args.node_selection,
            time_limit_per_lp=args.time_limit_per_lp,
            use_initial_heuristic=args.use_initial_heuristic,
        )

        print("\n========== MANUAL BRANCH AND BOUND RESULT ==========")
        print("best_obj           =", result["best_obj"])
        print("has_solution       =", result["best_solution"] is not None)
        print("optimal_proved     =", result["optimal_proved"])
        print("stopped_node_limit =", result["stopped_by_node_limit"])
        print("remaining_nodes    =", result["remaining_nodes"])

        print("\nStats:")
        for k, v in result["stats"].items():
            if k != "log":
                print(f"  {k}: {v}")

        if result["best_solution"] is not None:
            routes = result["best_solution"]["routes"]
            print("\nTuyến xe từ Branch and Bound:")
            print_routes(routes)
            routes_df = summarize_routes(data, routes)
        else:
            routes = []
            routes_df = pd.DataFrame()
            print("\nManual B&B chưa tìm được nghiệm nguyên trong giới hạn hiện tại.")

    elif args.method == "milp":
        result = solve_direct_milp_for_check(data, time_limit=args.time_limit)

        print("\n========== GUROBI DIRECT MILP RESULT ==========")
        print("status       =", result["status"])
        print("has_solution =", result["has_solution"])
        print("obj          =", result["obj"])
        print("valid        =", result.get("valid"))
        print("message      =", result.get("message"))
        print("mip_gap      =", result.get("mip_gap"))

        if result["has_solution"]:
            routes = result["routes"]
            print("\nTuyến xe từ Gurobi direct MILP:")
            print_routes(routes)
            routes_df = summarize_routes(data, routes)
        else:
            routes = []
            routes_df = pd.DataFrame()
    #
    # elif args.method == "branch_and_cut":
    #     result = solve_branch_and_cut(data, time_limit=args.time_limit)
    #
    #     print("\n========== BRANCH AND CUT BASELINE RESULT ==========")
    #     print("status       =", result["status"])
    #     print("has_solution =", result["has_solution"])
    #     print("obj          =", result["obj"])
    #
    #     if result["has_solution"]:
    #         routes = result["routes"]
    #         print_routes(routes)
    #         routes_df = summarize_routes(data, routes)
    #     else:
    #         routes = []
    #         routes_df = pd.DataFrame()
    #
    # elif args.method == "branch_and_price":
    #     result = solve_branch_and_price(data, time_limit=args.time_limit)
    #     routes = []
    #     routes_df = pd.DataFrame()

    else:
        raise ValueError(f"Method không hợp lệ: {args.method}")

    if args.save:
        save_result_summary(
            output_dir=Path(args.output_dir),
            instance_name=instance_name,
            method=args.method,
            result=result,
            routes_df=routes_df,
        )

    if args.plot and routes:
        plot_routes(data, routes, title=f"{instance_name} - {args.method}")

    return result


def parse_args():
    parser = argparse.ArgumentParser(description="VRPTW Solver")

    parser.add_argument(
        "--data-path",
        default=DEFAULT_DATA_PATH,
        help="Đường dẫn file Solomon, ví dụ data/C101.txt.",
    )

    parser.add_argument(
        "--max-customers",
        type=int,
        default=DEFAULT_MAX_CUSTOMERS,
        help="Số khách hàng dùng để test nhanh. Dùng -1 để lấy toàn bộ.",
    )

    parser.add_argument(
        "--method",
        choices=["bnb", "milp", "branch_and_cut", "branch_and_price"],
        default="bnb",
        help="Phương pháp giải.",
    )

    parser.add_argument(
        "--max-nodes",
        type=int,
        default=MAX_NODES,
        help="Giới hạn số node cho manual Branch and Bound.",
    )

    parser.add_argument(
        "--node-selection",
        choices=["dfs", "best_bound"],
        default=NODE_SELECTION,
        help="Chiến lược chọn node trong Branch and Bound.",
    )

    parser.add_argument(
        "--time-limit-per-lp",
        type=float,
        default=TIME_LIMIT_PER_LP,
        help="Giới hạn thời gian cho mỗi LP relaxation.",
    )

    parser.add_argument(
        "--time-limit",
        type=float,
        default=DIRECT_MILP_TIME_LIMIT,
        help="Giới hạn thời gian cho Gurobi direct MILP / branch_and_cut.",
    )

    parser.add_argument(
        "--use-initial-heuristic",
        action="store_true",
        default=USE_INITIAL_HEURISTIC,
        help="Dùng Gurobi direct MILP ngắn để tạo incumbent ban đầu.",
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Lưu kết quả vào thư mục results.",
    )

    parser.add_argument(
        "--output-dir",
        default="results",
        help="Thư mục lưu kết quả.",
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Vẽ tuyến đường sau khi giải.",
    )

    args = parser.parse_args()

    if args.max_customers == -1:
        args.max_customers = None

    return args


if __name__ == "__main__":
    run(parse_args())
