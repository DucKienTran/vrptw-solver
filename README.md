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
├── algorithms/                    # Chứa các thuật toán giải quyết bài toán
│   ├── branch_and_bound/
│   │   ├── __init__.py
│   │   ├── branching.py           # Logic chọn biến phân nhánh
│   │   ├── lp_relaxation.py       # Giải LP relaxation tại một node
│   │   ├── node.py                # Định nghĩa cấu trúc BBNode
│   │   └── solver.py              # Thực thi thuật toán Branch and Bound
│   │
│   ├── branch_and_cut/
│   │   ├── __init__.py
│   │   ├── cutting_planes.py      # Logic tìm và thêm các mặt cắt (Cuts)
│   │   ├── lp_relaxation_cuts.py  # Giải LP relaxation có kết hợp mặt cắt
│   │   └── solver.py              # Thực thi thuật toán Branch and Cut
│   │
│   └── branch_and_price/
│       ├── __init__.py
│       ├── branchBound.py         # Quản lý cây tìm kiếm của Branch and Price
│       ├── columnGen.py           # Logic sinh cột (Column Generation)
│       ├── paramsVRP.py           # Cấu hình các tham số VRP
│       ├── route.py               # Quản lý đối tượng tuyến đường
│       ├── solVisualization.py    # Trực quan hóa tuyến đường riêng cho B&P
│       ├── solver.py              # Thực thi thuật toán Branch and Price
│       └── SPPRC.py               # Giải bài toán con (Tìm đường đi ngắn nhất)
│
├── data/                          # Dataset Solomon (C101.txt, R101.txt...)
│
├── docs/                          # Tài liệu dự án
│   ├── presentation.pdf           # Slide báo cáo
│   └── report.pdf                 # Báo cáo chi tiết
│
├── models/                        # Xây dựng mô hình toán học
│   ├── __init__.py
│   └── vrptw_model.py             # Xây dựng mô hình MILP bằng Gurobi
│ 
├── notebooks/                     # Thử nghiệm và trực quan hóa kết quả độc lập
│   └── time_comparison.ipynb      # Jupyter Notebook so sánh thời gian và vẽ biểu đồ
│
├── solvers/                       # Gọi solver giải trực tiếp
│   ├── __init__.py
│   └── gurobi_direct.py           # Giải trực tiếp mô hình MILP bằng Gurobi
│
├── utils/                         # Các file tiện ích hỗ trợ
│   ├── __init__.py
│   ├── data_builder.py            # Tạo data dictionary cho VRPTW
│   ├── io.py                      # Đọc file dữ liệu đầu vào Solomon
│   ├── solution.py                # Truy vết, kiểm tra và tóm tắt tuyến đường
│   └── visualization.py           # Vẽ sơ đồ vị trí và lộ trình xe
│
├── .gitignore                     # Cấu hình loại trừ file khi push lên Git
├── benchmark.py                   # Khởi chạy Hệ thống so sánh thuật toán tự động
├── config.py                      # Cấu hình mặc định của hệ thống
├── main.py                        # File chạy chính chương trình từng thuật toán
├── README.md                      # Tài liệu giới thiệu và hướng dẫn sử dụng
└── requirements.txt               # Danh sách các thư viện Python cần cài đặt

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

Sau khi cài đặt môi trường và các thư viện cần thiết, bạn có hai cách để khởi chạy chương trình: chạy riêng lẻ từng thuật toán qua Terminal hoặc sử dụng giao diện Benchmark để chạy và so sánh tất cả các thuật toán cùng lúc.

### 7.1. Chạy riêng lẻ từng thuật toán (Interactive)

Để chạy đơn lẻ một phương pháp giải bài toán, bạn khởi chạy file `main.py`. Chương trình đã được thiết kế dưới dạng tương tác, cho phép bạn nhập trực tiếp các thông số trên Terminal.

Phần nhập đường dẫn file phải có dạng data/xxxx.txt , nếu chỉ đền mỗi tên bộ data (VD C101.txt) sẽ bị lỗi

Phần đường dẫn file và số lượng khách hàng có thể bấm Enter để chọn mặc định và bỏ qua, tuy nhiên phần chọn phương pháp bắt buộc phải điền một số nguyên từ 1 -> 3.

Sau khi thuật toán chạy xong và tìm được nghiệm, chương trình sẽ tự động bật một cửa sổ đồ thị trực quan hóa sơ đồ các tuyến xe dựa trên kết quả vừa giải.*

**Ví dụ quá trình chạy:**

    PS C:\Users\trand\IdeaProjects\vrptw-solver> python main.py
    Nhập đường dẫn file dữ liệu (Mặc định: data/C101.txt): 
    Nhập số lượng khách hàng muốn giải (Mặc định: 8):

    +=============================================+
    |         CHỌN PHƯƠNG PHÁP GIẢI VRPTW         |
    +=============================================+
    | (1) Branch and Bound (bnb)                  |
    | (2) Branch and Cut (branch_and_cut)         |
    | (3) Branch and Price (branch_and_price)     |
    +---------------------------------------------+
    Chọn phương pháp thực hiện (1-3): 1

*(Chạy nhanh bằng cách truyền tham số 1 dòng, ví dụ: python main.py --data-path data/C101.txt --method bnb --max-customers 8)*.

---

### 7.2. So sánh tất cả thuật toán (Benchmark)

Dự án đã cung cấp sẵn công cụ giao diện trực quan sử dụng thư viện Tkinter.

Để mở Hệ thống so sánh, chạy lệnh sau:

    python benchmark.py

