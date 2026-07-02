-- ==========================================================================
-- 03 · MERCHANT ANALYTICS
-- ==========================================================================
-- Merchant revenue contribution, category performance, and rankings.
-- Demonstrates RANK / DENSE_RANK, window share-of-total, and HAVING.
-- ==========================================================================


-- 3.1 — Top 10 merchants by revenue -------------------------------------------
SELECT
    merchant_id,
    merchant_name,
    merchant_category,
    COUNT(*)                                                 AS txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gpv,
    ROUND(SUM(revenue), 2)                                   AS revenue,
    RANK() OVER (ORDER BY SUM(revenue) DESC)                 AS revenue_rank
FROM v_transaction_enriched
GROUP BY merchant_id
ORDER BY revenue DESC
LIMIT 10;


-- 3.2 — Category performance with share of total revenue ----------------------
SELECT
    merchant_category,
    COUNT(DISTINCT merchant_id)                              AS merchants,
    COUNT(*)                                                 AS txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gpv,
    ROUND(SUM(revenue), 0)                                   AS revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS pct_of_total_revenue,
    ROUND(100.0 * SUM(is_success) / COUNT(*), 2)            AS success_rate_pct,
    ROUND(AVG(CASE WHEN status='SUCCESS' THEN amount END), 0) AS avg_ticket
FROM v_transaction_enriched
GROUP BY merchant_category
ORDER BY revenue DESC;


-- 3.3 — Top merchant per category (ROW_NUMBER partitioned) --------------------
WITH ranked AS (
    SELECT
        merchant_category,
        merchant_name,
        SUM(revenue)                                       AS revenue,
        ROW_NUMBER() OVER (PARTITION BY merchant_category
                           ORDER BY SUM(revenue) DESC)      AS rn
    FROM v_transaction_enriched
    GROUP BY merchant_category, merchant_id
)
SELECT merchant_category, merchant_name, ROUND(revenue, 0) AS revenue
FROM ranked
WHERE rn = 1
ORDER BY revenue DESC;


-- 3.4 — Revenue concentration: what % of merchants drive 80% of revenue? ------
-- Running cumulative revenue share ranked high-to-low (Pareto / 80-20).
WITH merch AS (
    SELECT merchant_id, SUM(revenue) AS revenue
    FROM v_transaction_enriched
    GROUP BY merchant_id
),
ranked AS (
    SELECT
        merchant_id, revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_rev,
        SUM(revenue) OVER ()                                                 AS total_rev,
        ROW_NUMBER() OVER (ORDER BY revenue DESC)                            AS rn,
        COUNT(*) OVER ()                                                     AS n_merchants
    FROM merch
)
SELECT
    MIN(rn)                                          AS merchants_to_80pct,
    (SELECT n_merchants FROM ranked LIMIT 1)         AS total_merchants,
    ROUND(100.0 * MIN(rn) / (SELECT n_merchants FROM ranked LIMIT 1), 1) AS pct_of_merchants
FROM ranked
WHERE cum_rev >= 0.80 * total_rev;


-- 3.5 — Best & worst merchant success rates (min volume filter) ---------------
SELECT
    merchant_name,
    merchant_category,
    COUNT(*)                                    AS txns,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 1)  AS success_rate_pct
FROM v_transaction_enriched
GROUP BY merchant_id
HAVING COUNT(*) >= 100
ORDER BY success_rate_pct DESC
LIMIT 10;
