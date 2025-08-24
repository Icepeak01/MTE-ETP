# app.py
import streamlit as st
import pandas as pd

from lib.sheets import get_client, ensure_all_sheets, read_df
from lib.utils import naira, today_str
from lib.auth import ensure_logged_in, logout_button, role_badge, goto, can_access

st.set_page_config(page_title="Agent Ops", page_icon="🧾", layout="wide")

# ====== Cosmetics: hide Streamlit sidebar & menu ======
st.markdown("""
<style>
/* hide left sidebar & hamburger */
[data-testid="stSidebar"], header [data-testid="baseButton-header"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ====== Hardcoded users (same passwords as before) ======
USERS = {
    "admin":     {"name": "ADMIN",   "password": "owner123",  "role": "admin"},
    "attendant": {"name": "SALES",   "password": "attend123", "role": "attendant"},
}
ALIASES = {"sales":"attendant","owner":"admin","boss":"admin","admin":"admin","attendant":"attendant"}

def resolve_username(u_norm: str):
    if u_norm in ALIASES: return ALIASES[u_norm]
    for key, info in USERS.items():
        if info["name"].strip().lower() == u_norm:
            return key
    return None

# ====== Minimal login (in-page) ======
if not st.session_state.get("auth"):
    st.title("Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        key = resolve_username((u or "").strip().lower())
        if key and p == USERS[key]["password"]:
            st.session_state["auth"] = True
            st.session_state["username"] = key
            st.session_state["role"] = USERS[key]["role"]
            st.session_state["view"] = "home"
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ====== Bootstrap Sheets (friendly error if misconfigured) ======
try:
    gc = get_client()
    ensure_all_sheets(gc)
except Exception as e:
    st.error("Google Sheets connection failed. Check that:\n"
             "• Sheets API is enabled\n"
             "• The spreadsheet is shared to the service account (Editor)\n"
             "• SHEET_ID and secrets.toml are correct\n\n"
             f"Details: {e}")
    st.stop()

# ====== Router (Hub & Spoke) ======
if "view" not in st.session_state:
    st.session_state["view"] = "home"

def home_card(title, desc, view_key, kpi=None, allowed_roles=("admin","attendant")):
    role = st.session_state["role"]
    if role not in allowed_roles:
        return
    with st.container(border=True):
        st.subheader(title)
        if kpi: st.caption(kpi)
        st.write(desc)
        if st.button(f"Open {title}", key=f"open_{view_key}"):
            goto(view_key)

def compute_today_kpis():
    # small KPIs for the home cards
    tx = read_df("transactions")
    op = read_df("daily_openings")
    t = today_str()
    fees = 0.0; gas_sales = 0.0; cash=pos=tr=gas=0.0
    if not tx.empty:
        d = tx[tx["date"] == t].copy()
        for c in ["fee","amount_value","cash_delta","pos_delta","transfer_delta","gas_kg_delta"]:
            if c in d.columns: d[c] = pd.to_numeric(d[c], errors='coerce').fillna(0.0)
        fees = d["fee"].sum()
        gas_sales = d.loc[d["category"]=="gas_sale","amount_value"].sum()
        if not op.empty and any(op["date"] == t):
            o = op[op["date"] == t].iloc[0]
            cash = float(o.get("cash_open",0)); pos = float(o.get("pos_open",0))
            tr = float(o.get("transfer_open",0)); gas = float(o.get("gas_open_kg",0))
            cash += d["cash_delta"].sum(); pos += d["pos_delta"].sum()
            tr += d["transfer_delta"].sum(); gas += d["gas_kg_delta"].sum()
    return dict(fees=fees, gas_sales=gas_sales, cash=cash, pos=pos, tr=tr, gas=gas)

def render_home():
    role = st.session_state["role"]
    username = st.session_state["username"]

    # Header
    cols = st.columns([6,2,2])
    with cols[0]: st.title("Agent Ops — Home")
    with cols[1]: role_badge(role)
    with cols[2]: logout_button()

    k = compute_today_kpis()

    st.write("")  # spacing
    c1,c2,c3 = st.columns(3)

    with c1:
        home_card("Attendant", "Record withdrawals, deposits, bill payments, gas refill, charging.",
                  "attendant", kpi=f"Fees today: {naira(k['fees'])}", allowed_roles=("admin","attendant"))
        home_card("Today’s Transactions", "See today’s entries. Attendant is limited to today; Admin can change date in view.",
                  "today_tx", kpi=f"Gas stock (exp): {k['gas']:,.2f} kg", allowed_roles=("admin","attendant"))

    with c2:
        home_card("Gas Inventory", "Admin: stock-in & costs. Attendant: read-only (unless allowed by flag).",
                  "gas_inventory", kpi=f"POS exp: {naira(k['pos'])}", allowed_roles=("admin","attendant"))
        home_card("Open Day", "Review or set today’s opening balances. Attendant: view-only.",
                  "open_day", kpi=f"Cash exp: {naira(k['cash'])}", allowed_roles=("admin","attendant"))

    with c3:
        home_card("Admin Dashboard", "KPIs, balances, service mix.", "admin_dashboard",
                  kpi=f"Transfer exp: {naira(k['tr'])}", allowed_roles=("admin",))
        home_card("Prices & Fees", "Tiered fees, bill fees, charging categories, gas price.",
                  "prices_and_fees", allowed_roles=("admin",))
        home_card("Corrections", "Approve corrections / refunds.", "corrections", allowed_roles=("admin",))

# Map of views → renderers
from views.attendant import render as view_attendant
from views.today_tx import render as view_today_tx
from views.gas_inventory import render as view_gas_inventory
from views.admin_dashboard import render as view_admin_dashboard
from views.prices_and_fees import render as view_prices_and_fees
from views.open_day import render as view_open_day
from views.corrections import render as view_corrections

VIEWS = {
    "home": render_home,
    "attendant": view_attendant,
    "today_tx": view_today_tx,
    "gas_inventory": view_gas_inventory,
    "admin_dashboard": view_admin_dashboard,
    "prices_and_fees": view_prices_and_fees,
    "open_day": view_open_day,
    "corrections": view_corrections,
}

VIEWS.get(st.session_state["view"], render_home)()