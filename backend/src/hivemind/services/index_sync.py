"""Build/refresh the Postgres index from content storage.

Used by the `hivemind reindex` CLI and by the application's startup hook (which
runs reindex if the subjects table is empty).

Algorithm:
  1. Load domains.yaml and upsert the `domains` table (preserving tree order).
  2. For each subject directory in storage, load the SubjectState (manifest +
     lessons), upsert the subject row, replace its join rows and lessons.
  3. Authors are linked only if the user already exists; seed content authored
     by `user_seed` (the placeholder) is allowed to have no live user link.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from hivemind.db.models import DomainRow, SubjectDomainRow, SubjectRow
from hivemind.logging_setup import get_logger
from hivemind.services import content_io
from hivemind.services.db_sync import upsert_subject_state
from hivemind.storage.base import StorageBackend

log = get_logger("hivemind.index_sync")


@dataclass
class ReindexReport:
    domains: int
    subjects: int
    lessons: int
    skipped: list[tuple[str, str]]


def _sync_domains(db: Session, storage: StorageBackend) -> int:
    tree = content_io.load_domains(storage)
    db.execute(delete(SubjectDomainRow))
    db.execute(delete(DomainRow))
    flat = tree.flatten()
    for i, (node, parent) in enumerate(flat):
        db.add(
            DomainRow(slug=node.slug, parent_slug=parent, title=node.title, sort_order=i)
        )
    db.flush()
    return len(flat)


def _sync_subject(db: Session, storage: StorageBackend, slug: str) -> tuple[int, int]:
    """Sync a single subject. Returns (1_if_indexed, lesson_count) on success."""
    state = content_io.load_subject_state(storage, slug)
    upsert_subject_state(db, state)
    return 1, len(state.lessons)


def reindex(db: Session, storage: StorageBackend) -> ReindexReport:
    log.info("reindex.start")
    domain_count = _sync_domains(db, storage)

    slugs = content_io.list_subject_slugs(storage)
    subjects_synced = 0
    lessons_synced = 0
    skipped: list[tuple[str, str]] = []
    for slug in slugs:
        try:
            n_subj, n_lesson = _sync_subject(db, storage, slug)
            subjects_synced += n_subj
            lessons_synced += n_lesson
        except ValueError as exc:
            skipped.append((slug, str(exc)))
            log.warning("reindex.skip", slug=slug, reason=str(exc))

    db.commit()
    report = ReindexReport(
        domains=domain_count,
        subjects=subjects_synced,
        lessons=lessons_synced,
        skipped=skipped,
    )
    log.info(
        "reindex.done",
        domains=report.domains,
        subjects=report.subjects,
        lessons=report.lessons,
        skipped=len(report.skipped),
    )
    return report


def needs_reindex(db: Session) -> bool:
    """Return True if the index appears empty (no subjects)."""
    count = db.execute(select(SubjectRow.id).limit(1)).first()
    return count is None
