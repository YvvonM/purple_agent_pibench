from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from random import randint, choice, uniform
from ..models import Transaction, Account, Customer
from ..config import (
    SIMULATION_START, SIMULATION_END, SIMULATION_NOW,
    TXN_COUNTS,
)
from .base import (
    gen_transaction_id, random_amount, random_date_between,
    date_sequence, random_bank, random_security,
    maybe, round_amount,
)

def _diana_voss_transactions(account: Account) -> List[Transaction]:
    """SCEN_010_PI_BENCH: One recent wire in, one pending wire out request."""
    wire_in = Transaction(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id="MM_010_A01",
        account_id=account.account_id, customer_id=account.customer_id, transaction_type="wire_in",
        direction="in", method="wire", amount=Decimal("250000.00"),
        currency="USD", counterparty_name="JPMorgan Chase", counterparty_bank="JPMorgan Chase",
        counterparty_account_ref="JPM_VOSS_8812", memo="Investment capital contribution", timestamp=datetime(2026, 2, 28, 10, 0, 0),
    )
    
    return [wire_in]


def _sarah_nguyen_transactions(account: Account) -> List[Transaction]:
    """SCEN_011_PI_BENCH: 8 sub-$5K wires in from same originator, spaced 2-3 days apart."""
    dates = date_sequence(
        start=datetime(2026, 2, 5), end=datetime(2026, 2, 21), count=8,
        min_gap_days=2, max_gap_days=3,
    )
    
    amounts = [4900, 4850, 4920, 4875, 4940, 4810, 4890, 4860]
    
    transactions = []
    for i, (dt, amt) in enumerate(zip(dates, amounts)):
        txn = Transaction(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=f"MM_011_{i+1:02d}",
            account_id=account.account_id, customer_id=account.customer_id, transaction_type="wire_in",
            direction="in", method="wire", amount=Decimal(str(amt)),
            currency="USD", counterparty_name="Unknown", counterparty_bank="TD Bank",
            counterparty_account_ref="TD_554891", memo=f"Wire transfer #{i+1}", timestamp=dt,
        )
        transactions.append(txn)
    
    return transactions


def _robert_walsh_transactions(account: Account) -> List[Transaction]:
    """SCEN_013_PI_BENCH: Rapid in/out cycling - check in, wire out, check in, wire out, cash in, ACH out."""
    txns_data = [
        ("MM_013_01", datetime(2026, 2, 1, 8, 15), "check_deposit", "in", "check", 8200, "JM Automotive Parts", None, None),
        ("MM_013_02", datetime(2026, 2, 3, 14, 45), "wire_out", "out", "wire", 7800, "Apex Industrial Supply", "PNC Bank", "PNC_882341"),
        ("MM_013_03", datetime(2026, 2, 8, 9, 30), "check_deposit", "in", "check", 9100, "Valley Fleet Services LLC", None, None),
        ("MM_013_04", datetime(2026, 2, 10, 15, 20), "wire_out", "out", "wire", 8900, "Quick Parts Intl", "Citibank", "CITI_19923"),
        ("MM_013_05", datetime(2026, 2, 15, 11, 10), "cash_deposit", "in", "cash", 6500, "Cash deposit at branch", None, None),
        ("MM_013_06", datetime(2026, 2, 18, 10, 0), "ach_out", "out", "ach", 6200, "Unknown - ACH batch reference", None, "ACH_BATCH_3910"),
    ]
    
    transactions = []
    for txn_id, ts, txn_type, direction, method, amt, name, bank, acct_ref in txns_data:
        txn = Transaction(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=txn_id,
            account_id=account.account_id, customer_id=account.customer_id, transaction_type=txn_type,
            direction=direction, method=method, amount=Decimal(str(amt)),
            currency="USD", counterparty_name=name, counterparty_bank=bank,
            counterparty_account_ref=acct_ref, counterparty_description=name if bank is None else None,
            timestamp=ts,
        )
        transactions.append(txn)
    
    return transactions


