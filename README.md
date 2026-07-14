# purple_agent_pibench

A comprehensive multi-agent framework for regulatory compliance and financial risk intelligence, combining hybrid retrieval-augmented generation (RAG), text-to-SQL agents, and orchestrated policy/data agents.

## Overview

`purple_agent_pibench` is a production-ready benchmark project that integrates:

- **FINRA_HYBRID_RAG**: Semantic + keyword retrieval with cross-encoder reranking for regulatory documents
- **TEXT_TO_SQL_AGENT**: Natural language to SQL translation for financial compliance databases
- **AGENTS**: Orchestrated multi-agent framework with conversation, data, policy, and manager agents
- **Data_cleaning**: Regulatory document processing, entity extraction, and ontology building

The system is designed to:
- Answer compliance questions with grounded regulatory context
- Execute natural language queries against financial databases
- Orchestrate specialized agents for collaborative decision-making
- Evaluate retrieval and answer quality through benchmark metrics

## Project Structure

```
purple_agent_pibench/
├── README.md                          # This file
├── requirements.txt                   # Project dependencies
├── FINRA_HYBRID_RAG/                 # Regulatory document RAG system
│   ├── README.md                      # Full documentation
│   ├── hybrid_rag.py                  # Main RAG pipeline
│   ├── finra_rag_mcp_server.py       # MCP server interface
│   ├── cypher_rag.py                  # Neo4j graph query engine
│   ├── vector_db_creation.py          # Vector store setup
│   ├── rag_eval.py                    # Evaluation framework
│   ├── prompts.py                     # LLM prompt templates
│   ├── chroma/                        # Vector store (persistent)
│   ├── Data_cleaning/                 # Raw data & evaluation datasets
│   └── requirements.txt               # Module-specific dependencies
│
├── TEXT_TO_SQL_AGENT/                # Natural language SQL agent
│   ├── README.md                      # Full documentation
│   ├── main_mcp.py                    # MCP server entry point
│   ├── text_to_sql_rag.py             # RAG pipeline core
│   ├── text_to_sql_client.py          # Test client
│   ├── db_schema_ingestion.py         # Schema processing
│   ├── sqlite_connection.py           # Database interface
│   ├── prompts.py                     # LLM prompts
│   └── requirements.txt               # Module-specific dependencies
│
├── AGENTS/                            # Multi-agent orchestration
│   ├── README.md                      # Full documentation
│   ├── conversation_agent.py          # Conversation management
│   ├── data_agent.py                  # Database query agent
│   ├── policy_agent.py                # Regulatory policy agent
│   ├── manager_agent.py               # Agent orchestrator
│   ├── mcp_client.py                  # MCP client interface
│   ├── prompt.py                      # Agent prompts
│   ├── session_db/                    # Session memory database
│   └── requirements.txt               # Module-specific dependencies
│
├── Data_cleaning/                     # Regulatory data processing
│   ├── README.md                      # Data pipeline documentation
│   ├── md_json.py                     # Markdown to JSON conversion
│   ├── extraction/                    # Entity and relationship extraction
│   ├── ontology/                      # Ontology building and linking
│   ├── FINRA/                         # FINRA policy source files
│   └── evaluation_dataset/            # Benchmark test cases
│
└── ollama_setup/                      # Local Ollama deployment
    └── docker-compose.yml             # Docker setup for Ollama
```

## Key Components

### 1. FINRA_HYBRID_RAG
A sophisticated hybrid RAG system for regulatory compliance queries:
- **Semantic Retrieval**: BGE embeddings with Chroma vector store
- **Keyword Retrieval**: BM25 for fast keyword matching
- **Cross-Encoder Reranking**: BAAI/bge-reranker-v2-m3 for relevance scoring
- **Graph Integration**: Neo4j-backed Cypher query generation for structured relationships
- **MCP Interface**: Two tools: `query_finra_regulations` and `get_retrieval_context`

**Use case**: Regulatory compliance questions, policy guidance, entity relationship navigation.

### 2. TEXT_TO_SQL_AGENT
A production-ready text-to-SQL system for financial databases:
- **RAG-Powered SQL Generation**: Retrieves schema context, generates valid queries
- **Safety Filtering**: SELECT-only queries, no mutations allowed
- **Hybrid Retrieval**: BM25 + semantic search with cross-encoder reranking
- **MCP Interface**: 5 tools for SQL generation, execution, and result translation
- **Error Recovery**: Graceful handling of invalid queries and missing tables

**Use case**: Financial transaction analysis, compliance reporting, customer data queries.

### 3. AGENTS (Multi-Agent Orchestration)
A collaborative framework with specialized agents:
- **ConversationAgent**: Natural language response generation with context awareness
- **DataAgent**: Bridges user questions to database queries via TEXT_TO_SQL_AGENT
- **PolicyAgent**: Bridges user questions to regulatory guidance via FINRA_HYBRID_RAG
- **ManagerAgent**: Orchestrates the multi-agent workflow, decides task delegation
- **SessionMemory**: Persistent session tracking and reasoning audit trail

