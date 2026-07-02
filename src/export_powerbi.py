"""
PayPulse — Power BI export  (Phase 6 prep)
==========================================

Free Power BI Desktop imports CSV/Excel cleanly but needs an ODBC driver to read
SQLite directly. To keep the project friction-free, this script writes an
import-ready star schema to ``data/powerbi/``:

    dim_date.csv          calendar table for time-intelligence DAX
    fact_transactions.csv flattened fact (from v_transaction_enriched)
    dim_customers.csv     copied from raw
    dim_merchants.csv     copied from raw
    dim_banks.csv         copied from raw
    dim_devices.csv       copied from raw

In Power BI: Get Data -> Folder / Text-CSV, then wire relationships on
customer_id / merchant_id / bank_id / device_id and dim_date[date] -> fact[txn_date].

Run (after build_database.py):
    python src/export_powerbi.py
"""

from __future__ import annotations

import sqlite3

import pandas as pd

import config as cfg

OUT_DIR = cfg.DATA_DIR / "powerbi"


def build_dim_date() -> pd.DataFrame:
    dates = pd.date_range(cfg.TXN_START, cfg.TXN_END, freq="D")
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.strftime("%b"),
        "year_month": dates.strftime("%Y-%m"),
        "day": dates.day,
        "day_of_week": dates.dayofweek + 1,          # 1=Mon ... 7=Sun
        "day_name": dates.strftime("%a"),
        "week_of_year": dates.isocalendar().week.astype(int).values,
        "is_weekend": (dates.dayofweek >= 5).astype(int),
    })


def main() -> None:
    if not cfg.DB_PATH.exists():
        raise FileNotFoundError("paypulse.db not found — run build_database.py first")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(cfg.DB_PATH)
    try:
        print(f"exporting Power BI star schema -> {OUT_DIR}")

        # Calendar dimension.
        dim_date = build_dim_date()
        dim_date.to_csv(OUT_DIR / "dim_date.csv", index=False)
        print(f"  dim_date.csv          {len(dim_date):>7,} rows")

        # Flattened fact from the enriched view.
        fact = pd.read_sql_query("SELECT * FROM v_transaction_enriched", conn)
        fact.to_csv(OUT_DIR / "fact_transactions.csv", index=False)
        print(f"  fact_transactions.csv {len(fact):>7,} rows")

        # Dimension copies (clean, already generated).
        for src, dst in [("customers", "dim_customers"), ("merchants", "dim_merchants"),
                         ("banks", "dim_banks"), ("devices", "dim_devices")]:
            df = pd.read_sql_query(f"SELECT * FROM {src}", conn)
            df.to_csv(OUT_DIR / f"{dst}.csv", index=False)
            print(f"  {dst + '.csv':<21} {len(df):>7,} rows")

        # Optional: the Phase-4 engineered customer table (RFM / CLV / churn),
        # handy for the Customer Analytics page. Present only if features.py ran.
        cust_feat = cfg.PROCESSED_DIR / "customer_features.csv"
        if cust_feat.exists():
            df = pd.read_csv(cust_feat)
            df.to_csv(OUT_DIR / "customer_features.csv", index=False)
            print(f"  {'customer_features.csv':<21} {len(df):>7,} rows")
    finally:
        conn.close()
    print("done. Import the data/powerbi/ folder into Power BI Desktop.")


if __name__ == "__main__":
    main()
