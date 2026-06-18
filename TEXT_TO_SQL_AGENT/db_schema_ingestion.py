import json 
import os
from typing import Dict, List
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from pathlib import Path
import pickle

SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = Path("FINRA_HYBRID_RAG/chroma")
COLLECTION_NAME = "tables_schema"

with open("data_generation/db_data/AML_schema.json", "r") as f:
    schema = json.load(f)

for s in schema:
    print(s["key_columns"])
    print("*"* 70)

def build_db_schema_documents(schema: List[Dict]) -> List[Document]:
    documents = []
    for s in schema:
        table_name = s['table_name']
        table_category = s["category"]
        table_description = s["purpose"]
        when_to_use = s["when_to_query"]
        columns = s["key_columns"]
        table_relationships = s["relationships"]
        example_queries = s["common_queries"]
        gotchas = s["gotchas"]
        content = f"Table: {table_name}\nCategory: {table_category}\nDescription: {table_description}\nWhen to Use: {when_to_use}\nColumns: {', '.join(columns)}\nRelationships: {table_relationships}"
        metadata = {
            "table_name": table_name,
            "example_queries": example_queries,
            "gotchas": gotchas
        }
        documents.append(Document(page_content=content, metadata=metadata))
    return documents

docs = build_db_schema_documents(schema)
print(f"Total number of docs created: {len(docs)}")

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

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embedding_fn,
    collection_name=COLLECTION_NAME,
    persist_directory=str(DB_PATH)
)

with open(f"{DB_PATH}/title_chunks.pkl", "wb") as f:
    pickle.dump(docs, f)
print(f"Saved {len(docs)} documents to collection '{COLLECTION_NAME}' in {DB_PATH}")
test = vectorstore.similarity_search("customer risk rating", k=3)
print(f"Retrieved {len(test)} documents for query 'customer risk rating':")
for doc in test:
    print(f" - {doc.metadata['table_name']}")


