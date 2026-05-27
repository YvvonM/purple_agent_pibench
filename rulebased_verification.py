
import json
import re
import sys
from collections import defaultdict
from gazetteer_table import (GAZETTEER, VALID_ENTITY_TYPES, REGULATION_PATTERNS, 
EMAIL_PATTERN, PHONE_PATTERN, MONEY_PATTERN)



def verify_regulation(value):
    # Check against regex patterns
    if any(p.fullmatch(value) for p in REGULATION_PATTERNS):
        return True
    # Also accept known regulation abbreviations from gazetteer
    known_regulations = {"BSA", "AML"}  # Add more as needed
    return value in known_regulations

def verify_email(value):
    return bool(EMAIL_PATTERN.fullmatch(value))

def verify_phone(value):
    return bool(PHONE_PATTERN.fullmatch(value))

def verify_money(value):
    return bool(MONEY_PATTERN.fullmatch(value))

def verify_structural(entity_type, value):
    if entity_type == "regulation":
        return verify_regulation(value)
    if entity_type == "email":
        return verify_email(value)
    if entity_type == "phone":
        return verify_phone(value)
    if entity_type == "money":
        return verify_money(value)
    return True

def verify_type(entity_type):
    return entity_type in VALID_ENTITY_TYPES

def verify_canonical(canonical, valid_canonicals):
    return canonical in valid_canonicals

def get_context(text, start, end, window=100):  # Increased from 75
    left = max(0, start - window)
    right = min(len(text), end + window)
    return text[left:right].lower()

def verify_context(entity_type, context):
    context_terms = {
        "report_type": {"suspicious", "activity", "report", "file", "filing", "fincen", "treasury", "bsa", "aml", "transaction", "sar"},
        "regulation": {"rule", "act", "compliance", "regulation", "treasury", "finra", "sec", "cfr", "usc", "bsa", "require", "implement"},
        "organization": {"finra", "fincen", "treasury", "sec", "fatf", "department", "network"},
        "regulatory_program": {"program", "compliance", "aml", "bsa", "policy", "procedure"},
        "customer_type": {"customer", "account", "client", "firm", "entity", "open", "broker", "dealer", "person", "trust", "company"},
        "security_type": {"security", "stock", "bond", "share", "certificate", "issuer", "asset"},
        "transaction_type": {"transaction", "transfer", "deposit", "withdraw", "wire", "trade", "funds", "payment"},
        "risk_factor": {"risk", "suspicious", "red flag", "indicator", "concern", "potential", "financing", "laundering", "terrorist"},
        "compliance_action": {"due diligence", "monitor", "investigate", "file", "report", "review", "filing"},
        "financial_concept": {"price", "market", "bid", "offer", "float", "account", "period", "nostro", "correspondent"},
        "threshold": {"day", "year", "period", "least", "every", "minimum", "maximum", "days"},
        "person": {"director", "counsel", "contact", "phone", "email", "general"},
        "regulatory_notice": {"notice", "regulatory", "finra", "guidance"}
    }

    terms = context_terms.get(entity_type, set())
    if not terms:
        return True
    return any(term in context for term in terms)

def calculate_confidence(structural_valid, canonical_valid, context_valid, type_valid):
    score = 0
    if structural_valid:
        score += 0.3
    if canonical_valid:
        score += 0.3
    if context_valid:
        score += 0.2
    if type_valid:
        score += 0.2
    return round(score, 2)

def verify_entity(entity, text, valid_canonicals):
    entity_type = entity["type"]
    value = entity["value"]
    canonical = entity.get("canonical", "")

    structural_valid = verify_structural(entity_type, value)
    type_valid = verify_type(entity_type)
    canonical_valid = verify_canonical(canonical, valid_canonicals)

    context = get_context(text, entity["start"], entity["end"])
    context_valid = verify_context(entity_type, context)

    confidence = calculate_confidence(structural_valid, canonical_valid, context_valid, type_valid)

    # Relaxed threshold: if canonical is valid and type is valid, be more lenient on context
    if canonical_valid and type_valid and structural_valid:
        verified = True
    else:
        verified = type_valid and structural_valid and context_valid and confidence >= 0.7

    return {
        **entity,
        "verified": verified,
        "confidence": confidence,
        "verification": {
            "structural_valid": structural_valid,
            "canonical_valid": canonical_valid,
            "context_valid": context_valid,
            "type_valid": type_valid
        }
    }


def verify_text_block(text, entities, valid_canonicals):
    return [verify_entity(ent, text, valid_canonicals) for ent in entities]


