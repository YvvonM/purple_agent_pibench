import os
import sys
import json 
import asyncio
from pathlib import Path 
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server 
from mcp.server.stdio import stdio_server
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, Tool

from hybrid_rag import (make_prediction_async, embedding_fn, vectorstore, 
    all_chunks, extract_entity_ids, format_context)
from langchain_community.retrievers.bm25 import BM25Retriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from cypher_rag import neo4j_mcp_server, generate_cypher, execute_cypher, format_graph_results, get_entity_expansion
from mcp import ClientSession
from dotenv import load_dotenv
load_dotenv()

server = Server("finra-hybrid-rag")

TOOLS = [
    Tool(
        name="query_finra_regulations",
        description=(
            "Query FINRA regulatory documents using a hybrid RAG pipeline. "
            "Combines semantic search (Chroma/BGE), BM25 keyword search, "
            "cross-encoder reranking, and Neo4j graph enrichment. "
            "Returns a compliance-grounded answer with citations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The regulatory compliance question to answer."
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name = "get_retrieval_context",
        description=(
            "Run the retrieval pipeline only (no LLM generation). "
            "Returns the raw retrieved documents and graph context for inspection."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to run through the retrieval pipeline."
                }
            },
            "required": ["query"]
        }
    )
]

@server.list_tools()
async def list_tools() -> List[Tool]:
    return TOOLS

@server.call_tool()
async def call_tools(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "query_finra_regulations":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text="Error: 'query' is required.")]
        
        answer, retrieved_docs, full_context = await make_prediction_async(query)

        result = {
            "answer": answer,
            "retrieved_count": len(retrieved_docs),
            "sources":[
                {"text": doc[:700] + "..." if len(doc) > 700 else doc}
            for doc in retrieved_docs
            ]
            
        }
        return [TextContent(type = "text", text = json.dumps(result, indent = 2))]

    elif name == "get_retrieval_context":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text="Error: 'query' is required.")]

        sim_retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 20})
        bm25_retriever = BM25Retriever.from_documents(all_chunks, k=20)
        ensemble = EnsembleRetriever(retrievers=[bm25_retriever, sim_retriever], weights=[0.6, 0.4])
        reranker = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
        compressor = CrossEncoderReranker(model=reranker, top_n=5)
        final_retriever = ContextualCompressionRetriever(base_retriever=ensemble, base_compressor=compressor)
        docs = final_retriever.invoke(query)
        entity_ids = extract_entity_ids(docs)
        graph_context = ""
        if entity_ids:
            try:
                async with stdio_client(neo4j_mcp_server) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        try:
                            cypher = await generate_cypher(session, query, entity_ids)
                            records = await execute_cypher(session, cypher)
                            graph_context = format_graph_results(records)
                        except Exception:
                            graph_context = await get_entity_expansion(session, entity_ids)
            except Exception:
                graph_context = ""

        context_string  = format_context(docs, graph_context)
        result = {
            "retrieved_count": len(docs),
            "entity_ids": entity_ids,
            "graph_context_present": bool(graph_context),
            "full_context": full_context 
        }

        return [TextContent(type="text", text = json.dumps(result, indent = 2))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())


        
