"""
PayPulse — Phase 4 pipeline: cleaning + feature engineering
===========================================================

Importable functions (used by the Phase 4/5 notebooks) plus a runnable script
that writes engineered tables to ``data/processed/``:

    transactions_features.csv   one row per txn + engineered columns
    customer_features.csv       one row per customer (RFM / CLV / behaviour)

Run:
    python src/features.py

Design: the raw CSVs are treated as the source layer. We audit quality, clean,
join into an analysis frame, then derive the features the brief asks for
(txn hour, day-of-week, month, weekend flag, customer tenure, high-value flag,
avg spend per customer, and more).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config as cfg

VALID_STATUSES = {"SUCCESS", "FAILED", "PENDING"}
HIGH_VALUE_QUANTILE = 0.90       # top-decile ticket = "high value"
INACTIVE_DAYS = 90               # recency threshold for churn/inactive flag


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
def load_raw() -> dict[str, pd.DataFrame]:
    """Read every raw CSV into a dict of DataFrames."""
    names = ["transactions", "customers", "merchants", "banks", "devices",
             "campaigns", "cashback"]
    return {n: pd.read_csv(cfg.RAW_DIR / f"{n}.csv") for n in names}


# --------------------------------------------------------------------------- #
# Data-quality audit
# --------------------------------------------------------------------------- #
def data_quality_report(txn: pd.DataFrame) -> pd.DataFrame:
    """Return a tidy audit table for the transactions frame."""
    n = len(txn)
    ts = pd.to_datetime(txn["txn_timestamp"], errors="coerce")
    checks = {
        "rows": n,
        "duplicate_txn_ids": int(txn["transaction_id"].duplicated().sum()),
        "full_duplicate_rows": int(txn.duplicated().sum()),
        "missing_customer_id": int(txn["customer_id"].isna().sum()),
        "missing_amount": int(txn["amount"].isna().sum()),
        "non_positive_amount": int((txn["amount"] <= 0).sum()),
        "invalid_timestamps": int(ts.isna().sum()),
        "invalid_status": int((~txn["status"].isin(VALID_STATUSES)).sum()),
        # failure_reason SHOULD be null unless FAILED — flag violations
        "reason_without_failure": int(((txn["status"] != "FAILED")
                                       & txn["failure_reason"].notna()).sum()),
        "failure_without_reason": int(((txn["status"] == "FAILED")
                                       & txn["failure_reason"].isna()).sum()),
    }
    return pd.DataFrame({"check": list(checks), "value": list(checks.values())})


def clean_transactions(txn: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply standard cleaning; return (clean_df, actions_taken)."""
    actions: dict[str, int] = {}
    df = txn.copy()

    before = len(df)
    df = df.drop_duplicates(subset="transaction_id")
    actions["dropped_duplicate_ids"] = before - len(df)

    # Type conversions.
    df["txn_dt"] = pd.to_datetime(df["txn_timestamp"], errors="coerce")
    actions["dropped_bad_timestamps"] = int(df["txn_dt"].isna().sum())
    df = df[df["txn_dt"].notna()]

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    bad_amt = df["amount"].isna() | (df["amount"] <= 0)
    actions["dropped_bad_amounts"] = int(bad_amt.sum())
    df = df[~bad_amt]

    # Normalise status casing / whitespace; drop unknowns.
    df["status"] = df["status"].str.upper().str.strip()
    bad_status = ~df["status"].isin(VALID_STATUSES)
    actions["dropped_bad_status"] = int(bad_status.sum())
    df = df[~bad_status]

    return df.reset_index(drop=True), actions


