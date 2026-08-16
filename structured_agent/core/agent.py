import uuid
from typing import Type, TypeVar, List, Dict, Any, Optional
from pydantic import BaseModel

from structured_agent.core.schema import ValidationResult, AgentMessage
from structured_agent.core.validator import SchemaValidator
from structured_agent.core.tool import Tool
from structured_agent.providers.base import BaseLLMProvider
from structured_agent.providers.mock_provider import MockLLMProvider
from structured_agent.telemetry.logger import get_logger, AgentLogger
from structured_agent.telemetry.metrics import global_telemetry

T = TypeVar("T", bound=BaseModel)

class StructuredAgent:
    """
    Enterprise-Grade Structured Output Agent.
    Enforces Pydantic schemas, handles self-correction retries on validation errors,
    executes type-safe tools, and records telemetry.
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        tools: Optional[List[Tool]] = None,
        max_retries: int = 3,
        agent_name: str = "StructuredAgent",
        verbose: bool = True
    ):
        self.provider = provider or MockLLMProvider()
        self.tools: Dict[str, Tool] = {t.name: t for t in (tools or [])}
        self.max_retries = max_retries
        self.agent_name = agent_name
        self.logger: AgentLogger = get_logger(agent_name=agent_name, verbose=verbose)

    def run(
        self,
        user_prompt: str,
        response_model: Type[T],
        system_instruction: Optional[str] = None
    ) -> ValidationResult[T]:
        """
        Executes user prompt against the LLM, enforcing the response_model schema
        with self-correcting retry loop up to max_retries.
        """
        run_id = str(uuid.uuid4())[:8]
        self.logger.log_header(f"Starting Run [{run_id}] - Schema: {response_model.__name__}")

        schema_json = response_model.model_json_schema()

        # Build base system instruction with JSON Schema guidance
        base_system = (
            f"{system_instruction or 'You are an expert AI assistant that provides strictly structured JSON outputs.'}\n\n"
            "CRITICAL INSTRUCTION:\n"
            "You MUST respond ONLY with a single valid JSON object adhering exactly to the following Pydantic JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            "Do not add markdown text outside the JSON block."
        )

        messages: List[Dict[str, str]] = [
            {"role": "user", "content": user_prompt}
        ]

        attempt = 1
        error_history_types: List[str] = []

        while attempt <= self.max_retries + 1:
            self.logger.log_prompt(system_prompt=base_system, user_prompt=messages[-1]["content"], attempt=attempt)

            # Generate response from provider
            try:
                raw_response = self.provider.generate(
                    messages=messages,
                    system_instruction=base_system
                )
            except Exception as llm_err:
                self.logger.log_fatal_error(f"LLM Provider Generation Failed: {llm_err}")
                global_telemetry.record_run(
                    run_id=run_id,
                    target_schema=response_model.__name__,
                    success=False,
                    total_retries=attempt - 1,
                    error_types=["llm_provider_error"]
                )
                return ValidationResult(
                    is_valid=False,
                    parsed_object=None,
                    raw_response=f"LLM Provider Error: {llm_err}",
                    cleaned_json_str=None,
                    errors=[],
                    retry_count=attempt - 1,
                    repair_prompt=None
                )

            self.logger.log_raw_response(raw_response)

            # Validate response against Pydantic schema
            val_result = SchemaValidator.validate(
                raw_response=raw_response,
                schema_class=response_model,
                retry_count=attempt - 1
            )

            if val_result.is_valid:
                self.logger.log_validation_success(val_result.parsed_object, attempt=attempt)
                global_telemetry.record_run(
                    run_id=run_id,
                    target_schema=response_model.__name__,
                    success=True,
                    total_retries=attempt - 1,
                    error_types=error_history_types
                )
                return val_result

            # If validation failed
            for err in val_result.errors:
                error_history_types.append(err.error_type)

            self.logger.log_validation_failure(val_result.errors, attempt=attempt, max_retries=self.max_retries + 1)

            # If max retries reached, return failure
            if attempt > self.max_retries:
                self.logger.log_fatal_error(f"Max retries ({self.max_retries}) exceeded without valid schema match.")
                global_telemetry.record_run(
                    run_id=run_id,
                    target_schema=response_model.__name__,
                    success=False,
                    total_retries=attempt - 1,
                    error_types=error_history_types
                )
                return val_result

            # Prepare for self-correction retry
            repair_prompt = val_result.repair_prompt or "Your output was invalid. Please fix and return JSON."
            self.logger.log_retry_notice(repair_prompt, next_attempt=attempt + 1)

            # Append the assistant's bad response and user repair prompt to message history
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": repair_prompt})

            attempt += 1

        global_telemetry.record_run(
            run_id=run_id,
            target_schema=response_model.__name__,
            success=False,
            total_retries=attempt - 1,
            error_types=error_history_types
        )
        return val_result