**Hoạt động của Giao diện Benchmark:**
* **Cấu hình trực quan:** Cửa sổ UI cho phép bạn nhập đường dẫn file dữ liệu, số lượng khách hàng và giới hạn node (max nodes) duyệt tối đa.
* **Chạy tự động:** Khi bấm nút KÍCH HOẠT BENCHMARK, hệ thống sẽ tự động cấp một quỹ thời gian độc lập và lần lượt chạy bài toán qua cả 3 thuật toán: Branch & Bound, Branch & Cut, và Branch & Price.
* **Báo cáo chi tiết:** Kết thúc quá trình chạy, màn hình sẽ hiển thị một bảng tổng kết so sánh trực tiếp các chỉ số hiệu suất: Chi phí tối ưu (Min cost), Tổng thời gian giải (s), Thời gian trung bình giải 1 node (ms/node), Tỷ lệ cắt nhánh (Pruning rate), và Optimality Gap.

## 8. Giải thích các chỉ số đánh giá (Metrics)

Dù chạy riêng lẻ từng thuật toán hay chạy đối sánh qua Benchmark GUI, hệ thống đều trả về một bộ các chỉ số (metrics) chi tiết để đánh giá hiệu năng. Dưới đây là ý nghĩa của các chỉ số và cách phân tích chúng:

### 8.1. Các chỉ số cơ bản (Performance Metrics)

* **Min cost (objective):** Tổng chi phí (thường là tổng quãng đường di chuyển) của phương án điều xe tốt nhất tìm được. Nếu các thuật toán đều chạy đến cùng (`Optimal proved = True`), chúng phải ra cùng một con số (Ví dụ: `216.8406`).
* **Total time (s):** Tổng thời gian thuật toán thực thi (tính bằng giây).
* **Time / node (ms):** Thời gian trung bình để xử lý một node trên cây tìm kiếm.
    * *Đặc trưng:* Thuật toán Branch & Price (B&P) thường tốn rất nhiều thời gian cho mỗi node (hàng chục ngàn ms) vì nó phải giải bài toán con (Pricing Problem/SPPRC) để sinh cột. Ngược lại, B&B và B&C xử lý mỗi node rất nhanh (khoảng 11-13 ms).
* **Optimality gap (%):** Khoảng cách giữa nghiệm tốt nhất hiện tại (Upper Bound) và giới hạn dưới lý thuyết (Lower Bound).
    * Gap = `0.00%` nghĩa là thuật toán đã chứng minh được đây là nghiệm tối ưu tuyệt đối, không thể có phương án nào rẻ hơn.
* **Optimal proved:** Bằng `True` nếu thuật toán đã duyệt xong toàn bộ cây tìm kiếm. Nếu bị ép dừng do hết giờ (Time Limit), giá trị này sẽ là `False` (lúc này Gap thường > 0%).

### 8.2. Các chỉ số về Cây tìm kiếm (Search Tree Metrics)

* **Nodes solved & Branches:** Số lượng trạng thái (node) đã duyệt và số lần phân nhánh.
* **Pruned nodes & Pruning rate (%):** Số lượng node bị "cắt bỏ" (không thèm duyệt tiếp vì chi phí chắc chắn đắt hơn nghiệm tốt nhất hiện tại) và tỷ lệ cắt tỉa. Tỷ lệ này càng cao chứng tỏ thuật toán càng thông minh trong việc thu hẹp không gian tìm kiếm.
* **Infeasible nodes:** Số lượng node vi phạm ràng buộc (quá tải trọng, trễ giờ...) bị loại bỏ ngay lập tức.
* **Integer solutions:** Số lần thuật toán tìm thấy một phương án điều xe hợp lệ (nghiệm nguyên) trong suốt quá trình chạy.

### 8.3. Lộ trình xe (Routes)
Kết quả trả về cuối cùng luôn bao gồm danh sách các xe được điều động:
* *Ví dụ:* `Route 1: 0 -> 13 -> 17 -> ... -> 12 -> 0`
* *Ý nghĩa:* Xe số 1 xuất phát từ Depot (0), giao hàng lần lượt cho các khách 13, 17... và quay trở về Depot (0) hoàn thành chuyến đi.

## 9. Tác giả

Project được thực hiện phục vụ mục đích học tập, nghiên cứu và thử nghiệm thuật toán tối ưu hóa cho bài toán VRPTW.

```aiignore
Author: Vu Tien Dat, Tran Duc Kien, Ta Van Nghia
Project: VRPTW Solver
Topic: Vehicle Routing Problem with Time Windows
Algorithm: Branch and Bound, Branch and Cut, Branch and Price
```

## 10. Tài liệu tham khảo:
```aiignore
1. Kallehauge, B. (2006). *On the vehicle routing problem with time windows* (Luận án Tiến sĩ). Centre for Traffic and Transport, Technical University of Denmark.
2. Desrochers, M., Desrosiers, J., & Solomon, M. (1992). A New Optimization Algorithm for the Vehicle Routing Problem with Time Windows. *Operations Research*, 40(2), 342-354. https://doi.org/10.1287/opre.40.2.342
3. Bard, J. F., Kontoravdis, G., & Yu, G. *A Branch-and-Cut Procedure for the Vehicle Routing Problem with Time Windows*. The University of Texas, Austin.
4. Lysgaard, J. (2005). *Reachability Cuts for the Vehicle Routing Problem with Time Windows*. Department of Accounting, Finance and Logistics, Aarhus School of Business, Denmark.
``` 