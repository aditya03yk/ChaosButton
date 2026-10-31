"""SQLite engine management and session helpers."""
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

_engine: Optional[Engine] = None


def configure(database_url: str) -> Engine:
    """Create (or replace) the global engine and make sure the schema exists."""
    global _engine
    from app import models  # noqa: F401  (registers tables)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _engine = create_engine(database_url, connect_args=connect_args)
    SQLModel.metadata.create_all(_engine)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database is not configured")
    return _engine


@contextmanager
def session_scope() -> Iterator[Session]:
    """Short-lived session for services and background tasks."""
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session


def get_session() -> Iterator[Session]:
    """FastAPI dependency."""
    with session_scope() as session:
        yield session


def database_ok() -> bool:
    try:
        with session_scope() as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception:
        return False
