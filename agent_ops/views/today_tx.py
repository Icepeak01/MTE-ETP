# views/today_tx.py
import streamlit as st, pandas as pd
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import read_df
from lib.utils import today_str

def render():
    ensure_logged_in()
    require_role(("admin","attendant"))
    view_header("Today’s Transactions")

    tx = read_df("transactions")
    if tx.empty:
        st.info("No transactions yet.")
        return

    df = tx.copy()
    # Attendant is locked to today
    if st.session_state["role"] == "attendant":
        df = df[df["date"] == today_str()]
        st.caption("Showing today only (attendant scope).")
    else:
        # admin can filter (basic date filter)
        pick = st.date_input("Filter by date", value=pd.to_datetime(today_str()))
        df = df[df["date"] == str(pick)]

    # Prevent Arrow overflow if id/ref were numeric-looking
    for col in ["id","ref"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    st.dataframe(df, use_container_width=True, hide_index=True)