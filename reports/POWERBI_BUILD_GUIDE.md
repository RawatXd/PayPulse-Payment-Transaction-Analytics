# PayPulse — Power BI Dashboard Build Guide (Phase 6)

A step-by-step guide to assemble the executive dashboard in **Power BI Desktop**
(free, Windows) from the exported star schema. Follow the sections in order:
import → model → measures → theme → the six report pages → interactivity → polish.

> Why a guide and not a `.pbix`? Power BI files are a proprietary binary format
> authored inside Power BI Desktop — they can't be generated as code. Everything
> the file needs (clean star-schema tables + every DAX measure + exact visual
> specs) is provided here so the build is mechanical.

Estimated build time: **2–3 hours**.

---

## 0. Prerequisites

1. Install **Power BI Desktop** (Microsoft Store or the download page — free).
2. Generate the data (from `paypulse/`):
   ```
   python src/generate_data.py
   python src/build_database.py
   python src/features.py
   python src/export_powerbi.py
   ```
3. Confirm `data/powerbi/` contains:
   `dim_date.csv`, `fact_transactions.csv`, `dim_customers.csv`,
   `dim_merchants.csv`, `dim_banks.csv`, `dim_devices.csv`, `customer_features.csv`.

---

## 1. Import the data

**Home → Get Data → Text/CSV** (import each file), or **Get Data → Folder** and
point at `data/powerbi/` to load all at once. For each table click
**Transform Data** to verify column types (Power Query), then **Close & Apply**.

Rename queries to drop the `.csv` if needed so tables are:
`fact_transactions`, `dim_date`, `dim_customers`, `dim_merchants`, `dim_banks`,
`dim_devices`, `customer_features`.

### Column types to verify (Power Query → Data Type)
| Table | Column | Type |
|-------|--------|------|
| fact_transactions | `txn_date` | **Date** |
| fact_transactions | `txn_timestamp` | Date/Time |
| fact_transactions | `amount`, `revenue`, `commission_rate` | Decimal Number |
| fact_transactions | `is_success`, `is_weekend`, `txn_hour`, `txn_year`, `txn_month`, `txn_dow` | Whole Number |
| dim_date | `date` | **Date** |
| dim_customers | `registration_date` | **Date** |
| customer_features | `lifetime_spend`, `avg_ticket`, `success_rate` | Decimal Number |

---

## 2. Build the data model (star schema)

Open **Model view**. Create these relationships (drag the dimension key onto the
fact key). All are **one-to-many**, single cross-filter direction (dimension →
fact), and **active**:

| From (one) | To (many) |
|------------|-----------|
| `dim_date[date]` | `fact_transactions[txn_date]` |
| `dim_customers[customer_id]` | `fact_transactions[customer_id]` |
| `dim_merchants[merchant_id]` | `fact_transactions[merchant_id]` |
| `dim_banks[bank_id]` | `fact_transactions[bank_id]` |
| `dim_devices[device_id]` | `fact_transactions[device_id]` |

**Optional (advanced)** — an **inactive** relationship for signup analysis:
`dim_date[date]` → `dim_customers[registration_date]` (Power BI will make it
inactive automatically since a second date relationship exists). Used by the
`New Customers` measure via `USERELATIONSHIP`.

**`customer_features`** stays **standalone** (no relationship). It holds lifetime
RFM/CLV metrics that should NOT be sliced by the date filter, and already carries
its own `state`, `gender`, `age`, and `segment` columns for the Customer page.

### Mark the date table
Select `dim_date` → **Table tools → Mark as date table** → date column = `date`.
This enables correct time-intelligence (MoM, YTD).

### Sort-by columns (so months/days order chronologically)
- `dim_date[month_name]` → **Sort by column** → `month`
- `dim_date[day_name]` → **Sort by column** → `day_of_week`