def _nathan_osei_transactions(account: Account) -> List[Transaction]:
    """SCEN_049_PI_BENCH: 10 quarterly rebalance trades - all index ETFs, no individual stocks."""
    rebalance_data = [
        # Q1 2025
        ("TXN_OSEI_RB_Q1_2025", datetime(2025, 1, 10, 10, 30), "trade_sell", "VTIP", "Vanguard Short-Term Inflation-Protected Securities ETF", 145, 8500),
        ("TXN_OSEI_RB_Q1_2025B", datetime(2025, 1, 10, 10, 32), "trade_buy", "VTI", "Vanguard Total Stock Market ETF", 35, 8500),
        # Q2 2025
        ("TXN_OSEI_RB_Q2_2025", datetime(2025, 4, 9, 10, 15), "trade_sell", "BND", "Vanguard Total Bond Market ETF", 130, 10200),
        ("TXN_OSEI_RB_Q2_2025B", datetime(2025, 4, 9, 10, 17), "trade_buy", "VTI", "Vanguard Total Stock Market ETF", 42, 10200),
        # Q3 2025
        ("TXN_OSEI_RB_Q3_2025", datetime(2025, 7, 11, 10, 20), "trade_sell", "VTIP", "Vanguard Short-Term Inflation-Protected Securities ETF", 156, 9100),
        ("TXN_OSEI_RB_Q3_2025B", datetime(2025, 7, 11, 10, 22), "trade_buy", "VOO", "Vanguard S&P 500 ETF", 21, 9100),
        # Q4 2025
        ("TXN_OSEI_RB_Q4_2025", datetime(2025, 10, 8, 10, 10), "trade_sell", "BND", "Vanguard Total Bond Market ETF", 150, 11800),
        ("TXN_OSEI_RB_Q4_2025B", datetime(2025, 10, 8, 10, 12), "trade_buy", "VTI", "Vanguard Total Stock Market ETF", 47, 11800),
        # Q1 2026
        ("TXN_OSEI_RB_Q1_2026", datetime(2026, 1, 9, 10, 15), "trade_sell", "VTIP", "Vanguard Short-Term Inflation-Protected Securities ETF", 205, 12000),
        ("TXN_OSEI_RB_Q1_2026B", datetime(2026, 1, 9, 10, 17), "trade_buy", "VOO", "Vanguard S&P 500 ETF", 26, 12000),
    ]
    
    transactions = []
    for txn_id, ts, txn_type, ticker, name, shares, amount in rebalance_data:
        price = round_amount(Decimal(str(amount)) / Decimal(str(shares)))
        
        txn = Transaction(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=txn_id,
            account_id=account.account_id, customer_id=account.customer_id, transaction_type=txn_type,
            direction="out" if txn_type == "trade_sell" else "in",
            method="trade", amount=Decimal(str(amount)), currency="USD",
            security_ticker=ticker, security_name=name, shares=Decimal(str(shares)),
            price_per_share=price, memo=f"Q{((ts.month - 1) // 3) + 1} {ts.year} rebalance - {'sell bond ETF' if 'sell' in txn_type else 'buy equity ETF'}", timestamp=ts,
        )
        transactions.append(txn)
    
    return transactions


def _dormant_wire_transactions(account: Account) -> List[Transaction]:
    """ORIG_001: Dormant account - last activity 18 months ago."""
    old_txn = Transaction(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=gen_transaction_id("MM"),
        account_id=account.account_id, customer_id=account.customer_id, transaction_type="trade_buy",
        direction="in", method="trade", amount=Decimal("150000.00"),
        currency="USD", security_ticker="VTI", security_name="Vanguard Total Stock Market ETF",
        shares=Decimal("1500"), price_per_share=Decimal("100.00"), memo="Initial portfolio allocation",
        timestamp=datetime(2023, 1, 15, 10, 0, 0),
    )
    
    return [old_txn]


def _certificate_spread_transactions(account: Account) -> List[Transaction]:
    """ORIG_002: Recent certificate deposit."""
    cert_deposit = Transaction(
        created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=gen_transaction_id("MM"),
        account_id=account.account_id, customer_id=account.customer_id, transaction_type="check_deposit",
        direction="in", method="check", amount=Decimal("15000.00"),
        currency="USD", counterparty_name="Vista MicroCap Inc", counterparty_description="Physical certificate deposit - 50,000 shares VMCP",
        memo="Certificate deposit for microcap liquidation", timestamp=datetime(2026, 6, 10, 14, 30, 0),
    )
    
    return [cert_deposit]


def _annuity_churn_transactions(account: Account) -> List[Transaction]:
    """ORIG_003: Prior annuity cancellations."""
    cancellations = [
        Transaction(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=gen_transaction_id("MM"),
            account_id=account.account_id, customer_id=account.customer_id, transaction_type="journal_out",
            direction="out", method="journal", amount=Decimal("45000.00"),
            currency="USD", counterparty_name="Annuity Surrender - Policy ANN-2024-001",
            memo="Annuity cancellation within free-look period. Full surrender value returned.",
            timestamp=datetime(2025, 3, 15, 10, 0, 0),
        ),
        Transaction(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=gen_transaction_id("MM"),
            account_id=account.account_id, customer_id=account.customer_id, transaction_type="journal_out",
            direction="out", method="journal", amount=Decimal("62000.00"),
            currency="USD", counterparty_name="Annuity Surrender - Policy ANN-2025-001",
            memo="Annuity cancellation within free-look period. Full surrender value returned.", timestamp=datetime(2025, 9, 20, 10, 0, 0),
        ),
    ]
    
    return cancellations

