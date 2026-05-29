import json
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers  import SentenceTransformer, util 

with open("Data_cleaning/FINRA/ontology_output.json", "r") as f:
    main_json = json.load(f)

with open("Data_cleaning/FINRA/entity_index.json", "r") as f:
    metadata_registry = json.load(f)

def build_chunks(main_json, metadata_registry):
    all_chunks = []
    for section in main_json["sections"]:
        section_title = section["title"]

        for item in section["content"]:
            text = item.get("text", "")

            if "sub_items" in item:
                for sub in item["sub_items"]:
                    text += "\n- " + sub.get("text", "")

            if not text.strip():
                continue

            resolved_entities = []
            entity_names = []
            entity_types = []

            for entity in item.get("entities", []):
                entity_id = entity.get("entity_id")
                if entity_id in metadata_registry:
                    resolved = metadata_registry[entity_id]
                    
                    resolved_entities.append({
                        "id": entity_id,
                        "canonical_name": resolved["canonical_name"],
                        "ontology_type": resolved["ontology_type"]
                    })
                    entity_names.append(resolved["canonical_name"])
                    entity_types.append(resolved["ontology_type"])

            if entity_names:
                text += "\n[Entities: " + ", ".join(entity_names) + "]"
            doc = Document(
                page_content=text,
                metadata={
                    "source": "Regulatory Notice 19-18",
                    "section": section_title,
                    "item_number": str(item.get("number", "")),
                    "content_type": item.get("type", "paragraph"),
                    "domain": "AML",
                    "entity_names": ", ".join(entity_names) if entity_names else "",
                    "entity_types": ", ".join(entity_types) if entity_types else "",
                }
            )
            all_chunks.append(doc)
    return all_chunks

all_chunks = build_chunks(main_json, metadata_registry)
print(f"Total chunks created: {len(all_chunks)}")
print("*" * 50)
print("\nCHUNK TEXT")
print(all_chunks[10].page_content)
print("*" * 50)
print("\nCHUNK METADATA")
print(all_chunks[10].metadata)

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
    documents=all_chunks,
    embedding=embedding_fn,
    collection_name="FINRA",
    persist_directory= "./chroma"
)

 
print(f"Persisted {len(all_chunks)} chunks with metadata to ./chroma_db")
print(f"Collection count after load: {vectorstore._collection.count()}")