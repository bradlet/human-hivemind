"""Verify the moderate and regenerate_ai_representation stubs both run and
both pass through (they should not raise PipelineRejected).
"""
from __future__ import annotations

import pytest

from hivemind.models.user import User
from hivemind.pipeline.context import MutationContext, MutationOperation
from hivemind.pipeline.steps.moderate import moderate
from hivemind.pipeline.steps.regenerate_ai_representation import (
    regenerate_ai_representation,
)


def _ctx() -> MutationContext:
    return MutationContext(
        operation=MutationOperation.CREATE_SUBJECT,
        actor=User(id="u1", email="u1@example.com", name="u1"),
        slug="x",
        payload={},
        storage=None,  # type: ignore[arg-type]
        db=None,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_moderate_passes_through():
    ctx = _ctx()
    out = await moderate(ctx)
    assert out is ctx
    assert any(a["step"] == "moderate" for a in ctx.audit)


@pytest.mark.asyncio
async def test_regenerate_ai_passes_through():
    ctx = _ctx()
    out = await regenerate_ai_representation(ctx)
    assert out is ctx
    assert any(a["step"] == "regenerate_ai_representation" for a in ctx.audit)
