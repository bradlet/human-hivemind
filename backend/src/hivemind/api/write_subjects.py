"""Write endpoints for subjects/lessons/forks/restores.

All write endpoints route through the MutationPipeline. Failures raise
PipelineRejected, which is converted to an HTTPException with the right
status code by an exception handler in main.py.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from hivemind.api.deps import current_user_required, get_db, get_storage
from hivemind.api.schemas import (
    CreateSubjectIn,
    ForkSubjectIn,
    LessonIn,
    SubjectDetailOut,
    UpdateSubjectIn,
)
from hivemind.models.user import User
from hivemind.pipeline import (
    MutationContext,
    MutationOperation,
    pipeline_for_operation,
    run_pipeline,
)
from hivemind.services import content_io, subject_service
from hivemind.storage import StorageBackend
from hivemind.storage.base import StoredObjectNotFound

router = APIRouter(prefix="/subjects", tags=["subjects-write"])


def _lesson_payload(lesson_in: LessonIn) -> dict[str, Any]:
    return {
        "filename": lesson_in.filename,
        "frontmatter": lesson_in.frontmatter,
        "body": lesson_in.body,
    }


async def _execute_mutation(
    operation: MutationOperation,
    slug: str,
    payload: dict[str, Any],
    *,
    actor: User,
    storage: StorageBackend,
    db: Session,
    detail_slug: str | None = None,
) -> SubjectDetailOut:
    """Run a mutation pipeline and return the resulting SubjectDetailOut.

    `detail_slug` overrides the slug used to load the response (fork uses the new slug).
    """
    ctx = MutationContext(
        operation=operation,
        actor=actor,
        slug=slug,
        payload=payload,
        storage=storage,
        db=db,
    )
    await run_pipeline(ctx, pipeline_for_operation(operation))
    from hivemind.api.subjects import get_subject

    return get_subject(detail_slug or slug, db, storage)  # type: ignore[arg-type]


@router.post("", response_model=SubjectDetailOut, status_code=201)
async def create_subject(
    body: CreateSubjectIn,
    actor: Annotated[User, Depends(current_user_required)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    payload: dict[str, Any] = {
        "manifest": body.manifest.model_dump(),
        "overview": body.overview,
        "lessons": [_lesson_payload(l) for l in body.lessons],
    }
    return await _execute_mutation(
        MutationOperation.CREATE_SUBJECT, body.slug, payload,
        actor=actor, storage=storage, db=db,
    )


@router.put("/{slug}", response_model=SubjectDetailOut)
async def update_subject(
    slug: str,
    body: UpdateSubjectIn,
    actor: Annotated[User, Depends(current_user_required)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    payload: dict[str, Any] = {"manifest": body.manifest.model_dump()}
    if body.overview is not None:
        payload["overview"] = body.overview
    return await _execute_mutation(
        MutationOperation.UPDATE_SUBJECT, slug, payload,
        actor=actor, storage=storage, db=db,
    )


@router.put("/{slug}/lessons/{order}", response_model=SubjectDetailOut)
async def update_lesson(
    slug: str,
    order: int,
    body: LessonIn,
    actor: Annotated[User, Depends(current_user_required)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    if int(body.frontmatter.get("order", 0)) != order:
        raise HTTPException(
            status_code=422,
            detail=f"Lesson frontmatter.order ({body.frontmatter.get('order')}) must match URL order ({order}).",
        )
    return await _execute_mutation(
        MutationOperation.UPDATE_LESSON, slug, {"lesson": _lesson_payload(body)},
        actor=actor, storage=storage, db=db,
    )


@router.post("/{slug}/lessons", response_model=SubjectDetailOut, status_code=201)
async def create_lesson(
    slug: str,
    body: LessonIn,
    actor: Annotated[User, Depends(current_user_required)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    return await _execute_mutation(
        MutationOperation.CREATE_LESSON, slug, {"lesson": _lesson_payload(body)},
        actor=actor, storage=storage, db=db,
    )


@router.post("/{slug}/fork", response_model=SubjectDetailOut, status_code=201)
async def fork_subject(
    slug: str,
    body: ForkSubjectIn,
    actor: Annotated[User, Depends(current_user_required)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    return await _execute_mutation(
        MutationOperation.FORK_SUBJECT, slug, {"new_slug": body.new_slug},
        actor=actor, storage=storage, db=db, detail_slug=body.new_slug,
    )


@router.post("/{slug}/restore", response_model=SubjectDetailOut)
async def restore_subject(
    slug: str,
    version_id: Annotated[str, Query(..., description="GCS generation or local mtime_ns of subject.yaml to restore")],
    actor: Annotated[User, Depends(current_user_required)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    try:
        prior_manifest_bytes = storage.read(
            content_io.manifest_path(slug), version_id=version_id
        ).data
    except StoredObjectNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail=f"No version {version_id!r} found for {slug!r} subject.yaml",
        ) from exc

    import yaml

    parsed = yaml.safe_load(prior_manifest_bytes.decode("utf-8"))
    from hivemind.models.subject import SubjectManifest

    prior_manifest = SubjectManifest.model_validate(parsed)

    current = subject_service.load_state(storage, slug)
    restored_state = current.model_copy(update={"manifest": prior_manifest})

    return await _execute_mutation(
        MutationOperation.RESTORE_VERSION, slug, {"restored_state": restored_state},
        actor=actor, storage=storage, db=db,
    )
