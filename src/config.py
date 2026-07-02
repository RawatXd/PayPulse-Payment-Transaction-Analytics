"""
PayPulse — central configuration & reference data
==================================================

Everything that controls the *shape* of the synthetic dataset lives here so the
generator (`generate_data.py`) stays pure logic. Tuning these numbers changes the
business story the data tells.

Design philosophy
-----------------
The data is not uniform noise. Real, *discoverable* signals are deliberately baked
in so that the SQL / Python / Power BI analysis has something meaningful to find:

  * MONTHLY GROWTH     -> transaction volume compounds month over month
  * CUSTOMER CHURN     -> a slice of customers go inactive (retention analysis)
  * BANK FAILURES      -> some banks fail far more often than others
  * PEAK HOURS         -> bimodal daily curve (lunch + evening spikes)
  * REGIONAL SKEW      -> a few states dominate revenue (Maharashtra, Karnataka...)
  * REPEAT USERS       -> activity is log-normal, so a minority drive most volume
  * HIGH-VALUE RISK    -> larger amounts fail slightly more often

All monetary values are in INR (₹).
"""

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[1]      # .../paypulse
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"                               # generated CSVs land here
PROCESSED_DIR = DATA_DIR / "processed"                   # cleaned + engineered tables
DB_PATH = DATA_DIR / "paypulse.db"                       # SQLite database
SQL_DIR = PROJECT_ROOT / "sql"
SCHEMA_FILE = SQL_DIR / "schema.sql"
REPORTS_DIR = PROJECT_ROOT / "reports"                   # findings + figures
FIGURES_DIR = REPORTS_DIR / "figures"

# --------------------------------------------------------------------------- #
# Reproducibility & scale
# --------------------------------------------------------------------------- #
SEED = 42                       # fixed seed -> identical dataset every run
N_CUSTOMERS = 8_000
N_MERCHANTS = 1_200
TARGET_TRANSACTIONS = 250_000   # approximate; actual is close after monthly scaling

# Analysis window for transactions (36 months of history).
TXN_START = "2023-01-01"
TXN_END = "2025-12-31"

# Customers start registering *before* the transaction window so there is an
# established base to measure retention against.
REG_START = "2022-06-01"
REG_END = "2025-12-01"

# Engagement grows ~1.8% per month on top of customer-base growth.
MONTHLY_ENGAGEMENT_GROWTH = 0.018

# Share of customers who churn (stop transacting) at some point.
CHURN_RATE = 0.28

# --------------------------------------------------------------------------- #
# Geography: state -> cities, population weight, affluence multiplier
# --------------------------------------------------------------------------- #
# pop_weight   : relative share of the customer base living there
# affluence    : multiplier on transaction amounts (cost-of-living / spend power)
STATES = {
    "Maharashtra":    {"cities": ["Mumbai", "Pune", "Nagpur", "Nashik"],      "pop_weight": 16, "affluence": 1.25},
    "Karnataka":      {"cities": ["Bengaluru", "Mysuru", "Mangaluru"],        "pop_weight": 12, "affluence": 1.22},
    "Delhi":          {"cities": ["New Delhi", "Dwarka", "Rohini"],           "pop_weight": 10, "affluence": 1.20},
    "Tamil Nadu":     {"cities": ["Chennai", "Coimbatore", "Madurai"],        "pop_weight": 10, "affluence": 1.08},
    "Telangana":      {"cities": ["Hyderabad", "Warangal"],                   "pop_weight":  8, "affluence": 1.15},
    "Uttar Pradesh":  {"cities": ["Lucknow", "Noida", "Kanpur", "Ghaziabad"], "pop_weight": 12, "affluence": 0.85},
    "Gujarat":        {"cities": ["Ahmedabad", "Surat", "Vadodara"],          "pop_weight":  8, "affluence": 1.10},
    "West Bengal":    {"cities": ["Kolkata", "Howrah", "Siliguri"],           "pop_weight":  7, "affluence": 0.90},
    "Rajasthan":      {"cities": ["Jaipur", "Jodhpur", "Udaipur"],            "pop_weight":  5, "affluence": 0.88},
    "Kerala":         {"cities": ["Kochi", "Thiruvananthapuram", "Kozhikode"],"pop_weight":  5, "affluence": 1.05},
    "Punjab":         {"cities": ["Ludhiana", "Amritsar", "Chandigarh"],      "pop_weight":  4, "affluence": 1.00},
    "Madhya Pradesh": {"cities": ["Indore", "Bhopal", "Gwalior"],             "pop_weight":  3, "affluence": 0.82},
}

