"""audit_log: persist a record of the mutation to the edit_events table.

Captures who/what/when/which-version for observability and rollback discovery.
"""
from __future__ import annotations

from hivemind.db.models import EditEventRow
from hivemind.pipeline.context import MutationContext

STEP_NAME = "audit_log"


async def audit_log(ctx: MutationContext) -> MutationContext:
    assert ctx.proposed is not None
    payload = {
        "from_version": ctx.existing.manifest.version if ctx.existing else None,
        "to_version": ctx.proposed.manifest.version,
        "steps": ctx.audit,
    }
    ctx.db.add(
        EditEventRow(
            user_id=ctx.actor.id,
            operation=ctx.operation.value,
            slug=ctx.proposed.manifest.slug,
            payload=payload,
            accepted=True,
        )
    )
    ctx.db.flush()
    return ctx
