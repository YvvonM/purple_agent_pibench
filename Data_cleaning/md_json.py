import json 
import re
from pathlib import Path


def parse_markdown(md_text):
    lines = md_text.splitlines()
    document = {
        'title': None,
        "sections": []
    }
    current_section = None
    current_subsection = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("# "):
            document["title"] = line[2:].strip()

        elif line.startswith("## "):
            section_title = line[3:].strip()
            if section_title == "Endnotes":# Stop collecting
                break

            current_section = {
                "title": section_title,
                "content": [],
                "subsections": []
            }
            document["sections"].append(current_section)
            current_subsection = None

        elif line.startswith("### "):
            current_subsection = {
                "title": line[4:].strip(),
                "content": []
            }

            if current_section:
                current_section["subsections"].append(current_subsection)

        elif re.match(r"^\d+\.", line):
            match = re.match(r"^(\d+)\.\s*(.+)", line)
            if match:
                num, text = match.groups()
                item = {
                    "type": "numbered_item",
                    "number": int(num),
                    "text": text,
                    "sub_items": []  
                }
            if current_subsection:
                current_subsection["content"].append(item)
            elif current_section:
                current_section["content"].append(item)

        elif line.startswith("- "):

            bullet_text = line[2:].strip().rstrip(';')  # Clean semicolons
            
            # Check if previous item in current section was a numbered_item
            if current_section and current_section["content"]:
                last_item = current_section["content"][-1]
                
                if last_item["type"] == "numbered_item":
                    # This bullet belongs to the previous numbered item
                    last_item["sub_items"].append({
                        "type": "bullet",
                        "text": bullet_text
                    })
                else:
                    # Standalone bullet
                    current_section["content"].append({
                        "type": "bullet",
                        "text": bullet_text
                    })
        else:
            if current_subsection:
                current_subsection["content"].append({
                    "type": "paragraph",
                    "text": line
                })
            elif current_section:
                current_section["content"].append({
                    "type": "paragraph",
                    "text": line
                })

    return document


def main_func(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as file:
        md_text = file.read()

    parsed_document = parse_markdown(md_text)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            parsed_document,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"JSON saved to: {output_path}")

    return parsed_document


output = main_func("FINRA/policy.md", "FINRA/policy.json")
print(output)
