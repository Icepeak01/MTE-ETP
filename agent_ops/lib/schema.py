# Central schema for all worksheets and their headers

SHEETS = [
    "config_users",
    "config_prices",
    "config_fees_withdrawal",
    "config_fees_deposit",
    "config_fees_bill",
    "config_fees_charging",
    "daily_openings",
    "transactions",
    "closing_counts",
]

HEADERS = {
    "config_users": ["username", "role", "display_name", "active"],
    "config_prices": ["key", "value"],
    "config_fees_withdrawal": ["min_amount", "max_amount", "fee"],
    "config_fees_deposit": ["min_amount", "max_amount", "fee"],
    "config_fees_bill": ["bill_type", "fee"],
    "config_fees_charging": ["category", "fee"],
    "daily_openings": ["date", "attendant", "cash_open", "pos_open", "transfer_open", "gas_open_kg", "notes"],
    "transactions": [
        "id","datetime","date","user","role",
        "category","sub_type","customer_method","provider_method",
        "amount_value","gas_kg","price_per_kg","fee","total_paid_by_customer",
        "cash_delta","pos_delta","transfer_delta","gas_kg_delta",
        "note","ref"
    ],
    "closing_counts": ["date","cash_counted","gas_measured_kg","notes"]
}