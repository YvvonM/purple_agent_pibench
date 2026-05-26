import json 
import re 
from pathlib import Path

PATTERNS = {
    "finra_rule": r"\bFINRA Rule\s\d+(?:\([a-z]\))?\b",
    "sec_rule": r"\bSEC Rule\s[\w\-]+\b",
    "notice": r"\b(?:Notice to Members|NTM)\s\d{2}-\d{2}\b",
    "regulatory_notice": r"\bRegulatory Notice\s\d{2}-\d{2}\b",
    "money": r"\$\d[\d,]*(?:\.\d+)?",
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "phone": r"\(\d{3}\)\s\d{3}-\d{4}",
    "cfr_citation": r"\b\d+\s+CFR\s+[\d.]+\b",
    "usc_citation": r"\b\d+\s+U\.S\.C\.\s*\d+\b",
    "date": r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
}

def extract_entities(text: str):
    entities = []
    for entity_type, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            entities.append({
                "type": entity_type,
                "value": match.group(),
                "start": match.start(),
                "end": match.end()
            })
    return sorted(entities, key=lambda x: x["start"])

def process_document(doc):
    if "title" in doc:
        entities = extract_entities(doc["title"])
        if entities:
            doc["title_entities"] = entities

    for section in doc.get("sections", []):
        if "title" in section:
            entities = extract_entities(section["title"])
            if entities:
                section["title_entities"] = entities

        for item in section.get("content", []):
            text = item.get("text", "")
            if text:
                entities = extract_entities(text)
                if entities:
                    item["entities"] = entities

        for sub in item.get("sub_items", []):
                sub_text = sub.get("text", "")
                if sub_text:
                    entities = extract_entities(sub_text)
                    if entities:
                        sub["entities"] = entities

    for subsec in section.get("subsections", []):
        if "title" in subsec:
            entities = extract_entities(subsec["title"])
            if entities:
                subsec["title_entities"] = entities
        for item in subsec.get("content", []):
                text = item.get("text", "")
                if text:
                    entities = extract_entities(text)
                    if entities:
                        item["entities"] = entities
    return doc


def main(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    
    enriched_doc = process_document(doc)

    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_doc, f, indent=2)

    print(f"Saved enriched file -> {output_path}")

if __name__ =="__main__":
    main("FINRA/policy.json", "FINRA/deterministic_entities.json")


    