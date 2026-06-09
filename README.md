# purple_agent_pibench

## Overview

`purple_agent_pibench` is a hybrid retrieval-augmented generation (RAG) benchmark project built for regulatory compliance and financial risk intelligence. It combines:

- a Chroma vector store for semantic retrieval
- BM25 retrieval for keyword search
- cross-encoder reranking and contextual compression
- Neo4j graph query generation via Cypher and MCP
- evaluation through `deepeval` against FINRA-style goldens

The project is designed to inspect regulatory text, extract structured entities, build a knowledge-driven vector store, and answer compliance questions with grounded context.

## Key Components

- `vector_db_creation.py`
  - Generates document chunks from `Data_cleaning/FINRA/ontology_output.json`
  - Builds a Chroma vector store with `sentence-transformers` embeddings
  - Persists documents and metadata to `./chroma`

- `hybrid_rag.py`
  - Implements a hybrid retrieval pipeline using:
    - Chroma semantic search
    - BM25 keyword retrieval
    - ensemble retrieval
    - cross-encoder reranking
  - Extracts entity IDs from retrieved chunks
  - Uses `cypher_rag.py` to generate graph-aware Cypher queries
  - Answers questions using a Groq-powered LLM with curated regulatory prompts

- `cypher_rag.py`
  - Defines the Neo4j graph schema prompt and Cypher generation workflow
  - Connects to Neo4j via the `mcp-neo4j-cypher` adapter
  - Executes generated Cypher and formats graph results for the RAG prompt

- `rag_eval.py`
  - Evaluates RAG output using `deepeval`
  - Loads gold standard examples from `Data_cleaning/evaluation_dataset/goldens1.json`
  - Runs metrics such as precision, recall, relevancy, and faithfulness

- `Data_cleaning/`
  - Contains extraction, NER, ontology, and dataset preparation tools
  - Starts from the main FINRA markdown source file: `Data_cleaning/FINRA/policy.md`
  - Converts the policy markdown to structured JSON, resolves entities, builds an ontology index, and produces `ontology_output.json`

- `ollama_setup/`
  - Contains a Docker Compose setup for local Ollama service support

## Data cleaning pipeline

The data cleaning workflow is the project entrypoint for the FINRA content.
It begins with the primary markdown document at `Data_cleaning/FINRA/policy.md` and performs:

- markdown parsing and document structure extraction via `Data_cleaning/md_json.py`
- entity extraction and gazetteer matching
- ontology linking and relationship enrichment
- generation of `Data_cleaning/FINRA/verified.json`, `Data_cleaning/FINRA/ontology_output.json`, and `Data_cleaning/FINRA/entity_index.json`
- export of cleaned, metadata-rich regulatory text used by `vector_db_creation.py`

This section preserves the original document-based workflow and makes it clear that the main FINRA source is the markdown file.

## Requirements

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

The project depends on:

- `spacy`
- `python-dotenv`
- `google-genai`
- `openai`
- `neo4j`
- `langchain` and related adapters
- `sentence-transformers`
- `chromadb`
- `deepeval`
- `rank_bm25`
- `litellm`
- `pytest`

## Environment Variables

Create a `.env` file with at least the following values:

```ini
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_DATABASE=neo4j
GROQ_API_KEY=
DEEP_EVAL_API=
```

## Usage

1. Build or refresh the vector database:

```bash
python vector_db_creation.py
```

2. Run the hybrid RAG pipeline:

```bash
python hybrid_rag.py
```

3. Evaluate model and retrieval quality:

```bash
python rag_eval.py
```

4. Optionally test Neo4j connectivity:

```bash
python neo4j_db_connection_test.py
```

## Project Workflow

1. `Data_cleaning` prepares regulatory text and entity metadata.
2. `vector_db_creation.py` turns extracted content into Chroma-ready chunks.
3. `hybrid_rag.py` retrieves relevant passages, extracts entity IDs, and enriches answers with Neo4j graph context.
4. `cypher_rag.py` generates safe, read-only Cypher queries from user questions.
5. `rag_eval.py` measures retrieval and answer quality against gold labels.

## Notes

- Prompts in `prompts.py` are tuned for regulatory compliance and FINRA-specific terminology.
- The graph schema is designed around `Entity` nodes, regulatory relationships, and compliance concepts.
- The pipeline is intentionally hybrid: it blends keyword search, semantic search, and structured graph reasoning.


