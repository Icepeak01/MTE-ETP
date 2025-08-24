# views/gas_inventory.py
import streamlit as st, pandas as pd
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import read_df, append_row
from lib.utils import today_str, now_iso, naira, new_id, get_flag

def render():
    ensure_logged_in()
    require_role(("admin","attendant"))
    view_header("Gas Inventory")

    # Show current expected stock (from today’s openings + transactions)
    tx = read_df("transactions")
    op = read_df("daily_openings")
    t = today_str()
    gas = 0.0
    if not op.empty and any(op["date"]==t):
        gas = float(op[op["date"]==t]["gas_open_kg"].iloc[0])
    if not tx.empty:
        d = tx[tx["date"]==t].copy()
        if "gas_kg_delta" in d.columns:
            d["gas_kg_delta"] = pd.to_numeric(d["gas_kg_delta"], errors='coerce').fillna(0.0)
            gas += d["gas_kg_delta"].sum()

    st.metric("Gas in stock (expected, kg)", f"{gas:,.2f}")

    # Admin can record stock-in; attendant only if allowed via flag
    allow_attendant_stockin = get_flag("allow_attendant_stock_in_today", False)
    can_stock_in = (st.session_state["role"] == "admin") or (allow_attendant_stockin and st.session_state["role"]=="attendant")

    if not can_stock_in:
        st.info("View-only for attendants. Admin can enable attendant stock-in via Prices & Fees → Flags.")
        return

    st.subheader("Record Stock-In")
    kg_in = st.number_input("KG received", min_value=0.5, step=0.5, format="%.2f")
    cost_total = st.number_input("Total purchase cost (₦, optional)", min_value=0.0, step=500.0)
    paid_by = st.selectbox("Paid by", ["cash","transfer"])
    note = st.text_input("Note / supplier ref")

    if st.button("Record Stock-In"):
        rid = new_id()
        cash_delta = -cost_total if paid_by == "cash" and cost_total > 0 else 0.0
        transfer_delta = -cost_total if paid_by == "transfer" and cost_total > 0 else 0.0
        row = {
            "id": rid, "datetime": now_iso(), "date": today_str(),
            "user": st.session_state.get("username","?"), "role": st.session_state.get("role","?"),
            "category":"gas_stock_in","sub_type":"","customer_method":"","provider_method":paid_by,
            "amount_value": cost_total, "gas_kg": kg_in, "price_per_kg":"", "fee": 0.0,
            "total_paid_by_customer": 0.0,
            "cash_delta": cash_delta, "pos_delta": 0.0, "transfer_delta": transfer_delta, "gas_kg_delta": kg_in,
            "note": note, "ref": ""
        }
        append_row("transactions", row)
        st.success(f"Recorded stock-in: {kg_in} kg; Cost {naira(cost_total)} paid by {paid_by.upper()}.")