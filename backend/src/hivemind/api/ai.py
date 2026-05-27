"""AI-side read endpoints.

Serves the regenerated AI representation of a subject. These endpoints exist
specifically for LLM/agent clients that want a terse, token-efficient view of
a subject without the lesson prose.

All endpoints return 200 even when the AI representation is missing or stale —
the staleness flag and null fields communicate that. (v2 may queue a regen.)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from hivemind.api.deps import get_db, get_storage
from hivemind.api.schemas import AIFactsOut, AIGlossaryOut, AIRepresentationOut
from hivemind.services import content_io, subject_service
from hivemind.storage import StorageBackend

router = APIRouter(prefix="/subjects/{slug}/ai", tags=["ai"])


def _build_ai_response(
    storage: StorageBackend, db: Session, slug: str
) -> AIRepresentationOut:
    row = subject_service.get_subject_row(db, slug)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    ai = content_io.load_ai_representation(storage, slug)
    current_version = row.version
    regen_from = ai.meta.regenerated_from_human_version if ai.meta else None
    is_stale = ai.meta is None or regen_from is None or regen_from < current_version
    facts_out = (
        AIFactsOut(
            key_formulas=[f.model_dump() for f in ai.facts.key_formulas],
            key_theorems=[t.model_dump() for t in ai.facts.key_theorems],
            numeric_facts=list(ai.facts.numeric_facts),
        )
        if ai.facts is not None
        else None
    )
    glossary_out = (
        AIGlossaryOut(terms=dict(ai.glossary.terms)) if ai.glossary is not None else None
    )
    return AIRepresentationOut(
        slug=slug,
        agent_md=ai.agent.body if ai.agent else None,
        facts=facts_out,
        glossary=glossary_out,
        regenerated_at=ai.meta.regenerated_at if ai.meta else None,
        regenerated_from_human_version=regen_from,
        current_human_version=current_version,
        is_stale=is_stale,
        model=ai.meta.model if ai.meta else None,
    )


@router.get("", response_model=AIRepresentationOut)
def get_ai_representation(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> AIRepresentationOut:
    return _build_ai_response(storage, db, slug)


@router.get(".md")
def get_ai_markdown(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> Response:
    if subject_service.get_subject_row(db, slug) is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    ai = content_io.load_ai_representation(storage, slug)
    if ai.agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"AI representation not yet generated for {slug!r}.",
        )
    return Response(content=ai.agent.body, media_type="text/markdown; charset=utf-8")


@router.get("/facts", response_model=AIFactsOut)
def get_ai_facts(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> AIFactsOut:
    if subject_service.get_subject_row(db, slug) is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    ai = content_io.load_ai_representation(storage, slug)
    if ai.facts is None:
        return AIFactsOut()
    return AIFactsOut(
        key_formulas=[f.model_dump() for f in ai.facts.key_formulas],
        key_theorems=[t.model_dump() for t in ai.facts.key_theorems],
        numeric_facts=list(ai.facts.numeric_facts),
    )


@router.get("/glossary", response_model=AIGlossaryOut)
def get_ai_glossary(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> AIGlossaryOut:
    if subject_service.get_subject_row(db, slug) is None:
        raise HTTPException(status_code=404, detail=f"Subject {slug!r} not found")
    ai = content_io.load_ai_representation(storage, slug)
    if ai.glossary is None:
        return AIGlossaryOut()
    return AIGlossaryOut(terms=dict(ai.glossary.terms))
