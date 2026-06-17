import sqlite3 
import json 
from typing import List, Dict, Any
from decimal import Decimal 
from pathlib import Path 
from datetime import datetime 
from ..models import (
    Customer, Account, Transaction, PendingRequest,
    Alert, Case, Security, AccountEvent, ComplianceDecision, Employee,
)


def _to_sqlite(value: Any) -> Any:
    """Convert Python types to SQLite-compatible types."""
    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (List, Dict)):
        return json.dumps(value)

    return value


SCHEMA = """
CREATE TABLE IF NOT EXISTS customers(
    customer_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    date_of_birth TEXT,
    email TEXT,
    phone TEXT,
    residency_state TEXT,
    tier TEXT DEFAULT 'standard',
    kyc_status TEXT DEFAULT 'pending',
    risk_rating TEXT DEFAULT 'medium',
    pep_flag INTEGER DEFAULT 0,
    pep_description TEXT,
    employment_employer TEXT,
    employment_title TEXT,
    employment_salary_range TEXT,
    investment_profile_risk_tolerance TEXT,
    investment_profile_objective TEXT,
    investment_profile_strategy TEXT,
    investment_profile_stated_approach TEXT,
    assigned_banker_id TEXT,
    assigned_banker_name TEXT,
    compliance_notes TEXT DEFAULT '',
    archetype TEXT,
    scenario_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1
    );

CREATE TABLE IF NOT EXISTS accounts(
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    balance_usd REAL DEFAULT 0.0,
    available_balance_usd REAL DEFAULT 0.0,
    holds TEXT DEFAULT '[]',
    lock_up_period_start TEXT,
    lock_up_period_end TEXT,
    lock_up_penalty_description TEXT,
    compliance_flags TEXT DEFAULT '[]',
    investigation_hold INTEGER DEFAULT 0,
    account_opened_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    method TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    counterparty_name TEXT,
    counterparty_bank TEXT,
    counterparty_account_ref TEXT,
    counterparty_description TEXT,
    security_ticker TEXT,
    security_name TEXT,
    shares REAL,
    price_per_share REAL,
    memo TEXT,
    timestamp TEXT NOT NULL,
    fulfilled_request_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS pending_requests (
    request_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    request_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    details TEXT DEFAULT '{}',
    requested_at TEXT NOT NULL,
    requested_by TEXT,
    hold_reason TEXT,
    hold_expiry TEXT,
    decision TEXT,
    decision_recorded_at TEXT,
    decision_rationale TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    description TEXT DEFAULT '',
    linked_transaction_ids TEXT DEFAULT '[]',
    linked_request_ids TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    dismissed_at TEXT,
    dismissed_by TEXT,
    dismissed_reason TEXT,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    summary TEXT DEFAULT '',
    linked_alert_ids TEXT DEFAULT '[]',
    linked_account_ids TEXT DEFAULT '[]',
    linked_transaction_ids TEXT DEFAULT '[]',
    assigned_to TEXT,
    created_at TEXT NOT NULL,
    closed_at TEXT,
    closed_reason TEXT,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS securities (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    exchange TEXT,
    sector TEXT,
    market_cap_usd REAL,
    current_price REAL,
    avg_daily_volume INTEGER,
    upcoming_events TEXT DEFAULT '[]',
    insider_roster TEXT DEFAULT '[]',
    recent_price_action_note TEXT,
    recent_30_day_change_pct REAL
);
CREATE TABLE IF NOT EXISTS account_events (
    event_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    channel TEXT,
    origin_ip TEXT,
    details TEXT DEFAULT '{}',
    old_value TEXT,
    new_value TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS compliance_decisions (
    decision_id TEXT PRIMARY KEY,
    request_id TEXT,
    customer_id TEXT NOT NULL,
    account_id TEXT,
    decision TEXT NOT NULL,
    rationale TEXT DEFAULT '',
    policy_clauses_cited TEXT DEFAULT '[]',
    transactions_inspected TEXT DEFAULT '[]',
    alerts_considered TEXT DEFAULT '[]',
    decided_by TEXT DEFAULT 'agent',
    analyst_id TEXT,
    recorded_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    tenure_months INTEGER DEFAULT 0,
    can_grant_ctr_exemption INTEGER DEFAULT 0,
    escalation_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',
    deleted_at TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_requests_account ON pending_requests(account_id);
CREATE INDEX IF NOT EXISTS idx_requests_customer ON pending_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_alerts_account ON alerts(account_id);
CREATE INDEX IF NOT EXISTS idx_alerts_customer ON alerts(customer_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_cases_customer ON cases(customer_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_events_account ON account_events(account_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON account_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_decisions_customer ON compliance_decisions(customer_id);
"""
def _insert_customer(cursor: sqlite3.Cursor, customer: Customer) -> None:
    cursor.execute("""
        INSERT INTO customers VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """,(
        customer.customer_id,
        customer.display_name,
        _to_sqlite(customer.date_of_birth),
        customer.email,
        customer.phone,
        customer.residency_state,
        customer.tier,
        customer.kyc_status,
        customer.risk_rating,
        customer.pep_flag,
        customer.pep_description,
        customer.employment_employer,
        customer.employment_title,
        customer.employment_salary_range,
        customer.investment_profile_risk_tolerance,
        customer.investment_profile_objective,
        customer.investment_profile_strategy,
        customer.investment_profile_stated_approach,
        customer.assigned_banker_id,
        customer.assigned_banker_name,
        customer.compliance_notes,
        customer.archetype,
        customer.scenario_id,
        _to_sqlite(customer.created_at),
        _to_sqlite(customer.updated_at),
        customer.created_by,
        customer.updated_by,
        _to_sqlite(customer.deleted_at),
        customer.is_active,
    ))

