# AGENTS (Multi-Agent Orchestration Framework)

A production-ready multi-agent framework for collaborative regulatory compliance and financial risk decision-making. This module orchestrates specialized agents that work together to parse intent, retrieve data, query policy, and synthesize intelligent responses.

## Overview

The AGENTS framework provides:

- **ConversationAgent**: Natural language response synthesis with context awareness
- **DataAgent**: Bridges user intent to database queries via TEXT_TO_SQL_AGENT
- **PolicyAgent**: Bridges user intent to regulatory guidance via FINRA_HYBRID_RAG
- **ManagerAgent**: Orchestrates task delegation and adaptive planning
- **SessionMemory**: Persistent audit trail, reasoning steps, and multi-turn state
- **MCPClient**: Unified interface for calling external MCP servers

The framework is designed for multi-turn conversations where agents collaborate to answer questions with both data-driven and policy-grounded context.

## Architecture

### Agent Workflow

```
User Input
    ↓
ManagerAgent
├─ Intent Parsing (LLM)
├─ Initial Data Tasks
│  ├→ DataAgent
│  │  ├ Task Reframing
│  │  ├ SQL Generation (via TEXT_TO_SQL_AGENT MCP)
│  │  └ Result Processing
├─ Adaptive Planning (based on data findings)
├─ Policy Tasks
│  ├→ PolicyAgent
│  │  ├ Task Reframing
│  │  ├ Policy Query (via FINRA_HYBRID_RAG MCP)
│  │  └ Result Processing
├─ Follow-up Data Tasks (if needed)
└─ Compile Research Summary
    ↓
ConversationAgent
├─ Context Assembly (conversation history + data + policy facts)
├─ LLM Response Synthesis
└─ Response with Regulatory Justification
    ↓
User Response
```

### Session Tracking

Every turn is logged to SessionMemory:
- **Messages**: User and assistant messages per turn
- **Reasoning Steps**: Agent planning, decisions, observations
- **Tool Calls**: MCP calls to DATA and POLICY systems
- **Research Facts**: Aggregated data and policy findings
- **Full Trace**: Complete audit trail for compliance

## Core Components

### 1. ConversationAgent (`conversation_agent.py`)

**Purpose**: Generate natural language responses using context from other agents.

**Key Features**:
- Maintains conversation history (last 6 messages)
- Incorporates data findings and policy context
- Uses Groq LLM (qwen/qwen3-32b) for synthesis
- Logs all reasoning to SessionMemory

**Methods**:
```python
async def respond(
    user_message: str,
    session_id: str,
    turn_index: int,
    data_facts: Optional[List[Dict]] = None,
    policy_facts: Optional[List[Dict]] = None,
    decision: Optional[str] = None,
    rationale: Optional[str] = None
) -> str:
    """
    Generate response with context.
    
    Args:
        user_message: User's question/input
        session_id: Session identifier
        turn_index: Turn number (0-indexed)
        data_facts: Results from DataAgent
        policy_facts: Results from PolicyAgent
        decision: Optional system decision
        rationale: Optional decision justification
    
    Returns:
        Response string with regulatory citations
    """
```

**Example**:
```python
from AGENTS.conversation_agent import ConversationAgent
from AGENTS.session_db.memory import SessionMemory

memory = SessionMemory()
agent = ConversationAgent(memory=memory)

response = await agent.respond(
    user_message="Why was my transfer denied?",
    session_id="sess_123",
    turn_index=1,
    policy_facts=[
        {"task": "lock-up rules", "answer": "Investment accounts have 2-year lock-up period..."}
    ]
)
```

### 2. DataAgent (`data_agent.py`)

**Purpose**: Translate natural language queries into SQL and fetch results from financial database.

**Key Features**:
- Connects to TEXT_TO_SQL_AGENT MCP server
- Reframes data tasks for clarity
- Executes SQL queries safely (SELECT-only)
- Logs all steps to SessionMemory

**Methods**:
```python
async def run(
    data_tasks: List[str],
    memory: SessionMemory = None,
    session_id: str = None,
    turn_index: int = 0
) -> List[Dict[str, Any]]:
    """
    Execute a list of data tasks.
    
    Args:
        data_tasks: List of natural language queries (e.g., "Get customer balance")
        memory: SessionMemory for logging
        session_id: Session identifier
        turn_index: Turn number
    
    Returns:
        List of results with fields: task, reframed_query, sql, results, row_count, error
    """
```

