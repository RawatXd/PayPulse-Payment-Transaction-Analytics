# 💳 PayPulse — End-to-End UPI & Digital Payments Analytics Platform

PayPulse is an end-to-end data analytics project that analyzes UPI and digital payment transactions using **Python, SQL, and Statistical Analysis**. The project covers synthetic data generation, database design, SQL analytics, exploratory data analysis (EDA), feature engineering, and statistical hypothesis testing to uncover customer behavior, merchant performance, transaction trends, and payment success patterns.

> This folder is self-contained and independent of any other projects.

---

# 📌 Project Highlights

✅ Synthetic Data Generation

✅ Relational Database Design (SQLite)

✅ SQL Business Analytics

✅ Python Data Cleaning & Feature Engineering

✅ Exploratory Data Analysis (EDA)

✅ Statistical Analysis & Hypothesis Testing

---

# 🚀 Project Workflow

```
Raw Data Generation
        │
        ▼
SQLite Database
        │
        ▼
SQL Business Analytics
        │
        ▼
Python Data Cleaning
        │
        ▼
Feature Engineering
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Statistical Analysis
        │
        ▼
Business Insights
```

---

# 📊 Project Status

| Phase | Deliverable | Status |
|------|-------------|--------|
| Business Questions | Business problem definition | ✅ |
| Database Design | Synthetic data generator & SQLite schema | ✅ |
| SQL Analytics | 35 business queries across 6 modules | ✅ |
| Python Analytics | Data cleaning, EDA & feature engineering | ✅ |
| Statistical Analysis | Hypothesis testing, ANOVA & Chi-Square | ✅ |

---

# ⚙️ Quick Start

```bash
cd paypulse

pip install -r requirements.txt

python src/generate_data.py

python src/build_database.py

python src/features.py
```

Open the notebooks in Jupyter Notebook or VS Code.

```
notebooks/phase4_python_analytics.ipynb

notebooks/phase5_statistical_analysis.ipynb
```

Project findings are available in

```
reports/PHASE4_5_FINDINGS.md
```

---

# 📁 Project Structure

```
paypulse/
│
├── README.md
├── requirements.txt
│
├── src/
│   ├── config.py
│   ├── generate_data.py
│   ├── build_database.py
│   └── features.py
│
├── sql/
│   ├── schema.sql
│   └── analysis/
│       ├── 01_executive_overview.sql
│       ├── 02_customer_analytics.sql
│       ├── 03_merchant_analytics.sql
│       ├── 04_transaction_trends.sql
│       ├── 05_failure_analytics.sql
│       └── 06_regional_analytics.sql
│
├── notebooks/
│   ├── phase4_python_analytics.ipynb
│   └── phase5_statistical_analysis.ipynb
│
├── reports/
│   ├── PHASE4_5_FINDINGS.md
│   └── figures/
│
└── data/
    ├── raw/
    ├── processed/
    └── paypulse.db
```

---

# 🗄️ Database Model

The project follows a relational database design centered around transaction analytics.

### Fact Table

- Transactions

### Dimension Tables

- Customers
- Merchants
- Banks
- Devices
- Cashback
- Campaigns

Each transaction represents one UPI payment between a customer and a merchant.

---

# 📈 Key Business Insights

The synthetic dataset contains realistic patterns including:

- 📈 Rapid transaction growth over time
- 👥 Customer churn and retention behavior
- 🏦 Bank-wise payment success and failure rates
- 🕒 Peak transaction hours
- 🌍 Regional revenue distribution
- 💰 High-value transaction risk
- 📊 Merchant revenue concentration (Pareto Principle)

These patterns allow meaningful business analysis using SQL and Python.

---

# 🛠 SQL Analytics

The project contains over **35 business-oriented SQL queries** covering:

### Executive Analytics

- Revenue KPIs
- Monthly Growth
- Quarterly Growth
- Payment Mode Distribution

### Customer Analytics

- Customer Lifetime Value (CLV)
- Repeat Customers
- Customer Segmentation
- Retention Analysis

### Merchant Analytics

- Top Performing Merchants
- Category Revenue
- Revenue Concentration
- Merchant Rankings

### Transaction Analytics

- Hourly Trends
- Daily Trends
- Weekly Trends
- Moving Average
- Running Revenue

### Failure Analytics

- Bank Failure Rates
- Device Failure Rates
- Failure Reasons
- Revenue Lost

### Regional Analytics

- Revenue by State
- Revenue by City
- State-wise Rankings
- Regional Performance

---

# 🐍 Python Analytics

The Python workflow includes:

- Data Cleaning
- Missing Value Handling
- Duplicate Detection
- Outlier Detection
- Feature Engineering
- Exploratory Data Analysis
- Customer-Level Features
- Transaction-Level Features

---

# 📊 Statistical Analysis

The project demonstrates practical statistical techniques including:

- Confidence Intervals
- Correlation Analysis
- Independent t-Test
- One-Way ANOVA
- Chi-Square Test
- Outlier Detection
- Distribution Analysis

---

# 🛠 Technologies Used

- Python
- SQL (SQLite)
- Pandas
- NumPy
- Matplotlib
- Plotly
- SciPy
- Jupyter Notebook

---

# 📂 Reports

Detailed findings are available in:

```
reports/PHASE4_5_FINDINGS.md
```

---

# 🎯 Learning Outcomes

This project demonstrates practical skills in:

- Database Design
- SQL Querying
- Data Cleaning
- Exploratory Data Analysis
- Feature Engineering
- Statistical Analysis
- Business Intelligence Concepts
- Business Problem Solving
