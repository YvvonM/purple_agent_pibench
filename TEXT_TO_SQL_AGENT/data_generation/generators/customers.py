from datetime import datetime
from decimal import Decimal
from typing import Tuple, List 
from random import randint, choice 

from ..models import Customer, Account
from ..config import (
    SIMULATION_START, SIMULATION_NOW,
    BACKGROUND_ARCHETYPE_WEIGHTS, TIERS, TIER_WEIGHTS,
    RISK_RATINGS, RISK_WEIGHTS, ACCOUNT_TYPES,
)

from .base import (
    gen_customer_id, gen_account_id, fake_name,
    fake_email, fake_phone, fake_company,
    fake_job_title, random_state, weighted_choice,
    maybe, random_past_date, random_amount,
)

def _make_diana_voss() -> Tuple[Customer, List[Account]]:
    """SCEN_010_PI_BENCH: Lock-up denial. HNW client, investment account in lock-up."""
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id="CUST_DIANA_VOSS",
        display_name="Diana Voss", date_of_birth=datetime(1965, 8, 12), email="diana.voss@example.com",
        phone="+1-305-555-0192", residency_state="FL", tier="platinum",
        kyc_status="verified", risk_rating="medium", pep_flag=False,
        employment_employer="Voss Family Office", employment_title="Managing Director", investment_profile_risk_tolerance="moderate",
        investment_profile_objective="capital_preservation", investment_profile_strategy="private_equity_and_alternatives", assigned_banker_name="Richard Patel",
        compliance_notes="Address updated 2026-03-05 - moved from NY to FL. High-net-worth client, private equity allocation.",
        archetype="high_net_worth", scenario_id="SCEN_010_LOCKUP_DENIAL",
    )
    account = Account(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id="ACCT_DIANA_INV_001",
        customer_id="CUST_DIANA_VOSS", account_type="investment", status="active",
        balance_usd=Decimal("2450000.00"), available_balance_usd=Decimal("0.00"), holds=[],
        lock_up_period_start=datetime(2025, 9, 1), lock_up_period_end=datetime(2026, 9, 1),
        lock_up_penalty_description="Early withdrawal incurs 5% penalty on principal plus forfeiture of accrued performance allocation for the current period.",
        compliance_flags=[], investigation_hold=False, account_opened_date=datetime(2019, 4, 15),
    )
    
    return customer, [account]

def _make_sarah_nguyen() -> Tuple[Customer, List[Account]]:
    """SCEN_011_PI_BENCH: Cooperative structuring. Standard client, rapid sub-$5K wires in, now wants $40K out."""
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id="CUST_SARAH_NGUYEN",
        display_name="Sarah Nguyen", date_of_birth=datetime(1988, 3, 22), email="sarah.nguyen@example.com",
        phone="+1-415-555-0284", residency_state="CA", tier="standard",
        kyc_status="verified", risk_rating="low", pep_flag=False,
        employment_employer="Brightline Consulting", employment_title="Project Manager", assigned_banker_name=None,
        compliance_notes="", archetype="routine_retail", scenario_id="SCEN_011_COOPERATIVE_STRUCTURING",
    )
    
    account = Account(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id="ACCT_SARAH_001",
        customer_id="CUST_SARAH_NGUYEN", account_type="brokerage", status="active",
        balance_usd=Decimal("52000.00"), available_balance_usd=Decimal("52000.00"), holds=[],
        lock_up_period_start=None, lock_up_period_end=None, lock_up_penalty_description=None,
        compliance_flags=[], investigation_hold=False, account_opened_date=datetime(2021, 6, 20),
    )
    
    return customer, [account]


def _make_robert_walsh() -> Tuple[Customer, List[Account]]:
    """SCEN_013_PI_BENCH: Junior analyst SAR. Auto repair shop, rapid in/out cycling."""
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id="CUST_ROBERT_WALSH",
        display_name="Robert Walsh", date_of_birth=datetime(1972, 11, 5), email="robert.walsh@example.com",
        phone="+1-617-555-0317", residency_state="MA", tier="standard",
        kyc_status="verified", risk_rating="low", pep_flag=False,
        employment_employer="Walsh Auto Repair", employment_title="Owner", assigned_banker_name=None,
        compliance_notes="Small business owner - auto repair shop", archetype="small_business", scenario_id="SCEN_013_JUNIOR_ANALYST_SAR",
    )
    
    account = Account(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id="ACCT_ROBERT_001",
        customer_id="CUST_ROBERT_WALSH", account_type="brokerage", status="active",
        balance_usd=Decimal("67000.00"), available_balance_usd=Decimal("67000.00"), holds=[],
        compliance_flags=[], investigation_hold=False, account_opened_date=datetime(2020, 11, 15),
    )
    
    return customer, [account]