def _insert_account(cursor: sqlite3.Cursor, account: Account) -> None:
    cursor.execute("""
        INSERT INTO accounts VALUES (
             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        account.account_id,
        account.customer_id,
        account.account_type,
        account.status,
        _to_sqlite(account.balance_usd),
        _to_sqlite(account.available_balance_usd),
        _to_sqlite(account.holds),
        _to_sqlite(account.lock_up_period_start),
        _to_sqlite(account.lock_up_period_end),
        account.lock_up_penalty_description,
        _to_sqlite(account.compliance_flags),
        account.investigation_hold,
        _to_sqlite(account.account_opened_date),
        _to_sqlite(account.created_at),
        _to_sqlite(account.updated_at),
        account.created_by,
        account.updated_by,
        _to_sqlite(account.deleted_at),
        account.is_active,
    )) 

def _insert_transaction(cursor: sqlite3.Cursor, txn: Transaction) -> None:
    cursor.execute("""
        INSERT INTO transactions VALUES (
             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        txn.transaction_id,
        txn.account_id,
        txn.customer_id,
        txn.transaction_type,
        txn.direction,
        txn.method,
        _to_sqlite(txn.amount),
        txn.currency,
        txn.counterparty_name,
        txn.counterparty_bank,
        txn.counterparty_account_ref,
        txn.counterparty_description,
        txn.security_ticker,
        txn.security_name,
        _to_sqlite(txn.shares),
        _to_sqlite(txn.price_per_share),
        txn.memo,
        _to_sqlite(txn.timestamp),
        txn.fulfilled_request_id,
        _to_sqlite(txn.created_at),
        _to_sqlite(txn.updated_at),
        txn.created_by,
        txn.updated_by,
        _to_sqlite(txn.deleted_at),
        txn.is_active,
    ))

def _insert_request(cursor: sqlite3.Cursor, req: PendingRequest) -> None:
    cursor.execute("""
        INSERT INTO pending_requests VALUES (
           ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        req.request_id,
        req.customer_id,
        req.account_id,
        req.request_type,
        req.status,
        _to_sqlite(req.details),
        _to_sqlite(req.requested_at),
        req.requested_by,
        req.hold_reason,
        _to_sqlite(req.hold_expiry),
        req.decision,
        _to_sqlite(req.decision_recorded_at),
        req.decision_rationale,
        _to_sqlite(req.created_at),
        _to_sqlite(req.updated_at),
        req.created_by,
        req.updated_by,
        _to_sqlite(req.deleted_at),
        req.is_active,))

def _insert_alert(cursor: sqlite3.Cursor, alert: Alert) -> None:
    cursor.execute("""
        INSERT INTO alerts VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        alert.alert_id,
        alert.account_id,
        alert.customer_id,
        alert.category,
        alert.severity,
        alert.status,
        alert.description,
        _to_sqlite(alert.linked_transaction_ids),
        _to_sqlite(alert.linked_request_ids),
        _to_sqlite(alert.created_at),
        _to_sqlite(alert.dismissed_at),
        alert.dismissed_by,
        alert.dismissed_reason,
        _to_sqlite(alert.updated_at),
        alert.created_by,
        alert.updated_by,
        _to_sqlite(alert.deleted_at),
        alert.is_active,))

