import json
import re
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

def repair_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```json"): raw = raw[7:]
    if raw.startswith("```"): raw = raw[3:]
    if raw.endswith("```"): raw = raw[:-3]
    raw = raw.strip()
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return raw

class StructuredParser:
    @staticmethod
    def parse(content: str, schema: Type[T], max_retries: int = 2) -> T:
        for i in range(max_retries + 1):
            try:
                cleaned = repair_json(content)
                data = json.loads(cleaned)
                return schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                if i == max_retries:
                    raise ValueError(f"Failed to parse structured output after {max_retries} retries: {e}")
                content = f"Fix this JSON error: {e}. Original: {content}"
        raise ValueError("Unreachable")