**Output Format**:
```json
{
    "task": "Get pending request REQ_010_1",
    "reframed_query": "Fetch all pending requests for customer CUST_DIANA_VOSS with ID REQ_010_1",
    "sql": "SELECT * FROM pending_requests WHERE request_id='REQ_010_1' AND is_active=1",
    "results": [{"request_id": "REQ_010_1", "amount": 500000, "status": "denied", ...}],
    "row_count": 1,
    "error": null
}
```

**Example**:
```python
from AGENTS.data_agent import DataAgent

agent = DataAgent()
results = await agent.run(
    data_tasks=[
        "Get pending request REQ_010_1",
        "Get account ACCT_DIANA_INV_001 balance"
    ],
    memory=memory,
    session_id="sess_123",
    turn_index=0
)
```

### 3. PolicyAgent (`policy_agent.py`)

**Purpose**: Translate queries into regulatory guidance via FINRA_HYBRID_RAG.

**Key Features**:
- Connects to FINRA_HYBRID_RAG MCP server
- Reframes policy questions for regulatory domain
- Retrieves relevant FINRA rules and guidance
- Logs all steps to SessionMemory

**Methods**:
```python
async def run(
    policy_tasks: List[str],
    memory: SessionMemory = None,
    session_id: str = None,
    turn_index: int = 0
) -> List[Dict[str, Any]]:
    """
    Execute a list of policy tasks.
    
    Args:
        policy_tasks: List of regulatory questions
        memory: SessionMemory for logging
        session_id: Session identifier
        turn_index: Turn number
    
    Returns:
        List of results with fields: task, reframed_query, answer, retrieved_count, sources, error
    """
```

**Output Format**:
```json
{
    "task": "Find rules about wire transfers during lock-up periods",
    "reframed_query": "What are the regulations regarding fund transfers and lock-up period restrictions?",
    "answer": "FINRA Rule 3310 and Treasury Reg 31 CFR 1010.230 establish that investment accounts subject to lock-up agreements cannot transfer funds during the restriction period without explicit waiver or termination...",
    "retrieved_count": 5,
    "sources": [{"text": "FINRA Rule 3310...", ...}],
    "error": null
}
```

**Example**:
```python
from AGENTS.policy_agent import PolicyAgent

agent = PolicyAgent()
results = await agent.run(
    policy_tasks=[
        "Find rules about wire transfers during lock-up periods",
        "Find communication requirements for lock-up denials"
    ],
    memory=memory,
    session_id="sess_123",
    turn_index=0
)
```

### 4. ManagerAgent (`manager_agent.py`)

**Purpose**: Orchestrate the multi-agent workflow with intent parsing and adaptive planning.

**Key Features**:
- Parses user intent and extracts initial data tasks
- Coordinates DataAgent and PolicyAgent execution
- Adapts follow-up plan based on initial findings
- Maintains research summary and decision rationale

**Methods**:
```python
async def run(
    user_message: str,
    session_id: str = None,
    scenario_id: str = None,
    customer_id: str = None,
    turn_index: int = None
) -> Dict[str, Any]:
    """
    Orchestrate multi-agent workflow for a user message.
    
    Args:
        user_message: User's question
        session_id: Existing session ID (if continuing conversation)
        scenario_id: Scenario context (e.g., "SCEN_010_LOCKUP_DENIAL_GROUNDING")
        customer_id: Customer context (e.g., "CUST_DIANA_VOSS")
        turn_index: Turn number (auto-incremented if not provided)
    
    Returns:
        Dict with: user_message, intent, data_facts, policy_facts, session_id
    """
```

**Workflow Stages**:

1. **Intent Parsing**
   - LLM analyzes user message
   - Extracts: goal, initial_data_tasks
   - Output: `{"goal": "...", "initial_data_tasks": ["task1", "task2"]}`

2. **Initial Data Retrieval**
   - Execute initial_data_tasks via DataAgent
   - Collect results with row counts and errors

3. **Adaptive Planning**
   - LLM evaluates initial findings
   - Decides: policy_tasks, follow-up_data_tasks
   - Output: `{"policy_tasks": [...], "followup_data_tasks": [...]}`

