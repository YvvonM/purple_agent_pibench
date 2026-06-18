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

        print("\n=== ALL ENTITIES ===")
        result = session.run("""
            MATCH (e:Entity) 
            RETURN e.id, e.name, e.type 
            ORDER BY e.id
        """)
        for r in result:
            print(f"  {r['e.id']:15} | {r['e.type']:25} | {r['e.name']}")
        
        
        print("\n=== DOCUMENTS ===")
        result = session.run("""
            MATCH (d:Document) 
            RETURN d.id, d.name, d.title
        """)
        for r in result:
            print(f"  {dict(r)}")
        
        
        print("\n=== RELATIONSHIP COUNTS ===")
        result = session.run("""
            MATCH ()-[r]->() 
            RETURN type(r) AS rel, count(r) AS cnt 
            ORDER BY cnt DESC
        """)
        for r in result:
            print(f"  {r['rel']:30} | {r['cnt']}")
        
        
        print("\n=== SAMPLE RELATIONSHIPS (20) ===")
        result = session.run("""
            MATCH (a:Entity)-[r]->(b:Entity)
            RETURN a.id, a.name, type(r) AS rel, b.id, b.name
            LIMIT 20
        """)
        for r in result:
            print(f"  {r['a.id']:12} ({r['a.name'][:20]:20}) "
                f"--[{r['rel']:20}]--> "
                f"{r['b.id']:12} ({r['b.name'][:20]})")
        
        
        print("\n=== NOTICE NODES ===")
        result = session.run("""
            MATCH (n) 
            WHERE n.name CONTAINS 'Notice' OR n.name CONTAINS 'notice'
            RETURN labels(n) AS labels, n.id, n.name
        """)
        for r in result:
            print(f"  {r}")

        
        test_ids = ['NOTICE_001', 'NOTICE_002', 'REG_001', 'REG_002', 
                    'ORG_001', 'ORG_003', 'PROG_001', 'PROG_002']
        print("\n=== ID EXISTENCE CHECK ===")
        result = session.run("""
            MATCH (e:Entity)
            WHERE e.id IN $ids
            RETURN e.id, e.name
        """, ids=test_ids)
        found = {r['e.id'] for r in result}
        for id in test_ids:
            status = "✓ EXISTS" if id in found else "✗ MISSING"
            print(f"  {status} | {id}")
        session.run("""
        MATCH (n:Entity {id: 'NOTICE_001'})
        MATCH (org:Entity {id: 'ORG_001'})
        MATCH (date:Entity {id: 'DATE_001'})
        MATCH (reg:Entity {id: 'REG_002'})
        MATCH (notice2:Entity {id: 'NOTICE_002'})
        
        MERGE (org)-[:ISSUES]->(n)
        MERGE (n)-[:DATE]->(date)
        MERGE (n)-[:PROVIDES_GUIDANCE_ON]->(reg)
        MERGE (n)-[:INCORPORATED_INTO]->(notice2)
    """)
    print("NOTICE_001 relationships created")
except Exception as e:
    print(f"Error: {e}")

finally:
    driver.close()