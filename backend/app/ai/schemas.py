"""Validated AI input/output schemas."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CodeExample(BaseModel):
    language: str = Field(min_length=1)
    snippet: str = Field(min_length=1)
    assumptions: str = ""


class AnalysisResult(BaseModel):
    """Required response schema (core fields) plus explainer metadata."""
    finding: str = Field(min_length=3)
    severity: Severity
    severity_rationale: str = Field(min_length=3)
    what_happened: str = ""
    user_impact: str = ""
    evidence: list[str] = Field(min_length=1)
    likely_cause: str = Field(min_length=3)
    recommended_actions: list[str] = Field(min_length=1)
    code_example: CodeExample
    verification_steps: list[str] = Field(min_length=1)


class FixValidation(BaseModel):
    summary: str = Field(min_length=3)
    improvements: list[str] = []
    regressions: list[str] = []
    remaining_weaknesses: list[str] = []


class AIStatus(BaseModel):
    provider: str
    model: str
    reachable: bool
    model_available: bool
    message: str
    hint: Optional[str] = None


class AnalysisRequest(BaseModel):
    code_context: Optional[str] = Field(None, max_length=8000)
