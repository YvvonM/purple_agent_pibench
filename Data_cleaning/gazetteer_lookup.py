import json
from gazetteer_table import GAZETTEER
import re 
from collections import defaultdict
from pathlib import Path

GAZETTEER_PATTERNS = []

for canonical, (label, variants) in GAZETTEER.items():
    for variant in variants:
        escaped = re.escape(variant).replace(r'\ ', r'\s+')
        pattern = r'\b' + escaped + r'\b'
        GAZETTEER_PATTERNS.append((
            re.compile(pattern, re.IGNORECASE),
            label,
            canonical
        ))
GAZETTEER_PATTERNS.sort(key=lambda x: -len(x[2]))

def extract_gazetteer_entities(text):
    entities = []
    for pattern, label, canonical in GAZETTEER_PATTERNS:
        for match in pattern.finditer(text):
            entities.append({
                "type": label,
                "value": match.group(),
                "start": match.start(),
                "end": match.end(),
                "canonical": canonical
            })
    return entities

def resolve_overlap(entities):
    entities = sorted(entities, key=lambda e: (e["start"], -(e["end"] - e["start"])))
    resolved = []
    for ent in entities:
        overlap = False
        for existing in resolved:
            if not (ent["end"] <= existing["start"] or ent["start"] >= existing["end"]):
                overlap = True
                break
        if not overlap:
            resolved.append(ent)
    return sorted(resolved, key=lambda e: e["start"])

def merge_entities(regex_entities, gazetteer_entities):
    for ent in regex_entities:
        ent["source"] = "regex"

    for ent in gazetteer_entities:
        ent["source"] = "gazetteer"
    all_entities = regex_entities + gazetteer_entities
    all_entities = sorted(all_entities, key=lambda e: (
        e["start"],
        -(e["end"] - e["start"]),  
        0 if e.get("source") == "regex" else 1  
    ))

    resolved = []
    for ent in all_entities:
        overlap = False
        for existing in resolved:
            if not (ent["end"] <= existing["start"] or ent["start"] >= existing["end"]):
                overlap = True
                break
        if not overlap:
            resolved.append(ent)

    final = []
    for ent in sorted(resolved, key=lambda e: e["start"]):
        clean = {
            "type": ent["type"],
            "value": ent["value"],
            "canonical": ent.get("canonical", ent["value"]),
            "start": ent["start"],
            "end": ent["end"]
        }
        final.append(clean)

    return final


def process_document(doc):
    """Add gazetteer entities to all text blocks that already have regex entities."""

    def process_text_block(text, existing_entities):
        """Extract gazetteer entities and merge with existing regex ones."""
        gazetteer_entities = extract_gazetteer_entities(text)
        merged = merge_entities(existing_entities, gazetteer_entities)
        return merged

    # Document title
    if "title" in doc:
        existing = doc.get("title_entities", [])
        merged = process_text_block(doc["title"], existing)
        if merged:
            doc["title_entities"] = merged

    # Sections
    for section in doc.get("sections", []):
        # Section title
        if "title" in section:
            existing = section.get("title_entities", [])
            merged = process_text_block(section["title"], existing)
            if merged:
                section["title_entities"] = merged

        # Content items
        for item in section.get("content", []):
            text = item.get("text", "")
            if text:
                existing = item.get("entities", [])
                merged = process_text_block(text, existing)
                if merged:
                    item["entities"] = merged

            # Sub-items
            for sub in item.get("sub_items", []):
                sub_text = sub.get("text", "")
                if sub_text:
                    existing = sub.get("entities", [])
                    merged = process_text_block(sub_text, existing)
                    if merged:
                        sub["entities"] = merged

        # Subsections
        for subsec in section.get("subsections", []):
            if "title" in subsec:
                existing = subsec.get("title_entities", [])
                merged = process_text_block(subsec["title"], existing)
                if merged:
                    subsec["title_entities"] = merged

            for item in subsec.get("content", []):
                text = item.get("text", "")
                if text:
                    existing = item.get("entities", [])
                    merged = process_text_block(text, existing)
                    if merged:
                        item["entities"] = merged

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
    main("FINRA/deterministic_entities.json", "FINRA/gazetteer_entities.json")

