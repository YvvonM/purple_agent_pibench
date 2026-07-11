import json 
from typing import Dict, Optional, List, Any, Protocol
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser 
import os 
import asyncio
from dotenv import load_dotenv
from data_agent import DataAgent
from policy_agent import PolicyAgent
from pathlib import Path
import sys 
sys.path.insert(0, str(Path(__file__).parent / "session_db"))
from memory import SessionMemory
from prompt import (INTENT_PROMPT,
    ADAPTIVE_PROMPT)
load_dotenv()

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

_intent_prompt = ChatPromptTemplate.from_messages([
    ('system', INTENT_PROMPT),
    ('human', '{user_message}')
])
_adaptive_prompt = ChatPromptTemplate.from_messages([
    ('system', ADAPTIVE_PROMPT),
    ('human', 'Plan the next step.')
])

def _extract_json(raw: str) -> Dict[str, Any]:
    """LLMs sometimes wrap JSON in markdown fences or add stray text — strip that."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

class Worker(Protocol):
    async def run(self, tasks: List[str]) -> List[Dict[str, Any]]: ...

class ManagerAgent:
    def __init__(self, memory: SessionMemory = None):
        self._data_agent = DataAgent()
        self._policy_agent = PolicyAgent()
        self.memory = memory or SessionMemory()


    async def _parse_intent(self, user_message: str, session_id: str, turn_index: int) -> Dict[str, Any]:
        chain = _intent_prompt | _get_llm() | StrOutputParser()
        raw = await chain.ainvoke({"user_message": user_message})
        print("*"* 80)
        print(raw)
        print("*"* 80)
        result = _extract_json(raw)
        self.memory.log_reasoning_step(
            session_id=session_id,
            turn_index=turn_index,
            step_number=1,
            agent_name="manager",
            step_type="plan",
            description=f"Parsed intent: {result.get('goal', 'unknown')}",
            input_context={"raw_message": user_message},
            output_action={"intent": result}
        )
        return result

    async def _plan_adaptive(self, goal: str, data_facts: List[Dict[str, Any]], session_id: str, turn_index: int) -> Dict[str, Any]:
        chain = _adaptive_prompt | _get_llm() | StrOutputParser()
        raw = await chain.ainvoke({"goal": goal, "data_facts": json.dumps(data_facts, indent=2, default=str)})
        print("*"* 80)
        print(raw)
        print("*"* 80)
        result = _extract_json(raw)
        self.memory.log_reasoning_step(
            session_id=session_id,
            turn_index=turn_index,
            step_number=3,
            agent_name="manager",
            step_type="plan",
            description="Adaptive planning based on data findings",
            input_context={"data_facts": data_facts},
            output_action={"policy_tasks": result.get("policy_tasks", []),
                          "followup_data_tasks": result.get("followup_data_tasks", [])}
        )
        return result

    async def run(self, user_message: str, scenario_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        session_id = self.memory.create_session(
            scenario_id=scenario_id,
            customer_id=customer_id
        )
        turn_index = 0
        
        self.memory.log_message(session_id, turn_index, "user", user_message)
        intent = await self._parse_intent(user_message, session_id, turn_index)
        initial_data_tasks = intent.get("initial_data_tasks", [])

        data_facts = await self._data_agent.run(initial_data_tasks,
            memory=self.memory,
            session_id=session_id,
            turn_index=turn_index)
        adaptive_plan = await self._plan_adaptive(intent.get("goal", ""), data_facts, session_id, turn_index)
        policy_tasks = adaptive_plan.get("policy_tasks", [])
        followup_data_tasks = adaptive_plan.get("followup_data_tasks", [])
        policy_facts, followup_facts = await asyncio.gather(
            self._policy_agent.run(policy_tasks, memory=self.memory,
                session_id=session_id,
                turn_index=turn_index) if policy_tasks else _empty(),
            self._data_agent.run(followup_data_tasks, memory=self.memory,
                session_id=session_id,
                turn_index=turn_index) if followup_data_tasks else _empty(),
        )
        all_data_facts = data_facts + followup_facts
        self.memory.save_research_facts(session_id, 
            data_facts={"facts": all_data_facts},
            policy_facts={"facts": policy_facts}
        )
        

        return {
            "user_message": user_message,
            "intent": intent,
            "data_facts": all_data_facts,
            "policy_facts": policy_facts,
            "session_id": session_id,
        }


async def _empty() -> List[Dict[str, Any]]:
    return []

async def _demo():
    mem = SessionMemory()
    
    user_message = (
        "Hi, I need to wire $500,000 from my investment account to my family "
        "trust at Northern Trust. The request should already be in the system "
        "— REQ_010_1."
    )
    manager = ManagerAgent(memory = mem)
    result = await manager.run(user_message,
    scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING", 
    customer_id="CUST_DIANA_VOSS")
    sid = result["session_id"]
    print(f"\nCreated session: {sid}\n")
    mem.print_trace(sid)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(_demo())




