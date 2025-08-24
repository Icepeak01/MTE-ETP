# views/prices_and_fees.py
import streamlit as st, pandas as pd
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import read_df, write_df
from lib.utils import get_flag, set_flag

def render():
    ensure_logged_in()
    require_role(("admin",))
    view_header("Prices & Fees")

    st.subheader("Gas Price per KG")
    cfg = read_df("config_prices")
    if cfg.empty:
        cfg = pd.DataFrame({"key":["gas_price_per_kg"], "value":[0.0]})
    edited_cfg = st.data_editor(cfg, num_rows="dynamic", use_container_width=True, hide_index=True, key="cfg_editor")
    if st.button("Save Prices"):
        write_df("config_prices", edited_cfg)
        st.success("Saved gas price (and other keys).")

    st.divider()
    st.subheader("Withdrawal Fee Tiers")
    wd = read_df("config_fees_withdrawal")
    if wd.empty:
        wd = pd.DataFrame([
            {"min_amount":500,"max_amount":5000,"fee":100},
            {"min_amount":5000.01,"max_amount":10000,"fee":200},
            {"min_amount":10000.01,"max_amount":20000,"fee":300},
        ])
    edited_wd = st.data_editor(wd, num_rows="dynamic", use_container_width=True, hide_index=True, key="wd_editor")
    if st.button("Save Withdrawal Tiers"):
        write_df("config_fees_withdrawal", edited_wd)
        st.success("Saved withdrawal tiers.")

    st.subheader("Deposit Fee Tiers")
    dp = read_df("config_fees_deposit")
    if dp.empty:
        dp = pd.DataFrame([
            {"min_amount":500,"max_amount":5000,"fee":100},
            {"min_amount":5000.01,"max_amount":10000,"fee":200},
            {"min_amount":10000.01,"max_amount":20000,"fee":300},
        ])
    edited_dp = st.data_editor(dp, num_rows="dynamic", use_container_width=True, hide_index=True, key="dp_editor")
    if st.button("Save Deposit Tiers"):
        write_df("config_fees_deposit", edited_dp)
        st.success("Saved deposit tiers.")

    st.divider()
    st.subheader("Bill Fees (Fixed)")
    bf = read_df("config_fees_bill")
    if bf.empty:
        bf = pd.DataFrame([
            {"bill_type":"Electricity","fee":0},
            {"bill_type":"Cable","fee":0},
        ])
    edited_bf = st.data_editor(bf, num_rows="dynamic", use_container_width=True, hide_index=True, key="bf_editor")
    if st.button("Save Bill Fees"):
        write_df("config_fees_bill", edited_bf)
        st.success("Saved bill fees.")

    st.divider()
    st.subheader("Charging Categories")
    cc = read_df("config_fees_charging")
    if cc.empty:
        cc = pd.DataFrame([
            {"category":"Small phones & gadgets","fee":0},
            {"category":"Powerbank","fee":0},
            {"category":"Laptop / Heavy devices","fee":0},
        ])
    edited_cc = st.data_editor(cc, num_rows="dynamic", use_container_width=True, hide_index=True, key="cc_editor")
    if st.button("Save Charging Fees"):
        write_df("config_fees_charging", edited_cc)
        st.success("Saved charging fees.")

    st.divider()
    st.subheader("Flags")
    allow = st.toggle("Allow Attendant to record Gas Stock-In (today only)", value=get_flag("allow_attendant_stock_in_today", False))
    if st.button("Save Flags"):
        set_flag("allow_attendant_stock_in_today", allow)
        st.success("Saved flag(s).")