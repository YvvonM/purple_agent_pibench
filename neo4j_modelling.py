import json 
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv 
from gazetteer_table import REL_KEYS

load_dotenv()
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")


class Neo4jLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)

    
def load_ontology_nodes(loader, ontology):
    print("Creating entity nodes")
    for entity_id, data in ontology.items():
        query = """
            MERGE (n:Entity {
            id: $id,
            name: $name,
            type: $type,
            domain: $domain,
            description: $description
        })
            """
        loader.run(query,
            {
            "id": entity_id,
            "name": data.get("canonical_name", ""),
            "type": data.get("ontology_type", ""),
            "domain": data.get("domain", ""),
            "description": data.get("description", "")
            })

    print(f"{len(ontology)} entities created")

def load_ontology_relationships(loader, ontology):
    print("Creating relationships")
    count = 0
    for entity_id, data in ontology.items():
        for key in REL_KEYS:
            if key not in data:
                continue
            targets = data[key]
            if isinstance(targets, str):
                targets = [targets]
            for target_id in targets:
                valid_prefixes = (
                    "REG_", "ORG_", "REPORT_", "COMP_", "CUST_", "RISK_",
                    "SEC_", "TXN_", "ACCT_", "FIN_", "THR_", "NOTICE_",
                    "PROG_", "PERSON_", "CONTACT_", "DATE_"
                )
                if not any(target_id.startswith(p) for p in valid_prefixes):
                    continue
                query = f"""
                MATCH (a:Entity {{id: $from_id}})
                MATCH (b:Entity {{id: $to_id}})
                MERGE (a)-[:{key.upper()}]->(b)
                """
                try:
                    loader.run(query, {"from_id": entity_id, "to_id": target_id})
                    count += 1
                except Exception:
                    pass 
    print(f"{count} relationships created")


def load_document(loader, enriched, doc_name="Regulatory Notice 19-18"):
    print("Creating document structure")
    query = "CREATE (d:Document {name: $name})"
    loader.run(query, {"name": doc_name})
    chunk_count = 0
    mention_count = 0

    for sec_idx, section in enumerate(enriched.get("sections", [])):
        sec_id = f"{doc_name}_sec_{sec_idx}"
        query = """
        CREATE (s:Section {id: $id, title: $title})
        WITH s
        MATCH (d:Document {name: $doc_name})
        MERGE (d)-[:HAS_SECTION]->(s)
        """
        loader.run(query, {"id": sec_id, "title": section.get("title", ""), "doc_name": doc_name})
        chunk_count += 1

        for ent in section.get("title_entities", []):
            if ent.get("entity_id"):
                query = """
                MATCH (s:Section {id: $sid})
                MATCH (e:Entity {id: $eid})
                MERGE (s)-[:MENTIONS]->(e)
                """
                loader.run(query, {"sid": sec_id, "eid": ent["entity_id"]})
                mention_count += 1

        for item_idx, item in enumerate(section.get("content", [])):
            item_id = f"{sec_id}_item_{item_idx}"
            query = """
            CREATE (i:Item {id: $id, text: $text})
            WITH i
            MATCH (s:Section {id: $sid})
            MERGE (s)-[:HAS_ITEM]->(i)
            """
            loader.run(query, {
                "id": item_id,
                "text": item.get("text", "")[:300],
                "sid": sec_id
            })
            chunk_count +=1

            for ent in item.get("entities", []):
                if ent.get("entity_id"):
                    query = """
                    MATCH (i:Item {id: $iid})
                    MATCH (e:Entity {id: $eid})
                    MERGE (i)-[:MENTIONS]->(e)
                    """
                    loader.run(query, {"iid": item_id, "eid": ent["entity_id"]})
                    mention_count += 1
    
    print(f"{chunk_count} document chunks")
    print(f"{mention_count} mention links")


def main(ontology_link, enriched_link):

    with open(ontology_link, "r", encoding="utf-8") as f:
        ontology = json.load(f)
    with open(enriched_link, "r", encoding="utf-8") as f:
        enriched = json.load(f)
    
    print(f"Connecting to Aura at {URI}")
    loader = Neo4jLoader(URI, USER, PASSWORD)
    
    
    result = loader.run("RETURN 'Connected to Aura!' as msg")
    print(f"{result[0]['msg']}")
    load_ontology_nodes(loader, ontology)
    load_ontology_relationships(loader, ontology)
    load_document(loader, enriched)
    
    
    print("Done!")
    print("*" * 40)
    
    loader.close()


if __name__ == "__main__":
    main("FINRA/ontology_dictionary.json", "FINRA/ontology_output.json")
    
