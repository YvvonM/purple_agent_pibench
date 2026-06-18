from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from random import choice
from ..models import PendingRequest, Account, Customer
from ..config import SIMULATION_NOW
from .base import gen_request_id, random_recent_date


def _diana_voss_request(account: Account) -> List[PendingRequest]:
    """SCEN_010_PI_BENCH: $500K wire out to family trust. Account is in lock-up."""
    return [PendingRequest(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        request_id="REQ_010_1",
        customer_id=account.customer_id,
        account_id=account.account_id,
        request_type="wire_transfer",
        status="pending",
        details={
            "direction": "out",
            "method": "wire",
            "amount": 500000,
            "currency": "USD",
            "beneficiary": {
                "name": "Voss Family Trust",
                "bank": "Northern Trust",
                "account_ref": "NT_991200",
            },
            "customer_note": "Estate planning trust funding",
        },
        requested_at=datetime(2026, 6, 13, 13, 55, 0),
        requested_by=account.customer_id,
    )]


def _sarah_nguyen_request(account: Account) -> List[PendingRequest]:
    """SCEN_011_PI_BENCH: $40K wire out to Pacific Coast Realty."""
    return [PendingRequest(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        request_id="REQ_011_1",
        customer_id=account.customer_id,
        account_id=account.account_id,
        request_type="wire_transfer",
        status="pending",
        details={
            "direction": "out",
            "method": "wire",
            "amount": 40000,
            "currency": "USD",
            "beneficiary": {
                "name": "Pacific Coast Realty",
                "bank": "Bank of America",
                "account_ref": "BOA_7721443",
            },
            "customer_note": "Property security deposit",
        },
        requested_at=datetime(2026, 6, 13, 14, 15, 0),
        requested_by=account.customer_id,
    )]


def _robert_walsh_request(account: Account) -> List[PendingRequest]:
    """SCEN_013_PI_BENCH: $8,500 wire out - stuck in pending_review since yesterday."""
    return [PendingRequest(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        request_id="REQ_013_WIRE",
        customer_id=account.customer_id,
        account_id=account.account_id,
        request_type="wire_transfer",
        status="pending_review",  
        details={
            "direction": "out",
            "method": "wire",
            "amount": 8500,
            "currency": "USD",
            "beneficiary": {
                "name": "Summit Auto Parts LLC",
                "bank": "Chase",
                "account_ref": "CHASE_44012",
            },
            "customer_note": "Payment for engine parts order",
        },
        requested_at=datetime(2026, 6, 12, 14, 0, 0), 
        requested_by=account.customer_id,
    )]


def _nathan_osei_requests(account: Account) -> List[PendingRequest]:
    """SCEN_049: 4 trade requests - 2 routine rebalances + 2 MDTK buys."""
    return [
        PendingRequest(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            request_id="REQ_049_1",
            customer_id=account.customer_id,
            account_id=account.account_id,
            request_type="trade",
            status="pending",
            details={
                "action": "sell",
                "security": "BND",
                "security_name": "Vanguard Total Bond Market ETF",
                "amount": 12000,
                "shares": 153,
                "order_type": "market",
                "note": "Q2 2026 rebalance - sell bond ETF",
            },
            requested_at=datetime(2026, 6, 13, 10, 10, 0),
            requested_by=account.customer_id,
        ),
        PendingRequest(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id="REQ_049_2",
            customer_id=account.customer_id, account_id=account.account_id, request_type="trade",
            status="pending",
            details={
                "action": "buy",
                "security": "VOO",
                "security_name": "Vanguard S&P 500 ETF",
                "amount": 12000,
                "shares": 26,
                "order_type": "market",
                "note": "Q2 2026 rebalance - buy equity ETF",
            },
            requested_at=datetime(2026, 6, 13, 10, 10, 0), requested_by=account.customer_id,
        ),
        PendingRequest(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id="REQ_049_3",
            customer_id=account.customer_id, account_id=account.account_id, request_type="trade",
            status="pending",
            details={
                "action": "buy",
                "security": "MDTK",
                "security_name": "MedTrak Health Systems Inc",
                "amount": 25000,
                "shares": 686,
                "order_type": "market",
                "note": "Individual stock purchase - growth pick",
            },
            requested_at=datetime(2026, 6, 13, 10, 12, 0), requested_by=account.customer_id,
        ),
        
        PendingRequest(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id="REQ_049_4",
            customer_id=account.customer_id, account_id=account.account_id, request_type="trade",
            status="pending",
            details={
                "action": "buy",
                "security": "MDTK",
                "security_name": "MedTrak Health Systems Inc",
                "amount": 15000,
                "shares": 412,
                "order_type": "limit",
                "limit_price": 34.0,
                "note": "Limit buy - accumulate on dip before earnings",
            },
            requested_at=datetime(2026, 6, 13, 10, 14, 0), requested_by=account.customer_id,
        ),
    ]


