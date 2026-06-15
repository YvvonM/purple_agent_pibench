import random 
import string 
from datetime import datetime, timedelta 
from typing import Optional, List, Tuple
from decimal import Decimal, ROUND_HALF_UP
from faker import Faker

_faker = Faker("en_US")
Faker.seed_instance(42)

def gen_customer_id(name: str) -> str:
    """CUST_FIRST_LAST or CUST_FIRST_LAST_N"""
    clean = name.lower().replace(" ", "_").replace("-", "_")
    clean = "".join(c for c in clean if c.isalnum or c == "_")
    name = f"CUST_{clean[:20]}"

def gen_account_id(customer_id: str, seq: int) -> str:
    """ACCT_CUST_001, ACCT_CUST_002, etc."""
    cust_id = f"{customer_id.replace("CUST_", "ACCT_")}_CUST_{seq:03d}"
    return cust_id

def gen_transaction_id(prefix: str = "TXN") -> str:
    """TXN_20260613_A7K3M9 — includes date and random suffix."""
    date_str = datetime.now().strftime("%Y%m%d")
    suffix  = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    txn_id = f"{prefix}_{date_str}_{suffix}"
    return txn_id

def gen_alert_id() -> str:
    """ALERT_20260613_001, ALERT_20260613_002"""
    date_str = datetime.now().strftime("%Y%m%d")
    seq = random.randint(1,999)
    alert_id = f"ALART_{date_str}_{seq:03d}"
    return alert_id 

def gen_case_id() -> str:
    """CASE_20260613_001, CASE_20260613_002"""
    date_str = datetime.now().strftime("%Y%m%d")
    seq = random.randint(1, 999)
    case_id = f"CASE_{date_str}_{seq:03d}"
    return case_id

def gen_request_id() -> str:
    """REQ_20260613_001, REQ_20260613_002"""
    date_str = datetime.now().strftime("%Y%m%d")
    seq = random.randint(1, 999)
    req_id = f"REQ_{date_str}_{seq:03d}"
    return req_id

def gen_event_id() -> str:
    """EVT_20260613_001, EVT_20260613_002"""
    date_str = datetime.now().strftime("%Y%m%d")
    seq = random.randint(1, 999)
    evt_id = f"EVT_{date_str}_{seq:03d}"
    return evt_id

def gen_decision_id() -> str:
    """DEC_20260613_002, DEC_20260613_002"""
    date_str = datetime.now().strftime("%Y%m%d")
    seq = random.randint(1, 999)
    dec_id = f"DEC_{date_str}_{seq:03d}"
    return dec_id

def gen_employee_id() -> str:
    """EMP_001, EMP_002"""
    seq = random.randint(1, 999)
    emp_id = f"EMP_{seq:03d}"
    return emp_id 

def random_date_between(start: datetimez, end: datetime) -> datetime:
    delta = end - start 
    random_seconds = random.randint(0, int(delta.total_seconds()))
    time = start + timedelta(seconds = random_seconds)

def random_past_date(days_back: int, from_date: Optional[datetime] = None) -> datetime:
    ref = from_date or datetime.now()
    back = ref - timedelta(days=random.randint(0, days_back))
    return back 

def random_recent_date(hours_back: int, from_date: Optional[datetime] = None) -> datetime:
    ref = from_date or datetime.now()
    back = ref - timedelta(hours=random.randint(0, hours_back))
    return back 

def date_sequence(start: datetime, end: datetime, count: int, min_gap_days: int = 1, max_gap_days: int = 30) -> List[datetime]:
    dates = [start]
    current = start 
    for _ in range(count - 1):
        gap = timedelta(random.randint(min_gap_days, max_gap_days))
        current = min(current + gap, end)
        dates.append(current)
    return dates 

def random_amount(min_usd: float = 10.0, max_usd: float = 1000000.0) -> Decimal:
    """Random dollar amount, rounded to 2 decimal places."""
    amount = random.uniform(min_usd, max_usd)
    rand_amount =Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return rand_amount


def round_amount(amount: Decimal) -> Decimal:
    """Ensure 2 decimal places."""
    round_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return round_amount

def weighted_choice(options: List[str], weights: List[float]) -> str:
    """Pick one option based on weights."""
    return random.choices(options, weights=weights, k=1)[0]


def maybe(probability: float = 0.5) -> bool:
    """True with given probability."""
    return random.random() < probability

def fake_name() -> str:
    return _faker.name()

def fake_email(name: str) -> str:
    clean = name.lower().replace(" ", ".").replace("-", "")
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "example.com", "company.com"])
    email = f"{clean}@{domain}"
    return email 

def fake_phone() -> str:
    return _faker.phone_number()


def fake_address() -> dict:
    """Return structured address dict."""
    return {
        "street": _faker.street_address(),
        "city": _faker.city(),
        "state": _faker.state_abbr(),
        "zip": _faker.zipcode(),
    }

def fake_company() -> str:
    return _faker.company()


def fake_job_title() -> str:
    return _faker.job()

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
]

def random_state() -> str:
    return random.choice(US_STATES)


BANKS = [
    "JPMorgan Chase", "Bank of America", "Wells Fargo", "Citibank",
    "Goldman Sachs", "Morgan Stanley", "TD Bank", "PNC Bank",
    "Truist", "U.S. Bank", "Charles Schwab", "Fidelity",
    "Northern Trust", "State Street", "BNY Mellon", "HSBC",
    "Barclays", "Deutsche Bank", "Credit Suisse", "UBS",
]

def random_bank() -> str:
    return random.choice(BANKS)

COMMON_ETFS = ["VTI", "VOO", "BND", "VTIP", "VEA", "VWO", "VGIT", "VTEB"]
COMMON_STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM"]

def random_security() -> Tuple[str, str]:
    """Return (ticker, name) for a common security."""
    all_secs = COMMON_ETFS + COMMON_STOCKS
    ticker = random.choice(all_secs)
    
    names = {
        "VTI": "Vanguard Total Stock Market ETF",
        "VOO": "Vanguard S&P 500 ETF",
        "BND": "Vanguard Total Bond Market ETF",
        "VTIP": "Vanguard Short-Term Inflation-Protected Securities ETF",
        "VEA": "Vanguard FTSE Developed Markets ETF",
        "VWO": "Vanguard FTSE Emerging Markets ETF",
        "VGIT": "Vanguard Intermediate-Term Treasury ETF",
        "VTEB": "Vanguard Tax-Exempt Bond ETF",
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "META": "Meta Platforms Inc.",
        "NVDA": "NVIDIA Corporation",
        "JPM": "JPMorgan Chase & Co.",
    }
    return ticker, names.get(ticker, ticker)





