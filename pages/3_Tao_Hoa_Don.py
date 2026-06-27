import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import os

# ── KHÔNG gọi set_page_config ở đây (chỉ gọi trong main.py) ──────────────────

st.title("📄 Tạo Hóa Đơn Mới")

# ── Session State ─────────────────────────────────────────────────────────────
for key, default in [
    ("invoice_items", []),
    ("current_invoice_id", None),
    ("current_customer", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Load dữ liệu (không cache để luôn fresh) ──────────────────────────────────
def load_customers():
    try:
        return pd.read_csv("data/customers.csv", encoding='utf-8-sig')
    except:
        return pd.DataFrame(columns=["Ma_KH", "Ten_KH", "Dia_Chi", "So_Dien_Thoai"])

def load_products():
    try:
        df = pd.read_csv("data/products.csv", encoding='utf-8-sig')
        if "Don_Gia_Met" in df.columns and "Don_Gia" not in df.columns:
            df = df.rename(columns={"Don_Gia_Met": "Don_Gia"})
        return df
    except:
        return pd.DataFrame(columns=["Ma_SP", "Ten_SP", "Don_Gia", "Don_Vi"])

customers_df = load_customers()
products_df  = load_products()

# Tạo mã hóa đơn nếu chưa có
if not st.session_state.current_invoice_id:
    st.session_state.current_invoice_id = "HD" + datetime.now().strftime("%Y%m%d-%H%M%S")

st.caption(f"🔖 Mã hóa đơn: **{st.session_state.current_invoice_id}**  |  📅 Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.markdown("---")

# ── PHẦN 1: THÔNG TIN KHÁCH HÀNG ─────────────────────────────────────────────
st.subheader("👤 Thông tin khách hàng")

# Chọn từ danh sách
if not customers_df.empty:
    cust_opts = ["— Nhập mới —"] + customers_df["Ten_KH"].tolist()
    sel_cust  = st.selectbox("Chọn từ danh sách khách hàng", cust_opts, key="cust_select")

    if sel_cust != "— Nhập mới —":
        info = customers_df[customers_df["Ten_KH"] == sel_cust].iloc[0]
        st.session_state.current_customer = info.to_dict()
    elif sel_cust == "— Nhập mới —" and st.session_state.current_customer:
        # Chỉ reset nếu người dùng chủ động chọn "Nhập mới"
        pass
else:
    st.info("Chưa có khách hàng. Nhập trực tiếp hoặc vào trang Quản lý Khách hàng để thêm.")

# Fields nhập thông tin
col1, col2 = st.columns(2)
ten_kh = col1.text_input(
    "Tên khách hàng *",
    value=st.session_state.current_customer.get("Ten_KH", "") if st.session_state.current_customer else "",
    key="inp_ten_kh"
)
sdt = col2.text_input(
    "Số điện thoại",
    value=str(st.session_state.current_customer.get("So_Dien_Thoai", "")).replace(".0","") if st.session_state.current_customer else "",
    key="inp_sdt"
)
dia_chi = st.text_input(
    "Địa chỉ",
    value=st.session_state.current_customer.get("Dia_Chi", "") if st.session_state.current_customer else "",
    key="inp_dia_chi"
)

st.markdown("---")

# ── PHẦN 2: THÊM SẢN PHẨM VÀO HÓA ĐƠN ──────────────────────────────────────
st.subheader("➕ Thêm sản phẩm vào hóa đơn")

col_a, col_b = st.columns([1, 1])

with col_a:
    # Gợi ý từ danh mục sản phẩm
    sp_opts = ["— Nhập tên mới —"] + products_df["Ten_SP"].tolist() if not products_df.empty else ["— Nhập tên mới —"]
    sel_sp  = st.selectbox("Chọn từ danh mục sản phẩm", sp_opts, key="sel_sp")

    # Tự điền tên và đơn giá nếu chọn từ danh mục
    if sel_sp != "— Nhập tên mới —" and not products_df.empty:
        sp_row = products_df[products_df["Ten_SP"] == sel_sp].iloc[0]
        default_ten = sel_sp
        default_gia = int(pd.to_numeric(sp_row.get("Don_Gia", 550000), errors="coerce") or 550000)
    else:
        default_ten = ""
        default_gia = 550000

    ten_sp  = st.text_input("Tên sản phẩm *", value=default_ten, key="inp_ten_sp",
                            placeholder="Rèm Cầu Vồng, Rèm Cuốn...")
    vi_tri  = st.text_input("Vị trí *", key="inp_vi_tri",
                            placeholder="Tầng 1, Phòng khách, Cửa sổ trước...")

with col_b:
    don_gia = st.number_input("Đơn giá (VND)", min_value=0, value=default_gia,
                              step=10000, key="inp_don_gia")
    loai_tinh = st.radio("Loại tính toán", ["Mét vuông (Rộng × Cao)", "Mét ngang"],
                         horizontal=True, key="loai_tinh")

# Input kích thước tùy loại
if loai_tinh == "Mét vuông (Rộng × Cao)":
    c1, c2, c3 = st.columns(3)
    rong    = c1.number_input("Rộng (m)", min_value=0.0, value=1.0, step=0.01, key="inp_rong")
    cao     = c2.number_input("Cao (m)",  min_value=0.0, value=1.0, step=0.01, key="inp_cao")
    so_bo   = c3.number_input("Số bộ",    min_value=1,   value=1,   step=1,    key="inp_so_bo")
    dien_tich = round(rong * cao * so_bo, 2)
    don_vi  = "m²"
    so_met  = None
    st.caption(f"📐 Diện tích: {rong} × {cao} × {so_bo} bộ = **{dien_tich:.2f} m²**")
else:
    c1, c2 = st.columns(2)
    so_met  = c1.number_input("Số mét ngang", min_value=0.0, value=1.0, step=0.1, key="inp_so_met")
    so_bo   = c2.number_input("Số bộ",        min_value=1,   value=1,   step=1,   key="inp_so_bo2")
    dien_tich = round(so_met * so_bo, 2)
    don_vi  = "m"
    rong = cao = None
    st.caption(f"📐 Tổng mét: {so_met} × {so_bo} bộ = **{dien_tich:.2f} m**")

thanh_tien = int(dien_tich * don_gia)
st.info(f"💵 Thành tiền ước tính: **{thanh_tien:,} ₫**")

if st.button("➕ Thêm vào hóa đơn", type="primary", use_container_width=True):
    if not ten_sp.strip():
        st.error("⚠️ Vui lòng nhập tên sản phẩm")
    elif not vi_tri.strip():
        st.error("⚠️ Vui lòng nhập vị trí")
    else:
        new_item = {
            "id":         str(uuid.uuid4())[:8],
            "Ten_SP":     ten_sp.strip(),
            "Vi_Tri":     vi_tri.strip(),
            "Don_Vi":     don_vi,
            "Rong":       rong,
            "Cao":        cao,
            "So_Met":     so_met,
            "Dien_Tich":  dien_tich,
            "So_Bo":      int(so_bo),
            "Don_Gia":    int(don_gia),
            "Thanh_Tien": thanh_tien,
        }
        st.session_state.invoice_items.append(new_item)
        st.success(f"✅ Đã thêm: {ten_sp} — {vi_tri} → {thanh_tien:,} ₫")
        st.rerun()

st.markdown("---")

# ── PHẦN 3: BẢNG SẢN PHẨM TRONG HÓA ĐƠN ─────────────────────────────────────
st.subheader("📋 Sản phẩm trong hóa đơn")

if not st.session_state.invoice_items:
    st.info("Chưa có sản phẩm nào. Hãy thêm ở trên.")
else:
    df_items = pd.DataFrame(st.session_state.invoice_items)
    grand_total = 0

    # Hiển thị theo nhóm sản phẩm
    for ten, group in df_items.groupby("Ten_SP", sort=False):
        with st.expander(f"**{ten}** — {len(group)} hạng mục", expanded=True):
            is_vuong = group["Rong"].notna().any()

            if is_vuong:
                cols_show = ["Vi_Tri", "Rong", "Cao", "Dien_Tich", "So_Bo", "Don_Gia", "Thanh_Tien"]
                col_names = ["Vị Trí", "Rộng (m)", "Cao (m)", "DT (m²)", "Số Bộ", "Đơn Giá", "Thành Tiền"]
            else:
                cols_show = ["Vi_Tri", "So_Met", "Dien_Tich", "So_Bo", "Don_Gia", "Thanh_Tien"]
                col_names = ["Vị Trí", "Số Mét", "Tổng Mét", "Số Bộ", "Đơn Giá", "Thành Tiền"]

            disp = group[cols_show].copy()
            for c in ["Rong", "Cao", "Dien_Tich", "So_Met"]:
                if c in disp.columns:
                    disp[c] = disp[c].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
            disp["Don_Gia"]    = disp["Don_Gia"].apply(lambda x: f"{int(x):,}")
            disp["Thanh_Tien"] = disp["Thanh_Tien"].apply(lambda x: f"{int(x):,}")
            disp.columns = col_names
            st.dataframe(disp, use_container_width=True, hide_index=True)

            subtotal = int(group["Thanh_Tien"].sum())
            grand_total += subtotal
            st.markdown(f"<p style='text-align:right; font-weight:600; color:#1e3a8a;'>Cộng: {subtotal:,} ₫</p>",
                        unsafe_allow_html=True)

    # Tổng cộng
    st.markdown(f"""
    <div style='background:#1e3a8a; color:white; border-radius:10px; padding:16px 20px; margin-top:8px; display:flex; justify-content:space-between; align-items:center;'>
        <span style='font-size:1.1em; font-weight:600;'>💰 TỔNG TIỀN HÓA ĐƠN</span>
        <span style='font-size:1.6em; font-weight:700;'>{grand_total:,} ₫</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # Nút xóa từng item
    with st.expander("🗑️ Xóa hạng mục"):
        item_opts = [f"{it['Vi_Tri']} — {it['Ten_SP']} ({it['Thanh_Tien']:,} ₫)"
                     for it in st.session_state.invoice_items]
        del_item = st.selectbox("Chọn hạng mục cần xóa", item_opts, key="del_item_sel")
        if st.button("Xóa hạng mục đã chọn", type="secondary"):
            idx_del = item_opts.index(del_item)
            st.session_state.invoice_items.pop(idx_del)
            st.rerun()

st.markdown("---")

# ── PHẦN 3B: ĐIỀU CHỈNH HÓA ĐƠN ─────────────────────────────────────────────
st.subheader("🧾 Điều chỉnh hóa đơn")
st.caption("Bỏ trống nếu không áp dụng — sẽ không hiển thị trên hóa đơn in")

adj_col1, adj_col2, adj_col3 = st.columns(3)

with adj_col1:
    dat_coc = st.number_input(
        "💵 Đã đặt cọc (₫)",
        min_value=0, value=0, step=100000,
        key="inp_dat_coc",
        help="Số tiền khách đã đặt cọc — sẽ trừ vào tổng thanh toán"
    )

with adj_col2:
    thue_pct = st.number_input(
        "📊 Thuế VAT (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key="inp_thue_pct",
        help="Nhập % thuế nếu có. Ví dụ: 10 = 10% VAT"
    )

with adj_col3:
    chiet_khau_pct = st.number_input(
        "🎁 Chiết khấu (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key="inp_ck_pct",
        help="Giảm giá theo % trên tổng tiền hàng"
    )

ghi_chu = st.text_area(
    "📝 Ghi chú / Điều khoản",
    placeholder="Ví dụ: Bảo hành 12 tháng. Thanh toán còn lại khi giao hàng. Liên hệ: 0xxx xxx xxx",
    key="inp_ghi_chu",
    height=80
)

# Tính toán các khoản điều chỉnh
if st.session_state.invoice_items:
    _tong_hang = int(sum(i["Thanh_Tien"] for i in st.session_state.invoice_items))
    _chiet_khau_tien = int(_tong_hang * chiet_khau_pct / 100) if chiet_khau_pct > 0 else 0
    _sau_ck = _tong_hang - _chiet_khau_tien
    _thue_tien = int(_sau_ck * thue_pct / 100) if thue_pct > 0 else 0
    _con_lai = _sau_ck + _thue_tien - int(dat_coc)

    # Hiển thị bảng tổng kết nhỏ nếu có điều chỉnh
    if chiet_khau_pct > 0 or thue_pct > 0 or dat_coc > 0:
        ck_row = f"<div style='display:flex;justify-content:space-between;margin-bottom:5px;'><span style='color:#64748b'>Chiết khấu ({chiet_khau_pct:g}%):</span><span style='color:#ef4444;font-weight:600'>- {_chiet_khau_tien:,} ₫</span></div>" if chiet_khau_pct > 0 else ""
        thue_row = f"<div style='display:flex;justify-content:space-between;margin-bottom:5px;'><span style='color:#64748b'>Thuế VAT ({thue_pct:g}%):</span><span style='color:#f59e0b;font-weight:600'>+ {_thue_tien:,} ₫</span></div>" if thue_pct > 0 else ""
        coc_row = f"<div style='display:flex;justify-content:space-between;margin-bottom:5px;'><span style='color:#64748b'>Đã đặt cọc:</span><span style='color:#10b981;font-weight:600'>- {int(dat_coc):,} ₫</span></div>" if dat_coc > 0 else ""
        st.markdown(f"""
        <div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px; margin-top:8px;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                <span style='color:#64748b'>Tổng tiền hàng:</span>
                <span style='font-weight:600'>{_tong_hang:,} ₫</span>
            </div>
            {ck_row}{thue_row}{coc_row}
            <div style='display:flex; justify-content:space-between; border-top:2px solid #1e3a8a; padding-top:8px; margin-top:4px;'>
                <span style='font-weight:700; color:#1e3a8a; font-size:1.05em;'>💰 Còn lại phải thanh toán:</span>
                <span style='font-weight:800; color:#1e3a8a; font-size:1.2em;'>{_con_lai:,} ₫</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── PHẦN 4: LƯU & IN ─────────────────────────────────────────────────────────
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    if st.button("💾 LƯU HÓA ĐƠN", type="primary", use_container_width=True):
        if not st.session_state.invoice_items:
            st.error("⚠️ Hóa đơn chưa có sản phẩm!")
        elif not ten_kh.strip():
            st.error("⚠️ Vui lòng nhập tên khách hàng!")
        else:
            items_list = st.session_state.invoice_items
            tong_hang  = int(sum(i["Thanh_Tien"] for i in items_list))
            ck_tien    = int(tong_hang * chiet_khau_pct / 100) if chiet_khau_pct > 0 else 0
            thue_tien  = int((tong_hang - ck_tien) * thue_pct / 100) if thue_pct > 0 else 0
            total      = tong_hang - ck_tien + thue_tien - int(dat_coc)

            invoice_row = {
                "Ma_HD":          st.session_state.current_invoice_id,
                "Ngay_Lap":       datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Ten_KH":         ten_kh.strip(),
                "Dia_Chi":        dia_chi.strip(),
                "So_Dien_Thoai":  sdt.strip(),
                "Tong_Tien":      total,
                "Dat_Coc":        int(dat_coc),
                "Thue_Pct":       thue_pct,
                "Chiet_Khau_Pct": chiet_khau_pct,
                "Ghi_Chu":        ghi_chu.strip(),
                "Trang_Thai":     "Chưa thanh toán",
                "Items":          json.dumps(items_list, ensure_ascii=False),
            }

            inv_path = "data/invoices.csv"
            try:
                df_inv = pd.read_csv(inv_path, encoding='utf-8-sig')
            except:
                df_inv = pd.DataFrame(columns=invoice_row.keys())

            # Nếu đã tồn tại mã này thì cập nhật, không thêm trùng
            if invoice_row["Ma_HD"] in df_inv["Ma_HD"].values:
                for k, v in invoice_row.items():
                    df_inv.loc[df_inv["Ma_HD"] == invoice_row["Ma_HD"], k] = v
            else:
                df_inv = pd.concat([df_inv, pd.DataFrame([invoice_row])], ignore_index=True)

            df_inv.to_csv(inv_path, index=False, encoding='utf-8-sig')
            st.success(f"✅ Đã lưu hóa đơn **{invoice_row['Ma_HD']}** — Tổng: **{total:,} ₫**")
            st.balloons()

with col_s2:
    if st.button("🖨️ XEM & IN HÓA ĐƠN", use_container_width=True):
        st.session_state["show_preview"] = True

with col_s3:
    if st.button("🔄 Tạo hóa đơn mới", use_container_width=True):
        st.session_state.invoice_items = []
        st.session_state.current_invoice_id = None
        st.session_state.current_customer = None
        st.session_state["show_preview"] = False
        st.rerun()

# ── PHẦN 5: XEM HÓA ĐƠN ĐẦY ĐỦ ──────────────────────────────────────────────
import streamlit.components.v1 as components

def build_group_table(group_df, ten_sp, is_met_vuong):
    """Tạo HTML bảng cho 1 nhóm sản phẩm theo đúng mẫu."""
    title = ten_sp.upper()

    if is_met_vuong:
        # Bảng mét vuông: STT | Vị trí | Rộng (m) | Cao (m) | Số lượng (m²) | Số lượng (bộ) | Đơn giá/m² | Thành tiền
        header = """
        <tr>
          <th style="width:5%">STT</th>
          <th style="width:20%; text-align:center">VỊ TRÍ</th>
          <th style="width:11%">RỘNG (MÉT)</th>
          <th style="width:11%">CAO (MÉT)</th>
          <th style="width:13%">SỐ LƯỢNG (MÉT VUÔNG)</th>
          <th style="width:11%">SỐ LƯỢNG (BỘ)</th>
          <th style="width:15%">ĐƠN GIÁ/ MÉT VUÔNG</th>
          <th style="width:14%">THÀNH TIỀN</th>
        </tr>"""
        rows = ""
        for i, (_, r) in enumerate(group_df.iterrows()):
            bg = "#f0f4ff" if i % 2 == 1 else "white"
            rows += f"""
            <tr style="background:{bg}">
              <td style="text-align:center">{i+1}</td>
              <td style="text-align:center; padding-left:8px">{r['Vi_Tri']}</td>
              <td>{float(r['Rong']):.2f}</td>
              <td>{float(r['Cao']):.2f}</td>
              <td>{float(r['Dien_Tich']):.2f}</td>
              <td>{int(r['So_Bo'])}</td>
              <td>{int(r['Don_Gia']):,}</td>
              <td style="font-weight:700; color:#1e3a8a">{int(r['Thanh_Tien']):,}</td>
            </tr>"""
    else:
        # Bảng mét ngang: STT | Vị trí | ĐVT | Số lượng (mét) | Số lượng (bộ) | Đơn giá/mét | Thành tiền
        header = """
        <tr>
          <th style="width:5%">STT</th>
          <th style="width:25%; text-align:center">VỊ TRÍ</th>
          <th style="width:12%">ĐVT</th>
          <th style="width:15%">SỐ LƯỢNG (MÉT)</th>
          <th style="width:13%">SỐ LƯỢNG (BỘ)</th>
          <th style="width:16%">ĐƠN GIÁ/ MÉT</th>
          <th style="width:14%">THÀNH TIỀN</th>
        </tr>"""
        rows = ""
        for i, (_, r) in enumerate(group_df.iterrows()):
            bg = "#f0f4ff" if i % 2 == 1 else "white"
            rows += f"""
            <tr style="background:{bg}">
              <td style="text-align:center">{i+1}</td>
              <td style="text-align:center; padding-left:8px">{r['Vi_Tri']}</td>
              <td>mét ngang</td>
              <td>{float(r['So_Met']):.2f}</td>
              <td>{int(r['So_Bo'])}</td>
              <td>{int(r['Don_Gia']):,}</td>
              <td style="font-weight:700; color:#1e3a8a">{int(r['Thanh_Tien']):,}</td>
            </tr>"""

    subtotal = int(group_df['Thanh_Tien'].sum())
    return f"""
    <div class="group-block">
      <div class="group-title">{title}</div>
      <table class="items-table">
        <thead>{header}</thead>
        <tbody>{rows}</tbody>
      </table>
      <div class="group-subtotal">Cộng {ten_sp}: {subtotal:,} ₫</div>
    </div>"""


if st.session_state.get("show_preview") and st.session_state.invoice_items:
    st.markdown("---")

    if not ten_kh.strip():
        st.error("⚠️ Vui lòng nhập tên khách hàng trước khi xem hóa đơn")
    else:
        df_prev = pd.DataFrame(st.session_state.invoice_items)
        grand   = int(df_prev["Thanh_Tien"].sum())
        ma_hd   = st.session_state.current_invoice_id
        ngay_in = datetime.now().strftime('%d/%m/%Y %H:%M')
        sdt_hien = sdt.strip() if sdt.strip() else "—"
        dia_hien = dia_chi.strip() if dia_chi.strip() else "—"

        # Tính các khoản điều chỉnh
        _ck_tien   = int(grand * chiet_khau_pct / 100) if chiet_khau_pct > 0 else 0
        _sau_ck    = grand - _ck_tien
        _thue_tien = int(_sau_ck * thue_pct / 100) if thue_pct > 0 else 0
        _con_lai   = _sau_ck + _thue_tien - int(dat_coc)

        # Build HTML bảng tổng kết — chỉ hiển thị dòng nào có giá trị
        tong_ket_rows = f"""
        <tr>
          <td style="text-align:center; color:#475569">Tổng tiền hàng:</td>
          <td style="text-align:right; font-weight:600">{grand:,} ₫</td>
        </tr>"""
        if chiet_khau_pct > 0:
            tong_ket_rows += f"""
        <tr>
          <td style="text-align:center; color:#ef4444">Chiết khấu ({chiet_khau_pct:g}%):</td>
          <td style="text-align:right; color:#ef4444; font-weight:600">- {_ck_tien:,} ₫</td>
        </tr>"""
        if thue_pct > 0:
            tong_ket_rows += f"""
        <tr>
          <td style="text-align:center; color:#f59e0b">Thuế VAT ({thue_pct:g}%):</td>
          <td style="text-align:right; color:#f59e0b; font-weight:600">+ {_thue_tien:,} ₫</td>
        </tr>"""
        if dat_coc > 0:
            tong_ket_rows += f"""
        <tr>
          <td style="text-align:center; color:#10b981">Đã đặt cọc:</td>
          <td style="text-align:right; color:#10b981; font-weight:600">- {int(dat_coc):,} ₫</td>
        </tr>"""

        # Dòng "còn lại" chỉ hiện nếu có điều chỉnh; nếu không thì chỉ hiện tổng đơn giản
        has_adj = chiet_khau_pct > 0 or thue_pct > 0 or dat_coc > 0
        if has_adj:
            final_label = "Còn lại phải thanh toán:"
            final_amount = _con_lai
        else:
            final_label = "TỔNG TIỀN THANH TOÁN:"
            final_amount = grand

        # HTML ghi chú (chỉ hiện nếu có)
        ghi_chu_html = ""
        if ghi_chu.strip():
            ghi_chu_html = f"""
  <div style="margin-top:14px; padding:10px 14px; background:#fffbeb;
              border-left:3px solid #f59e0b; border-radius:4px; font-size:0.82em; color:#78350f;">
    <strong>Ghi chú:</strong> {ghi_chu.strip()}
  </div>"""

        # Build từng bảng nhóm
        all_groups_html = ""
        for ten_sp, group in df_prev.groupby("Ten_SP", sort=False):
            is_met_vuong = group["Rong"].notna().any()
            all_groups_html += build_group_table(group, ten_sp, is_met_vuong)

        # HTML đầy đủ — dùng UTF-8 thực, KHÔNG dùng HTML entities để tránh lỗi font
        full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Be Vietnam Pro', Arial, sans-serif;
    background: #f1f5f9;
    padding: 20px;
    font-size: 13px;
  }}
  .invoice {{
    max-width: 800px;
    margin: 0 auto;
    background: white;
    border: 2px solid #1e3a8a;
    border-radius: 10px;
    padding: 28px 36px 32px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  }}
  /* ── Header ── */
  .header {{
    text-align: center;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 12px;
    margin-bottom: 14px;
  }}
  .header .logo-row {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 2px;
  }}
  .header h1 {{
    color: #1e3a8a;
    font-size: 1.75em;
    font-weight: 800;
    letter-spacing: 1px;
  }}
  .header .sub {{
    color: #64748b;
    font-size: 0.82em;
    margin-bottom: 6px;
  }}
  .header h2 {{
    color: #334155;
    font-size: 1.05em;
    font-weight: 700;
    letter-spacing: 0.5px;
  }}
  /* ── Meta ── */
  .meta-row {{
    display: flex;
    justify-content: space-between;
    font-size: 0.88em;
    margin-bottom: 10px;
    color: #334155;
  }}
  /* ── Khách hàng ── */
  .customer-box {{
    background: #eff6ff;
    border-left: 4px solid #1e3a8a;
    padding: 9px 14px;
    border-radius: 4px;
    margin-bottom: 18px;
    font-size: 0.88em;
    line-height: 1.8;
  }}
  .customer-box strong {{ color: #1e3a8a; }}
  /* ── Nhóm sản phẩm ── */
  .group-block {{ margin-bottom: 18px; }}
  .group-title {{
    background: #334155;
    color: white;
    font-weight: 700;
    font-size: 0.9em;
    letter-spacing: 0.5px;
    padding: 6px 12px;
    border-radius: 4px 4px 0 0;
  }}
  .group-subtotal {{
    text-align: right;
    font-size: 0.85em;
    font-weight: 600;
    color: #1e3a8a;
    padding: 5px 4px 0;
    border-top: 1px dashed #cbd5e1;
    margin-top: 2px;
  }}
  /* ── Bảng sản phẩm ── */
  .items-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
  }}
  .items-table thead tr {{
    background: #1e3a8a;
    color: white;
  }}
  .items-table thead th {{
    padding: 7px 5px;
    text-align: center;
    font-weight: 600;
    font-size: 0.82em;
    letter-spacing: 0.2px;
    border: 1px solid #1e40af;
  }}
  .items-table tbody td {{
    padding: 7px 5px;
    text-align: center;
    border: 1px solid #e2e8f0;
    color: #1e293b;
  }}
  /* ── Tổng tiền ── */
  .total-box {{
    text-align: right;
    border-top: 2px solid #1e3a8a;
    padding-top: 12px;
    margin-top: 6px;
    margin-bottom: 28px;
  }}
  .total-label {{
    font-size: 0.95em;
    font-weight: 700;
    color: #334155;
    letter-spacing: 0.3px;
  }}
  .total-amount {{
    font-size: 1.55em;
    font-weight: 800;
    color: #1e3a8a;
    display: block;
    margin-top: 2px;
  }}
  /* ── Chữ ký ── */
  .sig-row {{
    display: flex;
    justify-content: space-between;
  }}
  .sig-box {{
    width: 44%;
    text-align: center;
  }}
  .sig-box .sig-label {{
    font-style: italic;
    color: #64748b;
    font-size: 0.85em;
    margin-bottom: 36px;
  }}
  .sig-box .sig-name {{
    border-top: 1px solid #94a3b8;
    padding-top: 5px;
    font-weight: 700;
    font-size: 0.9em;
    color: #1e293b;
  }}
  /* ── Bảng tổng kết ── */
  .summary-table {{
    width: 100%;
    max-width: 320px;
    margin-left: auto;
    border-collapse: collapse;
    font-size: 0.88em;
    margin-top: 10px;
  }}
  .summary-table td {{ padding: 5px 8px; }}
  .summary-table tr:last-child td {{
    border-top: 2px solid #1e3a8a;
    padding-top: 8px;
    font-weight: 800;
    font-size: 1.1em;
    color: #1e3a8a;
  }}
  /* ── Nút in ── */
  .print-btn {{
    display: block;
    margin: 20px auto 0;
    padding: 10px 36px;
    background: #1e3a8a;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 0.95em;
    font-weight: 600;
    cursor: pointer;
    font-family: 'Be Vietnam Pro', Arial, sans-serif;
    letter-spacing: 0.3px;
  }}
  .print-btn:hover {{ background: #1e40af; }}
  @media print {{
    body {{ background: white; padding: 0; }}
    .invoice {{ box-shadow: none; border-radius: 0; }}
    .print-btn {{ display: none; }}
    * {{
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
      color-adjust: exact !important;
    }}
  }}
</style>
</head>
<body>
<div class="invoice">

  <div class="header">
    <div class="logo-row">
      <span style="font-size:1.5em">🪟</span>
      <h1>RÈM KHÁNH LINH</h1>
    </div>
    <p class="sub">Chuyên rèm cửa cao cấp — Uy tín — Chất lượng</p>
    <h2>HÓA ĐƠN BÁN HÀNG</h2>
  </div>

  <div class="meta-row">
    <span><strong>Mã hóa đơn:</strong> {ma_hd}</span>
    <span><strong>Ngày lập:</strong> {ngay_in}</span>
  </div>

  <div class="customer-box">
    <strong>Khách hàng:</strong> {ten_kh}<br>
    <strong>Số điện thoại:</strong> {sdt_hien} &nbsp;&nbsp; <strong>Địa chỉ:</strong> {dia_hien}
  </div>

  {all_groups_html}

  <table class="summary-table">
    <tbody>
      {tong_ket_rows}
      <tr>
        <td style="text-align:left">{final_label}</td>
        <td style="text-align:right">{final_amount:,} ₫</td>
      </tr>
    </tbody>
  </table>

  {ghi_chu_html}

  <div class="sig-row">
    <div class="sig-box">
      <p class="sig-label">Khách hàng ký tên</p>
      <p class="sig-name">{ten_kh}</p>
    </div>
    <div class="sig-box">
      <p class="sig-label">Người lập hóa đơn</p>
      <p class="sig-name">Rèm Khánh Linh</p>
    </div>
  </div>

</div>
<button class="print-btn" onclick="window.print()">🖨️ In / Lưu PDF</button>
</body>
</html>"""

        st.info("🖨️ Nhấn nút **In / Lưu PDF** bên dưới hóa đơn, hoặc dùng **Ctrl+P**.")
        iframe_height = 720 + len(df_prev.groupby("Ten_SP")) * 60 + len(st.session_state.invoice_items) * 38 + (80 if ghi_chu.strip() else 0) + (has_adj * 30)
        components.html(full_html, height=iframe_height, scrolling=False)