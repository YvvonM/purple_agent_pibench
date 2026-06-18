import os 
import asyncio 
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from langchain_community.retrievers.bm25 import BM25Retriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path
from typing import List, Tuple
import pickle
from prompts import SQL_GENERATION_PROMPT
from sqlite_connection import execute_sql, extract_sql

load_dotenv()

SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = Path("FINRA_HYBRID_RAG/chroma")
COLLECTION_NAME = "tables_schema"

with open("FINRA_HYBRID_RAG/chroma/title_chunks.pkl", "rb") as f:
    docs = pickle.load(f)

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

class BGEEmbeddings(Embeddings):
    def __init__(self, model_name="BAAI/bge-large-en-v1.5"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        return self.model.encode(
            "Represent this sentence for searching relevant passages: " + text,
            normalize_embeddings=True,
        ).tolist()


embedding_fn = BGEEmbeddings()
llm = ChatGroq(
    model="qwen/qwen3-32b",
    api_key=rotator.get_and_advance(),
    temperature=0.0,
    reasoning_format="hidden",)

vectorstore = Chroma(
    persist_directory = str(DB_PATH),
    embedding_function=embedding_fn,
    collection_name=COLLECTION_NAME
)

def format_context(docs: List[Document]) -> str:
    chunks = []
    for i, doc in enumerate(docs):
        section = doc.metadata.get("section", "N/A")
        chunks.append(f"[Rank {i+1} | Section: {section}]\n{doc.page_content}")
    result = "\n\n".join(chunks)
    return result

_bm25_retriever = BM25Retriever.from_documents(docs, k=10)

_reranker = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
_reranker_compressor = CrossEncoderReranker(model=_reranker, top_n=5)

_sim_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10}
    )
_ensemble_retriever = EnsembleRetriever(
        retrievers=[_bm25_retriever, _sim_retriever],
        weights=[0.6, 0.4],
    )
_final_retriever = ContextualCompressionRetriever(
        base_retriever=_ensemble_retriever,
        base_compressor=_reranker_compressor,
    )
    
_prompt = ChatPromptTemplate.from_messages(
        [("system", SQL_GENERATION_PROMPT),
        ("human", "{question}"),
        ])
    
async def retrieve_relevant_tables(query: str) -> List[Document]:
    answer = await _final_retriever.ainvoke(query)
    formatted_answer = format_context(answer)

    rag_chain = (
    {
        "formatted_answer": lambda _: formatted_answer,  # fix here
        "question": RunnablePassthrough(),
    }
    | _prompt
    | llm
    | StrOutputParser()
)
    print("\nGenerating answer...")
    response = await rag_chain.ainvoke(query)

    return response

def generate_sql(query: str) -> str:
    return asyncio.run(retrieve_relevant_tables(query))

def main(query: str):
    sql_query = generate_sql(query)
    print("*"* 80)
    print("Generated SQL Query:")
    print(sql_query)
    sql_query = extract_sql(sql_query)
    execution_result = execute_sql(sql_query)
    print("*"*80)
    print("\nExecution Result:")
    print(execution_result)
    return {
        "question": query,
        "sql": sql_query,
        "results": execution_result['results'],
    }

if __name__ == "__main__":
    test_query = "Has customer CUST_DIANA_VOSS had any wire transfers over $10,000 in the last 30 days?"
    test_query1 = "Show me the 5 most recent transactions for customer CUST_DIANA_VOSS"
    sql_query = main(test_query1)
    print("answer:", sql_query)
    