### Hide redundant fact columns
The fact was exported flat, so it duplicates some dimension attributes. In the
Fields pane, right-click → **Hide** these on `fact_transactions` (use the
dimension versions instead): `customer_state`, `customer_city`, `customer_gender`,
`customer_age`, `merchant_name`, `merchant_category`, `bank_name`, `bank_type`,
`os_name`, `os_version`, `txn_year`, `txn_month`, `txn_year_month`.
Keep visible: `amount`, `revenue`, `commission_rate`, `status`, `is_success`,
`payment_mode`, `failure_reason`, `txn_hour`, `txn_dow`, `is_weekend`, `txn_date`.

---

## 3. DAX measures

Create an empty table to hold measures: **Home → Enter Data**, name it
`_Measures`, load, delete its dummy column. Add each measure below (**Model/Report
view → New Measure**). Set formats as noted.

### 3.1 Core KPIs
```DAX
Total Transactions = COUNTROWS ( fact_transactions )

Successful Transactions =
CALCULATE ( [Total Transactions], fact_transactions[is_success] = 1 )

Failed Transactions =
CALCULATE ( [Total Transactions], fact_transactions[status] = "FAILED" )

Pending Transactions =
CALCULATE ( [Total Transactions], fact_transactions[status] = "PENDING" )

Success Rate % = DIVIDE ( [Successful Transactions], [Total Transactions] )

Failure Rate % = DIVIDE ( [Failed Transactions], [Total Transactions] )

GPV = CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[is_success] = 1 )

Revenue = SUM ( fact_transactions[revenue] )

Avg Ticket Size = DIVIDE ( [GPV], [Successful Transactions] )

Active Customers = DISTINCTCOUNT ( fact_transactions[customer_id] )

Active Merchants = DISTINCTCOUNT ( fact_transactions[merchant_id] )
```
Formats: `Success Rate %`, `Failure Rate %` → **Percentage** (2 dp). `GPV`,
`Revenue`, `Avg Ticket Size` → **Whole Number**, ₹ prefix (Format → Custom:
`"₹"#,0`).

### 3.2 Time intelligence
```DAX
GPV PM = CALCULATE ( [GPV], DATEADD ( dim_date[date], -1, MONTH ) )
GPV MoM % = DIVIDE ( [GPV] - [GPV PM], [GPV PM] )

Revenue PM = CALCULATE ( [Revenue], DATEADD ( dim_date[date], -1, MONTH ) )
Revenue MoM % = DIVIDE ( [Revenue] - [Revenue PM], [Revenue PM] )

Transactions PM = CALCULATE ( [Total Transactions], DATEADD ( dim_date[date], -1, MONTH ) )
Txn MoM % = DIVIDE ( [Total Transactions] - [Transactions PM], [Transactions PM] )

Revenue YTD = TOTALYTD ( [Revenue], dim_date[date] )
GPV YTD = TOTALYTD ( [GPV], dim_date[date] )

Cumulative Revenue =
CALCULATE (
    [Revenue],
    FILTER ( ALLSELECTED ( dim_date[date] ), dim_date[date] <= MAX ( dim_date[date] ) )
)
```
Format the `MoM %` measures as Percentage.

### 3.3 Customer measures
```DAX
Repeat Customers =
COUNTROWS (
    FILTER ( VALUES ( fact_transactions[customer_id] ), [Total Transactions] > 1 )
)

Repeat Rate % = DIVIDE ( [Repeat Customers], [Active Customers] )

Avg Txns per Customer = DIVIDE ( [Total Transactions], [Active Customers] )

ARPU = DIVIDE ( [Revenue], [Active Customers] )

Avg Spend per Customer = DIVIDE ( [GPV], [Active Customers] )

New Customers =
CALCULATE (
    DISTINCTCOUNT ( dim_customers[customer_id] ),
    USERELATIONSHIP ( dim_date[date], dim_customers[registration_date] )
)
```
(`New Customers` needs the optional inactive relationship from §2.)

