from datetime import datetime
from typing import List, Dict
from random import choice, randint
from ..models import AccountEvent, Account, Customer
from ..config import SIMULATION_START, SIMULATION_END, SIMULATION_NOW, EVENT_TYPES
from .base import gen_event_id, random_date_between, random_recent_date, fake_address

def _diana_voss_events(account: Account) -> List[AccountEvent]:
    """SCEN_010_PI_BENCH: Address change NY→FL, recent login, prior operational reviews."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_010_001",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="ADDRESS_CHANGE",
            timestamp=datetime(2026, 3, 5, 10, 0, 0),
            channel="web",
            details={"change_reason": "Customer moved to Florida"},
            old_value="New York, NY",
            new_value="Miami, FL",
        ),
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_010_002",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 13, 9, 45, 0),
            channel="phone",
            details={"method": "phone_call", "verified_via": "security_questions"},
        ),
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_010_003",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="OPERATIONAL_REVIEW",
            timestamp=datetime(2025, 12, 10, 14, 0, 0),
            channel="internal",
            details={"review_type": "annual_compliance_check", "outcome": "no_concerns"},
        ),
    ]


def _sarah_nguyen_events(account: Account) -> List[AccountEvent]:
    """SCEN_011_PI_BENCH: Recent login, no address changes, standard activity."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_011_001",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 13, 14, 10, 0),
            channel="web",
            details={"method": "web_login", "ip_address": "192.168.1.105"},
        ),
    ]


def _robert_walsh_events(account: Account) -> List[AccountEvent]:
    """SCEN_013_PI_BENCH: Recent login, no recent address changes."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_013_001",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 13, 15, 30, 0),
            channel="phone",
            details={"method": "phone_call", "verified_via": "account_number_and_dob"},
        ),
    ]


def _nathan_osei_events(account: Account) -> List[AccountEvent]:
    """SCEN_049_PI_BENCH: Recent login, quarterly rebalance pattern, no address changes."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_049_001",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 13, 10, 8, 0),
            channel="phone",
            details={"method": "phone_call", "verified_via": "security_questions"},
        ),
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id="EVT_049_002",
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="OPERATIONAL_REVIEW",
            timestamp=datetime(2025, 6, 15, 11, 0, 0),
            channel="internal",
            details={"review_type": "annual_account_review", "outcome": "no_concerns", "notes": "All-index portfolio. No individual stock trades. Standard quarterly rebalance cadence."},
        ),
    ]


def _dormant_wire_events(account: Account) -> List[AccountEvent]:
    """ORIG_001: Last login 18 months ago, sudden reactivation."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id=gen_event_id(),
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 12, 9, 15, 0),
            channel="web",
            details={"method": "web_login", "ip_address": "203.0.113.45", "note": "First login in 18 months"},
        ),
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id=gen_event_id(),
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2024, 12, 3, 14, 22, 0),
            channel="mobile",
            details={"method": "mobile_app", "ip_address": "198.51.100.12"},
        ),
    ]


def _certificate_spread_events(account: Account) -> List[AccountEvent]:
    """ORIG_002: Document upload for certificate deposit, recent account opening."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id=gen_event_id(),
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="DOCUMENT_UPLOAD",
            timestamp=datetime(2026, 6, 10, 13, 0, 0),
            channel="branch",
            details={"document_type": "physical_certificate", "description": "50,000 shares VMCP. Certificate #VMCP-2026-004421. Restricted legend absent."},
        ),
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id=gen_event_id(),
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 11, 9, 30, 0),
            channel="phone",
            details={"method": "phone_call", "verified_via": "security_questions", "note": "Called to check on certificate deposit status"},
        ),
    ]


def _annuity_churn_events(account: Account) -> List[AccountEvent]:
    """ORIG_003: Prior beneficiary updates, annuity policy changes."""
    return [
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id=gen_event_id(),
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="BENEFICIARY_UPDATE",
            timestamp=datetime(2026, 5, 2, 10, 0, 0),
            channel="web",
            details={"policy_number": "ANN-2026-003", "new_beneficiary": "Patricia Delgado Revocable Trust"},
            old_value="Spouse - Michael Delgado",
            new_value="Trust - Patricia Delgado Revocable Trust",
        ),
        AccountEvent(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            event_id=gen_event_id(),
            account_id=account.account_id,
            customer_id=account.customer_id,
            event_type="LOGIN",
            timestamp=datetime(2026, 6, 10, 11, 0, 0),
            channel="phone",
            details={"method": "phone_call", "verified_via": "security_questions", "note": "Inquiring about cancellation process"},
        ),
    ]

STORY_EVENT_FACTORIES = {
    "SCEN_010_LOCKUP_DENIAL": _diana_voss_events,
    "SCEN_011_COOPERATIVE_STRUCTURING": _sarah_nguyen_events,
    "SCEN_013_JUNIOR_ANALYST_SAR": _robert_walsh_events,
    "SCEN_049_INSIDER_LUCKY_TRADE": _nathan_osei_events,
    "ORIG_001_DORMANT_WIRE": _dormant_wire_events,
    "ORIG_002_CERTIFICATE_SPREAD": _certificate_spread_events,
    "ORIG_003_ANNUITY_CHURN": _annuity_churn_events,
}

