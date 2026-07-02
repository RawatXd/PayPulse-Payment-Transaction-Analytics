-- ==========================================================================
-- 06 · REGIONAL ANALYTICS
-- ==========================================================================
-- State- and city-level revenue, adoption, and success rates. Feeds the
-- interactive India map page in Power BI.
-- ==========================================================================


-- 6.1 — State-wise scorecard (revenue, GPV, success rate, customers) ----------
SELECT
    customer_state                                        AS state,
    COUNT(DISTINCT customer_id)                           AS customers,
    COUNT(*)                                              AS txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gpv,
    ROUND(SUM(revenue), 0)                                AS revenue,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 2)           AS success_rate_pct,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END)
          / COUNT(DISTINCT customer_id), 0)              AS gpv_per_customer,
    RANK() OVER (ORDER BY SUM(revenue) DESC)             AS revenue_rank
FROM v_transaction_enriched
GROUP BY customer_state
ORDER BY revenue DESC;


-- 6.2 — Top 15 cities by GPV --------------------------------------------------
SELECT
    customer_city                                         AS city,
    customer_state                                        AS state,
    COUNT(*)                                              AS txns,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount END), 0) AS gpv,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 2)           AS success_rate_pct
FROM v_transaction_enriched
GROUP BY customer_city
ORDER BY gpv DESC
LIMIT 15;


-- 6.3 — Each state's share of national revenue (window share-of-total) --------
SELECT
    customer_state                                        AS state,
    ROUND(SUM(revenue), 0)                                AS revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS pct_of_national,
    ROUND(SUM(SUM(revenue)) OVER (ORDER BY SUM(revenue) DESC
              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
          * 100.0 / SUM(SUM(revenue)) OVER (), 2)         AS cumulative_pct
FROM v_transaction_enriched
GROUP BY customer_state
ORDER BY revenue DESC;


-- 6.4 — Top category per state (what each region spends most on) --------------
WITH state_cat AS (
    SELECT
        customer_state,
        merchant_category,
        SUM(CASE WHEN status='SUCCESS' THEN amount END)   AS gpv,
        ROW_NUMBER() OVER (PARTITION BY customer_state
                           ORDER BY SUM(CASE WHEN status='SUCCESS' THEN amount END) DESC) AS rn
    FROM v_transaction_enriched
    GROUP BY customer_state, merchant_category
)
SELECT customer_state AS state, merchant_category AS top_category, ROUND(gpv, 0) AS gpv
FROM state_cat
WHERE rn = 1
ORDER BY gpv DESC;


-- 6.5 — States ranked by success rate (operational reliability) ---------------
SELECT
    customer_state                                        AS state,
    COUNT(*)                                              AS txns,
    ROUND(100.0 * SUM(is_success)/COUNT(*), 2)           AS success_rate_pct
FROM v_transaction_enriched
GROUP BY customer_state
HAVING COUNT(*) >= 1000
ORDER BY success_rate_pct DESC;
