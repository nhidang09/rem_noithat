import streamlit as st
from datetime import datetime
import os

st.set_page_config(
    page_title="RÈM KHÁNH LINH",
    page_icon="🪟",
    layout="wide"
)

st.title("🪟 HỆ THỐNG QUẢN LÝ RÈM KHÁNH LINH")
st.caption(f"Ngày: {datetime.now().strftime('%d/%m/%Y')}")

st.success("✅ Hệ thống đã sẵn sàng. Hãy chọn chức năng ở **sidebar bên trái**.")

st.markdown("---")
st.info("📌 **Hướng dẫn sử dụng:**\n"
        "1. Quản lý Khách hàng → Thêm/Sửa khách\n"
        "2. Quản lý Sản phẩm → Thêm mẫu rèm thường dùng\n"
        "3. Tạo Hóa đơn Mới → Tạo và lưu hóa đơn\n"
        "4. Danh sách Hóa đơn → Xem tất cả hóa đơn đã lưu")