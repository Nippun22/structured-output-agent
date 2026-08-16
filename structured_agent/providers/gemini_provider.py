import os
from typing import List, Dict, Any, Optional
from structured_agent.providers.base import BaseLLMProvider

class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API Provider for real LLM invocations."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                # Will fallback to simple rest if needed
                pass

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        if not self.api_key or not self._client:
            raise ValueError(
                "Gemini API Key missing or google-genai library unavailable. "
                "Please set GEMINI_API_KEY environment variable or use MockLLMProvider for offline testing."
            )

        # Build contents from messages
        prompt_parts = []
        if system_instruction:
            prompt_parts.append(f"System Context:\n{system_instruction}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"[{role.upper()}]: {content}")

        full_prompt = "\n\n".join(prompt_parts)

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config={"temperature": temperature}
        )
        return response.text or ""
