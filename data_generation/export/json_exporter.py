import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Any

CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent 
DEFAULT_OUTPUT_DIR = CURRENT_DIR.parent / "db_data"

class DataEncoder(json.JSONEncoder):
    """Handle datetime and Decimal for JSON output."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def _dataclass_to_dict(obj: Any) -> dict:
    """Convert a dataclass instance to a plain dict."""
    result = {}
    for key, value in obj.__dict__.items():
        if key.startswith("_"):
            continue
        result[key] = value
    return result



def export_to_json(
    customers: List[Any],
    accounts: List[Any],
    transactions: List[Any],
    requests: List[Any],
    alerts: List[Any],
    cases: List[Any],
    securities: List[Any],
    events: List[Any],
    decisions: List[Any] = None,
    employees: List[Any] = None,
) -> None:
    """Export all data to JSON files in the given directory."""
    output_path = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    output_path.mkdir(parents=True, exist_ok=True)
    
    datasets = {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "pending_requests": requests,
        "alerts": alerts,
        "cases": cases,
        "securities": securities,
        "account_events": events,
    }
    
    if decisions:
        datasets["compliance_decisions"] = decisions
    if employees:
        datasets["employees"] = employees
    
    for name, data in datasets.items():
        filepath = output_path / f"{name}.json"
        records = [_dataclass_to_dict(item) for item in data]
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, cls=DataEncoder, indent=2)
        
        print(f"Exported {len(records)} records to {filepath}")


def export_single_file(
    output_path: str,
    customers: List[Any],
    accounts: List[Any],
    transactions: List[Any],
    requests: List[Any],
    alerts: List[Any],
    cases: List[Any],
    securities: List[Any],
    events: List[Any],
    decisions: List[Any] = None,
    employees: List[Any] = None,
) -> None:
    """Export all data to a single combined JSON file."""
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
        },
        "customers": [_dataclass_to_dict(c) for c in customers],
        "accounts": [_dataclass_to_dict(a) for a in accounts],
        "transactions": [_dataclass_to_dict(t) for t in transactions],
        "pending_requests": [_dataclass_to_dict(r) for r in requests],
        "alerts": [_dataclass_to_dict(a) for a in alerts],
        "cases": [_dataclass_to_dict(c) for c in cases],
        "securities": [_dataclass_to_dict(s) for s in securities],
        "account_events": [_dataclass_to_dict(e) for e in events],
    }
    
    if decisions:
        output["compliance_decisions"] = [_dataclass_to_dict(d) for d in decisions]
    if employees:
        output["employees"] = [_dataclass_to_dict(e) for e in employees]
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, cls=DataEncoder, indent=2)
    
    print(f"Exported combined dataset to {output_path}")