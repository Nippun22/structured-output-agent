import pytest
from pydantic import BaseModel, Field
from structured_agent.core.tool import Tool, tool, ToolExecutionError

class CalculationOutput(BaseModel):
    result: float
    operation: str

@tool(name="multiply", description="Multiplies two numbers", output_schema=CalculationOutput)
def multiply_numbers(a: float, b: float) -> CalculationOutput:
    return CalculationOutput(result=a * b, operation="multiplication")

def test_tool_schema_generation():
    schema = multiply_numbers.get_json_schema()
    assert schema["name"] == "multiply"
    assert "a" in schema["parameters"]["properties"]
    assert "b" in schema["parameters"]["properties"]

def test_tool_execution_success():
    res = multiply_numbers.execute({"a": 4.0, "b": 5.0})
    assert res["success"] is True
    assert res["output"]["result"] == 20.0

def test_tool_execution_invalid_arg_types():
    with pytest.raises(ToolExecutionError) as exc_info:
        multiply_numbers.execute({"a": "not_a_number", "b": 5.0})
    assert "argument validation failed" in str(exc_info.value)
