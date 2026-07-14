# TEXT_TO_SQL_AGENT

A production-ready Text-to-SQL agent powered by LLMs and Retrieval-Augmented Generation (RAG). This agent translates natural language questions into SQLite queries, executes them safely, and returns results with natural language explanations.

## Overview

The TEXT_TO_SQL_AGENT is designed to bridge the gap between non-technical users and database queries. It uses a hybrid retrieval system combining semantic search, BM25 keyword matching, and cross-encoder reranking to provide relevant database schema context to an LLM, which then generates accurate SQL queries.

### Key Features

- **Natural Language Processing**: Convert plain English questions into valid SQLite queries
- **Hybrid RAG Retrieval**: BM25 + semantic search + cross-encoder reranking for optimal schema retrieval
- **Safety Filtering**: Only SELECT queries are allowed; no data modification operations
- **Error Handling**: Graceful error recovery for invalid tables, malformed SQL, and edge cases
- **MCP Server Integration**: Model Context Protocol (MCP) server for standardized tool interface
- **API Key Rotation**: Automatic key switching for distributed LLM calls

## Architecture

### Core Components

1. **main_mcp.py** - MCP Server Implementation
   - Exposes 5 tools via the Model Context Protocol
   - Handles tool routing and error management
   - Supports both direct SQL execution and natural language queries

2. **text_to_sql_rag.py** - RAG Pipeline
   - Hybrid retriever combining BM25 and semantic search
   - Cross-encoder reranking for top-N relevance
   - LLM-based SQL generation with streaming
   - Result-to-text translation for non-technical stakeholders

3. **db_schema_ingestion.py** - Schema Processing
   - Converts database schema JSON into vector-embedded documents
   - Builds Chroma vector store for similarity search
   - Pre-processes schema with critical metadata (examples, gotchas, relationships)

4. **sqlite_connection.py** - Database Interface
   - Executes SQL queries against SQLite database
   - Safety filtering to prevent non-SELECT operations
   - Connection pooling and error handling

5. **prompts.py** - Prompt Templates
   - SQL generation system prompt with schema context and examples
   - Text translation prompt for results explanation

6. **text_to_sql_client.py** - Test Client
   - Comprehensive test suite demonstrating all tool capabilities
   - Happy path tests, edge cases, and error scenarios

## Available Tools

### 1. `generate_sql`
Generates a SQLite query from a natural language question using the RAG pipeline.

**Input:**
- `query` (string, required): Natural language question

**Output:**
- Raw SQL query with markdown formatting and explanations

**Example:**
```python
result = await session.call_tool(
    "generate_sql",
    {"query": "Show me the 5 most recent transactions for customer CUST_DIANA_VOSS"}
)
```

### 2. `execute_sql`
Executes a SQLite SELECT query (direct SQL or generated from natural language).

**Input:**
- `sql` (string, optional): Raw SQL SELECT statement
- `query` (string, optional): Natural language question (auto-generates SQL)

**Output:**
- JSON results with metadata (row count, execution time)

**Example:**
```python
result = await session.call_tool(
    "execute_sql",
    {"sql": "SELECT COUNT(*) as total FROM transactions"}
)
```

### 3. `sql_to_text`
Translates SQL query results into plain English for non-technical stakeholders.

**Input:**
- `query` (string): Original natural language question
- `sql` (string, optional): The SQL query (auto-generated if not provided)

**Output:**
- 1-2 sentence plain English summary

**Example:**
```python
result = await session.call_tool(
    "sql_to_text",
    {
        "query": "Has customer CUST_DIANA_VOSS had any wire transfers over $10,000?",
        "sql": "SELECT * FROM transactions WHERE ..."
    }
)
```

### 4. `answer_question`
End-to-end pipeline: question → SQL generation → execution → natural language answer.

**Input:**
- `query` (string, required): Natural language question

**Output:**
- JSON object containing:
  - `question`: Original question
  - `sql`: Generated SQL query
  - `results`: Raw database results
  - `text_answer`: Plain English summary

**Example:**
```python
result = await session.call_tool(
    "answer_question",
    {"query": "Has customer CUST_DIANA_VOSS had any wire transfers over $10,000?"}
)
```

### 5. `retrieve_schema_context`
Retrieves relevant database schema documents for inspection or manual query building.

**Input:**
- `query` (string, required): Query to find relevant schema

**Output:**
- Formatted list of top-N schema documents with ranking and section metadata

**Example:**
```python
result = await session.call_tool(
    "retrieve_schema_context",
    {"query": "transactions table schema"}
)
```

## Database Schema

The agent is designed for a **financial compliance database** with the following key conventions:

### Standard Columns (Present in Most Tables)
- `is_active` (INTEGER): 0 = false, 1 = true (default: 1)
- `deleted_at` (ISO datetime): Soft-delete timestamp (NULL = active)
- **Always filter**: `WHERE is_active = 1 AND deleted_at IS NULL`

### Data Type Notes
- **Booleans**: Stored as INTEGER (0 or 1)
- **Timestamps**: ISO text strings; use `date()` or `datetime()` for comparisons
- **JSON columns**: Stored as TEXT; use `json_extract()` for nested queries
- **Money**: Use `available_balance_usd` (not `balance_usd`) for spendable funds

