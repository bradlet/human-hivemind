"""End-to-end tests for the mutation pipeline.

Exercises:
  - composition (the stub moderation step logs and passes through)
  - schema rejection
  - authorship enforcement
  - storage + index writes (index uses SQLite here)
  - fork semantics (recursive copy + new author + forked_from set)
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from hivemind.db.models import (
    DomainRow,
    EditEventRow,
    LessonRow,
    SubjectAuthorRow,
    SubjectDomainRow,
    SubjectPrerequisiteRow,
    SubjectRow,
    UserRow,
)
from hivemind.models.user import User
from hivemind.pipeline import (
    MutationContext,
    MutationOperation,
    PipelineRejected,
    pipeline_for_operation,
    run_pipeline,
)
from hivemind.storage.local import LocalStorage


def _seed_domains(db: Session) -> None:
    db.add_all(
        [
            DomainRow(slug="computer-science", title="Computer Science", sort_order=0),
            DomainRow(slug="mathematics", title="Mathematics", sort_order=1),
        ]
    )
    db.flush()


def _seed_user(db: Session, user_id: str = "user_a", email: str | None = None) -> UserRow:
    row = UserRow(
        id=user_id,
        google_sub=f"sub-{user_id}",
        email=email or f"{user_id}@example.com",
        name=user_id,
    )
    db.add(row)
    db.flush()
    return row


def _actor(user_id: str = "user_a") -> User:
    return User(id=user_id, email=f"{user_id}@example.com", name=user_id)


def _create_payload(slug: str, *, prereqs: list[str] | None = None) -> dict:
    return {
        "manifest": {
            "title": "Test " + slug,
            "domains": ["computer-science"],
            "prerequisites": prereqs or [],
            "estimated_hours": 4,
            "difficulty": "beginner",
            "status": "draft",
        },
        "overview": "Overview text.",
        "lessons": [
            {
                "filename": "01-intro.md",
                "frontmatter": {
                    "order": 1,
                    "title": "Intro",
                    "estimated_minutes": 15,
                    "learning_objectives": ["Understand X"],
                },
                "body": "Hello.",
            }
        ],
    }


@pytest.mark.asyncio
async def test_create_subject_full_pipeline(db: Session, storage: LocalStorage):
    _seed_domains(db)
    _seed_user(db)
    ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor(),
        slug="alpha",
        payload=_create_payload("alpha"),
        storage=storage,
        db=db,
    )
    await run_pipeline(ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))

    row = db.query(SubjectRow).filter_by(slug="alpha").one()
    assert row.title == "Test alpha"
    assert row.version == 1
    assert len(db.query(LessonRow).filter_by(subject_id=row.id).all()) == 1
    assert len(db.query(SubjectDomainRow).filter_by(subject_id=row.id).all()) == 1
    assert len(db.query(SubjectAuthorRow).filter_by(subject_id=row.id).all()) == 1
    assert len(db.query(EditEventRow).all()) == 1
    audit_steps = [s["step"] for s in db.query(EditEventRow).first().payload["steps"]]
    assert "moderate" in audit_steps
    assert "regenerate_ai_representation" in audit_steps


@pytest.mark.asyncio
async def test_validate_schema_rejects_malformed(db: Session, storage: LocalStorage):
    _seed_domains(db)
    _seed_user(db)
    payload = _create_payload("alpha")
    payload["manifest"]["domains"] = []
    ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor(),
        slug="alpha",
        payload=payload,
        storage=storage,
        db=db,
    )
    with pytest.raises(PipelineRejected) as exc:
        await run_pipeline(ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))
    assert exc.value.step == "validate_schema"


@pytest.mark.asyncio
async def test_validate_references_rejects_missing_domain(
    db: Session, storage: LocalStorage
):
    _seed_user(db)  # no domains seeded
    payload = _create_payload("alpha")
    ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor(),
        slug="alpha",
        payload=payload,
        storage=storage,
        db=db,
    )
    with pytest.raises(PipelineRejected) as exc:
        await run_pipeline(ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))
    assert exc.value.step == "validate_references"


@pytest.mark.asyncio
async def test_check_authorship_blocks_non_author_update(
    db: Session, storage: LocalStorage
):
    _seed_domains(db)
    _seed_user(db, "user_a")
    _seed_user(db, "user_b")
    ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor("user_a"),
        slug="alpha",
        payload=_create_payload("alpha"),
        storage=storage,
        db=db,
    )
    await run_pipeline(ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))

    update_ctx = MutationContext(
        operation=MutationOperation.UPDATE_SUBJECT,
        actor=_actor("user_b"),
        slug="alpha",
        payload={
            "manifest": {
                "title": "Hijacked",
                "domains": ["computer-science"],
                "prerequisites": [],
                "estimated_hours": 4,
                "difficulty": "beginner",
                "status": "draft",
            }
        },
        storage=storage,
        db=db,
    )
    with pytest.raises(PipelineRejected) as exc:
        await run_pipeline(update_ctx, pipeline_for_operation(MutationOperation.UPDATE_SUBJECT))
    assert exc.value.step == "check_authorship"
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_fork_creates_new_slug_with_new_author(
    db: Session, storage: LocalStorage
):
    _seed_domains(db)
    _seed_user(db, "user_a")
    _seed_user(db, "user_b")

    create_ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor("user_a"),
        slug="alpha",
        payload=_create_payload("alpha"),
        storage=storage,
        db=db,
    )
    await run_pipeline(create_ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))

    fork_ctx = MutationContext(
        operation=MutationOperation.FORK_SUBJECT,
        actor=_actor("user_b"),
        slug="alpha",
        payload={"new_slug": "alpha-fork"},
        storage=storage,
        db=db,
    )
    await run_pipeline(fork_ctx, pipeline_for_operation(MutationOperation.FORK_SUBJECT))

    forked = db.query(SubjectRow).filter_by(slug="alpha-fork").one()
    assert forked.forked_from_slug == "alpha"
    assert forked.forked_from_version == 1
    forked_authors = db.query(SubjectAuthorRow).filter_by(subject_id=forked.id).all()
    assert {a.user_id for a in forked_authors} == {"user_b"}
    # The original is untouched
    orig = db.query(SubjectRow).filter_by(slug="alpha").one()
    orig_authors = db.query(SubjectAuthorRow).filter_by(subject_id=orig.id).all()
    assert {a.user_id for a in orig_authors} == {"user_a"}
    # And storage has both
    assert storage.exists("subjects/alpha/subject.yaml")
    assert storage.exists("subjects/alpha-fork/subject.yaml")


@pytest.mark.asyncio
async def test_update_bumps_version_and_writes_index(
    db: Session, storage: LocalStorage
):
    _seed_domains(db)
    _seed_user(db, "user_a")

    create_ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor("user_a"),
        slug="alpha",
        payload=_create_payload("alpha"),
        storage=storage,
        db=db,
    )
    await run_pipeline(create_ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))

    update_ctx = MutationContext(
        operation=MutationOperation.UPDATE_SUBJECT,
        actor=_actor("user_a"),
        slug="alpha",
        payload={
            "manifest": {
                "title": "Renamed",
                "domains": ["computer-science"],
                "prerequisites": [],
                "estimated_hours": 5,
                "difficulty": "intermediate",
                "status": "published",
            }
        },
        storage=storage,
        db=db,
    )
    await run_pipeline(update_ctx, pipeline_for_operation(MutationOperation.UPDATE_SUBJECT))

    row = db.query(SubjectRow).filter_by(slug="alpha").one()
    assert row.title == "Renamed"
    assert row.version == 2
    assert row.difficulty == "intermediate"
    assert row.status == "published"


@pytest.mark.asyncio
async def test_create_lesson_appends_and_bumps_version(
    db: Session, storage: LocalStorage
):
    _seed_domains(db)
    _seed_user(db, "user_a")

    create_ctx = MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=_actor("user_a"),
        slug="alpha",
        payload=_create_payload("alpha"),
        storage=storage,
        db=db,
    )
    await run_pipeline(create_ctx, pipeline_for_operation(MutationOperation.CREATE_SUBJECT))

    new_lesson = {
        "filename": "02-second.md",
        "frontmatter": {
            "order": 2,
            "title": "Second",
            "estimated_minutes": 20,
            "learning_objectives": ["Understand Y"],
        },
        "body": "More content.",
    }
    add_ctx = MutationContext(
        operation=MutationOperation.CREATE_LESSON,
        actor=_actor("user_a"),
        slug="alpha",
        payload={"lesson": new_lesson},
        storage=storage,
        db=db,
    )
    await run_pipeline(add_ctx, pipeline_for_operation(MutationOperation.CREATE_LESSON))

    row = db.query(SubjectRow).filter_by(slug="alpha").one()
    assert row.version == 2
    assert len(db.query(LessonRow).filter_by(subject_id=row.id).all()) == 2
