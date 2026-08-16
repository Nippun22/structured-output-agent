import os
from typing import List, Dict, Any, Optional
from structured_agent.providers.base import BaseLLMProvider

class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API Provider for GPT-4o / GPT-3.5 models."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                pass

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        if not self.api_key or not self._client:
            raise ValueError(
                "OpenAI API Key missing or openai library unavailable. "
                "Please set OPENAI_API_KEY environment variable or use MockLLMProvider for offline testing."
            )

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})

        for msg in messages:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=formatted_messages,
            temperature=temperature
        )
        return response.choices[0].message.content or ""
