import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.title("👥 Quản lý Khách hàng")

FILE_PATH = "data/customers.csv"
COLUMNS = ["Ma_KH", "Ten_KH", "Dia_Chi", "So_Dien_Thoai", "Email", "Ngay_Tao"]

# ── Load dữ liệu ──────────────────────────────────────────────────────────────
def load_customers():
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) == 0:
        df = pd.DataFrame(columns=COLUMNS)
        os.makedirs("data", exist_ok=True)
        df.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')
        return df
    try:
        return pd.read_csv(FILE_PATH, encoding='utf-8-sig')
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=COLUMNS)

def save_customers(df):
    df.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')

df = load_customers()

# ── Tìm kiếm & Hiển thị ──────────────────────────────────────────────────────
search = st.text_input("🔍 Tìm kiếm theo tên hoặc số điện thoại", placeholder="Nhập tên hoặc SĐT...")

if search.strip():
    mask = df.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
    df_display = df[mask]
else:
    df_display = df

st.subheader(f"Danh sách Khách hàng ({len(df_display)} người)")

if df_display.empty:
    st.info("Chưa có khách hàng nào. Hãy thêm khách hàng ở bên dưới.")
else:
    # Định dạng hiển thị đẹp hơn
    df_show = df_display.copy()
    df_show.columns = ["Mã KH", "Họ & Tên", "Địa Chỉ", "Số ĐT", "Email", "Ngày Tạo"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Thêm khách hàng mới ───────────────────────────────────────────────────────
st.subheader("➕ Thêm khách hàng mới")
with st.form("add_customer_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    ten_kh  = col1.text_input("Họ và tên *", placeholder="Nguyễn Văn A")
    sdt     = col2.text_input("Số điện thoại *", placeholder="0912345678")
    dia_chi = st.text_input("Địa chỉ", placeholder="Số nhà, đường, quận/huyện, tỉnh/thành")
    email   = st.text_input("Email", placeholder="example@gmail.com")

    submitted = st.form_submit_button("✅ Thêm khách hàng", type="primary", use_container_width=True)

    if submitted:
        if not ten_kh.strip() or not sdt.strip():
            st.error("⚠️ Vui lòng nhập ít nhất Họ tên và Số điện thoại")
        elif sdt.strip() in df["So_Dien_Thoai"].astype(str).values:
            st.warning(f"⚠️ Số điện thoại **{sdt}** đã tồn tại trong danh sách!")
        else:
            # Tạo mã KH không trùng dù có xóa bớt
            existing_ids = df["Ma_KH"].astype(str).tolist()
            counter = len(df) + 1
            new_id = f"KH{counter:03d}"
            while new_id in existing_ids:
                counter += 1
                new_id = f"KH{counter:03d}"

            new_row = pd.DataFrame([{
                "Ma_KH": new_id,
                "Ten_KH": ten_kh.strip(),
                "Dia_Chi": dia_chi.strip(),
                "So_Dien_Thoai": sdt.strip(),
                "Email": email.strip(),
                "Ngay_Tao": datetime.now().strftime("%d/%m/%Y")
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            save_customers(df)
            st.success(f"✅ Đã thêm khách hàng **{ten_kh}** ({new_id})")
            st.rerun()

# ── Sửa thông tin khách hàng ──────────────────────────────────────────────────
if not df.empty:
    st.markdown("---")
    st.subheader("✏️ Sửa thông tin khách hàng")

    options = df["Ten_KH"] + " (" + df["So_Dien_Thoai"].astype(str) + ")"
    selected = st.selectbox("Chọn khách hàng cần sửa", options, key="edit_select")
    idx = options[options == selected].index[0]
    row = df.loc[idx]

    with st.form("edit_customer_form"):
        c1, c2 = st.columns(2)
        new_ten  = c1.text_input("Họ và tên", value=str(row["Ten_KH"]))
        new_sdt  = c2.text_input("Số điện thoại", value=str(row["So_Dien_Thoai"]))
        new_addr = st.text_input("Địa chỉ", value=str(row["Dia_Chi"]) if pd.notna(row["Dia_Chi"]) else "")
        new_mail = st.text_input("Email", value=str(row["Email"]) if pd.notna(row["Email"]) else "")

        col_s, col_d = st.columns(2)
        save_edit = col_s.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True)
        del_btn   = col_d.form_submit_button("🗑️ Xóa khách hàng", use_container_width=True)

        if save_edit:
            df.loc[idx, "Ten_KH"] = new_ten.strip()
            df.loc[idx, "So_Dien_Thoai"] = new_sdt.strip()
            df.loc[idx, "Dia_Chi"] = new_addr.strip()
            df.loc[idx, "Email"] = new_mail.strip()
            save_customers(df)
            st.success("✅ Đã cập nhật thông tin!")
            st.rerun()

        if del_btn:
            st.session_state["pending_delete_kh"] = row["Ma_KH"]

# Xác nhận xóa bên ngoài form
if st.session_state.get("pending_delete_kh"):
    ma = st.session_state["pending_delete_kh"]
    ten = df[df["Ma_KH"] == ma]["Ten_KH"].values[0] if ma in df["Ma_KH"].values else ma
    st.warning(f"⚠️ Bạn có chắc muốn xóa khách hàng **{ten}**? Hành động này không thể hoàn tác.")
    c1, c2 = st.columns(2)
    if c1.button("✅ Xác nhận xóa", type="primary"):
        df = df[df["Ma_KH"] != ma]
        save_customers(df)
        del st.session_state["pending_delete_kh"]
        st.success("Đã xóa khách hàng!")
        st.rerun()
    if c2.button("❌ Hủy"):
        del st.session_state["pending_delete_kh"]
        st.rerun()