### 3.4 Customer lifetime / churn (from `customer_features`)
```DAX
Total Customers = COUNTROWS ( customer_features )

Inactive Customers =
CALCULATE ( COUNTROWS ( customer_features ), customer_features[is_inactive] = 1 )

Inactive Rate % = DIVIDE ( [Inactive Customers], [Total Customers] )

Avg CLV = AVERAGE ( customer_features[lifetime_spend] )

Avg Recency (days) = AVERAGE ( customer_features[recency_days] )
```

### 3.5 Merchant measures
```DAX
Merchant Revenue Rank =
RANKX ( ALL ( dim_merchants[merchant_name] ), [Revenue], , DESC )
```

### 3.6 Failure measures
```DAX
Failed GPV =
CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[status] = "FAILED" )

Est Revenue Lost =
CALCULATE (
    SUMX ( fact_transactions, fact_transactions[amount] * fact_transactions[commission_rate] ),
    fact_transactions[status] = "FAILED"
)
```

### 3.7 Handy display measure
```DAX
Peak Hour =
VAR t = ADDCOLUMNS ( VALUES ( fact_transactions[txn_hour] ), "@c", [Total Transactions] )
RETURN MAXX ( TOPN ( 1, t, [@c] ), fact_transactions[txn_hour] )
```

### 3.8 Calculated column — ticket band (on `fact_transactions`)
For the failure-by-ticket-size visual (**New Column** on the fact table):
```DAX
Ticket Band =
SWITCH (
    TRUE (),
    fact_transactions[amount] < 200, "a. <200",
    fact_transactions[amount] < 500, "b. 200-500",
    fact_transactions[amount] < 1000, "c. 500-1k",
    fact_transactions[amount] < 3000, "d. 1k-3k",
    fact_transactions[amount] < 10000, "e. 3k-10k",
    "f. 10k+"
)
```

### 3.9 Calculated column — country (on `dim_customers`, helps map geocoding)
```DAX
Country = "India"
```

---

## 4. Theme & global slicers

**View → Themes → Browse for themes** and load the included
[`reports/paypulse_theme.json`](paypulse_theme.json) (blue = primary, green =
success/GPV, red = failure — matching the visual conventions used throughout).

**Global slicers** (place on every page, top strip): `dim_date[year]`,
`dim_date[month_name]`, `dim_customers[state]`, `dim_merchants[category]`,
`fact_transactions[payment_mode]`. After building all pages, select each slicer →
**View → Sync slicers** → tick every page so filters carry across.

Add a title textbox "PayPulse — UPI & Digital Payments Analytics" on each page.

---

## 5. The six report pages

Each page: a KPI card strip along the top, then 3–5 visuals. Fields are written as
`Table[Column]`; `[Measure]` names refer to §3.

### Page 1 — Executive Overview
**Cards:** `[Total Transactions]`, `[GPV]`, `[Revenue]`, `[Success Rate %]`,
`[Active Customers]`, `[GPV MoM %]`.
| Visual | Type | Config |
|--------|------|--------|
| Revenue & GPV trend | Line chart | Axis `dim_date[month_name]` (or Date hierarchy); Values `[Revenue]`, `[GPV]` |
| Volume vs reliability | Line + clustered column | Axis month; Column `[Total Transactions]`; Line `[Success Rate %]` (secondary) |
| Revenue by payment mode | Donut | Legend `fact_transactions[payment_mode]`; Values `[Revenue]` |
| Revenue by quarter | Clustered column | Axis `dim_date[quarter]`; Values `[Revenue]` |
| KPI | KPI visual | Indicator `[Revenue]`; Trend axis month; Target `[Revenue PM]` |

