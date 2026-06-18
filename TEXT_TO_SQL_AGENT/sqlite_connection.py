import sqlite3
from pathlib import Path
import re


DB_PATH = Path("/workspaces/purple_agent_pibench/TEXT_TO_SQL_AGENT/data_generation/compliance_data.db")

def execute_sql(sql: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return {"sql": sql, "results": results, "row_count": len(results), "error": None}
    except sqlite3.Error as e:
        return {"sql": sql, "results": None, "row_count": 0, "error": str(e)}
    finally:
        conn.close()

def extract_sql(raw: str) -> str:
    """Extract clean SQL from LLM output that may have markdown or explanations."""
    match = re.search(r'```sql\s*(.*?)\s*```', raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Try generic code block
    match = re.search(r'```\s*(.*?)\s*```', raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback: find SELECT statement in text
    match = re.search(r'(SELECT\s+.*?;)', raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Last resort: return raw stripped
    return raw.strip()