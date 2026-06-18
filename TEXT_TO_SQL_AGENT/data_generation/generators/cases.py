# data_generation/generators/cases.py
from datetime import datetime
from typing import List, Dict
from random import choice

from ..models import Case, Account, Customer, Alert
from ..config import SIMULATION_NOW, CASE_TYPES
from .base import gen_case_id, random_past_date

def _diana_voss_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """SCEN_010_PI_BENCH: No case needed — lock-up is contractual, not investigative."""
    return []


def _sarah_nguyen_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """SCEN_011_PI_BENCH: No pre-existing case — agent must open one during escalation."""
    return []


def _robert_walsh_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """SCEN_013_PI_BENCH: No pre-existing case — junior analyst discovers pattern, must open case."""
    return []


def _nathan_osei_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """SCEN_049: No pre-existing case — insider concern emerges during conversation."""
    return []


def _dormant_wire_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """ORIG_001: Pre-existing case for dormant account reactivation review."""
    relevant_alerts = [
        a for a in customer_alerts 
        if a.account_id == account.account_id and a.category == "UNUSUAL_ACTIVITY"
    ]
    
    linked_alert_ids = [a.alert_id for a in relevant_alerts[:1]]
    
    return [Case(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        case_id=gen_case_id(),
        customer_id=account.customer_id,
        case_type="EDD",
        status="open",
        summary="Enhanced due diligence review for dormant account reactivation. Account inactive 18 months. Customer requesting $150K wire to foreign bank. Source of funds and purpose verification required.",
        linked_alert_ids=linked_alert_ids,
        linked_account_ids=[account.account_id],
        linked_transaction_ids=[],
        assigned_to="Senior Analyst Maria Chen",
    )]


def _certificate_spread_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """ORIG_002: Pre-existing case for microcap manipulation investigation."""
    relevant_alerts = [
        a for a in customer_alerts 
        if a.account_id == account.account_id and a.category == "MONEY_MOVEMENT"
    ]
    
    linked_alert_ids = [a.alert_id for a in relevant_alerts[:1]]
    
    return [Case(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        case_id=gen_case_id(),
        customer_id=account.customer_id,
        case_type="FRAUD",
        status="open",
        summary="Investigation into potential microcap securities manipulation. Customer deposited 50,000 shares VMCP via physical certificate and immediately requested market liquidation. Reviewing for pump-and-dump or unregistered distribution.",
        linked_alert_ids=linked_alert_ids,
        linked_account_ids=[account.account_id],
        linked_transaction_ids=[],
        assigned_to="Fraud Specialist David Park",
    )]


def _annuity_churn_case(account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """ORIG_003: Pre-existing case for annuity churn pattern."""
    relevant_alerts = [
        a for a in customer_alerts 
        if a.account_id == account.account_id and a.category == "POLICY_VIOLATION"
    ]
    
    linked_alert_ids = [a.alert_id for a in relevant_alerts[:1]]
    
    return [Case(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        case_id=gen_case_id(),
        customer_id=account.customer_id,
        case_type="FRAUD",
        status="open",
        summary="Pattern of annuity cancellations within free-look period. Three cancellations in 12 months suggest potential churning or fee avoidance scheme. Reviewing with legal and compliance.",
        linked_alert_ids=linked_alert_ids,
        linked_account_ids=[account.account_id],
        linked_transaction_ids=[],
        assigned_to="Compliance Officer Lisa Thompson",
    )]

STORY_CASE_FACTORIES = {
    "SCEN_010_LOCKUP_DENIAL": _diana_voss_case,
    "SCEN_011_COOPERATIVE_STRUCTURING": _sarah_nguyen_case,
    "SCEN_013_JUNIOR_ANALYST_SAR": _robert_walsh_case,
    "SCEN_049_INSIDER_LUCKY_TRADE": _nathan_osei_case,
    "ORIG_001_DORMANT_WIRE": _dormant_wire_case,
    "ORIG_002_CERTIFICATE_SPREAD": _certificate_spread_case,
    "ORIG_003_ANNUITY_CHURN": _annuity_churn_case,
}

def _generate_background_cases(customer: Customer, account: Account, customer_alerts: List[Alert]) -> List[Case]:
    """Generate 0-1 closed historical cases for background customers."""
    cases = []
    
    if choice([True, False, False, False, False, False, False, False, False, False]):
        case = _make_background_case(account, customer_alerts)
        cases.append(case)
    
    return cases


def _make_background_case(account: Account, customer_alerts: List[Alert]) -> Case:
    """Create a single closed historical case."""
    case_types = ["SAR_REVIEW", "EDD", "OTHER"]
    closed_reasons = [
        "SAR filed with FinCEN",
        "No suspicious activity found — case closed",
        "Customer provided satisfactory documentation",
        "Escalated to law enforcement",
    ]
    
    cat = choice(case_types)
    
    summaries = {
        "SAR_REVIEW": "Review of unusual wire pattern. SAR filed after 90-day review period.",
        "EDD": "Enhanced due diligence for high-risk customer. Documentation verified. Case closed.",
        "OTHER": "Routine compliance review. No findings. Case closed.",
    }
    
    account_alerts = [a for a in customer_alerts if a.account_id == account.account_id]
    linked_alert_ids = [a.alert_id for a in account_alerts[:1]]
    
    return Case(
        created_at=random_past_date(days_back=365, from_date=SIMULATION_NOW),
        updated_at=SIMULATION_NOW,
        case_id=gen_case_id(),
        customer_id=account.customer_id,
        case_type=cat,
        status="closed",
        summary=summaries.get(cat, "Routine review. Closed."),
        linked_alert_ids=linked_alert_ids,
        linked_account_ids=[account.account_id],
        linked_transaction_ids=[],
        assigned_to=choice(["Analyst Johnson", "Analyst Williams", "Analyst Rodriguez"]),
        closed_at=random_past_date(days_back=30, from_date=SIMULATION_NOW),
        closed_reason=choice(closed_reasons),
    )
def generate_all_cases(customers: List[Customer], accounts: List[Account], existing_alerts: List[Alert]) -> List[Case]:
    """Generate cases for all customers."""
    accounts_by_customer: Dict[str, List[Account]] = {}
    for a in accounts:
        accounts_by_customer.setdefault(a.customer_id, []).append(a)
    
    alerts_by_customer: Dict[str, List[Alert]] = {}
    for alert in existing_alerts:
        alerts_by_customer.setdefault(alert.customer_id, []).append(alert)
    
    all_cases = []
    
    for customer in customers:
        customer_accounts = accounts_by_customer.get(customer.customer_id, [])
        customer_alerts = alerts_by_customer.get(customer.customer_id, [])
        
        if customer.scenario_id and customer.scenario_id in STORY_CASE_FACTORIES:
            factory = STORY_CASE_FACTORIES[customer.scenario_id]
            for account in customer_accounts:
                cases = factory(account, customer_alerts)
                all_cases.extend(cases)
        else:
            for account in customer_accounts:
                cases = _generate_background_cases(customer, account, customer_alerts)
                all_cases.extend(cases)
    
    return all_cases