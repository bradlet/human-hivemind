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

from hivemind.db.models import (
    DomainRow,
    LessonRow,
    SubjectAuthorRow,
    SubjectDomainRow,
    SubjectPrerequisiteRow,
    SubjectRow,
    UserRow,
)
from hivemind.logging_setup import get_logger
from hivemind.services import content_io
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
    manifest = state.manifest

    row = db.execute(select(SubjectRow).where(SubjectRow.slug == manifest.slug)).scalar_one_or_none()
    if row is None:
        row = SubjectRow(slug=manifest.slug)
        db.add(row)
    row.title = manifest.title
    row.status = manifest.status.value
    row.difficulty = manifest.difficulty.value
    row.estimated_hours = manifest.estimated_hours
    row.version = manifest.version
    row.forked_from_slug = manifest.forked_from.slug if manifest.forked_from else None
    row.forked_from_version = manifest.forked_from.version if manifest.forked_from else None
    db.flush()

    db.execute(delete(SubjectDomainRow).where(SubjectDomainRow.subject_id == row.id))
    db.execute(
        delete(SubjectPrerequisiteRow).where(SubjectPrerequisiteRow.subject_id == row.id)
    )
    db.execute(delete(SubjectAuthorRow).where(SubjectAuthorRow.subject_id == row.id))
    db.execute(delete(LessonRow).where(LessonRow.subject_id == row.id))

    for d in manifest.domains:
        db.add(SubjectDomainRow(subject_id=row.id, domain_slug=d))
    for i, p in enumerate(manifest.prerequisites):
        db.add(SubjectPrerequisiteRow(subject_id=row.id, prereq_slug=p, position=i))

    existing_user_ids = set(
        db.execute(
            select(UserRow.id).where(UserRow.id.in_([a.id for a in manifest.authors]))
        ).scalars().all()
    )
    for a in manifest.authors:
        if a.id not in existing_user_ids:
            continue
        db.add(SubjectAuthorRow(subject_id=row.id, user_id=a.id, role=a.role.value))

    for lesson in state.lessons:
        db.add(
            LessonRow(
                subject_id=row.id,
                order=lesson.frontmatter.order,
                title=lesson.frontmatter.title,
                estimated_minutes=lesson.frontmatter.estimated_minutes,
                learning_objectives=list(lesson.frontmatter.learning_objectives),
                filename=lesson.filename,
            )
        )

    db.flush()
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
