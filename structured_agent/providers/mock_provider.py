import json
from typing import List, Dict, Any, Optional
from structured_agent.providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic & Fault-Injecting Mock LLM Provider for offline testing.
    Demonstrates how the agent automatically recovers when the LLM outputs bad data on first attempt.
    """

    def __init__(self, fault_mode: str = "auto_repair", valid_data: Optional[Dict[str, Any]] = None):
        """
        fault_mode choices:
        - 'none': Always returns perfectly valid JSON.
        - 'auto_repair': Return invalid data on attempt 1, then fix it when receiving repair feedback on attempt 2!
        - 'json_error': Always return invalid JSON syntax.
        """
        self.fault_mode = fault_mode
        self.valid_data = valid_data or {
            "name": "Alice Johnson",
            "age": 28,
            "email": "alice@example.com",
            "skills": ["Python", "Machine Learning", "Pydantic"],
            "score": 94.5
        }
        self.call_count = 0

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        self.call_count += 1
        last_user_msg = messages[-1]["content"] if messages else ""

        # If fault_mode is none or valid_data requested directly
        if self.fault_mode == "none":
            return f"```json\n{json.dumps(self.valid_data, indent=2)}\n```"

        if self.fault_mode == "json_error":
            return "{ 'name': 'Alice', age: 28, email: missing_quote }"

        if self.fault_mode == "auto_repair":
            # Check if this is a retry containing repair instructions
            if "VALIDATION ERRORS FOUND" in last_user_msg or "INSTRUCTIONS FOR CORRECTION" in last_user_msg:
                # LLM learned from feedback and returns valid fixed JSON!
                return f"```json\n{json.dumps(self.valid_data, indent=2)}\n```"
            else:
                # Attempt 1: Inject invalid schema types (e.g. age as string, missing email)
                invalid_payload = {
                    "name": "Alice Johnson",
                    "age": "TWENTY EIGHT",  # Wrong type! Expected integer
                    "skills": "Python, Machine Learning", # Wrong type! Expected list of strings
                    "score": 150.0  # Invalid score out of bounds
                }
                return f"Here is the data requested:\n```json\n{json.dumps(invalid_payload, indent=2)}\n```"

        return f"```json\n{json.dumps(self.valid_data, indent=2)}\n```"
