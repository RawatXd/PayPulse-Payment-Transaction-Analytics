# PayPulse — Digital Transaction Analytics Dashboard

## 📊 Project Overview

**PayPulse** is an **end-to-end digital payment analytics platform** analyzing **250K+ UPI transactions** (Jan 2023 – Dec 2025). Built with Python, SQL, and Power BI, the project delivers actionable business intelligence through a **6-page interactive dashboard** for executive stakeholders, merchant performance analysis, customer behavior insights, and failure diagnostics.

**Live Dashboard:** [https://app.powerbi.com/groups/me/reports/bcd4031b-9a69-47c3-a059-47d9d2e89504?ctid=19cae115-0ae3-4c47-a134-660fffd277d8&pbi_source=linkShare]

---

## 🎯 Key Metrics & Insights

| Metric | Value | Insight |
|--------|-------|---------|
| **Total Transactions** | 250K | 3-year payment volume analysis |
| **Total Revenue** | $3.24M | Merchant commission and transaction fees |
| **Success Rate** | 86.83% | Transaction reliability across 16 banks |
| **Total Customers** | 8K | Customer segmentation & RFM analysis |
| **Active Customers (30-day)** | ~2.4K | Repeat purchase behavior |
| **Failure Rate** | 13.17% | Root cause analysis & bank performance |
| **Top Merchant Revenue** | ~$320K | Merchant concentration analysis |
| **Mobile Transactions** | 78.5% | Device OS distribution (Android vs iOS) |

---

## 📈 Dashboard Pages

### 1. **Executive Dashboard**
High-level KPI summary with trend analysis for leadership decision-making.

**Visuals:**
- 4 KPI Cards: Total Transactions, Revenue, Success Rate, Customer Count
- Transactions Trend Line: Temporal patterns (2023–2025)
- Success vs Failed Pie Chart: Transaction outcome distribution
- Top 5 Merchants by Revenue: Merchant concentration analysis
- Revenue Trend Line: Monthly revenue trajectory

**Key Finding:** Consistent transaction volume (~250K/year) with stable 86.83% success rate indicates platform reliability.

---

### 2. **Customer Analytics**
Deep dive into customer segmentation, lifetime value, and behavioral patterns.

**Visuals:**
- Transactions by City: Geographic distribution across 30+ cities
- Avg Transaction Amount by Age: Age-group spending patterns
- High Value Customers by Gender: Gender-based RFM segmentation
- Customer Lifetime Value Scatter: Lifetime spend vs engagement score

**Key Findings:**
- Male customers dominate high-value segment (3.2K customers)
- Age 35–45 cohort shows highest transaction amounts (~₹1,600 avg)
- Mumbai & Delhi account for 35% of transaction volume
- RFM Scoring identifies 1.2K churn-risk customers (f_score ≤ 1)

---

### 3. **Merchant Analytics**
Merchant performance, category profitability, and commission analysis.

**Visuals:**
- Transactions by Merchant Category: Category distribution (Food, E-commerce, etc.)
- Top 10 Merchants by Revenue: Revenue concentration analysis
- Merchant Popularity vs Transaction Volume: Scatter analysis
- Avg Commission Rate by Merchant: Pricing strategy impact

**Key Findings:**
- E-commerce & Food Delivery dominate (52% of transactions)
- Top 10 merchants generate 28% of total revenue
- Commission rates range 0.8%–2.5% by merchant type
- High-popularity merchants don't always drive revenue (price elasticity)

---

### 4. **Transaction Details**
Drill-down transaction-level analysis with payment method and device insights.

**Visuals:**
- Transactions by Bank: Market share across 16 banks
- Device OS Distribution Pie: Mobile OS breakdown (Android 78.5%, iOS 21.45%)
- Transaction Details Table: Customer, Merchant, Amount, Date, Status columns

**Key Findings:**
- HDFC Bank leads with 32K transactions (12.8% market share)
- Android dominates mobile payments (78.5% of transactions)
- Transaction velocity peaks Fri–Sun (weekends)
- Average transaction amount: ₹1,296

---

### 5. **Failure Analysis**
Root cause analysis, bank-level performance, and failure trend monitoring.

**Visuals:**
- Failure Rate % by Date: Temporal failure trends (stable ~13.17%)
- Failure Rate % by Bank: Bank performance comparison
- Failed Transactions by Failure Reason: Root cause distribution
- Bank-Reason Failure Table: Drill-down on failure combinations

**Key Findings:**
- **Top Failure Reasons:**
  1. Insufficient Funds (4.2K failures)
  2. Bank Server Down (3.8K failures)
  3. Transaction Timeout (3.2K failures)
  4. Incorrect UPI PIN (2.1K failures)
  5. Beneficiary Bank Offline (1.9K failures)

- **Worst Performing Banks:** Paytm Payments (19.7% failure rate), Airtel Payments (17.3%)
- **Best Performing Banks:** ICICI, HDFC (8.5% average failure rate)
- **Recommendation:** Partner outreach for Paytm & Airtel to improve uptime

---

### 6. **Regional Analytics**
Geographic performance, state-level success rates, and regional revenue distribution.

**Visuals:**
- Transactions by City: City-wise transaction volume (top: Mumbai, Delhi, Bangalore)
- Revenue by City (Top 15): City-level profitability ranking
- Success Rate % by State: State-level reliability metrics
- Regional Performance Table: State, City, Customers, Transactions, Revenue, Success Rate

**Key Findings:**
- **Top 5 States by Volume:** Delhi, Maharashtra, Karnataka, Tamil Nadu, Telangana
- **Highest Revenue States:** Maharashtra ($520K), Delhi ($480K), Karnataka ($380K)
- **Highest Success Rates:** Punjab, Haryana (89.2%), Tamil Nadu (88.5%)
- **Lowest Success Rates:** Uttarakhand, Himachal Pradesh (81.3%)

---

## 🛠️ Technical Architecture

### Data Pipeline

```
Raw CSVs (250K records)
    ↓
[Python: Data Cleaning & Feature Engineering]
    ↓
SQLite Database (Normalized Star Schema)
    ↓
[SQL Queries: 35+ analytics queries]
    ↓
CSV Exports (for Power BI)
    ↓
Power BI: Data Import → Model → DAX → Publish
```

### Star Schema Design

**Fact Table:**
- `fact_transactions`: 250K rows, 14 columns
  - Keys: `customer_id`, `merchant_id`, `bank_id`, `device_id`, `txn_date`
  - Measures: `amount`, `revenue`, `is_success`, `commission_rate`

**Dimension Tables:**
- `dim_customers`: 8K customers (age, gender, city, state, registration_date)
- `dim_merchants`: 1.2K merchants (category, popularity, commission_rate)
- `dim_banks`: 16 banks (bank_type, failure_rate, market_share)
- `dim_devices`: 2.8K devices (os_name, os_version, device_model)
- `dim_date`: 1,095 dates (2023–2025) with hierarchies (year, quarter, month, day)
- `customer_features`: RFM scores, lifetime_spend, f_score, churn_risk

### Relationships

```
dim_date ──1→ fact_transactions (txn_date)
dim_customers ──1→ fact_transactions (customer_id)
dim_merchants ──1→ fact_transactions (merchant_id)
dim_banks ──1→ fact_transactions (bank_id)
dim_devices ──1→ fact_transactions (device_id)
```

---

## 📊 DAX Measures (33 Total)

### Core Metrics
```dax
Total Transactions = COUNTA(fact_transactions[txn_id])
Total Amount = SUM(fact_transactions[amount])
Total Revenue = SUM(fact_transactions[revenue])
Successful Transactions = CALCULATE([Total Transactions], fact_transactions[is_success] = 1)
Failed Transactions = CALCULATE([Total Transactions], fact_transactions[is_success] = 0)
Success Rate % = DIVIDE([Successful Transactions], [Total Transactions], 0) * 100
Avg Transaction Amount = DIVIDE([Total Amount], [Total Transactions], 0)
```

### Customer Metrics
```dax
Total Customers = DISTINCTCOUNT(fact_transactions[customer_id])
Repeat Customer Rate % = [Returning Customers] / [Total Customers] * 100
Avg Transactions per Customer = DIVIDE([Total Transactions], [Total Customers], 0)
High Value Customers = CALCULATE(DISTINCTCOUNT(customer_features[customer_id]), customer_features[f_score] >= 3)
Customer Lifetime Value Avg = CALCULATE(AVERAGE(customer_features[lifetime_spend]))
Active Customers (30 days) = CALCULATE(DISTINCTCOUNT(fact_transactions[customer_id]), FILTER(fact_transactions, fact_transactions[txn_date] >= TODAY() - 30))
Churn Risk Customers = CALCULATE(DISTINCTCOUNT(customer_features[customer_id]), customer_features[f_score] <= 1)
```

### Merchant Metrics
```dax
Total Merchants = DISTINCTCOUNT(fact_transactions[merchant_id])
Transactions per Merchant Avg = DIVIDE([Total Transactions], [Total Merchants], 0)
Top Merchant Revenue = MAXX(TOPN(1, SUMMARIZE(fact_transactions, fact_transactions[merchant_id], "Rev", SUM(fact_transactions[revenue])), [Rev]), [Rev])
Distinct Merchants Transacting = CALCULATE(DISTINCTCOUNT(fact_transactions[merchant_id]), fact_transactions[is_success] = 1)
```

### Failure & Bank Metrics
```dax
Failure Rate % = DIVIDE([Failed Transactions], [Total Transactions], 0) * 100
Most Common Failure Reason = MAXX(TOPN(1, SUMMARIZE(fact_transactions, fact_transactions[failure_reason], "Count", COUNTA(fact_transactions[failure_reason])), [Count]), fact_transactions[failure_reason])
Total Banks = DISTINCTCOUNT(fact_transactions[bank_id])
Base Failure Rate Avg = CALCULATE(AVERAGE(dim_banks[base_failure_rate]))
Bank Success Rate % = CALCULATE([Success Rate %])
```

### Device & Time Metrics
```dax
Total Devices = DISTINCTCOUNT(fact_transactions[device_id])
Mobile Transactions % = DIVIDE(CALCULATE([Total Transactions], fact_transactions[os_name] IN {"Android", "iOS"}), [Total Transactions]) * 100
Weekend Transactions % = DIVIDE(CALCULATE([Total Transactions], fact_transactions[is_weekend] = 1), [Total Transactions]) * 100
Peak Transaction Hour = MAXX(TOPN(1, SUMMARIZE(fact_transactions, fact_transactions[txn_hour], "HourCount", COUNTA(fact_transactions[txn_id])), [HourCount]), fact_transactions[txn_hour])
YTD Transactions = CALCULATE([Total Transactions], DATESYTD(dim_date[date]))
YTD Revenue = CALCULATE([Total Revenue], DATESYTD(dim_date[date]))
Month over Month Growth % = DIVIDE([Total Transactions] - CALCULATE([Total Transactions], DATEADD(dim_date[date], -1, MONTH)), CALCULATE([Total Transactions], DATEADD(dim_date[date], -1, MONTH))) * 100
```

### RFM & Segmentation
```dax
Avg RFM Score = CALCULATE(AVERAGE(customer_features[f_score]))
High Value Customer % = DIVIDE([High Value Customers], [Total Customers], 0) * 100
Avg Commission Rate = CALCULATE(AVERAGE(fact_transactions[commission_rate]))
Revenue per Transaction = DIVIDE([Total Revenue], [Total Transactions], 0)
```

---
### Key Interactions

- **Date Slicer:** Applies across all pages (Jan 2023 – Dec 2025)
- **City/State Filter:** Cross-filters customer, merchant, and transaction data
- **Bank Selection:** Isolates failure analysis for specific banks
- **Drill-through:** Click merchant names to view transaction details
- **Bookmarks:** Pre-built views for executive presentations

---

## 📂 Files & Structure

```
paypulse/
├── data/
│   └── powerbi/
│       ├── fact_transactions.csv (56MB) [transactions]
│       ├── dim_customers.csv (627KB) [8K customers]
│       ├── dim_merchants.csv (89KB) [1.2K merchants]
│       ├── dim_banks.csv (660B) [16 banks]
│       ├── dim_devices.csv (242KB) [2.8K devices]
│       ├── dim_date.csv (51KB) [1095 dates, 2023-2025]
│       └── customer_features.csv (1.3MB) [RFM scores]
│
├── src/
│   ├── generate_data.py [Synthetic data generation]
│   ├── build_database.py [SQLite schema & ETL]
│   ├── features.py [RFM & feature engineering]
│   └── export_powerbi.py [CSV export for BI]
│
├── sql/
│   ├── executive_queries.sql [KPI dashboard queries]
│   ├── customer_queries.sql [Segmentation analysis]
│   ├── merchant_queries.sql [Performance metrics]
│   ├── transaction_queries.sql [Drill-down queries]
│   ├── failure_queries.sql [Failure root cause]
│   └── regional_queries.sql [Geographic analysis]
│
├── reports/
│   ├── PayPulse_Dashboard.pbix [Main dashboard file]
│   ├── paypulse_theme.json [Custom theme (colors, fonts)]
│   └── POWERBI_BUILD_GUIDE.md [Dashboard build documentation]
│
└── README.md [This file]
```

---

## 🚀 Getting Started

### Prerequisites
- Power BI Desktop (free) or Power BI Cloud subscription
- Microsoft Excel (optional, for data validation)
- 200MB disk space (for .pbix + CSVs)

### Setup Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/[your-github]/paypulse-dashboard.git
   cd paypulse
   ```

2. **Download Dashboard File**
   ```bash
   # File: paypulse/reports/PayPulse_Dashboard.pbix
   ```

3. **Open in Power BI Desktop**
   ```
   File → Open → Select PayPulse_Dashboard.pbix
   ```

4. **Refresh Data (Optional)**
   - Home tab → Refresh
   - Data will load from the CSV exports in `data/powerbi/`

5. **Publish to Cloud (Optional)**
   - File tab → Publish
   - Select workspace → Create
   - Share link with stakeholders

---

## 📊 Sample Insights & Recommendations

### 1. **Failure Rate Optimization**
**Finding:** 13.17% failure rate driven by "Insufficient Funds" (4.2K failures)
- **Action:** Partner with banks on balance threshold notifications
- **Expected Impact:** Reduce failures by 2–3%, increase customer satisfaction

### 2. **Merchant Concentration**
**Finding:** Top 10 merchants generate 28% of revenue ($907K)
- **Risk:** Over-reliance on key merchants
- **Action:** Develop onboarding programs for mid-tier merchants (₹50K–₹200K revenue range)

### 3. **Regional Expansion**
**Finding:** Maharashtra & Delhi account for 60% of volume; Himachal Pradesh & Uttarakhand only 1.2%
- **Opportunity:** Tier-2/3 city marketing campaigns
- **Expected ROI:** 15–20% volume growth in underserving regions

### 4. **Customer Lifetime Value**
**Finding:** 1.2K churn-risk customers (f_score ≤ 1) generating only ₹12M of ₹310M LTV
- **Action:** Win-back campaigns, loyalty rewards for repeat transactions
- **Expected Impact:** Recover 20–30% of at-risk customer value

---

## 🔍 Data Quality & Validation

- **Synthetic Data:** Generated for privacy & compliance
- **Date Range:** Jan 1, 2023 – Dec 31, 2025 (3 years, 1,095 days)
- **Transaction Volume:** 250K rows across 8K customers, 1.2K merchants, 16 banks
- **Validation Checks:**
  - Transaction amounts: ₹100 – ₹50,000
  - Success rate consistency: 86.83% ±0.5%
  - No missing values in fact table keys

---

## 📝 SQL Query Examples

### Get Top 10 Merchants by Revenue
```sql
SELECT TOP 10
    merchant_id,
    merchant_name,
    SUM(revenue) as total_revenue,
    COUNT(*) as transaction_count,
    ROUND(AVG(amount), 2) as avg_amount
FROM fact_transactions ft
JOIN dim_merchants dm ON ft.merchant_id = dm.merchant_id
GROUP BY merchant_id, merchant_name
ORDER BY total_revenue DESC;
```

### Customer Segmentation by City
```sql
SELECT 
    city,
    COUNT(DISTINCT customer_id) as customer_count,
    COUNT(*) as transaction_count,
    SUM(amount) as total_spend,
    ROUND(AVG(amount), 2) as avg_transaction
FROM fact_transactions ft
JOIN dim_customers dc ON ft.customer_id = dc.customer_id
WHERE txn_date >= '2025-01-01'
GROUP BY city
ORDER BY customer_count DESC;
```

---

## 🎓 Skills Demonstrated

| Skill | Application |
|-------|-------------|
| **Python** | Data generation, ETL, feature engineering |
| **SQL** | 35+ analytics queries, star schema design |
| **Power BI** | 6-page dashboard, 33 DAX measures, interactive filters |
| **Data Modeling** | Fact/dimension tables, relationships, hierarchies |
| **Analytics** | RFM segmentation, failure analysis, trend forecasting |
| **Business Intelligence** | KPI tracking, executive dashboards, data storytelling |
| **Git/GitHub** | Version control, documentation, portfolio project |

---

## 📧 Contact & Questions

- **GitHub Issues:** [Create issue for bugs/questions]
- **Email:** abhishekrawat.du.or.26@gmail.com
- **LinkedIn:** [LinkedIn Profile Link]

---

## 📄 License

This project is open-source for educational & portfolio purposes.

---

## 🙏 Acknowledgments

- Inspired by real-world UPI payment systems in India
- Built as part of **Operational Research Master's** capstone project
- Dataset: 250K synthetic transactions for analysis practice

---
