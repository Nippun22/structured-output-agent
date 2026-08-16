"""
Example 04: Live Execution with Anthropic Claude API (claude-3-5-sonnet)
"""

import os
from pydantic import BaseModel, Field
from structured_agent import StructuredAgent
from structured_agent.providers.claude_provider import ClaudeLLMProvider

# 1. Define Target Schema
class TechCandidateEvaluation(BaseModel):
    candidate_name: str = Field(..., min_length=2, description="Full name")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Evaluation score 0-100")
    key_strengths: list[str] = Field(..., min_length=1, description="List of technical strengths")
    hire_recommendation: bool = Field(..., description="True if recommended to hire")

def main():
    print("==================================================================")
    print("       DEMO 04: ANTHROPIC CLAUDE 3.5 SONNET STRUCTURED RUN        ")
    print("==================================================================")

    # Check for ANTHROPIC_API_KEY
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n [WARNING] ANTHROPIC_API_KEY environment variable is not set!")
        print("Please set your API key in PowerShell before running:")
        print("   $env:ANTHROPIC_API_KEY=\"sk-ant-your-key-here\"\n")
        return

    # Initialize Claude 3.5 Sonnet Provider
    provider = ClaudeLLMProvider(model_name="claude-3-5-sonnet-20241022", api_key=api_key)
    agent = StructuredAgent(provider=provider, agent_name="ClaudeEvaluator")

    user_query = "Evaluate candidate Alex Rivera with 92.5 score skilled in Python, PyTorch, and Distributed Systems."

    result = agent.run(
        user_prompt=user_query,
        response_model=TechCandidateEvaluation
    )

    if result.is_valid:
        eval_obj: TechCandidateEvaluation = result.parsed_object
        print("\n Successfully extracted and validated object with Claude:")
        print(f"Name: {eval_obj.candidate_name}")
        print(f"Score: {eval_obj.overall_score}/100")
        print(f"Hire: {eval_obj.hire_recommendation}")
        print(f"Strengths: {eval_obj.key_strengths}")
    else:
        print("\n Validation Failed:")
        for err in result.errors:
            print(" -", err)

if __name__ == "__main__":
    main()
