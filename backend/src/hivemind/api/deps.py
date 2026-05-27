"""Shared FastAPI dependencies."""
from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from hivemind.config import Settings, get_settings
from hivemind.db.models import UserRow
from hivemind.db.session import get_db as _get_db
from hivemind.models.user import User
from hivemind.storage import StorageBackend, build_storage

_storage_singleton: StorageBackend | None = None


def get_settings_dep() -> Settings:
    return get_settings()


def get_storage(settings: Annotated[Settings, Depends(get_settings_dep)]) -> StorageBackend:
    global _storage_singleton
    if _storage_singleton is None:
        _storage_singleton = build_storage(settings)
    return _storage_singleton


def reset_storage_singleton() -> None:
    """Test helper: clear the cached storage backend."""
    global _storage_singleton
    _storage_singleton = None


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def _user_from_session(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        return None
    row = db.get(UserRow, user_id)
    if row is None:
        return None
    return User(id=row.id, email=row.email, name=row.name, avatar_url=row.avatar_url)


def current_user_optional(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> User | None:
    return _user_from_session(request, db)


def current_user_required(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> User:
    user = _user_from_session(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