4. **Parallel Execution**
   - PolicyAgent and DataAgent run in parallel
   - Collect all findings

5. **Research Summary**
   - Aggregate data and policy facts
   - Save to SessionMemory

**Example**:
```python
from AGENTS.manager_agent import ManagerAgent

manager = ManagerAgent(memory=memory)
result = await manager.run(
    user_message="Why was my wire transfer denied?",
    scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
    customer_id="CUST_DIANA_VOSS"
)

print(f"Session: {result['session_id']}")
print(f"Intent: {result['intent']}")
print(f"Data findings: {len(result['data_facts'])} items")
print(f"Policy findings: {len(result['policy_facts'])} items")
```

### 5. Orchestrator (`conversation_agent.py`)

**Purpose**: High-level orchestration of multi-turn conversations.

**Key Features**:
- Manages session creation and turn indexing
- Delegates to ManagerAgent for research
- Delegates to ConversationAgent for response
- Maintains conversation state

**Methods**:
```python
async def start_conversation(
    scenario_id: str = None,
    customer_id: str = None
) -> str:
    """
    Start a new conversation session.
    
    Returns:
        session_id: Unique session identifier
    """

async def handle_turn(
    user_message: str,
    session_id: str,
    scenario_id: str = None,
    customer_id: str = None
) -> Dict[str, Any]:
    """
    Process one turn in the conversation.
    
    Returns:
        Dict with: session_id, turn_index, response, research
    """
```

**Example**:
```python
from AGENTS.conversation_agent import Orchestrator

orchestrator = Orchestrator(memory=memory)

# Start session
session_id = await orchestrator.start_conversation(
    scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
    customer_id="CUST_DIANA_VOSS"
)

# Turn 1
result1 = await orchestrator.handle_turn(
    "I need to wire $500,000. Why was my request denied?",
    session_id
)
print(f"Response: {result1['response']}")

# Turn 2
result2 = await orchestrator.handle_turn(
    "When can I transfer the funds?",
    session_id
)
```

### 6. SessionMemory (`session_db/memory.py`)

**Purpose**: Persistent session state, reasoning audit trail, and multi-turn management.

**Key Features**:
- Session metadata (scenario_id, customer_id, creation timestamp)
- Message history (user and assistant)
- Reasoning steps (agent planning and decisions)
- Tool calls (to DATA and POLICY systems)
- Research facts (aggregated findings)

**Methods**:
```python
def create_session(
    scenario_id: str = None,
    customer_id: str = None
) -> str:
    """Create a new session and return session_id"""

def log_message(
    session_id: str,
    turn_index: int,
    role: str,  # "user" or "assistant"
    text: str
):
    """Log a message in the conversation"""

def log_reasoning_step(
    session_id: str,
    turn_index: int,
    step_number: int,
    agent_name: str,
    step_type: str,  # "plan", "observe", "decide", "respond"
    description: str,
    input_context: Dict,
    output_action: Dict
):
    """Log an agent's reasoning step"""

def log_tool_call(
    session_id: str,
    turn_index: int,
    step_number: int,
    agent_name: str,
    tool_name: str,
    arguments: Dict,
    result: Dict
):
    """Log a tool call (MCP server interaction)"""

def save_research_facts(
    session_id: str,
    data_facts: Dict,
    policy_facts: Dict
):
    """Save aggregated findings"""

def print_trace(session_id: str):
    """Print full session trace for debugging/audit"""
```

**Database Schema**:
```
sessions:
  - session_id (PK)
  - scenario_id
  - customer_id
  - created_at
  - updated_at

messages:
  - session_id (FK)
  - turn_index
  - role
  - text

reasoning_steps:
  - session_id (FK)
  - turn_index
  - step_number
  - agent_name
  - step_type
  - description
  - input_context (JSON)
  - output_action (JSON)

tool_calls:
  - session_id (FK)
  - turn_index
  - step_number
  - agent_name
  - tool_name
  - arguments (JSON)
  - result (JSON)

research_facts:
  - session_id (FK)
  - data_facts (JSON)
  - policy_facts (JSON)
```

### 7. MCPClient (`mcp_client.py`)

**Purpose**: Unified client for calling external MCP servers (DATA and POLICY systems).