**Workflow**:
1. User message → ManagerAgent parses intent
2. Initial data tasks → DataAgent (queries database)
3. Adaptive planning based on findings
4. Policy tasks → PolicyAgent (regulatory guidance)
5. Follow-up data queries as needed
6. Response synthesis → ConversationAgent

### 4. Data_cleaning
Automated regulatory text processing pipeline:
- **Markdown Parsing**: Convert FINRA policy markdown to structured JSON
- **Entity Extraction**: NER + gazetteer matching for regulatory entities
- **Ontology Linking**: Resolve entities against knowledge base
- **Metadata Enrichment**: Add domain labels, entity relationships, confidence scores
- **Output**: Ready-to-embed regulatory documents with rich metadata

## Installation

### Prerequisites
- Python 3.10+
- Neo4j Aura instance (optional, for graph features)
- Groq API key(s) for LLM access
- SQLite database (for TEXT_TO_SQL_AGENT)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YvvonM/purple_agent_pibench.git
cd purple_agent_pibench
```

2. Create a `.env` file:
```ini
# Groq API Keys (primary and rotation keys)
GROQ_API_KEY=your_primary_key
Y_GROQ=your_second_key
J_GROQ=your_third_key

# Neo4j (optional)
NEO4J_URI=neo4j+s://your-instance.neo4jdatabase.com
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# DeepEval (optional, for evaluation)
DEEP_EVAL_API=your_deepeval_api_key
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize vector stores (optional, for production):
```bash
cd FINRA_HYBRID_RAG && python vector_db_creation.py
cd ../TEXT_TO_SQL_AGENT && python db_schema_ingestion.py
```

## Quick Start

### Option 1: Multi-Agent Conversation
Run an interactive multi-agent workflow:

```python
import asyncio
from AGENTS.conversation_agent import Orchestrator

async def main():
    orchestrator = Orchestrator()
    session_id = await orchestrator.start_conversation(
        scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
        customer_id="CUST_DIANA_VOSS"
    )
    
    result = await orchestrator.handle_turn(
        "I need to wire $500,000 to my family trust. Why is my request denied?",
        session_id
    )
    print(result["response"])

asyncio.run(main())
```

### Option 2: Regulatory Queries Only
Query FINRA regulations directly:

```bash
cd FINRA_HYBRID_RAG
python finra_rag_mcp_server.py
```

Then use the MCP interface with your LLM client.

### Option 3: Database Queries Only
Query financial data with natural language:

```bash
cd TEXT_TO_SQL_AGENT
python main_mcp.py
```

Then use tools like `generate_sql`, `execute_sql`, `answer_question`.

## Architecture & Data Flow

```
User Input
    ↓
ManagerAgent (Intent Parsing)
    ↓
    ├→ DataAgent → TEXT_TO_SQL_AGENT → SQLite DB
    ├→ PolicyAgent → FINRA_HYBRID_RAG → Neo4j + Vector Store
    ├→ [Adaptive Planning based on findings]
    ├→ [Follow-up queries if needed]
    ↓
ConversationAgent (Response Synthesis)
    ↓
User Response
```

**SessionMemory** tracks all steps, including:
- User messages
- Reasoning steps (intent, planning, decisions)
- Tool calls (to DATA/POLICY MCPs)
- Final synthesis and response

## Configuration

### API Key Rotation
All agents support automatic key rotation to prevent rate limiting:
```python
rotator = KeyRotator(
    keys=[os.getenv("Y_GROQ"), os.getenv("J_GROQ"), os.getenv("GROQ_API_KEY")],
    questions_per_key=2
)
```

### Retrieval Weights (FINRA_HYBRID_RAG)
Adjust BM25 vs. semantic search balance:
```python
EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.6, 0.4]  # Higher = prefer keyword matching
)
```

### LLM Models
Default: `qwen/qwen3-32b` via Groq
- Change in any agent's `_get_llm()` function
- Consider temperature=0.0 for deterministic output

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `GROQ_API_KEY` | Primary LLM API key | `gsk_...` |
| `Y_GROQ`, `J_GROQ` | Rotation keys | `gsk_...` |
| `NEO4J_URI` | Knowledge graph endpoint | `neo4j+s://xxx.neo4jdatabase.com` |
| `NEO4J_USERNAME` | Graph DB auth | `neo4j` |
| `NEO4J_PASSWORD` | Graph DB auth | `secret` |
| `NEO4J_DATABASE` | Graph DB name | `neo4j` |
| `DEEP_EVAL_API` | Evaluation framework key | `deepeval_...` |

## Testing & Evaluation

### Test Multi-Agent Workflow
```bash
cd AGENTS
python conversation_agent.py  # Runs built-in demo
```

### Test Individual Agents
```bash
python data_agent.py        # DataAgent demo
python policy_agent.py      # PolicyAgent demo
python manager_agent.py     # ManagerAgent demo
```

