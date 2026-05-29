import json
import sys
import copy
from pathlib import Path
from onto_relationships import ONTOLOGY


RELATIONSHIP_KEYS = {
    "requires", "governed_by", "enforced_by", "regulates", "issues",
    "filed_with", "collects", "administers", "promulgates", "oversees",
    "produces", "may_produce", "related_to", "risk_level", "identified_by",
    "defined_by", "affiliated_with", "authorizes", "applies_to",
    "regulated_by", "subject_to", "must_file", "must_implement",
    "detects", "detected_by", "reported_via", "red_flags_issued_by",
    "parent_organization", "staff", "contact", "belongs_to",
    "associated_with", "incorporated_into", "provides_guidance_on",
    "recommended_by", "threshold", "retention_period", "review_period",
    "filing_deadline", "role", "purpose", "date", "risk_context",
    "used_by", "used_with", "includes", "promulgated_by", "defines",
    "registers", "issues_guidance"
}


class EntityLinker:
    """Maps extracted entity values to canonical ontology entries."""

    def __init__(self, ontology):
        self.ontology = ontology
        self.alias_index = {}
        for entity_id, data in ontology.items():
            for alias in data.get("aliases", []):
                self.alias_index[alias.lower().strip()] = entity_id
            canonical = data.get("canonical_name", "").lower().strip()
            if canonical:
                self.alias_index[canonical] = entity_id

    def link(self, value, canonical=None):
        key = value.lower().strip()
        if key in self.alias_index:
            return self.alias_index[key]
        if canonical:
            key = canonical.lower().strip()
            if key in self.alias_index:
                return self.alias_index[key]
        key_clean = key.rstrip(".,;:!?")
        if key_clean in self.alias_index:
            return self.alias_index[key_clean]
        if key.endswith("s"):
            singular = key[:-1]
            if singular in self.alias_index:
                return self.alias_index[singular]
        else:
            plural = key + "s"
            if plural in self.alias_index:
                return self.alias_index[plural]
        return None

    def enrich(self, entity):
        value = entity.get("value", "")
        canonical = entity.get("canonical", "")
        entity_id = self.link(value, canonical)

        if not entity_id:
            return {**entity, "entity_id": None, "linked": False}

        ont = self.ontology.get(entity_id, {})
        relationships = {k: v for k, v in ont.items() if k in RELATIONSHIP_KEYS and v}

        return {
            **entity,
            "entity_id": entity_id,
            "linked": True,
            "ontology_type": ont.get("ontology_type"),
            "domain": ont.get("domain"),
            "description": ont.get("description"),
            "relationships": relationships
        }


def process_item(item, linker):
    if "entities" in item:
        item["entities"] = [linker.enrich(e) for e in item["entities"]]
    if "sub_items" in item:
        for sub in item["sub_items"]:
            process_item(sub, linker)
    return item


def process_section(section, linker):
    if "content" in section:
        section["content"] = [process_item(item, linker) for item in section["content"]]
    if "title_entities" in section:
        section["title_entities"] = [linker.enrich(e) for e in section["title_entities"]]
    if "subsections" in section:
        for sub in section["subsections"]:
            process_section(sub, linker)
    return section


def build_entity_index(enriched):
    """Build flat lookup of all linked entities found in the document."""
    index = {}
    for section in enriched.get("sections", []):
        for item in section.get("content", []):
            for entity in item.get("entities", []):
                if entity.get("entity_id"):
                    index[entity["entity_id"]] = {
                        "canonical_name": entity.get("canonical"),
                        "ontology_type": entity.get("ontology_type"),
                        "domain": entity.get("domain"),
                        "value_found": entity.get("value"),
                        "type": entity.get("type")
                    }
            for sub in item.get("sub_items", []):
                for entity in sub.get("entities", []):
                    if entity.get("entity_id"):
                        index[entity["entity_id"]] = {
                            "canonical_name": entity.get("canonical"),
                            "ontology_type": entity.get("ontology_type"),
                            "domain": entity.get("domain"),
                            "value_found": entity.get("value"),
                            "type": entity.get("type")
                        }
    return index


def collect_stats(enriched):
    """Collect linkage statistics."""
    total = linked = unlinked = 0
    unlinked_values = []

    for section in enriched.get("sections", []):
        for item in section.get("content", []):
            for e in item.get("entities", []):
                total += 1
                if e.get("linked"):
                    linked += 1
                else:
                    unlinked += 1
                    unlinked_values.append({
                        "value": e.get("value"),
                        "canonical": e.get("canonical"),
                        "type": e.get("type")
                    })
            for sub in item.get("sub_items", []):
                for e in sub.get("entities", []):
                    total += 1
                    if e.get("linked"):
                        linked += 1
                    else:
                        unlinked += 1
                        unlinked_values.append({
                            "value": e.get("value"),
                            "canonical": e.get("canonical"),
                            "type": e.get("type")
                        })
        for te in section.get("title_entities", []):
            total += 1
            if te.get("linked"):
                linked += 1
            else:
                unlinked += 1
                unlinked_values.append({
                    "value": te.get("value"),
                    "canonical": te.get("canonical"),
                    "type": te.get("type")
                })

    return total, linked, unlinked, unlinked_values


def main(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Load extracted policy
    with open(input_path, "r", encoding="utf-8") as f:
        policy = json.load(f)

    # Initialize linker
    linker = EntityLinker(ONTOLOGY)

    # Enrich
    enriched = copy.deepcopy(policy)

    if "title_entities" in enriched:
        enriched["title_entities"] = [linker.enrich(e) for e in enriched["title_entities"]]

    for section in enriched.get("sections", []):
        process_section(section, linker)

    # Save enriched policy
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)

    # Save ontology dictionary
    dict_path = output_path.parent / "ontology_dictionary.json"
    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(ONTOLOGY, f, indent=2)

    # Save entity index
    entity_index = build_entity_index(enriched)
    index_path = output_path.parent / "entity_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(entity_index, f, indent=2)

    # Stats
    total, linked, unlinked, unlinked_values = collect_stats(enriched)

    print("*" * 60)
    print("ONTOLOGY MAPPING COMPLETE")
    print("*" * 60)
    print(f"Total entities:{total}")
    print(f"Linked:{linked} ({linked/total*100:.1f}%)")
    print(f"Unlinked:{unlinked} ({unlinked/total*100:.1f}%)")
    print()
    print("Files created:")
    print(f"{output_path.name:30s} - Document with ontology metadata")
    print(f"{dict_path.name:30s} - Full knowledge base")
    print(f"{index_path.name:30s} — Flat entity lookup")
    print()

    if unlinked_values:
        print("UNLINKED ENTITIES - Add these to ONTOLOGY:")
        seen = set()
        for u in unlinked_values:
            key = (u["value"], u.get("canonical", ""), u["type"])
            if key not in seen:
                seen.add(key)
                print(f"- value: '{u['value']}', canonical: '{u.get('canonical', 'n/a')}', type: {u['type']}")


if __name__ == "__main__":
    main("FINRA/verified.json", "FINRA/ontology_output.json")