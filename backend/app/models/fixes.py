"""Fix workspace records: proposed -> reviewed -> applied -> verified (manual steps)."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from app.core.clock import utcnow


class FixStatus(str, Enum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    APPLIED = "applied"
    VERIFIED = "verified"


FIX_ORDER = [FixStatus.PROPOSED, FixStatus.REVIEWED, FixStatus.APPLIED, FixStatus.VERIFIED]


class FixRecord(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    experiment_id: str = SQLField(foreign_key="experiment.id", index=True)
    analysis_id: int = SQLField(foreign_key="aianalysis.id")
    status: str = FixStatus.PROPOSED.value
    developer_notes: str = ""
    created_at: datetime = SQLField(default_factory=utcnow)
    updated_at: datetime = SQLField(default_factory=utcnow)


class FixUpdate(BaseModel):
    status: Optional[FixStatus] = None
    developer_notes: Optional[str] = Field(None, max_length=2000)