# --------------------------------------------------------------------------- #
# Join + feature engineering
# --------------------------------------------------------------------------- #
def build_analysis_frame(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Clean transactions and join the dimensions needed for analysis."""
    txn, _ = clean_transactions(raw["transactions"])

    merch = raw["merchants"][["merchant_id", "merchant_name", "category",
                              "commission_rate", "state", "city"]].rename(
        columns={"category": "merchant_category",
                 "state": "merchant_state", "city": "merchant_city"})
    cust = raw["customers"][["customer_id", "age", "gender", "state", "city",
                             "registration_date"]].rename(
        columns={"state": "customer_state", "city": "customer_city"})
    banks = raw["banks"][["bank_id", "bank_name", "bank_type"]]
    dev = raw["devices"][["device_id", "os_name", "os_version"]]

    df = (txn
          .merge(merch, on="merchant_id", how="left")
          .merge(cust, on="customer_id", how="left")
          .merge(banks, on="bank_id", how="left")
          .merge(dev, on="device_id", how="left"))
    return df


def engineer_transaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-transaction engineered columns."""
    df = df.copy()
    dt = df["txn_dt"]

    # Temporal features.
    df["txn_hour"] = dt.dt.hour
    df["txn_day"] = dt.dt.day
    df["txn_month"] = dt.dt.month
    df["txn_year"] = dt.dt.year
    df["txn_year_month"] = dt.dt.strftime("%Y-%m")
    df["txn_dow"] = dt.dt.dayofweek                    # 0=Mon
    df["txn_day_name"] = dt.dt.day_name()
    df["is_weekend"] = (df["txn_dow"] >= 5).astype(int)

    # Outcome features.
    df["is_success"] = (df["status"] == "SUCCESS").astype(int)
    df["is_failed"] = (df["status"] == "FAILED").astype(int)

    # Money features.
    df["revenue"] = np.where(df["is_success"] == 1,
                             (df["amount"] * df["commission_rate"]).round(2), 0.0)
    hv_threshold = df["amount"].quantile(HIGH_VALUE_QUANTILE)
    df["high_value_flag"] = (df["amount"] >= hv_threshold).astype(int)
    df["ticket_band"] = pd.cut(
        df["amount"],
        bins=[0, 200, 500, 1000, 3000, 10000, np.inf],
        labels=["<200", "200-500", "500-1k", "1k-3k", "3k-10k", "10k+"])

    # Time-of-day bucket (useful for EDA & modelling).
    df["daypart"] = pd.cut(
        df["txn_hour"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["Night", "Morning", "Afternoon", "Evening", "LateEve"])
    return df


def engineer_customer_features(txn_feat: pd.DataFrame,
                               customers: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to one row per customer: CLV / RFM / behaviour features."""
    data_max = txn_feat["txn_dt"].max()

    succ = txn_feat[txn_feat["is_success"] == 1]
    g = txn_feat.groupby("customer_id")
    gs = succ.groupby("customer_id")

    feats = pd.DataFrame({
        "n_txns": g.size(),
        "n_success": g["is_success"].sum(),
        "n_failed": g["is_failed"].sum(),
        "first_txn": g["txn_dt"].min(),
        "last_txn": g["txn_dt"].max(),
        "distinct_merchants": g["merchant_id"].nunique(),
        "high_value_txns": g["high_value_flag"].sum(),
        "lifetime_spend": gs["amount"].sum(),
        "avg_ticket": gs["amount"].mean(),
        "revenue_contributed": g["revenue"].sum(),
    })
    feats["success_rate"] = (feats["n_success"] / feats["n_txns"]).round(4)
    feats["high_value_share"] = (feats["high_value_txns"] / feats["n_txns"]).round(4)
    feats["lifetime_spend"] = feats["lifetime_spend"].fillna(0)
    feats["avg_ticket"] = feats["avg_ticket"].fillna(0)

    # Recency (days since last transaction, relative to the latest data point).
    feats["recency_days"] = (data_max - feats["last_txn"]).dt.days
    feats["active_lifespan_days"] = (feats["last_txn"] - feats["first_txn"]).dt.days
    feats["is_inactive"] = (feats["recency_days"] > INACTIVE_DAYS).astype(int)

    # Tenure from registration date.
    cust = customers.set_index("customer_id")
    reg = pd.to_datetime(cust["registration_date"])
    feats = feats.join(reg.rename("registration_date"))
    feats["tenure_days"] = (data_max - feats["registration_date"]).dt.days
    feats["age"] = cust["age"]
    feats["gender"] = cust["gender"]
    feats["state"] = cust["state"]

    # ---- RFM scoring (1-5; 5 = best) + segment label ----
    # rank(method='first') breaks ties so qcut always finds 5 clean bins.
    feats["r_score"] = pd.qcut(feats["recency_days"].rank(method="first"),
                               5, labels=[5, 4, 3, 2, 1]).astype(int)   # recent = high
    feats["f_score"] = pd.qcut(feats["n_txns"].rank(method="first"),
                               5, labels=[1, 2, 3, 4, 5]).astype(int)   # frequent = high
    feats["m_score"] = pd.qcut(feats["lifetime_spend"].rank(method="first"),
                               5, labels=[1, 2, 3, 4, 5]).astype(int)   # big spend = high
    r, f = feats["r_score"], feats["f_score"]
    feats["segment"] = np.select(
        [(r >= 4) & (f >= 4),
         (r >= 4) & (f < 4),
         (r <= 2) & (f >= 4),
         (r <= 2) & (f < 3)],
        ["Champions", "Promising / New", "At Risk (was loyal)", "Hibernating / Churned"],
        default="Needs Attention")

    return feats.reset_index()


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_all():
    """Full pipeline -> (txn_features, customer_features)."""
    raw = load_raw()
    frame = build_analysis_frame(raw)
    txn_feat = engineer_transaction_features(frame)
    cust_feat = engineer_customer_features(txn_feat, raw["customers"])
    return txn_feat, cust_feat


def main() -> None:
    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw()

    print("Phase 4 - cleaning + feature engineering")
    print("-" * 60)
    audit = data_quality_report(raw["transactions"])
    issues = audit[(audit["check"] != "rows") & (audit["value"] > 0)]
    print(f"  data-quality issues found: {len(issues)}")
    if len(issues):
        print(issues.to_string(index=False))

    frame = build_analysis_frame(raw)
    txn_feat = engineer_transaction_features(frame)
    cust_feat = engineer_customer_features(txn_feat, raw["customers"])

    # Drop the heavy datetime object before CSV (keep ISO string instead).
    out_txn = txn_feat.copy()
    out_txn["txn_dt"] = out_txn["txn_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    out_txn.to_csv(cfg.PROCESSED_DIR / "transactions_features.csv", index=False)
    cust_feat.to_csv(cfg.PROCESSED_DIR / "customer_features.csv", index=False)

    print("-" * 60)
    print(f"  transactions_features: {len(txn_feat):>7,} rows, {txn_feat.shape[1]} cols")
    print(f"  customer_features    : {len(cust_feat):>7,} rows, {cust_feat.shape[1]} cols")
    print(f"  new txn features     : txn_hour, txn_dow, is_weekend, high_value_flag,")
    print(f"                         ticket_band, daypart, revenue ...")
    print(f"  customer features    : lifetime_spend, avg_ticket, success_rate,")
    print(f"                         recency_days, tenure_days, is_inactive ...")
    print(f"  written to: {cfg.PROCESSED_DIR}")


if __name__ == "__main__":
    main()
