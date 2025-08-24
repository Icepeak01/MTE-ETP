# Agent Ops — Streamlit + Google Sheets

A lightweight, two-sided app (Attendant & Admin) for a Nigerian agent business:
cash withdrawals, deposits, bill payments, gas refills, and charging services — with
expected cash/POS/transfer balances and gas stock tracking.

## What you get
- Streamlit UI with hardcoded users (admin/attendant)
- Google Sheets storage (one workbook with multiple tabs)
- Tiered fees (withdrawal & deposit), fixed bill fees, charging categories
- Opening balances per day; transaction forms; live summaries & dashboard

## Setup (10–15 mins)
1) **Create a Google Cloud project** and a **Service Account** with role _Editor_ or _Sheets editor_.
2) Create a key (JSON). You’ll copy its content into `secrets.toml` below.
3) Create a Google Spreadsheet (blank). Copy its **Sheet ID** (the long ID in the URL).
4) **Share the spreadsheet** with your service account **client_email** with **Editor** access.
5) Open `.streamlit/secrets.toml` and fill:
   - `SHEET_ID = "your_sheet_id_here"`
   - Paste the full JSON under `[gcp_service_account]`

6) Install deps and run:
```bash
cd agent_ops
pip install -r requirements.txt
streamlit run app.py