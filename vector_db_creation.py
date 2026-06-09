import json
import re
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
import pickle

with open("Data_cleaning/FINRA/ontology_output.json", "r") as f:
    main_json = json.load(f)

with open("Data_cleaning/FINRA/entity_index.json", "r") as f:
    metadata_registry = json.load(f)


def build_chunks(main_json, metadata_registry):
    all_chunks = []
    doc_title = main_json.get("title", "")
    
    # --- Document title as its own chunk ---
    if doc_title:
        all_chunks.append(Document(
            page_content=doc_title,
            metadata={
                "source": doc_title,
                "section": "Document Title",
                "item_number": "",
                "content_type": "title",
                "domain": "AML",
                "entity_names": "",
                "entity_types": "",
                "entity_ids": "",
                "resolved_entities_json": "",
            }
        ))
    
    for section in main_json["sections"]:
        section_title = section["title"]

        # --- Section title as a chunk ---
        if section_title:
            all_chunks.append(Document(
                page_content=f"Section: {section_title}",
                metadata={
                    "source": doc_title,
                    "section": section_title,
                    "item_number": "",
                    "content_type": "section_title",
                    "domain": "AML",
                    "entity_names": "",
                    "entity_types": "",
                    "entity_ids": "",
                    "resolved_entities_json": "",
                }
            ))

        for item in section["content"]:
            clean_text = item.get("text", "")
            if "sub_items" in item:
                for sub in item["sub_items"]:
                    clean_text += "\n- " + sub.get("text", "")
            
            if not clean_text.strip():
                continue

            full_text = f"[{section_title}] {clean_text.strip()}" if section_title else clean_text.strip()

            # --- ENTITY RESOLUTION (this was missing!) ---
            entity_names = []
            entity_types = []
            entity_ids = []
            
            for entity in item.get("entities", []):
                entity_id = entity.get("entity_id")
                if entity_id in metadata_registry:
                    resolved = metadata_registry[entity_id]
                    entity_ids.append(entity_id)
                    entity_names.append(resolved["canonical_name"])
                    entity_types.append(resolved["ontology_type"])
            
            resolved_entities_json = json.dumps([
                {
                    "id": eid,
                    "canonical_name": name,
                    "ontology_type": etype
                }
                for eid, name, etype in zip(entity_ids, entity_names, entity_types)
            ]) if entity_ids else ""

            doc = Document(
                page_content=full_text,
                metadata={
                    "source": doc_title,
                    "section": section_title,
                    "item_number": str(item.get("number", "")),
                    "content_type": item.get("type", "paragraph"),
                    "domain": "AML",
                    "entity_names": ", ".join(entity_names) if entity_names else "",
                    "entity_types": ", ".join(entity_types) if entity_types else "",
                    "entity_ids": ", ".join(entity_ids) if entity_ids else "",
                    "resolved_entities_json": resolved_entities_json,
                }
            )
            all_chunks.append(doc)
    
    return all_chunks
all_chunks = build_chunks(main_json, metadata_registry)
print(f"Total chunks created: {len(all_chunks)}")


sample = all_chunks[10]
print("*" * 50)
print("\nCHUNK TEXT (CLEAN)")
print(sample.page_content)
print("*" * 50)
print("\nCHUNK METADATA")
print(sample.metadata)


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
    persist_directory="./chroma"
)

with open("./chroma/bm25_chunks.pkl", "wb") as f:
    pickle.dump(all_chunks, f)

print(f"Persisted {len(all_chunks)} chunks with metadata to ./chroma")
print(f"Collection count after load: {vectorstore._collection.count()}")
