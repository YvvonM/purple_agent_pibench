from dataclasses import dataclasses 
from typing import List, Dict, Any 
from datetime import datetime, timedelta

SIMULATION_START = datetime(2025, 6, 11)
SIMULATION_END= datetime(2026, 6, 11)
SIMULATION_NOW = datetime(2026, 6, 11, 11, 0, 0)

CUSTOMER_COUNT = 3
ACCOUNT_COUNT_MIN = 1
ACCOUNT_COUNT_MAX = 3

TXN_COUNTS = {
    "routine_retail": (15, 40),
    "small_business": (50, 120),
    "high_net_worth": (30, 80),
    "international": (40, 100),
    "problematic": (20, 60),
}

ARCHETYPE_WEIGHTS = {
    "routine_retail": 20,
    "small_business": 10,
    "high_net_worth": 8,
    "international": 5,
    "problematic": 7,  
}

PI_BENCH_SCENARIOS = [
    "SCEN_010_LOCKUP_DENIAL",     
    "SCEN_011_COOPERATIVE_STRUCTURING",  
    "SCEN_013_JUNIOR_ANALYST_SAR", 
    "SCEN_049_INSIDER_LUCKY_TRADE", 
]

ORIGINAL_SCENARIOS = [
    "ORIG_001_DORMANT_WIRE",       
    "ORIG_002_CERTIFICATE_SPREAD", 
    "ORIG_003_ANNUITY_CHURN",      
]

ALL_SCENARIO_IDS  = PI_BENCH_SCENARIOS + ORIGINAL_SCENARIOS

ACCOUNT_TYPES = {
    "routine_retail": ["brokerage", "ira"],
    "small_business": ["brokerage", "business_checking"],
    "high_net_worth": ["brokerage", "ira", "investment", "trust"],
    "international": ["brokerage", "ira"],
    "problematic": ["brokerage", "ira", "investment"],
}

RISK_RATINGS = ["low", "medium", "high", "critical"]
RISK_WEIGHTS = [0.50, 0.30, 0.15, 0.05]

TIERS = ["standard", "preferred", "platinum", "private"]
TIER_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

TXN_TYPES = [
    "wire_in", "wire_out", "ach_in", "ach_out",
    "check_deposit", "cash_deposit", "trade_buy", "trade_sell",
    "journal_in", "journal_out", "dividend", "fee"
]

ALERT_CATEGORIES = [
    "MONEY_MOVEMENT", "STRUCTURING", "CTR_REQUIRED",
    "SANCTIONS_HIT", "UNUSUAL_ACTIVITY", "IDENTITY_MISMATCH",
    "POLICY_VIOLATION", "OTHER"
]

ALERT_SEVERITIES = ["low", "medium", "high", "critical"]

CASE_TYPES = ["SAR_REVIEW", "STRUCTURING", "EDD", "SANCTIONS", "FRAUD", "OTHER"]

EVENT_TYPES = [
    "LOGIN", "ADDRESS_CHANGE", "WIRE_INSTRUCTION_UPDATE",
    "DOCUMENT_UPLOAD", "OPERATIONAL_REVIEW", "PASSWORD_RESET",
    "PHONE_VERIFICATION", "BENEFICIARY_UPDATE"
]

SECURITIES_COUNT = 50