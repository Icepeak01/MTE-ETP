# views/attendant.py
import streamlit as st, pandas as pd
from lib.auth import ensure_logged_in, require_role, view_header
from lib.sheets import read_df, append_row
from lib.fees import fee_from_tiers, bill_fee, charging_fee
from lib.utils import today_str, now_iso, naira, new_id, get_price

def _balances_today():
    openings = read_df("daily_openings")
    today_open = openings[openings["date"] == today_str()]
    cash0 = float(today_open["cash_open"].iloc[0]) if len(today_open)>0 else 0.0
    pos0 = float(today_open["pos_open"].iloc[0]) if len(today_open)>0 else 0.0
    tr0  = float(today_open["transfer_open"].iloc[0]) if len(today_open)>0 else 0.0
    gas0 = float(today_open["gas_open_kg"].iloc[0]) if len(today_open)>0 else 0.0

    tx = read_df("transactions")
    tx_today = tx[tx["date"] == today_str()].copy()
    for col in ["cash_delta","pos_delta","transfer_delta","gas_kg_delta"]:
        if col in tx_today.columns:
            tx_today[col] = pd.to_numeric(tx_today[col], errors='coerce').fillna(0.0)
    cash = cash0 + tx_today.get("cash_delta", pd.Series(dtype=float)).sum()
    pos  = pos0 + tx_today.get("pos_delta", pd.Series(dtype=float)).sum()
    tr   = tr0  + tx_today.get("transfer_delta", pd.Series(dtype=float)).sum()
    gas  = gas0 + tx_today.get("gas_kg_delta", pd.Series(dtype=float)).sum()
    return cash,pos,tr,gas

