# FINRA_HYBRID_RAG

A sophisticated hybrid Retrieval-Augmented Generation (RAG) system for querying FINRA regulatory documents. This system combines vector-based semantic search, keyword matching (BM25), cross-encoder reranking, and Neo4j graph database enrichment to provide accurate, compliance-grounded answers to regulatory questions.

## Overview

The FINRA_HYBRID_RAG system is designed to help compliance professionals, legal teams, and financial institutions quickly access regulatory guidance from FINRA rules, AML obligations, and related financial regulations. It uses a multi-stage retrieval pipeline followed by an LLM to synthesize answers with proper citations.

### Key Features

- **Hybrid Retrieval Pipeline**: Combines semantic search (Chroma/BGE), BM25 keyword matching, and cross-encoder reranking
- **Knowledge Graph Enrichment**: Optional Neo4j integration for structured relationship navigation
- **Entity Resolution**: Links documents to entity metadata (regulations, organizations, compliance processes)
- **MCP Server Interface**: Model Context Protocol server for integration with LLM tools
- **RAG Evaluation**: Built-in evaluation framework using DeepEval metrics
- **Performance Analytics**: Query latency and retrieval metrics tracking

## Architecture

### Core Components

1. **hybrid_rag.py** - Main RAG Pipeline
   - Ensemble retriever combining BM25 and semantic search
   - Cross-encoder reranking for top-5 candidate selection
   - Neo4j graph context retrieval via MCP
   - LLM-based answer synthesis with API key rotation

2. **finra_rag_mcp_server.py** - MCP Server
   - Exposes 2 tools via Model Context Protocol
   - Handles tool routing and error management
   - Supports both full pipeline and retrieval-only modes

3. **cypher_rag.py** - Graph Query Engine
   - LLM-based Cypher query generation
   - Neo4j Aura connection via MCP
   - Entity expansion fallback for graceful degradation
   - Graph results formatting for LLM consumption

4. **vector_db_creation.py** - Vector Store Setup
   - Chunk creation from ontology JSON
   - Entity resolution and metadata enrichment
   - Chroma vector store initialization with BGE embeddings

5. **prompts.py** - LLM Prompt Templates
   - Vector DB retrieval system prompt
   - Cypher generation prompt with entity catalog
   - Final synthesis prompt combining vector + graph context

6. **rag_eval.py** - Evaluation Framework
   - DeepEval metrics integration
   - Supports: Contextual Precision, Recall, Relevancy, Faithfulness, Answer Relevancy
   - Automated test case generation from golden dataset

7. **neo4j_db_connection_test.py** - Neo4j Connection Tester
   - Connection validation
   - Cypher query testing
   - Graph traversal verification

## Available Tools (MCP Server)

### 1. `query_finra_regulations`
Full pipeline: retrieval → graph enrichment → LLM answer generation.

**Input:**
- `query` (string, required): The regulatory compliance question

**Output:**
```json
{
  "answer": "Compliance-grounded answer with citations",
  "retrieved_count": 5,
  "sources": [
    {"text": "Retrieved document excerpt..."},
    ...
  ]
}
```

**Example:**
```python
result = await session.call_tool(
    "query_finra_regulations",
    {"query": "What are the requirements for AML compliance programs?"}
)
```

### 2. `get_retrieval_context`
Retrieval-only pipeline: no LLM, just document + graph context.

**Input:**
- `query` (string, required): Query for context retrieval

**Output:**
```json
{
  "retrieved_count": 5,
  "entity_ids": ["REG_002", "PROG_001"],
  "graph_context_present": true,
  "full_context": "Retrieved documents + graph results"
}
```

**Example:**
```python
result = await session.call_tool(
    "get_retrieval_context",
    {"query": "SAR filing deadlines"}
)
```

## Retrieval Pipeline Details

### Stage 1: Dual Retrieval (Ensemble)
- **BM25 Retriever** (60% weight): Fast keyword matching on document chunks
- **Vector Retriever** (40% weight): Semantic similarity using BGE embeddings
- **Result**: Top 20 candidates merged with weighted scores

### Stage 2: Cross-Encoder Reranking
- **Model**: BAAI/bge-reranker-v2-m3
- **Purpose**: Rerank top-20 to top-5 using fine-tuned relevance scoring
- **Benefit**: Removes false positives from ensemble stage

### Stage 3: Entity Extraction
- Extracted from document metadata (`entity_ids` field)
- Used to identify relevant graph entities
- Examples: REG_002 (FINRA Rule 3310), PROG_001 (AML Program)

### Stage 4: Graph Enrichment (Optional)
- **Default**: Cypher generation from question + entity IDs
- **Fallback**: Entity neighborhood expansion
- **Result**: Formatted graph triples for LLM context

### Stage 5: LLM Synthesis
- **Model**: Qwen/Qwen3-32B (via Groq)
- **Prompt**: Combines vector context + graph results
- **Output**: Compliance-grounded answer with regulatory citations

