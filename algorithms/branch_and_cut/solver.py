import inspect
from typing import Any, Dict

import algorithms.branch_and_bound.solver as bnb_solver
from algorithms.branch_and_cut.lp_relaxation_cuts import solve_lp_relaxation_with_cuts


def manual_branch_and_cut_vrptw(data: Dict[str, Any], **kwargs):
    """
    Bộ giải Branch and Cut kế thừa lõi xử lý cây của Branch and Bound.

    Điểm khác biệt so với B&B thuần túy:
    - Tại mỗi node, thay vì chỉ giải LP một lần, B&C chạy thêm
      cutting plane loop (Graph Shrinking) để thắt chặt cận dưới trước khi phân nhánh.
    - Cuts tìm được được lưu vào global pool và tái áp dụng ở mọi node tiếp theo.
    """
    print("=== Khởi động hệ thống BRANCH AND CUT ===")

    # 1. Khởi tạo cut pool — PHẢI có đủ cả 2 keys mà cutting_planes.py dùng:
    #    - global_cuts:     list of (frozenset(S), k_S) → dùng để dedup (tránh thêm cut trùng)
    #    - global_cuts_raw: list of (S_list, k_S)       → dùng để replay lên model mới
    #
    #    Bug cũ: chỉ khởi tạo global_cuts = [], không có global_cuts_raw
    #    → replay_global_cuts() không tìm thấy key → không replay gì cả
    #    → mọi node đều giải LP từ đầu như B&B thuần túy
    data["global_cuts"]     = []
    data["global_cuts_raw"] = []

    # 2. Log signature hàm gốc để debug nếu cần
    original_lp_relaxation_func = bnb_solver.solve_lp_relaxation_at_node
    original_params = list(inspect.signature(original_lp_relaxation_func).parameters.keys())
    print(f"[B&C] Signature hàm LP gốc của B&B: {original_params}")
    print(f"[B&C] Monkey-patching → solve_lp_relaxation_with_cuts")

    # 3. Wrapper đảm bảo forward đúng args/kwargs bất kể B&B gọi theo cách nào
    def lp_with_cuts_wrapper(*args, **kw):
        return solve_lp_relaxation_with_cuts(*args, **kw)

    # 4. Monkey patch: ép B&B dùng hàm LP mới có cutting plane
    bnb_solver.solve_lp_relaxation_at_node = lp_with_cuts_wrapper

    try:
        # 5. Chạy toàn bộ bộ máy B&B (duyệt cây, rẽ nhánh, quản lý stack/heap)
        result = bnb_solver.manual_branch_and_bound_vrptw(data, **kwargs)
        return result

    finally:
        # 6. Luôn khôi phục hàm gốc dù có exception hay không
        bnb_solver.solve_lp_relaxation_at_node = original_lp_relaxation_func

        # 7. Dọn cut pool khỏi data để không ảnh hưởng lần chạy B&B sau
        data.pop("global_cuts", None)
        data.pop("global_cuts_raw", None)