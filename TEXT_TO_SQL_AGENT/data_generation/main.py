import argparse
from pathlib import Path
import random
from .config import SIMULATION_NOW
from .models import Employee
from .generators.customers import generate_all_customers
from .generators.transactions import generate_all_transactions
from .generators.requests import generate_all_requests
from .generators.alerts import generate_all_alerts
from .generators.cases import generate_all_cases
from .generators.events import generate_all_events
from .generators.securities import generate_all_securities
from .db.sqlite_builder import build_database
from .export.json_exporter import export_to_json, export_single_file

def _generate_employees() -> list[Employee]:
    """Generate a small set of compliance staff."""
    return [
        Employee(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            employee_id="EMP_001",
            name="Richard Patel",
            role="registered_representative",
            department="Wealth Management",
            tenure_months=84,
            can_grant_ctr_exemption=False,
            escalation_path="EMP_002",
            is_active=True,
        ),
        Employee(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            employee_id="EMP_002",
            name="Maria Chen",
            role="senior_compliance",
            department="Compliance",
            tenure_months=120,
            can_grant_ctr_exemption=True,
            escalation_path="EMP_003",
            is_active=True,
        ),
        Employee(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            employee_id="EMP_003",
            name="David Park",
            role="fraud_specialist",
            department="Investigations",
            tenure_months=96,
            can_grant_ctr_exemption=False,
            escalation_path="EMP_004",
            is_active=True,
        ),
        Employee(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            employee_id="EMP_004",
            name="Lisa Thompson",
            role="compliance_officer",
            department="Compliance",
            tenure_months=156,
            can_grant_ctr_exemption=True,
            escalation_path=None,
            is_active=True,
        ),
        Employee(
            created_at=SIMULATION_NOW,
            updated_at=SIMULATION_NOW,
            employee_id="EMP_005",
            name="James Morrison",
            role="registered_representative",
            department="Private Banking",
            tenure_months=60,
            can_grant_ctr_exemption=False,
            escalation_path="EMP_002",
            is_active=True,
        ),
    ]


def generate_all_data():
    """Run the full generation pipeline in dependency order."""
    print(f"Starting data generation. Simulation date: {SIMULATION_NOW}")
    
    print("Generating customers and accounts...")
    customers, accounts = generate_all_customers()
    print(f"-> {len(customers)} customers, {len(accounts)} accounts")
    
    print("Generating transactions...")
    transactions = generate_all_transactions(customers, accounts)
    print(f"-> {len(transactions)} transactions")
    
    print("Generating pending requests...")
    requests = generate_all_requests(customers, accounts)
    print(f"-> {len(requests)} requests")
    
    print("Generating alerts...")
    alerts = generate_all_alerts(customers, accounts, requests)
    print(f"-> {len(alerts)} alerts")
    
    print("Generating cases...")
    cases = generate_all_cases(customers, accounts, alerts)
    print(f" -> {len(cases)} cases")
    
    print("Generating account events...")
    events = generate_all_events(customers, accounts)
    print(f"-> {len(events)} events")
    
    print("Generating securities master...")
    securities = generate_all_securities()
    print(f"-> {len(securities)} securities")
    
    print("Generating employees...")
    employees = _generate_employees()
    print(f"-> {len(employees)} employees")
    decisions = []
    
    return {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "requests": requests,
        "alerts": alerts,
        "cases": cases,
        "events": events,
        "securities": securities,
        "employees": employees,
        "decisions": decisions,
    }


def export_data(data: dict, output_dir: str, db_path: str) -> None:
    """Export to SQLite and JSON."""
    print(f"\nExporting to SQLite: {db_path}")
    build_database(
        db_path=db_path,
        customers=data["customers"],
        accounts=data["accounts"],
        transactions=data["transactions"],
        requests=data["requests"],
        alerts=data["alerts"],
        cases=data["cases"],
        securities=data["securities"],
        events=data["events"],
        decisions=data["decisions"],
        employees=data["employees"],
    )
    print("SQLite complete")
    
    print(f"\nExporting to JSON: {output_dir}")
    export_to_json(
        output_dir=output_dir,
        customers=data["customers"],
        accounts=data["accounts"],
        transactions=data["transactions"],
        requests=data["requests"],
        alerts=data["alerts"],
        cases=data["cases"],
        securities=data["securities"],
        events=data["events"],
        decisions=data["decisions"],
        employees=data["employees"],
    )
    print("JSON complete")
    combined_path = Path(output_dir) / "combined_dataset.json"
    export_single_file(
        output_path=str(combined_path),
        customers=data["customers"],
        accounts=data["accounts"],
        transactions=data["transactions"],
        requests=data["requests"],
        alerts=data["alerts"],
        cases=data["cases"],
        securities=data["securities"],
        events=data["events"],
        decisions=data["decisions"],
        employees=data["employees"],
    )

def main():
    parser = argparse.ArgumentParser(description="Generate compliance demo data")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for JSON output (default: auto-resolved db_data)",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path for SQLite DB (default: auto-resolved compliance_data.db)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    data = generate_all_data()
    
    current_file = Path(__file__).resolve()
    current_dir = current_file.parent
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = current_dir / "db_data"
    
    if args.db_path:
        db_path = args.db_path
    else:
        db_path = current_dir / "compliance_data.db"
    
    export_data(data, str(output_dir), str(db_path))
    
    print(f"\nDone.Files generated:")
    print(f"SQLite:{db_path}")
    print(f"JSON:{output_dir}")


if __name__ == "__main__":
    main()