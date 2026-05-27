"""Read-side helpers used by the API.

Anything that mixes Postgres queries with content-storage reads belongs here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from hivemind.db.models import LessonRow, SubjectAuthorRow, SubjectRow, UserRow
from hivemind.models.domain import DomainNode, DomainTree
from hivemind.models.subject import LessonRecord, SubjectState
from hivemind.services import content_io
from hivemind.storage.base import StorageBackend

SortField = Literal["title", "updated_at", "estimated_hours", "difficulty"]


def list_subjects(
    db: Session,
    *,
    domain: str | None = None,
    search: str | None = None,
    author_id: str | None = None,
    sort: SortField = "title",
    limit: int = 200,
) -> list[SubjectRow]:
    stmt = select(SubjectRow)
    if domain:
        stmt = stmt.join(SubjectRow.domains).where(
            SubjectRow.domains.any(domain_slug=domain)
        )
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(SubjectRow.title.ilike(like) | SubjectRow.slug.ilike(like))
    if author_id:
        stmt = stmt.join(SubjectRow.authors).where(SubjectAuthorRow.user_id == author_id)
    if sort == "title":
        stmt = stmt.order_by(SubjectRow.title.asc())
    elif sort == "updated_at":
        stmt = stmt.order_by(SubjectRow.updated_at.desc())
    elif sort == "estimated_hours":
        stmt = stmt.order_by(SubjectRow.estimated_hours.asc())
    elif sort == "difficulty":
        stmt = stmt.order_by(SubjectRow.difficulty.asc(), SubjectRow.title.asc())
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).unique().scalars().all())


def get_subject_row(db: Session, slug: str) -> SubjectRow | None:
    return db.execute(select(SubjectRow).where(SubjectRow.slug == slug)).scalar_one_or_none()


def get_lesson_row(db: Session, slug: str, order: int) -> LessonRow | None:
    return db.execute(
        select(LessonRow)
        .join(SubjectRow, SubjectRow.id == LessonRow.subject_id)
        .where(SubjectRow.slug == slug, LessonRow.order == order)
    ).scalar_one_or_none()


def get_authors(db: Session, subject_id: int) -> list[UserRow]:
    return list(
        db.execute(
            select(UserRow)
            .join(SubjectAuthorRow, SubjectAuthorRow.user_id == UserRow.id)
            .where(SubjectAuthorRow.subject_id == subject_id)
        ).scalars().all()
    )


@dataclass(frozen=True)
class PrereqNode:
    slug: str
    title: str
    depth: int
    via: str | None


def transitive_prereqs(db: Session, slug: str) -> list[PrereqNode]:
    """Recursive CTE: walk prereqs of `slug` outward. Each row gets a depth and
    `via` (the immediate predecessor in the walk) for tree rendering."""
    sql = text(
        """
        WITH RECURSIVE walk AS (
            SELECT
                sp.prereq_slug AS slug,
                s.id           AS subject_id,
                s.title        AS title,
                1              AS depth,
                start_s.slug   AS via
            FROM subjects start_s
            JOIN subject_prerequisites sp ON sp.subject_id = start_s.id
            JOIN subjects s ON s.slug = sp.prereq_slug
            WHERE start_s.slug = :start

            UNION

            SELECT
                sp.prereq_slug AS slug,
                ns.id          AS subject_id,
                ns.title       AS title,
                w.depth + 1    AS depth,
                w.slug         AS via
            FROM walk w
            JOIN subject_prerequisites sp ON sp.subject_id = w.subject_id
            JOIN subjects ns ON ns.slug = sp.prereq_slug
        )
        SELECT DISTINCT ON (slug) slug, title, depth, via
        FROM walk
        ORDER BY slug, depth ASC
        """
    )
    rows = db.execute(sql, {"start": slug}).all()
    nodes = [PrereqNode(slug=r.slug, title=r.title, depth=r.depth, via=r.via) for r in rows]
    nodes.sort(key=lambda n: (n.depth, n.slug))
    return nodes


def dependents(db: Session, slug: str) -> list[SubjectRow]:
    """Subjects that list `slug` as a direct prereq."""
    return list(
        db.execute(
            select(SubjectRow)
            .join(SubjectRow.prerequisites)
            .where(SubjectRow.prerequisites.any(prereq_slug=slug))
            .order_by(SubjectRow.title.asc())
        ).unique().scalars().all()
    )


def load_state(storage: StorageBackend, slug: str) -> SubjectState:
    return content_io.load_subject_state(storage, slug)


def load_lesson(storage: StorageBackend, slug: str, order: int) -> LessonRecord | None:
    state = content_io.load_subject_state(storage, slug)
    for lesson in state.lessons:
        if lesson.frontmatter.order == order:
            return lesson
    return None


def concatenated_raw_markdown(state: SubjectState) -> str:
    """Build a single AI-friendly markdown blob for the human side of a subject."""
    parts: list[str] = []
    m = state.manifest
    parts.append(f"# {m.title}")
    parts.append("")
    parts.append(f"slug: `{m.slug}`")
    if m.domains:
        parts.append(f"domains: {', '.join(m.domains)}")
    if m.prerequisites:
        parts.append(f"prerequisites: {', '.join(m.prerequisites)}")
    parts.append(f"difficulty: {m.difficulty.value}")
    parts.append(f"estimated_hours: {m.estimated_hours}")
    parts.append("")
    parts.append("## Overview")
    parts.append("")
    parts.append(state.overview.strip())
    parts.append("")
    for lesson in state.lessons:
        fm = lesson.frontmatter
        parts.append(f"## Lesson {fm.order}: {fm.title}")
        parts.append("")
        parts.append(f"_estimated time: {fm.estimated_minutes} minutes_")
        parts.append("")
        parts.append("**Learning objectives:**")
        for obj in fm.learning_objectives:
            parts.append(f"- {obj}")
        parts.append("")
        parts.append(lesson.body.strip())
        parts.append("")
    if state.references:
        parts.append("## References")
        parts.append("")
        parts.append(state.references.strip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


# ---------- Domain tree (for API) ----------


def load_domain_tree(db: Session) -> DomainTree:
    """Build a DomainTree DTO from the `domains` table."""
    from hivemind.db.models import DomainRow

    rows = list(db.execute(select(DomainRow).order_by(DomainRow.sort_order.asc())).scalars().all())
    by_slug: dict[str, DomainNode] = {}
    children_map: dict[str | None, list[DomainNode]] = {}
    for r in rows:
        node = DomainNode(slug=r.slug, title=r.title, children=[])
        by_slug[r.slug] = node
        children_map.setdefault(r.parent_slug, []).append(node)
    for parent, kids in children_map.items():
        if parent is None:
            continue
        if parent in by_slug:
            by_slug[parent].children.extend(kids)
    roots = children_map.get(None, [])
    return DomainTree(domains=roots)
