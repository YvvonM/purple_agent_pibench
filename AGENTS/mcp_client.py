import asyncio
import json 
import os
from contextlib import AsyncExitStack 
from typing import Any, Dict, List, Optional 
from mcp import ClientSession, StdioServerParameters 
from mcp.client.stdio import stdio_client
from mcp.types import TextContent 
from dotenv import load_dotenv
load_dotenv()

env={
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "Y_GROQ": os.getenv("Y_GROQ"),
        "J_GROQ": os.getenv("J_GROQ"),
    }


class MCPClient:
    def __init__(self, command:str, args:List[str]):
        self.command = command
        self.args = args 
        self.env = env 
        self._exit_stack: Optional[AsyncExitStack] = None 
        self._session: Optional[ClientSession] = None
        self._tools: List[Dict[str, Any]] = []
    async def connect(self) -> None:
        self._exit_stack = AsyncExitStack()
        params = StdioServerParameters(
            command = self.command,
            args = self.args,
            env = self.env
        )
        read, write = await self._exit_stack.enter_async_context(stdio_client(params))
        self._session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        tools_result = await self._session.list_tools()
        self._tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]

    def get_tools(self) -> List[Dict[str, Any]]:
        return self._tools.copy()

    def get_tool_names_and_description(self) -> List[str]:
        return [{t["name"]: t['input_schema']} for t in self._tools]


    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if self._session is None:
            raise RuntimeError("MCPClient not connected. Call connect() first.")

        result = await self._session.call_tool(name, arguments= arguments)
        texts = []
        for content in result.content:
            if isinstance(content, TextContent):
                texts.append(content.text)

            else:
                texts.append(str(content))

        return{
            "content": texts,
            "is_error": result.isError,
            "tool_name": name,
        }

    async def close(self) -> None:
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
        self._exit_stack = None
        self._session = None
        self._tools = []

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
async def _test():
    server_path = os.path.join(os.path.dirname(__file__), "..", "TEXT_TO_SQL_AGENT", "main_mcp.py")
    server_path = os.path.abspath(server_path)
    
    print(f"Connecting to MCP server: {server_path}")
    async with MCPClient(command="python", args=[server_path]) as client:
        print(f"\nConnected! Available tools: {client.get_tool_names_and_description()}")
        result = await client.call_tool("retrieve_schema_context", {"query": "wire transfer"})
        print(f"\nTool: retrieve_schema_context")
        print(f"Error: {result['is_error']}")
        print(f"Content preview: {result['content'][0][:500]}...")
        result = await client.call_tool("execute_sql", {
            "sql": "SELECT COUNT(*) as count FROM transactions"
        })
        print(f"\nTool: execute_sql")
        print(f"Error: {result['is_error']}")
        print(f"Content: {result['content']}")


if __name__ == "__main__":
    asyncio.run(_test())
        
