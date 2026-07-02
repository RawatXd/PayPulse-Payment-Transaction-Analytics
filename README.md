# PayPulse — End-to-End UPI & Digital Payments Analytics Platform

A portfolio-grade analytics project that simulates a Data Analyst's workflow at a
digital-payments company (PhonePe / Paytm / Razorpay style). It takes **synthetic
but realistic UPI transaction data** all the way from raw records → SQL database →
analysis → dashboard-ready star schema, and surfaces the business insights a
product/finance team actually uses.

> This folder is self-contained and unrelated to the Tally reconciliation work in
> the parent directory. Everything here lives under `paypulse/`.

---

## What's built so far (the foundation)

| Phase | Deliverable | Status |
|------|-------------|--------|
| 1 · Business questions | Encoded as the SQL analysis library | ✅ |
| 2 · Database design | Synthetic data generator + SQLite schema | ✅ |
| 3 · SQL analysis | 35 business queries across 6 files | ✅ |
| 4 · Python analytics | Cleaning, EDA & feature notebook | ✅ |
| 5 · Statistical analysis | Hypothesis tests, ANOVA, chi-square notebook | ✅ |
| 6 · Dashboard prep | Import-ready Power BI star schema | ✅ |
| 6 · Power BI report | Full page-by-page build guide + DAX | ✅ guide |
| 6 · Power BI report | The `.pbix` itself | ⏳ build in Desktop |

---

## Quick start

```bash
cd paypulse
pip install -r requirements.txt

python src/generate_data.py     # 1. raw CSVs  -> data/raw/
python src/build_database.py    # 2. SQLite DB -> data/paypulse.db
python src/features.py          # 3. cleaned + engineered tables -> data/processed/
python src/export_powerbi.py    # 4. star schema -> data/powerbi/  (Phase 6 prep)
```

Then open the analysis notebooks (VS Code / Jupyter) — they are already executed
with outputs and charts embedded, and can be re-run top-to-bottom:

```
notebooks/phase4_python_analytics.ipynb      # cleaning · EDA · feature engineering
notebooks/phase5_statistical_analysis.ipynb  # CIs · correlation · t-test · ANOVA · chi-square
```

Headline findings are summarised in [`reports/PHASE4_5_FINDINGS.md`](reports/PHASE4_5_FINDINGS.md).

The dataset is **deterministic** (`SEED = 42` in `src/config.py`) — re-running
produces byte-identical output. Generation + build takes a few seconds.

Explore the database with any SQLite tool (DB Browser for SQLite, VS Code SQLite
extension, or the `sqlite3` CLI) and run the files in `sql/analysis/`.

---

## Project structure

```
paypulse/
├── README.md
├── requirements.txt
├── src/
│   ├── config.py            # ALL reference data & tunable parameters
│   ├── generate_data.py     # Phase 2 — synthetic data -> data/raw/*.csv
│   ├── build_database.py    # Phase 2 — load CSVs -> data/paypulse.db
│   ├── features.py          # Phase 4 — cleaning + feature engineering
│   └── export_powerbi.py    # Phase 6 — star schema -> data/powerbi/*.csv
├── sql/
│   ├── schema.sql           # DDL: tables, indexes, reporting views
│   └── analysis/            # Phase 3 — the query library
│       ├── 01_executive_overview.sql
│       ├── 02_customer_analytics.sql
│       ├── 03_merchant_analytics.sql
│       ├── 04_transaction_trends.sql
│       ├── 05_failure_analytics.sql
│       └── 06_regional_analytics.sql
├── notebooks/               # Phases 4 & 5 (executed, outputs embedded)
│   ├── phase4_python_analytics.ipynb
│   └── phase5_statistical_analysis.ipynb
├── reports/                 # findings + saved figures
│   ├── PHASE4_5_FINDINGS.md
│   └── figures/*.png
└── data/                    # generated (git-ignored)
    ├── raw/                 # source CSVs
    ├── processed/           # cleaned + engineered feature tables
    ├── paypulse.db          # SQLite database
    └── powerbi/             # Power BI import folder
```

---

## Data model (star schema)

```
              ┌────────────┐        ┌────────────┐
              │   banks    │        │  devices   │
              └─────┬──────┘        └─────┬──────┘
                    │                     │
              ┌─────┴─────────────────────┴──────┐        ┌────────────┐
              │            customers              │        │ merchants  │
              └─────────────────┬─────────────────┘        └─────┬──────┘
                                │                                │
                          ┌─────┴────────────────────────────────┴─────┐
                          │              transactions                    │  ◄─ fact
                          └──────────────────────┬───────────────────────┘
                                                 │
                                          ┌──────┴──────┐   ┌────────────┐
                                          │  cashback   │──►│ campaigns  │
                                          └─────────────┘   └────────────┘
```

