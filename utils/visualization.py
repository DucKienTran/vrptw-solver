from typing import Any, Dict, List

import matplotlib.pyplot as plt

from utils.solution import route_load


def plot_locations(data: Dict[str, Any], title: str = "Vị trí depot và khách hàng"):
    """Vẽ vị trí depot và khách hàng."""
    df_plot = data["df"]
    depot = data["depot"]

    depot_df = df_plot[df_plot["cust_no"] == depot]
    cust_df = df_plot[df_plot["cust_no"] != depot]

    plt.figure(figsize=(9, 7))
    plt.scatter(cust_df["x"], cust_df["y"], s=45, label="Khách hàng")
    plt.scatter(depot_df["x"], depot_df["y"], s=160, marker="s", label="Depot")

    for _, row in df_plot.iterrows():
        plt.text(row["x"] + 0.5, row["y"] + 0.5, str(int(row["cust_no"])), fontsize=9)

    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def plot_routes(data: Dict[str, Any], routes: List[List[int]], title: str = "Tuyến xe VRPTW"):
    """Vẽ các tuyến xe."""
    df_plot = data["df"]
    depot = data["depot"]

    coord = {
        int(row["cust_no"]): (float(row["x"]), float(row["y"]))
        for _, row in df_plot.iterrows()
    }

    depot_df = df_plot[df_plot["cust_no"] == depot]
    cust_df = df_plot[df_plot["cust_no"] != depot]

    plt.figure(figsize=(11, 8))

    plt.scatter(cust_df["x"], cust_df["y"], s=45, label="Khách hàng")
    plt.scatter(depot_df["x"], depot_df["y"], s=170, marker="s", label="Depot")

    for _, row in df_plot.iterrows():
        plt.text(row["x"] + 0.5, row["y"] + 0.5, str(int(row["cust_no"])), fontsize=9)

    for k, route in enumerate(routes, start=1):
        clean_route = [node for node in route if isinstance(node, int)]
        if len(clean_route) < 2:
            continue

        xs = [coord[node][0] for node in clean_route]
        ys = [coord[node][1] for node in clean_route]
        load = route_load(data, clean_route)

        plt.plot(xs, ys, marker="o", linewidth=1.8, label=f"Route {k} | load={load:.0f}")

        for u, v in zip(clean_route[:-1], clean_route[1:]):
            x1, y1 = coord[u]
            x2, y2 = coord[v]
            plt.annotate(
                "",
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", lw=1.1, shrinkA=5, shrinkB=5),
            )

    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.title(title)
    plt.legend(loc="best", fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.show()
