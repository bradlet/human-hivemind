"""Domain taxonomy model.

A `domains.yaml` file at the root of content storage describes the domain tree.
Domains hold no content of their own; subjects reference them by slug.
"""
from __future__ import annotations

import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _validate_slug(value: str, *, field: str) -> str:
    if not SLUG_RE.match(value):
        raise ValueError(
            f"{field} must be a lowercase kebab-case slug (got {value!r}). "
            "Allowed characters: a-z, 0-9, and hyphens; cannot start or end with a hyphen."
        )
    return value


class DomainNode(BaseModel):
    """A node in the domain tree.

    `children` is a list to preserve declared ordering. The tree is purely
    taxonomy; subjects attach to domains via subject.yaml `domains:`.
    """

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., description="Lowercase kebab-case slug")
    title: str = Field(..., min_length=1)
    children: list[DomainNode] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, v: str) -> str:
        return _validate_slug(v, field="domain slug")


class DomainTree(BaseModel):
    """The full domain tree, loaded from `domains.yaml`."""

    model_config = ConfigDict(extra="forbid")

    domains: list[DomainNode]

    @model_validator(mode="after")
    def _check_unique_slugs(self) -> Self:
        seen: set[str] = set()

        def walk(nodes: list[DomainNode]) -> None:
            for n in nodes:
                if n.slug in seen:
                    raise ValueError(f"Duplicate domain slug in domains.yaml: {n.slug!r}")
                seen.add(n.slug)
                walk(n.children)

        walk(self.domains)
        return self

    def flatten(self) -> list[tuple[DomainNode, str | None]]:
        """Yield (node, parent_slug) pairs in pre-order traversal."""
        out: list[tuple[DomainNode, str | None]] = []

        def walk(nodes: list[DomainNode], parent: str | None) -> None:
            for n in nodes:
                out.append((n, parent))
                walk(n.children, n.slug)

        walk(self.domains, None)
        return out

    def slugs(self) -> set[str]:
        return {n.slug for n, _ in self.flatten()}


DomainNode.model_rebuild()
