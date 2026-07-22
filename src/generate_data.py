from __future__ import annotations

import numpy as np
import pandas as pd

import config as cfg


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _weighted(rng, items, weights, size):
    """Sample `size` values from `items` with the given (unnormalised) weights."""
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    idx = rng.choice(len(items), size=size, p=w)
    return np.asarray(items, dtype=object)[idx]


def _month_range(start: str, end: str) -> pd.DatetimeIndex:
    """Month-start dates covering [start, end] inclusive."""
    return pd.date_range(pd.Timestamp(start).replace(day=1),
                         pd.Timestamp(end).replace(day=1), freq="MS")


def _fmt(kind: str, arr) -> np.ndarray:
    """Vectorised ID formatting, e.g. 1 -> 'CUST00001'."""
    fmt = cfg.ID_FORMATS[kind]
    return np.array([fmt.format(int(i)) for i in arr], dtype=object)


# --------------------------------------------------------------------------- #
# Dimension tables
# --------------------------------------------------------------------------- #
def build_banks() -> pd.DataFrame:
    rows = []
    for i, b in enumerate(cfg.BANKS, start=1):
        rows.append({
            "bank_id": cfg.ID_FORMATS["bank"].format(i),
            "bank_name": b["bank_name"],
            "bank_type": b["bank_type"],
            "market_share": b["market_share"],
            "base_failure_rate": b["base_failure"],
        })
    return pd.DataFrame(rows)


def build_devices(rng, n: int) -> pd.DataFrame:
    """One device per customer (1:1). device_id aligns with customer index."""
    os_names = _weighted(rng, list(cfg.OS_DISTRIBUTION), list(cfg.OS_DISTRIBUTION.values()), n)
    versions = np.empty(n, dtype=object)
    models = np.empty(n, dtype=object)

    is_android = os_names == "Android"
    n_and = int(is_android.sum())
    n_ios = n - n_and

    versions[is_android] = _weighted(rng, cfg.ANDROID_VERSIONS, cfg.ANDROID_VERSION_WEIGHTS, n_and)
    models[is_android] = rng.choice(cfg.ANDROID_MODELS, size=n_and)
    versions[~is_android] = _weighted(rng, cfg.IOS_VERSIONS, cfg.IOS_VERSION_WEIGHTS, n_ios)
    models[~is_android] = rng.choice(cfg.IOS_MODELS, size=n_ios)

    return pd.DataFrame({
        "device_id": _fmt("device", np.arange(1, n + 1)),
        "os_name": os_names,
        "os_version": versions,
        "device_model": models,
    })


def build_merchants(rng, n: int) -> pd.DataFrame:
    cats = list(cfg.CATEGORIES)
    cat_demand = [cfg.CATEGORIES[c]["demand"] for c in cats]
    merch_cats = _weighted(rng, cats, cat_demand, n)

    # Home location weighted by state population.
    states = list(cfg.STATES)
    state_w = [cfg.STATES[s]["pop_weight"] for s in states]
    merch_states = _weighted(rng, states, state_w, n)
    merch_cities = np.array([rng.choice(cfg.STATES[s]["cities"]) for s in merch_states], dtype=object)

    # Names: <prefix> <suffix> #<n>  (n keeps them unique).
    names = []
    for i, c in enumerate(merch_cats, start=1):
        prefix = rng.choice(cfg.MERCHANT_PREFIXES[c])
        suffix = rng.choice(cfg.MERCHANT_SUFFIXES)
        names.append(f"{prefix}{suffix} #{i:04d}")

    commissions = np.array([cfg.CATEGORIES[c]["commission"] for c in merch_cats])

    # Popularity is Zipf-like: a minority of merchants capture most volume.
    popularity = rng.pareto(a=1.6, size=n) + 0.1

    return pd.DataFrame({
        "merchant_id": _fmt("merchant", np.arange(1, n + 1)),
        "merchant_name": names,
        "category": merch_cats,
        "city": merch_cities,
        "state": merch_states,
        "commission_rate": commissions,
        "popularity": popularity.round(4),
    })