# --------------------------------------------------------------------------- #
# Banks: market share + baseline failure rate (the core failure-analysis signal)
# --------------------------------------------------------------------------- #
# base_failure : intrinsic probability a transaction on this bank fails, before
#                amount / time-of-day / device effects are added.
BANKS = [
    {"bank_name": "HDFC Bank",              "bank_type": "Private", "market_share": 15, "base_failure": 0.045},
    {"bank_name": "State Bank of India",    "bank_type": "Public",  "market_share": 20, "base_failure": 0.110},
    {"bank_name": "ICICI Bank",             "bank_type": "Private", "market_share": 12, "base_failure": 0.050},
    {"bank_name": "Axis Bank",              "bank_type": "Private", "market_share": 10, "base_failure": 0.065},
    {"bank_name": "Kotak Mahindra Bank",    "bank_type": "Private", "market_share":  6, "base_failure": 0.055},
    {"bank_name": "Punjab National Bank",   "bank_type": "Public",  "market_share":  8, "base_failure": 0.135},
    {"bank_name": "Bank of Baroda",         "bank_type": "Public",  "market_share":  6, "base_failure": 0.120},
    {"bank_name": "Canara Bank",            "bank_type": "Public",  "market_share":  5, "base_failure": 0.125},
    {"bank_name": "Union Bank of India",    "bank_type": "Public",  "market_share":  4, "base_failure": 0.130},
    {"bank_name": "Yes Bank",               "bank_type": "Private", "market_share":  3, "base_failure": 0.075},
    {"bank_name": "IDFC First Bank",        "bank_type": "Private", "market_share":  3, "base_failure": 0.060},
    {"bank_name": "IndusInd Bank",          "bank_type": "Private", "market_share":  2, "base_failure": 0.070},
    {"bank_name": "Paytm Payments Bank",    "bank_type": "Payments","market_share":  4, "base_failure": 0.160},
    {"bank_name": "Airtel Payments Bank",   "bank_type": "Payments","market_share":  2, "base_failure": 0.150},
    {"bank_name": "Federal Bank",           "bank_type": "Private", "market_share":  2, "base_failure": 0.058},
]

# --------------------------------------------------------------------------- #
# Merchant categories: average ticket size, MDR (platform take rate), demand
# --------------------------------------------------------------------------- #
# avg_ticket  : median transaction value (INR); amounts are log-normal around it
# commission  : merchant discount rate -> PayPulse revenue on a SUCCESSFUL txn
# demand      : relative share of transaction volume for the category
CATEGORIES = {
    "Grocery":           {"avg_ticket":  420, "commission": 0.004, "demand": 18},
    "Food Delivery":     {"avg_ticket":  360, "commission": 0.020, "demand": 15},
    "Recharge & Bills":  {"avg_ticket":  310, "commission": 0.010, "demand": 14},
    "E-commerce":        {"avg_ticket": 1150, "commission": 0.015, "demand": 12},
    "Fashion & Apparel": {"avg_ticket":  900, "commission": 0.018, "demand":  8},
    "Fuel":              {"avg_ticket": 1450, "commission": 0.005, "demand":  8},
    "Pharmacy":          {"avg_ticket":  520, "commission": 0.010, "demand":  7},
    "Electronics":       {"avg_ticket": 4200, "commission": 0.012, "demand":  5},
    "Entertainment":     {"avg_ticket":  480, "commission": 0.025, "demand":  5},
    "Travel":            {"avg_ticket": 3600, "commission": 0.016, "demand":  4},
    "Education":         {"avg_ticket": 5200, "commission": 0.008, "demand":  4},
}

# --------------------------------------------------------------------------- #
# Transaction status & failure reasons
# --------------------------------------------------------------------------- #
PENDING_RATE = 0.018            # of *non-failed* txns, this fraction hang as PENDING

