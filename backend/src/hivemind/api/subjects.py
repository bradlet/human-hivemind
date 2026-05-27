"""/api/subjects and /api/subjects/{slug} read endpoints (write endpoints in
api.write_subjects)."""
from __future__ import annotations

from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from hivemind.api.deps import get_db, get_storage
from hivemind.api.schemas import (
    AuthorOut,
    DependentsOut,
    ForkedFromOut,
    HistoryEntryOut,
    HistoryOut,
    LessonOut,
    LessonSummaryOut,
    PrereqNodeOut,
    PrereqsOut,
    SubjectDetailOut,
    SubjectSummaryOut,
)
from hivemind.services import content_io, subject_service
from hivemind.storage import StorageBackend
from hivemind.storage.base import StoredObjectNotFound

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _subject_summary(row: subject_service.SubjectRow) -> SubjectSummaryOut:  # type: ignore[name-defined]
    return SubjectSummaryOut.model_validate(row)


@router.get("", response_model=list[SubjectSummaryOut])
def list_subjects(
    db: Annotated[Session, Depends(get_db)],
    domain: str | None = Query(default=None),
    search: str | None = Query(default=None),
    author_id: str | None = Query(default=None),
    sort: str = Query(default="title"),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[SubjectSummaryOut]:
    rows = subject_service.list_subjects(
        db,
        domain=domain,
        search=search,
        author_id=author_id,
        sort=sort,  # type: ignore[arg-type]
        limit=limit,
    )
    return [SubjectSummaryOut.model_validate(r) for r in rows]


@router.get("/{slug}", response_model=SubjectDetailOut)
def get_subject(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> SubjectDetailOut:
    row = subject_service.get_subject_row(db, slug)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    try:
        state = subject_service.load_state(storage, slug)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    authors = subject_service.get_authors(db, row.id)
    author_dtos = [
        AuthorOut(id=a.id, name=a.name, avatar_url=a.avatar_url) for a in authors
    ]
    if not author_dtos:
        author_dtos = [AuthorOut(id=a.id) for a in state.manifest.authors]

    return SubjectDetailOut(
        slug=state.manifest.slug,
        title=state.manifest.title,
        domains=state.manifest.domains,
        prerequisites=state.manifest.prerequisites,
        authors=author_dtos,
        estimated_hours=state.manifest.estimated_hours,
        difficulty=state.manifest.difficulty.value,
        status=state.manifest.status.value,
        version=state.manifest.version,
        forked_from=(
            ForkedFromOut(slug=state.manifest.forked_from.slug, version=state.manifest.forked_from.version)
            if state.manifest.forked_from
            else None
        ),
        overview=state.overview,
        lessons=[
            LessonOut(
                order=l.frontmatter.order,
                title=l.frontmatter.title,
                estimated_minutes=l.frontmatter.estimated_minutes,
                learning_objectives=l.frontmatter.learning_objectives,
                body=l.body,
            )
            for l in state.lessons
        ],
        references=state.references,
    )


@router.get("/{slug}/lessons/{order}", response_model=LessonOut)
def get_lesson(
    slug: str,
    order: int,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> LessonOut:
    lesson = subject_service.load_lesson(storage, slug, order)
    if lesson is None:
        raise HTTPException(status_code=404, detail=f"Lesson {order} not found in {slug!r}")
    fm = lesson.frontmatter
    return LessonOut(
        order=fm.order,
        title=fm.title,
        estimated_minutes=fm.estimated_minutes,
        learning_objectives=fm.learning_objectives,
        body=lesson.body,
    )


@router.get("/{slug}/lessons", response_model=list[LessonSummaryOut])
def list_lessons(
    slug: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> list[LessonSummaryOut]:
    try:
        state = subject_service.load_state(storage, slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        LessonSummaryOut(
            order=l.frontmatter.order,
            title=l.frontmatter.title,
            estimated_minutes=l.frontmatter.estimated_minutes,
            learning_objectives=l.frontmatter.learning_objectives,
        )
        for l in state.lessons
    ]


@router.get("/{slug}/raw.md")
def get_raw_markdown(
    slug: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> Response:
    try:
        state = subject_service.load_state(storage, slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    body = subject_service.concatenated_raw_markdown(state)
    return Response(content=body, media_type="text/markdown; charset=utf-8")


@router.get("/{slug}/prereqs", response_model=PrereqsOut)
def get_prereqs(
    slug: str, db: Annotated[Session, Depends(get_db)]
) -> PrereqsOut:
    if subject_service.get_subject_row(db, slug) is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    nodes = subject_service.transitive_prereqs(db, slug)
    return PrereqsOut(
        slug=slug,
        nodes=[PrereqNodeOut(slug=n.slug, title=n.title, depth=n.depth, via=n.via) for n in nodes],
    )


@router.get("/{slug}/dependents", response_model=DependentsOut)
def get_dependents(
    slug: str, db: Annotated[Session, Depends(get_db)]
) -> DependentsOut:
    if subject_service.get_subject_row(db, slug) is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    deps = subject_service.dependents(db, slug)
    return DependentsOut(
        slug=slug, dependents=[SubjectSummaryOut.model_validate(r) for r in deps]
    )


@router.get("/{slug}/history", response_model=HistoryOut)
def get_history(
    slug: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> HistoryOut:
    paths_to_check = [
        content_io.manifest_path(slug),
        content_io.overview_path(slug),
    ]
    paths_to_check.extend(storage.list_prefix(content_io.lessons_prefix(slug)))
    files: dict[str, list[HistoryEntryOut]] = defaultdict(list)
    for path in paths_to_check:
        try:
            versions = storage.list_versions(path)
        except StoredObjectNotFound:
            continue
        files[path] = [
            HistoryEntryOut(
                path=v.path,
                version_id=v.version_id,
                size=v.size,
                updated_at=v.updated_at,
                is_current=v.is_current,
            )
            for v in versions
        ]
    return HistoryOut(slug=slug, files=dict(files))
