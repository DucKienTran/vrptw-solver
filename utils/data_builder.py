import math
from typing import Any, Dict

import pandas as pd


def build_vrptw_data(df: pd.DataFrame, vehicle_number: int, capacity: float) -> Dict[str, Any]:
    """
    Xây dựng các tập, tham số và ma trận khoảng cách cho bài toán VRPTW.
    """
    df = df.copy().reset_index(drop=True)

    nodes = [int(v) for v in df["cust_no"].tolist()]
    depot = 0
    customers = [i for i in nodes if i != depot]

    xcoord = dict(zip(df["cust_no"].astype(int), df["x"].astype(float)))
    ycoord = dict(zip(df["cust_no"].astype(int), df["y"].astype(float)))
    q = dict(zip(df["cust_no"].astype(int), df["demand"].astype(float)))
    a = dict(zip(df["cust_no"].astype(int), df["ready"].astype(float)))
    b = dict(zip(df["cust_no"].astype(int), df["due"].astype(float)))
    service = dict(zip(df["cust_no"].astype(int), df["service"].astype(float)))

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    c = {}
    tau = {}
    M_time = {}

    for i, j in arcs:
        dist = math.hypot(xcoord[i] - xcoord[j], ycoord[i] - ycoord[j])
        c[i, j] = dist
        tau[i, j] = service[i] + dist
        M_time[i, j] = max(0.0, b[i] + tau[i, j] - a[j])

    return {
        "df": df,
        "nodes": nodes,
        "customers": customers,
        "depot": depot,
        "arcs": arcs,
        "m": int(vehicle_number),
        "Q": float(capacity),
        "xcoord": xcoord,
        "ycoord": ycoord,
        "q": q,
        "a": a,
        "b": b,
        "service": service,
        "c": c,
        "tau": tau,
        "M_time": M_time,
    }
