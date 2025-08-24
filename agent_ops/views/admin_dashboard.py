# views/admin_dashboard.py
import streamlit as st, pandas as pd
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import read_df
from lib.utils import today_str, naira

def render():
    ensure_logged_in()
    require_role(("admin",))
    view_header("Admin Dashboard")

    tx = read_df("transactions"); op = read_df("daily_openings")
    if tx.empty:
        st.info("No transactions yet today.")
        return

    for col in ["amount_value","fee","cash_delta","pos_delta","transfer_delta","gas_kg","gas_kg_delta"]:
        if col in tx.columns:
            tx[col] = pd.to_numeric(tx[col], errors='coerce').fillna(0.0)

    today = today_str()
    today_tx = tx[tx["date"] == today]
    cash0 = pos0 = tr0 = gas0 = 0.0
    if not op.empty and any(op["date"]==today):
        o = op[op["date"]==today].iloc[0]
        cash0 = float(o.get("cash_open",0)); pos0 = float(o.get("pos_open",0))
        tr0 = float(o.get("transfer_open",0)); gas0 = float(o.get("gas_open_kg",0))

    cash = cash0 + today_tx["cash_delta"].sum()
    pos  = pos0 + today_tx["pos_delta"].sum()
    tr   = tr0 + today_tx["transfer_delta"].sum()
    gas  = gas0 + today_tx["gas_kg_delta"].sum()

    fees_total = today_tx["fee"].sum()
    gas_revenue = today_tx.loc[today_tx["category"]=="gas_sale","amount_value"].sum()
    count_tx = len(today_tx)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Transactions today", f"{count_tx}")
    c2.metric("Total fees today", naira(fees_total))
    c3.metric("Gas sales ₦ today", naira(gas_revenue))
    c4.metric("Gas in stock (kg, expected)", f"{gas:,.2f} kg")

    c5,c6,c7 = st.columns(3)
    c5.metric("Cash (expected)", naira(cash))
    c6.metric("POS (expected)", naira(pos))
    c7.metric("Transfer (expected)", naira(tr))

    st.subheader("Service Mix")
    mix = today_tx.groupby("category")["id"].count().sort_values(ascending=False).reset_index().rename(columns={"id":"count"})
    st.dataframe(mix, use_container_width=True, hide_index=True)

    st.subheader("Today’s Transactions")
    show = today_tx[["datetime","category","sub_type","customer_method","amount_value","fee","cash_delta","pos_delta","transfer_delta","gas_kg_delta","note","ref"]].copy()
    st.dataframe(show, use_container_width=True, hide_index=True)