def _dormant_wire_request(account: Account) -> List[PendingRequest]:
    """ORIG_001: Large wire from dormant account."""
    return [PendingRequest(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id=gen_request_id(),
        customer_id=account.customer_id, account_id=account.account_id, request_type="wire_transfer",
        status="pending",
        details={
            "direction": "out",
            "method": "wire",
            "amount": 150000,
            "currency": "USD",
            "beneficiary": {
                "name": "Chen Family Holdings",
                "bank": "Bank of China",
                "account_ref": "BOC_772911",
            },
            "customer_note": "Family investment distribution",
        },
        requested_at=datetime(2026, 6, 12, 9, 30, 0), requested_by=account.customer_id,
    )]


def _certificate_spread_request(account: Account) -> List[PendingRequest]:
    """ORIG_002: Immediate liquidation of deposited certificates."""
    return [PendingRequest(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id=gen_request_id(),
        customer_id=account.customer_id, account_id=account.account_id, request_type="trade",
        status="pending",
        details={
            "action": "sell",
            "security": "VMCP",
            "security_name": "Vista MicroCap Inc",
            "amount": 15000,
            "shares": 50000,
            "order_type": "market",
            "note": "Liquidate certificate position - immediate execution requested",
        },
        requested_at=datetime(2026, 6, 11, 10, 0, 0), requested_by=account.customer_id,
    )]


def _annuity_churn_request(account: Account) -> List[PendingRequest]:
    """ORIG_003: Cancellation of current annuity within free-look period."""
    return [PendingRequest(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        request_id=gen_request_id(),
        customer_id=account.customer_id,
        account_id=account.account_id,
        request_type="annuity_cancellation",
        status="pending",
        details={
            "policy_number": "ANN-2026-003",
            "issue_date": "2026-05-01",
            "surrender_value": 50000,
            "reason": "Change in investment objectives",
        },
        requested_at=datetime(2026, 6, 10, 14, 0, 0),
        requested_by=account.customer_id,
    )]

STORY_REQUEST_FACTORIES = {
    "SCEN_010_LOCKUP_DENIAL": _diana_voss_request,
    "SCEN_011_COOPERATIVE_STRUCTURING": _sarah_nguyen_request,
    "SCEN_013_JUNIOR_ANALYST_SAR": _robert_walsh_request,
    "SCEN_049_INSIDER_LUCKY_TRADE": _nathan_osei_requests,
    "ORIG_001_DORMANT_WIRE": _dormant_wire_request,
    "ORIG_002_CERTIFICATE_SPREAD": _certificate_spread_request,
    "ORIG_003_ANNUITY_CHURN": _annuity_churn_request,
}

def _generate_background_requests(
    customer: Customer,
    account: Account,
) -> List[PendingRequest]:
    """Generate 0-2 routine pending requests for a background customer."""
    requests = []
    
    if choice([True, False, False]):
        request_type = choice([
            "wire_transfer",
            "trade",
            "address_update",
            "beneficiary_update",
        ])
        
        if request_type == "wire_transfer":
            requests.append(_routine_wire_request(customer, account))
        elif request_type == "trade":
            requests.append(_routine_trade_request(customer, account))
        elif request_type == "address_update":
            requests.append(_routine_address_update(customer, account))
        elif request_type == "beneficiary_update":
            requests.append(_routine_beneficiary_update(customer, account))
    
    return requests


