"""regenerate_ai_representation: v1 STUB.

Logs `todo: ai representation regen step` and passes through. The future
implementation will:

  - read the just-written human content from storage
  - diff against the previous human version (ctx.existing)
  - prompt an LLM to incrementally update ai/agent.md, ai/facts.yaml, and
    ai/glossary.yaml (passing the prior ai/* as anchor)
  - write the regenerated artifacts to storage under the `ai/` prefix
  - bump ai/meta.yaml's `regenerated_from_human_version` to match
    ctx.proposed.manifest.version

It will eventually move to an async background queue so the user-facing write
isn't blocked on an LLM call. The pipeline interface stays the same.
"""
from __future__ import annotations

from hivemind.logging_setup import get_logger
from hivemind.pipeline.context import MutationContext

STEP_NAME = "regenerate_ai_representation"

log = get_logger("hivemind.pipeline.regenerate_ai_representation")


async def regenerate_ai_representation(ctx: MutationContext) -> MutationContext:
    log.info(
        "todo: ai representation regen step",
        operation=ctx.operation,
        slug=ctx.slug,
        from_version=(ctx.existing.manifest.version if ctx.existing else None),
        to_version=(ctx.proposed.manifest.version if ctx.proposed else None),
    )
    ctx.record(STEP_NAME, action="skipped", reason="stub")
    return ctx
