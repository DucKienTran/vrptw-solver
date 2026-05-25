from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class BBNode:
    """Node trong cây Branch and Bound."""
    depth: int = 0
    fixed_arcs: Dict[Tuple[int, int], int] = field(default_factory=dict)
    vehicle_lb: int = 0
    vehicle_ub: Optional[int] = None
    time_bounds: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    note: str = "root"


def clone_node(parent: BBNode, note: str = "child") -> BBNode:
    """Tạo node con từ node cha."""
    return BBNode(
        depth=parent.depth + 1,
        fixed_arcs=dict(parent.fixed_arcs),
        vehicle_lb=parent.vehicle_lb,
        vehicle_ub=parent.vehicle_ub,
        time_bounds=dict(parent.time_bounds),
        note=note,
    )
