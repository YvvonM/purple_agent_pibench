from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

@dataclass(kw_only=True)
class AuditTable:
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    updated_by: str = "system"
    deleted_at: Optional[datetime] = None
    is_active: bool = True

@dataclass(kw_only=True)
class Customer(AuditTable):
    customer_id: str 
    display_name: str 
    date_of_birth: Optional[datetime] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    residency_state: Optional[str] = None
    tier: str = "standard"
    kyc_status: str = "pending"
    risk_rating: str = "medium"
    pep_flag: bool = False
    pep_description: Optional[str] = None 
    employment_employer: Optional[str] = None
    employment_title: Optional[str] = None
    employment_salary_range: Optional[str] = None
    investment_profile_risk_tolerance: Optional[str] = None
    investment_profile_objective: Optional[str] = None
    investment_profile_strategy: Optional[str] = None
    investment_profile_stated_approach: Optional[str] = None
    assigned_banker_id: Optional[str] = None
    assigned_banker_name: Optional[str] = None
    compliance_notes: str = ""
    archetype: Optional[str] = None      
    scenario_id: Optional[str] = None

@dataclass(kw_only=True)
class Account(AuditTable):
    account_id: str
    customer_id: str 
    account_type: str 
    status: str = "Active"
    balance_usd: Decimal = Decimal("0.00")
    available_balance_usd: Decimal = Decimal("0.00")
    holds: List[Dict[str, Any]] = field(default_factory=list)
    lock_up_period_start: Optional[datetime] = None
    lock_up_period_end: Optional[datetime] = None
    lock_up_penalty_description: Optional[str] = None
    compliance_flags: List[str] = field(default_factory=list)
    investigation_hold: bool = False
    account_opened_date: Optional[datetime] = None

@dataclass(kw_only=True)
class Transaction(AuditTable):
    transaction_id: str
    account_id: str
    customer_id: str
    transaction_type: str 
    direction: str  
    method: str 
    amount: Decimal
    currency: str = "USD"
    # Counterparty (who sent/received)
    counterparty_name: Optional[str] = None
    counterparty_bank: Optional[str] = None
    counterparty_account_ref: Optional[str] = None
    counterparty_description: Optional[str] = None
    # Trade-specific
    security_ticker: Optional[str] = None
    security_name: Optional[str] = None
    shares: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    memo: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    fulfilled_request_id: Optional[str] = None

@dataclass(kw_only=True)
class PendingRequest(AuditTable):
    request_id: str
    customer_id: str
    account_id: str
    request_type: str    
    status: str = "pending" 
    details: Dict[str, Any] = field(default_factory=dict)
    requested_at: datetime = field(default_factory=datetime.now)
    requested_by: str = "" 
    hold_reason: Optional[str] = None
    hold_expiry: Optional[datetime] = None
    decision: Optional[str] = None  
    decision_recorded_at: Optional[datetime] = None
    decision_rationale: Optional[str] = None

@dataclass(kw_only=True)
class Alert(AuditTable):
    alert_id: str
    account_id: str
    customer_id: str
    category: str                   
    severity: str                   
    status: str = "open"            
    description: str = ""
    linked_transaction_ids: List[str] = field(default_factory=list)
    linked_request_ids: List[str] = field(default_factory=list)
    dismissed_at: Optional[datetime] = None
    dismissed_by: Optional[str] = None
    dismissed_reason: Optional[str] = None


@dataclass(kw_only=True)
class Case(AuditTable):
    case_id: str
    customer_id: str
    case_type: str   
    status: str = "open"
    summary: str = ""
    linked_alert_ids: List[str] = field(default_factory=list)
    linked_account_ids: List[str] = field(default_factory=list)
    linked_transaction_ids: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None  
    closed_at: Optional[datetime] = None
    closed_reason: Optional[str] = None

@dataclass(kw_only=True)
class Security(AuditTable):
    ticker: str
    name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    market_cap_usd: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    avg_daily_volume: Optional[int] = None
    upcoming_events: List[Dict[str, Any]] = field(default_factory=list)
    insider_roster: List[Dict[str, Any]] = field(default_factory=list)
    recent_price_action_note: Optional[str] = None
    recent_30_day_change_pct: Optional[float] = None

@dataclass(kw_only=True)
class AccountEvent(AuditTable):
    event_id: str
    account_id: str
    customer_id: str
    event_type: str      
    timestamp: datetime = field(default_factory=datetime.now)
    channel: Optional[str] = None   
    origin_ip: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    old_value: Optional[str] = None
    new_value: Optional[str] = None

@dataclass(kw_only=True)
class ComplianceDecision(AuditTable):
    decision_id: str
    request_id: Optional[str] = None
    customer_id: str
    account_id: Optional[str] = None
    decision: str                   
    rationale: str = ""
    policy_clauses_cited: List[str] = field(default_factory=list)
    transactions_inspected: List[str] = field(default_factory=list)
    alerts_considered: List[str] = field(default_factory=list)
    decided_by: str = "agent"       
    analyst_id: Optional[str] = None
    recorded_at: datetime = field(default_factory=datetime.now)

@dataclass(kw_only=True)
class Employee(AuditTable):
    employee_id: str
    name: str
    role: str 
    department: Optional[str] = None
    tenure_months: int = 0
    can_grant_ctr_exemption: bool = False
    escalation_path: Optional[str] = None  
    is_active: bool = True