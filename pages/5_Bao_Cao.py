import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.title("📊 Báo cáo & Thống kê")

FILE_PATH = "data/invoices.csv"

if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) == 0:
    st.warning("Chưa có dữ liệu hóa đơn. Hãy tạo hóa đơn trước để xem báo cáo.")
    st.stop()

try:
    df = pd.read_csv(FILE_PATH, encoding='utf-8-sig')
except:
    st.error("Không đọc được file dữ liệu.")
    st.stop()

if df.empty:
    st.warning("Chưa có hóa đơn nào.")
    st.stop()

# Chuẩn hóa dữ liệu
df["Tong_Tien"] = pd.to_numeric(df["Tong_Tien"], errors="coerce").fillna(0)

# Chuẩn hóa ngày tháng (hỗ trợ nhiều format)
def parse_date(s):
    for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return pd.to_datetime(str(s), format=fmt)
        except:
            continue
    return pd.NaT

df["Ngay_dt"] = df["Ngay_Lap"].apply(parse_date)
df["Thang"]   = df["Ngay_dt"].dt.to_period("M").astype(str)
df["Nam"]     = df["Ngay_dt"].dt.year.fillna(0).astype(int)

# ── Tổng quan ─────────────────────────────────────────────────────────────────
st.subheader("📌 Tổng quan")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng hóa đơn",    len(df))
c2.metric("Tổng doanh thu",  f"{df['Tong_Tien'].sum():,.0f} ₫")
c3.metric("Đã thanh toán",   len(df[df["Trang_Thai"].astype(str).str.contains("Đã thanh toán", na=False)]))
c4.metric("Chưa thanh toán", len(df[df["Trang_Thai"].astype(str).str.contains("Chưa|lưu", na=False)]))

st.markdown("---")

# ── Doanh thu theo tháng ──────────────────────────────────────────────────────
st.subheader("📈 Doanh thu theo tháng")

df_month = df.groupby("Thang")["Tong_Tien"].sum().reset_index()
df_month.columns = ["Tháng", "Doanh Thu (₫)"]
df_month = df_month.sort_values("Tháng")

if len(df_month) > 0:
    st.bar_chart(df_month.set_index("Tháng"))

    # Bảng chi tiết
    df_month["Doanh Thu"] = df_month["Doanh Thu (₫)"].apply(lambda x: f"{int(x):,} ₫")
    df_month["Số HĐ"] = df.groupby("Thang").size().values
    st.dataframe(df_month[["Tháng", "Số HĐ", "Doanh Thu"]], use_container_width=True, hide_index=True)
else:
    st.info("Chưa đủ dữ liệu để vẽ biểu đồ tháng.")

st.markdown("---")

# ── Top sản phẩm bán chạy ─────────────────────────────────────────────────────
st.subheader("🏆 Sản phẩm / Loại rèm bán nhiều nhất")

import json

product_counts = {}
product_revenue = {}

for _, row in df.iterrows():
    try:
        items = json.loads(row.get("Items", "[]"))
        if not isinstance(items, list):
            continue
        for item in items:
            ten = str(item.get("Ten_SP", "Không rõ")).strip()
            tt  = int(item.get("Thanh_Tien", 0) or 0)
            product_counts[ten]  = product_counts.get(ten, 0) + 1
            product_revenue[ten] = product_revenue.get(ten, 0) + tt
    except:
        continue

if product_counts:
    df_prod = pd.DataFrame({
        "Sản Phẩm":     list(product_counts.keys()),
        "Số lần bán":   list(product_counts.values()),
        "Doanh thu (₫)": [product_revenue[k] for k in product_counts.keys()]
    }).sort_values("Doanh thu (₫)", ascending=False).head(10)

    df_prod["Doanh thu"] = df_prod["Doanh thu (₫)"].apply(lambda x: f"{int(x):,} ₫")
    st.bar_chart(df_prod.set_index("Sản Phẩm")["Doanh thu (₫)"])
    st.dataframe(df_prod[["Sản Phẩm", "Số lần bán", "Doanh thu"]], use_container_width=True, hide_index=True)
else:
    st.info("Không đọc được dữ liệu sản phẩm từ hóa đơn.")

st.markdown("---")

# ── Top khách hàng ────────────────────────────────────────────────────────────
st.subheader("👑 Khách hàng mua nhiều nhất")

df_cust = df.groupby("Ten_KH").agg(
    So_HĐ=("Ma_HD", "count"),
    Tong_Chi=("Tong_Tien", "sum")
).reset_index().sort_values("Tong_Chi", ascending=False).head(10)

df_cust.columns = ["Khách Hàng", "Số Hóa Đơn", "Tổng Chi (₫)"]
df_cust["Tổng Chi"] = df_cust["Tổng Chi (₫)"].apply(lambda x: f"{int(x):,} ₫")
st.dataframe(df_cust[["Khách Hàng", "Số Hóa Đơn", "Tổng Chi"]], use_container_width=True, hide_index=True)

st.markdown("---")

# ── Trạng thái hóa đơn ────────────────────────────────────────────────────────
st.subheader("📊 Trạng thái hóa đơn")
df_tt = df.groupby("Trang_Thai")["Tong_Tien"].agg(["count", "sum"]).reset_index()
df_tt.columns = ["Trạng Thái", "Số HĐ", "Tổng Tiền (₫)"]
df_tt["Tổng Tiền"] = df_tt["Tổng Tiền (₫)"].apply(lambda x: f"{int(x):,} ₫")
st.dataframe(df_tt[["Trạng Thái", "Số HĐ", "Tổng Tiền"]], use_container_width=True, hide_index=True)