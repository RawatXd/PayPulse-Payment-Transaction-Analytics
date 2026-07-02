-- ==========================================================================
-- 05 · FAILURE ANALYTICS
-- ==========================================================================
-- Why do payments fail, and where? Bank-wise, reason-wise, device-wise, and
-- by ticket size / hour. This is the highest-leverage operational analysis:
-- every recovered failure is direct GPV and revenue.
-- ==========================================================================


-- 5.1 — Overall status breakdown ----------------------------------------------
SELECT
    status,
    COUNT(*)                                            AS txns,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)  AS pct
FROM v_transaction_enriched
GROUP BY status
ORDER BY txns DESC;


-- 5.2 — Failure rate by bank (ranked worst-first) -----------------------------
SELECT
    bank_name,
    bank_type,
    COUNT(*)                                              AS txns,
    SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)      AS failed,
    ROUND(100.0 * SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)/COUNT(*), 2) AS failure_rate_pct,
    RANK() OVER (ORDER BY 1.0*SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)/COUNT(*) DESC) AS worst_rank
FROM v_transaction_enriched
GROUP BY bank_id
ORDER BY failure_rate_pct DESC;


-- 5.3 — Failure reason breakdown ----------------------------------------------
SELECT
    failure_reason,
    COUNT(*)                                            AS occurrences,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)  AS pct_of_failures,
    ROUND(SUM(amount), 0)                               AS failed_gpv_at_risk
FROM v_transaction_enriched
WHERE status = 'FAILED'
GROUP BY failure_reason
ORDER BY occurrences DESC;


-- 5.4 — Reason mix by bank type (public vs private vs payments) ---------------
-- Confirms the hypothesis that troubled banks skew to infrastructure failures.
SELECT
    bank_type,
    failure_reason,
    COUNT(*)                                                        AS failures,
    ROUND(100.0 * COUNT(*) /
          SUM(COUNT(*)) OVER (PARTITION BY bank_type), 2)          AS pct_within_type
FROM v_transaction_enriched
WHERE status = 'FAILED'
GROUP BY bank_type, failure_reason
ORDER BY bank_type, failures DESC;


-- 5.5 — Failure rate by device OS & version -----------------------------------
SELECT
    os_name,
    os_version,
    COUNT(*)                                              AS txns,
    ROUND(100.0 * SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)/COUNT(*), 2) AS failure_rate_pct
FROM v_transaction_enriched
GROUP BY os_name, os_version
HAVING COUNT(*) >= 500
ORDER BY failure_rate_pct DESC;


-- 5.6 — Failure rate by ticket-size band (is high-value riskier?) -------------
SELECT
    CASE
        WHEN amount < 200   THEN 'a. <200'
        WHEN amount < 500   THEN 'b. 200-500'
        WHEN amount < 1000  THEN 'c. 500-1k'
        WHEN amount < 3000  THEN 'd. 1k-3k'
        WHEN amount < 10000 THEN 'e. 3k-10k'
        ELSE 'f. 10k+'
    END                                                   AS ticket_band,
    COUNT(*)                                              AS txns,
    ROUND(100.0 * SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)/COUNT(*), 2) AS failure_rate_pct
FROM v_transaction_enriched
GROUP BY ticket_band
ORDER BY ticket_band;


-- 5.7 — Hourly failure rate (congestion at peak hours) ------------------------
SELECT
    txn_hour,
    COUNT(*)                                              AS txns,
    ROUND(100.0 * SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)/COUNT(*), 2) AS failure_rate_pct
FROM v_transaction_enriched
GROUP BY txn_hour
ORDER BY failure_rate_pct DESC;


-- 5.8 — GPV lost to failures per month (the business case) --------------------
SELECT
    txn_year_month,
    ROUND(SUM(CASE WHEN status='FAILED' THEN amount ELSE 0 END), 0) AS gpv_lost,
    ROUND(SUM(CASE WHEN status='FAILED' THEN amount ELSE 0 END)
          * (SELECT AVG(commission_rate) FROM merchants), 0)        AS est_revenue_lost
FROM v_transaction_enriched
GROUP BY txn_year_month
ORDER BY txn_year_month;
