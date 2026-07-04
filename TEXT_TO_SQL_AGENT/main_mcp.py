import os 
import sys 
import json
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional 
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


from mcp.server import Server 
from mcp.server.stdio import stdio_server
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent 
from text_to_sql_rag import (sql_to_text, extract_sql, execute_sql,
    format_context, embedding_fn, vectorstore, final_retriever, generate_sql, run_pipeline) 

from mcp import ClientSession 
import asyncio


server = Server("Text-To-SQL-MCP")
TOOLS = [
    Tool(
        name="generate_sql",
        description=(
            "Generate a SQLite SQL query from a natural language question. "
            "Uses hybrid retrieval (BM25 + semantic search + cross-encoder reranking) "
            "over database schema docs, then an LLM generates the SQL. "
            "Returns raw SQL with markdown fences and explanations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language question about compliance data."
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="execute_sql",
        description=(
            "Execute a SQLite SELECT query against the compliance database. "
            "Accepts either raw SQL or a natural language question. "
            "If 'sql' is provided, executes it directly. "
            "If 'query' is provided, generates SQL first then executes. "
            "Safety-filtered: only SELECT queries allowed. Returns results or error."
        ),
        inputSchema={"type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "Raw SQL SELECT statement to execute directly."
                },
                "query": {
                    "type": "string",
                    "description": "Natural language question. SQL will be generated automatically."
                }
            },
        }
    ),
    Tool(
        name="sql_to_text",
        description=(
            "Translate SQL query results into plain English summary. "
            "Consumes the question, SQL, and results; returns a 1-2 sentence answer "
            "for non-technical stakeholders."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Original natural language question."
                },
                "sql": {
                    "type": "string",
                    "description": "The SQL query that was executed."
                }
            },
        
        }
    ),
    Tool(
        name="answer_question",
        description=(
            "End-to-end pipeline: question → SQL generation → execution → natural language answer. "
            "Runs generate_sql, execute_sql, and sql_to_text in sequence. "
            "Returns SQL, raw results, and plain English summary."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language question about compliance data."
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="retrieve_schema_context",
        description=(
            "Run the schema retrieval pipeline only (no SQL generation). "
            "Returns the top-N relevant table schema documents for inspection "
            "or manual query building."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to retrieve relevant schema docs for."
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
async def call_tool(name: str, arguments: Dict[str, str]) -> List[TextContent]:
    if name == "generate_sql":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text="Error: 'query' is required.")]
        sql = await generate_sql(query)
        clean_sql = extract_sql(sql)
        return [TextContent(type="text", text=clean_sql)]

    elif name == "execute_sql":
        raw_sql = arguments.get("sql", "")
        query = arguments.get("query", "")
        if not raw_sql and not  query:
            return [TextContent(type="text", text="Error: 'sql' or 'query' is required.")]
        if raw_sql:
            clean_sql = extract_sql(raw_sql)
            print(f"executing the following sql: {clean_sql}")
        else:
            sql = await generate_sql(query)
            clean_sql = extract_sql(sql)
            print(f"executing the following sql: {clean_sql}")
        execution_result = execute_sql(clean_sql)
        return [TextContent(type="text", text=json.dumps(execution_result, indent=2))]

    elif name == "sql_to_text":
        query = arguments.get("query", "")
        raw_sql = arguments.get("sql", "")
        if not query and not raw_sql:
            return [TextContent(type="text", text="Error: 'sql' or 'query' is required.")]
        if raw_sql:
            clean_sql = extract_sql(raw_sql)
            execution_result = execute_sql(clean_sql)
        else:
            sql = await generate_sql(query)
            clean_sql = extract_sql(sql)
            execution_result = execute_sql(clean_sql)
        text_answer = await sql_to_text(query, clean_sql, execution_result['results'])
        return [TextContent(type="text", text=json.dumps(text_answer, indent=2))]

    elif name == "answer_question":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text="Error: 'query' is required.")]
        result = await run_pipeline(query)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "retrieve_schema_context":
        query = arguments.get("query", "")
        if not query:
            return [TextContent(type="text", text="Error: 'query' is required.")]
        vectordb_context = format_context(await final_retriever.ainvoke(query))
        return [TextContent(type="text", text=vectordb_context)]

    else:
        return [TextContent(type="text", text=f"Error: unknown tool '{name}'.")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())