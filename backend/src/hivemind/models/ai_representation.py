"""Schemas for the AI-side representation of a subject.

Files live under `subjects/{slug}/ai/`:

- `agent.md`     - AGENTS.md-style summary (markdown body, no frontmatter)
- `facts.yaml`   - structured key formulas / theorems / numeric facts
- `glossary.yaml`- term -> short definition
- `meta.yaml`    - bookkeeping: when/from-what-version this was regenerated

These files are *never* user-edited. The pipeline writes them via
`regenerate_ai_representation`. v1 stubs that step, so seed content includes
hand-written versions of these files.
"""
from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Formula(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    expression: str
    notes: str | None = None


class Theorem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    statement: str


class FactsFile(BaseModel):
    """`ai/facts.yaml`."""

    model_config = ConfigDict(extra="forbid")

    key_formulas: list[Formula] = Field(default_factory=list)
    key_theorems: list[Theorem] = Field(default_factory=list)
    numeric_facts: list[str] = Field(default_factory=list)


class GlossaryFile(BaseModel):
    """`ai/glossary.yaml`. Maps term -> short definition."""

    model_config = ConfigDict(extra="forbid")

    terms: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_nonempty(self) -> Self:
        for term, defn in self.terms.items():
            if not term.strip() or not defn.strip():
                raise ValueError("Glossary terms and definitions must be non-empty")
        return self


class AgentDoc(BaseModel):
    """`ai/agent.md` content as raw markdown body."""

    model_config = ConfigDict(extra="forbid")

    body: str = Field(..., min_length=1)


class AIMeta(BaseModel):
    """`ai/meta.yaml`. Tracks how stale the AI rep is vs the human source."""

    model_config = ConfigDict(extra="forbid")

    regenerated_at: datetime
    regenerated_from_human_version: int = Field(..., ge=1)
    model: str = "stub"
    prompt_hash: str = "stub"
