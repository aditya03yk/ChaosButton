"""Persisted Gemma analyses."""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.core.clock import utcnow


class AIAnalysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    model_name: str
    finding: str
    severity: str
    severity_rationale: str
    what_happened: str = ""
    user_impact: str = ""
    evidence: list = Field(default_factory=list, sa_column=Column(JSON))
    likely_cause: str
    recommended_actions: list = Field(default_factory=list, sa_column=Column(JSON))
    code_example: dict = Field(default_factory=dict, sa_column=Column(JSON))
    verification_steps: list = Field(default_factory=list, sa_column=Column(JSON))
    raw_status: str = "validated"
    created_at: datetime = Field(default_factory=utcnow)
