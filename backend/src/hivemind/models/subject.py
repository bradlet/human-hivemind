"""Subject and lesson schemas.

These are the contract that forces course structure over wiki-article structure:
`SubjectManifest` requires a populated authors list, a domains list, an
explicit difficulty, status, and version; `LessonFrontmatter` requires an
ordered position, a title, an estimated time, and at least one learning
objective.

`SubjectState` is the fully-assembled in-memory view of a subject (manifest +
ordered lessons + overview + optional supplementary files). It is what the
mutation pipeline operates on.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hivemind.models.validators import validate_slug


class Difficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Status(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AuthorRole(StrEnum):
    ORIGINAL = "original"
    CONTRIBUTOR = "contributor"


class SubjectAuthor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    role: AuthorRole = AuthorRole.CONTRIBUTOR


class ForkedFrom(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    version: int = Field(..., ge=1)

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, v: str) -> str:
        return validate_slug(v, field="forked_from.slug")


class SubjectManifest(BaseModel):
    """`subject.yaml`. Required for every subject."""

    model_config = ConfigDict(extra="forbid")

    slug: str
    title: str = Field(..., min_length=1, max_length=200)
    domains: list[str] = Field(..., min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    authors: list[SubjectAuthor] = Field(..., min_length=1)
    estimated_hours: float = Field(..., gt=0)
    difficulty: Difficulty
    status: Status = Status.DRAFT
    version: int = Field(default=1, ge=1)
    forked_from: ForkedFrom | None = None

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, v: str) -> str:
        return validate_slug(v, field="subject slug")

    @field_validator("domains", "prerequisites")
    @classmethod
    def _check_slug_lists(cls, v: list[str]) -> list[str]:
        for s in v:
            validate_slug(s, field="referenced slug")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate slugs are not allowed in domains/prerequisites")
        return v

    @model_validator(mode="after")
    def _check_no_self_prereq(self) -> Self:
        if self.slug in self.prerequisites:
            raise ValueError(f"Subject {self.slug!r} cannot list itself as a prerequisite")
        return self


class LessonFrontmatter(BaseModel):
    """YAML frontmatter at the top of every `lessons/NN-*.md`."""

    model_config = ConfigDict(extra="forbid")

    order: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    estimated_minutes: int = Field(..., ge=1)
    learning_objectives: list[str] = Field(..., min_length=1)

    @field_validator("learning_objectives")
    @classmethod
    def _check_objectives(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip() for s in v]
        if any(not s for s in cleaned):
            raise ValueError("learning_objectives entries must be non-empty strings")
        return cleaned


class LessonRecord(BaseModel):
    """A fully-loaded lesson: frontmatter + body markdown."""

    model_config = ConfigDict(extra="forbid")

    frontmatter: LessonFrontmatter
    body: str
    filename: str = Field(
        ..., description="The on-disk filename (e.g. '01-introduction.md'), preserved for round-tripping"
    )


class SubjectState(BaseModel):
    """Fully-assembled subject: manifest + overview + lessons + optional extras.

    This is what the mutation pipeline operates on. It's what gets diffed,
    validated, written, and indexed.
    """

    model_config = ConfigDict(extra="forbid")

    manifest: SubjectManifest
    overview: str
    lessons: list[LessonRecord]
    references: str | None = None
    exercises: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_lessons(self) -> Self:
        if not self.lessons:
            raise ValueError(
                f"Subject {self.manifest.slug!r} must declare at least one lesson "
                "in the lessons/ directory."
            )
        orders = [l.frontmatter.order for l in self.lessons]
        if len(set(orders)) != len(orders):
            raise ValueError(
                f"Subject {self.manifest.slug!r} has duplicate lesson `order` values: {orders}"
            )
        sorted_lessons = sorted(self.lessons, key=lambda l: l.frontmatter.order)
        object.__setattr__(self, "lessons", sorted_lessons)
        return self
