import json
import re
from typing import Type, TypeVar, Tuple, List, Optional, Any
from pydantic import BaseModel, ValidationError

from structured_agent.core.schema import ValidationResult, ValidationErrorDetail

T = TypeVar("T", bound=BaseModel)

class SchemaValidator:
    """
    Parses and validates LLM string outputs against arbitrary Pydantic schemas.
    Generates intelligent error feedback prompts for self-correction retries.
    """

    @staticmethod
    def extract_json_string(raw_text: str) -> str:
        """
        Extract clean JSON string from LLM response text, stripping markdown code blocks,
        preceding chatter, or trailing commentary.
        """
        if not raw_text or not raw_text.strip():
            return ""

        text = raw_text.strip()

        # Check for standard ```json ... ``` or ``` ... ``` code blocks
        json_code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if json_code_block_match:
            return json_code_block_match.group(1).strip()

        # Search for first '{' or '[' and last '}' or ']'
        obj_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if obj_match:
            return obj_match.group(1).strip()

        return text

    @classmethod
    def validate(cls, raw_response: str, schema_class: Type[T], retry_count: int = 0) -> ValidationResult[T]:
        """
        Validates raw response text against the given Pydantic model class.
        Returns a ValidationResult containing success state or diagnostic error feedback.
        """
        cleaned = cls.extract_json_string(raw_response)

        # 1. Test JSON Syntax
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as err:
            error_detail = ValidationErrorDetail(
                loc=["<JSON_PARSER>"],
                message=f"JSON Decode Error at line {err.lineno}, col {err.colno}: {err.msg}",
                error_type="json_decode_error",
                provided_value=cleaned[:200]
            )
            repair_prompt = cls._build_repair_prompt(
                schema_class=schema_class,
                raw_response=raw_response,
                errors=[error_detail],
                is_json_error=True
            )
            return ValidationResult(
                is_valid=False,
                parsed_object=None,
                raw_response=raw_response,
                cleaned_json_str=cleaned,
                errors=[error_detail],
                retry_count=retry_count,
                repair_prompt=repair_prompt
            )

        # 2. Test Pydantic Schema Validation
        try:
            parsed_inst = schema_class.model_validate(data)
            return ValidationResult(
                is_valid=True,
                parsed_object=parsed_inst,
                raw_response=raw_response,
                cleaned_json_str=cleaned,
                errors=[],
                retry_count=retry_count,
                repair_prompt=None
            )
        except ValidationError as val_err:
            error_details: List[ValidationErrorDetail] = []
            for e in val_err.errors():
                loc_strs = [str(x) for x in e.get("loc", [])]
                error_details.append(
                    ValidationErrorDetail(
                        loc=loc_strs,
                        message=e.get("msg", "Validation error"),
                        error_type=e.get("type", "value_error"),
                        provided_value=e.get("input")
                    )
                )

            repair_prompt = cls._build_repair_prompt(
                schema_class=schema_class,
                raw_response=raw_response,
                errors=error_details,
                is_json_error=False
            )

            return ValidationResult(
                is_valid=False,
                parsed_object=None,
                raw_response=raw_response,
                cleaned_json_str=cleaned,
                errors=error_details,
                retry_count=retry_count,
                repair_prompt=repair_prompt
            )

    @classmethod
    def _build_repair_prompt(
        cls,
        schema_class: Type[T],
        raw_response: str,
        errors: List[ValidationErrorDetail],
        is_json_error: bool
    ) -> str:
        """
        Constructs an explicit feedback prompt instructing the LLM on how to fix its response.
        """
        schema_json = json.dumps(schema_class.model_json_schema(), indent=2)

        prompt_lines = [
            "Your previous response failed validation and could not be processed.",
            "=== EXPECTED PYDANTIC JSON SCHEMA ===",
            schema_json,
            "====================================",
            "",
            "=== YOUR PREVIOUS INVALID RESPONSE ===",
            raw_response,
            "=====================================",
            "",
            "=== VALIDATION ERRORS FOUND ==="
        ]

        for i, err in enumerate(errors, 1):
            path_str = " -> ".join(err.loc) if err.loc else "root"
            prompt_lines.append(f"{i}. Field Path: `{path_str}`")
            prompt_lines.append(f"   Error Message: {err.message}")
            prompt_lines.append(f"   Error Code: {err.error_type}")
            if err.provided_value is not None:
                prompt_lines.append(f"   Received Value: {repr(err.provided_value)}")

        prompt_lines.extend([
            "===============================",
            "",
            "INSTRUCTIONS FOR CORRECTION:",
            "1. Output ONLY a valid JSON object wrapped in ```json ... ``` syntax.",
            "2. Ensure all required fields specified in the schema are present.",
            "3. Ensure all values match the exact types, bounds, and enum constraints.",
            "4. Do NOT include any intro text, conversational filler, or explanations outside the JSON."
        ])

        return "\n".join(prompt_lines)
