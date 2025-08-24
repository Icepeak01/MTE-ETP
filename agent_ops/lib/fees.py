import pandas as pd

def coerce_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
    return df

def fee_from_tiers(amount, df_tiers: pd.DataFrame) -> float:
    # Ranges semantics: [min, max] inclusive for first; (prev_max, next_max] for next rows
    df = df_tiers.copy()
    df = coerce_numeric(df, ["min_amount","max_amount","fee"])
    df = df.sort_values(["min_amount","max_amount"])
    # Find the first row where amount >= min and amount <= max
    for _, r in df.iterrows():
        mn, mx, fee = float(r["min_amount"]), float(r["max_amount"]), float(r["fee"])
        if amount >= mn and amount <= mx:
            return fee
    return 0.0

def bill_fee(bill_type: str, df_bills: pd.DataFrame) -> float:
    df = df_bills.copy()
    if "bill_type" not in df.columns or "fee" not in df.columns: return 0.0
    row = df[df["bill_type"].str.lower() == str(bill_type).lower()]
    if row.empty: return 0.0
    try:
        return float(row.iloc[0]["fee"])
    except Exception:
        return 0.0

def charging_fee(category: str, df_charge: pd.DataFrame) -> float:
    df = df_charge.copy()
    if "category" not in df.columns or "fee" not in df.columns: return 0.0
    row = df[df["category"].str.lower() == str(category).lower()]
    if row.empty: return 0.0
    try:
        return float(row.iloc[0]["fee"])
    except Exception:
        return 0.0