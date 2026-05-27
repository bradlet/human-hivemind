"""SQLAlchemy engine and session.

We construct a single engine at startup and produce sessions via `SessionLocal`.
FastAPI handlers use the `get_db` dependency to receive a scoped session.
"""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from hivemind.config import get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_engine(database_url: str | None = None, **engine_kwargs: Any) -> Engine:
    """Initialize the global engine. Idempotent if called with the same URL."""
    global _engine, _SessionLocal
    url = database_url or get_settings().database_url
    _engine = create_engine(url, pool_pre_ping=True, future=True, **engine_kwargs)
    _SessionLocal = sessionmaker(
        bind=_engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False
    )
    return _engine


def engine() -> Engine:
    if _engine is None:
        init_engine()
    assert _engine is not None
    return _engine


def SessionLocal() -> Session:
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency. Yields a session, rolls back on error, closes."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
