import sqlite3
import json 
import uuid 
from datetime import datetime, timezone
from pathlib import Path 
from typing import Optional, List, Dict, Any
import tempfile
import os

DEFAULT_DB_PATH = Path(__file__).parent / "sessions.db"

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

    def log_reasoning_step(self, session_id: str,turn_index: int, step_number: int, agent_name: str,
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

    def log_tool_call(self, session_id: str, turn_index: int, step_number: int,
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

    def save_research_facts(self, session_id: str, data_facts: Dict[str,Any], policy_facts: Dict[str,Any]):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO research_facts "
                "(session_id, data_facts, policy_facts, completed_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, json.dumps(data_facts), json.dumps(policy_facts), now)
            )

    def get_research_facts(self, session_id:str) -> Optional[Dict[str,Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM research_facts WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            if row:
                return {
                    "data_facts": json.loads(row["data_facts"]),
                    "policy_facts": json.loads(row["policy_facts"]),
                    "completed_at": row["completed_at"],
                }
            return None

    def record_decision(self, session_id: str, turn_index: int, decision: str,
        request_id: str, rationale: str, policy_clauses_cited: List[str] = None ):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO decisions "
                "(session_id, turn_index, decision, request_id, rationale, "
                " policy_clauses_cited, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, turn_index, decision, request_id, rationale,
                 json.dumps(policy_clauses_cited or []), now)
            )

    def get_decisions(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM decisions WHERE session_id = ? ORDER BY recorded_at",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_final_decision(self, session_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM decisions WHERE session_id = ? "
                "ORDER BY recorded_at DESC LIMIT 1",
                (session_id,)
            ).fetchone()
            return dict(row) if row else None


    def get_full_trace(self, session_id:str) -> Dict[str,Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            session = dict(conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
                ).fetchone() or {})
            messages = [dict(r) for r in conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY turn_index",
                (session_id,)
                ).fetchall()]

            reasoning = [dict(r) for r in conn.execute(
                    "SELECT * FROM reasoning_steps WHERE session_id = ? "
                    "ORDER BY turn_index, step_number",
                    (session_id,)
                ).fetchall()]

            tools = [dict(r) for r in conn.execute(
                "SELECT * FROM tool_calls WHERE session_id = ? ORDER BY turn_index, step_number",
                (session_id,)
                ).fetchall()]
            
            research = self.get_research_facts(session_id)
            decisions = self.get_decisions(session_id)
            final = self.get_final_decision(session_id)
            return {
                "session": session,
                "messages": messages,
                "reasoning_trace": reasoning,
                "tool_calls": tools,
                "research_facts": research,
                "decisions": decisions,
                "final_decision": final,
            }

    def print_trace(self, session_id: str):
        trace = self.get_full_trace(session_id)
        print("=" * 70)
        print(f"SESSION: {session_id}")
        print(f"Scenario: {trace['session'].get('scenario_id', 'N/A')}")
        print(f"Status: {trace['session'].get('status', 'N/A')}")
        print(f"Final Decision: {trace['final_decision'].get('decision', 'N/A') if trace['final_decision'] else 'N/A'}")
        print("=" * 70)

        print(f"\n--- Messages ({len(trace['messages'])}) ---")
        for m in trace["messages"]:
            print(f"[{m['role']}] {m['text'][:100]}...")

        print(f"\n--- Reasoning Steps ({len(trace['reasoning_trace'])}) ---")
        for r in trace["reasoning_trace"]:
            print(f"  [{r['agent_name']}/{r['step_type']}] {r['description']}")

        print(f"\n--- Tool Calls ({len(trace['tool_calls'])}) ---")
        for t in trace["tool_calls"]:
            print(f"  [{t['agent_name']}] {t['tool_name']}")

        print(f"\n--- Decisions ({len(trace['decisions'])}) ---")
        for d in trace["decisions"]:
            print(f"  {d['decision']} | {d['request_id']} | {d['rationale'][:60]}...")

def _test():
    db_path = tempfile.mktemp(suffix=".db")
    mem = SessionMemory(db_path)
    sid = mem.create_session(
        scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
        customer_id="CUST_DIANA_VOSS"
    )
    print(f"Created session: {sid}")

    
    mem.log_message(sid, 0, "user", "Hi, I need to wire $500K... request REQ_010_1")
    mem.log_message(sid, 0, "assistant", "Your wire request is denied because...")

    mem.log_reasoning_step(sid, 0, 1, "manager", "plan",
        "Parsed intent: wire_request, REQ_010_1",
        {"raw": "Hi, I need to wire..."},
        {"goal": "wire_request", "request_id": "REQ_010_1"})

    mem.log_reasoning_step(sid, 0, 2, "data_agent", "reframe",
        "Reframed task into NL question",
        {"task": "Get pending request REQ_010_1"},
        {"reframed": "Get all details of pending request REQ_010_1"})
    mem.log_reasoning_step(sid, 0, 3, "data_agent", "observe",
        "Found account ACCT_DIANA_INV_001 in lock-up until 2026-09-01",
        {"sql": "SELECT * FROM accounts..."},
        {"lock_up_end": "2026-09-01", "available_balance": 0.0})

    mem.log_reasoning_step(sid, 0, 4, "manager", "plan",
        "Adaptive plan: check lock-up policy",
        {"data_facts": {"lock_up": True}},
        {"policy_tasks": ["Find rules about lock-up periods"]})

    mem.log_reasoning_step(sid, 0, 5, "manager", "decide",
        "Decision: DENY due to contractual lock-up",
        {"data_facts": {}, "policy_facts": {}},
        {"decision": "DENY", "clauses": ["MFCP-LOCKUP-01"]})

    # Log tool calls
    mem.log_tool_call(sid, 0, 2, "data_agent", "generate_sql",
        {"query": "Get pending request REQ_010_1"},
        {"sql": "SELECT * FROM pending_requests..."})

    mem.log_tool_call(sid, 0, 2, "data_agent", "execute_sql",
        {"sql": "SELECT * FROM pending_requests..."},
        {"results": [{"request_id": "REQ_010_1", "amount": 500000}]})

    
    mem.save_research_facts(sid,
        data_facts={"account": {"lock_up_end": "2026-09-01"}},
        policy_facts={"clauses": [{"id": "MFCP-LOCKUP-01", "text": "No disbursements..."}]})

    
    mem.record_decision(sid, 0, "DENY", "REQ_010_1",
        "Account is in contractual lock-up until 2026-09-01",
        ["MFCP-LOCKUP-01", "MFCP-LOCKUP-02"])

    
    mem.complete_session(sid, "DENY")

    
    print("\n")
    mem.print_trace(sid)

    
    os.unlink(db_path)
    print("\nTest passed. Temp DB cleaned up.")


if __name__ == "__main__":
    _test()

    




                

    


        


