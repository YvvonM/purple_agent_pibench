import asyncio
import os
from dotenv import load_dotenv
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

server_params = StdioServerParameters(
    command="python",
    args=["main_mcp.py"],
    env={
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "Y_GROQ": os.getenv("Y_GROQ"),
        "J_GROQ": os.getenv("J_GROQ"),
    }
)


async def test():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            print("=" * 80)

            
            print("\n--- Test generate_sql ---")
            result = await session.call_tool(
                "generate_sql",
                {"query": "Show me the 5 most recent transactions for customer CUST_DIANA_VOSS"}
            )
            print(result.content[0].text)

           
            print("\n--- Test execute_sql ---")
            result = await session.call_tool(
                "execute_sql",
                {"query": "Show me the 5 most recent transactions for customer CUST_DIANA_VOSS"}
            )
            parsed = json.loads(result.content[0].text)
            print(json.dumps(parsed, indent=2))

            
            print("\n--- Test sql_to_text ---")
            result = await session.call_tool(
                "sql_to_text",
                {
                    "query": "Show me the 5 most recent transactions for customer CUST_DIANA_VOSS",
                    "sql": "SELECT * FROM transactions WHERE customer_id = 'CUST_DIANA_VOSS' ORDER BY timestamp DESC LIMIT 5",
                    "results": [{"transaction_id": "MM_010_A01", "amount": 250000.0}]
                }
            )
            print(result.content[0].text)

           
            print("\n--- Test answer_question ---")
            result = await session.call_tool(
                "answer_question",
                {"query": "Has customer CUST_DIANA_VOSS had any wire transfers over $10,000?"}
            )
            print(result.content[0].text)

           
            print("\n--- Test retrieve_schema_context ---")
            result = await session.call_tool(
                "retrieve_schema_context",
                {"query": "transactions table schema"}
            )
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(test())