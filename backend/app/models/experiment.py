"""Experiment models, enums and creation schemas (with hard safety limits)."""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from app.core.clock import utcnow
from app.core.config import get_settings


class FaultType(str, Enum):
    LATENCY = "latency"
    TIMEOUT = "timeout"
    HTTP_500 = "http_500"
    HTTP_503 = "http_503"


class FaultScope(str, Enum):
    INBOUND = "inbound"        # faults on client -> target requests
    DEPENDENCY = "dependency"  # faults on target -> upstream dependency requests


class ExperimentMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class ExperimentStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    BASELINE = "BASELINE"
    RUNNING = "RUNNING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


TERMINAL_STATUSES = {ExperimentStatus.COMPLETED, ExperimentStatus.STOPPED, ExperimentStatus.FAILED}


def new_experiment_id() -> str:
    return f"exp_{uuid4().hex[:10]}"


class FaultParams(BaseModel):
    scope: FaultScope = FaultScope.INBOUND
    dependency_route: Optional[str] = None
    delay_ms: Optional[int] = Field(None, ge=1)
    timeout_ms: Optional[int] = Field(None, ge=1)
    duration_s: int = Field(30, ge=1)
    max_affected: int = Field(10, ge=1)
    baseline_requests: int = Field(10, ge=1)
    request_timeout_ms: int = Field(5000, ge=100)
    concurrency: int = Field(1, ge=1)
    interval_ms: int = Field(100, ge=0, le=5000)


class Experiment(SQLModel, table=True):
    id: str = SQLField(default_factory=new_experiment_id, primary_key=True)
    target_id: int = SQLField(foreign_key="target.id", index=True)
    suite_id: Optional[str] = SQLField(default=None, index=True)
    name: str = ""
    mode: str = ExperimentMode.MANUAL.value
    route: str
    method: str = "GET"
    fault_type: str = SQLField(index=True)
    fault_configuration: dict = SQLField(default_factory=dict, sa_column=Column(JSON))
    status: str = SQLField(default=ExperimentStatus.CREATED.value, index=True)
    notes: str = ""
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    parent_experiment_id: Optional[str] = SQLField(default=None, index=True)
    created_at: datetime = SQLField(default_factory=utcnow, index=True)


class ExperimentCreate(BaseModel):
    target_id: int
    name: str = Field("", max_length=120)
    mode: ExperimentMode = ExperimentMode.MANUAL
    route: str = Field(min_length=1, max_length=200)
    method: str = Field("GET", pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    fault_type: FaultType
    fault_configuration: FaultParams = Field(default_factory=FaultParams)
    notes: str = Field("", max_length=1000)
    suite_id: Optional[str] = None
    parent_experiment_id: Optional[str] = None

    @model_validator(mode="after")
    def enforce_limits(self) -> "ExperimentCreate":
        """Apply defaults, then reject anything beyond the backend's hard limits."""
        limits, fault = get_settings(), self.fault_configuration
        if self.fault_type is FaultType.LATENCY and fault.delay_ms is None:
            fault.delay_ms = 500
        if self.fault_type is FaultType.TIMEOUT and fault.timeout_ms is None:
            fault.timeout_ms = 2000
        for value, limit, label in [
            (fault.duration_s, limits.max_experiment_duration, "duration_s"),
            (fault.max_affected, limits.max_affected_requests, "max_affected"),
            (fault.baseline_requests, limits.max_baseline_requests, "baseline_requests"),
            (fault.concurrency, limits.max_concurrency, "concurrency"),
            (fault.delay_ms or 0, limits.max_injected_delay_ms, "delay_ms"),
            (fault.timeout_ms or 0, limits.max_injected_delay_ms, "timeout_ms"),
        ]:
            if value > limit:
                raise ValueError(f"{label} exceeds the configured safety limit of {limit}")
        if not self.route.startswith("/") or self.route.rstrip("/*") == "":
            raise ValueError("route must start with '/' and be narrower than the whole site")
        if fault.scope is FaultScope.DEPENDENCY and not fault.dependency_route:
            raise ValueError("dependency_route is required for dependency-scoped faults")
        return self


class AutoSuiteRequest(BaseModel):
    target_id: int
    route: str = "/product"
    method: str = Field("GET", pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    scope: FaultScope = FaultScope.INBOUND
    dependency_route: Optional[str] = None


class RetestRequest(BaseModel):
    target_id: Optional[int] = None  # e.g. switch to the resilient demo app


class CompareRequest(BaseModel):
    other_experiment_id: str
    explain: bool = False
