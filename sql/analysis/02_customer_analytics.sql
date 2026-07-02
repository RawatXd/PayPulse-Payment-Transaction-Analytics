-- ==========================================================================
-- 02 · CUSTOMER ANALYTICS
-- ==========================================================================
-- Retention, repeat behaviour, lifetime value, segmentation, and churn.
-- Demonstrates CTEs, aggregation, NTILE, and date arithmetic.
-- ==========================================================================


-- 2.1 — Customer Lifetime Value (CLV) leaderboard -----------------------------
-- CLV proxy = total successful spend. Also shows tenure and revenue contributed.
SELECT
    c.customer_id,
    c.customer_name,
    c.state,
    COUNT(*)                                                 AS total_txns,
    SUM(t.is_success)                                        AS successful_txns,
    ROUND(SUM(CASE WHEN t.status='SUCCESS' THEN t.amount END), 0) AS lifetime_spend,
    ROUND(SUM(t.revenue), 2)                                 AS revenue_contributed,
    ROUND(julianday('now') - julianday(c.registration_date)) AS tenure_days
FROM v_transaction_enriched t
JOIN customers c ON c.customer_id = t.customer_id
GROUP BY c.customer_id
ORDER BY lifetime_spend DESC
LIMIT 20;


-- 2.2 — Repeat-customer rate --------------------------------------------------
-- What share of active customers transacted more than once?
WITH per_cust AS (
    SELECT customer_id, COUNT(*) AS txns
    FROM transactions
    GROUP BY customer_id
)
SELECT
    COUNT(*)                                                      AS active_customers,
    SUM(CASE WHEN txns > 1 THEN 1 ELSE 0 END)                     AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN txns > 1 THEN 1 ELSE 0 END)/COUNT(*), 2) AS repeat_rate_pct,
    ROUND(AVG(txns), 1)                                           AS avg_txns_per_customer
FROM per_cust;


-- 2.3 — RFM-style segmentation (Recency / Frequency / Monetary via NTILE) ------
WITH cust AS (
    SELECT
        customer_id,
        MAX(txn_date)                                    AS last_txn,
        julianday('now') - julianday(MAX(txn_date))      AS recency_days,
        COUNT(*)                                         AS frequency,
        SUM(CASE WHEN status='SUCCESS' THEN amount END)  AS monetary
    FROM v_transaction_enriched
    GROUP BY customer_id
),
scored AS (
    SELECT
        customer_id, last_txn, recency_days, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,  -- 5 = most recent
        NTILE(5) OVER (ORDER BY frequency)         AS f_score,  -- 5 = most frequent
        NTILE(5) OVER (ORDER BY monetary)          AS m_score   -- 5 = highest spend
    FROM cust
)
SELECT
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score <  4 THEN 'Promising / New'
        WHEN r_score <= 2 AND f_score >= 4 THEN 'At Risk (was loyal)'
        WHEN r_score <= 2 AND f_score <  3 THEN 'Hibernating / Churned'
        ELSE 'Needs Attention'
    END                                             AS segment,
    COUNT(*)                                         AS customers,
    ROUND(AVG(recency_days))                         AS avg_recency_days,
    ROUND(AVG(frequency), 1)                         AS avg_frequency,
    ROUND(AVG(monetary), 0)                          AS avg_monetary
FROM scored
GROUP BY segment
ORDER BY customers DESC;


-- 2.4 — Inactive / churned customers ------------------------------------------
-- Registered but no transaction in the last 90 days of available data.
WITH last_seen AS (
    SELECT c.customer_id, c.state,
           MAX(date(t.txn_timestamp)) AS last_txn
    FROM customers c
    LEFT JOIN transactions t ON t.customer_id = c.customer_id
    GROUP BY c.customer_id
),
data_max AS (SELECT MAX(date(txn_timestamp)) AS d FROM transactions)
SELECT
    COUNT(*)                                                         AS total_customers,
    SUM(CASE WHEN last_txn IS NULL THEN 1 ELSE 0 END)               AS never_transacted,
    SUM(CASE WHEN last_txn IS NOT NULL
              AND julianday((SELECT d FROM data_max)) - julianday(last_txn) > 90
             THEN 1 ELSE 0 END)                                     AS inactive_90d,
    ROUND(100.0 * SUM(CASE WHEN last_txn IS NOT NULL
              AND julianday((SELECT d FROM data_max)) - julianday(last_txn) > 90
             THEN 1 ELSE 0 END) / COUNT(*), 2)                      AS inactive_rate_pct
FROM last_seen;


-- 2.5 — Monthly signup cohort retention (activity in months since joining) -----
-- For each signup cohort (registration month), how many were still transacting
-- 0 / 1 / 3 / 6 months later. Classic cohort retention.
WITH firsts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort
    FROM customers
),
activity AS (
    SELECT DISTINCT
        t.customer_id,
        f.cohort,
        (CAST(strftime('%Y', t.txn_timestamp) AS INTEGER) * 12 + CAST(strftime('%m', t.txn_timestamp) AS INTEGER))
      - (CAST(substr(f.cohort,1,4) AS INTEGER)          * 12 + CAST(substr(f.cohort,6,2) AS INTEGER)) AS month_offset
    FROM transactions t
    JOIN firsts f ON f.customer_id = t.customer_id
)
SELECT
    cohort,
    COUNT(DISTINCT customer_id)                                              AS cohort_size,
    COUNT(DISTINCT CASE WHEN month_offset = 1 THEN customer_id END)          AS m1_active,
    COUNT(DISTINCT CASE WHEN month_offset = 3 THEN customer_id END)          AS m3_active,
    COUNT(DISTINCT CASE WHEN month_offset = 6 THEN customer_id END)          AS m6_active
FROM activity
WHERE cohort >= '2023-01'
GROUP BY cohort
ORDER BY cohort
LIMIT 24;


-- 2.6 — Demographic breakdown (age band × gender) -----------------------------
SELECT
    CASE
        WHEN customer_age < 25 THEN '18-24'
        WHEN customer_age < 35 THEN '25-34'
        WHEN customer_age < 45 THEN '35-44'
        WHEN customer_age < 55 THEN '45-54'
        ELSE '55+'
    END                                                     AS age_band,
    customer_gender,
    COUNT(DISTINCT customer_id)                             AS customers,
    COUNT(*)                                                AS txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gpv
FROM v_transaction_enriched
GROUP BY age_band, customer_gender
ORDER BY age_band, customer_gender;