**Grain:** one row per UPI transaction (~250,000 rows over Jan-2023 → Dec-2025).

Two reporting **views** keep analysis concise:
- `v_transaction_enriched` — fact joined to all dimensions, with derived columns
  (date parts, `is_weekend`, `is_success`, and pre-computed `revenue`).
- `v_monthly_summary` — the monthly executive KPI backbone.

### Modelling assumptions
- **Revenue** = `amount × merchant.commission_rate` on **SUCCESSFUL** transactions
  only (the Merchant Discount Rate / platform take-rate). Failed/pending = ₹0.
- Every transaction is a **customer → merchant** payment (P2M), so each ties to a
  merchant for a clean revenue calculation. `payment_mode` captures the UPI flow
  (QR Code / Intent / Collect Request / UPI Lite).
- A customer has one **primary bank** and one **device**; transactions record the
  bank/device used, enabling bank- and device-wise failure analysis.

---

## Signals baked into the data (what the analysis will find)

The generator deliberately embeds realistic, *discoverable* patterns rather than
uniform noise:

- **Growth** — transaction volume compounds (~1.1k/month early → ~16k/month late).
- **Churn & retention** — ~28% of customers go inactive; cohort retention decays.
- **Bank-wise failures** — Payments banks (~80% success) fail far more than HDFC
  (~91%); the failure-reason mix skews to "server down / offline" for weak banks.
- **Peak hours** — bimodal daily curve, strong evening peak (~7 PM), 3 AM trough.
- **Regional skew** — Maharashtra, Karnataka, Delhi dominate revenue.
- **High-value risk** — larger tickets fail slightly more often.
- **Pareto** — a minority of merchants drive ~80% of revenue.

Tune any of these in `src/config.py` and regenerate.

---

## The SQL analysis library (Phase 3)

Each file is a set of standalone, commented queries. Highlights:

- **01 Executive** — headline KPIs, MoM growth (LAG), QoQ, payment-mode mix.
- **02 Customer** — CLV leaderboard, repeat rate, RFM segmentation (NTILE),
  inactive/churn detection, signup-cohort retention.
- **03 Merchant** — top merchants (RANK), category share of revenue, top-per-
  category (ROW_NUMBER), 80/20 revenue concentration.
- **04 Trends** — hourly/weekday patterns, 7-day moving average, running revenue,
  DAU/MAU & stickiness.
- **05 Failures** — failure rate by bank/reason/device/ticket-band/hour, GPV lost.
- **06 Regional** — state & city scorecards, share of national revenue, top
  category per state.

Techniques demonstrated: JOINs, `GROUP BY`/`HAVING`, `CASE WHEN`, CTEs, and window
functions (`RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LAG`, `NTILE`, `SUM/AVG OVER` with
frames).

---

## Phase 4 & 5 — done (see notebooks + `reports/PHASE4_5_FINDINGS.md`)

- **Phase 4** — data-quality audit + cleaning toolkit, EDA (amount distribution,
  growth, peak hours, category/regional/failure trends), and feature engineering
  (transaction hour, weekend flag, customer tenure, high-value flag, avg spend per
  customer, RFM-style customer table).
- **Phase 5** — log-normality check, IQR/Z-score outliers, mean-ticket confidence
  intervals (t + bootstrap), correlation matrix, weekend-vs-weekday t-test
  (non-significant), one-way ANOVA across categories (highly significant), and
  chi-square tests (bank type × outcome significant; OS × failure independent).

## Phase 6 — Power BI dashboard

A complete, step-by-step build guide is in
[`reports/POWERBI_BUILD_GUIDE.md`](reports/POWERBI_BUILD_GUIDE.md): data import,
the star-schema model + relationships, **every DAX measure** (KPIs, time
intelligence, RFM/CLV, failure), a ready-to-load theme
([`reports/paypulse_theme.json`](reports/paypulse_theme.json)), and exact
visual specs for all six pages (Executive / Customer / Merchant / Transaction /
Failure / Regional) plus drill-through, bookmarks, and tooltips.

Since `.pbix` is a binary Power BI Desktop format it can't be generated as code —
the guide makes assembling it mechanical (~2–3 hours). Import the `data/powerbi/`
folder to begin.