## Database Schema

### Vector Store (Chroma)
- **Collection**: "FINRA"
- **Embeddings**: BGE-large-en-v1.5 (1024-dim)
- **Chunks**: Document titles, sections, paragraphs with metadata

### Chunk Metadata
```json
{
  "source": "Document title",
  "section": "Section heading",
  "item_number": "1.2.3",
  "content_type": "paragraph|section_title|title",
  "domain": "AML",
  "entity_names": "comma-separated entity names",
  "entity_types": "compliance_process, regulatory_program, etc.",
  "entity_ids": "PROG_001, COMP_002, etc.",
  "resolved_entities_json": "[{id, canonical_name, ontology_type}, ...]"
}
```

### Knowledge Graph (Neo4j)
**Entity Types:**
- `federal_regulation`, `finra_rule`, `treasury_regulation`
- `self_regulatory_organization`, `government_agency`, `international_organization`
- `regulatory_notice`, `compliance_process`, `compliance_obligation`
- `regulatory_program`, `regulatory_report`
- `regulated_entity`, `customer_risk_category`, `customer_type`, `legal_entity`
- `reporting_threshold`, `retention_period`, `review_period`, `filing_deadline`
- `financial_crime`, `market_manipulation`, `securities_violation`, `fraud_scheme`
- `transaction_type`, `transaction_pattern`
- `security_instrument`, `account_status`, `account_structure`

**Relationships:**
`REQUIRES`, `AUTHORIZES`, `PROMULGATED_BY`, `RELATED_REGULATIONS`, `ENFORCED_BY`, `APPLIES_TO`, `THRESHOLD`, `RETENTION_PERIOD`, `REGULATES`, `ISSUES`, `ENFORCES`, and 30+ others

## Setup & Installation

### Prerequisites
- Python 3.10+
- Chroma vector store configured
- Groq API keys (multiple for rotation)
- Neo4j Aura instance (optional but recommended)
- `uvx` for running MCP servers

### Environment Variables
Create a `.env` file:
```env
# Groq API Keys (for LLM calls)
GROQ_API_KEY=your_primary_key
Y_GROQ=your_second_key
J_GROQ=your_third_key

# Neo4j Aura
NEO4J_URI=neo4j+s://your-instance.neo4jdatabase.com
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# DeepEval (optional, for evaluation)
DEEP_EVAL_API=your_deepeval_api_key
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Initialize Vector Store
```bash
python vector_db_creation.py
```
This creates:
- Chroma vector store at `./chroma`
- Pickle file with BM25 chunks
- Embedded chunks with entity metadata

### Test Neo4j Connection (Optional)
```bash
python neo4j_db_connection_test.py
```
Verifies connectivity and basic Cypher execution.

## Running the System

### As an MCP Server
```bash
python finra_rag_mcp_server.py
```
Listens on stdin/stdout for MCP protocol messages. Perfect for integration with Claude, other LLMs, or custom tools.

### Direct Pipeline Usage
```python
from hybrid_rag import make_prediction

