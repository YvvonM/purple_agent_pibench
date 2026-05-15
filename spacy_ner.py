import json 
import spacy 
from pathlib import Path 

nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    entities = []

    for ent in doc.ents:
        entities.append(
            {
                "text": ent.text,
                "label": ent.label_
            }
        )
    return entities


def process_content_list(content_list):
    for item in content_list:
        if "text" in item:
            item['entities'] = extract_entities(item['text'])
        if "sub_items" in item and item['sub_items']:
            for sub in item["sub_items"]:
                if "text" in sub:
                    sub["entities"] = extract_entities(sub["text"])

    return content_list

def process_json_document(doc):

    if doc.get("title"):
        doc["title_entities"] = extract_entities(doc["title"])

    for section in doc.get("sections", []):
        if section.get("title"):
            section["title_entities"] = extract_entities(section["title"])

        if section.get("content"):
             section["content"] = process_content_list(section["content"])

    for sub in section.get("subsections", []):
        if sub.get("title"):
                sub["title_entities"] = extract_entities(sub["title"])

        if sub.get("content"):
            sub["content"] = process_content_list(sub["content"])

    return doc

def main(input_path, output_path):
    

    input_path = Path(input_path)
    output_path = Path(output_path)


    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    
    enriched_doc = process_json_document(doc)

    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_doc, f, indent=2)

    print(f"Saved enriched file -> {output_path}")


if __name__ == "__main__":
    main("FINRA/policy.json", "FINRA/policy_spacy_entities.json")
