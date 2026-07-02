-- ==========================================================================
-- PayPulse — SQLite schema  (Phase 2: Database Design)
-- ==========================================================================
-- Run automatically by src/build_database.py (via executescript), or manually:
--     sqlite3 data/paypulse.db < sql/schema.sql
--
-- Dates/timestamps are stored as ISO-8601 TEXT ('YYYY-MM-DD[ HH:MM:SS']).
-- SQLite's strftime()/date() work directly on that format.
-- ==========================================================================

PRAGMA foreign_keys = ON;

-- ---- drop in reverse-dependency order so the script is re-runnable ---------
DROP VIEW  IF EXISTS v_monthly_summary;
DROP VIEW  IF EXISTS v_transaction_enriched;
DROP TABLE IF EXISTS cashback;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS banks;

-- ---------------------------------------------------------------------------
-- Dimension tables
-- ---------------------------------------------------------------------------
CREATE TABLE banks (
    bank_id            TEXT PRIMARY KEY,
    bank_name          TEXT NOT NULL,
    bank_type          TEXT NOT NULL,          -- Public / Private / Payments
    market_share       REAL,                   -- relative %, for reference
    base_failure_rate  REAL                    -- intrinsic failure probability
);

CREATE TABLE devices (
    device_id     TEXT PRIMARY KEY,
    os_name       TEXT NOT NULL,               -- Android / iOS
    os_version    TEXT,
    device_model  TEXT
);

CREATE TABLE merchants (
    merchant_id      TEXT PRIMARY KEY,
    merchant_name    TEXT NOT NULL,
    category         TEXT NOT NULL,
    city             TEXT,
    state            TEXT,
    commission_rate  REAL NOT NULL,            -- MDR -> revenue on success
    popularity       REAL                      -- relative demand weight
);

CREATE TABLE campaigns (
    campaign_id      TEXT PRIMARY KEY,
    campaign_name    TEXT NOT NULL,
    target_category  TEXT NOT NULL,
    start_date       TEXT NOT NULL,
    end_date         TEXT NOT NULL,
    cashback_rate    REAL NOT NULL,
    max_cashback     REAL NOT NULL
);

CREATE TABLE customers (
    customer_id        TEXT PRIMARY KEY,
    customer_name      TEXT,
    age                INTEGER,
    gender             TEXT,
    city               TEXT,
    state              TEXT,
    registration_date  TEXT NOT NULL,
    primary_bank_id    TEXT REFERENCES banks(bank_id),
    device_id          TEXT REFERENCES devices(device_id)
);

-- ---------------------------------------------------------------------------
-- Fact tables
-- ---------------------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id   TEXT PRIMARY KEY,
    customer_id      TEXT NOT NULL REFERENCES customers(customer_id),
    merchant_id      TEXT NOT NULL REFERENCES merchants(merchant_id),
    bank_id          TEXT NOT NULL REFERENCES banks(bank_id),
    device_id        TEXT REFERENCES devices(device_id),
    amount           REAL NOT NULL,
    status           TEXT NOT NULL,            -- SUCCESS / FAILED / PENDING
    failure_reason   TEXT,                     -- NULL unless FAILED
    payment_mode     TEXT,                     -- QR Code / Intent / Collect / UPI Lite
    txn_timestamp    TEXT NOT NULL
);

CREATE TABLE cashback (
    cashback_id      TEXT PRIMARY KEY,
    transaction_id   TEXT NOT NULL REFERENCES transactions(transaction_id),
    campaign_id      TEXT NOT NULL REFERENCES campaigns(campaign_id),
    cashback_amount  REAL NOT NULL,
    cashback_date    TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Indexes (analytical query performance)
-- ---------------------------------------------------------------------------
CREATE INDEX idx_txn_customer   ON transactions(customer_id);
CREATE INDEX idx_txn_merchant   ON transactions(merchant_id);
CREATE INDEX idx_txn_bank       ON transactions(bank_id);
CREATE INDEX idx_txn_status     ON transactions(status);
CREATE INDEX idx_txn_timestamp  ON transactions(txn_timestamp);
CREATE INDEX idx_cust_state     ON customers(state);
CREATE INDEX idx_cust_bank      ON customers(primary_bank_id);
CREATE INDEX idx_merch_category ON merchants(category);
CREATE INDEX idx_cashback_txn   ON cashback(transaction_id);

-- ---------------------------------------------------------------------------
-- Reporting views
-- ---------------------------------------------------------------------------
-- Enriched fact view: one row per transaction with dimensions joined and the
-- common derived columns (revenue, date parts) pre-computed. Ideal as the base
-- table for Power BI and for keeping analysis SQL concise.
CREATE VIEW v_transaction_enriched AS
SELECT
    t.transaction_id,
    t.txn_timestamp,
    date(t.txn_timestamp)                                   AS txn_date,
    CAST(strftime('%Y', t.txn_timestamp) AS INTEGER)        AS txn_year,
    CAST(strftime('%m', t.txn_timestamp) AS INTEGER)        AS txn_month,
    strftime('%Y-%m', t.txn_timestamp)                      AS txn_year_month,
    CAST(strftime('%H', t.txn_timestamp) AS INTEGER)        AS txn_hour,
    CAST(strftime('%w', t.txn_timestamp) AS INTEGER)        AS txn_dow,   -- 0=Sun
    CASE WHEN strftime('%w', t.txn_timestamp) IN ('0','6')
         THEN 1 ELSE 0 END                                  AS is_weekend,
    t.amount,
    t.status,
    CASE WHEN t.status = 'SUCCESS' THEN 1 ELSE 0 END        AS is_success,
    t.failure_reason,
    t.payment_mode,
    -- Revenue is earned only on successful merchant payments (MDR * amount).
    CASE WHEN t.status = 'SUCCESS'
         THEN ROUND(t.amount * mer.commission_rate, 2)
         ELSE 0 END                                         AS revenue,
    t.customer_id,
    cus.state       AS customer_state,
    cus.city        AS customer_city,
    cus.gender      AS customer_gender,
    cus.age         AS customer_age,
    t.merchant_id,
    mer.merchant_name,
    mer.category    AS merchant_category,
    mer.commission_rate,
    t.bank_id,
    bnk.bank_name,
    bnk.bank_type,
    t.device_id,
    dev.os_name,
    dev.os_version
FROM transactions t
JOIN customers  cus ON cus.customer_id = t.customer_id
JOIN merchants  mer ON mer.merchant_id = t.merchant_id
JOIN banks      bnk ON bnk.bank_id     = t.bank_id
LEFT JOIN devices dev ON dev.device_id = t.device_id;

-- Monthly business summary — the executive KPI backbone.
CREATE VIEW v_monthly_summary AS
SELECT
    txn_year_month,
    COUNT(*)                                          AS total_txns,
    SUM(is_success)                                   AS successful_txns,
    ROUND(100.0 * SUM(is_success) / COUNT(*), 2)      AS success_rate_pct,
    ROUND(SUM(CASE WHEN status='SUCCESS' THEN amount ELSE 0 END), 2) AS gpv,
    ROUND(SUM(revenue), 2)                            AS revenue,
    COUNT(DISTINCT customer_id)                       AS active_customers
FROM v_transaction_enriched
GROUP BY txn_year_month;
