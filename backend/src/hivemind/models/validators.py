"""Shared pydantic-model validators."""
from __future__ import annotations

import re

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(value: str, *, field: str) -> str:
    if not SLUG_RE.match(value):
        raise ValueError(
            f"{field} must be a lowercase kebab-case slug (got {value!r}). "
            "Allowed characters: a-z, 0-9, and hyphens; cannot start or end with a hyphen."
        )
    return value
