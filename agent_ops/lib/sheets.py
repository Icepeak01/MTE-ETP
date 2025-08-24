# lib/sheets.py
import time
import gspread
import pandas as pd
import streamlit as st
from gspread.exceptions import APIError
from lib.schema import SHEETS, HEADERS

# ---------- Helpers ----------
def _col_letters(n: int) -> str:
    # 1->A, 26->Z, 27->AA ...
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def _ranges_for_all_sheets(max_rows: int = 20000) -> dict:
    """Return a mapping: sheet_name -> A1 range like 'Sheet!A1:AG20000'."""
    ranges = {}
    for s in SHEETS:
        last_col = _col_letters(max(1, len(HEADERS[s])))
        ranges[s] = f"{s}!A1:{last_col}{max_rows}"
    return ranges

# ---------- Client singletons ----------
@st.cache_resource
def _client_from_secrets():
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

def get_client():
    return _client_from_secrets()

def _with_retry(fn, *args, **kwargs):
    # Backoff with jitter for 429/500/503
    for i in range(5):
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (429, 500, 503):
                time.sleep((i + 1) * 1.2)  # 1.2s, 2.4s, 3.6s, ...
                continue
            raise
    return fn(*args, **kwargs)

def get_spreadsheet(gc):
    sheet_id = st.secrets["SHEET_ID"]
    return _with_retry(gc.open_by_key, sheet_id)

def ensure_sheet(spread, title, headers):
    try:
        ws = spread.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = _with_retry(spread.add_worksheet, title=title, rows=1000, cols=max(5, len(headers)))
        _with_retry(ws.append_row, headers)
        return ws
    if ws.row_values(1) != headers:
        _with_retry(ws.update, '1:1', [headers])
    return ws

def ensure_all_sheets(gc):
    spread = get_spreadsheet(gc)
    for s in SHEETS:
        ensure_sheet(spread, s, HEADERS[s])

# ---------- ONE batched read for everything ----------
@st.cache_data(ttl=300, show_spinner=False)  # 5 minutes on Cloud
def _batch_read_all() -> dict:
    """
    Returns {sheet_name: DataFrame} for every sheet, using one batchGet.
    Falls back to per-sheet reads if batchGet is unavailable.
    """
    gc = get_client()
    spread = get_spreadsheet(gc)

    # Try batch values API (1 request for many ranges)
    try:
        ranges = list(_ranges_for_all_sheets().values())
        resp = _with_retry(spread.values_batch_get, ranges)  # gspread wrapper
        value_ranges = resp.get("valueRanges", [])
        name_by_range = {v: k for k, v in _ranges_for_all_sheets().items()}
        out = {}
        for vr in value_ranges:
            rng = vr.get("range")
            values = vr.get("values", [])
            sheet_name = name_by_range.get(rng.split('!')[0] + '!' + rng.split('!')[1], None)
            # More robust: parse sheet name from "range"
            if sheet_name is None:
                sheet_name = vr["range"].split('!')[0]
            # Convert rows to DataFrame using our HEADERS
            hdrs = HEADERS.get(sheet_name, [])
            if values:
                # Align to headers, drop the header row if present
                if values[0] == hdrs:
                    rows = values[1:]
                else:
                    rows = values
                df = pd.DataFrame(rows, columns=hdrs[:len(rows[0])] if rows else hdrs)
            else:
                df = pd.DataFrame(columns=hdrs)
            out[sheet_name] = df
        # Ensure all sheets present
        for s in SHEETS:
            out.setdefault(s, pd.DataFrame(columns=HEADERS[s]))
        return out
    except Exception:
        # Fallback: read one by one (still cached)
        out = {}
        for s in SHEETS:
            ws = spread.worksheet(s)
            rows = _with_retry(ws.get_all_values)
            hdrs = HEADERS[s]
            if rows:
                if rows[0] == hdrs:
                    data = rows[1:]
                else:
                    data = rows
                df = pd.DataFrame(data, columns=hdrs[:len(data[0])] if data else hdrs)
            else:
                df = pd.DataFrame(columns=hdrs)
            out[s] = df
        return out

def clear_cache():
    _batch_read_all.clear()  # only clear our batched cache

# ---------- Public API used by views ----------
def read_df(sheet_name: str) -> pd.DataFrame:
    return _batch_read_all().get(sheet_name, pd.DataFrame(columns=HEADERS[sheet_name]))

def append_row(sheet_name: str, row: dict):
    gc = get_client()
    spread = get_spreadsheet(gc)
    ws = spread.worksheet(sheet_name)
    headers = HEADERS[sheet_name]
    values = [row.get(h, "") for h in headers]
    _with_retry(ws.append_row, values, value_input_option="USER_ENTERED")
    clear_cache()

def write_df(sheet_name: str, df: pd.DataFrame):
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
