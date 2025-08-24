# views/open_day.py
import streamlit as st, pandas as pd
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import read_df, append_row, write_df
from lib.utils import today_str

def render():
    ensure_logged_in()
    require_role(("admin","attendant"))
    view_header("Open Day")

    today = today_str()
    opens = read_df("daily_openings")
    existing = opens[opens["date"] == today]

    if st.session_state["role"] == "attendant":
        st.info("View-only for attendants.")
        if existing.empty:
            st.warning("Admin has not set today's opening yet.")
        else:
            st.dataframe(existing, use_container_width=True, hide_index=True)
        return

    # Admin flow (can set or edit)
    if existing.empty:
        st.info("Set today's opening balances.")
        att = st.text_input("Attendant name (optional)", value="attendant")
        c = st.number_input("Opening Cash (₦)", min_value=0.0, step=1000.0)
        p = st.number_input("Opening POS (₦)", min_value=0.0, step=1000.0)
        t = st.number_input("Opening Transfer (₦)", min_value=0.0, step=1000.0)
        g = st.number_input("Opening Gas (kg)", min_value=0.0, step=0.5, format="%.2f")
        notes = st.text_area("Notes")
        if st.button("Save Opening"):
            row = {"date": today, "attendant": att, "cash_open": c, "pos_open": p, "transfer_open": t, "gas_open_kg": g, "notes": notes}
            append_row("daily_openings", row)
            st.success("Opening saved.")
    else:
        st.success("Today's opening already set.")
        st.dataframe(existing, use_container_width=True, hide_index=True)
        st.caption("Edit values below and click Update.")
        edited = st.data_editor(existing.reset_index(drop=True), use_container_width=True, key="open_editor")
        if st.button("Update Opening"):
            opens2 = opens[opens["date"] != today]
            out = pd.concat([opens2, edited], ignore_index=True)
            write_df("daily_openings", out)
            st.success("Updated.")