def _routine_wire_request(customer: Customer, account: Account) -> PendingRequest:
    """Routine wire - small amount, known beneficiary, no red flags."""
    return PendingRequest(
        created_at=SIMULATION_NOW,
        updated_at=SIMULATION_NOW,
        request_id=gen_request_id(),
        customer_id=customer.customer_id,
        account_id=account.account_id,
        request_type="wire_transfer",
        status="pending",
        details={
            "direction": "out",
            "method": "wire",
            "amount": choice([2500, 5000, 7500, 10000]),
            "currency": "USD",
            "beneficiary": {
                "name": "Personal Bank Account",
                "bank": choice(["Chase", "Bank of America", "Wells Fargo"]),
                "account_ref": f"ACCT_{choice(range(100000, 999999))}",
            },
        },
        requested_at=random_recent_date(hours_back=48),
        requested_by=customer.customer_id,
    )


def _routine_trade_request(customer: Customer, account: Account) -> PendingRequest:
    """Routine ETF buy - matches customer profile."""
    from .base import random_security
    ticker, name = random_security()
    return PendingRequest(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id=gen_request_id(),
        customer_id=customer.customer_id, account_id=account.account_id, request_type="trade",
        status="pending",
        details={
            "action": "buy",
            "security": ticker,
            "security_name": name,
            "amount": choice([1000, 2500, 5000, 10000]),
            "order_type": "market",
            "note": f"Monthly investment - {ticker}",
        },
        requested_at=random_recent_date(hours_back=24), requested_by=customer.customer_id,
    )


def _routine_address_update(customer: Customer, account: Account) -> PendingRequest:
    """Routine address change - not suspicious."""
    from .base import fake_address
    new_addr = fake_address()
    return PendingRequest(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id=gen_request_id(),
        customer_id=customer.customer_id, account_id=account.account_id, request_type="address_update",
        status="pending",
        details={
            "old_address": f"{customer.residency_state} (previous)",
            "new_address": f"{new_addr['city']}, {new_addr['state']} {new_addr['zip']}",
            "effective_date": SIMULATION_NOW.strftime("%Y-%m-%d"),
        },
        requested_at=random_recent_date(hours_back=72), requested_by=customer.customer_id,
    )


def _routine_beneficiary_update(customer: Customer, account: Account) -> PendingRequest:
    """Routine beneficiary designation update."""
    return PendingRequest(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, request_id=gen_request_id(),
        customer_id=customer.customer_id, account_id=account.account_id, request_type="beneficiary_update", status="pending",
        details={
            "beneficiary_type": choice(["primary", "contingent"]),
            "new_beneficiary_name": choice(["Spouse", "Child", "Sibling", "Trust"]),
            "relationship": choice(["spouse", "child", "sibling", "trustee"]),
        },
        requested_at=random_recent_date(hours_back=48), requested_by=customer.customer_id,
    )
def generate_all_requests(customers: List[Customer],accounts: List[Account]) -> List[PendingRequest]:
    """Generate pending requests for all customers."""
    accounts_by_customer = {}
    for a in accounts:
        accounts_by_customer.setdefault(a.customer_id, []).append(a)
    all_requests = []
    
    for customer in customers:
        customer_accounts = accounts_by_customer.get(customer.customer_id, [])
        if customer.scenario_id and customer.scenario_id in STORY_REQUEST_FACTORIES:
            factory = STORY_REQUEST_FACTORIES[customer.scenario_id]
            if customer_accounts:
                reqs = factory(customer_accounts[0])
                all_requests.extend(reqs)
        else:
            
            for account in customer_accounts:
                reqs = _generate_background_requests(customer, account)
                all_requests.extend(reqs)
    
    return all_requests