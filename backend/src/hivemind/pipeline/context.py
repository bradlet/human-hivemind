"""MutationContext and PipelineRejected exception.

The pipeline operates entirely on a `MutationContext`. Each step takes a context
and returns a (possibly modified) context, or raises `PipelineRejected` with a
human-readable reason. The API layer catches `PipelineRejected` and surfaces it
as a 4xx response.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from hivemind.models.subject import SubjectState
from hivemind.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from hivemind.storage.base import StorageBackend


class MutationOperation(StrEnum):
    CREATE_SUBJECT = "create_subject"
    UPDATE_SUBJECT = "update_subject"
    CREATE_LESSON = "create_lesson"
    UPDATE_LESSON = "update_lesson"
    FORK_SUBJECT = "fork_subject"
    RESTORE_VERSION = "restore_version"


class PipelineRejected(Exception):
    """Raised by a pipeline step to abort the mutation with a human-readable reason."""

    def __init__(self, step: str, reason: str, *, status_code: int = 400) -> None:
        super().__init__(f"[{step}] {reason}")
        self.step = step
        self.reason = reason
        self.status_code = status_code


@dataclass
class MutationContext:
    """The single object that flows through the pipeline.

    Steps mutate fields in place. Anything not yet populated is `None`; later
    steps depend on earlier ones having filled in `existing` / `proposed`.
    """

    operation: MutationOperation
    actor: User
    slug: str
    payload: dict[str, Any]

    storage: StorageBackend
    db: Session

    existing: SubjectState | None = None
    proposed: SubjectState | None = None

    audit: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def record(self, step: str, **fields: Any) -> None:
        """Helper for steps to append audit entries."""
        self.audit.append({"step": step, **fields})
