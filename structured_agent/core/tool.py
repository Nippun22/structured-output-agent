import inspect
import json
from typing import Callable, Any, Dict, Optional, Type, get_type_hints
from pydantic import BaseModel, create_model, ValidationError

class ToolExecutionError(Exception):
    """Raised when tool execution fails or arguments violate schema."""
    pass

class Tool:
    """
    Type-safe Tool wrapper for agents.
    Validates tool inputs (arguments) and outputs against Pydantic schemas.
    """
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        args_schema: Optional[Type[BaseModel]] = None,
        output_schema: Optional[Type[BaseModel]] = None
    ):
        self.name = name
        self.description = description.strip()
        self.func = func
        self.args_schema = args_schema or self._infer_schema_from_func(func, name)
        self.output_schema = output_schema

    @classmethod
    def _infer_schema_from_func(cls, func: Callable[..., Any], name: str) -> Type[BaseModel]:
        """Automatically creates a Pydantic model for function arguments based on type hints."""
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        fields: Dict[str, Any] = {}

        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            param_type = type_hints.get(param_name, Any)
            if param.default is inspect.Parameter.empty:
                fields[param_name] = (param_type, ...)
            else:
                fields[param_name] = (param_type, param.default)

        return create_model(f"{name.capitalize()}Args", **fields)

    def get_json_schema(self) -> Dict[str, Any]:
        """Returns OpenAPI/JSON schema representation for LLM function calling formats."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema()
        }

    def execute(self, raw_args: Dict[str, Any] | str) -> Dict[str, Any]:
        """
        Validates input arguments, invokes the underlying function, and validates output.
        """
        # Parse arguments if string
        if isinstance(raw_args, str):
            try:
                args_dict = json.loads(raw_args)
            except json.JSONDecodeError as err:
                raise ToolExecutionError(f"Tool `{self.name}` received invalid JSON arguments: {err}")
        else:
            args_dict = raw_args

        # 1. Validate Input Arguments against args_schema
        try:
            validated_args = self.args_schema.model_validate(args_dict)
        except ValidationError as val_err:
            raise ToolExecutionError(f"Tool `{self.name}` argument validation failed:\n{val_err}")

        # 2. Execute underlying function
        try:
            result = self.func(**validated_args.model_dump())
        except Exception as e:
            raise ToolExecutionError(f"Tool `{self.name}` runtime execution error: {e}")

        # 3. Validate Output Schema if provided
        if self.output_schema:
            if isinstance(result, self.output_schema):
                return {"success": True, "output": result.model_dump()}
            elif isinstance(result, dict):
                try:
                    val_out = self.output_schema.model_validate(result)
                    return {"success": True, "output": val_out.model_dump()}
                except ValidationError as val_err:
                    raise ToolExecutionError(f"Tool `{self.name}` output failed schema validation:\n{val_err}")
            else:
                try:
                    val_out = self.output_schema.model_validate({"result": result})
                    return {"success": True, "output": val_out.model_dump()}
                except ValidationError:
                    raise ToolExecutionError(f"Tool `{self.name}` output `{result}` does not conform to output schema.")

        # Default string/dict response wrap
        if isinstance(result, BaseModel):
            return {"success": True, "output": result.model_dump()}
        return {"success": True, "output": result}

def tool(name: Optional[str] = None, description: Optional[str] = None, output_schema: Optional[Type[BaseModel]] = None):
    """Decorator to easily create Tool instances from functions."""
    def decorator(func: Callable[..., Any]) -> Tool:
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Execute tool {tool_name}"
        return Tool(name=tool_name, description=tool_desc, func=func, output_schema=output_schema)
    return decorator