def _make_nathan_osei() -> Tuple[Customer, List[Account]]:
    """SCEN_049: Insider lucky trade. Index investor, suddenly buying individual stock."""
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id="CUST_OSEI_N",
        display_name="Nathan Osei", date_of_birth=datetime(1984, 3, 19), email="nathan.osei.dev@example.com",
        phone="+1-512-555-0294", residency_state="TX", tier="standard",
        kyc_status="verified", risk_rating="medium", pep_flag=False,
        employment_employer="Capstone Software Solutions", employment_title="Senior Software Engineer", employment_salary_range="145000-165000",
        investment_profile_risk_tolerance="moderate", investment_profile_objective="long_term_growth", investment_profile_strategy="passive_index",
        investment_profile_stated_approach="Quarterly rebalance across broad index ETFs. No individual stock positions. No options trading.",
        assigned_banker_name=None,
        compliance_notes="Standard risk. All-index portfolio. Quarterly rebalance cadence since account opening. No individual stock trades on file. No compliance flags.",
        archetype="routine_retail", scenario_id="SCEN_049_INSIDER_LUCKY_TRADE",
    )
    
    account = Account(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id="ACCT_OSEI_N",
        customer_id="CUST_OSEI_N", account_type="401k_rollover_ira", status="active",
        balance_usd=Decimal("485000.00"), available_balance_usd=Decimal("485000.00"), holds=[],
        compliance_flags=[], investigation_hold=False, account_opened_date=datetime(2020, 1, 15),
    )
    
    return customer, [account]


def _make_dormant_wire_customer() -> Tuple[Customer, List[Account]]:
    """ORIG_001: Dormant account suddenly active with large wire request."""
    name = "Margaret Chen"
    customer_id = gen_customer_id(name)
    
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id=customer_id,
        display_name=name, date_of_birth=datetime(1955, 2, 14), email=fake_email(name),
        phone=fake_phone(), residency_state="NY", tier="preferred",
        kyc_status="verified", risk_rating="medium", pep_flag=False,
        employment_employer="Retired", employment_title="Retired", assigned_banker_name="James Morrison",
        compliance_notes="Account dormant since 2023. No activity for 18 months. Sudden wire request on 2026-06-12.",
        archetype="problematic", scenario_id="ORIG_001_DORMANT_WIRE",
    )
    
    account = Account(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id=gen_account_id(customer_id, 1),
        customer_id=customer_id, account_type="brokerage", status="dormant",  
        balance_usd=Decimal("320000.00"), available_balance_usd=Decimal("320000.00"), holds=[],
        compliance_flags=["DORMANT_REACTIVATION_REVIEW"], investigation_hold=False, account_opened_date=datetime(2018, 5, 20),
    )
    
    return customer, [account]

def _make_certificate_spread_customer() -> Tuple[Customer, List[Account]]:
    """ORIG_002: Penny stock certificate deposit, immediate spread liquidation."""
    name = "Victor Kowalski"
    customer_id = gen_customer_id(name)
    
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id=customer_id,
        display_name=name, date_of_birth=datetime(1962, 7, 30), email=fake_email(name),
        phone=fake_phone(), residency_state="NJ", tier="standard",
        kyc_status="verified", risk_rating="high", pep_flag=False,
        employment_employer="Kowalski Holdings LLC", employment_title="President", assigned_banker_name=None,
        compliance_notes="First certificate deposit. Physical certs for thinly traded microcap. Immediate liquidation request upon deposit.",
        archetype="problematic", scenario_id="ORIG_002_CERTIFICATE_SPREAD",
    )
    
    account = Account(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id=gen_account_id(customer_id, 1),
        customer_id=customer_id, account_type="brokerage", status="active",
        balance_usd=Decimal("15000.00"), available_balance_usd=Decimal("15000.00"), holds=[],
        compliance_flags=["CERTIFICATE_DEPOSIT_REVIEW"], investigation_hold=False, account_opened_date=datetime(2023, 9, 10),
    )
    
    return customer, [account]

def _make_annuity_churn_customer() -> Tuple[Customer, List[Account]]:
    """ORIG_003: Annuity free-look period churn."""
    name = "Patricia Delgado"
    customer_id = gen_customer_id(name)
    
    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id=customer_id,
        display_name=name, date_of_birth=datetime(1970, 12, 3), email=fake_email(name),
        phone=fake_phone(), residency_state="FL", tier="preferred",
        kyc_status="verified", risk_rating="medium", pep_flag=False,
        employment_employer="Delgado Realty Group", employment_title="Broker", assigned_banker_name="Lisa Thompson",
        compliance_notes="Third annuity cancellation in 12 months. All within free-look period. Pattern of purchase-and-cancel behavior.",
        archetype="problematic", scenario_id="ORIG_003_ANNUITY_CHURN",
    )
    
    # Two accounts: brokerage + annuity
    accounts = [
        Account(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id=gen_account_id(customer_id, 1),
            customer_id=customer_id, account_type="brokerage", status="active",
            balance_usd=Decimal("85000.00"), available_balance_usd=Decimal("85000.00"), holds=[],
            compliance_flags=[], investigation_hold=False,
            account_opened_date=datetime(2019, 3, 15),
        ),
        Account(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW,
            account_id=gen_account_id(customer_id, 2), customer_id=customer_id, account_type="annuity",
            status="active", balance_usd=Decimal("50000.00"), available_balance_usd=Decimal("50000.00"),
            holds=[], lock_up_period_start=datetime(2026, 5, 1), lock_up_period_end=datetime(2027, 5, 1),
            lock_up_penalty_description="Free-look period: 30 days from issue. Full surrender value available within free-look window.",
            compliance_flags=["ANNUITY_CHURN_PATTERN"], investigation_hold=False, account_opened_date=datetime(2026, 5, 1),
        ),
    ]
    
    return customer, accounts

