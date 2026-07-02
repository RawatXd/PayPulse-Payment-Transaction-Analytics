"""
PayPulse — build the SQLite database from generated CSVs
========================================================

Steps
-----
1. Create the schema (tables, indexes, views) from ``sql/schema.sql``.
2. Bulk-load every CSV in dependency order.
3. ANALYZE + a few sanity KPIs so you can see the load succeeded.

Run (after generate_data.py):
    python src/build_database.py
"""

from __future__ import annotations

import sqlite3

import pandas as pd

import config as cfg

# CSV -> table, in FK-safe load order (parents before children).
LOAD_ORDER = [
    ("banks.csv",        "banks"),
    ("devices.csv",      "devices"),
    ("merchants.csv",    "merchants"),
    ("campaigns.csv",    "campaigns"),
    ("customers.csv",    "customers"),
    ("transactions.csv", "transactions"),
    ("cashback.csv",     "cashback"),
]


def create_schema(conn: sqlite3.Connection) -> None:
    schema_sql = cfg.SCHEMA_FILE.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    print(f"schema created from {cfg.SCHEMA_FILE.name}")


def load_tables(conn: sqlite3.Connection) -> None:
    for csv_name, table in LOAD_ORDER:
        path = cfg.RAW_DIR / csv_name
        if not path.exists():
            raise FileNotFoundError(f"missing {path} — run generate_data.py first")
        df = pd.read_csv(path)
        # Append into the pre-created schema (maps by column name).
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"  loaded {table:<13} {len(df):>7,} rows")


def sanity_checks(conn: sqlite3.Connection) -> None:
    print("-" * 60)
    print("sanity checks")
    print("-" * 60)

    # Row counts.
    for _, table in LOAD_ORDER:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<13} {n:>8,}")

    # Referential integrity: any orphan transactions?
    orphans = conn.execute("""
        SELECT COUNT(*) FROM transactions t
        LEFT JOIN customers c ON c.customer_id = t.customer_id
        WHERE c.customer_id IS NULL
    """).fetchone()[0]
    print(f"  orphan txns (should be 0): {orphans}")

    # Headline KPIs straight from the monthly view.
    print("-" * 60)
    kpi = conn.execute("""
        SELECT
            COUNT(*)                                       AS txns,
            ROUND(100.0*SUM(is_success)/COUNT(*), 2)       AS success_rate,
            ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount ELSE 0 END)) AS gpv,
            ROUND(SUM(revenue))                            AS revenue,
            COUNT(DISTINCT customer_id)                    AS active_customers
        FROM v_transaction_enriched
    """).fetchone()
    print(f"  transactions     : {kpi[0]:>12,}")
    print(f"  success rate     : {kpi[1]:>11}%")
    print(f"  GPV (INR)        : {kpi[2]:>12,.0f}")
    print(f"  revenue (INR)    : {kpi[3]:>12,.0f}")
    print(f"  active customers : {kpi[4]:>12,}")

    print("-" * 60)
    print("  success rate by bank (top failure signal):")
    rows = conn.execute("""
        SELECT bank_name,
               ROUND(100.0*SUM(is_success)/COUNT(*), 1) AS sr
        FROM v_transaction_enriched
        GROUP BY bank_name
        ORDER BY sr ASC
        LIMIT 5
    """).fetchall()
    for name, sr in rows:
        print(f"    {name:<22} {sr:>5}%")


def main() -> None:
    if cfg.DB_PATH.exists():
        cfg.DB_PATH.unlink()          # rebuild from scratch
    conn = sqlite3.connect(cfg.DB_PATH)
    try:
        print(f"building database: {cfg.DB_PATH}")
        print("-" * 60)
        create_schema(conn)
        load_tables(conn)
        conn.commit()
        conn.execute("ANALYZE")
        conn.commit()
        sanity_checks(conn)
        print("-" * 60)
        print("done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
