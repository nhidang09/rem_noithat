import streamlit as st
import pandas as pd
import os, json, uuid
from datetime import datetime
import streamlit.components.v1 as components

st.title("📋 Danh sách Hóa đơn")

FILE_PATH = "data/invoices.csv"

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_invoices():
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(FILE_PATH, encoding='utf-8-sig')
    except:
        return pd.DataFrame()

def save_invoices(df):
    df.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')

def recalc_total(items, dat_coc=0, thue_pct=0, ck_pct=0):
    tong = sum(int(i.get("Thanh_Tien", 0) or 0) for i in items)
    ck   = int(tong * ck_pct / 100)
    thue = int((tong - ck) * thue_pct / 100)
    return tong - ck + thue - int(dat_coc)

def parse_items(raw):
    try:
        items = json.loads(raw)
        return items if isinstance(items, list) else []
    except:
        return []

def load_products():
    try:
        df = pd.read_csv("data/products.csv", encoding='utf-8-sig')
        if "Don_Gia_Met" in df.columns and "Don_Gia" not in df.columns:
            df = df.rename(columns={"Don_Gia_Met": "Don_Gia"})
        return df
    except:
        return pd.DataFrame(columns=["Ma_SP","Ten_SP","Don_Gia","Don_Vi"])

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_invoices()
products_df = load_products()

if df.empty:
    st.warning("Chưa có hóa đơn nào được tạo.")
    st.info("👉 Hãy tạo hóa đơn mới ở trang **Tạo Hóa Đơn Mới**")
    st.stop()

