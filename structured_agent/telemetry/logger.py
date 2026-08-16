import logging
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "agent": "bold magenta",
})

console = Console(theme=custom_theme)

class AgentLogger:
    """Rich console logger for telemetry, prompt monitoring, and schema validation tracking."""

    def __init__(self, agent_name: str = "StructuredAgent", verbose: bool = True):
        self.agent_name = agent_name
        self.verbose = verbose

    def log_header(self, title: str):
        if not self.verbose:
            return
        console.print(Panel(f"[bold white]{title}[/bold white]", title=f"[Agent: {self.agent_name}]", border_style="magenta"))

    def log_prompt(self, system_prompt: str, user_prompt: str, attempt: int = 1):
        if not self.verbose:
            return
        console.print(f"[info]-> Attempt {attempt}: Invoking LLM...[/info]")

    def log_raw_response(self, raw_text: str):
        if not self.verbose:
            return
        preview = raw_text.strip() if len(raw_text) < 300 else raw_text.strip()[:300] + "..."
        console.print(f"[dim]LLM Response preview: {preview}[/dim]")

    def log_validation_success(self, parsed_object: Any, attempt: int):
        if not self.verbose:
            return
        console.print(f"[success][PASS] VALIDATION SUCCESSFUL (Attempt {attempt})[/success]")
        syntax = Syntax(str(parsed_object), "python", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="Validated Output Instance", border_style="green"))

    def log_validation_failure(self, errors: List[Any], attempt: int, max_retries: int):
        if not self.verbose:
            return
        console.print(f"[error][FAIL] VALIDATION FAILED (Attempt {attempt}/{max_retries})[/error]")

        table = Table(title="Schema Errors", show_header=True, header_style="bold red")
        table.add_column("Field Path", style="cyan")
        table.add_column("Error Message", style="yellow")
        table.add_column("Error Type", style="dim")

        for err in errors:
            path_str = " -> ".join(err.loc) if getattr(err, 'loc', None) else "root"
            msg = getattr(err, 'message', str(err))
            err_type = getattr(err, 'error_type', 'validation_error')
            table.add_row(path_str, msg, err_type)

        console.print(table)

    def log_retry_notice(self, repair_prompt: str, next_attempt: int):
        if not self.verbose:
            return
        console.print(f"[warning][RETRY] Initiating Retry #{next_attempt} with Diagnostic Error Prompt...[/warning]")

    def log_tool_call(self, tool_name: str, args: Dict[str, Any]):
        if not self.verbose:
            return
        console.print(f"[agent][TOOL] Executing Tool `{tool_name}` with args: {args}[/agent]")

    def log_tool_result(self, tool_name: str, result: Dict[str, Any]):
        if not self.verbose:
            return
        console.print(f"[success][TOOL] Tool `{tool_name}` execution successful.[/success]")

    def log_fatal_error(self, message: str):
        console.print(Panel(f"[bold red]{message}[/bold red]", title="FATAL ERROR", border_style="red"))


def get_logger(agent_name: str = "StructuredAgent", verbose: bool = True) -> AgentLogger:
    return AgentLogger(agent_name=agent_name, verbose=verbose)
