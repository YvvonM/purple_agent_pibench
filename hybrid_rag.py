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
query = "What obligations does FINRA Rule 3310 impose on broker-dealers for AML compliance?"

top_docs = final_retriever.invoke(query)

for i, doc in enumerate(top_docs):
    print(f"\n{'='*60}")
    print(f"Rank {i+1} | Section: {doc.metadata.get('section')}")
    print(f"Entities : {doc.metadata.get('entity_names')}")
    print(f"Content  :\n{doc.page_content}")