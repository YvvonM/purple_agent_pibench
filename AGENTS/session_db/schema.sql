CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    scenario_id TEXT,
    customer_id TEXT,
    created_at TEXT,
    completed_at TEXT,
    status TEXT DEFAULT 'active',
    final_decision TEXT
);

CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    turn_index INTEGER,
    role TEXT,
    text TEXT,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE reasoning_steps (
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

CREATE TABLE tool_calls (
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

CREATE TABLE research_facts (
    session_id TEXT PRIMARY KEY,
    data_facts TEXT,
    policy_facts TEXT,
    completed_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE decisions (
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