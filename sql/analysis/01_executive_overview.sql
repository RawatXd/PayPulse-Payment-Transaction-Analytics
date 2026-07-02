-- ==========================================================================
-- 01 · EXECUTIVE OVERVIEW
-- ==========================================================================
-- Headline KPIs a business leader checks first: volume, GPV, revenue, success
-- rate, and month-over-month growth. Every query is standalone — run one at a
-- time in the SQLite CLI / DB Browser, or feed the whole file to sqlite3.
--
-- Revenue model: PayPulse earns MDR (commission_rate) on SUCCESSFUL merchant
-- payments only. This is pre-computed as `revenue` in v_transaction_enriched.
-- ==========================================================================


-- 1.1 — All-time headline KPIs -------------------------------------------------
SELECT
    COUNT(*)                                            AS total_transactions,
    SUM(is_success)                                     AS successful_transactions,
    ROUND(100.0 * SUM(is_success) / COUNT(*), 2)        AS success_rate_pct,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gross_payment_value,
    ROUND(AVG(CASE WHEN status='SUCCESS' THEN amount END), 0) AS avg_ticket_size,
    ROUND(SUM(revenue), 0)                              AS total_revenue,
    COUNT(DISTINCT customer_id)                         AS active_customers,
    COUNT(DISTINCT merchant_id)                         AS active_merchants
FROM v_transaction_enriched;


-- 1.2 — Monthly trend: volume, GPV, revenue, success rate ---------------------
SELECT
    txn_year_month,
    COUNT(*)                                        AS txns,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 2)      AS success_rate_pct,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gpv,
    ROUND(SUM(revenue), 0)                          AS revenue,
    COUNT(DISTINCT customer_id)                     AS active_customers
FROM v_transaction_enriched
GROUP BY txn_year_month
ORDER BY txn_year_month;


-- 1.3 — Month-over-month GPV growth % (LAG window function) --------------------
WITH monthly AS (
    SELECT txn_year_month,
           SUM(CASE WHEN status='SUCCESS' THEN amount END) AS gpv
    FROM v_transaction_enriched
    GROUP BY txn_year_month
)
SELECT
    txn_year_month,
    ROUND(gpv, 0)                                             AS gpv,
    ROUND(LAG(gpv) OVER (ORDER BY txn_year_month), 0)         AS prev_month_gpv,
    ROUND(100.0 * (gpv - LAG(gpv) OVER (ORDER BY txn_year_month))
                / LAG(gpv) OVER (ORDER BY txn_year_month), 2) AS mom_growth_pct
FROM monthly
ORDER BY txn_year_month;


-- 1.4 — Quarter-on-quarter summary --------------------------------------------
SELECT
    txn_year,
    ((txn_month - 1) / 3) + 1                        AS quarter,
    COUNT(*)                                         AS txns,
    ROUND(SUM(revenue), 0)                           AS revenue,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 2)       AS success_rate_pct
FROM v_transaction_enriched
GROUP BY txn_year, quarter
ORDER BY txn_year, quarter;


-- 1.5 — Payment-mode mix (share of successful volume) -------------------------
SELECT
    payment_mode,
    COUNT(*)                                                     AS txns,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)           AS pct_of_txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0)    AS gpv
FROM v_transaction_enriched
GROUP BY payment_mode
ORDER BY txns DESC;
