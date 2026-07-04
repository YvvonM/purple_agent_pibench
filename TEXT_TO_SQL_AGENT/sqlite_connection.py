import sqlite3
from pathlib import Path
import re


DB_PATH = Path("/workspaces/purple_agent_pibench/TEXT_TO_SQL_AGENT/data_generation/compliance_data.db")
DB_READONLY_URI = f"file:{DB_PATH}?mode=ro"

_DISALLOWED_KEYWORDS = re.compile(
    r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX)\b',
    re.IGNORECASE,
)

def _is_safe_select(sql: str) -> tuple[bool, str]:
    no_comments = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    no_comments = re.sub(r'/\*.*?\*/', '', no_comments, flags=re.DOTALL)
    body = no_comments.strip().rstrip(';').strip()

    if not body:
        return False, "Empty SQL statement."

    if ';' in body:
        return False, "Multiple SQL statements are not allowed."

    if not re.match(r'^\s*(SELECT|WITH)\b', body, re.IGNORECASE):
        return False, "Only SELECT statements are permitted."

    if _DISALLOWED_KEYWORDS.search(body):
        return False, "Statement contains a disallowed keyword."

    return True, ""

def execute_sql(sql: str) -> dict:
    conn = sqlite3.connect(DB_READONLY_URI, uri=True)
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