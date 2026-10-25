# Hướng dẫn Task B: Cascade, nhãn và chia tập

## Mục tiêu

Task B xây dựng bộ dữ liệu huấn luyện từ đồ thị toàn cục G của Task A, theo logic:

- Lọc các bài báo xuất bản trong khoảng 2003–2009.
- Với mỗi bài báo, xây dựng cascade g_c^t trong khoảng t = 1 năm.
- Tính delta_s = số lượng tác giả mới tham gia sau 1 năm.
- Tạo nhãn y = log2(delta_s + 1).
- Giảm 50% các cascade có delta_s = 0.
- Chia tập: 2003–2007 = train, 2008 = val, 2009 = test.
- Vẽ histogram của delta_s trước và sau biến đổi log.

---

## Cấu trúc thư mục output

Sau khi chạy script, thư mục sẽ có dạng:

```text
IE403/
├── outp/
│   └── task_b/
│       ├── train.csv
│       ├── val.csv
│       ├── test.csv
│       └── cascade_growth_distribution.png
```

---

## File script chính

- `build_task_b_dataset.py`: script sinh bộ dữ liệu Task B.

---

## Cách chạy

### 1. Từ thư mục IE403

```bash
cd IE403
python build_task_b_dataset.py
```

### 2. Nếu muốn chạy với file đồ thị của Task A

```bash
python build_task_b_dataset.py --graph outp/global_graph_1992_2002.pkl
```

### 3. Nếu muốn dùng file dữ liệu paper riêng

```bash
python build_task_b_dataset.py --paper-file outp/task_b/demo_papers.csv
```

---

## Dữ liệu mẫu

Vì Task A đang chờ Graph G đầy đủ, script mặc định sẽ tạo một bộ dữ liệu demo nhỏ khoảng 120 bài trong năm 2003–2009 để bạn có thể kiểm tra định dạng đầu ra ngay.

Bộ dữ liệu demo có dạng:

```csv
paper_id,year,authors,references
P_2003_001,2003,"Alice Chen|Bob Kumar",""
```

Trong đó:

- `paper_id`: mã bài báo
- `year`: năm xuất bản
- `authors`: danh sách tác giả cách nhau bởi dấu `|`
- `references`: danh sách paper_id được trích dẫn, cách nhau bởi dấu `|`

---

## Cột dữ liệu ở file train/val/test

Mỗi file output có các cột:

- `paper_id`
- `year`
- `cascade_size`
- `delta_s`
- `y`
- `split`

Trong đó:

- `cascade_size`: số tác giả xuất hiện trong cascade sau 1 năm
- `delta_s`: tăng trưởng sau 1 năm
- `y`: nhãn mục tiêu, tính theo công thức `log2(delta_s + 1)`

---

## Mô tả của hàm tính nhãn

```python
delta_s = max(0, len(cascade_authors) - len(root_authors))
y = log2(delta_s + 1)
```

Đây là cách đơn giản và ổn định để chuyển số tăng trưởng thành nhãn liên tục.

---

## Lưu ý khi dùng bộ dữ liệu thật

Khi có file G của Task A và dữ liệu paper đầy đủ, bạn nên thay thay đổi logic xây dựng cascade theo mô hình thực tế:

- Duyệt từng bài báo root theo năm.
- Tìm các bài báo xuất bản đúng 1 năm sau có trích dẫn root.
- Lấy tập tác giả của root và các bài báo đó.
- Xây dựng `g_c^t` bằng các tác giả thuộc tập đó.
- Tính `delta_s` và `log2(delta_s + 1)` tương tự như script demo.

---

## Kiểm tra nhanh

Sau khi chạy script, bạn có thể kiểm tra các file ngắn gọn như sau:

```bash
ls outp/task_b
```

Và kiểm tra sơ bộ nội dung train:

```bash
head outp/task_b/train.csv
```

---

## Ghi chú cho thành viên khác

Nếu bạn đang tham gia đội và muốn xem thử với dữ liệu mẫu, chỉ cần:

```bash
cd IE403
python build_task_b_dataset.py
```

Nếu sinh ra các file và biểu đồ thành công, phần Task B đã được chuẩn hóa đủ để tiếp tục phát triển cho dữ liệu thật sau này.