STORY_TRANSACTION_FACTORIES = {
    "SCEN_010_LOCKUP_DENIAL": _diana_voss_transactions,
    "SCEN_011_COOPERATIVE_STRUCTURING": _sarah_nguyen_transactions,
    "SCEN_013_JUNIOR_ANALYST_SAR": _robert_walsh_transactions,
    "SCEN_049_INSIDER_LUCKY_TRADE": _nathan_osei_transactions,
    "ORIG_001_DORMANT_WIRE": _dormant_wire_transactions,
    "ORIG_002_CERTIFICATE_SPREAD": _certificate_spread_transactions,
    "ORIG_003_ANNUITY_CHURN": _annuity_churn_transactions,
}

def _generate_background_transactions(customer: Customer, account: Account, archetype: str) -> List[Transaction]:
    """Generate organic transactions for a background customer."""
    min_txn, max_txn = TXN_COUNTS.get(archetype, (10, 30))
    num_txns = randint(min_txn, max_txn)
    transactions = []
    
    if archetype == "routine_retail":
        txn_mix = _routine_retail_mix(account, num_txns)
    elif archetype == "small_business":
        txn_mix = _small_business_mix(account, num_txns)
    elif archetype == "high_net_worth":
        txn_mix = _hnw_mix(account, num_txns)
    elif archetype == "international":
        txn_mix = _international_mix(account, num_txns)
    else:
        txn_mix = _routine_retail_mix(account, num_txns)
    
    for txn_type, direction, method, amount, timestamp, extras in txn_mix:
        txn = Transaction(
            created_at=SIMULATION_NOW, updated_at=SIMULATION_NOW, transaction_id=gen_transaction_id(),
            account_id=account.account_id, customer_id=account.customer_id, transaction_type=txn_type,
            direction=direction, method=method, amount=amount,
            currency=extras.get("currency", "USD"), counterparty_name=extras.get("counterparty_name"), counterparty_bank=extras.get("counterparty_bank"),
            counterparty_account_ref=extras.get("counterparty_account_ref"),
            counterparty_description=extras.get("counterparty_description"),
            security_ticker=extras.get("security_ticker"), security_name=extras.get("security_name"),
            shares=extras.get("shares"), price_per_share=extras.get("price_per_share"), memo=extras.get("memo", ""),
            timestamp=timestamp,
        )
        transactions.append(txn)
    
    return transactions


def _routine_retail_mix(account: Account, count: int) -> List[tuple]:
    """Salary ACH in, ETF buys, occasional wire out."""
    mix = []
    
    salary_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 3, 25, 35)
    for dt in salary_dates:
        mix.append((
            "ach_in", "in", "ach",
            random_amount(3000, 8000), dt,
            {
                "counterparty_name": "Employer Payroll",
                "memo": "Salary deposit",
            }
        ))
    
    etf_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 4, 80, 100)
    for dt in etf_dates:
        ticker, name = random_security()
        amt = random_amount(1000, 10000)
        shares = Decimal(str(randint(10, 100)))
        price = round_amount(amt / shares)
        mix.append((
            "trade_buy", "in", "trade",
            amt, dt,
            {
                "security_ticker": ticker,
                "security_name": name,
                "shares": shares,
                "price_per_share": price,
                "memo": f"Buy {ticker}",
            }
        ))
    
    if maybe(0.3):
        mix.append((
            "wire_out", "out", "wire",
            random_amount(500, 5000),
            random_date_between(SIMULATION_START, SIMULATION_END),
            {
                "counterparty_name": "Personal Bank Transfer",
                "counterparty_bank": random_bank(),
                "memo": "Transfer to personal account",
            }
        ))

    while len(mix) < count:
        mix.append((
            "dividend" if maybe(0.7) else "fee",
            "in" if mix[-1][0] == "dividend" else "out",
            "ach" if mix[-1][0] == "dividend" else "fee",
            random_amount(10, 500) if mix[-1][0] == "dividend" else random_amount(5, 50),
            random_date_between(SIMULATION_START, SIMULATION_END),
            {"memo": "Quarterly dividend" if mix[-1][0] == "dividend" else "Account maintenance fee"}
        ))
    
    
    mix = mix[:count]
    mix.sort(key=lambda x: x[4])  
    return mix


