# PayPulse — Phase 4 & 5 Findings

Results from [`notebooks/phase4_python_analytics.ipynb`](../notebooks/phase4_python_analytics.ipynb)
and [`notebooks/phase5_statistical_analysis.ipynb`](../notebooks/phase5_statistical_analysis.ipynb)
(both executed with outputs embedded). Figures are saved under `reports/figures/`.
Dataset: 250,001 transactions, 217,067 successful, 7,747 active customers.

---

## Phase 4 — Python Analytics

### Data quality
The source data passes **every** audit check (0 duplicates, 0 missing keys, 0
invalid timestamps, 0 bad statuses). The cleaning toolkit
(`features.clean_transactions`) is demonstrated on a deliberately corrupted
sample — it drops duplicate IDs, coerces/removes bad timestamps and non-positive
amounts, and normalises status values.

### Feature engineering (written to `data/processed/`)
- **Transaction level** (`transactions_features.csv`, 39 cols): `txn_hour`,
  `txn_dow`, `txn_day_name`, `txn_month`, `is_weekend`, `is_success`, `revenue`,
  `high_value_flag` (top-decile ticket), `ticket_band`, `daypart`.
- **Customer level** (`customer_features.csv`, 21 cols): `n_txns`,
  `lifetime_spend`, `avg_ticket`, `success_rate`, `high_value_share`,
  `recency_days`, `tenure_days`, `is_inactive`, `distinct_merchants`,
  `revenue_contributed`.

### EDA highlights
- **Amounts** are heavily right-skewed (raw skew **5.28**) but the log transform
  is near-symmetric — log-normal behaviour.
- **Growth** compounds strongly; **evening (~19:00)** is the daily peak.
- **Revenue** concentrates in Electronics, Travel, and E-commerce.
- **Regional:** Maharashtra, Karnataka, Delhi lead GPV.
- **Failures** are led by Payments banks and by "Insufficient Funds" /
  "Bank Server Down".

---

## Phase 5 — Statistical Analysis

| # | Test | Statistic | Result |
|---|------|-----------|--------|
| 1 | Distribution shape | raw skew 5.28 / log skew 0.34 | Log-normal confirmed |
| 2 | Outliers (IQR) | 20,403 (9.40%) | High-value tail flagged |
| 2 | Outliers (Z>3) | 4,518 (2.08%) | Genuine large tickets, not errors |
| 3 | Mean-ticket 95% CI (t) | ₹1,408.22 – ₹1,425.99 | Matches bootstrap CI |
| 4 | Corr: `n_txns` vs `lifetime_spend` | r = **0.887**, p ≈ 0 | Frequency drives value |
| 4 | Corr: `tenure_days` vs `lifetime_spend` | r = 0.257, p ≈ 1e-117 | Weak but significant |
| 5 | Weekend vs weekday ticket (Welch t) | t = −1.37, **p = 0.171** | **Fail to reject H0** — no weekend effect |
| 6 | Category ticket size (ANOVA) | F = **19,709**, p ≈ 0 | Reject H0 — category matters strongly |
| 7 | Outcome × bank type (χ²) | χ² = 3,084, p ≈ 0, V = 0.079 | Reject H0 — Payments banks fail most |
| 8 | Failure × OS family (χ²) | χ² = 0.48, **p = 0.488** | Independent at OS level |

### Key statistical conclusions
1. **Ticket size is log-normal** — parametric tests and modelling should use the
   log scale.
2. **Frequency, not tenure, drives customer value** (r = 0.89 vs 0.26). Retention
   and re-engagement programmes beat simply acquiring long-tenured users.
3. **No weekend effect** on ticket size — a legitimate negative result; don't
   over-index weekend promotions on basket size.
4. **Merchant category dominates ticket size** (ANOVA F ≈ 19.7k) — segment revenue
   models by category.
5. **Bank type is materially linked to failure** (Payments **18.0%** vs Public
   **14.7%** vs Private **8.2%**). Routing/retry logic that steers away from weak
   rails is the single highest-leverage reliability lever.
6. **OS family is *not* linked to failure** (p = 0.49) — the reliability gap is at
   the older-Android-*version* level, which pools away across all Android. Lesson:
   test at the right granularity.

---

## Business implications (for Phase 6 dashboard & recommendations)
- **Reduce failures** by prioritising smart retries on high-failure banks
  (Payments/Public) — directly recovers GPV and MDR revenue.
- **Grow value** via frequency (offers that increase transaction count), since
  frequency correlates far more with lifetime spend than tenure.
- **Target retention** at the ~21% inactive (>90-day) base surfaced in Phase 3/4.
- **Model revenue by category**, given the strong category effect on ticket size.
