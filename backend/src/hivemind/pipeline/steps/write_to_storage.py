"""write_to_storage: serialize ctx.proposed and write to the human side.

Only the human side is written here (subject.yaml, overview.md, lessons/*,
optional references.md / exercises/*). The AI representation is owned by the
`regenerate_ai_representation` step downstream.

For FORK_SUBJECT, the existing subject's full prefix is recursively copied to
the new slug's prefix first (so optional files like references.md are
preserved), and then the new manifest is written on top.
"""
from __future__ import annotations

from hivemind.pipeline.context import MutationContext, MutationOperation
from hivemind.services import content_io

STEP_NAME = "write_to_storage"


async def write_to_storage(ctx: MutationContext) -> MutationContext:
    assert ctx.proposed is not None

    if ctx.operation == MutationOperation.FORK_SUBJECT:
        src = content_io.subject_dir(ctx.slug)
        dst = content_io.subject_dir(ctx.proposed.manifest.slug)
        ctx.storage.copy_prefix(src, dst)

    content_io.dump_subject_state(ctx.storage, ctx.proposed)

    ctx.record(STEP_NAME, slug=ctx.proposed.manifest.slug, version=ctx.proposed.manifest.version)
    return ctx
