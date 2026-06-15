import re 
import json
from pydantic import BaseModel, Field, field_validator
from typing import List

class Entity(BaseModel):
    text: str = Field(..., min_legnth = 2, description = "Exact text from source")
    label: str = Field(..., pattern = r'^(REGULATION|REPORT_TYPE|THRESHOLD|CUSTOMER_TYPE|RISK_FACTOR|TRANSACTION_TYPE|ACCOUNT_STATUS|COMPLIANCE_ACTION|SECURITY_TYPE|DOCUMENT_TYPE)$')

    @field_validator('text')
    @classmethod
    def no_trailing_punctuations(cls, v:str) -> str:
        """Strip trailing punctuation that doesn't belong to the entity."""
        while v and v[-1] in ')]}.,;:"':
            if v[-1] in ')]}' and v.count(v[-1]) == 1:
                v = v[:-1]

            else:
                break
        return v.strip()

    @field_validator('text')
    @classmethod
    def no_footnotes_numbers(cls, v: str) -> str:
        v = re.sub(r'([a-zA-Z]{2,})\.(\d+)$', r'\1', v)
        v = re.sub(r'([a-zA-Z]{2,})(\d{1,2})$', r'\1', v)
        return v

    
class EntityResponse(BaseModel):
    entities: List[Entity] = Field(default_factory=list)

def parse_llm_response(raw_text: str) -> List[dict]:
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    if not raw_text or raw_text in ('[]', '{}'):
        return []

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                print(f"Unparseable JSON: {raw_text[:100]}")
                return []

        else:
            print(f"  [WARN] No JSON found in: {raw_text[:100]}")
            return []

    try:
        response = EntityResponse.model_validate(parsed)
        return [e.model_dump() for e in response.entities]
    except Exception as e:
        print(f"Validation failed: {str(e)[:100]}")
        return []