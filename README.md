# 🪟 Rèm Khánh Linh — Hệ thống Quản lý Hóa đơn

Ứng dụng web quản lý hóa đơn nội thất rèm cửa, xây dựng bằng Python & Streamlit.

---

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 📄 Tạo hóa đơn | Thêm nhiều sản phẩm, tính tự động theo m² hoặc mét ngang |
| 🖨️ In / Lưu PDF | Hóa đơn đẹp, in trực tiếp từ trình duyệt với đầy đủ màu sắc |
| 💰 Điều chỉnh | Hỗ trợ đặt cọc, thuế VAT, chiết khấu — tự tính số còn lại |
| 📋 Quản lý hóa đơn | Thêm / sửa / xóa từng dòng sản phẩm trong hóa đơn cũ |
| 👥 Quản lý khách hàng | Thêm, sửa, xóa — tránh trùng số điện thoại |
| 📦 Quản lý sản phẩm | Danh mục rèm, gợi ý đơn giá khi lập hóa đơn |
| 📊 Báo cáo | Doanh thu theo tháng, sản phẩm bán chạy, top khách hàng |

---

## 🖥️ Giao diện

> Hóa đơn in ra giữ nguyên màu sắc, hỗ trợ lưu PDF trực tiếp từ trình duyệt.

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.9+

### Các bước

```bash
# 1. Clone repo
git clone https://github.com/<your-username>/rem-khanh-linh.git
cd rem-khanh-linh

# 2. Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Cài thư viện
pip install -r requirements.txt

# 4. Chạy ứng dụng
streamlit run main.py
```

Mở trình duyệt tại `http://localhost:8501`

---

## 📁 Cấu trúc dự án

```
rem-khanh-linh/
├── main.py                     # Trang chủ / dashboard
├── pages/
│   ├── 1_Quan_Ly_Khach_Hang.py
│   ├── 2_Quan_Ly_San_Pham.py
│   ├── 3_Tao_Hoa_Don.py
│   ├── 4_Danh_Sach_Hoa_Don.py
│   └── 5_Bao_Cao.py
├── data/                       # CSV lưu trữ dữ liệu (không đưa lên Git)
│   ├── customers.csv
│   ├── products.csv
│   └── invoices.csv
├── reset_data.py               # Script xóa dữ liệu test
├── requirements.txt
└── .gitignore
```

---

## 🛠️ Công nghệ sử dụng

- **Python 3.13**
- **Streamlit** — framework web
- **Pandas** — xử lý dữ liệu CSV
- **HTML/CSS** — render hóa đơn in đẹp trong iframe

---

## 📌 Lưu ý

- Dữ liệu lưu dạng CSV trong thư mục `data/` (không đồng bộ lên GitHub theo `.gitignore`)
- Để reset dữ liệu về trống: `python reset_data.py`

---

*Dự án xây dựng cho mục đích học tập và thực hành phát triển ứng dụng web với Python.*