### Page 2 — Customer Analytics
**Cards:** `[Active Customers]`, `[Repeat Rate %]`, `[ARPU]`, `[Inactive Rate %]`,
`[Avg CLV]`.
| Visual | Type | Config |
|--------|------|--------|
| RFM segments | Clustered bar | Axis `customer_features[segment]`; Values `Count of customer_id` (drag `customer_id`, set to Count) |
| RFM scatter | Scatter | X `customer_features[n_txns]`; Y `customer_features[lifetime_spend]`; Legend `segment`; Size `recency_days` |
| CLV leaderboard | Table | `customer_features[customer_id]`, `state`, `segment`, `lifetime_spend`, `n_txns` — sort desc by `lifetime_spend`, Top 20 filter |
| Customers by gender | Donut | Legend `customer_features[gender]`; Values Count of `customer_id` |
| Recency distribution | Column/Histogram | Axis `customer_features[recency_days]` (binned); Values Count |
| New customers by month | Line | Axis `dim_date[month_name]`; Values `[New Customers]` |

> Cohort retention (SQL file `02`) is awkward in native DAX — if you want it,
> import the query result of §2.5 as a static table and use a Matrix.

### Page 3 — Merchant Analytics
**Cards:** `[Active Merchants]`, `[Revenue]`, `[GPV]`, `[Avg Ticket Size]`.
| Visual | Type | Config |
|--------|------|--------|
| Top 10 merchants | Clustered bar | Axis `dim_merchants[merchant_name]`; Values `[Revenue]`; Filter: Top 10 by `[Revenue]` |
| Category performance | Clustered bar | Axis `dim_merchants[category]`; Values `[Revenue]` |
| Category → merchant | Treemap or Decomposition tree | Group `category`, then `merchant_name`; Values `[GPV]` |
| Category detail | Matrix | Rows `category`; Values `[Revenue]`, `[GPV]`, `[Success Rate %]`, `[Avg Ticket Size]` |
| Volume vs reliability | Scatter | X `[Total Transactions]`; Y `[Success Rate %]`; Details `merchant_name` |

### Page 4 — Transaction Analytics
**Cards:** `[Total Transactions]`, `[Success Rate %]`, `[Avg Ticket Size]`,
`[Peak Hour]`.
| Visual | Type | Config |
|--------|------|--------|
| Hourly pattern | Column | Axis `fact_transactions[txn_hour]`; Values `[Total Transactions]` |
| Weekday pattern | Column | Axis `dim_date[day_name]`; Values `[Total Transactions]` |
| Daily trend | Line | Axis `dim_date[date]`; Values `[Total Transactions]` (add trend line) |
| Cumulative revenue | Area | Axis `dim_date[month_name]`; Values `[Cumulative Revenue]` |
| Month × weekday heatmap | Matrix | Rows `dim_date[month_name]`; Columns `dim_date[day_name]`; Values `[Total Transactions]`; background conditional formatting |

### Page 5 — Failure Analytics
**Cards:** `[Failed Transactions]`, `[Failure Rate %]`, `[Failed GPV]`,
`[Est Revenue Lost]`.
| Visual | Type | Config |
|--------|------|--------|
| Failure rate by bank | Clustered bar | Axis `dim_banks[bank_name]`; Values `[Failure Rate %]`; sort desc |
| Failure reasons | Clustered bar | Axis `fact_transactions[failure_reason]`; Values `[Failed Transactions]` |
| Failure by hour | Column | Axis `fact_transactions[txn_hour]`; Values `[Failure Rate %]` |
| Failure by ticket band | Column | Axis `fact_transactions[Ticket Band]`; Values `[Failure Rate %]` |
| Bank type × reason | Matrix | Rows `dim_banks[bank_type]`; Columns `failure_reason`; Values `[Failed Transactions]`; conditional format |
| GPV lost by month | Line/Column | Axis `dim_date[month_name]`; Values `[Failed GPV]` |

