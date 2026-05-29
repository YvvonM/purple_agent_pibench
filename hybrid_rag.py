from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

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

# Debug: check if collection has data
print(f"Collection count: {vectorstore._collection.count()}")


results = vectorstore.similarity_search(
    "What are the AML reporting requirements?",
    k=5
)
print(f"Unfiltered results: {len(results)}")
for r in results:
    print(f"- {r.metadata.get('section', 'N/A')}: {r.page_content[:500]}...")

results = vectorstore._collection.query(
    query_embeddings=[embedding_fn.embed_query("What are the AML reporting requirements?")],
    n_results=5,
    where_document={"$contains": "FinCEN"}
)
print(f"\nFaciltered results: {len(results)}")