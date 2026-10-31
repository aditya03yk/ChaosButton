"""Persisted, deterministic experiment metrics."""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.core.clock import utcnow


class ExperimentMetrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", unique=True, index=True)
    # Fault-period measurements
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_count: int = 0
    success_rate: Optional[float] = None
    error_rate: Optional[float] = None
    p50_latency: Optional[float] = None
    p95_latency: Optional[float] = None
    average_latency: Optional[float] = None
    fallback_score: Optional[float] = None
    recovery_time: Optional[float] = None
    resilience_score: Optional[float] = None
    # Baseline and context
    baseline_requests: int = 0
    baseline_p50_latency: Optional[float] = None
    baseline_p95_latency: Optional[float] = None
    sample_size: int = 0
    score_components: dict = Field(default_factory=dict, sa_column=Column(JSON))
    limitations: list = Field(default_factory=list, sa_column=Column(JSON))
    calculated_at: datetime = Field(default_factory=utcnow)