def render():
    ensure_logged_in()
    require_role(("admin","attendant"))
    view_header("Attendant — New Transaction")

    fees_wd = read_df("config_fees_withdrawal")
    fees_dep = read_df("config_fees_deposit")
    fees_bill = read_df("config_fees_bill")
    fees_chg = read_df("config_fees_charging")
    gas_price = get_price("gas_price_per_kg", 0.0)

    with st.expander("👀 Today’s Expected Balances", expanded=True):
        c,p,t,g = _balances_today()
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Cash (expected)", naira(c))
        col2.metric("POS (expected)", naira(p))
        col3.metric("Transfer (expected)", naira(t))
        col4.metric("Gas in stock (kg, expected)", f"{g:,.2f} kg")

    st.subheader("Cash Withdrawal")
    with st.form("cash_withdrawal"):
        amount = st.number_input("Withdraw amount (₦)", min_value=500.0, step=500.0)
        pay_method = st.selectbox("Customer pays by", ["pos","transfer"])
        fee = fee_from_tiers(amount, fees_wd)
        st.caption(f"Fee for this amount: **{naira(fee)}**")
        note = st.text_input("Note / reference (optional)")
        if st.form_submit_button("Save Withdrawal"):
            rid = new_id()
            row = {
                "id": rid, "datetime": now_iso(), "date": today_str(),
                "user":"attendant","role":"attendant",
                "category":"cash_withdrawal","sub_type":"","customer_method":pay_method,"provider_method":"cash",
                "amount_value": amount, "gas_kg": "", "price_per_kg":"", "fee": fee,
                "total_paid_by_customer": amount + fee,
                "cash_delta": -amount,
                "pos_delta": (amount + fee) if pay_method == "pos" else 0.0,
                "transfer_delta": (amount + fee) if pay_method == "transfer" else 0.0,
                "gas_kg_delta": 0.0,
                "note": note, "ref": ""
            }
            append_row("transactions", row)
            st.success(f"Saved: {pay_method.upper()} {naira(amount+fee)}; Cash out {naira(amount)}; Fee {naira(fee)}.")

    st.divider()

    st.subheader("Cash Deposit")
    with st.form("cash_deposit"):
        amount = st.number_input("Deposit amount (₦)", min_value=500.0, step=500.0, key="dep_amt")
        fee2 = fee_from_tiers(amount, fees_dep)
        st.caption(f"Fee for this amount: **{naira(fee2)}**")
        note2 = st.text_input("Account / reference")
        if st.form_submit_button("Save Deposit"):
            rid = new_id()
            row = {
                "id": rid, "datetime": now_iso(), "date": today_str(),
                "user":"attendant","role":"attendant",
                "category":"cash_deposit","sub_type":"","customer_method":"cash","provider_method":"transfer",
                "amount_value": amount, "gas_kg": "", "price_per_kg":"", "fee": fee2,
                "total_paid_by_customer": amount + fee2,
                "cash_delta": amount + fee2, "pos_delta": 0.0, "transfer_delta": -amount, "gas_kg_delta": 0.0,
                "note": note2, "ref": ""
            }
            append_row("transactions", row)
            st.success(f"Saved: Cash in {naira(amount+fee2)}; Transfer out {naira(amount)}; Fee {naira(fee2)}.")

    st.divider()

    st.subheader("Bill Payment")
    with st.form("bill_payment"):
        bill_type = st.selectbox("Bill type", ["Electricity","Cable"])
        amount_b = st.number_input("Bill amount (₦)", min_value=0.0, step=500.0)
        pay_m = st.selectbox("Customer pays by", ["cash","transfer"])
        fee_b = fees_bill[fees_bill["bill_type"].str.lower()==bill_type.lower()]["fee"]
        fee_b = float(fee_b.iloc[0]) if len(fee_b)>0 else 0.0
        st.caption(f"Fixed fee for {bill_type}: **{naira(fee_b)}**")
        ref_b = st.text_input("Meter/Smartcard/Account number")
        if st.form_submit_button("Save Bill Payment"):
            rid = new_id()
            cash_delta = amount_b + fee_b if pay_m == "cash" else 0.0
            transfer_delta = -amount_b if pay_m == "cash" else fee_b
            row = {
                "id": rid, "datetime": now_iso(), "date": today_str(),
                "user":"attendant","role":"attendant",
                "category":"bill_payment","sub_type":bill_type,"customer_method":pay_m,"provider_method":"transfer",
                "amount_value": amount_b, "gas_kg": "", "price_per_kg":"", "fee": fee_b,
                "total_paid_by_customer": amount_b + fee_b,
                "cash_delta": cash_delta, "pos_delta": 0.0, "transfer_delta": transfer_delta, "gas_kg_delta": 0.0,
                "note": "", "ref": ref_b
            }
            append_row("transactions", row)
            st.success(f"Saved: {bill_type} {naira(amount_b)}; Fee {naira(fee_b)}; Via {pay_m.upper()}.")

    st.divider()

    st.subheader("Gas Refill")
    with st.form("gas_refill"):
        kg = st.number_input("KG sold", min_value=0.5, step=0.5, format="%.2f")
        price = st.number_input("Price per KG (₦)", min_value=0.0, value=float(gas_price), step=50.0)
        pay_g = st.selectbox("Payment method", ["cash","pos","transfer"])
        total_g = kg * price
        st.caption(f"Total: **{naira(total_g)}**")
        note_g = st.text_input("Note (optional)")
        if st.form_submit_button("Save Gas Sale"):
            rid = new_id()
            row = {
                "id": rid, "datetime": now_iso(), "date": today_str(),
                "user":"attendant","role":"attendant",
                "category":"gas_sale","sub_type":"","customer_method":pay_g,"provider_method":"",
                "amount_value": total_g, "gas_kg": kg, "price_per_kg": price, "fee": 0.0,
                "total_paid_by_customer": total_g,
                "cash_delta": total_g if pay_g=="cash" else 0.0,
                "pos_delta": total_g if pay_g=="pos" else 0.0,
                "transfer_delta": total_g if pay_g=="transfer" else 0.0,
                "gas_kg_delta": -kg,
                "note": note_g, "ref": ""
            }
            append_row("transactions", row)
            st.success(f"Saved: Gas {kg} kg @ {naira(price)} = {naira(total_g)} via {pay_g.upper()}.")

    st.divider()

    st.subheader("Charging Spot")
    with st.form("charging"):
        category = st.selectbox("Device category", ["Small phones & gadgets","Powerbank","Laptop / Heavy devices"])
        pay_c = st.selectbox("Payment method", ["cash","transfer"])
        fee_c = float(charging_fee(category, read_df("config_fees_charging")))
        st.caption(f"Charge: **{naira(fee_c)}** for {category}")
        note_c = st.text_input("Note (optional)", key="chg_note")
        if st.form_submit_button("Save Charging"):
            rid = new_id()
            row = {
                "id": rid, "datetime": now_iso(), "date": today_str(),
                "user":"attendant","role":"attendant",
                "category":"charging","sub_type":category,"customer_method":pay_c,"provider_method":"",
                "amount_value": 0.0, "gas_kg": "", "price_per_kg":"", "fee": fee_c,
                "total_paid_by_customer": fee_c,
                "cash_delta": fee_c if pay_c=="cash" else 0.0,
                "pos_delta": 0.0, "transfer_delta": fee_c if pay_c=="transfer" else 0.0,
                "gas_kg_delta": 0.0,
                "note": note_c, "ref": ""
            }
            append_row("transactions", row)
            st.success(f"Saved: Charging {category} — {naira(fee_c)} via {pay_c.upper()}.")