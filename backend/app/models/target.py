"""Target application models and schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from app.core.clock import utcnow


class TechStack(str, Enum):
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_FLASK = "python_flask"
    NODE_EXPRESS = "node_express"
    JAVA_SPRING = "java_spring"
    OTHER = "other"


class EnvironmentType(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    DEMO = "demo"


class Target(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str = SQLField(index=True)
    base_url: str
    description: str = ""
    technology_stack: str = TechStack.PYTHON_FASTAPI.value
    environment_type: str = EnvironmentType.LOCAL.value
    notes: str = ""
    ownership_confirmed: bool = False
    last_validated_at: Optional[datetime] = None
    last_validation_ok: Optional[bool] = None
    created_at: datetime = SQLField(default_factory=utcnow)
    updated_at: datetime = SQLField(default_factory=utcnow)


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=500)
    description: str = Field("", max_length=500)
    technology_stack: TechStack = TechStack.PYTHON_FASTAPI
    environment_type: EnvironmentType = EnvironmentType.LOCAL
    notes: str = Field("", max_length=1000)
    ownership_confirmed: bool = False


class TargetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    base_url: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=500)
    technology_stack: Optional[TechStack] = None
    environment_type: Optional[EnvironmentType] = None
    notes: Optional[str] = Field(None, max_length=1000)
    ownership_confirmed: Optional[bool] = None


class ValidationRequest(BaseModel):
    base_url: str = Field(min_length=1, max_length=500)
    ownership_confirmed: bool = False
    environment_type: EnvironmentType = EnvironmentType.LOCAL


class ValidationResult(BaseModel):
    valid: bool
    reachable: bool = False
    normalized_url: str = ""
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    errors: list[str] = []
    warnings: list[str] = []
