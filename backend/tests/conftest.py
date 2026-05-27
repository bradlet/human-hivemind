"""Shared pytest fixtures.

Tests use SQLite (file-backed temp DB) instead of Postgres so the suite runs
without any infra. The Postgres-specific recursive CTE in
`transitive_prereqs` is exercised in a separate test that is skipped under
SQLite.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from hivemind.db.models import Base
from hivemind.storage.local import LocalStorage


@pytest.fixture
def temp_content(tmp_path: Path) -> Path:
    root = tmp_path / "content"
    root.mkdir()
    return root


@pytest.fixture
def storage(temp_content: Path) -> LocalStorage:
    return LocalStorage(temp_content)


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Session]:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[2]


@pytest.fixture
def seed_content_root(repo_root: Path) -> Path:
    return repo_root / "content"


@pytest.fixture
def is_postgres() -> bool:
    return bool(os.environ.get("TEST_DATABASE_URL", "").startswith("postgres"))
