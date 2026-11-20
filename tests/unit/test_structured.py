import pytest
from pydantic import BaseModel
from meridian.core.structured import StructuredParser

class UserSchema(BaseModel):
    name: str
    age: int

def test_structured_parser_repair() -> None:
    raw = '{"name": "Alice", "age": 30,}'
    parsed = StructuredParser.parse(raw, UserSchema)
    assert parsed.name == "Alice"
    assert parsed.age == 30

def test_structured_parser_markdown() -> None:
    raw = '```json\n{"name": "Bob", "age": 25}\n```'
    parsed = StructuredParser.parse(raw, UserSchema)
    assert parsed.name == "Bob"

def test_structured_parser_failure() -> None:
    with pytest.raises(ValueError):
        StructuredParser.parse("invalid json", UserSchema, max_retries=0)