# Failure reasons for a "healthy" bank vs. a "troubled" (high base_failure) bank.
# Troubled banks skew toward infrastructure problems (server down / offline).
FAILURE_REASONS_HEALTHY = {
    "Insufficient Funds":       28,
    "Incorrect UPI PIN":        22,
    "Transaction Timeout":      16,
    "Daily Limit Exceeded":     12,
    "Bank Server Down":         10,
    "Beneficiary Bank Offline":  6,
    "Technical Decline":         6,
}
FAILURE_REASONS_TROUBLED = {
    "Insufficient Funds":       16,
    "Incorrect UPI PIN":        12,
    "Transaction Timeout":      18,
    "Daily Limit Exceeded":      8,
    "Bank Server Down":         24,
    "Beneficiary Bank Offline": 16,
    "Technical Decline":         6,
}
# A bank counts as "troubled" if base_failure exceeds this threshold.
TROUBLED_BANK_THRESHOLD = 0.10

# --------------------------------------------------------------------------- #
# UPI payment modes (initiation flow). Weights are amount-dependent in the
# generator: small tickets lean QR / UPI Lite, large tickets lean Intent.
# --------------------------------------------------------------------------- #
PAYMENT_MODES = ["QR Code", "Intent", "Collect Request", "UPI Lite"]

# --------------------------------------------------------------------------- #
# Hour-of-day weights (0-23): bimodal — morning, lunch, and a strong evening peak.
# --------------------------------------------------------------------------- #
HOUR_WEIGHTS = [
    0.3, 0.2, 0.15, 0.1, 0.1, 0.2,   # 00-05  night trough
    0.6, 1.2, 2.2, 3.0, 3.2, 3.4,    # 06-11  morning ramp
    3.8, 4.2, 3.6, 2.8, 2.6, 3.2,    # 12-17  lunch peak then dip
    4.6, 5.2, 4.8, 3.6, 2.2, 1.0,    # 18-23  evening peak
]

# Peak hours get a small extra failure bump (network congestion).
PEAK_HOURS = {12, 13, 18, 19, 20, 21}
PEAK_HOUR_FAILURE_BUMP = 0.020

# --------------------------------------------------------------------------- #
# Devices
# --------------------------------------------------------------------------- #
# Android dominates volume; older OS versions fail slightly more often.
OS_DISTRIBUTION = {"Android": 0.78, "iOS": 0.22}
ANDROID_VERSIONS = ["11", "12", "13", "14", "15"]     # older = higher failure
ANDROID_VERSION_WEIGHTS = [0.10, 0.18, 0.30, 0.28, 0.14]
IOS_VERSIONS = ["15", "16", "17", "18"]
IOS_VERSION_WEIGHTS = [0.12, 0.28, 0.36, 0.24]
ANDROID_MODELS = ["Xiaomi Redmi", "Samsung Galaxy", "Vivo", "Oppo", "Realme", "OnePlus", "Motorola"]
IOS_MODELS = ["iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15", "iPhone SE"]
OLD_OS_FAILURE_BUMP = 0.015     # applied to Android 11/12

# --------------------------------------------------------------------------- #
# Demographics
# --------------------------------------------------------------------------- #
AGE_MIN, AGE_MAX = 18, 70
GENDERS = ["Male", "Female", "Other"]
GENDER_WEIGHTS = [0.54, 0.44, 0.02]

# Name pools (purely cosmetic; keeps the generator dependency-free — no Faker).
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Rohan", "Ananya", "Diya", "Aadhya", "Saanvi", "Pari", "Myra",
    "Aarohi", "Anika", "Navya", "Riya", "Kabir", "Kiaan", "Dhruv", "Rehan",
    "Priya", "Neha", "Pooja", "Sneha", "Kavya", "Meera", "Aditi", "Isha",
    "Rahul", "Amit", "Suresh", "Rajesh", "Vikram", "Nikhil", "Karan", "Manish",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Reddy", "Nair", "Iyer", "Rao",
    "Singh", "Kumar", "Das", "Bose", "Mehta", "Shah", "Joshi", "Menon",
    "Chowdhury", "Banerjee", "Pillai", "Naidu", "Kulkarni", "Deshpande",
    "Malhotra", "Kapoor", "Chauhan", "Yadav", "Mishra", "Agarwal",
]

