from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract interface for LLM Providers (Gemini, OpenAI, Mock)."""

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """
        Sends chat history to LLM and returns the raw string response.
        """
        pass
