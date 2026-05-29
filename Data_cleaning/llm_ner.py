import json
import os
import sys
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # fallback

if not GROQ_API_KEY and not OPENROUTER_API_KEY:
    raise ValueError("Set at least GROQ_API_KEY or OPENROUTER_API_KEY in your .env")


PROVIDERS = []

if GROQ_API_KEY:
    PROVIDERS.append({
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key": GROQ_API_KEY,
        "model": "llama-3.3-70b-versatile",  
        "rpm_limit": 28,        
        "retry_delay": 62,      
    })

if OPENROUTER_API_KEY:
    PROVIDERS.append({
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": OPENROUTER_API_KEY,
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "rpm_limit": 15,        
        "retry_delay": 65,
    })


FINRA_ENTITY_TYPES = [
    "REGULATION", "REPORT_TYPE", "THRESHOLD", "CUSTOMER_TYPE",
    "RISK_FACTOR", "TRANSACTION_TYPE", "ACCOUNT_STATUS",
    "COMPLIANCE_ACTION", "SECURITY_TYPE", "DOCUMENT_TYPE",
]

_request_times = {p["name"]: [] for p in PROVIDERS}

def _check_rate_limit(provider: dict) -> bool:
    """Returns True if we can make a request now."""
    name = provider["name"]
    now = time.time()
    # Keep only requests in the last 60 seconds
    _request_times[name] = [t for t in _request_times[name] if now - t < 60]
    return len(_request_times[name]) < provider["rpm_limit"]

def _record_request(provider: dict):
    _request_times[provider["name"]].append(time.time())


def _call_llm(provider: dict, prompt: str) -> list | None:
    """
    Call an OpenAI-compatible endpoint.
    Returns parsed entity list or None on failure.
    """
    import urllib.request
    import urllib.error

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider['api_key']}",
    }
    if provider["name"] == "OpenRouter":
        headers["HTTP-Referer"] = "https://localhost"  # required by OpenRouter

    payload = json.dumps({
        "model": provider["model"],
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_tokens": 1000,
        "temperature": 0,
    }).encode("utf-8")

    req = urllib.request.Request(
        provider["base_url"], data=payload, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            # Accept {"entities": [...]} or bare [...]
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ("entities", "result", "data"):
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
            return []
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 429:
            print(f"  [{provider['name']}] Rate limited (429). Body: {body[:120]}", flush=True)
            return None  # signal to try fallback / retry
        print(f"  [{provider['name']}] HTTP {e.code}: {body[:200]}", flush=True)
        return None
    except Exception as e:
        print(f"  [{provider['name']}] Error: {type(e).__name__}: {str(e)[:150]}", flush=True)
        traceback.print_exc()
        return None


def llm_extract_entities(text: str, section_context: str = "") -> list:
    if not text or len(text.strip()) < 10:
        return []

    prompt = f"""You are a financial compliance expert specializing in FINRA AML regulations.
Extract domain-specific named entities from this text.

TEXT: "{text}"
SECTION: {section_context}

Extract ONLY these entity types:
- REGULATION: Specific rules, laws, regulations (e.g., "FINRA Rule 3310", "Bank Secrecy Act")
- REPORT_TYPE: Types of reports (e.g., "SAR", "Suspicious Activity Report")
- THRESHOLD: Monetary amounts, time periods, numerical thresholds (e.g., "$5,000", "90 days")
- CUSTOMER_TYPE: Types of customers or entities (e.g., "broker-dealer", "non-profit organization")
- RISK_FACTOR: Risk indicators or geographic concerns (e.g., "high-risk jurisdiction", "tax haven")
- TRANSACTION_TYPE: Types of transactions (e.g., "wire transfer", "structuring", "wash trade")
- ACCOUNT_STATUS: Account conditions (e.g., "dormant account", "shell company")
- COMPLIANCE_ACTION: Required compliance actions (e.g., "SAR filing", "customer due diligence")
- SECURITY_TYPE: Types of securities (e.g., "penny stock", "bearer bond", "ADR")
- DOCUMENT_TYPE: Regulatory documents (e.g., "Regulatory Notice", "Notice to Members")

Return ONLY a JSON object with key "entities" containing an array. Example:
{{"entities": [
  {{"text": "FINRA Rule 3310", "label": "REGULATION"}},
  {{"text": "$5,000", "label": "THRESHOLD"}},
  {{"text": "wire transfer", "label": "TRANSACTION_TYPE"}}
]}}

If no entities match, return {{"entities": []}}"""

    for provider in PROVIDERS:
        # Wait if needed to respect rate limit
        attempts = 0
        while not _check_rate_limit(provider) and attempts < 3:
            wait = provider["retry_delay"]
            print(f"  [{provider['name']}] Rate limit buffer full, waiting {wait}s...", flush=True)
            time.sleep(wait)
            attempts += 1

        _record_request(provider)
        result = _call_llm(provider, prompt)

        if result is not None:
            # Filter to only FINRA entity types
            return [e for e in result if e.get("label") in FINRA_ENTITY_TYPES]

        # If None (rate limit hit), try next provider
        print(f"  Falling back from {provider['name']}...", flush=True)

    print("  All providers failed for this item.", flush=True)
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

# ── Batch processing ──────────────────────────────────────────────────────────
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
    print("Starting NER enrichment (Groq primary, OpenRouter fallback)...", flush=True)
    active = [p["name"] for p in PROVIDERS]
    print(f"Active providers: {active}", flush=True)

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