**Key Features**:
- Subprocess management for MCP servers
- JSON-RPC communication via stdin/stdout
- Tool discovery and invocation
- Automatic error handling

**Methods**:
```python
async def connect():
    """Start MCP server subprocess"""

async def close():
    """Stop MCP server and cleanup"""

async def call_tool(
    tool_name: str,
    arguments: Dict
) -> Dict:
    """
    Call a tool on the MCP server.
    
    Returns:
        Dict with: content (list of response objects)
    """

def get_tool_names_and_description() -> str:
    """Get list of available tools"""
```

## Setup & Installation

### Prerequisites
- Python 3.10+
- TEXT_TO_SQL_AGENT and FINRA_HYBRID_RAG modules set up
- Groq API keys configured in `.env`
- SQLite database for financial data
- Neo4j instance (optional, for policy agent)

### Install Dependencies

```bash
cd AGENTS
pip install -r requirements.txt
```

Or install from parent directory:
```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```ini
# Groq API Keys
GROQ_API_KEY=gsk_your_primary_key
Y_GROQ=gsk_your_second_key
J_GROQ=gsk_your_third_key

# Neo4j (for PolicyAgent)
NEO4J_URI=neo4j+s://your-instance.neo4jdatabase.com
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# DeepEval (optional)
DEEP_EVAL_API=your_deepeval_api_key
```

### SessionMemory Database

By default, SessionMemory creates a SQLite database at:
```
AGENTS/session_db/sessions.db
```

No manual setup required — created automatically on first use.

## Usage

### Multi-Turn Conversation (Recommended)

```python
import asyncio
from AGENTS.conversation_agent import Orchestrator

async def main():
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Start conversation
    session_id = await orchestrator.start_conversation(
        scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
        customer_id="CUST_DIANA_VOSS"
    )
    print(f"Session started: {session_id}\n")
    
    # Turn 1: Initial inquiry
    result1 = await orchestrator.handle_turn(
        "I need to wire $500,000 from my investment account to my family trust. The request should already be in the system — REQ_010_1.",
        session_id
    )
    print(f"User: {result1['research']['user_message']}")
    print(f"Assistant: {result1['response']}\n")
    
    # Turn 2: Follow-up
    result2 = await orchestrator.handle_turn(
        "Why was my request denied? Can you explain the lock-up period?",
        session_id
    )
    print(f"User: Follow-up question")
    print(f"Assistant: {result2['response']}\n")
    
    # Turn 3: Another follow-up
    result3 = await orchestrator.handle_turn(
        "When will the lock-up end? Can I schedule the transfer for then?",
        session_id
    )
    print(f"Assistant: {result3['response']}\n")
    
    # Print full trace for audit
    memory = orchestrator.memory
    memory.print_trace(session_id)

asyncio.run(main())
```

### Individual Agent Usage

**DataAgent only**:
```python
from AGENTS.data_agent import DataAgent
from AGENTS.session_db.memory import SessionMemory

async def main():
    memory = SessionMemory()
    session_id = memory.create_session(
        scenario_id="SCEN_010",
        customer_id="CUST_DIANA_VOSS"
    )
    
    agent = DataAgent()
    results = await agent.run(
        data_tasks=[
            "Get pending request REQ_010_1",
            "Get account ACCT_DIANA_INV_001 balance"
        ],
        memory=memory,
        session_id=session_id,
        turn_index=0
    )
    
    for result in results:
        print(f"Task: {result['task']}")
        print(f"Results: {result['row_count']} rows")
```

**PolicyAgent only**:
```python
from AGENTS.policy_agent import PolicyAgent
from AGENTS.session_db.memory import SessionMemory

async def main():
    memory = SessionMemory()
    session_id = memory.create_session(
        scenario_id="SCEN_010",
        customer_id="CUST_DIANA_VOSS"
    )
    
    agent = PolicyAgent()
    results = await agent.run(
        policy_tasks=[
            "Find rules about wire transfers during lock-up periods",
            "Find communication requirements for lock-up denials"
        ],
        memory=memory,
        session_id=session_id,
        turn_index=0
    )
    
    for result in results:
        print(f"Task: {result['task']}")
        print(f"Answer: {result['answer'][:200]}...")
```

### Direct Orchestrator (No Conversation)

```python
from AGENTS.conversation_agent import Orchestrator

