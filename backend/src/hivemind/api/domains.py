"""/api/domains."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from hivemind.api.deps import get_db
from hivemind.api.schemas import DomainNodeOut, DomainTreeOut
from hivemind.models.domain import DomainNode
from hivemind.services.subject_service import load_domain_tree

router = APIRouter(prefix="/domains", tags=["domains"])


def _to_dto(node: DomainNode) -> DomainNodeOut:
    return DomainNodeOut(
        slug=node.slug,
        title=node.title,
        children=[_to_dto(c) for c in node.children],
    )


@router.get("", response_model=DomainTreeOut)
def get_domains(db: Annotated[Session, Depends(get_db)]) -> DomainTreeOut:
    tree = load_domain_tree(db)
    return DomainTreeOut(domains=[_to_dto(n) for n in tree.domains])
