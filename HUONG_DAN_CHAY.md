# Hướng Dẫn Cài Đặt & Chạy Mã Nguồn (Task A)

Tài liệu này hướng dẫn chi tiết từng bước thiết lập môi trường, thực thi pipeline xử lý dữ liệu và tạo báo cáo trực quan cho **Task A: Dựng Đồ thị Toàn cục $G$**.

---

## 1. Yêu cầu Môi trường

* **Hệ điều hành:** Windows, Linux hoặc macOS
* **Python:** Phiên bản `>= 3.10` (khuyên dùng Python 3.11 hoặc 3.12)
* **Bộ nhớ RAM:** Tối thiểu 4 GB (pipeline đọc dữ liệu dạng stream line-by-line nên chỉ tiêu tốn ~500 MB - 1 GB RAM)
* **Dung lượng ổ đĩa:** ~2 GB trống (để lưu dữ liệu thô `dblp.txt` và các file output)

---

## 2. Cài đặt Thư viện Cần thiết

Mở Terminal (Command Prompt hoặc PowerShell trên Windows) tại thư mục dự án và chạy lệnh:

```bash
cd D:\IE403
pip install -r requirements.txt
```

Hoặc cài đặt trực tiếp qua `pip`:

```bash
pip install networkx matplotlib plotly scipy
```

---

## 3. Quy trình Thực thi (Pipeline Execution)

Toàn bộ quy trình gồm 3 kịch bản chạy chính tùy theo nhu cầu:

### Bước 1: Chạy Pipeline Toàn diện (Chính thức)

Chạy script [`build_global_graph.py`](build_global_graph.py) để thực hiện trọn vẹn:
1. Đọc stream file thô `dblp.v8/dblp.txt` (hơn 3.1 triệu bài báo).
2. Lọc thời gian giai đoạn lịch sử `1992 <= Year <= 2002`.
3. Dựng đồ thị có hướng $G$ của các tác giả theo chiều lan truyền ảnh hưởng ($A \to B$).
4. Tính toán trước các chỉ số mạng: `In-Degree`, `Out-Degree`, `PageRank`.
5. Tự động kiểm thử tính hợp lệ (Validation) và đối sánh với mốc DeepCas.
6. Xuất ra 2 file nhị phân vào thư mục `outp/`.

```bash
python build_global_graph.py
```

* **Thời gian thực thi:** Khoảng **50 – 60 giây**.
* **Đầu ra tạo thành:**
  * `outp/global_graph_1992_2002.pkl`
  * `outp/global_node_metrics.pkl`

---

### Bước 2: Tái tính toán Chỉ số Mạng Độc lập (Tùy chọn)

Nếu bạn muốn thay đổi tham số tính toán (ví dụ: thay đổi hệ số suy giảm `alpha` của PageRank từ 0.85 sang giá trị khác) mà **không muốn đọc lại file thô 800 MB**, hãy chạy:

```bash
python compute_global_metrics.py
```

* Script sẽ tải trực tiếp đồ thị đã dựng từ `outp/global_graph_1992_2002.pkl`, tính lại metrics và ghi đè `outp/global_node_metrics.pkl` trong **vài giây**.

---

### Bước 3: Xuất Báo cáo & Trực quan hóa Dữ liệu

Chạy script [`visualize_global_graph.py`](visualize_global_graph.py) để sinh dashboard và ảnh tĩnh:

```bash
python visualize_global_graph.py
```

* **Thời gian thực thi:** Khoảng **10 – 15 giây**.
* **Đầu ra tạo thành:**
  1. `outp/global_graph_dashboard.html`:
     * Dashboard tương tác bằng Plotly.
     * Đã nhúng sẵn mã thư viện JavaScript (chạy hoàn toàn **offline**, mở trực tiếp bằng trình duyệt Chrome/Edge bằng cách click đúp).
  2. `outp/global_graph_static.png`:
     * Ảnh tổng hợp 6 panel sắc nét (180 DPI).
     * Dùng để dán trực tiếp vào slide thuyết trình hoặc file báo cáo Word/PDF.

---

## 4. Kiểm tra Kết quả Bàn giao

Sau khi chạy xong, hãy kiểm tra thư mục `outp/` để đảm bảo có đầy đủ 4 file sản phẩm:

```bash
# Kiểm tra danh sách file trên PowerShell
Get-ChildItem D:\IE403\outp
```

Kết quả kỳ vọng:

| Tên File | Kích thước xấp xỉ | Ý nghĩa |
| :--- | :--- | :--- |
| `global_graph_1992_2002.pkl` | ~46 MB | Đồ thị NetworkX DiGraph chứa 133,857 tác giả & 2.26 triệu cạnh |
| `global_node_metrics.pkl` | ~5.4 MB | Bảng Dictionary Python chứa chỉ số tra cứu của 133,857 tác giả |
| `global_graph_dashboard.html` | ~5.0 MB | Trang web tương tác để thuyết minh kết quả |
| `global_graph_static.png` | ~1.0 MB | Ảnh đồ thị tĩnh 6 panel phục vụ báo cáo |

---

## 5. Xử lý Sự cố Thường gặp (Troubleshooting)

1. **Lỗi `ModuleNotFoundError: No module named 'networkx'` (hoặc `plotly`, `scipy`):**
   * *Nguyên nhân:* Thiếu thư viện hoặc đang chạy sai môi trường Python.
   * *Khắc phục:* Chạy `pip install networkx matplotlib plotly scipy`.
2. **Lỗi mở file HTML bị trắng trang:**
   * *Nguyên nhân:* Các file HTML dùng CDN cần mạng internet.
   * *Khắc phục:* Bản HTML mới đã được nhúng inline JavaScript offline 100%, bạn có thể mở bình thường mà không cần kết nối mạng.
3. **Lỗi đường dẫn file không tìm thấy:**
   * Hãy đảm bảo thư mục làm việc hiện tại là `D:\IE403` hoặc đường dẫn thư mục `dblp.v8/` được đặt cạnh các file script `.py`.
