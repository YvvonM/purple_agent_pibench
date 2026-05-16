import json 
import os
from dotenv import load_dotenv
import logging 
from pathlib import Path 
from google import genai

load_dotenv()
NER_KEY = os.getenv("NER_API")
if not NER_KEY:
    raise ValueError("Api key missing!")

client = genai.Client(api_key = NER_KEY)
FINRA_ENTITY_TYPES = [
    "REGULATION",       # FINRA Rule 3310, BSA, 31 CFR 1023.320
    "REPORT_TYPE",      # SAR, CTR, Suspicious Activity Report
    "THRESHOLD",        # $5,000, $10,000, 90 days, 120 days
    "CUSTOMER_TYPE",    # PEP, shell company, nonprofit, foreign financial institution
    "RISK_FACTOR",      # high-risk geographic location, conflict zone, secrecy haven
    "TRANSACTION_TYPE", # wire transfer, deposit, structuring, layering, spoofing
    "ACCOUNT_STATUS",   # dormant, active, new account, lock-up
    "COMPLIANCE_ACTION",# escalate, file SAR, deny, hold, investigate
    "SECURITY_TYPE",    # penny stock, bearer bonds, ADR, restricted securities
    "DOCUMENT_TYPE", 
]

def llm_extract_entities(text:str, section_context:str = "")-> list:
    if not text or len(text.strip) < 10:
        return []

    prompt = f"""
You are a financial compliance expert specializing in FINRA AML regulations.

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
If no entities match, return [].
    """
    try:
        response = client.models.generate_content(
            model = "gemini-2.5-pro",
            content = prompt,
            config = {"response_mime_type": "application/json"}
        )
        entities = json.loads(
            response.text
        )
        return entities if isinstance(entities, list) else []

    except Exception as e: 
        print(f"LLM error for text '{text[:50]}...': {e}")
        return []

def merged_entity(spacy_entities: list, llm_entities: list) -> list:
    merged = {}
    for ent in spacy_entities:
        key = ent['text'].lower().strip()
        merged[key] = ent

    for ent in llm_entities:
        key = ent['text'].lower().strip()
        if ent['label'] in FINRA_ENTITY_TYPES:
            merged[key] = ent

    return list(merged.values())

def proecess_content_list(content_list:list, section_title= ""):
    for item in content_list:
        if "text" in item:
            spacy_ents = item.get('entities', [])
            
