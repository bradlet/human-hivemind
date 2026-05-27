"""update_index: upsert Postgres rows from ctx.proposed.

This makes the new state queryable by /api/subjects, /api/subjects/{slug},
/api/subjects?domain=..., prereq DAG queries, etc.

Authors are upserted by user id. If an author id corresponds to a user not yet
in the users table (e.g. legacy seed content authored by `user_seed`), the
join row is skipped silently — the index can be rebuilt safely from storage
and missing user FKs would just block everything otherwise.
"""
from __future__ import annotations

from hivemind.pipeline.context import MutationContext
from hivemind.services.db_sync import upsert_subject_state

STEP_NAME = "update_index"


async def update_index(ctx: MutationContext) -> MutationContext:
    assert ctx.proposed is not None
    row = upsert_subject_state(ctx.db, ctx.proposed)
    ctx.record(STEP_NAME, subject_id=row.id)
    return ctx
