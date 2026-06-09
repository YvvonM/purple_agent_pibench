
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

print(f"Connecting to: {URI}")
print(f"Username: {USERNAME}")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

try:
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        print("Connection successful!")
        print(f"Test result: {result.single()['test']}")
        
        
        result = session.run("CALL db.labels() YIELD label RETURN collect(label) AS labels")
        labels = result.single()["labels"]
        print(f"\nLabels: {labels}")
        
        result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS types")
        types = result.single()["types"]
        print(f"Relationships: {types}")
        
        
        result = session.run("MATCH (n) RETURN n LIMIT 1")
        for record in result:
            node = record["n"]
            print(f"\nSample node: {dict(node)}")
            print(f"Labels: {list(node.labels)}")

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.close()