DEFAULT_DATA_PATH = "data/C101.txt"

DEFAULT_MAX_CUSTOMERS = 8

EPS = 1e-6

# Giới hạn thời gian cho mỗi LP relaxation trong manual Branch and Bound.
TIME_LIMIT_PER_LP = 600000

# Giới hạn số node trong manual Branch and Bound.
MAX_NODES = 100000000

# "dfs" hoặc "best_bound"
NODE_SELECTION = "dfs"

# Có dùng Gurobi MILP ngắn để tạo incumbent ban đầu hay không.
USE_INITIAL_HEURISTIC = False

# Giới hạn thời gian cho Gurobi direct MILP.
DIRECT_MILP_TIME_LIMIT = 30000
