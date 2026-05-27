"""API response/request DTOs. Distinct from storage-side pydantic models so the
on-disk schema can evolve independently from the wire format.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DomainNodeOut(BaseModel):
    slug: str
    title: str
    children: list[DomainNodeOut] = Field(default_factory=list)


DomainNodeOut.model_rebuild()


class DomainTreeOut(BaseModel):
    domains: list[DomainNodeOut]


class AuthorOut(BaseModel):
    id: str
    name: str | None = None
    avatar_url: str | None = None


class ForkedFromOut(BaseModel):
    slug: str
    version: int


class SubjectSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    status: str
    difficulty: str
    estimated_hours: float
    version: int
    updated_at: datetime


class LessonSummaryOut(BaseModel):
    order: int
    title: str
    estimated_minutes: int
    learning_objectives: list[str]


class LessonOut(LessonSummaryOut):
    body: str


class SubjectDetailOut(BaseModel):
    slug: str
    title: str
    domains: list[str]
    prerequisites: list[str]
    authors: list[AuthorOut]
    estimated_hours: float
    difficulty: str
    status: str
    version: int
    forked_from: ForkedFromOut | None = None
    overview: str
    lessons: list[LessonOut]
    references: str | None = None


class PrereqNodeOut(BaseModel):
    slug: str
    title: str
    depth: int
    via: str | None


class PrereqsOut(BaseModel):
    slug: str
    nodes: list[PrereqNodeOut]


class DependentsOut(BaseModel):
    slug: str
    dependents: list[SubjectSummaryOut]


class HistoryEntryOut(BaseModel):
    path: str
    version_id: str
    size: int
    updated_at: datetime
    is_current: bool


class HistoryOut(BaseModel):
    slug: str
    files: dict[str, list[HistoryEntryOut]]


# ---------- AI representation ----------


class AIFactsOut(BaseModel):
    key_formulas: list[dict[str, Any]] = Field(default_factory=list)
    key_theorems: list[dict[str, Any]] = Field(default_factory=list)
    numeric_facts: list[str] = Field(default_factory=list)


class AIGlossaryOut(BaseModel):
    terms: dict[str, str] = Field(default_factory=dict)


class AIRepresentationOut(BaseModel):
    slug: str
    agent_md: str | None = None
    facts: AIFactsOut | None = None
    glossary: AIGlossaryOut | None = None
    regenerated_at: datetime | None = None
    regenerated_from_human_version: int | None = None
    current_human_version: int
    is_stale: bool = Field(
        ..., description="True if regenerated_from_human_version < current_human_version"
    )
    model: str | None = None


# ---------- Auth ----------


class AuthMeOut(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: str | None = None


# ---------- Write request bodies ----------


class LessonIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    frontmatter: dict[str, Any]
    body: str


class ManifestIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    domains: list[str]
    prerequisites: list[str] = Field(default_factory=list)
    estimated_hours: float
    difficulty: str
    status: str | None = None


class CreateSubjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    manifest: ManifestIn
    overview: str
    lessons: list[LessonIn]


class UpdateSubjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: ManifestIn
    overview: str | None = None


class ForkSubjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_slug: str