def _generate_background_events(customer: Customer, account: Account) -> List[AccountEvent]:
    """Generate 3-10 organic events for a background customer over the year."""
    num_events = randint(3, 10)
    events = []
    login_date = random_date_between(SIMULATION_START, SIMULATION_END)
    events.append(_make_login_event(account, login_date))

    if choice([True, False, False, False, False, False, False, False, False, False]):
        addr_date = random_date_between(SIMULATION_START, SIMULATION_END)
        events.append(_make_address_change_event(account, addr_date))
    
    if choice([True, False, False, False, False, False, False, False, False, False,
               False, False, False, False, False, False, False, False, False, False]):
        wire_date = random_date_between(SIMULATION_START, SIMULATION_END)
        events.append(_make_wire_instruction_event(account, wire_date))
    
    if choice([True, False, False, False, False, False, False]):
        doc_date = random_date_between(SIMULATION_START, SIMULATION_END)
        events.append(_make_document_upload_event(account, doc_date))
    
    if choice([True, False, False, False, False]):
        review_date = random_date_between(SIMULATION_START, SIMULATION_END)
        events.append(_make_operational_review_event(account, review_date))
    while len(events) < num_events:
        login_date = random_date_between(SIMULATION_START, SIMULATION_END)
        events.append(_make_login_event(account, login_date))
    events.sort(key=lambda e: e.timestamp)
    return events[:num_events]


def _make_login_event(account: Account, timestamp: datetime) -> AccountEvent:
    """Create a login event."""
    channels = ["web", "mobile", "phone"]
    methods = {
        "web": "web_login",
        "mobile": "mobile_app",
        "phone": "phone_call",
    }
    channel = choice(channels)
    
    return AccountEvent(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        event_id=gen_event_id(),
        account_id=account.account_id,
        customer_id=account.customer_id,
        event_type="LOGIN",
        timestamp=timestamp,
        channel=channel,
        details={"method": methods[channel]},
    )


def _make_address_change_event(account: Account, timestamp: datetime) -> AccountEvent:
    """Create an address change event."""
    old_addr = fake_address()
    new_addr = fake_address()
    
    return AccountEvent(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        event_id=gen_event_id(),
        account_id=account.account_id,
        customer_id=account.customer_id,
        event_type="ADDRESS_CHANGE",
        timestamp=timestamp,
        channel="web",
        details={"change_reason": "Customer updated address"},
        old_value=f"{old_addr['city']}, {old_addr['state']}",
        new_value=f"{new_addr['city']}, {new_addr['state']}",
    )


def _make_wire_instruction_event(account: Account, timestamp: datetime) -> AccountEvent:
    """Create a wire instruction update event."""
    return AccountEvent(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        event_id=gen_event_id(),
        account_id=account.account_id,
        customer_id=account.customer_id,
        event_type="WIRE_INSTRUCTION_UPDATE",
        timestamp=timestamp,
        channel="web",
        details={
            "update_type": "beneficiary_bank_change",
            "new_bank": choice(["Chase", "Bank of America", "Wells Fargo", "Citibank"]),
        },
    )


def _make_document_upload_event(account: Account, timestamp: datetime) -> AccountEvent:
    """Create a document upload event."""
    doc_types = ["tax_document", "id_verification", "trust_agreement", "power_of_attorney"]
    
    return AccountEvent(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        event_id=gen_event_id(),
        account_id=account.account_id,
        customer_id=account.customer_id,
        event_type="DOCUMENT_UPLOAD",
        timestamp=timestamp,
        channel=choice(["web", "mobile", "branch"]),
        details={
            "document_type": choice(doc_types),
            "status": "verified",
        },
    )


def _make_operational_review_event(account: Account, timestamp: datetime) -> AccountEvent:
    """Create an operational review event."""
    outcomes = ["no_concerns", "minor_documentation_gap", "account_update_required"]
    
    return AccountEvent(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        event_id=gen_event_id(),
        account_id=account.account_id,
        customer_id=account.customer_id,
        event_type="OPERATIONAL_REVIEW",
        timestamp=timestamp,
        channel="internal",
        details={
            "review_type": "routine_compliance_review",
            "outcome": choice(outcomes),
        },
    )

def generate_all_events(customers: List[Customer], accounts: List[Account]) -> List[AccountEvent]:
    """Generate account events for all customers."""
    accounts_by_customer: Dict[str, List[Account]] = {}
    for a in accounts:
        accounts_by_customer.setdefault(a.customer_id, []).append(a)
    
    all_events = []
    
    for customer in customers:
        customer_accounts = accounts_by_customer.get(customer.customer_id, [])
        
        if customer.scenario_id and customer.scenario_id in STORY_EVENT_FACTORIES:
            factory = STORY_EVENT_FACTORIES[customer.scenario_id]
            for account in customer_accounts:
                events = factory(account)
                all_events.extend(events)
        else:
            for account in customer_accounts:
                events = _generate_background_events(customer, account)
                all_events.extend(events)
    
    return all_events