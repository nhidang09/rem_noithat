import streamlit as st
from datetime import datetime
import pandas as pd
import os

st.set_page_config(
    page_title="Rèm Khánh Linh",
    page_icon="🪟",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("data", exist_ok=True)

st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .stButton > button[kind="primary"] {
        background: #1e3a8a;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e3a8a,#2563eb); color:white;
            padding:20px 30px; border-radius:12px; margin-bottom:24px;
            display:flex; justify-content:space-between; align-items:center;">
    <div>
        <h1 style="margin:0; font-size:2em;">🪟 RÈM KHÁNH LINH</h1>
        <p style="margin:0; opacity:0.85; font-size:0.95em;">Hệ thống quản lý hóa đơn</p>
    </div>
    <div style="text-align:right;">
        <p style="margin:0; font-size:1.1em; font-weight:600;">{datetime.now().strftime('%A')}</p>
        <p style="margin:0; font-size:1.5em; font-weight:700;">{datetime.now().strftime('%d/%m/%Y')}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Metrics ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

try:
    df_inv = pd.read_csv("data/invoices.csv", encoding="utf-8-sig")
    total_invoices = len(df_inv)
    total_revenue  = int(pd.to_numeric(df_inv["Tong_Tien"], errors="coerce").fillna(0).sum())
    unpaid = len(df_inv[df_inv["Trang_Thai"].astype(str).str.contains("Chưa|lưu", na=False)])
except:
    total_invoices = total_revenue = unpaid = 0

try:
    total_customers = len(pd.read_csv("data/customers.csv", encoding="utf-8-sig"))
except:
    total_customers = 0

with col1:
    st.metric("📄 Tổng hóa đơn", total_invoices)
with col2:
    st.metric("💰 Tổng doanh thu", f"{total_revenue:,} ₫")
with col3:
    st.metric("⏳ Chưa thanh toán", unpaid)
with col4:
    st.metric("👥 Khách hàng", total_customers)

st.markdown("---")

st.info("""
📌 **Hướng dẫn sử dụng** — Chọn chức năng ở **sidebar bên trái**:
- **Tạo Hóa Đơn** → Tạo hóa đơn mới, in PDF gửi khách
- **Danh Sách Hóa Đơn** → Xem, sửa, xóa từng dòng sản phẩm
- **Quản Lý Khách Hàng** → Thêm/sửa thông tin khách
- **Quản Lý Sản Phẩm** → Danh mục rèm và đơn giá
- **Báo Cáo** → Thống kê doanh thu theo tháng
""")