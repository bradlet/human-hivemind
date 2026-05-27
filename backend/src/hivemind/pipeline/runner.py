"""Pipeline composer / runner."""
from __future__ import annotations

from collections.abc import Awaitable, Callable

from hivemind.logging_setup import get_logger
from hivemind.pipeline.context import MutationContext, PipelineRejected

Step = Callable[[MutationContext], Awaitable[MutationContext]]

log = get_logger("hivemind.pipeline")


async def run_pipeline(ctx: MutationContext, steps: list[Step]) -> MutationContext:
    """Run `steps` in order. A step may raise PipelineRejected to abort."""
    log.info(
        "pipeline.start",
        operation=ctx.operation,
        slug=ctx.slug,
        actor=ctx.actor.id,
        steps=[s.__name__ for s in steps],
    )
    for step in steps:
        try:
            ctx = await step(ctx)
        except PipelineRejected as exc:
            log.warning(
                "pipeline.rejected",
                operation=ctx.operation,
                slug=ctx.slug,
                step=exc.step,
                reason=exc.reason,
            )
            raise
        except Exception:
            log.exception(
                "pipeline.error",
                operation=ctx.operation,
                slug=ctx.slug,
                step=step.__name__,
            )
            raise
    log.info("pipeline.done", operation=ctx.operation, slug=ctx.slug)
    return ctx
