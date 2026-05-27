"""validate_schema: build the proposed SubjectState from payload and validate.

Each operation has its own way of constructing the proposed state from
`ctx.payload` + `ctx.existing`. Schema validation happens implicitly through
the pydantic models.
"""
from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from hivemind.models.subject import (
    LessonRecord,
    SubjectManifest,
    SubjectState,
)
from hivemind.pipeline.context import MutationContext, MutationOperation, PipelineRejected

STEP_NAME = "validate_schema"


def _validate(model_cls: Any, data: Any) -> Any:
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise PipelineRejected(STEP_NAME, str(exc), status_code=422) from exc


def _next_version(existing: SubjectState | None) -> int:
    if existing is None:
        return 1
    return existing.manifest.version + 1


def _build_proposed(ctx: MutationContext) -> SubjectState:
    op = ctx.operation
    payload = ctx.payload

    if op == MutationOperation.CREATE_SUBJECT:
        manifest_in = dict(payload.get("manifest") or {})
        manifest_in.setdefault("slug", ctx.slug)
        manifest_in.setdefault("version", 1)
        manifest_in.setdefault(
            "authors", [{"id": ctx.actor.id, "role": "original"}]
        )
        manifest = _validate(SubjectManifest, manifest_in)
        overview = str(payload.get("overview") or "").strip()
        if not overview:
            raise PipelineRejected(STEP_NAME, "overview.md content is required", status_code=422)
        lessons_in = payload.get("lessons") or []
        if not lessons_in:
            raise PipelineRejected(
                STEP_NAME,
                "A new subject must include at least one lesson.",
                status_code=422,
            )
        lessons = [_validate(LessonRecord, l) for l in lessons_in]
        return _validate(
            SubjectState,
            {"manifest": manifest, "overview": overview, "lessons": lessons},
        )

    assert ctx.existing is not None

    if op == MutationOperation.UPDATE_SUBJECT:
        manifest_in = dict(payload.get("manifest") or {})
        manifest_in.setdefault("slug", ctx.slug)
        manifest_in["version"] = _next_version(ctx.existing)
        # Preserve authors unless explicitly overwritten
        if "authors" not in manifest_in:
            manifest_in["authors"] = [a.model_dump() for a in ctx.existing.manifest.authors]
        if "forked_from" not in manifest_in and ctx.existing.manifest.forked_from is not None:
            manifest_in["forked_from"] = ctx.existing.manifest.forked_from.model_dump()
        manifest = _validate(SubjectManifest, manifest_in)
        overview = str(payload.get("overview") or ctx.existing.overview)
        return _validate(
            SubjectState,
            {
                "manifest": manifest,
                "overview": overview,
                "lessons": [l.model_dump() for l in ctx.existing.lessons],
                "references": ctx.existing.references,
                "exercises": dict(ctx.existing.exercises),
            },
        )

    if op == MutationOperation.UPDATE_LESSON:
        lesson_in = payload.get("lesson") or {}
        new_lesson = _validate(LessonRecord, lesson_in)
        new_lessons = [
            new_lesson if l.frontmatter.order == new_lesson.frontmatter.order else l
            for l in ctx.existing.lessons
        ]
        if not any(l.frontmatter.order == new_lesson.frontmatter.order for l in new_lessons):
            raise PipelineRejected(
                STEP_NAME,
                f"No existing lesson with order {new_lesson.frontmatter.order} to update.",
                status_code=404,
            )
        manifest = ctx.existing.manifest.model_copy(update={"version": _next_version(ctx.existing)})
        return _validate(
            SubjectState,
            {
                "manifest": manifest,
                "overview": ctx.existing.overview,
                "lessons": [l.model_dump() for l in new_lessons],
                "references": ctx.existing.references,
                "exercises": dict(ctx.existing.exercises),
            },
        )

    if op == MutationOperation.CREATE_LESSON:
        lesson_in = payload.get("lesson") or {}
        new_lesson = _validate(LessonRecord, lesson_in)
        existing_orders = {l.frontmatter.order for l in ctx.existing.lessons}
        if new_lesson.frontmatter.order in existing_orders:
            raise PipelineRejected(
                STEP_NAME,
                f"A lesson with order {new_lesson.frontmatter.order} already exists.",
                status_code=409,
            )
        lessons = [*ctx.existing.lessons, new_lesson]
        manifest = ctx.existing.manifest.model_copy(update={"version": _next_version(ctx.existing)})
        return _validate(
            SubjectState,
            {
                "manifest": manifest,
                "overview": ctx.existing.overview,
                "lessons": [l.model_dump() for l in lessons],
                "references": ctx.existing.references,
                "exercises": dict(ctx.existing.exercises),
            },
        )

    if op == MutationOperation.FORK_SUBJECT:
        new_slug = str(payload.get("new_slug") or "").strip()
        if not new_slug:
            raise PipelineRejected(STEP_NAME, "Fork requires `new_slug`", status_code=422)
        base = ctx.existing.manifest.model_dump(mode="python")
        base.update(
            {
                "slug": new_slug,
                "version": 1,
                "status": "draft",
                "authors": [{"id": ctx.actor.id, "role": "original"}],
                "forked_from": {
                    "slug": ctx.existing.manifest.slug,
                    "version": ctx.existing.manifest.version,
                },
            }
        )
        manifest = _validate(SubjectManifest, base)
        return _validate(
            SubjectState,
            {
                "manifest": manifest,
                "overview": ctx.existing.overview,
                "lessons": [l.model_dump() for l in ctx.existing.lessons],
                "references": ctx.existing.references,
                "exercises": dict(ctx.existing.exercises),
            },
        )

    if op == MutationOperation.RESTORE_VERSION:
        # Build proposed from a previously written state already loaded into payload.
        restored = payload.get("restored_state")
        if not isinstance(restored, SubjectState):
            raise PipelineRejected(
                STEP_NAME,
                "Restore must supply `restored_state` in payload (set by load_existing-equivalent).",
                status_code=500,
            )
        manifest = restored.manifest.model_copy(update={"version": _next_version(ctx.existing)})
        return _validate(
            SubjectState,
            {
                "manifest": manifest,
                "overview": restored.overview,
                "lessons": [l.model_dump() for l in restored.lessons],
                "references": restored.references,
                "exercises": dict(restored.exercises),
            },
        )

    raise PipelineRejected(STEP_NAME, f"Unknown operation: {op}", status_code=500)


async def validate_schema(ctx: MutationContext) -> MutationContext:
    ctx.proposed = _build_proposed(ctx)
    if ctx.proposed.manifest.slug != ctx.slug and ctx.operation != MutationOperation.FORK_SUBJECT:
        raise PipelineRejected(
            STEP_NAME,
            f"Proposed manifest slug {ctx.proposed.manifest.slug!r} does not match URL slug "
            f"{ctx.slug!r}.",
            status_code=422,
        )
    return ctx
