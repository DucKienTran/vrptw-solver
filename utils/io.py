from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


def read_solomon_instance(path: str, max_customers: Optional[int] = None) -> Tuple[int, int, pd.DataFrame]:
    """
    Đọc file Solomon VRPTW dạng .txt.
    df:
        DataFrame gồm các cột:
        cust_no, x, y, demand, ready, due, service.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {path}")

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        lines = [line.rstrip("\n") for line in f]

    vehicle_number, capacity = None, None
    for idx, line in enumerate(lines):
        if "NUMBER" in line and "CAPACITY" in line:
            parts = lines[idx + 1].split()
            vehicle_number = int(parts[0])
            capacity = int(parts[1])
            break

    if vehicle_number is None or capacity is None:
        raise ValueError("Không đọc được NUMBER/CAPACITY trong file Solomon.")

    rows = []
    for line in lines:
        parts = line.split()
        if len(parts) == 7 and parts[0].lstrip("-").isdigit():
            rows.append([float(x) for x in parts])

    if not rows:
        raise ValueError("Không đọc được bảng CUSTOMER trong file Solomon.")

    df = pd.DataFrame(
        rows,
        columns=["cust_no", "x", "y", "demand", "ready", "due", "service"],
    )
    df["cust_no"] = df["cust_no"].astype(int)

    if max_customers is not None:
        depot_df = df[df["cust_no"] == 0]
        customer_df = df[df["cust_no"] != 0].head(max_customers)
        df = pd.concat([depot_df, customer_df], ignore_index=True)

    return vehicle_number, capacity, df
