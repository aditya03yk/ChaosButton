"""Per-request events and experiment timeline entries."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.clock import utcnow


class RequestEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    timestamp: datetime = Field(default_factory=utcnow)
    phase: str = "fault"  # baseline | fault | recovery
    route: str
    method: str
    status_code: Optional[int] = None
    latency_ms: float
    success: bool
    timed_out: bool = False
    fault_applied: bool = False
    fallback_used: bool = False
    error_category: Optional[str] = None


class TimelineEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: Optional[str] = Field(default=None, index=True)
    timestamp: datetime = Field(default_factory=utcnow, index=True)
    level: str = "info"  # info | warning | error | success
    kind: str = "system"
    message: str
