from typing import Any, Generic, TypeVar, Optional, List, Dict
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

class ValidationErrorDetail(BaseModel):
    """Detailed metadata for a single schema validation failure."""
    loc: List[str] = Field(default_factory=list, description="JSON path field location of error")
    message: str = Field(..., description="Human-readable validation error description")
    error_type: str = Field(..., description="Pydantic validation error code")
    provided_value: Optional[Any] = Field(None, description="The invalid value supplied by the LLM")

class ValidationResult(BaseModel, Generic[T]):
    """Container for LLM output validation outcomes."""
    is_valid: bool = Field(..., description="True if output parsed and passed all Pydantic validators")
    parsed_object: Optional[Any] = Field(None, description="Validated Pydantic object instance if valid")
    raw_response: str = Field(..., description="Original raw text response from the LLM")
    cleaned_json_str: Optional[str] = Field(None, description="Extracted JSON string before validation")
    errors: List[ValidationErrorDetail] = Field(default_factory=list, description="Validation failure details")
    retry_count: int = Field(0, description="Number of repair retries required")
    repair_prompt: Optional[str] = Field(None, description="Self-correction feedback prompt sent to LLM")

class AgentMessage(BaseModel):
    """Standardized internal chat message."""
    role: str = Field(..., description="'system', 'user', 'assistant', or 'tool'")
    content: str = Field(..., description="Text payload of the message")
    name: Optional[str] = Field(None, description="Optional tool name or sender identity")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Structured tool call payload")
