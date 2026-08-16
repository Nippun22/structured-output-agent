import sys
import os
import json
import streamlit as st
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

# Ensure structured_agent is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from structured_agent import StructuredAgent
from structured_agent.providers.mock_provider import MockLLMProvider
from structured_agent.providers.gemini_provider import GeminiLLMProvider
from structured_agent.providers.openai_provider import OpenAILLMProvider
from structured_agent.telemetry.metrics import global_telemetry

st.set_page_config(
    page_title="Structured Output Agent Studio",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for modern UI styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1E1E2E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #313244;
        text-align: center;
    }
    .stCodeBlock {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.markdown('<div class="main-header">🛡️ Structured Output Agent Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Guaranteed Pydantic JSON Schema Validation, Auto-Repair Retry Loops & Telemetry for LLMs</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Agent & Provider Configuration")

provider_choice = st.sidebar.selectbox(
    "LLM Provider",
    ["Mock LLM (Fault Injection Demo)", "Google Gemini API", "OpenAI API"]
)

if provider_choice == "Mock LLM (Fault Injection Demo)":
    fault_mode = st.sidebar.selectbox(
        "Mock Fault Mode",
        ["auto_repair", "none", "json_error"],
        help="'auto_repair' simulates 1st attempt failure & 2nd attempt self-correction."
    )

    valid_data_preset = {
        "name": "David Miller",
        "age": 34,
        "email": "david.miller@techcorp.io",
        "skills": ["Python", "Pydantic", "Docker", "System Architecture"],
        "score": 96.5
    }
    provider = MockLLMProvider(fault_mode=fault_mode, valid_data=valid_data_preset)
elif provider_choice == "Google Gemini API":
    gemini_key = st.sidebar.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
    gemini_model = st.sidebar.text_input("Gemini Model", value="gemini-2.5-flash")
    if not gemini_key:
        st.sidebar.warning("Please enter your GEMINI_API_KEY to run live calls.")
    provider = GeminiLLMProvider(model_name=gemini_model, api_key=gemini_key)
else:
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    openai_model = st.sidebar.text_input("OpenAI Model", value="gpt-4o-mini")
    if not openai_key:
        st.sidebar.warning("Please enter your OPENAI_API_KEY to run live calls.")
    provider = OpenAILLMProvider(model_name=openai_model, api_key=openai_key)

max_retries = st.sidebar.slider("Max Self-Correction Retries", min_value=1, max_value=5, value=3)

# Target Pydantic Schema Options
st.subheader("1️⃣ Select Target Pydantic Schema")

class CandidateProfile(BaseModel):
    name: str = Field(..., min_length=2, description="Candidate name")
    age: int = Field(..., ge=18, le=100, description="Age between 18 and 100")
    email: EmailStr = Field(..., description="Valid corporate email")
    skills: List[str] = Field(..., min_length=1, description="List of skills")
    score: float = Field(..., ge=0.0, le=100.0, description="Score 0-100")

class FinancialSecurityAnalysis(BaseModel):
    ticker: str = Field(..., description="Stock symbol e.g. NVDA, AAPL")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Risk rating 0-10")
    buy_recommendation: bool = Field(..., description="True if recommended buy")
    catalysts: List[str] = Field(..., min_length=1, description="Key growth triggers")

schema_option = st.radio(
    "Choose target output schema:",
    ["Candidate Profile (User, Age, Email, Skills, Score)", "Financial Security Analysis (Ticker, Risk, Recommendation)"],
    horizontal=True
)

target_model = CandidateProfile if "Candidate" in schema_option else FinancialSecurityAnalysis

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("**Target Pydantic Model Schema (JSON)**:")
    st.json(target_model.model_json_schema())

with col_right:
    st.markdown("**User Query Prompt**:")
    default_prompt = (
        "Extract candidate profile for David Miller, age 34, email david.miller@techcorp.io, skilled in Python, Pydantic, Docker with score 96.5"
        if "Candidate" in schema_option else
        "Analyze NVIDIA (NVDA) stock with a low risk score of 2.5, buy recommendation true, and key catalysts: AI Chips, Data Center Growth."
    )
    user_prompt_input = st.text_area("Query", value=default_prompt, height=120)

    run_button = st.button("🚀 Run Agent Execution", type="primary", use_container_width=True)

# Main Execution Flow
if run_button:
    st.subheader("2️⃣ Execution & Live Retry Trace")

    agent = StructuredAgent(
        provider=provider,
        max_retries=max_retries,
        agent_name="StudioAgent",
        verbose=False  # We handle Streamlit display
    )

    with st.spinner("Invoking LLM & Enforcing Pydantic Schema..."):
        result = agent.run(
            user_prompt=user_prompt_input,
            response_model=target_model
        )

    if result.is_valid:
        st.success(f"✅ **SUCCESS** - Output validated against Pydantic schema in {result.retry_count + 1} attempt(s)!")

        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.markdown("### Validated Python Object Instance")
            st.write(result.parsed_object)

        with res_col2:
            st.markdown("### Validated Clean JSON")
            st.code(result.cleaned_json_str, language="json")
    else:
        st.error(f"❌ **VALIDATION FAILED** - Exceeded max retries ({max_retries}) without satisfying Pydantic schema.")

        if result.errors:
            st.markdown("### Validation Error Table")
            err_data = [
                {
                    "Field Path": " -> ".join(e.loc),
                    "Error Message": e.message,
                    "Error Code": e.error_type,
                    "Provided Value": repr(e.provided_value)
                }
                for e in result.errors
            ]
            st.table(err_data)

    # Diagnostic Repair Prompt View
    if result.repair_prompt:
        with st.expander("🔍 View Diagnostic Feedback Repair Prompt sent to LLM"):
            st.code(result.repair_prompt, language="markdown")

# Telemetry Dashboard Section
st.markdown("---")
st.subheader("3️⃣ Reliability & Telemetry Analytics")

summary = global_telemetry.get_summary()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Runs", summary["total_runs"])
m2.metric("Overall Success Rate", summary["overall_success_rate"])
m3.metric("First-Pass Accuracy", summary["first_pass_accuracy"])
m4.metric("Auto-Repair Recovery Rate", summary["auto_repair_recovery_rate"])

if summary["error_breakdown"]:
    st.markdown("**Validation Error Classifications Breakdown**:")
    st.bar_chart(summary["error_breakdown"])
