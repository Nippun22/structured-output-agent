from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ExecutionMetric(BaseModel):
    """Record of a single agent execution run."""
    run_id: str
    target_schema: str
    success: bool
    first_pass_success: bool
    total_retries: int
    error_types: List[str] = Field(default_factory=list)

class AgentTelemetryCollector:
    """Collects and aggregates performance and reliability metrics for structured output agents."""

    def __init__(self):
        self.records: List[ExecutionMetric] = []

    def record_run(
        self,
        run_id: str,
        target_schema: str,
        success: bool,
        total_retries: int,
        error_types: List[str]
    ):
        first_pass = (success and total_retries == 0)
        metric = ExecutionMetric(
            run_id=run_id,
            target_schema=target_schema,
            success=success,
            first_pass_success=first_pass,
            total_retries=total_retries,
            error_types=error_types
        )
        self.records.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        total_runs = len(self.records)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "overall_success_rate": "0.0%",
                "first_pass_accuracy": "0.0%",
                "auto_repair_recovery_rate": "0.0%",
                "total_retries": 0,
                "error_breakdown": {}
            }

        successful_runs = sum(1 for r in self.records if r.success)
        first_pass_successes = sum(1 for r in self.records if r.first_pass_success)
        repaired_runs = sum(1 for r in self.records if r.success and r.total_retries > 0)
        failed_runs_with_retries = sum(1 for r in self.records if not r.success and r.total_retries > 0)

        total_retries = sum(r.total_retries for r in self.records)

        # Auto-repair recovery rate = repaired_runs / (repaired_runs + failed_runs_with_retries)
        repair_denominator = repaired_runs + failed_runs_with_retries
        auto_repair_rate = (repaired_runs / repair_denominator * 100) if repair_denominator > 0 else 100.0

        error_counts: Dict[str, int] = {}
        for r in self.records:
            for err in r.error_types:
                error_counts[err] = error_counts.get(err, 0) + 1

        return {
            "total_runs": total_runs,
            "overall_success_rate": f"{(successful_runs / total_runs) * 100:.1f}%",
            "first_pass_accuracy": f"{(first_pass_successes / total_runs) * 100:.1f}%",
            "auto_repair_recovery_rate": f"{auto_repair_rate:.1f}%",
            "total_retries_executed": total_retries,
            "error_breakdown": error_counts
        }

# Global singleton collector
global_telemetry = AgentTelemetryCollector()
