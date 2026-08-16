import pytest
from pydantic import BaseModel, Field
from structured_agent.core.validator import SchemaValidator

class DummyModel(BaseModel):
    name: str = Field(..., min_length=2)
    count: int = Field(..., ge=1, le=10)

def test_extract_json_string_clean():
    raw = '```json\n{"name": "Test", "count": 5}\n```'
    extracted = SchemaValidator.extract_json_string(raw)
    assert extracted == '{"name": "Test", "count": 5}'

def test_extract_json_string_with_chatter():
    raw = 'Here is your data:\n{"name": "Test", "count": 5}\nHope this helps!'
    extracted = SchemaValidator.extract_json_string(raw)
    assert extracted == '{"name": "Test", "count": 5}'

def test_validate_success():
    raw = '{"name": "Alice", "count": 3}'
    res = SchemaValidator.validate(raw, DummyModel)
    assert res.is_valid is True
    assert res.parsed_object.name == "Alice"
    assert res.parsed_object.count == 3
    assert len(res.errors) == 0

def test_validate_pydantic_error():
    raw = '{"name": "A", "count": 50}'  # name too short (<2), count too large (>10)
    res = SchemaValidator.validate(raw, DummyModel)
    assert res.is_valid is False
    assert len(res.errors) == 2
    assert res.repair_prompt is not None
    assert "VALIDATION ERRORS FOUND" in res.repair_prompt

def test_validate_json_decode_error():
    raw = '{"name": "Alice", count: 5}'  # Invalid unquoted key
    res = SchemaValidator.validate(raw, DummyModel)
    assert res.is_valid is False
    assert res.errors[0].error_type == "json_decode_error"
