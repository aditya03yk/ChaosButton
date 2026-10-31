
"""Time helpers. All timestamps are timezone-aware UTC."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
