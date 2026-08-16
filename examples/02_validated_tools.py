"""
Example 02: Type-Safe Tool Calling with Pydantic Input/Output Schemas
Demonstrates how Pydantic guarantees tool parameters and return values match strict contracts.
"""

from pydantic import BaseModel, Field
from structured_agent import Tool, tool, StructuredAgent
from structured_agent.providers.mock_provider import MockLLMProvider

# 1. Define Tool Input and Output Schemas
class WeatherRequest(BaseModel):
    city: str = Field(..., description="Target city name e.g. San Francisco, Tokyo")
    units: str = Field("celsius", description="Temperature units: 'celsius' or 'fahrenheit'")

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    condition: str
    humidity_pct: int = Field(..., ge=0, le=100)

# 2. Define Validated Tool using @tool decorator
@tool(
    name="get_current_weather",
    description="Fetch live weather metrics for a specified city.",
    output_schema=WeatherResponse
)
def get_current_weather(city: str, units: str = "celsius") -> WeatherResponse:
    """Mock implementation of weather API."""
    city_clean = city.strip().title()
    mock_temps = {"New York": 22.5, "Tokyo": 18.0, "London": 15.2}
    temp = mock_temps.get(city_clean, 20.0)

    return WeatherResponse(
        city=city_clean,
        temperature=temp,
        condition="Partly Cloudy",
        humidity_pct=65
    )

class WeatherAgentSummary(BaseModel):
    queried_city: str
    weather_summary: str
    clothing_advice: str

def main():
    print("==================================================================")
    print("        DEMO 02: PYDANTIC VALIDATED TOOL CALLING AGENT           ")
    print("==================================================================")

    # Inspect Tool JSON Schema generated for LLM function calling
    weather_tool: Tool = get_current_weather
    print("\n Generated OpenAPI / JSON Schema for Tool:")
    import json
    print(json.dumps(weather_tool.get_json_schema(), indent=2))

    # Test Tool Direct Execution with Validation
    print("\n Executing Tool with raw dict input:")
    tool_result = weather_tool.execute({"city": "New York", "units": "celsius"})
    print("Tool Output Result:", tool_result)

    # Test Agent Response validation
    mock_agent_data = {
        "queried_city": "New York",
        "weather_summary": "New York is currently 22.5°C and Partly Cloudy with 65% humidity.",
        "clothing_advice": "Wear a light jacket or comfortable sweater."
    }

    provider = MockLLMProvider(fault_mode="none", valid_data=mock_agent_data)
    agent = StructuredAgent(provider=provider, tools=[weather_tool], agent_name="WeatherAgent")

    result = agent.run(
        user_prompt="What is the weather in New York and what should I wear?",
        response_model=WeatherAgentSummary
    )

    if result.is_valid:
        summary: WeatherAgentSummary = result.parsed_object
        print("\n Successfully executed and validated summary:")
        print(f"City: {summary.queried_city}")
        print(f"Summary: {summary.weather_summary}")
        print(f"Advice: {summary.clothing_advice}")

if __name__ == "__main__":
    main()
