"""User model used by the auth layer and the mutation pipeline.

Kept lightweight to avoid coupling to SQLAlchemy in the pipeline (which only
needs `id` for authorship checks and audit logging).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """A lightweight DTO view of a user. Built from db.UserRow at the API boundary."""

    model_config = ConfigDict(frozen=True)

    id: str
    email: str
    name: str
    avatar_url: str | None = None