# Session state
for k, v in [("edit_item_idx", None), ("add_item_mode", False), ("pending_delete_hd", None), ("pending_delete_item", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Tìm kiếm & Lọc ───────────────────────────────────────────────────────────
col_s, col_f = st.columns([3, 1])
search    = col_s.text_input("🔍 Tìm theo mã HD hoặc tên khách hàng", placeholder="Tìm kiếm...")
filter_tt = col_f.selectbox("Lọc trạng thái", ["Tất cả", "Chưa thanh toán", "Đã thanh toán", "Hủy"])

df_display = df.copy()
if search.strip():
    mask = df_display.astype(str).apply(lambda c: c.str.contains(search.strip(), case=False, na=False)).any(axis=1)
    df_display = df_display[mask]
if filter_tt != "Tất cả":
    df_display = df_display[df_display["Trang_Thai"].astype(str).str.contains(filter_tt, na=False)]

# ── Metrics ───────────────────────────────────────────────────────────────────
m1, m2, m3 = st.columns(3)
m1.metric("📄 Tổng hóa đơn", len(df))
m2.metric("💰 Tổng doanh thu", f"{pd.to_numeric(df['Tong_Tien'], errors='coerce').sum():,.0f} ₫")
m3.metric("⏳ Chưa thanh toán", len(df[df["Trang_Thai"].astype(str).str.contains("Chưa|lưu", na=False)]))

st.markdown("---")

# ── Bảng danh sách ────────────────────────────────────────────────────────────
show_cols = [c for c in ["Ma_HD","Ngay_Lap","Ten_KH","So_Dien_Thoai","Tong_Tien","Trang_Thai"] if c in df_display.columns]
df_show = df_display[show_cols].copy()
df_show["Tong_Tien"] = pd.to_numeric(df_show["Tong_Tien"], errors="coerce").apply(lambda x: f"{int(x):,} ₫" if pd.notna(x) else "—")
df_show.columns = ["Mã HD","Ngày Lập","Khách Hàng","Số ĐT","Tổng Tiền","Trạng Thái"][:len(show_cols)]
st.dataframe(df_show, use_container_width=True, hide_index=True)
st.caption(f"Hiển thị {len(df_display)} / {len(df)} hóa đơn")

st.markdown("---")

# ── Chọn hóa đơn để làm việc ─────────────────────────────────────────────────
st.subheader("🔎 Chọn hóa đơn để chỉnh sửa")

hd_labels = [f"{r['Ma_HD']} — {r.get('Ten_KH','?')} — {pd.to_numeric(r.get('Tong_Tien',0), errors='coerce'):,.0f} ₫"
             for _, r in df.iterrows()]
hd_list   = df["Ma_HD"].tolist()

sel_label = st.selectbox("Chọn hóa đơn", hd_labels, key="hd_detail_sel")
sel_hd    = hd_list[hd_labels.index(sel_label)]
invoice   = df[df["Ma_HD"] == sel_hd].iloc[0].to_dict()
items     = parse_items(invoice.get("Items", "[]"))

# Đọc các trường điều chỉnh cũ (nếu có)
_dat_coc  = float(invoice.get("Dat_Coc",  0) or 0)
_thue_pct = float(invoice.get("Thue_Pct", 0) or 0)
_ck_pct   = float(invoice.get("Chiet_Khau_Pct", 0) or 0)
_ghi_chu  = str(invoice.get("Ghi_Chu", "") or "")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📋 Thông tin & Trạng thái", "📦 Sản phẩm trong hóa đơn", "🗑️ Xóa hóa đơn"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: THÔNG TIN CƠ BẢN
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    with st.form("edit_invoice_form"):
        c1, c2 = st.columns(2)
        new_ten  = c1.text_input("Tên khách hàng", value=str(invoice.get("Ten_KH", "")))
        new_sdt  = c2.text_input("Số điện thoại",  value=str(invoice.get("So_Dien_Thoai","")).replace(".0",""))
        new_addr = st.text_input("Địa chỉ", value=str(invoice.get("Dia_Chi","")) if pd.notna(invoice.get("Dia_Chi","")) else "")

        c3, c4, c5 = st.columns(3)
        new_coc  = c3.number_input("💵 Đặt cọc (₫)",    min_value=0.0, value=_dat_coc,  step=100000.0)
        new_thue = c4.number_input("📊 Thuế VAT (%)",    min_value=0.0, value=_thue_pct, step=0.5, max_value=100.0)
        new_ck   = c5.number_input("🎁 Chiết khấu (%)", min_value=0.0, value=_ck_pct,   step=0.5, max_value=100.0)

        new_gc = st.text_area("📝 Ghi chú", value=_ghi_chu, height=70)

        tt_opts = ["Chưa thanh toán", "Đã thanh toán", "Hủy"]
        curr_tt = str(invoice.get("Trang_Thai","Chưa thanh toán"))
        tt_idx  = next((i for i, x in enumerate(tt_opts) if x in curr_tt), 0)
        new_tt  = st.selectbox("Trạng thái", tt_opts, index=tt_idx)

        save_btn = st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True)

    if save_btn:
        new_total = recalc_total(items, new_coc, new_thue, new_ck)
        df.loc[df["Ma_HD"]==sel_hd, "Ten_KH"]         = new_ten.strip()
        df.loc[df["Ma_HD"]==sel_hd, "So_Dien_Thoai"]  = new_sdt.strip()
        df.loc[df["Ma_HD"]==sel_hd, "Dia_Chi"]        = new_addr.strip()
        df.loc[df["Ma_HD"]==sel_hd, "Trang_Thai"]     = new_tt
        df.loc[df["Ma_HD"]==sel_hd, "Dat_Coc"]        = int(new_coc)
        df.loc[df["Ma_HD"]==sel_hd, "Thue_Pct"]       = new_thue
        df.loc[df["Ma_HD"]==sel_hd, "Chiet_Khau_Pct"] = new_ck
        df.loc[df["Ma_HD"]==sel_hd, "Ghi_Chu"]        = new_gc.strip()
        df.loc[df["Ma_HD"]==sel_hd, "Tong_Tien"]      = new_total
        save_invoices(df)
        st.success("✅ Đã cập nhật!")
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: SẢN PHẨM — THÊM / SỬA / XÓA TỪNG DÒNG
# ─────────────────────────────────────────────────────────────────────────────
with tab2:

    if not items:
        st.info("Hóa đơn này chưa có sản phẩm nào.")
    else:
        # ── Bảng tổng quan sản phẩm ──────────────────────────────────────────
        st.markdown(f"**{len(items)} hạng mục** trong hóa đơn `{sel_hd}`")

        for idx, it in enumerate(items):
            is_vuong = it.get("Rong") is not None and it.get("Rong") != ""
            if is_vuong:
                dim_str = f"{float(it.get('Rong',0)):.2f} × {float(it.get('Cao',0)):.2f} = {float(it.get('Dien_Tich',0)):.2f} m²"
            else:
                dim_str = f"{float(it.get('So_Met',0) or 0):.2f} m × {it.get('So_Bo',1)} bộ"

            col_info, col_gia, col_btn = st.columns([5, 2, 2])
            with col_info:
                st.markdown(f"**{idx+1}. {it.get('Ten_SP','')}** — {it.get('Vi_Tri','')}")
                st.caption(f"{dim_str} | ĐG: {int(it.get('Don_Gia',0)):,} ₫")
            with col_gia:
                st.markdown(f"<p style='text-align:right; font-weight:700; color:#1e3a8a; margin-top:8px'>{int(it.get('Thanh_Tien',0)):,} ₫</p>", unsafe_allow_html=True)
            with col_btn:
                bcol1, bcol2 = st.columns(2)
                if bcol1.button("✏️", key=f"edit_{idx}", help="Sửa hạng mục này"):
                    st.session_state.edit_item_idx = idx
                    st.session_state.add_item_mode = False
                if bcol2.button("🗑️", key=f"del_{idx}", help="Xóa hạng mục này"):
                    st.session_state.pending_delete_item = idx

            st.divider()

        # Tổng
        tong_hang = int(sum(i.get("Thanh_Tien", 0) or 0 for i in items))
        st.markdown(f"<p style='text-align:right; font-weight:700; font-size:1.1em'>Tổng tiền hàng: {tong_hang:,} ₫</p>", unsafe_allow_html=True)

    # ── Xác nhận xóa dòng ────────────────────────────────────────────────────
    if st.session_state.pending_delete_item is not None:
        del_idx = st.session_state.pending_delete_item
        if del_idx < len(items):
            it_del = items[del_idx]
            st.warning(f"⚠️ Xóa dòng **{it_del.get('Ten_SP','')} — {it_del.get('Vi_Tri','')}** ({int(it_del.get('Thanh_Tien',0)):,} ₫)?")
            dc1, dc2 = st.columns(2)
            if dc1.button("✅ Xác nhận xóa dòng", type="primary"):
                items.pop(del_idx)
                new_total = recalc_total(items, _dat_coc, _thue_pct, _ck_pct)
                df.loc[df["Ma_HD"]==sel_hd, "Items"]     = json.dumps(items, ensure_ascii=False)
                df.loc[df["Ma_HD"]==sel_hd, "Tong_Tien"] = new_total
                save_invoices(df)
                st.session_state.pending_delete_item = None
                st.success("Đã xóa!")
                st.rerun()
            if dc2.button("❌ Hủy xóa"):
                st.session_state.pending_delete_item = None
                st.rerun()

    st.markdown("---")

    # ── FORM SỬA DÒNG ────────────────────────────────────────────────────────
    edit_idx = st.session_state.edit_item_idx
    if edit_idx is not None and edit_idx < len(items):
        it = items[edit_idx]
        st.subheader(f"✏️ Sửa hạng mục #{edit_idx+1}: {it.get('Ten_SP','')}")

        is_vuong_edit = it.get("Rong") is not None and it.get("Rong") != ""

        with st.form("edit_item_form"):
            # Gợi ý sản phẩm
            sp_opts = ["— Nhập tên mới —"] + products_df["Ten_SP"].tolist() if not products_df.empty else ["— Nhập tên mới —"]
            sel_sp  = st.selectbox("Chọn từ danh mục (tùy chọn)", sp_opts, key="edit_sp_sel")
            if sel_sp != "— Nhập tên mới —" and not products_df.empty:
                sp_row = products_df[products_df["Ten_SP"]==sel_sp].iloc[0]
                default_ten_edit = sel_sp
                default_gia_edit = int(pd.to_numeric(sp_row.get("Don_Gia",0), errors="coerce") or 0)
            else:
                default_ten_edit = str(it.get("Ten_SP",""))
                default_gia_edit = int(it.get("Don_Gia", 0) or 0)

            ec1, ec2 = st.columns(2)
            e_ten   = ec1.text_input("Tên sản phẩm *", value=default_ten_edit)
            e_vitri = ec2.text_input("Vị trí *",        value=str(it.get("Vi_Tri","")))

            e_loai = st.radio("Loại tính", ["Mét vuông (Rộng × Cao)", "Mét ngang"],
                              index=0 if is_vuong_edit else 1, horizontal=True, key="edit_loai")

            if e_loai == "Mét vuông (Rộng × Cao)":
                ef1, ef2, ef3 = st.columns(3)
                e_rong = ef1.number_input("Rộng (m)", value=float(it.get("Rong") or 1.0), step=0.01, min_value=0.0)
                e_cao  = ef2.number_input("Cao (m)",  value=float(it.get("Cao")  or 1.0), step=0.01, min_value=0.0)
                e_sobo = ef3.number_input("Số bộ",    value=int(it.get("So_Bo",1)),        step=1,    min_value=1)
                e_dt   = round(e_rong * e_cao * e_sobo, 2)
                e_dv   = "m²"; e_somet = None
            else:
                ef1, ef2 = st.columns(2)
                e_somet = ef1.number_input("Số mét ngang", value=float(it.get("So_Met") or 1.0), step=0.1, min_value=0.0)
                e_sobo  = ef2.number_input("Số bộ",        value=int(it.get("So_Bo",1)),          step=1,   min_value=1)
                e_dt    = round(e_somet * e_sobo, 2)
                e_dv    = "m"; e_rong = None; e_cao = None

            e_gia = st.number_input("Đơn giá (₫)", value=default_gia_edit, step=10000, min_value=0)
            e_tt  = int(e_dt * e_gia)
            st.info(f"📐 Diện tích: {e_dt:.2f} {e_dv} | 💵 Thành tiền: **{e_tt:,} ₫**")

            sb1, sb2 = st.columns(2)
            save_item = sb1.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True)
            cancel    = sb2.form_submit_button("❌ Hủy", use_container_width=True)

        if save_item:
            if not e_ten.strip() or not e_vitri.strip():
                st.error("Vui lòng nhập tên sản phẩm và vị trí")
            else:
                items[edit_idx].update({
                    "Ten_SP":     e_ten.strip(),
                    "Vi_Tri":     e_vitri.strip(),
                    "Don_Vi":     e_dv,
                    "Rong":       e_rong,
                    "Cao":        e_cao,
                    "So_Met":     e_somet,
                    "Dien_Tich":  e_dt,
                    "So_Bo":      int(e_sobo),
                    "Don_Gia":    int(e_gia),
                    "Thanh_Tien": e_tt,
                })
                new_total = recalc_total(items, _dat_coc, _thue_pct, _ck_pct)
                df.loc[df["Ma_HD"]==sel_hd, "Items"]     = json.dumps(items, ensure_ascii=False)
                df.loc[df["Ma_HD"]==sel_hd, "Tong_Tien"] = new_total
                save_invoices(df)
                st.session_state.edit_item_idx = None
                st.success(f"✅ Đã cập nhật: {e_ten} — {e_vitri}")
                st.rerun()
        if cancel:
            st.session_state.edit_item_idx = None
            st.rerun()

    # ── FORM THÊM DÒNG MỚI ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("➕ Thêm hạng mục mới vào hóa đơn này", expanded=st.session_state.add_item_mode):
        sp_opts2 = ["— Nhập tên mới —"] + products_df["Ten_SP"].tolist() if not products_df.empty else ["— Nhập tên mới —"]
        sel_sp2  = st.selectbox("Chọn từ danh mục (tùy chọn)", sp_opts2, key="add_sp_sel2")
        if sel_sp2 != "— Nhập tên mới —" and not products_df.empty:
            sp_row2 = products_df[products_df["Ten_SP"]==sel_sp2].iloc[0]
            def2_ten = sel_sp2
            def2_gia = int(pd.to_numeric(sp_row2.get("Don_Gia",550000), errors="coerce") or 550000)
        else:
            def2_ten = ""; def2_gia = 550000

        with st.form("add_item_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            a_ten   = ac1.text_input("Tên sản phẩm *", value=def2_ten, placeholder="Rèm cuốn, Rèm cầu vồng...")
            a_vitri = ac2.text_input("Vị trí *", placeholder="Tầng 1, Phòng khách...")

            a_loai = st.radio("Loại tính", ["Mét vuông (Rộng × Cao)", "Mét ngang"], horizontal=True, key="add_loai")

            if a_loai == "Mét vuông (Rộng × Cao)":
                af1, af2, af3 = st.columns(3)
                a_rong = af1.number_input("Rộng (m)", value=1.0, step=0.01, min_value=0.0, key="a_rong")
                a_cao  = af2.number_input("Cao (m)",  value=1.0, step=0.01, min_value=0.0, key="a_cao")
                a_sobo = af3.number_input("Số bộ",    value=1,   step=1,    min_value=1,   key="a_sobo")
                a_dt   = round(a_rong * a_cao * a_sobo, 2)
                a_dv   = "m²"; a_somet = None; a_r = a_rong; a_c = a_cao
            else:
                af1, af2 = st.columns(2)
                a_somet = af1.number_input("Số mét ngang", value=1.0, step=0.1, min_value=0.0, key="a_somet")
                a_sobo  = af2.number_input("Số bộ",        value=1,   step=1,   min_value=1,   key="a_sobo2")
                a_dt    = round(a_somet * a_sobo, 2)
                a_dv    = "m"; a_r = None; a_c = None

            a_gia = st.number_input("Đơn giá (₫)", value=def2_gia, step=10000, min_value=0, key="a_gia")
            a_tt  = int(a_dt * a_gia)
            st.info(f"📐 Diện tích: {a_dt:.2f} {a_dv} | 💵 Thành tiền: **{a_tt:,} ₫**")

            add_btn = st.form_submit_button("➕ Thêm vào hóa đơn", type="primary", use_container_width=True)

        if add_btn:
            if not a_ten.strip() or not a_vitri.strip():
                st.error("Vui lòng nhập tên sản phẩm và vị trí")
            else:
                new_item = {
                    "id":         str(uuid.uuid4())[:8],
                    "Ten_SP":     a_ten.strip(),
                    "Vi_Tri":     a_vitri.strip(),
                    "Don_Vi":     a_dv,
                    "Rong":       a_r,
                    "Cao":        a_c,
                    "So_Met":     a_somet,
                    "Dien_Tich":  a_dt,
                    "So_Bo":      int(a_sobo),
                    "Don_Gia":    int(a_gia),
                    "Thanh_Tien": a_tt,
                }
                items.append(new_item)
                new_total = recalc_total(items, _dat_coc, _thue_pct, _ck_pct)
                df.loc[df["Ma_HD"]==sel_hd, "Items"]     = json.dumps(items, ensure_ascii=False)
                df.loc[df["Ma_HD"]==sel_hd, "Tong_Tien"] = new_total
                save_invoices(df)
                st.success(f"✅ Đã thêm: {a_ten} — {a_vitri} → {a_tt:,} ₫")
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: XÓA HÓA ĐƠN
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.warning(f"Bạn đang chuẩn bị xóa hóa đơn **{sel_hd}** của khách **{invoice.get('Ten_KH','?')}**.")
    st.error("⚠️ Hành động này **không thể hoàn tác**. Toàn bộ dữ liệu hóa đơn sẽ bị xóa vĩnh viễn.")

    if st.button(f"🗑️ Xóa hóa đơn {sel_hd}", type="secondary"):
        st.session_state.pending_delete_hd = sel_hd

    if st.session_state.pending_delete_hd:
        hd_del = st.session_state.pending_delete_hd
        st.markdown("**Nhập mã hóa đơn để xác nhận:**")
        confirm_input = st.text_input("", placeholder=f"Gõ: {hd_del}", key="confirm_del_input")
        c1, c2 = st.columns(2)
        if c1.button("✅ Xác nhận xóa vĩnh viễn", type="primary", disabled=(confirm_input != hd_del)):
            df = df[df["Ma_HD"] != hd_del]
            save_invoices(df)
            st.session_state.pending_delete_hd = None
            st.success("Đã xóa hóa đơn!")
            st.rerun()
        if c2.button("❌ Hủy"):
            st.session_state.pending_delete_hd = None
            st.rerun()