import json
import os
import sys
import traceback
from dotenv import load_dotenv
from pathlib import Path
from google import genai
from google.genai import types

load_dotenv()
NER_KEY = os.getenv("NER_API")
if not NER_KEY:
    raise ValueError("API key missing!")

client = genai.Client(api_key=NER_KEY)

FINRA_ENTITY_TYPES = [
    "REGULATION", "REPORT_TYPE", "THRESHOLD", "CUSTOMER_TYPE",
    "RISK_FACTOR", "TRANSACTION_TYPE", "ACCOUNT_STATUS",
    "COMPLIANCE_ACTION", "SECURITY_TYPE", "DOCUMENT_TYPE",
]

def llm_extract_entities(text: str, section_context: str = "") -> list:
    if not text or len(text.strip()) < 10:
        return []
    prompt = f"""You are a financial compliance expert specializing in FINRA AML regulations.
Extract domain-specific entities from this text:
"{text}"
Section context: {section_context}
Extract ONLY these entity types:
- REGULATION: Specific rules, laws, regulations
- REPORT_TYPE: Types of reports firms must file
- THRESHOLD: Monetary amounts, time periods, numerical thresholds
- CUSTOMER_TYPE: Types of customers or entities
- RISK_FACTOR: Risk indicators or geographic concerns
- TRANSACTION_TYPE: Types of transactions or patterns
- ACCOUNT_STATUS: Account conditions
- COMPLIANCE_ACTION: Required compliance actions
- SECURITY_TYPE: Types of securities
- DOCUMENT_TYPE: Regulatory documents
Return ONLY a JSON array. Example:
[
  {{"text": "FINRA Rule 3310", "label": "REGULATION"}},
  {{"text": "$5,000", "label": "THRESHOLD"}}
]
If no entities match, return []."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        entities = json.loads(response.text)
        return entities if isinstance(entities, list) else []
    except Exception as e:
        print(f"  LLM ERROR [{type(e).__name__}]: {str(e)[:150]}", flush=True)
        traceback.print_exc()
        return []

def merge_entities(spacy_entities: list, llm_entities: list) -> list:
    merged = {}
    for ent in spacy_entities:
        key = ent['text'].lower().strip()
        merged[key] = ent
    for ent in llm_entities:
        key = ent['text'].lower().strip()
        if ent['label'] in FINRA_ENTITY_TYPES:
            merged[key] = ent
    return list(merged.values())

def collect_all_text_items(doc):
    items = []
    if doc.get("title"):
        items.append((doc, "title_entities", doc["title"], "document title", False))
    for section in doc.get("sections", []):
        section_title = section.get("title", "")
        if section_title:
            items.append((section, "title_entities", section_title, "section title", False))
        for item in section.get("content", []):
            if "text" in item:
                items.append((item, "entities", item["text"], section_title, False))
            for sub in item.get("sub_items", []):
                if "text" in sub:
                    items.append((sub, "entities", sub["text"], section_title, True))
        for sub in section.get("subsections", []):
            if sub.get("title"):
                items.append((sub, "title_entities", sub["title"], "subsection title", False))
            for item in sub.get("content", []):
                if "text" in item:
                    items.append((item, "entities", item["text"], section_title, False))
                for sub_item in item.get("sub_items", []):
                    if "text" in sub_item:
                        items.append((sub_item, "entities", sub_item["text"], section_title, True))
    return items

def process_batch(batch):
    results = []
    for target_dict, field_name, text, context, is_subitem in batch:
        spacy_ents = target_dict.get(field_name, [])
        llm_ents = llm_extract_entities(text, context)
        merged = merge_entities(spacy_ents, llm_ents)
        results.append((target_dict, field_name, merged, len(spacy_ents), len(llm_ents)))
    return results

def process_json_document_batched(doc, batch_size=5):
    all_items = collect_all_text_items(doc)
    total = len(all_items)
    print(f"Total items to process: {total}", flush=True)
    processed = 0
    for i in range(0, total, batch_size):
        batch = all_items[i:i + batch_size]
        print(f"Batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}...", flush=True)
        results = process_batch(batch)
        for target_dict, field_name, merged, spacy_count, llm_count in results:
            target_dict[field_name] = merged
            if field_name == "entities":
                target_dict["entity_sources"] = {
                    "spacy_count": spacy_count,
                    "llm_count": llm_count,
                    "merged_count": len(merged)
                }
        processed += len(batch)
        print(f"  Processed {processed}/{total}", flush=True)
    return doc

def main(input_path, output_path, batch_size=10):
    print("DEBUG: Starting main()", flush=True)
    input_path = Path(input_path)
    output_path = Path(output_path)
    print(f"DEBUG: Input exists? {input_path.exists()}", flush=True)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path.absolute()}", flush=True)
        sys.exit(1)
    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    print(f"DEBUG: Loaded '{doc.get('title')}' with {len(doc.get('sections', []))} sections", flush=True)
    enriched_doc = process_json_document_batched(doc, batch_size)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_doc, f, indent=2, ensure_ascii=False)
    print(f"\nDONE: Saved to {output_path}", flush=True)

if __name__ == "__main__":
    print("DEBUG: Script started", flush=True)
    main(
        input_path="FINRA/policy_spacy_entities.json",
        output_path="FINRA/policy_hybrid_entities.json",
        batch_size=10
    )