def process_document(doc, valid_canonicals):
    # Document title
    if "title" in doc and "title_entities" in doc:
        doc["title_entities"] = verify_text_block(doc["title"], doc["title_entities"], valid_canonicals)

    # Sections
    for section in doc.get("sections", []):
        # Section title
        if "title" in section and "title_entities" in section:
            section["title_entities"] = verify_text_block(section["title"], section["title_entities"], valid_canonicals)

        # Content items
        for item in section.get("content", []):
            text = item.get("text", "")
            if text and "entities" in item:
                item["entities"] = verify_text_block(text, item["entities"], valid_canonicals)

            # Sub-items
            for sub in item.get("sub_items", []):
                sub_text = sub.get("text", "")
                if sub_text and "entities" in sub:
                    sub["entities"] = verify_text_block(sub_text, sub["entities"], valid_canonicals)

    return doc


def generate_summary(processed_doc):
    total = 0
    verified = 0
    entity_counts = defaultdict(int)
    rejection_reasons = defaultdict(int)

    # Document title entities
    for ent in processed_doc.get("title_entities", []):
        total += 1
        entity_counts[ent["type"]] += 1
        if ent["verified"]:
            verified += 1
        else:
            v = ent["verification"]
            if not v["type_valid"]: rejection_reasons["invalid_type"] += 1
            if not v["structural_valid"]: rejection_reasons["structural_fail"] += 1
            if not v["context_valid"]: rejection_reasons["context_mismatch"] += 1
            if not v["canonical_valid"]: rejection_reasons["unknown_canonical"] += 1

    # Sections
    for section in processed_doc.get("sections", []):
        # Section title entities
        for ent in section.get("title_entities", []):
            total += 1
            entity_counts[ent["type"]] += 1
            if ent["verified"]:
                verified += 1
            else:
                v = ent["verification"]
                if not v["type_valid"]: rejection_reasons["invalid_type"] += 1
                if not v["structural_valid"]: rejection_reasons["structural_fail"] += 1
                if not v["context_valid"]: rejection_reasons["context_mismatch"] += 1
                if not v["canonical_valid"]: rejection_reasons["unknown_canonical"] += 1

        # Content items
        for item in section.get("content", []):
            for ent in item.get("entities", []):
                total += 1
                entity_counts[ent["type"]] += 1
                if ent["verified"]:
                    verified += 1
                else:
                    v = ent["verification"]
                    if not v["type_valid"]: rejection_reasons["invalid_type"] += 1
                    if not v["structural_valid"]: rejection_reasons["structural_fail"] += 1
                    if not v["context_valid"]: rejection_reasons["context_mismatch"] += 1
                    if not v["canonical_valid"]: rejection_reasons["unknown_canonical"] += 1

            for sub in item.get("sub_items", []):
                for ent in sub.get("entities", []):
                    total += 1
                    entity_counts[ent["type"]] += 1
                    if ent["verified"]:
                        verified += 1
                    else:
                        v = ent["verification"]
                        if not v["type_valid"]: rejection_reasons["invalid_type"] += 1
                        if not v["structural_valid"]: rejection_reasons["structural_fail"] += 1
                        if not v["context_valid"]: rejection_reasons["context_mismatch"] += 1
                        if not v["canonical_valid"]: rejection_reasons["unknown_canonical"] += 1

    return {
        "total": total,
        "verified": verified,
        "rejected": total - verified,
        "verification_rate": round(verified / total, 4) if total else 0,
        "entity_counts": dict(entity_counts),
        "rejection_reasons": dict(rejection_reasons)
    }


def print_summary(summary):
    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print(f"\nTotal entities:      {summary['total']}")
    print(f"Verified:            {summary['verified']} ({summary['verification_rate']:.1%})")
    print(f"Rejected:            {summary['rejected']}")

    print("\nBy type:")
    for t, c in sorted(summary['entity_counts'].items(), key=lambda x: -x[1]):
        print(f"  {t:25}: {c}")

    if summary['rejection_reasons']:
        print("\nRejection reasons:")
        for r, c in sorted(summary['rejection_reasons'].items(), key=lambda x: -x[1]):
            print(f"  {r:20}: {c}")

    print("\n" + "=" * 60)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Parse arguments
    input_path = "FINRA/gazetteer_entities.json"
    output_path = "FINRA/verified.json"

    VALID_CANONICALS = set(GAZETTEER.keys())

    print(f"Loading document: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    print("Processing...")
    processed_doc = process_document(doc, VALID_CANONICALS)

    print("Generating summary...")
    summary = generate_summary(processed_doc)
    print_summary(summary)

    # Add summary to output
    processed_doc["_verification_summary"] = summary

    print(f"Saving to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_doc, f, indent=2, ensure_ascii=False)

    print("Done!")