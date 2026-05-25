# VRPTW Solver

Project này xây dựng và thử nghiệm thuật toán giải bài toán **Vehicle Routing Problem with Time Windows (VRPTW)** trên bộ dữ liệu Solomon Benchmark.

## 1. Giới thiệu bài toán

**Vehicle Routing Problem with Time Windows (VRPTW)** là bài toán mở rộng của Vehicle Routing Problem, trong đó mỗi khách hàng phải được phục vụ trong một khoảng thời gian cho trước.

Mục tiêu chính của bài toán là:

- Tối thiểu hóa tổng quãng đường di chuyển.
- Sử dụng số lượng xe hợp lý.
- Đảm bảo mỗi khách hàng được phục vụ đúng một lần.
- Đảm bảo tải trọng xe không vượt quá sức chứa.
- Đảm bảo thời gian phục vụ nằm trong khoảng thời gian cho phép của từng khách hàng.

## 2. Mục tiêu của project

Project này được xây dựng với các mục tiêu chính:

- Đọc và xử lý dữ liệu Solomon Benchmark.
- Mô hình hóa bài toán VRPTW.
- Triển khai thuật toán Branch and Bound, Branch and Cut, Branch and Price.
- Kiểm tra các ràng buộc về tải trọng, thời gian và tuyến đường.
- Tìm nghiệm khả thi cho từng instance.
- Tính tổng quãng đường di chuyển.
- Lưu kết quả thực nghiệm.

## 3. Bộ dữ liệu
Project sử dụng bộ dữ liệu **Solomon Benchmark** cho bài toán VRPTW.

Các instance Solomon thường được chia thành 3 nhóm chính:

| Nhóm | Ý nghĩa |
|---|---|
| `C` | Khách hàng phân bố theo cụm |
| `R` | Khách hàng phân bố ngẫu nhiên |
| `RC` | Kết hợp giữa phân bố ngẫu nhiên và phân cụm |

Ngoài ra, mỗi nhóm thường có hai loại:

| Loại | Đặc điểm |
|---|---|
| `1xx` | Time window hẹp, thường cần nhiều xe hơn |
| `2xx` | Time window rộng hơn, thường có thể gom nhiều khách hàng vào một tuyến hơn |

Nguồn dữ liệu chính thức được sử dụng trong project: 

- SINTEF TOP - VRPTW 100 customers:  
```text 
https://www.sintef.no/projectweb/top/vrptw/100-customers
```

## 4. Cấu trúc các thư mục project

```text
vrptw-solver/
├── algorithm/
│   ├── branch_and_bound/
│   │   ├── __init__.py
│   │   ├── node.py              # Định nghĩa BBNode và clone_node
│   │   ├── lp_relaxation.py     # Giải LP relaxation tại một node
│   │   ├── branching.py         # Chọn biến phân số và tạo node con
│   │   └── solver.py            # Manual Branch and Bound 
│   │
│   ├── branch_and_cut/
│   │   ├── __init__.py
│   │   └── solver.py            # Baseline Branch and Cut bằng Gurobi MILP
│   │
│   └── branch_and_price/
│       ├── __init__.py
│       └── solver.py            # Placeholder cho Branch and Price
│
├── data/                         # Đặt C101.txt, R101.txt, RC201.txt...
│
├── docs/
├── models/
│   ├── __init__.py
│   └── vrptw_model.py            # Xây dựng mô hình VRPTW bằng Gurobi
│
├── notebooks/                    # Lưu notebook
├── results/                      # Kết quả chạy 
│
├── solvers/
│   ├── __init__.py
│   └── gurobi_direct.py           # Giải trực tiếp MILP bằng Gurobi
│
├── utils/
│   ├── __init__.py
│   ├── io.py                      # Đọc file Solomon
│   ├── data_builder.py            # Tạo data dictionary cho VRPTW
│   ├── solution.py                # Truy vết route, kiểm tra nghiệm, tóm tắt route
│   └── visualization.py           # Vẽ node và route
│
├── config.py                      # Cấu hình mặc định
├── main.py                        # File chạy chính
├── requirements.txt
└── .gitignore
```

## 5. Cài đặt môi trường 
| Thành phần | Khuyến nghị |
|---|---|
| Python | Python 3.9 trở lên |
| pip | Trình quản lý package của Python |
| Git | Dùng để clone project từ GitHub |
| Gurobi Optimizer | Dùng để giải mô hình tối ưu |
| IDE | Visual Studio Code, PyCharm hoặc IntelliJ IDEA |
| Hệ điều hành | Windows, Linux hoặc macOS |

### 5.1. Clone project

```bash
git clone <https://github.com/vutiendat2302/vrptw-solver.git>
cd vrptw-solver
```
Sau đó, mở terminal tại thư mục project.
### 5.2. Tạo môi trường ảo
Trên Windows:

```bash
python -m venv .venv
```

Trên Linux hoặc macOS:

```bash
python3 -m venv .venv
```

### 5.3. Kích hoạt môi trường ảo

Trên Windows:

```bash
.venv\Scripts\activate
```

Trên Linux hoặc macOS:

```bash
source .venv/bin/activate
```

### 5.4. Cài đặt Gurobi Optimizer

Project sử dụng **Gurobi** để giải các mô hình tối ưu, đặc biệt phù hợp với các thuật toán như **Branch and Cut** hoặc các mô hình quy hoạch nguyên hỗn hợp.

Cần thực hiện các bước sau:

