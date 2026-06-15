import json 
import os 
import sys 
import time 
import traceback 
from pathlib import Path 
from dotenv import load_dotenv
from openai import OpenAI
from pydantic_models import parse_llm_response
from connection_checker import check_connection, log_connection_status

load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")

CONN_INFO = check_connection(OLLAMA_HOST)
log_connection_status(CONN_INFO)

client = OpenAI(
    base_url=f"{OLLAMA_HOST}/v1",
    api_key=OLLAMA_TOKEN,
    timeout=300
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
    prompt = f"""Extract domain-specific entities from the following text. Only extract entities that are EXPLICITLY MENTIONED in the text. Do not infer, generalize, or add labels that do not appear verbatim.

Text:
"{text}"

Section context: {section_context}

Allowed entity types and examples:
- REGULATION: specific cited rules like "FINRA Rule 3310", "31 U.S.C. 5311", "Bank Secrecy Act", "31 CFR 1023.320"
- REPORT_TYPE: "suspicious activity reports", "SARs", "continuing activity SAR filing"
- THRESHOLD: "$5,000", "90 days", "120 days", "five years"
- CUSTOMER_TYPE: "broker-dealer", "politically exposed person", "shell company", "non-profit organization"
- RISK_FACTOR: "money laundering red flags", "high-risk geographic location", "structuring", "unregistered basis"
- TRANSACTION_TYPE: "wire transfers", "deposits", "liquidation", "journal entries"
- ACCOUNT_STATUS: "dormant account", "new account", "master/sub structure"
- COMPLIANCE_ACTION: "file SARs", "notify by telephone", "customer due diligence"
- SECURITY_TYPE: "penny stocks", "bearer bonds", "restricted securities", "American Depository Receipts"
- DOCUMENT_TYPE: "Notice to Members 02-21", "Regulatory Notice 19-18"

Rules:
1. ONLY extract text that literally appears in the passage
2. Do NOT extract "FINRA AML regulations" — this phrase never appears in the text
3. Do NOT extract generic topic descriptions as regulations
4. Do NOT extract phone numbers, email addresses, or footnote citation numbers
5. Extract the COMPLETE phrase including all words, numbers, and punctuation that belong to the entity
6. If the entity includes parentheses like "(PEP)" or "(NBBO)", include them
7. Do NOT include trailing punctuation from the surrounding sentence
8. Return ONLY a JSON object with key "entities" containing an array

Example 1 — dense paragraph:
{{"entities": [
  {{"text": "FINRA Rule 3310", "label": "REGULATION"}},
  {{"text": "$5,000", "label": "THRESHOLD"}},
  {{"text": "wire transfer", "label": "TRANSACTION_TYPE"}}
]}}

Example 2 — no matching entities:
{{"entities": []}}

If no entities match, return {{"entities": []}}"""
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

        raw = response.choices[0].message.content.strip()
        return parse_llm_response(raw)
        
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:100]}", flush=True)
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
        output_path="FINRA/policy_hybrid_entities2.json",
        batch_size=5)