### Test RAG Systems
```bash
cd FINRA_HYBRID_RAG
python rag_eval.py          # Run evaluation metrics
python test_client.py       # Test MCP client

cd ../TEXT_TO_SQL_AGENT
python text_to_sql_client.py  # Test SQL generation and execution
```

## Performance & Scalability

### Latency Breakdown (Per Query)
- **Data Agent**: 1-3s (SQL generation + execution)
- **Policy Agent**: 5-10s (Cypher generation + graph traversal)
- **ConversationAgent**: 2-5s (LLM synthesis)
- **Total**: ~10-20s per multi-agent turn

### Throughput
- Groq API: ~12,000 tokens/minute
- Typical query: ~3,500 tokens
- Max throughput: ~3-4 queries/minute with key rotation

### Optimization Tips
1. Cache common queries at the SQLite and vector store levels
2. Use API key rotation for distributed deployments
3. Parallelize data + policy agent calls (already in manager_agent.py)
4. Pre-compute Cypher patterns for common policy questions
5. Use streaming for long-form responses

## Troubleshooting

### "MCP Connection Failed"
- Ensure TEXT_TO_SQL_AGENT and FINRA_HYBRID_RAG MCP servers are running
- Check server paths in data_agent.py and policy_agent.py

### "No API Keys Available"
- Verify `.env` file has at least one `*_GROQ` key
- Check key format: `gsk_...`

### "Vector Store Not Found"
- Run `python vector_db_creation.py` in FINRA_HYBRID_RAG folder
- Run `python db_schema_ingestion.py` in TEXT_TO_SQL_AGENT folder

### "Neo4j Connection Error"
- Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in `.env`
- Test with `neo4j_db_connection_test.py`

### "SessionMemory Database Locked"
- Ensure only one process accesses the session DB at a time
- Close any open database connections

## Project Workflow

1. **Data Preparation** (Data_cleaning/)
   - Parse FINRA markdown → JSON
   - Extract entities and relationships
   - Build ontology index

2. **Vector Store Setup** (FINRA_HYBRID_RAG/)
   - Chunk regulatory documents
   - Embed with BGE
   - Store in Chroma with metadata

3. **SQL Schema Ingestion** (TEXT_TO_SQL_AGENT/)
   - Convert database schema to documents
   - Embed schema descriptions
   - Store in Chroma for schema retrieval

4. **Agent Deployment** (AGENTS/)
   - Start MCP servers for both RAG systems
   - Initialize SessionMemory
   - Deploy Orchestrator for multi-agent conversations

5. **Evaluation** (Each module)
   - Run evaluation scripts
   - Collect metrics (precision, recall, faithfulness)
   - Iterate on prompts and retrieval weights

## Use Cases

### Compliance Reporting
```
User: "Show me all customers with critical AML alerts in the last 7 days"
→ DataAgent queries customer alerts
→ ConversationAgent summarizes results
```

### Policy-Driven Decisions
```
User: "Why was my wire transfer request denied?"
→ ManagerAgent parses intent
→ PolicyAgent retrieves lock-up period rules
→ DataAgent checks account status
→ ConversationAgent synthesizes response with regulatory justification
```

### Multi-Hop Reasoning
```
User: "What are the SAR filing deadlines for transactions over $10,000?"
→ PolicyAgent retrieves SAR requirements
→ DataAgent finds relevant transactions
→ ManagerAgent adapts plan based on findings
→ ConversationAgent provides actionable guidance
```

## Future Enhancements

- [ ] Streaming responses for long-form answers
- [ ] Multi-database support (PostgreSQL, MySQL)
- [ ] GraphRAG integration for complex relationships
- [ ] Query caching layer with TTL
- [ ] Fine-tuned retriever models for compliance domain
- [ ] A/B testing framework for agent strategies
- [ ] Multilingual regulatory document support
- [ ] Real-time regulatory change tracking
- [ ] Audit trail export (compliance logging)

## Dependencies

Core dependencies:
- `langchain` - Agent orchestration and prompt management
- `langchain-groq` - Groq LLM integration
- `chromadb` - Vector store
- `neo4j` - Knowledge graph
- `sentence-transformers` - Embeddings (BGE)
- `rank_bm25` - Keyword retrieval
- `deepeval` - Evaluation metrics
- `python-dotenv` - Environment configuration
- `pytest` - Testing framework

See `requirements.txt` for full list with versions.

## License

Part of the purple_agent_pibench project. Regulatory and compliance-specific.

## Support

For issues, feature requests, or questions:
1. Check module-specific READMEs (FINRA_HYBRID_RAG/, TEXT_TO_SQL_AGENT/, AGENTS/)
2. Review example scripts in each module
3. Run test clients to validate setup
4. Check GitHub issues for known problems

---

**Last Updated**: 2026
**Python Version**: 3.10+
**Status**: Production-Ready with Benchmarks
