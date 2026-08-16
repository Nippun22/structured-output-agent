import os
from typing import List, Dict, Any, Optional
from structured_agent.providers.base import BaseLLMProvider

class ClaudeLLMProvider(BaseLLMProvider):
    """Anthropic Claude API Provider for Claude 3.5 Sonnet / Haiku models."""

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
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
                "Anthropic Claude API Key missing or anthropic library unavailable. "
                "Please set ANTHROPIC_API_KEY environment variable or pass api_key to ClaudeLLMProvider."
            )

        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            # Anthropic messages API only accepts 'user' and 'assistant' roles
            if role in ("user", "assistant"):
                formatted_messages.append({"role": role, "content": msg.get("content", "")})
            elif role == "system":
                # System prompt is passed separately in system parameter
                if system_instruction:
                    system_instruction += f"\n\nSystem Note:\n{msg.get('content', '')}"
                else:
                    system_instruction = msg.get("content", "")

        response = self._client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_instruction or "You are an expert AI assistant that provides strictly structured JSON outputs.",
            messages=formatted_messages,
            temperature=temperature
        )

        if response.content and len(response.content) > 0:
            return response.content[0].text or ""
        return ""