query = "What are the suspicious activity reporting requirements?"
answer, retrieved_docs, full_context = make_prediction(query)
print(answer)
```

### Batch Processing
```bash
python hybrid_rag.py
```
Reads from `Data_cleaning/evaluation_dataset/goldens1.json`, processes all queries, outputs to `rag_answers.json`.

### Evaluation
```bash
python rag_eval.py
```
Runs DeepEval metrics against test dataset:
- Contextual Precision
- Contextual Recall
- Contextual Relevancy
- Faithfulness
- Answer Relevancy

## Performance Considerations

### Latency Breakdown
- **Vector retrieval**: ~50-100ms
- **BM25 retrieval**: ~20-50ms
- **Cross-encoder reranking**: ~100-200ms
- **Cypher generation**: ~1-2s (LLM call)
- **Cypher execution**: ~100-500ms
- **LLM synthesis**: ~2-5s (Groq)
- **Total**: ~5-10s per query

### Optimization Tips
1. **Cache embeddings**: Reuse vector results for identical queries
2. **Batch Cypher queries**: Process multiple entity expansions simultaneously
3. **Increase reranker top_n**: Balance precision vs. LLM token budget
4. **Use API key rotation**: Prevents rate limiting with multiple keys
5. **Async processing**: All I/O is non-blocking (asyncio)

### Throughput
- **Groq API limit**: 12,000 TPM
- **Typical tokens/query**: 2,000 (generation) + 1,500 (synthesis) = 3,500
- **Max queries/minute**: ~3-4 queries

## Common Use Cases

### 1. Compliance Program Review
```
"What is required for an effective Anti-Money Laundering compliance program?"
→ Returns FINRA Rule 3310, FinCEN guidance, Treasury requirements
```

### 2. SAR Filing Guidance
```
"When must a Suspicious Activity Report be filed?"
→ Returns timelines, thresholds, and filing procedures
```

### 3. Customer Due Diligence
```
"What customer information must be collected for KYC purposes?"
→ Returns CDD requirements, beneficial owner identification, risk assessment procedures
```

### 4. Transaction Monitoring
```
"What patterns indicate potential money laundering?"
→ Returns red flags, structuring indicators, and investigation triggers
```

### 5. Regulatory Updates
```
"What organizations oversee AML compliance?"
→ Returns FinCEN, SEC, FINRA, and international regulators
```

## Project Structure

```
FINRA_HYBRID_RAG/
├── README.md                              # This file
├── hybrid_rag.py                          # Main RAG pipeline
├── finra_rag_mcp_server.py               # MCP server entry point
├── cypher_rag.py                         # Neo4j Cypher generation
├── vector_db_creation.py                 # Vector store setup
├── prompts.py                            # LLM prompt templates
├── rag_eval.py                           # Evaluation framework
├── rag_performance.py                    # Performance metrics
├── test_client.py                        # MCP client test
├── neo4j_db_connection_test.py           # Neo4j connectivity tester
├── chroma/                               # Vector store (persistent)
│   ├── chroma.parquet
│   ├── header.parquet
│   └── bm25_chunks.pkl
├── Data_cleaning/                        # Raw data & evaluation datasets
│   ├── FINRA/
│   │   ├── ontology_output.json         # Document chunks with structure
│   │   └── entity_index.json            # Entity metadata registry
│   └── evaluation_dataset/
│       ├── goldens1.json                 # Golden Q&A pairs
│       └── rag_answers2.json            # Generated answers
└── requirements.txt
```

## Troubleshooting

### Issue: "Chroma collection not found"
**Solution**: Run `python vector_db_creation.py` to initialize the vector store.

### Issue: Neo4j MCP connection fails
**Solution**: 
1. Check Neo4j URI, credentials in `.env`
2. Run `python neo4j_db_connection_test.py` to validate connection
3. Fall back to vector-only mode if Neo4j unavailable

### Issue: Slow Cypher generation
**Solution**: 
- Increase `temperature` in `_get_llm()` for faster generation (but potentially lower quality)
- Pre-compute common Cypher patterns and cache them

### Issue: Rate limiting on Groq
**Solution**: 
- Add more API keys to `.env` (Y_GROQ, J_GROQ)
- Decrease `questions_per_key` in KeyRotator
- Increase sleep time between batches

### Issue: Out of memory during vector store creation
**Solution**: 
- Process documents in smaller batches
- Use a lower-dimensional embedding model (e.g., BGE-small)
- Stream documents to Chroma instead of loading all at once

## Advanced Configuration

### Tuning Retrieval Weights
In `hybrid_rag.py`, line 149:
```python
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, sim_retriever],
    weights=[0.6, 0.4],  # Adjust: higher = prefer keyword matching
)
```

### Changing Reranker Top-N
In `hybrid_rag.py`, line 153:
```python
reranker_compressor = CrossEncoderReranker(model=reranker, top_n=5)  # Increase for more precision
```

### Entity Extraction Strategy
In `cypher_rag.py`, line 115-128: Customize fallback entity expansion query.

## Integration with LLMs

### With Claude (via Anthropic SDK)
```python
import anthropic
from mcp.client.stdio import stdio_client

client = anthropic.Anthropic()
with stdio_client(...) as server:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=[...],  # Include FINRA RAG tools
        messages=[{"role": "user", "content": "Query about FINRA compliance"}]
    )
```

### With Other LLMs
The MCP server interface makes it compatible with:
- Any MCP-compatible LLM platform
- Custom Python agents
- Web UI wrappers

## Evaluation & Metrics

The `rag_eval.py` script provides:

**Metrics:**
1. **Contextual Precision**: Ratio of relevant retrieval context
2. **Contextual Recall**: Completeness of retrieved context
3. **Contextual Relevancy**: Relevance of full context to question
4. **Faithfulness**: Answer fidelity to source documents
5. **Answer Relevancy**: Direct relevance of answer to question

**Output:**
```
Contextual Precision: 0.847
Contextual Recall: 0.923
Contextual Relevancy: 0.812
Faithfulness: 0.956
Answer Relevancy: 0.891
```

## Future Enhancements

- [ ] Support for multi-hop reasoning (traverse graph for 2+ hops)
- [ ] Streaming responses for long-form answers
- [ ] Query expansion and synonym resolution
- [ ] Document versioning and regulatory change tracking
- [ ] Fine-tuned retriever for compliance domain
- [ ] GraphRAG integration for better structural understanding
- [ ] Cache layer for common queries
- [ ] A/B testing framework for retriever improvements
- [ ] Multilingual regulatory document support

## License

Part of the purple_agent_pibench project.

## Support

For issues:
1. Check Neo4j connectivity: `python neo4j_db_connection_test.py`
2. Verify vector store: Check `./chroma` directory exists
3. Test retrieval: Run `python test_client.py`
4. Review logs: Stderr contains detailed pipeline info