def build_campaigns() -> pd.DataFrame:
    rows = []
    for i, c in enumerate(cfg.CAMPAIGNS, start=1):
        rows.append({
            "campaign_id": cfg.ID_FORMATS["campaign"].format(i),
            "campaign_name": c["campaign_name"],
            "target_category": c["target_category"],
            "start_date": c["start_date"],
            "end_date": c["end_date"],
            "cashback_rate": c["cashback_rate"],
            "max_cashback": c["max_cashback"],
        })
    return pd.DataFrame(rows)


def build_customers(rng, n: int, banks: pd.DataFrame) -> pd.DataFrame:
    # Home state / city weighted by population.
    states = list(cfg.STATES)
    state_w = [cfg.STATES[s]["pop_weight"] for s in states]
    cust_states = _weighted(rng, states, state_w, n)
    cust_cities = np.array([rng.choice(cfg.STATES[s]["cities"]) for s in cust_states], dtype=object)

    ages = rng.integers(cfg.AGE_MIN, cfg.AGE_MAX + 1, size=n)
    genders = _weighted(rng, cfg.GENDERS, cfg.GENDER_WEIGHTS, n)

    first = rng.choice(cfg.FIRST_NAMES, size=n)
    last = rng.choice(cfg.LAST_NAMES, size=n)
    names = np.array([f"{f} {l}" for f, l in zip(first, last)], dtype=object)

    # Primary bank weighted by market share.
    bank_w = banks["market_share"].to_numpy(dtype=float)
    bank_idx = rng.choice(len(banks), size=n, p=bank_w / bank_w.sum())
    primary_bank = banks["bank_id"].to_numpy()[bank_idx]

    # Registration dates: signups accelerate over time (linear-ish ramp weight).
    reg_months = _month_range(cfg.REG_START, cfg.REG_END)
    ramp = np.linspace(1.0, 3.5, len(reg_months))            # later months attract more signups
    m_idx = rng.choice(len(reg_months), size=n, p=ramp / ramp.sum())
    day_offset = rng.integers(0, 28, size=n)
    reg_dates = reg_months[m_idx] + pd.to_timedelta(day_offset, unit="D")

    # Activity weight (log-normal) -> a few heavy users drive most transactions.
    activity = rng.lognormal(mean=0.0, sigma=1.0, size=n)

    # Per-customer spend factor (some customers simply spend bigger tickets).
    spend_factor = rng.lognormal(mean=0.0, sigma=0.35, size=n)

    df = pd.DataFrame({
        "customer_id": _fmt("customer", np.arange(1, n + 1)),
        "customer_name": names,
        "age": ages,
        "gender": genders,
        "city": cust_cities,
        "state": cust_states,
        "registration_date": reg_dates.strftime("%Y-%m-%d"),
        "primary_bank_id": primary_bank,
        "device_id": _fmt("device", np.arange(1, n + 1)),   # 1:1 with devices table
        # --- internal columns (dropped before saving) ---
        "_reg_ts": reg_dates,
        "_activity": activity,
        "_spend": spend_factor,
    })

    # Churn: a share of customers go inactive some months after registration.
    churn_ts = pd.Series(pd.NaT, index=df.index)
    churned = rng.random(n) < cfg.CHURN_RATE
    # Active lifespan of 3-20 months after registration for churned users.
    lifespan = rng.integers(3, 20, size=int(churned.sum()))
    churn_ts.loc[churned] = (
        df.loc[churned, "_reg_ts"].to_numpy() + pd.to_timedelta(lifespan * 30, unit="D")
    )
    df["_churn_ts"] = churn_ts
    return df


