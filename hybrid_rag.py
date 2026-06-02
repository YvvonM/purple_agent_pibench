import os
import pickle
from langchain_chroma import Chroma
from dotenv import load_dotenv
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
load_dotenv()

VDB_API_KEY = os.getenv("GROQ_API_KEY")
with open("./chroma/bm25_chunks.pkl", "rb") as f:
    all_chunks = pickle.load(f)

class BGEEmbeddings(Embeddings):
    def __init__(self, model_name="BAAI/bge-large-en-v1.5"):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True
        ).tolist()
    
    def embed_query(self, text):
        return self.model.encode(
            "Represent this sentence for searching relevant passages: " + text,
            normalize_embeddings=True
        ).tolist()



embedding_fn = BGEEmbeddings()

vectorstore = Chroma(
        persist_directory="./chroma",
        embedding_function=embedding_fn,
        collection_name="FINRA" 
    )


print(f"Collection count: {vectorstore._collection.count()}")


def make_prediction(query: str):
    sim_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5})

    bm25_retriever = BM25Retriever.from_documents(all_chunks, k = 5)

    ensemble_retriever = EnsembleRetriever(
        retrievers= [bm25_retriever, sim_retriever],
        weights=[0.6, 0.4]
    )

    reranker = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
    reranker_compressor = CrossEncoderReranker(model= reranker, top_n = 5)
    final_retriever = ContextualCompressionRetriever(
        base_retriever = ensemble_retriever,
        base_compressor=reranker_compressor
    )


    llm = ChatGroq(
        model = "qwen/qwen3-32b",
        api_key = VDB_API_KEY,
        temperature = 0.1
    )

    prompt = ChatPromptTemplate.from_messages(
        [("system", VECTOR_DB_RETRIEVER_PROMPT),
        ("human", "{question}")]
    )

    def format_context(docs):
        chunks = []
        for i, doc in enumerate(docs):
            chunk = (
                f"[Rank {i+1} | Section: {doc.metadata.get('section', 'N/A')} | "
                f"Item: {doc.metadata.get('item_number', 'N/A')}]\n"
                f"Entities: {doc.metadata.get('entity_names', 'N/A')}\n"
                f"{doc.page_content}"
            )
            chunks.append(chunk)
        return "\n\n".join(chunks)

    rag_chain = (
        {"context": final_retriever | format_context,
        "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    response = rag_chain.invoke(query)
    return response
  
if __name__ == "__main__":
    query = "What is the title of FINRA Regulatory Notice 19-18?"
    answer = make_prediction(query)
    print(answer)