import os
import asyncio
import pickle
import time
import json
from typing import List, Tuple
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
from prompts import VECTOR_DB_RETRIEVER_PROMPT
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

from cypher_rag import (
    neo4j_mcp_server,
    generate_cypher,
    execute_cypher,
    format_graph_results,
    get_entity_expansion,
)
from mcp import ClientSession
from mcp.client.stdio import stdio_client

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

vectorstore = Chroma(
    persist_directory="./chroma",
    embedding_function=embedding_fn,
    collection_name="FINRA",
)

with open("./chroma/bm25_chunks.pkl", "rb") as f:
    all_chunks = pickle.load(f)

print(f"Collection count: {vectorstore._collection.count()}")



def extract_entity_ids(docs: List[Document]) -> List[str]:
    ids = []
    for doc in docs:
        eids = doc.metadata.get("entity_ids", "")
        if eids:
            ids.extend([e.strip() for e in eids.split(",") if e.strip()])
    return list(set(ids))


def format_context(docs: List[Document], graph_text: str = "") -> str:
    chunks = []
    for i, doc in enumerate(docs):
        section = doc.metadata.get("section", "N/A")
        chunks.append(f"[Rank {i+1} | Section: {section}]\n{doc.page_content}")
    result = "\n\n".join(chunks)
    if graph_text:
        result = f"{result}\n\n{graph_text}"
    return result


async def make_prediction_async(query: str) -> Tuple[str, List[str], str]:
    """Hybrid RAG: Ensemble + Reranker + Graph (via MCP). Uses rotated API key."""

    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    
    api_key = rotator.get_and_advance()
    print(f"[KeyRotator] Using key: ...{api_key[-6:]}")

    sim_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 20},
    )
    bm25_retriever = BM25Retriever.from_documents(all_chunks, k=20)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, sim_retriever],
        weights=[0.6, 0.4],
    )
    reranker = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
    reranker_compressor = CrossEncoderReranker(model=reranker, top_n=5)
    final_retriever = ContextualCompressionRetriever(
        base_retriever=ensemble_retriever,
        base_compressor=reranker_compressor,
    )

    print("\nRetrieving documents...")
    docs = final_retriever.invoke(query)
    print(f"Retrieved {len(docs)} documents after reranking")

    entity_ids = extract_entity_ids(docs)
    print(f"   Entities found: {entity_ids[:5]}")

    graph_context = ""
    if entity_ids:
        print("\nConnecting to Neo4j Aura via MCP...")
        try:
            async with stdio_client(neo4j_mcp_server) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("Generating Cypher...")
                    try:
                        cypher = await generate_cypher(session, query, entity_ids)
                        records = await execute_cypher(session, cypher)
                        graph_context = format_graph_results(records)
                        if graph_context:
                            print(f"Graph: {len(records)} records")
                    except Exception as e:
                        print(f"Cypher failed: {e}")
                        print("Falling back to entity expansion...")
                        graph_context = await get_entity_expansion(session, entity_ids)
                        if graph_context:
                            print("Graph: fallback expansion")
        except Exception as e:
            print(f"MCP connection failed: {e}")
            graph_context = ""

    context_string = format_context(docs, graph_context)

    llm = ChatGroq(
        model="qwen/qwen3-32b",
        api_key=api_key,
        temperature=0.1,
        reasoning_format="hidden",
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", VECTOR_DB_RETRIEVER_PROMPT),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": lambda _: context_string,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    print("\nGenerating answer...")
    response = await rag_chain.ainvoke(query)

    return response, [d.page_content for d in docs], context_string


def make_prediction(query: str) -> Tuple[str, List[str], str]:
    return asyncio.run(make_prediction_async(query))



if __name__ == "__main__":
    with open("Data_cleaning/evaluation_dataset/goldens.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    answers = []
    for d in data:
        query = d["input"]
        rag_answer, retrieved_context, full_context = make_prediction(query)
        result = {
            "query": query,
            "answer": rag_answer,
            "retrieved_context": retrieved_context,
            "full_context": full_context,
        }
        answers.append(result)

        print(f"QUERY: {query}")
        print(f"ANSWER: {rag_answer}")
        print(f"\n{'*'*50}")
        print("RETRIEVED DOCUMENTS:")
        for ctx in retrieved_context:
            print(ctx[:200] + "...")
            print("-" * 30)

        with open("Data_cleaning/evaluation_dataset/rag_answers.json", "w", encoding="utf-8") as f:
            json.dump(answers, f)

        time.sleep(20)

    print(f"All done! {len(answers)} answers saved to rag_answers.json")