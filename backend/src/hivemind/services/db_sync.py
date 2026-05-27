"""Shared "upsert SubjectState into the Postgres index" helpers.

Used by both the mutation pipeline's update_index step and the reindex
algorithm in services/index_sync. Authors whose user id is not in the users
table are skipped silently — see update_index step docstring for rationale.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from hivemind.db.models import (
    LessonRow,
    SubjectAuthorRow,
    SubjectDomainRow,
    SubjectPrerequisiteRow,
    SubjectRow,
    UserRow,
)
from hivemind.models.subject import SubjectState


def upsert_subject_row(db: Session, state: SubjectState) -> SubjectRow:
    manifest = state.manifest
    row = db.execute(
        select(SubjectRow).where(SubjectRow.slug == manifest.slug)
    ).scalar_one_or_none()
    if row is None:
        row = SubjectRow(slug=manifest.slug)
        db.add(row)
    row.title = manifest.title
    row.status = manifest.status.value
    row.difficulty = manifest.difficulty.value
    row.estimated_hours = manifest.estimated_hours
    row.version = manifest.version
    row.forked_from_slug = manifest.forked_from.slug if manifest.forked_from else None
    row.forked_from_version = (
        manifest.forked_from.version if manifest.forked_from else None
    )
    db.flush()
    return row


def replace_join_rows(db: Session, state: SubjectState, subject_id: int) -> None:
    manifest = state.manifest

    db.execute(delete(SubjectDomainRow).where(SubjectDomainRow.subject_id == subject_id))
    db.execute(
        delete(SubjectPrerequisiteRow).where(SubjectPrerequisiteRow.subject_id == subject_id)
    )
    db.execute(delete(SubjectAuthorRow).where(SubjectAuthorRow.subject_id == subject_id))

    for d in manifest.domains:
        db.add(SubjectDomainRow(subject_id=subject_id, domain_slug=d))

    for i, p in enumerate(manifest.prerequisites):
        db.add(SubjectPrerequisiteRow(subject_id=subject_id, prereq_slug=p, position=i))

    existing_user_ids = set(
        db.execute(
            select(UserRow.id).where(UserRow.id.in_([a.id for a in manifest.authors]))
        ).scalars().all()
    )
    for a in manifest.authors:
        if a.id not in existing_user_ids:
            continue
        db.add(SubjectAuthorRow(subject_id=subject_id, user_id=a.id, role=a.role.value))


def replace_lesson_rows(db: Session, state: SubjectState, subject_id: int) -> None:
    db.execute(delete(LessonRow).where(LessonRow.subject_id == subject_id))
    for lesson in state.lessons:
        db.add(
            LessonRow(
                subject_id=subject_id,
                order=lesson.frontmatter.order,
                title=lesson.frontmatter.title,
                estimated_minutes=lesson.frontmatter.estimated_minutes,
                learning_objectives=list(lesson.frontmatter.learning_objectives),
                filename=lesson.filename,
            )
        )


def upsert_subject_state(db: Session, state: SubjectState) -> SubjectRow:
    """Upsert a SubjectState's row, join rows, and lesson rows. Caller flushes/commits."""
    row = upsert_subject_row(db, state)
    replace_join_rows(db, state, row.id)
    replace_lesson_rows(db, state, row.id)
    db.flush()
    return row
