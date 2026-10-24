# Hướng Dẫn Cấu Trúc Dữ Liệu (Schema) AMiner DBLP Citation Network

Tài liệu này mô tả chi tiết cấu trúc dữ liệu thô (Schema) của bộ dữ liệu
**AMiner DBLP Citation Network V8** (định dạng văn bản `.txt`) và hướng dẫn
trích xuất phục vụ cho **Task A: Dựng Đồ Thị Toàn Cục $G$**.

---

## 1. Cấu Trúc Tiền Tố (Schema Prefixes)

Trong file dữ liệu thô, mỗi bài báo được lưu thành một khối dữ liệu (data block).
Các thuộc tính của bài báo được đánh dấu bằng các ký hiệu tiền tố ở đầu mỗi dòng:

| Tiền tố | Tên trường | Ý nghĩa | Ví dụ |
| :--- | :--- | :--- | :--- |
| **`#*`** | **Paper Title** | Tên bài báo khoa học | `#*Information geometry...` |
| **`#@`** | **Authors** | Danh sách tác giả (phân cách bằng dấu phẩy) | `#@Noboru Murata,Takashi...` |
| **`#t`** | **Year** | Năm xuất bản | `#t2004` |
| **`#c`** | **Publication Venue** | Tạp chí / Hội nghị xuất bản bài báo | `#cNeural Computation` |
| **`#index`** | **Paper ID** | Mã định danh duy nhất của bài báo | `#index436405` |
| **`#%`** | **Reference ID** | Mã ID của bài báo được trích dẫn (1 dòng = 1 trích dẫn) | `#%94584` |
| **`#!`** | **Abstract** | Tóm tắt nội dung bài báo | `#!We aim at...` |

---

## 2. Ví Dụ Mẫu Một Khối Dữ Liệu (Data Block Example)

```text
#*Information geometry of U-Boost and Bregman divergence
#@Noboru Murata,Takashi Takenouchi,Takafumi Kanamori,Shinto Eguchi
#t2004
#cNeural Computation
#index436405
#%94584
#%282290
#%605546
#!We aim at an extension of AdaBoost to U-Boost...
```

---

## 3. Cấu Trúc Đồ Thị $G$ (Task A Output) - AUTHOR CITATION NETWORK

> **Quy ước chuẩn DeepCas (arXiv:1611.05373):** Đồ thị nền toàn cục $G$ là
> **mạng trích dẫn tác giả (Author Citation Network)**.

### 3.1 Định nghĩa thực thể

| Thành phần | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| **Nút (Nodes)** | `str` | **Tên tác giả** (trích xuất từ trường `#@`) |
| **Cạnh (Edges) $A \to B$** | Cạnh có hướng | Tác giả $A$ **được tác giả $B$ trích dẫn** (chiều lan truyền ảnh hưởng) |

### 3.2 Quy tắc tạo cạnh (Cartesian Product)

```text
Với mỗi bài báo P (xuất bản 1992–2002) trích dẫn bài báo R (xuất bản 1992–2002):
  - A = danh sách tác giả của bài R (tác giả được trích dẫn)
  - B = danh sách tác giả của bài P (tác giả đi trích dẫn)
  - Với mọi cặp (a in A, b in B) với a != b:
      Thêm cạnh có hướng a -> b vào G
```

### 3.3 Điều kiện lọc thời gian

Chỉ xử lý các bài báo có năm xuất bản trong giai đoạn `1992 <= Year <= 2002`.
Cả bài trích dẫn ($P$) và bài được trích dẫn ($R$) đều phải thuộc khoảng thời gian này để chống rò rỉ dữ liệu (data leakage).

---

## 4. Bảng So Sánh Với Bài Báo Gốc DeepCas

| Chỉ số | Kết quả thực nghiệm Task A | Mục tiêu DeepCas (Table 1) | Mức độ khớp & Đánh giá |
| :--- | :---: | :---: | :--- |
| **Số Nút (Tác giả)** | **133,857** | **131,415** | ✅ **Khớp 98.2%** (chỉ lệch 1.8%) |
| **Số Cạnh (Quan hệ tác giả)** | **2,266,378** | **842,542** | ℹ️ Cao hơn do tích Descartes đồng tác giả ($|A| \times |B|$) |
| **Lượt trích dẫn bài báo gốc** | **718,679 – 931,324** | **842,542** | ✅ Con số 842k của bài nằm trọn trong khoảng này |

---

## 5. Danh Mục Sản Phẩm Bàn Giao (`outp/`)

| Tên File | Định dạng | Mô tả & Cách sử dụng |
| :--- | :--- | :--- |
| `outp/global_graph_1992_2002.pkl` | Binary (`nx.DiGraph`) | Đồ thị mạng NetworkX chứa 133,857 tác giả và 2.26 triệu cạnh |
| `outp/global_node_metrics.pkl` | Binary (`dict`) | Bảng tra cứu $O(1)$ chỉ số `{in_degree, out_degree, pagerank}` |
| `outp/global_graph_dashboard.html` | HTML / JS (Plotly) | Dashboard tương tác offline kiểm tra phân phối bậc & mạng trích dẫn |
| `outp/global_graph_static.png` | Hình ảnh PNG (180 DPI) | Ảnh tổng hợp 6 panel phục vụ slide thuyết trình và báo cáo |
