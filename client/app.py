import json
import uuid
import streamlit as st
from datetime import datetime, date
import api

st.set_page_config(page_title="BarBitch", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def _session_store():
    """Server-side token → user dict. Survives Streamlit reruns within the process."""
    return {}

ss = st.session_state


# ── Session state bootstrap ────────────────────────────────────────────────────

def _init(key, val):
    if key not in ss:
        ss[key] = val

# Auth
_init("user", None)            # None = not logged in; dict with id, name, permissions, etc.
# Navigation
_init("screen", "tables")      # tables | table_detail | menu | staff | roles
_init("table_id", None)
# Tables board
_init("show_open_form", False)
_init("status_filter", "Active")
_init("confirm_close_card_id", None)
# Table detail
_init("show_add_order", False)
_init("editing_name", False)
_init("confirm_close_table", False)
_init("confirm_del_order_id", None)
# Menu
_init("show_item_form", False)
_init("edit_item", None)
_init("confirm_del_item_id", None)
# Staff
_init("show_user_form", False)
_init("edit_user", None)
_init("confirm_del_user_id", None)
# Roles
_init("show_role_form", False)
_init("edit_role", None)
_init("confirm_del_role_id", None)
# Stats
_init("stats_date", None)  # None = today
# Tables — closed date filter
_init("closed_date_filter", None)   # None = show all dates
_init("date_filter_enabled", True)  # True = filter active
# Stock
_init("stock_adjust_id", None)
_init("stock_delta", 0.0)


# ── Helpers ────────────────────────────────────────────────────────────────────

def nav_to(screen, table_id=None):
    ss.screen = screen
    ss.table_id = table_id
    ss.show_open_form = False
    ss.show_add_order = False
    ss.editing_name = False
    ss.confirm_close_card_id = None
    ss.confirm_close_table = False
    ss.confirm_del_order_id = None
    ss.show_item_form = False
    ss.edit_item = None
    ss.confirm_del_item_id = None
    ss.show_user_form = False
    ss.edit_user = None
    ss.confirm_del_user_id = None
    ss.show_role_form = False
    ss.edit_role = None
    ss.confirm_del_role_id = None
    ss.stats_date = None
    ss.stock_adjust_id = None
    ss.stock_delta = 0.0
    st.rerun()


def has_perm(perm: str) -> bool:
    return perm in (ss.user or {}).get("permissions", [])


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("## 🍺 BarBitch")
        st.markdown("### Sign in")
        with st.container(border=True):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign in", type="primary", use_container_width=True):
                if username and password:
                    data, err = api.login(username, password)
                    if err:
                        st.error(err)
                    else:
                        api.set_token(data["access_token"])
                        token = str(uuid.uuid4())
                        _session_store()[token] = data
                        st.query_params["t"] = token
                        ss.user = data
                        st.rerun()
                else:
                    st.warning("Enter username and password.")


if ss.user is None:
    token = st.query_params.get("t")
    if token:
        ss.user = _session_store().get(token)
        if ss.user:
            api.set_token(ss.user.get("access_token"))

# Token expired mid-session — clear and go back to login
if api.is_auth_expired():
    api.set_token(None)
    api.clear_auth_expired()
    session_token = st.query_params.get("t")
    if session_token:
        _session_store().pop(session_token, None)
    st.query_params.clear()
    ss.user = None
    st.rerun()

if ss.user is None:
    login_screen()
    st.stop()

_NAV_ITEMS = [
    ("🗂 Tables",  "tables", "tables"),
    ("🍹 Menu",    "menu",   "items"),
    ("📦 Stock",   "stock",  "stock"),
    ("👥 Staff",   "staff",  "users"),
    ("🔑 Roles",   "roles",  "roles"),
    ("📊 Stats",   "stats",  "stats"),
]

# Redirect to first permitted screen if current screen is inaccessible
_screen_perms = {"tables": "tables", "table_detail": "tables", "menu": "items",
                 "stock": "stock", "staff": "users", "roles": "roles", "stats": "stats"}
if not has_perm(_screen_perms.get(ss.screen, "")):
    _first = next((target for _, target, perm in _NAV_ITEMS if has_perm(perm)), None)
    if _first and ss.screen != _first:
        ss.screen = _first
        st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🍺 BarBitch")
    st.divider()
    for label, target, perm in _NAV_ITEMS:
        if not has_perm(perm):
            continue
        is_active = ss.screen == target or (ss.screen == "table_detail" and target == "tables")
        if st.button(label, use_container_width=True,
                     type="primary" if is_active else "secondary",
                     key=f"nav_{target}"):
            nav_to(target)
    st.divider()
    st.caption(f"Signed in as **{ss.user['name']}**")
    st.caption(f"Role: {ss.user['role_name']}")
    if st.button("Sign out", use_container_width=True, key="nav_logout"):
        token = st.query_params.get("t")
        if token:
            _session_store().pop(token, None)
        api.set_token(None)
        st.query_params.clear()
        ss.user = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TABLES BOARD
# ══════════════════════════════════════════════════════════════════════════════

def tables_board():
    col_h, col_btn = st.columns([4, 1])
    col_h.title("Tables")
    with col_btn:
        st.write("")  # vertical alignment
        if st.button("➕ Open Table", use_container_width=True, type="primary"):
            ss.show_open_form = not ss.show_open_form
            st.rerun()

    # Open table form
    if ss.show_open_form:
        with st.container(border=True):
            st.markdown("**Open New Table**")
            name = st.text_input("Table name", placeholder="e.g. Table 3, Bar Tab, Terrace",
                                  max_chars=100, key="new_table_name_in")
            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                if st.button("Open", type="primary", use_container_width=True,
                             disabled=not (name or "").strip()):
                    _, err = api.create_table(name.strip())
                    if err:
                        st.error(err)
                    else:
                        ss.show_open_form = False
                        st.rerun()
            with c2:
                if st.button("Cancel", use_container_width=True):
                    ss.show_open_form = False
                    st.rerun()

    # Status filter
    ss.status_filter = st.radio(
        "Filter", ["Active", "Closed", "All"],
        horizontal=True,
        index=["Active", "Closed", "All"].index(ss.status_filter),
        label_visibility="collapsed",
    )

    # Date filter — only shown when Closed is selected
    closed_date = None
    if ss.status_filter == "Closed":
        # Pre-set widget state before it renders (Today button sets this flag on previous rerun)
        if ss.get("_date_picker_jump"):
            ss["closed_date_picker"] = ss.closed_date_filter
            del ss["_date_picker_jump"]

        tog_col, date_col, today_col = st.columns([2, 3, 1])
        with tog_col:
            st.write("")
            ss.date_filter_enabled = st.toggle(
                "Filter by date",
                value=ss.date_filter_enabled,
                key="date_filter_toggle",
            )
        if ss.date_filter_enabled:
            with date_col:
                date_val = ss.closed_date_filter if ss.closed_date_filter else date.today()
                picked = st.date_input(
                    "Closed on",
                    value=date_val,
                    max_value=date.today(),
                    key="closed_date_picker",
                    label_visibility="collapsed",
                )
                ss.closed_date_filter = picked
                closed_date = picked.isoformat()
            with today_col:
                st.write("")
                if st.button("Today", key="today_date_filter", use_container_width=True):
                    ss.closed_date_filter = date.today()
                    ss["_date_picker_jump"] = True
                    st.rerun()

    # Close confirmation (card-level)
    if ss.confirm_close_card_id:
        tables_data, _ = api.get_tables()
        t = next((x for x in (tables_data or []) if x["id"] == ss.confirm_close_card_id), None)
        if t:
            with st.container(border=True):
                st.warning(f"Close **{t['table_name']}**? This will lock the bill.", icon="⚠️")
                c1, c2, _ = st.columns([1, 1, 2])
                with c1:
                    if st.button("Confirm Close", type="primary", use_container_width=True):
                        _, err = api.close_table(ss.confirm_close_card_id)
                        if err:
                            st.error(err)
                        ss.confirm_close_card_id = None
                        st.rerun()
                with c2:
                    if st.button("Cancel", use_container_width=True, key="cancel_close_card"):
                        ss.confirm_close_card_id = None
                        st.rerun()

    # Load tables
    status_param = None if ss.status_filter == "All" else ss.status_filter
    tables, err = api.get_tables(status_param, date=closed_date)
    if err:
        st.error(err)
        return
    if not tables:
        st.info("No tables yet — tap **➕ Open Table** to get started.")
        return

    # Card grid (3 columns)
    cols = st.columns(3)
    for i, t in enumerate(tables):
        with cols[i % 3]:
            is_closed = t["status"] == "Closed"
            with st.container(border=True):
                # Name + status badge (badge hidden when filter already shows only Closed)
                if is_closed:
                    st.markdown(f"**{t['table_name']}**")
                else:
                    st.markdown(f"### {t['table_name']}")
                    st.markdown("🟢 **Active**")

                if is_closed:
                    total_str = f"${t['total']:.2f}"
                    st.markdown(f"<span style='font-size:1.8rem;font-weight:700'>{total_str}</span>", unsafe_allow_html=True)
                    if t.get("closed_at"):
                        closed = datetime.fromisoformat(t["closed_at"]).strftime("%b %d, %H:%M")
                        st.caption(f"🔒 Closed {closed}")
                    if st.button("View receipt", key=f"view_{t['id']}", use_container_width=True, type="secondary"):
                        nav_to("table_detail", t["id"])
                else:
                    table, err = api.get_table(t['id'])
                    if err:
                        st.error(err)
                        return
                    orders = table.get("orders", [])
                    running_total = sum(o["price"] * o["quantity"] for o in orders)
                    st.metric("Running Total", f"${running_total:.2f}")

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("View", key=f"view_{t['id']}", use_container_width=True, type="primary"):
                            nav_to("table_detail", t["id"])
                    with b2:
                        if st.button("Close", key=f"close_card_{t['id']}", use_container_width=True):
                            ss.confirm_close_card_id = t["id"]
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TABLE DETAIL
# ══════════════════════════════════════════════════════════════════════════════

def table_detail():
    if not ss.table_id:
        nav_to("tables")
        return

    table, err = api.get_table(ss.table_id)
    if err:
        st.error(err)
        if st.button("← Back to Tables"):
            nav_to("tables")
        return

    # Also fetch items for name lookup
    all_items, _ = api.get_items()
    item_names = {it["id"]: it["name"] for it in (all_items or [])}

    orders = table.get("orders", [])
    is_active = table["status"] == "Active"
    running_total = sum(o["price"] * o["quantity"] for o in orders)

    # ── Header ─────────────────────────────────────────────────────────────────
    col_back, col_title, col_status = st.columns([1, 5, 2])

    with col_back:
        st.write("")
        if st.button("← Tables"):
            nav_to("tables")

    with col_title:
        if ss.editing_name:
            new_name = st.text_input(
                "Name", value=table["table_name"],
                max_chars=100, key="edit_name_in", label_visibility="collapsed"
            )
            s1, s2, _ = st.columns([1, 1, 4])
            with s1:
                if st.button("Save", type="primary"):
                    _, err = api.update_table(ss.table_id, new_name.strip())
                    if err:
                        st.error(err)
                    else:
                        ss.editing_name = False
                        st.rerun()
            with s2:
                if st.button("Cancel", key="cancel_rename"):
                    ss.editing_name = False
                    st.rerun()
        else:
            t1, t2 = st.columns([8, 1])
            t1.title(table["table_name"])
            if is_active and t2.button("✏️", key="btn_rename"):
                ss.editing_name = True
                st.rerun()

    with col_status:
        st.write("")
        if is_active:
            st.markdown("### 🟢 Active")
        else:
            st.markdown("### ⚫ Closed")
            if table.get("closed_at"):
                closed = datetime.fromisoformat(table["closed_at"]).strftime("%b %d, %Y  %H:%M")
                st.caption(f"Closed {closed}")

    st.divider()

    # ── Confirm close table ────────────────────────────────────────────────────
    if ss.confirm_close_table:
        with st.container(border=True):
            st.warning(
                f"Close **{table['table_name']}**?\n\n"
                f"Total: **${running_total:.2f}**  \nThis will lock the bill.",
                icon="⚠️"
            )
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                if st.button("Confirm Close", type="primary", use_container_width=True):
                    _, err = api.close_table(ss.table_id)
                    if err:
                        st.error(err)
                    ss.confirm_close_table = False
                    st.rerun()
            with c2:
                if st.button("Cancel", use_container_width=True, key="cancel_close_tbl"):
                    ss.confirm_close_table = False
                    st.rerun()

    # ── Confirm delete order ───────────────────────────────────────────────────
    if ss.confirm_del_order_id:
        order = next((o for o in orders if o["id"] == ss.confirm_del_order_id), None)
        if order:
            item_label = item_names.get(order["item_id"], f"Item #{order['item_id']}")
            with st.container(border=True):
                st.warning(f"Remove **{item_label}** × {order['quantity']} from the bill?", icon="⚠️")
                c1, c2, _ = st.columns([1, 1, 4])
                with c1:
                    if st.button("Remove", type="primary", use_container_width=True):
                        _, err = api.delete_order(ss.table_id, ss.confirm_del_order_id)
                        if err:
                            st.error(err)
                        ss.confirm_del_order_id = None
                        st.rerun()
                with c2:
                    if st.button("Keep", use_container_width=True):
                        ss.confirm_del_order_id = None
                        st.rerun()

    # ── Orders list ────────────────────────────────────────────────────────────
    st.markdown("**Orders**")

    if not orders:
        st.info("No orders yet." + (" Add items below ↓" if is_active else ""))
    else:
        hcols = st.columns([4, 2, 2, 2, 1])
        for hdr, col in zip(["Item", "Unit price", "Qty", "Line total", ""], hcols):
            col.markdown(f"**{hdr}**")
        st.divider()

        for order in orders:
            iname = item_names.get(order["item_id"], f"Item #{order['item_id']}")
            rc = st.columns([4, 2, 2, 2, 1])
            rc[0].markdown(iname)
            rc[1].markdown(f"${order['price']:.2f}")

            if is_active:
                # Qty number input — update on change
                def _make_qty_cb(tid=ss.table_id, oid=order["id"]):
                    def _cb():
                        new_qty = ss.get(f"qty_{oid}", 1.0)
                        _, qerr = api.update_order(tid, oid, new_qty)
                        if qerr:
                            ss[f"qty_err_{oid}"] = qerr
                    return _cb

                rc[2].number_input(
                    "Qty", min_value=0.5, step=0.5,
                    value=float(order["quantity"]),
                    key=f"qty_{order['id']}",
                    label_visibility="collapsed",
                    on_change=_make_qty_cb(),
                )
                if ss.get(f"qty_err_{order['id']}"):
                    st.error(ss.pop(f"qty_err_{order['id']}"))
            else:
                rc[2].markdown(str(order["quantity"]))

            line = order["price"] * order["quantity"]
            rc[3].markdown(f"${line:.2f}")

            if is_active:
                if rc[4].button("×", key=f"del_ord_{order['id']}"):
                    ss.confirm_del_order_id = order["id"]
                    st.rerun()

    # ── Bill footer ────────────────────────────────────────────────────────────
    st.divider()
    foot_left, foot_right = st.columns([2, 3])

    with foot_left:
        if is_active:
            st.metric("Running Total", f"${running_total:.2f}")
        else:
            st.metric("Total (locked)", f"${table['total']:.2f}")

    with foot_right:
        if is_active:
            if st.button("🔒 Close Table", type="primary", use_container_width=True):
                ss.confirm_close_table = True
                st.rerun()
        else:
            pdf_bytes, err = api.get_receipt(table["id"])
            if err:
                st.error(f"Receipt unavailable: {err}")
            else:
                st.download_button(
                    "📄 Download Receipt",
                    data=pdf_bytes,
                    file_name=f"receipt_{table['id']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    # ── Add order panel ────────────────────────────────────────────────────────
    if is_active:
        st.divider()

        col_add_btn, _ = st.columns([2, 4])
        with col_add_btn:
            btn_label = "▲ Hide" if ss.show_add_order else "➕ Add Item to Table"
            if st.button(btn_label, use_container_width=True, type="secondary"):
                ss.show_add_order = not ss.show_add_order
                st.rerun()

        if ss.show_add_order:
            with st.container(border=True):
                avail_items, err = api.get_items(available_only=True)
                if err:
                    st.error(f"Could not load items: {err}")
                elif not avail_items:
                    st.warning("No available items on the menu. Add items in the **Menu** section first.")
                else:
                    item_map = {f"{it['name']}  —  ${it['price']:.2f}": it for it in avail_items}
                    sel = st.selectbox("Item", options=list(item_map.keys()), key="add_ord_sel")
                    qty = st.number_input("Quantity", min_value=0.5, step=0.5, value=1.0, key="add_ord_qty")

                    if sel:
                        it = item_map[sel]
                        st.caption(f"Line total: **${it['price'] * qty:.2f}**")

                    if st.button("Add to Table", type="primary", key="btn_add_to_tbl"):
                        it = item_map[sel]
                        _, err = api.add_order(ss.table_id, it["id"], qty)
                        if err:
                            st.error(err)
                        else:
                            # Show confirmation including stock deduction if applicable
                            item_detail, _ = api.get_item(it["id"])
                            if item_detail and item_detail.get("stock_qty") is not None:
                                st.success(f"✓ Added {qty} × {it['name']} | Stock: {item_detail['stock_qty']:.0f} left")
                            else:
                                st.success(f"✓ Added {qty} × {it['name']}")
                            ss.show_add_order = False
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════════════════

def menu():
    col_h, col_btn = st.columns([4, 1])
    col_h.title("Menu")
    with col_btn:
        st.write("")
        if st.button("➕ Add Item", use_container_width=True, type="primary"):
            ss.show_item_form = True
            ss.edit_item = None
            st.rerun()

    # Add / Edit form
    if ss.show_item_form:
        editing = ss.edit_item is not None
        with st.container(border=True):
            st.markdown(f"**{'Edit' if editing else 'New'} Item**")
            d = ss.edit_item or {}
            name_v = st.text_input("Name", value=d.get("name", ""), max_chars=100, key="item_name_in")
            price_v = st.number_input("Price ($)", value=float(d.get("price", 1.0)),
                                       min_value=0.01, step=0.5, format="%.2f", key="item_price_in")
            cat_v = st.text_input("Category", value=d.get("category") or "",
                                   placeholder="beer, cocktail, food, soft drink…", key="item_cat_in")
            avail_v = st.toggle("Available", value=d.get("is_available", True), key="item_avail_in")

            stock_enabled = st.toggle("Track stock", value=d.get("stock_qty") is not None, key="item_stock_enabled_in")
            stock_v = None
            if stock_enabled:
                stock_v = st.number_input("Stock quantity", value=float(d.get("stock_qty", 0) or 0),
                                         min_value=0.0, step=1.0, format="%.0f", key="item_stock_in")

            s1, s2, _ = st.columns([1, 1, 3])
            with s1:
                if st.button("Save", type="primary", use_container_width=True,
                             disabled=not (name_v or "").strip()):
                    if editing:
                        _, err = api.update_item(
                            ss.edit_item["id"],
                            name=name_v.strip(), price=price_v,
                            category=cat_v.strip() or None, is_available=avail_v,
                            stock_qty=stock_v,
                        )
                    else:
                        _, err = api.create_item(name_v.strip(), price_v, cat_v.strip() or None, avail_v)
                        if not err and stock_v is not None:
                            item_id = _.get("id")
                            _, err = api.update_item(item_id, stock_qty=stock_v)
                    if err:
                        st.error(err)
                    else:
                        ss.show_item_form = False
                        ss.edit_item = None
                        st.rerun()
            with s2:
                if st.button("Cancel", use_container_width=True, key="cancel_item_frm"):
                    ss.show_item_form = False
                    ss.edit_item = None
                    st.rerun()

    # Delete confirmation
    if ss.confirm_del_item_id:
        all_items_chk, _ = api.get_items()
        item_chk = next((i for i in (all_items_chk or []) if i["id"] == ss.confirm_del_item_id), None)
        if item_chk:
            with st.container(border=True):
                st.warning(f"Delete **{item_chk['name']}**? This cannot be undone.", icon="⚠️")
                c1, c2, _ = st.columns([1, 1, 3])
                with c1:
                    if st.button("Delete", type="primary", use_container_width=True, key="confirm_del_item_btn"):
                        _, err = api.delete_item(ss.confirm_del_item_id)
                        if err:
                            st.error(err)
                        ss.confirm_del_item_id = None
                        st.rerun()
                with c2:
                    if st.button("Cancel", use_container_width=True, key="cancel_del_item_btn"):
                        ss.confirm_del_item_id = None
                        st.rerun()

    # Filter bar
    f1, f2, f3 = st.columns([3, 2, 2])
    search = f1.text_input("Search", placeholder="Search items…", label_visibility="collapsed", key="menu_search_in")

    all_items, err = api.get_items()
    if err:
        st.error(err)
        return

    cats = sorted({i["category"] for i in all_items if i.get("category")})
    cat_sel = f2.selectbox("Category", ["All categories"] + cats,
                            label_visibility="collapsed", key="menu_cat_sel")
    show_unavail = f3.toggle("Show unavailable", key="menu_unavail_tog", value=True)

    # Filter client-side
    items = all_items
    if search:
        items = [i for i in items if search.lower() in i["name"].lower()]
    if cat_sel != "All categories":
        items = [i for i in items if i.get("category") == cat_sel]
    if not show_unavail:
        items = [i for i in items if i["is_available"]]

    if not items:
        st.info("No items match your filters.")
        return

    # List header
    hcols = st.columns([4, 2, 2, 1, 3])
    for hdr, col in zip(["Name", "Price", "Category", "Available", "Actions"], hcols):
        col.markdown(f"**{hdr}**")
    st.divider()

    for item in items:
        rc = st.columns([4, 2, 2, 1, 3])
        name_txt = item["name"] if item["is_available"] else f"~~{item['name']}~~"
        rc[0].markdown(name_txt)
        rc[1].markdown(f"${item['price']:.2f}")
        rc[2].markdown(item.get("category") or "—")

        # Available toggle
        cur_avail = ss.get(f"avail_{item['id']}", item["is_available"])
        new_avail = rc[3].toggle("", value=item["is_available"],
                                  key=f"avail_tog_{item['id']}", label_visibility="collapsed")
        if new_avail != item["is_available"]:
            _, err = api.update_item(item["id"], is_available=new_avail,
                                      name=item["name"], price=item["price"],
                                      category=item.get("category"))
            if err:
                st.error(err)
            else:
                st.rerun()

        with rc[4]:
            a1, a2 = st.columns(2)
            if a1.button("Edit", key=f"edit_item_{item['id']}", use_container_width=True):
                ss.show_item_form = True
                ss.edit_item = item
                st.rerun()
            if a2.button("Del", key=f"del_item_{item['id']}", use_container_width=True):
                ss.confirm_del_item_id = item["id"]
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAFF
# ══════════════════════════════════════════════════════════════════════════════

def staff():
    col_h, col_btn = st.columns([4, 1])
    col_h.title("Staff")
    with col_btn:
        st.write("")
        if st.button("➕ Add Member", use_container_width=True, type="primary"):
            ss.show_user_form = True
            ss.edit_user = None
            st.rerun()

    roles_data, roles_err = api.get_roles()
    if roles_err:
        st.error(f"Could not load roles: {roles_err}")
        return
    roles_list = roles_data or []
    role_map = {r["id"]: r for r in roles_list}
    role_options = [r["name"] for r in roles_list]
    role_ids = [r["id"] for r in roles_list]

    # Add / Edit form
    if ss.show_user_form:
        editing = ss.edit_user is not None
        with st.container(border=True):
            st.markdown(f"**{'Edit' if editing else 'New'} Staff Member**")
            d = ss.edit_user or {}
            name_v = st.text_input("Name", value=d.get("name", ""), max_chars=50, key="user_name_in")
            username_v = st.text_input("Username", value=d.get("username", ""), max_chars=50, key="user_username_in")
            password_v = st.text_input(
                "Password" + (" (leave blank to keep)" if editing else ""),
                type="password", key="user_password_in"
            )
            # Role selector
            cur_role_id = d.get("role_id")
            cur_role_idx = role_ids.index(cur_role_id) if cur_role_id in role_ids else 0
            role_sel_idx = st.selectbox(
                "Role", range(len(role_options)),
                format_func=lambda i: role_options[i],
                index=cur_role_idx,
                key="user_role_in",
            )
            selected_role_id = role_ids[role_sel_idx]

            s1, s2, _ = st.columns([1, 1, 3])
            with s1:
                can_save = bool((name_v or "").strip()) and bool((username_v or "").strip())
                if not editing:
                    can_save = can_save and bool((password_v or "").strip())
                if st.button("Save", type="primary", use_container_width=True,
                             disabled=not can_save, key="save_user_btn"):
                    if editing:
                        kw = {"name": name_v.strip(), "username": username_v.strip(), "role_id": selected_role_id}
                        if password_v.strip():
                            kw["password"] = password_v.strip()
                        _, err = api.update_user(ss.edit_user["id"], **kw)
                    else:
                        _, err = api.create_user(name_v.strip(), username_v.strip(), password_v.strip(), selected_role_id)
                    if err:
                        st.error(err)
                    else:
                        ss.show_user_form = False
                        ss.edit_user = None
                        st.rerun()
            with s2:
                if st.button("Cancel", use_container_width=True, key="cancel_user_frm"):
                    ss.show_user_form = False
                    ss.edit_user = None
                    st.rerun()

    # Delete confirmation
    if ss.confirm_del_user_id:
        users_chk, _ = api.get_users()
        user_chk = next((u for u in (users_chk or []) if u["id"] == ss.confirm_del_user_id), None)
        if user_chk:
            with st.container(border=True):
                st.warning(f"Remove **{user_chk['name']}** from staff?", icon="⚠️")
                c1, c2, _ = st.columns([1, 1, 3])
                with c1:
                    if st.button("Remove", type="primary", use_container_width=True, key="confirm_del_user_btn"):
                        _, err = api.delete_user(ss.confirm_del_user_id)
                        if err:
                            st.error(err)
                        ss.confirm_del_user_id = None
                        st.rerun()
                with c2:
                    if st.button("Cancel", use_container_width=True, key="cancel_del_user_btn"):
                        ss.confirm_del_user_id = None
                        st.rerun()

    users, err = api.get_users()
    if err:
        st.error(err)
        return
    if not users:
        st.info("No staff members yet.")
        return

    hcols = st.columns([3, 2, 3, 3])
    for hdr, col in zip(["Name", "Username", "Role", "Actions"], hcols):
        col.markdown(f"**{hdr}**")
    st.divider()

    for user in users:
        rc = st.columns([3, 2, 3, 3])
        rc[0].markdown(user["name"])
        rc[1].markdown(user.get("username") or "—")
        rc[2].markdown(user.get("role_name") or "—")
        with rc[3]:
            a1, a2 = st.columns(2)
            if a1.button("Edit", key=f"edit_user_{user['id']}", use_container_width=True):
                ss.show_user_form = True
                ss.edit_user = user
                st.rerun()
            if a2.button("Del", key=f"del_user_{user['id']}", use_container_width=True):
                ss.confirm_del_user_id = user["id"]
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ROLES
# ══════════════════════════════════════════════════════════════════════════════

ALL_PERMS = ["tables", "items", "stock", "stats", "users", "roles"]
PERM_LABELS = {
    "tables": "🗂 Tables — manage tables & orders",
    "items":  "🍹 Items — view & edit menu",
    "stock":  "📦 Stock — view & adjust stock",
    "stats":  "📊 Stats — view daily statistics",
    "users":  "👥 Users — manage staff accounts",
    "roles":  "🔑 Roles — manage roles & permissions",
}


def roles():
    col_h, col_btn = st.columns([4, 1])
    col_h.title("Roles")
    with col_btn:
        st.write("")
        if st.button("➕ Add Role", use_container_width=True, type="primary"):
            ss.show_role_form = True
            ss.edit_role = None
            st.rerun()

    # Add / Edit form
    if ss.show_role_form:
        editing = ss.edit_role is not None
        with st.container(border=True):
            st.markdown(f"**{'Edit' if editing else 'New'} Role**")
            d = ss.edit_role or {}
            name_v = st.text_input("Role name", value=d.get("name", ""), max_chars=50, key="role_name_in")
            desc_v = st.text_input("Description", value=d.get("description") or "", key="role_desc_in")
            cur_perms = d.get("permissions", [])
            selected_perms = []
            st.markdown("**Permissions**")
            for perm in ALL_PERMS:
                checked = st.checkbox(PERM_LABELS[perm], value=(perm in cur_perms), key=f"perm_{perm}_in")
                if checked:
                    selected_perms.append(perm)

            s1, s2, _ = st.columns([1, 1, 3])
            with s1:
                if st.button("Save", type="primary", use_container_width=True,
                             disabled=not (name_v or "").strip(), key="save_role_btn"):
                    if editing:
                        _, err = api.update_role(ss.edit_role["id"],
                                                  name=name_v.strip(),
                                                  description=desc_v.strip() or None,
                                                  permissions=selected_perms)
                    else:
                        _, err = api.create_role(name_v.strip(), desc_v.strip() or None, selected_perms)
                    if err:
                        st.error(err)
                    else:
                        ss.show_role_form = False
                        ss.edit_role = None
                        st.rerun()
            with s2:
                if st.button("Cancel", use_container_width=True, key="cancel_role_frm"):
                    ss.show_role_form = False
                    ss.edit_role = None
                    st.rerun()

    # Delete confirmation
    if ss.confirm_del_role_id:
        roles_chk, _ = api.get_roles()
        role_chk = next((r for r in (roles_chk or []) if r["id"] == ss.confirm_del_role_id), None)
        if role_chk:
            with st.container(border=True):
                st.warning(f"Delete role **{role_chk['name']}**? This cannot be undone.", icon="⚠️")
                c1, c2, _ = st.columns([1, 1, 3])
                with c1:
                    if st.button("Delete", type="primary", use_container_width=True, key="confirm_del_role_btn"):
                        _, err = api.delete_role(ss.confirm_del_role_id)
                        if err:
                            st.error(err)
                        ss.confirm_del_role_id = None
                        st.rerun()
                with c2:
                    if st.button("Cancel", use_container_width=True, key="cancel_del_role_btn"):
                        ss.confirm_del_role_id = None
                        st.rerun()

    roles_data, err = api.get_roles()
    if err:
        st.error(err)
        return
    if not roles_data:
        st.info("No roles defined.")
        return

    hcols = st.columns([2, 3, 4, 2])
    for hdr, col in zip(["Name", "Description", "Permissions", "Actions"], hcols):
        col.markdown(f"**{hdr}**")
    st.divider()

    for role in roles_data:
        rc = st.columns([2, 3, 4, 2])
        rc[0].markdown(f"**{role['name']}**")
        rc[1].markdown(role.get("description") or "—")
        perm_badges = " · ".join(role["permissions"]) if role["permissions"] else "—"
        rc[2].markdown(perm_badges)
        with rc[3]:
            a1, a2 = st.columns(2)
            if a1.button("Edit", key=f"edit_role_{role['id']}", use_container_width=True):
                ss.show_role_form = True
                ss.edit_role = role
                st.rerun()
            if a2.button("Del", key=f"del_role_{role['id']}", use_container_width=True):
                ss.confirm_del_role_id = role["id"]
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STOCK
# ══════════════════════════════════════════════════════════════════════════════

def stock():
    st.title("📦 Stock Management")

    items, err = api.get_items()
    if err:
        st.error(err)
        return

    if not items:
        st.info("No items to manage stock for.")
        return

    # Filter to items with stock tracking
    tracked_items = [i for i in items if i.get("stock_qty") is not None]
    untracked_items = [i for i in items if i.get("stock_qty") is None]

    # Display tracked items
    if tracked_items:
        st.markdown("### Items with Stock")

        hcols = st.columns([3, 2, 2, 3])
        for hdr, col in zip(["Name", "Stock", "Category", "Actions"], hcols):
            col.markdown(f"**{hdr}**")
        st.divider()

        for item in tracked_items:
            rcols = st.columns([3, 2, 2, 3])

            # Name
            rcols[0].markdown(item["name"])

            # Stock level
            stock_val = item.get("stock_qty", 0)
            color = "🟢" if stock_val > 0 else "🔴"
            rcols[1].metric("", f"{color} {stock_val:.0f}")

            # Category
            rcols[2].markdown(item.get("category") or "—")

            # Action buttons
            with rcols[3]:
                a1, a2, a3 = st.columns(3)

                with a1:
                    if st.button("−", key=f"remove_{item['id']}", use_container_width=True):
                        _, err = api.update_stock(item["id"], -1)
                        if err:
                            st.error(err)
                        else:
                            st.success(f"Removed 1 from {item['name']}")
                            st.rerun()

                with a2:
                    if st.button("+", key=f"add_{item['id']}", use_container_width=True, type="primary"):
                        _, err = api.update_stock(item["id"], 1)
                        if err:
                            st.error(err)
                        else:
                            st.success(f"Added 1 to {item['name']}")
                            st.rerun()

                with a3:
                    if st.button("Set", key=f"set_{item['id']}", use_container_width=True):
                        ss.stock_adjust_id = item["id"]
                        st.rerun()

        # Set stock form
        if ss.stock_adjust_id:
            item = next((i for i in tracked_items if i["id"] == ss.stock_adjust_id), None)
            if item:
                with st.container(border=True):
                    st.markdown(f"**Set stock for {item['name']}**")
                    current = item.get("stock_qty", 0)
                    new_qty = st.number_input(
                        "New stock level",
                        min_value=0.0,
                        value=float(current),
                        step=0.5,
                        key="stock_set_input"
                    )
                    delta = new_qty - current

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", type="primary", use_container_width=True):
                            if delta != 0:
                                _, err = api.update_stock(item["id"], delta)
                                if err:
                                    st.error(err)
                                else:
                                    st.success(f"Updated stock to {new_qty:.0f}")
                                    ss.stock_adjust_id = None
                                    st.rerun()
                            else:
                                st.info("No change needed")
                    with col2:
                        if st.button("Cancel", use_container_width=True):
                            ss.stock_adjust_id = None
                            st.rerun()

    # Show untracked items notice
    if untracked_items:
        st.divider()
        st.markdown("### Items without Stock Tracking")
        st.info(f"The following {len(untracked_items)} item(s) don't have stock tracking enabled. Edit them to enable stock tracking.")
        with st.expander("Show untracked items"):
            for item in untracked_items:
                st.markdown(f"- {item['name']} (${item['price']:.2f})")


# ══════════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════════

def stats():
    import pandas as pd

    col_h, col_date = st.columns([3, 2])
    col_h.title("📊 Stats")

    with col_date:
        st.write("")
        picked = st.date_input(
            "Date", value=date.today(), max_value=date.today(),
            key="stats_date_pick", label_visibility="collapsed",
        )

    date_str = picked.isoformat() if picked else None
    data, err = api.get_daily_stats(date_str)
    if err:
        st.error(err)
        return

    # ── Metrics row ────────────────────────────────────────────────────────────
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💰 Total Revenue",  f"${data['revenue_total']:.2f}")
    m2.metric("🔒 Locked",         f"${data['revenue_locked']:.2f}",
              help="From closed tables")
    m3.metric("🟢 Running",        f"${data['revenue_running']:.2f}",
              help="From still-active tables")
    m4.metric("🧾 Orders",         data["orders_count"])
    m5.metric("🗂 Tables served",  data["tables_served"])

    st.divider()

    # ── Items sold ─────────────────────────────────────────────────────────────
    st.markdown("**Items sold**")

    if not data["items_sold"]:
        st.info("No orders recorded for this date.")
    else:
        items_df = pd.DataFrame(data["items_sold"])
        items_df.columns = ["Item", "Qty sold", "Revenue ($)"]

        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.bar_chart(items_df.set_index("Item")["Revenue ($)"])
        with col_table:
            st.dataframe(items_df, hide_index=True, use_container_width=True)

    # ── Orders log ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("**Orders log**")

    if not data["orders_log"]:
        st.info("No orders recorded for this date.")
    else:
        log_rows = []
        for entry in data["orders_log"]:
            ts = datetime.fromisoformat(entry["created_at"]).strftime("%H:%M:%S")
            log_rows.append({
                "Time":       ts,
                "Table":      entry["table_name"],
                "Item":       entry["item_name"],
                "Qty":        entry["quantity"],
                "Unit price": f"${entry['price']:.2f}",
                "Line total": f"${entry['line_total']:.2f}",
            })
        log_df = pd.DataFrame(log_rows)
        st.dataframe(log_df, hide_index=True, use_container_width=True)


# ── Router ─────────────────────────────────────────────────────────────────────

def _access_denied():
    st.error("You don't have permission to view this page.")

if ss.screen == "table_detail":
    if has_perm("tables"):
        table_detail()
    else:
        _access_denied()
elif ss.screen == "tables":
    if has_perm("tables"):
        tables_board()
    else:
        _access_denied()
elif ss.screen == "menu":
    if has_perm("items"):
        menu()
    else:
        _access_denied()
elif ss.screen == "stock":
    if has_perm("stock"):
        stock()
    else:
        _access_denied()
elif ss.screen == "staff":
    if has_perm("users"):
        staff()
    else:
        _access_denied()
elif ss.screen == "roles":
    if has_perm("roles"):
        roles()
    else:
        _access_denied()
elif ss.screen == "stats":
    if has_perm("stats"):
        stats()
    else:
        _access_denied()
