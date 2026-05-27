"""validate_references: every referenced domain and prereq slug must exist.

Domain slugs are checked against the `domains` table. Prereq slugs are checked
against the `subjects` table. Self-references were already rejected by
SubjectManifest.
"""
from __future__ import annotations

from sqlalchemy import select

from hivemind.db.models import DomainRow, SubjectRow
from hivemind.pipeline.context import MutationContext, PipelineRejected

STEP_NAME = "validate_references"


async def validate_references(ctx: MutationContext) -> MutationContext:
    assert ctx.proposed is not None
    manifest = ctx.proposed.manifest

    if manifest.domains:
        rows = ctx.db.execute(
            select(DomainRow.slug).where(DomainRow.slug.in_(manifest.domains))
        ).scalars().all()
        missing = sorted(set(manifest.domains) - set(rows))
        if missing:
            raise PipelineRejected(
                STEP_NAME,
                f"Domain slug(s) do not exist: {missing}. Add them to domains.yaml first.",
                status_code=422,
            )

    if manifest.prerequisites:
        rows = ctx.db.execute(
            select(SubjectRow.slug).where(SubjectRow.slug.in_(manifest.prerequisites))
        ).scalars().all()
        missing = sorted(set(manifest.prerequisites) - set(rows))
        if missing:
            raise PipelineRejected(
                STEP_NAME,
                f"Prerequisite subject(s) do not exist: {missing}.",
                status_code=422,
            )

    return ctx