# --------------------------------------------------------------------------- #
# Fact table: transactions (month-by-month)
# --------------------------------------------------------------------------- #
def build_transactions(rng, customers: pd.DataFrame, merchants: pd.DataFrame,
                       banks: pd.DataFrame, old_os_flag: np.ndarray) -> pd.DataFrame:
    months = _month_range(cfg.TXN_START, cfg.TXN_END)
    n_months = len(months)

    # --- 1. size each month from the active base * compounding engagement ------
    cust_reg = customers["_reg_ts"].to_numpy()
    cust_churn = customers["_churn_ts"].to_numpy()
    activity = customers["_activity"].to_numpy()

    month_starts = months.to_numpy()
    month_ends = (months + pd.offsets.MonthEnd(0)).to_numpy()

    active_masks = []
    raw_volume = np.zeros(n_months)
    for m in range(n_months):
        # Active = registered on/before month end AND not churned before month start.
        registered = cust_reg <= month_ends[m]
        not_churned = pd.isna(cust_churn) | (cust_churn >= month_starts[m])
        mask = registered & not_churned
        active_masks.append(mask)
        engagement = (1 + cfg.MONTHLY_ENGAGEMENT_GROWTH) ** m
        raw_volume[m] = activity[mask].sum() * engagement

    # Scale so the totals land near TARGET_TRANSACTIONS.
    scale = cfg.TARGET_TRANSACTIONS / raw_volume.sum()
    month_counts = np.round(raw_volume * scale).astype(int)

    # --- 2. pre-compute merchant sampling data --------------------------------
    m_pop = merchants["popularity"].to_numpy(dtype=float)
    m_pop = m_pop / m_pop.sum()
    m_ids = merchants["merchant_id"].to_numpy()
    m_cat = merchants["category"].to_numpy()
    m_comm = merchants["commission_rate"].to_numpy()
    cat_ticket = {c: cfg.CATEGORIES[c]["avg_ticket"] for c in cfg.CATEGORIES}

    # Per-customer static lookups (indexed positionally).
    c_ids = customers["customer_id"].to_numpy()
    c_bank = customers["primary_bank_id"].to_numpy()
    c_device = customers["device_id"].to_numpy()
    c_state = customers["state"].to_numpy()
    c_spend = customers["_spend"].to_numpy()
    state_affluence = np.array([cfg.STATES[s]["affluence"] for s in c_state])

    # Bank base failure lookup.
    bank_fail = dict(zip(banks["bank_id"], banks["base_failure_rate"]))
    bank_troubled = {bid: (bf > cfg.TROUBLED_BANK_THRESHOLD) for bid, bf in bank_fail.items()}

    # `old_os_flag` (Android 11/12) is passed in, aligned 1:1 with customers.

    hour_vals = np.arange(24)
    hour_w = np.array(cfg.HOUR_WEIGHTS, dtype=float)
    hour_w = hour_w / hour_w.sum()

    frames = []
    txn_counter = 0
    for m in range(n_months):
        n = int(month_counts[m])
        if n == 0:
            continue
        mask = active_masks[m]
        pos = np.nonzero(mask)[0]                        # positional indices of active customers
        act = activity[pos]
        pick = rng.choice(pos, size=n, p=act / act.sum())   # customers for this month

        # Timestamp within the month.
        days_in_month = pd.Timestamp(month_ends[m]).day
        day = rng.integers(1, days_in_month + 1, size=n)
        hour = _weighted(rng, hour_vals, hour_w, n).astype(int)
        minute = rng.integers(0, 60, size=n)
        second = rng.integers(0, 60, size=n)
        base = pd.Timestamp(month_starts[m])
        ts = (pd.to_datetime(base)
              + pd.to_timedelta(day - 1, unit="D")
              + pd.to_timedelta(hour, unit="h")
              + pd.to_timedelta(minute, unit="m")
              + pd.to_timedelta(second, unit="s"))

        # Merchant + amount.
        m_pick = rng.choice(len(m_ids), size=n, p=m_pop)
        cats = m_cat[m_pick]
        tickets = np.array([cat_ticket[c] for c in cats])
        # Log-normal around the category median, scaled by affluence & spend factor.
        amt = (rng.lognormal(mean=0.0, sigma=0.55, size=n)
               * tickets
               * state_affluence[pick]
               * c_spend[pick])
        amt = np.clip(amt, 10, None).round(2)

        # Payment mode: small tickets -> QR / UPI Lite, large -> Intent.
        mode = np.empty(n, dtype=object)
        small = amt < 500
        mid = (amt >= 500) & (amt < 3000)
        large = amt >= 3000
        mode[small] = _weighted(rng, cfg.PAYMENT_MODES, [50, 8, 12, 30], int(small.sum()))
        mode[mid] = _weighted(rng, cfg.PAYMENT_MODES, [45, 25, 25, 5], int(mid.sum()))
        mode[large] = _weighted(rng, cfg.PAYMENT_MODES, [30, 50, 20, 0], int(large.sum()))

        # ---- status model ----
        banks_row = c_bank[pick]
        p_fail = np.array([bank_fail[b] for b in banks_row])
        p_fail = p_fail + np.minimum(amt / 100_000, 0.06)            # high-value risk
        peak = np.isin(hour, list(cfg.PEAK_HOURS))
        p_fail = p_fail + peak * cfg.PEAK_HOUR_FAILURE_BUMP           # congestion
        p_fail = p_fail + old_os_flag[pick] * cfg.OLD_OS_FAILURE_BUMP  # device effect
        p_fail = np.clip(p_fail + rng.normal(0, 0.01, n), 0.005, 0.6)

        roll = rng.random(n)
        is_fail = roll < p_fail
        is_pending = (~is_fail) & (rng.random(n) < cfg.PENDING_RATE)
        status = np.where(is_fail, "FAILED", np.where(is_pending, "PENDING", "SUCCESS"))

        # Failure reasons (troubled banks skew to infra failures).
        reason = np.empty(n, dtype=object)
        reason[:] = None
        fail_pos = np.nonzero(is_fail)[0]
        if fail_pos.size:
            troubled = np.array([bank_troubled[b] for b in banks_row[fail_pos]])
            rh_items = list(cfg.FAILURE_REASONS_HEALTHY)
            rh_w = list(cfg.FAILURE_REASONS_HEALTHY.values())
            rt_items = list(cfg.FAILURE_REASONS_TROUBLED)
            rt_w = list(cfg.FAILURE_REASONS_TROUBLED.values())
            r = np.empty(fail_pos.size, dtype=object)
            n_t = int(troubled.sum())
            n_h = fail_pos.size - n_t
            if n_h:
                r[~troubled] = _weighted(rng, rh_items, rh_w, n_h)
            if n_t:
                r[troubled] = _weighted(rng, rt_items, rt_w, n_t)
            reason[fail_pos] = r

        ids = _fmt("txn", np.arange(txn_counter + 1, txn_counter + n + 1))
        txn_counter += n

        frames.append(pd.DataFrame({
            "transaction_id": ids,
            "customer_id": c_ids[pick],
            "merchant_id": m_ids[m_pick],
            "bank_id": banks_row,
            "device_id": c_device[pick],
            "amount": amt,
            "status": status,
            "failure_reason": reason,
            "payment_mode": mode,
            "txn_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            # keep numeric commission for cashback / revenue steps
            "_commission": m_comm[m_pick],
            "_category": cats,
            "_ts": ts,
        }))

    txns = pd.concat(frames, ignore_index=True)
    return txns