1. Tải và cài đặt Gurobi Optimizer từ trang chính thức:

```text
https://www.gurobi.com/downloads/
```
2. Đăng ký hoặc đăng nhập tài khoản Gurobi.

3. Kích hoạt license Gurobi.

Với academic license, sau khi lấy license key, chạy lệnh tương tự:

```bash
grbgetkey <license-key>
```

Trong đó `<license-key>` là mã license được Gurobi cung cấp.

4. Kiểm tra Gurobi đã được cài đặt thành công:

```bash
gurobi_cl --version
```

## 6. Cài đặt thư viện 
Chạy lệnh:

```bash
pip install -r requirements.txt
```
Nếu trong quá trình phát triển có cài thêm thư viện mới, cập nhật lại file `requirements.txt` bằng lệnh:

```bash
pip freeze > requirements.txt
```

## 7. Cách chạy project 

Sau khi cài đặt môi trường và các thư viện cần thiết, chương trình có thể được chạy thông qua file `main.py`.

Cú pháp tổng quát:

```bash
python main.py --data-path <path_to_data> --method <method_name> [OPTIONS]
```

Trong đó:

| Tham số | Ý nghĩa                                                 |
|---|---------------------------------------------------------|
| `--data-path` | Đường dẫn tới file dữ liệu Solomon `.txt`               |
| `--method` | Phương pháp giải bài toán                               |
| `--max-customers` | Số lượng khách hàng dùng để chạy thử, -1 : lấy toàn bộ  |
| `--time-limit` | Giới hạn thời gian chạy, tính bằng giây                 |
| `--save` | Lưu kết quả chạy vào thư mục `results/`                 |
| `--plot` | Trực quan hóa tuyến đường sau khi giải                  |

Các phương pháp có thể sử dụng:

| Method | Ý nghĩa |
|--------|---|
| `bnb`  | Chạy thuật toán Branch and Bound |
| `milp` | Chạy mô hình MILP trực tiếp bằng Gurobi |
| `bnc`  | Chạy Branch and Cut baseline bằng Gurobi |
| `bnp`  | Chạy Branch and Price nếu đã được triển khai |

---

### 7.1. Chạy Branch and Bound

Ví dụ chạy thuật toán **Branch and Bound** trên instance `C101.txt` với 8 khách hàng đầu tiên:

```bash
python main.py --data-path data/C101.txt --method bnb --max-customers 8
```

Lưu ý: với số lượng khách hàng lớn, Branch and Bound có thể chạy lâu do số lượng nhánh tăng nhanh.

---

### 7.2. Chạy mô hình MILP bằng Gurobi

Ví dụ chạy mô hình MILP trực tiếp bằng **Gurobi**:

```bash
python main.py --data-path data/C101.txt --method milp --max-customers 8
```

Cách chạy này dùng Gurobi để xây dựng và giải trực tiếp mô hình tối ưu của bài toán VRPTW.

---

### 7.3. Lưu kết quả

Để lưu kết quả chạy vào thư mục `results/`, thêm tùy chọn `--save`.

Ví dụ:

```bash
python main.py --data-path data/C101.txt --method bnb --max-customers 8 --save
```
---

### 7.4. Trực quan hóa tuyến đường

Để vẽ tuyến đường sau khi giải, thêm tùy chọn `--plot`.

Ví dụ chạy Branch and Bound và trực quan hóa tuyến đường:

```bash
python main.py --data-path data/C101.txt --method bnb --max-customers 8 --plot
```

Có thể kết hợp vừa lưu kết quả vừa trực quan hóa:

```bash
python main.py --data-path data/C101.txt --method milp --max-customers 8 --save --plot
```

---

### 7.6. Một số ví dụ chạy thường dùng

Chạy Branch and Bound:

```bash
python main.py --data-path data/C101.txt --method bnb --max-customers 8
```

```bash
python main.py --data-path data/C101.txt --method bnb --max-customers 8 --save --plot
```

Chạy Gurobi MILP :

```bash
python main.py --data-path data/C101.txt --method milp --max-customers 8 --plot --save 
```

```bash
python main.py --data-path data/C101.txt --method milp --max-customers -1 --time-limit 3600
```

## 8. Tác giả

Project được thực hiện phục vụ mục đích học tập, nghiên cứu và thử nghiệm thuật toán tối ưu hóa cho bài toán VRPTW.

```aiignore
Author: Vu Tien Dat, Tran Duc Kien, Ta Van Nghia
Project: VRPTW Solver
Topic: Vehicle Routing Problem with Time Windows
Algorithm: Branch and Bound, Branch and Cut, Branch and Price
```

## 9. Tài liệu tham khảo:
```aiignore
1. Kallehauge, B. (2006). *On the vehicle routing problem with time windows* (Luận án Tiến sĩ). Centre for Traffic and Transport, Technical University of Denmark.
2. Desrochers, M., Desrosiers, J., & Solomon, M. (1992). A New Optimization Algorithm for the Vehicle Routing Problem with Time Windows. *Operations Research*, 40(2), 342-354. https://doi.org/10.1287/opre.40.2.342
3. Bard, J. F., Kontoravdis, G., & Yu, G. *A Branch-and-Cut Procedure for the Vehicle Routing Problem with Time Windows*. The University of Texas, Austin.
4. Lysgaard, J. (2005). *Reachability Cuts for the Vehicle Routing Problem with Time Windows*. Department of Accounting, Finance and Logistics, Aarhus School of Business, Denmark.
``` 