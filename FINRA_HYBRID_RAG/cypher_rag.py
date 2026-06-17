import os
import json
from typing import List, Dict
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from prompts import GRAPH_SCHEMA

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
VDB_API_KEY = os.getenv("GROQ_API_KEY")


neo4j_mcp_server = StdioServerParameters(
    command="uvx",
    args=["mcp-neo4j-cypher@0.6.0", "--transport", "stdio"],
    env={
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USERNAME,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE", "neo4j"),
    }
)


cypher_llm = ChatGroq(
    model="qwen/qwen3-32b",
    api_key=VDB_API_KEY,
    temperature=0.1,
    reasoning_format="hidden"
)


async def generate_cypher(session: ClientSession, user_question: str, entity_ids: List[str] = None) -> str:
    """Ask LLM to write Cypher based on question and known entities."""
    
    prompt_text = f"""{GRAPH_SCHEMA}

The user asks: "{user_question}"
Known entity IDs: {entity_ids or 'None found'}

Write a Cypher query to answer this. Return ONLY the Cypher query, no backticks."""

    response = await cypher_llm.ainvoke([HumanMessage(content=prompt_text)])
    
    cypher = response.content.strip()
    cypher = cypher.replace("```cypher", "").replace("```", "").strip()
    
    print(f"\nGenerated Cypher:\n{cypher}")
    return cypher


async def execute_cypher(session: ClientSession, cypher: str, params: Dict = None) -> List[Dict]:
    """Execute Cypher via MCP and return results."""
    result = None
    try:
        raw = await session.call_tool(
            "read_neo4j_cypher",
            {
                "query": cypher,
                "params": params or {}
            }
        )
        result = raw.content[0].text
        
        print(f"Raw Cypher Result: {result}")
        print("*"*50)
        print(f"Type of result: {type(result)}")
        content = getattr(result, 'content', result)
        
        if isinstance(content, list):
            return [dict(r) if hasattr(r, 'items') else r for r in content]
        elif isinstance(content, str):
            try:
                return json.loads(content)
            except:
                return [{"raw": content}]
        else:
            return [{"raw": str(content)}]
            
    except Exception as e:
        print(f"Cypher execution failed: {e}")
        return []


def format_graph_results(records: List[Dict]) -> str:
    """Format Neo4j records into readable text for the LLM."""
    if not records:
        return ""
    
    lines = ["\n=== KNOWLEDGE GRAPH RESULTS ==="]
    for i, record in enumerate(records[:15], 1):
        parts = []
        for key, value in record.items():
            if value is not None:
                parts.append(f"{key}: {value}")
        
        if parts:
            lines.append(f"  [{i}] " + " | ".join(parts))
    
    lines.append("=== END GRAPH RESULTS ===\n")
    return "\n".join(lines)


async def get_entity_expansion(session: ClientSession, entity_ids: List[str]) -> str:
    """Fallback: simple neighborhood expansion from known entities."""
    if not entity_ids:
        return ""
    
    cypher = """
    MATCH (e:Entity)
    WHERE e.id IN $entity_ids
    OPTIONAL MATCH (e)-[r]-(related:Entity)
    RETURN DISTINCT
        e.name AS from_entity,
        type(r) AS relationship,
        related.name AS to_entity,
        related.type AS to_type
    LIMIT 20
    """
    
    records = await execute_cypher(session, cypher, {"entity_ids": entity_ids})
    return format_graph_results(records)