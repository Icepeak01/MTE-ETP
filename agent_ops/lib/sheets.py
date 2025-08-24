import time
import gspread
import pandas as pd
import streamlit as st
from lib.schema import SHEETS, HEADERS
from gspread.exceptions import APIError

# Reuse the client across reruns
@st.cache_resource
def _client_from_secrets():
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

def get_client():
    return _client_from_secrets()

def _with_retry(fn, *args, **kwargs):
    # retry on 429/500/503 up to 3 times
    for i in range(3):
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (429, 500, 503):
                time.sleep(1.5 * (i + 1))
                continue
            raise
    # last try
    return fn(*args, **kwargs)

def get_spreadsheet(gc):
    sheet_id = st.secrets["SHEET_ID"]
    # wrap open_by_key with retry
    return _with_retry(gc.open_by_key, sheet_id)

def ensure_sheet(spread, title, headers):
    try:
        ws = spread.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = _with_retry(spread.add_worksheet, title=title, rows=1000, cols=max(5,len(headers)))
        _with_retry(ws.append_row, headers)
        return ws
    first_row = ws.row_values(1)
    if first_row != headers:
        _with_retry(ws.update, '1:1', [headers])
    return ws

def ensure_all_sheets(gc):
    spread = get_spreadsheet(gc)
    for s in SHEETS:
        ensure_sheet(spread, s, HEADERS[s])

@st.cache_data(ttl=60, show_spinner=False)  # a bit longer
def read_df(sheet_name: str) -> pd.DataFrame:
    gc = get_client()
    spread = get_spreadsheet(gc)
    ws = spread.worksheet(sheet_name)
    data = _with_retry(ws.get_all_records)
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=HEADERS[sheet_name])
    return df

def clear_cache():
    st.cache_data.clear()

def append_row(sheet_name: str, row: dict):
    gc = get_client()
    spread = get_spreadsheet(gc)
    ws = spread.worksheet(sheet_name)
    headers = HEADERS[sheet_name]
    values = [row.get(h, "") for h in headers]
    _with_retry(ws.append_row, values, value_input_option="USER_ENTERED")
    clear_cache()

def write_df(sheet_name: str, df):
    gc = get_client()
    spread = get_spreadsheet(gc)
    ws = spread.worksheet(sheet_name)
    headers = HEADERS[sheet_name]
    out = df.copy()
    for h in headers:
        if h not in out.columns:
            out[h] = ""
    out = out[headers]
    _with_retry(ws.clear)
    _with_retry(ws.update, '1:1', [headers])
    if len(out) > 0:
        _with_retry(
            ws.update,
            "A2",
            [[("" if pd.isna(x) else x) for x in row] for row in out.to_numpy()],
            value_input_option="USER_ENTERED",
        )
    clear_cache()