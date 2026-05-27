"""load_existing: fetch the current SubjectState from storage if any.

Sets `ctx.existing`. Leaves `proposed` untouched. For CREATE_SUBJECT operations,
verifies that no subject with this slug already exists.
"""
from __future__ import annotations

from hivemind.pipeline.context import MutationContext, MutationOperation, PipelineRejected
from hivemind.services import content_io

STEP_NAME = "load_existing"


async def load_existing(ctx: MutationContext) -> MutationContext:
    try:
        ctx.existing = content_io.load_subject_state(ctx.storage, ctx.slug)
    except ValueError:
        ctx.existing = None

    if ctx.operation == MutationOperation.CREATE_SUBJECT and ctx.existing is not None:
        raise PipelineRejected(
            STEP_NAME,
            f"Subject {ctx.slug!r} already exists; pick a different slug or fork it instead.",
            status_code=409,
        )

    if (
        ctx.operation
        in {
            MutationOperation.UPDATE_SUBJECT,
            MutationOperation.UPDATE_LESSON,
            MutationOperation.CREATE_LESSON,
            MutationOperation.FORK_SUBJECT,
            MutationOperation.RESTORE_VERSION,
        }
        and ctx.existing is None
    ):
        raise PipelineRejected(
            STEP_NAME,
            f"Subject {ctx.slug!r} does not exist in storage.",
            status_code=404,
        )

    return ctx
