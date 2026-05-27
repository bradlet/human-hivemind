"""moderate: v1 STUB.

Logs a `todo: moderation step` line and passes through. The future
implementation will:

  - compute a diff between ctx.existing and ctx.proposed
  - call an LLM fact-checker / safety classifier
  - screen for CSAM, illegal content, prompt injection
  - attach a `moderation_decision` to ctx.metadata
  - either raise PipelineRejected(...) to block the write, or pass through
"""
from __future__ import annotations

from hivemind.logging_setup import get_logger
from hivemind.pipeline.context import MutationContext

STEP_NAME = "moderate"

log = get_logger("hivemind.pipeline.moderate")


async def moderate(ctx: MutationContext) -> MutationContext:
    log.info(
        "todo: moderation step",
        operation=ctx.operation,
        slug=ctx.slug,
        actor=ctx.actor.id,
        from_version=(ctx.existing.manifest.version if ctx.existing else None),
        to_version=(ctx.proposed.manifest.version if ctx.proposed else None),
    )
    ctx.record(STEP_NAME, decision="passthrough", reason="stub")
    return ctx
