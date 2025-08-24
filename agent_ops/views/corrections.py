# views/corrections.py
import streamlit as st
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import append_row
from lib.utils import today_str, now_iso, new_id

def render():
    ensure_logged_in()
    require_role(("admin",))
    view_header("Corrections / Refunds")

    st.caption("Enter exact opposite deltas to reverse a mistaken entry.")
    category = st.selectbox("Type", ["correction","refund"])
    note = st.text_area("Reason / reference id")
    cash_d = st.number_input("cash_delta (can be negative)", step=100.0, format="%.2f")
    pos_d = st.number_input("pos_delta (can be negative)", step=100.0, format="%.2f")
    tr_d  = st.number_input("transfer_delta (can be negative)", step=100.0, format="%.2f")
    gas_d = st.number_input("gas_kg_delta (can be negative)", step=0.5, format="%.2f")

    if st.button("Save Correction/Refund"):
        rid = new_id()
        row = {
            "id": rid, "datetime": now_iso(), "date": today_str(),
            "user":"admin","role":"admin",
            "category": category, "sub_type":"","customer_method":"","provider_method":"",
            "amount_value": 0.0, "gas_kg": "", "price_per_kg":"", "fee": 0.0,
            "total_paid_by_customer": 0.0,
            "cash_delta": cash_d, "pos_delta": pos_d, "transfer_delta": tr_d, "gas_kg_delta": gas_d,
            "note": note, "ref": ""
        }
        append_row("transactions", row)
        st.success("Saved.")