-- ==========================================================================
-- 04 · TRANSACTION TRENDS  (time-series & window functions)
-- ==========================================================================
-- Daily/weekly/hourly patterns, running totals, moving averages, and DAU/MAU.
-- Showcases SUM() OVER, AVG() OVER (moving window), and date parts.
-- ==========================================================================


-- 4.1 — Hourly transaction distribution (peak-hour discovery) -----------------
SELECT
    txn_hour,
    COUNT(*)                                                AS txns,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_day,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 2)             AS success_rate_pct
FROM v_transaction_enriched
GROUP BY txn_hour
ORDER BY txn_hour;


-- 4.2 — Day-of-week pattern (weekend vs weekday) ------------------------------
SELECT
    CASE txn_dow
        WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue'
        WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri'
        WHEN 6 THEN 'Sat' END                               AS day_name,
    txn_dow,
    COUNT(*)                                                AS txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END),0) AS gpv,
    ROUND(AVG(CASE WHEN status='SUCCESS' THEN amount END),0) AS avg_ticket
FROM v_transaction_enriched
GROUP BY txn_dow
ORDER BY txn_dow;


-- 4.3 — Daily volume with 7-day moving average (window frame) -----------------
WITH daily AS (
    SELECT txn_date,
           COUNT(*)                                          AS txns,
           SUM(CASE WHEN status='SUCCESS' THEN amount END)   AS gpv
    FROM v_transaction_enriched
    GROUP BY txn_date
)
SELECT
    txn_date,
    txns,
    ROUND(AVG(txns) OVER (ORDER BY txn_date
              ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1)  AS ma7_txns,
    ROUND(gpv, 0)                                            AS gpv
FROM daily
ORDER BY txn_date DESC
LIMIT 30;


-- 4.4 — Running (cumulative) revenue total over time --------------------------
WITH monthly AS (
    SELECT txn_year_month, SUM(revenue) AS revenue
    FROM v_transaction_enriched
    GROUP BY txn_year_month
)
SELECT
    txn_year_month,
    ROUND(revenue, 0)                                        AS monthly_revenue,
    ROUND(SUM(revenue) OVER (ORDER BY txn_year_month
              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS cumulative_revenue
FROM monthly
ORDER BY txn_year_month;


-- 4.5 — Daily Active Users (DAU) and its own 7-day average --------------------
WITH dau AS (
    SELECT txn_date, COUNT(DISTINCT customer_id) AS dau
    FROM v_transaction_enriched
    GROUP BY txn_date
)
SELECT
    txn_date,
    dau,
    ROUND(AVG(dau) OVER (ORDER BY txn_date
              ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS dau_ma7
FROM dau
ORDER BY txn_date DESC
LIMIT 30;


-- 4.6 — Monthly Active Users (MAU) & stickiness (DAU/MAU) ---------------------
-- Stickiness = avg daily active users / monthly active users. Higher = more
-- habitual usage.
WITH per_month AS (
    SELECT
        txn_year_month,
        COUNT(DISTINCT customer_id)                                     AS mau,
        COUNT(DISTINCT customer_id) * 1.0 / COUNT(DISTINCT txn_date)    AS approx_dau,
        COUNT(DISTINCT txn_date)                                        AS active_days
    FROM v_transaction_enriched
    GROUP BY txn_year_month
)
SELECT
    txn_year_month,
    mau,
    ROUND(approx_dau, 0)                              AS avg_daily_active,
    ROUND(100.0 * approx_dau / mau, 1)               AS stickiness_pct
FROM per_month
ORDER BY txn_year_month;
