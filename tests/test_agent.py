import pytest
from pydantic import BaseModel, Field
from structured_agent.core.agent import StructuredAgent
from structured_agent.providers.mock_provider import MockLLMProvider

class SimpleModel(BaseModel):
    name: str
    age: int

def test_agent_first_pass_success():
    valid_data = {"name": "Bob", "age": 30}
    provider = MockLLMProvider(fault_mode="none", valid_data=valid_data)
    agent = StructuredAgent(provider=provider, verbose=False)

    result = agent.run("Get profile", SimpleModel)
    assert result.is_valid is True
    assert result.retry_count == 0
    assert result.parsed_object.name == "Bob"

def test_agent_auto_repair_recovery():
    valid_data = {"name": "Bob", "age": 30}
    # Initial call gives invalid age ("thirty" str instead of int)
    provider = MockLLMProvider(fault_mode="auto_repair", valid_data=valid_data)
    agent = StructuredAgent(provider=provider, max_retries=3, verbose=False)

    result = agent.run("Get profile", SimpleModel)
    assert result.is_valid is True
    assert result.retry_count == 1  # Fixed in retry #1
    assert result.parsed_object.age == 30

def test_agent_max_retries_exceeded():
    provider = MockLLMProvider(fault_mode="json_error")
    agent = StructuredAgent(provider=provider, max_retries=2, verbose=False)

    result = agent.run("Get profile", SimpleModel)
    assert result.is_valid is False
    assert result.retry_count == 2
