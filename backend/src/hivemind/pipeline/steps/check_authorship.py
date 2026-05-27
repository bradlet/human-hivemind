"""check_authorship: enforce author-only edits on existing subjects.

- CREATE_SUBJECT and FORK_SUBJECT: any authenticated user may perform.
- UPDATE_SUBJECT, UPDATE_LESSON, CREATE_LESSON, RESTORE_VERSION: actor must be
  in the existing manifest's authors list.
"""
from __future__ import annotations

from hivemind.pipeline.context import MutationContext, MutationOperation, PipelineRejected

STEP_NAME = "check_authorship"

EDIT_OPS = {
    MutationOperation.UPDATE_SUBJECT,
    MutationOperation.UPDATE_LESSON,
    MutationOperation.CREATE_LESSON,
    MutationOperation.RESTORE_VERSION,
}


async def check_authorship(ctx: MutationContext) -> MutationContext:
    if ctx.operation in {MutationOperation.CREATE_SUBJECT, MutationOperation.FORK_SUBJECT}:
        return ctx

    if ctx.operation in EDIT_OPS:
        assert ctx.existing is not None
        author_ids = {a.id for a in ctx.existing.manifest.authors}
        if ctx.actor.id not in author_ids:
            raise PipelineRejected(
                STEP_NAME,
                f"User {ctx.actor.id!r} is not an author of {ctx.slug!r}. "
                "Fork this subject to make your own version instead.",
                status_code=403,
            )
        return ctx

    raise PipelineRejected(STEP_NAME, f"Unhandled operation {ctx.operation}", status_code=500)
