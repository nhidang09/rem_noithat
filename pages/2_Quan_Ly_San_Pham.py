import streamlit as st
import pandas as pd
import os

st.title("📦 Quản lý Sản phẩm / Dịch vụ")

FILE_PATH = "data/products.csv"
COLUMNS   = ["Ma_SP", "Ten_SP", "Don_Gia", "Don_Vi", "Ghi_Chu"]

# ── Load ──────────────────────────────────────────────────────────────────────
def load_products():
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) == 0:
        df = pd.DataFrame(columns=COLUMNS)
        os.makedirs("data", exist_ok=True)
        df.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')
        return df
    try:
        df = pd.read_csv(FILE_PATH, encoding='utf-8-sig')
        # Tương thích cột cũ "Don_Gia_Met"
        if "Don_Gia_Met" in df.columns and "Don_Gia" not in df.columns:
            df = df.rename(columns={"Don_Gia_Met": "Don_Gia"})
        return df
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_products(df):
    df.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')

df = load_products()

# ── Tìm kiếm & Hiển thị ───────────────────────────────────────────────────────
search = st.text_input("🔍 Tìm kiếm sản phẩm", placeholder="Tên rèm, loại...")

if search.strip():
    mask = df.astype(str).apply(lambda c: c.str.contains(search.strip(), case=False, na=False)).any(axis=1)
    df_display = df[mask]
else:
    df_display = df

st.subheader(f"Danh sách Sản phẩm ({len(df_display)})")

if df_display.empty:
    st.info("Chưa có sản phẩm nào. Hãy thêm ở bên dưới.")
else:
    df_show = df_display.copy()
    if "Don_Gia" in df_show.columns:
        df_show["Don_Gia"] = pd.to_numeric(df_show["Don_Gia"], errors="coerce").apply(
            lambda x: f"{int(x):,} ₫" if pd.notna(x) else ""
        )
    df_show.columns = ["Mã SP", "Tên Sản Phẩm", "Đơn Giá", "Đơn Vị", "Ghi Chú"] if len(df_show.columns) == 5 else df_show.columns
    st.dataframe(df_show, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Thêm sản phẩm ─────────────────────────────────────────────────────────────
st.subheader("➕ Thêm sản phẩm / Mẫu rèm")
with st.form("add_product_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    ten_sp  = col1.text_input("Tên sản phẩm *", placeholder="Rèm Cầu Vồng, Rèm Cuốn...")
    ma_sp   = col2.text_input("Mã sản phẩm (tự tạo nếu bỏ trống)", placeholder="RV01, RC02...")

    col3, col4 = st.columns(2)
    don_gia = col3.number_input("Đơn giá (VND)", min_value=0, value=550000, step=10000,
                                help="Đơn giá trên mỗi đơn vị (m², mét, bộ)")
    don_vi  = col4.selectbox("Đơn vị tính", ["m²", "mét ngang", "bộ", "cái"])
    ghi_chu = st.text_input("Ghi chú / Mô tả ngắn", placeholder="Loại vải, màu sắc, xuất xứ...")

    submitted = st.form_submit_button("✅ Thêm sản phẩm", type="primary", use_container_width=True)

    if submitted:
        if not ten_sp.strip():
            st.error("⚠️ Vui lòng nhập tên sản phẩm")
        else:
            existing_ids = df["Ma_SP"].astype(str).tolist()
            new_id = ma_sp.strip() if ma_sp.strip() else f"SP{len(df)+1:03d}"
            # Tránh trùng mã
            counter = 1
            original_id = new_id
            while new_id in existing_ids:
                new_id = f"{original_id}_{counter}"
                counter += 1

            new_row = pd.DataFrame([{
                "Ma_SP": new_id,
                "Ten_SP": ten_sp.strip(),
                "Don_Gia": int(don_gia),
                "Don_Vi": don_vi,
                "Ghi_Chu": ghi_chu.strip()
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            save_products(df)
            st.success(f"✅ Đã thêm: **{ten_sp}** — {don_gia:,} ₫/{don_vi}")
            st.rerun()

# ── Sửa / Xóa ─────────────────────────────────────────────────────────────────
if not df.empty:
    st.markdown("---")
    st.subheader("✏️ Sửa / Xóa sản phẩm")

    options = df["Ten_SP"] + " — " + pd.to_numeric(df["Don_Gia"], errors="coerce").apply(
        lambda x: f"{int(x):,} ₫" if pd.notna(x) else "?"
    ) + "/" + df["Don_Vi"]

    selected = st.selectbox("Chọn sản phẩm", options, key="edit_sp_select")
    idx = options[options == selected].index[0]
    row = df.loc[idx]

    with st.form("edit_product_form"):
        c1, c2 = st.columns(2)
        new_ten  = c1.text_input("Tên sản phẩm", value=str(row["Ten_SP"]))
        new_gia  = c2.number_input("Đơn giá", value=int(pd.to_numeric(row["Don_Gia"], errors="coerce") or 0), step=10000)
        c3, c4   = st.columns(2)
        new_dv   = c3.selectbox("Đơn vị", ["m²", "mét ngang", "bộ", "cái"],
                                index=["m²", "mét ngang", "bộ", "cái"].index(row["Don_Vi"])
                                if row["Don_Vi"] in ["m²", "mét ngang", "bộ", "cái"] else 0)
        new_gchu = c4.text_input("Ghi chú", value=str(row["Ghi_Chu"]) if pd.notna(row["Ghi_Chu"]) else "")

        cs, cd = st.columns(2)
        save_btn = cs.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True)
        del_btn  = cd.form_submit_button("🗑️ Xóa sản phẩm", use_container_width=True)

        if save_btn:
            df.loc[idx, "Ten_SP"]  = new_ten.strip()
            df.loc[idx, "Don_Gia"] = int(new_gia)
            df.loc[idx, "Don_Vi"]  = new_dv
            df.loc[idx, "Ghi_Chu"] = new_gchu.strip()
            save_products(df)
            st.success("✅ Đã cập nhật sản phẩm!")
            st.rerun()

        if del_btn:
            st.session_state["pending_delete_sp"] = row["Ma_SP"]

if st.session_state.get("pending_delete_sp"):
    ma = st.session_state["pending_delete_sp"]
    ten = df[df["Ma_SP"] == ma]["Ten_SP"].values[0] if ma in df["Ma_SP"].values else ma
    st.warning(f"⚠️ Xóa sản phẩm **{ten}**?")
    c1, c2 = st.columns(2)
    if c1.button("✅ Xác nhận xóa", type="primary"):
        df = df[df["Ma_SP"] != ma]
        save_products(df)
        del st.session_state["pending_delete_sp"]
        st.success("Đã xóa!")
        st.rerun()
    if c2.button("❌ Hủy"):
        del st.session_state["pending_delete_sp"]
        st.rerun()

st.caption("💡 Đơn giá ở đây dùng làm giá trị mặc định khi tạo hóa đơn — bạn vẫn có thể sửa trực tiếp lúc lập hóa đơn.")