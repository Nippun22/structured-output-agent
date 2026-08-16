"""
Example 03: Live Fault Injection & Self-Correction Retry Loop
Demonstrates how the agent automatically detects malformed JSON and Pydantic validation errors,
generates diagnostic error feedback prompts, and forces the LLM to self-repair its output.
"""

from typing import List
from pydantic import BaseModel, Field, EmailStr
from structured_agent import StructuredAgent
from structured_agent.providers.mock_provider import MockLLMProvider
from structured_agent.telemetry.metrics import global_telemetry

# 1. Define Target Schema with strict constraints
class UserCandidateProfile(BaseModel):
    name: str = Field(..., min_length=2, description="Candidate full name")
    age: int = Field(..., ge=18, le=100, description="Age in years (integer between 18 and 100)")
    email: EmailStr = Field(..., description="Valid candidate email address")
    skills: List[str] = Field(..., min_length=1, description="List of technical skills")
    score: float = Field(..., ge=0.0, le=100.0, description="Evaluation score (0.0 to 100.0)")

def main():
    print("==================================================================")
    print("     DEMO 03: LIVE FAULT INJECTION & SELF-CORRECTION RETRY        ")
    print("==================================================================")
    print("Scenario: The LLM initially outputs invalid data (age as string,")
    print("skills as string instead of list, score > 100). The agent will")
    print("catch these Pydantic errors and auto-repair in Retry #2.")
    print("------------------------------------------------------------------\n")

    # Target valid response for Attempt 2 after self-correction
    valid_repaired_data = {
        "name": "Alice Johnson",
        "age": 28,
        "email": "alice@example.com",
        "skills": ["Python", "Machine Learning", "Pydantic"],
        "score": 94.5
    }

    # Initialize provider in 'auto_repair' fault injection mode
    provider = MockLLMProvider(fault_mode="auto_repair", valid_data=valid_repaired_data)
    agent = StructuredAgent(provider=provider, max_retries=3, agent_name="CandidateEvaluator")

    user_query = "Extract profile details for candidate Alice Johnson."

    result = agent.run(
        user_prompt=user_query,
        response_model=UserCandidateProfile,
        system_instruction="Extract candidate profile data."
    )

    print("\n------------------------------------------------------------------")
    print("                      FINAL RUN OUTCOME                           ")
    print("------------------------------------------------------------------")
    print(f"Is Valid: {result.is_valid}")
    print(f"Total Retries Needed: {result.retry_count}")

    if result.is_valid:
        profile: UserCandidateProfile = result.parsed_object
        print("\n Repaired Candidate Profile:")
        print(f" Name: {profile.name}")
        print(f" Age: {profile.age} (Fixed integer constraint!)")
        print(f" Email: {profile.email}")
        print(f" Skills: {profile.skills} (Fixed List[str] type!)")
        print(f" Score: {profile.score}/100 (Fixed bounds <= 100!)")

    print("\n==================================================================")
    print("                    TELEMETRY SUMMARY                             ")
    print("==================================================================")
    import json
    print(json.dumps(global_telemetry.get_summary(), indent=2))

if __name__ == "__main__":
    main()