### Page 6 — Regional Analytics
**Cards:** `[Revenue]`, `[GPV]`, `[Success Rate %]`, `[Active Customers]`.
| Visual | Type | Config |
|--------|------|--------|
| India map | Filled map (or Azure/Shape map) | Location `dim_customers[state]` (set **Data category = State or Province**); Legend/Color saturation `[GPV]`; add `dim_customers[Country]` if geocoding needs help |
| Revenue by state | Clustered bar | Axis `dim_customers[state]`; Values `[Revenue]`; sort desc |
| Success rate by state | Clustered bar | Axis `dim_customers[state]`; Values `[Success Rate %]` |
| State × category | Matrix | Rows `state`; Columns `dim_merchants[category]`; Values `[GPV]` |
| Top cities | Table | `dim_customers[city]`, `[GPV]`, `[Success Rate %]` — Top 15 by GPV |

---

## 6. Interactivity (the "senior" touches)

- **Sync slicers** — already set in §4; verify filters carry across pages.
- **Drill-through** — add a hidden page `Merchant Detail`: drag `dim_merchants[merchant_id]`
  into the page's **Drill-through** well, then build merchant-specific visuals.
  Right-click any merchant in a bar → **Drill through → Merchant Detail**.
  Repeat for a `Bank Detail` page keyed on `dim_banks[bank_id]`.
- **Report tooltips** — create a small page (Page Information → **Allow use as
  tooltip = On**) with `[Total Transactions]`, `[Success Rate %]`; assign it as the
  tooltip on the map/bar visuals for rich hover cards.
- **Bookmarks** — **View → Bookmarks**. Example: a Revenue-vs-GPV toggle (two
  overlaid charts + two bookmarks + buttons), or a **Reset Filters** bookmark that
  captures the cleared-slicer state. Wire buttons via **Action → Bookmark**.
- **Conditional formatting** — on matrices/tables: color `[Success Rate %]` on a
  green–red scale; add **data bars** to `[Revenue]`/`[GPV]` columns.
- **Top-N filters** — use the visual-level filter for the Top-10 merchant and
  Top-15 city visuals.

---

## 7. Polish & deliver

- Consistent card formatting (one decimal, ₹ prefix on money, % on rates).
- Titles on every visual; hide axis clutter; align to the grid.
- Page navigation buttons (Insert → Buttons → Page navigation) or a bookmark nav.
- **Save as `PayPulse.pbix`** in the project root.
- Free Power BI Desktop can't publish to the Service — for a portfolio, export
  each page (**File → Export → PDF**) or take screenshots, and commit the `.pbix`.

---

## Appendix A — where each field lives
| Field | Table |
|-------|-------|
| Money: `amount`, `revenue`, `commission_rate` | `fact_transactions` |
| Outcome: `status`, `is_success`, `failure_reason`, `payment_mode` | `fact_transactions` |
| Time parts: `txn_hour`, `txn_dow`, `is_weekend`, `Ticket Band` | `fact_transactions` |
| Calendar: `date`, `month_name`, `quarter`, `day_name`, `year` | `dim_date` |
| Customer attrs: `state`, `city`, `gender`, `age`, `registration_date`, `Country` | `dim_customers` |
| Merchant attrs: `merchant_name`, `category`, `city`, `state` | `dim_merchants` |
| Bank attrs: `bank_name`, `bank_type` | `dim_banks` |
| Device attrs: `os_name`, `os_version`, `device_model` | `dim_devices` |
| RFM/CLV/churn: `segment`, `lifetime_spend`, `n_txns`, `recency_days`, `is_inactive` | `customer_features` |

## Appendix B — mapping to the project brief
| Brief page | This guide |
|------------|-----------|
| Executive Overview | Page 1 |
| Customer Analytics (segments, retention, repeat, avg spend) | Page 2 |
| Merchant Analytics (revenue, category, top contributors) | Page 3 |
| Transaction Analytics (daily/weekly/monthly, peak hours) | Page 4 |
| Failure Analytics (reasons, bank-wise, device-wise) | Page 5 |
| Regional Analytics (India map, state revenue & success) | Page 6 |

Every KPI the brief lists (GPV, Revenue, Success Rate, MoM growth, CLV, Retention,
DAU/MAU, ARPU, Repeat %) has a measure in §3 or a query in `sql/analysis/`.
