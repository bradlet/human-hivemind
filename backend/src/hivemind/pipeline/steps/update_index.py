"""update_index: upsert Postgres rows from ctx.proposed.

This makes the new state queryable by /api/subjects, /api/subjects/{slug},
/api/subjects?domain=..., prereq DAG queries, etc.

Authors are upserted by user id. If an author id corresponds to a user not yet
in the users table (e.g. legacy seed content authored by `user_seed`), the
join row is skipped silently — the index can be rebuilt safely from storage
and missing user FKs would just block everything otherwise.
"""
from __future__ import annotations

from sqlalchemy import delete, select

from hivemind.db.models import (
    LessonRow,
    SubjectAuthorRow,
    SubjectDomainRow,
    SubjectPrerequisiteRow,
    SubjectRow,
    UserRow,
)
from hivemind.pipeline.context import MutationContext

STEP_NAME = "update_index"


def upsert_subject_row(ctx: MutationContext) -> SubjectRow:
    assert ctx.proposed is not None
    manifest = ctx.proposed.manifest
    row = ctx.db.execute(
        select(SubjectRow).where(SubjectRow.slug == manifest.slug)
    ).scalar_one_or_none()
    if row is None:
        row = SubjectRow(slug=manifest.slug)
        ctx.db.add(row)
    row.title = manifest.title
    row.status = manifest.status.value
    row.difficulty = manifest.difficulty.value
    row.estimated_hours = manifest.estimated_hours
    row.version = manifest.version
    row.forked_from_slug = manifest.forked_from.slug if manifest.forked_from else None
    row.forked_from_version = manifest.forked_from.version if manifest.forked_from else None
    ctx.db.flush()
    return row


def replace_join_rows(ctx: MutationContext, subject_row: SubjectRow) -> None:
    assert ctx.proposed is not None
    manifest = ctx.proposed.manifest

    ctx.db.execute(
        delete(SubjectDomainRow).where(SubjectDomainRow.subject_id == subject_row.id)
    )
    ctx.db.execute(
        delete(SubjectPrerequisiteRow).where(
            SubjectPrerequisiteRow.subject_id == subject_row.id
        )
    )
    ctx.db.execute(
        delete(SubjectAuthorRow).where(SubjectAuthorRow.subject_id == subject_row.id)
    )

    for d in manifest.domains:
        ctx.db.add(SubjectDomainRow(subject_id=subject_row.id, domain_slug=d))

    for i, p in enumerate(manifest.prerequisites):
        ctx.db.add(
            SubjectPrerequisiteRow(subject_id=subject_row.id, prereq_slug=p, position=i)
        )

    existing_user_ids = set(
        ctx.db.execute(
            select(UserRow.id).where(UserRow.id.in_([a.id for a in manifest.authors]))
        ).scalars().all()
    )
    for a in manifest.authors:
        if a.id not in existing_user_ids:
            continue
        ctx.db.add(
            SubjectAuthorRow(subject_id=subject_row.id, user_id=a.id, role=a.role.value)
        )


def replace_lesson_rows(ctx: MutationContext, subject_row: SubjectRow) -> None:
    assert ctx.proposed is not None
    ctx.db.execute(delete(LessonRow).where(LessonRow.subject_id == subject_row.id))
    for lesson in ctx.proposed.lessons:
        ctx.db.add(
            LessonRow(
                subject_id=subject_row.id,
                order=lesson.frontmatter.order,
                title=lesson.frontmatter.title,
                estimated_minutes=lesson.frontmatter.estimated_minutes,
                learning_objectives=list(lesson.frontmatter.learning_objectives),
                filename=lesson.filename,
            )
        )


async def update_index(ctx: MutationContext) -> MutationContext:
    subject_row = upsert_subject_row(ctx)
    replace_join_rows(ctx, subject_row)
    replace_lesson_rows(ctx, subject_row)
    ctx.db.flush()
    ctx.record(STEP_NAME, subject_id=subject_row.id)
    return ctx
