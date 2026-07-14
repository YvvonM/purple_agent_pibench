import os 
import json 
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import StrOutputParser
import sys 
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "session_db"))
from typing import Any, Optional, Dict, List
from memory import SessionMemory
from manager_agent import ManagerAgent
import asyncio
from prompt import CONVERSATION_SYSTEM_PROMPT

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

class ConversationAgent:
    def __init__(self, memory: Optional[SessionMemory] = None):
        self.memory = memory or SessionMemory()
        self._prompt = ChatPromptTemplate.from_messages([
            ('system', CONVERSATION_SYSTEM_PROMPT),
            ('human', "{context}\n\nUser: {user_message}\n\nAssistant:")
        ])

    async def respond(self, user_message: str, session_id: str, turn_index: int,
        data_facts: Optional[List[Dict]] = None, policy_facts: Optional[List[Dict]] = None, decision: Optional[str] = None, rationale: Optional[str] = None,):

        context_parts = []
        messages = self.memory.get_messages(session_id)
        if messages:
            history = []
            for m in messages:
                role ='User' if m['role'] == 'user' else 'Assistant'
                history.append(f'{role}: {m['text'][:500]}')
            context_parts.append("conversation history \n" +"\n".join(history[-6:]))

        if data_facts:
            facts_summary = []
            for f in data_facts:
                if f.get("error"):
                    facts_summary.append(f"- Task '{f['task']}': Error - {f['error']}")

                elif f.get("results"):
                    results = f["results"]
                    if isinstance(results, list) and len(results) > 0:
                        first = results[0]
                        if isinstance(first, dict):
                            summary = "\n".join(f"{k}={v}" for k, v in list(first.items())[:5])
                            facts_summary.append(f"- {f['task']}: Found {f.get('row_count', 0)} records. Key: {summary}")

                        else: 
                            facts_summary.append(f"- {f['task']}: {str(results)[:200]}")

                    else:
                        facts_summary.append(f"- {f['task']}: {str(results)[:200]}")

                else:
                    facts_summary.append(f"- {f['task']}: No results")

            context_parts.append("## Data Findings\n" + "\n".join(facts_summary))

        if policy_facts:
            policy_summary = []
            for p in policy_facts:
                answer = p.get("answer", "No answer")
                policy_summary.append(f"- {p['task']}: {answer[:300]}")

            context_parts.append("## Policy Findings\n" + "\n".join(policy_summary))

        if decision:
            context_parts.append(f"## System Decision \nDecision: {decision}")
            if rationale:
                context_parts.append(f"Rationale: {rationale}")

        context = "\n\n".join(context_parts) if context_parts else "No additional information available."
        self.memory.log_reasoning_step(
            session_id=session_id,
            turn_index=turn_index,
            step_number=50,
            agent_name="conversation",
            step_type="respond",
            description=f"Generating response for turn {turn_index}",
            input_context={"user_message": user_message},
            output_action={"context_length": len(context)},
        )
        chain = self._prompt | _get_llm() | StrOutputParser()
        response = await chain.ainvoke({
            "context": context,
            "user_message": user_message
        })

        self.memory.log_message(session_id, turn_index, "assistant", response)

        return response.strip()

class Orchestrator:
    def __init__(self, memory: Optional[SessionMemory] = None):
        self.memory = memory or SessionMemory()
        self.manager = ManagerAgent(memory=self.memory)
        self.conversation = ConversationAgent(memory=self.memory)

    async def start_conversation(self, scenario_id: str = None, customer_id: str = None) -> str:
        session_id = self.memory.create_session(
            scenario_id=scenario_id,
            customer_id=customer_id,
        )
        return session_id


    async def handle_turn(self, user_message:str, session_id: str, scenario_id:str = None, customer_id:str = None) -> Dict[str, Any]:
        if scenario_id is None or customer_id is None:
            session_meta = self.memory.get_session(session_id)
            scenario_id = scenario_id or session_meta.get("scenario_id")
            customer_id = customer_id or session_meta.get("customer_id")
        turn_index = self.memory.get_next_turn_index(session_id)
        self.memory.log_message(session_id, turn_index, "user", user_message)
        research = await self.manager.run(
            user_message=user_message,
            scenario_id=scenario_id,
            customer_id=customer_id,
            turn_index=turn_index
        )

        response = await self.conversation.respond(
            user_message=user_message,
            session_id=session_id,
            turn_index=turn_index,
            data_facts=research.get("data_facts"),
            policy_facts=research.get("policy_facts"),
        )

        return {
            "session_id": session_id,
            "turn_index": turn_index,
            "response": response,
            "research": research,
        }

async def _demo_multi_turn():
    mem = SessionMemory()
    orchestrator = Orchestrator(memory=mem)


    session_id = await orchestrator.start_conversation(
        scenario_id="SCEN_010_LOCKUP_DENIAL_GROUNDING",
        customer_id="CUST_DIANA_VOSS",
    )

    print(f"Started session: {session_id}\n")

    
    msg1 = (
        "Hi, I need to wire $500,000 from my investment account to my family "
        "trust at Northern Trust. The request should already be in the system "
        "— REQ_010_1."
    )
    result1 = await orchestrator.handle_turn(msg1, session_id)
    print(f"Turn 0:\nUser: {msg1}\nAssistant: {result1['response']}\n")

    
    msg2 = "Why was my request denied? Can you explain the lock-up period?"
    result2 = await orchestrator.handle_turn(msg2, session_id)
    print(f"Turn 1:\nUser: {msg2}\nAssistant: {result2['response']}\n")

    
    msg3 = "When will the lock-up end? Can I schedule the transfer for then?"
    result3 = await orchestrator.handle_turn(msg3, session_id)
    print(f"Turn 2:\nUser: {msg3}\nAssistant: {result3['response']}\n")

    print("=" * 70)
    print("FULL TRACE:")
    mem.print_trace(session_id)


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo_multi_turn())