async def main():
    orchestrator = Orchestrator()
    
    result = await orchestrator.handle_turn(
        "Show me all pending wire transfer requests over $100,000",
        session_id="existing_session_id"
    )
    
    print(result['response'])
```

## Running Examples

### Demo: Full Multi-Agent Workflow

```bash
cd AGENTS
python conversation_agent.py  # Runs built-in _demo_multi_turn()
```

Output:
```
Started session: sess_123abc...

Turn 0:
User: Hi, I need to wire $500,000 from my investment account...
Assistant: I understand you're looking to make a wire transfer. Let me look into your account and the regulatory constraints...

Turn 1:
User: Why was my request denied? Can you explain the lock-up period?
Assistant: Based on our records, your investment account (ACCT_DIANA_INV_001) is subject to a 2-year lock-up period per FINRA Rule 3310...

Turn 2:
User: When will the lock-up end? Can I schedule the transfer for then?
Assistant: The lock-up period for your account expires on [date]. After that, you can initiate wire transfers...

========================================
FULL TRACE:
[Complete session history with all reasoning steps, tool calls, and decisions]
```

### Demo: DataAgent Only

```bash
python data_agent.py
```

### Demo: PolicyAgent Only

```bash
python policy_agent.py
```

### Demo: ManagerAgent Only

```bash
python manager_agent.py
```

## Project Structure

```
AGENTS/
├── README.md                          # This file
├── conversation_agent.py              # ConversationAgent & Orchestrator
├── data_agent.py                      # DataAgent (queries database)
├── policy_agent.py                    # PolicyAgent (queries regulations)
├── manager_agent.py                   # ManagerAgent (orchestration)
├── mcp_client.py                      # MCP client for external servers
├── prompt.py                          # LLM prompts for all agents
├── session_db/
│   ├── __init__.py
│   ├── memory.py                      # SessionMemory implementation
│   └── sessions.db                    # SQLite database (auto-created)
└── requirements.txt
```

## Prompts

All LLM prompts are centralized in `prompt.py`:

- `CONVERSATION_SYSTEM_PROMPT`: Conversation agent behavior
- `INTENT_PROMPT`: Intent parsing for user messages
- `ADAPTIVE_PROMPT`: Adaptive planning based on findings
- `POLICY_REFRAME_SYSTEM_PROMPT`: Reframing user queries for policy retrieval
- `REFRAME_SYSTEM_PROMPT`: Reframing user queries for data retrieval

Customize these to adjust agent behavior.

## Performance & Scalability

### Typical Latency Per Turn
- Intent parsing: 1-2s (LLM)
- Initial data retrieval: 2-3s (DataAgent)
- Adaptive planning: 1-2s (LLM)
- Policy retrieval: 3-5s (PolicyAgent)
- Follow-up queries: 2-3s (DataAgent, if needed)
- Response synthesis: 2-4s (LLM)
- **Total**: ~12-20s per turn

### Throughput
- Groq API: 12,000 TPM limit
- Typical tokens per turn: 4,000-5,000
- Max throughput: 2-3 turns/minute with key rotation

### Optimization Tips
1. **Parallel execution**: DataAgent and PolicyAgent already run in parallel
2. **Key rotation**: Automatic switching prevents rate limiting
3. **Caching**: SessionMemory can be extended with result caching
4. **Batch processing**: Run multiple sessions in different processes
5. **Prompt optimization**: Shorten prompts to reduce token usage

## Troubleshooting

### Issue: "MCP Connection Failed"
```
Error: Failed to connect to MCP server at ...
```
**Solution**:
1. Ensure TEXT_TO_SQL_AGENT and FINRA_HYBRID_RAG are set up
2. Check server paths in data_agent.py (line 19) and policy_agent.py (line 18)
3. Verify Python paths and dependencies are installed
4. Run servers manually to test: `python TEXT_TO_SQL_AGENT/main_mcp.py`

### Issue: "No API Keys Provided"
```
ValueError: No API keys provided.
```
**Solution**:
1. Verify `.env` file exists in project root
2. Check that at least one `*_GROQ` variable is set
3. Verify format: `GROQ_API_KEY=gsk_...` (not wrapped in quotes)

### Issue: "SessionMemory Database Locked"
```
sqlite3.OperationalError: database is locked
```
**Solution**:
1. Ensure only one process accesses the session DB
2. Close other Python processes using the DB
3. Check file permissions on `sessions.db`

### Issue: "Tool Not Found" in MCP Server
```
Error: Tool 'execute_sql' not found
```
**Solution**:
1. Verify TEXT_TO_SQL_AGENT/main_mcp.py is running
2. Check that server started successfully (no import errors)
3. Call `get_tools()` to list available tools

### Issue: Empty or Incorrect Agent Results
```
DataAgent returns: {"error": "Reframe step returned empty output"}
```
**Solution**:
1. Check Groq API key is valid
2. Review prompts in `prompt.py` for clarity
3. Test LLM directly: check temperature=0.0 for determinism
4. Enable debug logging in agents

## Advanced Configuration

### Custom Prompts

Edit `prompt.py` to customize agent behavior:

```python
INTENT_PROMPT = """
You are an intent parser for compliance scenarios.
Parse the user message and extract:
- goal: The user's primary objective
- initial_data_tasks: List of database queries needed
- scenario_context: Regulatory scenario if applicable

Respond ONLY with valid JSON.
"""
```

### API Key Rotation Strategy

Adjust `questions_per_key` in each agent:

```python
rotator = KeyRotator(
    keys=[...],
    questions_per_key=5  # Use each key for 5 questions before rotating
)
```

### SessionMemory Persistence

Store sessions in a different location:

```python
memory = SessionMemory(db_path="/custom/path/sessions.db")
```

### Async Execution

All agent methods are async. For synchronous code:

```python
import asyncio

