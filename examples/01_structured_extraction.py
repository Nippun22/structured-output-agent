"""
Example 01: Basic Structured Output Extraction with Pydantic Enforcement
Demonstrates creating complex nested Pydantic models and enforcing type safety on LLM outputs.
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
from structured_agent import StructuredAgent
from structured_agent.providers.mock_provider import MockLLMProvider

# 1. Define Enum & Nested Pydantic Schemas
class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class InvestmentRecommendation(BaseModel):
    asset_class: str = Field(..., description="Target asset type e.g. Equities, Bonds, Crypto")
    allocation_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of portfolio (0-100)")
    rationale: str = Field(..., description="Strategic justification for allocation")

class PortfolioAnalysisReport(BaseModel):
    investor_name: str = Field(..., min_length=2, description="Name of account holder")
    risk_profile: RiskLevel = Field(..., description="Categorized risk profile")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0")
    recommendations: List[InvestmentRecommendation] = Field(..., min_length=1, description="List of allocation recommendations")
    disclaimer: str = Field(..., description="Mandatory regulatory disclaimer")

    @field_validator("recommendations")
    def validate_allocations_sum(cls, v: List[InvestmentRecommendation]) -> List[InvestmentRecommendation]:
        total = sum(r.allocation_percentage for r in v)
        if not (99.0 <= total <= 101.0):
            raise ValueError(f"Investment allocations must sum up to ~100%. Current sum: {total:.1f}%")
        return v

def main():
    print("==================================================================")
    print("      DEMO 01: STRUCTURED PORTFOLIO ANALYSIS EXTRACTION          ")
    print("==================================================================")

    # Mock data representing expected output
    mock_payload = {
        "investor_name": "Sophia Martinez",
        "risk_profile": "MEDIUM",
        "confidence_score": 0.94,
        "recommendations": [
            {
                "asset_class": "US Tech Equities (S&P 500)",
                "allocation_percentage": 50.0,
                "rationale": "Strong historical performance and growth trajectory."
            },
            {
                "asset_class": "Government Treasury Bonds",
                "allocation_percentage": 30.0,
                "rationale": "Capital preservation and steady yield income."
            },
            {
                "asset_class": "Global REITs",
                "allocation_percentage": 20.0,
                "rationale": "Real estate diversification against inflation."
            }
        ],
        "disclaimer": "This report is for educational purposes and does not constitute formal financial advice."
    }

    # Initialize Mock Provider with valid data
    provider = MockLLMProvider(fault_mode="none", valid_data=mock_payload)
    agent = StructuredAgent(provider=provider, agent_name="PortfolioAnalyst")

    user_query = "Analyze investor Sophia Martinez with a moderate risk appetite and recommend a $100k portfolio allocation."

    result = agent.run(
        user_prompt=user_query,
        response_model=PortfolioAnalysisReport,
        system_instruction="You are a certified senior financial strategist."
    )

    if result.is_valid:
        report: PortfolioAnalysisReport = result.parsed_object
        print("\n Successfully extracted and validated object:")
        print(f"Investor: {report.investor_name}")
        print(f"Risk Level: {report.risk_profile.value}")
        print(f"Confidence: {report.confidence_score * 100}%")
        print("\nAllocations:")
        for r in report.recommendations:
            print(f" - {r.asset_class}: {r.allocation_percentage}% ({r.rationale})")
    else:
        print("\n Extraction failed:")
        for err in result.errors:
            print(f" - {err}")

if __name__ == "__main__":
    main()
