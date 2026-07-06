import os 
import json 
import asyncio
from typing import Any, List, Dict, Optional 
from mcp_client import MCPClient
from langchain_groq import ChatGroq 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from pathlib import Path
from prompt import POLICY_REFRAME_SYSTEM_PROMPT
load_dotenv()

SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "FINRA_HYBRID_RAG", "finra_rag_mcp_server.py")
SERVER_PATH = os.path.abspath(SERVER_PATH)
print(f"Connecting to MCP server: {SERVER_PATH}")

client = MCPClient(command="python", args=[SERVER_PATH])
_reframe_prompt = ChatPromptTemplate.from_messages([
    ('system', POLICY_REFRAME_SYSTEM_PROMPT),
    ('human', '{task}')
])

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

def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="qwen/qwen3-32b",
        api_key=rotator.get_and_advance(),
        temperature=0.0,
        reasoning_format="hidden",
    )

class PolicyAgent:
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
        tool_result = await self.mcp_client.call_tool("query_finra_regulations", {"query": reframed_query})
        raw_text = tool_result["content"][0] if tool_result["content"] else "{}"
        try:
            payload = json.loads(raw_text)

        except json.JSONDecodeError:
            payload = {"answer": None, "retrieved_count": 0, "sources": None, "error": raw_text}

        return {
            "task": task,
            "reframed_query": reframed_query,
            "answer": payload.get("answer"),
            "retrieved_count": payload.get("retrieved_count", 0),
            "sources": payload.get("sources"),
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
    policy_tasks = [
        "What is the SAR filing threshold?",
        "Who enforces FINRA Rule 3310?",
    ]

    agent = PolicyAgent()
    answer = await agent.run(policy_tasks)
    print(json.dumps(answer, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(_demo())