def build_cashback(rng, txns: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
    """Attach cashback to eligible SUCCESSFUL transactions during live campaigns."""
    rows = []
    cb_counter = 0
    succ = txns[txns["status"] == "SUCCESS"]
    for _, camp in campaigns.iterrows():
        start = pd.Timestamp(camp["start_date"])
        end = pd.Timestamp(camp["end_date"]) + pd.Timedelta(days=1)
        elig = succ[(succ["_category"] == camp["target_category"])
                    & (succ["_ts"] >= start) & (succ["_ts"] < end)]
        if elig.empty:
            continue
        # `attach_rate` from config (indexed by campaign order).
        attach = cfg.CAMPAIGNS[int(camp["campaign_id"][-2:]) - 1]["attach_rate"]
        take = elig.sample(frac=attach, random_state=int(cfg.SEED + cb_counter))
        cb_amt = np.minimum(take["amount"].to_numpy() * camp["cashback_rate"],
                            camp["max_cashback"]).round(2)
        ids = _fmt("cashback", np.arange(cb_counter + 1, cb_counter + len(take) + 1))
        cb_counter += len(take)
        rows.append(pd.DataFrame({
            "cashback_id": ids,
            "transaction_id": take["transaction_id"].to_numpy(),
            "campaign_id": camp["campaign_id"],
            "cashback_amount": cb_amt,
            "cashback_date": take["_ts"].dt.strftime("%Y-%m-%d").to_numpy(),
        }))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["cashback_id", "transaction_id", "campaign_id", "cashback_amount", "cashback_date"])


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    rng = np.random.default_rng(cfg.SEED)
    cfg.RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"PayPulse data generation  (seed={cfg.SEED})")
    print("-" * 60)

    banks = build_banks()
    devices = build_devices(rng, cfg.N_CUSTOMERS)
    merchants = build_merchants(rng, cfg.N_MERCHANTS)
    campaigns = build_campaigns()
    customers = build_customers(rng, cfg.N_CUSTOMERS, banks)

    # Old-OS flag aligned positionally with customers (device 1:1).
    old_os_flag = ((devices["os_name"] == "Android")
                   & (devices["os_version"].isin(["11", "12"]))).to_numpy()

    print(f"  banks       : {len(banks):>7,}")
    print(f"  devices     : {len(devices):>7,}")
    print(f"  merchants   : {len(merchants):>7,}")
    print(f"  campaigns   : {len(campaigns):>7,}")
    print(f"  customers   : {len(customers):>7,}")
    print("  transactions: generating month-by-month ...")

    txns = build_transactions(rng, customers, merchants, banks, old_os_flag)
    cashback = build_cashback(rng, txns, campaigns)

    # ----- drop internal helper columns before saving -----
    customers_out = customers.drop(columns=["_reg_ts", "_activity", "_spend", "_churn_ts"])
    txns_out = txns.drop(columns=["_commission", "_category", "_ts"])

    # ----- write CSVs -----
    banks.to_csv(cfg.RAW_DIR / "banks.csv", index=False)
    devices.to_csv(cfg.RAW_DIR / "devices.csv", index=False)
    merchants.to_csv(cfg.RAW_DIR / "merchants.csv", index=False)
    campaigns.to_csv(cfg.RAW_DIR / "campaigns.csv", index=False)
    customers_out.to_csv(cfg.RAW_DIR / "customers.csv", index=False)
    txns_out.to_csv(cfg.RAW_DIR / "transactions.csv", index=False)
    cashback.to_csv(cfg.RAW_DIR / "cashback.csv", index=False)

    # ----- summary -----
    succ = txns[txns["status"] == "SUCCESS"]
    gpv = succ["amount"].sum()
    revenue = (succ["amount"] * succ["_commission"]).sum()
    sr = len(succ) / len(txns) * 100
    print("-" * 60)
    print(f"  transactions: {len(txns):>7,}")
    print(f"  cashback    : {len(cashback):>7,}")
    print(f"  date range  : {txns['_ts'].min():%Y-%m-%d} -> {txns['_ts'].max():%Y-%m-%d}")
    print(f"  success rate: {sr:5.2f}%")
    print(f"  GPV (INR)   : {gpv:>16,.0f}")
    print(f"  revenue(INR): {revenue:>16,.0f}")
    print(f"  cashback    : {cashback['cashback_amount'].sum():>16,.0f}")
    print("-" * 60)
    print(f"CSVs written to: {cfg.RAW_DIR}")


if __name__ == "__main__":
    main()