def _insert_case(cursor: sqlite3.Cursor, case: Case) -> None:
    cursor.execute("""
        INSERT INTO cases VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        case.case_id,
        case.customer_id,
        case.case_type,
        case.status,
        case.summary,
        _to_sqlite(case.linked_alert_ids),
        _to_sqlite(case.linked_account_ids),
        _to_sqlite(case.linked_transaction_ids),
        case.assigned_to,
        _to_sqlite(case.created_at),
        _to_sqlite(case.closed_at),
        case.closed_reason,
        _to_sqlite(case.updated_at),
        case.created_by,
        case.updated_by,
        _to_sqlite(case.deleted_at),
        case.is_active,
    ))

def _insert_security(cursor: sqlite3.Cursor, sec: Security) -> None:
    cursor.execute("""
        INSERT INTO securities VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        sec.ticker,
        sec.name,
        sec.exchange,
        sec.sector,
        _to_sqlite(sec.market_cap_usd),
        _to_sqlite(sec.current_price),
        sec.avg_daily_volume,
        _to_sqlite(sec.upcoming_events),
        _to_sqlite(sec.insider_roster),
        sec.recent_price_action_note,
        sec.recent_30_day_change_pct,
    ))

def _insert_event(cursor: sqlite3.Cursor, event: AccountEvent) -> None:
    cursor.execute("""
        INSERT INTO account_events VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        event.event_id,
        event.account_id,
        event.customer_id,
        event.event_type,
        _to_sqlite(event.timestamp),
        event.channel,
        event.origin_ip,
        _to_sqlite(event.details),
        event.old_value,
        event.new_value,
        _to_sqlite(event.created_at),
        _to_sqlite(event.updated_at),
        event.created_by,
        event.updated_by,
        _to_sqlite(event.deleted_at),
        event.is_active,
    ))

def _insert_decision(cursor: sqlite3.Cursor, decision: ComplianceDecision) -> None:
    cursor.execute("""
        INSERT INTO compliance_decisions VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, (
        decision.decision_id,
        decision.request_id,
        decision.customer_id,
        decision.account_id,
        decision.decision,
        decision.rationale,
        _to_sqlite(decision.policy_clauses_cited),
        _to_sqlite(decision.transactions_inspected),
        _to_sqlite(decision.alerts_considered),
        decision.decided_by,
        decision.analyst_id,
        _to_sqlite(decision.recorded_at),
        _to_sqlite(decision.created_at),
        _to_sqlite(decision.updated_at),
        decision.created_by,
        decision.updated_by,
        _to_sqlite(decision.deleted_at),
        decision.is_active,
    ))

def _insert_employee(cursor: sqlite3.Cursor, emp: Employee) -> None:
    cursor.execute("""
        INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        emp.employee_id,
        emp.name,
        emp.role,
        emp.department,
        emp.tenure_months,
        emp.can_grant_ctr_exemption,
        emp.escalation_path,
        emp.is_active,
        _to_sqlite(emp.created_at),
        _to_sqlite(emp.updated_at),
        emp.created_by,
        emp.updated_by,
        _to_sqlite(emp.deleted_at),
    ))

def build_database(db_path: str, customers: List[Customer], accounts: List[Account], transactions: List[Transaction], requests: List[PendingRequest], alerts: List[Alert], cases: List[Case], securities: List[Security], events: List[AccountEvent], decisions: List[ComplianceDecision] = None, employees: List[Employee] = None) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.executescript(SCHEMA)
    
    # Insert data
    for customer in customers:
        _insert_customer(cursor, customer)
    
    for account in accounts:
        _insert_account(cursor, account)
    
    for txn in transactions:
        _insert_transaction(cursor, txn)
    
    for req in requests:
        _insert_request(cursor, req)
    
    for alert in alerts:
        _insert_alert(cursor, alert)
    
    for case in cases:
        _insert_case(cursor, case)
    
    for sec in securities:
        _insert_security(cursor, sec)

    for event in events:
        _insert_event(cursor, event)
    
    if decisions:
        for decision in decisions:
            _insert_decision(cursor, decision)
    
    if employees:
        for emp in employees:
            _insert_employee(cursor, emp)
    
    conn.commit()
    conn.close()