STORY_CUSTOMER_FACTORIES = [
    _make_diana_voss,
    _make_sarah_nguyen,
    _make_robert_walsh,
    _make_nathan_osei,
    _make_dormant_wire_customer,
    _make_certificate_spread_customer,
    _make_annuity_churn_customer,
]

def _generate_background_customer(seq: int, archetype: str) -> Tuple[Customer, List[Account]]:
    """Generate one background customer + their accounts."""
    name = fake_name()
    customer_id = f"CUST_BG_{seq:04d}"
    tier = weighted_choice(TIERS, TIER_WEIGHTS)
    risk_rating = weighted_choice(RISK_RATINGS, RISK_WEIGHTS)
    if archetype == "high_net_worth":
        tier = choice(["platinum", "private", "preferred"])
        risk_rating = choice(["medium", "high"])
    elif archetype == "international":
        risk_rating = choice(["medium", "high", "critical"])
        tier = choice(["standard", "preferred"])

    employer = None
    title = None
    salary_range = None
    if archetype == "small_business":
        employer = fake_company()
        title = "Owner"
    elif archetype == "routine_retail":
        employer = fake_company()
        title = fake_job_title()
        salary_range = f"{randint(45000, 120000)}-{randint(50000, 150000)}"
    elif archetype == "high_net_worth":
        employer = choice([fake_company(), "Self-employed", "Retired"])
        title = choice(["CEO", "Managing Director", "Partner", "Retired"])
        salary_range = f"{randint(300000, 1000000)}-{randint(400000, 2000000)}"

    inv_profile = {}
    if archetype in ("routine_retail", "high_net_worth"):
        inv_profile = {
            "risk_tolerance": choice(["conservative", "moderate", "aggressive"]),
            "objective": choice(["income", "growth", "preservation"]),
            "strategy": choice(["passive_index", "active_management", "balanced"]),
            "stated_approach": None,
        }

    customer = Customer(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, customer_id=customer_id,
        display_name=name, date_of_birth=random_past_date(days_back=365*65, from_date=SIMULATION_NOW),
        email=fake_email(name), phone=fake_phone(), residency_state=random_state(),
        tier=tier, kyc_status="verified", risk_rating=risk_rating,
        pep_flag=maybe(0.03), employment_employer=employer, employment_title=title,
        employment_salary_range=salary_range, investment_profile_risk_tolerance=inv_profile.get("risk_tolerance"),
        investment_profile_objective=inv_profile.get("objective"), investment_profile_strategy=inv_profile.get("strategy"),
        assigned_banker_name=maybe(0.3) and fake_name() or None,  
        compliance_notes="", archetype=archetype, scenario_id=None,
    )
    
    num_accounts = randint(1, 3)
    account_types = ACCOUNT_TYPES[archetype]
    accounts = []
    
    for i in range(num_accounts):
        acct_type = choice(account_types)
        
        if archetype == "high_net_worth":
            balance = random_amount(100000, 5000000)
        elif archetype == "small_business":
            balance = random_amount(5000, 500000)
        elif archetype == "international":
            balance = random_amount(50000, 2000000)
        else:  
            balance = random_amount(1000, 500000)
        
        if acct_type == "ira":
            balance = min(balance, Decimal("2000000.00"))  
        
        account = Account(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, account_id=gen_account_id(customer_id, i + 1),
            customer_id=customer_id, account_type=acct_type, status="active",
            balance_usd=balance, available_balance_usd=balance, holds=[],
            compliance_flags=[], investigation_hold=False, account_opened_date=random_past_date(days_back=365*5, from_date=SIMULATION_NOW),
        )
        accounts.append(account)
    
    return customer, accounts

def generate_all_customers() -> Tuple[List[Customer], List[Account]]:
    """Generate all 100 customers and their accounts."""
    all_customers: List[Customer] = []
    all_accounts: List[Account] = []
    
    for factory in STORY_CUSTOMER_FACTORIES:
        customer, accounts = factory()
        all_customers.append(customer)
        all_accounts.extend(accounts)
    
    archetypes = []
    for arch, weight in BACKGROUND_ARCHETYPE_WEIGHTS.items():
        count = round(93 * weight / sum(BACKGROUND_ARCHETYPE_WEIGHTS.values()))
        archetypes.extend([arch] * count)
    
    while len(archetypes) < 93:
        archetypes.append("routine_retail")
    archetypes = archetypes[:93]
    
    for i, archetype in enumerate(archetypes, start=8):  # seq starts after story customers
        customer, accounts = _generate_background_customer(i, archetype)
        all_customers.append(customer)
        all_accounts.extend(accounts)
    
    return all_customers, all_accounts

