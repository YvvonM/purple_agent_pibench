import os 
import json 
import asyncio
from typing import Any, List, Dict, Optional 
from mcp_client import MCPClient
from langchain_groq import ChatGroq 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sys
from dotenv import load_dotenv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "session_db"))
from prompt import POLICY_REFRAME_SYSTEM_PROMPT
from memory import SessionMemory

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

    async def _reframe(self, task:str,) -> str:
        chain = _reframe_prompt | _get_llm() | StrOutputParser()
        reframed = await chain.ainvoke({'task':task})
        return reframed.strip()

    async def _handle_task(self, task:str, memory: SessionMemory = None, session_id: str = None, turn_index: int = 0, step_base: int = 0) -> Dict[str, Any]:
        step = step_base
        reframed_query = await self._reframe(task)
        step += 1
        if memory and session_id:
            memory.log_reasoning_step(
                session_id=session_id,
                turn_index = turn_index,
                step_number=step,
                agent_name="policy_agent",
                step_type="reframe",
                description=f"Reframed policy task: '{task}' -> '{reframed_query}'",
                input_context={"original_task": task},
                output_action={"reframed_query": reframed_query})
        tool_result = await self.mcp_client.call_tool("query_finra_regulations", {"query": reframed_query})
        step += 1
        if memory and session_id:
            memory.log_tool_call(
                session_id=session_id,
                turn_index = turn_index,
                step_number=step,
                agent_name="policy_agent",
                tool_name="query_finra_regulations",
                arguments={"query": reframed_query},
                result={"content": tool_result["content"][0][:500]})
        raw_text = tool_result["content"][0] if tool_result["content"] else "{}"
        try:
            payload = json.loads(raw_text)

        except json.JSONDecodeError:
            payload = {"answer": None, "retrieved_count": 0, "sources": None, "error": raw_text}

        step += 1
        if memory and session_id:
            memory.log_reasoning_step(
                session_id=session_id,
                turn_index = turn_index,
                step_number=step,
                agent_name="policy_agent",
                step_type="observe",
                description=f"Policy retrieval returned {payload.get('retrieved_count', 0)} sources",
                input_context={"reframed_query": reframed_query},
                output_action={"answer_preview": payload.get("answer", "")[:200] if payload.get("answer") else None,
                    "retrieved_count": payload.get("retrieved_count", 0),
                    "has_error": bool(payload.get("error"))}

            )

        return {
            "task": task,
            "reframed_query": reframed_query,
            "answer": payload.get("answer"),
            "retrieved_count": payload.get("retrieved_count", 0),
            "sources": payload.get("sources"),
            "error": payload.get("error"),
            }
        

    async def run(self, policy_tasks:List[str], memory: SessionMemory = None, session_id: str = None, turn_index: int = 0) -> List[Dict[str, Any]]:
        await self.start()
        try:
            results = []
            for i, task in enumerate(policy_tasks):
                result = await self._handle_task(task=task, memory=memory, 
                session_id=session_id, turn_index=turn_index, step_base=i * 10)
                print("*" * 80)
                print(result)
                print("*" * 80)
                results.append(result)
            return results
        finally:
            await self.stop()

async def _demo():
    # Create memory
    mem = SessionMemory()

    # Create session
    sid = mem.create_session(
        scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
        customer_id="CUST_DIANA_VOSS"
    )
    print(f"\nCreated session: {sid}\n")

    policy_tasks = [
        "Find rules about wire transfers during lock-up periods",
        "Find communication requirements for lock-up denials",
    ]

    agent = PolicyAgent()
    answers = await agent.run(
        policy_tasks=policy_tasks,
        memory=mem,
        session_id=sid,
        turn_index=0
    )

    # Print trace
    print("\n")
    mem.print_trace(sid)

    # Cleanup (optional — keep for inspection)
    # import os
    # os.unlink(mem.db_path)


if __name__ == "__main__":
    asyncio.run(_demo())