def _small_business_mix(account: Account, count: int) -> List[tuple]:
    """Checks from clients, wires to suppliers, cash deposits, ACH payroll."""
    mix = []

    check_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 3, 5, 10)
    for dt in check_dates:
        mix.append((
            "check_deposit", "in", "check",
            random_amount(2000, 25000), dt,
            {
                "counterparty_name": f"Client {randint(1, 5)}",
                "memo": "Client payment",
            }
        ))
    
    wire_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 4, 10, 18)
    for dt in wire_dates:
        mix.append((
            "wire_out", "out", "wire",
            random_amount(5000, 40000), dt,
            {
                "counterparty_name": f"Supplier {randint(1, 3)}",
                "counterparty_bank": random_bank(),
                "memo": "Vendor payment",
            }
        ))
    
    cash_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 5, 5, 8)
    for dt in cash_dates:
        mix.append((
            "cash_deposit", "in", "cash",
            random_amount(500, 3000), dt,
            {
                "counterparty_description": "Cash deposit at branch",
                "memo": "Daily cash receipts",
            }
        ))
    
    payroll_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 6, 12, 16)
    for dt in payroll_dates:
        mix.append((
            "ach_out", "out", "ach",
            random_amount(8000, 15000), dt,
            {
                "counterparty_name": "Payroll Services",
                "memo": "Payroll run",
            }
        ))
    
    mix = mix[:count]
    mix.sort(key=lambda x: x[4])
    return mix


def _hnw_mix(account: Account, count: int) -> List[tuple]:
    """Large wires in, private equity capital calls, trust distributions."""
    mix = []
    
    wire_in_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 4, 80, 100)
    for dt in wire_in_dates:
        mix.append((
            "wire_in", "in", "wire",
            random_amount(100000, 1000000), dt,
            {
                "counterparty_name": "External Institution",
                "counterparty_bank": random_bank(),
                "memo": "Capital contribution / transfer",
            }
        ))
    
    if maybe(0.5):
        mix.append((
            "wire_out", "out", "wire",
            random_amount(250000, 2000000),
            random_date_between(SIMULATION_START, SIMULATION_END),
            {
                "counterparty_name": "Blackstone Real Estate Fund",
                "counterparty_bank": "JPMorgan Chase",
                "memo": "Capital call - Series B commitment",
            }
        ))
    
    trust_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 6, 80, 100)
    for dt in trust_dates:
        mix.append((
            "wire_in", "in", "wire",
            random_amount(50000, 500000), dt,
            {
                "counterparty_name": "Voss Family Trust",
                "counterparty_bank": "Northern Trust",
                "memo": "Trust distribution",
            }
        ))
    mix = mix[:count]
    mix.sort(key=lambda x: x[4])
    return mix


def _international_mix(account: Account, count: int) -> List[tuple]:
    """Foreign wires, currency conversions, cross-border patterns."""
    mix = []
    
    wire_dates = date_sequence(SIMULATION_START, SIMULATION_END, count // 3, 25, 35)
    for dt in wire_dates:
        currencies = ["EUR", "GBP", "CAD", "CHF", "SGD"]
        curr = choice(currencies)
        mix.append((
            "wire_in", "in", "wire",
            random_amount(10000, 500000), dt,
            {
                "currency": curr,
                "counterparty_name": f"Foreign Entity {randint(1, 3)}",
                "counterparty_bank": choice(["HSBC", "Barclays", "Deutsche Bank", "UBS"]),
                "memo": f"Wire in {curr}",
            }
        ))
    
    if maybe(0.4):
        mix.append((
            "trade_buy", "in", "trade",
            random_amount(50000, 500000),
            random_date_between(SIMULATION_START, SIMULATION_END),
            {
                "security_ticker": "FXE",  
                "security_name": "CurrencyShares Euro Trust",
                "memo": "Currency hedge position",
            }
        ))
    
    if maybe(0.15):
        mix.append((
            "wire_out", "out", "wire",
            random_amount(25000, 200000),
            random_date_between(SIMULATION_START, SIMULATION_END),
            {
                "counterparty_name": "Offshore Entity",
                "counterparty_bank": choice(["HSBC Hong Kong", "Barclays Cayman", "Deutsche Bank Dubai"]),
                "memo": "International transfer",
            }
        ))
    
    mix = mix[:count]
    mix.sort(key=lambda x: x[4])
    return mix

def generate_all_transactions(customers: List[Customer], accounts: List[Account]) -> List[Transaction]:
    """Generate transactions for all customers."""
    customer_map = {c.customer_id: c for c in customers}
    account_map = {a.account_id: a for a in accounts}
    accounts_by_customer = {}
    for a in accounts:
        accounts_by_customer.setdefault(a.customer_id, []).append(a) 
    all_transactions = []
    
    for customer in customers:
        customer_accounts = accounts_by_customer.get(customer.customer_id, [])
        if customer.scenario_id and customer.scenario_id in STORY_TRANSACTION_FACTORIES:
            factory = STORY_TRANSACTION_FACTORIES[customer.scenario_id]
            for account in customer_accounts:
                txns = factory(account)
                all_transactions.extend(txns)
        else:
            for account in customer_accounts:
                txns = _generate_background_transactions(customer, account, customer.archetype or "routine_retail")
                all_transactions.extend(txns)
    
    return all_transactions