result = asyncio.run(orchestrator.handle_turn(...))
```

## Use Cases

### 1. Compliance Decision Support
```
User: "Can I liquidate my tech stocks to fund an acquisition?"
→ Manager parses intent, seeks regulatory guidance
→ PolicyAgent retrieves SEC rules on affiliate transactions
→ DataAgent checks portfolio restrictions
→ Conversation synthesizes regulatory compliance response
```

### 2. Regulatory Investigation
```
User: "What transactions by customer CUST_X_Y triggered SAR filings in Q3?"
→ DataAgent queries suspicious activity reports
→ PolicyAgent retrieves SAR filing thresholds
→ Manager plans follow-up questions on related customers
→ Conversation provides investigation summary
```

### 3. Multi-Hop Reasoning
```
User: "Why was wire transfer request REQ_123 denied and what are my options?"
→ DataAgent retrieves request and account status
→ PolicyAgent finds applicable lock-up rules
→ Manager adapts plan based on findings
→ Conversation explains regulatory basis and alternatives
```

## Integration with LLMs

### Claude Integration
```python
from anthropic import Anthropic
from AGENTS.conversation_agent import Orchestrator

client = Anthropic()
orchestrator = Orchestrator()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[
        {
            "name": "get_compliance_guidance",
            "description": "Get regulatory guidance on compliance questions",
            "input_schema": {...}
        }
    ],
    messages=[
        {"role": "user", "content": "Can I wire transfer funds during a lock-up?"}
    ]
)
```

### Custom Orchestration
```python
# Integrate AGENTS framework into your own system
from AGENTS.manager_agent import ManagerAgent
from AGENTS.conversation_agent import ConversationAgent
from AGENTS.session_db.memory import SessionMemory

memory = SessionMemory()
manager = ManagerAgent(memory=memory)
conversation = ConversationAgent(memory=memory)

# Use as building blocks
```

## Future Enhancements

- [ ] Multi-language support for regulatory documents
- [ ] Streaming responses for long-form synthesis
- [ ] Caching layer for common queries
- [ ] Custom agent roles (compliance officer, trader, investigator)
- [ ] GraphRAG integration for complex relationships
- [ ] Real-time regulatory change tracking
- [ ] Decision logging and audit export
- [ ] A/B testing framework for agent strategies
- [ ] Fine-tuned models for compliance domain

## License

Part of the purple_agent_pibench project.

## Support

For issues:
1. Check SessionMemory trace: `memory.print_trace(session_id)`
2. Review MCP server logs: stdout/stderr from agent processes
3. Test individual agents with demo functions
4. Check parent README and module-specific docs

---

**Last Updated**: 2024
**Framework Status**: Production-Ready
**Python Version**: 3.10+