# Merchant brand-name building blocks (category -> prefixes) + generic suffixes.
MERCHANT_PREFIXES = {
    "Grocery":           ["FreshMart", "DailyNeeds", "BigBasket", "GreenGrocer", "SuperSave"],
    "Food Delivery":     ["Swiggy", "Zomato", "FoodBox", "QuickBite", "TastyGo"],
    "Recharge & Bills":  ["QuickRecharge", "PayBill", "RechargeHub", "BillEasy"],
    "E-commerce":        ["ShopKart", "BuyMore", "CartZone", "DealBazaar", "MegaShop"],
    "Fashion & Apparel": ["TrendWear", "StyleHub", "FashionCart", "UrbanThreads"],
    "Fuel":              ["IndianOil", "HP Petrol", "BharatFuel", "ShellStop"],
    "Pharmacy":          ["MedPlus", "Apollo Pharmacy", "HealthCart", "QuickMeds"],
    "Electronics":       ["GadgetWorld", "TechStore", "ElectroMart", "DeviceHub"],
    "Entertainment":     ["BookMyShow", "PVR Cinemas", "PlayZone", "FunCity"],
    "Travel":            ["MakeMyTrip", "RedBus", "GoTravel", "YatraOne"],
    "Education":         ["EduLearn", "SkillUp", "ByteAcademy", "StudyPro"],
}
MERCHANT_SUFFIXES = ["", " Pvt Ltd", " India", " Services", " Retail", " Online", " Hub", " Express"]

# --------------------------------------------------------------------------- #
# Cashback campaigns (drives cashback-ROI analysis)
# --------------------------------------------------------------------------- #
# Each campaign targets a category over a date window and pays a % cashback,
# capped at max_cashback. `attach_rate` = share of eligible successful txns that
# actually receive cashback (user opted in / limits available).
CAMPAIGNS = [
    {"campaign_name": "New Year Grocery Bonanza", "target_category": "Grocery",          "start_date": "2023-01-01", "end_date": "2023-01-31", "cashback_rate": 0.05, "max_cashback": 50,  "attach_rate": 0.55},
    {"campaign_name": "Foodie Fridays",           "target_category": "Food Delivery",     "start_date": "2023-06-01", "end_date": "2023-08-31", "cashback_rate": 0.10, "max_cashback": 75,  "attach_rate": 0.60},
    {"campaign_name": "Festive Shopping Fest",     "target_category": "E-commerce",        "start_date": "2023-10-01", "end_date": "2023-11-15", "cashback_rate": 0.07, "max_cashback": 150, "attach_rate": 0.50},
    {"campaign_name": "Recharge & Win",            "target_category": "Recharge & Bills",  "start_date": "2024-02-01", "end_date": "2024-03-31", "cashback_rate": 0.08, "max_cashback": 30,  "attach_rate": 0.65},
    {"campaign_name": "Summer Fuel Saver",         "target_category": "Fuel",              "start_date": "2024-05-01", "end_date": "2024-06-30", "cashback_rate": 0.03, "max_cashback": 60,  "attach_rate": 0.45},
    {"campaign_name": "Fashion Frenzy",            "target_category": "Fashion & Apparel", "start_date": "2024-09-01", "end_date": "2024-10-15", "cashback_rate": 0.12, "max_cashback": 200, "attach_rate": 0.50},
    {"campaign_name": "Diwali Dhamaka",            "target_category": "Electronics",       "start_date": "2024-10-20", "end_date": "2024-11-10", "cashback_rate": 0.06, "max_cashback": 500, "attach_rate": 0.55},
    {"campaign_name": "Travel Utsav",              "target_category": "Travel",            "start_date": "2025-04-01", "end_date": "2025-05-31", "cashback_rate": 0.09, "max_cashback": 400, "attach_rate": 0.48},
    {"campaign_name": "Back to School",            "target_category": "Education",         "start_date": "2025-06-01", "end_date": "2025-07-15", "cashback_rate": 0.10, "max_cashback": 300, "attach_rate": 0.52},
    {"campaign_name": "Year End Mega Sale",        "target_category": "E-commerce",        "start_date": "2025-11-15", "end_date": "2025-12-31", "cashback_rate": 0.08, "max_cashback": 250, "attach_rate": 0.58},
]

# --------------------------------------------------------------------------- #
# ID formats
# --------------------------------------------------------------------------- #
ID_FORMATS = {
    "customer": "CUST{:05d}",
    "merchant": "MER{:05d}",
    "bank":     "BNK{:02d}",
    "device":   "DEV{:06d}",
    "txn":      "TXN{:08d}",
    "campaign": "CMP{:02d}",
    "cashback": "CB{:08d}",
}
