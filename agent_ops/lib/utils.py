# lib/utils.py
from datetime import datetime
from pytz import timezone
import streamlit as st
import pandas as pd
from lib.sheets import read_df, write_df

TZ = timezone("Africa/Lagos")

def today_str():
    return datetime.now(TZ).date().isoformat()

def now_iso():
    return datetime.now(TZ).isoformat()

def naira(x):
    try:
        return f"₦{float(x):,.2f}"
    except Exception:
        return x

def new_id(prefix="tx"):
    return f"{prefix}_{datetime.now(TZ).strftime('%Y%m%d%H%M%S%f')}"

# ---- config helpers (also stores simple flags in config_prices) ----
def get_price(key: str, default=0.0):
    cfg = read_df("config_prices")
    row = cfg[cfg["key"] == key]
    if row.empty: return default
    try: return float(row.iloc[0]["value"])
    except Exception: return default

def set_price(key: str, value):
    cfg = read_df("config_prices")
    if cfg.empty:
        cfg = pd.DataFrame({"key":[key], "value":[value]})
    else:
        if key in cfg["key"].values:
            cfg.loc[cfg["key"]==key, "value"] = value
        else:
            cfg = pd.concat([cfg, pd.DataFrame({"key":[key], "value":[value]})], ignore_index=True)
    write_df("config_prices", cfg)

def get_flag(key: str, default=False):
    val = str(get_price(key, 1 if default else 0)).strip().lower()
    return val in ("1","true","yes","y","on")

def set_flag(key: str, value: bool):
    set_price(key, 1 if value else 0)