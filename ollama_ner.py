import json 
import os 
import sys 
import time 
import traceback 
from pathlib import Path 
from dotenv import load_dotenv
from openai import OpenAI
from connection_checker import check_connection, log_connection_status

load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")

CONN_INFO = check_connection(OLLAMA_HOST)
log_connection_status(CONN_INFO)

client = OpenAI(
    base_url=f"{OLLAMA_HOST}/v1",
    api_key=OLLAMA_TOKEN
)

FINRA_ENTITY_TYPES = [
    "REGULATION", "REPORT_TYPE", "THRESHOLD", "CUSTOMER_TYPE",
    "RISK_FACTOR", "TRANSACTION_TYPE", "ACCOUNT_STATUS",
    "COMPLIANCE_ACTION", "SECURITY_TYPE", "DOCUMENT_TYPE",
]

def llm_extract_entities(text: str, section_context: str = "") -> list:
    print("started extraction")
    if not text or len(text.strip()) < 10:
        return []
    if not CONN_INFO["reachable"]:
        print("WARNING: Ollama was unreachable at startup. Retrying...", flush=True)
        fresh = check_connection(OLLAMA_HOST)
        log_connection_status(fresh)
        if not fresh["reachable"]:
            print("ERROR: Still unreachable. Skipping LLM call.", flush=True)
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
If no entities match, return []"""
    try: 
        response = client.chat.completions.create(model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial compliance expert. Return valid JSON arrays only. No markdown, no explanation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )

        result = response.choices[0].message.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            parsed = next(iter(parsed.values()))
        return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f"  LLM ERROR [{type(e).__name__}]: {str(e)[:150]}", flush=True)
        traceback.print_exc()
        return []


def merge_entities(spacy_entities: list, llm_entities: list) -> list:
    merged = {}
    # spaCy entities go in first (lower priority for FINRA types)
    for ent in spacy_entities:
        key = ent["text"].lower().strip()
        merged[key] = ent
    # LLM FINRA entities override spaCy (higher quality for domain labels)
    for ent in llm_entities:
        key = ent["text"].lower().strip()
        if ent["label"] in FINRA_ENTITY_TYPES:
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
        print(f"\nBatch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}...", flush=True)
        results = process_batch(batch)
        for target_dict, field_name, merged, spacy_count, llm_count in results:
            target_dict[field_name] = merged
            if field_name == "entities":
                target_dict["entity_sources"] = {
                    "spacy_count": spacy_count,
                    "llm_count": llm_count,
                    "merged_count": len(merged),
                }
        processed += len(batch)
        print(f"  Processed {processed}/{total}", flush=True)
    return doc


def main(input_path, output_path, batch_size=5):
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        print(f"ERROR: File not found: {input_path.absolute()}", flush=True)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    print(f"Loaded '{doc.get('title')}' with {len(doc.get('sections', []))} sections", flush=True)

    enriched_doc = process_json_document_batched(doc, batch_size)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_doc, f, indent=2, ensure_ascii=False)

    print(f"\nDONE: Saved to {output_path}", flush=True)

if __name__ == "__main__":
    main(
        input_path="FINRA/policy_spacy_entities.json",
        output_path="FINRA/policy_hybrid_entities.json",
        batch_size=5)