### Key Tables
- **customers**: Customer profiles, KYC status, risk ratings
- **accounts**: Bank accounts, balances, compliance flags
- **transactions**: Wire transfers, deposits, withdrawals
- **alerts**: Compliance alerts, severity levels
- **pending_requests**: Pending wire transfers and other requests

## Setup & Installation

### Prerequisites
- Python 3.10+
- SQLite database at `YOUR_DB_PATH.db`
- Groq API key(s) for LLM access

### Environment Variables
Create a `.env` file with:
```env
GROQ_API_KEY=your_primary_key
Y_GROQ=your_second_key
J_GROQ=your_third_key
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Initialize Database Schema
```bash
python db_schema_ingestion.py
```
This generates:
- Chroma vector store at `FINRA_HYBRID_RAG/chroma`
- Pickle file with schema documents

## Running the Agent

### As an MCP Server
```bash
python main_mcp.py
```
The server listens on stdin/stdout for MCP protocol messages.

### Using the Test Client
```bash
python text_to_sql_client.py
```
Runs comprehensive tests of all tools and edge cases.

### Standalone Usage
```python
import asyncio
from text_to_sql_rag import run_pipeline

result = asyncio.run(run_pipeline("Your natural language question here"))
print(result)
```

## Safety & Validation

### Query Filtering
- **Only SELECT queries** are allowed
- All mutations (INSERT, UPDATE, DELETE, DROP) are rejected
- Invalid table references are caught and reported with user-friendly errors

### Error Handling
- Malformed SQL is caught and logged
- Database connection errors are gracefully recovered
- Missing tables/columns trigger informative error messages

## RAG Pipeline Details

### Retrieval Strategy
1. **BM25 Retriever** (60% weight): Keyword matching on schema documents
2. **Semantic Retriever** (40% weight): Vector similarity using BGE embeddings
3. **Ensemble Retriever**: Combines both retrievers
4. **Cross-Encoder Reranker**: Reranks top-10 candidates to top-5 using BAAI/bge-reranker-v2-m3

### Embedding Model
- **Model**: BAAI/bge-large-en-v1.5 (1024-dim embeddings)
- **Normalization**: L2 normalized
- **Query Prefix**: "Represent this sentence for searching relevant passages: "

### LLM Configuration
- **Model**: Qwen/Qwen3-32B (via Groq)
- **Temperature**: 0.0 (deterministic)
- **Reasoning**: Hidden reasoning format
- **Key Rotation**: Automatic switching after 2 questions per key

## Performance Considerations

### Vector Store
- Chroma with persistent storage
- Collection: `tables_schema`
- Fast retrieval in <100ms for typical queries

### LLM Calls
- Groq API provides ~500 tokens/second throughput
- Key rotation prevents rate limiting
- Async/await throughout for non-blocking calls

### Database Queries
- SQLite is efficient for compliance data (millions of rows)
- Proper indexing on `customer_id`, `account_id`, timestamps recommended
- Safe filtering prevents accidental full-table scans

## Common Use Cases

### 1. Compliance Reporting
```
"Show me all customers with critical alerts in the last 7 days"
```

### 2. Transaction Monitoring
```
"Has customer CUST_DIANA_VOSS had any wire transfers over $10,000?"
```

### 3. KYC Management
```
"List all customers with pending KYC verification"
```

### 4. Account Analysis
```
"What is the total balance across all accounts for customer CUST_JOHN_DOE?"
```

### 5. Investigation Support
```
"Show me all transactions with counterparty_bank matching 'Unknown Bank' in the last 30 days"
```

## Project Structure

```
TEXT_TO_SQL_AGENT/
├── README.md                      # This file
├── main_mcp.py                    # MCP server entry point
├── text_to_sql_client.py          # Test client & integration examples
├── text_to_sql_rag.py             # RAG pipeline core
├── db_schema_ingestion.py         # Schema processing & vector store setup
├── sqlite_connection.py           # Database connection & safety filtering
├── prompts.py                     # LLM prompt templates
├── sql.py                         # SQL utility functions
├── YOUR_DB_PATH.db                # SQLite database (placeholder)
└── data_generation/               # Sample data & schema definitions
    └── db_data/
        └── AML_schema.json        # Schema metadata for ingestion
```

## Troubleshooting

### Issue: "Error: 'query' is required"
**Solution:** Ensure required parameters are provided to the tool.

### Issue: Invalid table name errors
**Solution:** Check schema context using `retrieve_schema_context` to verify table names.

### Issue: Slow retrieval
**Solution:** Ensure Chroma vector store is properly initialized with `db_schema_ingestion.py`.

### Issue: Rate limiting on API calls
**Solution:** Add more Groq API keys to the `.env` file and increase `questions_per_key` in `KeyRotator`.

## Future Enhancements

- [ ] Multi-database support (PostgreSQL, MySQL)
- [ ] Query optimization suggestions
- [ ] Performance metrics and query analytics
- [ ] Schema versioning and migrations
- [ ] Custom prompt engineering per domain
- [ ] Streaming results for large datasets
- [ ] Query caching to reduce LLM calls

## License

Part of the purple_agent_pibench project.

## Support

For issues or questions, refer to the test client examples in `text_to_sql_client.py`.
