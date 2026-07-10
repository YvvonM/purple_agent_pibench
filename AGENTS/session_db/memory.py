import sqlite3
import json 
import uuid 
from datetime import datetime, timezone
from pathlib import Path 
from typing import Optional, List, Dict, Any

DEFAULT_DB_PATH = Path(__file__).parent / "session_db/sessions.db"

class SessionMemory:
    def __init__(self, db_path: str | Path = None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        self._init_db()
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    scenario_id TEXT,
                    customer_id TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    status TEXT DEFAULT 'active',
                    final_decision TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    turn_index INTEGER,
                    role TEXT,
                    text TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS reasoning_steps (
                    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    turn_index INTEGER,
                    step_number INTEGER,
                    agent_name TEXT,
                    step_type TEXT,
                    description TEXT,
                    input_context TEXT,
                    output_action TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS tool_calls (
                    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    turn_index INTEGER,
                    step_number INTEGER,
                    agent_name TEXT,
                    tool_name TEXT,
                    arguments TEXT,
                    result TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS research_facts (
                    session_id TEXT PRIMARY KEY,
                    data_facts TEXT,
                    policy_facts TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    turn_index INTEGER,
                    decision TEXT,
                    request_id TEXT,
                    rationale TEXT,
                    policy_clauses_cited TEXT,
                    recorded_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
            """
            )
        
    def create_session(self, scenario_id: str = None, customer_id: str = None) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, scenario_id, customer_id, created_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, scenario_id, customer_id, now)
            )

            return session_id

    def complete_session(self, session_id: str, final_decision: str = None):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET status = ?, completed_at = ?, final_decision = ? "
                "WHERE session_id = ?",
                ("completed", now, final_decision, session_id)
            )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
                ).fetchone()
            return dict(row) if row else None

    def log_message(self, session_id: str, turn_index: int, role: str, text: str):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (session_id, turn_index, role, text, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, turn_index, role, text, now)
            )

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY turn_index",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def log_reasoning_steps(self, session_id: str,turn_index: int, step_number: int, agent_name: str,
        step_type: str, description: str, input_context: dict = None, output_action: dict = None):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reasoning_steps "
                "(session_id, turn_index, step_number, agent_name, step_type, "
                " description, input_context, output_action, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, turn_index, step_number, agent_name, step_type,
                 description, json.dumps(input_context or {}),
                 json.dumps(output_action or {}), now)
            )

    def get_reasoning_trace(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM reasoning_steps WHERE session_id = ? "
                "ORDER BY turn_index, step_number",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def log_tool_calls(self, session_id: str, turn_index: int, step_number: int,
        agent_name: str, tool_name: str, arguments: dict, result: dict):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tool_calls "
                "(session_id, turn_index, step_number, agent_name, tool_name, "
                " arguments, result, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, turn_index, step_number, agent_name, tool_name,
                 json.dumps(arguments), json.dumps(result), now)
            )

    def get_tool_calls(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM tool_calls WHERE session_id = ? ORDER BY turn_index, step_number",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    

    


        


