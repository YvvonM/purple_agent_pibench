# entity_cleaner.py
import json
import re
from pathlib import Path

BANNED_PHRASES = {
    "finra aml regulations",
    "high-risk geographic location",
    "suspicious activity reports",
}

BANNED_LABEL_COMBOS = {
    ("V. Potential", "PERSON"),
    ("II", "CARDINAL"),
    ("Offer", "PERSON"),
    ("threat", "CARDINAL"),
}

# Only strip footnotes: word + 1-2 digits (company10) or word.digits (threat.11)
# NOT years (2019), rule numbers (3310), or document IDs (02-21)
FOOTNOTE_PATTERN = re.compile(r'([a-zA-Z]{2,})(\d{1,2})$')
FOOTNOTE_PATTERN2 = re.compile(r'([a-zA-Z]{2,})\.(\d+)$')

def strip_footnote(text: str) -> str:
    """Remove trailing footnote numbers like 'company10' or 'threat.11'."""
    text = FOOTNOTE_PATTERN2.sub(r'\1', text)
    text = FOOTNOTE_PATTERN.sub(r'\1', text)
    return text

def recover_truncated(entity_text: str, source_text: str) -> str:
    """Recover full word if entity was truncated."""
    source_lower = source_text.lower()
    et_lower = entity_text.lower()
    
    idx = source_lower.find(et_lower)
    if idx == -1:
        return entity_text
    
    # Extend to capture complete word/number
    end_idx = idx + len(entity_text)
    
    # If next chars are alphanumeric, we truncated mid-word
    while end_idx < len(source_text) and source_text[end_idx].isalnum():
        entity_text += source_text[end_idx]
        end_idx += 1
    
    # Also capture trailing punctuation that belongs (like ')', ']', etc.)
    if end_idx < len(source_text):
        next_char = source_text[end_idx]
        if next_char in ')]}':
            entity_text += next_char
            end_idx += 1
    
    return entity_text

def is_valid_entity(text: str, label: str, source_text: str) -> bool:
    """Check if entity text actually appears in source and isn't banned."""
    text_lower = text.lower().strip()
    
    # Banned phrase check
    if text_lower in BANNED_PHRASES:
        return False
    
    # Banned label combo check
    if (text, label) in BANNED_LABEL_COMBOS:
        return False
    
    # Must literally appear in source text (case-insensitive)
    if text_lower not in source_text.lower():
        return False
    
    # Length sanity check
    if len(text.strip()) < 3:
        return False
    
    return True

def clean_entities(entities: list, source_text: str) -> list:
    """Filter and clean a list of entities."""
    cleaned = []
    seen = set()
    
    for ent in entities:
        text = ent.get("text", "")
        label = ent.get("label", "")
        
        # First strip footnotes
        text = strip_footnote(text)
        
        # Then recover truncation against source
        text = recover_truncated(text, source_text)
        
        if not is_valid_entity(text, label, source_text):
            continue
        
        # Deduplicate by (text_lower, label)
        key = (text.lower().strip(), label)
        if key in seen:
            continue
        seen.add(key)
        
        cleaned.append({"text": text, "label": label})
    
    return cleaned

def clean_document(doc: dict) -> dict:
    """Recursively clean all entities in a document."""
    
    def clean_item(item, source_text):
        if "entities" in item:
            item["entities"] = clean_entities(item["entities"], source_text)
            # Update entity_sources counts
            if "entity_sources" in item:
                item["entity_sources"]["merged_count"] = len(item["entities"])
        return item
    
    # Clean title entities
    if "title_entities" in doc:
        doc["title_entities"] = clean_entities(doc["title_entities"], doc.get("title", ""))
    
    for section in doc.get("sections", []):
        # Section title
        if "title_entities" in section:
            section["title_entities"] = clean_entities(
                section["title_entities"], section.get("title", "")
            )
        
        # Content items
        for item in section.get("content", []):
            clean_item(item, item.get("text", ""))
            
            # Sub-items
            for sub in item.get("sub_items", []):
                clean_item(sub, sub.get("text", ""))
        
        # Subsections
        for subsec in section.get("subsections", []):
            if "title_entities" in subsec:
                subsec["title_entities"] = clean_entities(
                    subsec["title_entities"], subsec.get("title", "")
                )
            for item in subsec.get("content", []):
                clean_item(item, item.get("text", ""))
                for sub in item.get("sub_items", []):
                    clean_item(sub, sub.get("text", ""))
    
    return doc


def main(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    
    cleaned = clean_document(doc)
    
    def count_entities(d):
        total = 0
        for section in d.get("sections", []):
            for item in section.get("content", []):
                total += len(item.get("entities", []))
                for sub in item.get("sub_items", []):
                    total += len(sub.get("entities", []))
        return total
    
    print(f"Entities cleaned. Output saved to {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(
        input_path="FINRA/policy_hybrid_entities.json",
        output_path="FINRA/policy_cleaned_entities.json"
    )