from typing import Any, List, Dict, Optional
import asyncio
from pathlib import Path
from langchain_groq import ChatGroq 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from mcp_client import MCPClient
from dotenv import load_dotenv
import json
from prompt import REFRAME_SYSTEM_PROMPT
import os

load_dotenv()

SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "TEXT_TO_SQL_AGENT", "main_mcp.py")
SERVER_PATH = os.path.abspath(SERVER_PATH)
print(f"Connecting to MCP server: {SERVER_PATH}")

client = MCPClient(command="python", args=[SERVER_PATH])
_reframe_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', REFRAME_SYSTEM_PROMPT),
        ('human', '{task}')
    ]
)
def get_tools():
    return f"\nConnected! Available tools: {client.get_tool_names_and_description()}"

class KeyRotator:
    """Rotates through API keys, switching after `questions_per_key` calls."""

    def __init__(self, keys: List[str], questions_per_key: int = 2):
        if not keys:
            raise ValueError("No API keys provided.")
        self.keys = keys
        self.questions_per_key = questions_per_key
        self._index = 0
        self._count = 0

    @property
    def current_key(self) -> str:
        return self.keys[self._index]

    def advance(self):
        """Call after each question is answered."""
        self._count += 1
        if self._count >= self.questions_per_key:
            self._count = 0
            self._index = (self._index + 1) % len(self.keys)
            print(f"[KeyRotator] Switched to key index {self._index}")

    def get_and_advance(self) -> str:
        """Return the current key, then advance the counter."""
        key = self.current_key
        self.advance()
        return key


rotator = KeyRotator(
    keys=[
        k for k in [
            os.getenv("Y_GROQ"),
            os.getenv("J_GROQ"),
            os.getenv("GROQ_API_KEY"),   
        ]
        if k  
    ],
    questions_per_key=2,
)

def _get_llm() ->ChatGroq:
    return ChatGroq(
        model="qwen/qwen3-32b",
        api_key=rotator.get_and_advance(),
        temperature=0.0,
        reasoning_format="hidden",
    )

class DataAgent:
    def __init__(self):
        self.mcp_client = client 
    async def start(self):
        await self.mcp_client.connect()

    async def stop(self):
        await self.mcp_client.close()

    async def _reframe(self, task:str) -> str:
        chain = _reframe_prompt | _get_llm() | StrOutputParser()
        reframed = await chain.ainvoke({'task':task})
        return reframed.strip()

    async def _handle_task(self, task:str) -> Dict[str, Any]:
        reframed_query = await self._reframe(task)
        print(reframed_query)
        if not reframed_query:
            return {
            "task": task,
            "reframed_query": reframed_query,
            "sql": None,
            "results": None,
            "row_count": 0,
            "error": f"Reframe step returned empty output for task: {task!r}",
            }
        tool_result = await self.mcp_client.call_tool("execute_sql", {"query": reframed_query})
        print(tool_result)
        raw_text = tool_result["content"][0] if tool_result["content"] else "{}"
        try:
            payload = json.loads(raw_text)

        except json.JSONDecodeError:
            payload = {"sql": None, "results": None, "row_count": 0, "error": raw_text}

        return{
            "task": task,
            "reframed_query": reframed_query,
            "sql": payload.get("sql"),
            "results": payload.get("results"),
            "row_count": payload.get("row_count", 0),
            "error": payload.get("error"),
        }

    async def run(self, data_tasks:List[str]) -> List[Dict[str, Any]]:
        await self.start()
        try:
            results = []
            for task in data_tasks:
                result = await self._handle_task(task)
                print("*" * 80)
                print(result)
                print("*" * 80)
                results.append(result)
            return results
        finally:
            await self.stop()

async def _demo():
    data_tasks = [
        "Get pending request REQ_010_1",
        "Get account ACCT_DIANA_INV_001 status",
    ]

    agent = DataAgent()
    answer = await agent.run(data_tasks)
    print(json.dumps(answer, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(_demo())


